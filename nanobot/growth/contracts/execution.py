from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import BaseModel, Field

ExecutionMode = Literal[
    "conversational",
    "planning",
    "reflection",
    "recovery",
    "scheduled_review",
]


class RuntimeSnapshot(BaseModel):
    """Small, query-friendly runtime view used by selectors and assemblers."""

    user_id: str
    session_id: str | None = None
    active_goal_ids: list[str] = Field(default_factory=list)
    active_habit_ids: list[str] = Field(default_factory=list)
    open_task_ids: list[str] = Field(default_factory=list)
    recent_feedback_ids: list[str] = Field(default_factory=list)


class ModeSelector(Protocol):
    """Decides which execution mode should handle the current event."""

    async def select(
        self,
        event: GrowthEvent,
        snapshot: RuntimeSnapshot,
    ) -> ExecutionMode: ...


if TYPE_CHECKING:
    from nanobot.growth.contracts.events import GrowthEvent
