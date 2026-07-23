---
name: evolve
description: Graduate clusters of related approved learned-context instincts into canonical repository assets (skills or rules) with provenance, then — as a separate explicit step after the asset merges — retire the source instincts so a lesson never loads twice. Use when the user runs /evolve, asks to promote/graduate approved lessons into shared skills or rules, or to retire instincts whose evolved asset has merged. Requires at least two approved instincts sharing a domain (or an explicit user-named cluster). Not for reviewing pending candidates (that is /instinct-review) and never commits, pushes, or merges anything itself.
---

# Evolve

**Learning compounds through normal code review.** This skill turns
accumulated personal lessons into repo assets every contributor gets — but
the asset lands as an ordinary working-tree change, and the human merges
it. You draft; git review decides.

## Phase 1 — cluster and draft

1. Run `python3 hooks/learned/lib/learned_store.py check` from the
   project root — it resolves the store (worktree-safe) and prints
   invariant warnings. Report any warnings to the user before
   proceeding.
2. Read `.vibe/learned/instincts/approved/*.md`. Cluster by `domain`, then
   by trigger similarity — plain string grouping, no scoring machinery. A
   cluster needs ≥ 2 instincts (or the user names one explicitly). No
   cluster → report "nothing to evolve yet" and stop.
3. Present the clusters; the user picks one.
4. Generate the draft canonical asset in the working tree:
   - a new/edited **skill** (`skills/<name>/SKILL.md`) when the cluster is
     a workflow with judgment ("how"), or a **rule** addition
     (`rules/common/…` or a language pack) when it is a short normative
     constraint ("what") — follow [CONTRIBUTING.md](../../CONTRIBUTING.md)
     and the target pack's conventions (rules ≤ ~100 lines, every rule
     carries its why).
   - carry provenance: `evolved_from: [<instinct-id>, …]` in the skill
     frontmatter, or a header comment for rule files.
   - validate a new skill with
     `uvx --from 'skills-ref==0.1.1' agentskills validate skills/<name>`.
5. Stop. Tell the user the draft is ready for normal git review. **Do not
   commit, push, stage, or merge. Do not retire anything yet** — the
   source instincts stay in `approved/` (and keep loading) until the asset
   actually merges; a lesson must never sit in limbo.

## Phase 2 — retire (separate, explicit)

Entered via `/evolve --retire <asset-path>` or a re-run that detects
merged provenance. Run only when the user confirms the evolved asset
merged — or verify it
yourself: `git show main:<asset-path>` succeeds and the output still
carries the `evolved_from` provenance listing the source instinct ids.
Working-tree presence is not enough; an unmerged draft can be discarded,
and a retired lesson must never point at a file that vanished.

For each source instinct:

1. Edit frontmatter: `status: retired`, add
   `evolved-into: <repo-path-of-asset>`.
2. Move the file `instincts/approved/` → `instincts/retired/` (create
   the directory if missing).
3. After all moves, mirror the backup once
   (`python3 hooks/learned/lib/learned_store.py backup`), then re-run
   `learned_store.py check` — zero warnings is the done condition; a
   warning means a move was mis-applied, so show it to the user.

Retired instincts stop loading at the next session start (the loader reads
only `approved/`), and provenance stays traceable in both directions: the
asset lists instinct ids, each instinct points at the asset path.

## Hard rules

- Never touch `pending/` or `rejected/` — those belong to
  `/instinct-review`.
- Never retire on generation; retirement follows a *merged* asset only.
- One cluster per run — small, reviewable diffs beat batch graduation.
