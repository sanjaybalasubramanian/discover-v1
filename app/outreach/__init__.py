"""
Email Outreach Module - Configuration
"""

# Email service providers
EMAIL_PROVIDERS = {
    'smtp': {
        'name': 'SMTP (Gmail, Outlook, etc.)',
        'cost': 'Free',
        'daily_limit': 500,  # Gmail limit
        'requires_setup': True
    },
    'sendgrid': {
        'name': 'SendGrid',
        'cost': 'Free tier: 100/day, Paid: $19.95/month for 50k',
        'daily_limit': 100,  # Free tier
        'requires_setup': True
    },
    'resend': {
        'name': 'Resend',
        'cost': 'Free tier: 100/day, Paid: $20/month for 50k',
        'daily_limit': 100,
        'requires_setup': True
    },
    'aws_ses': {
        'name': 'AWS SES',
        'cost': '$0.10 per 1,000 emails',
        'daily_limit': 200,  # Sandbox mode, can request increase
        'requires_setup': True
    }
}

# Default provider
DEFAULT_EMAIL_PROVIDER = 'smtp'  # Can be changed via .env

# Email templates
EMAIL_TEMPLATES = {
    'cold_outreach': {
        'subject': 'Interest in {company} - {your_role}',
        'template': 'cold_outreach.html'
    },
    'follow_up': {
        'subject': 'Following up - {company} Opportunity',
        'template': 'follow_up.html'
    },
    'thank_you': {
        'subject': 'Thank you for connecting',
        'template': 'thank_you.html'
    }
}

# Safety limits
SAFETY_LIMITS = {
    'max_daily_emails': 50,  # Conservative to avoid spam flags
    'max_hourly_emails': 10,
    'min_delay_between_emails': 60,  # seconds
    'max_delay_between_emails': 180,  # seconds
}

# Tracking
TRACK_OPENS = True
TRACK_CLICKS = True
TRACK_REPLIES = True
