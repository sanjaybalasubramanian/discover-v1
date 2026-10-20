#!/usr/bin/env python
"""
Research Neubrain Solutions - Test all fixes live!
"""
import asyncio
from app.db import SessionLocal
from app.research.agent import research_company_contacts

async def research_neubrain():
    """Research Neubrain Solutions and verify all fixes"""
    
    print("\n" + "=" * 80)
    print("🚀 RESEARCHING: NEUBRAIN SOLUTIONS")
    print("=" * 80)
    print()
    print("🔍 This will test all implemented fixes:")
    print("  ✅ URL Cache (no duplicate fetches)")
    print("  ✅ Agent Classification (is_generic parameter)")
    print("  ✅ RocketReach Blacklist (skips blocked sites)")
    print("  ✅ unifers.ai Priority (tries best sources first)")
    print()
    print("-" * 80)
    
    db = SessionLocal()
    
    try:
        result = await research_company_contacts(
            company_name="Neubrain Solutions",
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
                classification = "personal" if not contact.get('is_generic') else "generic"
                print(f"  • {contact['name']} - {contact['email']} ({classification})")
                if contact.get('title'):
                    print(f"    Title: {contact['title']}")
                if contact.get('source'):
                    print(f"    Source: {contact['source']}")
                print()
        
        if result['fallback_contacts']:
            print("📧 FALLBACK CONTACTS:")
            print("-" * 80)
            for contact in result['fallback_contacts']:
                classification = "generic" if contact.get('is_generic') else "personal"
                print(f"  • {contact['name']} - {contact['email']} ({classification})")
                print()
        
        # Query database to verify is_generic field
        from app.models.contact import Contact
        from app.models.company import Company
        
        # Get the company first
        company = db.query(Company).filter(Company.name == "Neubrain Solutions").first()
        if company:
            contacts = db.query(Contact).filter(Contact.company_id == company.id).all()
        else:
            contacts = []
        
        print("=" * 80)
        print("💾 DATABASE VERIFICATION")
        print("=" * 80)
        print(f"Total contacts saved: {len(contacts)}")
        print()
        if contacts:
            print("Classification details:")
            for c in contacts:
                classification = "personal" if not c.is_generic else "generic"
                print(f"  • {c.email} → is_generic={c.is_generic} ({classification})")
        print()
        
        print("=" * 80)
        print("✅ CHECK LOGS ABOVE FOR:")
        print("=" * 80)
        print("  1. [fetch_and_read_page] Cache hit: <url>  ← URL caching works")
        print("  2. No 'rocketreach.co' mentions  ← Blacklist works")
        print("  3. 'unifers.ai' attempts  ← Search optimization works")
        print("  4. Agent provides is_generic values  ← Classification works")
        print()
        
        print("=" * 80)
        print("🎉 RESEARCH COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERROR DURING RESEARCH")
        print("=" * 80)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(research_neubrain())
