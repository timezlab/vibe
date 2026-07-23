# Data Model: Learned Context

**Feature**: [spec.md](spec.md) · **Date**: 2026-07-23

All entities are plain Markdown files with YAML frontmatter — greppable,
diffable, editor-reviewable (ADR 0003 rationale). Exact serialization rules
live in [contracts/instinct-file.md](contracts/instinct-file.md); this
document defines the entities, fields, and state machine.

## Entity: Instinct

One reviewable lesson. One file per instinct; filename is `<id>.md`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | kebab-case slug | yes | Stable; doubles as filename. Unique within the store (all states). |
| `status` | enum | yes | `pending` \| `approved` \| `rejected` \| `retired`. MUST match the directory the file sits in (directory is authoritative; field is informational — see gate invariant). |
| `trigger` | string | yes | "when …" — the situation the lesson applies to. |
| `domain` | slug | yes | e.g. `code-style`, `workflow`, `testing`. Free vocabulary; used for evolve clustering. |
| `scope` | enum | yes | `project` (only value in this feature; `global` reserved). |
| `source` | enum | yes | `session-extraction` \| `hand-authored` \| `imported`. |
| `confidence` | float 0–1 | yes | Set at creation (ADR 0003 "must now be true"). Informational in this feature — no automatic updates; the review verdict is the quality gate (see research.md D4). |
| `evidence` | list of strings | yes, ≥1 | Each entry cites a verifiable event: user correction, failing→passing check, repeated observation — with session date/id. Never contains secret material. |
| `created` | ISO date | yes | |
| `last-confirmed` | ISO date | yes | = `created` at birth; review approval updates it; loader sorts by it. |
| `evolved-into` | repo path | no | Set on retirement: the canonical asset this instinct graduated into. |
| `sessions` | list of session ids | no | Sessions that contributed evidence. |

Body (Markdown, after frontmatter):

- `## Action` — required: the behavior to adopt, imperative, self-contained.
- `## Evidence` — optional prose expansion of the frontmatter evidence list.
- `## Review notes` — optional: appended by the review flow (verdict, date,
  reviewer edits summary).

### State machine

```text
                       ┌────────────┐  approve / improve-then-approve
        extraction ──▶ │  pending   │ ─────────────────────────────▶ ┌──────────┐
   (or hand-author     └────────────┘                                │ approved │
    directly into           │  reject                                └──────────┘
    approved/ — the         ▼                                          │ evolve merged
    human IS the గate) ┌────────────┐                                  ▼
                       │  rejected  │  (archive; consulted by       ┌──────────┐
                       └────────────┘   extraction dedup, FR-007)   │ retired  │
                            │ TTL only for pending:                 └──────────┘
                            ▼ stale pending pruned (FR-009)
                          deleted
```

Transitions and their actors:

| From → To | Actor | Mechanism |
|---|---|---|
| (none) → pending | extraction pass | new file in `instincts/pending/` |
| (none) → approved | human only | hand-author or move file into `instincts/approved/` |
| pending → approved | human via review | file moved (optionally edited first); `last-confirmed` set; backup mirror updated |
| pending → rejected | human via review | file moved to `instincts/rejected/` |
| pending → deleted | prune (automatic) | only files older than retention window, only in `pending/` |
| approved → retired | evolve flow, after asset merge | `status: retired`, `evolved-into` set, file moved out of `approved/` (to `rejected/`-sibling `retired/`? No — retired files live in `instincts/retired/`; loader never sees them) |
| rejected → (anything) | never automatic | human may hand-move; system never resurrects |

**Gate invariant (FR-004 / constitution III)**: the loader reads exactly one
directory — `instincts/approved/` — and nothing else. State is enforced by
*location*; the `status` field exists for greppability and cross-checking
(a mismatch is reported as a warning by the review skill, never silently
fixed).

## Entity: Session summary

One file per session end: `session-data/<YYYY-MM-DD>-<session-id>.md`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `session-id` | string | yes | From the harness. |
| `date` | ISO datetime | yes | Session end time. |
| `cwd` | string | yes | Working directory (main checkout or worktree path). |

Body: 5–15 lines — what was worked on, decisions made, unresolved threads.
No secrets (scrubbed). The loader injects only the **latest** summary;
retention keeps the last K summaries (research.md D9), older ones deleted by
the same prune pass as pending TTL.

## Entity: Learned store

Not a file — a directory contract (full layout in
[contracts/store-layout.md](contracts/store-layout.md)):

```text
<main-repo>/.vibe/learned/
├── session-data/                  # session summaries (last K kept)
└── instincts/
    ├── pending/                   # extraction output; TTL-pruned
    ├── approved/                  # ONLY directory the loader reads
    ├── rejected/                  # archive; dedup input; never pruned
    └── retired/                   # graduated instincts; provenance kept
```

Relationships and invariants:

- **Resolution**: always relative to the *main* repository root (worktree
  sessions resolve through the shared git metadata — never a nested store
  inside `.vibe/worktrees/*`). Non-git directories fall back to the cwd
  with a visible notice.
- **Exclusion**: the store path is excluded from version control via the
  repo-local ignore mechanism, restored idempotently before every write.
- **Backup**: `instincts/approved/` mirrors to
  `~/.local/share/vibe/backup/<project-id>/approved/` on every approval and
  retirement (write events, no scheduler). `project-id` = short hash of the
  git remote URL, falling back to the repo path hash.
- **Atomicity**: every file write is temp-file + rename within the same
  filesystem; concurrent session ends may interleave but never corrupt.

## Entity: Review verdict

Not persisted as its own file — a decision applied to one pending instinct
by the review skill. Outcomes:

| Verdict | File effect | Other effects |
|---|---|---|
| Approve | move to `approved/` | `last-confirmed` ← today; backup mirror |
| Improve then approve | edit in place, then as Approve | edits summarized in `## Review notes` |
| Absorb | move to `rejected/` | the absorbing edit (to a rule/skill/CLAUDE.md) is proposed to the user, never auto-applied outside the store |
| Reject | move to `rejected/` | none |

## Entity: Evolved asset

A draft skill (`skills/<name>/SKILL.md`) or rule addition produced by the
evolve skill from a cluster of approved instincts. Carries provenance in its
frontmatter/header: `evolved_from: [<instinct-ids>]`. Delivered as working-
tree changes for normal git review — never committed or merged by the
system. On merge, source instincts transition approved → retired with
`evolved-into` pointing at the asset path.

## Validation rules (enforced by code)

1. An instinct file missing any required field is **malformed**: loader
   skips it with a warning naming the file and field (FR-013); review skill
   reports it; nothing crashes.
2. `id` collision across states: extraction must not create a pending
   instinct whose `id` exists anywhere in the store (FR-007 dedup floor).
3. Evidence entries and summary bodies pass the secret-pattern scrub before
   write (same pattern classes as `hooks/security/protect-secrets.py`);
   a scrub hit redacts the value and flags the file for review attention.
4. Injected block hard caps: ≤ N instincts (default 20, research.md D8) and
   ≤ 200 lines / 25 KB total — truncation drops oldest-`last-confirmed`
   first and appends one line stating how many were omitted (no silent
   truncation).
