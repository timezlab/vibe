# Prompting Techniques (provider-agnostic)

General techniques that hold across providers. Distilled primarily from Anthropic's "Prompting best practices" and "Writing effective tools for agents"; cross-checked against OpenAI and Google guidance. For provider-specific deltas (delimiter preferences, deprecated features, model-family quirks), read the matching `provider-*.md` after this file.

## Contents
1. Clarity and directness
2. Structure and delimiters
3. Examples (multishot)
4. Reasoning / chain of thought
5. Long context
6. Output formatting
7. Tool descriptions

## 1. Clarity and directness

- Treat the model as a brilliant new employee with no context on your norms. Spell out the situation, the audience, and what "done" looks like.
- Golden rule: show the prompt to a colleague with minimal context — if they'd be confused, the model will be.
- Use numbered steps when order or completeness matters.
- Attach motivation to rules; models generalize from the why. `"Your response is read aloud by TTS, so never use ellipses — the engine can't pronounce them"` covers cases a bare prohibition doesn't.
- Modern frontier models follow instructions literally: say exactly what you want ("Change this function", not "Can you suggest improvements?") and request above-and-beyond behavior explicitly rather than relying on inference.

## 2. Structure and delimiters

- Wrap each content type in its own clearly-named section so instructions and data can't blur: instructions, context, input, examples, documents.
- Use one delimiter style consistently throughout the prompt. The preferred style varies by provider — XML tags for Claude, markdown or XML for OpenAI models, either for Gemini (see the `provider-*.md` files) — but consistency matters more than the choice; JSON performs poorly as a delimiter.
- Nest sections for hierarchy (documents → document → source/content); give sections descriptive names.
- Group behavioral policies into named blocks (one topic per block) so they're easy to find, tune, and remove during iteration.

## 3. Examples (multishot)

- 3–5 examples, clearly delimited (e.g. `<example>` tags or an "Examples" section).
- Make them **relevant** (mirror the real use case), **diverse** (cover distinct patterns and edge cases without embedding unintended regularities), **structured**.
- Examples silently teach everything they contain — format, tone, length, reasoning style. Audit them for accidental patterns (all examples short → model answers short).
- To teach reasoning style, include worked reasoning inside the examples; the model generalizes the demonstrated pattern.

## 4. Reasoning / chain of thought

- For **reasoning-capable models** (extended thinking / o-series / Gemini thinking): prefer general encouragement ("consider the edge cases before answering") over prescriptive step-by-step reasoning scripts — the model's own reasoning usually beats a hand-written plan, and forced CoT can degrade reasoning models. Control depth via API knobs (effort/budget), not prompt begging.
- For **non-reasoning models**: structure manual CoT with explicit reasoning-then-answer sections (`<thinking>` / `<answer>`).
- Add self-checks: `"Before you finish, verify your answer against <criteria>."`
- For agents: instruct reflection after tool results before deciding next steps.

## 5. Long context

- Put longform data (20k+ tokens) at the **top** of the prompt; query and instructions at the **end**. Anthropic reports up to ~30% quality improvement from query-at-the-end. (Some providers additionally recommend repeating key instructions at both top and bottom — see provider files.)
- Wrap each document in an indexed section with source metadata.
- Ground answers in evidence: `"First find the quotes most relevant to the question and place them in <quotes> tags; then answer based on those quotes."`

## 6. Output formatting

- State what TO produce: `"Respond in smoothly flowing prose paragraphs"` — not `"Do not use markdown"`.
- Prompt style begets output style: markdown-heavy prompts produce markdown-heavy answers.
- For strict machine-readable output (JSON), use the provider's structured-output / response-schema API feature, not prompt begging.
- Suppressing preamble: instruct `"Respond directly without preamble. Do not start with phrases like 'Here is…'"`.

## 7. Tool descriptions

Tool descriptions are prompts and are optimized the same way:

- Describe each tool "as you would to a new hire": purpose, example usage, edge cases, input format, and explicit boundaries against sibling tools. Small description refinements yield outsized accuracy gains.
- Unambiguous parameter names: `user_id`, not `user`. Poka-yoke arguments so mistakes are structurally hard (e.g., require absolute paths).
- Few consolidated tools over many endpoint wrappers: `schedule_event` beats `list_users` + `list_events` + `create_event`. Namespace related tools (`asana_projects_search`).
- Returns must be token-efficient and human-readable: names over UUIDs, pagination/filtering/truncation defaults, optional `response_format: concise|detailed`.
- Error messages must be actionable — suggest the fix, don't emit codes.
- Let the model improve its own tools: give it failure transcripts and ask it to rewrite the descriptions (Anthropic reports large measured gains from Claude-optimized tool descriptions on its internal Slack/Asana tooling).
