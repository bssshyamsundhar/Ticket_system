"""
Google ADK Runner for executing agents with state-based confirmation flow
Supports proper multi-turn conversations with user confirmations
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from agents.self_service.agent import create_self_service_agent
from agents.escalation.agent import create_escalation_agent
from config import config
from db.postgres import db
from tools.tool_registry import (
    SELF_SERVICE_TOOLS_DICT,
    ESCALATION_TOOLS_DICT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """States for conversation flow"""
    ACTIVE = "active"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    AWAITING_TICKET_CONFIRMATION = "awaiting_ticket_confirmation"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AgentOrchestrator:
    """Orchestrates multi-agent workflow using Google ADK with state management"""

    def __init__(self):
        self.session_service = InMemorySessionService()

        self.self_service_agent = create_self_service_agent()
        self.escalation_agent = create_escalation_agent()

        # Store tools dict for both agents
        self.self_service_tools = SELF_SERVICE_TOOLS_DICT
        self.escalation_tools = ESCALATION_TOOLS_DICT

        self.self_service_runner = Runner(
            agent=self.self_service_agent,
            app_name=config.APP_NAME,
            session_service=self.session_service,
        )

        self.escalation_runner = Runner(
            agent=self.escalation_agent,
            app_name=config.APP_NAME,
            session_service=self.session_service,
        )

        logger.info("Agent Orchestrator initialized with state management")

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any], tools_dict: Dict) -> Any:
        """
        Execute a tool function from the tools dict.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
            tools_dict: Dictionary mapping tool names to functions
            
        Returns:
            Result from the tool function
        """
        if tool_name not in tools_dict:
            logger.error(f"Tool {tool_name} not found in tools_dict")
            raise ValueError(f"Function {tool_name} is not found in the tools_dict.")
        
        tool_func = tools_dict[tool_name]
        try:
            result = tool_func(**tool_args)
            logger.info(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise

    async def create_user_session(self, user_id: str) -> str:
        """Create a new session for a user"""
        session = await self.session_service.create_session(
            app_name=config.APP_NAME,
            user_id=user_id,
        )
        logger.info(f"Created session {session.id} for user {user_id}")
        return session.id

    def _initialize_conversation_state(self) -> Dict[str, Any]:
        """Initialize a new conversation state"""
        return {
            "state": ConversationState.ACTIVE,
            "clarification_count": 0,
            "issue_summary": "",
            "refined_query": None,
            "confidence_score": None,
            "pending_ticket_data": None,  # Store ticket data during confirmation
        }

    # ------------------------------------------------------------------
    # SELF SERVICE AGENT
    # ------------------------------------------------------------------

    async def run_self_service_agent(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """Run the self-service agent to handle user query"""

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )

        final_response = ""
        needs_escalation = False
        needs_clarification = False
        escalation_issue = None

        async for event in self.self_service_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                final_response = event.content.parts[0].text

                # Check for escalation signal
                if "ESCALATE_TO_HUMAN:" in final_response:
                    needs_escalation = True
                    # Extract issue summary from escalation marker
                    parts = final_response.split("ESCALATE_TO_HUMAN:", 1)
                    if len(parts) > 1:
                        escalation_issue = parts[1].strip()
                    else:
                        escalation_issue = user_message

                # Check for clarification signal
                if "CLARIFICATION_NEEDED:" in final_response or "clarify" in final_response.lower():
                    needs_clarification = True

        return {
            "success": True,
            "response": final_response,
            "needs_escalation": needs_escalation,
            "escalation_issue": escalation_issue,
            "needs_clarification": needs_clarification,
            "agent": "self_service",
        }

    # ------------------------------------------------------------------
    # ESCALATION AGENT - PREVIEW STEP
    # ------------------------------------------------------------------

    async def run_escalation_preview(
        self,
        user_id: str,
        session_id: str,
        issue_summary: str,
        user_email: str,
        refined_query: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run escalation agent to show ticket preview.
        This is STEP 1 of the escalation flow.
        """

        escalation_prompt = f"""
You have been asked to escalate an IT support issue to create a support ticket.

ESCALATION CONTEXT:
- User ID: {user_id}
- User Email: {user_email}
- Issue Summary: {issue_summary}
- Refined Query: {refined_query or "Not provided"}
- KB Confidence Score: {confidence_score if confidence_score is not None else "Not available"}

YOUR TASK:
1. Call the preview_escalation_ticket tool with the issue details
2. Show the preview to the user
3. Ask the user to confirm (yes/no)
4. DO NOT create the ticket yet - just show the preview and wait

Remember: You must CALL the preview_escalation_ticket tool, not simulate it.
"""

        content = types.Content(
            role="user",
            parts=[types.Part(text=escalation_prompt)],
        )

        final_response = ""

        async for event in self.escalation_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                final_response = event.content.parts[0].text

        logger.info(f"Escalation preview shown to user {user_id}")

        return {
            "success": True,
            "response": final_response,
            "agent": "escalation",
            "stage": "preview",
        }

    # ------------------------------------------------------------------
    # ESCALATION AGENT - CONFIRMATION STEP
    # ------------------------------------------------------------------

    async def run_escalation_confirmation(
        self,
        user_id: str,
        session_id: str,
        user_response: str,
        issue_summary: str,
        user_email: str,
        refined_query: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Handle user's yes/no response to ticket creation.
        This is STEP 2 of the escalation flow.
        """

        # Detect user intent
        user_response_lower = user_response.lower().strip()
        
        # Check for affirmative responses
        affirmative = any(word in user_response_lower for word in [
            'yes', 'y', 'confirm', 'create', 'proceed', 'ok', 'sure', 'please'
        ])
        
        # Check for negative responses
        negative = any(word in user_response_lower for word in [
            'no', 'n', 'cancel', 'don\'t', 'skip', 'nevermind', 'nope'
        ])

        if affirmative and not negative:
            # User confirmed - create the ticket
            confirmation_prompt = f"""
The user has confirmed they want to create the support ticket.

ESCALATION DETAILS:
- User ID: {user_id}
- User Email: {user_email}
- Issue Summary: {issue_summary}
- Refined Query: {refined_query or "Not provided"}
- KB Confidence Score: {confidence_score if confidence_score is not None else "Not available"}

YOUR TASK:
Call the confirm_and_create_escalation_ticket tool with ALL the details above.
Show the user the confirmation message with the Ticket ID.

Remember: You must CALL the confirm_and_create_escalation_ticket tool.
"""

            content = types.Content(
                role="user",
                parts=[types.Part(text=confirmation_prompt)],
            )

            final_response = ""
            ticket_id = None

            async for event in self.escalation_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.is_final_response():
                    final_response = event.content.parts[0].text
                    
                    # Try to extract ticket ID from response
                    import re
                    match = re.search(r'[Tt]icket\s*ID[:\s#]+(\d+)', final_response)
                    if match:
                        ticket_id = int(match.group(1))

            logger.info(f"Ticket created for user {user_id}, ticket_id: {ticket_id}")

            return {
                "success": True,
                "response": final_response,
                "agent": "escalation",
                "stage": "confirmed",
                "ticket_id": ticket_id,
                "ticket_created": True,
            }

        elif negative:
            # User declined ticket creation
            response = (
                "No problem, I've cancelled the ticket creation. "
                "If your issue becomes urgent or you change your mind, feel free to ask for help again. "
                "You can also email support@company.com directly."
            )

            logger.info(f"User {user_id} cancelled ticket creation")

            return {
                "success": True,
                "response": response,
                "agent": "escalation",
                "stage": "cancelled",
                "ticket_created": False,
            }

        else:
            # Unclear response - ask again
            response = (
                "I want to make sure I understand correctly. "
                "Would you like me to create this support ticket? "
                "Please reply 'yes' to create it or 'no' to cancel."
            )

            return {
                "success": True,
                "response": response,
                "agent": "escalation",
                "stage": "awaiting_confirmation",
                "ticket_created": False,
            }

    # ------------------------------------------------------------------
    # MAIN ORCHESTRATION ENTRY
    # ------------------------------------------------------------------

    async def get_or_create_session(self, user_id: str, session_id: str) -> str:
        """Get existing session or create a new one"""
        try:
            # Try to get the existing session
            session = await self.session_service.get_session(
                app_name=config.APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            if session:
                return session.id
        except Exception:
            pass  # Session doesn't exist, create a new one
        
        # Create a new session
        session = await self.session_service.create_session(
            app_name=config.APP_NAME,
            user_id=user_id,
            session_id=session_id  # Use the provided session_id
        )
        logger.info(f"Created new ADK session {session.id} for user {user_id}")
        return session.id

    async def handle_user_query(
        self,
        user_id: int,
        user_email: str,
        session_id: str,
        message: str,
        conversation_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for handling user queries with state-based flow.
        
        Args:
            user_id: Database user ID
            user_email: User's email from login token
            session_id: Session identifier
            message: User's message
            conversation_state: Current conversation state
            
        Returns:
            Dictionary with response and updated state
        """
        
        user_id_str = str(user_id)

        # Ensure session exists in ADK
        adk_session_id = await self.get_or_create_session(user_id_str, session_id)

        # Initialize conversation state if needed
        if conversation_state is None:
            conversation_state = self._initialize_conversation_state()

        current_state = conversation_state.get("state", ConversationState.ACTIVE)
        
        logger.info(f"Handling query for user {user_id} in state: {current_state}")

        # ------------------------------------------------------------------
        # STATE: AWAITING TICKET CONFIRMATION
        # ------------------------------------------------------------------
        if current_state == ConversationState.AWAITING_TICKET_CONFIRMATION:
            pending_data = conversation_state.get("pending_ticket_data", {})
            
            result = await self.run_escalation_confirmation(
                user_id=user_id_str,
                session_id=adk_session_id,
                user_response=message,
                issue_summary=pending_data.get("issue_summary", ""),
                user_email=user_email,
                refined_query=pending_data.get("refined_query"),
                confidence_score=pending_data.get("confidence_score"),
            )

            # Save conversation
            db.save_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='agent',
                message_content=result["response"],
                ticket_id=result.get("ticket_id"),
            )

            # Update state based on outcome
            if result.get("ticket_created"):
                conversation_state["state"] = ConversationState.ESCALATED
            elif result.get("stage") == "cancelled":
                conversation_state = self._initialize_conversation_state()
            # else: still awaiting confirmation

            return {
                "success": True,
                "response": result["response"],
                "agent": result["agent"],
                "ticket_id": result.get("ticket_id"),
                "escalated": result.get("ticket_created", False),
                "conversation_state": conversation_state,
            }

        # ------------------------------------------------------------------
        # STATE: AWAITING CLARIFICATION - Process clarification response
        # ------------------------------------------------------------------
        if current_state == ConversationState.AWAITING_CLARIFICATION:
            logger.info(f"Processing clarification response from user {user_id}")
            
            # Store the clarification as refined_query
            original_issue = conversation_state.get("issue_summary", "")
            conversation_state["refined_query"] = message
            
            # Build enhanced query with original issue + clarification
            enhanced_message = f"""Original issue: {original_issue}
            
User's clarification: {message}

Please search the knowledge base with this additional context and provide a solution."""

            # Change state back to ACTIVE to continue processing
            conversation_state["state"] = ConversationState.ACTIVE
            
            # Now run self-service agent with enhanced context
            result = await self.run_self_service_agent(
                user_id=user_id_str,
                session_id=adk_session_id,
                user_message=enhanced_message,
            )
            
            response_text = result["response"]
            
            # Check if agent still needs clarification or wants to escalate
            if result["needs_escalation"]:
                issue_summary = result.get("escalation_issue", original_issue + " - " + message)
                
                escalation_result = await self.run_escalation_preview(
                    user_id=user_id_str,
                    session_id=adk_session_id,
                    issue_summary=issue_summary,
                    user_email=user_email,
                    refined_query=message,
                    confidence_score=conversation_state.get("confidence_score"),
                )
                
                db.save_conversation(
                    user_id=user_id,
                    session_id=session_id,
                    message_type='agent',
                    message_content=response_text + "\n\n" + escalation_result["response"],
                )
                
                conversation_state["state"] = ConversationState.AWAITING_TICKET_CONFIRMATION
                conversation_state["pending_ticket_data"] = {
                    "issue_summary": issue_summary,
                    "refined_query": message,
                    "confidence_score": conversation_state.get("confidence_score"),
                }
                
                return {
                    "success": True,
                    "response": response_text + "\n\n" + escalation_result["response"],
                    "agent": "escalation",
                    "awaiting_confirmation": True,
                    "conversation_state": conversation_state,
                }
            
            # If agent needs more clarification
            if result["needs_clarification"]:
                conversation_state["clarification_count"] += 1
                conversation_state["issue_summary"] = original_issue + " | " + message
                conversation_state["state"] = ConversationState.AWAITING_CLARIFICATION
                
                remaining = config.MAX_CLARIFICATION_ATTEMPTS - conversation_state["clarification_count"]
                if remaining <= 0:
                    # Max clarifications reached, force escalation
                    logger.info(f"Max clarifications reached after response for user {user_id}")
                    escalation_result = await self.run_escalation_preview(
                        user_id=user_id_str,
                        session_id=adk_session_id,
                        issue_summary=original_issue + " | " + message,
                        user_email=user_email,
                        refined_query=message,
                    )
                    
                    conversation_state["state"] = ConversationState.AWAITING_TICKET_CONFIRMATION
                    conversation_state["pending_ticket_data"] = {
                        "issue_summary": original_issue + " | " + message,
                        "refined_query": message,
                    }
                    
                    db.save_conversation(
                        user_id=user_id,
                        session_id=session_id,
                        message_type='agent',
                        message_content=escalation_result["response"],
                    )
                    
                    return {
                        "success": True,
                        "response": escalation_result["response"],
                        "agent": "escalation",
                        "awaiting_confirmation": True,
                        "conversation_state": conversation_state,
                    }
                
                if remaining == 1:
                    response_text += "\n\n*Note: If I need more details after this, I'll connect you with our support team.*"
            
            db.save_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='agent',
                message_content=response_text,
            )
            
            return {
                "success": True,
                "response": response_text,
                "agent": "self_service",
                "conversation_state": conversation_state,
                "needs_clarification": result["needs_clarification"],
            }

        # ------------------------------------------------------------------
        # STATE: CHECK FOR MAX CLARIFICATIONS (Force Escalation)
        # ------------------------------------------------------------------
        if conversation_state["clarification_count"] >= config.MAX_CLARIFICATION_ATTEMPTS:
            logger.info(f"Max clarifications reached for user {user_id}, forcing escalation")
            
            # Show preview and ask for confirmation
            result = await self.run_escalation_preview(
                user_id=user_id_str,
                session_id=adk_session_id,
                issue_summary=conversation_state.get("issue_summary", message),
                user_email=user_email,
                refined_query=conversation_state.get("refined_query"),
                confidence_score=conversation_state.get("confidence_score"),
            )

            # Save conversation
            db.save_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='agent',
                message_content=result["response"],
            )

            # Update state to awaiting confirmation
            conversation_state["state"] = ConversationState.AWAITING_TICKET_CONFIRMATION
            conversation_state["pending_ticket_data"] = {
                "issue_summary": conversation_state.get("issue_summary", message),
                "refined_query": conversation_state.get("refined_query"),
                "confidence_score": conversation_state.get("confidence_score"),
            }

            return {
                "success": True,
                "response": result["response"],
                "agent": "escalation",
                "awaiting_confirmation": True,
                "conversation_state": conversation_state,
            }

        # ------------------------------------------------------------------
        # STATE: ACTIVE - Run Self-Service Agent
        # ------------------------------------------------------------------
        result = await self.run_self_service_agent(
            user_id=user_id_str,
            session_id=adk_session_id,
            user_message=message,
        )

        response_text = result["response"]

        # ------------------------------------------------------------------
        # CHECK: Agent Requested Escalation
        # ------------------------------------------------------------------
        if result["needs_escalation"]:
            issue_summary = result.get("escalation_issue", message)

            logger.info(f"Self-service agent requested escalation for user {user_id}")

            # Show preview and ask for confirmation
            escalation_result = await self.run_escalation_preview(
                user_id=user_id_str,
                session_id=adk_session_id,
                issue_summary=issue_summary,
                user_email=user_email,
                refined_query=conversation_state.get("refined_query"),
                confidence_score=conversation_state.get("confidence_score"),
            )

            # Save both conversations
            db.save_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='agent',
                message_content=response_text,
            )

            db.save_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='escalation',
                message_content=escalation_result["response"],
            )

            # Update state to awaiting confirmation
            conversation_state["state"] = ConversationState.AWAITING_TICKET_CONFIRMATION
            conversation_state["pending_ticket_data"] = {
                "issue_summary": issue_summary,
                "refined_query": conversation_state.get("refined_query"),
                "confidence_score": conversation_state.get("confidence_score"),
            }

            combined_response = response_text + "\n\n" + escalation_result["response"]

            return {
                "success": True,
                "response": combined_response,
                "agent": "escalation",
                "awaiting_confirmation": True,
                "conversation_state": conversation_state,
            }

        # ------------------------------------------------------------------
        # CHECK: Agent Needs Clarification
        # ------------------------------------------------------------------
        if result["needs_clarification"]:
            conversation_state["clarification_count"] += 1
            conversation_state["issue_summary"] = message
            conversation_state["state"] = ConversationState.AWAITING_CLARIFICATION

            # Add progress indicator if approaching limit
            remaining = config.MAX_CLARIFICATION_ATTEMPTS - conversation_state["clarification_count"]
            if remaining == 1:
                response_text += "\n\n*Note: If I need more details after this, I'll connect you with our support team.*"

        # Save conversation
        db.save_conversation(
            user_id=user_id,
            session_id=session_id,
            message_type='agent',
            message_content=response_text,
        )

        return {
            "success": True,
            "response": response_text,
            "agent": "self_service",
            "conversation_state": conversation_state,
            "needs_clarification": result["needs_clarification"],
        }

    # ------------------------------------------------------------------
    # SUMMARIZATION - Uses self-service agent for ticket summarization
    # ------------------------------------------------------------------

    async def summarize_for_ticket(
        self,
        user_id: str,
        session_id: str,
        conversation_history: list,
        category: str,
    ) -> Dict[str, Any]:
        """
        Use the self-service agent to summarize conversation into a concise ticket summary.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            conversation_history: List of user messages
            category: Issue category
            
        Returns:
            Dict with 'subject' and 'description' keys
        """
        conversation_text = "\n".join([f"- {msg}" for msg in conversation_history])
        
        summarize_prompt = f"""Summarize this IT support conversation into a brief ticket.

User Messages:
{conversation_text}

Category: {category}

IMPORTANT: Be extremely concise. 

Provide a response in this EXACT format (no extra text, no markdown, no explanations):
SUBJECT: [One brief sentence (max 80 chars) that captures the main issue]
DESCRIPTION: [1-2 sentences summarizing the problem and key details. Include any error messages, software names, or specific symptoms mentioned. Max 200 characters.]

Example output:
SUBJECT: Outlook crashes when opening attachments
DESCRIPTION: User reports Outlook 365 crashing whenever they try to open PDF attachments. Issue started after recent Windows update.
"""

        content = types.Content(
            role="user",
            parts=[types.Part(text=summarize_prompt)],
        )

        final_response = ""

        try:
            async for event in self.self_service_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.is_final_response():
                    final_response = event.content.parts[0].text

            # Parse the response
            subject = "Support Request"
            description = conversation_text

            if "SUBJECT:" in final_response and "DESCRIPTION:" in final_response:
                parts = final_response.split("DESCRIPTION:", 1)
                subject_part = parts[0].replace("SUBJECT:", "").strip()
                description_part = parts[1].strip() if len(parts) > 1 else ""

                # Clean up subject - remove quotes, extra spaces
                subject = subject_part.strip('"\'').strip()[:80] if subject_part else "Support Request"
                
                # Clean up description - keep it concise
                description = description_part.strip('"\'').strip()[:300] if description_part else conversation_text[:300]

            logger.info(f"Agent summarized ticket - Subject: {subject}")

            return {
                "success": True,
                "subject": subject,
                "description": description,
            }

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Fallback - create a simple summary
            first_msg = conversation_history[0] if conversation_history else "Support Request"
            return {
                "success": False,
                "subject": first_msg[:80] if first_msg else "Support Request",
                "description": f"User reported: {first_msg}" if first_msg else "User requested support",
            }


# Global singleton
orchestrator = AgentOrchestrator()