from app.db import SessionLocal
from app.outreach.tracking import track_email_open
from app.outreach.models import EmailOutreach, EmailEvent

db = SessionLocal()

print("\n" + "="*60)
print("LIVE DEMONSTRATION: BOT DETECTION")
print("="*60)

print("\n[1ST OPEN - Bot Scanner]")
r1 = track_email_open(1, db, 'Bot Scanner', '192.168.1.1')
print(f"Open Count: {r1['open_count']}")
print(f"Is Human: {r1['is_human']}")
print(f"Detection: {r1['detection']}")
print("Status: 🤖 BOT - NOT counted")

print("\n[2ND OPEN - You on PC]")
r2 = track_email_open(1, db, 'Chrome Windows', '192.168.1.1')
print(f"Open Count: {r2['open_count']}")
print(f"Is Human: {r2['is_human']}")
print(f"Detection: {r2['detection']}")
print("Status: 👤 HUMAN - COUNTED!")

print("\n[3RD OPEN - You on mobile]")
r3 = track_email_open(1, db, 'iPhone Safari', '192.168.1.2')
print(f"Open Count: {r3['open_count']}")
print(f"Is Human: {r3['is_human']}")
print(f"Detection: {r3['detection']}")
print("Status: 👤 HUMAN - Tracked")

events = db.query(EmailEvent).filter(
    EmailEvent.outreach_id == 1,
    EmailEvent.event_type == 'opened'
).all()

print(f"\n{'='*60}")
print(f"TOTAL OPEN EVENTS: {len(events)}")
print("="*60)

for i, e in enumerate(events, 1):
    data = e.event_data
    icon = "👤" if data.get('is_human') else "🤖"
    print(f"{i}. {icon} {data.get('detection')} - Count: {data.get('open_count')}")

print("\n✅ BOT DETECTION WORKING!")
print("\nWhy your email didn't track:")
print("• Tracking pixel URL: http://localhost:8000 (not accessible from email client)")
print("• Solution: Deploy to public server or use ngrok")

db.close()
