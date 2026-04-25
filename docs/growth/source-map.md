# growth Source Map

This document is the fastest way to understand where the final V1 behavior
lives in code.

## Read This First

If you only have a few minutes, read in this order:

1. `docs/growth/architecture.md`
2. `docs/growth/memory-and-rag.md`
3. `nanobot/growth/orchestrator/service.py`
4. `nanobot/growth/memory/snapshot.py`
5. `nanobot/growth/context/assembler.py`
6. `nanobot/cli/commands.py` (`growth` command)

That is the shortest path from architecture to executable behavior.

## Runtime Boundary

These files are the core runtime and are reused rather than replaced:

- `nanobot/nanobot.py`
- `nanobot/agent/loop.py`
- `nanobot/agent/runner.py`
- `nanobot/agent/context.py`
- `nanobot/agent/memory.py`
- `nanobot/session/manager.py`
- `nanobot/cli/commands.py`

What they mean:

- `nanobot/nanobot.py`
  This is the small programmatic facade over `AgentLoop`.
- `nanobot/agent/loop.py`
  This is the main runtime loop and direct processing path.
- `nanobot/agent/context.py`
  This is where the base runtime still injects memory and media into prompts.
- `nanobot/agent/memory.py`
  This is the underlying file-based memory implementation used by growth.

## Growth Contracts

These files define the stable growth-facing shapes:

- `nanobot/growth/contracts/events.py`
- `nanobot/growth/contracts/execution.py`
- `nanobot/growth/contracts/memory.py`
- `nanobot/growth/contracts/context.py`
- `nanobot/growth/contracts/evidence.py`
- `nanobot/growth/contracts/tasks.py`

What they mean:

- `events.py`
  Defines `GrowthEvent`, the normalized entry envelope.
- `execution.py`
  Defines `ExecutionMode` and `RuntimeSnapshot`.
- `memory.py`
  Defines `MemoryWriteCandidate`, the boundary before long-term persistence.
- `context.py`
  Defines `ContextPacket`, the final sectioned context bundle.
- `evidence.py`
  Defines `EvidenceItem`, the current-turn evidence contract.

## Growth Memory

These files define the growth-specific memory behavior:

- `nanobot/growth/memory/governor.py`
- `nanobot/growth/memory/extractor.py`
- `nanobot/growth/memory/snapshot.py`

What they mean:

- `governor.py`
  Implements `RuleBasedMemoryGovernor`. This is the main safety and
  explainability boundary.
- `extractor.py`
  Implements a thin explicit-user extractor for `user_message`.
- `snapshot.py`
  Implements `HermesStyleMemoryService`, core memory snapshot building,
  relevant history retrieval, SQLite FTS indexing, and candidate persistence.

## Growth Context

These files define how growth context is assembled:

- `nanobot/growth/context/assembler.py`
- `nanobot/growth/context/evidence.py`
- `nanobot/growth/context/retrievers.py`
- `nanobot/growth/context/ranking.py`

What they mean:

- `assembler.py`
  Builds the stable prompt shape:
  `[Role & Policies]`, `[Task]`, `[State]`, `[Current Evidence]`,
  `[Memory Snapshot]`, `[Relevant History]`
- `evidence.py`
  Loads current-turn evidence from inline text and workspace files.
- `retrievers.py` / `ranking.py`
  These are still mostly interface-level placeholders for future retrieval
  expansion. They are not the main production path yet.

## Growth Orchestration

These files define the current executable growth path:

- `nanobot/growth/orchestrator/service.py`
- `nanobot/growth/integration/nanobot_runtime.py`

What they mean:

- `service.py`
  This is the main file to read if you want to understand the final V1 flow.
  It handles:
  - mode selection
  - memory candidate derivation
  - governance
  - context assembly
  - runtime call
- `nanobot_runtime.py`
  Keeps growth code insulated from direct `nanobot` runtime internals.

## CLI Entry

The real user-facing entrypoint is:

- `nanobot/cli/commands.py`

Read the `growth(...)` command if you want to see how the project is exercised
from the outside.

It currently supports:

- `--message`
- `--event-type`
- `--user-id`
- `--session`
- `--source`
- `--priority`
- `--status`
- `--result`
- `--mood`
- `--energy`
- `--remember`
- `--evidence`
- `--evidence-text`

## Tests That Matter Most

If you want the smallest high-signal test reading order:

1. `tests/growth/test_orchestrator.py`
2. `tests/growth/test_memory_snapshot.py`
3. `tests/growth/test_memory_extractor.py`
4. `tests/growth/test_context_assembler.py`
5. `tests/cli/test_commands.py` (only the `growth` command cases)

What they prove:

- `test_orchestrator.py`
  The growth path really executes end to end.
- `test_memory_snapshot.py`
  Core memory and searchable history behave as expected.
- `test_memory_extractor.py`
  Explicit-user extraction is intentionally narrow and high precision.
- `test_context_assembler.py`
  The final prompt shape is stable.
- `test_commands.py`
  The real CLI entrypoint builds correct `GrowthEvent` payloads.

## Actual V1 Control Flow

The real production slice is:

1. `nanobot growth ...`
2. CLI builds `GrowthEvent`
3. `HermesStyleGrowthOrchestrator.handle(...)`
4. `RuleBasedModeSelector.select(...)`
5. derive `MemoryWriteCandidate` values
6. `RuleBasedMemoryGovernor`
7. `HermesStyleMemoryService.persist_candidate(...)`
8. `HermesStyleContextAssembler.assemble(...)`
9. `NanobotRuntimeAdapter.run_text_turn(...)`
10. `nanobot` runtime handles the model turn

## Things That Are Still Mostly Explanatory, Not Production-Heavy

These should not be over-sold:

- `nanobot/growth/context/retrievers.py`
- `nanobot/growth/context/ranking.py`
- `nanobot/growth/repositories/interfaces.py`
- `nanobot/growth/domain/models.py`

These files help define the architecture boundary and future direction, but the
final V1 behavior today is concentrated in:

- contracts
- memory
- context assembly
- orchestrator
- CLI

## Best Reading Strategy For Interviews

If asked to explain the codebase live, use this sequence:

1. Show the final architecture docs.
2. Show the `growth` CLI entrypoint.
3. Show `GrowthEvent` and `MemoryWriteCandidate`.
4. Show `RuleBasedMemoryGovernor`.
5. Show `HermesStyleMemoryService`.
6. Show `HermesStyleContextAssembler`.
7. Show `HermesStyleGrowthOrchestrator`.

That keeps the story narrow, concrete, and defensible.
