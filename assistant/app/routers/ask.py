from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from ..services.rag import RAGService

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    top_k: int | None = 4


@router.post("/", response_model=dict[str, object])
def ask_question(payload: AskRequest, rag: RAGService = Depends(RAGService.depends)) -> dict[str, object]:
    answer, sources = rag.query(payload.question, top_k=payload.top_k or 4)
    return {
        "question": payload.question,
        "answer": answer,
        "sources": sources,
    }
