from __future__ import annotations

from typing import Protocol

from nanobot.growth.domain.models import (
    ActionTask,
    FeedbackEvent,
    GrowthGoal,
    HabitLoop,
    ReflectionNote,
)


class GoalRepository(Protocol):
    async def list_active(self, *, user_id: str) -> list[GrowthGoal]: ...


class HabitRepository(Protocol):
    async def list_active(self, *, user_id: str) -> list[HabitLoop]: ...


class TaskRepository(Protocol):
    async def list_open(self, *, user_id: str) -> list[ActionTask]: ...


class FeedbackRepository(Protocol):
    async def list_recent(self, *, user_id: str, limit: int = 20) -> list[FeedbackEvent]: ...


class ReflectionRepository(Protocol):
    async def list_recent(self, *, user_id: str, limit: int = 10) -> list[ReflectionNote]: ...
