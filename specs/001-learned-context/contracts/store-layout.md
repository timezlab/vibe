# Contract: Store layout, resolution, exclusion, backup

## Layout

```text
<main-checkout>/.vibe/learned/
├── session-data/
│   └── <YYYY-MM-DD>-<session-id>.md      # last 10 kept (research.md D9)
└── instincts/
    ├── pending/<id>.md                    # extraction output; 30-day TTL prune
    ├── approved/<id>.md                   # THE ONLY DIRECTORY THE LOADER READS
    ├── rejected/<id>.md                   # archive; dedup input; never pruned
    └── retired/<id>.md                    # graduated; provenance kept; never pruned
```

`.vibe/` is a shared namespace — this feature owns only `.vibe/learned/`
and must not touch sibling entries (e.g. future `.vibe/worktrees/`).
Constitution IV: create/delete only inside `.vibe/learned/` and the backup
namespace below.

## Resolution algorithm (all consumers)

```text
1. d = `git rev-parse --git-common-dir` (run in session cwd)
   - success → main = parent directory of d → store = main/.vibe/learned/
   - failure (not a git repo / no git) → store = cwd/.vibe/learned/
     and emit one notice line "learned store: non-git fallback at <path>"
2. Never resolve relative to a worktree root (`--show-toplevel` is
   forbidden in this codepath — it re-creates per-worktree fragmentation).
```

Store directories are created on first write (`mkdir -p` semantics), never
on read: a read against a missing store returns "empty" silently (US1
scenario 5).

## Git exclusion (research.md D5)

Before every write, ensure `$(git rev-parse --git-common-dir)/info/exclude`
contains a line `.vibe/` (exact match); append it if absent (add-only,
idempotent). Non-git fallback skips this step. The shared `.gitignore` is
never modified by this system.

## Prune pass (FR-009, D9)

Runs at the start of every capture (SessionEnd), before new writes:

- delete files in `instincts/pending/` with `created` older than 30 days;
- delete all but the newest 10 files in `session-data/`;
- touch nothing in `approved/`, `rejected/`, `retired/`;
- report what was pruned in hook stderr (visible, not silent).

## Backup (research.md D7)

- Trigger: every approval and retirement event (write-event driven).
- Target: `${XDG_DATA_HOME:-~/.local/share}/vibe/backup/<project-id>/`
  mirroring `instincts/approved/` and `instincts/retired/`.
  Windows: `%LOCALAPPDATA%\vibe\backup\<project-id>\` (documented only).
- `project-id`: first 12 hex chars of SHA-256 of the normalized first git
  remote URL (`git remote get-url origin`, lowercased, trailing `.git`
  stripped); fallback: same hash of the main-checkout absolute path.
- Mirror is copy-on-event (overwrite same-id file); deletions in the store
  do NOT propagate — the backup is append-favoring by design (recovery
  beats symmetry). A `restore` is a manual copy back, documented in the
  hook pack README.

## Concurrency

All writes atomic (tmp + rename). Filenames embed unique ids (instinct id,
session id) so parallel session ends touch disjoint files; the prune pass
tolerates concurrently-vanishing files (ENOENT is not an error).
