# Email Dispatcher - Setup Guide

The Email Dispatcher automates sending personalized job application emails.

## Features
- AI-generated personalized emails
- Multiple providers (SMTP, SendGrid, Resend)
- Rate limiting (50/day, 10/hour)
- Email tracking (opens, clicks, replies)
- Campaign management

## Quick Start

### 1. Run Database Migration
```bash
python db/migrations/add_email_outreach_tables.py
```

### 2. Configure Email Provider (.env)
```env
# Email Provider
EMAIL_PROVIDER=smtp

# SMTP Configuration (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_USE_TLS=true

# Sender Name (optional)
FROM_NAME=Your Name

# Safety Limits
MAX_DAILY_EMAILS=50
MAX_HOURLY_EMAILS=10
MIN_EMAIL_DELAY=60
MAX_EMAIL_DELAY=180
```

**Note:** FROM_EMAIL automatically defaults to SMTP_USERNAME (same email you login with). For Gmail/Outlook, login email = sender email.

**Gmail App Password:** Google Account → Security → 2-Step Verification → App passwords → Generate

**Gmail App Password:**
1. Google Account → Security → 2-Step Verification
2. App passwords → Generate
3. Use that password in .env

### 3. Usage Example
```python
import asyncio
from app.db import SessionLocal
from app.outreach.dispatcher import EmailDispatcher
from app.models.contact import Contact

YOUR_PROFILE = {
    'name': 'Your Name',
    'current_role': 'Software Engineer',
    'skills': ['Python', 'React', 'AWS'],
    'experience': '5 years',
    'location': 'India'
}

async def main():
    db = SessionLocal()
    dispatcher = EmailDispatcher(db)
    
    # Get contacts
    contacts = db.query(Contact).filter(
        Contact.status == 'discovered'
    ).limit(20).all()
    
    contact_ids = [c.id for c in contacts]
    
    # Create campaign
    campaign_id = await dispatcher.create_campaign_from_contacts(
        name="Job Application",
        contact_ids=contact_ids,
        your_profile=YOUR_PROFILE
    )
    
    # Send batch
    results = await dispatcher.send_campaign_batch(campaign_id, batch_size=10)
    print(f"Sent: {results['sent']}, Failed: {results['failed']}")

asyncio.run(main())
```



## Safety Features
- Daily limit: 50 emails (configurable)
- Hourly limit: 10 emails (configurable)
- 60-180s random delay between emails (human-like)
- Email warm-up recommended (start with 5-10/day, increase gradually)

## Best Practices
1. **Personalize every email** - Use recipient's name, company, title
2. **Keep it short** - Under 200 words, clear call-to-action
3. **Timing matters** - Send 9-11 AM on weekdays
4. **Follow up** - After 5-7 days if no response
5. **Track metrics** - Monitor open rates (>20%) and response rates (>5%)

## Files Created
- `app/outreach/models.py` - Database models (4 tables)
- `app/outreach/providers.py` - Email providers (SMTP)
- `app/outreach/message_generator.py` - AI email generation
- `app/outreach/dispatcher.py` - Main orchestrator
- `db/migrations/add_email_outreach_tables.py` - Migration
- `test_email_dispatcher.py` - Example usage
