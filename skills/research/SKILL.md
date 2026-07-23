---
name: research
description: Disciplined research workflow for agents — scales effort to the question, decomposes topics into sub-questions, searches broad-to-narrow across web/docs/academic sources, deep-reads instead of trusting snippets, cross-verifies claims against primary sources, and synthesizes a cited report that separates fact from inference. Covers every sense of "research" — investigating how to do a task (docs, guides, best practices), evaluating technologies/libraries/competitors, market or due-diligence questions, and academic literature search (papers, citation chasing, arXiv/Semantic Scholar). Use whenever the user asks to research, investigate, "deep dive", survey the state of the art, compare options with evidence, or find papers — including "tìm hiểu về", "nghiên cứu", "tổng hợp paper", "khảo sát tài liệu" — and before answering any question that should rest on current external sources rather than memory. For fanning research across subagents use parallel-agents; this skill defines what each researcher does.
---

# Research

Research is manufacturing claims with quality control. Anyone can search and
paraphrase; the discipline is in what you *don't* pass along: the unread
source, the single-sourced "fact", the SEO paraphrase of a paper you never
opened, the model prior dressed up as a finding.

**Core principle:** every claim traces to a source you actually read, and the
effort spent is proportional to what the answer is for.

## Scale effort to the question

Decide the tier before the first search — over-investing in trivia and
under-investing in decisions are the two default failures:

| Tier | Looks like | Budget |
|---|---|---|
| **Lookup** | One verifiable fact, current version, "does X support Y" | 1–3 searches, answer inline, no report |
| **Bounded comparison** | "X vs Y for our use case", "best library for Z" | 5–15 sources, short cited brief |
| **Open survey** | State of the art, due diligence, literature review | Full pipeline below; consider fan-out |

If sources for a lookup disagree, promote it a tier — disagreement is the
signal the question was never simple.

## Clarify, then plan

- Ask 1–2 clarifying questions **only if the answer changes what you search**
  — the goal (learning, deciding, writing?), and the binding constraints
  (use case, region, budget, timeframe). If the question is already specific
  or the user says "just research it", proceed with stated defaults.
- Decompose the topic into **3–5 sub-questions** covering genuinely different
  angles — not five phrasings of the same one. Write them down; they become
  the report's spine and the done-condition: research ends when each is
  answered or declared a gap, not when searching gets boring.

## Search: broad to narrow

- **Inventory tools first.** Check what search/fetch tools this session has
  (web search, page fetch, MCP search tools, `gh`/API access) and prefer the
  specialized tool over the generic one. Don't promise coverage a missing
  tool can't deliver.
- **Start with short, broad queries**, read the landscape, then narrow.
  Overly specific first queries return thin, skewed results; broad-to-narrow
  mirrors how expert researchers actually work.
- 2–3 keyword variations per sub-question; mix general, news-focused, and
  site-targeted queries. When new searches only resurface already-seen
  sources, that sub-question is saturated — stop.
- **Source hierarchy:** primary (official docs, specs, papers, filings,
  changelogs, the actual code) > reputable secondary (established outlets,
  known experts) > blogs > forums and SEO content farms. Agents measurably
  drift toward SEO-optimized farms over authoritative sources — counter it
  deliberately: prefer the domain that *owns* the fact.
- **Date every source.** Prefer recent (last 12 months for fast-moving
  topics) and never present an old snapshot as the current state.

## Deep-read, don't snippet-graze

- Snippets are bait, not evidence — they omit the caveats, the "however"
  paragraph, and the version qualifier. **Fetch full content** for the 3–5
  most load-bearing sources per sub-question before citing them.
- Retrieve just-in-time: keep lightweight identifiers (URLs, titles, one-line
  hooks) and fetch full text only when a sub-question needs it — don't bulk
  pre-load everything the search returned.

## Verify

- **Cross-reference.** A claim only one source makes is *unverified* and gets
  labeled that way in the report — or dropped if it's load-bearing.
- **Trace to primary.** Press coverage of a paper is not the paper; a blog
  about a benchmark is not the benchmark. For any claim the conclusion rests
  on, read the origin.
- **Search against yourself.** For load-bearing claims, run at least one
  disconfirming query ("X problems", "X criticism", "X vs alternatives") —
  a corpus assembled only from confirming queries is confirmation bias with
  citations.
- **Label epistemic status.** Verified fact, single-source claim, estimate/
  projection, opinion, and your own inference are five different things —
  the report must not let them blur.
- Gaps are findings. "Insufficient data found on sub-question 4" beats a
  plausible paragraph invented to fill the section.

## Academic mode (papers)

When the topic is scholarly literature:

- Search arXiv, Semantic Scholar, Google Scholar, and field-specific venues
  (ACL Anthology, PubMed, Papers with Code) — not just the general web.
- **Snowball from anchors:** find 1–2 clearly central papers, then chase
  backward (their references) and forward (who cites them). A survey paper,
  if one exists, is the highest-value single fetch.
- Note peer-review status — preprint ≠ published — plus version, venue, and
  year; check for retractions or failed replications on pivotal results.
- Cite properly: authors, year, venue, link. Benchmark numbers come from the
  paper's tables, not from a leaderboard screenshot of it.

## Synthesize

Structure the output; findings scattered across a transcript are not a
deliverable:

```markdown
# <Topic> — research report
*Date · N sources · confidence: high/medium/low*

## Executive summary          — 3–5 sentences, the answer up front
## <Theme per sub-question>   — findings with inline [source](url) citations
## Key takeaways              — what the reader should *do* with this
## Gaps and caveats           — what wasn't found, what's single-source
## Sources                    — numbered, each with a one-line hook
## Method                     — queries run, sub-questions, tools used
```

Short tiers collapse this to a few cited paragraphs. Long reports go to a
file with the executive summary inline. Answer first, evidence after —
a report that buries its conclusion under methodology has it backwards.

## Fan out (open surveys only)

Multi-agent research burns ~15× the tokens of a single pass — reserve it for
questions that earn it, and for the three cases where it genuinely wins:
independent facets to explore in parallel, high-volume intermediate reading
that would drown one context, or per-facet tool specialization.

- One subagent per **facet** (sub-question or source domain), never per role
  — a searcher→reader→writer pipeline is a telephone game that loses context
  at each handoff.
- If the harness ships predefined research lanes (this repo's
  `agents/research/`: web-researcher, academic-researcher, code-researcher,
  fact-checker), dispatch to the matching lane instead of rebuilding its
  brief — then the dispatch only needs the facet, constraints, and output
  path.
- Each brief needs an objective, output format, source guidance, and scope
  boundaries; without boundaries subagents duplicate work and leave gaps.
  Brief anatomy and dispatch mechanics → **parallel-agents**.
- Subagents return **condensed findings (1–2k tokens) with citations**, or
  write full notes to a file and return the path — never full page dumps
  into the lead's context.
- The lead re-checks claims that cross facet boundaries; synthesis is where
  contradictions between lanes surface, and finding them is the lead's job.

## Context discipline

For long-running research, keep a **notes file**: sub-questions, findings so
far, each with its source URL and date, plus the queries already run.
Context gets compacted mid-task; the notes file is what survives, and it
doubles as the report's raw material. Extract what matters from each fetched
page, keep the link, and let the full text leave context.

## Failure modes

- **Snippet-grazing** — citing pages never fetched; the caveat was in the
  body.
- **SEO sourcing** — the top result is optimized for the query, not correct.
- **Confirmation-only querying** — every search phrased to agree with the
  emerging answer.
- **Laundered priors** — model memory presented as a sourced finding; if you
  didn't read it this session, it isn't research.
- **Wrong tier** — ten searches for a version number; one search for a
  decision the user will spend money on.
- **Coverage theater** — a long sources list where only snippets were read.
- **Stale-as-current** — undated claims from 2023 answering a "right now"
  question.
- **Role-sliced fan-out** — subagents split by pipeline stage instead of by
  facet, losing context at every handoff.

## Boundaries

- Fan-out mechanics — briefs, dispatch, ledgers, verifying subagent claims →
  **parallel-agents**; this skill defines what each research lane does.
- The question is really a fuzzy idea to develop, not a query to answer →
  **brainstorming**.
- Recording conclusions in repo docs or an ADR → **docs-architect**.
- Wordsmithing a research brief or subagent prompt → **prompt-guru**.
