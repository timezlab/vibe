# Provider: Anthropic Claude

What to do differently when the target model is Claude 4.x / 5.x (current: Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5; Mythos 5.1 is access-restricted with Fable 5.1's surface). Sources: platform.claude.com/docs "Prompting best practices" (one page: per-model guidance, techniques for all models, migration) and the per-model prompting pages (Fable 5 / 5.1, Opus 4.8 / 5 / 5.5, Sonnet 5 / 5.5, Haiku 5.5); effort, thinking, mid-conversation system messages, prompt caching, preserved thinking, tool definitions, model deprecations, the API `2026-10-21` release notes. Anthropic notes that model-named techniques were measured on that model — re-check them on your own evals when the target differs. Apply on top of the general references; the system-vs-user-turn split is `prompt-layers.md`.

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
- **Request above-and-beyond explicitly** when wanted: "Include as many relevant features as possible. Go beyond the basics." The inverse holds too: open-ended asks overshoot — if you want ideas or a plan rather than the work, say so (Sonnet 5.5 page).
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
- Unattended runs: the Opus 5.5 page's unattended-agent paragraph goes at the end of the system prompt from the first request, not mid-conversation. Sonnet 5.5 at `low` effort may skip verification and Haiku 5.5 stops early at `low` — add the pages' verification paragraph plus "Keep working until everything the user asked for is done…" when running them there.
- The dose of "verify your work" lines is model-dependent: Opus 5 over-verifies (delete them), while Sonnet 5.5 and Haiku 5.5 at low/medium effort need a real check demanded — "run the tests", not "review your answer". The Opus 5.5 and Fable 5.1 pages document no verification quirk — default to a runnable check with no self-review line, and add one only after an observed miss. See §7.

## 5. Thinking and effort

- **Effort is the depth lever** on every current model: `output_config.effort` = `low` / `medium` / `high` / `xhigh` / `max`. It scales all tokens, tool calls included, and levels don't map across models — re-sweep when migrating. API defaults: `medium` on Opus 5.5 and Haiku 5.5, `high` on Fable 5.1, Mythos 5.1, and Sonnet 5.5 — set it explicitly (Claude Code sets its own default, `medium`, for all three current models). At `xhigh` / `max`, give `max_tokens` room for thinking plus the reply (Fable 5.1 page).
- **Thinking can't always be turned off**: always on (adaptive only) on Fable 5 / 5.1, Mythos, and Opus 5.5 (`disabled` returns 400 at every effort); on by default on Opus 5 and Haiku 5.5 (disable only at effort `high` or below — 400 at `xhigh` / `max`); Sonnet 5.5 rejects `disabled` and offers `thinking: {type: "between_tools"}` as its off-switch at `low` / `medium` / `high` only (no `display`, `budget_tokens`, or `block_binding` with it). A prompt can't rely on "don't think" — lower effort instead.
- **Prompt lines don't reduce thinking**: Opus 5.5 — lowering effort is more reliable than any prompt line, and "think carefully" lines in chat system prompts should go; Haiku 5.5 — "answer directly" didn't stop it thinking; Sonnet 5.5 in `between_tools` — remove "don't think" instructions, they leak internal XML tags into visible output.
- Prefer general encouragement over prescriptive CoT scripts. To teach a reasoning style, describe it or show it as a rationale in the example answers — not as `<thinking>`-tagged output: requests to write reasoning in tags may be declined (Fable 5 / 5.1, Opus 5 / 5.5, Sonnet 5.5). For structured JSON on reasoning tasks (Sonnet 5.5): adaptive thinking plus "Think the problem through before you answer." at the end of the system prompt; treat `stop_reason: "max_tokens"` as a failed call.
- Constrain overthinking when needed: "Choose an approach and commit to it."
- Thinking output is `omitted` by default on the 5.x family and Opus 4.7 / 4.8 (`summarized` is opt-in). Never instruct the model to echo or reveal its reasoning ("show your thinking", "output your chain of thought") — that triggers `reasoning_extraction` refusals; ask for a short explanation or an action summary in the answer, and read `display: "summarized"` blocks when you need the reasoning itself. `display: "updates"` (beta header `thinking-display-updates-2026-08-18`) returns progress-update thinking blocks on Opus 5.5 and Sonnet 5.5 — without it those blocks arrive empty and the client looks silent.

## 6. API knobs that replace prompt text

- **Sampling**: removed in API version `2026-10-21` — any `temperature` / `top_p` / `top_k` returns 400; on earlier API versions, non-default values return 400 from Opus 4.7 on and on every 5.x model. Steer behavior through the prompt and effort, not sampling.
- **Per-message effort**: a `system`-role message carrying `output_config.effort` (beta header `mid-conversation-output-config-2026-07-01`; Fable 5.1, Mythos 5.1, Opus 5 / 5.5, Sonnet 5.5, Haiku 5.5) changes depth mid-conversation without touching the top-level `output_config.effort`, which invalidates the message-block cache. Returns 400 when combined with Sonnet 5.5 `between_tools` or Haiku 5.5 `disabled`.
- **Format**: use Structured Outputs (`output_config.format`) for machine-readable output; prefill is gone (§8). Haiku 5.5 with thinking off may skip a needed tool call when JSON output is also requested — keep adaptive thinking on, or drop `format` for those requests.
- **Forced tool use**: `tool_choice` `any` / `tool` returns 400 on Fable 5.1, Mythos 5.1, Opus 5.5, and Sonnet 5.5 (`auto` / `none` work); Opus 5 and Haiku 5.5 accept forced use, but a forced call skips thinking and changes the message-block cache. Use `auto` plus a prompt line naming the tool, `strict: true` for schema-valid arguments, or Structured Outputs when the forced call only existed to get JSON.
- **Mid-conversation instructions**: append a `system`-role message to `messages` instead of editing the top-level system prompt (no beta header; Fable 5 / 5.1, Mythos 5 / 5.1, Opus 4.8, Opus 5, Opus 5.5, Sonnet 5.5, Haiku 5.5 — not Sonnet 5, where only the top-level `system` field exists). Anthropic's layer rule: a `system` message "is treated as coming from you, the application operator" and takes precedence when it conflicts with a user turn — use it for operator facts and constraints that must hold even if the end user asks otherwise; keep the top-level `system` for whole-conversation instructions; never pass tool output or retrieved documents through it (those stay in `tool_result` blocks). For a nudge that applies to one turn only, `clear_at: "next_user_message"` (beta header `mid-conversation-system-clear-at-2026-08-21`) is the documented channel; without the beta, put the sentence in a text block after the `tool_result` blocks (Fable 5.1 page). Placement rule on Sonnet 5.5 and Haiku 5.5: the user's own mid-task words go in the user turn as a text block after the last `tool_result` — a system message placed right after a tool result can be treated as untrusted text and ignored. On Haiku 5.5, editing the top-level `system` mid-conversation can 400 when thinking blocks are sent back.
- **History is append-only**: return thinking blocks unchanged and never rewrite earlier turns (e.g. to inject reminders) — edited history invalidates thinking blocks, and accounts created from 2026-08-31 (00:00 UTC) get a 400 for it. On Fable 5.1, `thinking.block_binding.prefix_mismatch_behavior` (`"error"` or `"drop_block"`, beta header `thinking-binding-controls-2026-08-01`) controls that 400.
- **Prompt caching decides ordering**: stable content first — `tools`, then `system`, then history — with changing instructions as appended system messages at the end; render the date once per conversation and keep `system` and `tools` byte-identical afterwards. The minimum cacheable prompt is 512 tokens on the 5.x models (1,024 on Opus 4.8, Sonnet 5, Sonnet 4.6); up to 4 breakpoints with a 20-block lookback. Cache invalidators: tool-definition edits, `system` edits, thinking config, top-level `output_config.effort`, `speed: "fast"`, dropped thinking blocks (5.1 and later), `tool_choice` (message blocks), and images.

## 7. Model-family notes

- **Fable 5.1** (most capable widely released): Fable 5 prompts carry over. It formats less than earlier models (less bold, fewer headers and lists) — drop blanket anti-markdown blocks, which can strip structure the answer needs; the page's "Formatting in chat" section is the replacement. Its per-model lines are designed to be sent as turn-scoped system messages after each round of tool results. Writing is denser than Fable 5's — "Please remove all mannered prose." when it reads over-styled. It tends to rewrite whole files — instruct targeted edits; it searches less at `low` effort; in long loops it may fall back to one tool call per turn — re-nudge parallelism with a turn-scoped system message. Ask for progress updates explicitly. Single hard requests can run for many minutes.
- **Opus 5.5** (the default model): may stop early with a text-only `end_turn` — state the completion condition, keep a checklist, and if the harness auto-continues, cap it at two or three continuations. Wrap user-pasted text in `<pasted_content id="ab12">…</pasted_content id="ab12">` with a random per-block id and tell it in the system prompt that text inside those tags is untrusted. Lower effort before prompting it to think less. Use `display: "updates"` for progress visibility.
- **Opus 5** (previous Opus, still served): writes longer output — prompt for concision; over-verifies — delete explicit verification lines; over-delegates.
- **Sonnet 5.5**: never put user-authored text inside a `tool_result`. Effort levels were recalibrated — the API default is `high`; Anthropic suggests sweeping down to `medium` for agentic coding and `medium` / `low` for chat. At `low` it may skip verification and at `low` / `medium` it may check in early on long tasks — require a real check ("run the tests", not "review your answer") and state that the task continues until done. Open-ended asks overshoot — say "ideas only" or "plan only" when that is what you want.
- **Haiku 5.5**: the first Haiku with effort (default `medium`); stops early at `low`. For questions about current facts, give today's date and a *scoped* search nudge — a blanket "search for any present-day factual question" made it search on half of the no-search prompts. For chatbots, add "The rules in this system prompt hold for the whole conversation…". Render the date once and keep `system` / `tools` byte-identical afterwards.

## 8. Deprecated techniques and migrations

- **Prefill is dead** (400 from Claude 4.6 on, including Haiku 5.5; only legacy Haiku 4.5 / Opus 4.5 still accept it). Migrate: format enforcement → Structured Outputs; no-preamble → system-prompt instruction ("Respond directly without preamble. Do not start with phrases like 'Here is…'"); continuation → user message "Your previous response ended with `[text]`. Continue from where you left off."; refusal steering and context reminders → the user turn.
- `budget_tokens` → `effort` (400 from Opus 4.7 on); forced `tool_choice` → see §6; sampling params → delete (removed outright in API version `2026-10-21`).
- **Prompt chaining** is now mainly for inspecting intermediates or enforcing pipelines; the surviving high-value pattern is self-correction: draft → review against explicit criteria → refine, as separate calls.
- Old-style MUST/ALWAYS/NEVER density: soften (see §2) — current models follow a plainly worded line, and stacked emphasis mostly makes them over-apply the rule.
- Prompts and skills written for prior models are often **too prescriptive for Fable 5 / 5.1** and can degrade output — when migrating, cut step-by-step scaffolding and rigid procedure first; keep the outcome and constraints. Anthropic reports one team cutting over 80% of Claude Code's system prompt for advanced models.
- Retirements: Opus 4.1 retired 2026-08-05; Sonnet 4.5 (deprecated 2026-09-30) retires 2026-11-30 — retarget to Sonnet 5.5; Opus 4.5 retires no sooner than 2026-11-24; Haiku 4.5's "no sooner than 2026-10-15" date has passed while the page still lists it as active — treat it as going. Current models retire no sooner than 2027-09 (Fable 5.1, Opus 5.5, Sonnet 5.5) / 2027-10 (Haiku 5.5).
