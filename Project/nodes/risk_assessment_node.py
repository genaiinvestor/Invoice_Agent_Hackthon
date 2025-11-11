# """Risk Assessment Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState
# from agents.risk_agent import RiskAgent


# async def risk_assessment_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass


"""Risk Assessment Node"""

# Implemented node

from state import InvoiceProcessingState
from agents.risk_agent import RiskAgent


async def risk_assessment_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """
    LangGraph node to execute RiskAgent as part of the workflow.
    """
    agent = RiskAgent()
    updated_state = await agent.execute(state)
    return updated_state
