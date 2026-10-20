"""
Main FastAPI application
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db import get_db, Base, engine
from app.routes import api, dashboard, tracking

load_dotenv()

app = FastAPI(
    title="Job Outreach Automation",
    description="Automated job discovery and outreach system",
    version="1.0.0"
)

# Mount routes
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(tracking.router, prefix="/track", tags=["tracking"])

# Create tables on startup (with error handling)
@app.on_event("startup")
async def startup():
    """Initialize database tables on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not connect to database on startup: {e}")
        print("  The application will start, but database operations will fail.")

# Health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "Job Outreach Automation API"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check with database connection test"""
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
