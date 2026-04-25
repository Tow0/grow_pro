# Growth 项目中文说明

本文档用于说明当前项目的最终 V1 状态、架构边界、核心代码路径、验证方式，以及如何上传到远程 Git 仓库。

## 1. 项目定位

本项目是基于 `nanobot` 的二次开发，不是重新实现一个 Agent 框架。

最终目标是做出一个可运行、可解释、可面试讲清楚的“个人成长 Agent 助手”最小版本。

一句话概括：

> 我们复用 `nanobot` 作为 runtime，在其上增加 growth 领域层；记忆采用 Hermes-style 小核心记忆方案，并通过 `MemoryWriteCandidate + RuleBasedMemoryGovernor` 控制长期记忆写入。

## 2. 当前最终架构

最终架构已经收束为：

```text
nanobot runtime
+ Hermes-style memory
+ growth write governance
+ searchable history
+ current-turn evidence lane
```

其中：

- `nanobot/` 负责通用 runtime。
- `nanobot/growth/` 只负责 growth 领域逻辑。
- 不创建第二套 runtime、skill、workflow、memory、cron 系统。
- 不做 vector-first RAG。
- 不做 graph memory。
- 不做 perceptual memory 平台。
- 不做多模态长期记忆系统。

## 3. nanobot 负责什么

`nanobot` 底座继续负责：

- Agent loop
- runner
- providers
- channels
- sessions
- cron
- file-based memory
- skills
- CLI / API 入口

这些能力不在 `growth` 里重写。

## 4. growth 负责什么

`growth` 层只新增必要领域能力：

- `GrowthEvent`：统一 growth 事件入口。
- `ExecutionMode`：运行模式，如 conversational、planning、reflection、recovery。
- `MemoryWriteCandidate`：长期记忆写入候选。
- `RuleBasedMemoryGovernor`：长期记忆写入治理。
- `HermesStyleMemoryService`：核心记忆快照、history 检索、持久化。
- `HermesStyleContextAssembler`：稳定上下文装配。
- `HermesStyleGrowthOrchestrator`：最小执行链路。
- `EvidenceItem`：当前回合证据输入。

## 5. 当前目录结构

核心代码集中在：

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

真实 CLI 入口在：

```text
nanobot/cli/commands.py
```

命令为：

```powershell
nanobot growth
```

## 6. 记忆系统设计

当前实现层采用三层记忆：

1. Working Memory
   - 对应 `Session.messages`
   - 生命周期绑定当前会话
   - 不在 growth 下另做一套短期记忆系统

2. Core Memory
   - 对应 `USER.md`
   - 对应 `memory/MEMORY.md`
   - 存放小而稳定的长期用户信息、偏好、策略、规则

3. History Layer
   - 对应 `memory/history.jsonl`
   - 当前已经有薄 SQLite FTS 索引：`memory/history_index.sqlite3`
   - `history.jsonl` 仍是 source of truth
   - SQLite 索引失败时自动回退 lexical search

语义上可以解释为：

- working memory：当前会话短期状态
- semantic memory：稳定偏好、规则、策略
- episodic memory：过往事件与历史
- perceptual memory：暂不做长期记忆，只作为后续扩展方向

## 7. 长期记忆治理

长期记忆不能直接写入。

写入流程是：

```text
user message
-> memory extractor
-> MemoryWriteCandidate
-> RuleBasedMemoryGovernor
-> USER.md / memory/MEMORY.md
```

`MemoryWriteCandidate` 包含：

- `scope`
- `type`
- `content`
- `provenance`
- `confidence`
- `reason`

治理规则：

- `explicit_user`：直接允许。
- `observed`：需要达到置信度阈值。
- `inferred`：需要更高置信度，且不能直接写成 `fact`。

这是本项目最重要的差异化边界。

## 8. RAG 状态

当前项目不是完整自定义 RAG 系统。

更准确的说法是：

> 当前是 retrieval-informed context assembly。

已经实现：

- core memory 注入
- history 检索
- SQLite FTS history search
- current-turn evidence lane
- 固定 section 的 context packet

没有实现：

- vector retriever
- cross-source ranking platform
- graph memory
- full GSSC platform
- 多模态长期检索

## 9. Current-Turn Evidence Lane

当前已经支持当前回合证据输入。

CLI 参数：

```powershell
--evidence
--evidence-text
```

用途：

- 文本证据进入 `[Current Evidence]`
- 文档会被尽量文本化后进入 `[Current Evidence]`
- 图片目前作为引用型 evidence，不做真正图像 embedding 或跨模态检索
- evidence 默认只影响当前 turn
- evidence 不会自动写入长期记忆
- 如需长期沉淀，仍必须走 `MemoryWriteCandidate + RuleBasedMemoryGovernor`

## 10. 当前执行链路

真实链路如下：

```text
nanobot growth ...
-> CLI builds GrowthEvent
-> HermesStyleGrowthOrchestrator.handle(...)
-> RuleBasedModeSelector.select(...)
-> derive MemoryWriteCandidate
-> RuleBasedMemoryGovernor
-> HermesStyleMemoryService.persist_candidate(...)
-> HermesStyleContextAssembler.assemble(...)
-> render stable context sections
-> NanobotRuntimeAdapter.run_text_turn(...)
-> nanobot runtime calls model
```

## 11. 推荐阅读顺序

如果要快速理解代码，按这个顺序读：

1. `docs/growth/architecture.md`
2. `docs/growth/memory-and-rag.md`
3. `docs/growth/source-map.md`
4. `nanobot/cli/commands.py`
5. `nanobot/growth/orchestrator/service.py`
6. `nanobot/growth/memory/governor.py`
7. `nanobot/growth/memory/snapshot.py`
8. `nanobot/growth/context/assembler.py`
9. `docs/growth/interview-narrative.md`
10. `docs/growth/demo-walkthrough.md`

## 12. 验证命令

正式环境：

```text
D:\Anaconda\envs\growpro
```

运行测试：

```powershell
D:\Anaconda\envs\growpro\python.exe -m pytest D:\codex\project\grow_pro\tests\growth D:\codex\project\grow_pro\tests\cli\test_commands.py -p no:cacheprovider
```

运行 lint：

```powershell
D:\Anaconda\envs\growpro\python.exe -m ruff check D:\codex\project\grow_pro\nanobot\growth D:\codex\project\grow_pro\nanobot\cli\commands.py D:\codex\project\grow_pro\tests\growth D:\codex\project\grow_pro\tests\cli\test_commands.py
```

最近一次验证结果：

```text
94 passed
ruff: All checks passed
```

剩余 warning 来自第三方 `websockets/lark_oapi` 的 deprecation warning，不是 growth 代码问题。

## 13. Demo 命令

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
  --message "根据这些材料帮我总结成长风险。" `
  --event-type checkin `
  --evidence-text "本周三次熬夜，第二天专注度明显下降。" `
  --user-id demo-user `
  --session demo-session
```

## 14. 如何上传到远程 Git 仓库

当前 `D:\codex\project\grow_pro` 还不是 Git 仓库，所以第一次上传需要先初始化。

进入项目目录：

```powershell
cd D:\codex\project\grow_pro
```

初始化 Git：

```powershell
git init
```

检查状态：

```powershell
git status
```

添加文件：

```powershell
git add .
```

创建第一次提交：

```powershell
git commit -m "Initial growth agent V1"
```

绑定远程仓库：

```powershell
git remote add origin <你的远程仓库地址>
```

例如：

```powershell
git remote add origin https://github.com/<用户名>/<仓库名>.git
```

或 SSH：

```powershell
git remote add origin git@github.com:<用户名>/<仓库名>.git
```

设置主分支名：

```powershell
git branch -M main
```

推送：

```powershell
git push -u origin main
```

后续每次更新：

```powershell
git status
git add .
git commit -m "Update growth agent"
git push
```

## 15. 上传前建议检查

上传前建议确认：

```powershell
git status
```

不要上传：

- `.env`
- `.nanobot/`
- API key
- 临时日志
- 大型本地缓存
- 私人 workspace 数据
- `workspace/`
- `history_index.sqlite3`

当前 `.gitignore` 已经包含这些本地运行态规则：

```text
.nanobot/
workspace/
**/history_index.sqlite3
```

如果你确实想把示例 workspace 也上传，可以单独创建一个脱敏后的 `examples/` 目录，而不要直接提交本地运行目录。

## 16. 面试讲法

推荐回答：

> 我没有重写一个 Agent 框架，而是复用 `nanobot` 的 runtime，包括 loop、session、tool、provider、memory、skills 等能力。在此基础上，我加了一个很窄的 growth 层：用 `GrowthEvent` 表达成长事件，用 `MemoryWriteCandidate + RuleBasedMemoryGovernor` 控制长期记忆写入，用 Hermes-style 小核心记忆保持系统可运行、可审计，再通过 searchable history 和 current-turn evidence lane 组装稳定上下文。这个项目的重点不是堆功能，而是把记忆、上下文和治理边界讲清楚，并且能端到端跑起来。

## 17. 当前完成状态

当前可以认为 V1 已完成：

- growth CLI 入口已完成
- memory extractor 已完成
- memory governor 已完成
- core memory snapshot 已完成
- searchable history 已完成
- SQLite FTS history index 已完成
- current-turn evidence lane 已完成
- final docs 已完成
- source map 已完成
- interview narrative 已完成
- demo walkthrough 已完成
- tests 通过
- ruff 通过

后续如果继续扩展，优先考虑：

1. structured state integration
2. mode-aware retrieval policy
3. context budget management
4. 更完整的 demo 数据

不建议立刻做：

- vector RAG
- graph memory
- perceptual memory
- cross-modal retrieval
- 第二套 runtime
