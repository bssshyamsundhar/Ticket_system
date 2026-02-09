"""Check ticket status constraint"""
import sys
sys.path.insert(0, '.')
from db.postgres import db

result = db.execute_query("""
    SELECT conname, pg_get_constraintdef(c.oid) 
    FROM pg_constraint c 
    JOIN pg_class t ON c.conrelid = t.oid 
    WHERE t.relname = 'tickets' AND c.contype = 'c'
""", fetch=True)
print(f"Result: {result}")
