# VIBE Roadmap

**Last updated:** 2026-07-22
**Current phase:** 1

## Phases

| Phase | Status | Content |
|-------|--------|---------|
| 1 | **current** | Harness foundation: minimal `rules/ + agents/ + commands/ + hooks/` set (memory hooks, 3–4 agents, common/TypeScript rules), canonical format + `vibe sync` spec (Claude target first), simple installer. See [harness-foundation.md](harness-foundation.md). |
| 2 | planned | App core: server + xterm.js + Dockview, open/close panes, saveable layout templates. Resolves the HTTP-framework gate below. |
| 3 | planned | Setup wizard + Learning tab (built on Phase 1 hooks). |
| 4 | planned | Broadcast prompt, pane status badges + notifications, per-pane Git panel, cost/metrics. Later: task queue hand-off between panes, hook log viewer, mini security audit (AgentShield-style), session replay. |

Deliberately not planned: deep cross-harness adapters (Zed/Copilot/Qwen…),
fully automatic learning, a desktop app.

## Open decision gates

Decisions intentionally deferred — do not resolve them ahead of their phase:

1. **HTTP framework** (decide in Phase 2) — Hono / Fastify / Express / none.
   Criteria: first-class WebSocket, TypeScript without patching, fast startup.
   Cheap to change later.
2. **Harness distribution mechanism** (decide after Phase 1 evidence) —
   Claude Code plugin / npx skills CLI / own installer / hybrid. The current
   layout stays plugin-compatible so any choice is additive
   ([ADR 0005](../decisions/0005-use-a-claude-compatible-plugin-layout.md)).
   Known constraint: Claude Code plugins cannot distribute `rules/`, so a copy
   script into `~/.claude/rules/` is needed regardless.

## Administrative checklist

- [ ] Delete GitHub repo `timezlab/skills` (needs `delete_repo` scope:
      `gh auth refresh -h github.com -s delete_repo`, then
      `gh repo delete timezlab/skills --yes`).
- [ ] Create `timezlab/vibe` on the org and push (local origin already points
      at it).
- [ ] Check `@timezlab/vibe` availability on npm before first publish.
