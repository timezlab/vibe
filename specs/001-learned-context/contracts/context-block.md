# Contract: Injected learned-context block

Produced by the SessionStart loader on stdout (research.md D1). Consumed by
the session as context. This is the ONLY output of the loader besides
warnings on stderr.

## Format

```markdown
# Learned context (7 approved instincts · human-reviewed)

## Instincts
- [code-style] when creating a new TypeScript module → use named exports;
  default only where a framework requires it
- [workflow] when validating a skill → run `uvx --from 'skills-ref==0.1.1'
  agentskills validate skills/<name>`
…

## Previous session (2026-07-22)
<body of the latest session summary, 5–15 lines>
```

## Rules

1. **Source**: instincts read exclusively from `instincts/approved/`
   (gate — FR-004); summary is the single newest file in `session-data/`.
2. **Rendering**: one line per instinct: `- [<domain>] <trigger> → <action
   first sentence(s)>`, target ≤ 2 lines each. Frontmatter is never dumped.
3. **Budget** (SC-003, D8): ≤ 20 instincts AND ≤ 200 lines AND ≤ 25 KB for
   the whole block, whichever binds first. Selection: `last-confirmed`
   descending. When truncating, append: `- …and M more approved instincts
   not loaded (run /instinct-review to consolidate)` — never silent.
4. **Empty store / no store**: print nothing at all (empty stdout), exit 0
   — no header, no error (US1 scenario 5).
5. **Malformed approved file**: skip it; one stderr warning
   `learned: skipping malformed instinct <file>: <reason>`; continue
   (FR-013, SC-007).
6. **Header count** states the number actually loaded, and the
   `human-reviewed` marker is always present — it tells the model (and any
   reader of `/context`) that these lines carry review-backed authority.
7. Loader is read-only: it never writes, prunes, or mutates the store.
   (Prune belongs to capture — one writer per store lifecycle event.)
