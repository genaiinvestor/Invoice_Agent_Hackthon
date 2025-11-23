# api_review.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# def create_fastapi_app(workflow, db):
from singleton import get_shared_workflow

def create_fastapi_app(db):
    workflow = get_shared_workflow()

    app = FastAPI()

    class ReviewRequest(BaseModel):
        process_id: str
        decision: str
        reviewer: str
        comments: str = ""

    @app.post("/api/review/submit")
    async def submit_review(req: ReviewRequest):

        doc = db.collection("pending_reviews").document(req.process_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Pending review not found")

        db.collection("pending_reviews").document(req.process_id).delete()

        review_input = {
            "decision": req.decision,
            "reviewer": req.reviewer,
            "comments": req.comments,
        }

        # ⭐ FIX: use the SAME shared workflow instance
        # result_state = await workflow.resume(
        #     process_id=req.process_id,
        #     input=review_input
        # )
        result_state = await workflow.resume(
            process_id=req.process_id,
            value=review_input
        )
        pd = result_state.payment_decision or {}
        payment_status = pd.get("payment_status", "UNKNOWN")

        overall_status = (
            result_state.overall_status.name
            if hasattr(result_state.overall_status, "name")
            else str(result_state.overall_status)
        )

        return {
            "ok": True,
            "process_id": req.process_id,
            "payment_status": payment_status,
            "overall_status": overall_status
        }

        # return {
        #     "ok": True,
        #     "process_id": req.process_id,
        #     "payment_status": result_state.payment_decision.get("payment_status"),
        #     "overall_status": result_state.overall_status.name
        # }
        # return {
        #     "ok": True,
        #     "process_id": req.process_id,
        #     "payment_status" = result_state.payment_decision.get("payment_status"),
        #     "overall_status": result_state.overall_status.name
        # }

    return app
