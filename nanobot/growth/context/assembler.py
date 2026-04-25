from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from nanobot.growth.context.evidence import load_evidence_items, render_evidence_section
from nanobot.growth.contracts.context import ContextPacket
from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.execution import ExecutionMode, RuntimeSnapshot
from nanobot.growth.memory.snapshot import HermesStyleMemoryService


class ContextAssemblyInput(BaseModel):
    """Single object passed into context assembly to keep call sites small."""

    event: GrowthEvent
    snapshot: RuntimeSnapshot
    mode: ExecutionMode


class GrowthContextAssembler(Protocol):
    """Growth-facing context assembly contract."""

    async def assemble(self, input: ContextAssemblyInput) -> ContextPacket: ...


class HermesStyleContextAssembler:
    """Assemble a small, stable context packet from core memory and history."""

    def __init__(self, memory_service: HermesStyleMemoryService) -> None:
        self._memory_service = memory_service

    async def assemble(self, input: ContextAssemblyInput) -> ContextPacket:
        event_text = extract_event_text(input.event)
        snapshot = self._memory_service.build_snapshot(event_text)
        evidence_items = load_evidence_items(input.event, self._memory_service.store.workspace)

        return ContextPacket(
            identity_section="You are a growth-focused assistant running on the nanobot runtime.",
            task_section=_render_task_section(input.event, input.mode, event_text),
            profile_section=_render_profile_section(input.snapshot),
            goal_section=_render_goal_section(input.snapshot),
            recent_state_section=_render_recent_state_section(input.snapshot),
            evidence_section=render_evidence_section(evidence_items),
            memory_section=snapshot.render_memory_section(),
            history_section=snapshot.render_history_section(),
            capability_section=(
                "Keep long-term memory small. Use the core memory snapshot and only "
                "pull in relevant history when it helps the current turn."
            ),
            policy_section=(
                "Long-term writes must pass the memory governor. Do not treat inferred "
                "content as durable fact."
            ),
            retrieval_meta={
                "candidates": snapshot.history_candidates,
                "selected": len(snapshot.history_hits),
                "dropped": max(snapshot.history_candidates - len(snapshot.history_hits), 0),
            },
        )


def extract_event_text(event: GrowthEvent) -> str:
    payload = event.payload or {}
    for key in ("text", "message", "content", "note", "summary"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{event.type} event from {event.source}"


def render_context_packet(packet: ContextPacket) -> str:
    sections = [
        (
            "Role & Policies",
            _join_nonempty(
                packet.identity_section,
                packet.capability_section,
                packet.policy_section,
            ),
        ),
        ("Task", packet.task_section),
        (
            "State",
            _join_nonempty(
                packet.profile_section,
                packet.goal_section,
                packet.recent_state_section,
            ),
        ),
        ("Current Evidence", packet.evidence_section),
        ("Memory Snapshot", packet.memory_section),
        ("Relevant History", packet.history_section),
    ]
    return "\n\n".join(
        f"[{title}]\n{_default_section(content)}"
        for title, content in sections
    )


def _render_task_section(event: GrowthEvent, mode: ExecutionMode, event_text: str) -> str:
    return "\n".join([
        f"Mode: {mode}",
        f"Event Type: {event.type}",
        f"Priority: {event.priority}",
        f"Source: {event.source}",
        f"Current Input: {event_text}",
    ])


def _render_profile_section(snapshot: RuntimeSnapshot) -> str:
    return "\n".join([
        f"User ID: {snapshot.user_id}",
        f"Session ID: {snapshot.session_id or '(none)'}",
    ])


def _render_goal_section(snapshot: RuntimeSnapshot) -> str:
    if not snapshot.active_goal_ids:
        return ""
    return "Active Goals:\n" + "\n".join(f"- {goal_id}" for goal_id in snapshot.active_goal_ids)


def _render_recent_state_section(snapshot: RuntimeSnapshot) -> str:
    lines: list[str] = []
    if snapshot.active_habit_ids:
        lines.append("Active Habits:")
        lines.extend(f"- {habit_id}" for habit_id in snapshot.active_habit_ids)
    if snapshot.open_task_ids:
        lines.append("Open Tasks:")
        lines.extend(f"- {task_id}" for task_id in snapshot.open_task_ids)
    if snapshot.recent_feedback_ids:
        lines.append("Recent Feedback IDs:")
        lines.extend(f"- {feedback_id}" for feedback_id in snapshot.recent_feedback_ids)
    return "\n".join(lines)


def _join_nonempty(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if part.strip())


def _default_section(text: str) -> str:
    stripped = text.strip()
    return stripped if stripped else "(none)"
