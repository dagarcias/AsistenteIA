from __future__ import annotations

import os
from typing import Iterable, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]


class LLMService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.client: Optional[OpenAI]
        if OpenAI and api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None

    def answer(self, question: str, documents: Iterable[str]) -> str:
        context = "\n---\n".join(documents)
        if not context:
            return "No supporting context was provided."
        if not self.client:
            # Fallback summarisation without external API access
            snippet = context[:500]
            return (
                "(Local) Based on the available notes: \n"
                f"{snippet}\n\nQuestion: {question}\n"
                "Consider reviewing the referenced documents for more detail."
            )
        prompt = (
            "You are a helpful assistant with access to the following notes from the user's vault. "
            "Use them to answer the question."
        )
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}\nAnswer concisely and cite sources if possible.",
            },
        ]
        completion = self.client.chat.completions.create(model=self.model, messages=messages)
        return completion.choices[0].message.content or ""

    @classmethod
    def depends(cls) -> "LLMService":
        return cls()
