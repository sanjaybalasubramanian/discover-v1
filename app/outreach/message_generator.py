"""
AI-powered email message generator
"""
import os
import json
from typing import Dict
import boto3


class EmailMessageGenerator:
    """Generate personalized email messages using AI"""
    
    def __init__(self):
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-2'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.model_id = os.getenv('BEDROCK_MODEL', 'us.anthropic.claude-haiku-5-5')
    
    async def generate_cold_outreach(
        self,
        contact: Dict,
        your_profile: Dict,
        job_info: Dict = None
    ) -> Dict:
        """Generate cold outreach email"""
        
        job_details_str = ""
        if job_info:
            job_title = job_info.get('title', '')
            job_desc = job_info.get('description', '')[:200]
            job_details_str = f"JOB DETAILS:\n- Title: {job_title}\n- Description: {job_desc}"
        
        prompt = f"""Generate a professional cold outreach email for a job application.

RECIPIENT:
- Name: {contact.get('name', 'Hiring Manager')}
- Title: {contact.get('title', 'Recruiter')}
- Company: {contact.get('company')}

SENDER PROFILE:
- Name: {your_profile['name']}
- Current Role: {your_profile.get('current_role', '')}
- Skills: {', '.join(your_profile.get('skills', []))}
- Experience: {your_profile.get('experience', '')}
- Location: {your_profile.get('location', '')}

{job_details_str}

REQUIREMENTS:
1. Subject line (under 50 characters, compelling)
2. Professional yet personable tone
3. Mention specific skills relevant to company
4. Show genuine interest in the company
5. Clear call-to-action (request for interview/call)
6. Keep email under 200 words
7. Include proper greeting and signature

Return JSON format:
{{
    "subject": "...",
    "html_body": "...",
    "text_body": "..."
}}

Make it natural, not templated. Avoid cliches."""

        response = self._call_bedrock(prompt)
        return self._parse_email_response(response)
    
    async def generate_follow_up(
        self,
        contact: Dict,
        previous_email: Dict,
        days_since: int
    ) -> Dict:
        """Generate follow-up email"""
        
        prompt = f"""Generate a polite follow-up email for a job application.

CONTEXT:
- Originally emailed {days_since} days ago
- No response yet
- Previous subject: {previous_email.get('subject')}

RECIPIENT:
- Name: {contact.get('name')}
- Title: {contact.get('title')}
- Company: {contact.get('company')}

REQUIREMENTS:
1. Polite and brief
2. Reference previous email
3. Add new value (don't just say "following up")
4. Respectful of their time
5. Clear call-to-action
6. Under 150 words

Return JSON format:
{{
    "subject": "...",
    "html_body": "...",
    "text_body": "..."
}}"""

        response = self._call_bedrock(prompt)
        return self._parse_email_response(response)
    
    def _call_bedrock(self, prompt: str) -> str:
        """Call Bedrock Claude API"""
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        
        # Handle different response formats
        if 'content' in response_body:
            # New format: content is an array of blocks
            for block in response_body['content']:
                if 'text' in block:
                    return block['text']
                elif isinstance(block, dict) and block.get('type') == 'text':
                    return block.get('text', '')
        
        # Fallback to old format
        return response_body.get('completion', '')
    
    def _parse_email_response(self, response: str) -> Dict:
        """Parse AI response to extract email components"""
        
        try:
            # Try to parse as JSON
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            data = json.loads(response.strip())
            return data
        
        except:
            # Fallback: return raw response
            return {
                'subject': 'Job Application - Software Engineer',
                'html_body': f'<p>{response}</p>',
                'text_body': response
            }
