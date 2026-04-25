# growth Interview Narrative

This document is the recommended explanation of the project at its final V1
state.

## One-Sentence Version

This project is a growth-focused agent layer built on top of `nanobot`; it
keeps the existing runtime, adopts a Hermes-style small-memory architecture,
adds governed long-term writes, and now supports a current-turn evidence lane
without turning growth into a second RAG or memory platform.

## The Five Core Questions

### 1. What did `nanobot` already provide?

`nanobot` already provided the generic runtime:

- agent loop
- runner
- providers
- channels
- sessions
- cron
- file-based memory
- skills
- CLI and API entrypoints

So we did not need to rebuild an agent framework.

### 2. What did this project add?

The project added the growth-specific layer:

- normalized `GrowthEvent`
- execution modes
- `MemoryWriteCandidate`
- `RuleBasedMemoryGovernor`
- Hermes-style growth memory service
- stable growth context assembly
- a real `nanobot growth` entrypoint
- a current-turn evidence lane

### 3. Why were those additions necessary?

Because `nanobot` gives a generic runtime, but it does not define growth-domain
semantics.

The project needed:

- a way to express growth events
- a way to explain which memory writes are safe
- a way to keep long-term memory small and inspectable
- a way to inject current-turn growth evidence and history into context

### 4. Why did we not rebuild the runtime?

Because that would weaken both the engineering and the interview story.

If we rebuilt sessions, tools, memory, cron, and context from scratch, the
project would stop looking like a disciplined extension of an existing runtime
and start looking like an unfinished parallel framework.

The strongest decision was restraint.

### 5. How does the final path actually work?

The path is:

1. user calls `nanobot growth`
2. CLI builds a `GrowthEvent`
3. orchestrator selects an `ExecutionMode`
4. memory candidates are derived
5. governor decides what can persist
6. core memory snapshot and relevant history are assembled
7. current-turn evidence is added
8. context is rendered into stable sections
9. `nanobot` runtime handles the actual model call

## What The Project Is Not

It is not:

- a new general-purpose agent framework
- a four-store memory platform
- a vector-first RAG system
- a graph memory system
- a perceptual memory system
- a multimodal long-term memory platform
- a second skill system
- a second workflow engine

This is important because the quality of the project comes from clear
boundaries, not from the number of abstractions.

## How To Explain Memory

The implementation uses a Hermes-style three-layer shape:

1. working memory
2. core memory
3. history layer

In concrete terms:

- working memory = `Session.messages`
- core memory = `USER.md` + `memory/MEMORY.md`
- history layer = `memory/history.jsonl` + thin SQLite FTS index

At the same time, the project keeps its own governance layer:

- every durable write first becomes a `MemoryWriteCandidate`
- every durable write passes through `RuleBasedMemoryGovernor`

That means the differentiator is not just storage.
The differentiator is governed persistence.

## How To Explain RAG

The safest wording is:

The project does not yet implement a full custom growth-specific RAG stack.
Instead, it uses retrieval-informed context assembly.

What that means:

- core memory is injected directly
- relevant history is retrieved from `history.jsonl`
- a thin SQLite FTS index improves history search
- current-turn evidence is injected into a dedicated evidence section

What it does not mean:

- no vector retriever in production
- no cross-source ranking system in production
- no end-to-end GSSC platform in production

## How To Explain Multimodality

The project supports a current-turn evidence lane, not multimodal memory.

The important distinction is:

- documents, inline text, and lightweight file references can affect the
  current turn
- they do not automatically become long-term memory
- they do not create a perceptual memory subsystem

That keeps the system aligned with the V1 goal: narrow, inspectable, and safe.

## Strongest Technical Decision

The strongest technical decision in the project is this:

Long-term memory writes are explicitly modeled, reviewed, and governed before
they are persisted.

That gives every durable memory:

- scope
- provenance
- confidence
- reason

This makes the memory system explainable in a way that file-only or
vector-only designs often are not.

## Strongest Product Decision

The strongest product decision is also restraint:

We chose a Hermes-style small-memory V1 because it is much easier to run,
inspect, test, and explain than a large speculative memory architecture.

## Best Demo Story

A clean demo is:

1. run `nanobot growth` with a `user_message`
2. show explicit preference extraction and governed persistence
3. run `nanobot growth` with a `task_update --status blocked`
4. show that mode changes to `recovery`
5. run `nanobot growth` with `--evidence` or `--evidence-text`
6. show `[Current Evidence]` in the assembled context story
7. explain that evidence affects the current turn, but durable memory still
   goes through the governor

That demo covers:

- runtime reuse
- growth-specific semantics
- memory governance
- searchable history
- current-turn evidence

## The Final Answer To "What Did You Build?"

The best final answer is:

I did not build a new agent framework. I took `nanobot` as the runtime kernel,
kept its loop, sessions, tools, and memory foundation, and added a disciplined
growth layer on top. That layer contributes normalized growth events, governed
long-term memory writes, a Hermes-style small-memory strategy, searchable
history, stable context assembly, and a current-turn evidence lane. The result
is intentionally narrow, but it runs end to end and is easy to explain.
