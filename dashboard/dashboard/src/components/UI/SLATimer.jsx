import React, { useState, useEffect } from 'react';
import './SLATimer.css';

/**
 * Parse a date string safely, ensuring UTC interpretation.
 * Handles both RFC 2822 ("Tue, 10 Feb 2026 06:11:38 GMT") from Flask
 * and ISO 8601 ("2026-02-10T06:11:38") formats.
 * Returns a valid Date or null.
 */
const parseUTCDate = (value) => {
    if (!value) return null;
    let str = String(value);

    // Already has explicit timezone (GMT, UTC, Z, or offset) — parse directly
    if (str.includes('GMT') || str.includes('UTC') || str.endsWith('Z') || /[+-]\d{2}:\d{2}\s*$/.test(str)) {
        const d = new Date(str);
        return isNaN(d.getTime()) ? null : d;
    }

    // ISO-like naive datetime — treat as UTC by appending 'Z'
    str = str.replace(/^(\d{4}-\d{2}-\d{2})\s/, '$1T');
    if (!str.endsWith('Z')) str += 'Z';
    const d = new Date(str);
    return isNaN(d.getTime()) ? null : d;
};

/**
 * SLATimer Component
 * Displays a countdown timer for ticket SLA deadlines with color-coded urgency
 * Colors: Green (>50% remaining), Yellow (25-50%), Red (<25% or breached)
 */
const SLATimer = React.memo(({ slaDeadline, slaBreached, status }) => {
    const [timeRemaining, setTimeRemaining] = useState(null);
    const [urgencyLevel, setUrgencyLevel] = useState('normal');

    useEffect(() => {
        if (!slaDeadline) return;

        // For resolved/closed tickets, show static status — no countdown needed
        const isClosed = status === 'Resolved' || status === 'Closed';
        if (isClosed) {
            if (slaBreached) {
                setTimeRemaining({ breached: true, text: 'SLA Breached' });
                setUrgencyLevel('critical');
            } else {
                setTimeRemaining({ breached: false, text: 'SLA Met', hours: 999, minutes: 0 });
                setUrgencyLevel('normal');
            }
            return;
        }

        const calculateTime = () => {
            const deadline = parseUTCDate(slaDeadline);
            if (!deadline) {
                setTimeRemaining({ breached: false, text: 'No SLA', hours: 0, minutes: 0 });
                setUrgencyLevel('normal');
                return;
            }

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
    }, [slaDeadline, slaBreached, status]);

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
            ) : timeRemaining.text === 'SLA Met' ? (
                <span className="sla-met">✅ SLA Met</span>
            ) : (
                <span className="sla-remaining">⏱️ {timeRemaining.text}</span>
            )}
        </span>
    );
});

/**
 * SLADueDate Component
 * For user-facing display - shows "Due on: [Date/Time]" instead of countdown
 */
export const SLADueDate = ({ slaDeadline, slaBreached }) => {
    if (!slaDeadline) {
        return <span className="sla-due-date sla-due-none">-</span>;
    }

    const deadline = parseUTCDate(slaDeadline);
    if (!deadline) {
        return <span className="sla-due-date sla-due-none">-</span>;
    }

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
