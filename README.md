# grow_pro

`grow_pro` is a personal growth agent project built as a focused extension on
top of the existing `nanobot` runtime.

The goal is not to rebuild an agent framework. The goal is to show how memory,
context assembly, governed persistence, searchable history, and current-turn
evidence can be added to an existing agent runtime with a clear boundary.

## Current Status

The project is at final V1 state.

Completed:

- `nanobot growth` CLI entrypoint
- normalized `GrowthEvent` contract
- rule-based execution mode selection
- Hermes-style core memory snapshot
- explicit memory candidate extraction
- governed durable memory writes
- searchable history over `history.jsonl`
- thin SQLite FTS history index
- current-turn evidence lane
- growth-specific tests and documentation

Validation:

```text
pytest tests/growth tests/cli/test_commands.py -p no:cacheprovider
94 passed

ruff check nanobot/growth nanobot/cli/commands.py tests/growth tests/cli/test_commands.py
All checks passed
```

## Architecture

The final architecture is:

```text
nanobot runtime
+ Hermes-style memory
+ growth write governance
+ searchable history
+ current-turn evidence lane
```

`nanobot` remains the runtime layer. It still owns:

- agent loop
- runner
- providers
- channels
- sessions
- cron
- file-based memory
- skills
- CLI and API foundation

`nanobot/growth` adds only the growth-specific layer:

- growth event contracts
- execution mode vocabulary
- memory write candidates
- memory write governor
- core memory snapshot service
- stable context assembler
- growth orchestrator
- current-turn evidence loader

This keeps the implementation narrow and explainable.

## Memory Design

The implementation uses a Hermes-style three-layer memory shape.

Working memory:

- implemented by existing `Session.messages`
- scoped to the active session
- not reimplemented under `growth`

Core memory:

- `USER.md`
- `memory/MEMORY.md`
- small, durable, human-readable, auditable

History layer:

- `memory/history.jsonl` as the source of truth
- `memory/history_index.sqlite3` as a thin SQLite FTS index
- lexical fallback when the index is unavailable

Durable memory writes are governed by:

```text
user message
-> memory extractor
-> MemoryWriteCandidate
-> RuleBasedMemoryGovernor
-> USER.md / memory/MEMORY.md
```

This is the main project distinction: memory is not just stored; durable memory
is explicitly modeled, reviewed, and governed before it is persisted.

## Context And Retrieval

This project does not claim to be a full custom RAG platform.

The accurate description is:

```text
retrieval-informed context assembly
```

The final context shape is stable:

```text
[Role & Policies]
[Task]
[State]
[Current Evidence]
[Memory Snapshot]
[Relevant History]
```

Implemented retrieval/context inputs:

- core memory snapshot
- relevant history from `history.jsonl`
- SQLite FTS history search
- current-turn evidence text and files

Not implemented in V1:

- vector-first RAG
- graph memory
- cross-source ranking platform
- perceptual memory
- cross-modal retrieval

## Current-Turn Evidence

The growth CLI supports evidence for the current turn:

```powershell
nanobot growth `
  --message "根据这些材料帮我总结成长风险。" `
  --event-type checkin `
  --evidence-text "本周三次熬夜，第二天专注度明显下降。" `
  --user-id demo-user `
  --session demo-session
```

Evidence behavior:

- inline evidence text enters `[Current Evidence]`
- workspace file evidence is loaded and textualized when possible
- image files are treated as lightweight references
- evidence affects the current turn by default
- evidence is not automatically written into long-term memory
- long-term persistence still requires `MemoryWriteCandidate` and governor approval

## CLI Usage

Show the growth command:

```powershell
nanobot growth --help
```

Explicit preference persistence:

```powershell
nanobot growth `
  --message "以后回答直接一点，少些铺垫。" `
  --event-type user_message `
  --user-id demo-user `
  --session demo-session
```

Blocked task recovery:

```powershell
nanobot growth `
  --message "The task is blocked because the reviewer has not replied." `
  --event-type task_update `
  --status blocked `
  --priority high `
  --user-id demo-user `
  --session demo-session
```

Current-turn evidence:

```powershell
nanobot growth `
  --message "根据这份复盘材料，帮我识别下周最该避免的问题。" `
  --event-type checkin `
  --evidence .\workspace\weekly_review.md `
  --user-id demo-user `
  --session demo-session
```

## Project Structure

Growth-specific implementation:

```text
nanobot/growth
├─ contracts/
│  ├─ context.py
│  ├─ events.py
│  ├─ evidence.py
│  ├─ execution.py
│  ├─ memory.py
│  └─ tasks.py
├─ context/
│  ├─ assembler.py
│  ├─ evidence.py
│  ├─ ranking.py
│  └─ retrievers.py
├─ memory/
│  ├─ extractor.py
│  ├─ governor.py
│  └─ snapshot.py
├─ orchestrator/
│  ├─ interfaces.py
│  └─ service.py
├─ integration/
│  └─ nanobot_runtime.py
├─ domain/
│  └─ models.py
└─ repositories/
   └─ interfaces.py
```

Real user-facing entrypoint:

```text
nanobot/cli/commands.py
```

Growth tests:

```text
tests/growth
├─ test_context_assembler.py
├─ test_contracts.py
├─ test_evidence_loader.py
├─ test_memory_extractor.py
├─ test_memory_governor.py
├─ test_memory_snapshot.py
└─ test_orchestrator.py
```

## Development Setup

Recommended environment:

```text
Python 3.11
Conda env: growpro
```

Install in editable mode:

```powershell
D:\Anaconda\envs\growpro\python.exe -m pip install -e D:\codex\project\grow_pro
```

Install development dependencies:

```powershell
D:\Anaconda\envs\growpro\python.exe -m pip install -e "D:\codex\project\grow_pro[dev]"
```

Verify import source:

```powershell
D:\Anaconda\envs\growpro\python.exe -c "import nanobot; print(nanobot.__file__)"
```

Expected source:

```text
D:\codex\project\grow_pro\nanobot\__init__.py
```

Run tests:

```powershell
D:\Anaconda\envs\growpro\python.exe -m pytest D:\codex\project\grow_pro\tests\growth D:\codex\project\grow_pro\tests\cli\test_commands.py -p no:cacheprovider
```

Run lint:

```powershell
D:\Anaconda\envs\growpro\python.exe -m ruff check D:\codex\project\grow_pro\nanobot\growth D:\codex\project\grow_pro\nanobot\cli\commands.py D:\codex\project\grow_pro\tests\growth D:\codex\project\grow_pro\tests\cli\test_commands.py
```

## Documentation

Recommended reading order:

1. `docs/growth/project-guide.zh-CN.md`
2. `docs/growth/architecture.md`
3. `docs/growth/memory-and-rag.md`
4. `docs/growth/multimodal-evidence.md`
5. `docs/growth/source-map.md`
6. `docs/growth/interview-narrative.md`
7. `docs/growth/demo-walkthrough.md`

## Relationship To nanobot

This repository includes and extends the `nanobot` codebase. The runtime,
provider, channel, session, skill, cron, and base memory systems come from the
underlying nanobot architecture.

The growth-specific contribution lives under `nanobot/growth` and in the
`nanobot growth` CLI path.

In short:

```text
nanobot provides the runtime.
grow_pro adds the growth memory and context layer.
```

## What This Project Is Not

This project is not:

- a new general-purpose agent framework
- a second runtime
- a second skill system
- a workflow platform
- a vector RAG system
- a graph memory system
- a perceptual memory platform
- a multimodal long-term memory system

V1 intentionally stays narrow so the behavior can be run, tested, audited, and
explained.

## License And Attribution

This project is based on the open-source `nanobot` project and keeps the
original license and third-party notices in this repository.

See:

- `LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `docs/growth/project-guide.zh-CN.md`
