# """Document Processing Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState
# from agents.document_agent import DocumentAgent


# async def document_processing_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass


"""Document Processing Node"""
 
from state import InvoiceProcessingState
from agents.document_agent import DocumentAgent
 
 
async def document_processing_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """
    LangGraph node that executes the DocumentAgent.
    Handles PDF extraction and structured AI parsing.
    """
    agent = DocumentAgent()
    updated_state = await agent.execute(state)
    return updated_state
 
