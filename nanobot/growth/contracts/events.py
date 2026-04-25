from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

GrowthEventType = Literal[
    "user_message",
    "checkin",
    "task_update",
    "calendar_event",
    "scheduled_wakeup",
    "weekly_review",
    "external_signal",
]

GrowthEventSource = Literal["chat", "calendar", "todo", "email", "system"]
Priority = Literal["low", "normal", "high"]


class GrowthEvent(BaseModel):
    """Normalized input envelope for every growth workflow entrypoint."""

    id: str
    type: GrowthEventType
    user_id: str = Field(alias="userId")
    session_id: str | None = Field(default=None, alias="sessionId")
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    source: GrowthEventSource
    priority: Priority = "normal"
