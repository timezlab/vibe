---
name: coding-style
description: Coding-style discipline for writing, reviewing, and refactoring code — applies the vibe rule packs (common/TypeScript/Python) — reading-first code, schema as the single source of shape, fail-closed error handling, kebab-case files with named exports, and tool-enforced formatting with no unenforced suppressions. Use whenever writing significant new code, reviewing or refactoring existing code, starting a new project or module (gates come first), deciding where code or an abstraction belongs, or when the user mentions coding style, conventions, standards, code smells, clean code, or lint/format/type-check setup — including "chuẩn hóa code", "code sạch", "coding convention", "setup linter", "refactor cho gọn". For test discipline use tdd; for commits and PRs use git-workflow.
---

# Coding Style

The rule packs in `rules/` are the *what* — short, always-on constraints.
This skill is the *how*: applying them while writing, reviewing, and
setting up projects. In this repo the rules are already loaded via
`.claude/rules`; elsewhere, read
[rules/common/coding-style.md](../../rules/common/coding-style.md) plus the
language pack for the code at hand. If the packs aren't present (skill
installed standalone), continue without them — the review checklist below
and the references carry every constraint the packs encode.

Priority when goals collide, highest first:

1. **Correct** — style never outranks working code.
2. **Clear** — the next reader understands it without a tour guide.
3. **Simple** — the least mechanism that does the job.
4. **Consistent** — with the file, then the repo, then the rules.
5. **Concise** — brevity last; it is a tiebreaker, not a goal.

## First, match the room

Style serves readers, and readers live in an existing codebase — so before
writing, read the neighbors: the files you're editing, siblings in the same
directory, and the repo's configs (`tsconfig`, `eslint`, `pyproject`,
`CODING_STYLE.md`, `AGENTS.md`). Then:

- **Repo has a convention** → follow it, even where it differs from the
  rule packs. A codebase with two styles is worse than a codebase with one
  suboptimal style. Never mix styles within a file.
- **Repo is silent** → the rule packs decide.
- **Repo convention is actively harmful** → raise it with the user with
  evidence before deviating; don't silently "fix" a convention mid-task.
  Harm means correctness, not taste: swallowed errors, fail-open
  validation, secrets in defaults — never casing or export style. Only
  harm justifies breaking local consistency.

## Writing new code

1. Read the neighbors and configs (above).
2. Write to the rules; when unsure about a specific pattern, consult the
   language reference —
   [references/typescript.md](references/typescript.md) ·
   [references/python.md](references/python.md).
3. Style the code the task touches; don't drive-by upgrade neighboring
   code (renames, added docstrings, reformatting) — note the issue and
   propose it separately, so the diff stays reviewable.
4. Self-check against the review list below before presenting.
5. Run the repo's gates (formatter, linter, type-checker, tests) before
   declaring done. If the repo has no gates, say so and offer to set them
   up — [references/enforcement.md](references/enforcement.md).

## Starting a project or module

Gates come before code: an unenforced style rule drifts from day one, and
retrofitting a formatter onto a grown codebase produces a noise-diff that
buries real history. Follow
[references/enforcement.md](references/enforcement.md) to stand up
formatter + linter + type-checker + CI first, then write the first
feature through them.

## Reviewing for style

Review with the rules as the shared authority, not personal taste. For
each finding give `file:line`, the rule or reason, and a concrete fix.
Separate two severities:

- **Defect** — violates correctness-adjacent rules: swallowed or
  double-handled errors, fail-open validation/auth paths, unvalidated
  boundary input, secret-shaped defaults, suppression comments for tools
  that don't run, hand-written types drifting from their schema.
- **Nit** — consistency and polish: naming, file placement, comment
  wording. Prefix with "Nit:" so the author knows it's optional — style
  review loses authority when preferences are dressed as defects.

The checklist:

- Does each name state intent (units included) without restating types?
- Any error caught and ignored, logged-and-rethrown (double-handled), or
  defaulted to success on a validation/review/auth path?
- Is external input (API, user, LLM output, env, files) parsed through a
  schema at the boundary — and only there?
- Do schemas and types share one source, or is a hand-written twin
  drifting?
- Magic numbers? Secret-shaped defaults?
- Comments that restate code, or missing where the code is genuinely
  non-obvious (invariants, workarounds, incident links)?
- Any abstraction with one caller, layer with one implementation, or
  dependency added for a one-liner? (Speculative generality.)
- Duplication: is it knowledge-duplication (extract) or incidental
  similarity better left visible (rule of three)?
- Files organized by feature/domain, or by technical layer?
- Suppression comments (`# noqa`, `eslint-disable`, `type: ignore`)
  without a reason — or for tools the project doesn't run?
- Sync/async or copy-paste twins of the same logic?

## Refactoring for style

- Behavior-preserving refactors happen on green tests only — the tdd skill
  owns that discipline (characterization tests first when none exist).
- Keep mechanical changes (rename, reformat, move) in separate commits
  from behavior changes, so review and `git blame` stay readable — the
  git-workflow skill owns commit mechanics.
- Don't reformat a whole codebase inside a feature change; one dedicated
  mechanical commit, then the feature.

## References

| Read | When |
|---|---|
| [references/principles.md](references/principles.md) | You need the why behind a rule, are asked to justify or debate one, or are writing/adapting style rules for a team |
| [references/typescript.md](references/typescript.md) | Writing or reviewing TypeScript/React beyond the basics — tsconfig/lint baselines, type patterns, Zod, Next.js boundaries |
| [references/python.md](references/python.md) | Writing or reviewing Python beyond the basics — ruff/mypy baselines, Pydantic, Protocol seams, async structure |
| [references/enforcement.md](references/enforcement.md) | Setting up or fixing gates: formatter, linter, type-checker, hooks, CI; adopting gates in an existing repo |

## Boundaries

- Test discipline (write the test first, never weaken it) → **tdd**.
- Commits, branches, PRs → **git-workflow** (this skill only says *what*
  stays separate: mechanical vs behavior changes).
- Recording a contested style decision for a team → an ADR via
  **docs-architect**, not an ever-growing rules file.
