from langgraph.checkpoint.base import BaseCheckpointSaver
from google.cloud import firestore
import json
import asyncio

class FirestoreCheckpointer(BaseCheckpointSaver):

    def __init__(self, collection="invoice_checkpoints"):
        self.db = firestore.AsyncClient()
        self.collection = self.db.collection(collection)

    # ---------------------------------------------------------------
    # SAVE CHECKPOINT
    # ---------------------------------------------------------------
    async def aput(self, config, checkpoint, metadata=None):
        """
        LangGraph calls aput() whenever a node returns state.
        We must store: v, ts, config
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]

        doc_ref = self.collection.document(f"{checkpoint_ns}_{thread_id}")

        data = {
            "v": checkpoint["values"],   # state dict
            "ts": checkpoint["ts"],      # timestamp
            "config": config,            # config must be saved!
        }

        await doc_ref.set(data)

    # ---------------------------------------------------------------
    # LOAD CHECKPOINT
    # ---------------------------------------------------------------
    async def aget(self, config):
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]

        doc_ref = self.collection.document(f"{checkpoint_ns}_{thread_id}")
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        return doc.to_dict()

    # ---------------------------------------------------------------
    # REQUIRED BY LANGGRAPH 0.2.50
    # ---------------------------------------------------------------
    async def aget_tuple(self, config):
        """
        LangGraph expects (checkpoint_dict, metadata_dict).
        If you do not implement, you get NotImplementedError.
        """
        doc = await self.aget(config)
        if doc is None:
            return (None, None)

        return (doc, {})  # metadata is optional
