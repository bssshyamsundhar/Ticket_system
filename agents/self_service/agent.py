"""Self-Service Agent using Google ADK"""
from google import adk
from google.adk.planners.built_in_planner import BuiltInPlanner
from google.genai import types
from agents.prompts import SELF_SERVICE_AGENT_INSTRUCTION
from tools.tool_registry import SELF_SERVICE_TOOLS


def create_self_service_agent():
    """
    Create and configure the Self-Service Agent.
    
    Returns:
        ADK Agent configured for self-service support
    """
    
    # Define the agent with tools
    agent = adk.Agent(
        model="gemini-2.5-flash",
        name="self_service_agent",
        instruction=SELF_SERVICE_AGENT_INSTRUCTION,
        tools=SELF_SERVICE_TOOLS,
        planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False, thinking_budget=0
        )
        )
    )
    
    return agent