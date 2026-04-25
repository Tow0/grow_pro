# growth Coding Order

The implementation order is now driven by the final V1 architecture:

- `nanobot` runtime
- Hermes-style small memory
- governed long-term writes
- minimal growth-specific additions

The order below is intentionally narrow.

## Step 1: Keep the current runtime

Do not rebuild:

- loop
- runner
- sessions
- cron
- providers
- channels
- skills
- current file-based memory

The first rule is to avoid expanding the runtime surface.

## Step 2: Preserve the governance layer

Keep and validate:

- `nanobot.growth.contracts.memory`
- `nanobot.growth.memory.governor`

This is the main project-specific contribution and should remain the clearest
architectural boundary.

## Step 3: Standardize core memory usage

Use the existing files as the V1 core memory:

- `USER.md`
- `memory/MEMORY.md`
- `memory/history.jsonl`

Do not build a second long-term storage system before the basic path runs.

## Step 4: Build the first executable path

The first concrete path should be:

1. receive a normalized growth event
2. derive one or more `MemoryWriteCandidate` values when appropriate
3. approve or reject them through the governor
4. build a small memory snapshot from `USER.md` and `MEMORY.md`
5. inject only relevant recent history
6. call nanobot through the existing runtime

That is enough for a real V1.

Status:

- completed
- includes the `nanobot growth` CLI entrypoint
- includes a thin explicit-user extractor for `user_message`

## Step 5: Add lightweight retrieval only if needed

If history search becomes a practical bottleneck, add a thin retrieval layer.

The preferred order is:

1. search `history.jsonl`
2. add a thin SQLite FTS index if lexical search becomes limiting
3. delay vector retrieval until after V1 is stable

Status:

- completed
- `history.jsonl` remains the source of truth
- SQLite FTS now exists as a thin, rebuildable index

## Step 6: Add a current-turn evidence lane

After the core memory path is stable, add a narrow evidence lane:

1. accept inline evidence text
2. accept workspace-relative file evidence
3. textualize documents when possible
4. inject evidence into `[Current Evidence]`
5. keep evidence out of long-term memory by default

Status:

- completed for V1 text and document evidence
- image inputs are treated as lightweight references, not perceptual memory

## Step 7: Delay large memory expansions

Do not implement these in V1:

- perceptual memory subsystem
- vector-first RAG
- graph memory
- M-Flow-style memory graph
- growth-specific MCP memory integration
- growth-specific A2A memory integration
