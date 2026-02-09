"""Tool registry for Google ADK - ensures tools are properly registered and executable"""

from typing import Any, Callable, Dict
from tools.tools import (
    search_knowledge_base,
    preview_escalation_ticket,
    confirm_and_create_escalation_ticket
)

# Define tool registry with all available tools
TOOLS_REGISTRY: Dict[str, Callable] = {
    'search_knowledge_base': search_knowledge_base,
    'preview_escalation_ticket': preview_escalation_ticket,
    'confirm_and_create_escalation_ticket': confirm_and_create_escalation_ticket,
}

# Self-service agent tools - only KB search (no clarification questions)
SELF_SERVICE_TOOLS = [search_knowledge_base]
SELF_SERVICE_TOOLS_DICT = {
    'search_knowledge_base': search_knowledge_base,
}

# Escalation agent tools
ESCALATION_TOOLS = [preview_escalation_ticket, confirm_and_create_escalation_ticket]
ESCALATION_TOOLS_DICT = {
    'preview_escalation_ticket': preview_escalation_ticket,
    'confirm_and_create_escalation_ticket': confirm_and_create_escalation_ticket,
}


def get_tool_by_name(tool_name: str) -> Callable:
    """Get a tool function by name"""
    if tool_name not in TOOLS_REGISTRY:
        raise ValueError(f"Tool '{tool_name}' not found in registry")
    return TOOLS_REGISTRY[tool_name]


def execute_tool(tool_name: str, **kwargs) -> Any:
    """Execute a tool by name with the provided arguments"""
    tool_func = get_tool_by_name(tool_name)
    return tool_func(**kwargs)
