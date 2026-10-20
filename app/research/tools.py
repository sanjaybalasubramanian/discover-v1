"""
Phase 2 Research Tools for LangGraph Agent
Refactored: Tools extract data, Agent decides what to save
"""
import contextvars
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from app.extract.emails import extract_emails
from app.fetch.crawler import fetch_page

# Use ContextVar for thread-safe context storage across async tasks
_tool_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    '_tool_context',
    default={'company': None, 'db': None}
)


def set_tool_context(company, db):
    """Set the company and db context for tools"""
    _tool_context.set({'company': company, 'db': db})


def get_tool_context():
    """Get the current tool context"""
    return _tool_context.get()



@tool
def web_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search the web for any query - you decide what to search for.

    Think like Google AI: craft queries that will find what you need.

    Args:
        query: Your search query (e.g., "GE Vernova recruiting team contact email")
        max_results: Number of results to return (default: 10)

    Returns:
        List of search results with:
        - title: Page title
        - snippet: Search result snippet
        - url: Page URL
        - emails: List of emails found in snippet with metadata
          Each email has: email, name, title, surrounding_text, classification
    """
    from app.search.router import SearchRouter
    from app.db import SessionLocal
    
    # Use SearchRouter for caching and failover
    router = SearchRouter(SessionLocal())
    results = router.search(query, max_results=max_results)
    
    enriched_results = []
    for r in results:
        # Extract emails from snippet text
        snippet_text = f"{r.title} {r.snippet}"
        extracted = extract_emails(snippet_text, r.url)
        
        result_dict = {
            'title': r.title,
            'snippet': r.snippet,
            'url': r.url,
            'emails': [
                {
                    'email': e.email,
                    'name': e.name,
                    'title': e.title,
                    'surrounding_text': e.surrounding_text,
                    'classification': e.classification
                }
                for e in extracted
            ]
        }
        
        enriched_results.append(result_dict)
    
    return enriched_results



# Global cache for fetched URLs (prevents duplicates)
_fetched_url_cache: Dict[str, Dict[str, Any]] = {}

@tool
async def fetch_and_read_page(url: str) -> Dict[str, Any]:
    """
    Fetch and read content from a URL to extract emails.
    
    Use this when search results show a promising page that might contain
    recruiter emails or contact information.

    Args:
        url: URL to fetch and read

    Returns:
        Dictionary with:
        - success: True/False
        - url: The fetched URL
        - content: First 2000 chars of page content
        - emails: List of extracted emails with metadata
          Each email has: email, name, title, surrounding_text, classification
    """
    # Check cache first (prevent duplicate fetches)
    if url in _fetched_url_cache:
        print(f"[fetch_and_read_page] Cache hit: {url}")
        return _fetched_url_cache[url]
    
    print(f"[fetch_and_read_page] Fetching: {url}")
    
    content = await fetch_page(url)

    if not content:
        result = {
            'success': False,
            'error': 'Failed to fetch page',
            'url': url,
            'emails': []
        }
        # Cache failed results too (avoid retry)
        _fetched_url_cache[url] = result
        return result

    # Extract emails from page content
    extracted = extract_emails(content, url)
    
    print(f"[fetch_and_read_page] Found {len(extracted)} emails in {url}")
    if extracted:
        for e in extracted:
            print(f"[fetch_and_read_page]   → {e.email} (classification: {e.classification})")

    result = {
        'success': True,
        'url': url,
        'content': content[:2000],  # First 2000 chars for context
        'emails': [
            {
                'email': e.email,
                'name': e.name,
                'title': e.title,
                'surrounding_text': e.surrounding_text,
                'classification': e.classification
            }
            for e in extracted
        ]
    }
    
    # Cache result
    _fetched_url_cache[url] = result
    return result



@tool
def save_discovered_contacts(contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Save contacts YOU verified are relevant, authentic, and currently employed.
    
    YOU are responsible for checking:
    - Email domain matches the target company (backend will double-check)
    - Person is NOT an ex-employee (read the context carefully)
    - Email looks authentic (not test@, dummy@, etc - backend will check)
    - Contact is relevant (recruiter, HR, talent acquisition)
    
    For each contact provide:
    - email: The email address (REQUIRED)
    - is_generic: bool (REQUIRED) - YOU decide the classification:
        * False = Personal email (chris@, priya.sharma@, john.doe@, arun.k@)
        * True = Generic email (careers@, hr@, info@, contact@, recruiting@)
    - name: Person's name (if known, required for personal emails)
    - title: Job title (if known)  
    - source_url: Where you found it (REQUIRED)
    - surrounding_text: Context around the email (helps with verification)
    - reasoning: 2-3 sentences explaining WHY this is a good contact
    
    CLASSIFICATION EXAMPLES:
    ✅ is_generic=False: chris@company.com, priya.sharma@company.com, john@company.com
    ✅ is_generic=True: careers@company.com, hr@company.com, info@company.com
    
    The tool will:
    - Validate email format & domain (backend safety check)
    - Check for duplicates
    - Save to database with evidence
    
    Args:
        contacts: List of contact dictionaries
    
    Returns:
        Summary with saved count, skipped count, and any errors
    """
    from app.models.contact import Contact, Evidence
    
    ctx = get_tool_context()
    company = ctx.get('company')
    db = ctx.get('db')
    
    if not company or not db:
        return {'error': 'Tool context not set', 'saved': 0, 'skipped': 0}
    
    saved_count = 0
    skipped_count = 0
    errors = []
    
    for contact_data in contacts:
        email = contact_data.get('email')
        source_url = contact_data.get('source_url')
        
        # Validate required fields
        if not email or not source_url:
            errors.append(f"Missing email or source_url: {contact_data}")
            skipped_count += 1
            continue
        
        try:
            email_lower = email.lower()
            local_part, email_domain = email_lower.split('@')
            
            # BACKEND ENFORCEMENT 1: Reject personal domains (safety check)
            PERSONAL_DOMAINS = [
                "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                "yahoo.co.in", "rediffmail.com", "protonmail.com",
                "live.com", "icloud.com", "aol.com", "mail.com"
            ]
            if email_domain in PERSONAL_DOMAINS:
                errors.append(f"Personal domain rejected: {email}")
                print(f"[save_discovered_contacts] REJECTED - Personal domain: {email}")
                skipped_count += 1
                continue
            
            # BACKEND ENFORCEMENT 2: Reject test/dummy patterns (safety check)
            TEST_PATTERNS = [
                "test", "dummy", "example", "sample", "user", "email",
                "john.doe", "jane.doe", "johndoe", "janedoe"
            ]
            if any(pattern in local_part for pattern in TEST_PATTERNS):
                errors.append(f"Test email rejected: {email}")
                print(f"[save_discovered_contacts] REJECTED - Test pattern: {email}")
                skipped_count += 1
                continue
            
            # BACKEND ENFORCEMENT 3: Reject non-recruiting generic emails (backup safety check)
            # Agent should primarily decide, but backend blocks obvious bad ones
            # Keep: info@, contact@, hello@ (used for job applications)
            # Block: sales@, support@, noreply@, marketing@
            NON_RECRUITING_PREFIXES = [
                "sales", "support", "noreply", "no-reply", "donotreply",
                "webmaster", "postmaster", "marketing", "business", 
                "customerservice", "service", "admin"
            ]
            if local_part in NON_RECRUITING_PREFIXES or local_part.startswith("sales."):
                errors.append(f"Non-recruiting email rejected: {email}")
                print(f"[save_discovered_contacts] REJECTED - Non-recruiting: {email}")
                skipped_count += 1
                continue
            
            # BACKEND ENFORCEMENT 4: Domain validation (safety check)
            expected_domain = company.domain.lower() if company.domain else None
            
            # Auto-discover domain from first saved email if not set
            if not expected_domain and saved_count == 0:
                # First email - use its domain as the company domain
                expected_domain = email_domain
                company.domain = email_domain
                db.flush()
                print(f"[save_discovered_contacts] 🔍 Auto-discovered domain: {email_domain}")
            
            if not expected_domain:
                # Fallback: derive from company name
                expected_domain = company.name.lower().replace(' ', '').replace('-', '') + '.com'
            
            # Debug logging
            print(f"[save_discovered_contacts] Domain check: email_domain={email_domain}, expected={expected_domain}")
            
            # Check domain match (flexible matching for subdomains and partial matches)
            domain_matches = (
                email_domain == expected_domain or
                email_domain.endswith('.' + expected_domain) or
                expected_domain.endswith('.' + email_domain) or
                # Flexible: Check if core domain matches (mindpro vs mindprotech)
                expected_domain in email_domain or
                email_domain in expected_domain
            )
            
            print(f"[save_discovered_contacts] Domain matches: {domain_matches}")
            
            if not domain_matches:
                errors.append(f"Domain mismatch: {email} (expected @{expected_domain})")
                print(f"[save_discovered_contacts] REJECTED - Wrong domain: {email}")
                skipped_count += 1
                continue
            
        except (IndexError, AttributeError) as ex:
            errors.append(f"Invalid email format: {email}")
            skipped_count += 1
            continue
        
        # Check for duplicates
        db.expire_all()  # Refresh session
        existing = db.query(Contact).filter(
            Contact.email == email,
            Contact.company_id == company.id
        ).first()
        
        if existing:
            print(f"[save_discovered_contacts] Skipped duplicate: {email}")
            skipped_count += 1
            continue
        
        try:
            # Get agent's classification (REQUIRED)
            is_generic = contact_data.get('is_generic')
            
            # Validate is_generic is provided
            if is_generic is None:
                errors.append(f"Missing is_generic classification for {email}")
                print(f"[save_discovered_contacts] REJECTED - No classification: {email}")
                skipped_count += 1
                continue
            
            # Create new contact
            contact = Contact(
                company_id=company.id,
                email=email,
                name=contact_data.get('name'),
                title=contact_data.get('title'),
                linkedin_url=contact_data.get('linkedin_url'),
                location=contact_data.get('location'),
                priority_score=contact_data.get('priority_score'),
                is_generic=is_generic,  # Use agent's classification
                inferred=False,
                status='discovered'
            )
            db.add(contact)
            db.flush()
            
            # Add evidence with reasoning
            surrounding_text = contact_data.get('surrounding_text', '')
            reasoning = contact_data.get('reasoning', '')
            evidence_text = f"{reasoning}\n\nContext: {surrounding_text}"[:500]
            
            evidence = Evidence(
                contact_id=contact.id,
                source_url=source_url,
                source_type='agent_verified',
                surrounding_text=evidence_text
            )
            db.add(evidence)
            
            saved_count += 1
            print(f"[save_discovered_contacts] Saved: {email}")
            
        except Exception as e:
            # Handle duplicate key violations (race condition) and other DB errors
            if 'duplicate key' in str(e).lower() or 'unique constraint' in str(e).lower():
                print(f"[save_discovered_contacts] Skipped duplicate (race condition): {email}")
                db.rollback()
                skipped_count += 1
            else:
                print(f"[save_discovered_contacts] Error saving {email}: {e}")
                db.rollback()
                errors.append(f"Failed to save {email}: {str(e)[:100]}")
                skipped_count += 1

    
    # Commit all changes
    if saved_count > 0:
        db.commit()
    
    result = {
        'saved': saved_count,
        'skipped': skipped_count,
        'message': f'Saved {saved_count} contacts, skipped {skipped_count}'
    }
    
    if errors:
        result['errors'] = errors[:5]  # First 5 errors
    
    return result





@tool
async def scrape_job_for_recruiter(job_url: str) -> dict:
    """
    Scrape LinkedIn or Naukri job post for recruiter contact info.
    
    ONLY works when running locally with authenticated browser session.
    Uses your Chrome profile to access LinkedIn (must be logged in).
    
    Args:
        job_url: LinkedIn or Naukri job URL
    
    Returns:
        Dictionary with recruiter name, email (if found), title, source
    """
    try:
        from app.fetch.linkedin_scraper import scrape_linkedin_job, scrape_naukri_job
        
        # Scrape based on URL type
        if 'linkedin.com/jobs' in job_url:
            result = await scrape_linkedin_job(job_url)
        elif 'naukri.com' in job_url:
            result = await scrape_naukri_job(job_url)
        else:
            return {'error': 'Unsupported URL - must be LinkedIn or Naukri job'}
        
        return result
    except Exception as e:
        print(f"[scrape_job] Error: {e}")
        return {'error': str(e)}



@tool
def infer_emails_from_names(names: list[str], domain: str) -> dict:
    """
    Generate inferred emails for recruiter names using common patterns.
    
    Tries patterns like:
    - first.last@domain (most common)
    - firstlast@domain
    - flast@domain
    
    Args:
        names: List of recruiter names found (e.g., ["Priya Sharma", "Rahul Verma"])
        domain: Company email domain (e.g., "infosys.com")
    
    Returns:
        Dictionary with summary of how many emails were generated and saved
    """
    try:
        from app.utils.patterns import save_inferred_contacts
        
        ctx = get_tool_context()
        company = ctx.get('company')
        db = ctx.get('db')
        
        if not company or not db:
            return {'error': 'Tool context not set', 'inferred': 0, 'total_names': len(names), 'domain': domain}
        
        saved = save_inferred_contacts(names, domain, company.id, db)
        
        return {
            'inferred': saved,
            'total_names': len(names),
            'domain': domain,
            'message': f"Generated and saved {saved} inferred email contacts using pattern: first.last@{domain}"
        }
    except Exception as e:
        print(f"[infer_emails] Error: {e}")
        return {'error': str(e), 'inferred': 0, 'total_names': len(names) if names else 0, 'domain': domain}


@tool
def extract_names_from_search_results(results: list[dict]) -> dict:
    """
    Extract recruiter names from search result titles and snippets.
    
    Looks for patterns like:
    - "Priya Sharma - Technical Recruiter"
    - "Posted by Rahul Verma, Talent Acquisition"
    
    Args:
        results: List of search results (from web_search tool)
    
    Returns:
        Dictionary with list of names found
    """
    try:
        from app.utils.patterns import extract_names_from_text
        
        all_names = []
        
        for result in results:
            try:
                # Combine title and snippet
                text = f"{result.get('title', '')} {result.get('snippet', '')}"
                
                # Extract names
                names = extract_names_from_text(text)
                all_names.extend(names)
            except Exception as e:
                print(f"[extract_names] Error processing result: {e}")
                continue
        
        # Deduplicate
        unique_names = list(set(all_names))
        
        return {
            'names': unique_names,
            'count': len(unique_names),
            'message': f"Extracted {len(unique_names)} recruiter names from {len(results)} search results"
        }
    except Exception as e:
        print(f"[extract_names] Error: {e}")
        return {'error': str(e), 'names': [], 'count': 0, 'message': 'Error extracting names'}


# Export all tools
RESEARCH_TOOLS = [
    web_search,
    fetch_and_read_page,
    scrape_job_for_recruiter,
    infer_emails_from_names,
    extract_names_from_search_results,
    save_discovered_contacts,
]
