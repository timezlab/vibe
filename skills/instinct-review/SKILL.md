---
name: instinct-review
description: Guided human review of pending learned-context instincts — present each candidate with its evidence and an overlap report against existing guidance, collect one of four verdicts (approve / improve-then-approve / absorb / reject), and apply the matching file move in .vibe/learned/. Use when the user runs /instinct-review, asks to review pending lessons, instincts, or learned context, or after a session end reports "candidates pending review". Not for creating instincts (the capture hook owns that) or graduating approved clusters into skills/rules (that is /evolve).
---

# Instinct review

**The human is the gate.** Every verdict below is chosen by the user — you
present, they decide, you apply the file effect. Never approve, edit, or
absorb on your own judgment; never touch `instincts/approved/` except
through an explicit verdict (constitution principle III).

## Setup

1. Run `python3 hooks/learned/lib/learned_store.py check` from the
   project root. It resolves the store the same way every consumer does
   (worktree-safe, main checkout) and prints invariant warnings
   (malformed files, status/directory mismatches). Report any warnings
   to the user before proceeding — never silently fix them; the
   directory is authoritative.
2. List `.vibe/learned/instincts/pending/*.md`. If empty: say so, mention
   any warnings from step 1, and stop.

## Per candidate, in `created` order

Present three things, then ask for one verdict:

**1. The instinct** — id, trigger, action, confidence, and each evidence
line verbatim. Evidence flagged `[REDACTED:…]` means the scrubber caught a
secret shape at capture time — point it out.

**2. Overlap report** (the dedup mechanism, FR-008). Grep for the
candidate's key terms in each of these, and quote every match with its
file path:

- rule packs: `rules/**/*.md`
- skill surfaces: `skills/*/SKILL.md` frontmatter (name + description)
- project instructions: `CLAUDE.md`, `AGENTS.md`
- platform memory index: `MEMORY.md` under
  `~/.claude/projects/<project>/memory/` if present
- existing instincts in ALL states (`pending/`, `approved/`, `rejected/`,
  `retired/`)

No matches → say "no overlap found" explicitly.

**3. The four verdicts** — one question, user chooses:

| Verdict | File effect | Side effects |
|---|---|---|
| **Approve** | move `pending/<id>.md` → `approved/` | set `status: approved`; set `last-confirmed` to today; append a `## Review notes` line (date + verdict); then run the backup (below) |
| **Improve then approve** | apply the user's edits (or propose edits and get confirmation), then as Approve | summarize the edits in `## Review notes` |
| **Absorb** | move → `rejected/` with a `## Review notes` line naming the absorbing target | draft the edit to the existing rule/skill/doc as a normal working-tree change for the user to review |
| **Reject** | move → `rejected/` | set `status: rejected`; the archive prevents re-proposal (FR-007) |

Apply each verdict immediately (move + field updates in one step) so an
interrupted review leaves no half-applied state.

## After the last verdict

If anything was approved this session, run the backup mirror once:

```bash
python3 hooks/learned/lib/learned_store.py backup
```

This copies `approved/` and `retired/` to
`~/.local/share/vibe/backup/<project-id>/` so `git clean -fdx` cannot
destroy reviewed learning.

Then re-run `learned_store.py check` and confirm it reports no
warnings — that is the observable proof the review left the store
consistent. A warning here means a verdict was mis-applied; show it to
the user instead of patching it.

## Hard rules

- Decisions take effect next session (the loader reads the store at
  SessionStart) — tell the user that, don't try to inject anything now.
- Never edit files outside `.vibe/learned/` except as *proposed*
  working-tree changes under an Absorb verdict.
- Never commit, push, or stage anything.
- A malformed pending file is presented as malformed (with the parse
  error) and offered only Reject or hand-fix — never silently repaired.
