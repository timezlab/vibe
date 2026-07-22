# System Prompts & Agent Instructions

Distilled from anthropic.com/engineering: "Effective context engineering for AI agents", "Building effective agents", "Claude Code: Best practices for agentic coding", "How we built our multi-agent research system" — plus structural patterns observable in Anthropic's published Claude.ai system prompts (release notes).

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
- Prefer just-in-time loading over pre-loading: keep lightweight identifiers (paths, links, queries) in the prompt and let the agent fetch details with tools when needed.

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
- **Strategic mix**: aspirational positives for judgment areas + a small number of hard prohibitions + pervasive conditionals.
- **Named failure modes are named explicitly**: banned filler words are listed verbatim ("avoids 'genuinely', 'honestly'"), not gestured at. Explicitness beats inference for known failure modes.
- **Nested XML-ish section tags** (`<refusal_handling>`, `<tone_and_formatting>`) with prose paragraphs inside — prose composes better than bullet fragments for behavioral nuance.
- **Built-in epistemic humility**: "Claude often can't know either way and explicitly says so."

## 5. CLAUDE.md / AGENTS.md specifics

- These files are *always-loaded* system-prompt extensions — the attention budget applies at full force. Anthropic's own warning: "Bloated CLAUDE.md files cause Claude to ignore your actual instructions."
- Include only what the model **cannot infer**: unguessable build/test commands, style deltas from language defaults, repo etiquette (branch naming, merge vs rebase), environment quirks, known gotchas.
- Exclude anything derivable from the code, standard conventions, or generic best practices ("write tests", "handle errors") — the model already knows.
- Move situational knowledge into skills or on-demand child files; keep the root file a table of contents (~100 lines is a good target).
- Emphasis ("IMPORTANT", "YOU MUST") does boost adherence — which is exactly why it must be rationed to the one or two rules that deserve it.
- Advisory instructions for judgment calls; deterministic hooks for zero-exception rules. If a rule must hold 100% of the time, enforce it in tooling, not prose.

## 6. Agentic prompts: verification, planning, long horizons

- **Always give the agent a check it can run** — tests, build exit codes, screenshot diffs, validators — and require evidence of success, not claims. This is the single highest-leverage line in an agentic prompt.
- Instruct root-cause fixes, not symptom suppression ("do not weaken the test to make it pass").
- Encode a workflow when the task benefits: explore → plan → code → verify → commit. Gate coding on an approved plan for non-trivial tasks.
- Transparency: have the agent show its plan before executing.
- Long horizons: state how context compaction behaves; instruct persistent note-taking (structured state file + freeform progress notes); consider distinct first-window vs continuation prompts.
- Prefer workflows (fixed pipelines with programmatic gates) for predictable tasks; reserve open-ended agent loops for tasks where the step count genuinely can't be predicted. Start with the simplest structure that works.

## 7. Subagent briefs and multi-agent orchestration

Every subagent brief needs, explicitly:

1. **Objective** — one sentence, narrow. "Research X" is a bad brief.
2. **Context transplant** — the subagent has zero conversation memory; paste every fact it needs.
3. **Tool guidance** — which tools, which sources, what to avoid.
4. **Boundaries** — what NOT to do; scope fences against sibling agents.
5. **Output contract** — exact return shape and length cap ("bullet list of file:line, no prose, under 200 words"). Without it you get pages of narration.

Orchestrator prompts additionally need **effort-scaling rules** (Anthropic's research system: simple query = 1 agent / 3–10 tool calls; comparison = 2–4 subagents; complex = 10+) and search strategy ("start wide, then narrow"). Subagents should return condensed summaries (1–2k tokens), keeping the orchestrator's context clean.

## 8. What to move OUT of the system prompt

- Rarely-needed reference material → files/skills loaded on demand (progressive disclosure).
- Zero-exception rules → hooks/validators/CI, not prose.
- Per-request data → user messages with XML-tagged sections, not the system prompt.
- Anything the current model reliably does unprompted → delete, then re-add only if a real failure appears.
- Old workarounds for older models (caps-lock emphasis, prefill hacks, prescriptive CoT scripts) → re-test on the current model; most are now harmful (see prompting-techniques.md §4 and the provider file's deprecation notes).
