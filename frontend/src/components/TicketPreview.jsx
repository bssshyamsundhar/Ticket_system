import React from 'react';
import './TicketPreview.css';

function TicketPreview({ ticket, onClose }) {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    const colors = {
      open: '#ffc107',
      in_progress: '#2196f3',
      resolved: '#4caf50',
      closed: '#9e9e9e'
    };
    return colors[status] || '#9e9e9e';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>🎫 Ticket Details</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="ticket-info">
            <div className="info-row">
              <span className="label">Ticket ID:</span>
              <span className="value">#{ticket.id}</span>
            </div>

            <div className="info-row">
              <span className="label">Status:</span>
              <span
                className="status-badge"
                style={{ backgroundColor: getStatusColor(ticket.status) }}
              >
                {ticket.status?.toUpperCase()}
              </span>
            </div>

            <div className="info-row">
              <span className="label">Created:</span>
              <span className="value">{formatDate(ticket.created_at)}</span>
            </div>

            {ticket.updated_at && ticket.updated_at !== ticket.created_at && (
              <div className="info-row">
                <span className="label">Updated:</span>
                <span className="value">{formatDate(ticket.updated_at)}</span>
              </div>
            )}

            {ticket.sla_deadline && (
              <div className="info-row">
                <span className="label">SLA Deadline:</span>
                <span className={`value ${new Date(ticket.sla_deadline) < new Date() ? 'overdue' : ''}`}>
                  {ticket.sla_breached ? (
                    <span style={{ color: '#dc2626', fontWeight: '600' }}>⚠️ Overdue</span>
                  ) : (
                    <>Due on: {formatDate(ticket.sla_deadline)}</>
                  )}
                </span>
              </div>
            )}

            <div className="info-section">
              <span className="label">Issue Summary:</span>
              <div className="value-block">{ticket.issue_summary}</div>
            </div>

            {ticket.refined_query && (
              <div className="info-section">
                <span className="label">Refined Query:</span>
                <div className="value-block">{ticket.refined_query}</div>
              </div>
            )}

            {ticket.confidence_score !== null && ticket.confidence_score !== undefined && (
              <div className="info-row">
                <span className="label">KB Confidence:</span>
                <span className="value">{(ticket.confidence_score * 100).toFixed(1)}%</span>
              </div>
            )}

            {ticket.resolution_text && (
              <div className="info-section resolution">
                <span className="label">✅ Resolution:</span>
                <div className="value-block">{ticket.resolution_text}</div>
              </div>
            )}

            {ticket.resolved_at && (
              <div className="info-row">
                <span className="label">Resolved At:</span>
                <span className="value">{formatDate(ticket.resolved_at)}</span>
              </div>
            )}

            {/* Support both attachment_urls (array) and legacy attachment_url (string) */}
            {(ticket.attachment_urls?.length > 0 || ticket.attachment_url) && (
              <div className="info-section">
                <span className="label">📎 Attachments:</span>
                <div className="attachments-grid" style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                  gap: '12px',
                  marginTop: '8px'
                }}>
                  {(ticket.attachment_urls || [ticket.attachment_url].filter(Boolean)).map((url, index) => (
                    <div key={index} className="attachment-preview" style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      overflow: 'hidden',
                      background: '#f8f9fa'
                    }}>
                      <img
                        src={url}
                        alt={`Attachment ${index + 1}`}
                        style={{
                          width: '100%',
                          height: '120px',
                          objectFit: 'cover',
                          display: 'block'
                        }}
                      />
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'block',
                          padding: '8px',
                          color: '#2196f3',
                          textDecoration: 'none',
                          fontSize: '12px',
                          textAlign: 'center',
                          borderTop: '1px solid #eee'
                        }}
                      >
                        🔗 Open #{index + 1}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default TicketPreview;