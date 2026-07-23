# Contract: Instinct file format

One instinct = one Markdown file with YAML frontmatter. Filename `<id>.md`.
Entity semantics: [data-model.md](../data-model.md).

## Canonical example

```markdown
---
id: prefer-named-exports
status: pending
trigger: "when creating a new TypeScript module"
domain: code-style
scope: project
source: session-extraction
confidence: 0.7
evidence:
  - "2026-07-23 session 3f2a: user corrected default→named export twice"
  - "2026-07-23 session 3f2a: lint rule discussion settled on named exports"
created: 2026-07-23
last-confirmed: 2026-07-23
sessions: [3f2a]
---
# Prefer named exports

## Action
Use named exports in new TypeScript modules; default exports only where a
framework requires them.
```

## Field rules

| Field | Rule |
|---|---|
| `id` | kebab-case, `[a-z0-9-]{3,64}`, unique across ALL state directories; equals filename stem |
| `status` | `pending` \| `approved` \| `rejected` \| `retired`; informational — directory is authoritative (mismatch ⇒ warning, never silent fix) |
| `trigger` | non-empty string, "when …" phrasing |
| `domain` | kebab-case slug, free vocabulary |
| `scope` | `project` (this feature); `global` reserved |
| `source` | `session-extraction` \| `hand-authored` \| `imported` |
| `confidence` | float in [0,1]; extractor heuristic: 2 evidence items → 0.5, 3–5 → 0.7, >5 → 0.85; informational (research.md D4) |
| `evidence` | ≥1 entry; each cites a verifiable event with session date/id; secret-scrubbed |
| `created`, `last-confirmed` | ISO dates; `last-confirmed` updated on approval |
| `evolved-into` | repo-relative path; required iff `status: retired` |
| `sessions` | optional list of contributing session ids |
| body | `## Action` required, imperative, self-contained; `## Evidence`, `## Review notes` optional |

## Parsing requirements

- Parser is stdlib-only (no PyYAML): frontmatter is restricted to the flat
  subset above — scalar strings/floats/dates and single-level lists (block
  `- item` or inline `[a, b]`). Files using YAML beyond this subset are
  malformed.
- **Malformed handling (FR-013)**: any missing required field, unparsable
  frontmatter, or empty `## Action` ⇒ the consumer skips the file and emits
  one warning line naming file + defect. Never crash, never partially load.
- Size guard: a single instinct file over 10 KB is treated as malformed
  (learned lessons are atomic; essays belong in skills).

## Write requirements

- Atomic: write to `<file>.tmp` in the same directory, then rename.
- Extraction may only ever create files under `instincts/pending/`
  (constitution III; FR-003). Any other state transition is performed by
  the review or evolve skill acting on explicit human verdicts.
- Before write, all field values and body pass the secret scrub
  (research.md D10).
