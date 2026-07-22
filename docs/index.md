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

## Debt

- [tech-debt.md](tech-debt.md) — flat, grep-able debt log (empty).

## Process records (historical)

- [superpowers/specs/2026-07-22-docs-foundation-design.md](superpowers/specs/2026-07-22-docs-foundation-design.md) — approved design for this documentation foundation.
- [superpowers/plans/2026-07-22-docs-foundation.md](superpowers/plans/2026-07-22-docs-foundation.md) — implementation plan executed for the foundation.
