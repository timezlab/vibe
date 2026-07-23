# Enforcement — gates that make style real

Read when setting up a new project, when a repo has style rules but no
tooling, or when suppression comments reference tools that never run. The
premise (common rules § Formatting and enforcement): **a style rule no
tool enforces will drift** — documented conventions without gates produce
codebases that *look* strict (suppression comments, style manifestos) while
actually being governed by whatever the last editor did.

Order of operations for a new project: gates first, then the first
feature *through* them. Retrofitting a formatter later means one giant
noise-diff that buries real history.

## Contents

1. What counts as a gate
2. TypeScript setup
3. Python setup
4. Git hooks — fast reminders, not the gate
5. CI — the actual gate
6. Agent loop: run gates before declaring done
7. Adopting gates in an existing repo

## 1. What counts as a gate

A check is a gate only if something *fails* when it's violated — a CI job,
a blocking hook, a build step. A hook that prints a reminder and exits 0,
a `CODING_STYLE.md` nobody executes, or lint rules configured in one
developer's editor are documentation, not gates. Keep the honest hierarchy:

| Layer | Speed | Role |
|---|---|---|
| Editor/format-on-save | instant | convenience |
| Git pre-commit hook | seconds | fast feedback; skippable, so never the only line |
| CI required check | minutes | the gate — blocks merge |

Every gate runs the same commands a developer (or agent) runs locally —
one entry point (`pnpm check`, `make check`, `uv run poe check`), so local
and CI cannot disagree.

## 2. TypeScript setup

`package.json` scripts — the single entry point:

```jsonc
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "check": "pnpm typecheck && pnpm lint && pnpm format:check",
    "test": "vitest run"
  }
}
```

`eslint.config.mjs` (flat config):

```js
import tseslint from "typescript-eslint";
import prettier from "eslint-config-prettier";

export default tseslint.config(
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  { languageOptions: { parserOptions: { projectService: true } } },
  prettier, // last: silences rules Prettier owns
);
```

- Prettier stays zero-config (`.prettierrc` only if the team already
  agreed on an option; every option is a standing debate).
- Framework configs (`eslint-config-next`, …) slot in before the
  typechecked tiers.
- **Biome** is a fine single-tool alternative (`biome check --write`);
  pick one formatter per repo, never two.

## 3. Python setup

All in `pyproject.toml` (baseline from
[python.md](python.md) §1 — `ruff` for format+lint, `mypy --strict` for
types), plus the entry point and dev-dependency pinning:

```toml
[dependency-groups]
dev = ["ruff>=0.8", "mypy>=1.13", "pytest>=8"]
```

```bash
uv run ruff format --check .   # or: make check / poe check wrapping all four
uv run ruff check .
uv run mypy .
uv run pytest
```

The test runner is a declared dev dependency — a suite that only runs via
a globally-installed tool is not reproducible from a fresh clone.

## 4. Git hooks — fast reminders, not the gate

Hooks give seconds-fast feedback but are trivially skipped (`--no-verify`,
fresh clones without `core.hooksPath`), so treat them as convenience in
front of CI, never instead of it.

```bash
git config core.hooksPath .githooks   # committed, versioned hooks
```

`.githooks/pre-commit` — keep it under a few seconds: format check +
lint on staged files only (`lint-staged`, `ruff check` on changed paths).
Full type-check and tests belong to CI, not pre-commit — a slow hook
trains everyone to skip it.

## 5. CI — the actual gate

Minimal single workflow; anything less means style is voluntary:

```yaml
# .github/workflows/check.yml
name: check
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # TS: setup pnpm + node with cache, then
      - run: pnpm install --frozen-lockfile && pnpm check && pnpm test
      # Python: setup uv, then
      - run: uv sync && uv run ruff format --check . && uv run ruff check . && uv run mypy . && uv run pytest
```

Mark the job as a required status check on the default branch. One
workflow, same commands as local — expand only when the project earns it
(matrix builds, coverage upload).

## 6. Agent loop: run gates before declaring done

An agent without a runnable check has only "looks done". Before reporting
completion: run the repo's `check` entry point and the tests, and include
the actual output (pass counts, not "tests pass") — the tdd skill owns the
evidence format. If the repo has no gates, say so explicitly and offer
this file's setup; don't silently work gateless.

Claude Code users can additionally wire the check command into hooks
(e.g. a `Stop` hook running `pnpm check`) so the harness itself enforces
the loop — configure per repo in `.claude/settings.json`. (VIBE's shared
`hooks/` directory is planned, not yet available.)

## 7. Adopting gates in an existing repo

- **Formatter**: one dedicated mechanical commit (`chore: apply prettier`
  / `chore: apply ruff format`) with zero logic changes, then the check
  turns on. Add the commit hash to `.git-blame-ignore-revs` so blame stays
  useful.
- **Linter**: start from the recommended tier; for existing violations
  either fix-all in the mechanical commit (small repos) or enable
  per-rule as directories come clean. Never bulk-add suppression
  comments to get to green — that hides the debt the gate exists to
  surface.
- **Type-checker ratchet**: `strict = true` for new modules from day one;
  existing code tightens per-module (mypy `[[tool.mypy.overrides]]`,
  `strict: false` islands) with the override list only ever shrinking.
- **Suppression audit**: delete suppressions referencing tools that don't
  run (`# noqa` with no ruff, `eslint-disable` with no such rule
  enabled); each survivor gains its reason.
- The first PR after adoption is the proof: gates green, no new
  suppressions, history readable.
