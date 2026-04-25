from __future__ import annotations

from typing import Iterable

from nanobot.growth.context.assembler import (
    ContextAssemblyInput,
    HermesStyleContextAssembler,
    render_context_packet,
)
from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.execution import ExecutionMode, ModeSelector, RuntimeSnapshot
from nanobot.growth.contracts.memory import MemoryWriteCandidate
from nanobot.growth.integration.nanobot_runtime import NanobotRuntimeAdapter
from nanobot.growth.memory.extractor import extract_memory_candidates
from nanobot.growth.memory.governor import RuleBasedMemoryGovernor
from nanobot.growth.memory.snapshot import HermesStyleMemoryService


class RuleBasedModeSelector(ModeSelector):
    """Small deterministic mode selector for the first executable path."""

    async def select(
        self,
        event: GrowthEvent,
        snapshot: RuntimeSnapshot,
    ) -> ExecutionMode:
        del snapshot
        if event.type == "weekly_review":
            return "scheduled_review"
        if event.type == "scheduled_wakeup":
            return "recovery"
        if event.type == "checkin":
            return "reflection"
        if event.type == "task_update":
            status = str((event.payload or {}).get("status") or "").lower()
            if status in {"blocked", "missed", "failed"}:
                return "recovery"
            return "planning"
        if event.priority == "high":
            return "planning"
        return "conversational"


class HermesStyleGrowthOrchestrator:
    """First executable growth path built on the final V1 architecture."""

    def __init__(
        self,
        runtime: NanobotRuntimeAdapter,
        *,
        memory_service: HermesStyleMemoryService,
        governor: RuleBasedMemoryGovernor | None = None,
        mode_selector: ModeSelector | None = None,
        context_assembler: HermesStyleContextAssembler | None = None,
    ) -> None:
        self._runtime = runtime
        self._memory_service = memory_service
        self._governor = governor or RuleBasedMemoryGovernor()
        self._mode_selector = mode_selector or RuleBasedModeSelector()
        self._context_assembler = context_assembler or HermesStyleContextAssembler(memory_service)

    async def handle(self, event: GrowthEvent) -> str:
        snapshot = RuntimeSnapshot(
            user_id=event.user_id,
            session_id=event.session_id,
        )
        mode = await self._mode_selector.select(event, snapshot)
        for candidate in self._derive_memory_candidates(event):
            if self._governor.approve(candidate):
                self._memory_service.persist_candidate(candidate)

        context = await self._context_assembler.assemble(
            ContextAssemblyInput(event=event, snapshot=snapshot, mode=mode)
        )
        prompt = render_context_packet(context)
        result = await self._runtime.run_text_turn(
            prompt,
            session_key=self._session_key(event),
        )
        return result.content

    def _derive_memory_candidates(self, event: GrowthEvent) -> list[MemoryWriteCandidate]:
        payload = event.payload or {}
        candidates: list[MemoryWriteCandidate] = []
        raw_candidates = payload.get("memory_candidates")
        if isinstance(raw_candidates, list):
            for item in raw_candidates:
                if isinstance(item, dict):
                    candidates.append(MemoryWriteCandidate.model_validate(item))

        remember = payload.get("remember")
        if isinstance(remember, str) and remember.strip():
            candidates.append(self._explicit_preference_candidate(remember.strip()))
        elif isinstance(remember, list):
            for item in remember:
                if isinstance(item, str) and item.strip():
                    candidates.append(self._explicit_preference_candidate(item.strip()))

        if not candidates:
            candidates.extend(extract_memory_candidates(event))

        return _dedupe_candidates(candidates)

    @staticmethod
    def _explicit_preference_candidate(content: str) -> MemoryWriteCandidate:
        return MemoryWriteCandidate(
            scope="user",
            type="preference",
            content=content,
            provenance="explicit_user",
            confidence=1.0,
            reason="User explicitly asked the assistant to remember this.",
        )

    @staticmethod
    def _session_key(event: GrowthEvent) -> str:
        suffix = event.session_id or "default"
        return f"growth:{event.user_id}:{suffix}"


def _dedupe_candidates(
    candidates: Iterable[MemoryWriteCandidate],
) -> list[MemoryWriteCandidate]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[MemoryWriteCandidate] = []
    for candidate in candidates:
        key = (
            candidate.scope,
            candidate.type,
            candidate.content.strip().casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique
