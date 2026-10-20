"""
Phase 2 Research Tools for LangGraph Agent
Simplified tool set for intelligent, agentic research
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




@tool
async def fetch_and_read_page(url: str) -> Dict[str, Any]:
    """
    Fetch and read content from a URL. 
    - If LinkedIn profile: Extract location data and update existing contact
    - If other page: Extract and SAVE any emails found

    Use this when search results show a promising page.

    Args:
        url: URL to fetch and read

    Returns:
        Dictionary with content, emails found, location data, and save status
    """
    print(f"[fetch_and_read_page] FETCHING PAGE: {url}")
    
    content = await fetch_page(url)

    if not content:
        return {
            'success': False,
            'error': 'Failed to fetch page',
            'emails': [],
            'content': '',
            'location': None
        }

    # Skip LinkedIn location extraction - LinkedIn shows login wall for unauthenticated requests
    # Location data will come from other sources (unifers.ai, RocketReach, etc.)
    
    extracted = extract_emails(content, url)

    # Debug logging
    print(f"[fetch_and_read_page] Extracted {len(extracted)} emails from {url}")
    
    saved_count = 0
    if extracted:
        print(f"[fetch_and_read_page] Emails found: {[e.email for e in extracted]}")
        
        # AUTO-SAVE to database
        try:
            from app.models.contact import Contact, Evidence
            
            ctx = get_tool_context()
            company = ctx.get('company')
            db = ctx.get('db')
            
            if company and db:
                for e in extracted:
                    # FILTER 1: Domain validation - Only accept emails from target company domain
                    try:
                        email_domain = e.email.split('@')[1].lower()
                        
                        # Get expected domain from company
                        expected_domain = None
                        if company.domain:
                            # Use company.domain directly
                            expected_domain = company.domain.lower()
                        
                        # Fallback: derive from company name
                        if not expected_domain:
                            expected_domain = company.name.lower().replace(' ', '').replace('-', '') + '.com'
                        
                        # Check if email domain matches (exact or subdomain)
                        domain_matches = (
                            email_domain == expected_domain or
                            email_domain.endswith('.' + expected_domain) or
                            expected_domain.endswith('.' + email_domain)
                        )
                        
                        if not domain_matches:
                            print(f"[fetch_and_read_page] Skipped wrong domain: {e.email} (expected @{expected_domain}, got @{email_domain})")
                            continue
                            
                    except (IndexError, AttributeError) as ex:
                        print(f"[fetch_and_read_page] Domain validation error for {e.email}: {ex}")
                        continue
                    
                    # FILTER 2: Skip ex-employees or former employees
                    # Check only the surrounding text of THIS email, not the entire page
                    import re
                    surrounding_lower = (e.surrounding_text or "").lower()
                    
                    # Use word boundaries to avoid false positives like "Alex" or "left corner"
                    ex_employee_patterns = [
                        r'\bex-employee\b', r'\bformer\s+employee\b', r'\bformer\s+\w+\b',
                        r'\bleft\s+(?:the\s+)?company\b', r'\bleft\s+(?:the\s+)?team\b',
                        r'\balumni\b', r'\bprevious\s+role\b', r'\bno\s+longer\s+with\b'
                    ]
                    
                    if any(re.search(pattern, surrounding_lower) for pattern in ex_employee_patterns):
                        print(f"[fetch_and_read_page] Skipped ex-employee: {e.email} (context: {surrounding_lower[:100]}...)")
                        continue
                    
                    # CRITICAL FIX: Check duplicates BEFORE creating object
                    # Refresh session to see any recently flushed contacts
                    db.expire_all()
                    existing = db.query(Contact).filter(
                        Contact.email == e.email,
                        Contact.company_id == company.id
                    ).first()
                    
                    if existing:
                        # Contact already exists - UPDATE with additional data if available
                        updated = False
                        if e.name and not existing.name:
                            existing.name = e.name
                            updated = True
                        if e.title and not existing.title:
                            existing.title = e.title
                            updated = True
                        if e.linkedin_url and not existing.linkedin_url:
                            existing.linkedin_url = e.linkedin_url
                            updated = True
                        if e.location and not existing.location:
                            existing.location = e.location
                            updated = True
                        if e.priority_score and not existing.priority_score:
                            existing.priority_score = e.priority_score
                            updated = True
                        
                        if updated:
                            db.commit()
                            print(f"[fetch_and_read_page] Updated existing: {e.email}")
                        else:
                            print(f"[fetch_and_read_page] Skipped duplicate: {e.email}")
                        continue
                    
                    # Create NEW contact (not a duplicate)
                    contact = Contact(
                        company_id=company.id,
                        email=e.email,
                        name=e.name,
                        title=e.title,
                        linkedin_url=e.linkedin_url,  # LinkedIn URL from extraction
                        location=e.location,  # Geographic location
                        priority_score=e.priority_score,  # Priority score
                        inferred=False,
                        status='discovered'
                    )
                    db.add(contact)
                    db.flush()
                    
                    # Add evidence
                    evidence = Evidence(
                        contact_id=contact.id,
                        source_url=url,
                        source_type='web_crawl',
                        surrounding_text=e.surrounding_text[:500] if e.surrounding_text else ''
                    )
                    db.add(evidence)
                    saved_count += 1
                    print(f"[fetch_and_read_page] Auto-saved: {e.email}")
                
                if saved_count > 0:
                    db.commit()
                    print(f"[fetch_and_read_page] Saved {saved_count} contacts")
        except Exception as ex:
            print(f"[fetch_and_read_page] Auto-save error: {ex}")
            import traceback
            traceback.print_exc()

    return {
        'success': True,
        'url': url,
        'content': content[:2000],
        'emails': [e.email for e in extracted],
        'saved_count': saved_count,
        'location': location_data,
        'message': f"Found and saved {saved_count} contacts" if saved_count > 0 else ("Location extracted: " + location_data if location_data else "No new contacts saved")
    }



@tool
def save_discovered_contacts(contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Save discovered contacts to database.

    CRITICAL: Only save REAL emails you found on actual pages.
    DO NOT save generated, guessed, or inferred emails.

    Args:
        contacts: List with email, name, title, source, url

    Returns:
        Summary of how many contacts were saved
    """
    from app.models.contact import Contact, Evidence
    from app.research.prioritizer import calculate_contact_priority

    ctx = get_tool_context()
    company = ctx['company']
    db = ctx['db']

    if not company or not db:
        return {'error': 'Tool context not set', 'saved': 0}

    saved_count = 0
    skipped_count = 0

    for contact_data in contacts:
        email = contact_data.get('email')
        url = contact_data.get('url')

        if not email or not url:
            skipped_count += 1
            continue

        existing = db.query(Contact).filter(Contact.email == email).first()
        if existing:
            skipped_count += 1
            continue

        contact = Contact(
            company_id=company.id,
            email=email,
            name=contact_data.get('name'),
            title=contact_data.get('title'),
            linkedin_url=contact_data.get('linkedin_url'),  # LinkedIn URL from agent
            inferred=False,
            status='discovered'
        )
        db.add(contact)
        db.flush()

        evidence = Evidence(
            contact_id=contact.id,
            source_url=url,
            source_type='agent_discovery',
            surrounding_text=contact_data.get('context', '')[:500]
        )
        db.add(evidence)

        saved_count += 1
        print(f"[Tool] Saved contact: {email} from {url}")

    db.commit()

    return {
        'saved': saved_count,
        'skipped': skipped_count,
        'message': f'Saved {saved_count} new contacts, skipped {skipped_count}'
    }




def set_tool_context(company, db):
    """Set tool context for current async task"""
    _tool_context.set({'company': company, 'db': db})

def get_tool_context():
    """Get tool context for current async task"""
    return _tool_context.get()





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
        from app.models.contact import Contact, Evidence
        
        # Scrape based on URL type
        if 'linkedin.com/jobs' in job_url:
            result = await scrape_linkedin_job(job_url)
        elif 'naukri.com' in job_url:
            result = await scrape_naukri_job(job_url)
        else:
            return {'error': 'Unsupported URL - must be LinkedIn or Naukri job', 'saved': False}
        
        # Auto-save if email found
        if result.get('email'):
            ctx = get_tool_context()
            company = ctx.get('company')
            db = ctx.get('db')
            
            if company and db:
                try:
                    # Check if email already exists
                    existing = db.query(Contact).filter(Contact.email == result['email']).first()
                    if not existing:
                        contact = Contact(
                            company_id=company.id,
                            email=result['email'],
                            name=result.get('name'),
                            title=result.get('title'),
                            inferred=False,  # Real email from scraping
                            status='discovered'
                        )
                        db.add(contact)
                        db.flush()
                        
                        evidence = Evidence(
                            contact_id=contact.id,
                            source_url=job_url,
                            source_type=result.get('source', 'job_scrape'),
                            surrounding_text=''
                        )
                        db.add(evidence)
                        db.commit()
                        
                        print(f"[scrape_job] Saved: {result['email']}")
                        result['saved'] = True
                    else:
                        result['saved'] = False
                        result['message'] = 'Email already exists'
                except Exception as e:
                    print(f"[scrape_job] Error saving: {e}")
                    result['saved'] = False
                    result['error'] = str(e)
        
        return result
    except Exception as e:
        print(f"[scrape_job] Error: {e}")
        return {'error': str(e), 'saved': False}


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


# NOTE: LinkedIn location extraction removed - LinkedIn shows login wall for unauthenticated requests
# Location data should come from other sources (unifers.ai, RocketReach, company websites)


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


