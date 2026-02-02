import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, Eye, UserPlus, Edit, XCircle } from 'lucide-react';
import Card from '../components/UI/Card';
import Table from '../components/UI/Table';
import Button from '../components/UI/Button';
import Badge, { PriorityBadge, StatusBadge } from '../components/UI/Badge';
import Modal from '../components/UI/Modal';
import { ticketsAPI, techniciansAPI } from '../services/api';
import './Tickets.css';

const Tickets = () => {
    const [tickets, setTickets] = useState([]);
    const [technicians, setTechnicians] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [filterPriority, setFilterPriority] = useState('all');
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [showDetailModal, setShowDetailModal] = useState(false);
    
    // Track modifications
    const [editedTicket, setEditedTicket] = useState(null);
    const [hasChanges, setHasChanges] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [ticketsRes, techsRes] = await Promise.all([
                ticketsAPI.getAll(),
                techniciansAPI.getAll()
            ]);
            setTickets(ticketsRes.data);
            setTechnicians(techsRes.data.filter(t => t.activeStatus));
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleViewTicket = (ticket) => {
        setSelectedTicket(ticket);
        setEditedTicket({
            status: ticket.status,
            assignedToId: ticket.assignedToId || '',
            resolutionNotes: ticket.resolutionNotes || ''
        });
        setHasChanges(false);
        setShowDetailModal(true);
    };

    const handleCloseModal = () => {
        setShowDetailModal(false);
        setSelectedTicket(null);
        setEditedTicket(null);
        setHasChanges(false);
    };

    const handleFieldChange = (field, value) => {
        setEditedTicket(prev => ({
            ...prev,
            [field]: value
        }));
        
        // Check if anything actually changed from original
        const original = {
            status: selectedTicket.status,
            assignedToId: selectedTicket.assignedToId || '',
            resolutionNotes: selectedTicket.resolutionNotes || ''
        };
        
        const newValues = {
            ...editedTicket,
            [field]: value
        };
        
        const changed = 
            newValues.status !== original.status ||
            newValues.assignedToId !== original.assignedToId ||
            newValues.resolutionNotes !== original.resolutionNotes;
        
        setHasChanges(changed);
    };

    const handleSaveChanges = async () => {
        if (!hasChanges || saving) return;
        
        setSaving(true);
        try {
            // Update status if changed
            if (editedTicket.status !== selectedTicket.status) {
                await ticketsAPI.update(selectedTicket.id, { 
                    status: editedTicket.status,
                    resolution_notes: editedTicket.resolutionNotes
                });
            }
            
            // Update assignment if changed
            if (editedTicket.assignedToId !== (selectedTicket.assignedToId || '')) {
                if (editedTicket.assignedToId) {
                    await ticketsAPI.assign(selectedTicket.id, editedTicket.assignedToId);
                }
            }
            
            // Reload data and close modal
            await loadData();
            handleCloseModal();
        } catch (error) {
            console.error('Error saving changes:', error);
            alert('Failed to save changes. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const filteredTickets = tickets.filter(ticket => {
        const matchesSearch = ticket.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            ticket.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
            ticket.subject.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus;
        const matchesPriority = filterPriority === 'all' || ticket.priority === filterPriority;
        return matchesSearch && matchesStatus && matchesPriority;
    });

    const columns = [
        { key: 'id', label: 'Ticket ID', sortable: true },
        { key: 'userName', label: 'User', sortable: true },
        {
            key: 'category',
            label: 'Category',
            sortable: true,
            render: (value) => <Badge variant="default">{value}</Badge>
        },
        {
            key: 'priority',
            label: 'Priority',
            sortable: true,
            render: (value) => <PriorityBadge priority={value} />
        },
        {
            key: 'status',
            label: 'Status',
            sortable: true,
            render: (value) => <StatusBadge status={value} />
        },
        {
            key: 'assignedTo',
            label: 'Assigned To',
            sortable: true,
            render: (value) => value || <span className="text-muted">Unassigned</span>
        },
        {
            key: 'createdAt',
            label: 'Created',
            sortable: true,
            render: (value) => new Date(value).toLocaleDateString()
        },
        {
            key: 'actions',
            label: 'Actions',
            sortable: false,
            render: (_, row) => (
                <div className="table-actions">
                    <button
                        className="action-btn action-btn-view"
                        onClick={(e) => { e.stopPropagation(); handleViewTicket(row); }}
                        title="View Details"
                    >
                        <Eye size={16} />
                    </button>
                </div>
            )
        },
    ];

    return (
        <div className="tickets-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>Ticket Management</h1>
                    <p className="page-subtitle">Manage and track all support tickets</p>
                </div>
                <Button variant="primary" icon={<Plus size={18} />}>
                    Create Ticket
                </Button>
            </div>

            <Card className="filters-card" glass>
                <div className="filters-row">
                    <div className="search-box">
                        <Search size={18} className="search-icon" />
                        <input
                            type="text"
                            placeholder="Search by ticket ID, user, or subject..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>

                    <div className="filter-group">
                        <Filter size={18} />
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="filter-select"
                        >
                            <option value="all">All Status</option>
                            <option value="Open">Open</option>
                            <option value="In Progress">In Progress</option>
                            <option value="Resolved">Resolved</option>
                            <option value="Closed">Closed</option>
                        </select>

                        <select
                            value={filterPriority}
                            onChange={(e) => setFilterPriority(e.target.value)}
                            className="filter-select"
                        >
                            <option value="all">All Priority</option>
                            <option value="Low">Low</option>
                            <option value="Medium">Medium</option>
                            <option value="High">High</option>
                            <option value="Critical">Critical</option>
                        </select>
                    </div>
                </div>
            </Card>

            <Card className="table-card">
                <div className="table-header">
                    <h3>All Tickets ({filteredTickets.length})</h3>
                </div>
                {loading ? (
                    <div className="loading-state">Loading tickets...</div>
                ) : (
                    <Table
                        columns={columns}
                        data={filteredTickets}
                        onRowClick={handleViewTicket}
                    />
                )}
            </Card>

            {/* Ticket Detail Modal */}
            <Modal
                isOpen={showDetailModal}
                onClose={handleCloseModal}
                title={`Ticket Details - ${selectedTicket?.id}`}
                size="large"
                footer={
                    <>
                        <Button variant="secondary" onClick={handleCloseModal}>
                            Close
                        </Button>
                        <Button 
                            variant="success" 
                            onClick={handleSaveChanges}
                            disabled={!hasChanges || saving}
                        >
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </>
                }
            >
                {selectedTicket && editedTicket && (
                    <div className="ticket-detail">
                        <div className="detail-grid">
                            <div className="detail-item">
                                <label>User</label>
                                <div>{selectedTicket.userName}</div>
                            </div>
                            <div className="detail-item">
                                <label>Email</label>
                                <div>{selectedTicket.userEmail}</div>
                            </div>
                            <div className="detail-item">
                                <label>Category</label>
                                <div><Badge>{selectedTicket.category}</Badge></div>
                            </div>
                            <div className="detail-item">
                                <label>Priority</label>
                                <div><PriorityBadge priority={selectedTicket.priority} /></div>
                            </div>
                            <div className="detail-item">
                                <label>Status</label>
                                <div>
                                    <select
                                        value={editedTicket.status}
                                        onChange={(e) => handleFieldChange('status', e.target.value)}
                                        className="status-select"
                                    >
                                        <option value="Open">Open</option>
                                        <option value="In Progress">In Progress</option>
                                        <option value="Resolved">Resolved</option>
                                        <option value="Closed">Closed</option>
                                    </select>
                                </div>
                            </div>
                            <div className="detail-item">
                                <label>Assigned To</label>
                                <div>
                                    <select
                                        value={editedTicket.assignedToId}
                                        onChange={(e) => handleFieldChange('assignedToId', e.target.value)}
                                        className="assign-select"
                                    >
                                        <option value="">Unassigned</option>
                                        {technicians.map(tech => (
                                            <option key={tech.id} value={tech.id}>{tech.name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div className="detail-section">
                            <label>Subject</label>
                            <div className="detail-value">{selectedTicket.subject}</div>
                        </div>

                        <div className="detail-section">
                            <label>Description</label>
                            <div className="detail-value">{selectedTicket.description}</div>
                        </div>

                        <div className="detail-section">
                            <label>Resolution Notes</label>
                            <textarea
                                className="resolution-textarea"
                                placeholder="Add resolution notes..."
                                value={editedTicket.resolutionNotes}
                                onChange={(e) => handleFieldChange('resolutionNotes', e.target.value)}
                                rows={4}
                            />
                        </div>

                        <div className="detail-footer">
                            <div className="detail-meta">
                                <span>Created: {new Date(selectedTicket.createdAt).toLocaleString()}</span>
                                <span>Updated: {new Date(selectedTicket.updatedAt).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default Tickets;
