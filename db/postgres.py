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
from datetime import datetime, timedelta, timezone

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
            'password': config.POSTGRES_PASSWORD,
            'options': '-c TimeZone=UTC'
        }
        self._ensure_pool()
        # Migrate TIMESTAMP columns to TIMESTAMPTZ on first init
        self._migrate_to_timestamptz()

    def _ensure_pool(self):
        with self._pool_lock:
            if PostgresDB._pool is None:
                PostgresDB._pool = pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    **self.connection_params
                )
                logger.info("PostgreSQL connection pool initialized")

    def _migrate_to_timestamptz(self):
        """
        One-time migration: convert all TIMESTAMP WITHOUT TIME ZONE columns to
        TIMESTAMP WITH TIME ZONE (TIMESTAMPTZ).

        IMPORTANT: This uses a SEPARATE connection WITHOUT TimeZone=UTC so that
        PostgreSQL's ALTER TYPE interprets existing naive timestamps using the
        server's native timezone (e.g. Asia/Kolkata).  After the ALTER, the data
        is stored internally as UTC, and subsequent reads through the pool
        (TimeZone=UTC) return proper UTC-aware datetimes.
        """
        # All (table, column) pairs that need migration
        columns_to_migrate = [
            ('tickets', 'sla_deadline'),
            ('tickets', 'created_at'),
            ('tickets', 'updated_at'),
            ('tickets', 'resolved_at'),
            ('tickets', 'closed_at'),
            ('tickets', 'manager_approval_date'),
            ('users', 'created_at'),
            ('users', 'updated_at'),
            ('technicians', 'created_at'),
            ('technicians', 'updated_at'),
            ('sla_config', 'created_at'),
            ('sla_config', 'updated_at'),
            ('priority_rules', 'created_at'),
            ('priority_rules', 'updated_at'),
            ('knowledge_articles', 'created_at'),
            ('knowledge_articles', 'updated_at'),
            ('kb_categories', 'created_at'),
            ('audit_logs', 'timestamp'),
            ('solution_feedback', 'created_at'),
            ('ticket_feedback', 'created_at'),
            ('conversation_history', 'created_at'),
            ('notification_settings', 'updated_at'),
        ]

        # Use a fresh connection WITHOUT TimeZone=UTC so the server's native
        # timezone (e.g. Asia/Kolkata) is used for the TIMESTAMP→TIMESTAMPTZ cast.
        native_params = {
            'host': config.POSTGRES_HOST,
            'port': config.POSTGRES_PORT,
            'database': config.POSTGRES_DB,
            'user': config.POSTGRES_USER,
            'password': config.POSTGRES_PASSWORD,
        }

        try:
            conn = psycopg2.connect(**native_params)
            conn.autocommit = True
            cur = conn.cursor()

            # Check which columns still need migration
            cur.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND data_type = 'timestamp without time zone'
            """)
            existing = set((r[0], r[1]) for r in cur.fetchall())

            migrated = 0
            for table, col in columns_to_migrate:
                if (table, col) in existing:
                    try:
                        cur.execute(
                            f'ALTER TABLE {table} ALTER COLUMN {col} '
                            f'TYPE TIMESTAMPTZ USING {col} AT TIME ZONE current_setting(\'timezone\')'
                        )
                        migrated += 1
                    except Exception as col_err:
                        logger.warning(f"Could not migrate {table}.{col}: {col_err}")

            cur.close()
            conn.close()

            if migrated:
                logger.info(f"Timezone migration: converted {migrated} columns from TIMESTAMP to TIMESTAMPTZ")
            else:
                logger.info("Timezone migration: all columns already TIMESTAMPTZ, nothing to do")

        except Exception as e:
            logger.warning(f"Timezone migration skipped (non-fatal): {e}")

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
    
    def create_technician(self, name, email, role, department='IT Support', specialization=None, joined_date=None, shift_start=None, shift_end=None):
        """Create a new technician"""
        tech_id = generate_id('TECH')
        joined_date = joined_date or datetime.now().date()
        query = """
            INSERT INTO technicians (id, name, email, role, department, specialization, joined_date, shift_start, shift_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_one(query, (tech_id, name, email, role, department, specialization, joined_date, shift_start, shift_end))
    
    def update_technician(self, tech_id, **kwargs):
        """Update technician fields"""
        allowed_fields = ['name', 'email', 'role', 'department', 'active_status', 'specialization', 'shift_start', 'shift_end']
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
    
    def delete_technician(self, tech_id):
        """Delete a technician by ID. Unassigns their tickets first."""
        # Unassign tickets from this technician
        self.execute_query(
            "UPDATE tickets SET assigned_to_id = NULL, assigned_to = NULL WHERE assigned_to_id = %s",
            (tech_id,)
        )
        query = "DELETE FROM technicians WHERE id = %s"
        return self.execute_query(query, (tech_id,))
    
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

    def get_on_shift_technician_round_robin(self):
        """Get next technician for strict round-robin assignment based on current shift.
        
        Finds active technicians whose shift covers the current IST time,
        then picks the one who was assigned a ticket LEAST RECENTLY (strict turn-based).
        Handles overnight shifts (e.g. 7PM-4AM) where shift_end < shift_start.
        A technician with no recent assignment (NULL last_assigned_at or no tickets) goes first.
        """
        from datetime import datetime, timezone, timedelta
        # Get current IST time
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist).time()
        
        # Strict round-robin: pick the on-shift technician who was assigned longest ago
        # Uses LEFT JOIN on tickets to find the MAX updated_at for assignments
        # Technicians with no assignments go first (NULLS FIRST)
        query = """
            SELECT t.*, 
                   MAX(tk.updated_at) as last_assigned_at
            FROM technicians t
            LEFT JOIN tickets tk ON t.id = tk.assigned_to_id
            WHERE t.active_status = true
              AND t.shift_start IS NOT NULL
              AND t.shift_end IS NOT NULL
              AND (
                    -- Normal shift: e.g. 7AM-4PM
                    (t.shift_start < t.shift_end AND %s >= t.shift_start AND %s < t.shift_end)
                    OR
                    -- Overnight shift: e.g. 7PM-4AM
                    (t.shift_start > t.shift_end AND (%s >= t.shift_start OR %s < t.shift_end))
                  )
            GROUP BY t.id
            ORDER BY last_assigned_at ASC NULLS FIRST, t.id ASC
            LIMIT 1
        """
        return self.execute_one(query, (now_ist, now_ist, now_ist, now_ist))

    def auto_assign_ticket(self, ticket_id):
        """Auto-assign a ticket to the next on-shift technician using round-robin.
        Returns the technician dict if assigned, None otherwise."""
        tech = self.get_on_shift_technician_round_robin()
        if not tech:
            logger.info(f"No on-shift technician available for ticket {ticket_id}")
            return None
        
        query = """
            UPDATE tickets 
            SET assigned_to_id = %s, assigned_to = %s, status = 'In Progress', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING *
        """
        result = self.execute_one(query, (tech['id'], tech['name'], ticket_id))
        
        if result:
            self.increment_technician_stats(tech['id'], assigned=1)
            self.create_audit_log('Auto-Assigned', ticket_id, 'SYSTEM', 'Round Robin',
                                  f"Auto-assigned to {tech['name']} (on-shift, least loaded)")
            logger.info(f"Ticket {ticket_id} auto-assigned to {tech['name']} ({tech['id']})")
        
        return tech

    # ==========================================
    # Ticket Methods
    # ==========================================
    
    def get_assignment_group(self, smart_category):
        """Map smart category to assignment group"""
        # Default mapping - all go to GSS Infradesk IT
        # Can be extended later for other groups based on category
        mapping = {
            'Network Connection Issues': 'GSS Infradesk IT',
            'Operating System Issues': 'GSS Infradesk IT',
            'PC / Laptop / Peripherals / Accessories Issues': 'GSS Infradesk IT',
            'Printer / Scanner / Copier Issues': 'GSS Infradesk IT',
            'Laptop Request': 'GSS Infradesk IT',
            'Modification Request': 'GSS Infradesk IT',
            'Access Request': 'GSS Infradesk IT',
        }
        return mapping.get(smart_category, 'GSS Infradesk IT')
    
    def create_ticket(self, user_id, user_name, user_email, category, subject, description,
                      subcategory=None, priority='P3', session_id=None, attachment_urls=None):
        """Create a new ticket with auto-priority, SLA, and assignment group"""
        ticket_id = generate_id('TKT')
        
        # Auto-determine priority based on rules
        priority = self.determine_priority(subject, description, category) or priority
        
        # Calculate SLA deadline
        sla_deadline = self.calculate_sla_deadline(priority)
        
        # Determine assignment group based on smart category (stored in subcategory)
        assignment_group = self.get_assignment_group(subcategory)
        
        query = """
            INSERT INTO tickets (id, user_id, user_name, user_email, category, subcategory,
                                 priority, status, subject, description, attachment_urls, sla_deadline, chatbot_session_id, assignment_group)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Open', %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        result = self.execute_one(query, (ticket_id, user_id, user_name, user_email, category,
                                          subcategory, priority, subject, description, attachment_urls, sla_deadline, session_id, assignment_group))
        
        # Create audit log
        if result:
            self.create_audit_log('Ticket Created', ticket_id, user_id, user_name,
                                  f"New ticket created: {subject}")
            
            # Auto-assign to on-shift technician via round-robin
            try:
                tech = self.auto_assign_ticket(ticket_id)
                if tech:
                    # Re-fetch ticket with updated assignment
                    result = self.get_ticket_by_id(ticket_id)
            except Exception as assign_err:
                logger.warning(f"Auto-assignment failed for {ticket_id}: {assign_err}")
        
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
        """Calculate SLA deadline based on priority (UTC)"""
        sla = self.get_sla_by_priority(priority)
        if sla:
            return datetime.now(timezone.utc) + timedelta(hours=sla['sla_hours'])
        return datetime.now(timezone.utc) + timedelta(hours=24)  # Default 24 hours

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
        """
        Determine priority based on rules, smart category mapping, and keyword analysis.
        Returns P2, P3, P4, or Critical depending on urgency indicators.
        """
        text = f"{subject} {description}".lower()
        rules = self.get_priority_rules()
        
        # Priority order: P2 > P3 > P4
        priority_order = {'P2': 3, 'P3': 2, 'P4': 1}
        max_priority = None
        max_order = 0
        
        # Check database rules first
        for rule in rules:
            if rule['keyword'].lower() in text:
                if rule['category'] and rule['category'] != category:
                    continue
                rule_order = priority_order.get(rule['priority'], 0)
                if rule_order > max_order:
                    max_order = rule_order
                    max_priority = rule['priority']
        
        # If a high-priority rule matched, return it
        if max_priority and max_order >= 3:  # P2
            return max_priority
        
        # Smart category-based priority mapping
        smart_category_priorities = {
            'Network Connection Issues': 'P2',  # Network issues often affect productivity
            'Operating System Issues': 'P3',    # OS issues vary in severity
            'PC / Laptop / Peripherals / Accessories Issues': 'P3',
            'Printer / Scanner / Copier Issues': 'P4',  # Usually lower priority
        }
        
        if category and category in smart_category_priorities:
            category_priority = smart_category_priorities[category]
            category_order = priority_order.get(category_priority, 0)
            if category_order > max_order:
                max_order = category_order
                max_priority = category_priority
        
        # Extended keyword matching for better priority detection
        p2_keywords = [
            'server down', 'outage', 'all users affected', 'entire department', 
            'production down', 'business critical', 'security breach', 'data loss',
            'system failure', 'complete failure', 'emergency',
            'cannot work', 'blocked', 'unable to access', 'vpn not working',
            'cannot login', 'authentication failed', 'password expired',
            'locked out', 'urgent', 'deadline', 'meeting', 'presentation',
            'network down', 'no internet', 'cannot connect', 'not responding',
            'frozen', 'crashes', 'blue screen', 'boot failure', 'corrupt'
        ]
        
        p4_keywords = [
            'question', 'inquiry', 'when', 'how to', 'information',
            'minor', 'cosmetic', 'font', 'preference', 'suggestion',
            'would like', 'nice to have', 'improvement', 'training'
        ]
        
        # Check for P2 keywords
        for keyword in p2_keywords:
            if keyword in text:
                if max_order < 3:  # Don't downgrade if already P2
                    return 'P2'
        
        # Check for P4 keywords (only if nothing else matched)
        if max_priority is None:
            for keyword in p4_keywords:
                if keyword in text:
                    return 'P4'
        
        # If a rule matched, return it
        if max_priority:
            return max_priority
        
        # Smart default based on category presence
        if category:
            # If category is provided but no high-priority match, assign P3 or P4
            # based on simple heuristics
            import random
            # 60% P3, 40% P4 for variety when no rules match
            return random.choice(['P3', 'P3', 'P3', 'P4', 'P4'])
        
        # Default to P3 for unmatched cases
        return 'P3'

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
        """Get ticket statistics with real-time data including live SLA breach detection"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN (
                    sla_breached = true 
                    OR (sla_deadline IS NOT NULL AND sla_deadline < CURRENT_TIMESTAMP AND status NOT IN ('Resolved', 'Closed'))
                ) THEN 1 ELSE 0 END) as sla_breached,
                SUM(CASE WHEN priority = 'P2' THEN 1 ELSE 0 END) as p2_tickets,
                SUM(CASE WHEN priority = 'P3' THEN 1 ELSE 0 END) as p3_tickets,
                SUM(CASE WHEN priority = 'P4' THEN 1 ELSE 0 END) as p4_tickets,
                SUM(CASE WHEN status = 'Resolved' AND resolved_at >= CURRENT_DATE THEN 1 ELSE 0 END) as resolved_today
            FROM tickets
        """
        return self.execute_one(query)
    
    def get_active_technician_count(self):
        """Get count of technicians currently on shift (real-time based on IST time)"""
        query = """
            SELECT COUNT(*) as count
            FROM technicians
            WHERE active_status = true
            AND shift_start IS NOT NULL AND shift_end IS NOT NULL
            AND (
                CASE 
                    WHEN shift_start <= shift_end THEN
                        (CURRENT_TIME AT TIME ZONE 'Asia/Kolkata')::time BETWEEN shift_start AND shift_end
                    ELSE
                        (CURRENT_TIME AT TIME ZONE 'Asia/Kolkata')::time >= shift_start 
                        OR (CURRENT_TIME AT TIME ZONE 'Asia/Kolkata')::time <= shift_end
                END
            )
        """
        result = self.execute_one(query)
        return result['count'] if result else 0
    
    def get_avg_resolution_time(self):
        """Get average resolution time for resolved tickets"""
        query = """
            SELECT 
                ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600), 1) as avg_hours
            FROM tickets
            WHERE status IN ('Resolved', 'Closed') 
            AND resolved_at IS NOT NULL
        """
        result = self.execute_one(query)
        if result and result['avg_hours'] is not None:
            hours = float(result['avg_hours'])
            if hours >= 24:
                days = hours / 24
                return f"{days:.1f}d"
            return f"{hours:.1f}h"
        return 'N/A'
    
    def get_ticket_trends(self):
        """Get ticket trend comparisons (this week vs last week) for real trend percentages"""
        query = """
            WITH this_week AS (
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved,
                    SUM(CASE WHEN (
                        sla_breached = true 
                        OR (sla_deadline IS NOT NULL AND sla_deadline < CURRENT_TIMESTAMP AND status NOT IN ('Resolved', 'Closed'))
                    ) THEN 1 ELSE 0 END) as sla_breached,
                    SUM(CASE WHEN priority = 'P2' THEN 1 ELSE 0 END) as p2,
                    SUM(CASE WHEN priority = 'P3' THEN 1 ELSE 0 END) as p3,
                    SUM(CASE WHEN priority = 'P4' THEN 1 ELSE 0 END) as p4
                FROM tickets
                WHERE created_at >= date_trunc('week', CURRENT_DATE)
            ),
            last_week AS (
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved,
                    SUM(CASE WHEN (
                        sla_breached = true 
                        OR (sla_deadline IS NOT NULL AND sla_deadline < CURRENT_TIMESTAMP AND status NOT IN ('Resolved', 'Closed'))
                    ) THEN 1 ELSE 0 END) as sla_breached,
                    SUM(CASE WHEN priority = 'P2' THEN 1 ELSE 0 END) as p2,
                    SUM(CASE WHEN priority = 'P3' THEN 1 ELSE 0 END) as p3,
                    SUM(CASE WHEN priority = 'P4' THEN 1 ELSE 0 END) as p4
                FROM tickets
                WHERE created_at >= date_trunc('week', CURRENT_DATE) - INTERVAL '7 days'
                AND created_at < date_trunc('week', CURRENT_DATE)
            )
            SELECT 
                tw.total as tw_total, lw.total as lw_total,
                tw.open as tw_open, lw.open as lw_open,
                tw.in_progress as tw_in_progress, lw.in_progress as lw_in_progress,
                tw.resolved as tw_resolved, lw.resolved as lw_resolved,
                tw.sla_breached as tw_sla_breached, lw.sla_breached as lw_sla_breached,
                tw.p2 as tw_p2, lw.p2 as lw_p2,
                tw.p3 as tw_p3, lw.p3 as lw_p3,
                tw.p4 as tw_p4, lw.p4 as lw_p4
            FROM this_week tw, last_week lw
        """
        result = self.execute_one(query)
        if not result:
            return {}
        
        def calc_trend(current, previous):
            current = current or 0
            previous = previous or 0
            if previous == 0:
                if current > 0:
                    return '+100%', True
                return '0%', True
            change = ((current - previous) / previous) * 100
            sign = '+' if change >= 0 else ''
            return f'{sign}{change:.0f}%', change >= 0
        
        trends = {}
        for key in ['total', 'open', 'in_progress', 'resolved', 'sla_breached', 'p2', 'p3', 'p4']:
            trend_str, trend_up = calc_trend(result.get(f'tw_{key}'), result.get(f'lw_{key}'))
            trends[f'{key}_trend'] = trend_str
            trends[f'{key}_trend_up'] = trend_up
        
        return trends
    
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
                    WHEN 'P2' THEN 1 
                    WHEN 'P3' THEN 2 
                    WHEN 'P4' THEN 3 
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
        """Get real-time workload per technician from tickets table"""
        query = """
            SELECT 
                t.id, t.name,
                COUNT(tk.id) as total_assigned,
                SUM(CASE WHEN tk.status = 'Open' THEN 1 ELSE 0 END) as open_tickets,
                SUM(CASE WHEN tk.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN tk.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved_tickets
            FROM technicians t
            LEFT JOIN tickets tk ON t.id = tk.assigned_to_id
            WHERE t.active_status = true
            GROUP BY t.id, t.name
            ORDER BY total_assigned DESC
        """
        return self.execute_query(query, fetch=True)

    def get_tickets_by_status(self):
        """Get ticket count by status"""
        query = """
            SELECT status, COUNT(*) as count
            FROM tickets
            GROUP BY status
            ORDER BY count DESC
        """
        return self.execute_query(query, fetch=True)

    def get_sla_compliance_stats(self):
        """Get real-time SLA compliance statistics (computes breaches live from sla_deadline)"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN (
                    sla_breached = true 
                    OR (sla_deadline < CURRENT_TIMESTAMP AND status NOT IN ('Resolved', 'Closed'))
                ) THEN 1 ELSE 0 END) as breached,
                SUM(CASE WHEN NOT (
                    sla_breached = true 
                    OR (sla_deadline < CURRENT_TIMESTAMP AND status NOT IN ('Resolved', 'Closed'))
                ) THEN 1 ELSE 0 END) as within_sla,
                ROUND(
                    SUM(CASE WHEN NOT (
                        sla_breached = true 
                        OR (sla_deadline < CURRENT_TIMESTAMP AND status NOT IN ('Resolved', 'Closed'))
                    ) THEN 1 ELSE 0 END)::numeric / 
                    NULLIF(COUNT(*), 0) * 100, 1
                ) as compliance_rate
            FROM tickets
            WHERE sla_deadline IS NOT NULL
        """
        return self.execute_one(query)

    def get_resolution_time_distribution(self):
        """Get distribution of resolution times in hour buckets"""
        query = """
            SELECT 
                CASE 
                    WHEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600 < 1 THEN '< 1h'
                    WHEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600 < 4 THEN '1-4h'
                    WHEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600 < 8 THEN '4-8h'
                    WHEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600 < 24 THEN '8-24h'
                    WHEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600 < 48 THEN '1-2d'
                    ELSE '2d+'
                END as bucket,
                COUNT(*) as count
            FROM tickets
            WHERE resolved_at IS NOT NULL
            GROUP BY bucket
            ORDER BY MIN(EXTRACT(EPOCH FROM (resolved_at - created_at)))
        """
        return self.execute_query(query, fetch=True)

    def get_daily_resolution_trend(self, days=30):
        """Get daily resolved ticket count for last N days"""
        query = """
            SELECT DATE(resolved_at) as date, COUNT(*) as count
            FROM tickets
            WHERE resolved_at >= CURRENT_DATE - INTERVAL '%s days'
            AND resolved_at IS NOT NULL
            GROUP BY DATE(resolved_at)
            ORDER BY date
        """
        return self.execute_query(query, (days,), fetch=True)

    def get_technician_real_stats(self):
        """Get real-time resolved ticket counts for all technicians from tickets table"""
        query = """
            SELECT 
                t.id,
                COUNT(CASE WHEN tk.status IN ('Resolved', 'Closed') THEN 1 END) as real_resolved,
                COUNT(CASE WHEN tk.status NOT IN ('Resolved', 'Closed') THEN 1 END) as real_assigned
            FROM technicians t
            LEFT JOIN tickets tk ON t.id = tk.assigned_to_id
            GROUP BY t.id
        """
        return self.execute_query(query, fetch=True)

    # ==========================================
    # Feedback Methods
    # ==========================================
    def save_solution_feedback(self, ticket_id=None, session_id=None, solution_index=1, 
                               solution_text="", feedback_type=None):
        """Save per-solution feedback (tried/not_tried/helpful/not_helpful)"""
        query = """
            INSERT INTO solution_feedback (ticket_id, session_id, solution_index, solution_text, feedback_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_one(query, (ticket_id, session_id, solution_index, solution_text, feedback_type))
    
    def save_ticket_feedback(self, ticket_id=None, session_id=None, flow_type='incident',
                             rating=None, feedback_text=None):
        """Save end-of-flow feedback with rating"""
        query = """
            INSERT INTO ticket_feedback (ticket_id, session_id, flow_type, rating, feedback_text)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_one(query, (ticket_id, session_id, flow_type, rating, feedback_text))
    
    def save_all_feedback(self, feedback_data):
        """Save all feedback data from conversation state"""
        ticket_id = feedback_data.get('ticket_id')
        session_id = feedback_data.get('session_id')
        flow_type = feedback_data.get('flow_type', 'incident')
        rating = feedback_data.get('rating')
        feedback_text = feedback_data.get('feedback_text')
        solution_feedback = feedback_data.get('solution_feedback', {})
        solutions_shown = feedback_data.get('solutions_shown', [])
        
        # Save per-solution feedback (isolated per-item so one failure doesn't block ticket feedback)
        for index_str, feedback_type in solution_feedback.items():
            try:
                index = int(index_str) if isinstance(index_str, str) else index_str
                sol_entry = solutions_shown[index - 1] if index <= len(solutions_shown) else ""
                # Handle both plain strings and dict objects from solutions_list
                if isinstance(sol_entry, dict):
                    solution_text = sol_entry.get('text', str(sol_entry))
                else:
                    solution_text = str(sol_entry) if sol_entry else ""
                self.save_solution_feedback(ticket_id, session_id, index, solution_text, feedback_type)
            except Exception as e:
                logger.warning(f"Failed to save solution feedback for index {index_str}: {e}")
        
        # Save overall ticket feedback (star rating + text)
        try:
            if rating is not None or feedback_text:
                self.save_ticket_feedback(ticket_id, session_id, flow_type, rating, feedback_text)
        except Exception as e:
            logger.warning(f"Failed to save ticket feedback: {e}")
        
        return True
    
    def get_feedback_stats(self):
        """Get feedback statistics for analytics"""
        query = """
            SELECT 
                ROUND(AVG(rating), 2) as avg_rating,
                COUNT(*) as total_ratings,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_ratings,
                SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as negative_ratings
            FROM ticket_feedback
            WHERE rating IS NOT NULL
        """
        return self.execute_one(query)
    
    def get_solution_feedback_stats(self):
        """Get solution feedback statistics"""
        query = """
            SELECT 
                COUNT(*) as total_solutions,
                SUM(CASE WHEN feedback_type = 'helpful' THEN 1 ELSE 0 END) as helpful_count,
                SUM(CASE WHEN feedback_type = 'not_helpful' THEN 1 ELSE 0 END) as not_helpful_count,
                SUM(CASE WHEN feedback_type = 'tried' THEN 1 ELSE 0 END) as tried_count,
                SUM(CASE WHEN feedback_type = 'not_tried' THEN 1 ELSE 0 END) as not_tried_count
            FROM solution_feedback
        """
        return self.execute_one(query)
    
    def get_helpful_solutions_for_ticket(self, ticket_id):
        """Get solutions that were tried or marked helpful for a ticket"""
        query = """
            SELECT solution_index, solution_text, feedback_type
            FROM solution_feedback
            WHERE ticket_id = %s
            ORDER BY solution_index
        """
        return self.execute_query(query, (ticket_id,), fetch=True)


# Global database instance
db = PostgresDB()