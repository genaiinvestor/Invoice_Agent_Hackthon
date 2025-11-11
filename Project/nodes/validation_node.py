# """Validation Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState
# from agents.validation_agent import ValidationAgent


# async def validation_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass


"""Validation Node"""
 
from state import InvoiceProcessingState
from agents.validation_agent import ValidationAgent
 
 
async def validation_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """
    LangGraph node that validates extracted invoice data
    against the purchase orders dataset.
    """
    agent = ValidationAgent()
    updated_state = await agent.execute(state)
    return updated_state
 
