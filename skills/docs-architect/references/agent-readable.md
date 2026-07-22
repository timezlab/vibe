# Agent-Readable Docs

Docs written for humans often fail agents. Humans skim, infer, and fill gaps from experience; agents read literally and act on exactly what they find. These principles make docs usable when the reader is an LLM — and they cost nothing for human readers, who benefit from the same precision.

## Contents
1. Core principles
2. Library reference files (`docs/reference/<lib>.md`)
3. Progressive disclosure in prose
4. Anti-patterns

---

## 1. Core principles

### Concrete over abstract

**Weak:** "The auth layer should handle tokens carefully to ensure security."
**Strong:** "All session tokens go through `SessionStore.create()`. Direct inserts into `sessions` bypass the audit log. Rationale: `docs/decisions/0007-session-storage.md`."

An agent can act on the second; it can only guess at the first. Name the file/function/symbol, not the concept. State the rule, not the philosophy. Show the invariant, not the intent.

### Symptom → cause → fix

Known issues and quirks go in the shape an agent needs at the moment it hits the error:

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ERR_CACHE_MISS` during `pnpm build` | Stale tsup cache after TS config change | `rm -rf packages/*/dist packages/*/.tsup` |
| Tests hang on `SessionStore.create()` | Missing `DATABASE_URL` in test env | Source `.env.test` before `pnpm test` |

One lookup from symptom to fix. "Sometimes the build fails due to cache issues, try clearing the cache" forces the agent to rediscover all three columns.

### Link, don't duplicate

Two copies of a fact = one wrong within months, and the agent will trust the wrong one. If you're copying a paragraph between files, replace the copy with a link. Single source of truth, every time.

### Stable anchors

Agents quote paths and headings. Keep them stable: link files by path (not line numbers, unless structurally stable), use headings as anchor targets, and when reorganizing a doc keep old heading names pointing forward for a cycle.

## 2. Library reference files (`docs/reference/<lib>.md`)

When a library is used repeatedly in project-specific ways, capture **how this project uses it** — never a rewrite of the library's own docs.

```markdown
# <library> — usage in this project

**Library:** <name + version>   **Where:** <packages/modules>

## Project conventions
- We always <pattern>
- We never <anti-pattern>, because <reason>
- Import from <subpath>, not the default export, because <reason>

## Common tasks
### <e.g. "Add a new CLI command">
```ts
// minimal working example in THIS project's structure
```
- <Gotcha specific to our setup>

## Known quirks
- <Quirk> — workaround: <fix>
```

One page gets read; five pages don't. If the library publishes an `llms.txt` / agent-oriented docs index, link it under a "Full docs" line — but the project-specific conventions above are the part no upstream doc can provide.

## 3. Progressive disclosure in prose

Assume the reader has only the current doc in context. Pattern: (1) state the rule in one sentence → (2) minimum context to understand it → (3) link deeper.

> **Rule:** All session writes go through `SessionStore`.
>
> The `sessions` table has an audit trigger that only fires for store-issued writes; direct `INSERT` breaks compliance reporting.
>
> Full rationale: `docs/decisions/0007-session-storage.md`.

The reader who needs the rule stops at line 1; who needs why, reads on; who wants the debate, follows the link.

## 4. Anti-patterns

- **Walls of prose** — 10+ lines without a list, table, or heading gets skimmed and missed.
- **Vague verbs** — "handle", "manage", "process" say nothing; write "validate", "transform into X", "persist to Y".
- **Hedges** — "generally", "usually" signal an undocumented exception. Document the exception or drop the hedge.
- **Future tense** — "we will add X" doesn't age. Present tense for what's true, past tense for decisions, explicit dates for plans.
- **Unlabeled code blocks** — every example gets a one-line caption saying what it shows.
