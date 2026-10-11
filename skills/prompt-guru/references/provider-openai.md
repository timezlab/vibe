# Provider: OpenAI (GPT-6, GPT-5.x, GPT-4.1, legacy o-series)

What to do differently when the target model is an OpenAI model — current flagships are the GPT-6 family (Astra, 6.1 Sol, Sol, Luna, Sept 2026); GPT-5.6 is previous-gen; the o-series retires 2026-10-23 / 2026-12-11. Sources: developers.openai.com — GPT-6 Astra guide, GPT-5.6 prompt guidance and upgrade guide, reasoning, function-calling, prompt-engineering, deprecations, changelog; the developer blog post on skills and prompts for GPT-6 Astra; the OpenAI Model Spec (v2026.08.18). Apply on top of the general references.

## Contents
1. Structure and delimiters
2. Instruction placement and conflicts
3. Reasoning control
4. Agentic behavior and eagerness tuning
5. API knobs that replace prompt text
6. Instruction hierarchy and untrusted content
7. Model-family gotchas
8. Migration checklist (to GPT-6 / GPT-5.6)

## 1. Structure and delimiters

- Prefer **Markdown structure**, not XML-first as with Claude. The newest official template (GPT-5.6 guide, offered as the GPT-6 starting point) is short labeled sections in prose: Role / Personality / Goal / Success criteria / Constraints / Tools / Output / Stop rules. Named XML constraint blocks (`<tool_preambles>`, `<persistence>`, `<context_gathering>`) are the GPT-5/5.2-era pattern — still sanctioned, no longer the newest style.
- XML is a sanctioned secondary delimiter, mainly for document collections in long context. Avoid JSON-wrapping document collections — it performed poorly.
- Put cache-stable content at the start, variable context near the end.
- Pass tools via the API `tools` field with `strict: true`, never pasted schemas; keep the active set small (around 20 or fewer — use `allowed_tools`, namespaces, or tool search on 5.4+). Tool usage examples go in an Examples section, not the description field; few-shot examples can hurt reasoning models, so add them only on observed need.
- Prompts are code: reusable prompt objects (`v1/prompts`) shut down 2026-11-30 — keep prompt text in your repo and send it via `instructions` / `input`.

## 2. Instruction placement and conflicts

- Long context: place instructions at **BOTH beginning AND end** (if only once, above the context). This differs from Claude's top-data/bottom-query pattern.
- **Conflicts cost more than gaps** — OpenAI: "conflicting rules cause more instability than missing detail." Audit for contradictions first and state each rule once (a rule repeated in several places, like "ask first", produces needless approval stops).
- On conflicting instructions, GPT-4.1 follows the one **closest to the end**; in long GPT-4.1 conversations, restate formatting rules every 3–5 messages.
- `instructions` is not carried over by `previous_response_id` — resend it on every call.

## 3. Reasoning control

- **Reasoning models**: keep prompts brief and high-level — goal, constraints, success criteria, output contract. No "think step by step" (it can hurt); zero-shot first.
- **The newest flagships always reason**: GPT-6 Astra and GPT-6.1 Sol reject effort `none` (400) and drop `minimal` — map both to `low`. GPT-4.1-style scaffolding (explicit CoT, "plan extensively before each function call, and reflect extensively on the outcomes") belongs only where `none` exists: GPT-6 Sol / Luna, GPT-5.6, GPT-4.1.
- Migrating to 5.6 or GPT-6: strip generic "be brief" / "be thorough", "think step by step", and blanket language rules. Pro mode takes the same prompt — don't add "think harder".

## 4. Agentic behavior and eagerness tuning

- **Persistence + escape hatch**: "Keep going until the user's query is completely resolved before ending your turn" plus "decide the most reasonable assumption, proceed, and document it" — the model acts under uncertainty instead of stopping. Define autonomy per request type: answer vs change vs external write.
- **Reduce over-exploration**: lower effort, set tool-call budgets ("absolute maximum of 2 tool calls for this step"), and define early-stop criteria. Retrieval budget (5.6): one broad search, re-search only for a missing required fact, one or two fallbacks on empty results — loop-minimizing must not outrank correctness.
- **Preambles** (5.6+): one or two sentences before the first tool call of multi-step work, sparse updates at phase changes, no routine narration. Reserve ALWAYS / NEVER for true invariants.
- Quantify where Claude prompts would use prose: update cadence, answer length ("≤10-line change: 2–5 sentences or ≤3 bullets"), plan granularity ("2–5 milestone items, exactly one in_progress").
- **Outcome-first** on 5.6 and GPT-6: define the desired outcome and stopping conditions instead of stacking prescriptive procedure (OpenAI cites 10–15% eval gains on 5.6); over-prescription, not under-specification, is the failure mode.
- **Skills and AGENTS.md** (GPT-6 guidance): short descriptions, narrow triggers, progressive disclosure; drop standing "always test" and "read X before every edit" rules (in someone else's prompt that's a policy change — propose it in the change log); define "done"; no mandatory stop-for-review.

## 5. API knobs that replace prompt text

- `reasoning.effort`: none / minimal / low / medium / high / xhigh / max, availability per model. When migrating, keep the prior level, then test one lower; add missing success criteria before raising effort; reserve `max` for the hardest work. GPT-6 can change effort mid-conversation with a `configuration_update` input item — keep request-level effort fixed for cache hits.
- `text.verbosity` (low / medium / high) sets global output length, overridable in natural language per context ("Use high verbosity for writing code").
- **Sampling**: remove `temperature`, `top_p`, and `top_logprobs` whenever effort isn't `none` — steer with prompt text.
- **Responses API**: tool calling on GPT-6 Astra / 6.1 Sol requires it (Chat Completions works only without tools; on 5.6 and GPT-6 Sol / Luna, Chat Completions function calling works only at `none`). `previous_response_id` carries reasoning state across tool calls (measured +4.3pt on Tau-Bench) — prefer it over re-prompting context.
- Caching: `prompt_cache_retention` is deprecated → `prompt_cache_options.ttl`. Reserve at least ~25K `max_output_tokens` for reasoning plus output.
- Pin dated snapshots where they exist and check the deprecations page first — GPT-6 lists none, and dated snapshots now carry shutdown dates. Change one thing per eval run.
- Metaprompting is first-class: feed the model its own failure traces and ask "what minimal edits would fix these shortcomings?" (The dataset-backed Prompt Optimizer and Evals platform shut down 2026-11-30.)

## 6. Instruction hierarchy and untrusted content

- Model Spec chain of command: **Root > System > Developer > User > Guideline** (Platform was renamed Root in v2025.09.12; root principles can't be overridden by system messages). `instructions` acts as a system/developer message; both roles are accepted.
- Quoted or tool-returned text carries **no instruction authority** — wrap retrieved or user-supplied data in quoted blocks / untrusted-text markers so injected instructions are ignored. Users can implicitly delegate authority to a file like AGENTS.md, so treat such files as instructions and audit them.

## 7. Model-family gotchas

- **GPT-6 Astra** (top tier): asks and stops more often than Sol. Add an initiative block — infer intent and scope from context; "bias towards action and carry the user's intended task to completion"; don't stop at acknowledging, proposing a plan, or offering to continue; ask for approval only with a concrete, reviewable result; no permission needed for reversible or read-only work. It also tests more broadly than small tasks need (scope tests to the change), delegates less than expected (say when to use subagents), and over-formats (ask for paragraphs; lists only for parallel items). It reacts strongly to skill and AGENTS.md text — audit those for conflicts and state that user instructions outrank skills.
- **GPT-6.1 Sol**: near-Astra quality at lower cost; always reasons (no `none` / `minimal`). **GPT-6 Sol / Luna** accept `none`. OpenAI offers its Astra prompts as a starting point across GPT-6 — eval per model.
- **GPT-5.6** (Sol / Terra / Luna): outcome-first (§4); more concise by default than 5.5, so recheck old "be concise" lines. The plan / preamble / TODO-tool pattern comes from the general prompt-engineering guide, not the 5.6 page.
- **GPT-5.1 / 5.2**: effort `none` behaves like a non-reasoning model; quantify cadence and length numerically; 5.2 over-engineers — "Implement EXACTLY and ONLY what the user requests… no UX embellishments" — and needs schema-plus-null rules for extraction ("set null rather than guessing; re-scan before returning").
- **GPT-5**: hurt most by vague or contradictory prompts; may over-explore (soften "BE THOROUGH" maximizers, add budgets) or stop early (persistence + escape hatches).
- **GPT-4.1**: extremely literal; one clear sentence redirects it. Needs explicit CoT plus persistence / tool-use / planning reminders (worth ~20% on SWE-bench). Diff format: context lines (SEARCH/REPLACE, V4A), no line numbers.
- **o-series** (legacy — o1 / o3-mini / o4-mini retire 2026-10-23, o3 / o3-pro 2026-12-11): brief high-level prompts, no CoT prompting, `Formatting re-enabled` on the first line to restore markdown. Migrate to GPT-6 / 5.6.

## 8. Migration checklist (to GPT-6 / GPT-5.6)

1. Set the model; on Astra / 6.1 Sol, map effort `none` / `minimal` to `low`.
2. Move tool use to the Responses API.
3. Drop `temperature` / `top_p` / `top_logprobs` (unless effort is `none`); swap `prompt_cache_retention` for `prompt_cache_options`.
4. Keep the prior effort level, test one lower, and add success criteria before raising it.
5. Strip generic brevity / thoroughness / step-by-step lines and blanket rules; remove contradictions and duplicated rules.
6. Astra: add the initiative block, scope testing to the change, set delegation and formatting expectations.
7. Make surgical prompt edits tied to measured failures, one change per eval run.
