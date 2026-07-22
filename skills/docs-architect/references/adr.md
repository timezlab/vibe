# ADRs & Product Specs

ADRs (Architecture Decision Records) capture **why** the code is the way it is. Of all documentation they pay back the most: code shows *what*, git shows *when*, only decisions show *why*. When in doubt whether to document something, write the ADR.

Two rules inherited from the ADR tradition (Nygard, MADR, AWS, Microsoft — all agree):
- **Append-only.** An accepted ADR is never edited into a new decision. Reversing course = new ADR + mark the old one `superseded by NNNN-<new>.md`, bidirectional links. Superseded ADRs explain why the *current* decision was made.
- **Numbered.** `docs/decisions/NNNN-<kebab-topic>.md`, monotonic, never reused. First ADR is `0001`; next = highest existing + 1 (`ls docs/decisions/`). If parallel branches collide on a number, renumber the later one at merge.

## ADR template

```markdown
# <Decision title — active voice: "Use Postgres for session storage">

**Status:** accepted            <!-- proposed | accepted | superseded by NNNN-x.md | deprecated -->
**Date:** 2026-07-22
**Deciders:** <who approved — in an agent session, the human who signed off, not "the team">

## Context
<What problem forced this decision, what constraints shaped it. 2–5 sentences —
enough that a reader in 2 years gets it without asking anyone.>

## Decision
<What we chose. One specific paragraph. If it spans three options, you haven't decided.>

## Alternatives considered
- **<Option A>** — rejected because <specific reason>.
- **<Option B>** — seriously considered; would revisit if <trigger>.

## Consequences

**Better:**
- <Capability gained — specific, not "more flexibility">

**Worse:**
- <Cost accepted — "adds 80ms to cold start" is useful; "some tradeoffs" is not>

**Must now be true:**
- <Invariants future code must respect, in code terms:
  "All session writes go through `SessionStore.create()`; direct table inserts bypass the audit log">

## Revisit if
<The specific signal that reopens this decision — not "if requirements change".>
```

## The Consequences section is where ADRs fail

Most ADRs list benefits and stop. The three-way split forces honest accounting:

- **Better** — specific capabilities gained.
- **Worse** — if you can't name a downside, you haven't thought hard enough; every real decision has one. A pure-Better list is propaganda.
- **Must now be true** — the most valuable lines for agents: invariants concrete enough to grep for violations. An agent reading "all session tokens go through `SessionStore.create()`" knows exactly which guardrail not to cross.

Rejected alternatives are equally load-bearing — they stop the same debate from recurring in 6 months. "We considered other databases" teaches nothing; "Redis — rejected: sessions need relational joins to users/teams/audit; denormalizing would hurt" teaches the constraint.

A per-alternative "would revisit if" and the top-level Revisit-if answer different questions — when a *rejected option* becomes attractive vs. what signal reopens the *decision itself*. Both may exist; don't duplicate one into the other.

## When to write an ADR

Any of: the decision creates an invariant other code must respect · reasonable engineers would disagree · you'd be annoyed if someone undid it silently · the debate took over an hour. Skip for: obvious choices, pure implementation details, things the library's own docs already state.

Sources feeding ADRs: `/speckit.plan` decisions that outlive the feature (graduate them — `freshness.md` §Graduation), chat debates that reached a conclusion, "why don't we just…" questions answered for the second time.

## Self-review before saving

- [ ] Status + Date present (undatable docs are unjudgeable in a year)
- [ ] Context names the forcing constraint — *why now, what bounded the choice*
- [ ] Decision is one specific paragraph
- [ ] ≥1 rejected alternative with a specific reason
- [ ] Consequences split Better / Worse / Must-now-be-true; Worse is non-empty
- [ ] Must-now-be-true invariants are greppable (name symbols, not concepts)
- [ ] Revisit-if names a signal, not a platitude
- [ ] If superseding: old ADR updated with a forward link
- [ ] Indexed: one-line entry added to `docs/index.md` in the same commit — an unindexed ADR is invisible

---

# Product specs (`docs/product/`)

Product specs answer "what is this feature and why does it exist, from the user/business angle" — not "what technical choice did we make". Different author, different audience, different lifecycle → different directory. A feature (one product spec) often spawns several ADRs; cross-reference, don't merge.

`docs/product/DESIGN.md` is the standing product-direction doc: where the product is heading, current phase, explicit non-goals. Per-feature specs sit beside it.

```markdown
# <Feature name>

**Status:** planned | in-progress | shipped
**Owner:** <PM or tech lead>
**Last updated:** 2026-07-22

## Problem
<Who hurts today and how. Evidence if available.>

## Goals
- <Specific, measurable where possible>

## Non-goals
- <Explicit exclusions — the scope-creep fence>

## Solution sketch
<High-level shape, not implementation.>

## Success metrics
<How we'll know it worked.>

## Open questions
<Unresolved items that could change the approach.>
```

Product spec vs Spec Kit `spec.md`: the product spec is durable direction ("what this feature is, forever"); the Spec Kit spec is the ephemeral execution artifact for one build cycle and inherits its intent from the product spec when one exists.
