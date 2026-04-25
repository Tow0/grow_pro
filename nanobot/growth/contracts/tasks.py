from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel

TaskState = Literal[
    "created",
    "queued",
    "running",
    "completed",
    "failed",
    "skipped",
    "canceled",
    "rescheduled",
]


class ScheduledTaskRecord(BaseModel):
    """Minimal task envelope for orchestration and follow-up scheduling."""

    id: str
    kind: str
    status: TaskState
    related_goal_id: str | None = None
    related_habit_id: str | None = None


class TaskStateMachine:
    """Explicit transition rules for scheduled task lifecycle."""

    _ALLOWED_TRANSITIONS: ClassVar[dict[TaskState, set[TaskState]]] = {
        "created": {"queued", "canceled"},
        "queued": {"running", "skipped", "canceled", "rescheduled"},
        "running": {"completed", "failed", "skipped", "canceled", "rescheduled"},
        "failed": {"queued", "canceled", "rescheduled"},
        "skipped": {"queued", "canceled"},
        "rescheduled": {"queued", "canceled"},
        "completed": set(),
        "canceled": set(),
    }

    @classmethod
    def can_transition(cls, current: TaskState, target: TaskState) -> bool:
        return target in cls._ALLOWED_TRANSITIONS[current]

    @classmethod
    def assert_transition(cls, current: TaskState, target: TaskState) -> None:
        if not cls.can_transition(current, target):
            raise ValueError(f"Invalid task transition: {current} -> {target}")
