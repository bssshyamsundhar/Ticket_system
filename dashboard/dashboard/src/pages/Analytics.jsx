import React, { useState, useEffect } from 'react';
import { Doughnut, Bar, Line, Pie } from 'react-chartjs-2';
import {
    Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale,
    LinearScale, BarElement, PointElement, LineElement, Title, Filler
} from 'chart.js';
import Card from '../components/UI/Card';
import { analyticsAPI } from '../services/api';
import { BarChart3, TrendingUp, Clock, ShieldCheck, Users, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import './Analytics.css';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Filler);

const COLORS = {
    primary: 'rgba(99, 102, 241, 0.85)',
    primaryLight: 'rgba(99, 102, 241, 0.15)',
    purple: 'rgba(139, 92, 246, 0.85)',
    purpleLight: 'rgba(139, 92, 246, 0.15)',
    pink: 'rgba(236, 72, 153, 0.85)',
    green: 'rgba(16, 185, 129, 0.85)',
    greenLight: 'rgba(16, 185, 129, 0.15)',
    amber: 'rgba(245, 158, 11, 0.85)',
    amberLight: 'rgba(245, 158, 11, 0.15)',
    red: 'rgba(239, 68, 68, 0.85)',
    redLight: 'rgba(239, 68, 68, 0.15)',
    blue: 'rgba(59, 130, 246, 0.85)',
    blueLight: 'rgba(59, 130, 246, 0.15)',
    gray: 'rgba(107, 114, 128, 0.85)',
    cyan: 'rgba(6, 182, 212, 0.85)',
    cyanLight: 'rgba(6, 182, 212, 0.15)',
};

const STATUS_COLORS = {
    'Open': COLORS.amber,
    'In Progress': COLORS.blue,
    'Resolved': COLORS.green,
    'Closed': COLORS.gray,
    'Pending Approval': COLORS.purple,
    'Approved': COLORS.cyan,
};

const PRIORITY_COLORS = {
    'P2': COLORS.red,
    'P3': COLORS.amber,
    'P4': COLORS.green,
};

const Analytics = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [trendDays, setTrendDays] = useState(30);

    const loadAnalytics = async (showLoading = true) => {
        try {
            setError(null);
            if (showLoading) setLoading(true);
            const [chartRes, slaRes, resTimeRes, statusRes, workloadRes, trendRes, resTrendRes] = await Promise.all([
                analyticsAPI.getChartData(),
                analyticsAPI.getSLACompliance(),
                analyticsAPI.getResolutionTimeDistribution(),
                analyticsAPI.getStatusBreakdown(),
                analyticsAPI.getWorkload(),
                analyticsAPI.getTrend(trendDays), // ✅ Now passes trendDays parameter
                analyticsAPI.getResolutionTrend(trendDays),
            ]);
            setData({
                chart: chartRes.data,
                sla: slaRes.data,
                resolutionTime: resTimeRes.data,
                statuses: statusRes.data,
                workload: workloadRes.data,
                trend: trendRes.data,
                resTrend: resTrendRes.data,
            });
        } catch (err) {
            console.error('Error loading analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadAnalytics(); }, [trendDays]);

    // Auto-refresh every 30 seconds for real-time data
    useEffect(() => {
        const refreshInterval = setInterval(() => {
            loadAnalytics(false); // silent refresh without loading spinner
        }, 30000);
        return () => clearInterval(refreshInterval);
    }, [trendDays]);

    if (loading) {
        return (
            <div className="analytics-page">
                <div className="analytics-loading">
                    <RefreshCw size={32} className="spin" />
                    <span>Loading analytics...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="analytics-page">
                <div className="analytics-error">
                    <AlertTriangle size={32} />
                    <span>{error}</span>
                    <button onClick={loadAnalytics} className="retry-btn">Retry</button>
                </div>
            </div>
        );
    }

    const { chart, sla, resolutionTime, statuses, workload, trend, resTrend } = data;
    const ticketsByCategory = chart?.ticketsByCategory || {};
    const ticketsByPriority = chart?.ticketsByPriority || {};
    const totalTickets = Object.values(ticketsByCategory).reduce((a, b) => a + b, 0);
    const slaRate = sla?.compliance_rate || sla?.complianceRate || 0;
    const slaTotalVal = sla?.total || 0;
    const slaBreachedVal = sla?.breached || 0;

    // --- Chart Data ---

    // 1. Status Doughnut
    const statusChartData = {
        labels: statuses.map(s => s.status),
        datasets: [{
            data: statuses.map(s => s.count),
            backgroundColor: statuses.map(s => STATUS_COLORS[s.status] || COLORS.gray),
            borderWidth: 0,
            hoverOffset: 8,
        }],
    };

    // 2. Category Pie
    const catLabels = Object.keys(ticketsByCategory);
    const catColors = [COLORS.primary, COLORS.purple, COLORS.pink, COLORS.green, COLORS.amber, COLORS.cyan, COLORS.red, COLORS.blue];
    const categoryChartData = {
        labels: catLabels.map(l => l.length > 25 ? l.substring(0, 25) + '...' : l),
        datasets: [{
            data: Object.values(ticketsByCategory),
            backgroundColor: catLabels.map((_, i) => catColors[i % catColors.length]),
            borderWidth: 0,
            hoverOffset: 8,
        }],
    };

    // 3. Priority Bar
    const prioLabels = Object.keys(ticketsByPriority);
    const priorityChartData = {
        labels: prioLabels.map(p => ({ 'P2': 'P2 (High)', 'P3': 'P3 (Medium)', 'P4': 'P4 (Low)' }[p] || p)),
        datasets: [{
            label: 'Tickets',
            data: Object.values(ticketsByPriority),
            backgroundColor: prioLabels.map(p => PRIORITY_COLORS[p] || COLORS.gray),
            borderRadius: 8,
            borderSkipped: false,
            maxBarThickness: 60,
        }],
    };

    // 4. Ticket Trend Line (creation)
    const trendChartData = {
        labels: (trend || []).map(t => {
            const d = new Date(t.date || t.month);
            return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
        }),
        datasets: [{
            label: 'Tickets Created',
            data: (trend || []).map(t => t.count || 0),
            borderColor: COLORS.primary,
            backgroundColor: COLORS.primaryLight,
            tension: 0.4,
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 6,
        }],
    };

    // 5. Resolution Trend Line
    const resTrendChartData = {
        labels: (resTrend || []).map(t => {
            const d = new Date(t.date);
            return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
        }),
        datasets: [{
            label: 'Tickets Resolved',
            data: (resTrend || []).map(t => t.count || 0),
            borderColor: COLORS.green,
            backgroundColor: COLORS.greenLight,
            tension: 0.4,
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 6,
        }],
    };

    // 6. Resolution Time Distribution Bar
    const resTimeBuckets = (resolutionTime || []);
    const resTimeChartData = {
        labels: resTimeBuckets.map(r => r.bucket),
        datasets: [{
            label: 'Tickets',
            data: resTimeBuckets.map(r => r.count),
            backgroundColor: [COLORS.green, COLORS.cyan, COLORS.blue, COLORS.amber, COLORS.purple, COLORS.red],
            borderRadius: 8,
            borderSkipped: false,
            maxBarThickness: 50,
        }],
    };

    // 7. Workload Horizontal Bar
    const wl = (workload || []).slice(0, 10);
    const workloadChartData = {
        labels: wl.map(w => w.name),
        datasets: [
            {
                label: 'Open',
                data: wl.map(w => w.open_tickets || 0),
                backgroundColor: COLORS.amber,
                borderRadius: 4,
            },
            {
                label: 'In Progress',
                data: wl.map(w => w.in_progress || 0),
                backgroundColor: COLORS.blue,
                borderRadius: 4,
            },
            {
                label: 'Resolved',
                data: wl.map(w => w.resolved_tickets || 0),
                backgroundColor: COLORS.green,
                borderRadius: 4,
            },
        ],
    };

    // 8. SLA Doughnut
    const slaChartData = {
        labels: ['Within SLA', 'Breached'],
        datasets: [{
            data: [slaTotalVal - slaBreachedVal, slaBreachedVal],
            backgroundColor: [COLORS.green, COLORS.red],
            borderWidth: 0,
            hoverOffset: 8,
        }],
    };

    // --- Chart Options ---
    const doughnutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
            legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 12 } } },
            tooltip: { backgroundColor: 'rgba(0,0,0,0.8)', cornerRadius: 8, padding: 12 },
        },
        animation: { animateScale: true, animateRotate: true },
    };

    const barOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: 'rgba(0,0,0,0.8)', cornerRadius: 8, padding: 12 },
        },
        scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { display: true, color: 'rgba(255,255,255,0.05)' } },
            x: { grid: { display: false } },
        },
    };

    const lineOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: 'rgba(0,0,0,0.8)', cornerRadius: 8, padding: 12, mode: 'index', intersect: false },
        },
        scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } },
            x: { grid: { display: false }, ticks: { maxRotation: 45 } },
        },
        interaction: { mode: 'nearest', axis: 'x', intersect: false },
    };

    const stackedBarOptions = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
            legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'circle', font: { size: 12 } } },
            tooltip: { backgroundColor: 'rgba(0,0,0,0.8)', cornerRadius: 8, padding: 12 },
        },
        scales: {
            x: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { stacked: true, grid: { display: false } },
        },
    };

    return (
        <div className="analytics-page animate-fade-in">
            <div className="analytics-header">
                <div>
                    <h1>Reports & Analytics</h1>
                    <p className="analytics-subtitle">Comprehensive insights into support operations</p>
                </div>
                <div className="analytics-controls">
                    <div className="trend-period-selector">
                        {[7, 14, 30, 60].map(d => (
                            <button
                                key={d}
                                className={`period-btn ${trendDays === d ? 'active' : ''}`}
                                onClick={() => setTrendDays(d)}
                            >
                                {d}d
                            </button>
                        ))}
                    </div>
                    <button className="refresh-btn" onClick={loadAnalytics} title="Refresh">
                        <RefreshCw size={18} />
                    </button>
                </div>
            </div>

            {/* KPI Summary Cards */}
            <div className="analytics-kpi-grid">
                <div className="kpi-card kpi-primary">
                    <div className="kpi-icon"><BarChart3 size={22} /></div>
                    <div className="kpi-content">
                        <span className="kpi-value">{totalTickets}</span>
                        <span className="kpi-label">Total Tickets</span>
                    </div>
                </div>
                <div className="kpi-card kpi-success">
                    <div className="kpi-icon"><CheckCircle size={22} /></div>
                    <div className="kpi-content">
                        <span className="kpi-value">{statuses.find(s => s.status === 'Resolved')?.count || 0}</span>
                        <span className="kpi-label">Resolved</span>
                    </div>
                </div>
                <div className="kpi-card kpi-warning">
                    <div className="kpi-icon"><Clock size={22} /></div>
                    <div className="kpi-content">
                        <span className="kpi-value">{statuses.find(s => s.status === 'Open')?.count || 0}</span>
                        <span className="kpi-label">Open</span>
                    </div>
                </div>
                <div className="kpi-card kpi-info">
                    <div className="kpi-icon"><ShieldCheck size={22} /></div>
                    <div className="kpi-content">
                        <span className="kpi-value">{slaRate}%</span>
                        <span className="kpi-label">SLA Compliance</span>
                    </div>
                </div>
                <div className="kpi-card kpi-danger">
                    <div className="kpi-icon"><AlertTriangle size={22} /></div>
                    <div className="kpi-content">
                        <span className="kpi-value">{slaBreachedVal}</span>
                        <span className="kpi-label">SLA Breached</span>
                    </div>
                </div>
                <div className="kpi-card kpi-purple">
                    <div className="kpi-icon"><Users size={22} /></div>
                    <div className="kpi-content">
                        <span className="kpi-value">{workload.length}</span>
                        <span className="kpi-label">Active Technicians</span>
                    </div>
                </div>
            </div>

            {/* Charts Grid */}
            <div className="analytics-charts-grid">
                {/* Row 1: Status + Category + Priority */}
                <Card className="analytics-chart-card" glass>
                    <h3 className="chart-title"><span className="chart-dot status" /> Ticket Status Overview</h3>
                    <div className="chart-container">
                        {statuses.length > 0 ? (
                            <Doughnut data={statusChartData} options={doughnutOptions} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>

                <Card className="analytics-chart-card" glass>
                    <h3 className="chart-title"><span className="chart-dot category" /> Tickets by Category</h3>
                    <div className="chart-container">
                        {catLabels.length > 0 ? (
                            <Pie data={categoryChartData} options={{ ...doughnutOptions, cutout: 0 }} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>

                <Card className="analytics-chart-card" glass>
                    <h3 className="chart-title"><span className="chart-dot priority" /> Priority Distribution</h3>
                    <div className="chart-container">
                        {prioLabels.length > 0 ? (
                            <Bar data={priorityChartData} options={barOptions} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>

                {/* Row 2: Ticket creation trend (wide) + SLA compliance */}
                <Card className="analytics-chart-card wide" glass>
                    <h3 className="chart-title">
                        <span className="chart-dot trend" />
                        Ticket Creation Trend
                        <span className="chart-period">(Last {trendDays} days)</span>
                    </h3>
                    <div className="chart-container-wide">
                        {(trend || []).length > 0 ? (
                            <Line data={trendChartData} options={lineOptions} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>

                <Card className="analytics-chart-card" glass>
                    <h3 className="chart-title"><span className="chart-dot sla" /> SLA Compliance</h3>
                    <div className="chart-container">
                        <Doughnut data={slaChartData} options={{
                            ...doughnutOptions,
                            cutout: '70%',
                            plugins: {
                                ...doughnutOptions.plugins,
                                legend: { ...doughnutOptions.plugins.legend },
                            },
                        }} />
                        <div className="sla-center-label">
                            <span className="sla-rate">{slaRate}%</span>
                            <span className="sla-sub">compliance</span>
                        </div>
                    </div>
                </Card>

                {/* Row 3: Resolution trend (wide) + Resolution time distribution */}
                <Card className="analytics-chart-card wide" glass>
                    <h3 className="chart-title">
                        <span className="chart-dot resolved" />
                        Resolution Trend
                        <span className="chart-period">(Last {trendDays} days)</span>
                    </h3>
                    <div className="chart-container-wide">
                        {(resTrend || []).length > 0 ? (
                            <Line data={resTrendChartData} options={lineOptions} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>

                <Card className="analytics-chart-card" glass>
                    <h3 className="chart-title"><span className="chart-dot restime" /> Resolution Time</h3>
                    <div className="chart-container">
                        {resTimeBuckets.length > 0 ? (
                            <Bar data={resTimeChartData} options={barOptions} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>

                {/* Row 4: Technician Workload (full width) */}
                <Card className="analytics-chart-card full-width" glass>
                    <h3 className="chart-title"><span className="chart-dot workload" /> Technician Workload</h3>
                    <div className="chart-container-full">
                        {wl.length > 0 ? (
                            <Bar data={workloadChartData} options={stackedBarOptions} />
                        ) : <p className="no-data">No data available</p>}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Analytics;
