"""
Email tracking utilities - Open/Click tracking with bot detection
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.outreach.models import EmailOutreach, EmailEvent


def track_email_open(outreach_id: int, db: Session, user_agent: str = None, ip_address: str = None) -> dict:
    """
    Track email open event with bot detection
    
    Bot Detection Logic:
    - First open (open_count = 1): Usually email security scanner
    - Second+ open (open_count >= 2): Real human opened the email
    """
    
    outreach = db.query(EmailOutreach).filter(EmailOutreach.id == outreach_id).first()
    
    if not outreach:
        return {'error': 'Outreach not found'}
    
    # Increment open count
    outreach.open_count += 1
    
    # First open? Mark timestamp but don't count as "human opened"
    if outreach.open_count == 1:
        outreach.opened_at = datetime.now()
        is_human = False
        detection_status = 'likely_bot'
    else:
        # Second+ open = Human!
        is_human = True
        detection_status = 'human_confirmed'
        
        # Update campaign stats only when human confirmed
        if outreach.campaign_id:
            from app.outreach.models import EmailCampaign
            campaign = db.query(EmailCampaign).filter(
                EmailCampaign.id == outreach.campaign_id
            ).first()
            if campaign and outreach.open_count == 2:  # Only increment once
                campaign.emails_opened += 1
    
    # Log event
    event = EmailEvent(
        outreach_id=outreach.id,
        event_type='opened',
        event_data={
            'user_agent': user_agent,
            'ip_address': ip_address,
            'open_count': outreach.open_count,
            'is_human': is_human,
            'detection': detection_status
        }
    )
    db.add(event)
    db.commit()
    
    return {
        'success': True,
        'open_count': outreach.open_count,
        'is_human': is_human,
        'detection': detection_status
    }


def track_email_click(outreach_id: int, db: Session, link_url: str = None, user_agent: str = None, ip_address: str = None) -> dict:
    """
    Track email link click (always human - bots don't click links)
    """
    
    outreach = db.query(EmailOutreach).filter(EmailOutreach.id == outreach_id).first()
    
    if not outreach:
        return {'error': 'Outreach not found'}
    
    # Increment click count
    outreach.click_count += 1
    
    # First click? Mark timestamp
    if outreach.click_count == 1:
        outreach.clicked_at = datetime.now()
    
    # Update campaign stats
    if outreach.campaign_id and outreach.click_count == 1:
        from app.outreach.models import EmailCampaign
        campaign = db.query(EmailCampaign).filter(
            EmailCampaign.id == outreach.campaign_id
        ).first()
        if campaign:
            campaign.emails_clicked += 1
    
    # Log event
    event = EmailEvent(
        outreach_id=outreach.id,
        event_type='clicked',
        event_data={
            'link_url': link_url,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'click_count': outreach.click_count
        }
    )
    db.add(event)
    db.commit()
    
    return {
        'success': True,
        'click_count': outreach.click_count
    }


def get_tracking_stats(campaign_id: int, db: Session) -> dict:
    """
    Get tracking statistics with human vs bot breakdown
    """
    
    from app.outreach.models import EmailCampaign
    from sqlalchemy import func
    
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    
    if not campaign:
        return {'error': 'Campaign not found'}
    
    # Get all outreach records for this campaign
    outreach_records = db.query(EmailOutreach).filter(
        EmailOutreach.campaign_id == campaign_id
    ).all()
    
    total_sent = len([o for o in outreach_records if o.status == 'sent'])
    
    # Bot detection breakdown
    opened_by_bot_only = len([o for o in outreach_records if o.open_count == 1])
    opened_by_human = len([o for o in outreach_records if o.open_count >= 2])
    
    # Click stats (all clicks are human)
    clicked = len([o for o in outreach_records if o.click_count > 0])
    
    # Calculate rates
    human_open_rate = (opened_by_human / total_sent * 100) if total_sent > 0 else 0
    click_rate = (clicked / total_sent * 100) if total_sent > 0 else 0
    
    return {
        'campaign_id': campaign_id,
        'campaign_name': campaign.name,
        'total_sent': total_sent,
        'opened_by_bot_only': opened_by_bot_only,
        'opened_by_human': opened_by_human,
        'clicked': clicked,
        'human_open_rate': round(human_open_rate, 2),
        'click_rate': round(click_rate, 2)
    }
