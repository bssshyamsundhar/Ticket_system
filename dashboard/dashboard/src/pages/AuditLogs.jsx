import React, { useState, useEffect } from 'react';
import { FileText, Download, Filter } from 'lucide-react';
import Card from '../components/UI/Card';
import Table from '../components/UI/Table';
import Button from '../components/UI/Button';
import Badge from '../components/UI/Badge';
import { auditLogsAPI } from '../services/api';
import '../pages/Tickets.css';

const AuditLogs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterAction, setFilterAction] = useState('all');

    useEffect(() => {
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const response = await auditLogsAPI.getAll();
            setLogs(response.data);
        } catch (error) {
            console.error('Error loading logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredLogs = filterAction === 'all'
        ? logs
        : logs.filter(log => log.action === filterAction);

    const getActionBadgeVariant = (action) => {
        const variants = {
            'Ticket Created': 'info',
            'Ticket Assigned': 'primary',
            'Status Changed': 'warning',
            'Ticket Resolved': 'success',
            'Ticket Closed': 'default',
            'Priority Changed': 'warning',
        };
        return variants[action] || 'default';
    };

    const columns = [
        { key: 'id', label: 'Log ID', sortable: true },
        {
            key: 'action',
            label: 'Action',
            sortable: true,
            render: (value) => <Badge variant={getActionBadgeVariant(value)}>{value}</Badge>
        },
        { key: 'ticketId', label: 'Ticket ID', sortable: true },
        { key: 'user', label: 'User', sortable: true },
        { key: 'details', label: 'Details', sortable: false },
        {
            key: 'timestamp',
            label: 'Timestamp',
            sortable: true,
            render: (value) => new Date(value).toLocaleString()
        },
    ];

    return (
        <div className="tickets-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>Audit Logs</h1>
                    <p className="page-subtitle">Track all system activities and changes</p>
                </div>
                <Button variant="primary" icon={<Download size={18} />}>
                    Export Logs
                </Button>
            </div>

            <Card className="filters-card" glass>
                <div className="filters-row">
                    <div className="filter-group">
                        <Filter size={18} />
                        <select
                            value={filterAction}
                            onChange={(e) => setFilterAction(e.target.value)}
                            className="filter-select"
                        >
                            <option value="all">All Actions</option>
                            <option value="Ticket Created">Ticket Created</option>
                            <option value="Ticket Assigned">Ticket Assigned</option>
                            <option value="Status Changed">Status Changed</option>
                            <option value="Ticket Resolved">Ticket Resolved</option>
                            <option value="Ticket Closed">Ticket Closed</option>
                            <option value="Priority Changed">Priority Changed</option>
                        </select>
                    </div>
                </div>
            </Card>

            <Card className="table-card">
                <div className="table-header">
                    <h3>Activity Logs ({filteredLogs.length})</h3>
                </div>
                {loading ? (
                    <div className="loading-state">Loading logs...</div>
                ) : (
                    <Table columns={columns} data={filteredLogs} />
                )}
            </Card>
        </div>
    );
};

export default AuditLogs;
