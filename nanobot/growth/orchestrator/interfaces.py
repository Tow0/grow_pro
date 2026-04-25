from __future__ import annotations

from typing import Protocol

from nanobot.growth.contracts.context import ContextPacket
from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.execution import ExecutionMode, RuntimeSnapshot


class GrowthOrchestrator(Protocol):
    """Top-level growth entrypoint that decides and executes the next step."""

    async def handle(self, event: GrowthEvent) -> str: ...


class WorkflowSelector(Protocol):
    """Maps an execution mode to a concrete workflow implementation."""

    async def select(self, mode: ExecutionMode): ...


class ContextAssembler(Protocol):
    """Builds structured context without leaking retrieval concerns upward."""

    async def assemble(
        self,
        event: GrowthEvent,
        snapshot: RuntimeSnapshot,
        mode: ExecutionMode,
    ) -> ContextPacket: ...
