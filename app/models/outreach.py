"""
Outreach, Opens, and other tracking models
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from app.db import Base

class Outreach(Base):
    __tablename__ = 'outreach'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'))
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='SET NULL'))
    subject = Column(String(500), nullable=False)
    resume_file = Column(String(255), nullable=False)
    status = Column(String(50), default='queued')
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    bounced_at = Column(DateTime)
    replied_at = Column(DateTime)
    reply_type = Column(String(50))
    reply_notes = Column(Text)
    message_id = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

class Open(Base):
    __tablename__ = 'opens'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'))
    outreach_id = Column(Integer, ForeignKey('outreach.id', ondelete='CASCADE'))
    opened_at = Column(DateTime, server_default=func.now())
    user_agent = Column(Text)
    ip_hash = Column(Text)
    is_machine_open = Column(Boolean, default=False)

class Suppression(Base):
    __tablename__ = 'suppression'
    
    id = Column(Integer, primary_key=True)
    email_hash = Column(Text, nullable=False, unique=True)
    reason = Column(String(100), nullable=False)
    added_at = Column(DateTime, server_default=func.now())

class ProviderUsage(Base):
    __tablename__ = 'provider_usage'
    
    id = Column(Integer, primary_key=True)
    provider = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    calls = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    estimated_cost = Column(DECIMAL(10, 2), default=0.00)

class CacheSearch(Base):
    __tablename__ = 'cache_search'
    
    id = Column(Integer, primary_key=True)
    query_hash = Column(Text, nullable=False, unique=True)
    results = Column(Text, nullable=False)  # JSON string
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class CachePage(Base):
    __tablename__ = 'cache_pages'
    
    id = Column(Integer, primary_key=True)
    url_hash = Column(Text, nullable=False, unique=True)
    content = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False, unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class GmailAuth(Base):
    __tablename__ = 'gmail_auth'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    refresh_token = Column(Text, nullable=False)
    access_token = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
