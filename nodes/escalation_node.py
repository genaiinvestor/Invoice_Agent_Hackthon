# """Escalation Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState
# from agents.escalation_agent import EscalationAgent


# async def escalation_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass


"""Escalation Node"""

from state import InvoiceProcessingState
from agents.escalation_agent import EscalationAgent


async def escalation_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """
    LangGraph node for handling escalation routing and notification logic.
    If SLA triggers or high risk is detected, routes to the proper approver.
    """
    agent = EscalationAgent()
    updated_state = await agent.execute(state)
    return updated_state
