import React from 'react';
import { Shield, CheckCircle, XCircle } from 'lucide-react';
import Card from '../components/UI/Card';
import Badge from '../components/UI/Badge';
import '../pages/Tickets.css';

const Roles = () => {
    const roles = [
        {
            name: 'Administrator',
            description: 'Full system access with all permissions',
            permissions: [
                'View all tickets',
                'Create/Edit/Delete tickets',
                'Manage technicians',
                'Manage knowledge base',
                'Configure priority rules',
                'View analytics',
                'Manage SLA settings',
                'View audit logs',
                'Configure notifications',
                'Manage roles and permissions'
            ]
        },
        {
            name: 'Technician',
            description: 'Limited access for support staff',
            permissions: [
                'View assigned tickets',
                'Update ticket status',
                'Add resolution notes',
                'View knowledge base',
                'View own performance metrics'
            ],
            restrictions: [
                'Cannot delete tickets',
                'Cannot manage other technicians',
                'Cannot configure system settings',
                'Cannot view audit logs'
            ]
        }
    ];

    return (
        <div className="tickets-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>Role-Based Access Control</h1>
                    <p className="page-subtitle">Manage user roles and permissions</p>
                </div>
            </div>

            <div style={{ display: 'grid', gap: 'var(--spacing-lg)', maxWidth: '1000px' }}>
                {roles.map((role, index) => (
                    <Card key={index} className="dashboard-card" glass>
                        <div style={{ display: 'flex', alignItems: 'start', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-lg)' }}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                background: 'var(--gradient-primary)',
                                borderRadius: 'var(--radius-md)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white'
                            }}>
                                <Shield size={24} />
                            </div>
                            <div style={{ flex: 1 }}>
                                <h3 style={{ margin: 0, marginBottom: 'var(--spacing-xs)' }}>{role.name}</h3>
                                <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                                    {role.description}
                                </p>
                            </div>
                            <Badge variant="primary">{role.name === 'Administrator' ? 'Full Access' : 'Limited Access'}</Badge>
                        </div>

                        <div>
                            <h4 style={{ marginBottom: 'var(--spacing-md)', fontSize: 'var(--font-size-base)' }}>Permissions</h4>
                            <div style={{ display: 'grid', gap: 'var(--spacing-sm)' }}>
                                {role.permissions.map((perm, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                                        <CheckCircle size={16} color="var(--color-success)" />
                                        <span style={{ color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}>{perm}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {role.restrictions && (
                            <div style={{ marginTop: 'var(--spacing-lg)' }}>
                                <h4 style={{ marginBottom: 'var(--spacing-md)', fontSize: 'var(--font-size-base)' }}>Restrictions</h4>
                                <div style={{ display: 'grid', gap: 'var(--spacing-sm)' }}>
                                    {role.restrictions.map((rest, i) => (
                                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                                            <XCircle size={16} color="var(--color-danger)" />
                                            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>{rest}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </Card>
                ))}
            </div>
        </div>
    );
};

export default Roles;
