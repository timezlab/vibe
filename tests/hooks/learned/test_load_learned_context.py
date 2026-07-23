"""Process-level tests for hooks/learned/load-learned-context.py.

Each test pipes SessionStart stdin JSON to the real script and asserts on
stdout/stderr/exit — the same interface the harness uses (research.md D12).
The gate test is this feature's constitution-III proof: never weaken it.
"""

from __future__ import annotations

from conftest import make_instinct, run_hook


def load(cwd, session_id="t1", source="startup"):
    return run_hook(
        "load-learned-context.py",
        {"session_id": session_id, "cwd": str(cwd), "source": source},
        cwd=cwd,
    )


def write_summary(store, name, body):
    path = store / "session-data" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nsession-id: {name}\ndate: 2026-07-22T10:00:00\ncwd: /x\n---\n{body}\n"
    )


class TestGate:
    def test_gate_never_loads_pending_or_rejected(self, git_repo, store):
        """SC-002: pending/rejected/retired content NEVER reaches stdout."""
        make_instinct(store, "approved", "approved-lesson-marker")
        make_instinct(store, "pending", "pending-secret-marker")
        make_instinct(store, "rejected", "rejected-secret-marker")
        make_instinct(
            store, "retired", "retired-secret-marker", status="approved"
        )  # even a file *claiming* approved status: directory is authoritative
        result = load(git_repo)
        assert result.returncode == 0
        assert "approved-lesson-marker" in result.stdout
        for marker in ("pending-secret-marker", "rejected-secret-marker",
                       "retired-secret-marker"):
            assert marker not in result.stdout

    def test_loader_is_read_only(self, git_repo):
        # no store at all: loading must not create one
        result = load(git_repo)
        assert result.returncode == 0
        assert not (git_repo / ".vibe").exists()


class TestBlockFormat:
    def test_header_and_line_format(self, git_repo, store):
        make_instinct(
            store, "approved", "run-the-linter",
            trigger="when finishing an edit", domain="workflow",
            action="Run the linter before declaring done.",
        )
        result = load(git_repo)
        assert "# Learned context (1 approved instinct" in result.stdout
        assert "human-reviewed" in result.stdout
        assert (
            "- [workflow] when finishing an edit → Run the linter before "
            "declaring done." in result.stdout
        )

    def test_ordering_last_confirmed_descending(self, git_repo, store):
        make_instinct(store, "approved", "older-lesson", last_confirmed="2026-01-01")
        make_instinct(store, "approved", "newer-lesson", last_confirmed="2026-07-01")
        out = load(git_repo).stdout
        assert out.index("newer-lesson") < out.index("older-lesson")

    def test_latest_summary_only(self, git_repo, store):
        write_summary(store, "2026-07-20-old.md", "OLD-SUMMARY-BODY")
        write_summary(store, "2026-07-22-new.md", "NEW-SUMMARY-BODY")
        make_instinct(store, "approved", "some-lesson")
        out = load(git_repo).stdout
        assert "NEW-SUMMARY-BODY" in out
        assert "OLD-SUMMARY-BODY" not in out
        assert "## Previous session (2026-07-22)" in out


class TestBudget:
    def test_budget_caps_and_states_truncation(self, git_repo, store):
        """SC-003: 30 approved ⇒ ≤ 20 loaded, explicit 'and N more' line."""
        for i in range(30):
            make_instinct(
                store, "approved", f"lesson-number-{i:02d}",
                last_confirmed=f"2026-06-{(i % 28) + 1:02d}",
            )
        result = load(git_repo)
        out = result.stdout
        instinct_lines = [l for l in out.splitlines() if l.startswith("- [")]
        assert len(instinct_lines) <= 20
        assert "and 10 more approved instincts" in out
        assert len(out.splitlines()) <= 200
        assert len(out.encode()) <= 25 * 1024

    def test_block_never_exceeds_line_cap_with_huge_actions(self, git_repo, store):
        for i in range(20):
            make_instinct(
                store, "approved", f"wordy-lesson-{i:02d}",
                action=("Very long action sentence that goes on. " * 40),
            )
        out = load(git_repo).stdout
        assert len(out.splitlines()) <= 200
        assert len(out.encode()) <= 25 * 1024


class TestResilience:
    def test_empty_store_prints_nothing(self, git_repo, store):
        result = load(git_repo)
        assert result.returncode == 0
        assert result.stdout == ""

    def test_absent_store_prints_nothing(self, git_repo):
        result = load(git_repo)
        assert result.returncode == 0
        assert result.stdout == ""

    def test_malformed_approved_skipped_with_warning(self, git_repo, store):
        """SC-007: corruption never breaks session start."""
        make_instinct(store, "approved", "good-lesson")
        bad = store / "instincts" / "approved" / "corrupted.md"
        bad.write_text("garbage without frontmatter")
        result = load(git_repo)
        assert result.returncode == 0
        assert "good-lesson" in result.stdout
        assert "corrupted.md" in result.stderr
        assert "corrupted" not in result.stdout

    def test_garbage_stdin_still_exits_zero(self, git_repo):
        import subprocess
        import sys
        from conftest import HOOK_DIR

        result = subprocess.run(
            [sys.executable, str(HOOK_DIR / "load-learned-context.py")],
            input="not json at all", cwd=git_repo,
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0


class TestWorktree:
    def test_worktree_loads_identical_block(self, git_repo, worktree, store):
        """FR-010: worktree sessions share the main checkout's store."""
        make_instinct(store, "approved", "shared-lesson")
        main_out = load(git_repo).stdout
        wt_out = load(worktree).stdout
        assert "shared-lesson" in wt_out
        assert wt_out == main_out
