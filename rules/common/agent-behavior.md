# Agent behavior — common

Always-on floor for how an agent *acts* on a task — distinct from how code
should read (`coding-style`) or what's safe (`security`). These are
language-agnostic conduct rules: the failure modes here are the ones that
survive a clean-looking diff and a passing test, so no linter catches them.
The deep "how" — planning, decomposition, review workflow — lives in
skills; this file is the short list of things to never do.

## Scope discipline

- Change only what the task requires. No drive-by refactors, reformatting,
  renames, or dependency bumps in code the task didn't touch — an
  unrelated edit hides the real change from review and widens the blast
  radius of a mistake.
- If you spot a worthwhile improvement outside scope, note it for the
  human; don't fold it silently into the diff.

## Verify before you assert

- Call only APIs, flags, config keys, and imports you have confirmed
  exist — in the codebase or the installed dependency's actual surface. A
  plausible-looking method is a hallucination until verified; guessing
  invents bugs, and a guessed *package* name is a typosquat waiting to be
  installed (see [security](security.md)).
- Prefer reading the real definition over recalling it from memory; the
  installed version may differ from what you remember.

## Report only what happened

- Never claim a result you didn't produce: don't say tests pass, a command
  ran, a build is green, or a task is done without having actually run it
  and seen the outcome. A false "done" costs far more than an honest
  "blocked" — it moves the failure downstream to someone with less context.
- A stub, `TODO`, or `NotImplementedError` is unfinished work; say so
  plainly rather than presenting it as complete.
- When something fails or is skipped, surface it with the evidence
  (the error, the skipped step) — don't bury it.

## Follow what's already there

- Match the surrounding code's existing patterns, libraries, file
  layout, and naming before introducing a new approach; consistency the
  reader already relies on beats your preferred style. Introduce a new
  pattern only with a reason the existing one can't satisfy, and apply it
  consistently when you do.

## Don't game the checks

- Never weaken, skip, comment out, or delete a test to make a suite pass.
  A green run that no longer asserts the behavior is worse than a red one —
  it hides the regression instead of reporting it.
- Ship a bug fix with a regression test that fails before the fix and
  passes after; a fix with no test invites the same bug back.
- The same holds for types and lints: fixing the cause beats silencing the
  check. A suppression is a last resort that states its reason (per
  [coding-style](coding-style.md)).

## Debug causes, not symptoms

- Reproduce before you fix: without a command that failed before the
  change and passes after it, "fixed" is a guess wearing a claim's
  clothes.
- Fix the cause, not the symptom. Swallowing the exception, deleting the
  assertion, adding a retry or a sleep — each makes the failure invisible
  while the defect ships. Any of these is only a *mitigation*, stated as
  such with the real cause named.
- Change one thing per attempt, and after two failed fixes stop patching
  and re-investigate — each further guess is made in a context polluted
  by the last one, so attempts stop converging. The full loop (evidence
  before hypotheses, circuit breakers, RCA reporting) is the `debugging`
  skill.
