---
name: docs-architect
description: Sets up and runs a repo's spec + documentation system end-to-end — installs and configures GitHub Spec Kit (specify CLI), guides writing specs/plans/tasks for features, scaffolds the docs/ tree (ADRs in docs/decisions, guides, reference, product specs), writes and audits AGENTS.md/CLAUDE.md/ARCHITECTURE.md, and keeps docs fresh after refactors. Use whenever the user wants to set up spec-kit or spec-driven development, create a spec for a feature, set up docs or a documentation structure for a project, asks where to document something, records an architectural decision (ADR), captures tech debt, complains that docs are stale or drifted from code, or starts a feature with 3+ tasks — even if they only say "setup speckit", "tạo spec", "add docs", or "document this decision".
---

# Docs Engineer

**The repository is the system of record.** If a decision, plan, or constraint lives only in chat or someone's head, it doesn't exist for the next agent or teammate.

Two artifact classes, two lifecycles — most documentation failures come from mixing them up:

- **Specs are ephemeral.** One folder per feature (`specs/NNN-<name>/`), created by Spec Kit when work starts, frozen as historical record when it ships. Treating specs as living documentation is how they drift into fiction.
- **Docs are durable.** `docs/` holds decisions (append-only), guides, reference, product direction — updated in the same PR as the code, for the life of the repo. Treating docs as write-once is how they rot.

When a feature ships, valuable knowledge **graduates** from the spec into durable docs (decisions → ADRs, gotchas → reference, debt → tech-debt log). That handoff is this skill's core loop.

## Target layout

```
repo/
├── README.md                  # human entry point: what/why, quickstart, links into docs/
├── AGENTS.md                  # agent entry point: ≤150 lines, routing table (CLAUDE.md mirrors/symlinks it)
├── ARCHITECTURE.md            # module map + dependency direction — one page
├── .specify/                  # Spec Kit engine: memory/constitution.md, templates/, scripts/
├── specs/NNN-<feature>/       # spec.md + plan.md + tasks.md — ephemeral, one folder per feature
└── docs/
    ├── index.md               # map of the docs — navigation only, no content
    ├── decisions/             # ADRs: NNNN-<topic>.md — append-only, superseded not edited
    ├── product/               # product specs, DESIGN.md — direction, goals, non-goals
    ├── guides/                # how-to: setup, deploy, debug, release
    ├── reference/             # dry facts: how THIS project uses each lib, config, schemas
    ├── concepts/              # explanation: domain concepts, background
    └── tech-debt.md           # single flat grep-able debt log
```

Only create directories you populate now — an empty `docs/concepts/` is noise. Rationale for this shape (Diátaxis × context tiers × lifecycle): `references/docs-structure.md`.

Every doc serves one **context tier**. Hot docs crowd out the task, so they must earn every line:

| Tier | Loads | Budget | Examples |
|------|-------|--------|----------|
| **Hot** | Every session | ≤150 lines total | `AGENTS.md` / `CLAUDE.md` |
| **Warm** | Per task | Thorough | active `specs/NNN-*/`, `ARCHITECTURE.md` |
| **Cold** | On demand via routing | Thorough, indexed | everything under `docs/` |

## Routes

| Situation | Do | Read first |
|-----------|----|------------|
| Set up spec-kit and/or docs from scratch | **Bootstrap** — four sub-tasks in order: install Spec Kit → scaffold the minimum docs tree → write AGENTS.md → capture the first ADR | Per sub-task, as you reach it: `references/speckit.md` §Setup → `references/docs-structure.md` §Minimum scaffold → `references/agents-md.md` → `references/adr.md` |
| Start a feature / create a spec | **Spec**: check the size gate first — below it (under ~3 tasks / 2 days), just make the change, no spec, and say so; if the user still wants one, state the gate and let them decide | `references/speckit.md` §When-to-use (the gate), then §Workflow + `references/spec-authoring.md` only if the gate passes |
| "Where do I document X?" | **Route**: use the table below, then the matching reference | table below |
| Write or audit AGENTS.md / CLAUDE.md | **Hot-doc discipline** | `references/agents-md.md` |
| A refactor happened / docs feel stale | **Freshness sweep** | `references/freshness.md` |
| A feature just shipped | **Graduate the spec**: distill decisions into ADRs, mark spec done in place | `references/freshness.md` §Graduation |

Load references per sub-task as you reach them — one or two in context at a time, never all up front.

## Where does X get written?

| What you have | Doc type | Location | Read |
|---------------|----------|----------|------|
| Feature about to start (≥3 tasks or >2 days) | Spec Kit feature | `specs/NNN-<name>/` | `references/spec-authoring.md` |
| Why a technical decision was made | ADR | `docs/decisions/NNNN-<topic>.md` | `references/adr.md` |
| Product intent, goals, non-goals | Product spec | `docs/product/<feature>.md` | `references/adr.md` §Product specs |
| Known debt, quirk, workaround | Debt entry | `docs/tech-debt.md` | `references/spec-authoring.md` §Tech debt |
| How to use a library in this project | Reference | `docs/reference/<lib>.md` | `references/agent-readable.md` |
| Operational how-to (deploy, debug, release) | Guide | `docs/guides/<task>.md` | `references/docs-structure.md` |
| Module map, dependency direction | Architecture | `ARCHITECTURE.md` | `references/docs-structure.md` |
| Standing principles for all features | Constitution | `.specify/memory/constitution.md` | `references/speckit.md` |

When in doubt: write an ADR. Decisions are the highest-value capture — code shows *what*, git shows *when*, only docs show *why*.

## Non-negotiables

These are the convergent practice of Google (g3doc), GitLab, and Spotify (TechDocs) — and they matter more for agents than for humans, because agents trust docs literally:

1. **Docs change in the same PR as the code.** "Clean up docs later" means never; a stale doc poisons every future agent session that loads it.
2. **Trust the code, fix the doc.** On any code/doc divergence, the code is the truth and the doc is the bug.
3. **Link, don't duplicate.** Two copies of a fact means one is wrong within months — single source of truth, always.
4. **Never scaffold empty structure.** Grow the tree when real content exists (Diátaxis's own warning: don't impose the taxonomy top-down).
5. **Write for the agent reader.** Name files/symbols not concepts, symptom→cause→fix tables, observable done conditions — see `references/agent-readable.md`.

## Reference index

- **`references/speckit.md`** — install/init Spec Kit, what it scaffolds, the command workflow (`/speckit.specify` → … → `/speckit.converge`), when NOT to use it, Claude Code–specific practices
- **`references/spec-authoring.md`** — what a good spec/plan/tasks looks like: executable-spec checklist, committable-unit task rule, banned phrasings, tech-debt entry format, status lifecycle
- **`references/docs-structure.md`** — the full docs tree with rationale, minimum scaffold, ARCHITECTURE.md conventions, naming
- **`references/agents-md.md`** — AGENTS.md/CLAUDE.md discipline: 150-line target, routing-table pattern, hard platform limits, audit procedure
- **`references/adr.md`** — ADR template (Better/Worse/Must-now-be-true), rejected alternatives, status lifecycle, product spec template
- **`references/agent-readable.md`** — concrete-over-abstract, symptom→cause→fix, library reference files, progressive disclosure
- **`references/freshness.md`** — divergence triggers, grep-driven post-refactor sweep, spec graduation ritual

Spec Kit ships new releases weekly — if its commands or paths look different from `references/speckit.md`, trust `specify --help` and see `MAINTENANCE.md`.
