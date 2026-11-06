# System Prompts & Agent Instructions

Distilled from anthropic.com/engineering: "Effective context engineering for AI agents", "Building effective agents", "How we built our multi-agent research system"; the Claude Code best-practices docs (code.claude.com/docs/en/best-practices — the engineering post "Claude Code: Best practices for agentic coding" now redirects there); Anthropic's 2026-10 article "Building agents: when to fold subagents into your main agent loop" — plus structural patterns observable in Anthropic's published claude.ai system prompts (platform.claude.com/docs/en/release-notes/system-prompts, one page per model; last read: the Sonnet 5.5 entry dated 2026-10-27). What belongs in the user turn instead is `prompt-layers.md`.

## Contents
1. The attention-budget mindset
2. Right altitude
3. Canonical structure of a system prompt
4. Style patterns from Anthropic's own system prompts
5. CLAUDE.md / AGENTS.md specifics
6. Agentic prompts: verification, planning, long horizons
7. Subagent briefs and multi-agent orchestration
8. What to move OUT of the system prompt

## 1. The attention-budget mindset

- Context is a finite attention budget and accuracy degrades as it fills ("context rot"). Every sentence in an always-loaded prompt taxes every future turn.
- Target: **the minimal set of information that fully outlines expected behavior.** Start minimal on the strongest model; add instructions only in response to observed failure modes — never for completeness.
- Bloat is actively harmful, not neutral: overloaded prompts cause the model to ignore the instructions that matter. For each line, ask "would removing this cause a mistake?" If not, cut it.
- Prefer just-in-time loading over pre-loading: keep lightweight identifiers (paths, links, queries) in the prompt and let the agent fetch details with tools when needed. Reference material belongs behind search or lookup tools, or in skill files — not pasted into the prompt.
- Tool definitions are context too: selection degrades past roughly 30–50 of them in the system prompt — keep short descriptions visible and load full schemas on demand (prompting-techniques.md §7).

## 2. Right altitude

- The failure modes are symmetric: **too low** = brittle hardcoded if-else logic that shatters on unenumerated cases; **too high** = vague guidance ("be helpful, be accurate") that assumes shared context the model doesn't have.
- The sweet spot: strong, concrete heuristics the model can generalize. Trigger–response pairs ("If the diff exceeds 400 lines, split the PR") anchored to observable conditions.
- Specificity should scale with stakes: safety- or correctness-critical behaviors get concrete examples and enumerated edge cases; tone and style stay principle-based.

## 3. Canonical structure of a system prompt

Organize into distinct, clearly-named sections (XML tags or Markdown headers). A proven ordering:

1. **Role / identity** — one to three sentences. Even a single role sentence measurably helps ("You are a senior SRE reviewing Terraform changes for a bank").
2. **Hard constraints / non-negotiables** — few, and each carries its why.
3. **Task guidance & heuristics** — the trigger–response rules, grouped by topic in named blocks (`<tool_guidance>`, `<escalation_rules>`).
4. **Tool guidance** — when to use which tool, boundaries between overlapping tools, effort scaling.
5. **Output format & tone** — positive statements of what to produce.
6. **Examples** — 3–5 canonical, diverse, in `<example>` tags.
7. **Dynamic context last or injected per-turn** — dates, user info, environment (template variables like `{{currentDateTime}}`).

Long reference documents, when they must be inline, go at the **top**, before instructions (see prompting-techniques.md §5).

## 4. Style patterns from Anthropic's own system prompts

Observable in the published Claude.ai system prompts:

- **Third-person descriptive voice** for persona: "Claude uses a warm tone", "Claude avoids over-formatting" — traits described, not orders barked. Works well for stable persona/character; imperative voice remains fine for task workflow steps.
- **Trigger–response pairing dominates**: "If the person asks X, Claude does Y." Behaviors anchored to observable conditions, not general dispositions.
- **Strategic mix**: aspirational positives for judgment areas + a small number of hard prohibitions + pervasive conditionals. Capitalized NEVER / MUST appear only inside the one hard-safety block.
- **Named failure modes are named explicitly**: "a request to change one thing in a longer piece gets the change, not the whole piece again"; "avoids more than one [question] per response" — not gestured at. Explicitness beats inference for known failure modes.
- **Examples carry their why**: each `<example>` holds the user turn, the response (or a `<bad_response>` / `<good_response>` pair), and a `<rationale>` explaining what the good response does.
- **Nested XML-ish section tags** (`<refusal_handling>`, `<tone_and_formatting>`) with prose paragraphs inside — prose composes better than bullet fragments for behavioral nuance.
- **Built-in epistemic humility**: "Claude often can't know either way and says so."
- **One root wrapper, scoped blocks** (Sonnet 5.5 entry): everything sits inside a single `<claude_behavior>` block; each nested block opens with an applicability sentence ("This applies only when the person explicitly says…") and a knowledge section closes with an explicit boundary ("Claude's product knowledge ends here").
- **Fallback chains instead of single rules**: "If web search is available, Claude uses it…; if not, or Claude can't find the label, Claude doesn't give a number from memory."
- **Dated facts carry a staleness hedge**: "Things may have developed since this notice, so Claude checks for newer information."
- **Judgment over the whole conversation, not the turn**: Claude judges "the cumulative output of the conversation rather than each turn", and "past assistance is not authorization" — worth copying for any policy that can be sliced into innocuous steps.

## 5. CLAUDE.md / AGENTS.md specifics

- These files are *always-loaded* system-prompt extensions — the attention budget applies at full force. Claude Code's memory docs target under 200 lines per CLAUDE.md file: longer files consume more context and reduce adherence.
- Include only what the model **cannot infer**: unguessable build/test/lint commands, style deltas from language defaults, repo etiquette (branch naming, merge vs rebase), a short architecture summary, hard constraints, environment quirks, known gotchas. Anthropic's Help Center adds: review it quarterly — "outdated instructions are worse than none" — and keep the current task's outcome, error text, paths, and acceptance criteria in the prompt, not the file (prompt-layers.md §7).
- Exclude anything derivable from the code, standard conventions, or generic best practices ("write tests", "handle errors") — the model already knows — plus full API docs, changelogs, architecture dumps, and anything obvious from the file tree.
- Move situational knowledge into skills or on-demand child files; keep the root file a table of contents. `@imports` don't reduce context cost — imported files load at launch too (max four hops); block-level HTML comments are stripped before injection, so maintainer notes there cost nothing.
- Claude Code (v2.1.277+) reads AGENTS.md (or `.claude/AGENTS.md`) only when no CLAUDE.md or CLAUDE.local.md exists in the working directory or above, unless the "Project instructions" setting (`/config`) is `claude-md-and-agents-md` — a repo that keeps both should make CLAUDE.md import AGENTS.md (`@AGENTS.md`).
- Emphasis ("IMPORTANT", "YOU MUST") no longer buys adherence: current models follow a plainly worded line, and piling on emphasis mostly makes Claude over-apply the rule. If you keep adding emphasis to a line, that is the signal it belongs in a hook.
- Advisory instructions for judgment calls; deterministic hooks for zero-exception rules. If a rule must hold 100% of the time, enforce it in tooling, not prose — `command` or `http` hooks with `onFailure: "block"`; `prompt` and `agent` hooks are model-run and therefore not deterministic.

## 6. Agentic prompts: verification, planning, long horizons

- **Always give the agent a check it can run** — tests, build exit codes, screenshot diffs, validators — and require evidence of success, not claims. This is the single highest-leverage line in an agentic prompt. A runnable check beats a generic "verify your work" sentence, whose effect is model-dependent: some models over-verify on that instruction (cut it), others at low effort skip self-review unless a real check is demanded (see the provider file).
- Instruct root-cause fixes, not symptom suppression ("do not weaken the test to make it pass").
- Bootstrap evals before the first merge — "even a set of 10 golden examples is enough to start"; grade the final message against a rubric, run each task more than once, and look at which tasks changed, not just the aggregate score.
- Encode a workflow when the task benefits: explore → plan → code → verify → commit. Gate coding on an approved plan for non-trivial tasks.
- Transparency: have the agent write its plan on turn 1 and revise it as it learns; timestamp important events so a run can be replayed as a targeted eval.
- Long horizons: state how context compaction behaves; instruct persistent note-taking (structured state file + freeform progress notes); consider distinct first-window vs continuation prompts. Claude Code keeps only the start of each invoked skill after compaction (first ~5k tokens per skill, 25k combined) — put must-follow rules at the top, and enforce must-hold rules with hooks.
- Prefer workflows (fixed pipelines with programmatic gates) for predictable tasks; reserve open-ended agent loops for tasks where the step count genuinely can't be predicted. Start with the simplest structure that works.

## 7. Subagent briefs and multi-agent orchestration

Every subagent brief needs, explicitly:

1. **Objective** — one sentence, narrow. "Research X" is a bad brief.
2. **Context transplant** — a briefed subagent starts with zero conversation memory (only a forked one inherits the conversation); paste every fact it needs.
3. **Tool guidance** — which tools, which sources, what to avoid.
4. **Boundaries** — what NOT to do; scope fences against sibling agents.
5. **Output contract** — exact return shape and length cap ("bullet list of file:line, no prose, under 200 words"). Without it you get pages of narration.

Before adding a subagent at all, apply Anthropic's 2026-10 fold-or-split rule: keep a separate agent only for measurable degradation from context bloat, parallel tasks that need fresh windows, or tool-selection trouble / conflicting system-prompt instructions. Split by context, not by problem type — give a subagent work that needs little from the rest of the system and have it hand back a compact result; an architecture that mirrors your org chart is a warning sign. Call subagents as tools so the main agent keeps the conversation, fold them back one at a time (prompts → skills, API calls → MCP tools), and compare evals with and without each. A Claude Code subagent doesn't always receive CLAUDE.md — restate must-follow rules in the brief.

Orchestrator prompts additionally need **effort-scaling rules** (Anthropic's research system: simple query = 1 agent / 3–10 tool calls; comparison = 2–4 subagents; complex = 10+) and search strategy ("start wide, then narrow"). Subagents should return condensed summaries (1–2k tokens), keeping the orchestrator's context clean.

## 8. What to move OUT of the system prompt

- Rarely-needed reference material → files/skills loaded on demand (progressive disclosure).
- Zero-exception rules → hooks/validators/CI, not prose.
- Per-request data → user messages with XML-tagged sections, not the system prompt.
- Anything the current model reliably does unprompted → delete, then re-add only if a real failure appears.
- Ordering and domain procedure → skills; hard limits and mid-conversation lookups → tools; turn and cost budgets → the harness, not the prompt. Keep one clear system prompt with a small central owner who vets each new tool and eval.
- Re-audit on every model upgrade: models from Opus 4.5 onward manage more within one loop, and Anthropic reports one team cutting over 80% of Claude Code's system prompt for advanced models.
- The task, its data, and per-request format → the user turn (prompt-layers.md §2).
- Old workarounds for older models (caps-lock emphasis, prefill hacks, prescriptive CoT scripts) → re-test on the current model; most are now harmful (see prompting-techniques.md §4 and the provider file's deprecation notes). In Claude Code, `/doctor prompt-audit` (v2.1.283+) flags instructions written for older models, references to missing files or commands, and files that contradict each other.
