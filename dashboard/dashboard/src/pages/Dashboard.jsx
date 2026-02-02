import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    TrendingDown,
    AlertCircle,
    CheckCircle,
    Clock,
    Activity
} from 'lucide-react';
import Card from '../components/UI/Card';
import { analyticsAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
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

    const statCards = [
        {
            title: 'Total Tickets',
            value: stats?.totalTickets || 0,
            icon: Activity,
            color: 'primary',
            trend: '+12%',
            trendUp: true,
        },
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

            <div className="stats-grid">
                {statCards.map((stat, index) => (
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
                        <div className="activity-item">
                            <div className="activity-dot activity-dot-success"></div>
                            <div className="activity-content">
                                <div className="activity-text">Ticket TKT-1005 resolved by Mike Chen</div>
                                <div className="activity-time">2 minutes ago</div>
                            </div>
                        </div>
                        <div className="activity-item">
                            <div className="activity-dot activity-dot-warning"></div>
                            <div className="activity-content">
                                <div className="activity-text">New high priority ticket TKT-1007 created</div>
                                <div className="activity-time">15 minutes ago</div>
                            </div>
                        </div>
                        <div className="activity-item">
                            <div className="activity-dot activity-dot-info"></div>
                            <div className="activity-content">
                                <div className="activity-text">Ticket TKT-1002 assigned to Mike Chen</div>
                                <div className="activity-time">1 hour ago</div>
                            </div>
                        </div>
                        <div className="activity-item">
                            <div className="activity-dot activity-dot-danger"></div>
                            <div className="activity-content">
                                <div className="activity-text">Critical ticket TKT-1003 created</div>
                                <div className="activity-time">2 hours ago</div>
                            </div>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Dashboard;
