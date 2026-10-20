"""
Quick fix - Test tracking with ngrok tunnel
This exposes your localhost to the internet temporarily
"""
import subprocess
import time
import os

def test_with_ngrok():
    """
    Instructions to test tracking with ngrok
    """
    
    print("=" * 60)
    print("🌐 Testing Tracking with ngrok")
    print("=" * 60)
    
    print("\n📋 The Problem:")
    print("   • Tracking URL: http://localhost:8000")
    print("   • Your mobile can't reach localhost")
    print("   • Your PC email client might block localhost")
    
    print("\n✅ Solution: Use ngrok to expose localhost")
    
    print("\n📥 Step 1: Download ngrok")
    print("   • Go to: https://ngrok.com/download")
    print("   • Download for Windows")
    print("   • Extract ngrok.exe to v:/discover")
    
    print("\n🚀 Step 2: Start tracking server")
    print("   Terminal 1:")
    print("   cd v:/discover")
    print("   python tracking_server.py")
    
    print("\n🌍 Step 3: Start ngrok tunnel")
    print("   Terminal 2:")
    print("   cd v:/discover")
    print("   ngrok http 8000")
    
    print("\n   You'll see:")
    print("   Forwarding: https://abc123.ngrok.io -> http://localhost:8000")
    
    print("\n📧 Step 4: Send NEW test email with ngrok URL")
    print("   • Update APP_URL in .env to ngrok URL")
    print("   • Send new test email")
    print("   • Open on mobile/PC - tracking will work!")
    
    print("\n" + "=" * 60)
    print("⚠️  Easier Solution: Test on the same PC")
    print("=" * 60)
    
    print("\n💡 Alternative: Test tracking without ngrok")
    print("   1. Start tracking server on your PC")
    print("   2. Open Gmail in browser on SAME PC")
    print("   3. Open the email in Gmail web")
    print("   4. Watch terminal for tracking!")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_with_ngrok()
