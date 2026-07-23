# Python — deep guidance

Read when writing or reviewing Python beyond the basics. The
[Python rules pack](../../../rules/python/coding-style.md) states the
constraints; this file shows the patterns that satisfy them. Always defer
to the repo's existing configs first (SKILL.md: match the room).

## Contents

1. Tooling baseline
2. Project shape
3. Typing patterns
4. Pydantic: schema as the single source
5. Errors
6. Async structure
7. Logging

## 1. Tooling baseline

One fast tool covers formatting and linting; one type-checker makes
annotations mean something. Committed config, not editor defaults — an
uncommitted setup produces the "suppression comments for tools that don't
run" smell.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"

[tool.ruff.lint]
select = [
  "E", "W", "F",   # pycodestyle + pyflakes — the floor
  "I",             # import sorting (isort)
  "UP",            # pyupgrade — modern idioms (X | None, list[str])
  "B",             # bugbear — real bug patterns
  "SIM",           # simplify — nesting/boolean cleanups
  "BLE",           # blind-except — flags bare `except Exception`
  "RET",           # return consistency
]

[tool.mypy]
python_version = "3.12"
strict = true                      # new projects; existing: see ratchet in enforcement.md
```

`ruff format` replaces black; `ruff check` at this selection catches the
error-handling and modernity rules mechanically. Run both via the same
entry point the CI uses (`uv run ruff check .`, `uv run mypy .`) so local
and CI can't disagree. Full wiring: [enforcement.md](enforcement.md).

## 2. Project shape

- `src/` layout (`src/<package>/…`) so tests import the installed package,
  not the working directory by accident.
- Feature/domain modules over layer-first trees; when a layered split
  exists (`routers/ → services/ → models/`), state the dependency
  direction in `ARCHITECTURE.md` and keep imports flowing one way.
- Module-private helpers get `_prefix`; a module's public surface is what
  it exports without underscore plus `__all__` where re-export matters.
- One barrel exception: `models/__init__.py` may aggregate ORM models for
  mapper registration — with a docstring saying that's why.

## 3. Typing patterns

- **Seams as `Protocol`** (+ `@runtime_checkable` only if you actually
  `isinstance` it): callers depend on the shape, implementations stay
  swappable without inheritance. A typed Protocol beats `getattr`
  duck-typing precisely where correctness matters — typos in `getattr`
  strings fail silently; a Protocol fails in type-check.
- **Value objects**: `@dataclass(frozen=True, slots=True)` for internal
  immutable data; Pydantic models where validation or serialization is
  needed. Don't reach for Pydantic for purely internal structures — it
  buys validation you don't need at a runtime cost.
- **`TypedDict`** only for dict-shaped data you don't own (a third-party
  payload you index into); prefer converting to a dataclass/model at the
  boundary.
- **Containing `Any`**: a function that receives dynamic data
  (`dict[str, Any]` from an LLM or JSON) converts it to a typed shape
  before returning — `Any` that escapes a boundary function infects every
  caller.

## 4. Pydantic: schema as the single source

```python
class ReportSection(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    weight: float = Field(ge=0, le=1)

class ReportConfig(BaseModel):
    sections: list[ReportSection] = Field(min_length=1)
```

- Constraints live in `Field(...)`/validators, not docstrings — prose
  constraints aren't checked and drift.
- Parse at the boundary: `ReportConfig.model_validate(payload)` where the
  data enters; inside, pass the model.
- **Collect-all-errors validation** for agent-facing or user-facing
  config: gather every problem in one pass and raise once with the full
  list — the caller (human or LLM) fixes everything in one round instead
  of a fix-one-resubmit loop. Pydantic does this natively;
  hand-rolled validators should mirror it.
- Settings: `BaseSettings` with required fields for secrets — no
  `"sk-1234"`-style defaults; boot fails loudly instead.
- **LLM output is external input**: use the provider/framework's
  structured-output or tool-calling API and validate into a model. String
  search (`find("```json")`) breaks on the first formatting change and
  bypasses every constraint the schema encodes.

## 5. Errors

- Per-domain exception hierarchy, module-scoped:

  ```python
  class StorageError(Exception): ...
  class StorageNotFoundError(StorageError): ...
  ```

  Callers catch exactly what they can handle; a generic `AppError`
  forfeits that.
- The operational-boundary pattern — the only sanctioned broad catch:

  ```python
  while True:
      try:
          await process_next()
      except Exception:  # noqa: BLE001 — a bad cycle must not kill the loop
          logger.exception("cycle failed; continuing")
  ```

  Boundary + `logger.exception` + a comment saying why broad is safe.
  Everywhere else, catch the specific exception.
- Chain: `raise ConfigError(f"bad expr: {expr}") from exc` — without
  `from`, the original traceback is gone when you need it most.
- **Fail closed**: a validation/review/auth step that errors returns
  reject/retry — never a defaulted pass. If a framework forces
  string-returning tools (LangGraph-style `"ERROR: …"` contracts), the
  error string is still a *failure* the caller must branch on; document
  the contract where the tool is defined.
- Transaction boundaries: the request handler owns the single
  `commit()`; services `flush()` at most. Two layers committing
  independently is how a half-written aggregate gets orphaned.

## 6. Async structure

- **No sync/async twins**: implement the logic once. Either the core is
  async and the sync wrapper is one `asyncio.run`/`to_thread` call, or
  the core is pure/sync and the async layer only awaits I/O around it.
  Twin `_do()` / `_ado()` copies drift the first time one gets a bugfix.
- **Owned tasks only**: every spawned task has an owner that awaits or
  cancels it — `asyncio.TaskGroup` (structured concurrency) by default; a
  bare `create_task` without a stored handle is a leak and an
  error-swallower (its exceptions vanish).
- Independent awaits gather: `asyncio.gather(...)` /
  `TaskGroup` — not a sequential await chain.
- Async code never calls blocking I/O directly; wrap it
  (`asyncio.to_thread`) or use the async client.

## 7. Logging

- `logger = logging.getLogger(__name__)` at module top; no `print`
  outside CLI entry points.
- `logger.exception(...)` inside handlers (it captures the traceback);
  `logger.error(...)` only when there is no live exception context.
- Log at the boundary that handles the error — the handle-once rule:
  layers that re-log while re-raising produce triple noise for one
  failure.
