# Use a Claude-compatible plugin layout while distribution stays open

**Status:** accepted
**Date:** 2026-07-22
**Deciders:** Liam Lee

## Context

How VIBE's harness content reaches users is undecided: Claude Code plugin,
`npx skills` CLI, a dedicated installer, or a hybrid. Choosing an installer
now would be a guess; choosing a directory layout cannot wait, because content
is being written today.

## Decision

Organize harness content in this repository following the **Claude Code
plugin directory standard**, so that all three distribution paths remain
compatible — picking one later means "adding files", not restructuring.
The distribution decision itself is deferred to the
[roadmap gate](../product/roadmap.md#open-decision-gates), to be made with
Phase 1 evidence.

Known constraint accepted now: Claude Code plugins cannot distribute
`rules/` — whichever path wins, a script must copy rules into
`~/.claude/rules/`.

## Alternatives considered

- **Pick a single installer now** — rejected: no usage evidence yet; a wrong
  guess costs a migration for every early adopter.
- **Maintain layouts for every possible channel** — rejected: N layouts is
  the same drift trap as N hand-maintained platform copies
  ([ADR 0004](0004-compile-canonical-content-through-adapters.md)).

## Consequences

**Better:**

- Content work proceeds today without betting on a distribution channel.
- Plugin compatibility is the strictest layout constraint; satisfying it keeps
  the other channels free.

**Worse:**

- The plugin standard constrains naming/structure even if the plugin path is
  never chosen.
- The `rules/` gap means every distribution path needs a supplementary copy
  script.

**Must now be true:**

- New harness content directories follow the Claude Code plugin structure.
- No distribution-specific files (marketplace manifests, installers) are added
  before the gate is resolved.

## Revisit if

Phase 1 ships and real installation feedback exists — this ADR **must** be
revisited when the distribution gate is resolved; its successor records the
chosen channel.
