"""
Dashboard routes
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Run, Job
from app.models.contact import Contact
from app.models.schedule import Schedule

from app.models.outreach import Outreach, Open

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def check_password(password: str):
    """
    Check dashboard password (DISABLED - Currently public)
    To enable: Set DASHBOARD_PASSWORD in .env and uncomment checks below
    """
    # expected = os.getenv('DASHBOARD_PAkiSSWORD')
    # if not expected:
    #     raise HTTPException(status_code=500, detail="DASHBOARD_PASSWORD not configured")
    # return password == expected
    return True  # Always allow for now

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """Dashboard home page"""
    
    # Get latest runs
    runs = db.query(Run).order_by(Run.started_at.desc()).limit(10).all()
    latest_run = runs[0] if runs else None
    
    # Get comprehensive stats
    from app.models import Company
    from datetime import datetime, timedelta
    
    total_jobs = db.query(Job).count()
    total_contacts = db.query(Contact).count()
    total_companies = db.query(Company).count()
    companies_completed = db.query(Company).filter(Company.research_status == 'completed').count()
    
    # Count personal vs generic contacts (simple heuristic)
    # Personal emails usually have firstname.lastname pattern
    personal_contacts = 0
    generic_contacts = 0
    
    all_contacts = db.query(Contact).all()
    for contact in all_contacts:
        if contact.email and '@' in contact.email:
            email_local = contact.email.split('@')[0]
            # Check if has dot in local part (firstname.lastname pattern)
            if '.' in email_local and not email_local.startswith(('info', 'contact', 'careers', 'hr', 'jobs', 'sales')):
                personal_contacts += 1
            else:
                generic_contacts += 1
    
    # Calculate success rate
    if companies_completed > 0:
        success_rate = round((companies_completed / total_companies * 100) if total_companies > 0 else 0)
        avg_contacts = round(total_contacts / companies_completed, 1)
    else:
        success_rate = 0
        avg_contacts = 0
    
    # Count new companies today
    today = datetime.now().date()
    new_companies_today = db.query(Company).filter(
        Company.created_at >= today
    ).count()
    
    total_sent = db.query(Outreach).filter(Outreach.sent_at.isnot(None)).count()
    total_opened = db.query(Open).filter(Open.opened_at.isnot(None)).count()
    open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0, 1)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "runs": runs,
            "latest_run": latest_run,
            "stats": {
                "total_jobs": total_jobs,
                "total_contacts": total_contacts,
                "total_companies": companies_completed,
                "companies_completed": companies_completed,
                "personal_contacts": personal_contacts,
                "generic_contacts": generic_contacts,
                "success_rate": success_rate,
                "avg_contacts_per_company": avg_contacts,
                "new_companies_today": new_companies_today,
                "total_sent": total_sent,
                "open_rate": open_rate
            }
        }
    )

@router.post("/run")
async def trigger_run_from_dashboard(
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Trigger run from dashboard"""
    from fastapi.responses import RedirectResponse
    
    if not check_password(password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    from app.routes.api import trigger_run
    await trigger_run(db)
    
    # Redirect back to dashboard
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/schedules", response_class=HTMLResponse)
async def view_schedules(request: Request, db: Session = Depends(get_db)):
    """View and manage schedules"""
    
    schedules = db.query(Schedule).order_by(Schedule.created_at.desc()).all()
    
    return templates.TemplateResponse(
        request=request,
        name="schedules.html",
        context={
            "schedules": schedules
        }
    )

@router.post("/schedules/create")
async def create_schedule(
    name: str = Form(...),
    hour: int = Form(...),
    minute: int = Form(...),
    enabled: bool = Form(True),
    max_jobs: int = Form(50),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new schedule"""
    
    if not check_password(password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Convert IST to UTC for cron
    # IST is UTC+5:30
    utc_hour = (hour - 5) if minute >= 30 else (hour - 6)
    utc_minute = (minute - 30) if minute >= 30 else (minute + 30)
    
    if utc_hour < 0:
        utc_hour += 24
    
    cron = f"{utc_minute} {utc_hour} * * *"
    
    schedule = Schedule(
        name=name,
        cron_expression=cron,
        timezone='Asia/Kolkata',
        enabled=enabled,
        max_jobs=max_jobs
    )
    
    db.add(schedule)
    db.commit()
    
    return RedirectResponse(url="/dashboard/schedules", status_code=303)

@router.post("/schedules/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Enable/disable a schedule"""
    
    if not check_password(password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.enabled = not schedule.enabled
    db.commit()
    
    return RedirectResponse(url="/dashboard/schedules", status_code=303)

@router.post("/schedules/{schedule_id}/delete")
async def delete_schedule(
    schedule_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a schedule"""
    
    if not check_password(password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    
    return RedirectResponse(url="/dashboard/schedules", status_code=303)

# ============================================================================
# COMPANIES & CONTACTS PAGES
# ============================================================================

@router.get("/companies", response_class=HTMLResponse)
async def companies_page(request: Request, db: Session = Depends(get_db)):
    """Companies list page"""
    from app.models import Company
    from sqlalchemy import func
    
    # Get filter params
    status_filter = request.query_params.get('status', 'all')
    
    # Build query with contact counts
    query = db.query(
        Company,
        func.count(Contact.id).label('contact_count')
    ).outerjoin(Contact, Company.id == Contact.company_id)\
     .group_by(Company.id)\
     .order_by(Company.created_at.desc())
    
    if status_filter != 'all':
        query = query.filter(Company.research_status == status_filter)
    
    results = query.all()
    
    # Format results with contact counts
    companies_with_counts = []
    for company, contact_count in results:
        company.contact_count = contact_count
        companies_with_counts.append(company)
    
    # Stats
    total = db.query(Company).count()
    pending = db.query(Company).filter(Company.research_status == 'pending').count()
    completed = db.query(Company).filter(Company.research_status == 'completed').count()
    failed = db.query(Company).filter(Company.research_status == 'failed').count()
    
    return templates.TemplateResponse(
        request=request,
        name="companies.html",
        context={
            "companies": companies_with_counts,
            "status_filter": status_filter,
            "stats": {
                "total": total,
                "pending": pending,
                "completed": completed,
                "failed": failed
            }
        }
    )

@router.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request, db: Session = Depends(get_db)):
    """Contacts list page"""
    from app.models import Company
    
    # Get filter params
    company_filter = request.query_params.get('company', None)
    type_filter = request.query_params.get('type', 'all')  # all, personal, generic
    
    # Build query
    query = db.query(Contact).order_by(Contact.created_at.desc())
    
    if company_filter:
        query = query.filter(Contact.company_id == int(company_filter))
    
    all_contacts = query.all()
    
    # Filter by type (personal vs generic)
    if type_filter == 'personal':
        contacts = [c for c in all_contacts if c.email and '@' in c.email and '.' in c.email.split('@')[0] 
                   and not c.email.split('@')[0].startswith(('info', 'contact', 'careers', 'hr', 'jobs', 'sales'))]
    elif type_filter == 'generic':
        contacts = [c for c in all_contacts if c.email and '@' in c.email and 
                   (('.' not in c.email.split('@')[0]) or c.email.split('@')[0].startswith(('info', 'contact', 'careers', 'hr', 'jobs', 'sales')))]
    else:
        contacts = all_contacts
    
    # Get companies for filter dropdown
    companies = db.query(Company).order_by(Company.name).all()
    
    # Stats
    total = len(all_contacts)
    personal = sum(1 for c in all_contacts if c.email and '@' in c.email and '.' in c.email.split('@')[0] 
                  and not c.email.split('@')[0].startswith(('info', 'contact', 'careers', 'hr', 'jobs', 'sales')))
    generic = total - personal
    
    return templates.TemplateResponse(
        request=request,
        name="contacts.html",
        context={
            "contacts": contacts,
            "companies": companies,
            "company_filter": company_filter,
            "type_filter": type_filter,
            "stats": {
                "total": total,
                "personal": personal,
                "generic": generic
            }
        }
    )

@router.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_details(run_id: int, request: Request, db: Session = Depends(get_db)):
    """Run details page showing phase-by-phase breakdown"""
    
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get jobs from this run
    jobs = db.query(Job).filter(Job.run_id == run_id).all()
    
    # Get companies researched in this run (approximate based on created_at)
    from app.models import Company
    companies = []
    if run.started_at and run.completed_at:
        companies = db.query(Company).filter(
            Company.created_at >= run.started_at,
            Company.created_at <= run.completed_at
        ).all()
    
    # Get contacts found in this run
    contacts = []
    if run.started_at and run.completed_at:
        contacts = db.query(Contact).filter(
            Contact.created_at >= run.started_at,
            Contact.created_at <= run.completed_at
        ).all()
    
    # Get emails sent in this run
    emails = []
    if run.started_at and run.completed_at:
        emails = db.query(Outreach).filter(
            Outreach.sent_at >= run.started_at,
            Outreach.sent_at <= run.completed_at
        ).all()
    
    return templates.TemplateResponse(
        request=request,
        name="run_details.html",
        context={
            "run": run,
            "jobs": jobs,
            "companies": companies,
            "contacts": contacts,
            "emails": emails
        }
    )
