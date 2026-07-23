# Adopt Claude-native Markdown rule packs (common + per-language)

**Status:** accepted
**Date:** 2026-07-23
**Deciders:** Liam Lee

## Context

`rules/` is a Phase 1 module ([ARCHITECTURE.md](../../ARCHITECTURE.md)),
and [harness-foundation.md](../product/harness-foundation.md) left the
exact canonical file format open. The first rule content (coding style)
is being written now, so the format can't stay open. Constraints already
in force: the repo layout is Claude-plugin-compatible
([ADR 0005](0005-use-a-claude-compatible-plugin-layout.md)), plugins
cannot distribute rules, and the
[platform survey](../reference/platform-directories.md) shows no
cross-vendor rules standard exists — every platform has its own path and
format, unlike skills.

## Decision

Canonical rules are **Claude Code's native rule format, unmodified**:
`rules/<pack>/<topic>.md`, plain Markdown with optional `paths:` glob
frontmatter for scoping.

- **Packs**: `common/` (unscoped — loads every session) plus per-language
  packs (`typescript/`, `python/`) scoped via `paths:`.
- **Precedence**: language packs open with an "extends" line and override
  `common/` on conflict — idiomatic exceptions beat generic defaults
  (model borrowed from ECC's rules library).
- **Thin rules, deep skills**: rules state the *what* in ≤~100 lines per
  file; the *how* lives in a companion skill (`skills/coding-style/`),
  which — unlike rules — is plugin-distributable.
- **Dogfooding**: `.claude/rules → ../rules` symlink, mirroring the
  `agents/` pattern.
- Distribution to other repos remains a copy step
  (`~/.claude/rules/vibe/` or project `.claude/rules/`), owned by the
  planned installer/`vibe sync` (ADR 0005's known constraint).

## Alternatives considered

- **Fold rules into AGENTS.md/CLAUDE.md** — rejected: no path scoping, so
  every session pays for every language's rules; bloats the file the
  routing table lives in.
- **A custom canonical format compiled through adapters** — rejected for
  now: with no cross-vendor standard to target, a custom format buys
  nothing today and costs a transform before the first rule loads;
  adapters can still be added per ADR 0004 when a second platform target
  is actually built.
- **A large ECC-style rules library (10 common files × 20 languages)** —
  rejected: always-on token cost grows with every file, and most content
  would duplicate what skills already carry on demand.

## Consequences

**Better:**

- Rules load in Claude Code today with zero adapter work, in this repo
  and in any repo that copies a pack.
- Path scoping keeps the always-on cost to one small common file unless
  matching code is actually touched.

**Worse:**

- Other platforms (Cursor `.mdc`, Copilot `.instructions.md`, …) need
  per-platform transforms in `vibe sync` — already true for every
  non-skill dimension per the platform survey.
- Claude Code's rule frontmatter (`paths:`) is a single-vendor contract;
  if it changes, packs must follow.

**Must now be true:**

- Rule files stay thin (the why in one line per rule; deep guidance goes
  to the companion skill).
- New language packs mirror `common/` filenames and declare the extends
  relationship.

## Revisit if

A cross-vendor rules standard emerges (as agentskills.io did for
skills), or the `vibe sync` spec lands and needs a richer canonical
format than Claude's native one.
