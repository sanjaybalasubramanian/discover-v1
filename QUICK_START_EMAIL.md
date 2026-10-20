# Quick Start - Auto Email with Resume

## Answer to Your Questions

### Q1: "If I run the job, does it fetch jobs, find emails, and email my application to all contacts?"

**YES! ✅** That's exactly what it does now.

```bash
python app/cli.py run
```

This single command:
1. ✅ **Fetches jobs** from LinkedIn, Indeed, Naukri (Phase 1)
2. ✅ **Finds HR emails** using AI agent (Phase 2)  
3. ✅ **Emails your application** to all contacts (Phase 3) **← NEW!**

### Q2: "Does it allow me to upload my resume and attach it to emails?"

**YES! ✅** Just set the path in `.env`:

```env
RESUME_PATH=C:/Users/YourName/Documents/Resume.pdf
```

Every email sent will automatically include your resume as an attachment.

---

## Complete Setup (5 Minutes)

### Step 1: Configure Email (.env)
```env
# SMTP (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_USE_TLS=true

# Your Info
FROM_NAME=Sanjay Kumar
YOUR_ROLE=Full Stack Developer
YOUR_SKILLS=Python,FastAPI,React,AWS,PostgreSQL
YOUR_EXPERIENCE=5 years building scalable web applications
YOUR_LOCATION=Bangalore, India

# Resume
RESUME_PATH=C:/Users/Sanjay/Documents/Resume.pdf

# Sending Limits
EMAIL_BATCH_SIZE=10
```

### Step 2: Get Gmail App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Click **App Passwords**
4. Generate password for "Mail"
5. Copy 16-character password to `SMTP_PASSWORD`

### Step 3: Run Pipeline
```bash
python app/cli.py run
```

**That's it!** 🎉

---

## What Happens

```
============================================================
PHASE 1: DISCOVERY
============================================================
Found 75 jobs from LinkedIn, Indeed, Naukri

============================================================
PHASE 2: RESEARCH
============================================================
Researching 5 companies...
✓ TCS - Found 2 contacts
✓ Infosys - Found 1 contact
✓ Wipro - Found 2 contacts
Total: 5 contacts ready to email

============================================================
PHASE 3: OUTREACH
============================================================
[INFO] Found 5 contacts to email
[INFO] Will attach: Resume.pdf

Creating campaign...
[EmailDispatcher] Created campaign with 5 emails
[EmailDispatcher] Each email will include 1 attachment(s)

Sending emails...
[SMTP] Attached: Resume.pdf (245.3 KB)
[SMTP] Sent email to santhosh.kumar@tcs.com

[COMPLETE] Sent 5 emails, 0 failed

============================================================
✅ PIPELINE COMPLETED
============================================================
Phase 1: 75 jobs discovered
Phase 2: 5 companies researched, 5 contacts found
Phase 3: 5 emails sent, 0 failed
```

---

## Email Example

**To:** santhosh.kumar@tcs.com  
**From:** Sanjay Kumar <your.email@gmail.com>  
**Subject:** Full Stack Developer - Interested in TCS Opportunities  
**Attachment:** Resume.pdf (245 KB)

```
Hi Santhosh Kumar,

I came across your role as Recruiter at TCS and wanted to reach out 
regarding full-stack development opportunities.

I have 5 years of experience building scalable web applications with:
- Python & FastAPI for backend services
- React for modern frontend development
- AWS for cloud infrastructure
- PostgreSQL for database management

I'm particularly impressed by TCS's work in enterprise solutions and 
digital transformation. I believe my skills in full-stack development 
align well with your team's needs.

Would you be open to a brief conversation this week?

I've attached my resume for your review.

Best regards,
Sanjay Kumar
```

**[Attached: Resume.pdf]** ✅

---

## Summary

✅ **Full automation works end-to-end**
- Discovers jobs ✓
- Finds HR emails ✓
- Sends personalized emails ✓
- Attaches resume ✓

✅ **Simple configuration**
- Just add SMTP credentials
- Set resume path
- Run one command

✅ **Safe & professional**
- Rate limiting (60-180s delays)
- Personalized content
- Human-like behavior

**You're ready to start!** 🚀

1. Configure `.env` (5 minutes)
2. Test: `python test_email_with_resume.py`
3. Run: `python app/cli.py run`
4. Monitor sent folder
5. Wait for responses! 📧
