"""
Database connection and utilities
"""
import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError('DATABASE_URL must be set in environment variables')

# Fix DATABASE_URL format for SQLAlchemy 2.x (postgres:// -> postgresql://)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_email(email: str) -> str:
    """Hash email for privacy (suppression list)"""
    return hashlib.sha256(email.lower().encode()).hexdigest()

def hash_ip(ip: str) -> str:
    """Hash IP address with salt"""
    salt = os.getenv('IP_HASH_SALT', 'default-salt-change-me')
    return hashlib.sha256((ip + salt).encode()).hexdigest()
