# Implementation Plan: Learned Context

**Branch**: `001-learned-context` | **Date**: 2026-07-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-learned-context/spec.md`

## Summary

Reviewed, file-based memory (ADR 0003): sessions end with a batch pass that
writes a session summary and extracts candidate lessons ("instincts") into a
`pending` store with evidence; a human reviews them (approve / improve /
absorb / reject); only the `approved` store is readable by the session-start
loader, which injects a capped, condensed learned-context block. Approved
clusters graduate into canonical skills/rules via an evolve flow with
provenance. Technical approach: two Python stdlib hook scripts (SessionStart
loader, SessionEnd capture trigger) following the existing `hooks/security/`
conventions, a headless background extraction pass, and two user-invocable
skills (`instinct-review`, `evolve`) — all storage as plain Markdown files
under `.vibe/learned/` with an out-of-repo backup for `approved/`.

## Technical Context

**Language/Version**: Python 3.9+ (hook scripts, stdlib only — matches
`hooks/security/` convention); Markdown (skills, instinct files)

**Primary Dependencies**: none (stdlib-only hooks; extraction uses the
`claude` CLI already present in the target environment; `git` for store
resolution)

**Storage**: plain files — `.vibe/learned/{session-data,
instincts/{pending,approved,rejected}}` per project (git-excluded);
`~/.local/share/vibe/backup/<project-id>/` mirror of `approved/`

**Testing**: pytest (unit tests per hook script: loader gate, budget, scrub,
prune, store resolution; integration tests feeding fixture stdin JSON to the
scripts end-to-end)

**Target Platform**: Claude Code on Linux/macOS (hooks wired via
`.claude/settings.json`, per-project opt-in). Other harnesses: explicitly
degraded, owned by planned `vibe sync` (constitution II). Windows: store
paths work; backup path falls back to `%LOCALAPPDATA%\vibe\` (documented,
not CI-tested in this feature).

**Project Type**: harness content pack — hook scripts + skills + file
formats (no app/server code)

**Performance Goals**: SessionStart loader completes < 500 ms (must not
delay session start); extraction runs synchronously inside the SessionEnd
hook with an internal ~120 s cap (docs confirm detached children may be
killed at session cleanup — research.md D2), best-effort: a failed or
timed-out extraction skips cleanly and visibly, never blocks session exit
beyond its cap

**Constraints**: injected block ≤ 200 lines / 25 KB (SC-003); loader
structurally unable to read outside `approved/` (FR-004); no secrets in any
written file (SC-006); all store writes atomic (temp file + rename) to
survive parallel session ends

**Scale/Scope**: single-developer per project store; expected steady state
tens of approved instincts, pending queue bounded by TTL prune; 2 hook
scripts + 2 skills + ~4 contract documents

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|---|---|---|
| I | Canonical sources, generated targets | ✅ Pass | Hooks live canonically in `hooks/learned/`, skills in `skills/`; nothing generated is hand-patched. Wiring is documented JSON for `settings.json` (opt-in), same as `hooks/security/`. |
| II | Explicit capability degradation | ✅ Pass | Feature is declared Claude Code-native; other harnesses degrade visibly (documented in the hook pack README, adapter work deferred to `vibe sync`). No no-op adapters are shipped. |
| III | Human-approved learning | ✅ Pass | The feature *is* this principle: instincts born `pending` with confidence + evidence (FR-002/003), loader path-gated to `approved/` only (FR-004), no automatic approval anywhere. |
| IV | Safe repository mutation | ✅ Pass | Git-exclusion uses the repo-local ignore mechanism add-only and idempotently; prune/retire delete only files inside the store the system itself registered; backup writes only under its own `~/.local/share/vibe/` namespace. No `--dry-run`-needing shared-file mutations. |
| V | Documentation ships with code | ✅ Pass (obligation) | Plan includes same-change updates: `hooks/learned/README.md`, `ARCHITECTURE.md`, `AGENTS.md` docs map, and graduation of spec decisions per constitution governance. Tracked as tasks in Phase 2. |
| VI | Observable verification | ✅ Pass | quickstart.md defines runnable checks per user story; SC-002 (gate) and SC-006 (no secrets) get automated tests, not inspection. |

**Post-design re-check (after Phase 1)**: no violations introduced; design
artifacts keep the gate structural (separate directories, loader globs
`approved/` only) and all mutations inside registered namespaces. No entries
needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-learned-context/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── instinct-file.md      # Instinct file format (frontmatter schema, states)
│   ├── store-layout.md       # Store paths, resolution, backup, git exclusion
│   ├── context-block.md      # Injected learned-context block format + budget
│   ├── hook-io.md            # SessionStart/SessionEnd hook I/O contract
│   └── review-verdicts.md    # Review + evolve command contracts
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
hooks/
├── security/                      # existing — conventions to match
└── learned/                       # NEW hook pack
    ├── README.md                  # what/why, wiring JSON, degradation note
    ├── load-learned-context.py    # SessionStart: resolve store → render block → stdout
    ├── capture-learned-context.py # SessionEnd: write summary, run extraction (capped, best-effort)
    ├── extract-instincts.py       # extraction pass: transcript → pending instincts (headless claude)
    └── lib/
        └── learned_store.py       # shared: store resolution (worktree-aware), atomic
                                   # writes, frontmatter parse, scrub, prune, backup

skills/
├── instinct-review/               # NEW skill: guided review (/instinct-review)
│   └── SKILL.md
└── evolve/                        # NEW skill: cluster → draft skill/rule (/evolve)
    └── SKILL.md

tests/
└── hooks/learned/
    ├── test_load_learned_context.py    # gate, budget, recency, malformed-skip, no-store
    ├── test_capture_learned_context.py # summary write, trivial-session skip, atomicity
    ├── test_learned_store.py           # resolution (worktree/no-git), scrub, prune, backup
    └── fixtures/                       # sample stores, transcripts, hook stdin JSON
```

**Structure Decision**: mirror the only existing executable-content pattern
in the repo (`hooks/security/`): a self-contained hook pack under
`hooks/learned/` with stdlib-only Python and a README that carries the
`settings.json` wiring block. Review/evolve ship as skills (canonical in
`skills/`, auto-symlinked via `.claude/skills/`) because they are
user-invoked workflows, not lifecycle automation. Tests introduce the
repo's first `tests/` tree — pytest, no new dependencies beyond dev-time
pytest itself.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
