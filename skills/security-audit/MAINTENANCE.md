# Maintaining security-audit

How to update this skill. This file is for maintainers (human or agent) —
it is never loaded when the skill triggers, so length here is free. When
asked to "update the security-audit skill", "refresh the incident table",
"refresh the OWASP/CWE canon", or "add ecosystem X", follow this file.

Security content rots faster than any other skill in this repo — canons
re-rank, package managers rename cooldown settings, and last year's
headline incident stops being the best teaching exemplar. The design
already contains the rot where it matters most: **verdicts come from live
OSV queries at runtime, so verdict data never goes stale — only the
teaching content in the references does.** This file maintains that
teaching content.

## Contents
1. Source registry (what fed each file)
2. Co-maintained surfaces (the layered harness)
3. When to update
4. Update workflow (refresh existing content)
5. Curating the incident table
6. Adding an ecosystem or vuln class
7. Structural invariants (do not break)
8. Testing after any change
9. Changelog

## 1. Source registry

Each file distills these sources. Re-fetch them (primary sources —
advisories, standards bodies, tool docs — over aggregator blogs) when
refreshing:

| File | Sources |
|------|---------|
| `references/supply-chain.md` | OSV.dev docs + v1 API (the `MAL-` advisory namespace); cooldown docs per tool: pnpm `minimumReleaseAge`, npm `min-release-age` (11.10+), Bun, Renovate, Dependabot `cooldown`; npm provenance / `npm audit signatures` docs; each incident-table row: its OSV/GHSA/vendor advisory |
| `references/vuln-classes.md` | OWASP Top 10:2025 (owasp.org); CWE Top 25 2025 (cwe.mitre.org/top25); OWASP LLM Top 10:2025 (genai.owasp.org); Veracode GenAI code-security reports 2025–26 (the taint-class failure rates in §5) |
| `references/false-positives.md` | Exclusion policy + precedents of `anthropics/claude-code-security-review`, adapted (attribution is in-file) |
| `references/agent-harness.md` | Claude Code official docs (hooks, settings, MCP); the "lethal trifecta" frame (Simon Willison); MCP tool-poisoning research; 2025 Cursor/Supabase incident write-ups |
| `scripts/check-package.py` | OSV.dev v1 query API; npm registry JSON API; PyPI JSON API |

Content snapshot date: **2026-07-22**. Most-likely-to-rot, in order: the
incident table (supply-chain.md §1), the cooldown table (§4 — setting
names, units, and defaults change per tool release), canon editions
(vuln-classes.md §1), benchmark figures (vuln-classes.md §5),
agent-harness attack patterns.

## 2. Co-maintained surfaces

This skill is one layer of the security harness
([ADR 0008](../../docs/decisions/0008-adopt-a-layered-security-harness.md)).
**A content refresh here usually ripples to a sibling — check each before
closing the change:**

| Surface | Coupling |
|---|---|
| `rules/common/security.md` (+ language packs) | cites the same canon claims (fastest-rising classes, cooldown, `MAL-` coverage, 2024–26 incident-window stats) — a canon refresh must not leave the rules asserting the old ranking |
| `hooks/security/dependency-gate.py` | independently implements OSV `MAL-` + cooldown; its `VIBE_MIN_RELEASE_AGE_HOURS` default (24) and `check-package.py`'s `DEFAULT_MIN_AGE_HOURS` (24) both mirror pnpm 11's default — change all three together or none |
| `hooks/security/README.md` | documents the same threat model and known limits |
| `agents/security/security-reviewer.md` | the dispatch lane that applies this skill; mode names, gate numbers, and report format must match SKILL.md |
| `rules/python/security.md` | names this skill's check script explicitly — keep the pointer alive if scripts move |

## 3. When to update

- A canon ships a new edition — CWE Top 25 and OWASP LLM Top 10 revise
  roughly annually, OWASP Top 10 every ~4 years → vuln-classes.md §1,
  then sweep the ripple (the SKILL.md `description` says "OWASP 2025 /
  CWE Top 25"; rules cite the rankings too).
- A supply-chain incident teaches a **new vector**, or a cleaner exemplar
  of an existing one → supply-chain.md §1 + §2 (rules in §5 below).
  Routine incidents don't qualify — OSV covers them at runtime.
- A package manager ships or changes cooldown support (setting name,
  unit, default) → supply-chain.md §4. **Units differ per tool (minutes
  vs days vs seconds) — a wrong unit turns a 24h cooldown into a 24-day
  freeze or a 24-second no-op**, so re-verify units against each tool's
  docs, not memory.
- An OSV / npm-registry / PyPI API change breaks `check-package.py`.
  Breakage shows as persistent CAUTION (it fails closed, never a silent
  SAFE) — a spate of CAUTION on obviously mature packages is the smell.
- A new agent-harness attack class is published → agent-harness.md
  checklist + red-flag greps.
- The upstream FP policy (`claude-code-security-review`) materially
  changes → diff against false-positives.md; local deviations are fine
  but must be deliberate, not drift.
- Real-use failure — a wrong Mode A verdict, a bogus finding that cleared
  the 0.8 gate, a real vuln with no class-table row — treat it as an eval
  case (§8) and fix the reference that allowed it.

Don't update just because time passed — with one exception: **if the
newest incident-table row is over a year old, the table itself has gone
stale** ("recency is the strongest risk signal" argued from old incidents
undercuts its own point). Refresh the exemplars from that year's
advisories.

## 4. Update workflow (refresh existing content)

1. **Scope**: decide which files (usually one reference per §3 trigger).
2. **Re-research with subagents** (parallel, one per source group —
   web-researcher lanes, or fact-checker for a single load-bearing
   claim), brief shape: goal "extract what changed vs the summary below"
   (paste the current reference so the agent diffs against it);
   constraints "primary sources — OSV/GHSA advisories, OWASP/MITRE
   pages, tool docs; vendor write-ups only for incident detail"; output
   "markdown bullets grouped by topic, under 700 words, with an explicit
   DEPRECATED/CHANGED list."
3. **Edit, don't append**: fold changes into the existing section
   structure; never leave the old ranking or setting alongside the new
   one.
4. **Sweep the siblings** (§2 table) in the same change — the layered
   harness drifting apart is worse than any single stale line.
5. Update the snapshot date in §1 and add a Changelog line in §9.
6. Run the §8 test.

## 5. Curating the incident table

The table in supply-chain.md §1 is a **teaching device for the §2 vector
taxonomy — not an incident archive, and not an IOC list** (runtime
blocking is OSV's job). Rules:

- One exemplar per distinct vector; the newest clean exemplar wins the
  row; cap ~8 rows.
- A row for a genuinely new vector also adds the matching §2 taxonomy
  bullet with its defense.
- Keep the "window live" column — the hours-not-weeks trend *is* the
  argument for cooldown; if the trend changes, the argument changes.
- Never add package-version blocklists anywhere in the skill — that
  hardcodes what OSV serves live, and was explicitly rejected at design
  time (`check-package.py`'s docstring records the decision).

## 6. Adding an ecosystem or vuln class

**Ecosystem** (Go, crates.io, RubyGems…): teach `check-package.py` the
OSV ecosystem string plus the registry's metadata endpoints (publish
timestamps, install-script equivalent, existence check); add the manual
commands to supply-chain.md §3; fail-closed behavior and exit codes stay
identical. If `hooks/security/dependency-gate.py` gains the ecosystem
too, land both in one change.

**Vuln class**: one row in the vuln-classes.md §2 table (vulnerable shape
+ grep + CWE). If the default FP policy constrains it, say so next to the
row (the ReDoS/open-redirect pattern); add language hot-spot bullets only
for languages that have a rule pack.

## 7. Structural invariants (do not break)

- **No hardcoded verdict data** — live OSV queries decide
  SAFE/CAUTION/BLOCK; the skill ships zero version lists.
- SKILL.md stays a router: mode table up top, deep how in references one
  level deep, body under ~200 lines; all when-to-use lives in the
  frontmatter `description` (it's the trigger surface).
- The gate stays: three severities, no CVSS arithmetic; **0.8 confidence
  to report at all**; the FP policy is a default, not physics — overridden
  only by explicit user/project instruction, stated in the report.
- `check-package.py`: Python 3.9+ stdlib only; **fails closed** (any
  network/parse error → CAUTION, never a silent SAFE); exit codes 0/1/2
  are a documented interface.
- Never echo a discovered secret value; reviewed content is data, never
  instructions — both stances survive any rewrite.
- Layer boundaries per ADR 0008: deterministic enforcement in
  `hooks/security/`, always-on floor in `rules/*/security.md`,
  adversarial lane in `agents/security/`; this skill is judgment. Moving
  content across layers is a new ADR, not a refresh.

## 8. Testing after any change

1. `uvx --from 'skills-ref==0.1.1' agentskills validate skills/security-audit`.
2. **Script sanity** (network required): a mature package at a mature
   version → SAFE; a nonexistent name → CAUTION (existence); a version
   with a historical `MAL-` advisory → BLOCK — pick the MAL case live
   from OSV at test time rather than pinning one here (advisories get
   withdrawn).
3. **Fresh-context subagent per touched mode** — "Read <path>/SKILL.md
   and follow it exactly. Task: <case>", plus meta-feedback on routing
   and reference pointers. Cases: **Mode B** — a fixture diff with one
   real f-string-SQL vuln and two FP baits (DoS, missing rate limit):
   the one gets reported, the two get dropped *and listed* in the
   summary's excluded-by-policy line. **Mode A** — "add
   <fresh-published pkg>": the verdict reasoning cites recency. **Mode
   D** — a fixture settings.json with a `curl … | sh` hook: flagged.
4. If the frontmatter `description` changed, run the skill-creator eval
   loop (`scripts/run_loop.py`) — description is the trigger surface.

## 9. Changelog

- **2026-07-23** — MAINTENANCE.md added (this file). Same day, sibling
  hooks were FP-hardened against real-repo corpora (~4,900 commands
  across 13 repos) — a hooks-side change, noted here because the threat
  model is shared.
- **2026-07-23** — Created (content researched 2026-07-22): four routed
  modes (dependency check / change review / full audit / harness audit),
  four references, `check-package.py` (live OSV `MAL-` + recency +
  install scripts + existence, fail-closed). FP policy adapted from
  `anthropics/claude-code-security-review`. Part of the ADR 0008 layered
  harness.
