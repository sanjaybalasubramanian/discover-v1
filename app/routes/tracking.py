"""
Email open tracking endpoint
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
import io

from app.db import get_db, hash_ip
from app.models.outreach import Open
from app.models.contact import Contact

router = APIRouter()

# 1x1 transparent tracking pixel
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF,
    0x00, 0x00, 0x00, 0x21, 0xF9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2C, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B
])

@router.get("/open/{outreach_id}")
async def track_open(outreach_id: int, request: Request):
    """
    Track email open event
    Returns 1x1 transparent GIF
    """
    db = next(get_db())
    
    try:
        # Find outreach by ID
        from app.outreach.models import EmailOutreach
        outreach = db.query(EmailOutreach).filter(
            EmailOutreach.id == outreach_id
        ).first()
        
        if not outreach:
            # Return pixel even if not found (don't leak info)
            return StreamingResponse(io.BytesIO(TRACKING_PIXEL), media_type="image/gif")
        
        # Get user agent and IP
        user_agent = request.headers.get('user-agent', '')
        client_ip = request.client.host if request.client else ''
        
        # Detect machine open (email scanners, etc.)
        is_machine = detect_machine_open(user_agent)
        
        # Update outreach open count
        if outreach.open_count is None:
            outreach.open_count = 0
        outreach.open_count += 1
        
        # Set opened_at if first time
        if not outreach.opened_at:
            outreach.opened_at = datetime.now()
        
        # Commit the count update
        db.commit()
        
        print(f"[Tracking] ✅ Open #{outreach.open_count} for outreach {outreach_id} (machine={is_machine}) | {user_agent[:50]}")
        
    except Exception as e:
        print(f"[Tracking] ❌ Error: {e}")
    finally:
        db.close()
    
    # Always return tracking pixel
    return StreamingResponse(io.BytesIO(TRACKING_PIXEL), media_type="image/gif")

def detect_machine_open(user_agent: str) -> bool:
    """Detect if open is from email scanner/machine"""
    if not user_agent:
        return True
    
    ua_lower = user_agent.lower()
    
    # Known email scanners
    machine_patterns = [
        'bot', 'spider', 'crawler', 'scan', 'check',
        'proofpoint', 'mimecast', 'barracuda', 'ironport',
        'google image proxy', 'google-image-proxy', 'microsoft', 'outlook-android-sync'
    ]
    
    for pattern in machine_patterns:
        if pattern in ua_lower:
            return True
    
    return False
