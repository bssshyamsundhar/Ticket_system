import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Edit, Trash2, RefreshCw } from 'lucide-react';
import Card from '../components/UI/Card';
import Table from '../components/UI/Table';
import Button from '../components/UI/Button';
import Badge from '../components/UI/Badge';
import Modal from '../components/UI/Modal';
import { techniciansAPI, techStatsAPI } from '../services/api';
import '../pages/Tickets.css';

// Check if a technician is currently on shift based on IST time
const isOnShift = (shiftStart, shiftEnd) => {
    if (!shiftStart || !shiftEnd) return false;
    const parseTime = (timeStr) => {
        const parts = String(timeStr).split(':');
        return parseInt(parts[0]) * 60 + parseInt(parts[1] || 0);
    };
    const now = new Date();
    const istOffset = 5.5 * 60;
    const utcMinutes = now.getUTCHours() * 60 + now.getUTCMinutes();
    const istMinutes = (utcMinutes + istOffset) % (24 * 60);
    const start = parseTime(shiftStart);
    const end = parseTime(shiftEnd);
    if (start < end) {
        return istMinutes >= start && istMinutes < end;
    } else {
        return istMinutes >= start || istMinutes < end;
    }
};

const formatShiftTime = (timeStr) => {
    if (!timeStr) return '-';
    const parts = String(timeStr).split(':');
    const h = parseInt(parts[0]);
    const m = parts[1] || '00';
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return `${h12}:${m} ${ampm}`;
};

const Technicians = () => {
    const [technicians, setTechnicians] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [editingTech, setEditingTech] = useState(null);
    const [deletingTech, setDeletingTech] = useState(null);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState({
        name: '', email: '', role: '', department: 'IT Support',
        active_status: true, shift_start: '', shift_end: ''
    });

    const loadTechnicians = useCallback(async () => {
        try {
            const [techRes, statsRes] = await Promise.all([
                techniciansAPI.getAll(),
                techStatsAPI.getRealStats()
            ]);
            const techs = techRes.data;
            const stats = statsRes.data;
            const statsMap = {};
            stats.forEach(s => { statsMap[s.id] = s; });
            const merged = techs.map(t => ({
                ...t,
                resolvedTickets: statsMap[t.id]?.real_resolved ?? statsMap[t.id]?.realResolved ?? t.resolvedTickets,
                assignedTickets: statsMap[t.id]?.real_assigned ?? statsMap[t.id]?.realAssigned ?? t.assignedTickets,
                onShift: isOnShift(t.shiftStart, t.shiftEnd),
            }));
            setTechnicians(merged);
        } catch (error) {
            console.error('Error loading technicians:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadTechnicians();
        const interval = setInterval(loadTechnicians, 60000);
        return () => clearInterval(interval);
    }, [loadTechnicians]);

    const handleAddNew = () => {
        setEditingTech(null);
        setFormData({ name: '', email: '', role: '', department: 'IT Support', active_status: true, shift_start: '', shift_end: '' });
        setShowModal(true);
    };

    const handleEdit = (tech) => {
        setEditingTech(tech);
        setFormData({
            name: tech.name || '', email: tech.email || '', role: tech.role || '',
            department: tech.department || 'IT Support', active_status: tech.activeStatus !== false,
            shift_start: tech.shiftStart ? String(tech.shiftStart).slice(0, 5) : '',
            shift_end: tech.shiftEnd ? String(tech.shiftEnd).slice(0, 5) : '',
        });
        setShowModal(true);
    };

    const handleDelete = (tech) => { setDeletingTech(tech); setShowDeleteConfirm(true); };

    const confirmDelete = async () => {
        if (!deletingTech) return;
        setSaving(true);
        try {
            await techniciansAPI.delete(deletingTech.id);
            setShowDeleteConfirm(false); setDeletingTech(null);
            await loadTechnicians();
        } catch (error) { console.error('Error deleting technician:', error); alert('Failed to delete technician.'); }
        finally { setSaving(false); }
    };

    const handleSave = async () => {
        if (!formData.name || !formData.email || !formData.role) { alert('Name, Email, and Role are required.'); return; }
        setSaving(true);
        try {
            const payload = {
                name: formData.name, email: formData.email, role: formData.role,
                department: formData.department, active_status: formData.active_status,
                shift_start: formData.shift_start || null, shift_end: formData.shift_end || null,
            };
            if (editingTech) { await techniciansAPI.update(editingTech.id, payload); }
            else { await techniciansAPI.create(payload); }
            setShowModal(false); await loadTechnicians();
        } catch (error) { console.error('Error saving technician:', error); alert('Failed to save technician.'); }
        finally { setSaving(false); }
    };

    const onShiftCount = technicians.filter(t => t.onShift).length;

    const columns = [
        { key: 'id', label: 'ID', sortable: true },
        { key: 'name', label: 'Name', sortable: true },
        { key: 'email', label: 'Email', sortable: true },
        { key: 'role', label: 'Role', sortable: true },
        {
            key: 'onShift', label: 'Shift Status', sortable: true,
            render: (_, row) => (
                <Badge variant={row.onShift ? 'success' : 'default'}>
                    {row.onShift ? '🟢 On Shift' : '⚫ Off Shift'}
                </Badge>
            )
        },
        {
            key: 'shiftStart', label: 'Shift', sortable: false,
            render: (_, row) => (
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                    {row.shiftStart ? `${formatShiftTime(row.shiftStart)} - ${formatShiftTime(row.shiftEnd)}` : 'Not set'}
                </span>
            )
        },
        { key: 'assignedTickets', label: 'Assigned', sortable: true },
        { key: 'resolvedTickets', label: 'Resolved', sortable: true },
        {
            key: 'actions', label: 'Actions', sortable: false,
            render: (_, row) => (
                <div className="table-actions">
                    <button className="action-btn action-btn-view" title="Edit" onClick={(e) => { e.stopPropagation(); handleEdit(row); }}>
                        <Edit size={16} />
                    </button>
                    <button className="action-btn" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-danger)' }} title="Remove" onClick={(e) => { e.stopPropagation(); handleDelete(row); }}>
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
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Button variant="secondary" icon={<RefreshCw size={18} />} onClick={loadTechnicians}>Refresh</Button>
                    <Button variant="primary" icon={<Plus size={18} />} onClick={handleAddNew}>Add Technician</Button>
                </div>
            </div>

            <div className="stats-grid" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <Card className="stat-card" hover>
                    <div className="stat-value" style={{ color: 'var(--color-success)' }}>{onShiftCount}</div>
                    <div className="stat-title">On Shift Now</div>
                </Card>
                <Card className="stat-card" hover>
                    <div className="stat-value">{technicians.reduce((sum, t) => sum + (t.assignedTickets || 0), 0)}</div>
                    <div className="stat-title">Active Assigned Tickets</div>
                </Card>
                <Card className="stat-card" hover>
                    <div className="stat-value">{technicians.reduce((sum, t) => sum + (t.resolvedTickets || 0), 0)}</div>
                    <div className="stat-title">Total Resolved</div>
                </Card>
            </div>

            <Card className="table-card">
                <div className="table-header"><h3>All Technicians ({technicians.length})</h3></div>
                {loading ? <div className="loading-state">Loading technicians...</div> : <Table columns={columns} data={technicians} />}
            </Card>

            {/* Add/Edit Modal */}
            <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editingTech ? `Edit Technician - ${editingTech.name}` : 'Add New Technician'} size="medium"
                footer={<><Button variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button><Button variant="primary" onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : editingTech ? 'Update' : 'Create'}</Button></>}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.3rem', fontWeight: 500, fontSize: '0.875rem' }}>Name *</label>
                            <input type="text" value={formData.name} onChange={(e) => setFormData(f => ({ ...f, name: e.target.value }))} className="filter-select" style={{ width: '100%', padding: '0.6rem' }} placeholder="Full name" />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.3rem', fontWeight: 500, fontSize: '0.875rem' }}>Email *</label>
                            <input type="email" value={formData.email} onChange={(e) => setFormData(f => ({ ...f, email: e.target.value }))} className="filter-select" style={{ width: '100%', padding: '0.6rem' }} placeholder="email@company.com" />
                        </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.3rem', fontWeight: 500, fontSize: '0.875rem' }}>Role *</label>
                            <select value={formData.role} onChange={(e) => setFormData(f => ({ ...f, role: e.target.value }))} className="filter-select" style={{ width: '100%', padding: '0.6rem' }}>
                                <option value="">Select Role</option>
                                <option value="L1 Support">L1 Support</option>
                                <option value="L2 Support">L2 Support</option>
                                <option value="L3 Support">L3 Support</option>
                                <option value="Desktop Engineer">Desktop Engineer</option>
                                <option value="Network Engineer">Network Engineer</option>
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.3rem', fontWeight: 500, fontSize: '0.875rem' }}>Department</label>
                            <input type="text" value={formData.department} onChange={(e) => setFormData(f => ({ ...f, department: e.target.value }))} className="filter-select" style={{ width: '100%', padding: '0.6rem' }} />
                        </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.3rem', fontWeight: 500, fontSize: '0.875rem' }}>Shift Start</label>
                            <input type="time" value={formData.shift_start} onChange={(e) => setFormData(f => ({ ...f, shift_start: e.target.value }))} className="filter-select" style={{ width: '100%', padding: '0.6rem' }} />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.3rem', fontWeight: 500, fontSize: '0.875rem' }}>Shift End</label>
                            <input type="time" value={formData.shift_end} onChange={(e) => setFormData(f => ({ ...f, shift_end: e.target.value }))} className="filter-select" style={{ width: '100%', padding: '0.6rem' }} />
                        </div>
                    </div>
                    <div>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <input type="checkbox" checked={formData.active_status} onChange={(e) => setFormData(f => ({ ...f, active_status: e.target.checked }))} />
                            <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>Active (available for assignment)</span>
                        </label>
                    </div>
                </div>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal isOpen={showDeleteConfirm} onClose={() => setShowDeleteConfirm(false)} title="Confirm Delete" size="small"
                footer={<><Button variant="secondary" onClick={() => setShowDeleteConfirm(false)}>Cancel</Button><Button variant="danger" onClick={confirmDelete} disabled={saving} style={{ background: 'var(--color-danger)', color: '#fff' }}>{saving ? 'Deleting...' : 'Delete'}</Button></>}
            >
                <p>Are you sure you want to delete <strong>{deletingTech?.name}</strong>?</p>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>All tickets assigned to this technician will be unassigned.</p>
            </Modal>
        </div>
    );
};

export default Technicians;
