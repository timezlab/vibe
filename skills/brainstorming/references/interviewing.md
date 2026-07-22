# Interviewing: from vague idea to shared understanding

The goal of the interview is not to fill a template — it's to surface what the user actually wants, including the parts they can't articulate yet. Users routinely discover their real requirements while answering good questions. That only works when questions come one at a time and each one builds on the answer before it.

## Ground: explore before you ask

Before the first question, read what the repo can tell you:

- `README.md`, `AGENTS.md` / `CLAUDE.md` — what the project is and how it works
- Docs (product direction, ADRs, architecture) — what's already been decided
- Recent commits — what's actively moving
- For a feature idea: the code area it would touch, and its existing patterns

This changes your questions from generic ("what tech stack?") to informed ("you're on Node + node-pty already — does this feature live in the terminal layer or above it?"). A question the repo could have answered wastes the user's patience and your credibility.

**The epistemic line.** The repo reveals *technical* facts: how the system behaves today, its conventions, its contracts. It cannot reveal *business* facts: who the users are, what the pain costs them, priorities, pricing, compliance obligations, why now. Never reconstruct business facts from code or naming — a `free_tier_limit` constant tells you what the code does, not what the business requires. Business facts come from the user or a product artifact; until then they are assumptions, flagged as such.

## Scope check before detail

If the idea describes multiple independent subsystems ("a platform with chat, file storage, billing, and analytics"), say so immediately — don't spend questions refining details of something that needs decomposition first. Help split it: what are the independent pieces, how do they relate, what order makes sense? Then brainstorm the first piece through the normal flow. Each piece gets its own brief.

## What the interview must cover

Not a script — a coverage checklist. Ask in whatever order the conversation makes natural, and skip what's already answered.

1. **Who is this for?** A specific person or role, not "developers". If the user can't name one, that's a finding, not a formality.
2. **What's the pain?** How often does it hurt, how badly, and what's the workaround today? Unquantified pain tends to evaporate under scrutiny.
3. **Why now?** What changed that makes this worth building today?
4. **What's the 10-star version?** With unlimited time and money — this reveals the underlying desire the MVP must point toward.
5. **What's the smallest thing that proves the thesis?** The MVP is a test, not a small product.
6. **What are the anti-goals?** What is this explicitly *not*? Scope creep starts where anti-goals were never stated.
7. **How will you know it's working?** An observable signal, not vibes. If nothing observable would differ, question the idea.

## New project vs. feature in an existing product

The seven questions above assume greenfield. For a feature inside an existing product, the interview shifts shape:

- **Ground goes deeper.** Beyond README and docs, read the code area the feature would touch and its existing patterns, plus recorded decisions (ADRs, product direction). A feature that contradicts a recorded decision must say so out loud — the outcome is a rescope or a new superseding ADR, never silent drift.
- **"Who is this for?" becomes "which of our existing users?"** — and whether the feature serves them or is chasing a new segment. Chasing a new segment isn't wrong, but it's a strategy decision worth making consciously, not a side effect.
- **Add the brownfield questions** (same discipline — one per message, only the ones the repo can't answer):
  1. What does this change or break for existing users and their current workflows?
  2. Which contracts must survive unchanged — API, file formats, stored data, integrations?
  3. Does it overlap or conflict with an existing feature or a stated anti-goal?
  4. What happens to existing data — migration, defaults for records created before the feature existed?
  5. How does it reach users — feature flag, opt-in, everyone at once?
- **The premise check sharpens.** In an existing product, the strongest alternative is often a small extension of a feature that already exists — check for that before designing something new. And "the pain is real, but this product is the wrong place to solve it" is a legitimate finding, not a failure.

## Question craft

- **One question per message.** Non-negotiable. Multiple questions get partial answers, and the unanswered ones vanish silently.
- **Each question must fill a real gap.** Before asking, know which coverage item it serves. If you can't say what you'd do differently based on the answer, don't ask it.
- **Prefer multiple-choice** when you can enumerate the plausible options — it's faster to answer, and the options themselves teach the user what the decision space looks like. Actually write the options out: "Where should exports land — (a) download in the browser, (b) written into the repo, (c) both?" Open-ended is right only when you genuinely can't enumerate.
- **Build on answers.** Reference what they said. If an answer surprises you, follow the surprise — it usually marks a wrong assumption on one side.
- **Group only trivially-related facts.** "Which package manager and which Node version?" can be one message. "Who is it for and how should auth work?" cannot.

## Don't stop early

Efficient-feeling interviews are often premature: high pace, low information. The dialogue is done when the coverage list is genuinely covered and the *hard* parts have been examined — not when the user stops volunteering information. Before moving to approaches, ask yourself: what would an experienced engineer worry about here that hasn't come up? Failure modes, migration, concurrent edits, the empty state, the tenth-time user experience. Raise the one or two that matter; skip ceremony on the rest.

## When the user pushes back

Disagreement is signal, not a social problem to smooth over.

- If they push back with an argument, engage the argument. Concede when it's right — and say what changed your mind.
- If they push back with only pressure ("just trust me", "let's skip this"), hold your position once, briefly, with your reasons — then defer. It's their project; your job is to make sure the choice is informed, not to win.
- Never flip position merely because pushback occurred. A partner who agrees with everything is a mirror, and they didn't need a mirror.
- Invite critique of your own ideas in open-ended form ("what's wrong with this approach for your case?") rather than validation-seeking form ("does this look good?").
