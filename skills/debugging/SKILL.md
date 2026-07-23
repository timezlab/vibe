---
name: debugging
description: Systematic debugging and root-cause-analysis discipline for coding agents — reproduce the failure before touching code, gather evidence before hypothesizing (read the whole error, trace backward to the origin, sweep recent changes, bisect regressions), test one stated hypothesis at a time with the smallest discriminating experiment, fix the cause rather than suppress the symptom, and stop to re-investigate after failed fixes instead of stacking patches. Use whenever anything misbehaves — a bug report, failing or flaky test, crash, wrong output, performance regression, build/CI failure, "works on my machine" — or when the user says "debug", "why is this failing", "root cause", "trace this", "sửa lỗi", "tìm nguyên nhân", "lỗi này do đâu", "tại sao lại fail" — and especially when a fix has already failed once or the cause seems obvious. Hands off to tdd for writing the fix (failing test first); git-workflow owns bisect mechanics and history archaeology.
---

# Debugging

Reproduce → evidence → one hypothesis → fix the cause → verify fresh. The
order is the discipline: every phase exists to stop a specific, documented
way agents lose hours.

**The one non-negotiable: no fix before the cause is demonstrated.** Not
suspected, not "probably" — demonstrated: a reproduction that fails, a
traced origin, an experiment that separated your hypothesis from the
alternatives. A fix proposed before that point is a guess that may compile,
pass, and still be wrong — and its failure costs more than the
investigation it skipped, because now the context carries a dead theory
too. Everything below exists to get you to "demonstrated" *fast*, not to
slow the fix down.

**Why structure beats intuition here:** the best-documented agent debugging
failures are all shortcuts through this loop — patching a plausible cause
that was never confirmed, "fixing" by making the check stop failing
(SWE-bench audits found large fractions of passing patches weaken or dodge
the test rather than fix the bug), and thrashing: repeated corrections in a
context polluted by the previous failed attempts. A human debugging by
guesswork wastes their own time; an agent doing it also *sounds confident
while doing it*, which is worse. The loop below is what "address the root
cause, don't suppress the error" looks like as concrete steps.

**Scale, don't skip.** For a shallow bug the phases collapse naturally —
reading one error message *is* the investigation, and the whole loop takes
two minutes. The discipline is that no phase is skipped, not that every bug
gets a ceremony. Time pressure and "the fix is obvious" are the states in
which guessing feels cheapest and costs most — that is when the loop earns
its keep, because a wrong obvious fix costs a failed attempt *plus* a
polluted context.

## Phase 1 — Reproduce

Make it fail on command before changing anything. Capture the exact
command and the exact failure output — that pair is the oracle: it is what
"fixed" will mean later. No reproduction, no verifiable fix.

- Prefer the tightest reproduction available: a single test > a script >
  a manual multi-step flow. Shrink the input while the failure persists —
  a minimal repro often *is* the diagnosis.
- **Can't reproduce?** Gather more data — logs, exact inputs, environment
  diff against where it fails — rather than fixing blind. A fix for a
  failure you can't trigger is a guess you can't verify.
- **Intermittent?** Frequency is data: run it 20 times and count. Flaky
  tests have a small set of real causes (timing waits, shared state, test
  pollution, ordering) — read
  [references/flaky-tests.md](references/flaky-tests.md) before touching
  one.
- **Performance bug?** The reproduction is a measurement. Profile or time
  it before and after; "feels faster" is not an oracle.

## Phase 2 — Evidence before hypotheses

Quit thinking and look. Guessing from the symptom alone is how the wrong
layer gets patched. Collect, in rough order of information-per-minute:

- **Read the entire error**, not the first line: the full stack trace, the
  deepest frame that is *your* code, the values in the message. Most
  reported "mystery bugs" state their cause in text nobody finished
  reading.
- **Trace backward from the symptom to the origin.** The crash site is
  where bad state *arrived*, rarely where it was *made*. Follow the chain —
  what produced this value? what called that with these arguments? — until
  the first point where reality diverged from intent. Fix belongs at the
  origin; patching the crash site leaves the same bad state free to hit
  the next consumer.
- **Sweep recent changes.** `git diff`, recent commits, dependency bumps,
  config and environment changes. Bugs correlate overwhelmingly with what
  changed last.
- **"It used to work" → bisect before theorizing.** When a known-good
  state exists, binary search (`git bisect` over commits, or delta-shrink
  the failing input/config) finds the breaking change in log₂ steps —
  faster and more certain than any hypothesis about code you'd otherwise
  re-read for hours. Mechanics live in **git-workflow**.
- **Check the plug.** Verify the trivial assumptions explicitly: right
  branch, right environment, the file actually saved/built/deployed, the
  cache actually cleared, the test running the code you think it runs. The
  embarrassing causes are frequent precisely because nobody checks them.
- **Compare against a working analog.** Same codebase, similar path that
  works: read it fully (skimming produces false differences) and list
  every difference, however small — the bug lives in that list.
- **Multi-component path?** Add instrumentation at each boundary to see
  where good data turns bad, instead of hypothesizing across three layers
  at once — see [references/instrumentation.md](references/instrumentation.md)
  for tagging, Heisenbug cautions, and cleanup.

## Phase 3 — One hypothesis, smallest test

- State it explicitly, with its evidence: "I think X because Y, so if I do
  Z I should observe W." A hypothesis you can't attach a predicted
  observation to is a hunch, not a hypothesis.
- Run the **smallest experiment that discriminates** — one variable at a
  time. A log line, a narrowed input, a one-line probe. Multi-change
  experiments produce unreadable results: if it works you don't know why,
  and now neither does the next reader.
- **Keep the audit trail visible** — hypotheses tested and refuted, in
  your reply or the task todos. It stops you from re-testing refuted ideas
  after a long session or a context compaction, and it is the raw material
  for the report at the end.
- Refuted → new hypothesis from the evidence. Never leave the speculative
  change in place while trying the next idea — revert first; stacked
  half-fixes are how codebases accumulate mystery.
- "I don't understand X yet" is a legitimate, reportable state — it points
  the next experiment. Pretending to understand and patching anyway is the
  red-flag list below.

## Phase 4 — Fix the cause

The hand-off point to **tdd**: write the failing test that reproduces the
bug (usually the Phase 1 repro, distilled to the lowest level that shows
it), watch it fail, then implement **one fix, at the origin found in Phase
2, with nothing bundled** — no drive-by refactors, no "while I'm here".

These are symptom suppressions, not fixes — each makes the failure
invisible while the defect ships:

- catching and swallowing the exception
- deleting or loosening the failing assertion, or hardcoding its expected
  value
- adding a retry loop or `sleep` around flaky behavior
- widening a type / adding a null-check at the crash site when the real
  question is why the value was null
- suppressing the warning that was the symptom

Any of these can be a legitimate *mitigation* — but only stated as such,
with the root cause named and an issue/TODO linking the real fix, never
silently in place of one.

## Phase 5 — Verify like a skeptic

- Re-run the **original Phase 1 repro, fresh**, and the surrounding suite.
  Evidence is the command plus its output — "should be fixed now" is a
  claim, not a verification, and if you didn't watch it pass you don't
  know that it passes.
- Your explanation should predict both directions: with the fix the repro
  passes, without it it fails. The failing-test-first flow from tdd gives
  you this for free; if you fixed without one, back the fix out mentally —
  if you can't say why the failure would return, you don't yet know why it
  left.
- Remove all diagnostic instrumentation before presenting the diff
  (per [references/instrumentation.md](references/instrumentation.md)) —
  debug noise in the diff buries the actual fix.

## Circuit breakers

- **After 2 failed fixes: stop fixing.** Your context now contains two
  wrong theories and their wreckage, and further attempts inherit that
  bias — this is the documented point where correction loops stop
  converging. Return to Phase 2 with the new evidence, or hand the failure
  to a fresh-context investigator (the `root-cause-analyst` lane) that
  arrives without your assumptions.
- **3+ failed fixes, or every fix breaks something else:** the frame is
  wrong, not the patch. This is no longer a bug hunt but a design problem —
  stop, write up the evidence trail, and raise it with the user instead of
  producing patch number four.
- **"No root cause found"** is claimable only after the full loop, for
  genuinely environmental/external causes — and it pairs with added
  handling and monitoring, never with silence. Treat the claim itself with
  suspicion: most "no root cause" is investigation that stopped early.

## Reporting — root cause vs trigger vs contributing factors

When explaining the bug (in the fix's commit body, the reply, or an
RCA/postmortem the user asks for), separate three things the word "cause"
conflates:

- **Trigger** — what exposed it now (the input, the commit, the timing).
- **Root cause** — the defect itself, at the origin.
- **Contributing factors** — what let it exist and ship: the missing test,
  the unvalidated boundary, the ambiguous contract. Usually 2–3, and they
  are where the regression test and any hardening work come from —
  fixing only the defect leaves the door it walked through open.

Blameless framing: factors are about the system ("the schema wasn't
validated at the boundary"), not the author ("X forgot to validate").

## Red flags — stop, return to Phase 1

Catch yourself on any of these:

- "Quick fix now, investigate later" — later never comes; the symptom is
  gone.
- Proposing a fix before reading the full error / trace.
- "It's probably X" with no observation that could distinguish X from
  not-X.
- Editing multiple files speculatively in one attempt.
- "One more try" after two failed fixes (see circuit breakers).
- Explaining a fix with "should work" instead of a fresh passing run.
- Reaching for retry/sleep/try-catch to make a symptom disappear.
- Changing the test instead of the code without declaring it (tdd's
  read-only rule).
- **You are the bug**: re-running the same failing command unchanged,
  editing files that don't exist, looping — the same discipline applies to
  your own behavior; capture the state, form a hypothesis about your loop,
  change exactly one thing.

## Boundaries

- Writing the fix and its regression test → **tdd** (this skill ends at a
  named root cause and hands the repro over as the failing test).
- `git bisect` mechanics, reflog archaeology, "what broke this" history
  work → **git-workflow**.
- The bug is a vulnerability, or smells like one → **security-audit** for
  the finding discipline; fixing it comes back through here and tdd.
- Dispatching a fresh-context investigation, or parallel competing
  hypotheses → **parallel-agents**; the
  `root-cause-analyst` agent definition preloads this skill for that lane.
