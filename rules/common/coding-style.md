# Coding style — common

Always-on floor for writing code in any language. Language packs
([typescript](../typescript/coding-style.md), [python](../python/coding-style.md))
extend this file; where they conflict, the language pack wins. The deeper
"how" — per-language guidance, review checklists, gate setup — lives in the
`coding-style` skill.

## Reading beats writing

Code is read far more often than it is written — optimize for the next
reader, not the author. Prefer boring, explicit, locally readable code;
cleverness (metaprogramming, hidden magic, dense one-liners) needs a stated
reason. If understanding one unit requires assembling context from several
other files, restructure until it doesn't.

## Naming

- Names state role and intent, not mechanics: `marketSearchQuery`, not `q`;
  `retryDelayMs` — with units — not `delay`.
- Booleans read as predicates: `is`/`has`/`can`/`should`.
- Casing follows the language's convention (pinned in the language packs).
  Consistency within a file beats personal preference.

## Functions and modules

- Judge a unit by its interface, not its line count: a good module offers a
  small surface hiding real complexity. Splitting a coherent 60-line
  function into six fragments adds indirection, not clarity — split when a
  reader can no longer hold one idea, not to satisfy a quota.
- Organize by feature/domain, not by technical layer, so code that changes
  together lives together.
- Add layers (interfaces, indirection, service wrappers) when a second real
  implementation or a genuine seam exists — not "for later". Speculative
  generality is the most expensive mistake in this file.

## Duplication and abstraction

- Extract shared logic on the third occurrence, not the first — two
  occurrences rarely reveal the right shape (rule of three).
- The real DRY target is knowledge: business rules, constants, and schemas
  defined once. A little visible, local duplication beats an abstraction
  that scatters one behavior across files.

## Comments

- Comment the why: constraints, invariants, trade-offs, and links to the
  incident/spec/issue behind non-obvious code. The what belongs to names
  and structure.
- Delete comments that restate the next line; keep the ones a future reader
  cannot reconstruct from the code.

## Errors

- Never swallow an error silently: every catch either handles the failure
  meaningfully or rethrows with context. An intentionally-ignoring catch
  carries a comment saying why that is safe.
- Handle each error once — log-and-degrade or wrap-and-propagate, never
  both; double handling duplicates noise and buries the origin.
- Fail closed on validation, review, auth, and safety paths: when such a
  step errors, the outcome is reject/retry, never a defaulted "pass". Fail
  open only for genuinely best-effort side work, with a comment saying so.
- Error messages say what failed and what to do next.

## Boundaries and validation

- Validate external input (user input, API/LLM responses, files, env) with
  a schema at the system boundary; inside it, trust the types —
  re-validating everywhere is noise.
- No secret-shaped defaults (`"sk-1234"`, `"password"`): missing config
  fails loudly at startup instead of silently working with a fake value.
- Magic numbers become named constants, units in the name where relevant.

## Formatting and enforcement

- Formatting is the formatter's job: adopt the stack's standard tool, run
  it, never hand-argue brace placement or line breaks.
- A style rule no tool enforces will drift. When starting a project, set up
  the formatter, linter, and type-checker first, and run them before
  declaring work done.
- Never add a suppression comment (`# noqa`, `eslint-disable`,
  `type: ignore`) for a tool the project doesn't actually run; every real
  suppression states its reason.

## Simplicity

Prefer the simplest solution that actually works (KISS); implement what
the task needs and nothing speculative (YAGNI). New dependencies,
patterns, and abstractions each need a reason existing code can't answer.
When a simple version works, ship it and let real pressure justify the
next layer — premature optimization and premature abstraction are the
same mistake at different altitudes.

One performance mistake is not premature, though: never issue a query or
remote call inside a loop over unbounded data — batch or join instead. An
N+1 round-trip degrades linearly with data size, so it's a correctness-
scale bug that surfaces in production, not a micro-optimization to defer.
