from __future__ import annotations

from pathlib import Path

from nanobot.agent.hook import AgentHook
from nanobot.nanobot import Nanobot, RunResult


class NanobotRuntimeAdapter:
    """Minimal wrapper that keeps growth code insulated from nanobot internals."""

    def __init__(self, bot: Nanobot) -> None:
        self._bot = bot

    @classmethod
    def from_config(
        cls,
        config_path: str | Path | None = None,
        *,
        workspace: str | Path | None = None,
    ) -> "NanobotRuntimeAdapter":
        return cls(Nanobot.from_config(config_path=config_path, workspace=workspace))

    @property
    def workspace(self) -> Path:
        return self._bot._loop.workspace

    async def run_text_turn(
        self,
        message: str,
        *,
        session_key: str,
        hooks: list[AgentHook] | None = None,
    ) -> RunResult:
        return await self._bot.run(message, session_key=session_key, hooks=hooks)
