#!/usr/bin/env python
"""
Research IntellectDesign Arena Ltd
"""
import asyncio
from app.db import SessionLocal
from app.research.agent import research_company_contacts

async def research_intellectdesign():
    """Research IntellectDesign and show results"""
    
    print("\n" + "=" * 80)
    print("🚀 RESEARCHING: INTELLECTDESIGN ARENA")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        result = await research_company_contacts(
            company_name="IntellectDesign Arena",
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

if __name__ == "__main__":
    asyncio.run(research_intellectdesign())
