"""Migration script to add attachment_url column to tickets table"""

import psycopg2
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

def run_migration():
    """Add attachment_url column to tickets table if it doesn't exist"""
    
    conn = psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        database=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD
    )
    
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tickets' AND column_name = 'attachment_url'
        """)
        
        if cursor.fetchone():
            print("✅ Column 'attachment_url' already exists in tickets table")
            return
        
        # Add the column
        cursor.execute("""
            ALTER TABLE tickets 
            ADD COLUMN attachment_url TEXT
        """)
        
        conn.commit()
        print("✅ Successfully added 'attachment_url' column to tickets table")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
