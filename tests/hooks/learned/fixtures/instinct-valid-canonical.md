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
