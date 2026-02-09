import React, { useState, useEffect } from 'react';
import './SLATimer.css';

/**
 * SLATimer Component
 * Displays a countdown timer for ticket SLA deadlines with color-coded urgency
 * Colors: Green (>50% remaining), Yellow (25-50%), Red (<25% or breached)
 */
const SLATimer = ({ slaDeadline, slaBreached }) => {
    const [timeRemaining, setTimeRemaining] = useState(null);
    const [urgencyLevel, setUrgencyLevel] = useState('normal');

    useEffect(() => {
        if (!slaDeadline) return;

        const calculateTime = () => {
            const deadline = new Date(slaDeadline);
            const now = new Date();
            const diffMs = deadline - now;

            if (diffMs <= 0 || slaBreached) {
                setTimeRemaining({ breached: true, text: 'SLA Breached' });
                setUrgencyLevel('critical');
                return;
            }

            // Calculate remaining time
            const hours = Math.floor(diffMs / (1000 * 60 * 60));
            const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

            let text;
            if (hours >= 24) {
                const days = Math.floor(hours / 24);
                const remainingHours = hours % 24;
                text = `${days}d ${remainingHours}h remaining`;
            } else if (hours > 0) {
                text = `${hours}h ${minutes}m remaining`;
            } else {
                text = `${minutes}m remaining`;
            }

            setTimeRemaining({ breached: false, text, hours, minutes });

            // Calculate urgency based on percentage of total SLA time
            // Assuming we need to know original SLA time, use hours as proxy
            if (hours < 1) {
                setUrgencyLevel('critical');
            } else if (hours < 4) {
                setUrgencyLevel('warning');
            } else {
                setUrgencyLevel('normal');
            }
        };

        calculateTime();
        const interval = setInterval(calculateTime, 60000); // Update every minute

        return () => clearInterval(interval);
    }, [slaDeadline, slaBreached]);

    if (!slaDeadline) {
        return <span className="sla-timer sla-timer-none">No SLA</span>;
    }

    if (!timeRemaining) {
        return <span className="sla-timer sla-timer-loading">...</span>;
    }

    return (
        <span className={`sla-timer sla-timer-${urgencyLevel}`}>
            {timeRemaining.breached ? (
                <span className="sla-breached">⚠️ {timeRemaining.text}</span>
            ) : (
                <span className="sla-remaining">⏱️ {timeRemaining.text}</span>
            )}
        </span>
    );
};

/**
 * SLADueDate Component
 * For user-facing display - shows "Due on: [Date/Time]" instead of countdown
 */
export const SLADueDate = ({ slaDeadline, slaBreached }) => {
    if (!slaDeadline) {
        return <span className="sla-due-date sla-due-none">-</span>;
    }

    const deadline = new Date(slaDeadline);
    const now = new Date();
    const isOverdue = deadline < now || slaBreached;

    const formatDate = (date) => {
        const options = {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('en-US', options);
    };

    return (
        <span className={`sla-due-date ${isOverdue ? 'sla-due-overdue' : ''}`}>
            {isOverdue ? (
                <span>⚠️ Overdue</span>
            ) : (
                <span>Due on: {formatDate(deadline)}</span>
            )}
        </span>
    );
};

export default SLATimer;
