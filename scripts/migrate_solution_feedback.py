"""
Migration: Convert solution_feedback.was_helpful (BOOLEAN) to feedback_type (VARCHAR)
Values: 'tried', 'not_tried', 'helpful', 'not_helpful'
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import db

def migrate():
    print("=== Migrating solution_feedback: was_helpful → feedback_type ===")
    
    # Step 1: Add the new column
    print("Step 1: Adding feedback_type column...")
    db.execute_query("""
        ALTER TABLE solution_feedback 
        ADD COLUMN IF NOT EXISTS feedback_type VARCHAR(20) DEFAULT NULL
    """)
    
    # Step 2: Migrate existing data
    print("Step 2: Migrating existing data...")
    db.execute_query("""
        UPDATE solution_feedback 
        SET feedback_type = CASE 
            WHEN was_helpful = true THEN 'helpful'
            WHEN was_helpful = false THEN 'not_helpful'
            ELSE NULL
        END
        WHERE feedback_type IS NULL
    """)
    
    # Step 3: Drop old column and index
    print("Step 3: Dropping old was_helpful column...")
    db.execute_query("DROP INDEX IF EXISTS idx_solution_feedback_helpful")
    db.execute_query("ALTER TABLE solution_feedback DROP COLUMN IF EXISTS was_helpful")
    
    # Step 4: Add new index
    print("Step 4: Creating new index on feedback_type...")
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_solution_feedback_type 
        ON solution_feedback(feedback_type)
    """)
    
    # Step 5: Add CHECK constraint
    print("Step 5: Adding CHECK constraint...")
    try:
        db.execute_query("""
            ALTER TABLE solution_feedback 
            ADD CONSTRAINT chk_feedback_type 
            CHECK (feedback_type IN ('tried', 'not_tried', 'helpful', 'not_helpful'))
        """)
    except Exception as e:
        print(f"  Constraint may already exist: {e}")
    
    print("✅ Migration complete!")

if __name__ == '__main__':
    migrate()
