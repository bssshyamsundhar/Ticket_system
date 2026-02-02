import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Ticket,
    Users,
    Settings,
    BarChart3,
    Shield,
    FileText
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ isCollapsed, onToggle }) => {
    const menuItems = [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/tickets', icon: Ticket, label: 'Tickets' },
        { path: '/technicians', icon: Users, label: 'Technicians' },
        { path: '/analytics', icon: BarChart3, label: 'Analytics' },
        { path: '/roles', icon: Shield, label: 'Roles & Access' },
        { path: '/audit-logs', icon: FileText, label: 'Audit Logs' },
    ];

    return (
        <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="logo-icon">
                        <Settings size={24} />
                    </div>
                    {!isCollapsed && <span className="logo-text">IT Support Admin</span>}
                </div>
            </div>

            <nav className="sidebar-nav">
                {menuItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `sidebar-link ${isActive ? 'active' : ''}`
                        }
                        title={isCollapsed ? item.label : ''}
                    >
                        <item.icon size={20} className="sidebar-icon" />
                        {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
                <button className="sidebar-toggle" onClick={onToggle}>
                    {isCollapsed ? '→' : '←'}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
