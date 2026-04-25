from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

EvidenceKind = Literal["text", "image", "document", "audio", "unknown"]


class EvidenceItem(BaseModel):
    """One current-turn evidence item normalized for growth context assembly."""

    id: str
    source: str
    kind: EvidenceKind
    path: str | None = None
    mime_type: str | None = None
    title: str | None = None
    extracted_text: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
