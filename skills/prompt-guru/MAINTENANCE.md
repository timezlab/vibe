# Maintaining prompt-engineer

How to update this skill. This file is for maintainers (human or agent) — it is never loaded when the skill triggers, so length here is free. When asked to "update the prompt-engineer skill", "refresh provider guidance", or "add provider X", follow this file.

## Contents
1. Source registry (what fed each file)
2. When to update
3. Update workflow (refresh existing content)
4. Adding a new provider
5. Structural invariants (do not break)
6. Testing after any change
7. Changelog

## 1. Source registry

Each reference file distills these official sources. Re-fetch them (not third-party blogs) when refreshing:

| File | Sources |
|------|---------|
| `references/prompting-techniques.md` | platform.claude.com/docs "Prompting best practices" (all old prompt-engineering sub-pages redirect there); anthropic.com/engineering "Writing effective tools for agents" |
| `references/system-prompts.md` | anthropic.com/engineering: "Effective context engineering for AI agents", "Building effective agents", "Claude Code: Best practices for agentic coding", "How we built our multi-agent research system"; Anthropic published system-prompt release notes (docs.anthropic.com/en/release-notes/system-prompts) |
| `references/skills-authoring.md` | platform.claude.com/docs Agent Skills best-practices; anthropic.com/engineering "Equipping agents for the real world with Agent Skills" |
| `references/prompt-generation.md` | platform.claude.com/docs prompt-engineering overview (success-criteria-first workflow), "Console prompting tools", test-and-evaluate/develop-tests; claude.com/blog "Best practices for prompt engineering"; developers.openai.com prompt-engineering guide + GPT-4.1/GPT-5.x cookbook skeletons; ai.google.dev prompting-strategies; agent-architecture patterns distilled and modernized from the retired internal `prompt-engineering` skill (timezlab/skills-old) |
| `references/research.md` | Mirrors this registry as a runtime-facing table; update both together |
| `references/provider-claude.md` | platform.claude.com/docs "Prompting best practices" (Claude 4+ sections, deprecations/migrations) |
| `references/provider-openai.md` | developers.openai.com prompting guides (GPT-4.1, GPT-5, 5.1, 5.2, 5.6; cookbook.openai.com redirects there); platform.openai.com/docs guides: prompt-engineering, reasoning-best-practices; OpenAI Model Spec (instruction hierarchy) |
| `references/provider-gemini.md` | ai.google.dev/gemini-api/docs: prompting-strategies, gemini-3 (developer guide), thinking, long-context, system-instructions; cloud.google.com Vertex AI prompt-design-strategies |
| `references/provider-open-models.md` | llama.com prompt-format docs; docs.mistral.ai prompting_capabilities; Qwen model-card best practices (huggingface.co/Qwen); api-docs.deepseek.com + DeepSeek-R1 usage recommendations; docs.x.ai reasoning + prompt-engineering guides |

Content snapshot date: **2026-07-22** — the runtime-facing copy of this date lives in research.md §1; update both together. Anything model-version-specific (deprecated params, sampling defaults, "dead" features) is the most likely content to rot. The runtime research step (research.md) is the pressure valve between refreshes: it lets a job fetch newer official guidance and flags the drift back here.

## 2. When to update

- A provider ships a new major model family (GPT-6, Gemini 4, Claude 6, Llama 5…) or a new official prompting guide.
- A technique in a reference file stops matching reality (e.g., a param deprecated, a documented behavior changed) — verify against the official doc, then fix.
- The research step keeps firing for the same gap — that's the signal a reference file has drifted; fold the fetched guidance in.
- Repeated real-world use shows the skill giving stale or wrong advice — treat the failure as an eval case (see §6).
- A new artifact type keeps coming up that no reference covers (add a reference + a row to SKILL.md's artifact table).

Don't update just because time passed — update when a source changed or a failure was observed.

## 3. Update workflow (refresh existing content)

1. **Scope**: decide which files are affected (usually one provider file per provider change).
2. **Re-research with subagents** (parallel, one per source group), read-only, using this brief shape:
   - Goal: "Extract concrete, actionable prompt-engineering guidance from <official sources> — focus on what changed vs the summary below" (paste the current reference file so the agent diffs against it).
   - Constraints: official vendor sources only; techniques, not marketing.
   - Output contract: "markdown bullets, imperative form, grouped by topic, under 900 words; explicitly list DEPRECATED/CHANGED items vs the pasted summary."
3. **Edit, don't append**: fold changes into the existing section structure. Move dead techniques to a deprecation note with the migration path (see provider-claude.md §6 for the pattern) or delete them; never leave stale advice alongside new advice.
4. **Update the snapshot date** in §1 AND in research.md §1 (the runtime copy), plus the registry table in research.md if sources changed, and add a Changelog line in §7.
5. Run the §6 test.

## 4. Adding a new provider

1. Research that vendor's **official** prompting docs (same brief shape as §3.2; if no official guide exists, say so in the file rather than substituting blog content).
2. Create `references/provider-<name>.md` following the shared template:
   - Title: `# Provider: <Name>` + one-line "what to do differently" + source list + `## Contents`.
   - Sections ordered: structure/delimiters → instruction placement → reasoning control → examples policy → sampling/API knobs → model-family gotchas → migration checklist (if the vendor documents one).
   - Keep it a **delta** file: only what differs from the general references — no re-explaining universal principles.
3. Register it in **SKILL.md** (provider table + frontmatter `description` — it's the trigger surface), and in the research.md source registry.
4. If the provider introduces a genuinely new universal lesson, promote it to the general references instead of duplicating it per provider.

## 5. Structural invariants (do not break)

- SKILL.md body < 500 lines (currently ~100); references one level deep; every reference file > 100 lines gets a table of contents.
- Reference files load on demand — keep each focused so agents never need more than ~4 files per job (general + artifact + provider, plus prompt-generation.md on the create path).
- All when-to-use information lives in the frontmatter `description`, none in the body.
- Provider files are deltas; general files are provider-neutral. If a general file names a provider, it's either an attributed example ("documented for Claude 4+") or a bug.
- The two-path routing stays in SKILL.md step 0: create (4A → self-review via 4B) vs optimize (4B); the create path always hands its draft back to the diagnose loop.
- Research is conditional (SKILL.md step 2 criteria) — never make it unconditional; official-sources-only rule stays in research.md.
- Conflict order stays: fresh official research > provider file > general references, and the provider file wins over general references for its target.
- Language rule stays: the produced prompt keeps its consumer's language; change log in the user's language.
- The deliverable contract stays: prompt + change log (or design-decision log) + 2–3 test inputs.

## 6. Testing after any change

Minimum sanity test (what was used at creation) — run BOTH paths:

1. **Optimize path**: write a deliberately flawed prompt for the affected area (e.g., for a provider file: a prompt using that provider's known anti-patterns — caps-lock MUSTs for Claude, temperature 0.2 for Gemini 3, few-shot for DeepSeek R1). **Create path**: write a bare task description ("build me an agent that does X with tools A, B") with no prompt text.
2. Spawn a **fresh-context subagent** per case: "Read the skill at <path>/SKILL.md and follow it exactly. Task: <case>." plus an output contract asking for (a) the deliverable and (b) meta-feedback on the skill itself (was the routing clear, were reference pointers right, anything ambiguous/missing).
3. Check: did it route correctly (create vs optimize), read the right reference files, apply/skip the research step per the criteria, catch planted anti-patterns (optimize) or run intake + self-review (create), and produce the 3-part deliverable? Fix real gaps from the meta-feedback; ignore stylistic nitpicks.

For bigger changes, run the full skill-creator eval loop (`~/.claude/skills/skill-creator/`): multiple test prompts, with-skill vs baseline subagents, eval viewer for human review. The description-optimization script there (`scripts/run_loop.py`) is the tool to use if the frontmatter description changes significantly.

## 7. Changelog

- **2026-07-22** — Post-review fix pass (4-subagent evaluation: structural review vs skill-creator criteria, 25-claim online fact-check, with-skill vs baseline functional test). Fixed: frontmatter description trimmed to <1024 chars and rewritten in third person, scoped the "poor output quality" trigger to instruction-caused failures; broken create-path routing-table row repaired; snapshot date given a runtime copy in research.md §1 (SKILL.md step 2 no longer points at this maintainer file); DeepSeek guidance scoped by generation (original R1 vs R1-0528+/V4, hosted thinking mode rejects sampling params, deepseek-chat/reasoner alias sunset 2026-07-24); Llama 4 token set added; Fable 5/Mythos 5 delta added to provider-claude.md (always-on adaptive thinking, xhigh effort, reasoning_extraction refusals, de-prescription warning); GPT-5.6 outcome-first guidance added; Gemini scope refreshed to 3.1; unverified "~40% task-time" figure hedged; provider deltas removed from prompt-generation.md §3; dead cross-ref in system-prompts.md §8 fixed; cookbook→developers.openai.com redirect noted in registry.
- **2026-07-22** — Same day: fresh-research validation pass against live official docs (Anthropic best-practices/develop-tests/prompting-tools/blog; OpenAI prompt-engineering + GPT-4.1/5/5.2 cookbooks; Gemini prompting-strategies). Fixes folded in: examples sweet spot 3–5, length bands labeled as heuristic (no vendor publishes token budgets), skeleton labeled as scaffold (no vendor prescribes a section order), `{{variable}}` fixed-vs-variable separation, cache-aware ordering, contradiction-audit emphasis, uncertainty permission, always-on-thinking caveat, OpenAI XML-constraint-block note.
- **2026-07-22** — Created as **prompt-engineer**, superseding `prompt-optimizer` (removed same day). Unified three capabilities: (1) the full optimize/diagnose loop and all 7 reference files carried over from prompt-optimizer unchanged; (2) a create-from-scratch path (`references/prompt-generation.md`) distilling the retired `prompt-engineering` skill's intake questions, agent architectures, and length calibration — modernized to current guidance (positive phrasing, whys, minimal-first; dropped its stale model-specific advice, OpenAI meta-prompt, and NEVER-list templates); (3) a conditional research step (`references/research.md`) with an official-source registry for provider drift, domain constants, and exemplars.
- *(inherited)* **2026-07-22** — prompt-optimizer created: Anthropic-based core (docs + engineering blog + skills guidance) with 3 general references; same day extended to multi-provider: Claude specifics split out, added provider-openai.md, provider-gemini.md, provider-open-models.md, provider tables and conflict rule in SKILL.md.
