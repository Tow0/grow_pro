# growth Demo Walkthrough

This document is the recommended live demo path for the final V1 project.

## Demo Goal

Show that the project:

- reuses the existing `nanobot` runtime
- adds growth-specific semantics
- governs durable memory writes
- supports searchable history
- supports a current-turn evidence lane

The demo should stay narrow and concrete.

## Demo Order

Run the demo in this order:

1. explicit preference persistence
2. blocked task recovery mode
3. current-turn evidence lane

That sequence tells the strongest story with the least setup.

## Demo 1: Explicit Preference Persistence

Command:

```powershell
nanobot growth `
  --message "以后回答直接一点，少些铺垫。" `
  --event-type user_message `
  --user-id demo-user `
  --session demo-session
```

What to explain:

- the CLI builds a `GrowthEvent`
- the extractor recognizes an explicit durable preference
- the project creates a `MemoryWriteCandidate`
- the governor allows it because the provenance is `explicit_user`
- the preference is persisted into `USER.md` or `memory/MEMORY.md`

What this proves:

- the project is not just chatting
- durable memory writes are governed, not implicit

## Demo 2: Blocked Task Triggers Recovery Mode

Command:

```powershell
nanobot growth `
  --message "The task is blocked because the reviewer has not replied." `
  --event-type task_update `
  --status blocked `
  --priority high `
  --user-id demo-user `
  --session demo-session
```

What to explain:

- this event is not treated like a generic chat turn
- the mode selector maps blocked task updates to `recovery`
- the rest of the path still reuses the same orchestrator, memory, and runtime

What this proves:

- the project has growth-specific execution semantics
- those semantics were added without rebuilding the runtime

## Demo 3: Current-Turn Evidence Lane

Command:

```powershell
nanobot growth `
  --message "根据这份复盘材料，帮我识别下周最该避免的问题。" `
  --event-type checkin `
  --evidence .\workspace\weekly_review.md `
  --user-id demo-user `
  --session demo-session
```

Alternative:

```powershell
nanobot growth `
  --message "根据这些材料帮我总结成长风险。" `
  --event-type checkin `
  --evidence-text "本周三次熬夜，第二天专注度明显下降。" `
  --user-id demo-user `
  --session demo-session
```

What to explain:

- evidence is normalized into `EvidenceItem`
- evidence is placed into `[Current Evidence]`
- evidence affects only the current turn by default
- evidence does not automatically become long-term memory

What this proves:

- the system can use richer current-turn material
- this is not a multimodal memory platform
- long-term persistence still goes through the governor

## Source Files To Show During The Demo

If you need to open code while explaining the demo, show these files:

1. `nanobot/cli/commands.py`
2. `nanobot/growth/contracts/events.py`
3. `nanobot/growth/contracts/memory.py`
4. `nanobot/growth/memory/extractor.py`
5. `nanobot/growth/memory/governor.py`
6. `nanobot/growth/memory/snapshot.py`
7. `nanobot/growth/context/assembler.py`
8. `nanobot/growth/orchestrator/service.py`

## Short Narration Script

Recommended narration:

1. `nanobot` already gave me the runtime.
2. I did not rewrite the loop, tools, sessions, or providers.
3. I added a narrow growth layer with domain events, governed memory writes,
   stable context assembly, and an evidence lane.
4. The key idea is not storing more data. The key idea is controlling what is
   allowed to become durable memory and what should only affect the current
   turn.

## Things Not To Claim

Do not claim:

- full custom RAG
- vector memory in production
- perceptual memory
- cross-modal retrieval
- a new agent framework

The best demo is disciplined, not maximal.
