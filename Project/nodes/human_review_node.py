# import json
# from datetime import datetime, timezone

# from state import InvoiceProcessingState, ProcessingStatus, PaymentStatus
# from utils.logger import StructuredLogger

# UTC = timezone.utc

# # LangGraph interrupt (import if available)
# try:
#     from langgraph.prebuilt import interrupt
# except:
#     interrupt = None


# async def human_review_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
#     """Handles manual approval/rejection after escalation (HITL step)."""

#     logger = StructuredLogger("HumanReviewNode")
#     state.current_agent = "human_review_node"
#     state.overall_status = ProcessingStatus.IN_PROGRESS

#     # ---------------------------------------------------------
#     # 1️⃣ Skip if no escalation record
#     # ---------------------------------------------------------
#     if not hasattr(state, "escalation_record") or not state.escalation_record:
#         logger.info("No escalation record found — skipping manual review.")
#         state.overall_status = ProcessingStatus.COMPLETED
#         return state

#     escalation = state.escalation_record

#     approver = escalation.get("approver", {}).get("name", "Finance Manager")
#     priority = escalation.get("priority", "medium")
#     invoice_number = escalation.get("invoice_number", "N/A")
#     process_id = state.process_id

#     # ---------------------------------------------------------
#     # 2️⃣ Handle resume() from FastAPI / Streamlit
#     # ---------------------------------------------------------
#     resume_obj = getattr(state, "resume", None)
#     if resume_obj and resume_obj.value:
#         # ⭐ THIS IS THE APPROVE/REJECT DATA
#         review_input = resume_obj.value

#         logger.info(
#             f"Resumed human review for {process_id} "
#             f"with user decision: {json.dumps(review_input)}"
#         )

#     else:
#         review_input = None

#     # ---------------------------------------------------------
#     # 3️⃣ If no resume_input → try interrupt or fallback
#     # ---------------------------------------------------------
#     if not review_input:
#         if interrupt:
#             # try to pause workflow
#             try:
#                 logger.info(f"⏸️ Pausing for human input via interrupt()")
#                 review_input = await interrupt({
#                     "prompt": f"Manual review required for invoice {invoice_number} (priority: {priority}). Approver: {approver}"
#                 })
#             except RuntimeError:
#                 # running in Cloud Run or background — cannot interrupt
#                 logger.warning("Non-interactive environment — saving pending review to Firestore.")

#                 if state.db:   # if Firestore client injected
#                     pending_doc = {
#                         "process_id": process_id,
#                         "invoice_number": invoice_number,
#                         "priority": priority,
#                         "approver": approver,
#                         "escalation_id": escalation.get("escalation_id"),
#                         "status": "PENDING_REVIEW",
#                         "created_at": datetime.now(UTC).isoformat(),
#                     }
#                     state.db.collection("pending_reviews").document(process_id).set(pending_doc)
#                     logger.info(f"Saved pending review request for process_id={process_id}")

#                 state.overall_status = ProcessingStatus.PAUSED
#                 state.human_review_required = True
#                 return state

#         # else:
#             # auto fallback
#             # logger.warning("Interrupt unavailable — auto-approving non-critical escalation.")
#             # review_input = {
#             #     "decision": "approved" if priority != "critical" else "rejected",
#             #     "reviewer": approver,
#             #     "comments": "Auto decision fallback — no interrupt available.",
#             # }
#         else:
#             logger.warning("Interrupt unavailable — pausing for manual review.")

#             if state.db:
#                 pending_doc = {
#                     "process_id": process_id,
#                     "invoice_number": invoice_number,
#                     "priority": priority,
#                     "approver": approver,
#                     "status": "PENDING_REVIEW",
#                     "created_at": datetime.now(UTC).isoformat(),
#                 }
#                 state.db.collection("pending_reviews").document(process_id).set(pending_doc)

#             state.overall_status = ProcessingStatus.PAUSED
#             state.human_review_required = True
#             return state


#     # ---------------------------------------------------------
#     # 4️⃣ Process final user decision
#     # ---------------------------------------------------------
#     decision = review_input.get("decision", "approved").lower()
#     reviewer = review_input.get("reviewer", approver)
#     comments = review_input.get("comments", "")

#     payment_status = (
#         PaymentStatus.APPROVED if decision == "approved"
#         else PaymentStatus.REJECTED
#     )

#     # ---------------------------------------------------------
#     # 5️⃣ Update state with review outcome
#     # ---------------------------------------------------------
#     # state.payment_decision = type("PaymentDecision", (), {
#     #     "payment_status": payment_status,
#     #     "approved_amount": getattr(state.invoice_data, "total", 0.0),
#     #     "method": "MANUAL_REVIEW",
#     #     "reviewed_by": reviewer,
#     #     "review_comments": comments,
#     # })()

#     state.payment_decision = {
#         "payment_status": payment_status.name if hasattr(payment_status, "name") else str(payment_status),
#         "approved_amount": getattr(state.invoice_data, "total", 0.0),
#         "method": "MANUAL_REVIEW",
#         "reviewed_by": reviewer,
#         "review_comments": comments,
#     }

#     output_json = {
#         "human_review": {
#             "reviewer": reviewer,
#             "priority": priority,
#             "decision": decision,
#             "comments": comments,
#             "timestamp": datetime.now(UTC).isoformat(),
#         },
#         "overall_status": "completed",
#         "current_agent": "human_review_node",
#         "payment_status": payment_status.name,
#     }

#     logger.info(f"HumanReviewNode Output: {json.dumps(output_json, indent=2)}")

#     # ---------------------------------------------------------
#     # 6️⃣ Log audit trail
#     # ---------------------------------------------------------
#     state.log_action(
#         agent_name="human_review_node",
#         action="manual_review",
#         status="completed",
#         details=output_json["human_review"],
#         duration_ms=300,
#     )

#     # ---------------------------------------------------------
#     # 7️⃣ Finalize workflow
#     # ---------------------------------------------------------
#     state.overall_status = ProcessingStatus.COMPLETED
#     state.human_review_required = False

#     return state

import json
from datetime import datetime, timezone

from state import InvoiceProcessingState, ProcessingStatus, PaymentStatus
from utils.logger import StructuredLogger

UTC = timezone.utc

# LangGraph interrupt (import if available)
try:
    from langgraph.prebuilt import interrupt
except:
    interrupt = None


async def human_review_node(state: InvoiceProcessingState) -> InvoiceProcessingState:
    """Handles manual approval/rejection after escalation (HITL step)."""

    logger = StructuredLogger("HumanReviewNode")
    state.current_agent = "human_review_node"
    state.overall_status = ProcessingStatus.IN_PROGRESS

    # ---------------------------------------------------------
    # 1️⃣ Skip if no escalation record
    # ---------------------------------------------------------
    if not state.escalation_record:
        logger.info("No escalation record found — skipping manual review.")
        state.overall_status = ProcessingStatus.COMPLETED
        return state

    escalation = state.escalation_record
    approver = escalation.get("approver", {}).get("name", "Finance Manager")
    priority = escalation.get("priority", "medium")
    invoice_number = escalation.get("invoice_number", "N/A")
    process_id = state.process_id

    # ---------------------------------------------------------
    # 2️⃣ If workflow resumed (Approve/Reject) → use that
    # ---------------------------------------------------------
    resume_obj = getattr(state, "resume", None)
    if resume_obj and resume_obj.value:
        review_input = resume_obj.value
        logger.info(f"Resumed human review for {process_id}: {json.dumps(review_input)}")

    else:
        review_input = None

    # ---------------------------------------------------------
    # 3️⃣ Pause workflow & write pending review to Firestore
    # ---------------------------------------------------------
    if not review_input:

        # ---- Try interrupt() if available (local testing) ----
        if interrupt:
            try:
                logger.info("⏸️ interrupt() available — pausing workflow")
                review_input = await interrupt({
                    "prompt": f"Manual review required for invoice {invoice_number}, priority={priority}"
                })
            except RuntimeError:
                pass  # fall through to Firestore pause

        # ---- ALWAYS save pending review to Firestore ----
        logger.warning("Pausing for manual human review (Firestore).")

        # if state.db:
        #     pending_doc = {
        #         "process_id": process_id,
        #         "invoice_number": invoice_number,
        #         "priority": priority,
        #         "approver": approver,
        #         "escalation_id": escalation.get("escalation_id"),
        #         "status": "PENDING_REVIEW",
        #         "created_at": datetime.now(UTC).isoformat(),
        #     }
        #     state.db.collection("pending_reviews").document(process_id).set(pending_doc)
        #     logger.info(f"Saved pending review request for process_id={process_id}")
            from google.cloud import firestore
            db = firestore.Client()

            pending_doc = {
                "process_id": process_id,
                "invoice_number": invoice_number,
                "priority": priority,
                "approver": approver,
                "escalation_id": escalation.get("escalation_id"),
                "status": "PENDING_REVIEW",
                "created_at": datetime.now(UTC).isoformat(),
            }

            db.collection("pending_reviews").document(process_id).set(pending_doc)
            logger.info(f"Saved pending review request for process_id={process_id}")

        # ---- Finish pause ----
        state.overall_status = ProcessingStatus.PAUSED
        state.human_review_required = True
        return state

    # ---------------------------------------------------------
    # 4️⃣ Process APPROVE / REJECT decision
    # ---------------------------------------------------------
    decision = review_input.get("decision", "approved").lower()
    reviewer = review_input.get("reviewer", approver)
    comments = review_input.get("comments", "")

    payment_status = PaymentStatus.APPROVED if decision == "approved" else PaymentStatus.REJECTED

    # ---------------------------------------------------------
    # 5️⃣ Prepare JSON-safe payment_decision
    # ---------------------------------------------------------
    state.payment_decision = {
        "payment_status": payment_status.name,
        "approved_amount": getattr(state.invoice_data, "total", 0.0),
        "method": "MANUAL_REVIEW",
        "reviewed_by": reviewer,
        "review_comments": comments,
    }

    logger.info(
        f"HumanReviewNode Final Decision: {json.dumps(state.payment_decision, indent=2)}"
    )

    # ---------------------------------------------------------
    # 6️⃣ Add audit trail entry
    # ---------------------------------------------------------
    state.log_action(
        agent_name="human_review_node",
        action="manual_review",
        status="completed",
        details=state.payment_decision,
        duration_ms=300,
    )

    # ---------------------------------------------------------
    # 7️⃣ Finalize workflow
    # ---------------------------------------------------------
    state.overall_status = ProcessingStatus.COMPLETED
    state.human_review_required = False

    return state
    # return state.dict()
