"""
Feedback Handler - Handles solution feedback and end-of-flow ratings
Supports per-solution Yes/No feedback and 1-5 star ratings with text comments
"""

# Feedback flow states
STATE_SOLUTION_FEEDBACK = 'solution_feedback'
STATE_END_RATING = 'end_rating'
STATE_END_FEEDBACK_TEXT = 'end_feedback_text'
STATE_FEEDBACK_COMPLETE = 'feedback_complete'


def format_solutions_with_feedback(bot_solution):
    """
    Format solutions as numbered points and return structure for feedback buttons.
    Returns: (formatted_text, solutions_list)
    """
    if not bot_solution:
        return "", []
    
    # Split solutions by common delimiters
    lines = bot_solution.strip().split('\n')
    solutions = []
    current_solution = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_solution:
                solutions.append(' '.join(current_solution))
                current_solution = []
            continue
        
        # Check if it's a numbered point or bullet
        if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            if current_solution:
                solutions.append(' '.join(current_solution))
                current_solution = []
            # Remove bullet/number prefix
            clean_line = line.lstrip('•-*0123456789. ').strip()
            if clean_line:
                current_solution.append(clean_line)
        else:
            current_solution.append(line)
    
    if current_solution:
        solutions.append(' '.join(current_solution))
    
    # If no structured solutions found, treat entire text as one solution
    if not solutions:
        solutions = [bot_solution.strip()]
    
    # Filter out filler/intro/outro sentences that aren't actionable solution steps
    filler_patterns = [
        "here's how to resolve",
        "here is how to resolve",
        "here are some solutions",
        "here's how to fix",
        "try the following",
        "follow these steps",
        "if this doesn't resolve your issue",
        "if this doesn't work",
        "if the issue persists",
        "if none of the above",
        "i can create a support ticket",
        "i can create a ticket",
        "let me create a support ticket",
        "create a support ticket for you",
        "you can create a ticket",
        "contact support for further",
        "please let me know if",
        "hope this helps",
        "i hope this resolves",
        "let me know if you need",
    ]
    
    filtered_solutions = []
    for sol in solutions:
        sol_lower = sol.lower().strip()
        # Skip empty or very short solutions
        if len(sol_lower) < 5:
            continue
        # Skip if it matches any filler pattern
        is_filler = any(pattern in sol_lower for pattern in filler_patterns)
        if not is_filler:
            filtered_solutions.append(sol)
    
    # Use filtered list, but fall back to original if all were filtered
    if filtered_solutions:
        solutions = filtered_solutions
    
    # Format as numbered list
    formatted_lines = []
    for i, sol in enumerate(solutions, 1):
        formatted_lines.append(f"**{i}.** {sol}")
    
    formatted_text = '\n\n'.join(formatted_lines)
    
    return formatted_text, solutions


def get_solution_feedback_buttons(solution_index, total_solutions):
    """Get Step 1 feedback buttons: Tried / Not Tried"""
    return {
        "solution_index": solution_index,
        "total_solutions": total_solutions,
        "step": 1,
        "buttons": [
            {
                'id': f'tried_{solution_index}',
                'label': '✅ Tried',
                'action': 'solution_helpful',
                'value': f'{solution_index}:tried'
            },
            {
                'id': f'not_tried_{solution_index}',
                'label': '⏭️ Not Tried',
                'action': 'solution_helpful',
                'value': f'{solution_index}:not_tried'
            }
        ]
    }


def get_solution_helpfulness_buttons(solution_index, total_solutions):
    """Get Step 2 feedback buttons: Helpful / Not Helpful (shown after 'Tried')"""
    return {
        "solution_index": solution_index,
        "total_solutions": total_solutions,
        "step": 2,
        "buttons": [
            {
                'id': f'helpful_{solution_index}',
                'label': '👍 Helpful',
                'action': 'solution_helpful',
                'value': f'{solution_index}:helpful'
            },
            {
                'id': f'not_helpful_{solution_index}',
                'label': '👎 Not Helpful',
                'action': 'solution_helpful',
                'value': f'{solution_index}:not_helpful'
            }
        ]
    }


def build_solution_with_feedback_ui(issue_text, bot_solution):
    """Build the solution display with per-solution feedback UI"""
    formatted_solutions, solutions_list = format_solutions_with_feedback(bot_solution)
    
    if not solutions_list:
        return {
            "formatted_text": bot_solution,
            "solutions": [],
            "show_solution_feedback": False
        }
    
    # Build feedback UI structure
    solution_feedback_ui = []
    for i, sol in enumerate(solutions_list):
        solution_feedback_ui.append({
            "index": i + 1,
            "text": sol,
            "feedback_buttons": get_solution_feedback_buttons(i + 1, len(solutions_list))
        })
    
    return {
        "formatted_text": formatted_solutions,
        "solutions": solution_feedback_ui,
        "solutions_count": len(solutions_list),
        "show_solution_feedback": True
    }


def handle_solution_helpful(value, conversation_state):
    """Handle per-solution feedback (tried/not_tried/helpful/not_helpful)"""
    parts = value.split(':')
    if len(parts) != 2:
        return None
    
    solution_index = int(parts[0])
    feedback_type = parts[1]  # 'tried', 'not_tried', 'helpful', 'not_helpful'
    
    # Store feedback in conversation state
    if 'solution_feedback' not in conversation_state:
        conversation_state['solution_feedback'] = {}
    
    conversation_state['solution_feedback'][solution_index] = feedback_type
    
    return {
        "success": True,
        "feedback_recorded": True,
        "solution_index": solution_index,
        "feedback_type": feedback_type
    }


def get_star_rating_ui():
    """Get the 1-5 star rating UI buttons"""
    return {
        "type": "star_rating",
        "min": 1,
        "max": 5,
        "buttons": [
            {'id': 'star_1', 'label': '⭐', 'action': 'submit_rating', 'value': '1'},
            {'id': 'star_2', 'label': '⭐⭐', 'action': 'submit_rating', 'value': '2'},
            {'id': 'star_3', 'label': '⭐⭐⭐', 'action': 'submit_rating', 'value': '3'},
            {'id': 'star_4', 'label': '⭐⭐⭐⭐', 'action': 'submit_rating', 'value': '4'},
            {'id': 'star_5', 'label': '⭐⭐⭐⭐⭐', 'action': 'submit_rating', 'value': '5'}
        ]
    }


def show_end_rating_prompt(conversation_state):
    """Show the end-of-flow rating prompt"""
    conversation_state['state'] = STATE_END_RATING
    
    return {
        "success": True,
        "response": "📊 **How was your experience?**\n\nPlease rate your interaction:",
        "show_star_rating": True,
        "star_rating": get_star_rating_ui(),
        "buttons": [
            {'id': 'skip', 'label': '⏭️ Skip', 'action': 'skip_rating', 'value': 'skip'}
        ],
        "state": STATE_END_RATING,
        "show_text_input": False
    }


def handle_rating_submit(rating, conversation_state):
    """Handle rating submission"""
    conversation_state['end_rating'] = int(rating)
    conversation_state['state'] = STATE_END_FEEDBACK_TEXT
    
    # Show text feedback prompt
    return {
        "success": True,
        "response": f"⭐ **Rating: {rating}/5** - Thank you!\n\n📝 Would you like to leave any additional comments? (Optional)",
        "buttons": [
            {'id': 'submit', 'label': '✅ Submit', 'action': 'submit_feedback_text', 'value': 'submit'},
            {'id': 'skip', 'label': '⏭️ Skip', 'action': 'skip_feedback_text', 'value': 'skip'}
        ],
        "state": STATE_END_FEEDBACK_TEXT,
        "show_text_input": True
    }


def handle_skip_rating(conversation_state):
    """Handle rating skip"""
    conversation_state['end_rating'] = None
    conversation_state['state'] = STATE_FEEDBACK_COMPLETE
    
    return get_feedback_complete_response(conversation_state)


def handle_feedback_text_submit(text, conversation_state):
    """Handle feedback text submission"""
    conversation_state['feedback_text'] = text
    conversation_state['state'] = STATE_FEEDBACK_COMPLETE
    
    return get_feedback_complete_response(conversation_state)


def handle_skip_feedback_text(conversation_state):
    """Handle feedback text skip"""
    conversation_state['feedback_text'] = None
    conversation_state['state'] = STATE_FEEDBACK_COMPLETE
    
    return get_feedback_complete_response(conversation_state)


def get_feedback_complete_response(conversation_state):
    """Get the feedback complete response"""
    rating = conversation_state.get('end_rating')
    
    if rating:
        thank_you = f"Thank you for your feedback! (⭐ {rating}/5)"
    else:
        thank_you = "Thank you for using IT Support!"
    
    return {
        "success": True,
        "response": f"✅ **{thank_you}**\n\nYour feedback helps us improve.\n\n---\n\nIs there anything else I can help you with?",
        "buttons": [
            {'id': 'new', 'label': '🆕 New Issue', 'action': 'start', 'value': 'new'},
            {'id': 'done', 'label': '✅ I\'m Done', 'action': 'end', 'value': 'done'}
        ],
        "state": STATE_FEEDBACK_COMPLETE,
        "show_text_input": False,
        "feedback_data": {
            "rating": conversation_state.get('end_rating'),
            "feedback_text": conversation_state.get('feedback_text'),
            "solution_feedback": conversation_state.get('solution_feedback', {}),
            "solutions_shown": conversation_state.get('solutions_list', []),
            "flow_type": conversation_state.get('ticket_type', 'incident').lower() if conversation_state.get('ticket_type') else 'incident',
            "ready_to_save": True
        }
    }


def collect_all_feedback(conversation_state, ticket_id=None, session_id=None):
    """Collect all feedback data for database storage"""
    return {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "flow_type": conversation_state.get('ticket_type', 'incident').lower(),
        "rating": conversation_state.get('end_rating'),
        "feedback_text": conversation_state.get('feedback_text'),
        "solution_feedback": conversation_state.get('solution_feedback', {}),
        "solutions_shown": conversation_state.get('solutions_list', [])
    }
