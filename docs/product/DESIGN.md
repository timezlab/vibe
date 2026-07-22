# VIBE — Product Design

**Status:** pre-alpha
**Owner:** Liam Lee
**Last updated:** 2026-07-22

## Problem

Agent-assisted development is fragmented across three surfaces that don't talk
to each other:

- **Harness configuration** — rules, skills, agents, and hooks are duplicated
  by hand per platform (Claude Code, Codex, Gemini CLI, Cursor…) and drift
  apart.
- **Parallel workspaces** — running several agent sessions against one
  repository means juggling terminals, branch collisions, and manual worktree
  management.
- **Learned context** — what an agent learns in one session (project quirks,
  fixes, preferences) evaporates instead of becoming a reusable team asset.

## Product

**VIBE** — *Vibe Integrated Build Environment* (a play on IDE: the "IDE of the
vibe-coding era") — combines three things in one place:

1. **Harness content** — canonical skills, rules, agents, commands, hooks, and
   MCP configs, compiled to each platform through adapters
   ([ADR 0004](../decisions/0004-compile-canonical-content-through-adapters.md)).
2. **A local multi-agent workspace** — a local web app (planned `vibe ui`)
   with a multi-pane terminal workspace, per-pane Git worktrees, and a harness
   setup wizard
   ([ADR 0001](../decisions/0001-build-vibe-as-a-local-web-app.md),
   [ADR 0002](../decisions/0002-use-repository-local-git-worktrees.md)).
3. **Human-governed learning** — session-derived instincts reviewed by a
   person before they load into future sessions
   ([ADR 0003](../decisions/0003-use-reviewed-file-based-memory.md)).

Identity: repo `timezlab/vibe` · CLI `vibe` (planned) · package
`@timezlab/vibe` (planned).

## Users

Developers and teams building with CLI coding agents — Claude Code first,
other harnesses through adapters with explicitly degraded capabilities.

## Goals

- One canonical harness source; platform outputs are generated, never
  hand-maintained.
- `vibe ui` as the eventual local workspace: setup wizard, multi-pane
  sessions, learning review.
- Safe parallel sessions via repository-local Git worktrees.
- Approved learning that compounds: personal instincts graduate into shared
  org skills and rules.

## Non-goals

- Fully autonomous learning (no human review) — excluded by decision.
- Deep support for every harness in Phase 1 — Claude Code first, `AGENTS.md`
  targets second, Cursor when the team needs it.
- A desktop application — if ever needed, wrap the web frontend in Tauri.
- Remote or hosted infrastructure — VIBE runs locally.

## Experience (planned)

Three main surfaces, all planned — none implemented yet:

- **Harness Setup wizard** — scan a repo, suggest rules/skills/agents, apply.
- **Workspace** — multi-pane terminal layout (saveable templates), command
  palette, per-pane worktrees, "Open in editor".
- **Learning tab** — browse pending instincts, approve/reject, evolve clusters
  into new skills or rules.

## Success

Phase 1 succeeds when canonical harness content can be installed and synced
for Claude Code without maintaining any hand-copied platform output. See the
[roadmap](roadmap.md) for phase details.
