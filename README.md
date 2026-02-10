# IT Support Ticket System 🎫

An enterprise-grade, intelligent AI-powered IT support ticket system that automates issue resolution using multi-agent AI architecture with semantic knowledge base search, real-time feedback collection, and comprehensive escalation workflows.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Key Features

### 🤖 **Intelligent Multi-Agent AI System**
- **Two-Stage Agent Architecture**: Self-Service Agent → Escalation Agent
- **Google ADK + Gemini 2.5 Flash**: Advanced orchestration and natural language understanding
- **Context-Aware Responses**: Maintains conversation history and state across sessions
- **Smart Escalation Detection**: Automatically detects when human intervention is needed

### 🔍 **Advanced Knowledge Management**
- **Semantic Search**: ChromaDB-based vector database with cosine similarity matching
- **GPU-Accelerated Embeddings**: SentenceTransformers with CUDA support (3-5x faster)
- **Dynamic KB Updates**: Add solutions from resolved tickets to knowledge base
- **Category-Based Navigation**: Structured navigation with Hardware, Software, and Access categories

### 🎫 **Comprehensive Ticket Management**
- **Dual Ticket Types**: Incident (fix broken things) and Request (new requirements)
- **4-Tier Priority System**: P4 (Low), P3 (Medium), P2 (High), Critical
- **SLA Tracking**: Automated SLA deadline calculation and breach monitoring
- **Status Workflow**: Open → In Progress → Pending Approval → Approved → Resolved → Closed
- **Manager Approval Flow**: Built-in approval system for access requests

### 📎 **Rich Media Support**
- **Multi-Image Attachments**: Upload up to 5 images per ticket
- **Cloudinary Integration**: Secure cloud storage with CDN delivery
- **Image Preview**: Full-screen image gallery in admin dashboard
- **Support for Multiple Formats**: JPEG, PNG, GIF, WebP (up to 5MB each)

### 📊 **Advanced Analytics & Monitoring**
- **Real-Time Dashboard**: Live ticket statistics and SLA monitoring
- **Performance Metrics**: Average resolution time, ticket volume trends
- **Technician Workload**: Track assigned/resolved tickets per technician
- **Visual Analytics**: Chart.js integration for data visualization

### 💬 **User Feedback System**
- **Star Ratings (1-5)**: Collect overall experience ratings
- **Per-Solution Feedback**: Thumbs up/down for each solution step
- **Text Feedback**: Optional detailed comments
- **Feedback Analytics**: Track solution effectiveness and user satisfaction

### 🔐 **Enterprise Security**
- **JWT-Based Authentication**: Secure token-based auth with 24-hour expiration
- **Role-Based Access Control**: User, Technician, Manager, Admin roles
- **Password Hashing**: Bcrypt for secure password storage
- **Security Headers**: XSS protection, CSRF protection, content security policy

### 👥 **Technician Management**
- **Shift-Based Scheduling**: Track technician availability with shift timings (IST)
- **Workload Balancing**: Monitor assigned vs. resolved ticket counts
- **Specialization Tags**: Assign tickets based on technician expertise
- **Department Organization**: Multi-department support structure

### 🚀 **Performance Optimizations**
- **GPU Acceleration**: PyTorch CUDA support for embedding generation
- **Request Performance Monitoring**: Automatic slow request detection (>1s)
- **Efficient Session Management**: SQLite-based agent session storage
- **Optimized Database Queries**: Indexed columns for faster lookups

### 📧 **Communication & Notifications**
- **Email Integration**: SMTP support for ticket notifications
- **Real-Time Updates**: Live status changes in dashboard
- **Audit Trails**: Complete history of ticket modifications
- **Conversation History**: Full chat transcripts with timestamps

## 🛠 Tech Stack

### **Backend**
- **Framework**: Flask 3.0.0 (REST API)
- **Database**: PostgreSQL 12+ (with array support for attachments)
- **Vector Database**: ChromaDB 0.4.22
- **AI/ML**: 
  - Google ADK 1.0.0 (Agent orchestration)
  - Gemini 2.5 Flash (LLM)
  - LiteLLM 1.66.3 (Multi-provider support)
  - SentenceTransformers 2.2.2 (Embeddings)
  - PyTorch 2.0+ (GPU acceleration)
- **Image Storage**: Cloudinary 1.36.0
- **Authentication**: PyJWT 2.8.1 + BCrypt 4.1.1
- **ORM**: SQLAlchemy 2.0.23
- **Database Driver**: psycopg2-binary 2.9.9

### **Frontend (User Portal)**
- **Framework**: React 18.2.0
- **HTTP Client**: Axios 1.6.0
- **Build Tool**: Create React App 5.0.1
- **Styling**: Pure CSS with responsive design

### **Admin Dashboard**
- **Framework**: React 19.2.0
- **Build Tool**: Vite 5.x
- **Routing**: React Router DOM 7.13.0
- **Charts**: Chart.js 4.5.1 + React-ChartJS-2 5.3.1
- **Icons**: Lucide React 0.563.0
- **Date Handling**: date-fns 4.1.0

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.8 or higher ([Download](https://www.python.org/downloads/))
- **Node.js** 14 or higher and npm ([Download](https://nodejs.org/))
- **PostgreSQL** 12 or higher ([Download](https://www.postgresql.org/download/))
- **Git** ([Download](https://git-scm.com/downloads))
- **NVIDIA GPU with CUDA** (Optional, but recommended for 3-5x faster embeddings)

### **Required API Keys**
- **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Cloudinary Account** - Free tier: 25GB storage, 25GB bandwidth/month ([Sign up](https://cloudinary.com))

### **Optional**
- **SMTP Credentials** - For email notifications
- **CUDA Toolkit** - For GPU acceleration

---

## 🚀 Installation Guide

### **Step 1: Clone the Repository**

```bash
git clone https://github.com/bssshyamsundhar/Ticket_system.git
cd Ticket_system
```

### **Step 2: Backend Setup**

#### **2.1 Create Virtual Environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### **2.2 Install Python Dependencies**

```bash
pip install -r requirements.txt
```

**For GPU Support (Recommended for 3-5x faster embeddings):**

```bash
# Install PyTorch with CUDA 12.1 support
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Verify GPU detection
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

#### **2.3 Configure Environment Variables**

Create a `.env` file in the project root:

```bash
# Linux/Mac
cp .env.example .env

# Windows - Or create manually
type nul > .env
```

Edit `.env` with your actual credentials:

```env
# ============================================
# Flask Configuration
# ============================================
FLASK_PORT=5000
FLASK_DEBUG=True
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# ============================================
# PostgreSQL Configuration
# ============================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticketdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

# ============================================
# Google Gemini API (Required)
# ============================================
GEMINI_API_KEY=your_google_gemini_api_key_here

# ============================================
# LLM Provider Configuration
# ============================================
# Choose: 'groq' (recommended) or 'xai'
LLM_PROVIDER=groq

# If using Groq (Fast & Free tier available)
GROQ_API_KEY=your_groq_api_key_here

# If using xAI Grok
XAI_API_KEY=your_xai_api_key_here

# ============================================
# Cloudinary Configuration (Required)
# ============================================
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

# ============================================
# SMTP Email Configuration (Optional)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=support@company.com
```

**Getting API Keys:**

1. **Google Gemini**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) → Create API key
2. **Cloudinary**: Sign up at [Cloudinary.com](https://cloudinary.com) → Dashboard → Copy Cloud Name, API Key, Secret
3. **Groq** (Optional): Visit [Groq Console](https://console.groq.com) → Create API key (Free tier)

### **Step 3: Database Setup**

#### **3.1 Create PostgreSQL Database**

```bash
# Using psql command line
psql -U postgres

# Inside PostgreSQL, create database  
CREATE DATABASE ticketdb;

# Exit PostgreSQL
\q
```

**Or using pgAdmin GUI:**
- Right-click on "Databases"
- Select "Create" → "Database"
- Name: `ticketdb`
- Save

#### **3.2 Initialize Database Schema**

```bash
# Run schema creation script
psql -U postgres -d ticketdb -f db/schema.sql
```

This creates all database tables:

**Core Tables:**
- `users` - End users who create tickets
- `technicians` - Support staff with shift timings (IST)
- `tickets` - Ticket records with multi-image support (`attachment_urls TEXT[]`)
- `ticket_feedback` - Star ratings (1-5) and text feedback
- `solution_feedback` - Per-solution thumbs up/down tracking
- `conversation_history` - Complete chat transcripts with timestamps

**Configuration Tables:**
- `sla_config` - Priority-based SLA rules (P4/P3/P2/Critical)
- `priority_rules` - Auto-priority assignment based on keywords
- `kb_categories` - Knowledge base category structure

**Management Tables:**
- `knowledge_articles` - KB entries for admin management
- `audit_logs` - Complete change tracking and audit trails
- `kb_updates` - History of KB modifications

#### **3.3 Seed Initial Data (Recommended)**

```bash
python scripts/seed_data.py
```

This populates:
- ✅ Default user accounts (admin, manager, technician, user)
- ✅ SLA configurations (P4: 72h, P3: 48h, P2: 24h, Critical: 4h)
- ✅ Priority auto-assignment rules
- ✅ Initial KB categories (Hardware, Software, Access, Network, etc.)
- ✅ Sample technicians with shift timings

### **Step 4: Knowledge Base Initialization**

```bash
# Populate knowledge base with sample IT solutions
python scripts/populate_kb.py
```

This process:
- Creates ChromaDB vector database in `kb/chroma_db/`
- Generates embeddings for all knowledge articles
- Indexes solutions by category (Hardware, Software, Access, Network, Email)
- **Uses GPU if available** for 3-5x faster embedding generation

**Note**: Initial population takes ~30-60 seconds (or 10-15 seconds with GPU).

### **Step 5: Frontend Setup (User Portal)**

```bash
cd frontend
npm install
cd ..
```

Installs:
- React 18.2.0
- Axios for API communication
- React Scripts for development server

### **Step 6: Admin Dashboard Setup**

```bash
cd dashboard/dashboard
npm install
cd ../..
```

Installs:
- React 19.2.0
- Vite for fast development
- Chart.js for analytics
- React Router for navigation
- Lucide React for icons

---

## 🎮 Running the Application

### **Method 1: Manual Start (Recommended for Development)**

Open **3 separate terminal windows**:

#### **Terminal 1: Backend API Server**

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start Flask backend
python app.py
```

✅ Backend API: `http://localhost:5000`

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * CUDA Available: True (if GPU detected)
 * Knowledge Base: 150 articles loaded
 * Database: Connected
```

#### **Terminal 2: User Frontend Portal**

```bash
cd frontend
npm start
```

✅ User Portal: `http://localhost:3000`

**Features:**
- User authentication
- AI-powered chat interface
- Ticket creation with image upload
- Real-time status tracking
- Feedback submission

#### **Terminal 3: Admin Dashboard**

```bash
cd dashboard/dashboard
npm run dev
```

✅ Admin Dashboard: `http://localhost:5173`

**Features:**
- Ticket management (view, assign, update status)
- SLA monitoring with countdown timers
- Technician workload tracking
- Analytics and reporting (Chart.js)
- Knowledge base management
- Audit logs and conversation history
- Image attachments viewer

### **Method 2: PowerShell Script (Windows Only)**

Create `start_all.ps1`:

```powershell
# Start Backend
Write-Host "Starting Backend API..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python app.py"

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting User Portal..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm start"

Start-Sleep -Seconds 2

# Start Dashboard
Write-Host "Starting Admin Dashboard..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\dashboard\dashboard'; npm run dev"

Write-Host "`nAll services started!" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:5000" -ForegroundColor Yellow
Write-Host "User Portal: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Admin Dashboard: http://localhost:5173" -ForegroundColor Yellow
```

Run: `.\start_all.ps1`

---

## 👤 Default Login Credentials

After running `seed_data.py`, login with these accounts:

### **User Portal** (`http://localhost:3000`)

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| End User | `john.doe@company.com` | `password123` | Create tickets, chat with AI |
| End User | `jane.smith@company.com` | `password123` | Test multiple users |

### **Admin Dashboard** (`http://localhost:5173`)

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Admin | `admin@company.com` | `admin123` | Full system access, analytics |
| Manager | `manager@company.com` | `manager123` | Approval workflows, reports |
| Technician | `tech@company.com` | `tech123` | Ticket resolution, KB updates |

> ⚠️ **SECURITY WARNING**: Change all default passwords before production deployment!

```bash
# Use this script to update passwords
python scripts/fix_password.py
```

---

## 📖 Usage Guide

### **For End Users (User Portal)**

1. **Login**: Access `http://localhost:3000` with user credentials
2. **Choose Ticket Type**:
   - 🔧 **Incident**: Something is broken (e.g., laptop not working, email issues)
   - 📝 **Request**: Need something new (e.g., software installation, access requests)

3. **Select Category & Issue**:
   - Navigate through categories (Hardware, Software, Access, Network, Email)
   - Select specific issue type from the list
   - Or use "Other Issue" for free-text description

4. **AI-Powered Resolution**:
   - Receive instant solutions from knowledge base
   - View step-by-step troubleshooting instructions
   - Rate each solution step (👍/👎)

5. **Escalation** (if needed):
   - AI automatically escalates if solution doesn't work
   - Or click "Create Ticket" button manually
   - Upload up to 5 screenshots (PNG, JPEG, GIF, WebP, max 5MB each)

6. **Provide Feedback**:
   - Rate your experience (1-5 stars)
   - Add optional text feedback
   - Help improve the system

7. **Track Tickets**:
   - View "My Tickets" to see all your requests
   - Monitor status: Open → In Progress → Resolved → Closed
   - Receive SLA deadline notifications

### **For Technicians (Admin Dashboard)**

1. **Login**: Access `http://localhost:3001` with technician credentials

2. **Ticket Management**:
   - View assigned tickets in dashboard
   - Filter by status, priority, category
   - See SLA countdown timers (🟢 Safe, 🟡 Warning, 🔴 Breached)

3. **Resolve Tickets**:
   - Click ticket to view full details
   - View attached images in grid (click for full-screen)
   - Read conversation history
   - Update status: In Progress → Pending Approval → Resolved
   - Add resolution notes

4. **Knowledge Base Updates**:
   - Add new solutions from resolved tickets
   - Update existing KB articles
   - Improve AI response quality

5. **Workload Management**:
   - View assigned vs. resolved ticket counts
   - Monitor average resolution time
   - Track personal performance metrics

### **For Managers (Admin Dashboard)**

1. **Approval Workflows**:
   - Review "Pending Approval" tickets (Access Requests, Software Install)
   - Approve or reject with comments
   - Track approval timestamps

2. **Analytics & Reporting**:
   - View ticket volume trends (Chart.js visualizations)
   - Monitor SLA compliance rates
   - Analyze category-wise ticket distribution
   - Track technician performance

### **For Administrators**

1. **System Configuration**:
   - Manage SLA rules (P4/P3/P2/Critical)
   - Configure priority auto-assignment keywords
   - Set up technician shifts and specializations

2. **User Management**:
   - Create/edit user accounts
   - Assign roles (User, Technician, Manager, Admin)
   - Reset passwords

3. **Audit & Compliance**:
   - Review audit logs (all ticket changes)
   - Export conversation history
   - Monitor system health and performance

---

## 🔌 API Endpoints

### **Authentication**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/login` | User login (returns JWT token) | No |
| POST | `/api/register` | New user registration | No |
| GET | `/api/verify-token` | Verify JWT token validity | Yes |

**Request Body (Login):**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "USR001",
    "name": "John Doe",
    "email": "user@example.com",
    "role": "user"
  }
}
```

### **Chat & AI Agent**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/chat` | Send message to AI agent | Yes |

**Request Body:**
```json
{
  "action": "start|select_category|free_text|confirm_ticket",
  "value": "Hardware|Software|...",
  "message": "User's text input",
  "session_id": "unique_session_id",
  "attachment_urls": ["https://...jpg", "https://...png"]
}
```

**Response:**
```json
{
  "success": true,
  "response": "AI agent response text (with **markdown**)",
  "buttons": [
    {"label": "Hardware", "action": "select_category", "value": "Hardware"}
  ],
  "state": "categories|awaiting_input|end",
  "session_id": "ABC123",
  "ticket_id": "TKT001",
  "show_star_rating": false,
  "show_text_input": false,
  "solutions_with_feedback": [
    {"index": 1, "text": "First solution step"},
    {"index": 2, "text": "Second solution step"}
  ]
}
```

### **Image Upload**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/upload/image` | Upload single image to Cloudinary | Yes |

**Request (Multipart):**
```bash
curl -X POST http://localhost:5000/api/upload/image \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@screenshot.png"
```

**Response:**
```json
{
  "success": true,
  "url": "https://res.cloudinary.com/.../.../image.jpg",
  "public_id": "tickets/img_abc123"
}
```

### **Tickets**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/tickets` | Get all tickets (admin/technician) | Yes (admin) |
| GET | `/api/tickets/user/<user_id>` | Get user's tickets | Yes |
| GET | `/api/tickets/<ticket_id>` | Get single ticket details | Yes |
| PUT | `/api/tickets/<ticket_id>/status` | Update ticket status | Yes (tech) |
| PUT | `/api/tickets/<ticket_id>/assign` | Assign to technician | Yes (admin) |
| POST | `/api/tickets/<ticket_id>/approve` | Approve/reject ticket | Yes (manager) |

**Ticket Object:**
```json
{
  "id": "TKT001",
  "user_id": "USR001",
  "user_name": "John Doe",
  "ticket_type": "Incident",
  "category": "Hardware",
  "subcategory": "Laptop",
  "priority": "P3",
  "status": "In Progress",
  "subject": "Laptop won't start",
  "description": "My laptop shows black screen...",
  "attachment_urls": [
    "https://res.cloudinary.com/...jpg",
    "https://res.cloudinary.com/...png"
  ],
  "assigned_to": "John Tech",
  "sla_deadline": "2026-02-10T18:00:00Z",
  "sla_breached": false,
  "created_at": "2026-02-09T10:00:00Z",
  "resolved_at": null
}
```

### **Feedback**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/feedback/ticket` | Submit star rating & text feedback | Yes |
| POST | `/api/feedback/solution` | Submit per-solution feedback (👍/👎) | Yes |
| GET | `/api/feedback/stats` | Get feedback statistics | Yes (admin) |

**Feedback Request:**
```json
{
  "ticket_id": "TKT001",
  "rating": 4,
  "comments": "Great solution, fixed my issue!",
  "session_id": "ABC123"
}
```

### **Knowledge Base**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/kb/search` | Search knowledge base | Yes |
| POST | `/api/kb/update` | Add new KB article | Yes (admin) |
| GET | `/api/kb/categories` | Get all categories | Yes |
| DELETE | `/api/kb/<article_id>` | Delete KB article | Yes (admin) |

**KB Search Request:**
```json
{
  "query": "laptop not starting",
  "category": "Hardware",
  "top_k": 5
}
```

**KB Search Response:**
```json
{
  "success": true,
  "results": [
    {
      "issue": "Laptop won't turn on",
      "solution": "1. Check power adapter...\n2. Hold power button...",
      "category": "Hardware",
      "confidence": 0.85
    }
  ]
}
```

### **Technicians**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/technicians` | Get all technicians | Yes |
| GET | `/api/technicians/<tech_id>` | Get technician details | Yes |
| PUT | `/api/technicians/<tech_id>` | Update technician info | Yes (admin) |
| GET | `/api/technicians/available` | Get on-shift technicians | Yes |

### **Analytics**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/analytics/dashboard` | Get dashboard stats | Yes (admin) |
| GET | `/api/analytics/tickets/trends` | Ticket volume trends | Yes (admin) |
| GET | `/api/analytics/sla` | SLA compliance metrics | Yes (admin) |
| GET | `/api/analytics/feedback` | Feedback analysis | Yes (admin) |

**Dashboard Stats Response:**
```json
{
  "total_tickets": 150,
  "open_tickets": 25,
  "in_progress": 30,
  "resolved_today": 12,
  "sla_breached": 3,
  "avg_resolution_time": "4.5 hours",
  "user_satisfaction": 4.2
}
```

---
- `GET /api/tickets/<ticket_id>` - Get single ticket
- `PUT /api/tickets/<ticket_id>/status` - Update ticket status

### Knowledge Base
- `POST /api/kb/update` - Add KB entry (admin)
- `POST /api/kb/search` - Search knowledge base

## Project Structure
 (includes torch & cloudinary)
├── agents/                # AI agent definitions
│   ├── self_service/      # First-line support agent
│   └── escalation/        # Escalation confirmation agent
├── db/                    # Database layer
│   ├── schema.sql         # PostgreSQL schema (with attachment_urls array)
│   └── postgres.py        # Database operations
├── kb/                    # Knowledge base
│   ├── kb_chroma.py       # ChromaDB wrapper
│   ├── embedding.py       # GPU-accelerated embeddings
│   └── data/              # Initial KB data
├── runners/               # Agent orchestration
│   └── run_agents.py      # Multi-agent workflow
├── tools/                 # Agent tools
│   └── tools.py           # KB search, clarification, ticket creation
├── services/              # External services
│   ├── email_service.py   # SMTP notifications
│   └── cloudinary_service.py  # Image upload/storage
├── frontend/              # React frontend
│   └── src/
│       ├── components/    # UI components (Chat with multi-image upload)
│       └── pages/         # Page components
├── dashboard/             # Admin dashboard (React + Vite)
│   └── dashboard/src/
│       └── pages/         # Tickets with image grid display
└──🐛 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env`
- Ensure `ticketdb` database exists

### Database Migration (For Existing Installations)
If upgrading from a previous version without multi-image support:

```bash
python scripts/add_attachment_column.py
```

Or manually:
```sql
ALTER TABLE tickets DROP COLUMN IF EXISTS attachment_url;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS attachment_urls TEXT[];
```

###🔧 Development

### Reset Database
```bash
python scripts/reset_database.py
```

### Test API Endpoints
```bash
# Windows
.\scripts\test_api.ps1

# Or use curl/Postman
```

### Add New KB Entries
1. Admin dashboard → Resolved ticket → "Add to KB"
2. Or use API: `POST /api/kb/update`

### Test Image Upload
```bash
# Using curl
curl -X POST http://localhost:5000/api/upload/image \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@screenshot.png"
```

## 🎨 Recent Updates

### v2.0.0 (February 2026)
- ✅ **Multi-Image Attachments**: Upload up to 5 images per ticket
- ✅ **Cloudinary Integration**: Secure cloud storage with CDN
- ✅ **GPU Acceleration**: PyTorch CUDA support for 3-5x faster embeddings
- ✅ **Enhanced UI**: Image grid display in admin dashboard
- ✅ **Database Migration**: Support for multiple attachments with PostgreSQL arrays
- ✅ **Improved UX**: Attachment upload at ticket confirmation step onlyisready`
- Check credentials in `.env`
- Ensure `ticketdb` database exists

### ChromaDB Errors
- Delete and recreate: `python scripts/reset_chromadb.py`
- Repopulate: `python scripts/populate_kb.py`

### API Key Issues
- Verify `GOOGLE_API_KEY` or `GROQ_API_KEY` in `.env`
- Check API quota and billing

### Port Already in Use
- Change `FLASK_PORT` in `.env`
- Kill process: `netstat -ano | findstr :5000` (Windows)

## Development

### Reset Database
```bash
python scripts/reset_database.py
```

### Test API Endpoints
```bash
# Windows
.\scripts\test_api.ps1

# Or use curl/Postman
```

### Add New KB Entries
1. Admin dashboard → Resolved ticket → "Add to KB"
2. Or use API: `POST /api/kb/update`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

This project is licensed under the **MIT License** - see LICENSE file for details.

Copyright (c) 2026 Shyam Sundhar

---

## 📞 Support & Contact

### **Get Help**

- 📧 **Email**: bssshyamsundhar@gmail.com
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/bssshyamsundhar/Ticket_system/issues)
- 💡 **Feature Requests**: Submit via GitHub Issues
- 📖 **Technical Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md)

### **Response Times**

- Critical bugs: Within 24 hours
- Feature requests: Within 1 week
- General questions: Within 3 days

---

## 📚 Additional Resources

- **Google ADK Documentation**: [Google AI Developer Kit](https://ai.google.dev/adk)
- **ChromaDB Guide**: [ChromaDB Docs](https://docs.trychroma.com/)
- **Cloudinary API**: [Cloudinary Documentation](https://cloudinary.com/documentation)
- **React Documentation**: [React.dev](https://react.dev/)
- **PostgreSQL Manual**: [PostgreSQL Docs](https://www.postgresql.org/docs/)
- **Flask Documentation**: [Flask Docs](https://flask.palletsprojects.com/)

---

## 🙏 Acknowledgments

- **Google AI** - Gemini 2.5 Flash LLM & ADK framework
- **ChromaDB** - Vector database for semantic search
- **Cloudinary** - Media management & CDN services
- **PostgreSQL** - Robust enterprise database
- **React Community** - Frontend framework
- **Open Source Contributors** - For inspiration and tools

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Total Lines of Code | ~15,000+ |
| Backend Files | 50+ |
| Frontend Components | 30+ |
| Database Tables | 13 |
| API Endpoints | 40+ |
| Knowledge Categories | 10+ |
| Default KB Articles | 150+ |
| Max Attachments/Ticket | 5 images |
| Supported Image Formats | PNG, JPEG, GIF, WebP |
| JWT Token Expiry | 24 hours |
| Max Image Size | 5MB |
| Priority Levels | 4 (P4, P3, P2, Critical) |
| Ticket Types | 2 (Incident, Request) |

---

## 🎯 Roadmap

### **Phase 1: Q1 2026** (In Progress)
- [x] Multi-image attachments
- [x] User feedback system
- [x] Per-solution feedback
- [x] Manager approval workflow
- [ ] Mobile responsive improvements
- [ ] WhatsApp integration

### **Phase 2: Q2 2026** (Planned)
- [ ] Mobile app (React Native)
- [ ] Voice assistant support
- [ ] Multi-language support (i18n)
- [ ] Slack/Teams integration
- [ ] Video attachment support

### **Phase 3: Q3 2026** (Planned)
- [ ] ML-based ticket auto-routing
- [ ] Knowledge base auto-learning
- [ ] Predictive SLA breach alerts
- [ ] Custom workflow builder
- [ ] Advanced reporting & exports
- [ ] Dark mode theme

---

**Built with ❤️ by [Shyam Sundhar](https://github.com/bssshyamsundhar)**

⭐ **Star this repo** if you find it helpful!

🔔 **Watch** for updates and new releases!

🍴 **Fork** to customize for your organization!

---

*Last Updated: February 2026 - Version 2.5.0*

