# # singleton.py
# from functools import lru_cache
# from graph import InvoiceProcessingGraph
# from google.cloud import firestore

# @lru_cache(maxsize=1)
# def get_shared_db():
#     return firestore.Client()

# @lru_cache(maxsize=1)
# def get_shared_workflow():
#     db = get_shared_db()
#     workflow = InvoiceProcessingGraph(config={}, db=db)
#     return workflow

# singleton.py
from functools import lru_cache
from graph import InvoiceProcessingGraph
from google.cloud import firestore


@lru_cache(maxsize=1)
def get_shared_db():
    return firestore.Client()


@lru_cache(maxsize=1)
def get_shared_workflow():
    db = get_shared_db()
    # DO NOT pass unhashable dicts into cached functions
    workflow = InvoiceProcessingGraph(db=db)
    return workflow
