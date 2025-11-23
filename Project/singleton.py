# singleton.py
from graph import InvoiceProcessingGraph
from google.cloud import firestore

_shared_workflow = None
_shared_db = None

def get_shared_db():
    global _shared_db
    if _shared_db is None:
        _shared_db = firestore.Client()
    return _shared_db

def get_shared_workflow():
    global _shared_workflow
    if _shared_workflow is None:
        db = get_shared_db()
        _shared_workflow = InvoiceProcessingGraph(config={}, db=db)
    return _shared_workflow
