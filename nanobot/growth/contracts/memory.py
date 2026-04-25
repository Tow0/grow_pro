from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MemoryScope = Literal["user", "goal", "session"]
MemoryType = Literal["fact", "preference", "pattern", "strategy", "warning"]
MemoryProvenance = Literal["explicit_user", "observed", "inferred"]


class MemoryWriteCandidate(BaseModel):
    """Candidate record that must be reviewed before long-term persistence."""

    scope: MemoryScope
    type: MemoryType
    content: str = Field(min_length=1)
    provenance: MemoryProvenance
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
