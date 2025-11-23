# """LangGraph workflow orchestrator"""
# # TODO: Implement graph workflow

# import asyncio
# from typing import Dict, Any, List, Optional, Literal
# from datetime import datetime
# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver

# from state import (
#     InvoiceProcessingState, ProcessingStatus, ValidationStatus,
#     RiskLevel, PaymentStatus, WORKFLOW_CONFIGS
# )
# from agents.base_agent import agent_registry
# from agents.document_agent import DocumentAgent
# from agents.validation_agent import ValidationAgent
# from agents.risk_agent import RiskAgent
# from agents.payment_agent import PaymentAgent
# from agents.audit_agent import AuditAgent
# from agents.escalation_agent import EscalationAgent
# from utils.logger import StructuredLogger


# class InvoiceProcessingGraph:
#     """Graph orchestrator"""

#     def __init__(self, config: Dict[str, Any] = None):
#         pass

#     def _initialize_agents(self):
#         pass

#     def _create_workflow_graph(self) -> StateGraph:
#         pass

#     async def _document_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _validation_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _risk_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _payment_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _audit_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _escalation_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _human_review_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     def _route_after_document(self, state: InvoiceProcessingState) -> Literal["validation", "escalation", "end"]:
#         pass

#     def _route_after_validation(self, state: InvoiceProcessingState) -> Literal["risk", "escalation", "end"]:
#         pass

#     def _route_after_risk(self, state: InvoiceProcessingState) -> Literal["payment", "escalation", "human_review", "end"]:
#         pass

#     def _route_after_payment(self, state: InvoiceProcessingState) -> Literal["audit", "escalation", "end"]:
#         pass

#     def _route_after_audit(self, state: InvoiceProcessingState) -> Literal["escalation", "end"]:
#         pass

#     async def process_invoice(self, file_name: str, workflow_type: str = "standard",
#                             config: Dict[str, Any] = None) -> InvoiceProcessingState:
#         pass

#     async def process_batch(self, file_names: List[str], workflow_type: str = "standard",
#                           max_concurrent: int = 5) -> List[InvoiceProcessingState]:
#         pass

#     async def get_workflow_status(self, process_id: str) -> Optional[Dict[str, Any]]:
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass

#     def _extract_final_state(self, result, initial_state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass


# invoice_workflow = None

# def get_workflow(config: Dict[str, Any] = None) -> InvoiceProcessingGraph:
#     pass




"""LangGraph workflow orchestrator"""
 
import asyncio
from typing import Dict, Any, List, Optional, Literal
# from datetime import datetime
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime, timezone
UTC = timezone.utc
from google.cloud import firestore

from nodes.human_review_node import human_review_node
from state import (
    InvoiceProcessingState, ProcessingStatus,
    RiskLevel, PaymentStatus
)
from agents.base_agent import agent_registry
from agents.document_agent import DocumentAgent
from agents.validation_agent import ValidationAgent
from agents.risk_agent import RiskAgent
from agents.payment_agent import PaymentAgent
from agents.audit_agent import AuditAgent
from agents.escalation_agent import EscalationAgent
from utils.logger import StructuredLogger
 
 
class InvoiceProcessingGraph:
    """Main LangGraph-based orchestrator for multi-agent invoice automation"""
 
    def __init__(self, config: Dict[str, Any] = None,db=None):
        self.config = config or {}
        self.logger = StructuredLogger("InvoiceWorkflow")
        self.memory = MemorySaver()
        self._initialize_agents()
        self.workflow_graph = self._create_workflow_graph()
        self.graph = self.workflow_graph
        self.compiled_graph = self.workflow_graph
        self.db = db
 
 
    # ----------------------------------------------------------------------
    # Initialize and register agents
    # ----------------------------------------------------------------------
    def _initialize_agents(self):
        agent_registry.register(DocumentAgent())
        agent_registry.register(ValidationAgent())
        agent_registry.register(RiskAgent())
        agent_registry.register(PaymentAgent())
        agent_registry.register(AuditAgent())
        agent_registry.register(EscalationAgent())
 

    # async def resume(self, process_id: str, value: dict):
    #     self.logger.info(f"[RESUME] Resuming {process_id} with value={value}")

    #     prev = await self.compiled_graph.checkpointer.aget(
    #         {
    #             "configurable": {
    #                 "thread_id": process_id,
    #                 "checkpoint_ns": "invoice_workflow",
    #             }
    #         }
    #     )


    #     if not prev or "state" not in prev:
    #         raise ValueError(f"No saved state found for process_id={process_id}")

    #     prev_state = prev["state"]["values"]  

    #     # Merge updated values
    #     merged_state = {
    #         **prev_state,
    #         "resume": {"value": value},
    #         "human_review_required": False,
    #         "current_agent": "human_review_node",
    #         "overall_status": "in_progress",
    #         "updated_at": datetime.utcnow().isoformat()
    #     }

    #     # Continue workflow
    #     result = await self.workflow_graph.ainvoke(
    #         merged_state,
    #         config={
    #             "configurable": {
    #                 "thread_id": process_id,
    #                 "checkpoint_ns": "invoice_workflow",
    #                 "db": self.db
    #             }
    #         }
    #     )

    #     return self._extract_final_state(result, None)

    async def resume(self, process_id: str, value: dict):
        self.logger.info(f"[RESUME] Resuming {process_id} with value={value}")

        # Load checkpoint
        checkpoint = await self.compiled_graph.checkpointer.aget(
            {"configurable": {
                "thread_id": process_id,
                "checkpoint_ns": "invoice_workflow"
            }}
        )

        if not checkpoint:
            raise ValueError(f"No saved state found for process_id={process_id}")

        saved_state = checkpoint["state"]["values"]

        saved_state["resume"] = {"value": value}
        saved_state["human_review_required"] = False

        result = await self.workflow_graph.ainvoke(
            saved_state,
            config={"configurable": {
                "thread_id": process_id,
                "checkpoint_ns": "invoice_workflow",
                "db": self.db
            }}
        )

        return self._extract_final_state(result, None)


    # ----------------------------------------------------------------------
    # Graph Creation
    # ----------------------------------------------------------------------
    def _create_workflow_graph(self) -> StateGraph:
        graph = StateGraph(InvoiceProcessingState)
 
        # Define nodes
        graph.add_node("document", self._document_agent_node)
        graph.add_node("validation", self._validation_agent_node)
        graph.add_node("risk", self._risk_agent_node)
        graph.add_node("payment", self._payment_agent_node)
        graph.add_node("audit", self._audit_agent_node)
        graph.add_node("escalation", self._escalation_agent_node)
        graph.add_node("human_review", self._human_review_node)
        graph.add_node("end", self._end_node)
        graph.add_edge("escalation", "human_review")
 
 
        # Define routing logic
        graph.add_conditional_edges("document", self._route_after_document)
        graph.add_conditional_edges("validation", self._route_after_validation)
        graph.add_conditional_edges("risk", self._route_after_risk)
        graph.add_conditional_edges("payment", self._route_after_payment)
        graph.add_conditional_edges("audit", self._route_after_audit)
 
        # Define entry and finish points
        graph.set_entry_point("document")
        graph.set_finish_point("end")

 
       
 
      
 
 
        self.logger.log_metric(
            "graph_initialization",
            value=1.0,
            description="Invoice processing workflow graph initialized successfully."
        )
        compiled_graph = graph.compile(checkpointer=self.memory)

        # Use a fixed namespace for all processes
        compiled_graph = compiled_graph.with_config(
            {"configurable": {"checkpoint_ns": "invoice_workflow"}}
        )

        return compiled_graph
 
     
 
    # ----------------------------------------------------------------------
    # Agent execution nodes
    # ----------------------------------------------------------------------
    # async def _document_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await agent_registry.get("document_agent").run(state)
 
    #     # return await agent_registry.get("document_agent").execute(state)
 
    # async def _validation_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await agent_registry.get("validation_agent").run(state)
 
    #     # return await agent_registry.get("validation_agent").execute(state)
 
    # async def _risk_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await agent_registry.get("risk_agent").run(state)
 
    #     # return await agent_registry.get("risk_agent").execute(state)
 
    # async def _payment_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await agent_registry.get("payment_agent").run(state)
 
    #     # return await agent_registry.get("payment_agent").execute(state)
 
    # async def _audit_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await agent_registry.get("audit_agent").run(state)
 
    #     # return await agent_registry.get("audit_agent").execute(state)
 
    # async def _escalation_agent_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await agent_registry.get("escalation_agent").run(state)
 
    #     # #return await agent_registry.get("escalation_agent").execute(state)
 
    # async def _human_review_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     return await human_review_node(state)
 
    # async def _end_node(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     """No-op terminal node used for clean workflow termination."""
    #     return state

    async def _document_agent_node(self, state: InvoiceProcessingState):
        new_state = await agent_registry.get("document_agent").run(state)
        return new_state

    async def _validation_agent_node(self, state: InvoiceProcessingState):
        new_state = await agent_registry.get("validation_agent").run(state)
        return new_state

    async def _risk_agent_node(self, state: InvoiceProcessingState):
        new_state = await agent_registry.get("risk_agent").run(state)
        return new_state

    async def _payment_agent_node(self, state: InvoiceProcessingState):
        new_state = await agent_registry.get("payment_agent").run(state)
        return new_state

    async def _audit_agent_node(self, state: InvoiceProcessingState):
        new_state = await agent_registry.get("audit_agent").run(state)
        return new_state

    async def _escalation_agent_node(self, state: InvoiceProcessingState):
        new_state = await agent_registry.get("escalation_agent").run(state)
        return new_state

    # async def _human_review_node(self, state: InvoiceProcessingState):
    #     new_state = await human_review_node(state)
    #     return new_state

    async def _human_review_node(self, state: InvoiceProcessingState, *, config=None):
        new_state = await human_review_node(state,config={"db": self.db})
        return new_state

    async def _end_node(self, state: InvoiceProcessingState):
        return state.dict()


    # ----------------------------------------------------------------------
    # Conditional routing functions
    # ----------------------------------------------------------------------
    def _route_after_document(self, state: InvoiceProcessingState) -> Literal["validation", "escalation", "end"]:
        if not state.invoice_data:
            self.logger.log_escalation("document_agent", state.process_id, "Document extraction failed.")
            state.escalation_required = True
            return "escalation"
        return "validation"
 
    # def _route_after_validation(self, state: InvoiceProcessingState) -> Literal["risk", "escalation", "end"]:
    #     if not state.validation_result or not state.validation_result.po_found:
    #         self.logger.log_escalation("validation_agent", state.process_id, "PO not found.")
    #         state.escalation_required = True
    #         return "escalation"
    #     return "risk"
 
    def _route_after_validation(self, state: InvoiceProcessingState) -> Literal["risk", "escalation", "end"]:
        """Always run RiskAgent even if PO is missing, so escalation can use risk level."""
        if not state.validation_result or not state.validation_result.po_found:
            self.logger.warning(f"PO not found for {state.process_id}. Proceeding to risk assessment before escalation.")
            state.escalation_required = True  # keep this flag
            return "risk"  # ✅ go to risk first
        return "risk"
 
   
 
 
 
    def _route_after_risk(self, state: InvoiceProcessingState) -> str:
        if not state.risk_assessment:
            self.logger.log_escalation("risk_agent", state.process_id, "Risk assessment missing.")
            return "escalation"
 
        # ✅ Extract value safely for both Enum and string
        raw_level = getattr(state.risk_assessment, "risk_level", "")
        level = (
            raw_level.value
            if hasattr(raw_level, "value")
            else str(raw_level)
        ).lower().replace("risklevel.", "").strip()
 
        # 🚨 High / Critical → escalation
        if level in ("high", "critical"):
            self.logger.log_escalation("risk_agent", state.process_id, f"High risk level: {level}")
            state.escalation_required = True
            return "escalation"
 
        # ✅ Medium / Low → payment
        elif level in ("medium", "low"):
            self.logger.info(f"Routing after RiskAgent: level={level} → next=payment")
            return "payment"
 
        # 🧩 Fallback
        self.logger.warning(f"Routing after RiskAgent: Unknown risk level '{level}', defaulting to end.")
        return "end"
 
 
 
 
    def _route_after_payment(self, state: InvoiceProcessingState) -> Literal["audit", "escalation", "end"]:
        pd = getattr(state, "payment_decision", None)

        # No decision → escalate
        if not pd:
            self.logger.log_escalation("payment_agent", state.process_id, "Missing payment decision.")
            return "escalation"

        # Extract status correctly from dict
        status = pd.get("payment_status")

        # If reviewer rejected → escalate
        if status == "REJECTED" or status == PaymentStatus.REJECTED.name:
            self.logger.log_escalation("payment_agent", state.process_id, "Payment rejected.")
            state.escalation_required = True
            return "escalation"

        # Otherwise move to audit
        return "audit"

 
    # def _route_after_payment(self, state: InvoiceProcessingState) -> Literal["audit", "escalation", "end"]:
    #     if not state.payment_decision:
    #         self.logger.log_escalation("payment_agent", state.process_id, "Missing payment decision.")
    #         return "escalation"
    #     if state.payment_decision.payment_status == PaymentStatus.REJECTED:
    #         self.logger.log_escalation("payment_agent", state.process_id, "Payment rejected.")
    #         state.escalation_required = True
    #         return "escalation"
    #     return "audit"
 
    # def _route_after_audit(self, state: InvoiceProcessingState) -> Literal["escalation", "end"]:
    #     if hasattr(state, "audit_report") and \
    #        state.audit_report.get("compliance", {}).get("overall_status") == "non_compliant":
    #         self.logger.log_escalation("audit_agent", state.process_id, "Non-compliant audit result.")
    #         state.escalation_required = True
    #         return "escalation"
    #     return "end"
 
    def _route_after_audit(self, state: InvoiceProcessingState) -> Literal["escalation", "end","human_review"]:
        """Route after audit based on compliance severity and risk level."""
        if not hasattr(state, "audit_report"):
            return "end"
 
        compliance = state.audit_report.get("compliance", {})
        overall = compliance.get("overall_status", "compliant")
        risk_level = getattr(state.risk_assessment, "risk_level", "low")
        risk_str = str(risk_level).lower()
 
        # 🚨 Escalate only if high-risk AND critical compliance issues
        sox_violations = len(compliance.get("sox", {}).get("violations", []))
        financial_violations = len(compliance.get("financial", {}).get("violations", []))
 
        if overall == "non_compliant" and (sox_violations > 0 or financial_violations > 0):
            if risk_str in ("high", "critical"):
                self.logger.log_escalation("audit_agent", state.process_id, "Critical non-compliance in high-risk invoice.")
                state.escalation_required = True
                return "escalation"
            else:
                self.logger.info(f"Low-risk invoice {state.process_id} has non-critical audit violations — skipping escalation.")
                return "end"
 
        # 🟡 Minor violations (e.g., GDPR, missing logs)
        if overall == "non_compliant":
            gdpr_violations = len(compliance.get("gdpr", {}).get("violations", []))
            trail_violations = len(compliance.get("trail", {}).get("violations", []))
            if gdpr_violations or trail_violations:
                self.logger.info(f"Minor audit non-compliance (GDPR/Trail) detected for {state.process_id}, continuing workflow.")
                return "end"
 # ✅ Handle pending approvals
        payment_decision = getattr(state, "payment_decision", None)
        if payment_decision and payment_decision.payment_status == PaymentStatus.PENDING_APPROVAL:
            self.logger.info(
                f"Routing {state.process_id} to human review for payment approval "
                f"(amount={payment_decision.approved_amount}, risk={risk_str})."
            )
            state.human_review_required = True
            return "human_review"
        return "end"
 
 
    # def _route_after_audit(self, state: InvoiceProcessingState) -> Literal["escalation", "end"]:
    #     if not hasattr(state, "audit_report"):
    #         return "end"
 
    #     compliance = state.audit_report.get("compliance", {})
    #     overall = compliance.get("overall_status", "compliant")
 
    #     if overall == "non_compliant":
    #         gdpr_violations = len(compliance.get("gdpr", {}).get("violations", []))
    #         financial_violations = len(compliance.get("financial", {}).get("violations", []))
    #         sox_violations = len(compliance.get("sox", {}).get("violations", []))
 
    #         # Escalate only for high-severity issues
    #         if financial_violations > 0 or sox_violations > 0:
    #             self.logger.log_escalation("audit_agent", state.process_id, "Critical non-compliance detected.")
    #             state.escalation_required = True
    #             return "escalation"
 
    #         # Skip escalation for minor GDPR or trail warnings
    #         self.logger.info(
    #             f"Minor audit non-compliance (GDPR/Trail) detected for {state.process_id}, continuing workflow."
    #         )
 
    #     return "end"
 
    # ----------------------------------------------------------------------
    # Workflow Execution
    # ----------------------------------------------------------------------
    async def process_invoice(
        self, file_name: str, workflow_type: str = "standard", config: Dict[str, Any] = None
    ) -> InvoiceProcessingState:
        """Run full workflow for a single invoice."""
        # process_id = f"proc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        import uuid
        unique_id = uuid.uuid4().hex[:8]  # unique 8-char identifier
        process_id = f"proc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{unique_id}"
        import streamlit as st
        st.session_state["current_process_id"] = process_id
        print("DEBUG saved current_process_id =", process_id)
        state = InvoiceProcessingState(
            process_id=process_id,
            file_name=file_name,
            overall_status=ProcessingStatus.IN_PROGRESS,
            workflow_type=workflow_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
           # ✅ THEN assign Firestore client to state
     
 
        self.logger.log_workflow_start(workflow_type, process_id, file=file_name)
 
 
        result = await self.workflow_graph.ainvoke(
            state.dict(),
            config={
                "configurable": {
                    "thread_id": process_id,
                    "checkpoint_ns": "invoice_workflow",
                    "db": self.db 
                }
            }
        )
 
 
        final_state = self._extract_final_state(result, state)
        self.logger.log_workflow_complete(workflow_type, process_id, duration_ms=0)
        print(f"✅ Created process_id: {process_id} for {file_name}")
 
        return final_state
 
    async def process_batch(
        self, file_names: List[str], workflow_type: str = "standard", max_concurrent: int = 5
    ) -> List[InvoiceProcessingState]:
        """Run multiple invoices concurrently."""
        results = []
        sem = asyncio.Semaphore(max_concurrent)
 
        async def _run_with_semaphore(f):
            async with sem:
                return await self.process_invoice(f, workflow_type)
 
        tasks = [_run_with_semaphore(f) for f in file_names]
        for coro in asyncio.as_completed(tasks):
            results.append(await coro)
        return results
 
    # ----------------------------------------------------------------------
    # Monitoring & Diagnostics
    # ----------------------------------------------------------------------
    async def get_workflow_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow state snapshot."""
        # ✅ Query using the same keys the checkpointer expects
        # checkpoint = await self.memory.aget_checkpoint(
        #     {"configurable": {"thread_id": process_id, "checkpoint_ns": "invoice_workflow"}}
        # )
        # checkpoint = await self.memory.aget_state(
        #     {
        #         "configurable": {
        #             "thread_id": process_id,
        #             "checkpoint_ns": "invoice_workflow"
        #         }
        #     }
        # )
        checkpoint = await self.memory.aget(
            {
                "configurable": {
                    "thread_id": process_id,
                    "checkpoint_ns": "invoice_workflow"
                }
            }
        )

        return checkpoint if checkpoint else None
 
    async def health_check(self) -> Dict[str, Any]:
        """Aggregate agent and workflow health."""
        agents_health = await agent_registry.health_check_all()
        return {
            "workflow": "InvoiceProcessingGraph",
            "status": "healthy",
            "agents": agents_health,
            "timestamp": datetime.utcnow().isoformat(),
        }
 
    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
 
    # def _extract_final_state(
    #     self, result, initial_state: InvoiceProcessingState
    # ) -> InvoiceProcessingState:
    #     """Ensure we always return a valid InvoiceProcessingState object."""
 
    #     # Handle LangGraph dict result
    #     if isinstance(result, dict):
    #         try:
    #             final_state = InvoiceProcessingState(**result)
    #         except Exception as e:
    #             self.logger.error(f"Failed to reconstruct state: {e}")
    #             final_state = initial_state
    #     else:
    #         final_state = result or initial_state
 
    #     # Ensure all attributes are valid
    #     try:
    #         if not getattr(final_state, "overall_status", None):
    #             final_state.overall_status = ProcessingStatus.COMPLETED
    #         final_state.updated_at = datetime.utcnow()
    #     except Exception as e:
    #         self.logger.error(f"Failed to finalize state: {e}")
    #         # As a fallback, reconstruct if dict
    #         if isinstance(final_state, dict):
    #             final_state = InvoiceProcessingState(**final_state)
    #             final_state.overall_status = ProcessingStatus.COMPLETED
    #             final_state.updated_at = datetime.utcnow()
 
    #     return final_state
 
 
    def _extract_final_state(self, result, initial_state):
        if isinstance(result, dict):
            return InvoiceProcessingState(**result)
        return initial_state




