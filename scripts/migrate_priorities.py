"""
Migration Script: Migrate Priorities from High/Medium/Low to P2/P3/P4
Run this script AFTER running reset_database.py if you have existing data
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import PostgresDB


def migrate_priorities():
    """Migrate priority values from old format to new P2/P3/P4 format"""
    
    print("=" * 60)
    print("PRIORITY MIGRATION SCRIPT")
    print("High → P2, Medium → P3, Low → P4")
    print("=" * 60)
    
    try:
        print("\n🔄 Connecting to database...")
        db = PostgresDB()
        
        # Check if there are any tickets with old priority format
        print("\n🔍 Checking for tickets with old priority format...")
        old_tickets = db.execute_query("""
            SELECT COUNT(*) as cnt FROM tickets 
            WHERE priority IN ('High', 'Medium', 'Low')
        """, fetch=True)
        
        old_count = old_tickets[0]['cnt'] if old_tickets else 0
        print(f"   Found {old_count} tickets with old priority format")
        
        if old_count > 0:
            print("\n📝 Migrating ticket priorities...")
            
            # First, drop the CHECK constraint if it exists
            print("   Dropping priority check constraint...")
            try:
                db.execute_query("""
                    ALTER TABLE tickets DROP CONSTRAINT IF EXISTS tickets_priority_check
                """)
                print("   ✓ Constraint dropped")
            except Exception as e:
                print(f"   Note: {e}")
            
            # Migrate High → P2
            result = db.execute_query("""
                UPDATE tickets SET priority = 'P2' WHERE priority = 'High'
            """)
            print("   ✓ High → P2 migrated")
            
            # Migrate Medium → P3
            result = db.execute_query("""
                UPDATE tickets SET priority = 'P3' WHERE priority = 'Medium'
            """)
            print("   ✓ Medium → P3 migrated")
            
            # Migrate Low → P4
            result = db.execute_query("""
                UPDATE tickets SET priority = 'P4' WHERE priority = 'Low'
            """)
            print("   ✓ Low → P4 migrated")
            
            # Re-add the CHECK constraint
            print("   Re-adding priority check constraint...")
            try:
                db.execute_query("""
                    ALTER TABLE tickets ADD CONSTRAINT tickets_priority_check 
                    CHECK (priority IN ('Critical', 'P2', 'P3', 'P4'))
                """)
                print("   ✓ Constraint re-added")
            except Exception as e:
                print(f"   Note: Constraint may already exist: {e}")
        
        # Check SLA config
        print("\n🔍 Checking SLA configuration...")
        old_sla = db.execute_query("""
            SELECT COUNT(*) as cnt FROM sla_config 
            WHERE priority IN ('High', 'Medium', 'Low')
        """, fetch=True)
        
        old_sla_count = old_sla[0]['cnt'] if old_sla else 0
        print(f"   Found {old_sla_count} SLA configs with old priority format")
        
        # Always update SLA config to ensure P2/P3/P4 values
        print("\n📝 Updating SLA configuration...")
        
        # Drop any CHECK constraints on sla_config
        try:
            db.execute_query("""
                ALTER TABLE sla_config DROP CONSTRAINT IF EXISTS sla_config_priority_check
            """)
        except Exception as e:
            pass  # Constraint may not exist
        
        # Clear and reinsert SLA config
        db.execute_query("DELETE FROM sla_config")
        
        sla_configs = [
            ('SLA-001', 'Critical', 2, 'Critical - Business-critical issues, 2 hours resolution'),
            ('SLA-002', 'P2', 8, 'P2 - High priority issues, 8 hours resolution'),
            ('SLA-003', 'P3', 72, 'P3 - Medium priority issues, 3 days resolution'),
            ('SLA-004', 'P4', 168, 'P4 - Low priority issues, 7 days resolution'),
        ]
        
        for sla in sla_configs:
            db.execute_query("""
                INSERT INTO sla_config (id, priority, sla_hours, description)
                VALUES (%s, %s, %s, %s)
            """, sla)
            print(f"   ✓ Inserted SLA: {sla[1]} = {sla[2]} hours")
        
        # Check priority rules
        print("\n🔍 Checking priority rules...")
        old_rules = db.execute_query("""
            SELECT COUNT(*) as cnt FROM priority_rules 
            WHERE priority IN ('High', 'Medium', 'Low')
        """, fetch=True)
        
        old_rules_count = old_rules[0]['cnt'] if old_rules else 0
        print(f"   Found {old_rules_count} priority rules with old format")
        
        if old_rules_count > 0:
            print("\n📝 Migrating priority rules...")
            
            # Drop any CHECK constraints on priority_rules
            try:
                db.execute_query("""
                    ALTER TABLE priority_rules DROP CONSTRAINT IF EXISTS priority_rules_priority_check
                """)
            except Exception as e:
                pass  # Constraint may not exist
            
            # Migrate High → P2
            db.execute_query("""
                UPDATE priority_rules SET priority = 'P2' WHERE priority = 'High'
            """)
            print("   ✓ High → P2 migrated")
            
            # Migrate Medium → P3
            db.execute_query("""
                UPDATE priority_rules SET priority = 'P3' WHERE priority = 'Medium'
            """)
            print("   ✓ Medium → P3 migrated")
            
            # Migrate Low → P4
            db.execute_query("""
                UPDATE priority_rules SET priority = 'P4' WHERE priority = 'Low'
            """)
            print("   ✓ Low → P4 migrated")
            
            # Re-add the CHECK constraint
            try:
                db.execute_query("""
                    ALTER TABLE priority_rules ADD CONSTRAINT priority_rules_priority_check 
                    CHECK (priority IN ('Critical', 'P2', 'P3', 'P4'))
                """)
                print("   ✓ Constraint re-added")
            except Exception as e:
                pass  # Constraint may already exist
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        
        # Check tickets
        new_tickets = db.execute_query("""
            SELECT priority, COUNT(*) as cnt FROM tickets 
            GROUP BY priority ORDER BY priority
        """, fetch=True)
        print("\n   Tickets by priority:")
        if new_tickets:
            for t in new_tickets:
                print(f"     {t['priority']}: {t['cnt']}")
        else:
            print("     No tickets found")
        
        # Check SLA
        new_sla = db.execute_query("""
            SELECT priority, sla_hours FROM sla_config ORDER BY sla_hours
        """, fetch=True)
        print("\n   SLA Configuration:")
        for s in new_sla:
            print(f"     {s['priority']}: {s['sla_hours']} hours")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = migrate_priorities()
    sys.exit(0 if success else 1)
