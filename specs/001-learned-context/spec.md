# Feature Specification: Learned Context

**Feature Branch**: `001-learned-context`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "Setup Learned context — the reviewed, file-based
memory system decided in ADR 0003: agent sessions produce candidate lessons
(instincts) with evidence, a person reviews them, and only approved lessons
load into future sessions, with a graduation path into shared skills and
rules. Design decisions were fixed in a prior research pass (2026-07-23):
in-repo visible storage under `.vibe/learned/` (gitignored), a code-enforced
pending→approved gate, batch extraction at session end, capped injection at
session start, explicit division of labor with the platform's own automatic
memory, and dedup at both the extraction and review gates."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approved lessons shape new sessions (Priority: P1)

As a developer using agent sessions in a project, I want lessons I have
approved to be present in every new session's context automatically, so the
agent stops repeating mistakes I already corrected and applies project
know-how without being re-told.

**Why this priority**: This is the consuming end of the whole loop — without
loading, captured lessons have no effect. It is also independently valuable
on its own: a user can hand-write an approved lesson today and benefit
immediately, before any capture automation exists.

**Independent Test**: Hand-author one approved instinct file in the project's
learned store, start a new agent session, and observe the lesson present in
the session's loaded context; place a second file in `pending` and observe it
absent.

**Acceptance Scenarios**:

1. **Given** a project with 3 approved instincts, **When** a new session
   starts, **Then** the session context contains a learned-context block
   listing all 3 lessons (trigger + action) and the latest session summary.
2. **Given** a project with instincts in `pending` and `rejected` states,
   **When** a new session starts, **Then** none of that content appears in
   the session context.
3. **Given** more approved instincts than the load budget allows, **When** a
   new session starts, **Then** the block contains at most the budgeted
   number, most-recently-confirmed first, and never exceeds the size cap.
4. **Given** a session running inside a project worktree, **When** it starts,
   **Then** it loads the same learned store as sessions in the main checkout
   (no per-worktree fragmentation).
5. **Given** a project with no learned store at all, **When** a session
   starts, **Then** the session starts normally with no learned-context block
   and no error.

---

### User Story 2 - Sessions capture candidate lessons (Priority: P2)

As a developer, I want each agent session to end by saving a short session
summary and extracting reusable lessons as *pending* candidates with cited
evidence, so knowledge produced during work is not lost when the session
closes — without anything unreviewed steering future sessions.

**Why this priority**: This is the producing end of the loop. It depends on
the store and format existing (US1) and is the step that makes the system
self-sustaining rather than hand-fed.

**Independent Test**: Run a session containing at least two corrections of
the same agent behavior, end it, and verify a pending instinct file exists
with evidence citing those corrections, plus a dated session summary file —
and that nothing was written to the approved store.

**Acceptance Scenarios**:

1. **Given** a session in which the user corrected the same agent behavior
   twice, **When** the session ends, **Then** a pending instinct exists whose
   evidence cites those verifiable events (corrections, failing→passing
   checks), created with `pending` status and a confidence value.
2. **Given** a candidate lesson that duplicates existing guidance (project
   instructions, rule packs, the platform's own memory, or an existing
   instinct), **When** extraction runs, **Then** no duplicate pending
   instinct is created.
3. **Given** any session end, **When** extraction and summary writing run,
   **Then** no secret material (credentials, tokens, keys) appears in any
   written file.
4. **Given** a first-ever capture in a repository, **When** the store is
   created, **Then** the store path is excluded from version control
   automatically (a person never has to remember to do it).
5. **Given** a short or trivial session (nothing worth learning), **When**
   it ends, **Then** no pending instinct is created (no noise candidates).

---

### User Story 3 - Reviewing the pending queue (Priority: P3)

As the human in the loop, I want to review pending instincts as plain files
visible in my editor and via a guided review command, approving, rejecting,
or absorbing each one, so that I control what steers future sessions and bad
patterns die in review.

**Why this priority**: Until dedicated tooling exists, approval can be done
by moving files by hand (US1's gate already enforces safety), so guided
review is an experience improvement on top of a working loop.

**Independent Test**: With 2 pending instincts present, run the review
command, approve one and reject the other, and verify the approved one loads
in the next session while the rejected one is archived and never re-proposed.

**Acceptance Scenarios**:

1. **Given** pending instincts exist, **When** the user runs the review
   command, **Then** each candidate is presented with its trigger, action,
   evidence, and any overlap found with existing guidance (rules, skills,
   project instructions, platform memory), and the user chooses a verdict:
   approve / improve-then-approve / absorb into existing guidance / reject.
2. **Given** a verdict is chosen, **When** the review completes, **Then** the
   file moves to the matching state (`approved`, edited-then-`approved`,
   `rejected` archive) and the decision takes effect in the next session.
3. **Given** a rejected instinct, **When** later sessions extract lessons,
   **Then** the same pattern is not re-proposed (the archive is consulted).
4. **Given** pending instincts older than a retention window, **When** the
   store is next touched, **Then** stale pending candidates are pruned so
   the queue cannot grow without bound.

---

### User Story 4 - Lessons graduate into shared assets (Priority: P4)

As a team member, I want clusters of related approved instincts to be
promotable into canonical skills or rules in the repository, with provenance
back to the instincts they came from, so personal learning compounds into an
org asset that reaches every contributor through normal code review.

**Why this priority**: This is the long-term payoff (per the product design:
"approved learning that compounds"), but it needs a populated approved store
to act on, so it comes last.

**Independent Test**: With 3+ approved instincts sharing a domain, run the
evolve command and verify it proposes a draft skill/rule carrying provenance
to the source instincts, as reviewable repository changes — and that the
source instincts are retired from the approved store once the asset merges.

**Acceptance Scenarios**:

1. **Given** several approved instincts in one domain, **When** the user
   runs the evolve command, **Then** a draft canonical asset (skill or rule)
   is generated in the repository working tree with provenance listing the
   source instinct ids, submitted through the normal review flow — never
   merged automatically.
2. **Given** an evolved asset is merged, **When** the source instincts are
   retired, **Then** they no longer load at session start (no double
   loading of a lesson and the rule it became).

---

### Edge Cases

- A cleanup command wipes ignored files (e.g. `git clean -fdx`): the learned
  store is lost. Approved instincts must be recoverable from a backup
  location outside the repository.
- A session runs inside a worktree stored under the same namespace directory
  as the learned store: resolution must reach the main repository's store,
  never create a nested store inside the worktree.
- The store's ignore entry is missing or was hand-removed: capture must
  restore it before writing, so personal, unreviewed lessons never end up in
  a commit.
- A malformed instinct file (bad metadata, missing required fields) is in
  `approved/`: loading must skip it with a visible warning, not crash the
  session start or silently load partial content.
- Two sessions end at the same time (parallel panes): concurrent writes to
  the store must not corrupt or lose candidates.
- The platform's own automatic memory already records a fact that an
  instinct also captures: extraction must not duplicate it; review surfaces
  the overlap so the human can absorb or reject.
- A repository has no git remote or is not a git repository at all: capture
  and load must still work (store resolution falls back gracefully) or
  degrade with a clear message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST persist learned content as plain, human-
  readable files inside the project at a dedicated, visible location
  (`.vibe/learned/`), nested one level under the shared `.vibe/` namespace,
  and MUST keep that location out of version control automatically.
- **FR-002**: Every captured lesson (instinct) MUST record: a stable id, a
  trigger ("when…"), an action, cited evidence referencing verifiable events
  (user corrections, failing→passing checks), a confidence value, scope,
  source, creation and last-confirmed dates, and a lifecycle state.
- **FR-003**: Instincts MUST be born in `pending` state; nothing may create
  content directly in the approved store except an explicit human approval.
- **FR-004**: The loading mechanism MUST be structurally unable to read
  anything except the approved store (gate enforced by storage location, not
  by checking a field) — pending and rejected content never reaches a
  session. *(Constitution Principle III.)*
- **FR-005**: At session start, the system MUST inject a condensed learned-
  context block: at most N approved instincts (trigger + action form) within
  a fixed size budget, selected most-recently-confirmed first, plus the
  latest session summary. Absence of a store yields no block and no error.
- **FR-006**: At session end, the system MUST write a dated session summary
  and extract candidate instincts in one batch pass over the session —
  skipping trivial sessions — with all output scrubbed of secret material.
- **FR-007**: Extraction MUST check existing guidance (project instructions,
  rule packs, platform memory, existing instincts in all states) and MUST
  NOT create a candidate that duplicates it; the rejected archive MUST
  prevent re-proposal of previously rejected patterns.
- **FR-008**: A guided review flow MUST present each pending instinct with
  its evidence and detected overlap, and offer four verdicts: approve,
  improve-then-approve, absorb into existing guidance, reject. Decisions
  take effect from the next session.
- **FR-009**: Pending candidates older than a retention window MUST be
  pruned automatically so the review queue stays bounded.
- **FR-010**: Sessions running in project worktrees MUST resolve to the main
  repository's learned store; no per-worktree stores may be created.
- **FR-011**: Approved instincts MUST be backed up outside the repository so
  that ignored-file cleanup does not destroy accumulated learning.
- **FR-012**: An evolve flow MUST cluster related approved instincts and
  generate draft canonical assets (skills/rules) in the repository working
  tree with provenance to source instinct ids, entering the normal review
  flow — and MUST retire source instincts from the approved store once
  their asset is merged.
- **FR-013**: Malformed files in the store MUST be skipped with a visible
  warning; a session MUST always be able to start.
- **FR-014**: The learned-context system MUST coexist with the platform's
  own automatic memory by division of labor: reviewed behavioral lessons
  live here; the platform's memory remains the unreviewed scratch layer.
  Overlap is handled by FR-007/FR-008, not by disabling either system.

### Key Entities

- **Instinct**: One reviewed-or-reviewable lesson. Attributes: id, trigger,
  action, evidence list, confidence, scope, source, dates, lifecycle state
  (`pending` → `approved` | `rejected`; `approved` → retired-by-evolution).
- **Session summary**: Dated, human-readable recap of one session; the
  latest one provides continuity to the next session. Replaced, not
  compounded.
- **Learned store**: The per-project home of summaries and instincts,
  visible in the project tree, excluded from version control, shared across
  worktrees of the same repository, mirrored to an out-of-repo backup.
- **Review verdict**: The human decision on a pending instinct — approve /
  improve-then-approve / absorb / reject — each with a defined file-state
  outcome.
- **Evolved asset**: A draft skill or rule generated from an instinct
  cluster, carrying `evolved_from` provenance, delivered through normal
  repository review.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A lesson approved (or hand-authored) in the store appears in
  the loaded context of 100% of subsequent sessions in that project,
  including sessions started from worktrees.
- **SC-002**: Content in `pending` or `rejected` state appears in loaded
  session context in 0% of sessions — verified by an automated check, not
  inspection.
- **SC-003**: The injected learned-context block never exceeds its fixed
  size budget (≤ 200 lines / 25 KB) regardless of how many instincts have
  accumulated.
- **SC-004**: After a session containing two or more corrections of the same
  agent behavior, a pending candidate citing that evidence exists at session
  end in at least 8 of 10 such sessions.
- **SC-005**: Reviewing one pending instinct (read, verdict, effect queued
  for next session) takes under one minute of user time.
- **SC-006**: Zero secret material (credentials, tokens, keys) is present in
  any file the system writes, verified by scanning the store in tests.
- **SC-007**: A session started with a deliberately corrupted store file
  still starts and surfaces a warning in 100% of trials.

## Assumptions

- Claude Code is the first and only target platform for this feature;
  other harnesses arrive later via the sync mechanism with explicitly
  degraded capability (constitution Principle II). Hook-based session
  start/end integration is assumed available there.
- Storage layout is fixed by prior decision: project scope at
  `.vibe/learned/{session-data, instincts/{pending,approved,rejected}}`;
  `.vibe/` is a shared namespace that will also hold worktrees. A global
  (cross-project) store location is reserved but out of scope here.
- Per ADR 0003, every instinct carries a confidence value and evidence at
  creation. Deterministic confidence *updates* (confirm/contradict/decay)
  are out of scope for this feature; the human review verdict is the
  governing quality gate, and confidence is informational until an update
  mechanism is designed.
- Always-on observation (recording every tool call during the session) is
  deliberately excluded; capture happens as one batch pass at session end.
  Research showed the always-on observer is the highest-maintenance part of
  the reference design.
- Promotion of instincts from project scope to a global cross-project scope
  is out of scope for this feature (reserved for a follow-up).
- The learning review UI ("Learning tab") is a later product phase; in this
  feature, the editor file tree plus the review command are the review
  experience.
- Backup cadence for the out-of-repo mirror follows write events (backup on
  approve) rather than a scheduler; losing *pending* candidates to cleanup
  is acceptable, losing *approved* instincts is not.
