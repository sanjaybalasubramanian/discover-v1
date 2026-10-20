#!/usr/bin/env python
"""
Pre-flight checks before running pipeline
Catches import errors, syntax errors, and missing dependencies
"""
import sys
import subprocess

def run_checks():
    """Run all pre-flight checks"""
    checks_passed = True
    
    print("=" * 60)
    print("🔍 PRE-FLIGHT CHECKS")
    print("=" * 60)
    print()
    
    # 1. Ruff linting
    print("1️⃣  Running Ruff linter...")
    result = subprocess.run(
        ["ruff", "check", "app/", "--select", "F,E", "--ignore", "E501"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("   ✅ No linting errors")
    else:
        print("   ❌ Linting errors found:")
        print(result.stdout)
        checks_passed = False
    print()
    
    # 2. Import checks
    print("2️⃣  Checking imports...")
    critical_imports = [
        ("app.models", "Run, Job, Company"),
        ("app.models.contact", "Contact"),
        ("app.models.outreach", "Outreach, Open"),
        ("app.db", "engine, SessionLocal"),
        ("app.cli", "run_command"),
        ("app.search.jobspy_scraper", "build_jobspy_searches"),
        ("app.research.agent", "research_company_contacts"),
    ]
    
    import_errors = []
    for module, items in critical_imports:
        try:
            exec(f"from {module} import {items}")
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ❌ {module}: {e}")
            import_errors.append((module, str(e)))
            checks_passed = False
    
    if not import_errors:
        print("   ✅ All imports successful")
    print()
    
    # 3. Environment variables
    print("3️⃣  Checking environment variables...")
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "DATABASE_URL",
        "AWS_ACCESS_KEY_ID", 
        "AWS_SECRET_ACCESS_KEY",
        "BEDROCK_MODEL",
        "SERPER_API_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}")
        else:
            print(f"   ❌ {var} MISSING")
            missing_vars.append(var)
            checks_passed = False
    
    if not missing_vars:
        print("   ✅ All required environment variables set")
    print()
    
    # 4. Database connection
    print("4️⃣  Checking database connection...")
    try:
        from app.db import engine
        conn = engine.connect()
        result = conn.execute(__import__('sqlalchemy').text('SELECT 1'))
        result.fetchone()
        conn.close()
        print("   ✅ Database connected")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        checks_passed = False
    print()
    
    # 5. Required tables
    print("5️⃣  Checking database schema...")
    try:
        from sqlalchemy import inspect
        from app.db import engine
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['runs', 'jobs', 'companies', 'contacts']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"   ❌ Missing tables: {', '.join(missing_tables)}")
            checks_passed = False
        else:
            print(f"   ✅ All required tables exist ({len(tables)} total)")
            
        # Check critical columns
        runs_cols = [c['name'] for c in inspector.get_columns('runs')]
        companies_cols = [c['name'] for c in inspector.get_columns('companies')]
        
        if 'phase' not in runs_cols:
            print("   ❌ runs.phase column missing")
            checks_passed = False
        else:
            print("   ✅ runs.phase exists")
            
        if 'research_status' not in companies_cols:
            print("   ❌ companies.research_status column missing")
            checks_passed = False
        else:
            print("   ✅ companies.research_status exists")
            
    except Exception as e:
        print(f"   ❌ Schema check error: {e}")
        checks_passed = False
    print()
    
    # 6. Configuration values
    print("6️⃣  Checking pipeline configuration...")
    config_vars = {
        'JOBSPY_RESULTS_PER_SITE': os.getenv('JOBSPY_RESULTS_PER_SITE', '25'),
        'RESEARCH_COMPANY_LIMIT': os.getenv('RESEARCH_COMPANY_LIMIT', '50'),
        'RESEARCH_PARALLEL_WORKERS': os.getenv('RESEARCH_PARALLEL_WORKERS', '3'),
        'RESEARCH_AGENT_TIMEOUT': os.getenv('RESEARCH_AGENT_TIMEOUT', '60'),
    }
    
    for var, value in config_vars.items():
        print(f"   ✅ {var} = {value}")
    print()
    
    # Final result
    print("=" * 60)
    if checks_passed:
        print("✅ ALL CHECKS PASSED - READY TO RUN")
        print("=" * 60)
        print()
        print("Run pipeline:")
        print("  uv run python -m app.cli run")
        return 0
    else:
        print("❌ CHECKS FAILED - FIX ERRORS BEFORE RUNNING")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(run_checks())
