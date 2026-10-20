"""
Schedule model for managing pipeline schedules
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.db import Base

class Schedule(Base):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, default='Daily Run')
    cron_expression = Column(String(100), nullable=False)  # e.g., "0 3 * * *" (03:00 UTC = 08:30 IST)
    timezone = Column(String(50), default='Asia/Kolkata')
    enabled = Column(Boolean, default=True)
    max_jobs = Column(Integer, default=50)
    config = Column(JSON)  # Additional config options
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

