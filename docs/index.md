# VIBE Documentation Index

Navigation only — content lives in the linked documents.

## Entry points (repo root)

- [README.md](../README.md) — human entry point: what VIBE is, status, repo contents.
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute skills and docs today.
- [AGENTS.md](../AGENTS.md) — canonical agent entry point and routing table.
- [ARCHITECTURE.md](../ARCHITECTURE.md) — implemented/planned module map and dependency invariants.

## Product

- [product/DESIGN.md](product/DESIGN.md) — standing product direction: problem, product, goals, non-goals.
- [product/roadmap.md](product/roadmap.md) — four phases, open decision gates, administrative checklist.
- [product/harness-foundation.md](product/harness-foundation.md) — Phase 1 product spec (planned).

## Decisions (ADRs — append-only)

- [0001 — Build VIBE as a local web app](decisions/0001-build-vibe-as-a-local-web-app.md) — Node/TypeScript, node-pty, xterm.js, Dockview.
- [0002 — Repository-local Git worktrees](decisions/0002-use-repository-local-git-worktrees.md) — `.vibe/worktrees/<branch>/` per pane.
- [0003 — Reviewed file-based memory](decisions/0003-use-reviewed-file-based-memory.md) — pending/approved instincts, human review required.
- [0004 — Canonical content compiled through adapters](decisions/0004-compile-canonical-content-through-adapters.md) — one source, generated platform targets.
- [0005 — Claude-compatible plugin layout](decisions/0005-use-a-claude-compatible-plugin-layout.md) — layout fixed, distribution deferred.
- [0006 — Predefined research agents by modality](decisions/0006-predefine-research-agents-by-modality.md) — canonical `agents/`, split by modality, thin definitions linked to skills.
- [0007 — Claude-native Markdown rule packs](decisions/0007-adopt-claude-native-rule-packs.md) — `rules/<pack>/*.md` with `paths:` scoping; thin rules, deep companion skill.
- [0008 — Layered security harness](decisions/0008-adopt-a-layered-security-harness.md) — security rules + `security-audit` skill + reviewer agent + fail-closed hooks; live OSV checks over IOC lists.
- [0009 — Debugging/RCA harness](decisions/0009-adopt-a-debugging-rca-harness.md) — debugging floor rules + `debugging` skill + fresh-context `root-cause-analyst` lane; deliberately no hooks layer.

## Reference

- [reference/platform-directories.md](reference/platform-directories.md) — where 9 platforms (Claude Code, Codex, Gemini CLI, Cursor, Windsurf/Devin, Cline, Kiro, Antigravity, Copilot) load root instructions, skills, rules, subagents, hooks, commands (verified 2026-07-23; drift-prone).

## Debt

- [tech-debt.md](tech-debt.md) — flat, grep-able debt log (empty).
