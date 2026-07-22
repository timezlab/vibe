# Alternatives: diverge, then converge

The first workable idea anchors everything after it — yours and the user's. The antidote is structural: generate genuinely different approaches *before* evaluating any of them, then converge deliberately.

## Diverge: 2-3 real approaches

- **Genuinely different, not strawmen.** Two variants of the same architecture plus a joke option is theater. Different approaches differ in something load-bearing: where state lives, what's built vs bought, what's manual vs automated, what ships first.
- **Name each approach** ("SQLite-first", "thin-client", "wrap-the-CLI") so the conversation can refer to them without re-describing.
- **Include the do-less option when honest.** "Cron job + existing dashboard" beating "new service" is a good brainstorming outcome, not a failure.
- **Check the premise itself.** Sometimes the strongest alternative is "don't build this — the pain named in the interview is solved by X that already exists". Raising that once is your job; pushing it after the user has heard and rejected it is not.

## Present with a recommendation

Lead with your pick and the reasons — a bare menu forces the user to do your analysis for them. Then the options, conversationally:

> I'd go with **B (wrap-the-CLI)** — it reuses the auth you already have and ships in days, and the main cost (no offline mode) doesn't matter for the users you described.
>
> **A. Native reimplementation** — full control, offline works; but months of work and you own every upstream change.
> **B. Wrap the CLI** — days not months, auth for free; no offline, and you inherit its output format.
> **C. Buy/adopt X** — zero build cost; but the pain you described (custom workflows) is exactly what it doesn't do.

Trade-offs must be real on both sides — an option with no honest cons hasn't been analyzed yet. Tie each pro/con back to what the interview surfaced; a trade-off that references "the users you described" is verifiable, one that references "best practices" is filler.

## Multiple lenses for consequential calls

When a decision is genuinely contested — multiple credible paths, no obvious winner, expensive to reverse — run it past distinct lenses before recommending:

- **Skeptic:** is the question itself right? What's the simplest credible alternative?
- **Pragmatist:** what ships fastest and what does operating it actually look like?
- **Critic:** where does this fail — edge cases, downside risk, expectation debt?

Inline, this is a paragraph per lens. For big decisions, spawn them as parallel subagents — each gets *only the question and minimal context*, never the conversation transcript (fresh context is the anti-anchoring mechanism). Write down your own position *before* reading theirs, keep the strongest dissent visible in what you present, and treat two lenses aligned against your position as real signal. Don't use this for code review or ordinary implementation choices — it's for decisions, and one round is the default.

## YAGNI, ruthlessly

Every feature in every approach must trace back to a pain the user actually named in the interview. Walk each design and cut what doesn't. "It would be easy to also add…" is how a brief dies. The user can always add scope later — removing it after approval is much harder, because by then it feels owned.

## Converge: present the design in sections

Once an approach is chosen, present the design incrementally:

- **Sections scaled to complexity** — a straightforward section gets a few sentences; a nuanced one gets a couple hundred words. Cover what applies: architecture, components and their boundaries, data flow, error handling, testing.
- **Checkpoint after each section.** Ask whether it looks right *so far*, and mean it — a checkpoint the user scrolls past is not approval. Dumping the whole design at once produces skim-and-rubber-stamp.
- **Design for isolation.** Prefer units with one clear purpose and well-defined interfaces. Test: can someone (including a future agent) understand what a unit does without reading its internals, and change the internals without breaking consumers? If not, the boundary needs work.
- **In existing codebases**, follow existing patterns. Where existing code has problems that directly affect this work (a file grown too large, tangled responsibilities), fold targeted fixes into the design; don't propose unrelated refactoring.
- **Loop back freely.** If a section exposes a gap in understanding, return to interviewing. Going backward here is far cheaper than going backward from code.

When every section is approved, move to the brief — [design-brief.md](design-brief.md).
