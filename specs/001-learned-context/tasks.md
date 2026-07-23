# Tasks: Learned Context

**Input**: Design documents from `/specs/001-learned-context/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — the spec requires automated verification (SC-002 gate,
SC-006 secrets, SC-007 corruption resilience; constitution VI). Test tasks
come first in each phase and must fail before their implementation task.

**Organization**: Tasks grouped by user story (US1–US4 from spec.md) so each
story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (load), US2 (capture), US3 (review), US4 (evolve)
- All paths are repo-root-relative

## Path Conventions

Harness content pack (plan.md structure): hook pack `hooks/learned/`,
skills `skills/instinct-review/` and `skills/evolve/`, tests
`tests/hooks/learned/` (repo's first tests tree). No `src/`.

---

## Phase 1: Setup

**Purpose**: Directory skeleton and pytest wiring for the repo's first tests tree

- [X] T001 Create directory skeleton per plan.md: `hooks/learned/lib/`, `tests/hooks/learned/fixtures/` (empty `hooks/learned/README.md` placeholder allowed; real content lands in T011/T017)
- [X] T002 [P] Add pytest wiring: `tests/hooks/learned/conftest.py` (put `hooks/learned` and `hooks/learned/lib` on `sys.path` for unit imports; helper to build scratch git repos/stores in `tmp_path`) and minimal `pytest.ini` at repo root (`testpaths = tests`)

**Checkpoint**: `pytest tests/` collects 0 tests and exits cleanly

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared store library every story consumes — resolution, parsing, validation, atomic writes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Author shared fixtures in `tests/hooks/learned/fixtures/`: valid instinct files (per contracts/instinct-file.md canonical example), malformed variants (missing field, bad YAML, >10 KB, empty `## Action`), sample session summaries, hook stdin JSON samples
- [X] T004 Write failing unit tests in `tests/hooks/learned/test_learned_store.py`: store resolution (main checkout, worktree → same store via `--git-common-dir` parent, non-git fallback + notice, `--show-toplevel` never used), frontmatter parse/serialize round-trip (flat YAML subset only), validation (each malformed fixture rejected with named reason, id regex, 10 KB guard), atomic write (tmp+rename, same dir)
- [X] T005 Implement store resolution in `hooks/learned/lib/learned_store.py`: `git rev-parse --git-common-dir` → parent dir → `.vibe/learned/`; non-git fallback to cwd with one notice line; read never creates directories, write does `mkdir -p` (contracts/store-layout.md)
- [X] T006 Implement frontmatter parser/serializer + instinct validation in `hooks/learned/lib/learned_store.py`: stdlib-only flat-YAML-subset parser (scalars + single-level lists), required-field checks per contracts/instinct-file.md, 10 KB size guard, malformed ⇒ structured skip-with-reason (never raise to caller)
- [X] T007 Implement atomic write helper in `hooks/learned/lib/learned_store.py`: `<file>.tmp` + `os.replace` in same directory; ENOENT-tolerant delete/list helpers for concurrent session ends (contracts/store-layout.md Concurrency)

**Checkpoint**: `pytest tests/hooks/learned/test_learned_store.py` green — foundation ready, user stories can begin

---

## Phase 3: User Story 1 - Approved lessons shape new sessions (Priority: P1) 🎯 MVP

**Goal**: SessionStart loader injects a capped learned-context block read exclusively from `instincts/approved/` + latest summary. Hand-authored approved instinct works today — no capture automation needed.

**Independent Test**: Hand-author one approved and one pending instinct in a scratch repo, pipe SessionStart stdin JSON to the loader, and see the approved lesson in stdout with zero trace of the pending one (quickstart §1).

### Tests for User Story 1

- [X] T008 [P] [US1] Write failing tests in `tests/hooks/learned/test_load_learned_context.py` (process-level: pipe stdin JSON, assert stdout/stderr/exit — research.md D12): `test_gate_never_loads_pending_or_rejected` — content seeded in `pending/`, `rejected/`, `retired/` never appears in stdout (SC-002); budget — 30 approved ⇒ ≤ 20 instinct lines, ≤ 200 lines / 25 KB, explicit "…and N more" line (SC-003); ordering — `last-confirmed` descending; malformed approved file ⇒ skipped, stderr names file, exit 0 (SC-007); empty/absent store ⇒ empty stdout, exit 0; worktree cwd ⇒ identical output to main-checkout cwd (FR-010); latest session summary included, older ones not

### Implementation for User Story 1

- [X] T009 [US1] Implement `hooks/learned/load-learned-context.py`: read hook JSON from stdin, resolve store (read-only — never create/mutate), glob `instincts/approved/` ONLY, render block per contracts/context-block.md (header with count + `human-reviewed`, one `- [<domain>] <trigger> → <action>` line each, latest summary section), enforce budget with stated truncation, warnings to stderr, always exit 0, < 500 ms, no subprocess except `git rev-parse`
- [X] T010 [US1] Write `hooks/learned/README.md` (initial): what/why, store layout pointer, SessionStart wiring JSON (matcher `startup|clear|compact` — contracts/hook-io.md), how to hand-author an approved instinct (the MVP path)
- [X] T011 [US1] Run quickstart §1 validation: loader-in-isolation, worktree variant, empty-store variant; plus budget + corruption spot-checks from quickstart §5; fix anything that fails

**Checkpoint**: US1 fully functional — a hand-fed store steers real sessions

---

## Phase 4: User Story 2 - Sessions capture candidate lessons (Priority: P2)

**Goal**: SessionEnd writes a dated summary and extracts pending candidates (evidence + confidence) via capped synchronous headless extraction — scrubbed, deduped, never touching `approved/`.

**Independent Test**: Pipe SessionEnd stdin JSON with a corrections-bearing fixture transcript and a stubbed extractor; verify pending instinct + summary appear, `approved/` untouched, exclusion ensured, no secrets at rest (quickstart §2).

### Tests for User Story 2

- [X] T012 [P] [US2] Author capture fixtures in `tests/hooks/learned/fixtures/`: `stub-claude.sh` (echoes canned extraction JSON; variants for timeout/garbage output), `transcript-with-corrections.jsonl`, `transcript-trivial.jsonl` (< 10 user messages), transcript containing planted secret-shaped strings
- [X] T013 [P] [US2] Write failing tests in `tests/hooks/learned/test_capture_learned_context.py` (process-level, `VIBE_LEARNED_CLAUDE_CMD` pointed at stub): summary file written with correct name/frontmatter; trivial transcript ⇒ no summary, no candidates (FR-006); candidates land in `pending/` only — `approved/` byte-identical before/after (FR-003); dedup — candidate whose id exists in any state dir is dropped (FR-007); `test_no_secrets_at_rest` — planted secrets absent from every written file (SC-006); `info/exclude` gains `.vibe/` idempotently (FR-001); prune — pending older than 30 days deleted, 11th-oldest summary deleted, `approved/`/`rejected/`/`retired/` untouched (FR-009); extractor failure/timeout/garbage ⇒ exit 0, stderr note, store unchanged

### Implementation for User Story 2

- [X] T014 [US2] Extend `hooks/learned/lib/learned_store.py`: secret scrub reusing pattern classes from `hooks/security/protect-secrets.py` (research.md D10 — redact + flag, don't reuse code by import if it couples packs; copy patterns with a provenance comment), git-exclusion ensure (`git rev-parse --git-common-dir`/info/exclude, exact-line `.vibe/`, add-only idempotent, skipped on non-git), prune pass (pending TTL 30 days, keep newest 10 summaries, report pruned names)
- [X] T015 [US2] Implement `hooks/learned/extract-instincts.py`: build extraction prompt (transcript tail + dedup context: ids+triggers from ALL state dirs, `MEMORY.md` index if present, rule-pack filenames — contracts/hook-io.md), invoke `claude -p --model haiku --max-turns 1 --output-format json` (binary overridable via `VIBE_LEARNED_CLAUDE_CMD`), parse/validate output into candidate instincts (confidence heuristic: 2 evidence → 0.5, 3–5 → 0.7, > 5 → 0.85 — contracts/instinct-file.md)
- [X] T016 [US2] Implement `hooks/learned/capture-learned-context.py` in contract order (contracts/hook-io.md): resolve store → ensure exclusion → prune → triviality check (< 10 user messages ⇒ skip summary+extraction) → write summary → run extraction synchronously under internal 120 s cap → validate + scrub + atomic-write pending files → one-line stdout status (`learned: N candidates pending review (/instinct-review)`, silent when nothing written) → always exit 0
- [X] T017 [US2] Extend `hooks/learned/README.md`: SessionEnd wiring JSON, capture behavior + triviality/cap notes, explicit degradation statement for non-Claude-Code harnesses (constitution II — no silent no-op)
- [X] T018 [US2] Run quickstart §2 validation with the stub; fix anything that fails

**Checkpoint**: full capture→review-queue loop works; US1 unaffected (rerun its tests)

---

## Phase 5: User Story 3 - Reviewing the pending queue (Priority: P3)

**Goal**: `/instinct-review` presents each pending instinct with evidence + overlap report and applies the four verdicts; approvals mirror to the out-of-repo backup.

**Independent Test**: With 2 pending instincts, run `/instinct-review`, approve one and reject the other; verify file states, `last-confirmed`, backup copy, and next-session loading (quickstart §3).

### Tests for User Story 3

- [X] T019 [P] [US3] Write failing backup tests (extend `tests/hooks/learned/test_learned_store.py`): project-id derivation (normalized remote URL hash → 12 hex; path-hash fallback when no remote), mirror on approval/retirement events to `${XDG_DATA_HOME:-~/.local/share}/vibe/backup/<project-id>/` (redirect via env in tests), append-favoring semantics — store deletions never propagate to backup (contracts/store-layout.md)

### Implementation for User Story 3

- [X] T020 [US3] Extend `hooks/learned/lib/learned_store.py`: backup mirror function + a minimal CLI entry (`python3 hooks/learned/lib/learned_store.py backup|check <store>`) so the review/evolve skills can invoke backup and invariant checks without duplicating logic (note: same file as T014 — do not parallelize with US2)
- [X] T021 [US3] Create `skills/instinct-review/SKILL.md` per contracts/review-verdicts.md: precondition + invariant warnings (status/directory mismatch, malformed), per-instinct presentation in `created` order, overlap report (grep `rules/`, `skills/*/SKILL.md` frontmatter, `CLAUDE.md`/`AGENTS.md`, `MEMORY.md`, all instinct state dirs — quote matches with paths), four verdicts table with exact file effects (`last-confirmed` update, `## Review notes` append, backup on approve, absorb edits proposed as working-tree changes only)
- [X] T022 [US3] Validate + verify: `uvx --from 'skills-ref==0.1.1' agentskills validate skills/instinct-review`; run quickstart §3 live check (approve/reject, backup present, loader reflects verdicts, prune of backdated pending)

**Checkpoint**: humans control the gate end-to-end with sub-minute per-instinct review (SC-005)

---

## Phase 6: User Story 4 - Lessons graduate into shared assets (Priority: P4)

**Goal**: `/evolve` clusters approved instincts by domain, drafts a canonical skill/rule with `evolved_from` provenance as uncommitted working-tree changes, and retires sources in a separate explicit step after merge.

**Independent Test**: With 3 approved instincts sharing a domain, run `/evolve`; verify draft asset with provenance, nothing committed, sources still approved; after merge + retire step, sources in `retired/` with `evolved-into` and no longer loaded (quickstart §4).

### Implementation for User Story 4

- [X] T023 [P] [US4] Create `skills/evolve/SKILL.md` per contracts/review-verdicts.md: cluster by `domain` + trigger string grouping (no ML), draft asset in working tree following repo conventions (CONTRIBUTING.md) with `evolved_from: [<ids>]` provenance, NEVER commit/push/merge, retirement as separate explicit step (detect merged provenance or `--retire <asset-path>`; move `approved/` → `retired/`, set `status: retired` + `evolved-into`, mirror to backup via the T020 CLI)
- [X] T024 [US4] Validate + verify: `uvx --from 'skills-ref==0.1.1' agentskills validate skills/evolve`; run quickstart §4 (draft → merge → retire → loader no longer emits sources; retired never loads is already pinned by T008's gate test)

**Checkpoint**: all four stories independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Docs shipped in the same change (constitution V) and full-loop verification

- [X] T025 [P] Update `ARCHITECTURE.md`: add `hooks/learned/` pack, `tests/` tree, `.vibe/learned/` runtime store (not source), backup namespace
- [X] T026 [P] Update `AGENTS.md`: docs-map row for the learned hook pack, `pytest tests/` in Commands, note that `/instinct-review` and `/evolve` exist
- [X] T027 [P] Add `docs/tech-debt.md` entries: Windows backup path documented-only (not CI-tested), confidence values informational pending an update mechanism (spec assumptions)
- [X] T028 Full verification: `pytest tests/` all green, then complete quickstart top-to-bottom (§0–§5) in a scratch repo; confirm every SC-referenced check ran (SC-002 T008, SC-003 T008, SC-006 T013, SC-007 T008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)** → **Foundational (P2)** → all user stories → **Polish (P7)**
- Foundational (T003–T007) BLOCKS every story: all consumers use `learned_store.py`

### User Story Dependencies

- **US1 (P1)**: only Foundational. No other story needed (hand-authored instincts).
- **US2 (P2)**: only Foundational. Produces what US3 consumes but is testable alone (stub + fixtures).
- **US3 (P3)**: Foundational + T014 (US2's lib extension — scrub/prune land in the same `learned_store.py` that T020 extends). Review of hand-placed pending files works without the rest of US2.
- **US4 (P4)**: Foundational + hand-authored approved instincts; backup CLI from T020 for the retire step.
- ⚠️ **Same-file constraint**: T005–T007, T014, T019–T020 all touch `hooks/learned/lib/learned_store.py` (and its test file) — execute these in ID order even if their stories run otherwise in parallel.

### Within Each Story

Fixtures → failing tests → implementation → README/docs → quickstart validation.

### Parallel Opportunities

- Phase 1: T002 ∥ T001
- Phase 2: T003 ∥ T004 (fixtures vs tests, different files)
- After Foundational: T008 (US1 tests) ∥ T012/T013 (US2 fixtures/tests) ∥ T023 (US4 skill) — all different files
- T021 (review skill) ∥ T023 (evolve skill) — different files
- Phase 7: T025 ∥ T026 ∥ T027

---

## Parallel Example: after Foundational checkpoint

```bash
# Different files, no shared state — safe to run together:
Task: "T008 failing loader tests in tests/hooks/learned/test_load_learned_context.py"
Task: "T012 capture fixtures in tests/hooks/learned/fixtures/"
Task: "T013 failing capture tests in tests/hooks/learned/test_capture_learned_context.py"
Task: "T023 evolve skill in skills/evolve/SKILL.md"
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1 (T001–T002) → Phase 2 (T003–T007) → Phase 3 (T008–T011)
2. **STOP and VALIDATE**: quickstart §1 in a scratch repo; wire the hook in one real project and confirm `/context` shows the block
3. This alone delivers value: hand-authored approved lessons steer sessions today

### Incremental Delivery

1. + US2 → the loop self-sustains (candidates appear without hand-feeding)
2. + US3 → guided review replaces hand-moving files
3. + US4 → learning compounds into shared skills/rules
4. Each story leaves prior stories' tests green (rerun the suite at every checkpoint)

## Notes

- Tests in this feature are process-level where possible (pipe stdin JSON to the real script) — that is what makes SC-002's "structurally unable" claim testable (research.md D12)
- Never weaken a failing gate/scrub test to pass — those two tests are the feature's constitution-III proof
- Commit after each task or logical group; commit format `chore(learned): …` / `skill: instinct-review (…)` per AGENTS.md
