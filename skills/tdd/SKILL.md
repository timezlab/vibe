---
name: tdd
description: Test-driven development discipline for coding agents — write a test list, watch each test fail for the right reason, commit tests before implementing, write minimal code to green, refactor only on green, and never weaken a test to make it pass. Use whenever implementing any feature, bugfix, refactor, or behavior change — BEFORE writing any production code — including when the user says "implement X", "fix this bug", "add tests", "viết test", "làm theo TDD", "sửa bug", or when deciding whether existing tests actually verify behavior. Also use when a test is failing and the temptation is to change the test. Skip only for throwaway spikes, generated code, or pure config — and say so explicitly before skipping.
---

# Test-Driven Development

Write the test first. Watch it fail. Write the minimum to pass. This order is not
ritual — it is the only way to know the test can fail at all.

**Why order matters more for agents than for humans:** a model that writes
implementation first and tests after is grading its own homework — tests and code
come from the same reasoning, so the tests statistically confirm the same mistakes
the code contains. And empirically (METR, 2025), telling a model "don't cheat,
don't weaken the tests" barely changes behavior; 70–95% of reward-hacking persists
through explicit warnings. What works is **structure**: a test that exists before
the code, committed where tampering shows up in the diff, verified by output the
orchestrator or user can read. That structure is this skill.

**Core principle:** if you didn't watch the test fail, you don't know that it
tests anything.

## The loop (Canon TDD)

1. **List** — write down the test scenarios the change needs, as behaviors, not
   implementation steps. Don't design internals here. Record the list somewhere
   visible — your reply, a comment atop the test file, or the task's todos. The
   list is the spec you are about to hold yourself to; a list that exists only
   in your head is the one you'll quietly shorten when items get inconvenient.
2. **Red** — turn exactly *one* item into a concrete, runnable test. Run it.
   Watch it fail — see below for what counts.
3. **Green** — write the simplest production code that passes this test and keeps
   all previous tests passing.
4. **Refactor** — on green only, improve structure without changing behavior.
   Re-run the suite after.
5. **Repeat** until the list is empty. New scenarios discovered mid-work go on
   the list, not into the current test.

One item at a time. Converting the whole list to tests up front (horizontal
slicing) delays feedback and locks in interface guesses before the first test has
taught you anything.

## Red — a failure you can trust

Run the new test and read the output before touching production code. Confirm
all three:

- It **fails**, not errors. An import error or typo failing is noise, not signal —
  fix until it fails for real.
- It fails **because the behavior is missing**, with the failure message you
  predicted. A surprise message means the test targets something other than what
  you think.
- If it **passes immediately**, you are testing behavior that already exists —
  the test proves nothing about your change. Rewrite it. (This rule polices the
  red phase. A probe added *after* green to confirm generalization or pin a
  contract may legitimately pass on arrival — that's verification, not a red.)

A test that was written but never executed does not count as red, and neither
does "it would obviously fail." A compile error counts as red only when the
missing symbol is in *production* code that the test references — the test would
compile and pass if the code existed. A syntax error or bad import inside the
test file itself is always noise, never signal.

## Structural gates

These are the agent-specific rules that make the discipline tamper-evident:

- **Commit the tests before writing any implementation.** If tests are later
  altered to pass, the diff says so — that is the safety net, for you as much as
  for the user. Only when committing is genuinely impossible (no repo, user
  forbids commits) fall back to keeping test edits strictly separate from
  implementation edits, and say that's what you're doing. The rhythm: each
  red→green cycle yields its own pair of commits — the test, then the
  implementation that passes it. Never fold implementation into a commit whose
  message says it's a test change; a mislabeled commit defeats the
  diff-as-evidence gate exactly where it's needed most.
- **During green, test files are read-only.** A failing test after you've
  implemented means the implementation is wrong until proven otherwise. If you
  become convinced the test itself is wrong, stop, say so, show why, and change
  it as its own visible step — never silently inside a "fix".
- **Evidence, not claims.** Report red and green — in your reply to the user or
  orchestrator — as the actual command run, the suite's summary counts (passed/
  failed), and the output lines for the test in question. Summary counts are
  what keep the excerpt honest: "3 failed" can't be cropped out of "the relevant
  lines". "Tests pass" without output is an assertion, not a verification; if
  you haven't run it in this session, you can't claim it.
- **Generalize, don't special-case.** As tests get more specific, code should get
  more generic. Code that pattern-matches test inputs (`if input == "example"`)
  passes the suite and fails reality — tests verify the solution; they are not
  the solution. The check, after each green: would this code work for a valid
  input the suite doesn't contain? If not, add that test now and generalize
  (triangulation) instead of shipping a lookup table.

## Green — minimal means minimal

Write only what this test demands. No extra parameters "while you're here", no
features the list doesn't mention, no refactoring of neighboring code — that
comes at step 4 or on its own list item. Three legitimate ways to get to green:

- **Obvious implementation** — if the real code is trivially clear, type it.
- **Fake it** — return the constant, then let the next test force the real logic.
- **Triangulate** — when unsure of the right abstraction, add a second example
  and generalize only what two examples force.

If obvious implementation starts failing, downshift to fake-it. Struggle at green
is design feedback: a test that is hard to pass simply usually means the
interface is wrong, not that you need cleverness.

## Refactor — the step everyone skips

Fowler: the most common TDD failure is neglecting this step, leaving "a messy
aggregation of code fragments." On green, clean up both new and old code —
naming, duplication, structure — then re-run the suite. Rules:

- Never refactor on red. Behavior work and structure work use different judgment;
  doing both at once does both badly.
- A green suite *before* a refactor doesn't prove the refactor safe — only
  re-running *after* does.
- Don't abstract on the first duplication; wait for the pattern to appear twice.

**Refactoring code that has no tests:** first write characterization tests that
pin the *current* behavior at the public interface, then restructure. These
tests pass immediately by design — they document what the code does today, not
what it should do — and, like post-green probes, are a legitimate exception to
the "passes immediately → rewrite it" rule in Red. Until they exist, the module has no
safety net and refactoring is guessing.

## Bug fixes

Reproduce the bug as a failing test before fixing it. Proving the bug exists is
what separates a fix from a tweak — and the test stays as the regression guard.
If a high-level test caught the bug, write the lowest-level test that reproduces
it and fix from there. Never fix a bug without a test that failed because of it.

## What a good test looks like

- Asserts **behavior at a public interface** — "given x, the result is z" — never
  call sequences or private state. The acid test: a pure refactor should not
  break it.
- One behavior per test, named after that behavior.
- Arrange–act–assert, minimal setup. A huge setup block is a design smell in the
  code under test, not a fact of life.
- **Test logic, not UI components.** Default targets are business rules, data
  transforms, and state logic — not component rendering. Don't write UI
  component/snapshot tests unless the user asks for them: they are brittle
  (break on styling churn), slow, and mostly verify the framework. When a
  behavior lives inside a component, that's the cue to extract it into a pure
  function or hook and test *that* — the UI layer stays a thin shell.
- **Mock external boundaries only** (network, clock, filesystem, DB); run your
  own code for real. Before adding any mock or test utility — and whenever a
  suite is green but confidence is low — read
  [references/anti-patterns.md](references/anti-patterns.md) — most fake-green
  suites are built from the patterns catalogued there.

Coverage is risk-driven, not ritual: test until fear turns to boredom. Error
paths and edge cases (empty, null, huge, concurrent) usually hold more fear than
another happy path.

## When TDD doesn't apply

- **Spikes and throwaway prototypes** — code written to answer a question, not to
  keep. The contract: declare the spike up front, and settle it in the same work
  session — delete the code, or backfill tests before any of it is kept (an
  unmerged spike commit is labeled as such). "Spike" is not a word that defers
  TDD to later; it's a promise the code won't survive without tests.
- **Generated code and pure configuration.**
- If tempted to skip for any other reason ("too simple", "just this once", "I'll
  add tests right after"), that's a rationalization — simple code breaks too, and
  tests-after verify what you remembered to build, not what was required. When
  genuinely unsure, ask the user rather than deciding silently.

## Boundaries

- Committing, branching, PRs → **git-workflow** (this skill only dictates *what*
  gets committed when: tests before implementation).
- The feature's task breakdown and spec → **speckit-\*** flow; each implement
  task then runs this loop.
- Independent test-writer/implementer/reviewer agents → **parallel-agents**; the
  writer/reviewer split is the strongest version of the structural gates above.
