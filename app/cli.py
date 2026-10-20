"""
CLI entrypoint for 3-phase pipeline execution
"""
import asyncio
import os
import sys
import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Run, Company


async def run_phase1_discovery(run_id: int, db: Session):
    """Phase 1: Job Discovery"""
    from app.pipeline.runner import run_pipeline
    
    print("\n" + "=" * 60)
    print("PHASE 1: JOB DISCOVERY")
    print("=" * 60)
    
    start = time.time()
    result = await run_pipeline(run_id, db)
    elapsed = time.time() - start
    
    print(f"✓ Completed in {elapsed:.1f}s")
    print(f"  Jobs found: {result['jobs_found']}")
    print(f"  Companies discovered: {db.query(Company).filter(Company.research_status=='pending').count()}")
    
    return result


async def run_phase2_research(run_id: int, db: Session, limit: int = None):
    """Phase 2: Research Contacts with Parallel Processing"""
    from app.research.agent import research_company_contacts
    
    # Get configuration from environment
    if limit is None:
        limit = int(os.getenv('RESEARCH_COMPANY_LIMIT', '50'))
    workers = int(os.getenv('RESEARCH_PARALLEL_WORKERS', '3'))
    
    print("\n" + "=" * 60)
    print(f"PHASE 2: CONTACT RESEARCH (PARALLEL - {workers} workers)")
    print("=" * 60)
    
    run = db.query(Run).filter(Run.id == run_id).first()
    run.phase = 'research'
    db.commit()
    
    companies = db.query(Company).filter(
        Company.research_status == 'pending'
    ).limit(limit).all()
    
    print(f"Researching {len(companies)} companies with {workers} concurrent workers...")
    print("(Rate limited to prevent system overload)")
    
    start = time.time()
    
    # Semaphore to limit concurrent research tasks
    # GitHub Actions: 2 cores, 7GB RAM
    # Configurable via RESEARCH_PARALLEL_WORKERS (2-5 recommended)
    semaphore = asyncio.Semaphore(workers)
    
    async def research_with_limit(company, index):
        """Research company with semaphore rate limiting and isolated DB session"""
        async with semaphore:
            print(f"\n[{index}/{len(companies)}] {company.name}")
            
            # Create isolated DB session for this worker
            from app.db import SessionLocal
            worker_db = SessionLocal()
            
            try:
                result = await research_company_contacts(company.name, worker_db, run_id=run_id)
                
                if result['success']:
                    print(f"  ✓ Found {result['total_contacts']} contacts ({len(result['personal_contacts'])} personal)")
                else:
                    print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                
                return result
            except Exception as e:
                print(f"  ✗ Error: {e}")
                return {
                    'company': company.name,
                    'success': False,
                    'error': str(e),
                    'personal_contacts': [],
                    'fallback_contacts': [],
                    'total_contacts': 0
                }
            finally:
                # Always close worker session
                worker_db.close()
    
    # Create tasks for all companies
    tasks = [research_with_limit(company, i+1) for i, company in enumerate(companies)]
    
    # Execute with asyncio.gather (handles exceptions gracefully)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and count results
    valid_results = [r for r in results if isinstance(r, dict)]
    
    elapsed = time.time() - start
    
    total_contacts = sum(r.get('total_contacts', 0) for r in valid_results)
    personal_contacts = sum(len(r.get('personal_contacts', [])) for r in valid_results)
    successful = sum(1 for r in valid_results if r.get('success', False))
    
    run.companies_researched = len(companies)
    run.contacts_found = total_contacts
    run.personal_contacts_found = personal_contacts
    db.commit()
    
    print(f"\n✓ Completed in {elapsed:.1f}s")
    print(f"  Companies researched: {len(companies)} ({successful} successful)")
    print(f"  Contacts found: {total_contacts} ({personal_contacts} personal)")
    if len(companies) > 0:
        print(f"  Average time per company: {elapsed/len(companies):.1f}s")
    
    return valid_results


async def run_phase3_outreach(run_id: int, db: Session, limit: int = 50):
    """Phase 3: Send Outreach Emails"""
    print("\n" + "=" * 60)
    print("PHASE 3: OUTREACH")
    print("=" * 60)
    
    # Check if email is configured
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        print("[SKIPPED] Email not configured")
        print("Add SMTP credentials to .env to enable automatic email sending")
        print("Contacts are ready in database for manual outreach")
        run = db.query(Run).filter(Run.id == run_id).first()
        run.phase = 'outreach'
        db.commit()
        return {'sent': 0, 'skipped': True}
    
    # Check for resume attachment
    resume_path = os.getenv('RESUME_PATH')
    if resume_path and not os.path.exists(resume_path):
        print(f"[WARNING] Resume not found: {resume_path}")
        resume_path = None
    
    # Get contacts from this run
    contacts = db.query(Contact).join(Company).filter(
        Company.run_id == run_id,
        Contact.email.isnot(None),
        Contact.status == 'discovered'
    ).limit(limit).all()
    
    if len(contacts) == 0:
        print("[INFO] No contacts found to email")
        return {'sent': 0, 'no_contacts': True}
    
    print(f"[INFO] Found {len(contacts)} contacts to email")
    
    # Get user profile from environment
    your_profile = {
        'name': os.getenv('FROM_NAME', 'Job Seeker'),
        'current_role': os.getenv('YOUR_ROLE', 'Software Engineer'),
        'skills': os.getenv('YOUR_SKILLS', 'Python,React,AWS').split(','),
        'experience': os.getenv('YOUR_EXPERIENCE', '5 years in software development'),
        'location': os.getenv('YOUR_LOCATION', 'India')
    }
    
    # Create dispatcher
    from app.outreach.dispatcher import EmailDispatcher
    dispatcher = EmailDispatcher(db)
    
    # Create campaign
    contact_ids = [c.id for c in contacts]
    attachments = [resume_path] if resume_path else None
    
    campaign_id = await dispatcher.create_campaign_from_contacts(
        name=f"Auto Campaign - Run {run_id}",
        contact_ids=contact_ids,
        your_profile=your_profile,
        attachments=attachments
    )
    
    # Send batch
    batch_size = int(os.getenv('EMAIL_BATCH_SIZE', 10))
    require_approval = os.getenv('REQUIRE_APPROVAL', 'true').lower() == 'true'
    
    results = await dispatcher.send_campaign_batch(
        campaign_id, 
        batch_size=batch_size,
        require_approval=require_approval
    )
    
    # Update run
    run = db.query(Run).filter(Run.id == run_id).first()
    run.phase = 'outreach'
    db.commit()
    
    print(f"\n[COMPLETE] Sent {results['sent']} emails, {results['failed']} failed")
    
    return results


async def run_command():
    """Execute full 3-phase pipeline"""
    
    print("=" * 60)
    print("🚀 3-PHASE JOB OUTREACH PIPELINE")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Create run
        run = Run(status='running', phase='discovery')
        db.add(run)
        db.commit()
        db.refresh(run)
        
        print(f"\n📊 Run ID: {run.id}")
        print(f"⏰ Started: {run.started_at}")
        
        # Phase 1: Discovery
        phase1 = await run_phase1_discovery(run.id, db)
        
        # Phase 2: Research (configured via RESEARCH_COMPANY_LIMIT env var)
        phase2 = await run_phase2_research(run.id, db)
        
        # Phase 3: Outreach
        phase3 = await run_phase3_outreach(run.id, db, limit=25)
        
        # Complete
        run.status = 'completed'
        run.completed_at = datetime.now()
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETED")
        print("=" * 60)
        print(f"Phase 1: {phase1['jobs_found']} jobs discovered")
        print(f"Phase 2: {run.companies_researched} companies researched")
        print(f"         {run.contacts_found} contacts found ({run.personal_contacts_found} personal)")
        
        if phase3.get('skipped'):
            print(f"Phase 3: Skipped (configure SMTP in .env to enable)")
        elif phase3.get('no_contacts'):
            print(f"Phase 3: No contacts to email")
        else:
            print(f"Phase 3: {phase3.get('sent', 0)} emails sent, {phase3.get('failed', 0)} failed")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ PIPELINE FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        
        import traceback
        traceback.print_exc()
        
        if 'run' in locals():
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = datetime.now()
            db.commit()
        
        return 1
        
    finally:
        db.close()

def main():
    """Main CLI entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command>")
        print()
        print("Commands:")
        print("  run    - Execute the outreach pipeline")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'run':
        exit_code = asyncio.run(run_command())
        sys.exit(exit_code)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
