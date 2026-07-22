# Use reviewed, file-based memory (instincts) instead of automatic learning

**Status:** accepted
**Date:** 2026-07-22
**Deciders:** Liam Lee

## Context

Agent sessions produce reusable knowledge (project quirks, fixes,
preferences) that is lost when the session ends. Fully automatic learning
loops exist (e.g. ECC continuous-learning), but unreviewed learned content
silently steers future sessions — a wrong "lesson" compounds invisibly.

## Decision

Adopt the **instinct + human review** model (after ECC continuous-learning
v2, deliberately not fully automatic):

1. A SessionStart hook loads the latest session summary plus at most N
   **approved** instincts above a confidence threshold.
2. A SessionEnd hook saves the summary and extracts candidate patterns as
   `pending` instinct files (with confidence and evidence).
3. Review happens via `/instinct-review` (CLI) or the Learning tab (web UI);
   only approved instincts ever load.
4. `/evolve` clusters related instincts into new skills/rules committed to
   this repo — personal learning becomes an org asset.

Storage is **file-based and harness-agnostic**, separated per project:
`~/.claude/timezlab/{session-data, instincts/pending, instincts/approved}`
(exact paths tunable at implementation time).

## Alternatives considered

- **Fully automatic learning** (auto-approve instincts) — rejected: a wrong
  inference poisons every future session with no visibility; the review cost
  is small compared to debugging misbehavior it prevents.
- **Session summaries only, no instincts** — rejected: summaries don't
  compound; there is no path from "learned once" to "team asset".
- **Database-backed store** — rejected: file-based storage stays greppable,
  diffable, and portable across harnesses.

## Consequences

**Better:**

- Humans control what steers future sessions; bad patterns die in review.
- `/evolve` gives individual learning a graduation path into shared skills.

**Worse:**

- Review is a manual chore; unreviewed queues can pile up and delay the
  benefit.

**Must now be true:**

- Only instincts in an `approved` state load at SessionStart; nothing in
  `pending` ever reaches a session.
- Every instinct file carries confidence and evidence at creation.

## Revisit if

Review queues consistently exceed what a person will triage (signal to add
better ranking/batching, not auto-approval), or a harness ships native memory
that satisfies the review-first requirement.
