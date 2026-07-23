# Flaky tests

Read this when a test fails intermittently — passes on retry, fails only
in CI, only under parallelism, or only in certain orders. Flakiness is not
weather; it is a small, enumerable set of real defects, and "re-run until
green" ships whichever one you have.

First: **measure it**. Run the test 20–50 times (`--repeat`, a shell
loop) and record the failure rate, alone vs. with the full suite, serial
vs. parallel. Those three comparisons alone usually name the cause class
below.

## Contents
1. The cause classes
2. Timing: replace waits-for-time with waits-for-condition
3. Test pollution: find the polluter by bisection
4. When a fixed timeout is legitimate

## 1. The cause classes

| Signature | Likely class | Confirm by |
|---|---|---|
| Fails alone and in suite, ~fixed rate | Real race/timing bug in code or test | Vary machine load; shrink to the racing pair |
| Passes alone, fails in full suite | Test pollution (shared state from an earlier test) | Bisection over the preceding tests (§3) |
| Fails only in parallel runs | Shared resource: port, file path, DB row, global | Run serial; grep for hardcoded ports/paths/ids |
| Fails only in some orders | Order dependence — a test depends on another's side effects | Run with randomized order + fixed seed |
| Fails only in CI | Environment delta: slower machine (timeouts), env vars, locale/TZ, missing service | Diff the environments; raise CI verbosity |
| Depends on date/time/randomness | Unpinned clock or seed | Grep for `now()`/`random` in the path; pin and re-run |

Two class-level rules:

- A flaky test is a **real bug with a wide repro** — in the test, the
  fixture, or occasionally the product code. Deleting it, skipping it, or
  wrapping it in auto-retry discards the report, not the defect. Auto-retry
  in particular converts "we have a race" into "we occasionally ship a
  race", silently.
- The fix mirrors the class: pin the clock/seed, isolate the shared
  resource per-test, make each test own its setup and teardown, or fix
  the actual race the test caught.

## 2. Timing: replace waits-for-time with waits-for-condition

The single most common flake: `sleep(2)` / `setTimeout(500)` guessing how
long an async operation takes. Too short on a loaded CI machine → flaky;
long enough to be safe → the suite crawls. Both, usually.

Replace every arbitrary wait with a poll on the **real condition** the
test needs:

```ts
// Instead of: await sleep(2000)   // hope the server is up by then
await waitFor(() => server.isReady(), { timeout: 5000, interval: 50 })
```

- Wait for the condition the next step actually requires ("file exists",
  "job status is done", "element visible"), not a proxy for it.
- The timeout on a condition-wait is a *failure deadline*, not a duration
  guess — generous is fine, because the wait returns the moment the
  condition holds; on timeout it should fail loudly, naming the condition
  it was waiting for.
- Most test frameworks ship this (`waitFor`, `eventually`,
  `awaitility`-style helpers) — prefer the framework's over hand-rolling.

## 3. Test pollution: find the polluter by bisection

When a test passes alone but fails in the suite, some earlier test leaks
state into it (globals, module caches, files, DB rows, env vars). Don't
read every preceding test — bisect:

1. Confirm: victim alone → pass; full suite up to victim → fail.
2. Run the *first half* of the preceding tests + the victim.
3. Fails → polluter in that half; passes → other half. Recurse: log₂(n)
   runs to a single test.
4. Then diff the world that polluter leaves behind (the global, the file,
   the row) against a clean run — that delta is the bug.

Fix at the polluter (restore what it touches) *and* consider hardening the
victim (own its preconditions in setup) — the polluter pair is one
instance; the shared mutable state that allowed it is the contributing
factor.

## 4. When a fixed timeout is legitimate

Rarely, a fixed wait is genuinely correct — but only when all three hold:

1. It comes **after** a condition-wait (the state is known; you now wait a
   deliberate duration, e.g. a debounce window that must elapse),
2. the duration derives from a **known constant in the code** (the
   debounce interval, the poll period), not from a guess about machine
   speed, and
3. a comment names that constant — so the next reader knows it is a
   designed delay, not a hopeful one.

A `sleep` that fails any of the three is a flake in incubation: replace it
with a condition-wait (§2).
