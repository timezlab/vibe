---
paths:
  - "**/*.py"
---

# Coding style — Python

Extends [common/coding-style.md](../common/coding-style.md) — read that
first; this file adds Python specifics and wins where they conflict.

## Naming and modernity

- `snake_case` modules/functions/variables, `PascalCase` classes,
  `UPPER_SNAKE_CASE` constants, `_leading_underscore` module-private
  helpers.
- New code uses `from __future__ import annotations`, `X | None` unions,
  and builtin generics (`list[str]`). When editing an older file, match it
  or migrate the whole file — never mix `Optional[X]` and `X | None` in
  one file.

## Types

- Annotate public functions and anything another module imports; let
  locals infer.
- `Any` is for genuinely dynamic payloads (LLM output, opaque JSON) and
  stays contained at the boundary that receives it — convert to typed
  shapes before passing data inward.
- Define seams as `Protocol`s rather than inheritance trees; value objects
  as `@dataclass(frozen=True, slots=True)` or Pydantic models.

## Schema as the single source of shape

Pydantic models define each externally-visible shape once: types derive
from the model, constraints live in `Field(...)` rather than docstrings.
Parse external data (requests, files, env via `BaseSettings`) through the
model at the boundary. LLM output is external input too: extract structured
results via the provider's structured-output/tool-calling API or schema
validation, never by string-searching the response text.

## Errors

- Catch the narrowest exception you can actually handle.
  `except Exception` belongs only at operational boundaries — top-level
  loops, background jobs, handlers of last resort — always with
  `logger.exception(...)` and a comment saying why broad is safe here.
- Chain re-raises: `raise NewError(...) from exc` — a dropped cause makes
  the real origin unrecoverable.
- Fail-closed (common rules) applies with force here: an `except` around a
  validation/review/auth step returns reject/retry, never a defaulted
  "pass".

## Structure

- Per-domain exception classes (`StorageError`, `ConfigError(ValueError)`)
  over one generic `AppError` — callers can catch precisely.
- Module-level `logger = logging.getLogger(__name__)`; no `print` outside
  CLIs.
- Don't maintain sync/async twin copies of the same logic — share the core
  and wrap it once; twins always drift.
