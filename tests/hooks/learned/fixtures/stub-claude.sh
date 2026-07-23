#!/bin/sh
# Test stub standing in for the `claude` CLI (research.md D12 seam:
# VIBE_LEARNED_CLAUDE_CMD points here). Consumes the prompt on stdin and
# emits `--output-format json`-shaped output whose `result` field holds the
# extraction payload — from $STUB_PAYLOAD (a file path) when set, else the
# built-in default below.
#
# The default payload deliberately plants secret-shaped strings (AWS key id,
# GitHub PAT) so test_no_secrets_at_rest can prove the capture scrub works,
# and a candidate id `existing-lesson` for the dedup test.
cat > /dev/null

python3 - "$STUB_PAYLOAD" <<'PYEOF'
import json
import os
import sys

payload_path = sys.argv[1] if len(sys.argv) > 1 else ""
if payload_path and os.path.exists(payload_path):
    inner = open(payload_path, encoding="utf-8").read()
else:
    inner = json.dumps({
        "summary": (
            "Worked on the demo feature. Corrected batching twice. "
            "Config pasted during session mentioned AKIAABCDEFGHIJKLMNOP "
            "which must never reach disk."
        ),
        "candidates": [
            {
                "id": "prefer-batch-writes",
                "trigger": "when writing many small files",
                "domain": "workflow",
                "action": "Batch the writes instead of looping one call per file.",
                "evidence": [
                    "2026-07-23 session t2: user corrected one-write-per-file loop twice",
                    "2026-07-23 session t2: token ghp_abcdefghijklmnopqrstuvwxyz0123456789 seen in pasted env dump",
                ],
                "sessions": ["t2"],
            },
            {
                "id": "existing-lesson",
                "trigger": "when checking dedup",
                "domain": "workflow",
                "action": "This id already exists in the store and must be dropped.",
                "evidence": [
                    "2026-07-23 session t2: duplicate pattern observed",
                    "2026-07-23 session t2: duplicate pattern observed again",
                ],
                "sessions": ["t2"],
            },
        ],
    })
print(json.dumps({"type": "result", "result": inner}))
PYEOF
