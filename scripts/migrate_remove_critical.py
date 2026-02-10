"""
Migration Script: Remove Critical Priority
Migrates all existing Critical tickets to P2 and removes Critical from DB constraints.
Run this ONCE against the live database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import PostgresDB

def migrate():
    db = PostgresDB()
    
    print("=== Migration: Remove Critical Priority ===\n")
    
    # Step 1: Migrate existing Critical tickets to P2
    print("1. Migrating Critical tickets to P2...")
    count = db.execute_query(
        "UPDATE tickets SET priority = 'P2' WHERE priority = 'Critical'"
    )
    print(f"   Updated {count} tickets from Critical to P2")
    
    # Step 2: Remove Critical SLA config
    print("2. Removing Critical SLA config...")
    count = db.execute_query(
        "DELETE FROM sla_config WHERE priority = 'Critical'"
    )
    print(f"   Deleted {count} SLA config entries")
    
    # Step 3: Update Critical priority rules to P2
    print("3. Updating Critical priority rules to P2...")
    count = db.execute_query(
        "UPDATE priority_rules SET priority = 'P2' WHERE priority = 'Critical'"
    )
    print(f"   Updated {count} priority rules")
    
    # Step 4: Update CHECK constraints
    print("4. Updating CHECK constraints...")
    
    # sla_config
    db.execute_query("ALTER TABLE sla_config DROP CONSTRAINT IF EXISTS sla_config_priority_check")
    db.execute_query("ALTER TABLE sla_config ADD CONSTRAINT sla_config_priority_check CHECK (priority IN ('P4', 'P3', 'P2'))")
    print("   Updated sla_config constraint")
    
    # priority_rules
    db.execute_query("ALTER TABLE priority_rules DROP CONSTRAINT IF EXISTS priority_rules_priority_check")
    db.execute_query("ALTER TABLE priority_rules ADD CONSTRAINT priority_rules_priority_check CHECK (priority IN ('P4', 'P3', 'P2'))")
    print("   Updated priority_rules constraint")
    
    # tickets
    db.execute_query("ALTER TABLE tickets DROP CONSTRAINT IF EXISTS tickets_priority_check")
    db.execute_query("ALTER TABLE tickets ADD CONSTRAINT tickets_priority_check CHECK (priority IN ('P4', 'P3', 'P2'))")
    print("   Updated tickets constraint")
    
    print("\n=== Migration Complete ===")


if __name__ == '__main__':
    migrate()
