---
name: brainstorming
description: Turns a vague idea into a validated design brief through structured dialogue before any code is written — grounds itself in repo context, interviews the user one question at a time, proposes 2-3 genuinely different approaches with trade-offs, pressure-tests the premise, and lands an approved brief that hands off to Spec Kit or implementation. Use whenever the user wants to brainstorm, explore, or develop an idea — starting (init) a new project, shaping a new feature, "I want to build…", "should we do X or Y", comparing approaches, or any creative request whose requirements are still fuzzy — even if they only say "brainstorm", "lên ý tưởng", "phát triển ý tưởng", or describe a wish without a concrete spec.
---

# Brainstorming

An idea is not a spec. The gap between "I want a dashboard" and something buildable is full of unexamined assumptions — about who it's for, what pain it solves, and what "done" looks like. Code written across that gap is the most expensive kind of waste, because it looks like progress. This skill closes the gap with dialogue *before* implementation, and its output is a decision-bearing brief, not an essay.

**The gate:** do not write code, scaffold a project, or invoke an implementation workflow until you have presented a design and the user has approved it. "Simple" projects are where unexamined assumptions burn the most work — a brief for a simple idea can be a few sentences, but it still gets presented and approved. The only exception is a change you could describe as a one-sentence diff with no debatable done condition: just make it, and say so.

## The process

Five phases, in order. Don't skip ahead — each phase exists because the next one is cheaper and better when it's done.

| Phase | What happens | Read first |
|---|---|---|
| **1. Ground** | Explore repo context (README, AGENTS.md, docs, recent commits) before asking anything — for a feature in an existing product, also the code it touches and prior ADRs | [references/interviewing.md](references/interviewing.md) §Ground |
| **2. Interview** | One question per message, each building on the last, until purpose, users, constraints, and success criteria are covered | [references/interviewing.md](references/interviewing.md) |
| **3. Diverge** | Propose 2-3 genuinely different approaches with trade-offs; lead with your recommendation and reasons | [references/alternatives.md](references/alternatives.md) |
| **4. Converge** | Present the design in sections scaled to complexity; checkpoint each section before moving on | [references/alternatives.md](references/alternatives.md) §Converge |
| **5. Record & hand off** | Write the brief, self-review it, get the user's review, route to Spec Kit / ADR / implementation | [references/design-brief.md](references/design-brief.md) |

Load one reference at a time, as you reach the phase that needs it.

## Question discipline (the two rules that matter most)

1. **One question per message.** A question-dump gets partial answers and leaves silent gaps. If a topic needs more exploration, that's several messages, not one long one. Prefer multiple-choice when the option space is knowable — it's easier to answer and surfaces options the user hadn't considered.
2. **Only ask what you can't discover.** The repo tells you technical facts — read it first. It cannot tell you business facts: who the users are, what the pain costs, priorities, compliance, "why now". Never infer those from code; ask, or record them as assumptions flagged for confirmation.

## Anti-patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| "Too simple to need a design" | Simple projects hide the most unexamined assumptions | Present a brief design anyway — a few sentences is fine |
| Question-dump (5 questions in one message) | User answers a fraction; gaps survive silently | One per message, build on answers |
| Premature solutioning | First idea anchors everything after it | Diverge before you converge — 2-3 approaches |
| Premature convergence | Efficient-feeling dialogue that ends before the hard parts | Dig into what the user *hasn't* considered before wrapping up |
| Outline-dump | Full design at once → user skims, rubber-stamps | Sections with a checkpoint after each |
| Sycophantic agreement | Flipping position on pushback destroys your value as a thinking partner | Hold positions you have reasons for; concede to arguments, not to pressure |
| Monolithic scoping | "Platform with chat, billing, and analytics" designed as one thing | Flag multi-subsystem ideas immediately; decompose, then brainstorm the first piece |
| Placeholder rot | "TBD" sections poison the handoff | Self-review scan; no placeholder survives into the approved brief |

## Handing off (this repo)

The brief's landing place depends on what it turned out to be — see [references/design-brief.md](references/design-brief.md) §Handoff for the full map. In short: feature work that crosses the spec gate (≥3 tasks / >2 days / changed contracts / debatable done condition) feeds `/speckit-specify`; a settled technical decision becomes an ADR in `docs/decisions/`; product direction lands in `docs/product/`; below-gate work goes straight to implementation with the brief as the conversation record. When brainstorming ends and implementation begins, prefer a fresh session that reads the written brief — a long ideation transcript pollutes implementation context.

## Key principles

- **Dialogue over interrogation** — this is a collaboration, not a form. React to answers, share hunches, think out loud.
- **YAGNI ruthlessly** — every feature in the design must trace to a pain the user actually named. Cut the rest.
- **Alternatives before commitment** — the premise deserves a challenge too: sometimes the right output is "don't build this".
- **Incremental validation** — approval of section 3 is real only if sections 1-2 were actually approved, not scrolled past.
- **The artifact is the point** — chat evaporates; the brief survives into specs, ADRs, and the next session.
