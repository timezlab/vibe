---
id: nested-yaml-user
status: pending
trigger: "when using YAML beyond the flat subset"
domain: workflow
scope: project
source: session-extraction
confidence: 0.5
evidence:
  - nested:
      structure: "not allowed"
created: 2026-07-23
last-confirmed: 2026-07-23
---
# Nested YAML

## Action
This file uses nested YAML, which the flat-subset parser must reject.
