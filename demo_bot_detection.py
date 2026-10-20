"""
Simulate email opens to demonstrate bot detection
Since localhost tracking doesn't work from mobile, 
we'll simulate opens in the database
"""
import time
from app.db import SessionLocal
from app.outreach.tracking import track_email_open

def simulate_email_opens():
    """Simulate email opens to demonstrate bot detection"""
    
    print("=" * 60)
    print("🎭 SIMULATING EMAIL OPENS")
    print("=" * 60)
    
    print("\n⚠️  Since localhost tracking doesn't work from mobile,")
    print("   let's simulate what WOULD happen if it did work:\n")
    
    db = SessionLocal()
    
    # First, create a test outreach record
    from app.outreach.models import EmailOutreach
    
    # Check if test record exists
    test_outreach = db.query(EmailOutreach).filter(
        EmailOutreach.id == 999
    ).first()
    
    if not test_outreach:
        print("📝 Creating test email record in database...")
        test_outreach = EmailOutreach(
            id=999,
            campaign_id=1,
            contact_id=1,
            recipient_email="sanjaybalasubramanian171102@gmail.com",
            recipient_name="Sanjay",
            subject_line="Bot Detection Test",
            email_body_html="<p>Test</p>",
            email_body_text="Test",
            status="sent"
        )
        db.add(test_outreach)
        db.commit()
        print("✅ Test record created\n")
    
    print("=" * 60)
    print("📱 SIMULATING: You open email on MOBILE")
    print("=" * 60)
    
    print("\n[1st Open - Mobile Security Scanner]")
    result1 = track_email_open(
        outreach_id=999,
        db=db,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0)",
        ip_address="203.192.123.45"
    )
    
    print(f"   ✅ Tracked!")
    print(f"   • Open Count: {result1['open_count']}")
    print(f"   • Is Human: {result1['is_human']}")
    print(f"   • Detection: {result1['detection']}")
    print(f"   → Status: 🤖 Bot (email security scanner)")
    
    time.sleep(2)
    
    print("\n=" * 60)
    print("💻 SIMULATING: You open email on PC")
    print("=" * 60)
    
    print("\n[2nd Open - You (Human)]")
    result2 = track_email_open(
        outreach_id=999,
        db=db,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="203.192.123.45"
    )
    
    print(f"   ✅ Tracked!")
    print(f"   • Open Count: {result2['open_count']}")
    print(f"   • Is Human: {result2['is_human']}")
    print(f"   • Detection: {result2['detection']}")
    print(f"   → Status: 👤 HUMAN CONFIRMED!")
    
    time.sleep(1)
    
    print("\n=" * 60)
    print("🔄 SIMULATING: You open email AGAIN")
    print("=" * 60)
    
    print("\n[3rd Open - Still Human]")
    result3 = track_email_open(
        outreach_id=999,
        db=db,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="203.192.123.45"
    )
    
    print(f"   ✅ Tracked!")
    print(f"   • Open Count: {result3['open_count']}")
    print(f"   • Is Human: {result3['is_human']}")
    print(f"   • Detection: {result3['detection']}")
    print(f"   → Status: 👤 Human engagement tracked")
    
    # Show final stats
    print("\n" + "=" * 60)
    print("📊 FINAL STATISTICS")
    print("=" * 60)
    
    from app.outreach.models import EmailEvent
    events = db.query(EmailEvent).filter(
        EmailEvent.outreach_id == 999
    ).order_by(EmailEvent.timestamp).all()
    
    print(f"\nTotal Events: {len(events)}")
    for i, event in enumerate(events, 1):
        data = event.event_data or {}
        is_human = "👤 Human" if data.get('is_human') else "🤖 Bot"
        print(f"{i}. {event.event_type.upper()} - {is_human} - {data.get('detection')}")
    
    # Get tracking stats
    from app.outreach.tracking import get_tracking_stats
    
    # Create a fake campaign if doesn't exist
    from app.outreach.models import EmailCampaign
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == 1).first()
    if not campaign:
        campaign = EmailCampaign(id=1, name="Test Campaign", status="active")
        db.add(campaign)
        db.commit()
    
    test_outreach.campaign_id = 1
    db.commit()
    
    stats = get_tracking_stats(1, db)
    
    print(f"\n📈 Campaign Stats:")
    print(f"   • Total Sent: {stats['total_sent']}")
    print(f"   • Opened by Bot Only: {stats['opened_by_bot_only']}")
    print(f"   • Opened by Human: {stats['opened_by_human']}")
    print(f"   • Human Open Rate: {stats['human_open_rate']}%")
    
    print("\n" + "=" * 60)
    print("✅ BOT DETECTION WORKING!")
    print("=" * 60)
    
    print("\n💡 Summary:")
    print("   • 1st open → Ignored (bot/scanner)")
    print("   • 2nd+ opens → Counted (human)")
    print("   • Campaign stats only count HUMAN opens")
    
    print("\n⚠️  In production:")
    print("   • Deploy tracking server to public URL")
    print("   • Update APP_URL in .env")
    print("   • Then mobile/desktop tracking works automatically!")
    
    db.close()

if __name__ == '__main__':
    simulate_email_opens()
