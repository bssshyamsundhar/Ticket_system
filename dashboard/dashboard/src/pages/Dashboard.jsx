import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    TrendingDown,
    AlertCircle,
    CheckCircle,
    Clock,
    Activity,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import Card from '../components/UI/Card';
import { analyticsAPI, auditLogsAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statsExpanded, setStatsExpanded] = useState(false);
    const [recentActivity, setRecentActivity] = useState([]);
    const [activityLoading, setActivityLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
        loadRecentActivity();
    }, []);

    const loadDashboardData = async () => {
        try {
            const response = await analyticsAPI.getDashboardStats();
            setStats(response.data);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadRecentActivity = async () => {
        try {
            const response = await auditLogsAPI.getAll({ limit: 5 });
            setRecentActivity(response.data || []);
        } catch (error) {
            console.error('Error loading recent activity:', error);
        } finally {
            setActivityLoading(false);
        }
    };

    // Get color for activity dot based on action type
    const getActivityColor = (action) => {
        if (action?.toLowerCase().includes('resolved') || action?.toLowerCase().includes('closed')) {
            return 'success';
        } else if (action?.toLowerCase().includes('critical') || action?.toLowerCase().includes('high')) {
            return 'danger';
        } else if (action?.toLowerCase().includes('assign') || action?.toLowerCase().includes('progress')) {
            return 'info';
        } else if (action?.toLowerCase().includes('created') || action?.toLowerCase().includes('new')) {
            return 'warning';
        }
        return 'info';
    };

    // Format time ago
    const formatTimeAgo = (timestamp) => {
        if (!timestamp) return 'Just now';
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    };

    if (loading) {
        return (
            <div className="dashboard">
                <div className="dashboard-header">
                    <h1>Dashboard</h1>
                </div>
                <div className="stats-grid">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <Card key={i} className="stat-card skeleton" style={{ height: '140px' }} />
                    ))}
                </div>
            </div>
        );
    }

    // Primary stat (Total Tickets - expandable)
    const primaryStat = {
        title: 'Total Tickets',
        value: stats?.totalTickets || 0,
        icon: Activity,
        color: 'primary',
        trend: '+12%',
        trendUp: true,
    };

    // Expandable child stats  
    const expandableStats = [
        {
            title: 'Open Tickets',
            value: stats?.openTickets || 0,
            icon: AlertCircle,
            color: 'info',
            trend: '+5%',
            trendUp: true,
        },
        {
            title: 'In Progress',
            value: stats?.inProgressTickets || 0,
            icon: Clock,
            color: 'warning',
            trend: '-3%',
            trendUp: false,
        },
        {
            title: 'Resolved Today',
            value: stats?.resolvedToday || 0,
            icon: CheckCircle,
            color: 'success',
            trend: '+8%',
            trendUp: true,
        },
        {
            title: 'SLA Breached',
            value: stats?.slaBreached || 0,
            icon: AlertCircle,
            color: 'danger',
            trend: '-1%',
            trendUp: false,
        },
    ];

    // Additional stats that always show
    const additionalStats = [
        {
            title: 'High Priority',
            value: stats?.highPriorityTickets || 0,
            icon: TrendingUp,
            color: 'warning',
            trend: '+2%',
            trendUp: true,
        },
        {
            title: 'Critical Tickets',
            value: stats?.criticalTickets || 0,
            icon: AlertCircle,
            color: 'danger',
            trend: '-1%',
            trendUp: false,
        },
    ];

    return (
        <div className="dashboard animate-fade-in">
            <div className="dashboard-header">
                <div>
                    <h1>Dashboard</h1>
                    <p className="dashboard-subtitle">Welcome back! Here's what's happening today.</p>
                </div>
                <div className="dashboard-actions">
                    <span className="last-updated">Last updated: {new Date().toLocaleTimeString()}</span>
                </div>
            </div>

            {/* Primary Total Tickets Card - Clickable to expand */}
            <div className="stats-section">
                <Card
                    className={`stat-card stat-card-${primaryStat.color} expandable-card ${statsExpanded ? 'expanded' : ''}`}
                    hover
                    onClick={() => setStatsExpanded(!statsExpanded)}
                    style={{ cursor: 'pointer' }}
                >
                    <div className="stat-header">
                        <div className={`stat-icon stat-icon-${primaryStat.color}`}>
                            <primaryStat.icon size={24} />
                        </div>
                        <div className="expand-toggle">
                            {statsExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </div>
                    </div>
                    <div className="stat-body">
                        <div className="stat-value">{primaryStat.value}</div>
                        <div className="stat-title">
                            {primaryStat.title}
                            <span className="expand-hint">{statsExpanded ? 'Click to collapse' : 'Click for details'}</span>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Expandable Stats Section */}
            <div className={`expandable-stats ${statsExpanded ? 'expanded' : 'collapsed'}`}>
                <div className="stats-grid child-stats">
                    {expandableStats.map((stat, index) => (
                        <Card key={index} className={`stat-card stat-card-${stat.color}`} hover>
                            <div className="stat-header">
                                <div className={`stat-icon stat-icon-${stat.color}`}>
                                    <stat.icon size={24} />
                                </div>
                                <div className={`stat-trend ${stat.trendUp ? 'trend-up' : 'trend-down'}`}>
                                    {stat.trendUp ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                    {stat.trend}
                                </div>
                            </div>
                            <div className="stat-body">
                                <div className="stat-value">{stat.value}</div>
                                <div className="stat-title">{stat.title}</div>
                            </div>
                        </Card>
                    ))}
                </div>
            </div>

            {/* Additional Stats */}
            <div className="stats-grid">
                {additionalStats.map((stat, index) => (
                    <Card key={index} className={`stat-card stat-card-${stat.color}`} hover>
                        <div className="stat-header">
                            <div className={`stat-icon stat-icon-${stat.color}`}>
                                <stat.icon size={24} />
                            </div>
                            <div className={`stat-trend ${stat.trendUp ? 'trend-up' : 'trend-down'}`}>
                                {stat.trendUp ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                {stat.trend}
                            </div>
                        </div>
                        <div className="stat-body">
                            <div className="stat-value">{stat.value}</div>
                            <div className="stat-title">{stat.title}</div>
                        </div>
                    </Card>
                ))}
            </div>

            <div className="dashboard-grid">
                <Card className="dashboard-card" glass>
                    <h3 className="card-title">Quick Stats</h3>
                    <div className="quick-stats">
                        <div className="quick-stat-item">
                            <span className="quick-stat-label">Avg Resolution Time</span>
                            <span className="quick-stat-value">{stats?.avgResolutionTime || 'N/A'}</span>
                        </div>
                        <div className="quick-stat-item">
                            <span className="quick-stat-label">SLA Breached</span>
                            <span className="quick-stat-value danger">{stats?.slaBreached || 0}</span>
                        </div>
                        <div className="quick-stat-item">
                            <span className="quick-stat-label">Active Technicians</span>
                            <span className="quick-stat-value">4</span>
                        </div>
                        <div className="quick-stat-item">
                            <span className="quick-stat-label">KB Articles</span>
                            <span className="quick-stat-value">25</span>
                        </div>
                    </div>
                </Card>

                <Card className="dashboard-card" glass>
                    <h3 className="card-title">Recent Activity</h3>
                    <div className="activity-list">
                        {activityLoading ? (
                            <div className="activity-loading">Loading activity...</div>
                        ) : recentActivity.length > 0 ? (
                            recentActivity.map((activity, index) => (
                                <div key={activity.id || index} className="activity-item">
                                    <div className={`activity-dot activity-dot-${getActivityColor(activity.action)}`}></div>
                                    <div className="activity-content">
                                        <div className="activity-text">
                                            {activity.action}: {activity.entityId || activity.ticketId || 'N/A'}
                                            {activity.performedByName && ` by ${activity.performedByName}`}
                                        </div>
                                        <div className="activity-time">{formatTimeAgo(activity.createdAt)}</div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="activity-empty">No recent activity</div>
                        )}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Dashboard;
