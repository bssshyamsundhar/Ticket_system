"""Agent initialization module"""

from agents.self_service.agent import create_self_service_agent
from agents.escalation.agent import create_escalation_agent

__all__ = ['create_self_service_agent', 'create_escalation_agent']