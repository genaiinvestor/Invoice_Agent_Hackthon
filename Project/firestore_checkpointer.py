from google.cloud import firestore
from langgraph.checkpoint.base import BaseCheckpointSaver

class FirestoreCheckpointer(BaseCheckpointSaver):
    def __init__(self, collection_name="lg_checkpoints"):
        self.db = firestore.Client()
        self.collection = self.db.collection(collection_name)

    # async def aget(self, config):
    #     tid = config["configurable"]["thread_id"]
    #     doc = self.collection.document(tid).get()
    #     return doc.to_dict() if doc.exists else None

    async def aget(self, config):
        tid = config["configurable"]["thread_id"]
        doc = self.collection.document(tid).get()

        if not doc.exists:
            return None

        data = doc.to_dict()

        # FIX: ensure correct structure
        if "state" in data and "values" in data["state"]:
            return data

        # Backward compatibility
        return {
            "state": {"values": data},
            "saved_at": None
        }

    # async def aput(self, config, checkpoint):
    #     tid = config["configurable"]["thread_id"]
    #     self.collection.document(tid).set(checkpoint)
    #     return checkpoint

    async def aput(self, config, checkpoint):
        tid = config["configurable"]["thread_id"]

        wrapped = {
            "state": {"values": checkpoint},
            "saved_at": datetime.utcnow().isoformat()
        }

        self.collection.document(tid).set(wrapped)
        return wrapped

    async def alist(self, config):
        return []
