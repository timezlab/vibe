# Predefine research subagents by modality, in a canonical agents/ directory

**Status:** accepted
**Date:** 2026-07-23
**Deciders:** Liam Lee

## Context

Research dispatches kept rebuilding the same subagent brief: ~80% of each
brief was the research discipline (source hierarchy, deep-read, verify,
output contract) restated by hand. All four major harnesses now load
predefined agents from files (survey:
[platform-directories](../reference/platform-directories.md)),
and Claude Code's `skills:` frontmatter can preload a skill into an agent's
context — so the boilerplate can live once, in files.

Two axes were considered for splitting predefined research agents:
by *subject-topic* (AI, healthcare, …) or by *modality/tier* (web, academic,
code, verification).

## Decision

1. **Predefine research subagents split by modality**, not subject-topic:
   `web-researcher`, `academic-researcher`, `code-researcher`,
   `fact-checker`. Modalities are stable and bounded; topics are unbounded
   and belong in the dispatch prompt. Platform guidance converges on few,
   focused agents (Cursor: "start with 2–3, expand cautiously"; Codex:
   "narrow and opinionated").
2. **Agents live in a canonical top-level `agents/` directory**, a sibling
   of `skills/` — the Claude Code plugin structure
   ([ADR 0005](0005-use-a-claude-compatible-plugin-layout.md)) and the
   layout of the largest prior-art collection (wshobson/agents). Not inside
   `skills/<name>/`: the skills spec gives an embedded `agents/` folder no
   meaning and no platform loads agents from skill folders.
3. **`.claude/agents → ../agents` symlink** serves Claude Code natively and
   Cursor via its cross-read of `.claude/agents/`. Codex (TOML) and Gemini
   CLI outputs are future `vibe sync` adapter targets
   ([ADR 0004](0004-compile-canonical-content-through-adapters.md)).
4. **Agent definitions stay thin** — role, lane, output contract — and pull
   the discipline via `skills: [research]`. The skill remains the single
   source of truth; agents never copy its content.

## Alternatives considered

- **Bundle agents inside `skills/research/agents/`** — rejected: validator
  tolerates it (verified empirically) but no harness reads it; dead files.
- **Split agents by subject-topic** — rejected: unbounded set, duplicates
  the skill per topic, and dilutes delegation (many vague descriptions).
- **No predefined agents (keep writing briefs ad hoc)** — rejected for
  research specifically: the brief was demonstrably repetitive; kept as the
  default for domains without that evidence.

## Consequences

**Better:**

- Dispatching a research lane needs only the facet, not the discipline.
- One canonical source covers two platforms today (Claude Code, Cursor)
  and gives `vibe sync` a concrete adapter test case (md → TOML for Codex).

**Worse:**

- The `skills:` link is Claude-specific; every other platform's adapter
  must resolve it (inline the skill or approximate it) — recorded as
  adapter work, not hand-patched output.
- A second canonical directory to keep consistent with README/AGENTS.md.

**Must now be true:**

- New canonical agents go in `agents/`; `.claude/agents/` stays a symlink,
  never hand-edited copies.
- New agent definitions follow the modality/tier rule or record their own
  reasoning here in a new ADR.

## Revisit if

`vibe sync` lands its agent adapters (the `skills:` translation strategy
gets decided then), or a platform starts loading agents from inside skill
folders, or delegation quality shows the four-way modality split is wrong.
