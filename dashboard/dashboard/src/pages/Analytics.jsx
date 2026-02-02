import React, { useState, useEffect } from 'react';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title } from 'chart.js';
import Card from '../components/UI/Card';
import { analyticsAPI } from '../services/api';
import '../pages/Dashboard.css';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title);

const Analytics = () => {
    const [analyticsData, setAnalyticsData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadAnalytics();
    }, []);

    const loadAnalytics = async () => {
        try {
            setError(null);
            const response = await analyticsAPI.getChartData();
            setAnalyticsData(response.data);
        } catch (error) {
            console.error('Error loading analytics:', error);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="tickets-page"><div className="loading-state">Loading analytics...</div></div>;
    }

    if (error) {
        return <div className="tickets-page"><div className="loading-state" style={{color: '#ef4444'}}>{error}</div></div>;
    }

    // Safely get data with defaults
    const ticketsByCategory = analyticsData?.ticketsByCategory || {};
    const ticketsByPriority = analyticsData?.ticketsByPriority || {};
    const monthlyTrend = analyticsData?.monthlyTrend || { labels: [], data: [] };

    const hasCategories = Object.keys(ticketsByCategory).length > 0;
    const hasPriorities = Object.keys(ticketsByPriority).length > 0;
    const hasTrend = monthlyTrend.labels.length > 0;

    const categoryChartData = {
        labels: Object.keys(ticketsByCategory),
        datasets: [{
            data: Object.values(ticketsByCategory),
            backgroundColor: [
                'rgba(99, 102, 241, 0.8)',
                'rgba(139, 92, 246, 0.8)',
                'rgba(236, 72, 153, 0.8)',
                'rgba(16, 185, 129, 0.8)',
                'rgba(245, 158, 11, 0.8)',
            ],
        }],
    };

    const priorityChartData = {
        labels: Object.keys(ticketsByPriority),
        datasets: [{
            label: 'Tickets',
            data: Object.values(ticketsByPriority),
            backgroundColor: 'rgba(99, 102, 241, 0.8)',
        }],
    };

    const trendChartData = {
        labels: monthlyTrend.labels,
        datasets: [{
            label: 'Tickets',
            data: monthlyTrend.data,
            borderColor: 'rgb(99, 102, 241)',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            tension: 0.4,
        }],
    };

    return (
        <div className="tickets-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>Reports & Analytics</h1>
                    <p className="page-subtitle">Visualize ticket trends and performance metrics</p>
                </div>
            </div>

            <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))' }}>
                <Card className="dashboard-card" glass>
                    <h3 className="card-title">Tickets by Category</h3>
                    <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {hasCategories ? (
                            <Pie data={categoryChartData} options={{ maintainAspectRatio: false, responsive: true }} />
                        ) : (
                            <p style={{ color: '#888' }}>No category data available</p>
                        )}
                    </div>
                </Card>

                <Card className="dashboard-card" glass>
                    <h3 className="card-title">Tickets by Priority</h3>
                    <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {hasPriorities ? (
                            <Bar data={priorityChartData} options={{ maintainAspectRatio: false, responsive: true }} />
                        ) : (
                            <p style={{ color: '#888' }}>No priority data available</p>
                        )}
                    </div>
                </Card>

                <Card className="dashboard-card" glass style={{ gridColumn: '1 / -1' }}>
                    <h3 className="card-title">Monthly Ticket Trend</h3>
                    <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {hasTrend ? (
                            <Line data={trendChartData} options={{ maintainAspectRatio: false, responsive: true }} />
                        ) : (
                            <p style={{ color: '#888' }}>No trend data available</p>
                        )}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Analytics;
