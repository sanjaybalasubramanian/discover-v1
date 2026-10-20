#!/usr/bin/env python
"""
Research a well-known company with public HR contacts
"""
import asyncio
from app.db import SessionLocal
from app.research.agent import research_company_contacts

async def research_company(company_name):
    """Research company and show results"""
    
    print("\n" + "=" * 80)
    print(f"🚀 RESEARCHING: {company_name}")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        result = await research_company_contacts(
            company_name=company_name,
            db=db,
            max_contacts=10
        )
        
        print("\n" + "=" * 80)
        print("📊 RESEARCH RESULTS")
        print("=" * 80)
        print(f"Company: {result['company']}")
        print(f"Success: {result['success']}")
        print(f"Total contacts: {result['total_contacts']}")
        print(f"Personal contacts: {len(result['personal_contacts'])}")
        print(f"Fallback contacts: {len(result['fallback_contacts'])}")
        print()
        
        if result['personal_contacts']:
            print("👥 PERSONAL CONTACTS FOUND:")
            print("-" * 80)
            for contact in result['personal_contacts']:
                print(f"  ✅ {contact['name']}")
                print(f"     Email: {contact['email']}")
                print(f"     Generic: {contact.get('is_generic', 'N/A')}")
                if contact.get('title'):
                    print(f"     Title: {contact['title']}")
                if contact.get('source'):
                    print(f"     Source: {contact['source']}")
                print()
        
        if result['fallback_contacts']:
            print("📧 FALLBACK CONTACTS:")
            print("-" * 80)
            for contact in result['fallback_contacts']:
                print(f"  • {contact['name']}")
                print(f"    Email: {contact['email']}")
                print(f"    Generic: {contact.get('is_generic', 'N/A')}")
                print()
        
        if result['total_contacts'] == 0:
            print("❌ NO CONTACTS FOUND")
            print()
            print("Reasons could be:")
            print("  • Company has limited online presence")
            print("  • Contact databases are blocked (Cloudflare)")
            print("  • No public employee directory")
            print()
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERROR DURING RESEARCH")
        print("=" * 80)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

async def test_multiple_companies():
    """Test with multiple companies to find contacts"""
    
    companies = [
        "neubrain solutions",  # Large company, likely has public data
        "straive",    # Another large company
        "trn digital",      # Tata Consultancy Services
    ]
    
    print("\n" + "=" * 80)
    print("🔍 TESTING MULTIPLE COMPANIES TO FIND CONTACTS")
    print("=" * 80)
    print()
    print("Will try these companies:")
    for i, company in enumerate(companies, 1):
        print(f"  {i}. {company}")
    print()
    
    results = []
    for company in companies:
        result = await research_company(company)
        if result and result['total_contacts'] > 0:
            print(f"\n✅ SUCCESS! Found {result['total_contacts']} contacts for {company}")
            results.append((company, result))
            break  # Stop after first success
        else:
            print(f"\n❌ No contacts for {company}, trying next...")
            print()
    
    if not results:
        print("\n" + "=" * 80)
        print("⚠️  NO CONTACTS FOUND FOR ANY COMPANY")
        print("=" * 80)
        print()
        print("This suggests:")
        print("  • These companies don't have public HR contact data")
        print("  • Contact databases are behind paywalls/blocks")
        print("  • Need to try different sources or companies")
        print()
    else:
        print("\n" + "=" * 80)
        print("🎉 TEST COMPLETE - CONTACTS FOUND!")
        print("=" * 80)
        for company, result in results:
            print(f"\n{company}: {result['total_contacts']} contacts")

if __name__ == "__main__":
    asyncio.run(test_multiple_companies())
