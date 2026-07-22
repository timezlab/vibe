# Creating Prompts from Scratch

For when there is no existing prompt — only a task description. This file produces a *first draft*; the main workflow's diagnose pass (SKILL.md step 4B) then tightens it. Distilled from Anthropic's prompt-engineering docs (define success criteria → draft → iterate empirically) and field-tested agent-prompt architectures, rewritten to current best practice (positive phrasing, whys attached, minimal-first).

## Contents
1. Intake — answer before writing
2. Choose an architecture
3. Canonical skeleton
4. Drafting rules
5. Length calibration
6. Worked example
7. Hand off to the optimize loop

## 1. Intake — answer before writing

Never draft from a vague description; a prompt can only be as specified as the task. Get answers to these (ask the user; in a non-interactive run, infer and state assumptions in the deliverable):

1. **Mission** — one sentence, verb-first: what does this agent produce, for whom?
2. **Audience of the output** — end users, developers, another agent, a TTS engine? This drives style, format, and vocabulary.
3. **Tools** — exact tool names, what each returns, and error behavior. If the agent has tools, the prompt's biggest lever is tool guidance (see prompting-techniques.md §7).
4. **Constraints** — tone, response length, latency/cost, compliance rules, language(s).
5. **Success criteria + 1–2 example inputs with ideal outputs** — Anthropic's prerequisite for prompt engineering is a success definition and a way to test it (criteria should be specific and measurable, and usually multidimensional: quality *and* latency *and* cost). If the user can't produce one example of "good", the task is underspecified: help specify it before writing anything.
6. **Failure behavior** — what should happen when the agent can't do the task (missing info, out of scope, tool failure)? Undefined failure behavior is the single most common gap in new prompts.

Quick constraint sweep (only note the ones that apply): max response length · multi-language · memory across turns · determinism needs · actions requiring human approval.

## 2. Choose an architecture

Pick the closest type; combine sections freely when the agent spans types.

| Agent type | Skeleton emphasis | Notes |
|---|---|---|
| Q&A / lookup | Identity → instructions → output format → boundaries + fallback | Smallest viable prompt; resist adding workflow steps |
| Conversational persona (support, writing assistant) | Identity → context → interaction style (style, tone, audience) → response format | The COSTAR mnemonic (Context, Objective, Style, Tone, Audience, Response) is a decent completeness check here — as a checklist, not section headers |
| Tool-using agent | Identity → tool guidance → workflow with decision heuristics → output format → boundaries | Decision heuristics as "If X, use tool Y because Z"; per-tool detail belongs in tool descriptions, not the system prompt |
| Analysis / reasoning | Identity → method → output format (answer first, then reasoning, confidence, caveats) | Reasoning control differs sharply by model class — the provider file decides whether to script steps at all |
| Domain expert (legal, medical, finance) | Identity → embedded domain constants → scope (in/out) → method → disclaimers | Constants come from real sources (research step), never from memory |
| Pipeline subagent / multi-agent role | Role + position in pipeline → input contract → processing rules → output contract → error behavior | Contracts exact (schemas); see system-prompts.md §7 for subagent briefs |

Ordering rule when combining: identity always first; contracts and output format near the end (recency); examples after the rules they illustrate; boundaries last.

## 3. Canonical skeleton

A working scaffold, not a vendor-prescribed order — no provider mandates a section sequence; what the docs do mandate is the *pieces* (role first via the system param, clearly delimited sections, long data on top, query at the end). Note that few-shot examples don't have to live in the system prompt: Anthropic's own tooling places them at the start of the first user message, and if any part of the prompt varies per call, split fixed from variable content with `{{variable}}` placeholders (wrapped in tags) — that separation is what makes the prompt testable and eval-able later.

```
[Identity: who the model is and what it produces — one paragraph, specific.
 "You are a financial data analyst that turns quarterly earnings data into
 executive-ready summaries" beats "You are a helpful assistant."]

[3–7 core behavioral instructions, each carrying its why when non-obvious]

[Context / domain constants — embedded verbatim. Never "follow our standard
 format" without including the format; the model can't read your wiki.]

[Workflow — numbered steps only where order genuinely matters; decision
 points as "If X, do Y because Z" heuristics, not exhaustive case lists]

[Output format — exact: structure, length, sections. For machine-readable
 output use the provider's structured-output API feature, not prompt begging.]

[Examples — 3–5 diverse, realistic ones is the documented sweet spot;
 starting with one and adding as tests fail is fine. Clearly delimited.
 They silently teach format, tone, length, and reasoning style.]

[Boundaries — scope limits plus fallback behavior, phrased as what TO do:
 "If the request is outside <scope>, say so in one sentence and point the
 user to <resource>" — not a list of NEVERs.]
```

Delimiter style and instruction placement come from the target provider's file — read it before finalizing structure (prompting-techniques.md §2 has the provider-neutral rules). The one thing vendor skeletons agree on is identity-first.

## 4. Drafting rules

- **Start minimal.** Draft the smallest prompt that could work on a strong model. The diagnose pass and real test runs tell you what to add; completeness-driven additions are how kitchen-sink prompts happen.
- **Define failure behavior explicitly** (intake Q6) — it's cheaper to write one fallback line now than to debug silent hallucination later.
- **Embed constants.** Rubrics, format templates, scoring guides, policy text go in the prompt verbatim — they are not injectable and remove a whole class of ambiguity.
- **No contradictions — audit for them explicitly.** "Be concise" + "provide comprehensive analysis" forces the model to guess; resolve with a conditional ("2–3 sentence summary; expand only when the user asks"). This is the property vendors flag as most damaging: reasoning models burn thinking tokens reconciling conflicts, so a lean contradiction-free prompt beats a comprehensive conflicted one.
- **Order for the cache.** Stable, reused content (identity, rules, constants) at the top; per-request variable content near the end — providers cache prompt prefixes, and this ordering is free money at scale.
- **Reasoning order** — for models running without thinking, structure reasoning before conclusions (`<thinking>`/`<answer>`); for thinking-capable models, don't script the steps — general encouragement plus API knobs (effort/adaptive thinking) win, and some current models have thinking always on, making manual CoT scaffolds pure overhead (prompting-techniques.md §4 and the provider file decide).
- **Permit uncertainty.** Give the model explicit permission to say it doesn't know or to ask — documented to reduce hallucination, and it's the natural companion of the failure-behavior line.
- **One promise per line.** Every instruction should be testable: you can look at an output and say whether it was followed.

## 5. Length calibration

No vendor publishes token budgets for system prompts — these bands are a working heuristic for noticing outliers, not rules:

| Agent complexity | Draft target | Typical sections |
|---|---|---|
| Simple Q&A / lookup | 200–500 tokens | Identity + instructions + format |
| Standard conversational agent | 500–1500 tokens | Full skeleton, few examples |
| Complex tool-using / domain agent | 1500–3000 tokens | Full skeleton + tool guidance + examples |
| Pipeline subagent | 1000–2000 tokens | Contract-heavy, workflow-focused |

Longer is not better: every prompt token competes with the context available for the actual task. If a draft lands well above its band, that's a diagnose-pass finding, not a fact of life.

## 6. Worked example

Task: support agent for "CloudSync" (file-storage SaaS), tools `search_kb(query)` and `lookup_account(email)`, must escalate billing disputes.

```
You are Alex, CloudSync's support agent. You resolve technical and account
issues for business users who know their work but not our internals — so
translate technical terms into plain language.

Work from evidence, not memory: check search_kb for how-to and known-issue
questions, and lookup_account when the issue depends on the user's plan or
settings. If neither answers it, say what you'd need to know rather than
guessing — a wrong answer costs the user more than a short delay.

Ask at most one clarifying question per reply, because support chats stall
when users face a wall of questions.

Each reply: acknowledge the issue in one sentence, give the fix as 1–3
numbered steps, end by confirming it worked or asking the one question you
need. Keep replies under 150 words.

Billing disputes and anything touching data loss go to a human: summarize
the issue, what you checked, and the account details in an escalation note
instead of attempting a fix yourself.
```

What to notice: identity is specific; every rule carries its why; the escalation boundary says what TO do; there's exactly one number-bound format rule; no CAPS, no NEVER-list, ~160 tokens for a simple agent.

## 7. Hand off to the optimize loop

A first draft is input, not the deliverable. Run SKILL.md step 4B on your own draft — first drafts reliably over-specify, and self-diagnosis is where the cuts happen. Then deliver per SKILL.md step 5: the prompt, a short design-decision log (architecture chosen and why, what was deliberately left out), and test inputs — the intake examples from §1 are the first two tests.

When proposing how to test further, follow the vendors' eval doctrine: many automatable checks beat a few hand-graded ones; include edge-case inputs (irrelevant, overlong, ambiguous); grade with a different model as judge when grading needs judgment.
