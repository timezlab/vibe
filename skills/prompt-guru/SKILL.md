---
name: prompt-guru
description: Creates and optimizes prompts end-to-end — writes new system prompts, agent instructions, SKILL.md skills, CLAUDE.md/AGENTS.md files, subagent briefs, and tool descriptions from a bare task description, and rewrites, debugs, or ports existing ones — following official provider best practices for Anthropic Claude, OpenAI GPT/o-series, Google Gemini, and open-weight models (Llama, Mistral, Qwen, DeepSeek, Grok), with a research step that fetches current vendor docs when the target model or domain isn't covered. Use whenever the user asks to create, improve, or debug any prompt, system prompt, agent persona, skill, or tool description — including when they only describe what an agent or bot should do ("build me an agent that…") without saying the word "prompt" — and when they complain that an agent ignores instructions, over- or under-triggers a skill/tool, hallucinates, produces the wrong format, or gives poor output quality traceable to its instructions.
---

# Prompt Engineer

One skill, two jobs: **create** a prompt from a task description, or **optimize** an existing one. Both end with the same deliverable: (a) the finished prompt, (b) a change log / design-decision log that maps each choice to the principle behind it — so the user learns the pattern, not just this fix — and (c) 2–3 concrete test inputs, because behavior on real tasks, not opinion, is the actual verdict.

## Workflow

### 0. Route the request

- **Nothing written yet** (only a task description, "build me an agent that…") → Create path (step 4A), after steps 1–3.
- **Existing prompt text** → Optimize path (step 4B).
- **Existing prompt + different target provider** → port: read both source and target provider files, apply the target's migration checklist (where the provider file has one; otherwise apply its full delta list), then step 4B.

### 1. Establish the ground truth

Before touching any text, determine:

- **Artifact type** — system prompt / agent instructions, a Skill (SKILL.md), CLAUDE.md / AGENTS.md, a tool description, a subagent brief, or a one-off task prompt. Each has a different reference file below.
- **Target model and provider** — techniques differ materially by provider (delimiter style, instruction placement, sampling defaults, reasoning control) and by whether the model is a reasoning model. Identify the exact model family; if unstated, ask — or when you can't, assume a current Claude model and say so.
- **Observed failure modes** (optimize) — ask or infer what actually goes wrong: ignores instructions, wrong format, hallucinates, over-triggers, too verbose, stops early. Optimization without a target failure is guessing.
- **Success criteria + 1–2 example inputs with ideal outputs** (create) — Anthropic's stated prerequisite for prompt engineering is a success definition and a way to test it. The intake questions live in [references/prompt-generation.md](references/prompt-generation.md) §1. When you can't ask (non-interactive run), state your assumptions explicitly in the deliverable.
- **The full current text** — read all of it. Never optimize a fragment; a "redundant" line may be load-bearing elsewhere.

### 2. Research when the references can't answer (conditional)

Read [references/research.md](references/research.md) and run it when ANY of these holds:

- The target model family is **missing** from the provider table below, or **newer** than the content snapshot date in research.md §1 — provider guidance rots fastest around sampling defaults and deprecated params.
- The prompt must embed **domain constants** (API schemas, product rules, regulatory text, rubrics) that neither the user nor the codebase supplied — never invent constants from memory; a confidently wrong constant is worse than a gap.
- The artifact is high-stakes and **exemplars** would help (Anthropic's published production system prompts, existing skills in this repo).

Otherwise skip — research answers specific questions; it is not a ritual. Cite every fetched source in the change log.

### 3. Read the matching references

| Artifact | Read |
|----------|------|
| New prompt from a bare task description | [references/prompt-generation.md](references/prompt-generation.md), then ALSO the row below matching the artifact being created |
| System prompt, agent persona, CLAUDE.md/AGENTS.md, subagent brief, multi-agent orchestration | [references/system-prompts.md](references/system-prompts.md) |
| Skill (SKILL.md + resources), skill description/triggering | [references/skills-authoring.md](references/skills-authoring.md) |
| Any prompt text: task prompts, formatting, examples, structure, tool descriptions | [references/prompting-techniques.md](references/prompting-techniques.md) |

Then read the provider file for the target model (always, when the provider is known):

| Target model | Read |
|--------------|------|
| Anthropic Claude | [references/provider-claude.md](references/provider-claude.md) |
| OpenAI GPT-4.1 / GPT-5.x / o-series | [references/provider-openai.md](references/provider-openai.md) |
| Google Gemini | [references/provider-gemini.md](references/provider-gemini.md) |
| Llama, Mistral, Qwen, DeepSeek, Grok, other open-weight | [references/provider-open-models.md](references/provider-open-models.md) |

Most optimize jobs need `prompting-techniques.md` + one artifact reference + one provider reference; the create path adds `prompt-generation.md` on top (four files). Read whole reference files, not the first 100 lines.

### 4A. Create path

Follow [references/prompt-generation.md](references/prompt-generation.md): intake → pick an architecture → draft minimal. Then treat your own draft as input to step 4B — first drafts, including yours, always over-specify, and the diagnose pass is what tightens them.

### 4B. Optimize path

**Diagnose before rewriting.** Walk the prompt against the reference checklists and list concrete findings ("line 12 says 'do NOT use bullets' — negative instruction, restate positively"), not vibes ("could be clearer"). Classify each finding:

- **Cut** — doesn't earn its tokens: derivable by the model, duplicated, dead weight. Bloat is not neutral; it causes real instructions to be ignored.
- **Rewrite** — right idea, wrong shape (vague, negative, aggressive caps, wrong altitude, missing the why).
- **Add** — a genuine gap tied to an observed/likely failure mode. Add instructions only for failures, not for completeness.
- **Restructure** — ordering and sectioning (long data on top, instructions at the end, clearly delimited sections).

**Then rewrite.** Apply the core principles below plus the reference specifics. Preserve the author's intent and domain rules exactly — you are changing the *engineering* of the prompt, not its *policy*. If a domain rule looks wrong, flag it in the change log instead of silently changing it.

### 5. Verify and deliver

Run a three-pass check on the result:

1. **Adversarial** — walk 2–3 hostile or edge inputs (ambiguous, out-of-scope, injection-shaped) through the prompt mentally: is the behavior defined?
2. **Compression** — for each line ask "would removing this cause a mistake on a strong model?" If no, cut it.
3. **Literal reading** — golden rule: would a competent colleague with minimal context know exactly what to do? A line that could be misread will be.

Deliver: (a) the full prompt, (b) the change log grouped by Cut / Rewrite / Add / Restructure (for the create path: a short design-decision log — architecture chosen and why, what was deliberately left out), (c) 2–3 concrete test inputs — for new prompts, the intake examples are the first tests.

## Core principles (apply always)

1. **Minimal set that fully specifies behavior.** Every token competes for attention ("context rot"). Start from the smallest prompt that could work on a strong model; add only in response to observed failures. For every existing line ask: "would removing this cause a mistake?"
2. **Right altitude.** Between brittle hardcoded if-else logic and vague platitudes sits the sweet spot: strong heuristics the model can generalize from. "If X, do Y" trigger–response pairs beat general dispositions; concrete beats abstract; but heuristics beat exhaustive case enumeration.
3. **Explain the why.** Models generalize from motivation. "Never use ellipses because the output is read by a text-to-speech engine" outperforms "NEVER use ellipses" — and covers cases you didn't enumerate.
4. **Positive over negative.** Say what to do, not what to avoid: "Respond in flowing prose paragraphs" beats "Do not use markdown."
5. **Calm over caps.** On modern instruction-following models, "Use this tool when…" works; "CRITICAL: You MUST…" causes overtriggering (documented for Claude 4+; Gemini 3 similarly over-analyzes persuasive language). Reserve emphasis (IMPORTANT) for the one or two rules that truly are critical. Frequent ALL-CAPS/MUST is a yellow flag that the why is missing.
6. **Be explicit about desired behavior.** Newer models do exactly what's asked, no more: "suggest changes" gets suggestions, not edits. Ask explicitly for above-and-beyond behavior when wanted ("Go beyond the basics; include as many relevant features as possible").
7. **Structure with tags/headers.** Separate instructions, context, data, and examples into clearly named sections, consistently — the delimiter style (XML vs Markdown) and instruction placement follow the target provider's file. Long documents (20k+ tokens) go at the top; the query at the end.
8. **Few, canonical examples.** 3–5 diverse, realistic examples wrapped in `<example>` tags beat a laundry list of edge cases. Examples teach patterns, including reasoning style.
9. **Give the model a check it can run.** For agentic prompts: a verification step, success criteria, or self-check ("Before finishing, verify your answer against …") — and require evidence, not claims.
10. **Iterate empirically.** The loop is: baseline on real tasks → identify gaps → minimal change → re-run → refine from observed behavior, not assumptions. Never declare a prompt "optimized" or "done" without at least proposing how to test it.

## Scope notes

- **Language**: keep the produced prompt in the language its model will consume (for rewrites, the language it was written in), unless the user asks otherwise; write the change log and all communication in the user's language.
- **Provider conflicts**: where a provider file contradicts the general references (e.g., Gemini wants instructions after the data; OpenAI wants them duplicated top and bottom; DeepSeek R1 forbids system prompts and few-shot), the provider file wins for that target. Official vendor guidance fetched via the research step that is newer than the snapshot date wins over the provider file — and is a signal to update it per MAINTENANCE.md.
- For a provider not covered by any provider file and unreachable via research: apply the general references, state that no provider-specific guidance was available, and recommend checking that vendor's official prompting docs.
- **Updating this skill itself** (refreshing provider guidance, adding a provider, fixing stale advice): follow [MAINTENANCE.md](MAINTENANCE.md) — not needed for normal use.
- If asked to build or optimize a prompt whose *content* is the problem (wrong requirements, unclear product intent), say that prompt engineering can't fix an unspecified task — help specify it first (the intake questions in prompt-generation.md §1 are the tool for that).
