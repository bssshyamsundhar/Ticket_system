-- Enterprise IT Support System Database Schema
-- Based on Dashboard Schema with enhancements for chatbot integration
-- Updated: Priority P2/P3/P4, Technician shifts, Feedback tables

-- Drop existing tables if they exist (for fresh start)
DROP TABLE IF EXISTS ticket_feedback CASCADE;
DROP TABLE IF EXISTS solution_feedback CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS kb_updates CASCADE;
DROP TABLE IF EXISTS conversation_history CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS knowledge_articles CASCADE;
DROP TABLE IF EXISTS priority_rules CASCADE;
DROP TABLE IF EXISTS sla_config CASCADE;
DROP TABLE IF EXISTS notification_settings CASCADE;
DROP TABLE IF EXISTS kb_categories CASCADE;
DROP TABLE IF EXISTS technicians CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- 1. Users Table (End users who create tickets)
-- ============================================
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    department VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',  -- 'user', 'admin'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================
-- 2. Technicians Table (Support staff with shift timings)
-- ============================================
CREATE TABLE technicians (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL,  -- 'L1 Support', 'L2 Support', 'Senior Engineer', etc.
    department VARCHAR(100) DEFAULT 'IT Support',
    active_status BOOLEAN DEFAULT true,
    assigned_tickets INTEGER DEFAULT 0,
    resolved_tickets INTEGER DEFAULT 0,
    avg_resolution_time VARCHAR(50),
    specialization TEXT[],
    shift_start TIME,  -- Shift start time (IST)
    shift_end TIME,    -- Shift end time (IST)
    joined_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_technicians_active ON technicians(active_status);
CREATE INDEX idx_technicians_email ON technicians(email);
CREATE INDEX idx_technicians_shift ON technicians(shift_start, shift_end);

-- ============================================
-- 3. SLA Configuration Table (P2/P3/P4 priority levels)
-- ============================================
CREATE TABLE sla_config (
    id VARCHAR(50) PRIMARY KEY,
    priority VARCHAR(50) UNIQUE NOT NULL CHECK (priority IN ('P4', 'P3', 'P2')),
    sla_hours INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. Priority Rules Table (Auto-assign priority)
-- ============================================
CREATE TABLE priority_rules (
    id VARCHAR(50) PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(50) NOT NULL CHECK (priority IN ('P4', 'P3', 'P2')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_priority_rules_keyword ON priority_rules(keyword);
CREATE INDEX idx_priority_rules_category ON priority_rules(category);

-- ============================================
-- 5. KB Categories Table (for button navigation)
-- ============================================
CREATE TABLE kb_categories (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. Tickets Table (Updated with P2/P3/P4 and new default assignment group)
-- ============================================
CREATE TABLE tickets (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    user_name VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    ticket_type VARCHAR(20) DEFAULT 'Incident' CHECK (ticket_type IN ('Incident', 'Request')),
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    priority VARCHAR(50) NOT NULL CHECK (priority IN ('P4', 'P3', 'P2')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('Open', 'In Progress', 'Pending Approval', 'Approved', 'Resolved', 'Closed')),
    assigned_to_id VARCHAR(50) REFERENCES technicians(id),
    assigned_to VARCHAR(255),
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    attachment_urls TEXT[],  -- Array of Cloudinary image URLs
    resolution_notes TEXT,
    sla_deadline TIMESTAMPTZ,
    sla_breached BOOLEAN DEFAULT false,
    chatbot_session_id VARCHAR(255),
    assignment_group VARCHAR(100) DEFAULT 'GSS Infradesk IT',  -- Updated default
    manager_approval_status VARCHAR(50) CHECK (manager_approval_status IN ('Pending', 'Approved', 'Rejected')),
    manager_approval_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ
);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_assigned_to ON tickets(assigned_to_id);
CREATE INDEX idx_tickets_user ON tickets(user_id);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_tickets_sla_deadline ON tickets(sla_deadline);
CREATE INDEX idx_tickets_type ON tickets(ticket_type);

-- ============================================
-- 7. Knowledge Articles Table (for admin management)
-- ============================================
CREATE TABLE knowledge_articles (
    id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    keywords TEXT[],
    solution TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    helpful INTEGER DEFAULT 0,
    not_helpful INTEGER DEFAULT 0,
    author VARCHAR(255),
    enabled BOOLEAN DEFAULT true,
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kb_category ON knowledge_articles(category);
CREATE INDEX idx_kb_subcategory ON knowledge_articles(subcategory);
CREATE INDEX idx_kb_enabled ON knowledge_articles(enabled);
CREATE INDEX idx_kb_keywords ON knowledge_articles USING GIN(keywords);

-- ============================================
-- 8. Audit Logs Table
-- ============================================
CREATE TABLE audit_logs (
    id VARCHAR(50) PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    ticket_id VARCHAR(50) REFERENCES tickets(id),
    user_id VARCHAR(50),
    user_name VARCHAR(255),
    details TEXT,
    ip_address VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_ticket ON audit_logs(ticket_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);

-- ============================================
-- 9. Notification Settings Table
-- ============================================
CREATE TABLE notification_settings (
    id SERIAL PRIMARY KEY,
    email_notifications BOOLEAN DEFAULT true,
    escalation_time_hours INTEGER DEFAULT 24,
    notify_on_ticket_creation BOOLEAN DEFAULT true,
    notify_on_ticket_assignment BOOLEAN DEFAULT true,
    notify_on_status_change BOOLEAN DEFAULT true,
    notify_on_sla_breach BOOLEAN DEFAULT true,
    notify_on_resolution BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 10. Conversation History Table (Chatbot sessions)
-- ============================================
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    session_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    buttons_shown JSONB,
    button_clicked VARCHAR(255),
    ticket_id VARCHAR(50) REFERENCES tickets(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conv_user_session ON conversation_history(user_id, session_id);
CREATE INDEX idx_conv_session ON conversation_history(session_id);
CREATE INDEX idx_conv_ticket ON conversation_history(ticket_id);

-- ============================================
-- 11. Solution Feedback Table (Per-solution helpfulness)
-- ============================================
CREATE TABLE solution_feedback (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) REFERENCES tickets(id),
    session_id VARCHAR(255),
    solution_index INTEGER NOT NULL,  -- Which solution (1, 2, 3, etc.)
    solution_text TEXT NOT NULL,
    feedback_type VARCHAR(20) CHECK (feedback_type IN ('tried', 'not_tried', 'helpful', 'not_helpful')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_solution_feedback_ticket ON solution_feedback(ticket_id);
CREATE INDEX idx_solution_feedback_session ON solution_feedback(session_id);
CREATE INDEX idx_solution_feedback_type ON solution_feedback(feedback_type);

-- ============================================
-- 12. Ticket Feedback Table (End-of-flow ratings)
-- ============================================
CREATE TABLE ticket_feedback (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) REFERENCES tickets(id),
    session_id VARCHAR(255),
    flow_type VARCHAR(20) CHECK (flow_type IN ('incident', 'request')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),  -- 1-5 stars
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ticket_feedback_ticket ON ticket_feedback(ticket_id);
CREATE INDEX idx_ticket_feedback_session ON ticket_feedback(session_id);
CREATE INDEX idx_ticket_feedback_rating ON ticket_feedback(rating);

-- ============================================
-- Insert default SLA config (P2=8hrs, P3=72hrs, P4=168hrs)
-- ============================================
INSERT INTO sla_config (id, priority, sla_hours, description) VALUES
    ('SLA-001', 'P4', 168, 'Low priority - 7 days resolution time'),
    ('SLA-002', 'P3', 72, 'Medium priority - 3 days resolution time'),
    ('SLA-003', 'P2', 8, 'High priority - 8 hours resolution time');

-- ============================================
-- Insert default priority rules (Updated for P2/P3/P4)
-- ============================================
INSERT INTO priority_rules (id, keyword, category, priority) VALUES
    ('PR-001', 'urgent', NULL, 'P2'),
    ('PR-002', 'critical', NULL, 'P2'),
    ('PR-003', 'emergency', NULL, 'P2'),
    ('PR-004', 'cannot access', NULL, 'P2'),
    ('PR-005', 'server down', NULL, 'P2'),
    ('PR-006', 'outage', NULL, 'P2'),
    ('PR-007', 'slow', NULL, 'P3'),
    ('PR-008', 'error', NULL, 'P3'),
    ('PR-009', 'help', NULL, 'P4'),
    ('PR-010', 'question', NULL, 'P4'),
    ('PR-011', 'vpn', 'VPN', 'P2'),
    ('PR-012', 'email', 'Email', 'P3'),
    ('PR-013', 'password', 'Account', 'P2');

-- ============================================
-- Insert default KB categories
-- ============================================
INSERT INTO kb_categories (id, name, display_name, icon, display_order) VALUES
    ('CAT-001', 'VPN', 'VPN & Remote Access', '🔐', 1),
    ('CAT-002', 'Email', 'Email & Outlook', '📧', 2),
    ('CAT-003', 'Windows', 'Windows & System', '💻', 3),
    ('CAT-004', 'Zoom', 'Zoom & Meetings', '📹', 4),
    ('CAT-005', 'Network', 'Network Drives', '📁', 5),
    ('CAT-006', 'Software', 'Software Installation', '📦', 6),
    ('CAT-007', 'Hardware', 'Hardware Issues', '🖥️', 7),
    ('CAT-008', 'Account', 'Password & Account', '🔑', 8),
    ('CAT-009', 'Other', 'Other Issues', '❓', 99);

-- ============================================
-- Insert default notification settings
-- ============================================
INSERT INTO notification_settings DEFAULT VALUES;

-- ============================================
-- Insert default admin user (password: admin123)
-- ============================================
INSERT INTO users (id, name, email, password_hash, role) 
VALUES (
    'USR-ADMIN001',
    'System Administrator',
    'admin@company.com',
    '$2b$12$vkxPBwHR/5b.QHgjc5lioOG8Ysx2EMLXsVNZOwNMROMeuxaIpulEW',
    'admin'
);

-- ============================================
-- Insert 10 technicians with shift timings (IST)
-- Shift 1: 7AM-4PM (4 technicians)
-- Shift 2: 2PM-11PM (3 technicians)
-- Shift 3: 7PM-4AM (3 technicians)
-- ============================================
INSERT INTO technicians (id, name, email, role, department, specialization, shift_start, shift_end, joined_date) VALUES
    -- Shift 1: 7AM-4PM (4 technicians)
    ('TECH-001', 'Rajesh Kumar', 'rajesh.kumar@company.com', 'L1 Support', 'IT Support', ARRAY['Windows', 'Email', 'VPN'], '07:00:00', '16:00:00', '2024-01-15'),
    ('TECH-002', 'Priya Sharma', 'priya.sharma@company.com', 'L1 Support', 'IT Support', ARRAY['Hardware', 'Software', 'Network'], '07:00:00', '16:00:00', '2024-02-01'),
    ('TECH-003', 'Amit Patel', 'amit.patel@company.com', 'L2 Support', 'IT Support', ARRAY['Network', 'Server', 'Security'], '07:00:00', '16:00:00', '2023-06-01'),
    ('TECH-004', 'Sneha Gupta', 'sneha.gupta@company.com', 'Senior Engineer', 'IT Support', ARRAY['Infrastructure', 'Cloud', 'Database'], '07:00:00', '16:00:00', '2022-03-20'),
    -- Shift 2: 2PM-11PM (3 technicians)
    ('TECH-005', 'Vikram Singh', 'vikram.singh@company.com', 'L1 Support', 'IT Support', ARRAY['Windows', 'Email', 'Zoom'], '14:00:00', '23:00:00', '2024-03-10'),
    ('TECH-006', 'Ananya Reddy', 'ananya.reddy@company.com', 'L2 Support', 'IT Support', ARRAY['Software', 'VPN', 'Account'], '14:00:00', '23:00:00', '2023-09-15'),
    ('TECH-007', 'Karthik Iyer', 'karthik.iyer@company.com', 'L1 Support', 'IT Support', ARRAY['Hardware', 'Network', 'Printing'], '14:00:00', '23:00:00', '2024-01-20'),
    -- Shift 3: 7PM-4AM (3 technicians)
    ('TECH-008', 'Deepak Verma', 'deepak.verma@company.com', 'L1 Support', 'IT Support', ARRAY['Windows', 'VPN', 'Email'], '19:00:00', '04:00:00', '2024-04-05'),
    ('TECH-009', 'Meera Nair', 'meera.nair@company.com', 'L2 Support', 'IT Support', ARRAY['Server', 'Security', 'Network'], '19:00:00', '04:00:00', '2023-11-01'),
    ('TECH-010', 'Rohit Joshi', 'rohit.joshi@company.com', 'Senior Engineer', 'IT Support', ARRAY['Infrastructure', 'Database', 'Cloud'], '19:00:00', '04:00:00', '2022-08-15');