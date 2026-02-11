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

  // Image upload state - Multiple images support
  const [selectedImages, setSelectedImages] = useState([]);  // Array of {file, preview}
  const [uploadingImages, setUploadingImages] = useState(false);
  const [uploadedImageUrls, setUploadedImageUrls] = useState([]);  // Array of URLs
  const [showAttachmentUpload, setShowAttachmentUpload] = useState(false);  // Only show at confirmation
  const fileInputRef = useRef(null);

  // Checkbox selection state (for multi-select options like Internet Access)
  const [checkboxSelections, setCheckboxSelections] = useState([]);
  const [showCheckboxes, setShowCheckboxes] = useState(false);
  const [checkboxOptions, setCheckboxOptions] = useState([]);

  // Star rating and feedback state
  const [showStarRating, setShowStarRating] = useState(false);
  const [selectedRating, setSelectedRating] = useState(0);
  const [hoveredStar, setHoveredStar] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [showFeedbackText, setShowFeedbackText] = useState(false);

  // Per-solution feedback state
  const [solutionsWithFeedback, setSolutionsWithFeedback] = useState([]);
  const [solutionFeedback, setSolutionFeedback] = useState({}); // { solutionIndex: 'yes'|'no' }

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
    // Handle restart action
    if (button.action === 'restart' || button.action === 'start') {
      handleRestart();
      return;
    }

    // Handle other_issue action (opens free text input)
    if (button.action === 'other_issue') {
      setShowOtherInput(true);
      setCurrentButtons([{
        label: '⬅️ Back',
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
        text: "📝 **Describe Your Issue**\n\nPlease describe your issue in detail so we can help you better:",
        timestamp: new Date().toISOString()
      }]);
      setConversationState('awaiting_free_text');
      return;
    }

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
      // Check if this is a ticket confirmation action - upload images first
      let imageUrls = [];
      if (button.action === 'confirm_ticket' && selectedImages.length > 0) {
        imageUrls = await uploadAllImages();
      }

      // Include message text for feedback text submission
      const requestData = {
        action: button.action,
        value: button.value,
        session_id: sessionId,
        attachment_urls: imageUrls.length > 0 ? imageUrls : undefined
      };

      // If submitting feedback text, include the typed message
      if (button.action === 'submit_feedback_text' && inputMessage.trim()) {
        requestData.message = inputMessage.trim();
        setInputMessage('');
        setShowOtherInput(false);
      }

      // If confirming internet access, include checkbox selections
      if (button.action === 'confirm_internet_access') {
        requestData.selected_options = checkboxSelections;
        setShowCheckboxes(false);
      }

      const response = await api.post('/api/chat', requestData);

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

        // Handle star rating flag from backend
        if (response.data.show_star_rating) {
          setShowStarRating(true);
          setSelectedRating(0);
        } else {
          setShowStarRating(false);
        }

        // Handle feedback text input flag
        if (response.data.state === 'end_feedback_text') {
          setShowFeedbackText(true);
        } else {
          setShowFeedbackText(false);
        }

        // Handle per-solution feedback data from backend
        if (response.data.solutions_with_feedback && response.data.solutions_with_feedback.length > 0) {
          setSolutionsWithFeedback(response.data.solutions_with_feedback);
          setSolutionFeedback({}); // Reset feedback for new solutions
        } else {
          setSolutionsWithFeedback([]);
        }

        // Handle checkbox options from backend (e.g., Internet Access multi-select)
        if (response.data.show_checkboxes && response.data.checkboxes) {
          setShowCheckboxes(true);
          setCheckboxOptions(response.data.checkboxes);
          setCheckboxSelections([]);
        } else {
          setShowCheckboxes(false);
        }

        // Show attachment upload option when at ticket confirmation state
        const isTicketConfirmation = response.data.buttons?.some(btn =>
          btn.action === 'confirm_ticket'
        );
        setShowAttachmentUpload(isTicketConfirmation);

        // Clear images after successful ticket creation
        if (response.data.ticket_id) {
          clearImages();
        }

        // Handle show_text_input flag from backend (for "need more help" and free text modes)
        if (response.data.show_text_input) {
          setShowOtherInput(true);
        } else {
          setShowOtherInput(false);
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

        // Handle star rating display
        if (response.data.show_star_rating) {
          setShowStarRating(true);
          setSelectedRating(0);
        } else {
          setShowStarRating(false);
        }

        // Show attachment upload option when at ticket confirmation state
        const isTicketConfirmation = response.data.buttons?.some(btn =>
          btn.action === 'confirm_ticket'
        );
        setShowAttachmentUpload(isTicketConfirmation);

        // Handle per-solution feedback data from backend (agent responses)
        if (response.data.solutions_with_feedback && response.data.solutions_with_feedback.length > 0) {
          setSolutionsWithFeedback(response.data.solutions_with_feedback);
          setSolutionFeedback({}); // Reset feedback for new solutions
        } else {
          setSolutionsWithFeedback([]);
        }

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

  // Handle multiple image selection
  const handleImageSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    const maxImages = 5; // Maximum 5 images

    const currentCount = selectedImages.length;
    const remainingSlots = maxImages - currentCount;

    if (remainingSlots <= 0) {
      alert(`Maximum ${maxImages} images allowed per ticket.`);
      return;
    }

    const validFiles = [];
    for (const file of files.slice(0, remainingSlots)) {
      if (!allowedTypes.includes(file.type)) {
        alert(`Invalid file type: ${file.name}. Please select JPEG, PNG, GIF, or WebP images.`);
        continue;
      }
      if (file.size > maxSize) {
        alert(`File too large: ${file.name}. Maximum size is 5MB.`);
        continue;
      }
      validFiles.push(file);
    }

    // Create previews for valid files
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImages(prev => [...prev, { file, preview: reader.result }]);
      };
      reader.readAsDataURL(file);
    });

    // Clear file input for next selection
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Upload all selected images
  const uploadAllImages = async () => {
    if (selectedImages.length === 0) return [];

    setUploadingImages(true);
    const uploadedUrls = [];

    try {
      for (const { file } of selectedImages) {
        const formData = new FormData();
        formData.append('image', file);

        const response = await api.post('/api/upload/image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.success) {
          uploadedUrls.push(response.data.url);
        }
      }

      setUploadedImageUrls(uploadedUrls);
      return uploadedUrls;
    } catch (error) {
      console.error('Error uploading images:', error);
      alert('Failed to upload some images. Please try again.');
      return uploadedUrls;
    } finally {
      setUploadingImages(false);
    }
  };

  // Remove a selected image
  const removeImage = (index) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
  };

  // Clear all selected images
  const clearImages = () => {
    setSelectedImages([]);
    setUploadedImageUrls([]);
    setShowAttachmentUpload(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle restart
  const handleRestart = () => {
    setSessionId(null);
    setCurrentButtons([]);
    setShowOtherInput(false);
    setInputMessage('');
    setConversationState('start');
    setShowStarRating(false);
    setSelectedRating(0);
    setShowFeedbackText(false);
    setFeedbackText('');
    setSolutionsWithFeedback([]);
    setSolutionFeedback({});
    clearImages();  // Clear any selected images
    startConversation();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleFreeTextSubmit();
    }
  };

  // Handle per-solution feedback (Yes/No for each solution step)
  const handleSolutionFeedback = async (solutionIndex, feedback) => {
    setSolutionFeedback(prev => ({
      ...prev,
      [solutionIndex]: feedback
    }));

    // Send feedback to backend
    try {
      await api.post('/api/chat', {
        action: 'solution_helpful',
        value: `${solutionIndex}:${feedback}`,
        session_id: sessionId
      });
    } catch (err) {
      console.error('Error sending solution feedback:', err);
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

  // Render per-solution feedback UI (Two-step: Tried/Not Tried → Helpful/Not Helpful)
  const renderSolutionFeedback = () => {
    if (!solutionsWithFeedback || solutionsWithFeedback.length === 0) return null;

    return (
      <div className="solution-feedback-container">
        <div className="solution-feedback-header">
          <span>📋 Rate each solution step:</span>
        </div>
        <div className="solution-feedback-list">
          {solutionsWithFeedback.map((solution, index) => {
            const feedback = solutionFeedback[solution.index];
            const isStep2 = feedback === 'tried'; // Show step 2 after clicking Tried
            const isDone = feedback === 'not_tried' || feedback === 'helpful' || feedback === 'not_helpful';

            return (
              <div key={index} className={`solution-feedback-item ${isDone ? 'done' : ''}`}>
                <div className="solution-text">
                  <strong>{solution.index}.</strong> {solution.text}
                </div>
                <div className="solution-feedback-buttons">
                  {/* Step 1: Tried / Not Tried */}
                  {!feedback && (
                    <>
                      <button
                        className="feedback-btn tried-btn"
                        onClick={() => handleSolutionFeedback(solution.index, 'tried')}
                      >
                        ✅ Tried
                      </button>
                      <button
                        className="feedback-btn not-tried-btn"
                        onClick={() => handleSolutionFeedback(solution.index, 'not_tried')}
                      >
                        ⏭️ Not Tried
                      </button>
                    </>
                  )}

                  {/* Step 2: Helpful / Not Helpful (after clicking Tried) */}
                  {isStep2 && (
                    <>
                      <button
                        className="feedback-btn helpful-btn"
                        onClick={() => handleSolutionFeedback(solution.index, 'helpful')}
                      >
                        👍 Helpful
                      </button>
                      <button
                        className="feedback-btn not-helpful-btn"
                        onClick={() => handleSolutionFeedback(solution.index, 'not_helpful')}
                      >
                        👎 Not Helpful
                      </button>
                    </>
                  )}

                  {/* Final state badges */}
                  {feedback === 'not_tried' && (
                    <span className="feedback-badge not-tried">⏭️ Not Tried</span>
                  )}
                  {feedback === 'helpful' && (
                    <span className="feedback-badge helpful">👍 Helpful</span>
                  )}
                  {feedback === 'not_helpful' && (
                    <span className="feedback-badge not-helpful">👎 Not Helpful</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Render category buttons in a grid/expandable format
  const renderButtons = () => {
    if (!currentButtons || currentButtons.length === 0) return null;

    console.log('renderButtons called with:', currentButtons);

    // Don't show separate buttons if we're showing the text input with its own back button
    // (But show action buttons like "Create Ticket Instead")
    if (showOtherInput && currentButtons.every(btn => btn.action === 'go_back')) {
      return null;  // The text input area has its own back button
    }

    // Star rating display - Traditional star rating with emotion emojis
    const ratingEmojis = { 1: '😞', 2: '😕', 3: '😐', 4: '😊', 5: '🤩' };
    const ratingLabels = { 1: 'Terrible', 2: 'Poor', 3: 'Average', 4: 'Good', 5: 'Excellent' };

    if (showStarRating) {
      const otherButtons = currentButtons.filter(btn => btn.action !== 'submit_rating');
      const activeRating = hoveredStar || selectedRating;

      return (
        <div className="button-container star-rating-container">
          <div className="star-rating-header">
            <span>⭐ Rate your experience:</span>
          </div>
          <div className="star-rating-emoji-area">
            {activeRating > 0 ? (
              <div className="star-rating-emoji" key={activeRating}>
                <span className="rating-emoji">{ratingEmojis[activeRating]}</span>
                <span className={`rating-label-text rating-${activeRating}`}>{ratingLabels[activeRating]}</span>
              </div>
            ) : (
              <div className="star-rating-emoji">
                <span className="rating-emoji" style={{ opacity: 0.3 }}>🌟</span>
                <span className="rating-label-text" style={{ color: '#a0aec0' }}>Select a rating</span>
              </div>
            )}
          </div>
          <div className="star-rating-stars">
            {[1, 2, 3, 4, 5].map((star) => (
              <span
                key={star}
                className={`star-icon ${selectedRating >= star ? 'filled' : 'empty'} ${hoveredStar >= star ? 'hover' : ''}`}
                onClick={() => {
                  setSelectedRating(star);
                  setShowStarRating(false);
                  setHoveredStar(0);
                  handleButtonClick({ action: 'submit_rating', value: String(star), label: `${ratingEmojis[star]} ${'⭐'.repeat(star)}` });
                }}
                onMouseEnter={() => setHoveredStar(star)}
                onMouseLeave={() => setHoveredStar(0)}
                role="button"
                tabIndex={0}
                title={`${star} star${star > 1 ? 's' : ''} - ${ratingEmojis[star]} ${ratingLabels[star]}`}
              >
                ★
              </span>
            ))}
          </div>
          {selectedRating > 0 && (
            <div className="star-rating-label">{ratingEmojis[selectedRating]} {selectedRating} of 5 stars - {ratingLabels[selectedRating]}</div>
          )}
          {otherButtons.length > 0 && (
            <div className="star-rating-skip">
              {otherButtons.map((button, index) => (
                <button
                  key={index}
                  className="chat-button skip-button"
                  onClick={() => {
                    setShowStarRating(false);
                    handleButtonClick(button);
                  }}
                  disabled={loading}
                >
                  {button.label}
                </button>
              ))}
            </div>
          )}
        </div>
      );
    }

    // Check if these are ticket type buttons (Incident/Request)
    const isTicketType = currentButtons.some(btn => btn.action === 'select_ticket_type');

    // Check if these are smart category buttons
    const isSmartCategory = currentButtons.some(btn => btn.action === 'select_smart_category');

    // Check if these are regular category buttons (Hardware & Connectivity, etc.)
    const isCategory = currentButtons.some(btn => btn.action === 'select_category');

    // Check if these are type buttons
    const isType = currentButtons.some(btn => btn.action === 'select_type');

    // Check if these are item buttons
    const isItem = currentButtons.some(btn => btn.action === 'select_item');

    // Check if these are issue buttons
    const isIssue = currentButtons.some(btn => btn.action === 'select_issue');

    // Check if these are solution response buttons
    const isSolutionResponse = currentButtons.some(btn =>
      btn.action === 'solution_resolved' || btn.action === 'solution_not_resolved'
    );

    // Check if these are confirmation buttons
    const isConfirmation = currentButtons.some(btn =>
      btn.action === 'confirm_ticket' || btn.action === 'decline_ticket' ||
      btn.action === 'preview_ticket'
    );

    // Check if restart button
    const isRestart = currentButtons.some(btn => btn.action === 'restart' || btn.action === 'start');

    // Ticket type selection (Incident/Request)
    if (isTicketType) {
      return (
        <div className="button-container category-container">
          <div className="category-header">
            <span> How can I help you today?</span>
          </div>
          <div className="category-grid ticket-type-grid">
            {currentButtons.map((button, index) => (
              <button
                key={index}
                className={`chat-button category-button ticket-type-button ${button.value === 'Incident' ? 'incident-btn' : 'request-btn'}`}
                onClick={() => handleButtonClick(button)}
                disabled={loading}
              >
                <span className="button-icon">{button.value === 'Incident' ? '🔧' : '📝'}</span>
                <span className="button-label">{button.label}</span>
              </button>
            ))}
          </div>
        </div>
      );
    }

    // Smart category selection
    if (isSmartCategory) {
      const mainButtons = currentButtons.filter(btn => btn.action !== 'start' && btn.action !== 'go_back');
      const backButton = currentButtons.find(btn => btn.action === 'start' || btn.action === 'go_back');

      return (
        <div className="button-container category-container">
          <div className="category-header">
            <span> Select an issue category:</span>
          </div>
          <div className="category-grid smart-category-grid">
            {mainButtons.map((button, index) => (
              <button
                key={index}
                className="chat-button category-button smart-category-button"
                onClick={() => handleButtonClick(button)}
                disabled={loading}
              >
                <span className="button-icon">{button.icon || '📁'}</span>
                <span className="button-label">{button.value || button.label}</span>
              </button>
            ))}
          </div>
          {backButton && (
            <div className="back-button-container">
              <button
                className="chat-button back-button"
                onClick={() => handleButtonClick(backButton)}
                disabled={loading}
              >
                {backButton.label}
              </button>
            </div>
          )}
        </div>
      );
    }

    // Solution response buttons - show immediately alongside solution feedback
    if (isSolutionResponse) {
      return (
        <div className="button-container solution-response-container">
          <div className="confirmation-buttons solution-buttons">
            {currentButtons.map((button, index) => (
              <button
                key={index}
                className={`chat-button ${button.action === 'solution_resolved' ? 'confirm-yes' : button.action === 'solution_not_resolved' ? 'confirm-no' : 'neutral-btn'}`}
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

    if (isRestart && currentButtons.length === 1) {
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
      const mainButtons = currentButtons.filter(btn => btn.action !== 'go_back');
      const backButton = currentButtons.find(btn => btn.action === 'go_back');

      return (
        <div className="button-container confirmation-container">
          <div className="confirmation-buttons">
            {mainButtons.map((button, index) => (
              <button
                key={index}
                className={`chat-button ${button.action === 'confirm_ticket' || button.action === 'preview_ticket' ? 'confirm-yes' : 'confirm-no'}`}
                onClick={() => handleButtonClick(button)}
                disabled={loading}
              >
                {button.label}
              </button>
            ))}
          </div>
          {backButton && (
            <div className="back-button-container">
              <button
                className="chat-button back-button"
                onClick={() => handleButtonClick(backButton)}
                disabled={loading}
              >
                {backButton.label}
              </button>
            </div>
          )}
        </div>
      );
    }

    // Issue list buttons - show as a list with "Other Issue" option
    if (isIssue) {
      const issueButtons = currentButtons.filter(btn => btn.action === 'select_issue');
      const otherButton = currentButtons.find(btn => btn.action === 'other_issue');
      const backButton = currentButtons.find(btn => btn.action === 'go_back');

      return (
        <div className="button-container subcategory-container issue-container">
          <div className="subcategory-header">
            <span> Select your issue:</span>
          </div>
          <div className="subcategory-list issue-list">
            {issueButtons.map((button, index) => (
              <button
                key={index}
                className="chat-button subcategory-button issue-button"
                onClick={() => handleButtonClick(button)}
                disabled={loading}
              >
                • {button.label}
              </button>
            ))}
            {otherButton && (
              <button
                className="chat-button subcategory-button other-issue-button"
                onClick={() => handleButtonClick(otherButton)}
                disabled={loading}
              >
                 {otherButton.label}
              </button>
            )}
          </div>
          {backButton && (
            <div className="back-button-container">
              <button
                className="chat-button back-button"
                onClick={() => handleButtonClick(backButton)}
                disabled={loading}
              >
                {backButton.label}
              </button>
            </div>
          )}
        </div>
      );
    }

    // Default - subcategory/navigation list format
    const mainButtons = currentButtons.filter(btn => btn.action !== 'go_back' && btn.action !== 'start');
    const backButton = currentButtons.find(btn => btn.action === 'go_back' || btn.action === 'start');

    return (
      <div className="button-container subcategory-container">
        {!showOtherInput && mainButtons.length > 0 && (
          <div className="subcategory-header">
            <span> Please select:</span>
          </div>
        )}
        <div className="subcategory-list">
          {mainButtons.map((button, index) => (
            <button
              key={index}
              className={`chat-button subcategory-button ${button.action === 'other_issue' ? 'other-issue-button' : ''} ${button.action === 'confirm_ticket' || button.action === 'preview_ticket' ? 'ticket-button' : ''}`}
              onClick={() => handleButtonClick(button)}
              disabled={loading}
            >
              {button.action === 'other_issue' ? '✏️ ' : button.action === 'confirm_ticket' || button.action === 'preview_ticket' ? '🎫 ' : '• '}
              {button.label}
            </button>
          ))}
        </div>
        {backButton && (
          <div className="back-button-container">
            <button
              className="chat-button back-button"
              onClick={() => handleButtonClick(backButton)}
              disabled={loading}
            >
              {backButton.label}
            </button>
          </div>
        )}
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
            <h3> My Tickets</h3>
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
                      {ticket.technician_name && (
                        <span className="ticket-technician" style={{ color: '#2e7d32', fontSize: '12px' }}>
                          👨‍💻 {ticket.technician_name}
                        </span>
                      )}
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
          <h3> Flexi5</h3>
          <p className="user-greeting">Hello, {user.username}!</p>
        </div>

        <div className="sidebar-actions">
          <button className="sidebar-btn" onClick={viewMyTickets}>
             My Tickets
          </button>
          <button className="sidebar-btn" onClick={handleRestart}>
             New Conversation
          </button>
        </div>

        <div className="sidebar-info">
          <h4>How it works</h4>
          <ol>
            <li>Select Incident or Request</li>
            <li>Choose issue category</li>
            <li>Select specific problem</li>
            <li>Get instant solution</li>
            <li>Or create a ticket</li>
          </ol>
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-header">
          <div className="header-info">
            <span className="header-title"> Flexi5</span>
            <span className="header-status">● Online</span>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((message, index) => (
            <React.Fragment key={index}>
              <div className={`message ${message.type}`}>
                <div className="message-content">
                  <div className="message-header">
                    <span className="message-sender">
                      {message.type === 'user' ? '👤 You' : ' Assistant'}
                    </span>
                    {message.ticketId && (
                      <span className="ticket-badge">
                        🎫 {message.ticketId}
                      </span>
                    )}
                  </div>
                  <div className="message-text">
                    {(message.text || '').split('\n').map((line, i) => (
                      <p key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                    ))}
                  </div>
                  {/* Show attached image if present */}
                  {message.image && (
                    <div className="message-image">
                      <img src={message.image} alt="Attached" />
                    </div>
                  )}
                  <div className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
              {/* Render buttons immediately after the last agent message */}
              {message.type === 'agent' && index === messages.length - 1 && !loading && (
                <div className="inline-buttons-wrapper">
                  {renderSolutionFeedback()}
                  {renderButtons()}
                </div>
              )}
            </React.Fragment>
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

        {/* Free text input for "Other Issues" */}
        {showOtherInput && (
          <div className="other-input-container">
            <div className="other-input-header">
              <span>{showFeedbackText ? ' Share your feedback:' : ' Describe your issue:'}</span>
            </div>
            <div className="other-input-form">
              <textarea
                className="other-input"
                placeholder={showFeedbackText ? "Share your thoughts or suggestions..." : "Please describe your IT issue in detail..."}
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

        {/* Checkbox Selection (Multi-select for Internet Access etc.) */}
        {showCheckboxes && checkboxOptions.length > 0 && (
          <div className="checkbox-selection-container">
            <div className="checkbox-header">
              <span>☑️ Select all that apply:</span>
            </div>
            <div className="checkbox-list">
              {checkboxOptions.map((option, index) => (
                <label key={index} className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={checkboxSelections.includes(option.value)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setCheckboxSelections(prev => [...prev, option.value]);
                      } else {
                        setCheckboxSelections(prev => prev.filter(v => v !== option.value));
                      }
                    }}
                    disabled={loading}
                  />
                  <span className="checkbox-label">{option.label || option.value}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Attachment Upload Section - Only shown at ticket confirmation */}
        {showAttachmentUpload && (
          <div className="attachment-upload-container">
            <div className="attachment-header">
              <span>📎 Attach Screenshots (Optional)</span>
              <span className="attachment-hint">Max 5 images, 5MB each</span>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/jpeg,image/png,image/gif,image/webp"
              multiple
              style={{ display: 'none' }}
              disabled={loading || uploadingImages}
            />

            <div className="attachment-content">
              {selectedImages.length > 0 && (
                <div className="selected-images-grid">
                  {selectedImages.map((img, index) => (
                    <div key={index} className="selected-image-item">
                      <img src={img.preview} alt={`Attachment ${index + 1}`} />
                      <button
                        className="remove-image-btn"
                        onClick={() => removeImage(index)}
                        disabled={loading || uploadingImages}
                        title="Remove"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {selectedImages.length < 5 && (
                <button
                  className="add-image-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading || uploadingImages}
                >
                  + Add Image{selectedImages.length > 0 ? ` (${5 - selectedImages.length} left)` : 's'}
                </button>
              )}

              {uploadingImages && (
                <div className="upload-progress">
                  <span className="upload-spinner"></span>
                  <span>Uploading images...</span>
                </div>
              )}
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