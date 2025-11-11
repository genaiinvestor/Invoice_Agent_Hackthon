# """Payment Processing Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState
# from agents.payment_agent import PaymentAgent


# async def payment_processing_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass

"""Payment Processing Node"""
 
from state import InvoiceProcessingState
from agents.payment_agent import PaymentAgent
 
 
async def payment_processing_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """
    LangGraph node that executes the PaymentAgent.
    Decides whether to auto-pay, route for approvals, or reject, and
    optionally calls the payment simulation microservice.
    """
    agent = PaymentAgent()
    updated_state = await agent.execute(state)
    return updated_state
