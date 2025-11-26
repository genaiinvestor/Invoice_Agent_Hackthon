# from google.cloud import firestore
# from langgraph.checkpoint.base import BaseCheckpointSaver

# class FirestoreCheckpointer(BaseCheckpointSaver):
#     def __init__(self, collection_name="lg_checkpoints"):
#         self.db = firestore.Client()
#         self.collection = self.db.collection(collection_name)

#     # async def aget(self, config):
#     #     tid = config["configurable"]["thread_id"]
#     #     doc = self.collection.document(tid).get()
#     #     return doc.to_dict() if doc.exists else None

#     async def aget(self, config):
#         tid = config["configurable"]["thread_id"]
#         doc = self.collection.document(tid).get()

#         if not doc.exists:
#             return None

#         data = doc.to_dict()

#         # FIX: ensure correct structure
#         if "state" in data and "values" in data["state"]:
#             return data

#         # Backward compatibility
#         return {
#             "state": {"values": data},
#             "saved_at": None
#         }

#     # async def aput(self, config, checkpoint):
#     #     tid = config["configurable"]["thread_id"]
#     #     self.collection.document(tid).set(checkpoint)
#     #     return checkpoint

#     async def aput(self, config, checkpoint):
#         tid = config["configurable"]["thread_id"]

#         wrapped = {
#             "state": {"values": checkpoint},
#             "saved_at": datetime.utcnow().isoformat()
#         }

#         self.collection.document(tid).set(wrapped)
#         return wrapped

#     async def alist(self, config):
#         return []



from typing import Any, Dict, Optional
from google.cloud import firestore
from langgraph.checkpoint.base import BaseCheckpointSaver

class FirestoreCheckpointer(BaseCheckpointSaver):
    """
    Fully implemented Firestore-based checkpointer.
    Supports all read/write methods required by LangGraph:
    - aget()
    - aput()
    - adelete()
    - aget_tuple()
    - aput_tuple()
    """

    def __init__(self, collection_name: str = "lg_checkpoints"):
        self.db = firestore.AsyncClient()
        self.collection = self.db.collection(collection_name)

    # ---------------------------------------------------------
    # SIMPLE READ
    # ---------------------------------------------------------
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "default")

        doc_ref = self.collection.document(f"{checkpoint_ns}_{thread_id}")
        doc = await doc_ref.get()

        return doc.to_dict() if doc.exists else None

    # ---------------------------------------------------------
    # SIMPLE WRITE
    # ---------------------------------------------------------
    async def aput(self, config: Dict[str, Any], value: Dict[str, Any]):
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "default")

        doc_ref = self.collection.document(f"{checkpoint_ns}_{thread_id}")
        await doc_ref.set(value)

    # ---------------------------------------------------------
    # DELETE CHECKPOINT
    # ---------------------------------------------------------
    async def adelete(self, config: Dict[str, Any]):
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "default")

        await self.collection.document(f"{checkpoint_ns}_{thread_id}").delete()

    # ---------------------------------------------------------
    # TUPLE READ (REQUIRED BY LangGraph)
    # MUST return (value, external_state)
    # ---------------------------------------------------------
    async def aget_tuple(self, config: Dict[str, Any]):
        data = await self.aget(config)
        if not data:
            return None, None

        # LangGraph expects:
        #   state = data["state"]
        #   external_state = data.get("external_state")
        return data.get("state"), data.get("external_state")

    # ---------------------------------------------------------
    # TUPLE WRITE (REQUIRED BY LangGraph)
    # ---------------------------------------------------------
    async def aput_tuple(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        external_state: Dict[str, Any]
    ):
        value = {
            "state": state,
            "external_state": external_state
        }
        await self.aput(config, value)
