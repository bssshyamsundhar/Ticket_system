import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, UserCheck, UserX } from 'lucide-react';
import Card from '../components/UI/Card';
import Table from '../components/UI/Table';
import Button from '../components/UI/Button';
import Badge from '../components/UI/Badge';
import { techniciansAPI } from '../services/api';
import '../pages/Tickets.css';

const Technicians = () => {
    const [technicians, setTechnicians] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadTechnicians();
    }, []);

    const loadTechnicians = async () => {
        try {
            const response = await techniciansAPI.getAll();
            setTechnicians(response.data);
        } catch (error) {
            console.error('Error loading technicians:', error);
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        { key: 'id', label: 'ID', sortable: true },
        { key: 'name', label: 'Name', sortable: true },
        { key: 'email', label: 'Email', sortable: true },
        { key: 'role', label: 'Role', sortable: true },
        {
            key: 'activeStatus',
            label: 'Status',
            sortable: true,
            render: (value) => (
                <Badge variant={value ? 'success' : 'default'}>
                    {value ? 'Active' : 'Inactive'}
                </Badge>
            )
        },
        { key: 'assignedTickets', label: 'Assigned', sortable: true },
        { key: 'resolvedTickets', label: 'Resolved', sortable: true },
        { key: 'avgResolutionTime', label: 'Avg Time', sortable: true },
        {
            key: 'actions',
            label: 'Actions',
            sortable: false,
            render: () => (
                <div className="table-actions">
                    <button className="action-btn action-btn-view" title="Edit">
                        <Edit size={16} />
                    </button>
                    <button className="action-btn" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-danger)' }} title="Remove">
                        <Trash2 size={16} />
                    </button>
                </div>
            )
        },
    ];

    return (
        <div className="tickets-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>Technician Management</h1>
                    <p className="page-subtitle">Manage support team and workload</p>
                </div>
                <Button variant="primary" icon={<Plus size={18} />}>
                    Add Technician
                </Button>
            </div>

            <div className="stats-grid" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <Card className="stat-card" hover>
                    <div className="stat-value">{technicians.filter(t => t.activeStatus).length}</div>
                    <div className="stat-title">Active Technicians</div>
                </Card>
                <Card className="stat-card" hover>
                    <div className="stat-value">{technicians.reduce((sum, t) => sum + t.assignedTickets, 0)}</div>
                    <div className="stat-title">Total Assigned Tickets</div>
                </Card>
                <Card className="stat-card" hover>
                    <div className="stat-value">{technicians.reduce((sum, t) => sum + t.resolvedTickets, 0)}</div>
                    <div className="stat-title">Total Resolved</div>
                </Card>
            </div>

            <Card className="table-card">
                <div className="table-header">
                    <h3>All Technicians ({technicians.length})</h3>
                </div>
                {loading ? (
                    <div className="loading-state">Loading technicians...</div>
                ) : (
                    <Table columns={columns} data={technicians} />
                )}
            </Card>
        </div>
    );
};

export default Technicians;
