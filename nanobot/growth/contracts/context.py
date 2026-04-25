from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalMeta(BaseModel):
    """Simple counters for understanding how retrieval behaved."""

    candidates: int = 0
    selected: int = 0
    dropped: int = 0


class ContextPacket(BaseModel):
    """Structured context sections assembled before model execution."""

    identity_section: str = ""
    task_section: str = ""
    profile_section: str = ""
    goal_section: str = ""
    recent_state_section: str = ""
    evidence_section: str = ""
    memory_section: str = ""
    history_section: str = ""
    capability_section: str = ""
    policy_section: str = ""
    retrieval_meta: RetrievalMeta = Field(default_factory=RetrievalMeta)
