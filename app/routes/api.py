"""
API routes for triggering pipeline via GitHub Actions
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Form
from sqlalchemy.orm import Session
from datetime import datetime
import os
import httpx

from app.db import get_db
from app.models import Run

router = APIRouter()

def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for triggering runs"""
    expected_key = os.getenv('RUN_API_KEY')
    if not expected_key:
        # If no key set, allow (for development)
        return True
    
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True

@router.post("/run")
async def trigger_run(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """
    Trigger GitHub Actions workflow to run the pipeline
    
    This endpoint:
    1. Creates a Run record in the database
    2. Triggers GitHub Actions workflow via API
    3. Returns immediately (async execution)
    """
    
    try:
        # Get GitHub config from environment
        github_token = os.getenv('GITHUB_TOKEN')
        github_repo = os.getenv('GITHUB_REPO')  # e.g., "username/repo-name"
        
        if not github_token or not github_repo:
            raise HTTPException(
                status_code=500,
                detail="GitHub integration not configured. Set GITHUB_TOKEN and GITHUB_REPO."
            )
        
        # Create new run record (will be picked up by workflow)
        run = Run(
            started_at=datetime.now(),
            status='queued'
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Trigger GitHub Actions workflow
        workflow_url = f"https://api.github.com/repos/{github_repo}/actions/workflows/daily-run.yml/dispatches"
        
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        payload = {
            'ref': 'main',  # or 'master' depending on your default branch
            'inputs': {
                'max_jobs': '50'
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                workflow_url,
                headers=headers,
                json=payload,
                timeout=10.0
            )
        
        if response.status_code == 204:
            # Success - workflow triggered
            return {
                "success": True,
                "message": "Pipeline queued via GitHub Actions",
                "run_id": run.id,
                "status": "queued"
            }
        else:
            # Failed to trigger
            run.status = 'failed'
            run.error_message = f"GitHub API error: {response.text}"
            db.commit()
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger workflow: {response.text}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error triggering pipeline: {str(e)}"
        )

@router.get("/status/{run_id}")
async def get_run_status(
    run_id: int,
    db: Session = Depends(get_db)
):
    """Get status of a specific run"""
    
    run = db.query(Run).filter(Run.id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "run_id": run.id,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "jobs_found": run.jobs_found,
        "emails_sent": run.emails_sent,
        "error_message": run.error_message
    }

@router.post("/run/{run_id}/cancel")
async def cancel_run(
    run_id: int,
    save_work: bool = Form(False),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Cancel a running pipeline
    
    Args:
        run_id: ID of the run to cancel
        save_work: If True, keep data discovered so far; if False, rollback
        password: Dashboard password for authorization
    """
    
    # Check password (if set)
    expected_password = os.getenv('DASHBOARD_PASSWORD')
    if expected_password and password != expected_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    run = db.query(Run).filter(Run.id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status not in ['running', 'queued']:
        raise HTTPException(status_code=400, detail=f"Cannot cancel run with status: {run.status}")
    
    if save_work:
        # Mark as cancelled but keep data
        run.status = 'cancelled'
        run.completed_at = datetime.now()
        run.error_message = "Cancelled by user (work saved)"
        db.commit()
        
        return {
            "success": True,
            "message": "Run cancelled, work saved",
            "run_id": run.id,
            "jobs_found": run.jobs_found
        }
    else:
        # Rollback: Delete associated jobs and contacts
        from app.models import Job
        
        # Delete jobs from this run
        db.query(Job).filter(Job.run_id == run_id).delete()
        
        # Mark run as cancelled
        run.status = 'cancelled'
        run.completed_at = datetime.now()
        run.error_message = "Cancelled by user (work discarded)"
        run.jobs_found = 0
        db.commit()
        
        return {
            "success": True,
            "message": "Run cancelled, work discarded",
            "run_id": run.id
        }


@router.get("/runs")
async def list_runs(
    limit: int = 10,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """List recent runs (Currently public - no API key required)"""
    runs = db.query(Run).order_by(Run.started_at.desc()).limit(limit).all()
    
    return [{
        "id": r.id,
        "started_at": r.started_at,
        "completed_at": r.completed_at,
        "status": r.status,
        "jobs_found": r.jobs_found,
        "emails_sent": r.emails_sent
    } for r in runs]

@router.get("/runs/{run_id}")
async def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """Get run details (Currently public - no API key required)"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "id": run.id,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "status": run.status,
        "jobs_found": run.jobs_found,
        "jobs_filtered": run.jobs_filtered,
        "companies_eligible": run.companies_eligible,
        "companies_contacted": run.companies_contacted,
        "emails_queued": run.emails_queued,
        "emails_sent": run.emails_sent,
        "shortfall_reason": run.shortfall_reason,
        "error_message": run.error_message
    }
