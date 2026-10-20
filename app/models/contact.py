"""
Contact and Evidence models
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db import Base
import uuid

class Contact(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'))
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    title = Column(String(255))
    linkedin_url = Column(Text)  # LinkedIn profile URL
    location = Column(String(255))  # Geographic location (Tamil Nadu, India, etc.)
    priority_score = Column(Float)  # Priority score (1.0=TN, 0.8=India, 0.5=Indian abroad, 0.3=Other)
    tracking_token = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    validation_status = Column(String(50), default='pending')
    validation_score = Column(Integer)
    mx_valid = Column(Boolean)
    source_count = Column(Integer, default=0)
    status = Column(String(50), default='discovered')
    inferred = Column(Boolean, default=False)
    is_generic = Column(Boolean, default=False)  # True=generic (careers@, hr@), False=personal (john@)
    approved = Column(Boolean, default=False)
    last_contacted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Evidence(Base):
    __tablename__ = 'evidence'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'))
    source_url = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False)
    surrounding_text = Column(Text)
    fetched_at = Column(DateTime, server_default=func.now())

class Validation(Base):
    __tablename__ = 'validations'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'))
    validator = Column(String(50), nullable=False)
    result = Column(String(50))
    score = Column(Integer)
    details = Column(Text)  # JSON string
    validated_at = Column(DateTime, server_default=func.now())
