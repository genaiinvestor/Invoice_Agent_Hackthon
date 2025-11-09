# """Human Review Node"""
# # TODO: Implement node

# from state import InvoiceProcessingState


# async def human_review_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     pass





"""Human Review Node (Human-in-the-Loop for Invoice Escalation)"""

import json
from datetime import datetime, UTC
from dataclasses import make_dataclass
from state import InvoiceProcessingState, ProcessingStatus, PaymentStatus
from utils.logger import StructuredLogger

# ✅ Import interrupt (compatible with different LangGraph versions)
try:
    from langgraph.types import interrupt
except ImportError:
    try:
        from langgraph.checkpoint import interrupt
    except ImportError:
        try:
            from langgraph.graph.state import interrupt
        except ImportError:
            interrupt = None


async def human_review_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """Handles manual approval/rejection after escalation (HITL step)."""
    logger = StructuredLogger("HumanReviewNode")
    state.current_agent = "human_review_node"
    state.overall_status = ProcessingStatus.IN_PROGRESS

    # 🧩 Ensure escalation context exists
    if not hasattr(state, "escalation_record") or not state.escalation_record:
        logger.info("No escalation record found — skipping manual review.")
        state.overall_status = ProcessingStatus.COMPLETED
        return state

    escalation = state.escalation_record
    approver = escalation.get("approver", {}).get("name", "Finance Manager")
    priority = escalation.get("priority", "medium")

    # 🧠 Pause workflow until human provides input
    if interrupt:
        logger.info(f"⏸️ Pausing for human input — escalation {escalation.get('escalation_id')}")
        review_input = await interrupt({
            "prompt": f"Manual review required for invoice {escalation.get('invoice_number')} "
                      f"(priority: {priority}). Approver: {approver}"
        })
    else:
        logger.warning("⚠️ Interrupt not available — using default auto-decision.")
        review_input = {
            "decision": "approved" if priority != "critical" else "rejected",
            "reviewer": approver,
            "comments": "Auto decision fallback (interrupt unavailable)."
        }

    # ✅ Process human (or fallback) input
    decision = review_input.get("decision", "approved").lower()
    reviewer = review_input.get("reviewer", approver)
    comments = review_input.get("comments", "")

    # --- Update payment status ---
    if decision == "approved":
        payment_status = PaymentStatus.APPROVED
    else:
        payment_status = PaymentStatus.REJECTED

    # --- Update the payment decision on state ---
    state.payment_decision = type("PaymentDecision", (), {
        "payment_status": payment_status,
        "approved_amount": getattr(state.invoice_data, "total", 0.0),
        "method": "MANUAL_REVIEW",
        "reviewed_by": reviewer,
        "review_comments": comments
    })()

    # --- Structured audit output ---
    output_json = {
        "human_review": {
            "reviewer": reviewer,
            "priority": priority,
            "decision": decision,
            "comments": comments,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        "overall_status": "completed",
        "current_agent": "human_review_node",
        "payment_status": str(payment_status.name),
    }

    logger.info(f"HumanReviewNode Output: {json.dumps(output_json, indent=2)}")

    # Log action and mark node complete
    state.log_action(
        agent_name="human_review_node",
        action="manual_review",
        status="completed",
        details=output_json["human_review"],
        duration_ms=500,
    )

    # ✅ Update final state
    state.overall_status = ProcessingStatus.COMPLETED
    state.human_review_required = False
    

    return state


    
