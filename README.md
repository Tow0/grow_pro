# grow_pro

`grow_pro` 是一个基于 `nanobot` 的个人成长 Agent 助手项目。

这个项目的目标不是重新实现一个 Agent 框架，而是在已有 `nanobot`
runtime 上，增加一层清晰、克制、可解释的成长领域能力：记忆治理、上下文装配、可搜索历史和当前回合证据输入。

## 当前状态

当前项目处于 V1 收尾状态。

已经完成：

- `nanobot growth` CLI 入口
- `GrowthEvent` 统一事件协议
- 基于规则的 `ExecutionMode` 选择
- Hermes-style 小核心记忆快照
- 显式长期记忆候选抽取
- `MemoryWriteCandidate + RuleBasedMemoryGovernor` 长期记忆治理
- 基于 `history.jsonl` 的历史层
- 薄 SQLite FTS history 索引
- 当前回合 Evidence Lane
- growth 相关测试和说明文档

已经验证：

```text
pytest tests/growth tests/cli/test_commands.py -p no:cacheprovider
94 passed

ruff check nanobot/growth nanobot/cli/commands.py tests/growth tests/cli/test_commands.py
All checks passed
```

需要说明：

- 上面的验证证明代码链路、CLI 参数、上下文装配、记忆治理和测试用例通过。
- 这不等于已经在没有配置 LLM 的情况下完成真实模型调用。
- 如果要做真实对话演示，需要先配置 LLM provider、model 和 API key。

## 架构概览

最终架构是：

```text
nanobot runtime
+ Hermes-style memory
+ growth write governance
+ searchable history
+ current-turn evidence lane
```

`nanobot` 继续负责通用 runtime：

- agent loop
- runner
- providers
- channels
- sessions
- cron
- file-based memory
- skills
- CLI / API 基础能力

`nanobot/growth` 只增加成长领域层：

- growth event contracts
- execution mode vocabulary
- memory write candidates
- memory write governor
- core memory snapshot service
- stable context assembler
- growth orchestrator
- current-turn evidence loader

## 记忆系统

当前实现采用 Hermes-style 三层记忆结构。

Working Memory：

- 对应已有 `Session.messages`
- 绑定当前会话
- 不在 `growth` 下重新实现一套短期记忆系统

Core Memory：

- `USER.md`
- `memory/MEMORY.md`
- 小而稳定、可读、可审计、可手工修正

History Layer：

- `memory/history.jsonl` 是 source of truth
- `memory/history_index.sqlite3` 是薄 SQLite FTS 索引
- 索引不可用时回退 lexical search

长期记忆写入流程：

```text
user message
-> memory extractor
-> MemoryWriteCandidate
-> RuleBasedMemoryGovernor
-> USER.md / memory/MEMORY.md
```

项目重点不是“把更多内容存起来”，而是控制什么内容可以成为长期记忆，以及为什么可以写入。

## 上下文与检索

当前项目不是完整自定义 RAG 平台。

更准确的说法是：

```text
retrieval-informed context assembly
```

最终上下文结构是稳定 section：

```text
[Role & Policies]
[Task]
[State]
[Current Evidence]
[Memory Snapshot]
[Relevant History]
```

已经实现：

- core memory snapshot 注入
- relevant history 检索
- SQLite FTS history search
- 当前回合 evidence 注入

没有实现：

- vector-first RAG
- graph memory
- cross-source ranking platform
- perceptual memory
- cross-modal retrieval

## 当前回合 Evidence Lane

`nanobot growth` 支持当前回合证据输入：

```powershell
nanobot growth `
  --message "根据这些材料帮我总结成长风险。" `
  --event-type checkin `
  --evidence-text "本周三次熬夜，第二天专注度明显下降。" `
  --user-id demo-user `
  --session demo-session
```

Evidence 行为：

- inline evidence text 会进入 `[Current Evidence]`
- workspace 文件会尽量文本化后进入 `[Current Evidence]`
- 图片文件当前作为轻量引用处理
- evidence 默认只影响当前 turn
- evidence 不会自动写入长期记忆
- 长期沉淀仍必须经过 `MemoryWriteCandidate + RuleBasedMemoryGovernor`

## LLM 配置

真实运行 `nanobot growth` 需要配置 LLM。

最小配置通常包括：

- provider
- model
- API key

配置方式沿用 `nanobot` 底座的配置系统。可以先运行：

```powershell
nanobot onboard
```

也可以直接编辑本地配置文件。配置文件属于本机运行环境，不应该提交到 Git 仓库。

配置时只需要在本地提供 provider、model 和 API key。README 不保存任何真实密钥或本机配置内容。

注意：

- 不要把真实 API key 写进 README。
- 不要把本地配置目录提交到 Git。
- 当前 `.gitignore` 已忽略本地运行态目录。

## CLI 示例

查看 growth 命令：

```powershell
nanobot growth --help
```

显式偏好写入：

```powershell
nanobot growth `
  --message "以后回答直接一点，少些铺垫。" `
  --event-type user_message `
  --user-id demo-user `
  --session demo-session
```

任务阻塞进入 recovery mode：

```powershell
nanobot growth `
  --message "The task is blocked because the reviewer has not replied." `
  --event-type task_update `
  --status blocked `
  --priority high `
  --user-id demo-user `
  --session demo-session
```

当前回合 evidence：

```powershell
nanobot growth `
  --message "根据这份复盘材料，帮我识别下周最该避免的问题。" `
  --event-type checkin `
  --evidence .\workspace\weekly_review.md `
  --user-id demo-user `
  --session demo-session
```

## 项目结构

growth 相关实现集中在：

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

真实 CLI 入口：

```text
nanobot/cli/commands.py
```

growth 测试：

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

## 开发与验证

安装：

```powershell
python -m pip install -e .
```

安装开发依赖：

```powershell
python -m pip install -e ".[dev]"
```

验证当前源码来源：

```powershell
python -c "import nanobot; print(nanobot.__file__)"
```

运行 growth 和 CLI 测试：

```powershell
python -m pytest tests/growth tests/cli/test_commands.py -p no:cacheprovider
```

运行 lint：

```powershell
python -m ruff check nanobot/growth nanobot/cli/commands.py tests/growth tests/cli/test_commands.py
```

## 文档

建议阅读顺序：

1. `docs/growth/project-guide.zh-CN.md`
2. `docs/growth/architecture.md`
3. `docs/growth/memory-and-rag.md`
4. `docs/growth/multimodal-evidence.md`
5. `docs/growth/source-map.md`
6. `docs/growth/interview-narrative.md`
7. `docs/growth/demo-walkthrough.md`

## 与 nanobot 的关系

本项目包含并复用了 `nanobot` 代码。

`nanobot` 提供 runtime：

- loop
- session
- tools
- providers
- channels
- memory foundation
- skills

`grow_pro` 增加 growth 领域层：

- growth event
- governed memory writes
- Hermes-style memory service
- searchable history
- current-turn evidence lane

一句话：

```text
nanobot provides the runtime.
grow_pro adds the growth memory and context layer.
```

## 本项目不是什么

本项目不是：

- 新的通用 Agent 框架
- 第二套 runtime
- 第二套 skill 系统
- workflow 平台
- vector RAG 系统
- graph memory 系统
- perceptual memory 平台
- 多模态长期记忆系统

V1 刻意保持窄边界，以便能运行、能测试、能审计、能讲清楚。

## 隐私与提交规则

不要提交：

- `.env`
- API key
- 本地 LLM 配置
- 本地运行目录
- 私人 workspace 数据
- SQLite history 索引
- 临时日志和缓存

当前 `.gitignore` 已忽略：

```text
.nanobot/
workspace/
**/history_index.sqlite3
```

## License And Attribution

本项目基于开源 `nanobot` 项目进行二次开发，并保留原始 license 和第三方声明。

相关文件：

- `LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `docs/growth/project-guide.zh-CN.md`
