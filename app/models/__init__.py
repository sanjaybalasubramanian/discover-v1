"""
Database models - Part 1: Core tables
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db import Base


class Run(Base):
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    status = Column(String(50), default='running')
    phase = Column(String(50), default='discovery')  # 'discovery', 'research', 'outreach'
    jobs_found = Column(Integer, default=0)
    jobs_filtered = Column(Integer, default=0)
    companies_eligible = Column(Integer, default=0)
    companies_researched = Column(Integer, default=0)
    companies_contacted = Column(Integer, default=0)
    contacts_found = Column(Integer, default=0)
    personal_contacts_found = Column(Integer, default=0)
    emails_queued = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    shortfall_reason = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('runs.id', ondelete='CASCADE'))
    company_name = Column(String(255), nullable=False)
    company_domain = Column(String(255))
    role_title = Column(String(500), nullable=False)
    location = Column(String(255), nullable=False)
    location_matched = Column(Boolean, default=False)
    posted_date = Column(Date)
    source_url = Column(Text, nullable=False)
    snippet = Column(Text)
    fit_score = Column(Integer, default=0)
    status = Column(String(50), default='discovered')
    filter_reason = Column(Text)
    fetched_text = Column(Text)
    # JobSpy fields
    job_source = Column(String(50))  # 'linkedin', 'naukri', 'indeed', 'glassdoor', 'ziprecruiter'
    job_type = Column(String(50))  # 'fulltime', 'parttime', 'contract', 'internship', 'temporary'
    is_remote = Column(Boolean, default=False)
    salary_info = Column(String(255))
    company_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('runs.id', ondelete='SET NULL'))  # Track which run discovered this company
    name = Column(String(255), nullable=False, unique=True)
    domain = Column(String(255))
    industry = Column(String(255))
    notes = Column(Text)
    research_status = Column(String(50), default='pending')  # 'pending', 'completed', 'failed'
    research_attempts = Column(Integer, default=0)
    researched_at = Column(DateTime)
    last_contacted_at = Column(DateTime)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
