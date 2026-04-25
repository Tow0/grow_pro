# growth Reuse Map

This file answers the question we should ask before every code change:

`Does nanobot already do this?`

## Reuse As-Is

- `nanobot.agent.loop.AgentLoop`
- `nanobot.agent.runner.AgentRunner`
- `nanobot.agent.tools.registry.ToolRegistry`
- `nanobot.providers.registry`
- `nanobot.channels.manager.ChannelManager`
- `nanobot.session.manager.SessionManager`
- `nanobot.cron.service.CronService`
- `nanobot.agent.memory.MemoryStore`
- `nanobot.agent.memory.Consolidator`
- `nanobot.agent.memory.Dream`
- `nanobot.skills/*`

These are runtime facilities. The growth project should consume them rather than replace them.

## Wrap, Don't Fork

- `nanobot.nanobot.Nanobot`
- `nanobot.agent.context.ContextBuilder`

These need a stable seam so growth logic is not spread across core runtime modules.

## Build New

- `nanobot.growth.contracts.*`
- `nanobot.growth.domain.models`
- `nanobot.growth.memory.governor`
- `nanobot.growth.context.*`
- `nanobot.growth.orchestrator.*`

These are product-specific concerns. nanobot does not and should not define them for us.
