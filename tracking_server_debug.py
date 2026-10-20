"""
Test tracking server with better error logging
"""
import sys
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import Response
import base64
from app.db import SessionLocal
from app.outreach.tracking import track_email_open, track_email_click

app = FastAPI(title="Email Tracking API - Debug Mode")

# 1x1 transparent pixel
TRACKING_PIXEL = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


@app.get("/track/open/{outreach_id}")
async def track_open(outreach_id: int, request: Request):
    """Track email open with debug logging"""
    
    print(f"\n{'='*60}")
    print(f"[TRACKING REQUEST] Email ID: {outreach_id}")
    print(f"{'='*60}")
    
    db = SessionLocal()
    try:
        # Get request metadata
        user_agent = request.headers.get('user-agent', '')
        client_host = request.client.host if request.client else None
        
        print(f"User-Agent: {user_agent}")
        print(f"IP: {client_host}")
        
        # Track the open
        result = track_email_open(
            outreach_id=outreach_id,
            db=db,
            user_agent=user_agent,
            ip_address=client_host
        )
        
        # Log result
        if result.get('success'):
            detection = result.get('detection')
            count = result.get('open_count')
            is_human = result.get('is_human')
            
            icon = "👤" if is_human else "🤖"
            print(f"\n{icon} TRACKED!")
            print(f"   Open Count: {count}")
            print(f"   Detection: {detection}")
            print(f"   Is Human: {is_human}")
            
            if count == 1:
                print(f"   → This is the FIRST open (likely bot/scanner)")
            elif count == 2:
                print(f"   → This is the SECOND open (HUMAN CONFIRMED!)")
            else:
                print(f"   → Human engagement tracked ({count} opens)")
                
        elif result.get('error'):
            print(f"❌ ERROR: {result['error']}")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        traceback.print_exc()
    finally:
        db.close()
    
    # Return 1x1 transparent PNG
    return Response(content=TRACKING_PIXEL, media_type="image/png")


@app.get("/track/click/{outreach_id}")
async def track_click(outreach_id: int, link: str, request: Request):
    """Track link click"""
    
    print(f"\n[CLICK] Email {outreach_id} - Link: {link}")
    
    db = SessionLocal()
    try:
        user_agent = request.headers.get('user-agent', '')
        client_host = request.client.host if request.client else None
        
        result = track_email_click(
            outreach_id=outreach_id,
            db=db,
            link_url=link,
            user_agent=user_agent,
            ip_address=client_host
        )
        
        if result.get('success'):
            print(f"✅ Click tracked! Count: {result.get('click_count')}")
        
    finally:
        db.close()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=link)


@app.get("/stats/{campaign_id}")
async def get_campaign_stats(campaign_id: int):
    """Get campaign stats"""
    
    db = SessionLocal()
    try:
        from app.outreach.tracking import get_tracking_stats
        stats = get_tracking_stats(campaign_id, db)
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 TRACKING SERVER - DEBUG MODE")
    print("="*60)
    print("\nWatching for email opens...")
    print("Open your email now and watch this terminal!\n")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
