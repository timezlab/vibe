"""Shared fixtures for the learned hook pack tests.

Hook scripts are exercised two ways (research.md D12):
  - unit tests import ``learned_store`` directly (sys.path below);
  - process-level tests pipe hook stdin JSON to the real scripts via
    ``run_hook`` and assert on stdout/stderr/exit/filesystem effects.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_DIR = REPO_ROOT / "hooks" / "learned"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# Make `import learned_store` work in unit tests.
sys.path.insert(0, str(HOOK_DIR / "lib"))


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A scratch git repository (main checkout) with one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.invalid", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (repo / "README.md").write_text("scratch\n")
    _git("add", ".", cwd=repo)
    _git("commit", "-qm", "init", cwd=repo)
    return repo


@pytest.fixture
def worktree(git_repo: Path) -> Path:
    """A linked worktree of ``git_repo`` (nested under .vibe/ like ADR 0002)."""
    wt = git_repo / ".vibe" / "worktrees" / "wt1"
    _git("worktree", "add", "-q", str(wt), "-b", "wt1", cwd=git_repo)
    return wt


def make_instinct(
    store: Path,
    state: str,
    instinct_id: str,
    *,
    trigger: str = "when testing",
    domain: str = "workflow",
    action: str | None = None,
    last_confirmed: str = "2026-07-23",
    created: str = "2026-07-23",
    status: str | None = None,
    evidence: list[str] | None = None,
) -> Path:
    """Write a valid instinct file into ``store``'s given state directory."""
    evidence = evidence or [f"2026-07-23 session t1: observed {instinct_id}"]
    # default action embeds the id so rendered loader lines are identifiable
    action = action or f"Apply the {instinct_id} behavior."
    path = store / "instincts" / state / f"{instinct_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    ev = "\n".join(f'  - "{e}"' for e in evidence)
    path.write_text(
        f"""---
id: {instinct_id}
status: {status or state}
trigger: "{trigger}"
domain: {domain}
scope: project
source: hand-authored
confidence: 0.7
evidence:
{ev}
created: {created}
last-confirmed: {last_confirmed}
---
# {instinct_id}

## Action
{action}
"""
    )
    return path


@pytest.fixture
def store(git_repo: Path) -> Path:
    """An empty learned store inside the scratch repo."""
    s = git_repo / ".vibe" / "learned"
    (s / "instincts" / "pending").mkdir(parents=True)
    (s / "instincts" / "approved").mkdir(parents=True)
    (s / "instincts" / "rejected").mkdir(parents=True)
    (s / "instincts" / "retired").mkdir(parents=True)
    (s / "session-data").mkdir(parents=True)
    return s


def run_hook(
    script: str,
    stdin_obj: dict,
    *,
    cwd: Path,
    env: dict | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """Run a hook script exactly as the harness would: JSON on stdin."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(HOOK_DIR / script)],
        input=json.dumps(stdin_obj),
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
