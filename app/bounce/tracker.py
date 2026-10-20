"""
Simple bounce tracking via Zoho webhook
"""
from datetime import datetime
from app.db import SessionLocal
from app.models.contact import Contact


def mark_email_bounced(email: str, bounce_type: str = 'hard') -> bool:
    """
    Mark email as bounced (called by webhook)
    
    Args:
        email: Email address that bounced
        bounce_type: 'hard' or 'soft' bounce
    
    Returns:
        True if contact found and updated, False otherwise
    """
    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.email == email).first()
        
        if contact:
            contact.validation_status = 'bounced'
            contact.status = 'invalid'
            contact.updated_at = datetime.utcnow()
            db.commit()
            
            print(f"[Bounce] Marked {email} as bounced ({bounce_type})")
            return True
        
        print(f"[Bounce] Contact not found: {email}")
        return False
    except Exception as e:
        print(f"[Bounce] Error marking {email}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def get_bounce_rate(company_id: int) -> dict:
    """
    Get bounce statistics for a company
    
    Args:
        company_id: Company ID
    
    Returns:
        dict with bounce statistics
    """
    db = SessionLocal()
    try:
        # Total contacts
        total = db.query(Contact).filter(Contact.company_id == company_id).count()
        
        # Bounced contacts
        bounced = db.query(Contact).filter(
            Contact.company_id == company_id,
            Contact.validation_status == 'bounced'
        ).count()
        
        # Inferred contacts stats
        inferred_total = db.query(Contact).filter(
            Contact.company_id == company_id,
            Contact.inferred == True
        ).count()
        
        inferred_bounced = db.query(Contact).filter(
            Contact.company_id == company_id,
            Contact.inferred == True,
            Contact.validation_status == 'bounced'
        ).count()
        
        # Real (non-inferred) contacts stats
        real_total = total - inferred_total
        real_bounced = bounced - inferred_bounced
        
        return {
            'total_contacts': total,
            'bounced': bounced,
            'bounce_rate': round((bounced / total * 100), 2) if total > 0 else 0,
            'inferred_total': inferred_total,
            'inferred_bounced': inferred_bounced,
            'inferred_bounce_rate': round((inferred_bounced / inferred_total * 100), 2) if inferred_total > 0 else 0,
            'real_total': real_total,
            'real_bounced': real_bounced,
            'real_bounce_rate': round((real_bounced / real_total * 100), 2) if real_total > 0 else 0
        }
    finally:
        db.close()


def cleanup_bounced_contacts(company_id: int = None) -> int:
    """
    Remove bounced contacts from database
    
    Args:
        company_id: Optional company ID to limit cleanup, or None for all
    
    Returns:
        Number of contacts deleted
    """
    db = SessionLocal()
    try:
        query = db.query(Contact).filter(Contact.validation_status == 'bounced')
        
        if company_id:
            query = query.filter(Contact.company_id == company_id)
        
        count = query.count()
        query.delete(synchronize_session=False)
        db.commit()
        
        print(f"[Bounce] Cleaned up {count} bounced contacts")
        return count
    except Exception as e:
        print(f"[Bounce] Cleanup error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

