# firestore_checkpointer.py changed

import asyncio
from typing import Optional, AsyncIterator

from google.cloud import firestore

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    CheckpointTuple,
    Checkpoint,
    CheckpointMetadata,
)
from langgraph.serde.json import JsonSerde
from langchain_core.runnables import RunnableConfig


class FirestoreCheckpointer(BaseCheckpointSaver):
    """
    Firestore-backed checkpoint saver compatible with LangGraph 0.2.50.

    Documents are stored in collection `langgraph_checkpoints` as:

      id = "{thread_id}:{ts}"
      {
        "thread_id": str,
        "ts": str,
        "checkpoint": <bytes>,
        "metadata": <bytes>,
      }
    """

    def __init__(
        self,
        *,
        db: firestore.Client | None = None,
        collection_name: str = "langgraph_checkpoints",
        serde=None,
    ) -> None:
        super().__init__(serde=serde or JsonSerde())
        self.db = db or firestore.Client()
        self.collection_name = collection_name

    # ---------- helpers ----------

    def _coll(self):
        return self.db.collection(self.collection_name)

    def _doc_id(self, thread_id: str, ts: str) -> str:
        return f"{thread_id}:{ts}"

    # ---------- sync methods (LangGraph uses these via async wrappers) ----------

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        Mirror MemorySaver.get_tuple but using Firestore.
        """
        cfg = config.get("configurable", {})
        thread_id: str = cfg["thread_id"]
        thread_ts: Optional[str] = cfg.get("thread_ts")

        coll = self._coll()

        # If specific ts provided → load that checkpoint
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

        # Otherwise → load latest checkpoint for this thread_id
        query = (
            coll.where("thread_id", "==", thread_id)
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        docs = list(query.stream())
        if not docs:
            return None

        doc = docs[0]
        data = doc.to_dict()
        ts = data["ts"]
        checkpoint = self.serde.loads(data["checkpoint"])
        metadata = self.serde.loads(data["metadata"])

        # As in MemorySaver, we return a config that includes thread_ts
        new_config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": ts,
                # we can ignore checkpoint_ns for storage, LangGraph passes it separately
            }
        }

        return CheckpointTuple(
            config=new_config,
            checkpoint=checkpoint,
            metadata=metadata,
        )

    def list(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """
        Sync version used by async wrapper; mirrors MemorySaver.list.
        """
        cfg = config.get("configurable", {})
        thread_id: str = cfg["thread_id"]

        coll = self._coll()
        query = coll.where("thread_id", "==", thread_id).order_by(
            "ts", direction=firestore.Query.DESCENDING
        )

        if before:
            before_ts = before["configurable"]["thread_ts"]
            query = query.where("ts", "<", before_ts)

        if limit:
            query = query.limit(limit)

        for snap in query.stream():
            data = snap.to_dict()
            ts = data["ts"]
            checkpoint = self.serde.loads(data["checkpoint"])
            metadata = self.serde.loads(data["metadata"])

            yield CheckpointTuple(
                config={"configurable": {"thread_id": thread_id, "thread_ts": ts}},
                checkpoint=checkpoint,
                metadata=metadata,
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        """
        Save checkpoint to Firestore and return updated config with thread_ts.
        """
        cfg = config.get("configurable", {})
        thread_id: str = cfg["thread_id"]

        ts = checkpoint["ts"]  # LangGraph sets this
        doc_id = self._doc_id(thread_id, ts)

        self._coll().document(doc_id).set(
            {
                "thread_id": thread_id,
                "ts": ts,
                "checkpoint": self.serde.dumps(checkpoint),
                "metadata": self.serde.dumps(metadata),
            }
        )

        # Return config including thread_ts (again, same as MemorySaver)
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": ts,
            }
        }

    # ---------- async wrappers required by BaseCheckpointSaver ----------

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_tuple, config)

    async def alist(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        loop = asyncio.get_running_loop()

        def _collect():
            return list(self.list(config, before=before, limit=limit))

        items = await loop.run_in_executor(None, _collect)
        for item in items:
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.put, config, checkpoint, metadata)
