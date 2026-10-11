# Testing Anti-Patterns

Read this when writing or changing tests, adding mocks or test utilities,
when a suite is green but confidence is low, or when pruning a bloated suite. Core principle: **test what the
code does, not what the mocks do.**

## Contents

1. Tautological tests
2. Testing mock behavior
3. Testing implementation details
4. Incomplete mocks
5. Assertion theater
6. Test-only production code
7. Change detectors and permutation explosion
8. The classic catalog (quick reference)
9. Gate: before you add a mock

## 1. Tautological tests

The assertion computes the expected value the same way the code does — the test
passes by construction and can never disagree with the implementation.

```js
// ❌ Tautological: expected value copied from the code's own logic
const expected = items.reduce((s, i) => s + i.price, 0);
expect(cartTotal(items)).toBe(expected);

// ✅ Independent: expected value stated from the spec
expect(cartTotal([{ price: 3 }, { price: 4 }])).toBe(7);
```

The agent-flavored variant: run the code, see the output, paste that output into
the assertion. The test now blesses whatever the code happened to do — including
the bug. Expected values come from the requirement, never from running the
implementation.

## 2. Testing mock behavior

Stub a return value, then assert the result equals the stubbed value — the test
verifies the mocking framework, not the code.

```js
// ❌ Tests the mock
api.fetchUser = jest.fn().mockResolvedValue({ name: "An" });
expect(await getUser(1)).toEqual({ name: "An" });

// ✅ Tests your logic around the boundary
api.fetchUser = jest.fn().mockResolvedValue({ name: "An", deleted: true });
expect(await getUser(1)).toBeNull(); // your rule: deleted users are hidden
```

Warning signs: mock setup longer than test logic; test breaks when the mock
changes but not when the code changes; assertions checking that a method *was
called* rather than what resulted; you can't explain why the mock is needed.

## 3. Testing implementation details

The tell: a pure refactor breaks the test while behavior is unchanged — the
safety net now punishes exactly the activity it exists to enable.

- Assert results at public interfaces, not call sequences on collaborators.
- The urge to test a private method is design feedback: extract it or test it
  through the public path.
- In UI tests, select semantically (role, label, `data-testid`), not by CSS
  structure that styling changes will break.

## 4. Incomplete mocks

Mocking only the fields the current test touches. The next test — or production —
meets the real object, whose shape differs from every mock in the suite. Mock
the complete data structure as it exists in reality, ideally built by one shared
factory so shape drift shows up in one place.

## 5. Assertion theater

Tests that execute code but verify nothing: no assertions ("for coverage"),
assertions that can't fail (`expect(x).toBeDefined()` on a value that is always
defined), snapshot tests nobody reads, or `console.log` dressed as verification.
Each green checkmark that verifies nothing is worse than no test — it
manufactures confidence.

The deletion test: if you can revert the production change and the test still
passes, the test verifies nothing about that change. (This revert-and-rerun
check is cheap and worth actually running for regression tests.)

## 6. Test-only production code

Methods, flags, or branches in production classes that exist only so tests can
reach them (`resetForTesting()`, `if (process.env.TEST_MODE)`). The production
API grows a second, untested personality. Restructure instead: inject the
dependency, extract the pure function, or test through the real interface.

## 7. Change detectors and permutation explosion

A change detector fails on any edit to what it watches — a reword, a rename, a
restyle — and almost never on a real bug. Its "fix" is regenerating the
expectation, which teaches everyone to stop reading failures. Shapes seen in
one real agent-written suite:

- A whole system prompt compared to a 300-line golden file, refreshed with
  `UPDATE_GOLDEN=1` after every wording change.
- Literal-token pins on prose: `"ALWAYS" not in description`,
  `len(words) <= 120`, `"80,000" in prompt`.
- Source inspection: `"trigger=profile.x" in inspect.getsource(build)` — breaks
  on a rename, passes when the call is wrong.
- SQL substrings on a recording fake: `"ESCAPE" in sql` held for the broken
  clause too.
- Expected values copied from a price or config table, and absence guards like
  `not hasattr(config, "old_flag")`.

Fix: assert observable behavior — the rows a real in-memory DB returns, the
prompt's output on an eval case — or delete the test. SKILL.md's Scope lists
these kinds so they never get written.

**Permutation explosion** is the sibling smell: one behavior asserted over and
over — the same five invalid IDs re-run for every route that shares one
validator, 29 assertions for a one-line `includes(raw.trim().toLowerCase())`
copied across three parsers. Test the shared predicate once, as a table; give
each caller one case proving it uses the predicate.

## 8. The classic catalog (quick reference)

From James Carr's list — name them when you see them:

| Name | Smell |
|---|---|
| The Liar | passes, looks valid, verifies nothing it claims to |
| The Giant | dozens of assertions in one test — first failure hides the rest |
| Excessive Setup | pages of arrange before one line of act |
| The Free Ride | new assertion piggybacks on an existing test instead of a new case |
| The Inspector | reaches into private state to assert |
| The Mockery | so many mocks the real code barely runs |
| The Slow Poke | slow test everyone learns to skip |
| Success Against All Odds | written to pass, never seen red |
| Hidden Dependency | passes only after some other test has run |

## 9. Gate: before you add a mock

1. What side effects does the real thing have? Do I understand them?
2. Does this test depend on any of those side effects?
3. Is the real thing actually slow/external/nondeterministic — or am I mocking
   "to be safe"?

If unsure, run the test against the real implementation first and observe what
it needs, then mock at the lowest level that isolates the genuine boundary.
"Mock it to be safe" is how suites end up testing mocks. Mocks are tools to
isolate — never things to test.
