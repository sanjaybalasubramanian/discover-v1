"""
Phase 2: Research Agent using LangGraph + AWS Bedrock
Finds personal recruiter contacts for companies using agentic workflow
"""
import os
from datetime import datetime
from typing import Any, Dict

from langchain_aws import ChatBedrockConverse
from langgraph.prebuilt import create_react_agent
from sqlalchemy.orm import Session

from app.models import Company
from app.models.contact import Contact
from app.research.tools import RESEARCH_TOOLS


async def research_company_contacts(
    company_name: str,
    db: Session,
    max_contacts: int = 5,
    run_id: int = None
) -> Dict[str, Any]:
    """
    Use LangGraph agent with Bedrock to find personal recruiter contacts

    Args:
        company_name: Company to research
        db: Database session
        max_contacts: Max contacts to find
        run_id: Pipeline run ID that discovered this company

    Returns:
        Dict with personal and fallback contacts
    """

    print(f"[Research] Starting agentic research for {company_name}")

    # Get/create company
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        company = Company(name=company_name, research_status='in_progress', run_id=run_id)
        db.add(company)
        db.flush()
    else:
        company.research_status = 'in_progress'
        company.research_attempts += 1
        # Update run_id if provided and not already set
        if run_id and not company.run_id:
            company.run_id = run_id
        db.commit()

    # Retry logic: max 3 attempts
    max_attempts = 3
    attempt = company.research_attempts

    if attempt > max_attempts:
        print(f"[Research] Max attempts ({max_attempts}) reached, marking as failed")
        company.research_status = 'failed'
        db.commit()

        return {
            'company': company_name,
            'personal_contacts': [],
            'fallback_contacts': [],
            'total_contacts': 0,
            'success': False,
            'error': f'Max retry attempts ({max_attempts}) exceeded'
        }

    try:
        print(f"[Research] Attempt {attempt}/{max_attempts}")

        # Create and run agent
        agent = await _create_research_agent()
        contacts_found = await _run_agent_research(agent, company_name, company, db)

        # Mark complete
        company.research_status = 'completed'
        company.researched_at = datetime.now()
        db.commit()

        # Categorize by email pattern (simple heuristic)
        # Personal: has firstname.lastname or similar patterns
        # Generic: sales@, info@, careers@, etc.
        personal = [c for c in contacts_found if c['email'] and '@' in c['email'] and '.' in c['email'].split('@')[0]]
        fallback = [c for c in contacts_found if c not in personal]

        print(f"[Research] FOUND {len(contacts_found)} contacts")
        print(f"[Research]   {len(personal)} personal, {len(fallback)} fallback")

        return {
            'company': company_name,
            'personal_contacts': personal,
            'fallback_contacts': fallback,
            'total_contacts': len(contacts_found),
            'success': True
        }

    except Exception as e:
        print(f"[Research] ERROR on attempt {attempt}: {e}")

        # Don't mark as failed yet, will retry
        if attempt < max_attempts:
            company.research_status = 'pending'
            print(f"[Research] Will retry (attempts left: {max_attempts - attempt})")
        else:
            company.research_status = 'failed'
            print("[Research] Max attempts reached, marking as failed")

        db.commit()

        return {
            'company': company_name,
            'personal_contacts': [],
            'fallback_contacts': [],
            'total_contacts': 0,
            'success': False,
            'error': str(e),
            'will_retry': attempt < max_attempts
        }


async def _create_research_agent():
    """Create LangGraph agent with Bedrock Claude"""

    print("[Agent] Initializing Bedrock Claude model")

    # Initialize Bedrock Chat Model using Converse API (fixes tool_use/tool_result errors)
    # Using inference profile for cross-region availability
    llm = ChatBedrockConverse(
        model=os.getenv('BEDROCK_MODEL', 'us.anthropic.claude-3-sonnet-20240229-v1:0'),  # Inference profile
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        credentials_profile_name=None,  # Use env vars
        additional_model_request_fields={
            "max_tokens": 4000,
        }
    )

    print(f"[Agent] Creating ReAct agent with {len(RESEARCH_TOOLS)} tools")

    # Create ReAct agent with research tools
    agent = create_react_agent(llm, RESEARCH_TOOLS)

    return agent



async def _run_agent_research(agent, company_name: str, company: Company, db: Session) -> list:
    """
    Execute agent research workflow

    Args:
        agent: LangGraph agent
        company_name: Company to research
        company: Company model instance
        db: Database session

    Returns:
        List of contact dictionaries
    """

    # Set tool context for database access
    from app.research.tools import set_tool_context
    set_tool_context(company, db)

    # Get company domain if available
    domain_hint = f"\n**Company Domain: {company.domain}**" if company.domain else ""
    
    # Extract short company name (remove common suffixes for better search results)
    short_name = company_name
    for suffix in [' Technologies', ' Technology', ' Solutions', ' Services', ' Pvt Ltd', ' Private Limited', ' Inc', ' LLC']:
        if company_name.endswith(suffix):
            short_name = company_name[:-len(suffix)].strip()
            break

    # Define research task - THREE-PHASE SEARCH STRATEGY WITH EMAIL SOURCE KNOWLEDGE
    task_prompt = f"""You are a research agent finding recruiter contact information for {company_name}.{domain_hint}

**SHORT NAME FOR SEARCHES: {short_name}**

==============================================================================
[TARGET] MISSION: WHY THIS RESEARCH MATTERS
==============================================================================

You are researching contacts for a CRITICAL HIRING PIPELINE.

**What Happens After You Finish:**
1. Your contacts will receive personalized job applications
2. Goal: Get interview calls from recruiters
3. Success = Recruiter replies and schedules interview

**Why Quality Matters:**
- 1 Chennai recruiter email > 5 US recruiter emails (10x conversion rate)
- Personal email (priya.sharma@) > Generic email (hr@) (3x conversion rate)
- Current employee > Ex-employee (∞x difference - ex-employees can't help!)

**Why Location is CRITICAL:**
- Tamil Nadu recruiters: Response rate ~40-50%
- Other India recruiters: Response rate ~20-30%  
- International recruiters: Response rate ~5-10%

**Your Job:**
Find 3-5 HIGH-QUALITY contacts who:
1. Are CURRENT employees (verified, not stale data)
2. Have PERSONAL emails preferred (priya.sharma@, arun.k@)
   - hr@, careers@, recruiting@ are acceptable as FALLBACK if no personal emails found
3. Are located in TAMIL NADU (or at least India) - LOCATION IS MANDATORY
4. Have correct domain (reject external recruiters)

**This is not web scraping - this is building a targeted outreach list that determines whether someone gets hired or not. Take it seriously.**

==============================================================================
CRITICAL RULES (Read First!)
==============================================================================

1. **NEVER FABRICATE EMAILS**: Only report emails you extracted from actual fetched pages or search snippets. Include source URL for every email.

2. **QUALITY OVER QUANTITY**: 1-2 verified personal emails better than 5 generic ones.

3. **DOMAIN VERIFICATION**: Every email must match company domain (@{company.domain if company.domain else short_name.lower() + '.com'})

==============================================================================
COMPANY SIZE & FOUNDER RULE
==============================================================================

**STEP 1: Check company size on LinkedIn**
Search: "{company_name} LinkedIn company page"
Look for employee count:
- 1-20 employees = STARTUP → Founders/CTOs ARE valid contacts (they hire directly)
- 21-100 employees = SMALL → Prefer recruiters, founders OK if no recruiters found
- 100+ employees = ESTABLISHED → Skip founders, only recruiters/HR

**FOUNDER/CTO RULE:**
[YES] Company ≤20 employees → Founders/CTOs/VPs are VALID (they do hiring)
[YES] Company 21-100 employees → Founders are fallback contacts only
[NO] Company >100 employees → Skip founders completely, only recruiters

==============================================================================
GEOGRAPHIC PRIORITY (CRITICAL REQUIREMENT)
==============================================================================

**PRIORITY ORDER** (from highest to lowest):

1. **[GOLD] TAMIL NADU, INDIA** (Priority Score: 1.0)
   - Cities: Chennai, Coimbatore, Madurai, Salem, Trichy, etc.
   - **ALWAYS prioritize these contacts FIRST**
   - Extract location from LinkedIn profile page

2. **[SILVER] OTHER INDIA** (Priority Score: 0.8)
   - Cities: Bangalore, Mumbai, Delhi, Hyderabad, Pune, etc.
   - Prioritize AFTER Tamil Nadu contacts
   - Still preferred over non-India contacts

3. **[BRONZE] OUTSIDE INDIA** (Priority Score: 0.5)
   - International recruiters
   - Only if no India-based recruiters found
   - Last resort

**MANDATORY LOCATION EXTRACTION (CRITICAL!):**

FOR EVERY CONTACT YOU FIND - YOU MUST:
1. Search for their LinkedIn profile: "[Full Name] [Company] LinkedIn"
2. FETCH the LinkedIn profile page: fetch_and_read_page(linkedin.com/in/[name])
3. Extract location field from profile
4. Assign priority score based on location (1.0 / 0.8 / 0.5)
5. Save contact WITH location data

[WARNING] DO NOT report any contact without attempting location extraction!

**EXAMPLE WORKFLOW:**
Found: "Priya Sharma - HR Manager at TCS"
→ Step 1: Search "Priya Sharma TCS LinkedIn"
→ Step 2: fetch_and_read_page(linkedin.com/in/priya-sharma-xyz)
→ Step 3: Extract "Chennai, Tamil Nadu, India" from profile
→ Step 4: Assign priority_score = 1.0
→ Step 5: Report contact WITH location

**If LinkedIn profile doesn't exist or is blocked:**
→ Mark location = "Unknown", priority = 0.5
→ Still report the contact (better than nothing)

**IMPORTANT:**
- If you find 3 recruiters in Chennai, DON'T waste time on US/UK recruiters
- Location extraction is NOT optional - it's MANDATORY for every contact
- Sort your final results by priority score

==============================================================================
TARGET ROLES
==============================================================================

**PRIMARY TARGETS:**
- Talent Acquisition Managers
- Technical Recruiters (especially for tech/engineering roles)
- HR Business Partners
- Recruiting Coordinators
- Engineering Hiring Managers

**SKIP (for companies >20 employees):**
- Ex-employees ("Former", "Previous", "Left", "Alumni")
- Non-hiring roles (CFO, CTO, VP Sales) unless company ≤20 employees

==============================================================================
HOW EMAIL SOURCES WORK (Read this first!)
==============================================================================

WHERE EMAILS APPEAR:

1. **Search Snippets** (Google/Serper results)
   - Generic emails (hr@, careers@, info@) often visible in snippet text
   - Personal emails (vidya@, arun.prasad@) rarely visible in snippet
   - Tool auto-saves ANY email found in snippets!

2. **People Directories** (unifers.ai, rocketreach.co, contactout.com)
   - Personal emails ALWAYS available, but need page fetch
   - Snippet text shows name/company but NOT the email
   - YOU MUST: fetch_and_read_page(url) to extract the email
   - WARNING: Data is 6-12 months stale (may include ex-employees)

3. **LinkedIn** (linkedin.com/in, linkedin.com/posts)
   - Posts/comments sometimes contain emails in post content
   - Profile snippets NEVER contain emails (LinkedIn privacy)
   - YOU MUST: fetch_and_read_page(url) on posts/profiles to find emails

4. **Company Career Pages** (company.com/careers)
   - Generic emails only (careers@, hr@)
   - Personal recruiter emails never listed
   - Good fallback source

==============================================================================
[WARNING] CRITICAL: WHEN TO FETCH PAGES (YOU MUST READ THIS!)
==============================================================================

**THE #1 REASON AGENTS FAIL: NOT FETCHING THIRD-PARTY PROFILE PAGES!**

ALWAYS FETCH these URL patterns (NO EXCEPTIONS!):

[YES] **unifers.ai/person/...** 
   - Snippet says "Email available" but WON'T show the actual email
   - YOU MUST: fetch_and_read_page(url) to get the email
   - EXAMPLE: unifers.ai/person/priya-sharma-mindpro → Fetch to get priya@mindpro.com

[YES] **rocketreach.co/...-email_...**
   - Snippet shows name but NOT the email (paywall teaser)
   - YOU MUST: fetch_and_read_page(url) to extract email
   - May be blocked (HTTP 403) → Try unifers.ai as backup

[YES] **contactout.com/...**
   - Same as above - email on page, not in snippet
   - YOU MUST: fetch_and_read_page(url)

[YES] **signalhire.com/...**
   - Personal email on page (not in snippet)
   - YOU MUST: fetch_and_read_page(url)

[YES] **linkedin.com/posts/[name]/...**
   - May have email in post content
   - Snippet doesn't show full post → YOU MUST fetch

[NO] **linkedin.com/in/[name]** - DON'T FETCH FOR EMAIL SEARCH!
   - LinkedIn profiles DO NOT show emails (LinkedIn blocks them)
   - SKIP profiles during Phase 2 (email search)
   - Only fetch if verifying employment status AFTER finding email

[NO] DON'T FETCH:
- Generic news articles
- Job boards (unless they show contact email in snippet)
- Company about pages (use careers pages instead)
- Social media (except LinkedIn)

[YES] **linkedin.com/posts/[name]/...**
   - May have email in post content
   - Snippet doesn't show full post → YOU MUST fetch

� **linkedin.com/in/[name]** - DON'T FETCH FOR EMAIL SEARCH!
   - LinkedIn profiles DO NOT show emails (LinkedIn blocks them)
   - SKIP profiles during Phase 2 (email search)
   - Only fetch if verifying employment status AFTER finding email

[NO] DON'T FETCH:
- Generic news articles
- Job boards (unless they show contact email in snippet)
- Company about pages (use careers pages instead)
- Social media (except LinkedIn)

[TARGET] **GOLDEN RULE:**
**If search result is from unifers.ai, rocketreach.co, contactout.com, or signalhire.com or similar websites:**
   → **ALWAYS fetch_and_read_page(url) - NO EXCEPTIONS!**
   → These sites have the emails, but NOT in search snippets
   → Fetching is MANDATORY to get the actual email address

==============================================================================
[SHIELD] HANDLING BLOCKED WEBSITES (HTTP 403, Cloudflare, etc.)
==============================================================================

**Expected Behavior:**
- RocketReach blocks ~90% of requests (anti-bot protection)
- SignalHire uses Cloudflare challenges
- Some LinkedIn profiles may be restricted

**Your Response Strategy:**

IF FETCH BLOCKED (HTTP 403, Cloudflare, Timeout):
[NO] DON'T: Give up and move to next contact
[YES] DO: Try alternative sources for SAME person

**Fallback Sequence for Each Person:**
1. Try RocketReach: rocketreach.co/[person]-email_[id]
   → Blocked (HTTP 403)? → TRY NEXT SOURCE
   
2. Try unifers.ai: unifers.ai/person/[name]-[company]
   → Blocked? → TRY NEXT SOURCE
   
3. Try LinkedIn profile: linkedin.com/in/[name]
   → Blocked? → TRY NEXT SOURCE
   
4. Try LinkedIn post search: site:linkedin.com/posts "[name]" "[company]" "@"
   → No email? → TRY NEXT SOURCE

5. Try contactout.com search
   → Still blocked? → MARK AS INSUFFICIENT DATA

**Rule: Try at least 3 alternative sources before giving up on a person**

**Example - Good Resilience:**
Found: "Divya Anbazhagan - Recruiter at Kitron"
→ Try: rocketreach.co/divya-anbazhagan-email_123 → HTTP 403 [NO]
→ Try: unifers.ai/person/divya-anbazhagan-kitron → Success! Email found [YES]
→ Try: linkedin.com/in/divya-anbazhagan → Extract location [YES]
→ Result: divya.anbazhagan@kitron.com with Chennai location

**Example - Poor Resilience (DON'T DO THIS):**
Found: "Divya Anbazhagan"
→ Try: rocketreach → HTTP 403 [NO]
→ Give up → Move to next person [NO] WRONG! Try unifers.ai next!

**Key Point: Website blocks are EXPECTED and NORMAL. Don't let them stop you!**

==============================================================================
==============================================================================
THREE-PHASE SEARCH STRATEGY (Execute in Order):
==============================================================================

🚫 BLACKLISTED SITES (DO NOT TRY - WASTE OF TIME!)
------------------------------
❌ **rocketreach.co** - ALWAYS 403 blocked, 0% success rate, SKIP ENTIRELY
❌ **crunchbase.com** - Cloudflare protection, skip
❌ **apollo.io** - Login required, skip
❌ **zoominfo.com** - Paywall, skip

✅ **USE THESE INSTEAD:**
- **unifers.ai** (reliable, works great!) ⭐ BEST SOURCE!
- **LinkedIn posts/profiles** (often have emails in posts)
- **Company websites directly**
- **Search snippets** (sometimes contain emails)

==============================================================================

PHASE 1: FIND RECRUITER NAMES
------------------------------
Goal: Identify WHO the recruiters are at {company_name}

Search queries:
- "{company_name} recruiter LinkedIn"
- "{company_name} talent acquisition team"
- site:linkedin.com/in "{company_name}" recruiter
- "{company_name} HR team hiring manager"

Extract names from results:
- "Arun Prasad - Recruiter at {company_name}" → Extract: "Arun Prasad"
- "Vidya Kannan | HR @ {company_name}" → Extract: "Vidya Kannan"

SKIP anyone with: "Ex-", "Former", "Previous", "Left", "Alumni"

TARGET: Find 2-4 recruiter names, then move to Phase 2



PHASE 2: FIND PERSONAL EMAILS (MANDATORY for each name!)
-----------------------------------------------------------
CRITICAL: For EVERY name from Phase 1, search for their email!

[WARNING] **IMPORTANT: WHERE EMAILS ARE ACTUALLY FOUND**
   
   [NO] **LinkedIn PROFILES** (linkedin.com/in/...) → NO EMAILS!
      - Profiles don't show emails (LinkedIn blocks them)
      - DON'T waste time fetching profiles unless checking employment status!
   
   [YES] **LinkedIn POSTS** (linkedin.com/posts/...) → YES, EMAILS HERE!
      - Indian recruiters POST emails in #hiring announcements
      - Example: "We're hiring! DM or email arun@company.com"
      - YOU MUST: fetch_and_read_page(post_url) to extract email!
   
   [YES] **Third-party sites** (unifers.ai) → YES, EMAILS HERE! ⭐ BEST!
      - unifers.ai SCRAPES LinkedIn posts and extracts emails
      - Snippet shows teaser: "Email available" but NOT the actual email
      - YOU MUST: fetch_and_read_page(unifers_url) to get the email!
      - NOTE: RocketReach is BLOCKED (403) - don't waste time, use unifers.ai instead!

**SEARCH STRATEGY:**

HIGH-PRECISION QUERY (use {short_name}):
   \"[FirstName]\" \"[LastName]\" \"{short_name}\" \"@\"

WHY SHORT NAME?
   BAD: \"Vidya\" \"Kannan\" \"Neoware Technologies\" \"@\" → 0 results
   GOOD: \"Vidya\" \"Kannan\" \"Neoware\" \"@\" → 10+ results
   
   The short name removes restrictive suffixes (Technologies, Solutions, etc.)

Examples:
- Found \"Vidya Kannan\" → Search: \"Vidya\" \"Kannan\" \"{short_name}\" \"@\"
- Found \"Arun Prasad\" → Search: \"Arun\" \"Prasad\" \"{short_name}\" \"@\"

**WHAT YOU'LL FIND:**

1. **LinkedIn POSTS** (linkedin.com/posts/...)
   - Recruiter posted #hiring announcement with email
   - Snippet WON'T show email (too long)
   - YOU MUST: fetch_and_read_page(url) → Find email in post text!

2. **Third-party profiles** (unifers.ai/person/...) ⭐ BEST!
   - Snippet: "Email available" or "Contact available"
   - Snippet WON'T show actual email (paywall teaser)
   - YOU MUST: fetch_and_read_page(url) → Get the email!
   - ❌ NOTE: DON'T use rocketreach.co (always 403 blocked)

3. **Occasionally in search snippets**
   - Sometimes email appears directly in snippet
   - Tool already extracted it for you
   - Check the emails list in search results!

**ALTERNATIVE QUERIES** (if first fails):
- site:linkedin.com/posts \"[FirstName LastName]\" \"{short_name}\" \"@\"
- \"[FirstName LastName] {short_name} email\"
- site:unifers.ai \"[FirstName LastName]\" \"{short_name}\"

**KEY LESSON:**
LinkedIn profiles = waste of time for emails (no emails shown)
LinkedIn posts = goldmine (emails in #hiring announcements)
Third-party sites = aggregated emails from posts

DON'T SKIP Phase 2! This is where personal emails are found!


PHASE 2: FIND PERSONAL EMAILS (MANDATORY for each name!)
--------------------------------------------------
If Phase 1+2 didn't find enough contacts, try these:

WILDCARD SEARCHES (find people missed in Phase 1):
- site:unifers.ai "{company_name}" "@"
- "{company_name}" "@" employee directory
- "{company_name}" "@" LinkedIn profile

GENERIC COMPANY SEARCHES:
- "@{company.domain if company.domain else short_name.lower()}" hiring recruiter
- "{company_name}" careers contact
- site:linkedin.com/posts "{company_name}" hiring "@"

Phase 3 often finds hidden gems in employee directories!

==============================================================================
SUCCESS PATTERNS (Learn from these real examples)
==============================================================================

EXAMPLE 1: Neoware Technologies [SUCCESS]
----------------------------------
Phase 1: "Neoware recruiter LinkedIn"
  → Result: "Vidya Kannan - Associate Manager HR at Neoware"
  → Extracted: "Vidya Kannan"

Phase 2: "Vidya" "Kannan" "Neoware" "@"
  → Result: linkedin.com/posts/vidya-kannan-9838885b_python...
  → Snippet: No email visible
  → ACTION: fetch_and_read_page(url)
  → FOUND: vidya@neoware.ai [SUCCESS]

KEY LESSON: LinkedIn posts need fetching - emails not in snippets!


EXAMPLE 2: Giggso [SUCCESS]
--------------------
Phase 1: "Giggso recruiter LinkedIn"
  → Found names but no emails

Phase 3: site:unifers.ai "Giggso" "@"
  → Result: unifers.ai/person/arun-prasad...
  → Snippet: "Arun Prasad. Giggso. arun.prasad@giggso.com"
  → Auto-saved: arun.prasad@giggso.com [SUCCESS]

KEY LESSON: unifers.ai wildcard search finds people missed in Phase 1!


EXAMPLE 3: Wrong Target [FAILED]
--------------------------
Phase 1: "C4Scale recruiter LinkedIn"
  → Result: "Chakravarthy V P - Founder & CTO at C4Scale"
  → SKIP: He's a founder, NOT a recruiter! [FAILED]

KEY LESSON: Filter by role - founders/CTOs are not hiring personnel (unless ≤20 employees)!


EXAMPLE 4: Stale Data [FAILED]
-------------------------------
Phase 2: Found "Sarah Miller - Recruiter" on unifers.ai
   → fetch_and_read_page(url)
   → Page text: "Former employee (Left company in 2023)"
   → SKIP: Not current employee [FAILED]

KEY LESSON: Check for "Former", "Left", "Ex-" in fetched page content!


EXAMPLE 5: Wrong Domain [FAILED]
---------------------------------
Phase 2: Found email in snippet: recruiter@staffing-agency.com
   → Domain is staffing-agency.com, NOT target company
   → SKIP: External recruiter agency, not company employee [FAILED]

KEY LESSON: Verify email domain matches company domain!

==============================================================================
EMAIL VERIFICATION CHECKLIST
==============================================================================

**BEFORE REPORTING ANY EMAIL, VERIFY:**

[YES] **Domain Match**: Email domain matches company domain
   - For Kitron: only accept @kitron.com emails
   - Reject: @gmail.com, @other-company.com, @recruitment-agency.com

[YES] **Not Generic**: Avoid generic prefixes (unless zero personal emails found)
   - Reject: info@, sales@, support@, contact@, hello@, noreply@
   - Accept as fallback only: hr@, careers@, jobs@, recruiting@, talent@

[YES] **Current Employee**: No indicators of ex-employee
   - Check page content for: "Former", "Previous", "Left", "Ex-", "Alumni"
   - If found near the person's name, SKIP that contact

[YES] **Has Source URL**: Every email must have the URL where it was found
   - Search snippet URL, fetched page URL, or LinkedIn profile URL
   - No source URL = fabricated email = NEVER report it

[YES] **Role Appropriate**: Person's role matches target
   - [YES] For startups (≤20 emp): Founders, CTOs, VPs OK
   - [YES] For all: Recruiters, HR, Talent Acquisition
   - [NO] For large companies: Skip founders/executives

==============================================================================
EXECUTION WORKFLOW
==============================================================================

**PHASE 0: Check Company Size (Do this FIRST)**
Search: "{company_name} LinkedIn company page"
   → Extract employee count
   → Determine if founders are valid contacts

1. PHASE 1: Run 2-3 searches to find recruiter names
   └─> Extract full names from snippets

2. PHASE 2: For EACH name found, run email search + location extraction
   ├─> Use short name: "FirstName" "LastName" "{short_name}" "@"
   ├─> Check results - look for unifers.ai, rocketreach, linkedin URLs
   ├─> FETCH those pages to extract emails
   └─> MANDATORY: Fetch LinkedIn profile for location data

3. PHASE 3: If < 3 contacts, run wildcard searches
   └─> site:unifers.ai "{company_name}" "@" is most effective

4. MINIMUM REQUIREMENTS BEFORE STOPPING:

**You MUST attempt:**
- At least 5 different recruiter name searches (Phase 1)
- At least 3 email source attempts per name found (Phase 2)
  * If RocketReach blocked → Try unifers.ai
  * If unifers.ai blocked → Try LinkedIn
  * Don't give up after one block!
- At least 2 wildcard searches (Phase 3)
- At least 3 LinkedIn profile fetches for location data (MANDATORY)

**Stopping Criteria:**
[YES] GOOD: Found 5+ contacts with location data
[YES] ACCEPTABLE: Found 3-4 contacts with location data + exhausted 10+ queries
[NO] UNACCEPTABLE: Stopped after 2 contacts with only 5 queries

**If blocked by websites:**
- Don't count blocks as attempts
- Try alternative sources (see Anti-Block Strategy)
- A blocked RocketReach ≠ exhausted search
- Try unifers.ai, LinkedIn, contactout as alternatives

**Remember: Quality over speed, but thoroughness matters!**

==============================================================================
FINAL VALIDATION CHECKLIST (Before Completing)
==============================================================================

**BEFORE REPORTING RESULTS, SELF-CHECK:**

□ **All emails have source URLs** - Every email has the URL where it was found

□ **All domains match target company** - No @gmail.com, @wrong-company.com emails

□ **No generic emails** (unless zero personal emails found)
   - If you only found hr@, careers@ → acceptable as fallback
   - If you have personal emails, prefer those but can include hr@ as extra

□ **No ex-employees** - Check that none say "Former", "Left", "Previous"

□ **Founders only if ≤20 employees** - Did you check company size first?

□ **Location extracted** - Did you extract location from LinkedIn profiles?
   - CRITICAL: Every contact must have location (or "Unknown" if impossible)

□ **Priority scores assigned** - Tamil Nadu (1.0) > India (0.8) > Outside (0.5)

□ **Quality check** - Are these REAL emails you saw, or guesses? (Never guess!)

**If any check fails, review and fix before completing.**

SUCCESS CRITERIA:

□ **Conversion Potential**: Are these contacts likely to respond and schedule interview?
   - Personal emails preferred (firstname.lastname@company.com)
   - Tamil Nadu recruiters prioritized (Chennai, Coimbatore, etc.)
   - Current employees verified (no "Former" in title)
   - hr@, careers@ acceptable as fallback if no personal emails found

□ **Completeness**: Did you extract ALL available data?
   - Every contact has location (or "Unknown" if LinkedIn blocked)
   - Every contact has priority_score (1.0, 0.8, 0.5)
   - Every contact has source_url in evidence

□ **Thoroughness**: Did you exhaust search options?
   - Tried at least 5 recruiter name searches
   - Tried at least 3 sources per person (if first blocked)
   - Fetched at least 3 LinkedIn profiles for location
   - Used anti-block strategy when websites blocked

**Remember: 1 high-quality Chennai recruiter email > 10 generic US emails**
**This determines whether someone gets hired - make it count!**

FINAL TARGET:
[CHECK] 3-5 verified contacts (quality over quantity!)
[CHECK] At least 1-2 personal emails with location (firstname@, name.lastname@)
[CHECK] All emails verified with source URLs
[CHECK] All phases attempted (don't give up after 2 contacts!)
[CHECK] Location data for every contact (mandatory!)

==============================================================================

TOOLS AVAILABLE:

1. **web_search(query)** 
   - Returns search results with any emails found in snippets
   - Emails in snippets include metadata (name, title, classification, context)
   - YOU decide which emails are worth saving (quality control)

2. **fetch_and_read_page(url)** 
   - Fetches page content and extracts emails
   - Returns page text + emails with metadata
   - YOU decide which emails to save based on relevance and authenticity

3. **save_discovered_contacts(contacts)** 
   - **YOU MUST CALL THIS** to save contacts you verified
   - **REQUIRED fields:**
     * email: The email address
     * is_generic: bool (False=personal like chris@, True=generic like careers@)
     * source_url: Where you found it
     * reasoning: WHY this is a good contact (2-3 sentences)
   - **OPTIONAL:** name, title, surrounding_text (context helps validation)
   - Backend validates domain, blocks personal emails (gmail), rejects obvious bad data

**CLASSIFICATION EXAMPLES:**
   ✅ is_generic=False: chris@company.com, priya.sharma@company.com, arun.k@company.com
   ✅ is_generic=True: careers@company.com, hr@company.com, recruiting@company.com

[WARNING] **IMPORTANT BEHAVIORAL CHANGE:**
   - Tools NO LONGER auto-save emails
   - YOU must evaluate each email and decide if it's worth saving
   - YOU must provide is_generic classification (REQUIRED!)
   - YOU must provide reasoning for each contact you save
   - Think: Is this person relevant? Are they still employed? Is the email authentic?

ACCEPTABLE EMAILS:
[OK] Personal: john.doe@company.com, priya.sharma@company.com, arun.prasad@company.com
[OK] Generic (fallback): careers@company.com, hr@company.com, recruiting@company.com, jobs@company.com
[OK] Department: talent@company.com, hiring@company.com
[NO] Junk: noreply@, donotreply@, example.com, test.com, placeholder emails

==============================================================================

START NOW: 
1. First, check company size (PHASE 0)
2. Then execute PHASE 1 to find recruiter names at {company_name}
3. Verify all emails against the checklist before completing
"""

    print(f"[Agent] Starting research task for {company_name}")
    print(f"[Agent] Short name for searches: {short_name}")
    print(f"[Agent] Target: Find 3-5 recruiter/HR contacts")

    # Execute agent with timeout (configurable via RESEARCH_AGENT_TIMEOUT)
    # Increased default to 120s to allow thorough research with location extraction
    import asyncio
    timeout_seconds = int(os.getenv('RESEARCH_AGENT_TIMEOUT', '120'))

    try:
        await asyncio.wait_for(
            agent.ainvoke({
                "messages": [("user", task_prompt)]
            }),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        raise Exception(f"Agent execution timed out after {timeout_seconds} seconds")

    print("[Agent] Completed, parsing results")

    # Refresh session to see committed changes from tools
    db.expire_all()
    
    # Query contacts that were saved
    contacts = db.query(Contact).filter(
        Contact.company_id == company.id,
        Contact.status == 'discovered'
    ).all()

    # Add logging for contact sources
    from app.models.contact import Evidence
    snippet_count = 0
    fetch_count = 0
    
    for c in contacts:
        evidence = db.query(Evidence).filter(Evidence.contact_id == c.id).first()
        if evidence:
            if evidence.source_type == 'search_snippet':
                snippet_count += 1
            elif evidence.source_type == 'page_content':
                fetch_count += 1
    
    print(f"[Agent] Contact Discovery Summary:")
    print(f"[Agent]   - {snippet_count} from search snippets (auto-saved)")
    print(f"[Agent]   - {fetch_count} from fetched pages (people directories/LinkedIn)")
    print(f"[Agent]   - {len(contacts) - snippet_count - fetch_count} from other sources")

    contacts_found = [
        {
            'email': c.email,
            'name': c.name,
            'title': c.title
        }
        for c in contacts
    ]

    print(f"[Agent] Extracted {len(contacts_found)} contacts from database")

    return contacts_found

