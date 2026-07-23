# Phase 0 Research: Learned Context

**Feature**: [spec.md](spec.md) · **Date**: 2026-07-23

Two research inputs feed this phase: the 2026-07-23 three-lane pattern
survey (ECC source read, community patterns, academic grounding — run before
this spec existed) and a hook-contract verification against current Claude
Code documentation (code.claude.com/docs, fetched 2026-07-23). All Technical
Context unknowns are resolved below; no NEEDS CLARIFICATION remains.

## D1 — Hook I/O contract (verified against official docs)

**Decision**: SessionStart hook injects the learned-context block via
**plain stdout** (documented: stdout is added to context; JSON
`additionalContext` is the alternative). Matcher: `startup|clear|compact` —
not `resume`, whose restored transcript already contains the block.
SessionEnd hook receives `reason` + common fields; its stdout is user-visible
only, it cannot block session end, default timeout 600 s.

**Rationale**: plain stdout is the simplest contract that satisfies FR-005
and concatenates predictably when other SessionStart hooks exist. Injecting
on `compact` re-asserts the block after compaction may have summarized it
away.

**Alternatives considered**: JSON `additionalContext` output — equivalent
capability, more moving parts; revisit only if plain stdout proves lossy.
Injecting on `resume` — rejected: duplicates the block in restored context.

## D2 — Extraction execution model

**Decision**: extraction runs **synchronously inside the SessionEnd hook**,
wrapped in an internal ~120 s cap, invoking headless `claude -p` (haiku,
`--max-turns 1`, restricted `--allowedTools`, JSON output) over the session
transcript. Failure or timeout skips extraction visibly (stderr note) and
exits 0 — best-effort side work, deliberately fail-open with a stated
reason.

**Rationale**: official docs confirm detached children spawned from hooks
"may be terminated by environment cleanup when the session ends" — exactly
our moment. A killed background extractor silently loses lessons; a
synchronous capped pass inside the generous 600 s hook budget is
deterministic. ECC's always-on background observer (its alternative answer)
is also its highest-maintenance component — its own comments document CPU
pegging, runaway processes, and lost counters.

**Alternatives considered**: detached `nohup`/`setsid` extractor — rejected
on the documented kill caveat (UNVERIFIED survival = not a foundation);
always-on PreToolUse/PostToolUse observation (ECC v2) — rejected as out of
spec scope and maintenance-heavy; manual-only `/learn` command — rejected:
FR-006 requires automatic capture (manual review is where the human sits,
not manual capture).

## D3 — Storage location and layout

**Decision**: per-project store at
`.vibe/learned/{session-data, instincts/{pending,approved,rejected,retired}}`,
one level under the shared `.vibe/` namespace (which will also hold
`worktrees/`). Global cross-project store reserved at
`~/.local/share/vibe/` (not built here).

**Rationale**: user decision (2026-07-23): in-repo visible storage — the
IDE file tree is the review UI until the Learning tab exists; per-project
scoping falls out for free. ADR 0003 named `~/.claude/timezlab/…` but
declared exact paths tunable at implementation time; this stays within that
allowance. ECC deliberately stores *outside* `~/.claude` to avoid
write-guard friction — in-repo storage sidesteps the same issue.

**Alternatives considered**: `~/.claude/timezlab/…` (ADR 0003 sketch) —
invisible to the editor, potential write-guard friction; XDG
`~/.local/share/vibe/projects/<hash>/` — harness-portable but equally
invisible; both rejected on the visibility requirement.

## D4 — Confidence: informational field, human verdict as gate

**Decision**: every instinct carries `confidence` at creation (ADR 0003
"must now be true") set by the extractor from evidence count; **no
automatic confidence updates** (confirm/contradict/decay) in this feature.
The review verdict (approve/improve/absorb/reject) is the governing gate.

**Rationale**: ECC's source shows its documented confidence-update rules
(+0.05/−0.1/weekly decay) are prompt text with zero enforcing code — the
field is write-once decoration there, and ECC's own `/learn-eval` later
replaced numeric scoring with holistic verdicts ("forcing rich qualitative
signals into numeric scores loses nuance"). Academic grounding agrees:
LLM-as-judge self-preference bias (swings of −38%→+90% in one study) makes
model-updated confidence untrustworthy as a gate.

**Alternatives considered**: deterministic confidence updates wired to
review events — deferred, not rejected (a follow-up can add it once real
usage shows which events should move the number); dropping the field —
rejected: ADR 0003 requires it.

## D5 — Git exclusion mechanism

**Decision**: before every store write, idempotently ensure an exclusion
entry for `.vibe/` in `$(git rev-parse --git-common-dir)/info/exclude`
(add-only append if absent). Do not touch the project's shared `.gitignore`.

**Rationale**: `info/exclude` is repo-local (never committed, no merge
surface — constitution IV favors this over mutating a shared file), and
living under `--git-common-dir` makes one entry cover all worktrees.
Restoring it before every write satisfies the "a person never has to
remember" edge case even if hand-removed.

**Alternatives considered**: writing `.gitignore` — touches a shared,
merge-sensitive file (would need preview-first flow per constitution IV)
and dirties the working tree; documenting "add it yourself" — fails the
spec's automatic-exclusion requirement (FR-001, US2 scenario 4).

## D6 — Store resolution (worktrees, non-git)

**Decision**: resolve the store root as: `git rev-parse --git-common-dir`
→ its parent directory is the main checkout → `<main>/.vibe/learned/`.
Outside any git repo, fall back to `<cwd>/.vibe/learned/` with a one-line
notice in hook output.

**Rationale**: `--git-common-dir` returns the main repository's `.git` from
any worktree, giving all panes one shared store and preventing nested
`.vibe/` inside `.vibe/worktrees/*` (ADR 0002 layout). Graceful non-git
fallback keeps the spec's "must still work" edge case.

**Alternatives considered**: `git rev-parse --show-toplevel` — returns the
*worktree* root, exactly the fragmentation bug to avoid; refusing to run
outside git — worse UX than a visible fallback.

## D7 — Backup and project identity

**Decision**: mirror `instincts/approved/` (and `retired/`) to
`~/.local/share/vibe/backup/<project-id>/` on approval and retirement
events. `project-id` = first 12 hex chars of SHA-256 of the normalized git
remote URL; fallback: hash of the main-checkout absolute path. Windows:
`%LOCALAPPDATA%\vibe\backup\…` (documented; not CI-tested here).

**Rationale**: `git clean -fdx` destroys ignored files — the store is one
command away from loss; approved instincts are months of accumulated
review. Event-driven mirroring needs no scheduler and can't fall behind by
more than one un-mirrored write. Remote-URL hashing is machine-portable
(ECC v2.1's lesson after its repo-path-only phase).

**Alternatives considered**: scheduled backup — needs a daemon this feature
doesn't have; backing up `pending/` too — rejected, spec assumption
explicitly accepts losing pending to cleanup; committing the store —
rejected, personal unreviewed content must not enter shared history.

## D8 — Load budget and selection

**Decision**: defaults N = 20 instincts, hard cap 200 lines / 25 KB for the
whole block (summary included). Selection: `last-confirmed` descending.
Truncation is stated in the block ("… and M more approved instincts not
loaded"), never silent.

**Rationale**: mirrors the platform's own MEMORY.md discipline (200
lines / 25 KB, documented) and Anthropic's finding that adherence drops as
always-loaded content grows; every learned line competes with task context
(same argument as `rules/README.md`). Recency-first is the simplest defensible
policy; Generative-Agents-style relevance scoring is a follow-up, not a
foundation.

**Alternatives considered**: relevance/embedding retrieval — real
machinery, deferred until recency demonstrably fails; no cap — rejected,
SC-003 forbids it.

## D9 — Session summary retention

**Decision**: keep the latest 10 summaries; the prune pass (which also
TTL-deletes pending older than 30 days) removes older ones. Only the latest
is injected.

**Rationale**: summaries provide continuity, not compounding (ADR 0003
rejected summaries-only for exactly that reason) — a short tail is enough
for "what was I doing this week", and unbounded growth violates the store's
bounded-queue promise (FR-009 spirit).

**Alternatives considered**: keep-forever — unbounded; keep-1 — loses the
short tail that helps after a week away.

## D10 — Secret scrubbing

**Decision**: extractor and summary writer run all output through the same
credential-shape pattern classes used by
`hooks/security/protect-secrets.py` (AWS/GitHub/Google/Slack/GitLab/npm/
private-key shapes) before write; a hit redacts the value, notes the
pattern class, and flags the file for review attention.

**Rationale**: one pattern vocabulary across the harness (single source of
knowledge per coding-style rules); transcripts routinely contain env dumps
and pasted configs, and SC-006 demands zero secrets at rest.

**Alternatives considered**: trusting the extraction model's judgment —
rejected: SC-006 is verified by scanning, so the guarantee must be
deterministic code, not a prompt.

## D11 — Coexistence with platform auto-memory

**Decision**: keep Claude Code auto-memory enabled (division of labor:
auto-memory = unreviewed scratch/continuity; instincts = reviewed
behavioral lessons). Extraction dedup (FR-007) reads MEMORY.md's index as
one of its overlap sources; the review skill surfaces MEMORY.md overlap for
absorb/reject verdicts. The documented off-switch (`autoMemoryEnabled:
false` / `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, verified) is noted in the
pack README for users who want a single memory system, not flipped by us.

**Rationale**: the two systems answer different trust questions; disabling
native behavior from a hook pack would be surprising action-at-a-distance.
Strategically, instincts are the harness-agnostic canonical layer (`vibe
sync` can port files + hooks; MEMORY.md is Claude-specific).

**Alternatives considered**: disabling auto-memory — user-hostile default,
rejected; writing instincts *into* the platform memory dir — couples the
canonical store to one harness's cap/prune behavior, rejected.

## D12 — Testing approach

**Decision**: pytest, first `tests/` tree in the repo
(`tests/hooks/learned/`). Hook scripts are tested as processes (fixture
stdin JSON → assert stdout/exit/filesystem effects) plus unit tests on
`lib/learned_store.py`. The extraction LLM call is faked behind a small
seam (env var pointing at a stub command) so tests are hermetic; SC-002
(gate) and SC-006 (scrub) get dedicated automated tests.

**Rationale**: constitution VI demands runnable proof; process-level tests
match how the harness actually invokes hooks. Stdlib-only production code
keeps pytest a dev-only dependency.

**Alternatives considered**: shell-script test harness — weaker assertions,
no fixtures; testing through a live `claude` session — non-hermetic, slow,
and needs credentials in CI.
