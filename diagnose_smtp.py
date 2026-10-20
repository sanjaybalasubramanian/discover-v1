"""
Diagnose SMTP connection issues
"""
import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("SMTP Connection Diagnostics")
print("=" * 60)

smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', 587))
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')

print(f"\nConfiguration:")
print(f"  Host: {smtp_host}")
print(f"  Port: {smtp_port}")
print(f"  Username: {smtp_username}")
print(f"  Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
print(f"  Password Length: {len(smtp_password) if smtp_password else 0} chars")

if not smtp_username or not smtp_password:
    print("\n❌ ERROR: SMTP credentials not configured")
    exit(1)

# Check if it's a Gmail App Password (should be 16 chars)
if 'gmail' in smtp_host and smtp_password:
    if len(smtp_password) != 16:
        print(f"\n⚠️  WARNING: Gmail App Passwords are 16 characters")
        print(f"   Your password is {len(smtp_password)} characters")
        print(f"\n   This looks like a regular password, not an App Password!")
        print(f"\n   To get a Gmail App Password:")
        print(f"   1. Go to: https://myaccount.google.com/security")
        print(f"   2. Enable 2-Step Verification (if not already)")
        print(f"   3. Search for 'App passwords'")
        print(f"   4. Generate new password for 'Mail'")
        print(f"   5. Copy the 16-character password (without spaces)")
        print(f"   6. Update SMTP_PASSWORD in .env")

print("\nTesting connection...")

try:
    # Test connection
    print(f"  Connecting to {smtp_host}:{smtp_port}...")
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
    print("  ✅ Connected")
    
    # Start TLS
    print("  Starting TLS encryption...")
    server.starttls()
    print("  ✅ TLS enabled")
    
    # Login
    print("  Logging in...")
    server.login(smtp_username, smtp_password)
    print("  ✅ Login successful!")
    
    server.quit()
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! SMTP is configured correctly")
    print("=" * 60)
    print("\nYou can now send emails!")
    print("Run: python test_email_with_resume.py")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication Failed: {e}")
    print("\nPossible causes:")
    print("1. Incorrect Gmail App Password")
    print("2. Using regular password instead of App Password")
    print("3. 2-Step Verification not enabled")
    print("\nSolution:")
    print("→ Generate a new Gmail App Password and update .env")
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP Error: {e}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
