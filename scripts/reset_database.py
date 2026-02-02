
"""
Reset Database Script
Drops all tables and recreates them from schema.sql
WARNING: This will delete ALL data!
"""

import os
import sys
import psycopg2
from psycopg2 import sql

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


def reset_database():
    """Drop all tables and recreate from schema.sql"""
    
    print("=" * 60)
    print("DATABASE RESET SCRIPT")
    print("=" * 60)
    print("\n⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print(f"Database: {Config.POSTGRES_DB}")
    print(f"Host: {Config.POSTGRES_HOST}")
    print()
    
    # Confirm action
    confirm = input("Type 'RESET' to confirm: ")
    if confirm != 'RESET':
        print("❌ Aborted. No changes made.")
        return False
    
    conn = None
    cursor = None
    
    try:
        # Connect to database
        print("\n📡 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            database=Config.POSTGRES_DB,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop all tables
        print("🗑️  Dropping existing tables...")
        tables_to_drop = [
            'conversation_history',
            'audit_logs',
            'notification_settings',
            'priority_rules',
            'knowledge_articles',
            'kb_categories',
            'tickets',
            'technicians',
            'sla_config',
            'users'
        ]
        
        for table in tables_to_drop:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql.Identifier(table)
                ))
                print(f"   ✓ Dropped {table}")
            except Exception as e:
                print(f"   ⚠ Warning dropping {table}: {e}")
        
        # Read schema file
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'db', 'schema.sql'
        )
        
        if not os.path.exists(schema_path):
            print(f"❌ Schema file not found: {schema_path}")
            return False
        
        print(f"\n📄 Reading schema from {schema_path}...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema
        print("🔨 Creating tables...")
        cursor.execute(schema_sql)
        
        # Verify tables created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"\n✅ Successfully created {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   • {table[0]} ({count} rows)")
        
        print("\n" + "=" * 60)
        print("✅ DATABASE RESET COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run: python scripts/seed_data.py")
        print("  2. Run: python scripts/populate_kb.py")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)
