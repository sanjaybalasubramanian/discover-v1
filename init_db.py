#!/usr/bin/env python3
"""
Initialize the database with schema
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

def init_db():
    """Initialize database with schema"""
    print("Initializing database...")
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Load and execute schema files
        db_dir = Path(__file__).parent / 'db'
        
        for schema_file in ['schema.sql', 'schema_part2.sql']:
            file_path = db_dir / schema_file
            if not file_path.exists():
                print(f"WARNING: {schema_file} not found")
                continue
            
            print(f"Executing {schema_file}...")
            with open(file_path, 'r') as f:
                sql = f.read()
                cur.execute(sql)
        
        conn.commit()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    init_db()
