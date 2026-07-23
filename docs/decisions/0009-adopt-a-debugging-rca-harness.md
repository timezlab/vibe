# Adopt a debugging/RCA harness (rules + skill + agent, no hooks)

**Status:** accepted
**Date:** 2026-07-23
**Deciders:** Liam Lee

## Context

Debugging was the next harness gap after security ([ADR 0008](0008-adopt-a-layered-security-harness.md)):
no first-party debugging skill exists (anthropics/skills ships none; an
open issue proposes only a skill-*triggering* debugger), while the
best-adopted community formalization is obra/superpowers'
`systematic-debugging`. Research for this decision (2-lane survey,
2026-07-23: full extraction of superpowers `systematic-debugging` +
`verification-before-completion` and ECC's `agent-introspection-debugging`
+ `verification-loop`; web survey of Anthropic best-practices docs, Agans'
9 rules, git-bisect/delta-debugging literature, SWE-bench reward-hacking
audits, Google SRE postmortem practice) established:

1. **Agent debugging failures are shortcut-shaped**: guess-patching
   unconfirmed causes, "fixing" by weakening the check (SWE-bench audits:
   large fractions of passing patches dodge rather than fix), and
   thrashing — repeated corrections in a context polluted by prior failed
   attempts (Anthropic documents "/clear after two failed corrections" as
   the mitigation).
2. **The methodology is stable and convergent**: superpowers' four-phase
   gate, Agans' rules ("make it fail", "quit thinking and look", "change
   one thing", "if you didn't fix it, it ain't fixed"), and SRE RCA all
   reduce to the same loop — reproduce → evidence → single hypothesis →
   fix at origin → fresh verification — plus circuit breakers.
3. **SRE practice adds the reporting frame**: trigger vs root cause vs
   contributing factors (plural, blameless) — richer than the single
   "root cause" field and the source of regression tests and hardening.

## Decision

One debugging concern, three layers — deliberately **no hooks layer**:

- **`rules/common/agent-behavior.md` § "Debug causes, not symptoms"** —
  always-on floor (per [ADR 0007](0007-adopt-claude-native-rule-packs.md)):
  reproduce before fixing, no symptom suppression, one change per
  attempt, stop after two failed fixes. Common-only: debugging conduct
  doesn't vary by language, so it extends the existing `agent-behavior`
  topic rather than opening a new one.
- **`skills/debugging/`** — the deep "how": five-phase loop scaled to bug
  depth, circuit breakers (2 fails → fresh context; 3+ → architecture
  question), trigger/root-cause/contributing-factors reporting, red-flag
  self-checks; references for boundary instrumentation (tagged probes,
  Heisenbug cautions, cleanup) and flaky tests (cause-class table,
  condition-based waiting, pollution bisection).
- **`agents/debugging/root-cause-analyst.md`** — dispatchable
  fresh-context diagnosis lane preloading the skill (the lane pattern of
  [ADR 0006](0006-predefine-research-agents-by-modality.md)/0008).
  Diagnosis-only by contract — it returns a verdict + evidence chain, the
  main lane writes the fix via tdd. `model: inherit`: diagnosis quality
  scales with model. Exists because context pollution is the one failure
  mode a skill in the *same* context cannot fix — the mitigation is a
  reader without the accumulated assumptions.

Cross-cutting choices:

- **No hooks**: the security harness's failure modes are command-shaped
  (blockable strings, scannable writes); debugging's are judgment-shaped
  (a plausible-but-wrong hypothesis produces the same tool calls as a
  right one). The deterministic gate that *does* exist — tests committed
  before the fix, tamper-evident in the diff — already belongs to the tdd
  skill's structural gates. A regex hook guessing at "guessing" would be
  noise, not enforcement.
- **Calm register over superpowers' "Iron Law" rhetoric**: same gates
  (phase order, red flags, escape-hatch skepticism), but each rule
  carries its why instead of all-caps mandates — matching the repo's
  prompt-guru principles and Claude 4+ guidance that heavy emphasis
  causes overtriggering.
- **Verification is not duplicated**: superpowers ships a separate
  `verification-before-completion` skill; here that floor already exists
  in `rules/common/agent-behavior.md` ("report only what happened") and
  tdd's evidence rules — the skill's Phase 5 points at them rather than
  restating them.

## Alternatives considered

- **Port superpowers' `systematic-debugging` verbatim** — rejected: CC-BY
  content in a distinct rhetorical register (Iron Laws, rationalization
  tables) that conflicts with the repo's calm-with-why house style, and
  it lacks the flaky-test and RCA-reporting surfaces this repo needs;
  synthesis over port.
- **A verification/Stop hook enforcing "tests ran before done"** —
  rejected for now: brittle (which command proves *this* task?), overlaps
  tdd's commit-first gate, and Anthropic's own escalation ladder puts
  deterministic Stop-gates at the *project* level, not the canonical
  content level. Revisit when `hooks/` grows per-project verification
  wiring.
- **Fold debugging into tdd** (its "Bug fixes" section) — rejected: tdd
  begins where the cause is known (write the failing test); the expensive
  failures happen *before* that point, and a section-sized treatment
  can't carry evidence-gathering, circuit breakers, or the agent lane.
- **A new `rules/common/debugging.md` topic file** — rejected: the floor
  is four lines of conduct; a new always-loaded file per topic is how
  rule packs bloat. It extends `agent-behavior`, which already owns
  "don't game the checks".

## Consequences

**Better:**

- The three documented agent failure modes each get a structural counter:
  guess-patching → phase order + floor rules; check-weakening → symptom-
  suppression list + tdd cross-link; thrashing → circuit breakers + a
  dispatchable fresh-context lane.
- Flaky-test discipline (measure → classify → condition-waits → pollution
  bisection) exists in the harness for the first time.

**Worse:**

- Nothing enforces the loop deterministically — by design (see above),
  but it means the floor rules are the only always-on pressure.
- Skill boundaries with tdd/git-workflow put one bug-fix journey across
  three skills; mitigated by explicit hand-off lines in each.

**Must now be true:**

- `debugging`, `tdd`, and `git-workflow` keep their hand-off boundaries
  aligned (repro → failing test → bisect mechanics); a change to one
  boundary updates the others in the same PR.
- The root-cause-analyst lane stays diagnosis-only; giving it write tools
  would collapse the fresh-context guarantee it exists for.

## Revisit if

Anthropic ships a first-party debugging skill; `hooks/` gains per-project
verification wiring (the rejected Stop-gate becomes wirable); or evals
show the calm register underperforms the Iron-Law register on debugging
benchmarks.
