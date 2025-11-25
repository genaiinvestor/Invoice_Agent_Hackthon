
# import json
# from datetime import datetime, timezone

# from state import InvoiceProcessingState, ProcessingStatus, PaymentStatus
# from utils.logger import StructuredLogger

# UTC = timezone.utc

# async def human_review_node(state: InvoiceProcessingState, config=None) -> InvoiceProcessingState:
#     logger = StructuredLogger("HumanReviewNode")
#     state.current_agent = "human_review_node"
#     state.overall_status = ProcessingStatus.IN_PROGRESS

#     if not state.escalation_record:
#         logger.info("No escalation record — skipping.")
#         state.overall_status = ProcessingStatus.COMPLETED
#         return state

#     escalation = state.escalation_record
#     approver = escalation.get("approver", {}).get("name", "Finance Manager")
#     priority = escalation.get("priority", "medium")
#     invoice_number = escalation.get("invoice_number", "N/A")
#     process_id = state.process_id

#     resume_obj = state.resume
#     if resume_obj and resume_obj.get("value"):
#         review_input = resume_obj["value"]
#         print("Review Input .................",review_input)
#         logger.info(f"Resumed human review for {process_id}: {json.dumps(review_input)}")
#     else:
#         review_input = None

#     # ---------------------------------------------------------------------
#     # ⭐ PAUSE BRANCH — MANDATORY FOR CHECKPOINT SAVING
#     # ---------------------------------------------------------------------
#     if not review_input:
#         logger.info(f"Pausing workflow for human review. process_id={process_id}")

#         state.overall_status = ProcessingStatus.PAUSED
#         state.human_review_required = True
#         state.resume = {}
#         db = config.get("db") if config else None

#         pending_doc = {
#             "process_id": process_id,
#             "invoice_number": invoice_number,
#             "priority": priority,
#             "approver": approver,
#             "escalation_id": escalation.get("escalation_id"),
#             "status": "PENDING_REVIEW",
#             "created_at": datetime.now(UTC).isoformat(),
#         }

#         db.collection("pending_reviews").document(process_id).set(pending_doc)
#         logger.info(f"Saved pending review for process_id={process_id}")
#         return state   # ⭐ THIS IS IMPORTANT

     

#     # ---------------------------------------------------------------------
#     # ⭐ FINAL DECISION BRANCH
#     # ---------------------------------------------------------------------
#     decision = review_input.get("decision", "approved").lower()
#     reviewer = review_input.get("reviewer", approver)
#     comments = review_input.get("comments", "")

#     payment_status = PaymentStatus.APPROVED if decision == "approved" else PaymentStatus.REJECTED

#     state.payment_decision = {
#         "payment_status": payment_status.name,
#         "approved_amount": getattr(state.invoice_data, "total", 0.0),
#         "method": "MANUAL_REVIEW",
#         "reviewed_by": reviewer,
#         "review_comments": comments,
#     }

#     logger.info(f"HumanReviewNode Final Decision: {json.dumps(state.payment_decision, indent=2)}")

#     state.log_action(
#         agent_name="human_review_node",
#         action="manual_review",
#         status="completed",
#         details=state.payment_decision,
#         duration_ms=300,
#     )

#     state.overall_status = ProcessingStatus.COMPLETED
#     state.human_review_required = False

#     return state

import json
from datetime import datetime, timezone

from state import InvoiceProcessingState, ProcessingStatus, PaymentStatus
from utils.logger import StructuredLogger

UTC = timezone.utc

async def human_review_node(state: InvoiceProcessingState, config=None) -> InvoiceProcessingState:
    logger = StructuredLogger("HumanReviewNode")
    process_id = state.process_id

    logger.info(f"[HRN] Entered human_review_node for {process_id}")
    logger.info(f"[HRN] Incoming state.resume = {state.resume}")

    # Always tag the current agent
    state.current_agent = "human_review_node"

    # If no escalation record, skip
    if not state.escalation_record:
        logger.info(f"[HRN] No escalation record — marking completed.")
        state.overall_status = ProcessingStatus.COMPLETED
        return state

    # Extract escalation context
    escalation = state.escalation_record
    approver = escalation.get("approver", {}).get("name", "Finance Manager")
    priority = escalation.get("priority", "medium")
    invoice_number = escalation.get("invoice_number", "N/A")

    # Check resume payload
    resume_obj = state.resume
    if resume_obj and isinstance(resume_obj, dict) and resume_obj.get("value"):
        review_input = resume_obj["value"]
        logger.info(f"[HRN] Found resume input: {review_input}")
    else:
        review_input = None
        logger.info("[HRN] No resume input — PAUSING workflow.")

    # ------------------------------------------------------------------
    # ⭐ PAUSE BRANCH — SAVE CHECKPOINT
    # ------------------------------------------------------------------
    if not review_input:
        logger.info(f"[HRN] PAUSING workflow for human review for {process_id}")

        # Save to Firestore (optional)
        db = config.get("db") if config else None
        if db:
            pending_doc = {
                "process_id": process_id,
                "invoice_number": invoice_number,
                "priority": priority,
                "approver": approver,
                "status": "PENDING_REVIEW",
                "created_at": datetime.now(UTC).isoformat(),
            }
            db.collection("pending_reviews").document(process_id).set(pending_doc)
            logger.info(f"[HRN] Firestore pending review saved for {process_id}")

        # Modify the state (return FULL STATE)
        state.overall_status = ProcessingStatus.PAUSED
        state.human_review_required = True
        state.resume = {}              # important
        state.updated_at = datetime.utcnow()

        logger.info(f"[HRN] Returning PAUSED state for checkpoint save: {state.dict()}")
        return state
    
    # ------------------------------------------------------------------
    # ⭐ FINAL DECISION BRANCH
    # ------------------------------------------------------------------
    logger.info(f"[HRN] Processing human decision for {process_id}")

    decision = review_input.get("decision", "approved").lower()
    reviewer = review_input.get("reviewer", approver)
    comments = review_input.get("comments", "")

    payment_status = (
        PaymentStatus.APPROVED if decision == "approved"
        else PaymentStatus.REJECTED
    )

    state.payment_decision = {
        "payment_status": payment_status.name,
        "approved_amount": getattr(state.invoice_data, "total", 0.0),
        "method": "MANUAL_REVIEW",
        "reviewed_by": reviewer,
        "review_comments": comments,
    }

    logger.info(f"[HRN] Final decision stored: {json.dumps(state.payment_decision, indent=2)}")

    state.overall_status = ProcessingStatus.COMPLETED
    state.human_review_required = False
    state.updated_at = datetime.utcnow()

    logger.info(f"[HRN] Returning COMPLETED state for {process_id}")
    return state

