"""
Migration: Add research tracking columns to runs table
"""
from app.db import engine
from sqlalchemy import text

def run_migration():
    sql = """
    -- Add research tracking columns to runs table
    ALTER TABLE runs 
    ADD COLUMN IF NOT EXISTS companies_researched INTEGER DEFAULT 0;

    ALTER TABLE runs 
    ADD COLUMN IF NOT EXISTS contacts_found INTEGER DEFAULT 0;

    ALTER TABLE runs 
    ADD COLUMN IF NOT EXISTS personal_contacts_found INTEGER DEFAULT 0;

    -- Update existing rows to have default values
    UPDATE runs 
    SET companies_researched = 0 
    WHERE companies_researched IS NULL;

    UPDATE runs 
    SET contacts_found = 0 
    WHERE contacts_found IS NULL;

    UPDATE runs 
    SET personal_contacts_found = 0 
    WHERE personal_contacts_found IS NULL;
    """
    
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    
    print("✅ Migration completed successfully")
    print("   Added columns: companies_researched, contacts_found, personal_contacts_found")

if __name__ == "__main__":
    run_migration()
