# """Audit Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState
# from agents.audit_agent import AuditAgent


# async def audit_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass



"""Audit Node"""
 
from state import InvoiceProcessingState
from agents.audit_agent import AuditAgent
 
 
async def audit_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """
    LangGraph node that executes the AuditAgent.
    Final step in the workflow — generates audit trail, compliance checks,
    and summary reports for archival and review.
    """
    agent = AuditAgent()
    updated_state = await agent.execute(state)
    return updated_state
 
