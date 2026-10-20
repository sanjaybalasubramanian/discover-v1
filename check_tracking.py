"""
Check Tracking Status - Clean Version
Shows open count for latest email
"""
import sys
sys.path.insert(0, 'v:/discover')

from app.db import SessionLocal
from app.outreach.models import EmailOutreach

db = SessionLocal()

# Get latest email
latest = db.query(EmailOutreach).order_by(EmailOutreach.id.desc()).first()

print("\n" + "="*80)
print("📊 TRACKING STATUS")
print("="*80)

if latest:
    print(f"\n📧 Email ID: {latest.id}")
    print(f"📧 To: {latest.recipient_email}")
    print(f"📝 Subject: {latest.subject_line}")
    print(f"📈 Open Count: {latest.open_count or 0}")
    print(f"🕐 First Opened: {latest.opened_at or 'Never'}")
    print(f"📊 Status: {latest.status}")
    print(f"📅 Sent: {latest.sent_at or 'Not sent'}")
    
    if latest.open_count and latest.open_count > 0:
        print(f"\n✅ Email has been opened {latest.open_count} time(s)! 🎉")
    else:
        print(f"\n⚠️  Email not opened yet")
        print(f"\n💡 Make sure:")
        print(f"   1. You opened the email")
        print(f"   2. Clicked 'Display images below'")
        print(f"   3. Images are actually loading")
else:
    print("\n❌ No emails in database")

print("\n" + "="*80 + "\n")

db.close()
