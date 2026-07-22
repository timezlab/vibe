# Provider: OpenAI (GPT-4.1, GPT-5.x, o-series)

What to do differently when the target model is an OpenAI model. Sources: developers.openai.com prompting guides (GPT-4.1, GPT-5, 5.1, 5.2, 5.6 — cookbook.openai.com redirects there), platform.openai.com prompt-engineering and reasoning-best-practices docs, Model Spec. Apply on top of the general references.

## Contents
1. Structure and delimiters
2. Instruction placement and conflicts
3. Reasoning models vs non-reasoning models
4. Agentic reminder blocks and eagerness tuning
5. API knobs that replace prompt text
6. Instruction hierarchy and untrusted content
7. Model-family gotchas

## 1. Structure and delimiters

- Prefer **Markdown headers** as the primary skeleton (not XML-first as with Claude). Proven skeleton: `# Role and Objective / # Instructions (+ subsections) / # Reasoning Steps / # Output Format / # Examples / # Context / # Final instructions`. Note the newest GPT-5.x cookbook prompts express behavioral policies as named XML constraint blocks (`<tool_preambles>`, `<persistence>`, `<context_gathering>`…) on top of that skeleton — both styles are sanctioned.
- XML is a sanctioned secondary delimiter, mainly for document collections in long context. Avoid JSON-wrapping document collections — it performed poorly.
- Structure developer messages as Identity / Instructions / Examples / Context; put cache-stable content at the start, variable context near the end.
- Pass tools via the API `tools` field, never pasted schemas; tool usage examples go in a `# Examples` section, not the description field.

## 2. Instruction placement and conflicts

- Long context: place instructions at **BOTH beginning AND end** (if only once, above the context). This differs from Claude's top-data/bottom-query pattern.
- On conflicting instructions, GPT-4.1 follows the one **closest to the end** — plan repetition and overrides accordingly.
- In long conversations, restate formatting rules every 3–5 messages.
- **Audit for contradictions first** — GPT-5.x burns reasoning tokens reconciling conflicts; removing contradictions beats adding instructions.

## 3. Reasoning models vs non-reasoning models

- **Reasoning models (o-series, GPT-5 at medium+ effort)**: keep prompts brief and high-level — goal, constraints, output contract. Do NOT add "think step by step" (it can hurt). Zero-shot first; add few-shot only if needed. `Formatting re-enabled` on the first line of the developer message restores markdown for o-series.
- **Non-reasoning models (GPT-4.1, GPT-5.1 at `none`, GPT-5 at `minimal`)**: induce CoT explicitly ("First, think carefully step by step about…"), add explicit planning/reflection reminders ("plan extensively before each function call, and reflect extensively on the outcomes"), and be precise — they follow instructions extremely literally.
- When reasoning effort drops to minimal/none, prompt text must compensate: reapply GPT-4.1-style scaffolding.

## 4. Agentic reminder blocks and eagerness tuning

- Three system-prompt reminders worth ~20% on SWE-bench (GPT-4.1):
  1. **Persistence**: "Keep going until the user's query is completely resolved before ending your turn."
  2. **Tool-calling**: "Use tools to gather information; do NOT guess or make up an answer."
  3. **Planning**: "Plan extensively before each function call, and reflect extensively on the outcomes."
- **Reduce over-exploration** (GPT-5): lower `reasoning_effort`, set tool-call budgets ("absolute maximum of 2 tool calls for this step"), define early-stop criteria.
- **Prevent premature stopping**: persistence text ("Never stop or hand back to the user when you encounter uncertainty") + **escape hatches** ("decide the most reasonable assumption, proceed, and document it") so the model acts under uncertainty instead of asking.
- Tool preambles: instruct the model to rephrase the goal and outline a plan before calling tools; "Parallelize tool calls whenever possible."
- Quantify where Claude prompts would use prose: update cadence ("at least every 6 execution steps or 8 tool calls"), answer length ("≤10-line change: 2–5 sentences or ≤3 bullets"), plan granularity ("2–5 milestone items, exactly one in_progress").
- GPT-5.2 over-engineers: "Implement EXACTLY and ONLY what the user requests… no UX embellishments."
- On the newest generation (GPT-5.6+), prefer **outcome-first** framing over stacking prescriptive reminder blocks — see §7.

## 5. API knobs that replace prompt text

- `reasoning_effort` controls depth (per-model); `verbosity` param sets global output length, overridable in natural language per-context ("Use high verbosity for writing code").
- Responses API with `previous_response_id` / `store: true` carries reasoning state across tool calls (measured +4.3pt on Tau-Bench) — prefer it over re-prompting context.
- Pin production to dated model snapshots (`gpt-4.1-2025-04-14`) and eval before switching. Change one thing per eval run.
- Metaprompting is first-class: feed the model its own failure traces and ask "what minimal edits would fix these shortcomings?"

## 6. Instruction hierarchy and untrusted content

- Use the `developer` role (replaces "system" in the Responses API). Model Spec chain of command: Platform > Developer > User > Guideline.
- Quoted/untrusted text carries **no instruction authority** — wrap retrieved or user-supplied data in quoted blocks / `untrusted_text` markers so injected instructions are ignored.

## 7. Model-family gotchas

- **GPT-4.1**: extremely literal; one clear sentence redirects it. Needs explicit CoT and the three agentic reminders. Diff format: context lines (SEARCH/REPLACE, V4A), no line numbers.
- **GPT-5**: hurt most by vague/contradictory prompts; may over-explore (soften "BE THOROUGH" maximizers, add budgets) or stop early (persistence + escape hatches).
- **GPT-5.1/5.2**: reasoning mode `none` behaves like a non-reasoning model; quantify cadence/length numerically; 5.2 needs scope discipline and schema-plus-null rules for extraction ("set null rather than guessing; re-scan before returning").
- **GPT-5.6** (Sol/Terra/Luna variants): prompt **outcome-first** — define the desired outcome and stopping conditions instead of prescribing procedure (OpenAI cites 10–15% eval gains over prescriptive prompts); over-prescription, not under-specification, is the failure mode. For agents, use the plan-thoroughly / tool-preamble / TODO-tool triad from the official guide.
- **o-series**: brief high-level prompts, no CoT prompting, zero-shot first, delimiters for input sections, `Formatting re-enabled` for markdown.
