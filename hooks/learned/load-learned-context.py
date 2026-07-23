#!/usr/bin/env python3
"""SessionStart hook (matcher: startup|clear|compact) — learned-context loader.

Reads the per-project learned store and prints the condensed learned-context
block on stdout (SessionStart stdout is added to session context). Reads
EXCLUSIVELY from instincts/approved/ — the pending→approved gate is this
path restriction, not a status-field check (FR-004, constitution III).

Read-only by contract: never creates, prunes, or mutates the store (prune
belongs to the SessionEnd capture — one writer per lifecycle event).

Fail-open on purpose: a loader failure must never break session start, so
every error path ends in empty-or-partial stdout + a stderr note + exit 0.
This is best-effort side work, unlike the fail-closed security guards.

Contracts: specs/001-learned-context/contracts/{context-block,hook-io}.md
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import learned_store as store_lib  # noqa: E402

MAX_INSTINCTS = 20
MAX_LINES = 200
MAX_BYTES = 25 * 1024
# one rendered line per instinct; long actions are condensed, not wrapped
MAX_ACTION_CHARS = 200
TRUNCATION_LINE = (
    "- …and {n} more approved instincts not loaded "
    "(run /instinct-review to consolidate)"
)


def condense_action(action: str) -> str:
    """First sentence(s) of the action, single line, capped."""
    one_line = " ".join(action.split())
    first = one_line.split(". ")[0].rstrip(".") + "."
    if len(first) < 60 and ". " in one_line:  # too terse alone — take two
        second = one_line.split(". ")[1].rstrip(".") + "."
        first = f"{first} {second}"
    return first[:MAX_ACTION_CHARS]


def instinct_line(inst: dict) -> str:
    f = inst["fields"]
    return f"- [{f['domain']}] {f['trigger']} → {condense_action(inst['action'])}"


def summary_section(store: Path) -> "list[str]":
    summaries = store_lib.list_summaries(store)
    if not summaries:
        return []
    latest = summaries[0]
    try:
        _, body = store_lib.parse_frontmatter(latest.read_text(encoding="utf-8"))
    except (OSError, store_lib.MalformedInstinct) as exc:
        print(f"learned: skipping malformed summary {latest.name}: {exc}",
              file=sys.stderr)
        return []
    date = latest.name[:10]
    body_lines = [l for l in body.strip().split("\n")]
    return ["", f"## Previous session ({date})"] + body_lines[:20]


def within_budget(lines: "list[str]") -> bool:
    text = "\n".join(lines) + "\n"
    return len(lines) <= MAX_LINES and len(text.encode()) <= MAX_BYTES


def build_block(store: Path) -> str:
    instincts = []
    for path in store_lib.list_state(store, "approved"):
        try:
            instincts.append(store_lib.load_instinct(path))
        except (store_lib.MalformedInstinct, OSError) as exc:
            # FR-013 / SC-007: skip visibly, keep loading the rest
            print(f"learned: skipping malformed instinct {path.name}: {exc}",
                  file=sys.stderr)
    instincts.sort(
        key=lambda i: (i["fields"]["last-confirmed"], i["fields"]["id"]),
        reverse=True,
    )
    total = len(instincts)
    selected = instincts[:MAX_INSTINCTS]
    summary = summary_section(store)
    if not selected and not summary:
        return ""  # empty store: no block, no header, no error (US1 sc.5)

    def render(selected_count: int) -> "list[str]":
        omitted = total - selected_count
        noun = "instinct" if selected_count == 1 else "instincts"
        lines = [
            f"# Learned context ({selected_count} approved {noun} · human-reviewed)",
        ]
        if selected_count:
            lines += ["", "## Instincts"]
            lines += [instinct_line(i) for i in selected[:selected_count]]
            if omitted > 0:
                lines.append(TRUNCATION_LINE.format(n=omitted))
        return lines

    # shrink until the whole block (summary included) fits the hard caps —
    # instincts drop from the tail (oldest last-confirmed) first, the summary
    # is trimmed only after that, and truncation is always stated (SC-003)
    count = len(selected)
    lines = render(count) + summary
    while not within_budget(lines) and count > 0:
        count -= 1
        lines = render(count) + summary
    while not within_budget(lines) and len(summary) > 2:
        summary = summary[:-1]
        lines = render(count) + summary
    return "\n".join(lines) + "\n"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()
    store, notice = store_lib.resolve_store(cwd)
    if notice:
        print(notice, file=sys.stderr)
    block = build_block(store)
    if block:
        sys.stdout.write(block)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # fail open: session start must never break
        print(f"learned: loader error, no context injected ({exc})",
              file=sys.stderr)
    sys.exit(0)
