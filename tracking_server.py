"""
Email Tracking API - Track opens/clicks with bot detection
"""
from fastapi import FastAPI, Request
from fastapi.responses import Response
import base64
from app.db import SessionLocal
from app.outreach.tracking import track_email_open, track_email_click

app = FastAPI(title="Email Tracking API")


# 1x1 transparent pixel
TRACKING_PIXEL = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


@app.get("/track/open/{outreach_id}")
async def track_open(outreach_id: int, request: Request):
    """
    Track email open via invisible 1x1 pixel
    
    Bot Detection:
    - open_count = 1 → Email security scanner (bot)
    - open_count >= 2 → Real human opened email
    """
    
    db = SessionLocal()
    try:
        # Get request metadata
        user_agent = request.headers.get('user-agent', '')
        client_host = request.client.host if request.client else None
        
        # Track the open
        result = track_email_open(
            outreach_id=outreach_id,
            db=db,
            user_agent=user_agent,
            ip_address=client_host
        )
        
        # Log for debugging
        if result.get('success'):
            detection = result.get('detection')
            count = result.get('open_count')
            print(f"[Tracking] Email {outreach_id} opened (count: {count}, detection: {detection})")
        
    finally:
        db.close()
    
    # Return 1x1 transparent PNG
    return Response(content=TRACKING_PIXEL, media_type="image/png")


@app.get("/track/click/{outreach_id}")
async def track_click(outreach_id: int, link: str, request: Request):
    """
    Track link click (always human - bots don't click)
    Then redirect to actual link
    """
    
    db = SessionLocal()
    try:
        user_agent = request.headers.get('user-agent', '')
        client_host = request.client.host if request.client else None
        
        # Track the click
        result = track_email_click(
            outreach_id=outreach_id,
            db=db,
            link_url=link,
            user_agent=user_agent,
            ip_address=client_host
        )
        
        if result.get('success'):
            print(f"[Tracking] Link clicked in email {outreach_id}: {link}")
        
    finally:
        db.close()
    
    # Redirect to actual link
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=link)


@app.get("/stats/{campaign_id}")
async def get_campaign_stats(campaign_id: int):
    """
    Get campaign tracking statistics with bot detection breakdown
    """
    
    db = SessionLocal()
    try:
        from app.outreach.tracking import get_tracking_stats
        stats = get_tracking_stats(campaign_id, db)
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
