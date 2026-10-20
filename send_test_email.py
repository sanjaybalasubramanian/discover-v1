"""
Final Test Email Sender - Clean Version
Sends tracked email with LocalTunnel URL
"""
import sys
import os
import asyncio
from datetime import datetime

sys.path.insert(0, 'v:/discover')

from dotenv import load_dotenv
load_dotenv()

from app.db import SessionLocal
from app.outreach.models import EmailOutreach
from app.models.contact import Contact
from app.outreach.providers import SMTPProvider

async def send_tracked_test_email():
    """Send test email with tracking pixel"""
    
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("📧 SENDING TRACKED TEST EMAIL")
    print("="*80)
    
    # Configuration
    to_email = "sanjaybalasubramanian171102@gmail.com"
    to_name = "Sanjay"
    
    # Get or create contact
    contact = db.query(Contact).filter(Contact.email == to_email).first()
    if not contact:
        contact = Contact(
            name=to_name,
            email=to_email,
            title="Test Contact",
            company_id=None
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
    
    # Create outreach record
    outreach = EmailOutreach(
        contact_id=contact.id,
        campaign_id=None,
        recipient_email=to_email,
        recipient_name=to_name,
        subject_line="📊 Email Tracking Test - Open Multiple Times!",
        email_body_text="This email has tracking enabled.",
        email_body_html="""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">📊 Email Tracking Test</h2>
            <p>Hi Sanjay!</p>
            <p>This email has <strong>live tracking</strong> enabled.</p>
            
            <div style="background: #f0f9ff; padding: 15px; margin: 20px 0; border-left: 4px solid #2563eb;">
                <h3 style="margin-top: 0;">How to test:</h3>
                <ol>
                    <li>Make sure images are displayed (click "Display images" if needed)</li>
                    <li>Run: <code>python check_tracking.py</code></li>
                    <li>Close and open email again</li>
                    <li>Run check script again - count increases!</li>
                </ol>
            </div>
            
            <p>Best regards,<br>Your Tracking System</p>
        </body>
        </html>
        """,
        status='pending'
    )
    
    db.add(outreach)
    db.commit()
    db.refresh(outreach)
    
    print(f"\n✅ Outreach created: ID {outreach.id}")
    
    # Send email
    provider = SMTPProvider()
    from_email = os.getenv('SMTP_USERNAME')
    from_name = os.getenv('FROM_NAME', 'Test Sender')
    
    result = await provider.send_email(
        to_email=to_email,
        to_name=to_name,
        subject=outreach.subject_line,
        html_body=outreach.email_body_html,
        text_body=outreach.email_body_text,
        from_email=from_email,
        from_name=from_name,
        tracking_id=str(outreach.id)  # This adds the tracking pixel!
    )
    
    if result['success']:
        outreach.status = 'sent'
        outreach.sent_at = datetime.now()
        db.commit()
        
        app_url = os.getenv('APP_URL', 'http://localhost:8000').rstrip('/')
        
        print(f"\n✅ Email sent successfully!")
        print(f"\n📊 Outreach ID: {outreach.id}")
        print(f"🔗 Tracking URL: {app_url}/track/open/{outreach.id}")
        print(f"\n{'='*80}")
        print(f"📋 NEXT STEPS:")
        print(f"{'='*80}")
        print(f"\n1. Open email in Gmail")
        print(f"2. Click 'Display images below' if prompted")
        print(f"3. Run: python check_tracking.py")
        print(f"4. Open email again")
        print(f"5. Run check script again - count increases!")
        print(f"\n{'='*80}\n")
    else:
        outreach.status = 'failed'
        outreach.error_message = result.get('error', 'Unknown error')
        db.commit()
        print(f"\n❌ Failed: {result.get('error')}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(send_tracked_test_email())
