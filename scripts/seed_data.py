"""
Seed Data Script
Populates the database with initial data (users, technicians, SLA config, etc.)
Matches the actual schema in db/schema.sql
"""

import os
import sys
import hashlib
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import PostgresDB


def hash_password(password):
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_data():
    """Populate database with seed data"""
    
    print("=" * 60)
    print("SEED DATA SCRIPT")
    print("=" * 60)
    
    try:
        print("\n🔄 Connecting to database...")
        db = PostgresDB()
        
        # ==========================================
        # SEED USERS
        # Schema: id, name, email, password_hash, department, role
        # ==========================================
        print("\n👤 Seeding users...")
        users = [
            ('USR-001', 'Admin User', 'admin@company.com', hash_password('admin123'), 'IT', 'admin'),
            ('USR-002', 'John Doe', 'john.doe@company.com', hash_password('user123'), 'Engineering', 'user'),
            ('USR-003', 'Jane Smith', 'jane.smith@company.com', hash_password('user123'), 'Marketing', 'user'),
            ('USR-004', 'Mike Wilson', 'mike.wilson@company.com', hash_password('user123'), 'Sales', 'user'),
            ('USR-005', 'Sarah Johnson', 'sarah.johnson@company.com', hash_password('user123'), 'HR', 'user'),
        ]
        
        for user in users:
            try:
                db.execute_query("""
                    INSERT INTO users (id, name, email, password_hash, department, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        password_hash = EXCLUDED.password_hash,
                        department = EXCLUDED.department,
                        role = EXCLUDED.role
                """, user)
                print(f"   ✓ User: {user[1]} ({user[5]})")
            except Exception as e:
                print(f"   ⚠ Error with user {user[1]}: {e}")
        
        # ==========================================
        # SEED TECHNICIANS
        # Schema: id, name, email, role, department, active_status, assigned_tickets,
        #         resolved_tickets, avg_resolution_time, specialization[], joined_date
        # ==========================================
        print("\n🔧 Seeding technicians...")
        technicians = [
            ('TECH-001', 'Alex Tech', 'alex.tech@company.com', 'L1 Support', 'IT Support', True, 0, 0, '2 hours', ['Hardware', 'Network'], date(2023, 1, 15)),
            ('TECH-002', 'Bob Engineer', 'bob.engineer@company.com', 'L2 Support', 'IT Support', True, 0, 0, '4 hours', ['Software', 'VPN'], date(2023, 3, 1)),
            ('TECH-003', 'Carol Admin', 'carol.admin@company.com', 'System Admin', 'Infrastructure', True, 0, 0, '3 hours', ['Servers', 'Active Directory'], date(2022, 6, 10)),
            ('TECH-004', 'David Senior', 'david.senior@company.com', 'L3 Support', 'IT Support', True, 0, 0, '6 hours', ['Complex Issues', 'Security'], date(2021, 11, 5)),
            ('TECH-005', 'Eve Network', 'eve.network@company.com', 'Network Engineer', 'Infrastructure', True, 0, 0, '5 hours', ['Network', 'VPN', 'Firewalls'], date(2022, 9, 20)),
        ]
        
        for tech in technicians:
            try:
                db.execute_query("""
                    INSERT INTO technicians (id, name, email, role, department, active_status, 
                        assigned_tickets, resolved_tickets, avg_resolution_time, specialization, joined_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        role = EXCLUDED.role,
                        department = EXCLUDED.department,
                        active_status = EXCLUDED.active_status,
                        specialization = EXCLUDED.specialization
                """, tech)
                print(f"   ✓ Technician: {tech[1]} ({tech[3]})")
            except Exception as e:
                print(f"   ⚠ Error with technician {tech[1]}: {e}")
        
        # ==========================================
        # SEED SLA CONFIG
        # Schema: id, priority (Low/Medium/High/Critical), sla_hours, description
        # ==========================================
        print("\n⏰ Seeding SLA configuration...")
        sla_configs = [
            ('SLA-001', 'Critical', 4, 'Critical issues must be resolved within 4 hours'),
            ('SLA-002', 'High', 8, 'High priority issues must be resolved within 8 hours'),
            ('SLA-003', 'Medium', 24, 'Medium priority issues must be resolved within 24 hours'),
            ('SLA-004', 'Low', 72, 'Low priority issues must be resolved within 72 hours'),
        ]
        
        for sla in sla_configs:
            try:
                db.execute_query("""
                    INSERT INTO sla_config (id, priority, sla_hours, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        priority = EXCLUDED.priority,
                        sla_hours = EXCLUDED.sla_hours,
                        description = EXCLUDED.description
                """, sla)
                print(f"   ✓ SLA: {sla[1]} = {sla[2]} hours")
            except Exception as e:
                print(f"   ⚠ Error with SLA {sla[1]}: {e}")
        
        # ==========================================
        # SEED PRIORITY RULES
        # Schema: id, keyword, category, priority (Low/Medium/High/Critical)
        # ==========================================
        print("\n📊 Seeding priority rules...")
        priority_rules = [
            ('RULE-001', 'urgent', None, 'Critical'),
            ('RULE-002', 'emergency', None, 'Critical'),
            ('RULE-003', 'down', None, 'Critical'),
            ('RULE-004', 'not working', None, 'High'),
            ('RULE-005', 'broken', None, 'High'),
            ('RULE-006', 'error', None, 'High'),
            ('RULE-007', 'slow', None, 'Medium'),
            ('RULE-008', 'issue', None, 'Medium'),
            ('RULE-009', 'help', None, 'Low'),
            ('RULE-010', 'question', None, 'Low'),
            ('RULE-011', 'vpn', 'VPN', 'High'),
            ('RULE-012', 'network', 'Network', 'High'),
            ('RULE-013', 'email', 'Email', 'Medium'),
            ('RULE-014', 'password', 'Account', 'Medium'),
        ]
        
        for rule in priority_rules:
            try:
                db.execute_query("""
                    INSERT INTO priority_rules (id, keyword, category, priority)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        keyword = EXCLUDED.keyword,
                        category = EXCLUDED.category,
                        priority = EXCLUDED.priority
                """, rule)
                print(f"   ✓ Rule: '{rule[1]}' → {rule[3]}")
            except Exception as e:
                print(f"   ⚠ Error with rule {rule[1]}: {e}")
        
        # ==========================================
        # SEED KB CATEGORIES
        # Schema: id, name, display_name, icon, display_order, enabled
        # ==========================================
        print("\n📁 Seeding KB categories...")
        kb_categories = [
            ('CAT-001', 'Hardware', 'Hardware Issues', '🖥️', 1, True),
            ('CAT-002', 'Software', 'Software Issues', '💻', 2, True),
            ('CAT-003', 'Network', 'Network & Connectivity', '🌐', 3, True),
            ('CAT-004', 'Account', 'Account & Access', '🔐', 4, True),
            ('CAT-005', 'Email', 'Email Issues', '📧', 5, True),
            ('CAT-006', 'VPN', 'VPN & Remote Access', '🔒', 6, True),
            ('CAT-007', 'Printing', 'Printer Issues', '🖨️', 7, True),
            ('CAT-008', 'Other', 'Other Issues', '❓', 8, True),
        ]
        
        for cat in kb_categories:
            try:
                db.execute_query("""
                    INSERT INTO kb_categories (id, name, display_name, icon, display_order, enabled)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        display_name = EXCLUDED.display_name,
                        icon = EXCLUDED.icon,
                        display_order = EXCLUDED.display_order,
                        enabled = EXCLUDED.enabled
                """, cat)
                print(f"   ✓ Category: {cat[3]} {cat[2]}")
            except Exception as e:
                print(f"   ⚠ Error with category {cat[1]}: {e}")
        
        # ==========================================
        # SEED NOTIFICATION SETTINGS
        # Schema: email_notifications, escalation_time_hours, notify_on_*
        # ==========================================
        print("\n🔔 Seeding notification settings...")
        try:
            # First delete any existing (since id is SERIAL)
            db.execute_query("DELETE FROM notification_settings")
            db.execute_query("""
                INSERT INTO notification_settings (
                    email_notifications, escalation_time_hours, 
                    notify_on_ticket_creation, notify_on_ticket_assignment,
                    notify_on_status_change, notify_on_sla_breach, notify_on_resolution
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (True, 24, True, True, True, True, True))
            print("   ✓ Notification settings configured")
        except Exception as e:
            print(f"   ⚠ Error with notification settings: {e}")
        
        # ==========================================
        # VERIFY
        # ==========================================
        print("\n🔍 Verifying seed data...")
        
        tables = ['users', 'technicians', 'sla_config', 'priority_rules', 'kb_categories', 'notification_settings']
        for table in tables:
            result = db.execute_query(f"SELECT COUNT(*) as cnt FROM {table}", fetch=True)
            count = result[0]['cnt'] if result else 0
            print(f"   {table}: {count} rows")
        
        print("\n" + "=" * 60)
        print("✅ SEED DATA INSERTED SUCCESSFULLY!")
        print("=" * 60)
        print("\nTest credentials:")
        print("  Admin: admin@company.com / admin123")
        print("  User:  john.doe@company.com / user123")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = seed_data()
    sys.exit(0 if success else 1)
