# Email Dispatcher - Complete Setup with Resume Attachment

## ✅ Phase 3 NOW IMPLEMENTED!

When you run `python app/cli.py run`, it will:
1. **Phase 1:** Discover jobs from LinkedIn/Indeed/Naukri
2. **Phase 2:** Find HR recruiter emails using AI agent
3. **Phase 3:** **Automatically send personalized emails with your resume!** ✨

---

## Configuration (.env)

### Required - Email Settings
```env
# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_USE_TLS=true

# Your Information (for email personalization)
FROM_NAME=Your Name
YOUR_ROLE=Software Engineer
YOUR_SKILLS=Python,React,AWS,PostgreSQL,FastAPI
YOUR_EXPERIENCE=5 years in full-stack development
YOUR_LOCATION=India

# Resume Attachment (OPTIONAL)
RESUME_PATH=C:/Users/YourName/Documents/Resume.pdf

# Email Sending Limits
EMAIL_BATCH_SIZE=10        # Send 10 emails per batch
MAX_DAILY_EMAILS=50
MAX_HOURLY_EMAILS=10
MIN_EMAIL_DELAY=60
MAX_EMAIL_DELAY=180
```

### Gmail App Password Setup
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Generate App Password
4. Use that password in `SMTP_PASSWORD`

---

## How It Works

### Full Auto Run
```bash
python app/cli.py run
```

This will:
1. Scrape ~75 jobs (3 per site × 25 sites)
2. Research top 5 companies for HR emails
3. **Generate AI-personalized emails for each contact**
4. **Attach your resume (if RESUME_PATH is set)**
5. **Send first 10 emails automatically with delays**

### Output Example
```
============================================================
PHASE 3: OUTREACH
============================================================
[INFO] Found 5 contacts to email
[INFO] Will attach: Resume.pdf

[EmailDispatcher] Creating campaign: Auto Campaign - Run 1
[INFO] Will attach: Resume.pdf
[EmailDispatcher] Created campaign with 5 emails
[EmailDispatcher] Each email will include 1 attachment(s)

[EmailDispatcher] Sending batch for campaign: Auto Campaign - Run 1
[EmailDispatcher] 5 emails to send

[EmailProvider] Waiting 127.3s before next email...
[SMTP] Attached: Resume.pdf
[SMTP] Sent email to santhosh.kumar@tcs.com

[EmailProvider] Waiting 89.2s before next email...
[SMTP] Attached: Resume.pdf
[SMTP] Sent email to sharanya.sricharan@tcs.com

[COMPLETE] Sent 5 emails, 0 failed

============================================================
✅ PIPELINE COMPLETED
============================================================
Phase 1: 75 jobs discovered
Phase 2: 5 companies researched
         5 contacts found (2 personal)
Phase 3: 5 emails sent, 0 failed
```

---

## Resume Attachment

### Setting Resume Path
```env
# Windows
RESUME_PATH=C:/Users/YourName/Documents/Resume.pdf

# Relative path
RESUME_PATH=./resume.pdf
```

### Supported Formats
- PDF (recommended): `Resume.pdf`
- Word: `Resume.docx`
- Any file: `CoverLetter.pdf`, `Portfolio.pdf`

### Multiple Attachments
Currently supports 1 file (resume). To add cover letter, modify in code:
```python
attachments = [
    'C:/path/to/Resume.pdf',
    'C:/path/to/CoverLetter.pdf'
]
```

---

## Email Personalization

Each email is **AI-generated and personalized** with:
- ✅ Recipient's name & title
- ✅ Company name
- ✅ Your skills matching their industry
- ✅ Professional but friendly tone
- ✅ Clear call-to-action

### Example Generated Email
```
Subject: Software Engineer - Interested in TCS Opportunities

Hi Santhosh Kumar,

I came across your role as Recruiter at TCS and wanted to reach out regarding 
software engineering opportunities.

I have 5 years of experience in full-stack development with:
- Python & FastAPI backend development
- React frontend development  
- AWS cloud infrastructure
- PostgreSQL databases

I'm particularly interested in TCS's work in enterprise solutions and would 
love to discuss how I can contribute to your team.

Would you be open to a brief conversation this week?

Best regards,
Your Name

[Attached: Resume.pdf]
```

---

## Manual Run (No Auto-Email)

If you don't configure SMTP, Phase 3 will skip:
```
[SKIPPED] Email not configured
Add SMTP credentials to .env to enable automatic email sending
Contacts are ready in database for manual outreach
```

You can then manually email using `test_email_dispatcher.py`.

---

## Safety Features

### Rate Limiting
- **10 emails per batch** (configurable via EMAIL_BATCH_SIZE)
- **60-180 second delays** between emails (human-like)
- **50 emails/day max** (configurable)
- **10 emails/hour max** (configurable)

### Email Warm-up (Recommended)
```
Day 1-3:  Set EMAIL_BATCH_SIZE=5  (send 5 emails)
Day 4-7:  Set EMAIL_BATCH_SIZE=10 (send 10 emails)
Day 8+:   Set EMAIL_BATCH_SIZE=20 (send 20 emails)
```

---

## Testing

### Test Email System
```bash
python test_email_system.py
```

### Test with Attachments
```bash
python test_email_with_resume.py
```

---

## Troubleshooting

### Resume Not Attaching
```
[WARNING] Resume not found: C:/path/to/Resume.pdf
```
→ Check file path, use absolute path, verify file exists

### SMTP Authentication Failed
```
[SMTP] Error: Authentication failed
```
→ Use Gmail App Password, not regular password

### Emails Going to Spam
→ Warm up sender reputation (start with 5 emails/day)
→ Personalize every email
→ Use professional email address

---

## Next Steps

1. Add SMTP credentials to `.env`
2. Set `RESUME_PATH` to your PDF resume
3. Update `YOUR_ROLE`, `YOUR_SKILLS`, `YOUR_EXPERIENCE`
4. Run `python app/cli.py run`
5. Monitor results in terminal
6. Check email sent folder
7. Wait for responses! 🎉

---

**Status:** ✅ Fully Functional - Auto-sends personalized emails with resume attachment!
