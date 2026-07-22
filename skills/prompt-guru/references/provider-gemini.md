# Provider: Google Gemini

What to do differently when the target model is Gemini (2.5 / 3 / 3.1 family — 3.x guidance carries over to 3.1 unchanged). Sources: ai.google.dev prompting-strategies, Gemini 3 Developer Guide, thinking docs, long-context docs, Vertex AI prompt design. Apply on top of the general references.

## Contents
1. Structure and instruction placement
2. Sampling: leave defaults alone (Gemini 3)
3. Thinking control
4. Examples: few-shot is near-mandatory
5. Verbosity and persona
6. Long context and caching
7. Structured output, multimodal, safety
8. Migrating a prompt from 2.5-era / other providers

## 1. Structure and instruction placement

- Structure with XML-style tags (`<role>`, `<constraints>`, `<context>`, `<task>` — recommended for Gemini 3) or Markdown headers (`# Identity`, `# Constraints`) — both officially sanctioned; pick one and stay consistent.
- **Instructions go at the END, after the data** — inverted emphasis vs the usual instructions-first habit. Anchor with "Based on the preceding information…". Instructions buried before a large context blob get ignored.
- Put persona/behavior in the `system_instruction` parameter, not the user message. Google documents current-date/knowledge-cutoff clauses and RAG grounding clauses ("Do not assume or infer beyond the provided facts") as standard system-instruction content.
- State the goal clearly and concisely; avoid persuasive or elaborate language — Gemini 3 over-analyzes verbose prompts.

## 2. Sampling: leave defaults alone (Gemini 3)

- **Keep temperature at 1.0 on Gemini 3.x.** Lowering it for "determinism" causes token loops and degraded reasoning — the opposite of common practice elsewhere. When migrating a prompt, delete explicit low-temperature settings.
- Older whitepaper recipes (temp 0 for CoT, 0.1–0.9 bands per task type) apply only to pre-3.x / non-thinking models.

## 3. Thinking control

- Control reasoning depth with `thinking_level` (minimal/low/medium/high), not prompt text. Don't ask thinking models to outline or plan their reasoning steps — the only prompt-side lever worth using is "Think very hard" (at token cost).
- Replace 2.5-era chain-of-thought scaffolding with a simple prompt + `thinking_level: "high"`.
- `thinking_level` and legacy `thinking_budget` cannot be combined in one request. Defaults vary by model (Pro models default high, Flash/Flash-Lite medium or minimal — e.g. 3.1-pro-preview high, 3.1-flash-lite minimal; 2.5-flash-lite off by default).
- In stateless multi-turn tool use, round-trip **thought signatures** (encrypted reasoning state) across calls, or reasoning continuity breaks; prefer stateful mode.

## 4. Examples: few-shot is near-mandatory

- Google: "always include few-shot examples" — 2–4 varied examples (≈6 for classification, with class labels shuffled); watch for overfitting beyond that.
- Keep formatting **identical** across shots (tags, whitespace, newlines) — Gemini keys heavily on format consistency.
- At long context, many-shot in-context learning (hundreds of examples) is a documented fine-tuning alternative.

## 5. Verbosity and persona

- Gemini 3 is **terse by default** — the optimizer's job often inverts from Claude's (reduce verbosity) to prompting chattiness in: "Explain this as a friendly, talkative assistant."
- Request the desired detail level and persona explicitly or terse answers will read as lazy.

## 6. Long context and caching

- Query at the very end after all context (same rule as Claude, stronger here).
- Plan prompt layout so the stable prefix is cacheable: explicit context caching is the long-context cost lever (~4x cheaper on Flash).
- Single-needle retrieval is ~99% at 1M tokens but multi-needle degrades — don't assume uniform recall; chunk or chain instead.

## 7. Structured output, multimodal, safety

- For JSON, use response schemas (JSON Schema / Pydantic), not prompt-only formatting; on Gemini 3 schemas combine with built-in tools.
- Multimodal: order media parts before the final text instruction; tune `media_resolution` (high for dense PDFs, lower if the context window overflows — reduce resolution rather than truncating content).
- Safety filters can silently return fallback responses; detect them and retry with higher temperature or a rephrased prompt.

## 8. Migrating a prompt from 2.5-era / other providers

Checklist when retargeting an existing prompt to Gemini 3:

1. Delete manual CoT scaffolding, role-play padding, and persuasion boilerplate → rely on `thinking_level`.
2. Remove explicit temperature settings → default 1.0.
3. Move instructions after the data; add the "Based on the preceding information…" anchor.
4. Add/keep 2–4 format-consistent few-shot examples.
5. Add explicit verbosity/persona instructions if conversational output is wanted.
6. Switch prompt-based JSON formatting to a response schema.
