#!/usr/bin/env python
"""
Verify IntellectDesign contacts in database
"""
from app.db import SessionLocal
from app.models.contact import Contact

db = SessionLocal()

print("\n" + "="*80)
print("INTELLECTDESIGN ARENA - DATABASE VERIFICATION")
print("="*80)
print()

contacts = db.query(Contact).filter(Contact.email.like('%intellectdesign%')).all()

if contacts:
    print(f"✅ FOUND {len(contacts)} CONTACT(S) IN DATABASE:")
    print("-"*80)
    for c in contacts:
        print(f"\n📧 Email: {c.email}")
        print(f"   Name: {c.name}")
        print(f"   Title: {c.title}")
        print(f"   is_generic: {c.is_generic} ({'Generic' if c.is_generic else 'Personal'})")
        print(f"   Status: {c.status}")
        print(f"   Created: {c.created_at}")
else:
    print("❌ NO INTELLECTDESIGN CONTACTS FOUND IN DATABASE")

print()
print("="*80)
print()

db.close()
