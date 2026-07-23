# Contract: Hook I/O and wiring

Verified against code.claude.com/docs (hooks, CLI reference; fetched
2026-07-23). Both scripts follow `hooks/security/` conventions: Python 3.9+,
stdlib only, and the wiring block lives in `hooks/learned/README.md` for
users to add to `.claude/settings.json` (per-project opt-in — AGENTS.md).

## SessionStart — `load-learned-context.py`

- **Matcher**: `startup|clear|compact` (not `resume`: restored transcript
  already contains the block — research.md D1).
- **stdin**: hook JSON (`session_id`, `cwd`, `source`, …). `cwd` drives
  store resolution; `source` is logged only.
- **stdout**: the learned-context block ([context-block.md](context-block.md))
  — docs confirm SessionStart stdout is added to session context. Empty
  stdout when the store is empty/absent.
- **stderr**: warnings only (malformed files, non-git fallback notice).
- **exit code**: always 0 (a loader failure must never break session start
  — deliberate fail-open for side work, with the error on stderr).
- **Performance**: < 500 ms; no network, no subprocesses except `git
  rev-parse`.

## SessionEnd — `capture-learned-context.py`

- **stdin**: hook JSON (`session_id`, `cwd`, `transcript_path`, `reason`).
- **Behavior** (in order):
  1. run prune pass ([store-layout.md](store-layout.md));
  2. write session summary (skip if transcript below triviality threshold
     — research.md D2 / FR-006: fewer than 10 user messages);
  3. run extraction synchronously with an internal 120 s cap: invoke
     `extract-instincts.py`, which shells to headless
     `claude -p --model haiku --max-turns 1 --output-format json` with a
     prompt containing the transcript tail plus the dedup context (existing
     instinct ids+triggers from ALL state dirs, MEMORY.md index if present,
     rule-pack filenames);
  4. validate + scrub extractor output, write pending instinct files.
- **stdout**: one-line human status (docs: SessionEnd stdout is shown to
  the user, not added to context) — e.g. `learned: 2 candidates pending
  review (/instinct-review)`; silent when nothing was written.
- **exit code**: always 0; SessionEnd cannot block session end. Extraction
  failure/timeout ⇒ skip with stderr note (best-effort, stated).
- **Testing seam**: env var `VIBE_LEARNED_CLAUDE_CMD` overrides the
  `claude` binary so tests substitute a stub (research.md D12).

## Wiring block (shipped in `hooks/learned/README.md`)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/learned/load-learned-context.py\"" }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/learned/capture-learned-context.py\"" }
        ]
      }
    ]
  }
}
```

## Degradation note (constitution II)

This pack is Claude Code-native. Other harnesses lack these lifecycle
events; the pack README states plainly that on such platforms the loop does
not run (no silent no-op adapters). Porting is owned by the planned
`vibe sync`.
