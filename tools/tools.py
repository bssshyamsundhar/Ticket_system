"""Tool implementations for IT support agents - Optimized version"""

import logging
from typing import Dict, Optional
from config import config
from kb.kb_chroma import kb
from db.postgres import db
from services.email_service import email_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_knowledge_base(query: str) -> str:
    """
    Search the semantic knowledge base for solutions to IT issues.
    
    Args:
        query: The user's IT issue or question
        
    Returns:
        Formatted string with search results and confidence score
    """
    try:
        results = kb.search(query, top_k=1)  # Single best result
        
        if not results:
            return "No relevant solutions found in the knowledge base."
        
        result = results[0]
        confidence = result['confidence']
        
        # Format response with confidence indicator
        response = f"Solution found (Confidence: {confidence:.0%}):\n\n"
        response += result['solution']
        
        # Add confidence context
        if confidence >= 0.70:
            response += "\n\n✓ High confidence - this solution should resolve your issue."
        else:
            response += "\n\n⚠ Low confidence - this might not fully address your specific situation."
        
        logger.info(f"KB search for '{query[:50]}...' returned confidence: {confidence:.2%}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return f"Error searching knowledge base. Please try rephrasing your question."


def ask_clarification(question: str) -> str:
    """
    Record that a clarification question was asked.
    This is mainly for tracking purposes.
    
    Args:
        question: The clarifying question being asked
        
    Returns:
        Confirmation message
    """
    logger.info(f"Clarification requested: {question[:100]}")
    return f"Clarification question recorded: {question}"


def preview_escalation_ticket(
    issue_summary: str, 
    refined_query: Optional[str] = None, 
    confidence_score: Optional[float] = None
) -> str:
    """
    Generate a preview of the ticket that will be created.
    Shows the user what the ticket will contain before confirmation.
    
    This is STEP 1 of the escalation process.
    
    Args:
        issue_summary: Summary of the issue
        refined_query: Refined version of the query after clarification
        confidence_score: Confidence score from KB search
        
    Returns:
        Formatted ticket preview text with clear call-to-action
    """
    try:
        # Build comprehensive preview
        preview = "\n" + "═" * 60 + "\n"
        preview += "         ESCALATION TICKET PREVIEW\n"
        preview += "═" * 60 + "\n\n"
        
        preview += "📋 ISSUE SUMMARY:\n"
        preview += f"{issue_summary}\n\n"
        
        if refined_query:
            preview += "🔍 REFINED QUERY:\n"
            preview += f"{refined_query}\n\n"
        
        if confidence_score is not None:
            preview += f"📊 KB CONFIDENCE SCORE: {confidence_score:.0%}\n"
            if confidence_score < 0.70:
                preview += "   (Below 70% threshold - escalation recommended)\n"
            preview += "\n"
        
        preview += "─" * 60 + "\n\n"
        preview += "⚡ WHAT HAPPENS NEXT:\n"
        preview += "• This ticket will be assigned to our support team\n"
        preview += "• You'll receive email updates at your registered address\n"
        preview += "• Average response time: 24 hours\n"
        preview += "• You can track status in the support portal\n\n"
        
        preview += "═" * 60 + "\n"
        preview += "💬 Please review the details above carefully.\n"
        preview += "═" * 60 + "\n"
        
        logger.info(f"Generated ticket preview for issue: {issue_summary[:50]}...")
        
        return preview
        
    except Exception as e:
        logger.error(f"Error generating ticket preview: {e}")
        return (
            "⚠ Error generating ticket preview. "
            "Please contact support@company.com directly if urgent."
        )


def confirm_and_create_escalation_ticket(
    user_id: str, 
    issue_summary: str, 
    user_email: str,
    user_name: str = "User",
    category: str = "Other",
    refined_query: Optional[str] = None, 
    confidence_score: Optional[float] = None,
    attachment_urls: Optional[list[str]] = None
) -> str:
    """
    Create an escalation ticket after user confirmation.
    This tool should ONLY be called after the user confirms "yes" to the preview.
    
    This is STEP 2 of the escalation process.
    
    Args:
        user_id: ID of the user creating the ticket
        issue_summary: Summary of the issue
        user_email: User's email for notification
        user_name: User's name
        category: Ticket category
        refined_query: Refined version of the query after clarification
        confidence_score: Confidence score from KB search
        attachment_urls: List of image URLs attached to the ticket
        
    Returns:
        Formatted confirmation message with ticket ID
    """
    try:
        # Create the ticket in database with correct parameters
        ticket = db.create_ticket(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            category=category,
            subject=issue_summary[:200] if issue_summary else "Support Request",
            description=refined_query or issue_summary or "User requested support",
            attachment_urls=attachment_urls
        )
        
        if ticket:
            ticket_id = ticket['id']
            logger.info(f"✓ Created escalation ticket #{ticket_id} for user {user_id}")
            
            # Send email notification
            try:
                email_service.send_ticket_created(
                    user_email=user_email,
                    user_name=user_name,
                    ticket_id=ticket_id,
                    category=category,
                    subject=issue_summary[:200] if issue_summary else "Support Request",
                    description=refined_query or issue_summary or "User requested support",
                    priority=ticket.get('priority', 'P3')
                )
            except Exception as email_error:
                logger.warning(f"Failed to send ticket creation email: {email_error}")
            
            # Build success confirmation
            confirmation = "\n✓ TICKET CREATED SUCCESSFULLY\n"
            confirmation += "═" * 60 + "\n\n"
            confirmation += f"🎫 **Ticket ID: #{ticket_id}**\n"
            confirmation += f"📧 Confirmation sent to: {user_email}\n\n"
            
            confirmation += "✅ Your support ticket has been created!\n\n"
            
            confirmation += "WHAT'S NEXT:\n"
            confirmation += "• Our support team will review your issue shortly\n"
            confirmation += "• You'll receive email updates on progress\n"
            confirmation += "• Track your ticket in the support portal\n"
            confirmation += f"• Reference Ticket ID #{ticket_id} in communications\n\n"
            
            confirmation += "Thank you for your patience. We're here to help! 💙\n"
            confirmation += "═" * 60 + "\n"
            
            return confirmation
        else:
            logger.error(f"Failed to create ticket for user {user_id}")
            return (
                "❌ Failed to create ticket. "
                "Please try again or email support@company.com directly."
            )
    
    except Exception as e:
        logger.error(f"Error creating escalation ticket: {e}", exc_info=True)
        return (
            f"❌ Error creating ticket: {str(e)}\n\n"
            "Please email support@company.com with your issue and mention "
            "you encountered an error creating a ticket via chat."
        )


def update_knowledge_base(issue: str, solution: str, source: str = "Admin Approved") -> Dict:
    """
    Add a new entry to the knowledge base (admin-approved only).
    
    Args:
        issue: Description of the issue
        solution: Solution to the issue
        source: Source of the solution
        
    Returns:
        Dictionary with result
    """
    try:
        entry_id = kb.add_entry(issue, solution, source)
        
        if entry_id:
            logger.info(f"Added KB entry: {entry_id}")
            return {
                "success": True,
                "entry_id": entry_id,
                "message": "Knowledge base updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update knowledge base"
            }
    
    except Exception as e:
        logger.error(f"Error updating knowledge base: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def get_ticket_details(ticket_id: int) -> Dict:
    """
    Get details of a specific ticket.
    
    Args:
        ticket_id: ID of the ticket
        
    Returns:
        Dictionary with ticket details
    """
    try:
        ticket = db.get_ticket_by_id(ticket_id)
        
        if ticket:
            return {
                "success": True,
                "ticket": dict(ticket)
            }
        else:
            return {
                "success": False,
                "message": f"Ticket #{ticket_id} not found"
            }
    
    except Exception as e:
        logger.error(f"Error getting ticket details: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }