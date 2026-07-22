# Use repository-local Git worktrees for parallel panes

**Status:** accepted
**Date:** 2026-07-22
**Deciders:** Liam Lee

## Context

Each workspace pane may run an agent on its own branch of the same
repository. Git does not allow two branches checked out simultaneously in one
working directory, so parallel sessions need isolated checkouts, and their
location determines editor integration, discoverability, and cleanup safety.

## Decision

Each pane can create a **Git worktree inside the host repository**, grouped
under a single state directory:

```
myrepo/
├── .vibe/
│   ├── worktrees/<branch>/   # one worktree per pane
│   ├── layouts/              # saved layout templates
│   └── sessions/             # project session summaries
└── .gitignore                # app appends "/.vibe/"
```

The app owns the lifecycle: appending the `.gitignore` entry, adding VS Code
search excludes (to prevent duplicated search results), creating/diffing/
merging/cleaning worktrees (`git worktree add/remove/prune`), and an "Open in
editor" action per pane.

## Alternatives considered

- **Multiple branches in one working tree** — rejected: Git forbids it; the
  workarounds (stash juggling, index tricks) corrupt agent sessions.
- **External worktree location (e.g. `~/.vibe/worktrees/`)** — rejected:
  breaks relative paths and editor context, and orphans state when the repo
  moves. Would revisit if in-repo worktrees measurably confuse tools that
  ignore `.gitignore`.
- **Container/overlayfs isolation per pane** — deferred, not rejected: noted
  as a future Linux option for stronger isolation.

## Consequences

**Better:**

- True parallel branch sessions with standard Git tooling — no custom VCS
  layer.
- All VIBE state per project lives in one discoverable place (`.vibe/`).

**Worse:**

- Worktrees inside the repo require active hygiene (gitignore, search
  excludes) or they pollute search and status output.
- Disk usage grows with one full checkout per active pane.

**Must now be true:**

- The app adds `/.vibe/` to `.gitignore` and editor search excludes before
  creating the first worktree.
- Cleanup resolves a specific registered worktree (from `.vibe/` state) before
  removal — never pattern-deletes directories.

## Revisit if

Worktree-in-repo causes recurring tool conflicts in practice, or pane
isolation needs grow beyond what worktrees provide (trigger for the
overlayfs/container option).
