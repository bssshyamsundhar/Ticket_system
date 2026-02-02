================================================================================
                    IT SUPPORT TICKET SYSTEM - ARCHITECTURE GUIDE
================================================================================

Comprehensive overview of system architecture, data flow, database schema,
agents, tools, and inter-component communication.

================================================================================
1. SYSTEM OVERVIEW
================================================================================

This is a multi-tiered AI-powered IT Support Ticket System that automates user
issue resolution using intelligent agents, semantic knowledge base search, and
escalation workflows.

CORE COMPONENTS:
  - Flask REST API Backend (Python)
  - React Frontend SPA
  - PostgreSQL Database (persistent data)
  - ChromaDB Knowledge Base (semantic search)
  - Google ADK Agents (AI orchestration)
  - Agent Tools (KB search, clarification, ticket creation)

KEY FEATURES:
  - User authentication with JWT tokens
  - Two-stage AI-powered support: Self-Service Agent → Escalation Agent
  - Semantic knowledge base using embeddings
  - Automated ticket creation on escalation
  - Admin dashboard for ticket management
  - Conversation history tracking

================================================================================
2. FILE STRUCTURE & ORGANIZATION
================================================================================

/app.py
  Main Flask application entry point
  - Initializes Flask app with CORS support
  - Registers all REST API endpoints
  - Handles JWT authentication
  - Maintains conversation state in memory (conversation_states dict)
  - Routes all client requests to appropriate handlers

/config.py
  Centralized configuration management
  - Database connection parameters (PostgreSQL)
  - LLM provider settings (Groq/xAI)
  - API keys and credentials
  - Model configurations
  - Application settings

/db/
  Database layer (PostgreSQL interactions)

  /schema.sql
    Database schema definition (DDL)
    Tables:
      - users: Authentication and role management
      - tickets: Support ticket storage
      - conversation_history: Chat message logs
      - kb_updates: Knowledge base update records

  /postgres.py
    Database abstraction layer (ORM-like helper)
    Classes:
      - PostgresDB: Handles all DB operations
    Methods:
      - User operations: create_user, get_user_by_id, get_user_by_email
      - Ticket operations: create_ticket, update_ticket_status, get_tickets
      - Conversation: save_conversation, get_conversation_history
      - KB operations: create_kb_update

/agents/
  AI agent definitions using Google ADK

  /prompts.py
    System prompts for agents
    - SELF_SERVICE_AGENT_INSTRUCTION: First-line support logic
    - ESCALATION_AGENT_INSTRUCTION: Escalation confirmation

  /self_service/
    /agent.py
      Self-Service Agent definition
      - Model: Google Gemini 2.5 Flash or LiteLlm
      - Tools: search_knowledge_base, ask_clarification
      - Task: Resolve issues from KB or escalate if not found

  /escalation/
    /agent.py
      Escalation Agent definition
      - Model: Google Gemini 2.5 Flash or LiteLlm
      - Tools: None (ticket creation handled by app)
      - Task: Confirm escalation and compose confirmation message

/tools/
  Callable tools/functions for agents

  /tools.py
    Implements tools available to agents:
    - search_knowledge_base(query: str) → str
      Searches ChromaDB for solutions, returns top 1 result
    - ask_clarification(question: str) → str
      Generates clarification request marker
    - create_ticket(user_id, issue_summary, ...) → dict
      Creates ticket in database
    - update_ticket_status(ticket_id, status, ...) → dict
      Updates ticket status
    - send_email_notification(...) → dict
      Sends email (if SMTP configured)
    - append_to_kb(...) → bool
      Adds new KB entries

/kb/
  Knowledge base (semantic search with ChromaDB)

  /kb_chroma.py
    ChromaDB wrapper for knowledge base
    Classes:
      - KnowledgeBase: Manages KB operations
    Methods:
      - add_entry(issue, solution, source) → entry_id
        Adds new KB entry with embeddings
      - search(query, top_k=1) → List[Dict]
        Semantic search returning issue + solution
      - delete_all_entries() → bool
        Clears entire KB

  /embedding.py
    Embedding model management
    - Uses SentenceTransformers (all-MiniLM-L6-v2)
    - Singleton pattern: get_embedding_model()

  /data/
    Initial data

    /initial_kb.json
      Pre-populated knowledge base entries
      Format: Array of {issue, solution, source} objects

  /chroma_db/
    Persistent ChromaDB storage
    - SQLite backend for embeddings
    - Collection: "it_support_kb"

/runners/
  Agent orchestration and execution

  /run_agents.py
    Classes:
      - AgentOrchestrator: Coordinates multi-agent workflow
    Methods:
      - create_user_session(user_id) → session_id
        Creates new ADK session for user
      - run_self_service_agent(...) → Dict
        Executes self-service agent
      - run_escalation_agent(...) → Dict
        Executes escalation agent + creates ticket
      - handle_user_query(...) → Dict
        Main orchestration logic for incoming queries

/frontend/
  React single-page application

  /public/
    /index.html
      Entry HTML file

  /src/
    /App.js
      Root component
      - Routing logic (Login, Chat, AdminDashboard)
      - Token and user state management
      - Navigation

    /App.css
      Global styles

    /index.js
      React entry point

    /components/
      /Login.jsx / Login.css
        User authentication (register/login)
        - API: POST /api/auth/register, /api/auth/login

      /Chat.jsx / Chat.css
        Main chat interface for users
        - API: POST /api/chat (main interaction)
        - Displays agent responses
        - Handles ticket creation UI

      /AdminDashboard.jsx / AdminDashboard.css
        Admin interface for ticket management
        - Views all tickets
        - Updates ticket status
        - Adds KB entries

      /TicketPreview.jsx / TicketPreview.css
        Ticket detail viewer

/sessions/
  Session storage (temporary)
  - ai_ticket_sessions.db: SQLite for ADK sessions

================================================================================
3. DATABASE SCHEMA & STRUCTURE
================================================================================

DATABASE: PostgreSQL

TABLE: users
  ┌─────────────────────────────────────────────┐
  │ Column            │ Type        │ Constraints │
  ├─────────────────────────────────────────────┤
  │ id                │ SERIAL      │ PRIMARY KEY │
  │ username          │ VARCHAR(100)│ UNIQUE      │
  │ email             │ VARCHAR(255)│ UNIQUE      │
  │ password_hash     │ VARCHAR(255)│ NOT NULL    │
  │ role              │ VARCHAR(20) │ NOT NULL    │
  │ created_at        │ TIMESTAMP   │ DEFAULT NOW │
  └─────────────────────────────────────────────┘

  ROLE VALUES: 'user' | 'admin'
  Default admin: username=admin, email=admin@company.com, password=admin123

TABLE: tickets
  ┌──────────────────────────────────────────────────────┐
  │ Column            │ Type        │ Constraints         │
  ├──────────────────────────────────────────────────────┤
  │ id                │ SERIAL      │ PRIMARY KEY         │
  │ user_id           │ INTEGER     │ FK(users.id)        │
  │ issue_summary     │ TEXT        │ NOT NULL            │
  │ refined_query     │ TEXT        │ (from clarification)│
  │ confidence_score  │ FLOAT       │ (from KB search)    │
  │ status            │ VARCHAR(20) │ NOT NULL, DEFAULT   │
  │ resolution_text   │ TEXT        │ (admin resolution)  │
  │ created_at        │ TIMESTAMP   │ DEFAULT NOW         │
  │ updated_at        │ TIMESTAMP   │ DEFAULT NOW         │
  │ resolved_at       │ TIMESTAMP   │ (when resolved)     │
  │ resolved_by       │ INTEGER     │ FK(users.id)        │
  └──────────────────────────────────────────────────────┘

  STATUS VALUES: 'open' | 'in_progress' | 'resolved' | 'closed'
  INDEXES: idx_tickets_user_id, idx_tickets_status

TABLE: conversation_history
  ┌──────────────────────────────────────────────────────┐
  │ Column            │ Type        │ Constraints         │
  ├──────────────────────────────────────────────────────┤
  │ id                │ SERIAL      │ PRIMARY KEY         │
  │ user_id           │ INTEGER     │ FK(users.id)        │
  │ session_id        │ VARCHAR(255)│ NOT NULL            │
  │ user_message      │ TEXT        │ NOT NULL            │
  │ agent_response    │ TEXT        │ NOT NULL            │
  │ ticket_id         │ INTEGER     │ FK(tickets.id)      │
  │ created_at        │ TIMESTAMP   │ DEFAULT NOW         │
  └──────────────────────────────────────────────────────┘

  Stores entire conversation for audit and replay
  INDEX: idx_conversation_user_session

TABLE: kb_updates
  ┌──────────────────────────────────────────────────────┐
  │ Column            │ Type        │ Constraints         │
  ├──────────────────────────────────────────────────────┤
  │ id                │ SERIAL      │ PRIMARY KEY         │
  │ ticket_id         │ INTEGER     │ FK(tickets.id)      │
  │ issue_text        │ TEXT        │ NOT NULL            │
  │ solution_text     │ TEXT        │ NOT NULL            │
  │ approved_by       │ INTEGER     │ FK(users.id)        │
  │ created_at        │ TIMESTAMP   │ DEFAULT NOW         │
  └──────────────────────────────────────────────────────┘

  Records when admins add solutions to KB
  INDEX: idx_kb_updates_ticket

KNOWLEDGE BASE (ChromaDB):
  Collection Name: "it_support_kb"
  Vector DB: SQLite-backed ChromaDB
  Embeddings: SentenceTransformers (all-MiniLM-L6-v2)
  Metadata stored:
    - issue: Original problem statement
    - solution: Solution text
    - source: "Admin Approved" or custom

================================================================================
4. API ENDPOINTS & REQUEST/RESPONSE FLOWS
================================================================================

AUTHENTICATION ENDPOINTS:
─────────────────────────────────────────────────────────────────────────────

POST /api/auth/register
  Request:
    {
      "username": "john_doe",
      "email": "john@example.com",
      "password": "secure_password"
    }
  Response (201):
    {
      "success": true,
      "token": "eyJ...",
      "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "user"
      }
    }
  Flow:
    1. Validate required fields
    2. Check if user exists
    3. Hash password with bcrypt
    4. INSERT into users table
    5. Generate JWT token (24h expiration)
    6. Return token and user info

POST /api/auth/login
  Request:
    {
      "email": "john@example.com",
      "password": "secure_password"
    }
  Response:
    {
      "success": true,
      "token": "eyJ...",
      "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "user"
      }
    }
  Flow:
    1. Fetch user by email
    2. Verify password hash
    3. Generate JWT token
    4. Return token and user info

USER ENDPOINTS:
─────────────────────────────────────────────────────────────────────────────

GET /api/users/<user_id>
  Headers: Authorization: Bearer <token>
  Response:
    {
      "success": true,
      "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "user"
      }
    }

CHAT ENDPOINT (MAIN INTERACTION):
─────────────────────────────────────────────────────────────────────────────

POST /api/chat
  Headers: Authorization: Bearer <token>
  Request:
    {
      "message": "My laptop won't turn on",
      "session_id": "optional_session_id"
    }
  Response:
    {
      "success": true,
      "response": "Agent's response text...",
      "session_id": "session_123",
      "agent": "self_service|escalation",
      "escalated": false,
      "needs_clarification": false,
      "ticket_preview": null
    }

  FLOW (DETAILED):
    1. USER SENDS MESSAGE
       → POST /api/chat with message
       → token_required decorator validates JWT
       → Extract user_id, user_email from token

    2. SESSION CREATION (if needed)
       → orchestrator.create_user_session(user_id)
       → Creates ADK in-memory session

    3. QUERY ORCHESTRATION
       → orchestrator.handle_user_query()
       → Initialize conversation_state if first message
       → Check if clarification limit exceeded (>=2)
         - If YES: Jump to ESCALATION
         - If NO: Continue to SELF-SERVICE

    4. SELF-SERVICE AGENT
       a) Agent Input:
          - User message
          - Instruction: Resolve from KB or escalate
          - Available tools: search_knowledge_base, ask_clarification

       b) Agent Decision Tree:
          i) User asks to escalate? → ESCALATE immediately
          ii) Escalation signal detected? → ESCALATE immediately
          iii) Otherwise: Call search_knowledge_base(message)
          iv) KB found with confidence ≥70%? → Return solution
          v) KB found with confidence <70%? → ESCALATE
          vi) No KB result? → Ask clarification or ESCALATE

       c) Agent Output:
          Returns final_response with optional:
          - "ESCALATE_TO_HUMAN: <issue_summary>" marker
          - "CLARIFICATION_NEEDED: <question>" marker

       d) Response Processing:
          - Parse for escalation/clarification signals
          - Update conversation_state (clarification_count++)
          - Save conversation to database

    5. ESCALATION (if triggered)
       a) Input:
          - issue_summary (from message or state)
          - user_email
          - refined_query (if from clarification)
          - confidence_score (if from KB)

       b) Escalation Agent:
          - Composes professional confirmation message
          - No tools (no KB search, no clarification)
          - Returns brief acknowledgment

       c) Ticket Creation:
          - create_ticket(user_id, issue_summary, ...)
          - INSERT into tickets table
          - Returns ticket_id

       d) Response:
          - Combine agent confirmation + ticket creation message
          - Return with escalated=true

    6. RESPONSE TO CLIENT
       {
         "success": true,
         "response": "Full agent response with ticket info",
         "agent": "self_service|escalation",
         "escalated": false|true,
         "needs_clarification": false|true,
         "session_id": "session_123"
       }

    7. CLIENT UPDATE
       - Update UI with agent response
       - Store session_id for next message
       - If escalated, show ticket confirmation
       - If needs_clarification, keep chat open

TICKET ENDPOINTS (Admin/User):
─────────────────────────────────────────────────────────────────────────────

GET /api/tickets/user/<user_id>
  Headers: Authorization: Bearer <token>
  Response:
    {
      "success": true,
      "tickets": [
        {
          "id": 1,
          "user_id": 1,
          "issue_summary": "...",
          "status": "open",
          "created_at": "2024-01-15T10:30:00",
          "resolved_at": null
        }
      ]
    }
  Flow:
    1. Verify user is requesting own tickets or is admin
    2. SELECT tickets WHERE user_id = <user_id>
    3. Return ticket list

GET /api/tickets/<ticket_id>
  Headers: Authorization: Bearer <token>
  Response: Single ticket object
  Flow: Similar to above, with authorization check

GET /api/tickets (Admin only)
  Response: All tickets in system
  Flow: Check user.role == 'admin', return all

PUT /api/tickets/<ticket_id>/status (Admin only)
  Headers: Authorization: Bearer <token>
  Request:
    {
      "status": "resolved",
      "resolution_text": "Reboot fixed the issue"
    }
  Response:
    {
      "success": true,
      "message": "Ticket #1 updated successfully"
    }
  Flow:
    1. Check admin role
    2. UPDATE tickets SET status=?, resolution_text=?, resolved_by=?
    3. Return success

KNOWLEDGE BASE ENDPOINTS:
─────────────────────────────────────────────────────────────────────────────

POST /api/kb/update (Admin only)
  Headers: Authorization: Bearer <token>
  Request:
    {
      "ticket_id": 1,
      "issue": "Laptop won't turn on",
      "solution": "Check power cable connection..."
    }
  Response:
    {
      "success": true,
      "entry_id": "kb_abc123",
      "message": "Knowledge base updated successfully"
    }
  Flow:
    1. Check admin role
    2. Call kb.add_entry(issue, solution, "Admin Approved")
       - Generate embedding from issue
       - Store in ChromaDB with solution in metadata
    3. INSERT into kb_updates table
    4. Return entry_id

POST /api/kb/search
  Headers: Authorization: Bearer <token>
  Request:
    {
      "query": "Monitor not displaying"
    }
  Response:
    {
      "success": true,
      "results": [
        {
          "confidence": 0.87,
          "issue": "Monitor not showing display",
          "solution": "Check HDMI cable..."
        }
      ]
    }
  Flow:
    1. Call kb.search(query, top_k=1)
    2. Generate embedding from query
    3. ChromaDB semantic search
    4. Return results with confidence scores

================================================================================
5. DATA FLOW - DETAILED EXAMPLE WALKTHROUGH
================================================================================

SCENARIO: User asks "My printer isn't printing"

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: FRONTEND (React)                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ User types message in Chat.jsx component                                    │
│ onClick → calls API:                                                        │
│                                                                             │
│   POST /api/chat                                                            │
│   Headers: Authorization: Bearer eyJ...                                     │
│   Body: {                                                                   │
│     "message": "My printer isn't printing",                                 │
│     "session_id": "existing_session_or_null"                                │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: FLASK BACKEND (app.py)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ @app.route('/api/chat', methods=['POST'])                                   │
│ @token_required                                                             │
│ def chat():                                                                  │
│                                                                             │
│ a) JWT Validation (token_required decorator):                               │
│    - Extract token from Authorization header                                │
│    - Decode: jwt.decode(token, SECRET, algorithms=["HS256"])                │
│    - Extract user_id=1, user_email="john@example.com", role="user"          │
│                                                                             │
│ b) Extract request data:                                                    │
│    - message = "My printer isn't printing"                                  │
│    - session_id = null (first message, so create new)                       │
│                                                                             │
│ c) Create/Get session:                                                      │
│    - session_id = asyncio.run(orchestrator.create_user_session("1"))        │
│    - Returns: "session_xyz_123"                                             │
│    - Stores in orchestrator.session_service                                 │
│                                                                             │
│ d) Initialize/Get conversation state:                                       │
│    - state_key = "1_session_xyz_123"                                        │
│    - conversation_state = {                                                 │
│        "clarification_count": 0,                                            │
│        "issue_summary": "",                                                 │
│        "refined_query": None,                                               │
│        "confidence_score": None                                             │
│      }                                                                       │
│                                                                             │
│ e) Call orchestrator:                                                       │
│    result = asyncio.run(orchestrator.handle_user_query(                     │
│      user_id=1,                                                             │
│      user_email="john@example.com",                                         │
│      session_id="session_xyz_123",                                          │
│      message="My printer isn't printing",                                   │
│      conversation_state={...}                                               │
│    ))                                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: AGENT ORCHESTRATOR (runners/run_agents.py)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ async def handle_user_query(...):                                            │
│                                                                             │
│ a) Check clarification limit:                                               │
│    if clarification_count >= 2:                                             │
│      → Jump to ESCALATION (not in this case, count=0)                       │
│                                                                             │
│ b) Run self-service agent:                                                  │
│    response = await self.run_self_service_agent(                            │
│      user_id="1",                                                           │
│      session_id="session_xyz_123",                                          │
│      user_message="My printer isn't printing"                               │
│    )                                                                        │
│                                                                             │
│    Inside run_self_service_agent():                                         │
│    - Create ADK Content with user message                                   │
│    - Call self_service_runner.run_async(...)                                │
│    - This invokes the self_service agent                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: SELF-SERVICE AGENT (agents/self_service/agent.py)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Agent: Google ADK Gemini 2.5 Flash                                          │
│ Instruction: SELF_SERVICE_AGENT_INSTRUCTION                                 │
│ Tools: [search_knowledge_base, ask_clarification]                           │
│                                                                             │
│ Agent's Decision Process:                                                   │
│                                                                             │
│ 1. Check escalation signals in "My printer isn't printing":                 │
│    - No keywords like "escalate", "human", "urgent"                         │
│    - No explicit escalation request                                         │
│    → Not escalation case                                                    │
│                                                                             │
│ 2. Not escalating, so search KB:                                            │
│    → Call tool: search_knowledge_base("My printer isn't printing")           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: KB SEARCH (tools/tools.py + kb/kb_chroma.py)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ def search_knowledge_base(query: str) -> str:                               │
│                                                                             │
│ a) Call KB search:                                                          │
│    results = kb.search(query="My printer isn't printing", top_k=1)          │
│                                                                             │
│    Inside kb.search():                                                      │
│    - Generate embedding for query:                                          │
│      embedding = embedding_model.encode(query)                              │
│      → Vector: [0.12, -0.45, 0.67, ..., 0.23] (384 dims)                   │
│                                                                             │
│    - Search ChromaDB collection:                                            │
│      collection.query(                                                      │
│        query_embeddings=[embedding],                                        │
│        n_results=1,                                                         │
│        where=None                                                           │
│      )                                                                      │
│                                                                             │
│    - ChromaDB returns documents with similarity scores (cosine)              │
│                                                                             │
│    Example matching documents in KB:                                        │
│    ┌──────────────────────────────────────────────────────────────┐         │
│    │ Document 1: "Printer not printing"                            │         │
│    │ Similarity: 0.89 (89%)                                        │         │
│    │ Metadata:                                                    │         │
│    │   solution: "Check if printer is connected..."               │         │
│    │   source: "Admin Approved"                                   │         │
│    └──────────────────────────────────────────────────────────────┘         │
│                                                                             │
│ b) Process result:                                                          │
│    result = results[0]                                                      │
│    confidence = 0.89                                                        │
│    solution = "Check if printer is connected. Try unplugging..."            │
│                                                                             │
│ c) Check confidence threshold:                                              │
│    if confidence >= 0.7 (70%):                                              │
│      → FOUND GOOD SOLUTION (0.89 > 0.7)                                     │
│                                                                             │
│ d) Return formatted result:                                                 │
│    return "Solution found (Confidence: 89%):\n\n" +                         │
│           "Check if printer is connected. Try unplugging..."                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: AGENT CONTINUES (agents/self_service/agent.py)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Tool call returned solution text                                            │
│                                                                             │
│ Agent reasoning:                                                            │
│ - KB returned solution with 89% confidence                                  │
│ - Confidence >= 70% threshold → Use this solution                           │
│ - Compose response with solution                                            │
│ - No escalation needed                                                      │
│                                                                             │
│ Agent generates response:                                                   │
│ "Here's a solution for your printer issue:\n\n                              │
│  Check if your printer is connected to power and network. If not printing:  │
│  1. Unplug printer for 30 seconds                                           │
│  2. Plug back in and wait for startup                                       │
│  3. Try printing a test page                                                │
│                                                                             │
│  If this doesn't work, let me know and I can escalate to our support team." │
│                                                                             │
│ final_response = "..."                                                      │
│ Returns to orchestrator                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: ORCHESTRATOR PROCESSES RESPONSE (runners/run_agents.py)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Back in run_self_service_agent():                                           │
│                                                                             │
│ async for event in self_service_runner.run_async(...):                      │
│   if event.is_final_response():                                             │
│     final_response = "..."  # Agent's response above                        │
│                                                                             │
│ Check for control signals:                                                  │
│ - "ESCALATE_TO_HUMAN" in response? NO                                       │
│ - "CLARIFICATION_NEEDED:" in response? NO                                   │
│                                                                             │
│ Return to handle_user_query():                                              │
│ {                                                                           │
│   "success": True,                                                          │
│   "response": "Here's a solution...",                                       │
│   "needs_escalation": False,                                                │
│   "needs_clarification": False,                                             │
│   "agent": "self_service"                                                   │
│ }                                                                           │
│                                                                             │
│ Back in handle_user_query():                                                │
│ - Check needs_escalation? NO                                                │
│ - Check needs_clarification? NO                                             │
│ - Save conversation to database:                                            │
│   db.save_conversation(                                                     │
│     user_id=1,                                                              │
│     session_id="session_xyz_123",                                           │
│     user_message="My printer isn't printing",                               │
│     agent_response="Here's a solution..."                                   │
│   )                                                                         │
│   INSERT into conversation_history table                                    │
│                                                                             │
│ - Return final result:                                                      │
│   {                                                                         │
│     "success": True,                                                        │
│     "response": "Here's a solution...",                                     │
│     "agent": "self_service",                                                │
│     "conversation_state": {...},                                            │
│     "needs_clarification": False,                                           │
│     "needs_escalation": False                                               │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: FLASK RETURNS RESPONSE (app.py)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ HTTP Response (200 OK):                                                     │
│ {                                                                           │
│   "success": true,                                                          │
│   "response": "Here's a solution for your printer issue:\n\n...",            │
│   "session_id": "session_xyz_123",                                          │
│   "agent": "self_service",                                                  │
│   "escalated": false,                                                       │
│   "needs_clarification": false,                                             │
│   "ticket_preview": null                                                    │
│ }                                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 9: FRONTEND UPDATES UI (Chat.jsx)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Receive JSON response                                                       │
│ - Parse response                                                            │
│ - Store session_id for next message                                         │
│ - Display agent response in chat UI                                         │
│ - Show "Problem solved?" buttons if not escalated                           │
│ - Keep chat open for follow-up                                              │
│                                                                             │
│ User can now:                                                               │
│ 1. Ask follow-up question (send new message) → Loop back to STEP 2         │
│ 2. Report issue still exists → Agent may ask clarification                   │
│ 3. Close chat and mark resolved                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

ALTERNATIVE SCENARIO: If KB match was LOW confidence or NO MATCH
────────────────────────────────────────────────────────────────────────────────

If confidence < 0.7 or no KB results:

Agent Decision:
  - Option 1: Ask clarification question using ask_clarification() tool
    → Returns "CLARIFICATION_NEEDED: <question>"
    → Orchestrator increments clarification_count
    → User responds with clarification
    → Agent searches KB again with refined query
    
  - Option 2: Escalate immediately
    → Returns "ESCALATE_TO_HUMAN: <issue_summary>"
    → Orchestrator detects marker
    → Calls run_escalation_agent()
    → Creates ticket in database
    → Returns escalation confirmation

ESCALATION FLOW (if triggered):
────────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│ ESCALATION AGENT (agents/escalation/agent.py)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Input:                                                                      │
│   escalation_message = """                                                  │
│   A user has an unresolved IT issue...                                      │
│   Issue: My printer isn't printing                                          │
│   User Email: john@example.com                                              │
│   ...                                                                       │
│   """                                                                       │
│                                                                             │
│ Agent (Gemini 2.5 Flash) generates confirmation:                            │
│   "I understand you're having trouble with your printer not printing.        │
│    I'm creating a support ticket for our team to investigate this issue.    │
│    You'll receive an email confirmation shortly at john@example.com."       │
│                                                                             │
│ No tools (no KB search, no clarification)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ TICKET CREATION (db/postgres.py)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Inside orchestrator.run_escalation_agent():                                 │
│                                                                             │
│ ticket_id = db.create_ticket(                                               │
│   user_id=1,                                                                │
│   issue_summary="My printer isn't printing",                                │
│   refined_query=None,  # If user clarified, this would have value           │
│   confidence_score=0.45  # If KB search was done, score would be here       │
│ )                                                                           │
│                                                                             │
│ SQL Executed:                                                               │
│   INSERT INTO tickets                                                       │
│   (user_id, issue_summary, refined_query, confidence_score, status)         │
│   VALUES (1, 'My printer isn't printing', NULL, 0.45, 'open')               │
│   RETURNING id                                                              │
│                                                                             │
│ Returns: ticket_id = 42                                                     │
│                                                                             │
│ Ticket created with:                                                        │
│ - status: 'open'                                                            │
│ - created_at: NOW()                                                         │
│ - updated_at: NOW()                                                         │
│ - resolved_at: NULL                                                         │
│ - resolved_by: NULL                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ RESPONSE WITH TICKET CONFIRMATION                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Escalation agent response + ticket confirmation:                            │
│                                                                             │
│ "I understand you're having trouble with your printer not printing.          │
│  I'm creating a support ticket for our team to investigate this issue.      │
│  You'll receive an email confirmation shortly at john@example.com.          │
│                                                                             │
│  ✓ Ticket #42 has been created successfully."                               │
│                                                                             │
│ Return to Flask:                                                            │
│ {                                                                           │
│   "success": true,                                                          │
│   "response": "...ticket confirmation...",                                  │
│   "agent": "escalation",                                                    │
│   "escalated": true,                                                        │
│   "ticket_preview": {                                                       │
│     "ticket_id": 42,                                                        │
│     "status": "open",                                                       │
│     "created_at": "2024-01-15T10:35:00"                                     │
│   }                                                                         │
│ }                                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
6. CONTROL FLOW & STATE MANAGEMENT
================================================================================

CONVERSATION STATE OBJECT:
──────────────────────────────────────────────────────────────────────────────

Structure (maintained per session in Flask app.conversation_states dict):
{
  "clarification_count": 0,           # Increments each clarification
  "issue_summary": "User's issue",    # Original or refined
  "refined_query": None,              # After clarification (optional)
  "confidence_score": None            # From KB search (optional)
}

State Transitions:
  
  START
    ↓
  initialize_state() → clarification_count=0
    ↓
  ─────────────────────────────────────────────────────────────────
  ├─→ [KB Search Success, confidence ≥ 70%]
  │       ↓
  │   return_solution()
  │       ↓
  │   RESOLVED
  │
  ├─→ [KB Search Success, confidence < 70%] OR [No KB Match]
  │       ↓
  │   ask_clarification()
  │       ↓
  │   clarification_count++
  │       ↓
  │   ─────────────────────────────────────────────────────────────
  │   ├─→ [User provides clarification]
  │   │       ↓
  │   │   [if clarification_count < 2]
  │   │       ↓
  │   │   run_self_service_agent_again()
  │   │       ↓
  │   │   (state updated, loop)
  │   │
  │   └─→ [clarification_count >= 2]
  │           ↓
  │       ESCALATE
  │
  ├─→ [Escalation Requested by User]
  │       ↓
  │   ESCALATE immediately
  │
  └─→ [Escalation Triggered]
        ↓
      run_escalation_agent()
        ↓
      create_ticket()
        ↓
      RESOLVED (Ticket Created)

CONVERSATION STATE PERSISTENCE:
──────────────────────────────────────────────────────────────────────────────

In Flask app.py:
  conversation_states = {}  # In-memory dictionary

Key: f"{user_id}_{session_id}"
Example: "1_session_xyz_123"

Lifecycle:
  1. First message → state created with defaults
  2. Each message → state updated (clarification_count, issue_summary)
  3. Session ends → state remains (for replay/audit)
  4. On server restart → all states lost (use Redis in production)

DATABASE RECORD:
  conversation_history table stores EVERY interaction:
  {
    user_id: 1,
    session_id: "session_xyz_123",
    user_message: "My printer isn't printing",
    agent_response: "Solution text...",
    ticket_id: 42,
    created_at: "2024-01-15T10:35:00"
  }

  This allows:
  - Full conversation replay
  - Audit trail
  - Training data for future improvements

================================================================================
7. MULTI-AGENT WORKFLOW - ORCHESTRATOR PATTERN
================================================================================

AGENT ORCHESTRATOR (runners/run_agents.py - AgentOrchestrator class):
──────────────────────────────────────────────────────────────────────────────

Responsibilities:
  1. Agent lifecycle management
  2. Session creation/management (ADK sessions)
  3. Control flow decisions (self-service vs escalation)
  4. State tracking across agent calls
  5. Database integration

Components:
  
  self_service_agent:
    - Model: Google Gemini 2.5 Flash
    - Instruction: SELF_SERVICE_AGENT_INSTRUCTION
    - Tools: [search_knowledge_base, ask_clarification]
    - Task: Resolve or clarify
    - Async Runner: self_service_runner
  
  escalation_agent:
    - Model: Google Gemini 2.5 Flash or LiteLlm
    - Instruction: ESCALATION_AGENT_INSTRUCTION
    - Tools: [] (none)
    - Task: Confirm escalation
    - Async Runner: escalation_runner
  
  session_service:
    - Type: InMemorySessionService
    - Stores: ADK conversation sessions
    - Scope: Per user, per conversation
    - Expiration: Server memory (no persistence)

DECISION TREE IN ORCHESTRATOR:
──────────────────────────────────────────────────────────────────────────────

handle_user_query(user_id, message, conversation_state)
  │
  ├─→ IF clarification_count >= MAX_CLARIFICATION_ATTEMPTS (2):
  │     └─→ run_escalation_agent() directly
  │         └─→ create_ticket()
  │         └─→ return escalated response
  │
  ├─→ ELSE:
      └─→ run_self_service_agent()
          │
          ├─→ IF "ESCALATE_TO_HUMAN" in response:
          │     └─→ run_escalation_agent()
          │         └─→ create_ticket()
          │         └─→ return escalated response
          │
          ├─→ ELSE IF "CLARIFICATION_NEEDED:" in response:
          │     └─→ clarification_count++
          │     └─→ save_conversation()
          │     └─→ return with needs_clarification=True
          │
          └─→ ELSE:
              └─→ save_conversation()
              └─→ return success response

================================================================================
8. KNOWLEDGE BASE SYSTEM
================================================================================

SEMANTIC SEARCH ARCHITECTURE:
──────────────────────────────────────────────────────────────────────────────

Pipeline:
  
  Text Input
    ↓
  Sentence Transformer (all-MiniLM-L6-v2)
    ↓ (generates 384-dimensional vector)
  Dense Vector
    ↓
  ChromaDB Collection
    ↓ (cosine similarity search)
  Ranked Results (by similarity score)
    ↓
  Filter by threshold (confidence ≥ 0.7)
    ↓
  Return Top K=1 result

KB ENTRY STRUCTURE:
──────────────────────────────────────────────────────────────────────────────

ChromaDB Document:
{
  "id": "kb_a1b2c3d4",
  "embedding": [0.12, -0.45, 0.67, ...],  # 384 dims
  "document": "Printer not printing",      # Original issue
  "metadata": {
    "issue": "Printer not printing",
    "solution": "Check power connection. If still not printing, restart...",
    "source": "Admin Approved"
  }
}

KB POPULATION WORKFLOW:
──────────────────────────────────────────────────────────────────────────────

Method 1: Admin Dashboard
  1. Admin resolves ticket and creates solution
  2. Admin clicks "Add to KB" on ticket detail
  3. Frontend: POST /api/kb/update
  4. Backend:
     - kb.add_entry(issue, solution, "Admin Approved")
     - Embed issue text
     - Store in ChromaDB
     - INSERT into kb_updates table
  5. KB now searchable

Method 2: Initial Population (populate_kb.py)
  1. Read initial_kb.json
  2. Parse [{issue, solution, source}]
  3. Add each entry to KB
  4. Used on first deployment

KB SEARCH FLOW (in detail):
──────────────────────────────────────────────────────────────────────────────

search_knowledge_base(query: str) in tools/tools.py:
  
  1. Input: "My printer isn't printing"
  
  2. Generate embedding:
     embedding = embedding_model.encode(query)
     → Vector: [0.12, -0.45, 0.67, ...] (384 dims)
  
  3. ChromaDB Search:
     results = collection.query(
       query_embeddings=[embedding],
       n_results=1,
       where=None
     )
  
  4. ChromaDB calculates cosine similarity:
     similarity = dot_product(query_vector, doc_vector) / 
                  (||query_vector|| × ||doc_vector||)
     → Results normalized to 0.0-1.0
  
  5. Sort by similarity (descending)
  
  6. Return top_k=1 result:
     {
       "documents": ["Printer not printing"],
       "distances": [0.11],  # Inverse of similarity
       "embeddings": [...],
       "metadatas": [{
         "solution": "Check power...",
         "source": "Admin Approved"
       }]
     }
  
  7. Convert to result dict:
     result = {
       "confidence": 1 - distance = 0.89,
       "issue": "Printer not printing",
       "solution": "Check power...",
       "source": "Admin Approved"
     }
  
  8. Check threshold:
     if confidence >= 0.7:
       → Use this solution
     else:
       → Escalate or ask clarification
  
  9. Return formatted string:
     "Solution found (Confidence: 89%):\n\nCheck power..."

================================================================================
9. AUTHENTICATION & AUTHORIZATION
================================================================================

JWT TOKEN STRUCTURE:
──────────────────────────────────────────────────────────────────────────────

Header: Authorization: Bearer <token>

Token Payload (JWT encoded):
{
  "user_id": 1,
  "email": "john@example.com",
  "username": "john_doe",
  "role": "user",  # or "admin"
  "exp": 1705352400  # Unix timestamp (24h from issue)
}

Signed with: HS256 algorithm, JWT_SECRET from config

TOKEN GENERATION:
──────────────────────────────────────────────────────────────────────────────

On login/register:
  token = jwt.encode({
    'user_id': user['id'],
    'email': user['email'],
    'username': user['username'],
    'role': user['role'],
    'exp': datetime.utcnow() + timedelta(hours=24)
  }, JWT_SECRET, algorithm="HS256")

TOKEN VALIDATION:
──────────────────────────────────────────────────────────────────────────────

token_required decorator (in app.py):
  
  1. Extract token from header:
     token = request.headers['Authorization'].split(" ")[1]
  
  2. Decode and validate:
     data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
  
  3. Check expiration (automatically checked)
     if token.exp < now():
       raise ExpiredSignatureError
  
  4. Extract user info:
     request.user_id = data['user_id']
     request.user_email = data['email']
     request.user_role = data['role']
  
  5. Proceed to endpoint handler

ROLE-BASED AUTHORIZATION:
──────────────────────────────────────────────────────────────────────────────

User Role: "user"
  - Can chat with agent
  - Can view own tickets
  - Can create tickets (via escalation)
  - Cannot admin operations

Admin Role: "admin"
  - All user capabilities
  - Can view all tickets
  - Can update ticket status
  - Can add entries to KB
  - Can resolve tickets

Example Authorization Check:
  @app.route('/api/tickets', methods=['GET'])
  @token_required
  def get_all_tickets():
    if request.user_role != 'admin':
      return {"error": "Admin access required"}, 403
    ...

PASSWORD HASHING:
──────────────────────────────────────────────────────────────────────────────

On Registration:
  password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
  INSERT into users.password_hash

On Login:
  stored_hash = SELECT password_hash FROM users WHERE email = ?
  if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
    → Valid password

================================================================================
10. FRONTEND ARCHITECTURE
================================================================================

COMPONENT HIERARCHY:
──────────────────────────────────────────────────────────────────────────────

App.js (Root)
├── Login.jsx
│   ├── Register form
│   └── Login form
│
├── Chat.jsx (Main user interface)
│   ├── Message display area
│   ├── Input box
│   ├── Agent response handler
│   └── Ticket preview
│
└── AdminDashboard.jsx (Admin-only view)
    ├── Ticket list
    ├── Ticket detail
    ├── KB update form
    └── Status management

STATE MANAGEMENT:
──────────────────────────────────────────────────────────────────────────────

App.js (Parent):
  - currentUser: {id, username, email, role}
  - token: JWT token string
  - currentView: 'chat' | 'admin'
  - loading: boolean

Local Storage:
  - 'token': JWT token
  - 'user': JSON stringified user object

Session Management:
  - session_id: Maintained per chat session
  - conversation_state: Not in frontend (only backend)

API COMMUNICATION:
──────────────────────────────────────────────────────────────────────────────

All requests include JWT:
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }

Typical flow:
  1. User types message in Chat.jsx
  2. onClick handler
  3. Fetch POST /api/chat with message
  4. Response parsed
  5. Update UI with agent response
  6. Store session_id for next message
  7. Loop on user input

ERROR HANDLING:
──────────────────────────────────────────────────────────────────────────────

Frontend catches API errors:
  - 401: Token expired/invalid → redirect to login
  - 403: Unauthorized access → show error
  - 500: Server error → show error message
  - Network error → show offline message

================================================================================
11. COMPLETE REQUEST-RESPONSE CYCLE
================================================================================

SINGLE MESSAGE FLOW (Top to Bottom):
──────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. USER ACTION (Frontend - React)                                            │
└──────────────────────────────────────────────────────────────────────────────┘
   User types "My monitor isn't working" in Chat.jsx
   Click send button
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. API REQUEST (Frontend - Fetch)                                            │
└──────────────────────────────────────────────────────────────────────────────┘
   const response = await fetch('http://localhost:5000/api/chat', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer eyJ...',
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       message: "My monitor isn't working",
       session_id: 'session_xyz' or null
     })
   })
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. FLASK ROUTING (Backend - app.py)                                          │
└──────────────────────────────────────────────────────────────────────────────┘
   @app.route('/api/chat', methods=['POST'])
   @token_required  ← Validates JWT
   def chat():
       user_id = request.user_id (from token)
       user_email = request.user_email (from token)
       message = request.json['message']
       session_id = request.json.get('session_id')
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. SESSION MANAGEMENT (app.py → runners/run_agents.py)                       │
└──────────────────────────────────────────────────────────────────────────────┘
   if not session_id:
       session_id = asyncio.run(orchestrator.create_user_session(str(user_id)))
       ← Creates ADK session in InMemorySessionService
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. STATE RETRIEVAL (app.py)                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
   state_key = f"{user_id}_{session_id}"
   conversation_state = conversation_states.get(state_key)
   if not conversation_state:
       conversation_state = {
           'clarification_count': 0,
           'issue_summary': '',
           ...
       }
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 6. ORCHESTRATOR CALL (app.py → runners/run_agents.py)                        │
└──────────────────────────────────────────────────────────────────────────────┘
   result = asyncio.run(orchestrator.handle_user_query(
       user_id=user_id,
       user_email=user_email,
       session_id=session_id,
       message=message,
       conversation_state=conversation_state
   ))
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 7. DECISION LOGIC (runners/run_agents.py → handle_user_query)               │
└──────────────────────────────────────────────────────────────────────────────┘
   if conversation_state['clarification_count'] >= 2:
       ← Run escalation directly
   else:
       ← Run self-service agent
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 8. AGENT EXECUTION (Google ADK)                                              │
└──────────────────────────────────────────────────────────────────────────────┘
   self_service_agent.run_async(
       user_id=user_id,
       session_id=session_id,
       new_message=content
   )
   ← Agent thinks, plans, calls tools
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 9. TOOL EXECUTION (tools/tools.py)                                           │
└──────────────────────────────────────────────────────────────────────────────┘
   Tool: search_knowledge_base("My monitor isn't working")
   ← Queries ChromaDB
   ← Returns solution with confidence
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 10. AGENT RESPONSE (Google ADK)                                              │
└──────────────────────────────────────────────────────────────────────────────┘
    Agent receives tool result
    Composes final response
    Returns to orchestrator
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 11. RESPONSE PROCESSING (runners/run_agents.py)                             │
└──────────────────────────────────────────────────────────────────────────────┘
    Checks for signals:
    - "ESCALATE_TO_HUMAN" ?
    - "CLARIFICATION_NEEDED:" ?
    ← Updates conversation_state
    ← Returns dict with response
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 12. DATABASE SAVE (db/postgres.py)                                           │
└──────────────────────────────────────────────────────────────────────────────┘
    db.save_conversation(
        user_id=user_id,
        session_id=session_id,
        user_message=message,
        agent_response=response
    )
    ← INSERT into conversation_history
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 13. FLASK RESPONSE (app.py)                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
    conversation_states[state_key] = conversation_state
    return jsonify({
        'success': true,
        'response': 'Agent response text...',
        'session_id': session_id,
        'agent': 'self_service',
        'escalated': false,
        ...
    })
     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 14. FRONTEND UPDATE (Chat.jsx)                                               │
└──────────────────────────────────────────────────────────────────────────────┘
    Receive JSON response
    Parse response
    this.setState({
        messages: [..., {role: 'agent', text: response}],
        session_id: session_id
    })
    ← Renders new message in chat
    ← Re-enables input
    User sees response and can continue

Total Time: ~1-3 seconds (network + agent + DB)

================================================================================
12. KEY TECHNOLOGIES & LIBRARIES
================================================================================

BACKEND:
──────────────────────────────────────────────────────────────────────────────
Flask: Web framework and REST API
PyJWT: JWT token generation and validation
bcrypt: Password hashing
psycopg2: PostgreSQL adapter
ChromaDB: Semantic search vector database
SentenceTransformers: Embedding model (all-MiniLM-L6-v2)
Google ADK: Multi-agent orchestration framework
Google Genai: Gemini API integration
LiteLlm: LLM provider abstraction
Groq SDK: Groq API client
SMTP/smtplib: Email notifications

FRONTEND:
──────────────────────────────────────────────────────────────────────────────
React: UI framework
CSS: Styling

DATABASE:
──────────────────────────────────────────────────────────────────────────────
PostgreSQL: Main relational database
ChromaDB: Vector database for embeddings

================================================================================
13. CONFIGURATION & ENVIRONMENT
================================================================================

Key Environment Variables (config.py):
──────────────────────────────────────────────────────────────────────────────
FLASK_PORT: 5000
FLASK_DEBUG: True/False

POSTGRES_HOST: localhost
POSTGRES_PORT: 5432
POSTGRES_DB: ticketdb
POSTGRES_USER: postgres
POSTGRES_PASSWORD: shyam123

GEMINI_API_KEY: Google Gemini API key
LLM_PROVIDER: 'groq' or 'xai'
GROQ_API_KEY: Groq API key
XAI_API_KEY: xAI API key

JWT_SECRET: Secret for JWT signing
SMTP_HOST: smtp.gmail.com
SMTP_PORT: 587
SMTP_USER: email@gmail.com
SMTP_PASSWORD: app password

CHROMA_PERSIST_DIR: kb/chroma_db (local storage)
EMBEDDING_MODEL: all-MiniLM-L6-v2 (HuggingFace model)

MAX_CLARIFICATION_ATTEMPTS: 2
KB_CONFIDENCE_THRESHOLD: 0.7

================================================================================
14. ERROR HANDLING & LOGGING
================================================================================

LOGGING STRATEGY:
──────────────────────────────────────────────────────────────────────────────

Configured in each module:
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  logger = logging.getLogger(__name__)

Log Levels Used:
  - INFO: Normal operations, user actions, agent calls
  - ERROR: Exceptions, failed operations, DB errors
  - DEBUG: Not enabled in current config (can be enabled)

Key Logged Events:
  - User registration/login
  - Agent execution start/completion
  - KB search results
  - Ticket creation
  - Database operations
  - API errors
  - Configuration initialization

ERROR RESPONSES:
──────────────────────────────────────────────────────────────────────────────

400 Bad Request:
  {
    "success": false,
    "error": "message is required"
  }

401 Unauthorized:
  {
    "success": false,
    "error": "Token is missing" or "Token has expired"
  }

403 Forbidden:
  {
    "success": false,
    "error": "Admin access required"
  }

404 Not Found:
  {
    "success": false,
    "message": "User/Ticket not found"
  }

500 Server Error:
  {
    "success": false,
    "error": "Exception message"
  }

================================================================================
15. DEPLOYMENT & SCALABILITY CONSIDERATIONS
================================================================================

CURRENT ARCHITECTURE LIMITATIONS:
──────────────────────────────────────────────────────────────────────────────
1. In-memory conversation state (conversation_states dict)
   - Lost on server restart
   - Not shared across multiple server instances
   - Solution: Use Redis or database session store

2. SQLite session storage for ADK
   - Limited concurrency
   - Solution: Use database backend

3. SMTP email notifications (optional)
   - Requires external email provider
   - Current: Disabled if not configured

4. Single LLM provider per agent
   - No fallback to alternative model
   - Solution: Implement provider switching

SCALABILITY IMPROVEMENTS:
──────────────────────────────────────────────────────────────────────────────

For Production:
  1. Use persistent session store (PostgreSQL or Redis)
  2. Implement distributed agent sessions
  3. Add request queuing for agent processing
  4. Cache KB search results
  5. Use connection pooling for database
  6. Implement rate limiting on API endpoints
  7. Add monitoring and alerting
  8. Use container orchestration (Docker/Kubernetes)
  9. Implement CI/CD pipeline
  10. Add comprehensive testing

================================================================================
16. SYSTEM INTERACTION DIAGRAM
================================================================================

                              ┌─────────────────────┐
                              │  Frontend (React)   │
                              │  - Chat.jsx         │
                              │  - AdminDashboard   │
                              │  - Login.jsx        │
                              └──────────┬──────────┘
                                         │ HTTP/JSON
                                         ↓
                    ┌────────────────────────────────────┐
                    │  Flask REST API (app.py)           │
                    │  - /api/chat                       │
                    │  - /api/auth/*                     │
                    │  - /api/tickets/*                  │
                    │  - /api/kb/*                       │
                    │  - JWT Authentication              │
                    └────────┬──────────────┬────────────┘
                             │              │
                    ↓        ↓              ↓
        ┌─────────────────────┐   ┌──────────────────────┐
        │ Agent Orchestrator  │   │   PostgreSQL DB      │
        │ (runners/run_agents)│   │  - users             │
        │  - Handle flow      │   │  - tickets           │
        │  - Create sessions  │   │  - conversation_*    │
        │  - Route agents     │   │  - kb_updates        │
        └────────┬────────────┘   └──────────────────────┘
                 │
        ┌────────┴────────┬──────────────┐
        ↓                 ↓              ↓
    ┌──────────┐  ┌──────────┐   ┌──────────────┐
    │ Self-    │  │Escalation│   │  ADK Runtime │
    │Service   │  │ Agent    │   │ (Sessions)   │
    │Agent     │  │          │   │              │
    │(Gemini)  │  │ (Gemini) │   │              │
    └────┬─────┘  └────┬─────┘   └──────────────┘
         │             │
         ├─────┬───────┘
         ↓     ↓
    ┌─────────────────────────┐
    │  Tools                  │
    │ - search_knowledge_base │
    │ - ask_clarification     │
    │ - create_ticket         │
    │ - update_ticket_status  │
    │ - send_email_notification
    └────────┬────────────────┘
             │
             ↓
    ┌─────────────────────────┐
    │  Knowledge Base (KB)    │
    │  - ChromaDB             │
    │  - SentenceTransformers │
    │  - Semantic Search      │
    │  - Embeddings           │
    └─────────────────────────┘

================================================================================
17. SUMMARY
================================================================================

This IT Support Ticket System is an intelligent multi-agent application that:

1. ACCEPTS user queries through a React frontend
2. AUTHENTICATES via JWT tokens
3. ROUTES queries through AI agents (Google ADK Gemini)
4. SEARCHES semantic knowledge base for solutions
5. PROVIDES solutions when confidence is high
6. ASKS CLARIFICATIONS when confidence is low
7. ESCALATES to human support after 2 clarifications or on request
8. CREATES tickets in PostgreSQL for escalated issues
9. MAINTAINS conversation history for audit and training
10. ALLOWS admins to manage tickets and update KB
11. USES embeddings for semantic similarity matching
12. ORCHESTRATES multi-agent workflows efficiently

Data flows from frontend → API → Orchestrator → Agents → Tools → DB/KB → Response

All interactions are logged, authenticated, and stored for compliance and analysis.

================================================================================ 

EOF
