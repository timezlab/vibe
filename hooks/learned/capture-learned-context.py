#!/usr/bin/env python3
"""SessionEnd hook — session summary + candidate-instinct capture.

Behavior, in contract order (contracts/hook-io.md): resolve store → ensure
git exclusion → prune pass → triviality check → one synchronous extraction
pass (internal cap, default 120 s) → validate + scrub → atomic writes into
instincts/pending/ ONLY (FR-003 — approval is a human act, never this
script's).

Fail-open on purpose with the reason stated: capture is best-effort side
work — SessionEnd cannot block session end, so every failure path is a
stderr note + exit 0, never a crash and never a partial/corrupt write.

stdout is shown to the user (not added to context): one status line when
candidates were written, silence otherwise.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import learned_store as store_lib  # noqa: E402

# fewer user messages than this = nothing worth learning (FR-006, D2)
TRIVIALITY_MIN_USER_MESSAGES = 10
# internal cap keeps us well inside the 600 s hook budget; env-overridable
# as a test seam (slow-stub timeout test) and an operator knob
DEFAULT_EXTRACT_TIMEOUT_S = 120

EXTRACTOR = Path(__file__).resolve().parent / "extract-instincts.py"


def warn(msg: str) -> None:
    print(f"learned: {msg}", file=sys.stderr)


def count_user_messages(transcript_path: Path) -> int:
    """User-authored messages in the transcript (tool results excluded)."""
    count = 0
    with transcript_path.open(encoding="utf-8") as fh:
        for raw in fh:
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "user":
                continue
            content = (entry.get("message") or {}).get("content")
            if isinstance(content, str):
                count += 1
            elif isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "text" for b in content
            ):
                count += 1
    return count


def run_extraction(transcript_path: Path, store: Path) -> "dict | None":
    """Run the extraction subprocess under the cap; None = skip visibly."""
    timeout_s = int(os.environ.get(
        "VIBE_LEARNED_EXTRACT_TIMEOUT", DEFAULT_EXTRACT_TIMEOUT_S))
    try:
        proc = subprocess.run(
            [sys.executable, str(EXTRACTOR), str(transcript_path), str(store)],
            capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        warn(f"extraction timed out after {timeout_s}s — skipping this session")
        return None
    if proc.returncode != 0:
        warn(f"extraction failed — skipping this session "
             f"({proc.stderr.strip()[:300]})")
        return None
    try:
        data = json.loads(proc.stdout)
        assert isinstance(data.get("summary"), str)
        assert isinstance(data.get("candidates"), list)
        return data
    except (json.JSONDecodeError, AssertionError):
        warn("extraction returned unusable output — skipping this session")
        return None


def scrub(text: str, context: str) -> str:
    scrubbed, hits = store_lib.scrub_secrets(str(text))
    for label in hits:
        warn(f"redacted {label} in {context} — review before approving")
    return scrubbed


def write_summary(store: Path, session_id: str, cwd: str, summary: str,
                  today: str) -> None:
    now = datetime.datetime.now().isoformat(timespec="seconds")
    text = (
        f"---\nsession-id: {session_id}\ndate: {now}\ncwd: {cwd}\n---\n"
        f"{scrub(summary, 'session summary').strip()}\n"
    )
    store_lib.atomic_write(store / "session-data" / f"{today}-{session_id}.md",
                           text)


def confidence_for(evidence_count: int) -> float:
    # extractor heuristic pinned in contracts/instinct-file.md
    if evidence_count > 5:
        return 0.85
    if evidence_count >= 3:
        return 0.7
    return 0.5


def write_candidates(store: Path, candidates: "list", today: str) -> int:
    existing_ids = {
        p.stem
        for state in store_lib.STATES
        for p in store_lib.list_state(store, state)
    }
    written = 0
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        cid = re.sub(r"[^a-z0-9-]", "-", str(cand.get("id", "")).lower()).strip("-")
        if not cid:
            continue
        if cid in existing_ids:  # FR-007: any state blocks re-proposal
            warn(f"dropped duplicate candidate '{cid}' (already in store)")
            continue
        evidence = [scrub(e, f"candidate {cid} evidence")
                    for e in cand.get("evidence", []) if str(e).strip()]
        fields = {
            "id": cid,
            "status": "pending",
            "trigger": scrub(cand.get("trigger", ""), f"candidate {cid}"),
            "domain": re.sub(r"[^a-z0-9-]", "-",
                             str(cand.get("domain", "workflow")).lower()) or "workflow",
            "scope": "project",
            "source": "session-extraction",
            "confidence": confidence_for(len(evidence)),
            "evidence": evidence,
            "created": today,
            "last-confirmed": today,
        }
        sessions = [str(s) for s in cand.get("sessions", []) if str(s).strip()]
        if sessions:
            fields["sessions"] = sessions
        action = scrub(cand.get("action", ""), f"candidate {cid}")
        text = store_lib.render_instinct(fields, action)
        try:
            # round-trip validation: only files the loader can read get written
            parsed_fields, body = store_lib.parse_frontmatter(text)
            store_lib.validate_instinct(parsed_fields, body)
        except store_lib.MalformedInstinct as exc:
            warn(f"dropped invalid candidate '{cid}': {exc}")
            continue
        store_lib.atomic_write(
            store / "instincts" / "pending" / f"{cid}.md", text)
        existing_ids.add(cid)
        written += 1
    return written


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()
    session_id = re.sub(r"[^A-Za-z0-9-]", "", str(payload.get("session_id")
                                                  or "unknown"))[:32] or "unknown"
    store, notice = store_lib.resolve_store(cwd)
    if notice:
        print(notice, file=sys.stderr)
    store_lib.ensure_git_exclude(cwd)

    pruned = store_lib.prune(store)
    if pruned:
        warn(f"pruned {len(pruned)} stale file(s): {', '.join(sorted(pruned))}")

    transcript_raw = payload.get("transcript_path")
    if not transcript_raw or not Path(transcript_raw).is_file():
        warn("no transcript available — skipping capture")
        return
    transcript_path = Path(transcript_raw)
    if count_user_messages(transcript_path) < TRIVIALITY_MIN_USER_MESSAGES:
        warn("trivial session — skipping capture")
        return

    data = run_extraction(transcript_path, store)
    if data is None:
        return  # reason already on stderr

    today = datetime.date.today().isoformat()
    write_summary(store, session_id, str(cwd), data["summary"], today)
    written = write_candidates(store, data["candidates"], today)
    if written:
        noun = "candidate" if written == 1 else "candidates"
        print(f"learned: {written} {noun} pending review (/instinct-review)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # fail open: SessionEnd must never be blocked
        warn(f"capture error, nothing written ({type(exc).__name__}: {exc})")
    sys.exit(0)
