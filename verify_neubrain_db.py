#!/usr/bin/env python
"""
Verify Neubrain contacts in database
"""
from app.db import SessionLocal
from app.models.contact import Contact

db = SessionLocal()

print("\n" + "="*80)
print("NEUBRAIN SOLUTIONS - DATABASE VERIFICATION")
print("="*80)
print()

contacts = db.query(Contact).filter(Contact.email.like('%neubrain%')).all()

if contacts:
    print(f"✅ FOUND {len(contacts)} CONTACT(S) IN DATABASE:")
    print("-"*80)
    for c in contacts:
        print(f"\n📧 Email: {c.email}")
        print(f"   Name: {c.name}")
        print(f"   is_generic: {c.is_generic} ({'Generic' if c.is_generic else 'Personal'})")
        print(f"   Status: {c.status}")
        print(f"   Created: {c.created_at}")
else:
    print("❌ NO NEUBRAIN CONTACTS FOUND IN DATABASE")

print()
print("="*80)
print()

db.close()
