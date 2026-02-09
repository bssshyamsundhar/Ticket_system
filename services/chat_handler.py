"""
Chat Handler - Handles the button-based navigation flow for ticket creation
Flow: Incident/Request → Smart Category → Category → Type → Item → Issue → Solution → Ticket
Enhanced with Request ticket flow and Feedback system
"""
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional
from services.ticket_data_service import ticket_data_service
from services import request_flow_handler as request_handler
from services import feedback_handler

logger = logging.getLogger(__name__)


def get_or_create_event_loop():
    """Get existing event loop or create a new one"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def run_async(coro):
    """Run an async coroutine from sync code"""
    loop = get_or_create_event_loop()
    return loop.run_until_complete(coro)


class ChatHandler:
    """Handles chat navigation and state management"""
    
    # Conversation state keys
    STATE_INITIAL = 'initial'
    STATE_AWAITING_TICKET_TYPE = 'awaiting_ticket_type'
    STATE_AWAITING_SMART_CATEGORY = 'awaiting_smart_category'
    STATE_AWAITING_CATEGORY = 'awaiting_category'
    STATE_AWAITING_TYPE = 'awaiting_type'
    STATE_AWAITING_ITEM = 'awaiting_item'
    STATE_AWAITING_ISSUE = 'awaiting_issue'
    STATE_SHOWING_SOLUTION = 'showing_solution'
    STATE_AWAITING_TICKET_CONFIRMATION = 'awaiting_ticket_confirmation'
    STATE_AWAITING_FREE_TEXT = 'awaiting_free_text'
    STATE_TICKET_CREATED = 'ticket_created'
    STATE_COMPLETED = 'completed'
    STATE_REQUEST_PLACEHOLDER = 'request_placeholder'
    # Request flow states
    STATE_REQUEST_CATEGORY = 'request_category'
    STATE_REQUEST_FLOW = 'request_flow'
    STATE_MANAGER_APPROVAL = 'manager_approval'
    # Feedback flow states
    STATE_SOLUTION_FEEDBACK = 'solution_feedback'
    STATE_END_RATING = 'end_rating'
    STATE_END_FEEDBACK_TEXT = 'end_feedback_text'
    STATE_FEEDBACK_COMPLETE = 'feedback_complete'
    
    def __init__(self):
        self.data_service = ticket_data_service
    
    def create_initial_state(self) -> Dict:
        """Create a new conversation state"""
        return {
            'state': self.STATE_INITIAL,
            'ticket_type': None,          # 'Incident' or 'Request'
            'smart_category': None,        # e.g., 'Network Connection Issues'
            'category': None,              # e.g., 'Hardware & Connectivity'
            'type': None,                  # e.g., 'Network'
            'item': None,                  # e.g., 'Network Port'
            'issue_index': None,           # Index of selected issue
            'issue_text': None,            # The issue description
            'bot_solution': None,          # The solution provided
            'free_text_description': None, # For "Other Issue" free text
            'issue_history': [],           # Conversation history for ticket
            'attachment_urls': [],         # Uploaded attachments
            'navigation_stack': []         # For back navigation
        }
    
    def handle_action(self, action: str, data: Dict, conversation_state: Dict, 
                      user_info: Dict) -> Dict:
        """
        Main handler for all chat actions
        Returns response_data dict with response, buttons, state, etc.
        """
        response_data = {
            "success": True,
            "buttons": [],
            "show_text_input": False,
            "state": conversation_state.get('state', self.STATE_INITIAL)
        }
        
        try:
            # Route to appropriate handler based on action
            if action == 'start' or action == 'restart':
                return self._handle_start(conversation_state, user_info)
            
            elif action == 'select_ticket_type':
                return self._handle_select_ticket_type(data, conversation_state, user_info)
            
            elif action == 'select_smart_category':
                return self._handle_select_smart_category(data, conversation_state)
            
            elif action == 'select_category':
                return self._handle_select_category(data, conversation_state)
            
            elif action == 'select_type':
                return self._handle_select_type(data, conversation_state)
            
            elif action == 'select_item':
                return self._handle_select_item(data, conversation_state)
            
            elif action == 'select_issue':
                return self._handle_select_issue(data, conversation_state)
            
            elif action == 'other_issue':
                return self._handle_other_issue(data, conversation_state)
            
            elif action == 'free_text':
                return self._handle_free_text(data, conversation_state, user_info)
            
            elif action == 'solution_resolved':
                return self._handle_solution_resolved(conversation_state)
            
            elif action == 'solution_not_resolved':
                return self._handle_solution_not_resolved(conversation_state)
            
            elif action == 'agent_continue':
                return self._handle_agent_continue(conversation_state)
            
            elif action == 'preview_ticket':
                return self._handle_preview_ticket(conversation_state, user_info)
            
            elif action == 'confirm_ticket':
                return self._handle_confirm_ticket(data, conversation_state, user_info)
            
            elif action == 'decline_ticket':
                return self._handle_decline_ticket(conversation_state)
            
            elif action == 'go_back':
                return self._handle_go_back(conversation_state)
            
            elif action == 'end':
                return self._handle_end(conversation_state)
            
            # Request flow actions
            elif action == 'select_request_category':
                result = request_handler.handle_request_category(data.get('value'), conversation_state)
                if result:
                    return result
            
            elif action == 'select_hardware_item':
                return request_handler.handle_hardware_item(data.get('value'), conversation_state)
            
            elif action == 'select_hardware_brand':
                return request_handler.handle_hardware_brand(data.get('value'), conversation_state)
            
            elif action == 'select_software_action':
                return request_handler.handle_software_action(data.get('value'), conversation_state)
            
            elif action == 'select_software_item':
                return request_handler.handle_software_item(data.get('value'), conversation_state)
            
            elif action == 'select_access_type':
                result = request_handler.handle_access_type(data.get('value'), conversation_state)
                if result:
                    return result
            
            elif action == 'confirm_internet_access':
                selected = data.get('selected_options', [])
                return request_handler.handle_internet_access_confirm(selected, conversation_state)
            
            elif action == 'select_folder_permission':
                return request_handler.handle_folder_permission(data.get('value'), conversation_state)
            
            elif action == 'submit_request':
                return request_handler.handle_submit_request(conversation_state, user_info)
            
            elif action == 'check_approval':
                return request_handler.handle_check_approval(conversation_state)
            
            # Feedback actions
            elif action == 'solution_helpful':
                result = feedback_handler.handle_solution_helpful(data.get('value'), conversation_state)
                if result:
                    return result
            
            elif action == 'submit_rating':
                return feedback_handler.handle_rating_submit(data.get('value'), conversation_state)
            
            elif action == 'skip_rating':
                return feedback_handler.handle_skip_rating(conversation_state)
            
            elif action == 'submit_feedback_text':
                return feedback_handler.handle_feedback_text_submit(data.get('message', ''), conversation_state)
            
            elif action == 'skip_feedback_text':
                return feedback_handler.handle_skip_feedback_text(conversation_state)
            
            else:
                # Unknown action - show start
                logger.warning(f"Unknown action: {action}")
                return self._handle_start(conversation_state, user_info)
        
        except Exception as e:
            logger.error(f"Error handling action {action}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "response": "Something went wrong. Please try again.",
                "buttons": [
                    {"id": "restart", "label": "🔄 Start Over", "action": "restart", "value": "restart"}
                ],
                "state": self.STATE_INITIAL
            }
    
    def _handle_start(self, conversation_state: Dict, user_info: Dict) -> Dict:
        """Handle start/restart action - show Incident/Request buttons"""
        # Reset state
        conversation_state.clear()
        conversation_state.update(self.create_initial_state())
        conversation_state['state'] = self.STATE_AWAITING_TICKET_TYPE
        
        user_name = user_info.get('name', 'there')
        
        return {
            "success": True,
            "response": f"Hi {user_name}! 👋\n\nI'm **Eve**, your IT Support Assistant. I'm here to help you with any technical issues or requests.\n\nPlease select an option to get started:",
            "buttons": self.data_service.get_ticket_types(),
            "state": self.STATE_AWAITING_TICKET_TYPE,
            "show_text_input": False
        }
    
    def _handle_select_ticket_type(self, data: Dict, conversation_state: Dict, 
                                    user_info: Dict) -> Dict:
        """Handle ticket type selection (Incident or Request)"""
        ticket_type = data.get('value')
        
        if ticket_type == 'Request':
            # Use new Request flow with Hardware/Software/Access categories
            conversation_state['navigation_stack'] = [('ticket_type', 'Request')]
            conversation_state['ticket_type'] = 'Request'
            conversation_state['state'] = self.STATE_REQUEST_CATEGORY
            
            # Get Request categories from request_handler
            request_categories = request_handler.get_request_categories()
            
            # Add back button
            buttons = request_categories + [
                {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
            ]
            
            return {
                "success": True,
                "response": "📝 **Make a Request**\n\nPlease select the type of request:",
                "buttons": buttons,
                "state": self.STATE_REQUEST_CATEGORY,
                "show_text_input": False
            }
        
        elif ticket_type == 'Incident':
            # Save to navigation stack
            conversation_state['navigation_stack'] = [('ticket_type', 'Incident')]
            conversation_state['ticket_type'] = 'Incident'
            conversation_state['state'] = self.STATE_AWAITING_SMART_CATEGORY
            
            # Get smart categories
            smart_categories = self.data_service.get_smart_categories('Incident')
            
            if not smart_categories:
                return {
                    "success": True,
                    "response": "No issue categories found. Please contact IT support directly.",
                    "buttons": [
                        {"id": "back", "label": "⬅️ Go Back", "action": "start", "value": "back"}
                    ],
                    "state": self.STATE_INITIAL
                }
            
            # Add back button
            buttons = smart_categories + [
                {"id": "back", "label": "⬅️ Go Back", "action": "start", "value": "back"}
            ]
            
            return {
                "success": True,
                "response": "🔧 **Report an Issue**\n\nPlease select the category that best describes your issue:",
                "buttons": buttons,
                "state": self.STATE_AWAITING_SMART_CATEGORY,
                "show_text_input": False
            }
        
        else:
            # Invalid selection
            return self._handle_start(conversation_state, user_info)
    
    def _handle_select_smart_category(self, data: Dict, conversation_state: Dict) -> Dict:
        """Handle smart category selection"""
        smart_category = data.get('value')
        
        # Update state
        conversation_state['smart_category'] = smart_category
        conversation_state['navigation_stack'].append(('smart_category', smart_category))
        conversation_state['state'] = self.STATE_AWAITING_CATEGORY
        
        # Get categories
        categories = self.data_service.get_categories(
            conversation_state['ticket_type'],
            smart_category
        )
        
        if not categories:
            return {
                "success": True,
                "response": f"No subcategories found for {smart_category}. Please select a different category.",
                "buttons": [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ],
                "state": self.STATE_AWAITING_SMART_CATEGORY
            }
        
        # Add back button
        buttons = categories + [
            {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
        ]
        
        return {
            "success": True,
            "response": f"📁 **{smart_category}**\n\nPlease select the category:",
            "buttons": buttons,
            "state": self.STATE_AWAITING_CATEGORY,
            "show_text_input": False
        }
    
    def _handle_select_category(self, data: Dict, conversation_state: Dict) -> Dict:
        """Handle category selection (Hardware & Connectivity / Applications & Software)"""
        category = data.get('value')
        
        # Update state
        conversation_state['category'] = category
        conversation_state['navigation_stack'].append(('category', category))
        conversation_state['state'] = self.STATE_AWAITING_TYPE
        
        # Get types
        types = self.data_service.get_types(
            conversation_state['ticket_type'],
            conversation_state['smart_category'],
            category
        )
        
        if not types:
            return {
                "success": True,
                "response": f"No types found for {category}. Please select a different category.",
                "buttons": [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ],
                "state": self.STATE_AWAITING_CATEGORY
            }
        
        # Add back button
        buttons = types + [
            {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
        ]
        
        return {
            "success": True,
            "response": f"📂 **{category}**\n\nPlease select the type of issue:",
            "buttons": buttons,
            "state": self.STATE_AWAITING_TYPE,
            "show_text_input": False
        }
    
    def _handle_select_type(self, data: Dict, conversation_state: Dict) -> Dict:
        """Handle type selection (e.g., Network, Windows 10, Laptop)"""
        type_name = data.get('value')
        
        # Update state
        conversation_state['type'] = type_name
        conversation_state['navigation_stack'].append(('type', type_name))
        conversation_state['state'] = self.STATE_AWAITING_ITEM
        
        # Get items
        items = self.data_service.get_items(
            conversation_state['ticket_type'],
            conversation_state['smart_category'],
            conversation_state['category'],
            type_name
        )
        
        if not items:
            return {
                "success": True,
                "response": f"No items found for {type_name}. Please select a different type.",
                "buttons": [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ],
                "state": self.STATE_AWAITING_TYPE
            }
        
        # Add back button
        buttons = items + [
            {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
        ]
        
        return {
            "success": True,
            "response": f"📋 **{type_name}**\n\nPlease select the specific area:",
            "buttons": buttons,
            "state": self.STATE_AWAITING_ITEM,
            "show_text_input": False
        }
    
    def _handle_select_item(self, data: Dict, conversation_state: Dict) -> Dict:
        """Handle item selection (e.g., Network Port, Battery Problems)"""
        item_name = data.get('value')
        
        # Update state
        conversation_state['item'] = item_name
        conversation_state['navigation_stack'].append(('item', item_name))
        conversation_state['state'] = self.STATE_AWAITING_ISSUE
        
        # Get issues
        issues = self.data_service.get_issues(
            conversation_state['ticket_type'],
            conversation_state['smart_category'],
            conversation_state['category'],
            conversation_state['type'],
            item_name
        )
        
        if not issues:
            return {
                "success": True,
                "response": f"No issues found for {item_name}. Would you like to describe your issue?",
                "buttons": [
                    {"id": "other", "label": "📝 Describe My Issue", "action": "other_issue", "value": "other"},
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ],
                "state": self.STATE_AWAITING_ISSUE
            }
        
        # Add back button
        buttons = issues + [
            {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
        ]
        
        return {
            "success": True,
            "response": f"📌 **{item_name}**\n\nPlease select your issue (or choose 'Other Issue' if not listed):",
            "buttons": buttons,
            "state": self.STATE_AWAITING_ISSUE,
            "show_text_input": False
        }
    
    def _handle_select_issue(self, data: Dict, conversation_state: Dict) -> Dict:
        """Handle issue selection - show solution with per-solution feedback"""
        issue_index = int(data.get('value', 0))
        
        # Get the solution
        solution_data = self.data_service.get_issue_solution(
            conversation_state['ticket_type'],
            conversation_state['smart_category'],
            conversation_state['category'],
            conversation_state['type'],
            conversation_state['item'],
            issue_index
        )
        
        if not solution_data:
            return {
                "success": True,
                "response": "Sorry, I couldn't find the solution. Would you like to create a ticket?",
                "buttons": [
                    {"id": "ticket", "label": "🎫 Create Ticket", "action": "preview_ticket", "value": "yes"},
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ],
                "state": self.STATE_AWAITING_ISSUE
            }
        
        # Update state
        conversation_state['issue_index'] = issue_index
        conversation_state['issue_text'] = solution_data['issue']
        conversation_state['bot_solution'] = solution_data['bot_solution']
        conversation_state['navigation_stack'].append(('issue', issue_index))
        conversation_state['state'] = self.STATE_SHOWING_SOLUTION
        
        # Store in history for ticket creation
        conversation_state['issue_history'].append(f"Issue: {solution_data['issue']}")
        
        # Build per-solution feedback UI
        solution_ui = feedback_handler.build_solution_with_feedback_ui(
            solution_data['issue'], 
            solution_data['bot_solution']
        )
        
        # Store solutions list for tracking feedback (text strings only for DB storage)
        conversation_state['solutions_list'] = [
            s.get('text', '') if isinstance(s, dict) else str(s)
            for s in solution_ui.get('solutions', [])
        ]
        
        return {
            "success": True,
            "response": f"💡 **{solution_data['issue']}**\n\n{solution_data['bot_solution']}\n\n---\n\n**Did this resolve your issue?**",
            "buttons": [
                {"id": "resolved", "label": "✅ Yes, Issue Resolved!", "action": "solution_resolved", "value": "yes"},
                {"id": "not_resolved", "label": "❌ No, Still Need Help", "action": "solution_not_resolved", "value": "no"}
            ],
            "state": self.STATE_SHOWING_SOLUTION,
            "show_text_input": False,
            "solutions_with_feedback": solution_ui.get('solutions', [])
        }
    
    def _handle_other_issue(self, data: Dict, conversation_state: Dict) -> Dict:
        """Handle 'Other Issue' selection - open free text input"""
        conversation_state['state'] = self.STATE_AWAITING_FREE_TEXT
        conversation_state['navigation_stack'].append(('other_issue', None))
        
        # Build context message
        context_parts = []
        if conversation_state.get('smart_category'):
            context_parts.append(conversation_state['smart_category'])
        if conversation_state.get('type'):
            context_parts.append(conversation_state['type'])
        if conversation_state.get('item'):
            context_parts.append(conversation_state['item'])
        
        context = " > ".join(context_parts) if context_parts else "General"
        
        return {
            "success": True,
            "response": f"📝 **Describe Your Issue**\n\nContext: {context}\n\nPlease describe your issue in detail so we can help you better:",
            "buttons": [
                {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
            ],
            "state": self.STATE_AWAITING_FREE_TEXT,
            "show_text_input": True
        }
    
    def _handle_free_text(self, data: Dict, conversation_state: Dict, user_info: Dict) -> Dict:
        """Handle free text input from user - routes to appropriate handler based on state"""
        message = data.get('message', '').strip()
        session_id = data.get('session_id', f"session_{user_info.get('id', 'unknown')}")
        
        if not message:
            return {
                "success": True,
                "response": "Please describe your issue:",
                "buttons": [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ],
                "state": self.STATE_AWAITING_FREE_TEXT,
                "show_text_input": True
            }
        
        # Check if we're in a request flow state - route to request handler (NOT agent)
        current_state = conversation_state.get('state', '')
        
        if current_state == 'request_justification':
            return request_handler.handle_justification(message, conversation_state)
        
        elif current_state == 'request_vpn_reason':
            return request_handler.handle_vpn_reason(message, conversation_state)
        
        elif current_state == 'request_shared_folder_path':
            return request_handler.handle_shared_folder_path(message, conversation_state)
        
        elif current_state == 'request_software_type':
            # "Other" software - user typed the software name
            conversation_state['request_item'] = message
            action = conversation_state.get('software_action', 'install')
            conversation_state['justification'] = f"Requesting {action} of {message}"
            conversation_state['state'] = 'request_preview'
            return request_handler.build_request_preview(conversation_state)
        
        elif current_state == 'end_feedback_text':
            # User typed feedback text
            return feedback_handler.handle_feedback_text_submit(message, conversation_state)
        
        # Store the free text
        conversation_state['free_text_description'] = message
        conversation_state['issue_text'] = message
        if 'issue_history' not in conversation_state:
            conversation_state['issue_history'] = []
        conversation_state['issue_history'].append(f"User: {message}")
        
        # Try to use the AI Agent for intelligent response
        try:
            # Import here to avoid circular imports
            from runners.run_agents import orchestrator
            
            # Get or initialize the agent conversation state
            agent_state = conversation_state.get('agent_state')
            
            logger.info(f"Processing free text with AI agent for user {user_info.get('id')}")
            
            agent_result = run_async(orchestrator.handle_user_query(
                user_id=user_info.get('id'),
                user_email=user_info.get('email'),
                session_id=session_id,
                message=message,
                conversation_state=agent_state
            ))
            
            # Store updated agent state
            conversation_state['agent_state'] = agent_result.get('conversation_state')
            
            # Get the agent's response
            agent_response = agent_result.get('response', '')
            
            # Store agent response in history
            conversation_state['issue_history'].append(f"Agent: {agent_response[:200]}...")
            
            # Check if agent needs escalation (ticket was created directly)
            if agent_result.get('escalated') or agent_result.get('ticket_id'):
                # Ticket was created by agent
                ticket_id = agent_result.get('ticket_id')
                
                if ticket_id:
                    conversation_state['state'] = self.STATE_TICKET_CREATED
                    return {
                        "success": True,
                        "response": agent_response,
                        "ticket_id": ticket_id,
                        "buttons": [
                            {"id": "new", "label": "🆕 New Issue", "action": "start", "value": "new"},
                            {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
                        ],
                        "state": self.STATE_TICKET_CREATED,
                        "show_text_input": False
                    }
                else:
                    # Escalation without ticket (fallback)
                    conversation_state['state'] = self.STATE_AWAITING_TICKET_CONFIRMATION
                    return {
                        "success": True,
                        "response": agent_response + "\n\n---\n\nWould you like me to create a support ticket for this issue?",
                        "buttons": [
                            {"id": "yes", "label": "✅ Yes, Create Ticket", "action": "preview_ticket", "value": "yes"},
                            {"id": "no", "label": "❌ No, Thanks", "action": "decline_ticket", "value": "no"}
                        ],
                        "state": self.STATE_AWAITING_TICKET_CONFIRMATION,
                        "show_text_input": False
                    }
            
            # Agent provided a solution - ask if it helped (with per-solution feedback like button nav)
            else:
                conversation_state['bot_solution'] = agent_response
                conversation_state['state'] = self.STATE_SHOWING_SOLUTION
                
                # Build per-solution feedback UI (same as button navigation)
                solution_ui = feedback_handler.build_solution_with_feedback_ui(
                    message, agent_response
                )
                
                # Store solutions list for tracking feedback
                conversation_state['solutions_list'] = [
                    s.get('text', '') if isinstance(s, dict) else str(s)
                    for s in solution_ui.get('solutions', [])
                ]
                
                return {
                    "success": True,
                    "response": agent_response + "\n\n---\n\n**Did this resolve your issue?**",
                    "buttons": [
                        {"id": "resolved", "label": "✅ Yes, Issue Resolved!", "action": "solution_resolved", "value": "yes"},
                        {"id": "not_resolved", "label": "❌ No, Still Need Help", "action": "solution_not_resolved", "value": "no"}
                    ],
                    "state": self.STATE_SHOWING_SOLUTION,
                    "show_text_input": False,
                    "solutions_with_feedback": solution_ui.get('solutions', [])
                }
            
        except Exception as agent_error:
            logger.error(f"AI Agent error: {agent_error}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback to simple search if agent fails
            logger.info("Falling back to keyword-based search")
            return self._handle_free_text_fallback(message, conversation_state)
    
    def _handle_free_text_fallback(self, message: str, conversation_state: Dict) -> Dict:
        """Fallback handler when AI agent is unavailable - uses keyword search"""
        # Try to find matching solutions from data.json
        search_results = self.data_service.search_issues(message, 'Incident')
        
        if search_results:
            # Found potential matches - show the best one
            best_match = search_results[0]
            conversation_state['bot_solution'] = best_match['bot_solution']
            conversation_state['state'] = self.STATE_SHOWING_SOLUTION
            
            # Build per-solution feedback UI (same as button navigation)
            solution_ui = feedback_handler.build_solution_with_feedback_ui(
                best_match['issue'], best_match['bot_solution']
            )
            
            # Store solutions list for tracking feedback
            conversation_state['solutions_list'] = [
                s.get('text', '') if isinstance(s, dict) else str(s)
                for s in solution_ui.get('solutions', [])
            ]
            
            return {
                "success": True,
                "response": f"💡 **I found a possible solution for your issue:**\n\n**{best_match['issue']}**\n\n{best_match['bot_solution']}\n\n---\n\n**Did this resolve your issue?**",
                "buttons": [
                    {"id": "resolved", "label": "✅ Yes, Issue Resolved!", "action": "solution_resolved", "value": "yes"},
                    {"id": "not_resolved", "label": "❌ No, Create Ticket", "action": "solution_not_resolved", "value": "no"}
                ],
                "state": self.STATE_SHOWING_SOLUTION,
                "show_text_input": False,
                "solutions_with_feedback": solution_ui.get('solutions', [])
            }
        else:
            # No matches - offer to create ticket directly
            conversation_state['state'] = self.STATE_AWAITING_TICKET_CONFIRMATION
            
            return {
                "success": True,
                "response": "I couldn't find an exact solution for your issue. Would you like me to create a support ticket for you?",
                "buttons": [
                    {"id": "yes", "label": "✅ Yes, Create Ticket", "action": "preview_ticket", "value": "yes"},
                    {"id": "no", "label": "❌ No, Go Back", "action": "go_back", "value": "no"}
                ],
                "state": self.STATE_AWAITING_TICKET_CONFIRMATION,
                "show_text_input": False
            }
    
    def _handle_solution_resolved(self, conversation_state: Dict) -> Dict:
        """Handle when user says solution resolved their issue - prompt for final feedback"""
        conversation_state['state'] = self.STATE_END_RATING
        
        star_ui = feedback_handler.get_star_rating_ui()
        
        # Include star rating buttons in the main buttons array so frontend renders them
        star_buttons = star_ui.get('buttons', [])
        star_buttons.append({"id": "skip", "label": "⏭️ Skip Rating", "action": "skip_rating", "value": "skip"})
        
        return {
            "success": True,
            "response": "🎉 **Great!** I'm glad the solution helped resolve your issue.\n\n📊 **How was your experience?** Please rate your interaction:",
            "show_star_rating": True,
            "buttons": star_buttons,
            "state": self.STATE_END_RATING,
            "show_text_input": False
        }
    
    def _handle_solution_not_resolved(self, conversation_state: Dict) -> Dict:
        """Handle when solution didn't resolve the issue"""
        conversation_state['state'] = self.STATE_AWAITING_TICKET_CONFIRMATION
        
        return {
            "success": True,
            "response": "I'm sorry the solution didn't resolve your issue. Would you like me to create a support ticket so our IT team can assist you further?",
            "buttons": [
                {"id": "yes", "label": "✅ Yes, Create Ticket", "action": "preview_ticket", "value": "yes"},
                {"id": "try_again", "label": "🔄 Try Different Issue", "action": "go_back", "value": "back"},
                {"id": "no", "label": "❌ No, I'm Done", "action": "end", "value": "no"}
            ],
            "state": self.STATE_AWAITING_TICKET_CONFIRMATION,
            "show_text_input": False
        }
    
    def _handle_agent_continue(self, conversation_state: Dict) -> Dict:
        """Handle when user wants to continue conversation with agent"""
        conversation_state['state'] = self.STATE_AWAITING_FREE_TEXT
        
        return {
            "success": True,
            "response": "Please provide more details or ask a follow-up question:",
            "buttons": [
                {"id": "ticket", "label": "🎫 Create Ticket Instead", "action": "preview_ticket", "value": "ticket"},
                {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
            ],
            "state": self.STATE_AWAITING_FREE_TEXT,
            "show_text_input": True
        }
    
    def _handle_preview_ticket(self, conversation_state: Dict, user_info: Dict) -> Dict:
        """Show ticket preview before creation"""
        # Build ticket details
        smart_category = conversation_state.get('smart_category', 'General')
        issue_text = conversation_state.get('issue_text', 'User reported issue')
        bot_solution = conversation_state.get('bot_solution', '')
        free_text = conversation_state.get('free_text_description', '')
        
        # Build description
        description_parts = []
        if issue_text:
            description_parts.append(f"**Issue:** {issue_text}")
        if free_text and free_text != issue_text:
            description_parts.append(f"**Additional Details:** {free_text}")
        if bot_solution:
            description_parts.append(f"\n**Solution Attempted:**\n{bot_solution}")
        
        description = "\n\n".join(description_parts) if description_parts else "User requested support"
        
        # Store prepared ticket data
        conversation_state['prepared_ticket'] = {
            'category': smart_category,
            'subject': issue_text[:100] if issue_text else 'Support Request',
            'description': description
        }
        
        conversation_state['state'] = self.STATE_AWAITING_TICKET_CONFIRMATION
        
        preview = f"""📋 **Ticket Preview**

**Category:** {smart_category}

**Subject:** {issue_text[:100] if issue_text else 'Support Request'}

**Description:**
{description[:500]}{'...' if len(description) > 500 else ''}

---
Would you like to create this ticket?"""
        
        return {
            "success": True,
            "response": preview,
            "buttons": [
                {"id": "confirm", "label": "✅ Create Ticket", "action": "confirm_ticket", "value": "yes"},
                {"id": "cancel", "label": "❌ Cancel", "action": "decline_ticket", "value": "no"}
            ],
            "state": self.STATE_AWAITING_TICKET_CONFIRMATION,
            "show_text_input": False,
            "show_attachment_upload": True  # Enable attachment upload at this stage
        }
    
    def _handle_confirm_ticket(self, data: Dict, conversation_state: Dict, 
                               user_info: Dict) -> Dict:
        """
        Handle ticket creation confirmation
        Note: Actual ticket creation is done in app.py with database access
        """
        # Return the prepared ticket data for app.py to create
        prepared_ticket = conversation_state.get('prepared_ticket', {})
        attachment_urls = data.get('attachment_urls', []) or conversation_state.get('attachment_urls', [])
        
        conversation_state['state'] = self.STATE_TICKET_CREATED
        
        return {
            "success": True,
            "create_ticket": True,  # Flag for app.py to create the ticket
            "ticket_data": {
                "category": prepared_ticket.get('category', 'General'),
                "subject": prepared_ticket.get('subject', 'Support Request'),
                "description": prepared_ticket.get('description', 'User requested support'),
                "attachment_urls": attachment_urls
            },
            "state": self.STATE_TICKET_CREATED
        }
    
    def _handle_decline_ticket(self, conversation_state: Dict) -> Dict:
        """Handle when user declines ticket creation"""
        conversation_state['state'] = self.STATE_COMPLETED
        
        return {
            "success": True,
            "response": "No problem! Is there anything else I can help you with?",
            "buttons": [
                {"id": "new", "label": "🆕 Report Another Issue", "action": "start", "value": "new"},
                {"id": "done", "label": "✅ I'm All Done", "action": "end", "value": "done"}
            ],
            "state": self.STATE_COMPLETED,
            "show_text_input": False
        }
    
    def _handle_go_back(self, conversation_state: Dict) -> Dict:
        """Handle back navigation"""
        nav_stack = conversation_state.get('navigation_stack', [])
        
        if not nav_stack or len(nav_stack) <= 1:
            # Go back to start
            return {
                "success": True,
                "go_to_start": True
            }
        
        # Pop current level
        nav_stack.pop()
        
        # Get the previous level
        if nav_stack:
            prev_level, prev_value = nav_stack[-1]
            
            # Check if this is a request flow (starts with 'request_' OR ticket_type='Request')
            if prev_level.startswith('request_') or (prev_level == 'ticket_type' and prev_value == 'Request'):
                return self._handle_request_go_back(prev_level, prev_value, conversation_state)
            
            # Otherwise, handle incident flow
            # Clear states from current level onward
            level_order = ['ticket_type', 'smart_category', 'category', 'type', 'item', 'issue', 'other_issue']
            try:
                current_idx = level_order.index(prev_level)
                for level in level_order[current_idx + 1:]:
                    if level in ['smart_category', 'category', 'type', 'item']:
                        conversation_state[level] = None
                    elif level == 'issue':
                        conversation_state['issue_index'] = None
                        conversation_state['issue_text'] = None
                        conversation_state['bot_solution'] = None
            except ValueError:
                pass
            
            # Return buttons for previous level based on what level we're at
            if prev_level == 'ticket_type':
                conversation_state['state'] = self.STATE_AWAITING_SMART_CATEGORY
                categories = self.data_service.get_smart_categories('Incident')
                buttons = categories + [
                    {"id": "back", "label": "⬅️ Go Back", "action": "start", "value": "back"}
                ]
                return {
                    "success": True,
                    "response": "🔧 **Report an Issue**\n\nPlease select the category:",
                    "buttons": buttons,
                    "state": self.STATE_AWAITING_SMART_CATEGORY
                }
            
            elif prev_level == 'smart_category':
                conversation_state['state'] = self.STATE_AWAITING_CATEGORY
                categories = self.data_service.get_categories(
                    conversation_state['ticket_type'],
                    conversation_state['smart_category']
                )
                buttons = categories + [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ]
                return {
                    "success": True,
                    "response": f"📁 **{conversation_state['smart_category']}**\n\nPlease select the category:",
                    "buttons": buttons,
                    "state": self.STATE_AWAITING_CATEGORY
                }
            
            elif prev_level == 'category':
                conversation_state['state'] = self.STATE_AWAITING_TYPE
                types = self.data_service.get_types(
                    conversation_state['ticket_type'],
                    conversation_state['smart_category'],
                    conversation_state['category']
                )
                buttons = types + [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ]
                return {
                    "success": True,
                    "response": f"📂 **{conversation_state['category']}**\n\nPlease select the type:",
                    "buttons": buttons,
                    "state": self.STATE_AWAITING_TYPE
                }
            
            elif prev_level == 'type':
                conversation_state['state'] = self.STATE_AWAITING_ITEM
                items = self.data_service.get_items(
                    conversation_state['ticket_type'],
                    conversation_state['smart_category'],
                    conversation_state['category'],
                    conversation_state['type']
                )
                buttons = items + [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ]
                return {
                    "success": True,
                    "response": f"📋 **{conversation_state['type']}**\n\nPlease select the area:",
                    "buttons": buttons,
                    "state": self.STATE_AWAITING_ITEM
                }
            
            elif prev_level == 'item':
                conversation_state['state'] = self.STATE_AWAITING_ISSUE
                issues = self.data_service.get_issues(
                    conversation_state['ticket_type'],
                    conversation_state['smart_category'],
                    conversation_state['category'],
                    conversation_state['type'],
                    conversation_state['item']
                )
                buttons = issues + [
                    {"id": "back", "label": "⬅️ Go Back", "action": "go_back", "value": "back"}
                ]
                return {
                    "success": True,
                    "response": f"📌 **{conversation_state['item']}**\n\nPlease select your issue:",
                    "buttons": buttons,
                    "state": self.STATE_AWAITING_ISSUE
                }
        
        # Default: go to start
        return {
            "success": True,
            "go_to_start": True
        }
    
    def _handle_request_go_back(self, prev_level: str, prev_value: str, conversation_state: Dict) -> Dict:
        """Handle back navigation for request flow"""
        from services.request_flow_handler import (
            REQUEST_CATEGORIES, 
            STATE_REQUEST_CATEGORY, 
            STATE_REQUEST_HARDWARE_TYPE, 
            STATE_REQUEST_HARDWARE_BRAND,
            STATE_REQUEST_SOFTWARE_ACTION,
            STATE_REQUEST_SOFTWARE_TYPE,
            STATE_REQUEST_ACCESS_TYPE,
            STATE_REQUEST_SHARED_FOLDER_PATH,
            STATE_REQUEST_SHARED_FOLDER_PERMISSION,
            STATE_REQUEST_INTERNET_ACCESS,
            HARDWARE_BRANDS
        )
        
        # Handle ticket_type='Request' - show request category selection
        if prev_level == 'ticket_type' and prev_value == 'Request':
            conversation_state['state'] = STATE_REQUEST_CATEGORY
            buttons = [
                {'id': 'hardware', 'label': '💻 Hardware', 'action': 'select_request_category', 'value': 'hardware'},
                {'id': 'software', 'label': '💿 Software', 'action': 'select_request_category', 'value': 'software'},
                {'id': 'access', 'label': '🔐 Access', 'action': 'select_request_category', 'value': 'access'},
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ]
            return {
                "success": True,
                "response": "📝 **Service Request**\n\nWhat would you like to request?",
                "buttons": buttons,
                "state": STATE_REQUEST_CATEGORY,
                "show_text_input": False
            }
        
        # Handle request_category - go back to request category selection
        elif prev_level == 'request_category':
            conversation_state['state'] = STATE_REQUEST_CATEGORY
            buttons = [
                {'id': 'hardware', 'label': '💻 Hardware', 'action': 'select_request_category', 'value': 'hardware'},
                {'id': 'software', 'label': '💿 Software', 'action': 'select_request_category', 'value': 'software'},
                {'id': 'access', 'label': '🔐 Access', 'action': 'select_request_category', 'value': 'access'},
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ]
            return {
                "success": True,
                "response": "📝 **Service Request**\n\nWhat would you like to request?",
                "buttons": buttons,
                "state": STATE_REQUEST_CATEGORY,
                "show_text_input": False
            }
        
        # Handle request_hardware_type - go back to hardware options
        elif prev_level == 'request_hardware_type':
            conversation_state['state'] = STATE_REQUEST_HARDWARE_TYPE
            buttons = [{'id': item['id'], 'label': item['label'], 
                       'action': 'select_hardware_item', 'value': item['value']} 
                       for item in REQUEST_CATEGORIES['hardware']['items']]
            buttons.append({'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'})
            return {
                "success": True,
                "response": "💻 **Hardware Request**\n\nWhat hardware do you need?",
                "buttons": buttons,
                "state": STATE_REQUEST_HARDWARE_TYPE,
                "show_text_input": False
            }
        
        # Handle request_hardware_brand - go back to brand selection
        elif prev_level == 'request_hardware_brand':
            conversation_state['state'] = STATE_REQUEST_HARDWARE_BRAND
            hardware_type = conversation_state.get('request_item', '')
            brands = HARDWARE_BRANDS.get(prev_value, [])
            buttons = [{'id': b['id'], 'label': b['label'], 
                       'action': 'select_hardware_brand', 'value': b['value']} 
                       for b in brands]
            buttons.append({'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'})
            return {
                "success": True,
                "response": f"💻 **{prev_value} Request**\n\nPlease select the brand/type:",
                "buttons": buttons,
                "state": STATE_REQUEST_HARDWARE_BRAND,
                "show_text_input": False
            }
        
        # Handle request_software_action - go back to install/remove selection
        elif prev_level == 'request_software_action':
            conversation_state['state'] = STATE_REQUEST_SOFTWARE_ACTION
            buttons = REQUEST_CATEGORIES['software']['actions'] + [
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ]
            return {
                "success": True,
                "response": "💿 **Software Request**\n\nWhat would you like to do?",
                "buttons": buttons,
                "state": STATE_REQUEST_SOFTWARE_ACTION,
                "show_text_input": False
            }
        
        # Handle request_software_type - go back to software item selection
        elif prev_level == 'request_software_type':
            conversation_state['state'] = STATE_REQUEST_SOFTWARE_TYPE
            action = conversation_state.get('software_action', 'install')
            action_text = "install" if action == "install" else "remove"
            buttons = [{'id': item['id'], 'label': item['label'], 
                       'action': 'select_software_item', 'value': item['value']} 
                       for item in REQUEST_CATEGORIES['software']['items']]
            buttons.append({'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'})
            return {
                "success": True,
                "response": f"💿 **Software {action_text.title()}**\n\nPlease select the software to {action_text}:",
                "buttons": buttons,
                "state": STATE_REQUEST_SOFTWARE_TYPE,
                "show_text_input": False
            }
        
        # Handle request_access_type - go back to access type selection
        elif prev_level == 'request_access_type':
            conversation_state['state'] = STATE_REQUEST_ACCESS_TYPE
            buttons = REQUEST_CATEGORIES['access']['types'] + [
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ]
            return {
                "success": True,
                "response": "🔐 **Access Request**\n\nWhat type of access do you need?",
                "buttons": buttons,
                "state": STATE_REQUEST_ACCESS_TYPE,
                "show_text_input": False
            }
        
        # Handle request_access_folder - go back to folder path input
        elif prev_level == 'request_access_folder':
            conversation_state['state'] = STATE_REQUEST_SHARED_FOLDER_PATH
            return {
                "success": True,
                "response": "📁 **Shared Folder Access**\n\nPlease enter the folder path (e.g., \\\\server\\share\\folder):",
                "buttons": [{'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}],
                "state": STATE_REQUEST_SHARED_FOLDER_PATH,
                "show_text_input": True
            }
        
        # Handle request_folder_path - go back to folder permission selection
        elif prev_level == 'request_folder_path':
            conversation_state['state'] = STATE_REQUEST_SHARED_FOLDER_PERMISSION
            folder_path = prev_value
            buttons = REQUEST_CATEGORIES['access']['folder_permissions'] + [
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ]
            return {
                "success": True,
                "response": f"📁 **Folder: {folder_path}**\n\nSelect the permission level you need:",
                "buttons": buttons,
                "state": STATE_REQUEST_SHARED_FOLDER_PERMISSION,
                "show_text_input": False
            }
        
        # Handle request_internet_confirm or request_access_vpn - go back to access type selection
        elif prev_level in ['request_internet_confirm', 'request_access_vpn', 'request_folder_permission']:
            conversation_state['state'] = STATE_REQUEST_ACCESS_TYPE
            buttons = REQUEST_CATEGORIES['access']['types'] + [
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ]
            return {
                "success": True,
                "response": "🔐 **Access Request**\n\nWhat type of access do you need?",
                "buttons": buttons,
                "state": STATE_REQUEST_ACCESS_TYPE,
                "show_text_input": False
            }
        
        # Default: go to start
        return {
            "success": True,
            "go_to_start": True
        }
    
    def _handle_end(self, conversation_state: Dict) -> Dict:
        """Handle end of conversation"""
        conversation_state['state'] = self.STATE_COMPLETED
        
        return {
            "success": True,
            "response": "Thank you for using IT Support! Have a great day! 👋\n\nFeel free to come back anytime you need help.",
            "buttons": [
                {"id": "new", "label": "🔄 Start New Conversation", "action": "start", "value": "new"}
            ],
            "state": self.STATE_COMPLETED,
            "show_text_input": False
        }


# Global instance
chat_handler = ChatHandler()
