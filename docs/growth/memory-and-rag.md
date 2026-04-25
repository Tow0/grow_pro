# growth Memory and Retrieval

This document describes the final V1 memory and retrieval strategy.

The project keeps `nanobot`'s existing memory stack and narrows the design to a
small, inspectable product shape.

## Memory Shape

V1 memory has three layers.

### Working Memory

Working memory is the current live session:

- source: `Session.messages`
- purpose: keep the current conversation coherent
- lifetime: bounded to the session

We do not create a separate working-memory store under `nanobot/growth/`.

### Core Memory

Core long-term memory is intentionally small:

- `USER.md`
- `memory/MEMORY.md`

These files are the stable memory snapshot used for prompt injection.

### History Layer

History is retrieval-oriented, not always-on prompt state:

- `memory/history.jsonl`
- thin SQLite FTS index in `memory/history_index.sqlite3`

This lets us keep durable evidence without bloating the default prompt.

## Memory Governance

This remains the main growth-specific addition.

Long-term writes first become `MemoryWriteCandidate` objects.

That makes each write explicit:

- scope
- provenance
- confidence
- reason

The governor can reject weak writes before they reach `USER.md` or
`MEMORY.md`.

## Is This Project Using RAG?

Not in the full custom-pipeline sense.

Today the project uses:

- core memory file injection
- recent history injection
- relevant history lookup through lexical search with a thin SQLite FTS index
- current-turn evidence injection for inline text and workspace files
- retrieval interfaces in `nanobot/growth/context/*`

Today the project does not yet use:

- a concrete growth retrieval pipeline
- cross-source scoring and ranking in production
- vector retrieval
- a fully implemented GSSC pipeline

So the correct summary is:

The project uses retrieval-informed context assembly, but not a full
growth-specific RAG system yet.

## Retrieval Direction

When retrieval is expanded later, the intended order remains conservative:

1. recent and relevant history
2. lexical lookup over `USER.md` and `MEMORY.md`
3. current-turn evidence
4. structured growth state when it exists
5. optional vector retrieval later

That keeps V1 simple and preserves a clear explanation of why each piece of
context entered the prompt.

## Current-Turn Evidence

M2 adds a current-turn evidence lane.

It lets the growth path ingest:

- inline evidence text
- workspace-relative file evidence
- textualized document evidence
- image references as lightweight current-turn inputs

Evidence is injected into `[Current Evidence]` and influences only the current
turn by default.

Evidence does not automatically become long-term memory. If any evidence should
become durable memory, it must still pass through `MemoryWriteCandidate` and
`RuleBasedMemoryGovernor`.

## Multimodal Direction

The base runtime already supports useful multimodal inputs:

- image blocks in user messages
- document text extraction
- attachment ingestion through channels
- audio transcription hooks in some channels

V1 treats multimodal capability as evidence for the current turn, not as a
separate perceptual-memory platform.

That means:

- use existing image and document support immediately
- persist only small references or summaries when needed
- delay perceptual memory and cross-modal retrieval to a later version
