"""
Add email outreach tables to database
"""
import sys
import os
sys.path.insert(0, 'v:/discover')

from dotenv import load_dotenv
import psycopg2

load_dotenv()

SQL = """
-- Email campaigns table
CREATE TABLE IF NOT EXISTS email_campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) DEFAULT 'cold_outreach',
    subject_line VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    daily_limit INTEGER DEFAULT 50,
    emails_per_hour INTEGER DEFAULT 10,
    total_contacts INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Email outreach table
CREATE TABLE IF NOT EXISTS email_outreach (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES email_campaigns(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    subject_line VARCHAR(255),
    email_body_html TEXT,
    email_body_text TEXT,
    personalization JSONB,
    status VARCHAR(50) DEFAULT 'queued',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    bounced_at TIMESTAMP,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    has_response BOOLEAN DEFAULT FALSE,
    response_text TEXT,
    response_sentiment VARCHAR(50),
    message_id VARCHAR(255),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Email templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    subject_template VARCHAR(255),
    html_template TEXT,
    text_template TEXT,
    variables JSONB,
    usage_count INTEGER DEFAULT 0,
    avg_open_rate FLOAT,
    avg_response_rate FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Email events table
CREATE TABLE IF NOT EXISTS email_events (
    id SERIAL PRIMARY KEY,
    outreach_id INTEGER REFERENCES email_outreach(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_email_outreach_campaign ON email_outreach(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_outreach_contact ON email_outreach(contact_id);
CREATE INDEX IF NOT EXISTS idx_email_outreach_status ON email_outreach(status);
CREATE INDEX IF NOT EXISTS idx_email_events_outreach ON email_events(outreach_id);
"""

if __name__ == '__main__':
    print("="*60)
    print("EMAIL OUTREACH DATABASE MIGRATION")
    print("="*60)
    
    database_url = os.getenv('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    try:
        cursor.execute(SQL)
        conn.commit()
        print("\n✓ Migration completed successfully!")
        print("\nAdded tables:")
        print("  - email_campaigns")
        print("  - email_outreach")
        print("  - email_templates")
        print("  - email_events")
    except Exception as e:
        print(f"\nError: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
