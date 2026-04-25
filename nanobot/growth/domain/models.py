from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    user_id: str
    timezone: str
    preferences: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class GrowthGoal(BaseModel):
    id: str
    title: str
    category: Literal["career", "fitness", "learning", "writing", "life"]
    status: Literal["active", "paused", "done", "dropped"]
    priority: int = 3
    success_criteria: list[str] = Field(default_factory=list)


class HabitLoop(BaseModel):
    id: str
    title: str
    routine: str
    frequency: str
    recovery_policy_id: str | None = None


class ActionTask(BaseModel):
    id: str
    title: str
    status: Literal["todo", "doing", "done", "blocked", "missed"]
    goal_id: str | None = None
    effort: Literal["tiny", "small", "medium", "large"] = "small"


class CheckinEvent(BaseModel):
    id: str
    result: Literal["done", "partial", "missed"]
    timestamp: datetime
    mood: int | None = None
    energy: int | None = None
    note: str | None = None


class FeedbackEvent(BaseModel):
    id: str
    source: Literal["user", "calendar", "todo", "email", "system"]
    signal_type: str
    content: str
    timestamp: datetime


class ReflectionNote(BaseModel):
    id: str
    period: Literal["daily", "weekly", "monthly"]
    findings: list[str] = Field(default_factory=list)
    strategy_updates: list[str] = Field(default_factory=list)
    next_focus: list[str] = Field(default_factory=list)
