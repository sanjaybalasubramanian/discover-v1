"""
AWS Bedrock LLM client for intelligent parsing and extraction
Supports Claude 3.5 Sonnet and Claude 3 Haiku
"""
import json
import os
from typing import List, Optional

import boto3
from pydantic import BaseModel

# Initialize Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# Model configuration
BEDROCK_MODEL = os.getenv('BEDROCK_MODEL', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
# Options:
# - anthropic.claude-3-5-sonnet-20240620-v1:0 (smart, expensive)
# - anthropic.claude-3-haiku-20240307-v1:0 (fast, cheap)

# Structured outputs
class ParsedJob(BaseModel):
    """Structured job data"""
    company_name: str
    role_title: str
    location: str
    experience_years: Optional[int] = None
    is_relevant: bool
    confidence: float  # 0-1

class ExtractedContact(BaseModel):
    """Structured contact data"""
    email: str
    name: Optional[str] = None
    title: Optional[str] = None
    is_recruiter: bool
    confidence: float  # 0-1
    reasoning: str

async def invoke_bedrock(prompt: str, system: str = "", max_tokens: int = 500) -> str:
    """
    Call AWS Bedrock with Claude model

    Args:
        prompt: User prompt
        system: System message
        max_tokens: Max response tokens

    Returns:
        Model response text
    """

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    # Only add thinking/output_config for Claude 3.7+ models
    # Claude 3.5 Sonnet v1 doesn't support these parameters
    if 'claude-3-7' in BEDROCK_MODEL or 'claude-4' in BEDROCK_MODEL:
        body["thinking"] = {"type": "adaptive"}
        body["output_config"] = {"effort": "low"}

    if system:
        body["system"] = system

    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps(body)
        )

        response_body = json.loads(response['body'].read())

        # Handle different response formats
        if 'content' in response_body:
            # Standard format: {"content": [{"text": "..."}, {"type": "thinking", ...}]}
            content_items = response_body['content']

            # Find the text content (skip thinking/other types)
            for item in content_items:
                if isinstance(item, dict):
                    if item.get('type') == 'text' and 'text' in item:
                        return item['text']
                    elif 'text' in item and item.get('type') != 'thinking':
                        return item['text']

            # Fallback: if no text found, check if there's thinking output
            for item in content_items:
                if isinstance(item, dict) and 'thinking' in item:
                    return item['thinking']

            # Last resort: return first item with text
            if content_items and isinstance(content_items[0], dict) and 'text' in content_items[0]:
                return content_items[0]['text']

            raise ValueError(f"No text content found in response: {content_items}")

        elif 'completion' in response_body:
            # Legacy format: {"completion": "..."}
            return response_body['completion']
        else:
            # Fallback: try to extract text from any structure
            print(f"Unknown response format: {response_body.keys()}")
            raise ValueError(f"Unexpected response format: {list(response_body.keys())}")

    except KeyError as e:
        print(f"Bedrock API error: Missing key '{e}' in response")
        print(f"Response structure: {response_body if 'response_body' in locals() else 'N/A'}")
        raise
    except Exception as e:
        print(f"Bedrock API error: {e}")
        raise

async def parse_job_listing(
    title: str,
    url: str,
    snippet: str,
    full_text: Optional[str] = None
) -> ParsedJob:
    """
    Parse job listing using LLM to extract structured data

    Args:
        title: Raw search result title
        url: Job listing URL
        snippet: Search result snippet
        full_text: Full page text (if available)

    Returns:
        ParsedJob with clean, structured data
    """

    context = full_text if full_text else snippet

    prompt = f"""You are an expert at parsing job listings. Extract structured data from this job posting.

URL: {url}
Title: {title}
Content: {context[:2000]}

Extract:
1. company_name: The company hiring (clean name only, no extra text)
2. role_title: The job role (clean title, e.g., "GenAI Engineer", "AI Engineer")
3. location: Primary work location (city name or "Remote")
4. experience_years: Required years of experience (integer, null if not specified)
5. is_relevant: Is this a GenAI/LLM/AI Engineer role? (boolean)
6. confidence: Your confidence in the extraction (0.0 to 1.0)

Return ONLY valid JSON:
{{
  "company_name": "string",
  "role_title": "string",
  "location": "string",
  "experience_years": number or null,
  "is_relevant": boolean,
  "confidence": number
}}

Rules:
- Clean company names (remove "Jobs at", "Careers", etc.)
- Standardize role titles (use "GenAI Engineer" not "Gen AI Eng")
- Location should be city name or "Remote" or "Remote (India)"
- Only mark is_relevant=true for AI/ML/GenAI engineering roles
"""

    system = "You are a precise job listing parser. Always return valid JSON only, no markdown or extra text."

    try:
        response_text = await invoke_bedrock(prompt, system, max_tokens=300)

        # Extract JSON from response (Claude sometimes adds markdown)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]

        result = json.loads(json_str)
        return ParsedJob(**result)

    except Exception as e:
        print(f"LLM parsing failed: {e}")
        # Fallback to basic parsing
        return ParsedJob(
            company_name=title.split('|')[0].strip() if '|' in title else "Unknown",
            role_title=title.split('|')[1].strip() if '|' in title else title[:100],
            location="Unknown",
            experience_years=None,
            is_relevant=True,
            confidence=0.3
        )

async def extract_best_contacts(
    page_text: str,
    url: str,
    found_emails: List[str]
) -> List[ExtractedContact]:
    """
    Use LLM to identify best contacts from extracted emails

    Args:
        page_text: Full page content
        url: Source URL
        found_emails: List of email addresses found via regex

    Returns:
        List of ExtractedContact, ranked by relevance
    """

    if not found_emails:
        return []

    # Limit context to reduce tokens
    context_snippet = page_text[:3000]

    prompt = f"""You are an expert at identifying the best contact person for job applications.

Source: {url}
Context: {context_snippet}

Found these email addresses:
{json.dumps(found_emails)}

For EACH email, determine:
1. email: The email address
2. name: Person's name if mentioned (or null)
3. title: Person's job title if mentioned (or null)
4. is_recruiter: Is this a recruiter/HR/hiring manager? (boolean)
5. confidence: How confident are you this is a good contact? (0.0 to 1.0)
6. reasoning: Brief explanation (1 sentence)

Ranking: Named recruiters > HR emails > Generic emails
Avoid: noreply@, info@, admin@

Return valid JSON array sorted by confidence (highest first):
[{{"email": "...", "name": null, "title": null, "is_recruiter": true, "confidence": 0.9, "reasoning": "..."}}]
"""

    system = "You are an expert at evaluating job contacts. Return valid JSON array only."

    try:
        response_text = await invoke_bedrock(prompt, system, max_tokens=800)

        # Extract JSON array from response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        json_str = response_text[json_start:json_end]

        contacts_data = json.loads(json_str)

        return [ExtractedContact(**contact) for contact in contacts_data]

    except Exception as e:
        print(f"LLM contact extraction failed: {e}")
        # Fallback
        return [
            ExtractedContact(
                email=email,
                name=None,
                title=None,
                is_recruiter='hr' in email.lower() or 'career' in email.lower(),
                confidence=0.5,
                reasoning="Fallback scoring"
            )
            for email in found_emails
        ]


