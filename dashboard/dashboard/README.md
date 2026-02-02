# IT Support Admin Dashboard

A modern React-based admin dashboard for the IT Support Ticketing System.

## Features

- **Dashboard Overview**: Real-time statistics and metrics
- **Ticket Management**: View, update, and assign tickets
- **Technician Management**: Manage support staff
- **Knowledge Base**: CRUD operations for KB articles
- **Priority Rules**: Configure auto-priority assignment
- **SLA Management**: Set and monitor SLA configurations
- **Analytics**: Charts and reports
- **Audit Logs**: Track all system changes
- **Notification Settings**: Configure email notifications

## Prerequisites

- Node.js 20.19+ or 22.12+
- Flask backend running on port 5000

## Installation

```bash
cd dashboard/dashboard
npm install
```

## Running the Dashboard

```bash
npm run dev
```

The dashboard will start on `http://localhost:3001` (or next available port).

## Configuration

Create a `.env` file with:

```env
VITE_API_URL=http://localhost:5000
```

## Architecture

This dashboard connects to the main Flask backend API at port 5000. All data is fetched from and persisted to the PostgreSQL database through the Flask API.

### API Integration

The dashboard uses the following Flask API endpoints:

- `/api/auth/*` - Authentication
- `/api/tickets/*` - Ticket management
- `/api/technicians/*` - Technician management
- `/api/knowledge-base/*` - Knowledge base
- `/api/priority-rules/*` - Priority rules
- `/api/sla/*` - SLA configuration
- `/api/analytics/*` - Statistics and reports
- `/api/audit-logs` - Audit logs
- `/api/notifications/settings` - Notification settings

## Tech Stack

- React 19
- Vite 7
- React Router 7
- Axios
- Chart.js
- Lucide React Icons
