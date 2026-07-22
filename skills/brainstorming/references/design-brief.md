# The design brief: record and hand off

Chat evaporates; the brief is what survives into the spec, the ADR, and the next session. It is a decision-bearing document: short, specific, and free of placeholders. Write it after the sectioned design is approved.

## Where it lives

| Situation | Destination |
|---|---|
| Feature that will get a spec | Paste/summarize into `/speckit-specify` — the brief is the *input* to the spec, not a parallel document to maintain |
| Product-level direction (new project, scope shift) | `docs/product/<topic>.md`, indexed in `docs/index.md` |
| Below-gate work the user wants recorded | A dated file where the project keeps notes, or just the conversation — ask only if a record seems genuinely wanted |
| Nothing approved (idea rejected during brainstorming) | A short note of *why* it was rejected can be worth more than a built feature — offer it |

Project conventions and user preference override this table. Don't create a `briefs/` directory structure speculatively.

## Template

Scale to the idea — a simple feature fills this in ten lines, a new project in a page. Every section either has real content or is deleted; no "TBD" survives.

```markdown
# <Idea name> — design brief (<YYYY-MM-DD>)

**Goal** — one sentence: who can do what, and what outcome changes.

**Users & pain** — the specific person/role and the quantified pain (how often, how bad, workaround today).

**Constraints** — split into:
- Discovered (from the repo: conventions, contracts, stack)
- Supplied (from the user: business rules, priorities, deadlines)
- Assumed (flagged, awaiting confirmation)

**Chosen approach** — the named approach and the shape of the design (components, boundaries, data flow — as much as was actually designed).

**Alternatives considered** — each named option and the one-line reason it lost. This section saves the next person from relitigating.

**Out of scope / anti-goals** — what this explicitly is not. The scope-creep firewall.

**Compatibility** *(features in existing products)* — what must not change: contracts, existing workflows, stored data. Note migration and rollout (flag / opt-in / everyone) if they apply.

**Success criteria** — observable signals, not vibes. "User can X and sees Y" beats "works well". Ban "correctly", "fast", "robust" unless tied to observable evidence.

**Open questions** — only genuine blockers, each with who/what unblocks it. An empty section is a claim: everything blocking is resolved.
```

## Self-review before showing it

Reread the brief with fresh eyes and fix inline — once, no polish loop:

1. **Placeholder scan** — any TBD, TODO, or vague requirement? Fix it now.
2. **Consistency** — do sections contradict each other? Does the approach actually serve the stated goal?
3. **Ambiguity** — could any line be read two ways? Pick one and make it explicit.
4. **Scope** — is this one implementable thing, or did a second project sneak in?
5. **Traceability** — does every feature trace to a named pain, and every success criterion to the goal?

For a large or high-stakes brief, a fresh-context subagent review catches what you can't — instruct it to flag only gaps that would cause a flawed plan (missing sections, contradictions, two-way-interpretable requirements), not wording preferences, and to approve otherwise.

## User review gate

Show the user the written brief — not a summary of it — and ask them to review before anything else happens:

> Brief written to `<path>`. Please look it over — anything to change before we move to <spec / implementation>?

If they request changes, make them and re-run the self-review. Only an explicit yes moves you forward. This gate is the last cheap moment to change course.

## Handoff

Apply the spec gate from `AGENTS.md` (≥3 tasks / >2 days / changed contracts / debatable done condition):

- **Above the gate** → `/speckit-specify`, feeding the brief in. Spec Kit's clarify/plan/tasks flow takes over; the brief keeps it honest.
- **Below the gate** → implement directly. The approved brief is the requirements record.
- **A settled, long-lived technical decision** emerged (stack choice, architecture direction) → capture it as an ADR in `docs/decisions/` regardless of which path the work takes. Decisions are the highest-value thing brainstorming produces.
- **Multi-piece idea** → hand off only the first piece; the decomposition map lives in the brief for the rest.

**Fresh context for implementation.** A long ideation transcript is noise to the implementing session — anchored on dead alternatives and half-revised ideas. When practical, start implementation in a fresh session that reads the brief (and spec, if one was written). The brief was written precisely so that this works.
