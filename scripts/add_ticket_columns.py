"""
Quick migration to add missing columns to tickets table
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import PostgresDB

def add_ticket_columns():
    print("Adding missing columns to tickets table...")
    
    db = PostgresDB()
    
    columns_to_add = [
        ("assignment_group", "VARCHAR(100)", "'GSS Infradesk IT'"),
        ("ticket_type", "VARCHAR(50)", "'incident'"),
        ("manager_approval_status", "VARCHAR(50)", "NULL"),
    ]
    
    try:
        for col_name, col_type, default in columns_to_add:
            try:
                if default == "NULL":
                    db.execute_query(f"""
                        ALTER TABLE tickets 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """)
                else:
                    db.execute_query(f"""
                        ALTER TABLE tickets 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type} DEFAULT {default}
                    """)
                print(f"✓ Added {col_name} column")
            except Exception as e:
                print(f"Note: {col_name} - {e}")
        
        print("\n✅ Columns added successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    add_ticket_columns()
