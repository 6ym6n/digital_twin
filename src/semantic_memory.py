"""Semantic memory store for the maintenance chatbot.

This is intentionally separate from the pump manual RAG collection.
We store short "memory notes" (facts, preferences, constraints) and
retrieve them with semantic search for future chat requests.

Persistence is handled by ChromaDB in the same persist directory.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma


load_dotenv()


class SemanticMemoryStore:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "semantic_memory",
        embedding_model: str = "models/text-embedding-004",
    ) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables!")

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key,
        )

        # Chroma will create the collection if it doesn't exist.
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def add_memory(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        content = (text or "").strip()
        if not content:
            raise ValueError("Memory text cannot be empty")

        meta = dict(metadata or {})
        meta.setdefault("created_at", datetime.now().astimezone().isoformat())
        meta.setdefault("type", "memory_note")

        ids = None
        if memory_id:
            ids = [str(memory_id)]

        added_ids = self.vector_store.add_texts(texts=[content], metadatas=[meta], ids=ids)
        return {"id": added_ids[0] if added_ids else None, "metadata": meta}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []

        results = self.vector_store.similarity_search_with_score(query=q, k=int(top_k))
        out: List[Dict[str, Any]] = []
        for doc, score in results:
            out.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata or {},
                    "score": float(score),
                }
            )
        return out

    def format_for_prompt(self, items: List[Dict[str, Any]], max_items: int = 5) -> str:
        if not items:
            return ""
        trimmed = items[: max(0, int(max_items))]
        lines = []
        for i, it in enumerate(trimmed, 1):
            content = (it.get("content") or "").strip()
            meta = it.get("metadata") or {}
            tag = meta.get("tag") or meta.get("source") or meta.get("type") or "memory"
            if content:
                lines.append(f"[{i}] ({tag}) {content}")
        return "\n".join(lines).strip()
