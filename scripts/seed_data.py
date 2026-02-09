"""
Seed Data Script
Populates the database with initial data (users, technicians, SLA config, etc.)
Updated for P2/P3/P4 priorities and technician shift timings
"""

import os
import sys
import hashlib
from datetime import date, time

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
        # SEED TECHNICIANS (10 technicians with shift timings)
        # Shift 1: 7AM-4PM (4 technicians)
        # Shift 2: 2PM-11PM (3 technicians)
        # Shift 3: 7PM-4AM (3 technicians)
        # ==========================================
        print("\n🔧 Seeding technicians with shift timings...")
        technicians = [
            # Shift 1: 7AM-4PM (4 technicians)
            ('TECH-001', 'Vinodh Kumar', 'vinodh.kumar@company.com', 'L1 Support', 'IT Support', True, 0, 0, '2 hours', ['Windows', 'Email', 'VPN'], time(7, 0), time(16, 0), date(2024, 1, 15)),
            ('TECH-002', 'Shyam Sundhar', 'shyam.sundhar@company.com', 'L1 Support', 'IT Support', True, 0, 0, '2 hours', ['Hardware', 'Software', 'Network'], time(7, 0), time(16, 0), date(2024, 2, 1)),
            ('TECH-003', 'Jayachandran', 'jayachandran@company.com', 'L2 Support', 'IT Support', True, 0, 0, '4 hours', ['Network', 'Server', 'Security'], time(7, 0), time(16, 0), date(2023, 6, 1)),
            ('TECH-004', 'Kamali', 'kamali@company.com', 'Senior Engineer', 'IT Support', True, 0, 0, '3 hours', ['Infrastructure', 'Cloud', 'Database'], time(7, 0), time(16, 0), date(2022, 3, 20)),
            # Shift 2: 2PM-11PM (3 technicians)
            ('TECH-005', 'Pramodh', 'pramodh@company.com', 'L1 Support', 'IT Support', True, 0, 0, '2 hours', ['Windows', 'Email', 'Zoom'], time(14, 0), time(23, 0), date(2024, 3, 10)),
            ('TECH-006', 'Varshini', 'varshini@company.com', 'L2 Support', 'IT Support', True, 0, 0, '4 hours', ['Software', 'VPN', 'Account'], time(14, 0), time(23, 0), date(2023, 9, 15)),
            ('TECH-007', 'Mugundhan', 'mugundhan@company.com', 'L1 Support', 'IT Support', True, 0, 0, '2 hours', ['Hardware', 'Network', 'Printing'], time(14, 0), time(23, 0), date(2024, 1, 20)),
            # Shift 3: 7PM-4AM (3 technicians)
            ('TECH-008', 'Vikram Anand', 'vikram.anand@company.com', 'L1 Support', 'IT Support', True, 0, 0, '2 hours', ['Windows', 'VPN', 'Email'], time(19, 0), time(4, 0), date(2024, 4, 5)),
            ('TECH-009', 'Parthiban', 'parthiban@company.com', 'L2 Support', 'IT Support', True, 0, 0, '4 hours', ['Server', 'Security', 'Network'], time(19, 0), time(4, 0), date(2023, 11, 1)),
            ('TECH-010', 'Ramesh', 'ramesh@company.com', 'Senior Engineer', 'IT Support', True, 0, 0, '5 hours', ['Infrastructure', 'Database', 'Cloud'], time(19, 0), time(4, 0), date(2022, 8, 15)),
        ]
        
        for tech in technicians:
            try:
                db.execute_query("""
                    INSERT INTO technicians (id, name, email, role, department, active_status, 
                        assigned_tickets, resolved_tickets, avg_resolution_time, specialization, 
                        shift_start, shift_end, joined_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        role = EXCLUDED.role,
                        department = EXCLUDED.department,
                        active_status = EXCLUDED.active_status,
                        specialization = EXCLUDED.specialization,
                        shift_start = EXCLUDED.shift_start,
                        shift_end = EXCLUDED.shift_end
                """, tech)
                shift_str = f"{tech[10].strftime('%I:%M %p')}-{tech[11].strftime('%I:%M %p')}"
                print(f"   ✓ Technician: {tech[1]} ({tech[3]}) - Shift: {shift_str}")
            except Exception as e:
                print(f"   ⚠ Error with technician {tech[1]}: {e}")
        
        # ==========================================
        # SEED SLA CONFIG (P2/P3/P4)
        # P2 = 8 hours, P3 = 72 hours (3 days), P4 = 168 hours (7 days)
        # ==========================================
        print("\n⏰ Seeding SLA configuration (P2/P3/P4)...")
        sla_configs = [
            ('SLA-001', 'Critical', 2, 'Critical - Business-critical issues, 2 hours resolution'),
            ('SLA-002', 'P2', 8, 'P2 - High priority issues, 8 hours resolution'),
            ('SLA-003', 'P3', 72, 'P3 - Medium priority issues, 3 days resolution'),
            ('SLA-004', 'P4', 168, 'P4 - Low priority issues, 7 days resolution'),
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
        # SEED PRIORITY RULES (P2/P3/P4)
        # ==========================================
        print("\n📊 Seeding priority rules (P2/P3/P4)...")
        priority_rules = [
            ('RULE-001', 'urgent', None, 'P2'),
            ('RULE-002', 'emergency', None, 'Critical'),
            ('RULE-003', 'critical', None, 'Critical'),
            ('RULE-004', 'down', None, 'Critical'),
            ('RULE-005', 'not working', None, 'P2'),
            ('RULE-006', 'broken', None, 'P2'),
            ('RULE-007', 'error', None, 'P3'),
            ('RULE-008', 'slow', None, 'P3'),
            ('RULE-009', 'issue', None, 'P3'),
            ('RULE-010', 'help', None, 'P4'),
            ('RULE-011', 'question', None, 'P4'),
            ('RULE-012', 'vpn', 'VPN', 'P2'),
            ('RULE-013', 'network', 'Network', 'P2'),
            ('RULE-014', 'email', 'Email', 'P3'),
            ('RULE-015', 'password', 'Account', 'P3'),
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
        
        # Show technician shift distribution
        print("\n📅 Technician Shift Distribution:")
        shifts = db.execute_query("""
            SELECT shift_start, shift_end, COUNT(*) as count 
            FROM technicians 
            GROUP BY shift_start, shift_end 
            ORDER BY shift_start
        """, fetch=True)
        for shift in shifts:
            start = shift['shift_start']
            end = shift['shift_end']
            count = shift['count']
            print(f"   {start} - {end}: {count} technicians")
        
        print("\n" + "=" * 60)
        print("✅ SEED DATA INSERTED SUCCESSFULLY!")
        print("=" * 60)
        print("\nTest credentials:")
        print("  Admin: admin@company.com / admin123")
        print("  User:  john.doe@company.com / user123")
        print("\nPriority Levels:")
        print("  Critical = 2 hours")
        print("  P2 = 8 hours")
        print("  P3 = 72 hours (3 days)")
        print("  P4 = 168 hours (7 days)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = seed_data()
    sys.exit(0 if success else 1)
