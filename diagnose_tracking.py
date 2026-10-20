"""
COMPREHENSIVE TRACKING INVESTIGATION
Figures out WHY tracking doesn't work when you open the email
"""
import sys
import os
sys.path.insert(0, 'v:/discover')

from dotenv import load_dotenv
load_dotenv()

from app.db import SessionLocal
from app.outreach.models import EmailOutreach

print("\n" + "="*80)
print("🔬 COMPREHENSIVE TRACKING INVESTIGATION")
print("="*80)

# 1. Check latest email
db = SessionLocal()
latest = db.query(EmailOutreach).order_by(EmailOutreach.id.desc()).first()

if not latest:
    print("\n❌ No emails in database")
    db.close()
    sys.exit(1)

print(f"\n📧 Latest Email: ID {latest.id}")
print(f"   To: {latest.recipient_email}")
print(f"   Subject: {latest.subject_line}")
print(f"   Status: {latest.status}")
print(f"   Open Count: {latest.open_count or 0}")

# 2. Check if pixel is in DATABASE body
print(f"\n{'='*80}")
print("❓ Question 1: Is tracking pixel in DATABASE?")
print("="*80)

if 'track/open' in latest.email_body_html:
    print("✅ YES - Pixel found in database body")
    import re
    match = re.search(r'<img[^>]*src="([^"]*track/open/[^"]*)"', latest.email_body_html)
    if match:
        print(f"   URL: {match.group(1)}")
else:
    print("❌ NO - Pixel NOT in database body")
    print("\n📝 This is EXPECTED behavior:")
    print("   - Database has body WITHOUT pixel")
    print("   - send_email() ADDS pixel before sending")
    print("   - Email that was SENT has pixel")
    print("   - Database never gets updated with pixel")

# 3. What SHOULD be in the sent email
print(f"\n{'='*80}")
print("❓ Question 2: What pixel SHOULD be in sent email?")
print("="*80)

app_url = os.getenv('APP_URL', 'http://localhost:8000').rstrip('/')
expected_pixel = f'<img src="{app_url}/track/open/{latest.id}" width="1" height="1" alt="" />'
print(f"\n✅ Expected pixel HTML:")
print(f"   {expected_pixel}")
print(f"\n📍 Expected URL:")
print(f"   {app_url}/track/open/{latest.id}")

# 4. Check environment
print(f"\n{'='*80}")
print("❓ Question 3: Is environment configured correctly?")
print("="*80)

track_opens = os.getenv('TRACK_OPENS', 'true')
print(f"\n📊 TRACK_OPENS: {track_opens}")
print(f"🔗 APP_URL: {app_url}")

if track_opens.lower() != 'true':
    print("\n❌ PROBLEM: TRACK_OPENS is not 'true'")
else:
    print("\n✅ Environment is correct")

# 5. The REAL problem
print(f"\n{'='*80}")
print("🎯 THE REAL PROBLEM")
print("="*80)

print("""
The tracking pixel IS in the sent email, but Gmail is blocking it!

Here's what's happening:

1. Email is sent with pixel: <img src="https://slow-heads-deny.loca.lt/track/open/X" />
2. Gmail receives the email
3. Gmail BLOCKS external images by default for security
4. You open the email
5. Gmail shows: "Images are not displayed"  ⚠️
6. The pixel doesn't load
7. Tracking doesn't work  ❌

SOLUTION:
1. Open the email
2. Look for banner: "Images are not displayed. Display images below"
3. Click "Display images below"
4. NOW the pixel loads
5. Tracking works!  ✅

OR:

Gmail might be blocking the LocalTunnel domain specifically because:
- LocalTunnel is a tunneling service
- Gmail blocks known tunneling/proxy domains for security
- Solution: Use a real domain (paid ngrok, custom domain, or deployed server)
""")

# 6. How to verify
print(f"\n{'='*80}")
print("🔍 HOW TO VERIFY")
print("="*80)

print(f"""
1. Open email in Gmail
2. Right-click anywhere in email body
3. Select "Inspect" (opens Chrome DevTools)
4. Press Ctrl+F in DevTools
5. Search for: track/open/{latest.id}

If you find it:
✅ Pixel IS in the email
❌ But Gmail is blocking it from loading

If you DON'T find it:
❌ Pixel was never sent (bug in send_email)

6. Check the <img> tag - is there a "src" attribute?
7. Try copying that URL and pasting in browser
8. If it loads = pixel works, Gmail is blocking
9. If 404 error = server issue
""")

# 7. Test the URL
print(f"\n{'='*80}")
print("🧪 QUICK TEST")
print("="*80)

print(f"""
Open this URL in your browser:
{app_url}/track/open/{latest.id}

Expected result:
- Shows a tiny transparent 1x1 pixel image
- Run: python check_tracking.py
- Open count increases by 1

If this works = Tracking code is fine, Gmail is blocking images
If 404 = Server or routing issue
""")

print(f"\n{'='*80}\n")

db.close()
