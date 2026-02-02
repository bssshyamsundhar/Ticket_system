import React from 'react';
import './Badge.css';

const Badge = ({
    children,
    variant = 'default',
    size = 'medium',
    className = '',
    ...props
}) => {
    const badgeClass = `
    badge
    badge-${variant}
    badge-${size}
    ${className}
  `.trim();

    return (
        <span className={badgeClass} {...props}>
            {children}
        </span>
    );
};

// Priority badge helper
export const PriorityBadge = ({ priority }) => {
    const variantMap = {
        'Low': 'default',
        'Medium': 'warning',
        'High': 'info',
        'Critical': 'danger',
    };

    return <Badge variant={variantMap[priority] || 'default'}>{priority}</Badge>;
};

// Status badge helper
export const StatusBadge = ({ status }) => {
    const variantMap = {
        'Open': 'info',
        'In Progress': 'warning',
        'Resolved': 'success',
        'Closed': 'default',
    };

    return <Badge variant={variantMap[status] || 'default'}>{status}</Badge>;
};

export default Badge;
