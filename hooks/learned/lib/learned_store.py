#!/usr/bin/env python3
"""Shared store library for the learned hook pack.

One home for everything more than one consumer needs: store resolution
(worktree-aware), the flat-YAML instinct parser + validation, and atomic
writes. The loader, capture, and review/evolve skills all go through here so
the gate and format rules exist exactly once.

Contracts: specs/001-learned-context/contracts/{store-layout,instinct-file}.md
Self-contained: Python 3.9+ stdlib, matching hooks/security/ conventions.
"""

from __future__ import annotations

import datetime
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

STORE_SUBDIR = Path(".vibe") / "learned"
STATES = ("pending", "approved", "rejected", "retired")

ID_RE = re.compile(r"^[a-z0-9-]{3,64}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Learned lessons are atomic; essays belong in skills (contracts/instinct-file.md).
MAX_INSTINCT_KB = 10
SOURCES = ("session-extraction", "hand-authored", "imported")
SCOPES = ("project", "global")  # global reserved, not built in this feature

PENDING_TTL_DAYS = 30
SUMMARIES_KEPT = 10

REQUIRED_FIELDS = (
    "id", "status", "trigger", "domain", "scope", "source",
    "confidence", "evidence", "created", "last-confirmed",
)


class MalformedInstinct(ValueError):
    """An instinct file that violates contracts/instinct-file.md.

    Consumers never crash on this: they skip the file and warn (FR-013).
    """


# --- Store resolution (research.md D6) --------------------------------------


def resolve_store(cwd) -> "tuple[Path, Optional[str]]":
    """Resolve the learned store for a session cwd.

    Returns (store_path, notice) where notice is a one-line message to show
    when falling back outside git. Worktrees resolve through
    `--git-common-dir` so every pane shares the main checkout's store;
    `--show-toplevel` is deliberately never used here — it returns the
    *worktree* root and would re-create per-worktree fragmentation (FR-010).

    Read-only: never creates directories.
    """
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(cwd), capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            common = Path(proc.stdout.strip())
            if not common.is_absolute():
                common = Path(cwd) / common
            main_checkout = common.resolve().parent
            return main_checkout / STORE_SUBDIR, None
    except (OSError, subprocess.TimeoutExpired):
        pass  # treated as "not a git repo" — fall through to cwd fallback
    store = (Path(cwd) / STORE_SUBDIR).resolve()
    return store, f"learned store: non-git fallback at {store}"


def list_state(store, state: str) -> "list[Path]":
    """Instinct files in one state directory; [] when the dir is absent."""
    state_dir = Path(store) / "instincts" / state
    try:
        return sorted(p for p in state_dir.iterdir() if p.suffix == ".md")
    except OSError:  # missing store reads as empty, never as an error (US1 sc.5)
        return []


def list_summaries(store) -> "list[Path]":
    """Session summaries, newest first (filenames start with ISO dates)."""
    data_dir = Path(store) / "session-data"
    try:
        return sorted(
            (p for p in data_dir.iterdir() if p.suffix == ".md"), reverse=True
        )
    except OSError:
        return []


# --- Frontmatter parsing (flat YAML subset — contracts/instinct-file.md) ----


def _parse_scalar(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def _parse_inline_list(raw: str) -> "list[str]":
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    return [_parse_scalar(part) for part in inner.split(",")]


def parse_frontmatter(text: str) -> "tuple[dict, str]":
    """Parse `---` frontmatter into (fields, body).

    Supports only the flat subset: scalar values, inline `[a, b]` lists, and
    single-level block lists. Anything deeper (nested maps, multi-line
    scalars) raises MalformedInstinct — by design, not as a limitation.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise MalformedInstinct("missing frontmatter opening '---'")
    fields: dict = {}
    current_list_key = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n".join(lines[i + 1:])
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if current_list_key is None:
                raise MalformedInstinct(f"stray list item outside a key: {stripped!r}")
            item = _parse_scalar(stripped[2:])
            # a "- key:"-shaped item means nested yaml, outside the flat subset
            if isinstance(item, str) and item.endswith(":"):
                raise MalformedInstinct(
                    "nested yaml is outside the supported flat subset"
                )
            fields[current_list_key].append(item)
            continue
        if line.startswith((" ", "\t")):
            raise MalformedInstinct(
                f"nested yaml is outside the supported flat subset: {stripped!r}"
            )
        if ":" not in stripped:
            raise MalformedInstinct(f"unparsable frontmatter line: {stripped!r}")
        key, _, raw = stripped.partition(":")
        key = key.strip()
        raw = raw.strip()
        if raw == "":
            fields[key] = []
            current_list_key = key
        elif raw.startswith("[") and raw.endswith("]"):
            fields[key] = _parse_inline_list(raw)
            current_list_key = None
        else:
            fields[key] = _parse_scalar(raw)
            current_list_key = None
    raise MalformedInstinct("missing frontmatter closing '---'")


def action_text(body: str) -> str:
    """The `## Action` section content, stripped; '' when absent/empty."""
    lines = body.split("\n")
    collected: "list[str]" = []
    in_action = False
    for line in lines:
        if line.startswith("## "):
            if in_action:
                break
            in_action = line.strip().lower() == "## action"
            continue
        if in_action:
            collected.append(line)
    return "\n".join(collected).strip()


def validate_instinct(fields: dict, body: str, path=None) -> None:
    """Raise MalformedInstinct on any contract violation; return None if valid."""
    for f in REQUIRED_FIELDS:
        if f not in fields:
            raise MalformedInstinct(f"missing required field '{f}'")
    iid = fields["id"]
    if not isinstance(iid, str) or not ID_RE.match(iid):
        raise MalformedInstinct(f"id must match [a-z0-9-]{{3,64}}, got {iid!r}")
    if path is not None and Path(path).stem != iid:
        raise MalformedInstinct(
            f"id {iid!r} does not equal filename stem {Path(path).stem!r}"
        )
    if fields["status"] not in STATES:
        raise MalformedInstinct(f"unknown status {fields['status']!r}")
    if not str(fields["trigger"]).strip():
        raise MalformedInstinct("trigger must be non-empty")
    if fields["scope"] not in SCOPES:
        raise MalformedInstinct(f"unknown scope {fields['scope']!r}")
    if fields["source"] not in SOURCES:
        raise MalformedInstinct(f"unknown source {fields['source']!r}")
    try:
        conf = float(fields["confidence"])
    except (TypeError, ValueError):
        raise MalformedInstinct(f"confidence not a number: {fields['confidence']!r}")
    if not 0.0 <= conf <= 1.0:
        raise MalformedInstinct(f"confidence out of [0,1]: {conf}")
    evidence = fields["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise MalformedInstinct("evidence must be a non-empty list")
    for key in ("created", "last-confirmed"):
        if not ISO_DATE_RE.match(str(fields[key])):
            raise MalformedInstinct(f"{key} is not an ISO date: {fields[key]!r}")
    if fields["status"] == "retired" and not fields.get("evolved-into"):
        raise MalformedInstinct("retired instinct missing 'evolved-into'")
    if not action_text(body):
        raise MalformedInstinct("empty or missing '## Action' section")


def load_instinct(path) -> dict:
    """Load + validate one instinct file.

    Returns {"fields", "body", "action", "path"}; raises MalformedInstinct.
    """
    path = Path(path)
    if path.stat().st_size > MAX_INSTINCT_KB * 1024:
        raise MalformedInstinct(f"file exceeds the {MAX_INSTINCT_KB} KB size guard")
    fields, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    validate_instinct(fields, body, path=path)
    fields["confidence"] = float(fields["confidence"])
    return {"fields": fields, "body": body,
            "action": action_text(body), "path": path}


# --- Serialization ----------------------------------------------------------

_FIELD_ORDER = (
    "id", "status", "trigger", "domain", "scope", "source", "confidence",
    "evidence", "created", "last-confirmed", "evolved-into", "sessions",
)
_QUOTED_FIELDS = {"trigger"}


def _scalar_out(value) -> str:
    # single-line always; our parser has no escape syntax, so drop the quote
    # character rather than emit an unparsable value
    return str(value).replace("\n", " ").replace('"', "'").strip()


def render_instinct(fields: dict, action: str, title: "Optional[str]" = None,
                    extra_body: str = "") -> str:
    """Serialize an instinct to the canonical file format."""
    out = ["---"]
    for key in _FIELD_ORDER:
        if key not in fields:
            continue
        value = fields[key]
        if isinstance(value, list):
            out.append(f"{key}:")
            out.extend(f'  - "{_scalar_out(item)}"' for item in value)
        elif key in _QUOTED_FIELDS:
            out.append(f'{key}: "{_scalar_out(value)}"')
        else:
            out.append(f"{key}: {_scalar_out(value)}")
    out.append("---")
    out.append(f"# {title or fields['id']}")
    out.append("")
    out.append("## Action")
    out.append(action.strip())
    if extra_body.strip():
        out.append("")
        out.append(extra_body.strip())
    out.append("")
    return "\n".join(out)


# --- Secret scrub (research.md D10, SC-006) ---------------------------------

# Pattern classes copied from hooks/security/protect-secrets.py — copied, not
# imported, so each hook pack stays independently copyable; keep the two
# lists in sync when either changes.
SECRET_CONTENT_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub personal access token"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub fine-grained PAT"),
    (r"AIza[0-9A-Za-z_\-]{35}", "Google API key"),
    # require a long *contiguous* alphanumeric run so hyphenated CSS/ident
    # tokens ("sk-ai-user-message-text") don't match — real keys are
    # high-entropy blocks, optionally after an sk-proj-/sk-svcacct- prefix.
    (r"sk-[A-Za-z0-9_\-]{0,12}[A-Za-z0-9]{20,}",
     "sk-prefixed API key (OpenAI/Anthropic-style)"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
    (r"glpat-[A-Za-z0-9_\-]{20,}", "GitLab personal access token"),
    (r"npm_[A-Za-z0-9]{36}", "npm access token"),
    (r"-----BEGIN\s+(RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|PGP\s+)?PRIVATE KEY(\s+BLOCK)?-----",
     "private key block"),
]

PLACEHOLDER_MARKERS = ("EXAMPLE", "PLACEHOLDER", "CHANGEME", "XXXX")

_SECRET_COMPILED = [(re.compile(p), label) for p, label in SECRET_CONTENT_PATTERNS]


def scrub_secrets(text: str) -> "tuple[str, list[str]]":
    """Redact live-credential shapes; returns (scrubbed_text, hit_labels).

    Deterministic code, not model judgment — SC-006 is verified by scanning,
    so the guarantee must not depend on a prompt. Obviously-fake
    placeholders (EXAMPLE/PLACEHOLDER/…) pass untouched, same as the
    security pack.
    """
    hits: "list[str]" = []

    for regex, label in _SECRET_COMPILED:
        def _repl(match, label=label):
            if any(m in match.group(0).upper() for m in PLACEHOLDER_MARKERS):
                return match.group(0)
            hits.append(label)
            return f"[REDACTED:{label}]"

        text = regex.sub(_repl, text)
    return text, hits


# --- Git exclusion (research.md D5, FR-001) ---------------------------------


def ensure_git_exclude(cwd) -> bool:
    """Idempotently ensure `.vibe/` is in the repo-local ignore file.

    Uses `$(git rev-parse --git-common-dir)/info/exclude` — repo-local (never
    committed, no merge surface) and shared by all worktrees. The project's
    `.gitignore` is never touched (constitution IV). Returns False outside
    git (fallback stores have nothing to exclude from).
    """
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(cwd), capture_output=True, text=True, timeout=10,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return False
        common = Path(proc.stdout.strip())
        if not common.is_absolute():
            common = Path(cwd) / common
        exclude = common.resolve() / "info" / "exclude"
        existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if any(line.strip() == ".vibe/" for line in existing.splitlines()):
            return True
        exclude.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if (not existing or existing.endswith("\n")) else "\n"
        with exclude.open("a", encoding="utf-8") as fh:
            fh.write(f"{prefix}.vibe/\n")
        return True
    except OSError:
        return False


# --- Prune pass (FR-009, research.md D9) ------------------------------------


def prune(store, today: "Optional[datetime.date]" = None) -> "list[str]":
    """Bound the store: TTL-delete stale pending, keep newest summaries.

    Touches ONLY instincts/pending/ and session-data/ — approved, rejected,
    and retired are never pruned (contracts/store-layout.md). Returns the
    deleted filenames so callers can report them (pruning is never silent).
    ENOENT during delete is tolerated: a parallel session end may have won.
    """
    today = today or datetime.date.today()
    cutoff = (today - datetime.timedelta(days=PENDING_TTL_DAYS)).isoformat()
    pruned: "list[str]" = []
    for path in list_state(store, "pending"):
        try:
            fields, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            created = str(fields.get("created", ""))
        except (OSError, MalformedInstinct):
            # unreadable pending file: age by mtime so garbage can't live forever
            try:
                created = datetime.date.fromtimestamp(
                    path.stat().st_mtime).isoformat()
            except OSError:
                continue
        if ISO_DATE_RE.match(created) and created < cutoff:
            try:
                path.unlink()
                pruned.append(path.name)
            except OSError:
                pass  # concurrently vanished — already gone is the goal state
    summaries = list_summaries(store)  # newest first
    for path in summaries[SUMMARIES_KEPT:]:
        try:
            path.unlink()
            pruned.append(path.name)
        except OSError:
            pass  # concurrently vanished
    return pruned


# --- Atomic writes (contracts/store-layout.md Concurrency) ------------------


# --- Backup (research.md D7, FR-011) ----------------------------------------

# only these states are mirrored: approved instincts are months of review,
# pending is explicitly expendable (spec assumption), rejected is only a
# dedup archive
BACKED_UP_STATES = ("approved", "retired")


def _data_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg:
        return Path(xdg)
    local = os.environ.get("LOCALAPPDATA", "").strip()  # Windows, documented only
    if local:
        return Path(local)
    return Path.home() / ".local" / "share"


def project_id(main_checkout) -> str:
    """Stable 12-hex project identity for the backup namespace.

    Prefers the normalized first remote URL (machine-portable); falls back
    to the main-checkout absolute path.
    """
    import hashlib

    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(main_checkout), capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            url = proc.stdout.strip().lower().rstrip("/")
            if url.endswith(".git"):
                url = url[:-4]
            return hashlib.sha256(url.encode()).hexdigest()[:12]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return hashlib.sha256(
        str(Path(main_checkout).resolve()).encode()).hexdigest()[:12]


def backup_store(store) -> Path:
    """Mirror approved/ and retired/ to the out-of-repo backup; returns dest.

    Copy-on-event, append-favoring: same-id files are overwritten, but
    nothing is ever deleted here — a store wiped by `git clean -fdx` must
    remain recoverable (restore = manual copy back, see the pack README).
    """
    import shutil

    store = Path(store)
    main_checkout = store.parents[1]  # store = <main>/.vibe/learned
    dest = _data_home() / "vibe" / "backup" / project_id(main_checkout)
    for state in BACKED_UP_STATES:
        state_dest = dest / "instincts" / state
        for path in list_state(store, state):
            state_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, state_dest / path.name)
    return dest


# --- Store health (consumed by the review/evolve skills) --------------------


def check_store(store) -> "list[str]":
    """Invariant warnings: malformed files and status/directory mismatches.

    Report-only — a mismatch is never silently fixed (data-model.md gate
    invariant): the directory stays authoritative and a human decides.
    """
    warnings: "list[str]" = []
    for state in STATES:
        for path in list_state(store, state):
            try:
                inst = load_instinct(path)
            except MalformedInstinct as exc:
                warnings.append(f"malformed {state}/{path.name}: {exc}")
                continue
            status = inst["fields"]["status"]
            if status != state:
                warnings.append(
                    f"status/directory mismatch: {state}/{path.name} claims "
                    f"status '{status}' (directory is authoritative)"
                )
    return warnings


# --- Atomic writes (contracts/store-layout.md Concurrency) ------------------


def atomic_write(path, text: str) -> None:
    """Write via temp file + rename in the same directory (never torn).

    Unique tempfile names keep parallel session ends from colliding even on
    the same target; os.replace makes the last writer win atomically.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, str(path))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass  # tmp already renamed or gone — nothing to clean
        raise


# --- CLI (used by the instinct-review and evolve skills) --------------------


def _cli(argv: "list[str]") -> int:
    """`python3 learned_store.py backup|check` — resolves the store from cwd.

    Gives the skills one vetted entry point for backup and invariant checks
    instead of each re-implementing store logic.
    """
    if len(argv) != 1 or argv[0] not in ("backup", "check"):
        print("usage: learned_store.py backup|check", file=sys.stderr)
        return 2
    store, notice = resolve_store(os.getcwd())
    if notice:
        print(notice, file=sys.stderr)
    if argv[0] == "backup":
        count = sum(len(list_state(store, s)) for s in BACKED_UP_STATES)
        dest = backup_store(store)
        noun = "file" if count == 1 else "files"
        print(f"backed up {count} {noun} to {dest}")
        return 0
    warnings = check_store(store)
    for w in warnings:
        print(f"warning: {w}")
    if not warnings:
        print("store ok")
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
