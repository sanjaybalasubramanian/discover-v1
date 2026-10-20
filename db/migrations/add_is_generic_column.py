"""
Add is_generic column to contacts table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.db import engine
from sqlalchemy import text

def add_is_generic_column():
    """Add is_generic column to contacts table"""
    
    print("=" * 60)
    print("ADDING is_generic COLUMN TO CONTACTS")
    print("=" * 60)
    print()
    
    with engine.connect() as conn:
        # Check if column exists
        check_sql = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='contacts' AND column_name='is_generic';
        """)
        
        result = conn.execute(check_sql)
        exists = result.fetchone() is not None
        
        if exists:
            print("✓ Column 'is_generic' already exists")
        else:
            print("Adding column 'is_generic'...")
            
            # Add column
            alter_sql = text("""
            ALTER TABLE contacts 
            ADD COLUMN is_generic BOOLEAN DEFAULT FALSE;
            """)
            
            conn.execute(alter_sql)
            conn.commit()
            
            print("✓ Column 'is_generic' added successfully")
            print()
            print("Default value: FALSE (personal email)")
            print("Usage:")
            print("  - FALSE = Personal email (john@company.com)")
            print("  - TRUE = Generic email (careers@, hr@, info@)")
    
    print()
    print("=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    add_is_generic_column()
