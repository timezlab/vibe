# Provider: Anthropic Claude

What to do differently when the target model is Claude (4.x / 5 family, including Fable 5 / Mythos 5). Sources: platform.claude.com/docs "Prompting best practices" and "Prompting Claude Fable 5". Apply on top of the general references.

## Contents
1. Delimiters and structure
2. Literal instruction-following (Claude 4+)
3. Named policy blocks
4. Agentic and long-horizon work
5. Thinking control
6. Deprecated techniques and migrations

## 1. Delimiters and structure

- **XML tags** help Claude parse complex prompts unambiguously — prefer them over markdown headers for separating instructions, context, data, examples: `<instructions>`, `<context>`, `<document index="n">`, `<example>`.
- Nest tags for hierarchy; keep tag names consistent across the prompt.
- Long documents (20k+ tokens) at the top, query/instructions at the end (~30% quality gain).

## 2. Literal instruction-following (Claude 4+)

Claude 4/4.5/5 models follow instructions precisely and literally — this inverts some older habits:

- **Say exactly what you want.** "Can you suggest improvements?" yields suggestions, not edits. Write "Change this function to improve its performance."
- **Dial back aggressive language.** These models are highly system-prompt-responsive: `"CRITICAL: You MUST use this tool when…"` causes overtriggering. Plain `"Use this tool when…"` is correct. Audit migrated prompts for caps-lock inflation.
- **Request above-and-beyond explicitly** when wanted: "Include as many relevant features as possible. Go beyond the basics."
- Opus 4.5 with thinking disabled is sensitive to the literal word "think" — use "consider", "evaluate", "reason through".

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
- Subagent delegation is native on 4.5+; curb overuse: "For simple tasks, sequential operations, or single-file edits, work directly rather than delegating."
- Irreversible actions: instruct confirmation before force-push, `rm -rf`, posting externally; "do not use destructive actions as a shortcut."
- Guide post-tool reflection: "After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding."

## 5. Thinking control

- `budget_tokens` is replaced by `effort` on 4.7+; adaptive thinking decides depth.
- Prefer general encouragement over prescriptive CoT scripts; to teach reasoning style, put `<thinking>` passages inside few-shot examples.
- Constrain overthinking when needed: "Choose an approach and commit to it."
- **Fable 5 / Mythos 5**: adaptive thinking is always on (the only mode) and thinking output is summarized-only, so manual CoT scaffolds are pure overhead. `effort` gains an `xhigh` level. Never instruct the model to echo or reveal its reasoning ("show your thinking", "output your chain of thought") — such instructions trigger `reasoning_extraction` refusals; ask for a rationale in the answer instead.

## 6. Deprecated techniques and migrations

- **Prefill is dead** (400 error from Claude 4.6 on). Migrate: format enforcement → Structured Outputs; no-preamble → system-prompt instruction ("Respond directly without preamble. Do not start with phrases like 'Here is…'"); continuation → user message "Your previous response ended with `[text]`. Continue from where you left off."
- **Prompt chaining** is now mainly for inspecting intermediates or enforcing pipelines; the surviving high-value pattern is self-correction: draft → review against explicit criteria → refine, as separate calls.
- Old-style MUST/ALWAYS/NEVER density: soften (see §2).
- Skills and prompts written for prior models are often **too prescriptive for Fable 5** and can degrade output — when migrating, cut step-by-step scaffolding and rigid procedure first, keep the outcome and constraints.
