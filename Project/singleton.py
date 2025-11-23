from graph import InvoiceProcessingGraph
from google.cloud import firestore

_shared_workflow = None

def get_shared_workflow():
    global _shared_workflow
    if _shared_workflow is None:
        db = firestore.Client()
        print("⚡ Creating SINGLE shared InvoiceProcessingGraph instance")
        _shared_workflow = InvoiceProcessingGraph({}, db=db)
    return _shared_workflow
