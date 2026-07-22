# VIBE Documentation Foundation Design

**Status:** approved
**Date:** 2026-07-22
**Language:** English is canonical

## Purpose

Establish the documentation and Spec Kit foundation for VIBE while the product is pre-alpha. The result must serve two audiences without duplicating facts:

- Humans discover the project through `README.md` and contributor guidance.
- Maintainers and coding agents navigate technical knowledge through short root entry points and durable documents under `docs/`.

This setup is below the Spec Kit size gate. It does not create a numbered feature spec. The first qualifying product feature retains `001`.

## Scope

- Rewrite stale repository entry points around VIBE rather than `timezlab/skills`.
- Turn the accepted content in `DECISIONS.md` into product documents and append-only ADRs.
- Add concise architecture and agent-routing entry points.
- Install the latest stable Spec Kit CLI and initialize its Claude integration.
- Seed a project-specific constitution with rules that apply across qualifying features.
- Define verification and freshness conditions for the documentation system.

## Non-goals

- Do not implement the `vibe` CLI, local web application, adapters, memory system, or worktree orchestration.
- Do not present planned commands as available.
- Do not decide the Phase 2 HTTP framework or the long-term harness distribution channel.
- Do not create empty `guides/`, `reference/`, or `concepts/` directories.
- Do not create a Spec Kit feature folder for this documentation setup.

## Information Architecture

The repository uses a lifecycle-first documentation model:

```text
README.md
CONTRIBUTING.md
AGENTS.md
CLAUDE.md
ARCHITECTURE.md
DECISIONS.md

.specify/

docs/
├── index.md
├── product/
│   ├── DESIGN.md
│   ├── roadmap.md
│   └── harness-foundation.md
├── decisions/
│   ├── 0001-build-vibe-as-a-local-web-app.md
│   ├── 0002-use-repository-local-git-worktrees.md
│   ├── 0003-use-reviewed-file-based-memory.md
│   ├── 0004-compile-canonical-content-through-adapters.md
│   └── 0005-use-a-claude-compatible-plugin-layout.md
├── superpowers/
│   └── specs/
│       └── 2026-07-22-docs-foundation-design.md
└── tech-debt.md
```

`specs/` is not created until the first feature passes the Spec Kit gate. Spec Kit may own engine files under `.specify/`; generated Claude integration files live under `.claude/skills/` according to the installed stable version.

## Source-of-Truth Rules

- `README.md` is the human entry point, not the complete documentation set.
- `AGENTS.md` is the canonical agent entry point and remains below 150 lines.
- `CLAUDE.md` contains only `@AGENTS.md` so Claude receives the same instructions without a copied mirror.
- `ARCHITECTURE.md` answers where responsibilities belong and which dependency directions are allowed.
- `docs/product/` owns product intent, scope, status, and roadmap.
- `docs/decisions/` owns accepted technical rationale and is append-only.
- `.specify/memory/constitution.md` owns standing rules inherited by qualifying features.
- `specs/NNN-*/` contains execution-time artifacts that become historical when work ships.
- Generated platform targets are build artifacts; canonical harness content is edited at its source.
- Links replace duplicated explanations.

## Migration from DECISIONS.md

| Existing subject | Canonical destination |
|---|---|
| Name, positioning, problem, and scope | `docs/product/DESIGN.md` |
| Four-phase roadmap | `docs/product/roadmap.md` |
| Detailed Phase 1 outcome | `docs/product/harness-foundation.md` |
| Node/TypeScript local web application | ADR 0001 |
| Repository-local Git worktrees | ADR 0002 |
| Human-reviewed file-based memory | ADR 0003 |
| Canonical content compiled through adapters | ADR 0004 |
| Claude-compatible plugin layout | ADR 0005 |
| Undecided HTTP framework and distribution mechanism | Explicit roadmap decision gates |
| Outstanding administrative work | Roadmap checklist rather than technical debt |

After migration, `DECISIONS.md` becomes a short compatibility pointer to the product and ADR indexes. It does not retain a second copy of the decisions.

## Entry-Point Content

### README.md

The README explains what VIBE is, the problem it addresses, its pre-alpha status, current repository contents, high-level roadmap, contribution path, and links into durable docs. It does not include a fake quickstart for commands that have not been implemented.

### CONTRIBUTING.md

Contributor guidance covers current skill validation, future harness contributions, documentation-in-the-same-PR discipline, and the Spec Kit size gate. Commands are included only when they work in the repository.

### AGENTS.md and CLAUDE.md

`AGENTS.md` contains project identity, current stack/status, a small set of critical invariants, real validation commands, the Spec Kit gate, and a routing table. It contains no roadmap narrative or architectural history. `CLAUDE.md` imports it without duplication.

## Architecture Representation

`ARCHITECTURE.md` separates implemented and planned structures:

- Implemented now: installable skills and their validation workflow.
- Planned Phase 1: canonical `rules/`, `agents/`, `commands/`, `hooks/`, `mcp-configs/`, `adapters/`, and supporting scripts.
- Planned later: the CLI and local web application.

The document records known boundaries without prematurely choosing an `apps/` or `packages/` monorepo layout. Its key invariants are:

- Canonical content flows into adapter transforms, then generated platform targets; dependencies never reverse that flow.
- Delivery surfaces use application services rather than accessing PTY, Git, or filesystem implementations directly.
- Memory candidates move from `pending` through explicit human approval to `approved` before loading.

Unknown package paths remain deferred to the relevant feature plan rather than appearing as placeholders.

## Spec Kit Setup

The currently installed CLI is a development build (`0.10.3.dev0`). Replace it with the latest stable release. On 2026-07-22, the authoritative PyPI release is `0.13.0`.

Setup sequence:

1. Inspect how the existing executable was installed.
2. Upgrade through the official stable path and verify `specify --version`.
3. Read the installed version's `specify init --help` before initialization.
4. Initialize the existing repository with the Claude integration.
5. Inspect the resulting diff before adapting generated files.
6. Seed `.specify/memory/constitution.md` with VIBE-specific principles.

The constitution establishes:

- canonical sources and generated targets;
- explicit capability degradation across adapters;
- human approval before learned memory becomes active;
- safe, preview-first repository and filesystem mutations;
- documentation updates in the same change as code;
- verification of observable output before work is declared complete.

No template override is added unless the default stable templates cannot express a VIBE requirement.

## Spec Lifecycle

Use Spec Kit when work has at least three tasks, exceeds roughly two days, changes user-visible behavior or contracts, must outlive one agent session, or has a meaningfully debatable done condition. Skip it for mechanical fixes, small documentation changes, and exploratory spikes.

When a qualifying feature ships:

1. Run the active-spec convergence step supported by the installed version.
2. Graduate durable decisions into ADRs.
3. Graduate project-specific gotchas into reference documents.
4. Move deferred shortcuts into `docs/tech-debt.md`.
5. Update living entry points and architecture in the same change.
6. Mark the feature spec done without rewriting its historical body.

## Failure Handling

- Preserve all pre-existing user files and unrelated changes.
- Do not force initialization through a collision.
- If Spec Kit output differs from the skill snapshot, follow the installed stable CLI and official documentation.
- Inspect generated changes immediately; remove only artifacts proven obsolete or outside the selected integration.
- Treat code as authoritative when code and living docs diverge, then fix the docs in the same change.
- Reverse an accepted ADR only with a new ADR and bidirectional supersession links.

## Acceptance Criteria

- `specify --version` reports stable `0.13.0`.
- Spec Kit initializes successfully for Claude and the constitution has no placeholder text.
- No active feature spec or `001` folder exists.
- `AGENTS.md` is no more than 150 lines and `CLAUDE.md` contains only its import.
- Every document under `docs/` is linked from `docs/index.md`.
- No empty documentation category directory exists.
- Every internal Markdown link resolves to an existing target.
- Stale project and skill names remain only in an intentional migration note, if needed.
- All three current skills pass the repository's `agentskills validate` workflow.
- Every command documented in README or CONTRIBUTING works in the current repository or is explicitly labeled planned.
- `git diff --check` reports no whitespace errors.
