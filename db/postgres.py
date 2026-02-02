"""
PostgreSQL database helper class with connection pooling
Updated for new dashboard-integrated schema
"""
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2 import pool
from contextlib import contextmanager
from config import config
import logging
import threading
import uuid
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_id(prefix):
    """Generate a unique ID with prefix"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


class PostgresDB:
    """PostgreSQL database helper class with connection pooling"""

    _pool = None
    _pool_lock = threading.Lock()

    def __init__(self):
        self.connection_params = {
            'host': config.POSTGRES_HOST,
            'port': config.POSTGRES_PORT,
            'database': config.POSTGRES_DB,
            'user': config.POSTGRES_USER,
            'password': config.POSTGRES_PASSWORD
        }
        self._ensure_pool()

    def _ensure_pool(self):
        with self._pool_lock:
            if PostgresDB._pool is None:
                PostgresDB._pool = pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    **self.connection_params
                )
                logger.info("PostgreSQL connection pool initialized")

    @contextmanager
    def get_connection(self):
        self._ensure_pool()
        conn = None
        try:
            conn = PostgresDB._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                PostgresDB._pool.putconn(conn)
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a query and optionally fetch results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                if fetch:
                    return cur.fetchall()
                return cur.rowcount
    
    def execute_one(self, query, params=None):
        """Execute a query and fetch one result"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                return cur.fetchone()
    
    def initialize_schema(self):
        """Initialize database schema only if tables don't exist (preserves existing data)"""
        try:
            # Check if tables already exist
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('users', 'tickets', 'technicians')
                    """)
                    result = cur.fetchone()
                    tables_exist = result[0] >= 3 if result else False
            
            if tables_exist:
                logger.info("Database tables already exist - skipping schema initialization to preserve data")
                return
            
            # Tables don't exist, create them
            logger.info("Creating database tables for the first time...")
            with open('db/schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema)
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    def reset_database(self):
        """Drop all tables and reinitialize schema"""
        try:
            with open('db/schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema)
            
            logger.info("Database reset and reinitialized successfully")
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise

    # ==========================================
    # User Methods
    # ==========================================
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        return self.execute_one(query, (user_id,))
    
    def get_user_by_email(self, email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        return self.execute_one(query, (email,))
    
    def create_user(self, name, email, password_hash=None, role='user', department=None):
        """Create a new user"""
        try:
            user_id = generate_id('USR')
            query = """
                INSERT INTO users (id, name, email, password_hash, role, department)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            result = self.execute_one(query, (user_id, name, email, password_hash, role, department))
            return result
        except Exception as e:
            logger.error(f"Error creating user {email}: {type(e).__name__}: {e}")
            raise
    
    def get_or_create_user(self, name, email, department=None):
        """Get existing user or create new one"""
        user = self.get_user_by_email(email)
        if user:
            return user
        return self.create_user(name, email, department=department)
    
    def user_exists(self, email):
        """Check if user exists by email"""
        query = "SELECT COUNT(*) as count FROM users WHERE email = %s"
        result = self.execute_one(query, (email,))
        return result['count'] > 0 if result else False
    
    def get_all_users(self):
        """Get all users"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        return self.execute_query(query, fetch=True)

    # ==========================================
    # Technician Methods
    # ==========================================
    def get_all_technicians(self):
        """Get all technicians"""
        query = "SELECT * FROM technicians ORDER BY name"
        return self.execute_query(query, fetch=True)
    
    def get_active_technicians(self):
        """Get active technicians"""
        query = "SELECT * FROM technicians WHERE active_status = true ORDER BY assigned_tickets ASC"
        return self.execute_query(query, fetch=True)
    
    def get_technician_by_id(self, tech_id):
        """Get technician by ID"""
        query = "SELECT * FROM technicians WHERE id = %s"
        return self.execute_one(query, (tech_id,))
    
    def create_technician(self, name, email, role, department='IT Support', specialization=None, joined_date=None):
        """Create a new technician"""
        tech_id = generate_id('TECH')
        joined_date = joined_date or datetime.now().date()
        query = """
            INSERT INTO technicians (id, name, email, role, department, specialization, joined_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_one(query, (tech_id, name, email, role, department, specialization, joined_date))
    
    def update_technician(self, tech_id, **kwargs):
        """Update technician fields"""
        allowed_fields = ['name', 'email', 'role', 'department', 'active_status', 'specialization']
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                values.append(value)
        
        if not updates:
            return None
        
        values.append(tech_id)
        query = f"""
            UPDATE technicians SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING *
        """
        return self.execute_one(query, tuple(values))
    
    def increment_technician_stats(self, tech_id, assigned=0, resolved=0):
        """Increment technician statistics"""
        query = """
            UPDATE technicians 
            SET assigned_tickets = assigned_tickets + %s,
                resolved_tickets = resolved_tickets + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self.execute_query(query, (assigned, resolved, tech_id))

    # ==========================================
    # Ticket Methods
    # ==========================================
    def create_ticket(self, user_id, user_name, user_email, category, subject, description,
                      subcategory=None, priority='Medium', session_id=None):
        """Create a new ticket with auto-priority and SLA"""
        ticket_id = generate_id('TKT')
        
        # Auto-determine priority based on rules
        priority = self.determine_priority(subject, description, category) or priority
        
        # Calculate SLA deadline
        sla_deadline = self.calculate_sla_deadline(priority)
        
        query = """
            INSERT INTO tickets (id, user_id, user_name, user_email, category, subcategory,
                                 priority, status, subject, description, sla_deadline, chatbot_session_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Open', %s, %s, %s, %s)
            RETURNING *
        """
        result = self.execute_one(query, (ticket_id, user_id, user_name, user_email, category,
                                          subcategory, priority, subject, description, sla_deadline, session_id))
        
        # Create audit log
        if result:
            self.create_audit_log('Ticket Created', ticket_id, user_id, user_name,
                                  f"New ticket created: {subject}")
        
        return result
    
    def get_ticket_by_id(self, ticket_id):
        """Get ticket by ID"""
        query = "SELECT * FROM tickets WHERE id = %s"
        return self.execute_one(query, (ticket_id,))
    
    def get_user_tickets(self, user_id):
        """Get all tickets for a user"""
        query = """
            SELECT t.*, tech.name as technician_name
            FROM tickets t
            LEFT JOIN technicians tech ON t.assigned_to_id = tech.id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
        """
        return self.execute_query(query, (user_id,), fetch=True)
    
    def get_all_tickets(self, status=None, priority=None, category=None, limit=100):
        """Get all tickets with optional filters"""
        query = """
            SELECT t.*, tech.name as technician_name
            FROM tickets t
            LEFT JOIN technicians tech ON t.assigned_to_id = tech.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND t.status = %s"
            params.append(status)
        if priority:
            query += " AND t.priority = %s"
            params.append(priority)
        if category:
            query += " AND t.category = %s"
            params.append(category)
        
        query += " ORDER BY t.created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.execute_query(query, tuple(params), fetch=True)
    
    def update_ticket_status(self, ticket_id, status, user_id=None, user_name=None, resolution_notes=None):
        """Update ticket status"""
        updates = ["status = %s", "updated_at = CURRENT_TIMESTAMP"]
        values = [status]
        
        if status == 'Resolved':
            updates.append("resolved_at = CURRENT_TIMESTAMP")
            if resolution_notes:
                updates.append("resolution_notes = %s")
                values.append(resolution_notes)
        elif status == 'Closed':
            updates.append("closed_at = CURRENT_TIMESTAMP")
        
        values.append(ticket_id)
        query = f"UPDATE tickets SET {', '.join(updates)} WHERE id = %s RETURNING *"
        result = self.execute_one(query, tuple(values))
        
        if result:
            self.create_audit_log(f'Status Changed to {status}', ticket_id, user_id, user_name,
                                  f"Ticket status updated to {status}")
        
        return result
    
    def assign_ticket(self, ticket_id, tech_id, assigner_id=None, assigner_name=None):
        """Assign ticket to technician"""
        tech = self.get_technician_by_id(tech_id)
        if not tech:
            return None
        
        query = """
            UPDATE tickets 
            SET assigned_to_id = %s, assigned_to = %s, status = 'In Progress', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING *
        """
        result = self.execute_one(query, (tech_id, tech['name'], ticket_id))
        
        if result:
            self.increment_technician_stats(tech_id, assigned=1)
            self.create_audit_log('Ticket Assigned', ticket_id, assigner_id, assigner_name,
                                  f"Assigned to {tech['name']}")
        
        return result
    
    def get_sla_breached_tickets(self):
        """Get tickets that have breached SLA"""
        query = """
            SELECT * FROM tickets 
            WHERE sla_breached = true AND status NOT IN ('Resolved', 'Closed')
            ORDER BY sla_deadline ASC
        """
        return self.execute_query(query, fetch=True)
    
    def check_and_update_sla_breaches(self):
        """Check for SLA breaches and update tickets"""
        query = """
            UPDATE tickets 
            SET sla_breached = true, updated_at = CURRENT_TIMESTAMP
            WHERE sla_deadline < CURRENT_TIMESTAMP 
              AND sla_breached = false 
              AND status NOT IN ('Resolved', 'Closed')
            RETURNING id
        """
        return self.execute_query(query, fetch=True)

    # ==========================================
    # SLA Methods
    # ==========================================
    def get_sla_config(self):
        """Get all SLA configurations"""
        query = "SELECT * FROM sla_config ORDER BY sla_hours"
        return self.execute_query(query, fetch=True)
    
    def get_sla_by_priority(self, priority):
        """Get SLA config for a priority"""
        query = "SELECT * FROM sla_config WHERE priority = %s"
        return self.execute_one(query, (priority,))
    
    def update_sla_config(self, sla_id, sla_hours, description=None):
        """Update SLA configuration"""
        query = """
            UPDATE sla_config SET sla_hours = %s, description = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING *
        """
        return self.execute_one(query, (sla_hours, description, sla_id))
    
    def calculate_sla_deadline(self, priority):
        """Calculate SLA deadline based on priority"""
        sla = self.get_sla_by_priority(priority)
        if sla:
            return datetime.now() + timedelta(hours=sla['sla_hours'])
        return datetime.now() + timedelta(hours=24)  # Default 24 hours

    # ==========================================
    # Priority Rules Methods
    # ==========================================
    def get_priority_rules(self):
        """Get all priority rules"""
        query = "SELECT * FROM priority_rules ORDER BY priority DESC"
        return self.execute_query(query, fetch=True)
    
    def create_priority_rule(self, keyword, priority, category=None):
        """Create a new priority rule"""
        rule_id = generate_id('PR')
        query = """
            INSERT INTO priority_rules (id, keyword, category, priority)
            VALUES (%s, %s, %s, %s) RETURNING *
        """
        return self.execute_one(query, (rule_id, keyword.lower(), category, priority))
    
    def delete_priority_rule(self, rule_id):
        """Delete a priority rule"""
        query = "DELETE FROM priority_rules WHERE id = %s"
        return self.execute_query(query, (rule_id,))
    
    def determine_priority(self, subject, description, category=None):
        """Determine priority based on rules"""
        text = f"{subject} {description}".lower()
        rules = self.get_priority_rules()
        
        # Priority order: Critical > High > Medium > Low
        priority_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        max_priority = None
        max_order = 0
        
        for rule in rules:
            if rule['keyword'].lower() in text:
                if rule['category'] and rule['category'] != category:
                    continue
                rule_order = priority_order.get(rule['priority'], 0)
                if rule_order > max_order:
                    max_order = rule_order
                    max_priority = rule['priority']
        
        return max_priority

    # ==========================================
    # Knowledge Base Methods
    # ==========================================
    def get_all_kb_articles(self, enabled_only=True):
        """Get all knowledge base articles"""
        query = "SELECT * FROM knowledge_articles"
        if enabled_only:
            query += " WHERE enabled = true"
        query += " ORDER BY category, title"
        return self.execute_query(query, fetch=True)
    
    def get_kb_article_by_id(self, article_id):
        """Get KB article by ID"""
        query = "SELECT * FROM knowledge_articles WHERE id = %s"
        return self.execute_one(query, (article_id,))
    
    def get_kb_articles_by_category(self, category):
        """Get KB articles by category"""
        query = "SELECT * FROM knowledge_articles WHERE category = %s AND enabled = true ORDER BY title"
        return self.execute_query(query, (category,), fetch=True)
    
    def create_kb_article(self, title, category, solution, subcategory=None, keywords=None, author=None, source=None):
        """Create a new KB article"""
        article_id = generate_id('KB')
        query = """
            INSERT INTO knowledge_articles (id, title, category, subcategory, keywords, solution, author, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_one(query, (article_id, title, category, subcategory, keywords, solution, author, source))
    
    def update_kb_article(self, article_id, **kwargs):
        """Update KB article"""
        allowed_fields = ['title', 'category', 'subcategory', 'keywords', 'solution', 'enabled', 'author', 'source']
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                values.append(value)
        
        if not updates:
            return None
        
        values.append(article_id)
        query = f"""
            UPDATE knowledge_articles SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING *
        """
        return self.execute_one(query, tuple(values))
    
    def delete_kb_article(self, article_id):
        """Delete KB article"""
        query = "DELETE FROM knowledge_articles WHERE id = %s"
        return self.execute_query(query, (article_id,))
    
    def increment_kb_views(self, article_id):
        """Increment article view count"""
        query = "UPDATE knowledge_articles SET views = views + 1 WHERE id = %s"
        self.execute_query(query, (article_id,))
    
    def update_kb_helpful(self, article_id, helpful=True):
        """Update helpful/not helpful count"""
        field = 'helpful' if helpful else 'not_helpful'
        query = f"UPDATE knowledge_articles SET {field} = {field} + 1 WHERE id = %s"
        self.execute_query(query, (article_id,))

    # ==========================================
    # KB Categories Methods
    # ==========================================
    def get_kb_categories(self, enabled_only=True):
        """Get all KB categories"""
        query = "SELECT * FROM kb_categories"
        if enabled_only:
            query += " WHERE enabled = true"
        query += " ORDER BY display_order"
        return self.execute_query(query, fetch=True)
    
    def get_kb_category_by_name(self, name):
        """Get category by name"""
        query = "SELECT * FROM kb_categories WHERE name = %s"
        return self.execute_one(query, (name,))

    # ==========================================
    # Audit Log Methods
    # ==========================================
    def create_audit_log(self, action, ticket_id=None, user_id=None, user_name=None, details=None, ip_address=None):
        """Create an audit log entry"""
        log_id = generate_id('LOG')
        query = """
            INSERT INTO audit_logs (id, action, ticket_id, user_id, user_name, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, (log_id, action, ticket_id, user_id, user_name, details, ip_address))
    
    def get_audit_logs(self, ticket_id=None, limit=100):
        """Get audit logs"""
        if ticket_id:
            query = "SELECT * FROM audit_logs WHERE ticket_id = %s ORDER BY timestamp DESC LIMIT %s"
            return self.execute_query(query, (ticket_id, limit), fetch=True)
        else:
            query = "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT %s"
            return self.execute_query(query, (limit,), fetch=True)

    # ==========================================
    # Notification Settings Methods
    # ==========================================
    def get_notification_settings(self):
        """Get notification settings"""
        query = "SELECT * FROM notification_settings LIMIT 1"
        return self.execute_one(query)
    
    def update_notification_settings(self, **kwargs):
        """Update notification settings"""
        allowed_fields = ['email_notifications', 'escalation_time_hours', 'notify_on_ticket_creation',
                         'notify_on_ticket_assignment', 'notify_on_status_change', 'notify_on_sla_breach',
                         'notify_on_resolution']
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                values.append(value)
        
        if not updates:
            return None
        
        query = f"UPDATE notification_settings SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP RETURNING *"
        return self.execute_one(query, tuple(values))

    # ==========================================
    # Conversation History Methods
    # ==========================================
    def save_conversation(self, user_id, session_id, message_type, message_content, 
                          buttons_shown=None, button_clicked=None, ticket_id=None):
        """Save conversation to history"""
        query = """
            INSERT INTO conversation_history 
            (user_id, session_id, message_type, message_content, buttons_shown, button_clicked, ticket_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        buttons_json = Json(buttons_shown) if buttons_shown else None
        self.execute_query(query, (user_id, session_id, message_type, message_content, 
                                   buttons_json, button_clicked, ticket_id))
    
    def get_conversation_history(self, session_id):
        """Get conversation history for a session"""
        query = """
            SELECT * FROM conversation_history
            WHERE session_id = %s
            ORDER BY created_at ASC
        """
        return self.execute_query(query, (session_id,), fetch=True)

    # ==========================================
    # Analytics Methods
    # ==========================================
    def get_ticket_stats(self):
        """Get ticket statistics"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN sla_breached = true THEN 1 ELSE 0 END) as sla_breached
            FROM tickets
        """
        return self.execute_one(query)
    
    def get_tickets_by_category(self):
        """Get ticket count by category"""
        query = """
            SELECT category, COUNT(*) as count
            FROM tickets
            GROUP BY category
            ORDER BY count DESC
        """
        return self.execute_query(query, fetch=True)
    
    def get_tickets_by_priority(self):
        """Get ticket count by priority"""
        query = """
            SELECT priority, COUNT(*) as count
            FROM tickets
            GROUP BY priority
            ORDER BY 
                CASE priority 
                    WHEN 'Critical' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    WHEN 'Low' THEN 4 
                END
        """
        return self.execute_query(query, fetch=True)
    
    def get_recent_ticket_trend(self, days=7):
        """Get ticket creation trend for last N days"""
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM tickets
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        return self.execute_query(query, (days,), fetch=True)
    
    def get_technician_workload(self):
        """Get workload per technician"""
        query = """
            SELECT 
                t.id, t.name,
                COUNT(tk.id) as total_assigned,
                SUM(CASE WHEN tk.status = 'Open' THEN 1 ELSE 0 END) as open_tickets,
                SUM(CASE WHEN tk.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                t.resolved_tickets
            FROM technicians t
            LEFT JOIN tickets tk ON t.id = tk.assigned_to_id
            WHERE t.active_status = true
            GROUP BY t.id, t.name, t.resolved_tickets
            ORDER BY total_assigned DESC
        """
        return self.execute_query(query, fetch=True)


# Global database instance
db = PostgresDB()