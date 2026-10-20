# 🛡️ ANTI-BOT BYPASS STRATEGIES

## YOUR STEALTH MODE IS ALREADY CONFIGURED! ✅

### Current Setup (in app/fetch/crawler.py):

```python
USE_STEALTH_MODE = os.getenv('USE_STEALTH_MODE', 'true').lower() == 'true'

# Stealth features enabled:
1. '--disable-blink-features=AutomationControlled'  # Hide Playwright detection
2. Random User-Agent rotation (4 different browsers)
3. Human-like delays (1-3 seconds between requests)
4. Optional real Chrome profile (cookies, history)
```

**PROBLEM:** RocketReach has ADVANCED anti-bot (defeats basic stealth)

---

## 🔥 ADDITIONAL BYPASS OPTIONS:

### ✅ **1. Rotating Proxies** (Most Effective)
**How it works:** Spread requests across many IPs
**Services:**
- Bright Data: $500/month (premium, 99% success)
- Oxylabs: $300/month
- ScraperAPI: $49/month (cheapest)
- Smartproxy: $75/month

**Implementation:**
```python
# Add to .env
PROXY_SERVICE=scraperapi
SCRAPERAPI_KEY=your_key_here

# In crawler.py
if PROXY_SERVICE == 'scraperapi':
    proxy_url = f'http://scraperapi:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001'
    browser_config.proxy = proxy_url
```

**PROS:**
- ✅ Bypasses most anti-bot (including RocketReach)
- ✅ IP rotation automatic
- ✅ High success rate

**CONS:**
- ❌ $49-500/month cost
- ❌ Slower (adds latency)

---

### ✅ **2. Playwright Stealth Plugin** (Enhanced Stealth)
**How it works:** Advanced evasion (WebGL, canvas fingerprinting, etc.)

**Install:**
```bash
pip install playwright-stealth
```

**Implementation:**
```python
from playwright_stealth import stealth_async

async def fetch_page_stealth(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Apply stealth
        await stealth_async(page)
        
        await page.goto(url)
        content = await page.content()
        return content
```

**PROS:**
- ✅ Free!
- ✅ Better than basic stealth
- ✅ Bypasses 60-70% of anti-bot

**CONS:**
- ❌ Still blocked by advanced systems (RocketReach, Crunchbase)
- ❌ Slower than simple requests

---

### ✅ **3. Browser CDP Session** (Real Browser Fingerprint)
**How it works:** Use REAL Chrome installation (looks 100% human)

**Current Support (Already Built!):**
```python
# In .env
USE_BROWSER_PROFILE=true
CHROME_PROFILE_PATH=C:\Users\91787\AppData\Local\Google\Chrome\User Data
```

**How it works:**
- Uses YOUR actual Chrome profile
- Has YOUR cookies, login sessions, browsing history
- Websites see you as logged-in human

**PROS:**
- ✅ FREE!
- ✅ Highest success rate (90%+)
- ✅ Can access logged-in LinkedIn pages

**CONS:**
- ❌ Must close Chrome when running
- ❌ Only works on your machine (can't deploy to GitHub Actions)
- ❌ Slower (full browser overhead)

---

### ✅ **4. API Services** (Skip Scraping Entirely)
**How it works:** Pay for clean data APIs

**Services:**
- RocketReach API: $99/month (500 lookups)
- Hunter.io: $49/month (email finder)
- Clearbit: $99/month (company data)
- Apollo.io: $49/month (contact data)

**Implementation:**
```python
import requests

def find_email_rocketreach(name, company):
    response = requests.post(
        'https://api.rocketreach.co/v2/api/search',
        headers={'Api-Key': ROCKETREACH_API_KEY},
        json={'name': name, 'current_employer': company}
    )
    return response.json()['emails'][0]
```

**PROS:**
- ✅ NO blocking (official API)
- ✅ Clean, structured data
- ✅ Fast

**CONS:**
- ❌ $49-99/month cost
- ❌ Rate limited
- ❌ Not all data available

---

### ✅ **5. CAPTCHA Solving Services**
**How it works:** Auto-solve CAPTCHAs when encountered

**Services:**
- 2Captcha: $2.99/1000 solves
- Anti-Captcha: $0.50/1000
- CapMonster: One-time $50 (self-hosted)

**Implementation:**
```python
from twocaptcha import TwoCaptcha

def solve_captcha(site_key, url):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    result = solver.recaptcha(
        sitekey=site_key,
        url=url
    )
    return result['code']
```

**PROS:**
- ✅ Bypasses CAPTCHA challenges
- ✅ Cheap ($3/1000)

**CONS:**
- ❌ Adds 10-30s delay per CAPTCHA
- ❌ Doesn't help with 403 blocks

---

## 🎯 MY RECOMMENDATIONS FOR YOUR CASE:

### **IMMEDIATE FIX (Free, 5 min):**
**Blacklist RocketReach in prompt** - Don't waste time trying
```
❌ rocketreach.co - 100% block rate, skip entirely
```

### **SHORT-TERM (Free, 1 hour):**
**Use browser profile for RocketReach specifically**
```env
USE_BROWSER_PROFILE=true  # Only for RocketReach fetches
```
This uses YOUR logged-in Chrome (90% success rate)

### **MEDIUM-TERM (Paid, best results):**
**Add rotating proxies**
```env
PROXY_SERVICE=scraperapi
SCRAPERAPI_KEY=xxx
```
**Cost:** $49/month, worth it if finding 10+ contacts/day

### **LONG-TERM (Alternative approach):**
**Switch from RocketReach to unifers.ai**
- unifers.ai has weaker anti-bot
- Agent already tries this
- Free, works better

---

## 💡 WHAT I RECOMMEND FOR YOU:

**Right now:**
1. ✅ **Blacklist RocketReach in prompt** (immediate, free)
2. ✅ **Prioritize unifers.ai** (already working)
3. ✅ **Use LinkedIn posts more** (no blocking)

**If budget allows:**
4. 💰 **Add ScraperAPI** ($49/month, solves 90% of blocking)

**Current stealth is good enough for:**
- ✅ Company websites (working)
- ✅ LinkedIn (working)
- ✅ unifers.ai (working)
- ❌ RocketReach (ALWAYS blocked - need proxies OR blacklist)

---

**Want me to:**
1. Blacklist RocketReach in prompt? (FREE, 5 min)
2. Enable browser profile mode? (FREE, more complex)
3. Add proxy support? (PAID, $49/month)
