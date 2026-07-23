---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.mts"
  - "**/*.cts"
  - "**/*.js"
  - "**/*.jsx"
  - "**/package.json"
---

# Security — TypeScript/Node

Extends [common/security.md](../common/security.md) — read that first;
this file adds npm-ecosystem and JS-runtime specifics and wins where they
conflict.

## npm supply chain

- Enable the package manager's cooldown so freshly-published
  (most-likely-malicious) versions can't auto-resolve: pnpm
  `minimumReleaseAge` (pnpm 11+ defaults to 24h), npm `min-release-age`
  (npm 11.10+), Bun `minimumReleaseAge`. Units differ per manager —
  minutes / days / seconds — check before copying a value.
- Pre-add checks: `npm view <pkg> time` (publish recency) and
  `npm view <pkg> scripts` (lifecycle hooks). Install scripts run
  arbitrary code; `--ignore-scripts` blocks them but breaks native builds
  and does not stop install-time execution via `binding.gyp` — one layer,
  not a fix.
- Emergency pin of a compromised transitive dep: `overrides` (npm),
  `pnpm.overrides`, or `resolutions` (Yarn) force one version across the
  whole dependency graph.

## Injection sinks

- `child_process.exec` interpolating external data → `execFile`/`spawn`
  with array args.
- React/Angular escape by default; `dangerouslySetInnerHTML`,
  `bypassSecurityTrustHtml`, `v-html` need sanitized input and a comment
  saying why.
- Guard `__proto__`/`constructor`/`prototype` keys in any deep-merge of
  external JSON (prototype pollution).

## Tokens and randomness

- `Math.random()` never produces tokens, session IDs, or reset codes —
  use `crypto.randomUUID()` / `crypto.getRandomValues()`.
- JWT verification pins `algorithms: […]` explicitly; accepting the
  token's own header algorithm defeats the signature.
