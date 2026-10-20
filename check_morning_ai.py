"""
Check what contacts were found for Morning AI
"""
from app.db import SessionLocal
from app.models import Company
from app.models.contact import Contact

db = SessionLocal()

# Find Morning AI company
company = db.query(Company).filter(Company.name == 'Morning AI').first()

print("\n" + "="*60)
print("MORNING AI - RESEARCH STATUS")
print("="*60)

if not company:
    print("\nNo company record found in database.")
else:
    print(f"\nCompany: {company.name}")
    print(f"Status: {company.research_status}")
    print(f"Research Attempts: {company.research_attempts}")
    print(f"Domain: {company.domain}")
    
    # Get all contacts
    contacts = db.query(Contact).filter(Contact.company_id == company.id).all()
    
    print(f"\nContacts Found: {len(contacts)}")
    print("="*60)
    
    if contacts:
        for i, contact in enumerate(contacts, 1):
            print(f"\n[{i}] {contact.name}")
            print(f"    Email: {contact.email}")
            print(f"    Title: {contact.title}")
            print(f"    Source: {contact.source}")
            print(f"    Priority: {contact.priority_score}")
            print(f"    Type: {contact.contact_type}")
    else:
        print("\nNo contacts saved yet (research timed out or failed)")

print("\n" + "="*60)

db.close()
