import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import TicketPreview from './TicketPreview';
import './Chat.css';

function Chat({ user, token }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTicketPreview, setShowTicketPreview] = useState(false);
  const [ticketData, setTicketData] = useState(null);
  const [allTickets, setAllTickets] = useState([]);
  const [showAllTickets, setShowAllTickets] = useState(false);
  
  // Button-based flow state
  const [currentButtons, setCurrentButtons] = useState([]);
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [conversationState, setConversationState] = useState('start');
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize chat on mount
  useEffect(() => {
    startConversation();
  }, []);

  // Start or restart conversation
  const startConversation = async () => {
    setLoading(true);
    setShowOtherInput(false);
    setCurrentButtons([]);
    
    try {
      const response = await api.post('/api/chat', {
        action: 'start',
        session_id: sessionId
      });

      if (response.data.success) {
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
        
        setMessages([{
          type: 'agent',
          text: response.data.response,
          timestamp: new Date().toISOString()
        }]);
        
        setCurrentButtons(response.data.buttons || []);
        setConversationState(response.data.state || 'categories');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      setMessages([{
        type: 'error',
        text: 'Failed to connect to the server. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle button click
  const handleButtonClick = async (button) => {
    // Special case: "Other Issues" (general) opens free text input without category context
    if (button.action === 'other_issues') {
      setShowOtherInput(true);
      setCurrentButtons([{
        label: '⬅️ Back to Categories',
        action: 'go_back',
        value: 'back'
      }]);
      setConversationState('awaiting_free_text');
      
      const userMessage = {
        type: 'user',
        text: `Selected: ${button.label}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, userMessage, {
        type: 'agent',
        text: "Please describe your issue in detail. I'll help identify the appropriate category and find a solution for you:",
        timestamp: new Date().toISOString()
      }]);
      return;
    }
    
    // Special case: "Other Issue" within a category - opens free text with category context
    if (button.action === 'category_other') {
      setShowOtherInput(true);
      setCurrentButtons([{
        label: '⬅️ Back to Categories',
        action: 'go_back',
        value: 'back'
      }]);
      
      const userMessage = {
        type: 'user',
        text: `Selected: ${button.label}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, userMessage, {
        type: 'agent',
        text: `Please describe your ${button.category || ''} issue in detail:`,
        timestamp: new Date().toISOString()
      }]);
      
      // Store the category context for the free text submission
      setConversationState(`category_other_${button.category}`);
      return;
    }
    
    // Add user selection as message
    const userMessage = {
      type: 'user',
      text: `Selected: ${button.label}`,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    setLoading(true);
    setCurrentButtons([]);
    
    try {
      const response = await api.post('/api/chat', {
        action: button.action,
        value: button.value,
        session_id: sessionId
      });

      if (response.data.success) {
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
        
        console.log('Button click API Response:', response.data);
        console.log('Buttons received:', response.data.buttons);
        console.log('Buttons have icon?', response.data.buttons?.some(btn => btn.icon));
        
        const agentMessage = {
          type: 'agent',
          text: response.data.response,
          timestamp: new Date().toISOString(),
          ticketId: response.data.ticket_id
        };
        setMessages(prev => [...prev, agentMessage]);
        
        setCurrentButtons(response.data.buttons || []);
        setConversationState(response.data.state || 'end');
        
        // Handle show_text_input flag from backend (for "need more help" and free text modes)
        if (response.data.show_text_input) {
          setShowOtherInput(true);
        }
        
        // If state is 'end', show restart option
        if (response.data.state === 'end' && !response.data.buttons?.length) {
          setCurrentButtons([{
            label: '🔄 Start New Conversation',
            action: 'restart',
            value: 'restart'
          }]);
        }
      } else {
        setMessages(prev => [...prev, {
          type: 'error',
          text: response.data.error || 'Something went wrong. Please try again.',
          timestamp: new Date().toISOString()
        }]);
        setCurrentButtons([{
          label: '🔄 Start Over',
          action: 'restart',
          value: 'restart'
        }]);
      }
    } catch (error) {
      console.error('Error handling button click:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        text: 'Failed to process your selection. Please try again.',
        timestamp: new Date().toISOString()
      }]);
      setCurrentButtons([{
        label: '🔄 Start Over',
        action: 'restart',
        value: 'restart'
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle free text submission (for "Other Issues")
  const handleFreeTextSubmit = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = {
      type: 'user',
      text: inputMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    const messageText = inputMessage;
    setInputMessage('');
    setLoading(true);
    setShowOtherInput(false);
    
    // Check if we have category context (from "Other Issue" within a category)
    let categoryContext = null;
    if (conversationState && conversationState.startsWith('category_other_')) {
      categoryContext = conversationState.replace('category_other_', '');
    }
    
    try {
      const response = await api.post('/api/chat', {
        action: 'free_text',
        message: messageText,
        category: categoryContext,  // Pass category context if available
        session_id: sessionId
      });

      if (response.data.success) {
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
        
        const agentMessage = {
          type: 'agent',
          text: response.data.response,
          timestamp: new Date().toISOString(),
          ticketId: response.data.ticket_id
        };
        setMessages(prev => [...prev, agentMessage]);
        
        setCurrentButtons(response.data.buttons || []);
        setConversationState(response.data.state || 'end');
        
        // Handle show_text_input flag from backend (for follow-up questions)
        if (response.data.show_text_input) {
          setShowOtherInput(true);
        } else {
          setShowOtherInput(false);
        }
        
        // Add restart button if at end
        if (response.data.state === 'end') {
          setCurrentButtons([{
            label: '🔄 Start New Conversation',
            action: 'restart',
            value: 'restart'
          }]);
        }
      }
    } catch (error) {
      console.error('Error submitting free text:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        text: 'Failed to submit your issue. Please try again.',
        timestamp: new Date().toISOString()
      }]);
      setCurrentButtons([{
        label: '🔄 Start Over',
        action: 'restart',
        value: 'restart'
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle restart
  const handleRestart = () => {
    setSessionId(null);
    setCurrentButtons([]);
    setShowOtherInput(false);
    setInputMessage('');
    setConversationState('start');
    startConversation();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleFreeTextSubmit();
    }
  };

  // View user tickets
  const viewMyTickets = async () => {
    try {
      const response = await api.get(`/api/tickets/user/${user.id}`);
      if (response.data.success && response.data.tickets.length > 0) {
        setAllTickets(response.data.tickets);
        setShowAllTickets(true);
      } else {
        alert('You have no tickets yet.');
      }
    } catch (error) {
      console.error('Error fetching tickets:', error);
      alert('Failed to fetch tickets.');
    }
  };

  // Render category buttons in a grid/expandable format
  const renderButtons = () => {
    if (!currentButtons || currentButtons.length === 0) return null;
    
    console.log('renderButtons called with:', currentButtons);
    console.log('isCategories check:', currentButtons.some(btn => btn.icon));
    
    // Don't show separate buttons if we're showing the text input with its own back button
    // (But show action buttons like "Create Ticket Instead")
    if (showOtherInput && currentButtons.every(btn => btn.action === 'go_back')) {
      return null;  // The text input area has its own back button
    }
    
    // Check if these are category buttons (have icons)
    const isCategories = currentButtons.some(btn => btn.icon);
    
    // Check if these are confirmation buttons
    const isConfirmation = currentButtons.some(btn => 
      btn.action === 'confirm_ticket' || btn.action === 'decline_ticket'
    );
    
    // Check if restart button
    const isRestart = currentButtons.some(btn => btn.action === 'restart');
    
    if (isRestart) {
      return (
        <div className="button-container restart-container">
          {currentButtons.map((button, index) => (
            <button
              key={index}
              className="chat-button restart-button"
              onClick={() => handleRestart()}
              disabled={loading}
            >
              {button.label}
            </button>
          ))}
        </div>
      );
    }
    
    if (isConfirmation) {
      return (
        <div className="button-container confirmation-container">
          <div className="confirmation-header">
            <span>⚠️ Would you like to create a support ticket?</span>
          </div>
          <div className="confirmation-buttons">
            {currentButtons.map((button, index) => (
              <button
                key={index}
                className={`chat-button ${button.action === 'confirm_ticket' ? 'confirm-yes' : 'confirm-no'}`}
                onClick={() => handleButtonClick(button)}
                disabled={loading}
              >
                {button.label}
              </button>
            ))}
          </div>
        </div>
      );
    }
    
    if (isCategories) {
      return (
        <div className="button-container category-container">
          <div className="category-header">
            <span>🔍 Select an issue category:</span>
          </div>
          <div className="category-grid">
            {currentButtons.map((button, index) => (
              <button
                key={index}
                className={`chat-button category-button ${button.action === 'other_issues' ? 'other-button' : ''}`}
                onClick={() => handleButtonClick(button)}
                disabled={loading}
              >
                <span className="button-icon">{button.icon || '📋'}</span>
                <span className="button-label">{button.label}</span>
              </button>
            ))}
          </div>
        </div>
      );
    }
    
    // Subcategory buttons - list format (also handles action buttons shown with text input)
    return (
      <div className="button-container subcategory-container">
        {!showOtherInput && (
          <div className="subcategory-header">
            <span>📝 Select your specific issue:</span>
          </div>
        )}
        <div className="subcategory-list">
          {currentButtons.map((button, index) => (
            <button
              key={index}
              className={`chat-button subcategory-button ${button.action === 'go_back' ? 'back-button' : ''} ${button.action === 'category_other' ? 'other-issue-button' : ''} ${button.action === 'confirm_ticket' ? 'ticket-button' : ''}`}
              onClick={() => {
                if (button.action === 'go_back') {
                  setShowOtherInput(false);  // Clear text input when going back
                  handleRestart();
                } else {
                  handleButtonClick(button);
                }
              }}
              disabled={loading}
            >
              {button.action === 'go_back' ? '⬅️ ' : button.action === 'category_other' ? '✏️ ' : button.action === 'confirm_ticket' ? '🎫 ' : '• '}
              {button.label}
            </button>
          ))}
        </div>
      </div>
    );
  };

  // Tickets list modal
  const TicketsModal = () => {
    if (!showAllTickets) return null;
    
    return (
      <div className="modal-overlay" onClick={() => setShowAllTickets(false)}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📋 My Tickets</h3>
            <button className="modal-close" onClick={() => setShowAllTickets(false)}>×</button>
          </div>
          <div className="modal-body">
            {allTickets.length === 0 ? (
              <p className="no-tickets">No tickets found.</p>
            ) : (
              <div className="tickets-list">
                {allTickets.map((ticket, index) => (
                  <div 
                    key={index} 
                    className={`ticket-item status-${ticket.status?.toLowerCase()}`}
                    onClick={() => {
                      setTicketData(ticket);
                      setShowAllTickets(false);
                      setShowTicketPreview(true);
                    }}
                  >
                    <div className="ticket-header">
                      <span className="ticket-id">{ticket.id}</span>
                      <span className={`ticket-status ${ticket.status?.toLowerCase()}`}>
                        {ticket.status}
                      </span>
                    </div>
                    <div className="ticket-subject">{ticket.subject}</div>
                    <div className="ticket-meta">
                      <span className="ticket-category">{ticket.category}</span>
                      <span className="ticket-priority priority-{ticket.priority?.toLowerCase()}">
                        {ticket.priority}
                      </span>
                      <span className="ticket-date">
                        {new Date(ticket.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-container">
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <h3>🎫 IT Support</h3>
          <p className="user-greeting">Hello, {user.username}!</p>
        </div>
        
        <div className="sidebar-actions">
          <button className="sidebar-btn" onClick={viewMyTickets}>
            📋 My Tickets
          </button>
          <button className="sidebar-btn" onClick={handleRestart}>
            🔄 New Conversation
          </button>
        </div>
        
        <div className="sidebar-info">
          <h4>How it works</h4>
          <ol>
            <li>Select issue category</li>
            <li>Choose specific problem</li>
            <li>Get instant solution</li>
            <li>Or create a ticket</li>
          </ol>
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-header">
          <div className="header-info">
            <span className="header-title">🤖 IT Support Assistant</span>
            <span className="header-status">● Online</span>
          </div>
        </div>
        
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {message.type === 'user' ? '👤 You' : '🤖 Assistant'}
                  </span>
                  {message.ticketId && (
                    <span className="ticket-badge">
                      🎫 {message.ticketId}
                    </span>
                  )}
                </div>
                <div className="message-text">
                  {(message.text || '').split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
                <div className="message-time">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message agent">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Button options */}
        {!loading && renderButtons()}
        
        {/* Free text input for "Other Issues" */}
        {showOtherInput && (
          <div className="other-input-container">
            <div className="other-input-header">
              <span>📝 Describe your issue:</span>
            </div>
            <div className="other-input-form">
              <textarea
                className="other-input"
                placeholder="Please describe your IT issue in detail..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
                rows="4"
                autoFocus
              />
              <div className="other-input-actions">
                <button
                  className="cancel-btn"
                  onClick={() => {
                    setShowOtherInput(false);
                    setInputMessage('');
                    handleRestart();
                  }}
                  disabled={loading}
                >
                  ← Back
                </button>
                <button
                  className="submit-btn"
                  onClick={handleFreeTextSubmit}
                  disabled={loading || !inputMessage.trim()}
                >
                  Submit →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tickets Modal */}
      <TicketsModal />

      {/* Single Ticket Preview */}
      {showTicketPreview && ticketData && (
        <TicketPreview
          ticket={ticketData}
          onClose={() => setShowTicketPreview(false)}
        />
      )}
    </div>
  );
}

export default Chat;