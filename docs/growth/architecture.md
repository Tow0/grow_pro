# growth Final Architecture

This document is the final V1 architecture for the project.

The goal is no longer to build a broad growth runtime abstraction layer.
The goal is to ship a small system that runs, is easy to inspect, and is easy
to explain in an interview.

## Final Shape

The project keeps `nanobot/` as the runtime kernel and adopts a
Hermes-style memory architecture on top of it.

V1 is:

- `nanobot` runtime
- small core memory
- searchable history
- current-turn evidence lane
- governed long-term writes
- minimal growth-specific domain semantics

This is intentionally narrower than the earlier growth-layer plan.

## Runtime Boundary

`nanobot/` remains responsible for generic runtime behavior:

- `AgentLoop`
- `AgentRunner`
- `ToolRegistry`
- providers
- channels
- sessions
- cron scheduling
- current file-based memory implementation
- skills loading

`nanobot/growth/` remains responsible only for growth-specific logic that is
still worth keeping:

- normalized events
- execution modes
- light domain vocabulary
- long-term memory write governance
- small context assembly hooks

The growth layer should not grow into a second runtime.

## Memory Architecture

V1 uses a three-layer memory design.

### 1. Working Memory

Working memory is the live session state already provided by `nanobot`.

- source: `Session.messages`
- lifetime: one session
- purpose: current task continuity
- persistence model: session storage, not durable long-term memory

We do not build a separate working-memory subsystem in `nanobot/growth/`.

### 2. Core Memory

Core long-term memory is intentionally small and stable.

- `USER.md`
- `memory/MEMORY.md`

These files are the always-on memory snapshot injected into model context.
They should stay compact, readable, and manually auditable.

### 3. History Layer

History is not always-on prompt context.

It is a retrieval layer used when recent or older interaction evidence is
needed.

V1 source of truth:

- `memory/history.jsonl`

Current implementation:

- a thin SQLite FTS index over `history.jsonl`
- automatic fallback to lexical search if the index is unavailable

The important design point is separation:

- core memory stays small
- history stays searchable

## Long-Term Write Governance

This is the main project-specific differentiator and must stay.

Long-term writes do not go directly into `USER.md` or `MEMORY.md`.
They first become `MemoryWriteCandidate` objects and then pass through the
`RuleBasedMemoryGovernor`.

That gives every write:

- scope
- provenance
- confidence
- reason

This boundary prevents inferred content from silently becoming durable fact.

## Context Injection

V1 does not use a heavy dynamic context platform.

It uses a small, stable assembly shape:

- `[Role & Policies]`
- `[Task]`
- `[State]`
- `[Current Evidence]`
- `[Memory Snapshot]`
- `[Relevant History]`

The memory snapshot is built from `USER.md` and `MEMORY.md` and should be
treated as a frozen snapshot for the current run.

Current-turn evidence is injected ahead of memory and history so user-provided
materials for the active turn stay easy to inspect and harder to drown out.

History is injected only when relevant.

This makes the system easier to debug, cheaper to run, and easier to explain.

## RAG Status

Strictly speaking, the project does not yet have a fully implemented
growth-specific RAG pipeline.

What exists today:

- memory file injection via `ContextBuilder`
- recent history injection from `history.jsonl`
- a thin SQLite FTS index over `history.jsonl`
- a current-turn evidence lane for inline text and workspace files
- growth retrieval interfaces for structured state, lexical memory, recent
  history, and future vector search

What does not exist yet:

- a concrete growth retrieval pipeline in production
- candidate scoring and selection across sources
- a concrete vector retriever
- an end-to-end GSSC implementation

So the correct statement is:

V1 uses retrieval-informed context assembly, but not a full custom growth RAG
stack yet.

## Multimodal Scope

The base runtime already has useful multimodal hooks:

- image inputs can be injected into user messages
- file tools can read text and images
- document text extraction already exists
- some channels can ingest attachments and transcribe audio

V1 should reuse those capabilities instead of building a separate perceptual
memory system.

Current V1 scope:

- accept inline evidence text through the growth CLI
- accept workspace file evidence through the growth CLI
- textualize documents where possible and inject them into `[Current Evidence]`
- treat images as current-turn references, not long-term perceptual memory
- persist only lightweight references or summaries if explicitly needed

Deferred beyond V1:

- perceptual memory as a first-class subsystem
- cross-modal retrieval
- embedding pipelines for images or audio
- dedicated multimodal vector storage

## What We Are Not Building

V1 explicitly does not build:

- a second runtime
- a second skill system
- a workflow framework
- a four-store memory platform
- vector-first memory
- graph memory
- M-Flow-style memory graph infrastructure
- growth-specific MCP integration
- growth-specific A2A infrastructure

## Interview Narrative

The final explanation should be simple:

1. `nanobot` already provides the runtime.
2. We kept that runtime and did not rebuild it.
3. We adopted a Hermes-style small-memory design because it is more practical
   for a V1 product.
4. We kept our own memory governance boundary so long-term writes remain
   explainable and safe.
5. We added a current-turn evidence lane without turning growth into a second
   multimodal or RAG platform.
6. The result is a system that runs, is inspectable, and is easy to explain.
