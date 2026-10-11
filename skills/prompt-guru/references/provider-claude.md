# Provider: Anthropic Claude

What to do differently when the target model is Claude 4.x / 5.x (current: Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5; Mythos 5.1 is access-restricted with Fable 5.1's surface). Sources: platform.claude.com/docs "Prompting best practices" (now a hub) and the per-model prompting pages (Fable 5 / 5.1, Opus 5 / 5.5, Sonnet 5.5, Haiku 5.5), effort, thinking, model-deprecations. Anthropic notes that model-named techniques were measured on that model — re-check them on your own evals when the target differs. Apply on top of the general references.

## Contents
1. Delimiters and structure
2. Literal instruction-following
3. Named policy blocks
4. Agentic and long-horizon work
5. Thinking and effort
6. API knobs that replace prompt text
7. Model-family notes
8. Deprecated techniques and migrations

## 1. Delimiters and structure

- **XML tags** help Claude parse complex prompts unambiguously — prefer them over markdown headers for separating instructions, context, data, examples: `<instructions>`, `<context>`, `<document index="n">`, `<example>`.
- Nest tags for hierarchy; keep tag names consistent across the prompt.
- Long documents (20k+ tokens) at the top, query/instructions at the end (~30% quality gain).

## 2. Literal instruction-following

Claude 4+ models follow instructions precisely and literally — this inverts some older habits:

- **Say exactly what you want.** "Can you suggest improvements?" yields suggestions, not edits. Write "Change this function to improve its performance."
- **Dial back aggressive language.** These models are highly system-prompt-responsive: `"CRITICAL: You MUST use this tool when…"` causes overtriggering. Plain `"Use this tool when…"` is correct. Audit migrated prompts for caps-lock inflation.
- **Request above-and-beyond explicitly** when wanted: "Include as many relevant features as possible. Go beyond the basics."
- Legacy Opus 4.5 with thinking disabled is sensitive to the literal word "think" — use "consider", "evaluate", "reason through".

## 3. Named policy blocks

Anthropic's own sample prompts wrap behavioral policies in named XML blocks — easy to find, tune, and remove:

- `<default_to_action>` (act without asking) vs `<do_not_act_before_instructions>` (propose first).
- `<use_parallel_tool_calls>`: "make all independent tool calls in parallel; never guess or use placeholder parameters" (pushes parallelism to ~100%).
- `<investigate_before_answering>`: "Never speculate about code you have not opened" (anti-hallucination).
- Anti-overengineering: "Only make changes that are directly requested. Don't add docstrings, comments, or type annotations to code you didn't change. Only validate at system boundaries."
- Anti-hardcoding: "Implement a solution that works correctly for all valid inputs, not just the test cases. Tests verify correctness; they do not define the solution."

## 4. Agentic and long-horizon work

- State how context compaction behaves: "don't stop early due to token-budget concerns; save progress and state to memory."
- Structured state files (e.g. `tests.json`) + a freeform progress note; git checkpoints; consider a different prompt for the first context window vs continuations.
- Recent models over-delegate to subagents (documented for Opus 4.6, Opus 5, Fable 5): "For simple tasks, sequential operations, or single-file edits, work directly rather than delegating."
- Irreversible actions: instruct confirmation before force-push, `rm -rf`, posting externally; "do not use destructive actions as a shortcut."
- Guide post-tool reflection: "After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding."
- The dose of "verify your work" lines is model-dependent: Opus 5 over-verifies (delete them), while Sonnet 5.5 and Haiku 5.5 at low/medium effort need a real check demanded — "run the tests", not "review your answer". See §7.

## 5. Thinking and effort

- **Effort is the depth lever** on every current model: `output_config.effort` = `low` / `medium` / `high` / `xhigh` / `max`. It scales all tokens, tool calls included, and levels don't map across models — re-sweep when migrating. Defaults: `medium` on Opus 5.5 and Haiku 5.5, `high` elsewhere — set it explicitly.
- **Thinking can't always be turned off**: it is always on (adaptive only) on Fable 5 / 5.1, Mythos, and Opus 5.5; on by default on Opus 5 and Haiku 5.5 (disable only at effort `high` or below); Sonnet 5.5 rejects `disabled` and offers `thinking: {type: "between_tools"}` as its off-switch. A prompt can't rely on "don't think" — lower effort instead; instructions to think less are unreliable on Sonnet 5.5 and Haiku 5.5.
- Prefer general encouragement over prescriptive CoT scripts. To teach a reasoning style, describe it or show it as a rationale in the example answers — not as `<thinking>`-tagged output: requests to write reasoning in tags may be declined (Fable 5 / 5.1, Opus 5 / 5.5, Sonnet 5.5).
- Constrain overthinking when needed: "Choose an approach and commit to it."
- Thinking output is `omitted` by default on the 5.x family and Opus 4.7 / 4.8 (`summarized` is opt-in). Never instruct the model to echo or reveal its reasoning ("show your thinking", "output your chain of thought") — that triggers `reasoning_extraction` refusals; ask for a rationale in the answer instead.

## 6. API knobs that replace prompt text

- **Sampling**: non-default `temperature` / `top_p` / `top_k` return 400 from Opus 4.7 on and on every 5.x model — steer behavior through the prompt and effort, not sampling.
- **Format**: use Structured Outputs (`output_config.format`) for machine-readable output; prefill is gone (§8).
- **Forced tool use**: `tool_choice` `any` / `tool` returns 400 on Fable 5.1, Mythos 5.1, Opus 5.5, and Sonnet 5.5. Use `auto` plus a prompt line naming the tool, `strict: true` for schema-valid arguments, or Structured Outputs when the forced call only existed to get JSON.
- **Mid-conversation instructions**: append a `system`-role message to `messages` instead of editing the top-level system prompt — it keeps the cached prefix and carries operator authority (Opus 4.8+ and 5.x, not Sonnet 5). For a nudge that should apply to one turn only, a turn-scoped system message (`clear_at: "next_user_message"`, beta) is the documented channel.
- **History is append-only**: return thinking blocks unchanged and never rewrite earlier turns (e.g. to inject reminders) — edited history invalidates thinking blocks, and accounts created from 2026-08-31 get a 400 for it.

## 7. Model-family notes

- **Fable 5.1** (most capable widely released): Fable 5 prompts carry over. It formats less than earlier models — drop blanket anti-markdown blocks, which can strip structure the answer needs. Ask for progress updates explicitly. In long loops it may fall back to one tool call per turn; re-nudge parallelism with a turn-scoped system message. Single hard requests can run for many minutes.
- **Opus 5.5** (the default model): may stop early with a text-only `end_turn` — state the completion condition, keep a checklist, and if the harness auto-continues, cap it at 2–3 continues.
- **Opus 5** (previous Opus, still served): writes longer output — prompt for concision; over-verifies — delete explicit verification lines; over-delegates.
- **Sonnet 5.5**: never put user-authored text inside a `tool_result`. At low/medium effort, require a real check rather than trusting self-review. Effort levels were recalibrated — start at `medium` for agentic coding, `low` for chat.
- **Haiku 5.5**: the first Haiku with effort (default `medium`); stops early at `low`. For questions about current facts, give today's date and nudge it to search.

## 8. Deprecated techniques and migrations

- **Prefill is dead** (400 from Claude 4.6 on, including Haiku 5.5; only legacy Haiku 4.5 / Opus 4.5 still accept it). Migrate: format enforcement → Structured Outputs; no-preamble → system-prompt instruction ("Respond directly without preamble. Do not start with phrases like 'Here is…'"); continuation → user message "Your previous response ended with `[text]`. Continue from where you left off."
- `budget_tokens` → `effort` (400 from Opus 4.7 on); forced `tool_choice` → see §6; explicit sampling params → delete.
- **Prompt chaining** is now mainly for inspecting intermediates or enforcing pipelines; the surviving high-value pattern is self-correction: draft → review against explicit criteria → refine, as separate calls.
- Old-style MUST/ALWAYS/NEVER density: soften (see §2).
- Prompts and skills written for prior models are often **too prescriptive for Fable 5 / 5.1** and can degrade output — when migrating, cut step-by-step scaffolding and rigid procedure first; keep the outcome and constraints.
- Retirements: Opus 4.1 is retired and Sonnet 4.5 retires 2026-11-30 — retarget to Sonnet 5.5.
