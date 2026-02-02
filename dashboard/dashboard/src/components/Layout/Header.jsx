import React, { useState, useEffect } from 'react';
import { Bell, Moon, Sun, User, Search, LogOut } from 'lucide-react';
import './Header.css';

const Header = ({ user, onLogout }) => {
    const [darkMode, setDarkMode] = useState(false);
    const [notifications, setNotifications] = useState(3);

    useEffect(() => {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            setDarkMode(true);
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }, []);

    const toggleDarkMode = () => {
        const newMode = !darkMode;
        setDarkMode(newMode);

        if (newMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    };

    return (
        <header className="header">
            <div className="header-search">
                <Search size={18} className="search-icon" />
                <input
                    type="text"
                    placeholder="Search tickets, users, articles..."
                    className="search-input"
                />
            </div>

            <div className="header-actions">
                <button
                    className="header-action-btn"
                    onClick={toggleDarkMode}
                    aria-label="Toggle dark mode"
                >
                    {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                </button>

                <button className="header-action-btn notification-btn" aria-label="Notifications">
                    <Bell size={20} />
                    {notifications > 0 && (
                        <span className="notification-badge">{notifications}</span>
                    )}
                </button>

                <div className="header-user">
                    <div className="user-avatar">
                        <User size={18} />
                    </div>
                    <div className="user-info">
                        <div className="user-name">{user?.name || 'Admin User'}</div>
                        <div className="user-role">{user?.role || 'Administrator'}</div>
                    </div>
                </div>

                {onLogout && (
                    <button 
                        className="header-action-btn logout-btn" 
                        onClick={onLogout}
                        aria-label="Logout"
                        title="Logout"
                    >
                        <LogOut size={20} />
                    </button>
                )}
            </div>
        </header>
    );
};

export default Header;
