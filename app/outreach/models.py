"""
Database models for email outreach
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from app.db import Base

class EmailCampaign(Base):
    """Email outreach campaign"""
    __tablename__ = 'email_campaigns'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Campaign settings
    template_type = Column(String(50), default='cold_outreach')
    subject_line = Column(String(255))
    
    # Status
    status = Column(String(50), default='draft')  # draft, scheduled, active, paused, completed
    
    # Schedule
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime)
    
    # Limits
    daily_limit = Column(Integer, default=50)
    emails_per_hour = Column(Integer, default=10)
    
    # Stats
    total_contacts = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EmailOutreach(Base):
    """Individual email outreach record"""
    __tablename__ = 'email_outreach'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('email_campaigns.id', ondelete='CASCADE'))
    contact_id = Column(Integer, nullable=True)  # Foreign key removed - contacts table doesn't exist yet
    
    # Email details
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255))
    subject_line = Column(String(255))
    email_body_html = Column(Text)
    email_body_text = Column(Text)
    
    # Personalization data
    personalization = Column(JSON)  # Store merge tags/variables
    
    # Status
    status = Column(String(50), default='queued')
    # Values: queued, scheduled, sending, sent, failed, bounced
    
    # Tracking
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    bounced_at = Column(DateTime)
    
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    
    # Response
    has_response = Column(Boolean, default=False)
    response_text = Column(Text)
    response_sentiment = Column(String(50))  # positive, neutral, negative
    
    # Delivery
    message_id = Column(String(255))  # Provider message ID
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EmailTemplate(Base):
    """Email templates"""
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    
    # Template content
    subject_template = Column(String(255))
    html_template = Column(Text)
    text_template = Column(Text)
    
    # Variables used in template
    variables = Column(JSON)  # List of variables like {name}, {company}, {title}
    
    # Stats
    usage_count = Column(Integer, default=0)
    avg_open_rate = Column(Float)
    avg_response_rate = Column(Float)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EmailEvent(Base):
    """Email tracking events"""
    __tablename__ = 'email_events'
    
    id = Column(Integer, primary_key=True)
    outreach_id = Column(Integer, ForeignKey('email_outreach.id', ondelete='CASCADE'))
    
    event_type = Column(String(50), nullable=False)
    # Values: sent, delivered, opened, clicked, bounced, complained, unsubscribed, replied
    
    event_data = Column(JSON)  # Additional data (IP, user agent, link clicked, etc.)
    timestamp = Column(DateTime, server_default=func.now())
