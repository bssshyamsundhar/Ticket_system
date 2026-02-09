"""
Google ADK Runner for executing agents with simplified flow
Direct answer from KB -> Escalate to ticket if needed (no clarification questions)
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
    """States for conversation flow - simplified"""
    ACTIVE = "active"
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
        """Initialize a new conversation state - simplified"""
        return {
            "state": ConversationState.ACTIVE,
            "issue_summary": "",
        }

    # ------------------------------------------------------------------
    # SELF SERVICE AGENT - Direct answers, no clarification
    # ------------------------------------------------------------------

    async def run_self_service_agent(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """Run the self-service agent to handle user query - provides direct answers"""

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )

        final_response = ""
        needs_escalation = False
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

        return {
            "success": True,
            "response": final_response,
            "needs_escalation": needs_escalation,
            "escalation_issue": escalation_issue,
            "agent": "self_service",
        }

    # ------------------------------------------------------------------
    # ESCALATION AGENT - Direct ticket creation (no confirmation needed)
    # ------------------------------------------------------------------

    async def run_escalation_and_create_ticket(
        self,
        user_id: str,
        session_id: str,
        issue_summary: str,
        user_email: str,
    ) -> Dict[str, Any]:
        """
        Run escalation agent to create ticket directly.
        No confirmation step - creates ticket immediately.
        """

        escalation_prompt = f"""
Create a support ticket immediately for this IT support issue.

ESCALATION CONTEXT:
- User ID: {user_id}
- User Email: {user_email}
- Issue Summary: {issue_summary}

YOUR TASK:
1. Call preview_escalation_ticket to generate the preview
2. IMMEDIATELY call confirm_and_create_escalation_ticket to create the ticket
3. Show the user the confirmation with the Ticket ID

DO NOT wait for user confirmation - create the ticket now.
"""

        content = types.Content(
            role="user",
            parts=[types.Part(text=escalation_prompt)],
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
            "ticket_id": ticket_id,
            "ticket_created": ticket_id is not None,
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
        Main entry point for handling user queries - simplified flow.
        
        Flow:
        1. Run self-service agent to provide direct answer
        2. If agent requests escalation -> create ticket immediately
        
        No clarification questions - direct answers only.
        
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

        logger.info(f"Handling query for user {user_id}")

        # ------------------------------------------------------------------
        # Run Self-Service Agent - Get direct answer
        # ------------------------------------------------------------------
        result = await self.run_self_service_agent(
            user_id=user_id_str,
            session_id=adk_session_id,
            user_message=message,
        )

        response_text = result["response"]

        # ------------------------------------------------------------------
        # Check if Agent Requested Escalation -> Create ticket immediately
        # ------------------------------------------------------------------
        if result["needs_escalation"]:
            issue_summary = result.get("escalation_issue", message)

            logger.info(f"Self-service agent requested escalation for user {user_id}")

            # Create ticket immediately (no confirmation needed)
            escalation_result = await self.run_escalation_and_create_ticket(
                user_id=user_id_str,
                session_id=adk_session_id,
                issue_summary=issue_summary,
                user_email=user_email,
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
                ticket_id=escalation_result.get("ticket_id"),
            )

            # Update state
            conversation_state["state"] = ConversationState.ESCALATED
            conversation_state["issue_summary"] = issue_summary

            combined_response = response_text + "\n\n" + escalation_result["response"]

            return {
                "success": True,
                "response": combined_response,
                "agent": "escalation",
                "ticket_id": escalation_result.get("ticket_id"),
                "escalated": True,
                "conversation_state": conversation_state,
            }

        # ------------------------------------------------------------------
        # Normal response - save and return
        # ------------------------------------------------------------------
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