import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Search, Filter, Eye, UserPlus, Edit, XCircle, Download, Calendar } from 'lucide-react';
import Card from '../components/UI/Card';
import Table from '../components/UI/Table';
import Button from '../components/UI/Button';
import Badge, { PriorityBadge, StatusBadge } from '../components/UI/Badge';
import Modal from '../components/UI/Modal';
import SLATimer from '../components/UI/SLATimer';
import { ticketsAPI, techniciansAPI } from '../services/api';
import './Tickets.css';

const Tickets = () => {
    const [tickets, setTickets] = useState([]);
    const [technicians, setTechnicians] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [filterPriority, setFilterPriority] = useState('all');
    const [filterDatePreset, setFilterDatePreset] = useState('all');
    const [filterDateFrom, setFilterDateFrom] = useState('');
    const [filterDateTo, setFilterDateTo] = useState('');
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

    const filteredTickets = useMemo(() => tickets.filter(ticket => {
        const matchesSearch = ticket.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            ticket.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
            ticket.subject.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus;
        const matchesPriority = filterPriority === 'all' || ticket.priority === filterPriority;

        // Date filter
        let matchesDate = true;
        if (filterDateFrom || filterDateTo) {
            const ticketDate = new Date(ticket.createdAt);
            if (filterDateFrom) {
                const from = new Date(filterDateFrom);
                from.setHours(0, 0, 0, 0);
                if (ticketDate < from) matchesDate = false;
            }
            if (filterDateTo) {
                const to = new Date(filterDateTo);
                to.setHours(23, 59, 59, 999);
                if (ticketDate > to) matchesDate = false;
            }
        }

        return matchesSearch && matchesStatus && matchesPriority && matchesDate;
    }), [tickets, searchTerm, filterStatus, filterPriority, filterDateFrom, filterDateTo]);

    const handleDatePresetChange = (preset) => {
        setFilterDatePreset(preset);
        const now = new Date();
        const today = now.toISOString().split('T')[0];

        switch (preset) {
            case 'today': {
                setFilterDateFrom(today);
                setFilterDateTo(today);
                break;
            }
            case 'yesterday': {
                const yesterday = new Date(now);
                yesterday.setDate(yesterday.getDate() - 1);
                const yd = yesterday.toISOString().split('T')[0];
                setFilterDateFrom(yd);
                setFilterDateTo(yd);
                break;
            }
            case 'this_week': {
                const startOfWeek = new Date(now);
                startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
                setFilterDateFrom(startOfWeek.toISOString().split('T')[0]);
                setFilterDateTo(today);
                break;
            }
            case 'this_month': {
                const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
                setFilterDateFrom(startOfMonth.toISOString().split('T')[0]);
                setFilterDateTo(today);
                break;
            }
            case 'last_30': {
                const last30 = new Date(now);
                last30.setDate(last30.getDate() - 30);
                setFilterDateFrom(last30.toISOString().split('T')[0]);
                setFilterDateTo(today);
                break;
            }
            case 'custom':
                // Keep current from/to — user will pick manually
                break;
            default:
                setFilterDateFrom('');
                setFilterDateTo('');
        }
    };

    const handleDownloadCSV = () => {
        if (filteredTickets.length === 0) return;

        const headers = [
            'Ticket ID', 'User', 'Email', 'Category', 'Priority', 'Status',
            'Assigned To', 'Assignment Group', 'Subject', 'Description',
            'SLA Deadline', 'SLA Breached', 'Created At', 'Updated At', 'Resolved At'
        ];

        const escapeCSV = (val) => {
            if (val === null || val === undefined) return '';
            const str = String(val);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        };

        const rows = filteredTickets.map(t => [
            t.id,
            t.userName,
            t.userEmail,
            t.category,
            t.priority,
            t.status,
            t.assignedTo || '',
            t.assignmentGroup || '',
            t.subject,
            t.description,
            t.slaDeadline ? new Date(t.slaDeadline).toLocaleString() : '',
            t.slaBreached ? 'Yes' : 'No',
            t.createdAt ? new Date(t.createdAt).toLocaleString() : '',
            t.updatedAt ? new Date(t.updatedAt).toLocaleString() : '',
            t.resolvedAt ? new Date(t.resolvedAt).toLocaleString() : ''
        ].map(escapeCSV));

        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const dateStr = new Date().toISOString().split('T')[0];
        link.download = `tickets_${dateStr}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

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
            key: 'slaDeadline',
            label: 'SLA',
            sortable: true,
            render: (value, row) => <SLATimer slaDeadline={value} slaBreached={row.slaBreached} status={row.status} />
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
                            <option value="P4">P4 (Low)</option>
                            <option value="P3">P3 (Medium)</option>
                            <option value="P2">P2 (High)</option>
                        </select>
                    </div>
                </div>

                {/* Date / Period Filter Row */}
                <div className="filters-row filters-row-date">
                    <div className="filter-group">
                        <Calendar size={18} />
                        <select
                            value={filterDatePreset}
                            onChange={(e) => handleDatePresetChange(e.target.value)}
                            className="filter-select"
                        >
                            <option value="all">All Time</option>
                            <option value="today">Today</option>
                            <option value="yesterday">Yesterday</option>
                            <option value="this_week">This Week</option>
                            <option value="this_month">This Month</option>
                            <option value="last_30">Last 30 Days</option>
                            <option value="custom">Custom Range</option>
                        </select>

                        {filterDatePreset === 'custom' && (
                            <>
                                <input
                                    type="date"
                                    value={filterDateFrom}
                                    onChange={(e) => setFilterDateFrom(e.target.value)}
                                    className="filter-date-input"
                                    placeholder="From"
                                />
                                <span className="date-range-separator">to</span>
                                <input
                                    type="date"
                                    value={filterDateTo}
                                    onChange={(e) => setFilterDateTo(e.target.value)}
                                    className="filter-date-input"
                                    placeholder="To"
                                />
                            </>
                        )}

                        {filterDatePreset !== 'all' && filterDatePreset !== 'custom' && filterDateFrom && (
                            <span className="date-range-label">
                                {filterDateFrom}{filterDateTo && filterDateTo !== filterDateFrom ? ` — ${filterDateTo}` : ''}
                            </span>
                        )}
                    </div>
                </div>
            </Card>

            <Card className="table-card">
                <div className="table-header">
                    <h3>All Tickets ({filteredTickets.length})</h3>
                    <Button
                        variant="secondary"
                        onClick={handleDownloadCSV}
                        disabled={filteredTickets.length === 0}
                        className="download-btn"
                    >
                        <Download size={16} />
                        Download CSV
                    </Button>
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

                        {/* Helpful Solutions - solutions that helped the user */}
                        {selectedTicket.solutionFeedback && selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'helpful' || s.feedbackType === 'tried').length > 0 && (
                            <div className="detail-section">
                                <label>💡 Solutions That Helped</label>
                                <div className="feedback-solutions-list">
                                    {selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'helpful' || s.feedbackType === 'tried').map((sol, idx) => (
                                        <div key={idx} className={`feedback-solution-item ${sol.feedbackType === 'helpful' ? 'feedback-helpful' : 'feedback-tried'}`}>
                                            <span><strong>Step {sol.index}:</strong> {sol.text}</span>
                                            <span className="feedback-badge-label">
                                                {sol.feedbackType === 'helpful' ? '👍 Helpful' : '✅ Tried'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Not Helpful Solutions */}
                        {selectedTicket.solutionFeedback && selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'not_helpful').length > 0 && (
                            <div className="detail-section">
                                <label>👎 Solutions Not Helpful</label>
                                <div className="feedback-solutions-list">
                                    {selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'not_helpful').map((sol, idx) => (
                                        <div key={idx} className="feedback-solution-item feedback-not-helpful">
                                            <span><strong>Step {sol.index}:</strong> {sol.text}</span>
                                            <span className="feedback-badge-label">
                                                👎 Not Helpful
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Feedback Summary Counts (only shown if more than 1 feedback) */}
                        {selectedTicket.solutionFeedback && selectedTicket.solutionFeedback.length > 1 && (
                            <div className="detail-section">
                                <label>📊 Feedback Summary</label>
                                <div className="feedback-summary">
                                    {selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'helpful').length > 0 && (
                                        <span className="feedback-count-helpful">
                                            👍 {selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'helpful').length} found helpful
                                        </span>
                                    )}
                                    {selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'not_helpful').length > 0 && (
                                        <span className="feedback-count-not-helpful">
                                            👎 {selectedTicket.solutionFeedback.filter(s => s.feedbackType === 'not_helpful').length} found not helpful
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Support both attachmentUrls (array) and legacy attachmentUrl (string) */}
                        {(selectedTicket.attachmentUrls?.length > 0 || selectedTicket.attachmentUrl) && (
                            <div className="detail-section">
                                <label>Attachments ({(selectedTicket.attachmentUrls || [selectedTicket.attachmentUrl].filter(Boolean)).length})</label>
                                <div className="attachments-grid">
                                    {(selectedTicket.attachmentUrls || [selectedTicket.attachmentUrl].filter(Boolean)).map((url, index) => (
                                        <div key={index} className="attachment-item">
                                            <img
                                                src={url}
                                                alt={`Attachment ${index + 1}`}
                                                className="attachment-img"
                                            />
                                            <a
                                                href={url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="attachment-link"
                                            >
                                                🔗 Open #{index + 1}
                                            </a>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

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
