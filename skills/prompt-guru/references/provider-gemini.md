# Provider: Google Gemini

What to do differently when the target model is Gemini 3.x (3.1 Pro preview; 3.5 / 3.6 / 3.8 Flash; 3.5 Flash-Lite — 2.5 is legacy, open only to prior users since 2026-09-18). Sources: ai.google.dev prompting-strategies, latest-model and what's-new pages (3.5, 3.6), thinking, caching, media-resolution, function-calling docs; Vertex AI prompt-design and migration guides (docs.cloud.google.com). Apply on top of the general references.

## Contents
1. Structure and instruction placement
2. Sampling: don't send it
3. Thinking control
4. Examples
5. Verbosity and persona
6. Long context and caching
7. Structured output, function calling, multimodal, safety
8. Migrating a prompt to current Gemini

## 1. Structure and instruction placement

- Structure with XML-style tags (`<role>`, `<constraints>`, `<context>`, `<task>`) or Markdown headers (`# Identity`, `# Constraints`) — both officially sanctioned; pick one and stay consistent.
- **Split placement**: persona, constraints, and output format go in `system_instruction` (or the very start of the prompt); the specific question goes at the **very end, after all context**. Anchor it with "Based on the preceding information…". A question buried before a large context blob gets ignored.
- State the goal clearly and concisely; avoid persuasive or elaborate language — Gemini 3 over-analyzes verbose prompts.
- For agents, mirror Google's agentic system-instruction template (prompting-strategies page; evaluated on agentic benchmarks) instead of inventing a structure: before acting, plan around logical dependencies, risk, and information availability; separate low-risk reads from high-risk writes; say when assumptions are allowed and when to pause; prefer calling a tool with the information at hand over asking the user; retry transient errors, but change strategy or arguments rather than repeat a failed call; check before assuming something doesn't apply. Fetch the page only when you need its verbatim text.
- Current-date and strict-grounding clauses ("Do not assume or infer beyond the provided facts") are documented system-instruction content. Don't copy a knowledge-cutoff date onto a model whose cutoff is unpublished.

## 2. Sampling: don't send it

- `temperature`, `top_p`, and `top_k` are **deprecated and ignored** from Gemini 3.6 Flash / 3.5 Flash-Lite on, and Google states future generations will reject them with HTTP 400. Delete them from requests; get determinism from explicit instructions and response schemas instead. `candidate_count` and the penalty params are deprecated too.
- On earlier 3.x models the guidance was already to leave temperature at its 1.0 default — lowering it caused token loops and degraded reasoning. Either way, the rule for every 3.x target is: don't tune sampling. (Older recipes — temp 0 for CoT, per-task bands — apply only to pre-3.x / non-thinking models.)
- **No prefill**: a request whose last non-empty turn is a `model` turn returns 400 (3.6+). Steer format with the system instruction or a response schema.

## 3. Thinking control

- Control depth with `thinking_level`, not prompt text. Levels and defaults differ per model — check the thinking page before setting one. As of 2026-10: 3.8 Flash low/medium/high (default medium; no `minimal`), 3.6 Flash minimal–high (medium), 3.5 Flash-Lite minimal–high (minimal — raise to medium/high for subagents and tool use), 3.1 Pro preview low/medium/high (high).
- The default dropped from high to medium starting with 3.5 Flash: when replacing old CoT scaffolding, set `high` explicitly instead of trusting the default.
- `thinking_budget` is legacy — replace it with `thinking_level`; combining both in one request is a 400.
- Prompt-side: skip "outline your reasoning" scaffolds. Asking the model to think harder raises depth at token cost; asking it to think less is a sanctioned way to save tokens on long outputs.
- Too many tool calls: lower the thinking level first, then add a tool-budget instruction.
- Multi-turn tool use: round-trip **thought signatures**. From 3.5 on, a missing expected signature is an error, not a warning; prefer stateful mode (Interactions API `previous_interaction_id`), where thought preservation is on by default.

## 4. Examples

- Google recommends always including few-shot examples, but publishes no fixed count: start with a few varied examples and adjust empirically — too many invite overfitting.
- Keep formatting **identical** across shots (tags, whitespace, newlines) — Gemini keys heavily on format consistency.
- At long context, many-shot in-context learning (hundreds of examples) is a documented fine-tuning alternative.

## 5. Verbosity and persona

- Gemini 3 is **terse by default** — the optimizer's job often inverts from Claude's (reduce verbosity) to prompting chattiness in: "Explain this as a friendly, talkative assistant."
- Request the desired detail level and persona explicitly, or terse answers will read as lazy.
- If a Flash model turns sycophantic, instruct it to be concise and professional, without excess compliments (Vertex migration guide).

## 6. Long context and caching

- Query at the very end after all context (same rule as Claude, stronger here).
- **Implicit caching is the default** (minimum ~4,096 tokens on 3.6/3.8 Flash and 3.1 Pro): put large, stable content first so the prefix is reused. Explicit context caching remains available on generateContent but not in the Interactions API.
- Single-query retrieval is ~99%, but multi-needle recall degrades — don't assume uniform recall; chunk or chain instead.

## 7. Structured output, function calling, multimodal, safety

- For JSON, use response schemas (JSON Schema / Pydantic), not prompt-only formatting. Schemas combined with built-in tools (Search, URL context, code execution, File Search, function calling) are preview, Gemini 3 only.
- Function calling: send one FunctionResponse per call, matching its id and name; multimodal tool output goes inside the FunctionResponse; append any inline instruction after a blank line (`\n\n`). On `MALFORMED_FUNCTION_CALL`, stop requiring text before tool calls.
- `media_resolution` is set per item (low / medium / high / `ultra_high`, Gemini 3): start with the default — PDF quality typically saturates at medium, so raise it only for genuinely dense images, and lower it rather than truncate content when the window overflows.
- Media-vs-text order: Google's own pages disagree for single images (image-understanding says text first, the files guide says media first) — test both.
- Safety filters can silently return fallback responses: detect them and retry with a rephrased prompt (raising temperature no longer does anything on 3.6+).

## 8. Migrating a prompt to current Gemini

Checklist when retargeting an older-Gemini or other-provider prompt:

1. Delete manual CoT scaffolding, role-play padding, and persuasion boilerplate → rely on `thinking_level` (set `high` explicitly if the old prompt depended on deep reasoning).
2. Remove `temperature` / `top_p` / `top_k`, `candidate_count`, and penalties.
3. Remove prefilled model turns → system instruction or response schema.
4. Replace `thinking_budget` with `thinking_level`, using a level the target model supports (`minimal` isn't available on 3.8 Flash or 3.1 Pro).
5. Persona and constraints into the system instruction; the question last, after the data, with the "Based on the preceding information…" anchor.
6. Add or keep a few format-consistent few-shot examples.
7. Add explicit verbosity/persona instructions if conversational output is wanted.
8. Switch prompt-based JSON formatting to a response schema; check function-call / response pairing.
