# api_review.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

def create_fastapi_app(workflow, db):
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
        return {
            "ok": True,
            "process_id": req.process_id,
            "payment_status": result_state.payment_decision.get("payment_status"),
            "overall_status": result_state.overall_status.name
        }
        # return {
        #     "ok": True,
        #     "process_id": req.process_id,
        #     "payment_status" = result_state.payment_decision.get("payment_status"),
        #     "overall_status": result_state.overall_status.name
        # }

    return app
