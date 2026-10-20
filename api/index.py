"""
Vercel Serverless Function for Email Tracking
Lightweight version that only handles tracking pixel endpoint
"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
import io
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# Initialize FastAPI
app = FastAPI()

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

Base = declarative_base()

# Minimal EmailOutreach model (only what we need for tracking)
class EmailOutreach(Base):
    __tablename__ = 'email_outreach'
    
    id = Column(Integer, primary_key=True)
    recipient_email = Column(String(255))
    open_count = Column(Integer, default=0)
    opened_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

# Create engine and session with psycopg2
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}  # Force psycopg2
) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

# 1x1 transparent tracking pixel (GIF)
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF,
    0x00, 0x00, 0x00, 0x21, 0xF9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2C, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B
])

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "message": "Email Tracking Service",
        "endpoints": ["/track/open/{outreach_id}"]
    }

@app.get("/track/open/{outreach_id}")
async def track_open(outreach_id: int, request: Request):
    """
    Track email open event
    Returns 1x1 transparent GIF pixel
    """
    try:
        # Get database session
        if not SessionLocal:
            print("[Tracking] ⚠️  No database connection")
            return StreamingResponse(io.BytesIO(TRACKING_PIXEL), media_type="image/gif")
        
        db = SessionLocal()
        
        try:
            # Find outreach by ID
            outreach = db.query(EmailOutreach).filter(
                EmailOutreach.id == outreach_id
            ).first()
            
            if not outreach:
                print(f"[Tracking] ⚠️  Outreach {outreach_id} not found")
                return StreamingResponse(io.BytesIO(TRACKING_PIXEL), media_type="image/gif")
            
            # Get user agent and IP
            user_agent = request.headers.get('user-agent', '')
            client_ip = request.client.host if request.client else 'unknown'
            
            # Update open count
            if outreach.open_count is None:
                outreach.open_count = 0
            outreach.open_count += 1
            
            # Set opened_at if first time
            if not outreach.opened_at:
                outreach.opened_at = datetime.now()
            
            # Commit changes
            db.commit()
            
            print(f"[Tracking] ✅ Open #{outreach.open_count} for outreach {outreach_id} from {client_ip}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"[Tracking] ❌ Error: {e}")
    
    # Always return tracking pixel
    return StreamingResponse(
        io.BytesIO(TRACKING_PIXEL), 
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Vercel handler - expose the FastAPI app directly
# Vercel will automatically handle requests through ASGI
from mangum import Mangum

handler = Mangum(app)
