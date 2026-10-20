"""
View All Email Tracking - Shows all tracked emails
"""
import sys
sys.path.insert(0, 'v:/discover')

from app.db import SessionLocal
from app.models.outreach import Open, Outreach
from sqlalchemy import desc, func

def view_all_tracking():
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("📊 ALL EMAIL TRACKING DATA")
    print("="*80)
    
    # Get all outreach records
    all_outreach = db.query(Outreach).all()
    
    if not all_outreach:
        print("\n⚠️  No emails in database yet")
        print("\nTo track emails, you need to:")
        print("1. Send emails using the dispatcher")
        print("2. Those will create real outreach records")
        print("3. Then tracking will work automatically")
        return
    
    print(f"\n✅ Found {len(all_outreach)} emails in database\n")
    
    # Get all opens
    all_opens = db.query(Open).order_by(desc(Open.opened_at)).all()
    
    print(f"📧 Total Tracked Opens: {len(all_opens)}")
    print("-"*80)
    
    if all_opens:
        for open_event in all_opens:
            outreach = db.query(Outreach).filter(Outreach.id == open_event.outreach_id).first()
            
            print(f"\n🔔 Outreach ID: {open_event.outreach_id}")
            if outreach:
                print(f"   To: {outreach.recipient_email}")
                print(f"   Subject: {outreach.subject[:50]}...")
            print(f"   Opened: {open_event.opened_at}")
            print(f"   Bot/Machine: {'Yes ❌' if open_event.is_machine_open else 'No ✅ (HUMAN!)'}")
            print(f"   User Agent: {open_event.user_agent[:80] if open_event.user_agent else 'N/A'}...")
    else:
        print("\n⚠️  No tracking events recorded yet")
        print("\nThis means either:")
        print("1. No one has opened the emails yet")
        print("2. Server wasn't running when emails were opened")
        print("3. Email clients blocked images")
        
        print("\n📋 Here are the emails that were sent:")
        print("-"*80)
        for outreach in all_outreach[:10]:  # Show first 10
            print(f"\n📧 Outreach ID: {outreach.id}")
            print(f"   To: {outreach.recipient_email}")
            print(f"   Status: {outreach.status}")
            print(f"   Sent: {outreach.sent_at if outreach.sent_at else 'Not sent yet'}")
            print(f"   Tracking URL: https://seldom-upbeat-elderly.ngrok-free.dev/track/open/{outreach.id}")
    
    print("\n" + "="*80)
    print("💡 TIP: Test tracking by visiting a tracking URL in your browser")
    print("   Example: https://seldom-upbeat-elderly.ngrok-free.dev/track/open/1")
    print("="*80 + "\n")
    
    db.close()

if __name__ == "__main__":
    view_all_tracking()
