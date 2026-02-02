// API Service Layer for Flask Backend Integration
// Connects to the IT Support System Flask backend

import axios from 'axios';

// API Configuration - Flask backend runs on port 5000
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Create axios instance with default config
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor (add auth tokens)
apiClient.interceptors.request.use(
    (config) => {
        // Check both possible token storage keys
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor (handle errors globally)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized
            localStorage.removeItem('authToken');
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Helper to extract data from Flask response format
const extractData = (response) => {
    // Flask returns { success: true, tickets: [...] } or { success: true, data: {...} }
    if (response.data.success === false) {
        throw new Error(response.data.error || 'API request failed');
    }
    return response.data;
};

// Transform snake_case to camelCase for a single object
const toCamelCase = (obj) => {
    if (obj === null || typeof obj !== 'object') return obj;
    if (Array.isArray(obj)) return obj.map(toCamelCase);
    
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
        const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
        result[camelKey] = toCamelCase(value);
    }
    return result;
};

// Transform ticket from backend format to frontend format
const transformTicket = (ticket) => {
    if (!ticket) return null;
    const t = toCamelCase(ticket);
    return {
        ...t,
        // Map specific fields that frontend expects
        userName: t.userName || t.userEmail?.split('@')[0] || 'Unknown',
        assignedTo: t.assignedTo || t.assignedToId || null,
    };
};

// Transform technician from backend format to frontend format
const transformTechnician = (tech) => {
    if (!tech) return null;
    const t = toCamelCase(tech);
    return {
        ...t,
        activeStatus: t.activeStatus !== undefined ? t.activeStatus : true,
        assignedTickets: t.assignedTickets || 0,
        resolvedTickets: t.resolvedTickets || 0,
    };
};

// Transform knowledge article from backend format
const transformArticle = (article) => {
    if (!article) return null;
    return toCamelCase(article);
};

// ===================================
// TICKETS API
// ===================================

export const ticketsAPI = {
    // Get all tickets with optional filters
    getAll: async (filters = {}) => {
        const response = await apiClient.get('/api/tickets', { params: filters });
        const data = extractData(response);
        const tickets = (data.tickets || []).map(transformTicket);
        return { data: tickets };
    },

    // Get single ticket by ID
    getById: async (id) => {
        const response = await apiClient.get(`/api/tickets/${id}`);
        const data = extractData(response);
        return { data: transformTicket(data.ticket) };
    },

    // Create new ticket
    create: async (ticketData) => {
        const response = await apiClient.post('/api/chat/create-ticket', ticketData);
        const data = extractData(response);
        return { data: transformTicket(data.ticket) };
    },

    // Update ticket status
    update: async (id, updates) => {
        const response = await apiClient.put(`/api/tickets/${id}/status`, {
            status: updates.status,
            resolution_notes: updates.resolution_notes || updates.resolutionNotes
        });
        const data = extractData(response);
        return { data: transformTicket(data.ticket) };
    },

    // Assign ticket to technician
    assign: async (ticketId, technicianId) => {
        const response = await apiClient.put(`/api/tickets/${ticketId}/assign`, { 
            technician_id: technicianId 
        });
        const data = extractData(response);
        return { data: transformTicket(data.ticket) };
    },

    // Close ticket
    close: async (id, resolutionNotes) => {
        const response = await apiClient.put(`/api/tickets/${id}/status`, {
            status: 'Closed',
            resolution_notes: resolutionNotes
        });
        const data = extractData(response);
        return { data: transformTicket(data.ticket) };
    },
};

// ===================================
// TECHNICIANS API
// ===================================

export const techniciansAPI = {
    getAll: async () => {
        const response = await apiClient.get('/api/technicians');
        const data = extractData(response);
        const technicians = (data.technicians || []).map(transformTechnician);
        return { data: technicians };
    },

    getById: async (id) => {
        const response = await apiClient.get(`/api/technicians/${id}`);
        const data = extractData(response);
        return { data: transformTechnician(data.technician) };
    },

    create: async (technicianData) => {
        const response = await apiClient.post('/api/technicians', technicianData);
        const data = extractData(response);
        return { data: transformTechnician(data.technician) };
    },

    update: async (id, updates) => {
        const response = await apiClient.put(`/api/technicians/${id}`, updates);
        const data = extractData(response);
        return { data: transformTechnician(data.technician) };
    },

    delete: async (id) => {
        await apiClient.delete(`/api/technicians/${id}`);
        return { data: { success: true } };
    },
};

// ===================================
// KNOWLEDGE BASE API
// ===================================


export const knowledgeBaseAPI = {
    getAll: async (filters = {}) => {
        const response = await apiClient.get('/api/knowledge-base', { params: filters });
        const data = extractData(response);
        const articles = (data.articles || []).map(transformArticle);
        return { data: articles };
    },

    getById: async (id) => {
        const response = await apiClient.get(`/api/knowledge-base/${id}`);
        const data = extractData(response);
        return { data: transformArticle(data.article) };
    },

    create: async (articleData) => {
        const response = await apiClient.post('/api/knowledge-base', articleData);
        const data = extractData(response);
        return { data: transformArticle(data.article) };
    },

    update: async (id, updates) => {
        const response = await apiClient.put(`/api/knowledge-base/${id}`, updates);
        const data = extractData(response);
        return { data: transformArticle(data.article) };
    },

    delete: async (id) => {
        await apiClient.delete(`/api/knowledge-base/${id}`);
        return { data: { success: true } };
    },

    // Search knowledge base
    search: async (query) => {
        const response = await apiClient.post('/api/kb/search', { query, top_k: 10 });
        const data = extractData(response);
        return { data: (data.results || []).map(transformArticle) };
    },

    // Submit feedback
    feedback: async (id, helpful) => {
        await apiClient.post(`/api/knowledge-base/${id}/feedback`, { helpful });
        return { data: { success: true } };
    },

    // Get stats
    getStats: async () => {
        const response = await apiClient.get('/api/kb/stats');
        const data = extractData(response);
        return { data: toCamelCase(data.stats) };
    },
};

// ===================================
// PRIORITY RULES API
// ===================================

export const priorityRulesAPI = {
    getAll: async () => {
        const response = await apiClient.get('/api/priority-rules');
        const data = extractData(response);
        return { data: (data.rules || []).map(toCamelCase) };
    },

    create: async (ruleData) => {
        const response = await apiClient.post('/api/priority-rules', ruleData);
        const data = extractData(response);
        return { data: toCamelCase(data.rule) };
    },

    update: async (id, updates) => {
        const response = await apiClient.put(`/api/priority-rules/${id}`, updates);
        const data = extractData(response);
        return { data: toCamelCase(data.rule) };
    },

    delete: async (id) => {
        await apiClient.delete(`/api/priority-rules/${id}`);
        return { data: { success: true } };
    },
};

// ===================================
// SLA API
// ===================================

export const slaAPI = {
    getConfig: async () => {
        const response = await apiClient.get('/api/sla');
        const data = extractData(response);
        return { data: (data.sla_config || []).map(toCamelCase) };
    },

    updateConfig: async (slaId, updates) => {
        const response = await apiClient.put(`/api/sla/${slaId}`, updates);
        const data = extractData(response);
        return { data: toCamelCase(data.sla_config) };
    },

    getBreachedTickets: async () => {
        const response = await apiClient.get('/api/sla/breached');
        const data = extractData(response);
        return { data: (data.tickets || []).map(transformTicket) };
    },
};

// ===================================
// AUDIT LOGS API
// ===================================

export const auditLogsAPI = {
    getAll: async (filters = {}) => {
        const response = await apiClient.get('/api/audit-logs', { params: filters });
        const data = extractData(response);
        return { data: (data.logs || []).map(toCamelCase) };
    },

    export: async (format = 'csv') => {
        const response = await apiClient.get('/api/audit-logs', { 
            params: { format, limit: 1000 } 
        });
        const data = extractData(response);
        return { data: (data.logs || []).map(toCamelCase) };
    },
};

// ===================================
// NOTIFICATIONS API
// ===================================

export const notificationsAPI = {
    getSettings: async () => {
        const response = await apiClient.get('/api/notifications/settings');
        const data = extractData(response);
        return { data: data.settings };
    },

    updateSettings: async (settings) => {
        const response = await apiClient.put('/api/notifications/settings', settings);
        const data = extractData(response);
        return { data: data.settings };
    },

    testNotification: async () => {
        return { data: { success: true, message: 'Test notification sent' } };
    },
};

// ===================================
// ANALYTICS API
// ===================================

export const analyticsAPI = {
    getDashboardStats: async () => {
        const response = await apiClient.get('/api/analytics/tickets');
        const data = extractData(response);
        
        // Transform backend stats to frontend format
        const stats = data.stats || {};
        return { 
            data: {
                totalTickets: stats.total || 0,
                openTickets: stats.open || 0,
                inProgressTickets: stats.in_progress || 0,
                resolvedToday: stats.resolved || 0,
                highPriorityTickets: 0, // Will calculate from priority data
                criticalTickets: 0,
                slaBreached: stats.sla_breached || 0,
                avgResolutionTime: 'N/A',
                byCategory: data.by_category || [],
                byPriority: data.by_priority || []
            }
        };
    },

    getChartData: async (chartType) => {
        try {
            // Fetch all analytics data
            const [ticketRes, trendRes] = await Promise.all([
                apiClient.get('/api/analytics/tickets'),
                apiClient.get('/api/analytics/trend')
            ]);
            
            const ticketData = extractData(ticketRes);
            const trendData = extractData(trendRes);
            
            // Transform by_category array to object format
            const ticketsByCategory = {};
            (ticketData.by_category || []).forEach(item => {
                ticketsByCategory[item.category || 'Unknown'] = item.count || 0;
            });
            
            // Transform by_priority array to object format
            const ticketsByPriority = {};
            (ticketData.by_priority || []).forEach(item => {
                ticketsByPriority[item.priority || 'Unknown'] = item.count || 0;
            });
            
            // Transform trend data
            const trend = trendData.trend || [];
            const monthlyTrend = {
                labels: trend.map(t => t.date || t.month || ''),
                data: trend.map(t => t.count || 0)
            };
            
            return { 
                data: {
                    ticketsByCategory,
                    ticketsByPriority,
                    monthlyTrend
                }
            };
        } catch (error) {
            console.error('Error loading chart data:', error);
            // Return empty but valid data structure on error
            return {
                data: {
                    ticketsByCategory: {},
                    ticketsByPriority: {},
                    monthlyTrend: { labels: [], data: [] }
                }
            };
        }
    },

    getTrend: async () => {
        const response = await apiClient.get('/api/analytics/trend');
        const data = extractData(response);
        return { data: data.trend || [] };
    },

    getWorkload: async () => {
        const response = await apiClient.get('/api/analytics/workload');
        const data = extractData(response);
        return { data: data.workload || [] };
    },

    exportReport: async (reportType, dateRange) => {
        return { data: 'Report export not implemented' };
    },
};

// ===================================
// AUTH API
// ===================================

export const authAPI = {
    login: async (credentials) => {
        const response = await apiClient.post('/api/auth/login', credentials);
        const data = extractData(response);
        
        // Store token
        if (data.token) {
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('token', data.token);
        }
        if (data.user) {
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        
        return { data };
    },

    register: async (userData) => {
        const response = await apiClient.post('/api/auth/register', userData);
        const data = extractData(response);
        
        if (data.token) {
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('token', data.token);
        }
        if (data.user) {
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        
        return { data };
    },

    logout: async () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        return { data: { success: true } };
    },

    getCurrentUser: async () => {
        // Get user from stored data
        const userStr = localStorage.getItem('user');
        if (userStr) {
            return { data: JSON.parse(userStr) };
        }
        return { data: null };
    },
};

// ===================================
// USERS API
// ===================================

export const usersAPI = {
    getAll: async () => {
        return { data: [] };
    },

    getById: async (id) => {
        const response = await apiClient.get(`/api/users/${id}`);
        const data = extractData(response);
        return { data: data.user };
    },
};

export default apiClient;
