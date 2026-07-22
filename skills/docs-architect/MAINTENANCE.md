# Maintaining docs-engineer

How to update this skill. This file is for maintainers (human or agent) — it is never loaded when the skill triggers, so length here is free. When asked to "update the docs-engineer skill" or "refresh the spec-kit guidance", follow this file.

## Contents
1. Source registry (what fed each file)
2. When to update
3. Update workflow
4. Structural invariants (do not break)
5. Testing after any change
6. Changelog

## 1. Source registry

| File | Sources |
|------|---------|
| `references/speckit.md` | github.com/github/spec-kit README + CHANGELOG + releases; github.github.io/spec-kit (quickstart, reference/overview, reference/integrations); community criticism from spec-kit discussions #1784 / issue #2673; martinfowler.com "Understanding SDD: Kiro, spec-kit, and Tessl" (Böckeler) |
| `references/spec-authoring.md` | Adapted from timezlab/specdeck skills `spec-driven` + `docs-as-code/references/plans-and-tasks.md`; committable-unit rule and banned phrasings validated against those skills' benchmark notes |
| `references/docs-structure.md` | diataxis.fr (+ its GitHub source repo); Google docguide (google.github.io/styleguide/docguide: README/best_practices/READMEs/philosophy) + SWE-at-Google ch.10 (abseil.io); Spotify Backstage TechDocs (backstage.io); GitLab docs guidelines + CTRT topic types (docs.gitlab.com/development/documentation); Mintlify "Structured docs coding agents" benchmark + "State of agent traffic" (mintlify.com/blog) |
| `references/agents-md.md` | agents.md spec; developers.openai.com/codex/guides/agents-md (32 KiB `project_doc_max_bytes` limit); code.claude.com/docs/en/memory (Claude Code reads CLAUDE.md not AGENTS.md; `@AGENTS.md` import is the official recommendation, depth ≤4); geminicli.com/docs (memport import processor, `context.fileName` setting); cursor.com/docs/rules, code.visualstudio.com custom-instructions (`chat.useAgentsMdFile` default on), docs.devin.ai (Windsurf), zed.dev/docs/ai/rules (first-match-wins), docs.cline.bot, aider.chat conventions; humanlayer.dev "Writing a good CLAUDE.md"; aihero.dev "Complete Guide to AGENTS.md"; adapted from specdeck `docs-as-code/references/agents-md.md` |
| `references/adr.md` | Nygard "Documenting Architecture Decisions" (cognitect.com); adr.github.io + MADR; AWS Prescriptive Guidance ADR process; Microsoft Azure Well-Architected ADR guidance; template adapted from specdeck `docs-as-code/references/design-doc.md` |
| `references/agent-readable.md` | Adapted from specdeck `docs-as-code/references/agent-readable.md`; llmstxt.org (status: weak as crawler standard, useful as explicit agent-facing index); anthropic.com/engineering "Effective context engineering for AI agents" |
| `references/freshness.md` | Adapted from specdeck `docs-as-code/references/freshness-refactor.md`; graduation ritual derived from the ephemeral-spec/durable-doc split (Böckeler/martinfowler.com; Kiro steering-vs-specs; spec-kit constitution-vs-specs) |

Content snapshot date: **2026-07-22**, Spec Kit **v0.13.4**. The spec-kit material rots fastest (weekly releases; the CLI/commands/paths in `speckit.md` §2–4 are the most likely stale content). `specify --help` is always the runtime truth.

## 2. When to update

- Spec Kit ships a breaking change: renamed commands, changed init flags, moved directories (watch: `--integration` flag, `specs/` at root, `.claude/skills/` install target, the `/speckit.*` command list).
- A platform changes hot-file mechanics: AGENTS.md spec revision, Codex size limit, Claude Code `@import` behavior, Gemini `contextFileName`.
- Real-world use shows the skill giving stale advice — treat the failure as an eval case (§5).
- The docs tree recommendation conflicts with what a major adopted framework now recommends (Diátaxis, MADR).

Don't update because time passed — update when a source changed or a failure was observed.

## 3. Update workflow

1. **Scope**: usually one file (`speckit.md` for tool drift; `agents-md.md` for platform drift).
2. **Re-research with subagents** (read-only, official sources from §1 first). For spec-kit: fetch the live README + CHANGELOG and diff against `speckit.md` §2–4.
3. **Edit, don't append**: fold changes into existing sections; never leave stale commands alongside new ones. Renamed commands get a one-line "(formerly X)" note for one cycle, then drop it.
4. **Update the snapshot date + version** in §1 here and the snapshot line in `speckit.md`, add a Changelog entry in §6.
5. Run §5.

## 4. Structural invariants (do not break)

- SKILL.md body < 500 lines (currently ~115); references one level deep; reference files > 100 lines carry a table of contents.
- All when-to-use information lives in the frontmatter `description`, none in the body.
- The two-lifecycle framing (specs ephemeral / docs durable) is the skill's spine — every reference assumes it. Changing it means rewriting the skill, not patching a file.
- The canonical tree stays consistent across SKILL.md, `docs-structure.md`, and `freshness.md` grep paths: `specs/` at root, `docs/decisions/` (MADR numbering), `docs/reference/` (singular), `docs/tech-debt.md`. A path change must update all three files plus the routing tables.
- AGENTS.md is canonical; CLAUDE.md/GEMINI.md are mirrors (symlink or `@import`) — never document them as independent files.
- Route guidance stays "load one or two references at a time"; no reference may require reading another reference to be usable.
- The when-NOT-to-use-spec-kit gate (≥3 tasks / >2 days) stays prominent in both SKILL.md and `speckit.md` — removing it recreates the tool's #1 failure mode.

## 5. Testing after any change

Spawn fresh-context subagents ("Read the skill at <path>/SKILL.md and follow it exactly. Task: <case>", plus a request for meta-feedback on routing clarity and reference pointers). Minimum cases:

1. **Bootstrap**: "Set up spec-driven development and a docs structure for this empty Node/TypeScript repo." — Check: installs/describes spec-kit with current commands, scaffolds only the minimum tree (no empty dirs), writes a ≤150-line AGENTS.md as a routing table.
2. **Routing**: "Where should I document that we chose SQLite over Postgres for local-first storage?" — Check: routes to `docs/decisions/NNNN-*.md`, applies the Better/Worse/Must-now-be-true template, does not read unrelated references. (Don't test with the Postgres-for-sessions scenario — it's the template's own worked example, so it measures parroting, not guidance.)
3. **Small-task gate**: "Create a spec for fixing this typo in the README." — Check: declines the spec-kit flow, says so explicitly.

For description/trigger changes, run the skill-creator description-optimization loop (`~/.claude/skills/skill-creator/`).

## 6. Changelog

- **2026-07-22** — Same day: per-tool verification of AGENTS.md mirroring (official docs, all 9 major tools). Corrections folded into `agents-md.md` §7: Claude Code does NOT read AGENTS.md natively (earlier draft claimed it did); single recommended mirror strategy is now the one-line import (`CLAUDE.md` = `@AGENTS.md`, `GEMINI.md` = `@./AGENTS.md` or `context.fileName` setting) — symlink option dropped due to the Windows `core.symlinks` silent-failure mode; added Zed first-match-wins and Aider `read:` gotchas.
- **2026-07-22** — Same day: three fresh-context sanity tests (bootstrap, ADR routing, small-task gate) all produced correct outcomes; folded in their meta-feedback — Bootstrap route now lists its full per-sub-task reading sequence, Spec route gates before loading §Workflow, user-override rule for below-gate spec requests, install-vs-init disambiguation, bootstrap ends at constitution, README.md + greenfield notes in the minimum scaffold, ADR numbering seed + index.md step + Deciders guidance.
- **2026-07-22** — Created. Integrates GitHub Spec Kit setup/workflow with a docs-as-code tree, adapted from timezlab/specdeck's `docs-as-code` + `spec-driven` skills and updated with fresh research: spec-kit v0.13.x realities (PyPI `specify-cli`, `--integration` flag, `specs/` at repo root, skills-based Claude Code integration, `/speckit.converge`), `docs/decisions/` per MADR (was `design-docs/`), Diátaxis-aligned `guides/reference/concepts/product` split, AGENTS.md platform limits (Codex 32 KiB, `@import` mirrors), and a new spec-graduation ritual formalizing the ephemeral-spec → durable-doc handoff.
