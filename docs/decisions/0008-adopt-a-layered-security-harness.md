# Adopt a layered security harness (rules + skill + agent + hooks)

**Status:** accepted
**Date:** 2026-07-23
**Deciders:** Liam Lee

## Context

Security content was the next harness gap: no first-party security skill
exists in the ecosystem (anthropics/skills ships none), and the reference
harness reviewed (affaan-m/ECC) checks dependencies against a hardcoded
incident list rather than live advisory data. Research for this decision
(4-lane survey, 2026-07-23: ECC assets, 2024–26 supply-chain incidents,
OWASP/CWE 2025 canon, Claude Code harness mechanics) established two
load-bearing facts:

1. **Rules, skills, and CLAUDE.md are context the model can ignore; only
   hooks and `permissions.deny` are client-enforced** (verified from
   Claude Code docs + independent community sources). A guidance-only
   security harness has no teeth.
2. **CVE auditors don't catch malware**: `npm audit`/Dependabot
   deliberately lag or skip malware advisories; OSV.dev's `MAL-` records
   are the free, queryable malware source. Most 2024–26 malicious
   versions were live under 3 hours, making publish recency the strongest
   pre-advisory signal.

[ARCHITECTURE.md](../../ARCHITECTURE.md) had `hooks/` as a planned module
("memory hooks first"); this decision opens it with security content
instead — enforcement is where a security harness earns its name.

## Decision

One security concern, four layers, each doing what only it can:

- **`rules/*/security.md`** — always-on floor (per [ADR 0007](0007-adopt-claude-native-rule-packs.md)):
  secrets, injection sinks, authz, dependency hygiene. Thin; every rule
  carries its why.
- **`skills/security-audit/`** — the deep "how", four modes (dependency
  check / change review / full audit / harness audit) with a bundled
  live checker (`check-package.py`: OSV `MAL-` + recency + install
  scripts + existence). Named `security-audit`, not `security-review`,
  to avoid colliding with Claude Code's builtin `/security-review`.
- **`agents/security/security-reviewer.md`** — dispatchable adversarial
  reviewer preloading the skill (mirrors [ADR 0006](0006-predefine-research-agents-by-modality.md)'s
  lane pattern). `model: inherit` — FP-judgment quality scales with model,
  unlike the cost-pinned research lanes.
- **`hooks/security/`** — deterministic enforcement: dangerous-command
  blocker, secret protection (path + written-content scanning), and an
  install-time dependency gate that denies on live `MAL-` advisories and
  asks on cooldown/unknown-name/unverifiable.

Cross-cutting choices:

- **Live advisory queries over IOC lists** — a hardcoded
  known-bad-versions list is stale the day it ships; OSV/registry calls
  reflect today's advisories.
- **False-positive policy adopted from Anthropic's
  claude-code-security-review** (hard exclusions + precedents +
  confidence ≥0.8) as an explicitly overridable default — report quality
  is what separates a reviewer from a noise generator.
- **Hooks fail closed**: a crashed guard denies (or asks, for the
  dependency gate) with the error attached — community hooks' `exit 0`
  on error turns every hook bug into a silent security hole, inverting
  the repo's own fail-closed rule.
- **Uncertainty asks, malware denies**: only a positive `MAL-` hit
  hard-blocks an install; cooldown/404/network failures escalate to the
  human. CVE-only advisories surface as context — blocking every CVE
  would get the gate disabled within a week.

## Alternatives considered

- **Rely on the builtin `/security-review`** — rejected: diff-review
  only (no supply-chain dimension, no harness audit), Claude-exclusive,
  and not distributable as canonical vibe content.
- **Wrap an external scanner** (ECC's unpinned `npx ecc-agentshield`
  pattern) — rejected: an unpinned third-party executable inside the
  security harness contradicts the harness's own supply-chain rules.
- **Hardcoded malicious-version IOC list** — rejected: strictly
  dominated by live OSV queries; stale by design.
- **Two skills (code review vs dependency audit)** — rejected: the
  shared methodology (severity, confidence gate, FP policy, output
  format) would be duplicated or split; modes inside one skill keep it
  single-sourced.

## Consequences

**Better:**

- Install-time malware gating exists — the gap neither first-party nor
  ECC tooling fills (verified in testing: `axios@1.14.1` → deny with
  `MAL-2026-2307`).
- The harness pairs every "should" (rules/skill) with a "can't" (hooks)
  where it matters most.

**Worse:**

- Hook wiring is Claude Code-native until `vibe sync` ships per-platform
  adapters (already true for rules, [ADR 0007](0007-adopt-claude-native-rule-packs.md)).
- The dependency gate needs the network; mitigated by failing closed to
  "ask", never silently allowing.
- Regex guards are tripwires, not a sandbox — documented in
  `hooks/security/README.md`; hard guarantees remain `permissions.deny`
  + OS sandboxing.

**Must now be true:**

- Hook scripts stay stdlib-only, self-contained, and tested with the
  stdin battery on every change.
- Wiring hooks into a repo's `.claude/settings.json` is per-project
  opt-in; this repo's own wiring is a separate, deliberate step.
- Time-sensitive supply-chain facts live in the skill's references with
  dates, so staleness is visible.

## Revisit if

Anthropic ships a first-party security skill or install-time gate; OSV's
malware coverage materially changes; `vibe sync` lands hook adapters; or
memory hooks arrive and `hooks/` needs a shared-utilities layout.
