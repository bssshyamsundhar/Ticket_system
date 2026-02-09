"""
Quick migration to add shift_start and shift_end columns to technicians table
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import PostgresDB

def add_shift_columns():
    print("Adding shift columns to technicians table...")
    
    db = PostgresDB()
    
    try:
        # Add shift_start column
        db.execute_query("""
            ALTER TABLE technicians 
            ADD COLUMN IF NOT EXISTS shift_start TIME DEFAULT '09:00:00'
        """)
        print("✓ Added shift_start column")
        
        # Add shift_end column
        db.execute_query("""
            ALTER TABLE technicians 
            ADD COLUMN IF NOT EXISTS shift_end TIME DEFAULT '18:00:00'
        """)
        print("✓ Added shift_end column")
        
        print("\n✅ Columns added successfully!")
        print("Now run: python scripts/seed_data.py")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    add_shift_columns()
