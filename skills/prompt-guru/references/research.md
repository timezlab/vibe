# Research Step

When the bundled references can't answer, fetch official sources — don't pad the prompt from memory or third-party blogs. Prompt-engineering guidance rots fast (sampling defaults, deprecated params, new model families), and domain constants invented from memory produce confidently wrong agents.

## Contents
1. When to research — and when not
2. Official source registry
3. How to run it
4. Recording results

## 1. When to research — and when not

Content snapshot date of the bundled references: **2026-07-22** (this line is the runtime copy; MAINTENANCE.md mirrors it for maintainers — update both together).

Research when ANY of these holds:

- **Provider gap or staleness** — the target model family is missing from the `provider-*.md` files, or newer than the snapshot date above. Fetch that vendor's official prompting guide, prioritizing its migration / what's-new page.
- **Domain constants needed** — the prompt must embed facts the user or codebase didn't supply: API schemas, product rules, regulatory text, scoring rubrics. Get them from the authoritative source or ask the user; a gap flagged honestly beats an invented constant.
- **Exemplars for high-stakes artifacts** — Anthropic publishes its production system prompts (release notes below); this repo's own skills are exemplars for SKILL.md work. Reading one strong exemplar beats reasoning from principles alone.

Skip research when the provider is covered, the snapshot is fresh, and the task is fully specified — research answers *specific questions you can name*; it is not a ritual. Timebox to a handful of fetches per job.

## 2. Official source registry

Official vendor documentation only. Blogs, Reddit, and social posts are fine as *leads*, never as ground truth for guidance.

| Provider / topic | Official sources |
|---|---|
| Anthropic Claude | platform.claude.com/docs — "Prompting best practices", prompt-engineering overview, "Define success criteria" (test-and-evaluate/develop-tests); anthropic.com/engineering blog; published system prompts: platform.claude.com/docs/en/release-notes/system-prompts |
| Agent Skills | platform.claude.com/docs Agent Skills best-practices; anthropic.com/engineering "Equipping agents for the real world with Agent Skills" |
| OpenAI | developers.openai.com prompting guides (per model family; cookbook.openai.com redirects there); platform.openai.com/docs guides: prompt-engineering, reasoning-best-practices; OpenAI Model Spec |
| Google Gemini | ai.google.dev/gemini-api/docs: prompting-strategies, model developer guides, thinking, long-context; cloud.google.com Vertex AI prompt-design-strategies |
| Meta Llama | llama.com prompt-format and model docs |
| Mistral | docs.mistral.ai (prompting capabilities) |
| Qwen | huggingface.co/Qwen model cards (usage/best-practice sections) |
| DeepSeek | api-docs.deepseek.com; R1 usage recommendations |
| xAI Grok | docs.x.ai (prompt-engineering, reasoning guides) |

## 3. How to run it

1. **Name the questions first** — "what changed in GPT-6 prompting vs GPT-5.x", "what params does Gemini 4 deprecate", "what is the exact response schema of the Stripe refund endpoint". If you can't phrase the question, you don't need research yet.
2. **Locate, then fetch** — search to find the official page, fetch it, and read what answers the named questions. Prefer vendor migration/what's-new pages: they list exactly the deltas that make bundled guidance stale.
3. **Diff against the loaded reference** — fetched official guidance that is *newer* than the snapshot date wins over the provider file for this job.
4. **Feed it back** — if research surfaced a genuinely new or changed technique, suggest updating the affected reference per MAINTENANCE.md so the next run doesn't need the same fetch.

## 4. Recording results

In the change log / design-decision log, cite each fetched source (URL + what it decided) and mark which guidance came from research versus the bundled references. This lets the user audit the advice and lets a maintainer see exactly which reference file has drifted.
