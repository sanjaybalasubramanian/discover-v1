"""
MORNING STATUS CHECK
Quick system diagnostic
"""
from app.db import SessionLocal
from app.outreach.models import EmailOutreach
from datetime import datetime
import os

print("\n" + "="*60)
print("🌅 GOOD MORNING!")
print("="*60)

# Check database connection
try:
    db = SessionLocal()
    
    # Email stats
    total = db.query(EmailOutreach).count()
    sent = db.query(EmailOutreach).filter(EmailOutreach.status == 'sent').count()
    pending = db.query(EmailOutreach).filter(EmailOutreach.status == 'pending').count()
    opened = db.query(EmailOutreach).filter(EmailOutreach.open_count > 0).count()
    human_opens = db.query(EmailOutreach).filter(EmailOutreach.open_count >= 2).count()
    
    print("\n📊 EMAIL SYSTEM STATUS:")
    print("-" * 60)
    print(f"  Total Emails in Database: {total}")
    print(f"  ✅ Sent: {sent}")
    print(f"  ⏳ Pending: {pending}")
    print(f"  📧 Opened (any): {opened}")
    print(f"  👤 Human Opens (2+ opens): {human_opens}")
    
    # Latest activity
    latest = db.query(EmailOutreach).filter(
        EmailOutreach.status == 'sent'
    ).order_by(EmailOutreach.sent_at.desc()).first()
    
    if latest:
        print(f"\n📬 Latest Sent Email:")
        print(f"  To: {latest.recipient_email}")
        print(f"  Sent: {latest.sent_at}")
        print(f"  Opens: {latest.open_count}")
        if latest.open_count >= 2:
            print(f"  👤 Human confirmed!")
    
    db.close()
    print("\n✅ Database connection: OK")
    
except Exception as e:
    print(f"\n❌ Database error: {e}")

# Check configuration
print("\n⚙️  CONFIGURATION:")
print("-" * 60)
approval_mode = os.getenv('REQUIRE_APPROVAL', 'false')
min_delay = os.getenv('MIN_EMAIL_DELAY', '60')
max_delay = os.getenv('MAX_EMAIL_DELAY', '180')
batch_size = os.getenv('EMAIL_BATCH_SIZE', '5')

print(f"  Manual Approval: {approval_mode.upper()}")
print(f"  Email Delays: {min_delay}-{max_delay}s")
print(f"  Batch Size: {batch_size}")

# Check tracking server
print("\n🔍 TRACKING SERVER:")
print("-" * 60)
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 8000))
if result == 0:
    print("  ✅ Server is RUNNING on port 8000")
else:
    print("  ⚠️  Server is NOT running")
    print("  Start with: python -m uvicorn tracking_server_debug:app --host 0.0.0.0 --port 8000")
sock.close()

print("\n" + "="*60)
print("🚀 System Ready!")
print("="*60)
print("\n💡 What would you like to do?")
print("  1. Send test email: python test_email_with_resume.py")
print("  2. Check tracking: python check_tracking_status.py")
print("  3. Test bot detection: python test_real_tracking.py")
print("  4. Send batch: python -m app.cli send-outreach --batch-size 5")
print()
