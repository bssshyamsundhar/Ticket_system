# IT Support Ticket System

An intelligent AI-powered IT support ticket system that automates issue resolution using multi-agent AI architecture with semantic knowledge base search and escalation workflows.

## Features

- 🤖 **AI-Powered Support**: Two-stage agent system (Self-Service → Escalation)
- 🔍 **Semantic Search**: ChromaDB-based knowledge base with vector embeddings
- 🎫 **Automated Ticketing**: Smart escalation with ticket creation
- 🔐 **Secure Authentication**: JWT-based auth with role management
- 💬 **Conversation History**: Full chat tracking and audit trails
- 📊 **Admin Dashboard**: Ticket management and KB updates
- 📧 **Email Notifications**: SMTP integration for alerts

## Tech Stack

**Backend:**
- Flask (REST API)
- PostgreSQL (Database)
- ChromaDB (Vector DB)
- Google ADK + Gemini AI (Multi-agent orchestration)
- SentenceTransformers (Embeddings)

**Frontend:**
- React
- CSS

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js 14+ and npm
- Git
- Google Gemini API Key (or Groq API Key)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bssshyamsundhar/Ticket_system.git
cd Ticket_system
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticketdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# LLM Provider
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Optional: SMTP for email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Database Setup

#### Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ticketdb;
\q
```

#### Initialize Schema

```bash
psql -U postgres -d ticketdb -f db/schema.sql
```

#### Seed Initial Data (Optional)

```bash
python scripts/seed_data.py
```

### 4. Knowledge Base Setup

Populate the initial knowledge base:

```bash
python scripts/populate_kb.py
```

### 5. Frontend Setup

#### Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### Install Dashboard Dependencies (Optional)

```bash
cd dashboard/dashboard
npm install
cd ../..
```

## Running the Application

### Start Backend Server

```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Run Flask server
python app.py
```

Backend will run on: `http://localhost:5000`

### Start Frontend (Development)

Open a new terminal:

```bash
cd frontend
npm start
```

Frontend will run on: `http://localhost:3000`

### Start Admin Dashboard (Optional)

Open another terminal:

```bash
cd dashboard/dashboard
npm run dev
```

Dashboard will run on: `http://localhost:5173`

## Default Credentials

**Admin Account:**
- Email: `admin@company.com`
- Password: `admin123`

**Test User Account:**
- Email: `john.doe@company.com`
- Password: `password123`

> ⚠️ **Security Note**: Change default passwords in production!

## Usage

### For End Users

1. **Register/Login** at the frontend
2. **Start Chat** with the AI support agent
3. **Describe Issue** in natural language
4. **Get Solutions** from the knowledge base
5. **Escalate** if unresolved (auto-creates ticket)
6. **Track Tickets** in your dashboard

### For Admins

1. **Login** to admin dashboard
2. **View All Tickets** from users
3. **Update Status** (Open → In Progress → Resolved)
4. **Add Solutions** to knowledge base from resolved tickets
5. **Monitor Analytics** and system usage

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Chat
- `POST /api/chat` - Send message to AI agent

### Tickets
- `GET /api/tickets` - Get all tickets (admin)
- `GET /api/tickets/user/<user_id>` - Get user tickets
- `GET /api/tickets/<ticket_id>` - Get single ticket
- `PUT /api/tickets/<ticket_id>/status` - Update ticket status

### Knowledge Base
- `POST /api/kb/update` - Add KB entry (admin)
- `POST /api/kb/search` - Search knowledge base

## Project Structure

```
ticket_sys/
├── app.py                 # Flask application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── agents/                # AI agent definitions
│   ├── self_service/      # First-line support agent
│   └── escalation/        # Escalation confirmation agent
├── db/                    # Database layer
│   ├── schema.sql         # PostgreSQL schema
│   └── postgres.py        # Database operations
├── kb/                    # Knowledge base
│   ├── kb_chroma.py       # ChromaDB wrapper
│   └── data/              # Initial KB data
├── runners/               # Agent orchestration
│   └── run_agents.py      # Multi-agent workflow
├── tools/                 # Agent tools
│   └── tools.py           # KB search, clarification, etc.
├── frontend/              # React frontend
│   └── src/
│       ├── components/    # UI components
│       └── pages/         # Page components
└── scripts/               # Utility scripts
    ├── populate_kb.py     # Load initial KB
    └── seed_data.py       # Create test users
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
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

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Email: bssshyamsundhar@gmail.com

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system architecture, data flows, and technical documentation.
