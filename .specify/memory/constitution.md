# VIBE Constitution

VIBE (Vibe Integrated Build Environment) combines canonical harness content, a
local multi-agent workspace, and human-governed learning. These principles bind
every qualifying feature spec, plan, and implementation in this repository.

## Core Principles

### I. Canonical Sources, Generated Targets

Harness content (skills, rules, agents, commands, hooks) is edited once, at its
canonical source in this repository. Platform-specific outputs are build
artifacts produced by adapters: they carry a generated-file warning header and
are never hand-maintained. When a generated target and its canonical source
diverge, the source is the truth and the target is regenerated — never patched
in place.

### II. Explicit Capability Degradation

Every adapter declares the capabilities its platform supports and does not
support (hooks, skills, memory, commands). Unsupported behavior degrades
visibly — surfaced to the user in the UI or sync output — rather than silently
dropped. No adapter may pretend a capability exists by emitting a no-op.

### III. Human-Approved Learning

Session-derived instincts are written as `pending` candidates with confidence
and evidence attached. They remain inactive until a person explicitly approves
them; only `approved` instincts load into future sessions. Fully automatic
learning loops are out of scope by decision, not omission.

### IV. Safe Repository Mutation

Merge-sensitive configuration changes (e.g. shared global config files) are
add-only and preview-first (`--dry-run` before write). Worktree and filesystem
operations resolve their explicit, registered target before mutating or
removing anything. No operation deletes or overwrites a path it did not create
or register.

### V. Documentation Ships with Code

Public surfaces, module boundaries, accepted decisions, and known debt update
in the same change as the implementation that alters them. "Clean up docs
later" is not an accepted state; a change that invalidates a document without
fixing it is incomplete.

### VI. Observable Verification

A completion claim names the command or observable check that proves the
outcome, and that check has been run. "Should work" is not done; done is a
passing command, a resolving link, or a visible behavior.

## Documentation Governance

- Accepted ADRs under `docs/decisions/` are append-only: a reversed decision
  gets a new ADR with bidirectional supersession links, never an edit to
  history.
- Spec Kit is used only above the size gate (roughly: three or more tasks, more
  than two days, changed user-visible behavior or contracts, or a debatable
  done condition). Below the gate, make the change directly.
- When a qualifying feature ships, its spec graduates: durable decisions become
  ADRs, project-specific gotchas become reference docs, deferred shortcuts move
  to `docs/tech-debt.md`, and living entry points update in the same change.

## Governance

This constitution supersedes ad-hoc practice for all qualifying features.
Amendments are made by commit with a dated rationale in the commit message and
a version bump below. Reviews of specs, plans, and implementations verify
compliance with the six principles before acceptance.

**Version**: 1.0.0 | **Ratified**: 2026-07-22 | **Last Amended**: 2026-07-22
