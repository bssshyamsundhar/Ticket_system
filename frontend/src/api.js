import axios from 'axios';

// Configure axios to point to Flask backend
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==========================================
// Authentication API
// ==========================================

export const authAPI = {
  register: (userData) => api.post('/api/auth/register', userData),
  login: (credentials) => api.post('/api/auth/login', credentials),
  getCurrentUser: () => api.get('/api/auth/me'),
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
};

// ==========================================
// Chat API (Button-based flow)
// ==========================================

export const chatAPI = {
  // Get available categories
  getCategories: () => api.get('/api/chat/categories'),
  
  // Get solution for a specific subcategory
  getSolution: (subcategoryId) => api.get(`/api/chat/solution/${subcategoryId}`),
  
  // Create ticket directly
  createTicket: (ticketData) => api.post('/api/chat/create-ticket', ticketData),
  
  // Send chat action (main endpoint)
  sendAction: (data) => api.post('/api/chat', data),
  
  // Reset conversation
  resetConversation: (sessionId) => api.post('/api/chat/reset', { session_id: sessionId })
};

// ==========================================
// Tickets API
// ==========================================

export const ticketsAPI = {
  // Get all tickets (with optional filters)
  getAll: (params = {}) => api.get('/api/tickets', { params }),
  
  // Get tickets for a specific user
  getUserTickets: (userId) => api.get(`/api/tickets/user/${userId}`),
  
  // Get single ticket
  getById: (ticketId) => api.get(`/api/tickets/${ticketId}`),
  
  // Update ticket status
  updateStatus: (ticketId, data) => api.put(`/api/tickets/${ticketId}/status`, data),
  
  // Assign ticket to technician
  assign: (ticketId, technicianId) => api.put(`/api/tickets/${ticketId}/assign`, { technician_id: technicianId })
};

// ==========================================
// Technicians API
// ==========================================

export const techniciansAPI = {
  getAll: (activeOnly = false) => api.get('/api/technicians', { params: { active: activeOnly } }),
  getById: (techId) => api.get(`/api/technicians/${techId}`),
  create: (data) => api.post('/api/technicians', data),
  update: (techId, data) => api.put(`/api/technicians/${techId}`, data)
};

// ==========================================
// SLA API
// ==========================================

export const slaAPI = {
  getConfig: () => api.get('/api/sla'),
  update: (slaId, data) => api.put(`/api/sla/${slaId}`, data),
  getBreachedTickets: () => api.get('/api/sla/breached')
};

// ==========================================
// Priority Rules API
// ==========================================

export const priorityRulesAPI = {
  getAll: () => api.get('/api/priority-rules'),
  create: (data) => api.post('/api/priority-rules', data),
  delete: (ruleId) => api.delete(`/api/priority-rules/${ruleId}`)
};

// ==========================================
// Knowledge Base API
// ==========================================

export const kbAPI = {
  // Get all articles
  getAll: () => api.get('/api/knowledge-base'),
  
  // Get single article
  getById: (articleId) => api.get(`/api/knowledge-base/${articleId}`),
  
  // Create article
  create: (data) => api.post('/api/knowledge-base', data),
  
  // Update article
  update: (articleId, data) => api.put(`/api/knowledge-base/${articleId}`, data),
  
  // Delete article
  delete: (articleId) => api.delete(`/api/knowledge-base/${articleId}`),
  
  // Submit feedback
  submitFeedback: (articleId, helpful) => api.post(`/api/knowledge-base/${articleId}/feedback`, { helpful }),
  
  // Search KB
  search: (query, topK = 3) => api.post('/api/kb/search', { query, top_k: topK }),
  
  // Get KB stats
  getStats: () => api.get('/api/kb/stats'),
  
  // Get KB categories
  getCategories: () => api.get('/api/kb/categories')
};

// ==========================================
// Analytics API
// ==========================================

export const analyticsAPI = {
  getTicketStats: () => api.get('/api/analytics/tickets'),
  getTicketTrend: (days = 7) => api.get('/api/analytics/trend', { params: { days } }),
  getTechnicianWorkload: () => api.get('/api/analytics/workload')
};

// ==========================================
// Audit Logs API
// ==========================================

export const auditAPI = {
  getLogs: (params = {}) => api.get('/api/audit-logs', { params })
};

// ==========================================
// Notification Settings API
// ==========================================

export const notificationsAPI = {
  getSettings: () => api.get('/api/notifications/settings'),
  updateSettings: (data) => api.put('/api/notifications/settings', data)
};

export default api;
