# firestore_checkpointer.py

import asyncio
from typing import Optional, AsyncIterator

from google.cloud import firestore

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    CheckpointTuple,
    Checkpoint,
    CheckpointMetadata,
)

# OLD VERSIONS USE JsonCheckpointSerde
from langgraph.checkpoint.serde import JsonCheckpointSerde
from langchain_core.runnables import RunnableConfig


class FirestoreCheckpointer(BaseCheckpointSaver):
    """
    Firestore-backed checkpoint saver compatible with older LangGraph versions
    (no `langgraph.serde` module).
    """

    def __init__(
        self,
        *,
        db: firestore.Client | None = None,
        collection_name: str = "langgraph_checkpoints",
        serde=None,
    ) -> None:
        super().__init__(serde=serde or JsonCheckpointSerde())
        self.db = db or firestore.Client()
        self.collection_name = collection_name

    # ------------ internal helpers ------------

    def _coll(self):
        return self.db.collection(self.collection_name)

    def _doc_id(self, thread_id: str, ts: str) -> str:
        return f"{thread_id}:{ts}"

    # ------------ REQUIRED sync methods (LangGraph calls async wrappers) ------------

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        Load a checkpoint. MUST return CheckpointTuple, not raw Python tuple.
        """
        cfg = config.get("configurable", {})
        thread_id = cfg["thread_id"]
        thread_ts = cfg.get("thread_ts")

        coll = self._coll()

        # --- load specific checkpoint
        if thread_ts:
            snap = coll.document(self._doc_id(thread_id, thread_ts)).get()
            if not snap.exists:
                return None

            data = snap.to_dict()
            checkpoint = self.serde.loads(data["checkpoint"])
            metadata = self.serde.loads(data["metadata"])

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
            )

        # --- load latest checkpoint
        query = (
            coll.where("thread_id", "==", thread_id)
                .order_by("ts", direction=firestore.Query.DESCENDING)
                .limit(1)
        )

        docs = list(query.stream())
        if not docs:
            return None

        doc = docs[0].to_dict()
        ts = doc["ts"]

        checkpoint = self.serde.loads(doc["checkpoint"])
        metadata = self.serde.loads(doc["metadata"])

        new_config = {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": ts,
            }
        }

        return CheckpointTuple(
            config=new_config,
            checkpoint=checkpoint,
            metadata=metadata,
        )

    def put(self, config, checkpoint, metadata):
        """
        Save checkpoint to Firestore.
        """
        cfg = config.get("configurable", {})
        thread_id = cfg["thread_id"]
        ts = checkpoint["ts"]

        self._coll().document(self._doc_id(thread_id, ts)).set({
            "thread_id": thread_id,
            "ts": ts,
            "checkpoint": self.serde.dumps(checkpoint),
            "metadata": self.serde.dumps(metadata),
        })

        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": ts,
            }
        }

    def list(self, config, *, before=None, limit=None):
        cfg = config["configurable"]
        thread_id = cfg["thread_id"]

        query = self._coll().where("thread_id", "==", thread_id).order_by(
            "ts", direction=firestore.Query.DESCENDING
        )

        if before:
            query = query.where("ts", "<", before["configurable"]["thread_ts"])

        if limit:
            query = query.limit(limit)

        for snap in query.stream():
            data = snap.to_dict()
            ts = data["ts"]

            yield CheckpointTuple(
                config={"configurable": {"thread_id": thread_id, "thread_ts": ts}},
                checkpoint=self.serde.loads(data["checkpoint"]),
                metadata=self.serde.loads(data["metadata"]),
            )

    # ------------ async wrappers ------------

    async def aget_tuple(self, config):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_tuple, config)

    async def aput(self, config, checkpoint, metadata):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.put, config, checkpoint, metadata)

    async def alist(self, config, *, before=None, limit=None):
        loop = asyncio.get_running_loop()

        def _collect():
            return list(self.list(config, before=before, limit=limit))

        items = await loop.run_in_executor(None, _collect)

        for item in items:
            yield item
