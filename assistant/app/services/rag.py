from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.config import Settings
from pypdf import PdfReader

from ..services.llm import LLMService

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
DEFAULT_COLLECTION = "vault"


@dataclass
class DocumentChunk:
    source: str
    content: str


class RAGService:
    def __init__(
        self,
        vault_path: Path | None = None,
        collection_name: str = DEFAULT_COLLECTION,
        llm: LLMService | None = None,
    ) -> None:
        self.vault_path = vault_path or Path(os.getenv("VAULT_PATH", "vault"))
        self.client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_DB_PATH", ".chroma"),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(collection_name)
        self.llm = llm or LLMService()
        self._ensure_index()

    @classmethod
    def depends(cls) -> "RAGService":
        return cls()

    def _ensure_index(self) -> None:
        docs = list(self._iter_documents())
        if not docs:
            return
        existing = set(self.collection.get()["ids"])
        new_docs = [(doc.source, doc) for doc in docs if doc.source not in existing]
        if not new_docs:
            return
        self.collection.add(
            documents=[doc.content for _, doc in new_docs],
            ids=[source for source, _ in new_docs],
            metadatas=[{"source": source} for source, _ in new_docs],
        )

    def _iter_documents(self) -> Iterable[DocumentChunk]:
        if not self.vault_path.exists():
            return []
        for path in self.vault_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            content = self._load_content(path)
            if not content:
                continue
            yield DocumentChunk(source=str(path.relative_to(self.vault_path)), content=content)

    def _load_content(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return path.read_text(encoding="utf-8", errors="ignore")

    def query(self, question: str, top_k: int = 4) -> tuple[str, list[dict[str, str]]]:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        results = self.collection.query(query_texts=[question], n_results=top_k)
        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        documents = documents[0] if documents else []
        metadatas = metadatas[0] if metadatas else []
        if not documents:
            return ("I could not find relevant information in the vault.", [])
        sources = []
        for content, metadata in zip(documents, metadatas):
            if not content:
                continue
            metadata = metadata or {}
            sources.append({"source": metadata.get("source"), "snippet": content[:280]})
        answer = self.llm.answer(question, documents)
        return answer, sources
