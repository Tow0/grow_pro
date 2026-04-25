from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RetrievedItem(BaseModel):
    """Normalized retrieval unit before ranking and compression."""

    source: Literal["structured", "memory", "history", "vector"]
    content: str
    score: float = 0.0
    reference: str | None = None
