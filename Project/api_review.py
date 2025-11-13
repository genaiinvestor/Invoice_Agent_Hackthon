# file: api_review.py
from fastapi import FastAPI, HTTPException
from google.cloud import firestore
from graph import get_workflow

app = FastAPI()
db = firestore.Client()
workflow = get_workflow({})

@app.post("/api/review/submit")
async def submit_review(process_id: str, decision: str, reviewer: str, comments: str = ""):
    doc = db.collection("pending_reviews").document(process_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Pending review not found")

    # Delete pending record
    db.collection("pending_reviews").document(process_id).delete()

    review_input = {"decision": decision, "reviewer": reviewer, "comments": comments}

    # Resume graph execution from paused state
    await workflow.resume(process_id=process_id, node="human_review_node", value=review_input)
    return {"status": "resumed", "process_id": process_id}
