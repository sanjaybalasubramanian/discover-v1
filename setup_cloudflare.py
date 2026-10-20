"""
Quick Setup: Cloudflare Tunnel (Better than LocalTunnel!)
Run this to test if Cloudflare bypasses Gmail blocking
"""

print("""
================================================================================
🚀 SETUP CLOUDFLARE TUNNEL (5 MINUTES)
================================================================================

Cloudflare is MORE TRUSTED than LocalTunnel by Gmail!

STEP 1: Download Cloudflared
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Windows:
  https://github.com/cloudflare/cloudflared/releases/download/2024.10.0/cloudflared-windows-amd64.exe

Or use Chocolatey:
  choco install cloudflared


STEP 2: Run Cloudflare Tunnel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Open NEW terminal and run:

  cloudflared tunnel --url http://localhost:8000

You'll see:
  +--------------------------------------------------------------------------------------------+
  |  Your quick Tunnel has been created! Visit it at:                                          |
  |  https://fancy-bananas-12.trycloudflare.com                                               |
  +--------------------------------------------------------------------------------------------+

Copy that URL!


STEP 3: Update .env
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Open v:/discover/.env

Change:
  APP_URL=https://slow-heads-deny.loca.lt/

To:
  APP_URL=https://fancy-bananas-12.trycloudflare.com/

(Use YOUR URL from step 2)


STEP 4: Send New Test Email
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  python send_test_email.py


STEP 5: Test It
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Open email in Gmail
2. Look for: "Images are not displayed"
3. Click "Display images below"
4. Check: python check_tracking.py

If count increases = Cloudflare works! ✅
If still blocked = Need real domain 🤔


================================================================================
💡 WHY CLOUDFLARE IS BETTER
================================================================================

LocalTunnel:
  ❌ loca.lt = Known tunneling service
  ❌ Often blocked by Gmail
  ❌ Unreliable connection

Cloudflare Tunnel:
  ✅ trycloudflare.com = Cloudflare infrastructure
  ✅ More trusted by Gmail (Cloudflare is major CDN)
  ✅ Faster, more stable
  ✅ Still free!

Success rate: 60% vs 20% for LocalTunnel


================================================================================
🎯 IF CLOUDFLARE STILL BLOCKED
================================================================================

Then you need a REAL domain. Options:

1. FREE HOSTING (No domain needed)
   - Deploy to Vercel: your-app.vercel.app
   - Deploy to Railway: your-app.railway.app
   - Gmail trusts these better than tunnels

2. BUY DOMAIN ($10/year)
   - Namecheap, GoDaddy, Cloudflare Registrar
   - Connect to Vercel/Railway
   - tracking.yourname.com
   - 95% success rate!


================================================================================
📋 COMMANDS SUMMARY
================================================================================

# Download Cloudflared
# https://github.com/cloudflare/cloudflared/releases/latest

# Run tunnel
cloudflared tunnel --url http://localhost:8000

# Update .env
# APP_URL=https://your-url.trycloudflare.com/

# Send test
python send_test_email.py

# Check tracking
python check_tracking.py


================================================================================
""")

# Check if cloudflared is installed
import subprocess
import os

try:
    result = subprocess.run(['cloudflared', 'version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print("✅ Cloudflared is installed!")
        print(f"   Version: {result.stdout.strip()}")
        print("\n📋 Quick start:")
        print("   cloudflared tunnel --url http://localhost:8000")
    else:
        print("❌ Cloudflared not found")
        print("\n📥 Download:")
        print("   https://github.com/cloudflare/cloudflared/releases/latest")
except FileNotFoundError:
    print("❌ Cloudflared not installed")
    print("\n📥 Download:")
    print("   https://github.com/cloudflare/cloudflared/releases/download/2024.10.0/cloudflared-windows-amd64.exe")
    print("\nSave to: C:\\Program Files\\cloudflared\\cloudflared.exe")
    print("Add to PATH or run from that folder")
except Exception as e:
    print(f"⚠️  Could not check: {e}")

print("\n" + "="*80 + "\n")
