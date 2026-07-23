# Learned hooks

The reviewed, file-based memory loop decided in
[ADR 0003](../../docs/decisions/0003-use-reviewed-file-based-memory.md):
sessions produce candidate lessons ("instincts") with evidence, a human
reviews them, and **only approved lessons load into future sessions**. The
gate is structural — the loader reads exactly one directory,
`instincts/approved/`, so nothing pending or rejected can reach a session
regardless of what any file claims (constitution principle III).

Full design: `specs/001-learned-context/` (spec, contracts, quickstart).

## Store

Plain Markdown files, visible in your editor — the file tree *is* the
review UI:

```text
<main-checkout>/.vibe/learned/
├── session-data/                  # session summaries (latest one loads)
└── instincts/
    ├── pending/                   # candidates awaiting review
    ├── approved/                  # ONLY directory the loader reads
    ├── rejected/                  # archive; prevents re-proposal
    └── retired/                   # graduated into skills/rules
```

Worktree sessions share the main checkout's store. The store is kept out
of version control automatically (`.git/info/exclude`, not your
`.gitignore`). One git caveat: ignore rules never apply to files already
*tracked* — if you committed `.vibe/` before adopting this pack, untrack
it once yourself (`git rm -r --cached .vibe`); the pack won't rewrite your
index for you.

## Loading (`load-learned-context.py`)

SessionStart hook. Prints a condensed block into session context: up to 20
approved instincts (`- [domain] trigger → action`, most recently confirmed
first, hard cap 200 lines / 25 KB, truncation always stated) plus the
latest session summary. Empty or missing store → no block, no error. A
malformed file is skipped with a stderr warning — session start never
breaks.

## Capture (`capture-learned-context.py`)

SessionEnd hook. In order: restores the git exclusion, prunes (pending
older than 30 days, all but the newest 10 summaries — approved/rejected/
retired are never pruned), skips trivial sessions (< 10 user messages),
then runs one synchronous extraction pass (headless `claude -p`, haiku,
capped at 120 s) that produces the session summary and candidate lessons
in a single batch. Candidates are validated, secret-scrubbed
(AWS/GitHub/Google/Slack/GitLab/npm/private-key shapes — same pattern
classes as [hooks/security](../security/README.md)), deduplicated against
every state directory, and written to `instincts/pending/` **only**.

Extraction failure or timeout skips cleanly with a stderr note — capture
is best-effort by design and never blocks session end. When candidates
were written you'll see one line: `learned: N candidates pending review
(/instinct-review)`.

## Wiring (Claude Code)

Add to `.claude/settings.json` (per-project opt-in, like
[hooks/security](../security/README.md)):

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

`resume` is deliberately not matched: a resumed transcript already
contains the block. Requirements: `python3` (3.9+), `git` and `claude` on
PATH; stdlib only.

## Degradation on other harnesses

This pack is Claude Code-native: it depends on SessionStart/SessionEnd
lifecycle events and the `claude` CLI. On harnesses without those (Cursor,
Codex, …) **the loop does not run** — there is no silent no-op adapter.
Porting is owned by the planned `vibe sync`
([ARCHITECTURE.md](../../ARCHITECTURE.md)).

## Coexistence with Claude Code auto-memory

Both stay on, with a division of labor: auto-memory is the platform's
unreviewed scratch layer; instincts are reviewed behavioral lessons.
Extraction reads the auto-memory index (`MEMORY.md`) as a dedup source, and
review surfaces overlap so you can absorb or reject. If you want a single
memory system, the platform switch is `autoMemoryEnabled: false` (or
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`) — this pack never flips it for you.

## Knobs

| Env var | Default | Meaning |
|---|---|---|
| `VIBE_LEARNED_EXTRACT_TIMEOUT` | `120` | extraction cap in seconds |
| `VIBE_LEARNED_CLAUDE_CMD` | `claude` | extraction binary (test seam) |

## Hand-authoring a lesson (works today, no capture needed)

Create `.vibe/learned/instincts/approved/<id>.md`:

```markdown
---
id: run-linter-before-done
status: approved
trigger: "when about to declare an edit done"
domain: workflow
scope: project
source: hand-authored
confidence: 0.9
evidence:
  - "2026-07-23: repeated review feedback about unlinted diffs"
created: 2026-07-23
last-confirmed: 2026-07-23
---
# Run the linter before done

## Action
Run the project linter and fix findings before reporting an edit complete.
```

The filename must equal `id`. Next session start, the lesson is in
context — check with `/context`.
