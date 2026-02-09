"""
Migration script to add missing feedback tables
- solution_feedback: Per-solution helpfulness tracking
- ticket_feedback: End-of-flow rating and comments
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import PostgresDB

def add_feedback_tables():
    print("Adding missing feedback tables...")
    
    db = PostgresDB()
    
    # Create solution_feedback table
    solution_feedback_sql = """
    CREATE TABLE IF NOT EXISTS solution_feedback (
        id SERIAL PRIMARY KEY,
        ticket_id VARCHAR(50) REFERENCES tickets(id),
        session_id VARCHAR(255),
        solution_index INTEGER NOT NULL,
        solution_text TEXT NOT NULL,
        was_helpful BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # Create ticket_feedback table
    ticket_feedback_sql = """
    CREATE TABLE IF NOT EXISTS ticket_feedback (
        id SERIAL PRIMARY KEY,
        ticket_id VARCHAR(50) REFERENCES tickets(id),
        session_id VARCHAR(255),
        flow_type VARCHAR(20) CHECK (flow_type IN ('incident', 'request')),
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        feedback_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_solution_feedback_ticket ON solution_feedback(ticket_id)",
        "CREATE INDEX IF NOT EXISTS idx_solution_feedback_session ON solution_feedback(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_solution_feedback_helpful ON solution_feedback(was_helpful)",
        "CREATE INDEX IF NOT EXISTS idx_ticket_feedback_ticket ON ticket_feedback(ticket_id)",
        "CREATE INDEX IF NOT EXISTS idx_ticket_feedback_session ON ticket_feedback(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_ticket_feedback_rating ON ticket_feedback(rating)"
    ]
    
    try:
        # Create tables
        db.execute_query(solution_feedback_sql)
        print("✓ Created solution_feedback table")
        
        db.execute_query(ticket_feedback_sql)
        print("✓ Created ticket_feedback table")
        
        # Create indexes
        for idx_sql in indexes:
            try:
                db.execute_query(idx_sql)
            except Exception as e:
                pass  # Index may already exist
        print("✓ Created indexes")
        
        print("\n✅ Feedback tables added successfully!")
        print("\nRun \\dt in psql to verify:")
        print("  - solution_feedback")
        print("  - ticket_feedback")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    add_feedback_tables()
