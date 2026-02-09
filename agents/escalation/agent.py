"""Escalation Agent using Google ADK - With Ticket Preview & Confirmation"""
from google import adk
from google.adk.planners.built_in_planner import BuiltInPlanner
from google.genai import types
from agents.prompts import ESCALATION_AGENT_INSTRUCTION
from tools.tool_registry import ESCALATION_TOOLS


def create_escalation_agent():
    """
    Create and configure the Escalation Agent.
    
    Agent now has tools to:
    1. Show ticket preview before creation
    2. Create ticket after user confirmation
    
    Returns:
        ADK Agent configured for ticket escalation with confirmation flow
    """
    
    # Define the agent WITH tools for preview and confirmation
    agent = adk.Agent(
        model="gemini-2.5-flash",
        name="escalation_agent",
        instruction=ESCALATION_AGENT_INSTRUCTION,
        tools=ESCALATION_TOOLS,
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False, thinking_budget=0
            )
        )
    )
    
    return agent