"""
Email extraction from text with evidence and classification
"""
import re
from typing import List, Optional


class ExtractedEmail:
    """Extracted email with context and classification"""
    def __init__(self, email: str, surrounding_text: str, name: str = None, title: str = None, classification: str = None, linkedin_url: str = None, location: str = None, priority_score: float = None):
        self.email = email
        self.surrounding_text = surrounding_text
        self.name = name
        self.title = title
        self.classification = classification
        self.linkedin_url = linkedin_url  # LinkedIn profile URL
        self.location = location  # Geographic location
        self.priority_score = priority_score  # Priority score (1.0 = highest)

    def to_dict(self):
        return {
            'email': self.email,
            'surrounding_text': self.surrounding_text,
            'name': self.name,
            'title': self.title,
            'classification': self.classification,
            'linkedin_url': self.linkedin_url,
            'location': self.location,
            'priority_score': self.priority_score
        }


def classify_email(email: str) -> str:
    """
    Classify email into categories for filtering
    
    Returns:
    - "official_recruiter" - Personal recruiter email (BEST)
    - "official_generic" - Recruiting-related generic email (GOOD)
    - "invalid_personal" - Personal domain (REJECT)
    - "invalid_non_recruiting" - Non-recruiting generic (REJECT)
    - "invalid_test" - Test/dummy email (REJECT)
    """
    if "@" not in email:
        return "invalid_test"
    
    local_part, domain = email.lower().split("@", 1)
    
    # Step 1: Reject personal domains
    PERSONAL_DOMAINS = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "yahoo.co.in", "rediffmail.com", "protonmail.com",
        "live.com", "icloud.com", "aol.com", "mail.com"
    ]
    if domain in PERSONAL_DOMAINS:
        return "invalid_personal"
    
    # Step 2: Reject single or double-letter prefixes (e@, ab@, etc.)
    if len(local_part) <= 2:
        return "invalid_too_short"
    
    # Step 3: Reject test/dummy patterns
    TEST_PATTERNS = [
        "test", "dummy", "example", "sample", "user", "email",
        "john.doe", "jane.doe", "johndoe", "janedoe"
    ]
    if any(pattern in local_part for pattern in TEST_PATTERNS):
        return "invalid_test"
    
    # Step 4: Agent decides relevance (no auto-filtering of info@, sales@, etc.)
    # Classification helps inform agent decisions

    # Step 5: Accept recruiting-related generic prefixes
    RECRUITING_PREFIXES = [
        "careers", "hr", "jobs", "recruiting", "recruitment",
        "talent", "hiring", "talentacquisition"
    ]
    if local_part in RECRUITING_PREFIXES or any(local_part.startswith(p) for p in RECRUITING_PREFIXES):
        return "official_generic"
    
    # Step 5: Check if name looks real (for personal recruiter emails)
    # Heuristic: has dot/underscore = real name, single word >3 chars = likely real
    has_separator = "." in local_part or "_" in local_part
    is_short_generic = len(local_part) <= 3
    
    if has_separator or (not is_short_generic):
        return "official_recruiter"
    
    # Fallback: uncertain
    return "official_recruiter"


def extract_emails(text: str, source_url: str) -> List[ExtractedEmail]:
    """
    Extract emails from text with surrounding context and classification
    """
    if not text:
        return []

    # Normalize obfuscations
    normalized = text
    replacements = [
        ('[at]', '@'), ('(at)', '@'), (' at ', '@'),
        ('[dot]', '.'), ('(dot)', '.'), (' dot ', '.'),
        ('[AT]', '@'), ('(AT)', '@'),
        ('[DOT]', '.'), ('(DOT)', '.')
    ]

    for old, new in replacements:
        normalized = normalized.replace(old, new)

    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.finditer(email_pattern, normalized)

    extracted = []
    seen = set()

    for match in matches:
        email = match.group(0).lower().strip()

        # Skip if already seen
        if email in seen:
            continue
        seen.add(email)

        # Classify email
        classification = classify_email(email)
        

        # Keep ALL emails - let agent decide if they are useful
        # Classification helps agent make informed decisions
        # Only backend enforcement: personal domains, test patterns (when saving)

        # Extract surrounding text (200 chars before and after)
        start = max(0, match.start() - 100)
        end = min(len(normalized), match.end() + 100)
        surrounding = normalized[start:end].strip()

        # Try to extract name and title
        name, title = extract_name_and_title(surrounding, email)

        # Try to extract LinkedIn URL
        linkedin_url = extract_linkedin_profile(surrounding, source_url)
        
        # Location and priority_score will be set to None here
        # The AGENT will determine these based on scraped LinkedIn/context data
        location = None
        priority_score = None

        extracted.append(ExtractedEmail(email, surrounding, name, title, classification, linkedin_url, location, priority_score))

    return extracted

def extract_name_and_title(text: str, email: str) -> tuple[Optional[str], Optional[str]]:
    """Extract name and title from surrounding text using enhanced role extraction"""
    name = None
    title = None

    # Use enhanced job role extraction
    extracted_title, confidence = extract_job_role(text, email)
    
    # Only accept titles with confidence > 0.5 (likely recruiters)
    if confidence > 0.5:
        title = extracted_title
    
    # Try to extract name from email
    if '@' in email:
        local_part = email.split('@')[0]
        # If has dot, likely firstname.lastname
        if '.' in local_part:
            parts = local_part.split('.')
            name = ' '.join(part.capitalize() for part in parts)
        elif '_' in local_part:
            parts = local_part.split('_')
            name = ' '.join(part.capitalize() for part in parts)
    
    return name, title

def validate_recruiter_role(title: str) -> float:
    """
    Validate if a title is recruiting-related and return confidence score
    
    Args:
        title: Job title to validate
        
    Returns:
        Confidence score 0.0-1.0
        - 1.0: Definitely recruiter
        - 0.8: Likely recruiter
        - 0.5: Possibly recruiter
        - 0.3: Unlikely recruiter
        - 0.0: Definitely NOT recruiter
    """
    if not title:
        return 0.0
    
    title_lower = title.lower()
    
    # DEFINITE RECRUITERS (1.0)
    recruiter_keywords = [
        'recruit', 'talent acquisition', 'ta specialist', 'ta lead', 'ta manager',
        'hr manager', 'hr director', 'hr lead', 'human resources manager',
        'people operations', 'people team', 'people manager',
        'hiring manager', 'hiring lead', 'talent partner', 'talent scout',
        'staffing', 'employment specialist', 'workforce planning'
    ]
    
    for keyword in recruiter_keywords:
        if keyword in title_lower:
            return 1.0
    
    # NON-RECRUITERS - Check this BEFORE generic keywords (0.0)
    # Use word boundaries to avoid false matches (e.g., "coo" in "coordinator")
    import re
    non_recruiter_patterns = [
        # Executives
        r'\bceo\b', r'\bcto\b', r'\bcfo\b', r'\bcoo\b', r'\bfounder\b', r'\bco-founder\b', r'\bpresident\b', r'\bvp\b',
        # Engineering
        r'\bengineer', r'\bdeveloper', r'\barchitect', r'\btech lead', r'\bsoftware', r'\bdevops',
        # Sales/Marketing
        r'\bsales', r'\baccount manager', r'\bbusiness development', r'\bbd\b', r'\bmarketing',
        r'\bcontent', r'\bsocial media', r'\bseo\b', r'\bgrowth',
        # Product
        r'\bproduct manager', r'\bproduct owner', r'\bpm\b', r'\bproduct lead',
        # Operations (non-people)
        r'\boperations', r'\bops\b', r'\bsupply chain',
        # Finance
        r'\baccountant', r'\bfinance', r'\bcontroller',
        # Legal
        r'\blegal', r'\bcounsel', r'\battorney',
        # Other
        r'\badmin', r'\bassistant', r'\banalyst', r'\bconsultant'
    ]
    
    for pattern in non_recruiter_patterns:
        if re.search(pattern, title_lower):
            # Exception: "People Operations" is recruiting
            if 'people' in title_lower and re.search(r'\boperations', title_lower):
                return 1.0
            return 0.0
    
    # Check "coordinator" last - could be talent/recruiting coordinator
    if 'coordinator' in title_lower:
        # If it's talent/recruiting/hr coordinator, it's recruiting
        if any(term in title_lower for term in ['talent', 'recruit', 'hr', 'hiring']):
            return 1.0
        else:
            return 0.0
    
    # LIKELY RECRUITERS (0.8)
    likely_keywords = [
        'hr', 'human resources', 'people', 'talent', 'hiring'
    ]
    
    for keyword in likely_keywords:
        if keyword in title_lower:
            return 0.8
    
    # POSSIBLY RECRUITERS (0.5) - Generic management titles
    generic_keywords = ['manager', 'director', 'lead', 'head', 'specialist']
    
    for keyword in generic_keywords:
        if keyword in title_lower:
            # Could be any type of manager
            return 0.5
    
    # Unknown title - neutral
    return 0.5


def extract_job_role(text: str, email: str = None) -> tuple[str, float]:
    """
    Extract job role/title from text with confidence score
    
    Args:
        text: Surrounding text to extract from
        email: Email address (optional, used for name inference)
        
    Returns:
        (title, confidence) where confidence is 0.0-1.0
    """
    import re
    
    title = None
    confidence = 0.0
    
    # Pattern 1: "Title: Something" or "Role: Something"
    match = re.search(r'(?:title|role|position):\s*([^\n,\.]+)', text, re.I)
    if match:
        title = match.group(1).strip()
        confidence = validate_recruiter_role(title)
        return (title, confidence)
    
    # Pattern 2: "Name - Title" (e.g., "John Doe - Recruiter")
    match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–—]\s*([^\n,\.]+)', text)
    if match:
        potential_title = match.group(2).strip()
        confidence = validate_recruiter_role(potential_title)
        if confidence > 0.5:  # Only accept if likely a title
            title = potential_title
            return (title, confidence)
    
    # Pattern 3: "works as/is a(n) Title"
    match = re.search(r'(?:works as|is|serves as)\s+(?:a|an|the)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text, re.I)
    if match:
        potential_title = match.group(1).strip()
        confidence = validate_recruiter_role(potential_title)
        if confidence > 0.5:
            title = potential_title
            return (title, confidence)
    
    # Pattern 4: Look for recruiting keywords in text
    recruiting_titles = [
        'Recruiter', 'Talent Acquisition Manager', 'HR Manager', 
        'Hiring Manager', 'Talent Partner', 'People Operations Manager',
        'HR Business Partner', 'Recruitment Lead'
    ]
    
    for recruiting_title in recruiting_titles:
        if recruiting_title.lower() in text.lower():
            title = recruiting_title
            confidence = validate_recruiter_role(title)
            return (title, confidence)
    
    # Pattern 5: Extract from email if it has role indicator
    if email and '@' in email:
        local = email.split('@')[0].lower()
        if 'hr' in local or 'recruit' in local or 'talent' in local:
            title = "Recruiting Team"
            confidence = 0.7
            return (title, confidence)
    
    return (None, 0.0)


def extract_linkedin_profile(text: str, source_url: str = None) -> str | None:
    """
    Extract LinkedIn profile URL from text or source URL
    
    Patterns:
    - linkedin.com/in/firstname-lastname
    - linkedin.com/in/firstname-lastname-12345678
    - in.linkedin.com/in/firstname-lastname
    """
    import re
    
    # Try source URL first
    if source_url and 'linkedin.com/in/' in source_url:
        # Clean up and normalize
        match = re.search(r'https?://(?:www\.)?(?:in\.)?linkedin\.com/in/([a-z0-9-]+)', source_url, re.I)
        if match:
            return f"https://www.linkedin.com/in/{match.group(1)}"
    
    # Try text content
    pattern = r'https?://(?:www\.)?(?:in\.)?linkedin\.com/in/([a-z0-9-]+)'
    matches = re.findall(pattern, text, re.I)
    
    if matches:
        # Return first match, normalized
        return f"https://www.linkedin.com/in/{matches[0]}"
    
    return None

    title_keywords = [
        'recruiter', 'talent acquisition', 'hr', 'human resources',
        'hiring', 'manager', 'lead', 'engineer', 'director', 'specialist'
    ]

    # Split into lines
    lines = re.split(r'\n|<br>|;', text)

    for line in lines:
        if email.lower() in line.lower():
            # Found line with email
            parts = re.split(r'[,\-–—|]', line)

            for part in parts:
                trimmed = part.strip()

                # Check for title keywords
                if not title:
                    for keyword in title_keywords:
                        if keyword in trimmed.lower():
                            title = trimmed[:100]  # Limit length
                            break

                # Check if looks like a name (2-3 capitalized words)
                if not name and re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', trimmed):
                    name = ' '.join(trimmed.split()[:3])

            break

    return name, title

def extract_from_snippet(snippet: str, url: str) -> List[ExtractedEmail]:
    """Extract emails from search result snippet"""
    return extract_emails(snippet, url)

def rank_contacts_by_relevance(extracted_emails: List[ExtractedEmail]) -> List[dict]:
    """
    Rank extracted emails by likelihood of being recruiter contacts.
    Simple heuristic-based approach - no LLM needed!

    Returns list of dicts with: email, name, title, confidence
    """
    ranked = []

    for extracted in extracted_emails:
        email = extracted.email.lower()
        context = extracted.surrounding_text.lower()
        score = 0.0

        # HIGH PRIORITY: Email prefix suggests recruiting role
        high_priority_prefixes = ['careers', 'jobs', 'recruit', 'talent', 'hr', 'hiring']
        if any(prefix in email for prefix in high_priority_prefixes):
            score += 0.9

        # MEDIUM PRIORITY: Context suggests recruiting role
        recruiting_keywords = [
            'recruiter', 'talent acquisition', 'hiring', 'hr',
            'human resources', 'people', 'talent', 'recruitment'
        ]
        if any(keyword in context for keyword in recruiting_keywords):
            score += 0.7

        # BONUS: Has title or name extracted
        if extracted.title:
            score += 0.1
        if extracted.name:
            score += 0.1

        # PENALTY: Generic contact emails (likely not personal recruiter)
        generic_prefixes = ['info', 'contact', 'hello', 'support', 'sales', 'press']
        if any(prefix in email for prefix in generic_prefixes):
            score = max(0.2, score - 0.6)  # Lower score but not zero

        # Cap at 1.0
        confidence = min(score, 1.0)

        ranked.append({
            'email': extracted.email,
            'name': extracted.name,
            'title': extracted.title,
            'confidence': confidence,
            'context': extracted.surrounding_text[:200]  # Keep some context
        })

    # Sort by confidence (highest first)
    return sorted(ranked, key=lambda x: x['confidence'], reverse=True)

