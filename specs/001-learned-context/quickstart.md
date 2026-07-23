# Quickstart: validating Learned Context

Runnable proof per user story (constitution VI). Prerequisites: this repo
checked out, `python3` (3.9+), `git`, `pytest` (dev), and for live-loop
checks a Claude Code session with the hooks wired per
[contracts/hook-io.md](contracts/hook-io.md).

## 0. Test suite (hermetic — no live session needed)

```bash
pytest tests/hooks/learned/ -v
```

Expected: all green, including the two guarantee tests —
`test_gate_never_loads_pending_or_rejected` (SC-002) and
`test_no_secrets_at_rest` (SC-006).

## 1. US1 — approved lessons load (P1)

```bash
# hand-author one approved and one pending instinct in a scratch repo
mkdir -p /tmp/lc-demo && cd /tmp/lc-demo && git init -q
mkdir -p .vibe/learned/instincts/{approved,pending}
cp <repo>/specs/001-learned-context/contracts/instinct-file.md /dev/null  # see format
$EDITOR .vibe/learned/instincts/approved/always-run-linter.md   # valid instinct
$EDITOR .vibe/learned/instincts/pending/never-load-me.md        # valid instinct

# loader in isolation (no session needed):
echo '{"session_id":"t1","cwd":"'"$PWD"'","source":"startup"}' \
  | python3 <repo>/hooks/learned/load-learned-context.py
```

Expected: stdout contains a `# Learned context` block with
`always-run-linter`, and **no trace** of `never-load-me`. In a live wired
session, `/context` shows the same block.

Worktree variant: `git worktree add .vibe/worktrees/wt1 && cd
.vibe/worktrees/wt1`, rerun the loader with that cwd — identical output
(FR-010).

Empty-store variant: run in a repo without `.vibe/` — empty stdout, exit 0.

## 2. US2 — capture at session end (P2)

```bash
# stub the extraction LLM (hermetic):
export VIBE_LEARNED_CLAUDE_CMD=<repo>/tests/hooks/learned/fixtures/stub-claude.sh
echo '{"session_id":"t2","cwd":"'"$PWD"'","transcript_path":"<repo>/tests/hooks/learned/fixtures/transcript-with-corrections.jsonl","reason":"other"}' \
  | python3 <repo>/hooks/learned/capture-learned-context.py
```

Expected:

- `session-data/` gains a dated summary;
- `instincts/pending/` gains candidate(s) with `status: pending`, evidence
  citing the corrections, confidence set;
- `instincts/approved/` untouched (compare `ls -la` before/after);
- `git check-ignore .vibe` exits 0 (exclusion auto-ensured);
- rerunning with a trivial transcript fixture writes nothing;
- `grep -rE '<secret patterns>' .vibe/learned/` finds nothing.

## 3. US3 — review flow (P3)

In a Claude Code session in the scratch repo with ≥ 2 pending instincts:

```
/instinct-review
```

Expected: each candidate presented with evidence + overlap report; choose
Approve for one, Reject for the other. Then verify on disk: first file now
in `approved/` with today's `last-confirmed` and a backup copy under
`~/.local/share/vibe/backup/<project-id>/`; second in `rejected/`. Rerun
the loader — only the approved one appears.

Prune check: backdate a pending file's `created` by 31 days, run capture
again, file is gone and stderr said so.

## 4. US4 — evolve (P4)

With 2–3 approved instincts sharing `domain: code-style`:

```
/evolve
```

Expected: a draft rule/skill appears as an uncommitted working-tree change
with `evolved_from: [<ids>]`; nothing was committed; source instincts still
in `approved/`. After merging the draft (normal git flow) and running the
retire step: sources moved to `retired/` with `evolved-into` set, and the
loader no longer emits them.

## 5. Budget and resilience spot-checks

- Generate 30 valid approved instincts (fixture script) → loader emits ≤ 20
  instinct lines, ≤ 200 lines / 25 KB total, and an explicit "…and N more"
  line (SC-003).
- Corrupt one approved file (`echo garbage > …`) → loader still exits 0,
  block renders the rest, stderr names the bad file (SC-007).
