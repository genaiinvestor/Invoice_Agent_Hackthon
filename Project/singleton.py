# singleton.py
from graph import InvoiceProcessingGraph
from google.cloud import firestore

db = firestore.Client()
workflow = InvoiceProcessingGraph({}, db=db)

def get_shared_workflow():
    return workflow
