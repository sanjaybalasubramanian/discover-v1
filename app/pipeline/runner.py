'''Main pipeline runner - using JobSpy for job discovery'''
import os
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.config import calculate_fit_score, matches_location
from app.models import Company, Job, Run
from app.models.contact import Contact
from app.search.jobspy_scraper import JobSpyScraper, build_jobspy_searches


async def run_pipeline(run_id: int, db: Session) -> Dict[str, Any]:
    """Main outreach pipeline with JobSpy"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise Exception(f"Run {run_id} not found")
    try:
        print(f"[Pipeline] Starting run #{run_id} with JobSpy")
        scraper = JobSpyScraper()
        searches = build_jobspy_searches()
        jobs_found = 0
        contacts_found = 0
        processed_urls = set()
        for search_config in searches:
            print(f"[Pipeline] Scraping: {search_config['search_term']} in {search_config['location']}")
            job_results = scraper.scrape_jobs(**search_config)
            for job_data in job_results:
                job_url = job_data['job_url']
                if job_url in processed_urls:
                    continue
                processed_urls.add(job_url)

                # Validate required fields
                if not job_data.get('title'):
                    print("[Pipeline] ⚠️  Skipping - no job title")
                    continue

                if not job_data.get('company'):
                    print("[Pipeline] ⚠️  Skipping - no company name")
                    continue

                print(f"[Pipeline] Processing: {job_data['title'][:60]}...")

                # Get description (may be empty for some jobs)
                description = job_data.get('description', '')
                if not description:
                    print("[Pipeline] ⚠️  No description available, using title only for relevance check")

                # Check relevance with simple keyword matching (no LLM!)
                from app.filters.relevance import is_relevant_job
                is_relevant, confidence = is_relevant_job(
                    title=job_data['title'],
                    description=description
                )

                if not is_relevant:
                    print(f"[Pipeline] Skipping irrelevant job (confidence: {confidence:.2f})")
                    continue

                # Get location (use "Unknown" if None to satisfy NOT NULL constraint)
                location = job_data.get('location') or "Unknown"
                if location == "Unknown":
                    print("[Pipeline] ⚠️  No location provided, using 'Unknown'")

                location_matched, reason = matches_location(job_data.get('location'))
                fit_score = calculate_fit_score(job_data['title'], description)
                company = db.query(Company).filter(Company.name == job_data['company']).first()
                if not company:
                    company = Company(
                        name=job_data['company'],
                        domain=extract_domain_from_url(job_data.get('company_url', '')),
                        industry=job_data.get('company_industry'),
                        research_status='pending'
                    )
                    db.add(company)
                    db.flush()
                job = Job(
                    run_id=run_id,
                    company_name=job_data['company'],
                    role_title=job_data['title'],
                    location=location,  # Use sanitized location (never None)
                    location_matched=location_matched,
                    posted_date=job_data.get('date_posted'),
                    source_url=job_data['job_url'],
                    snippet=description[:500] if description else job_data['title'],  # Use title if no description
                    fit_score=fit_score,
                    status='discovered',
                    fetched_text=description,
                    job_source=job_data['site'],
                    job_type=job_data.get('job_type', '')[:50] if job_data.get('job_type') else None,  # Truncate to 50 chars
                    is_remote=job_data.get('is_remote', False),
                    salary_info=job_data.get('salary'),
                    company_url=job_data.get('company_url'),
                )
                db.add(job)
                db.flush()
                jobs_found += 1
                print(f"[Pipeline] ✓ Saved job: {job_data['title'][:50]} at {job_data['company']}")

                # Extract contacts if company URL available (optional - can be disabled)
                if os.getenv('PHASE1_EXTRACT_CONTACTS', 'true').lower() == 'false':
                    continue  # Skip Phase 1 contact extraction

                company_url = job_data.get('company_url')
                if company_url:
                    try:
                        print(f"[Pipeline] Extracting contacts for {job_data['company']}...")
                        from app.extract.emails import (
                            extract_emails,
                            rank_contacts_by_relevance,
                        )
                        from app.fetch.crawler import fetch_page

                        # Fetch company page
                        page_content = await fetch_page(company_url)
                        if page_content:
                            # Extract emails using regex
                            extracted_emails_obj = extract_emails(page_content, company_url)

                            if extracted_emails_obj:
                                # Rank contacts using simple heuristics (no LLM!)
                                ranked_contacts = rank_contacts_by_relevance(extracted_emails_obj)

                                for contact_data in ranked_contacts:
                                    if contact_data['confidence'] < 0.5:
                                        continue
                                    contact = db.query(Contact).filter(Contact.email == contact_data['email']).first()
                                    if not contact:
                                        contact = Contact(
                                            company_id=company.id,
                                            email=contact_data['email'],
                                            name=contact_data.get('name'),
                                            title=contact_data.get('title'),
                                            source_count=1,
                                            status='discovered'
                                        )
                                        db.add(contact)
                                        db.flush()
                                        contacts_found += 1
                                        print(f"[Pipeline] ✓ Contact: {contact_data['email']} (confidence: {contact_data['confidence']:.2f})")
                            else:
                                print("[Pipeline] No emails found on company page")
                        else:
                            print("[Pipeline] Could not fetch company page")
                    except Exception as e:
                        print(f"[Pipeline] Error extracting contacts: {e}")
                else:
                    print("[Pipeline] No company URL available for contact extraction")

        db.commit()
        run.jobs_found = jobs_found
        run.companies_eligible = db.query(Company).count()
        run.status = 'completed'
        run.completed_at = datetime.now()
        db.commit()
        print(f"[Pipeline] Run #{run_id} completed. Found {jobs_found} jobs, {contacts_found} contacts")
        return {"jobs_found": jobs_found, "contacts_found": contacts_found, "message": "Pipeline completed successfully"}
    except Exception as e:
        print(f"[Pipeline] Error in run #{run_id}: {e}")
        import traceback
        traceback.print_exc()
        run.status = 'failed'
        run.error_message = str(e)
        run.completed_at = datetime.now()
        try:
            db.rollback()  # Rollback failed transaction before committing run status
            db.commit()
        except Exception as commit_error:
            print(f"[Pipeline] Failed to save error status: {commit_error}")
        raise

def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    if not url:
        return ""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace('www.', '')
        return domain
    except Exception:
        return ""

