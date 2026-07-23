"""Process-level tests for hooks/learned/capture-learned-context.py.

The extraction LLM is stubbed via VIBE_LEARNED_CLAUDE_CMD (research.md D12),
so everything here is hermetic. test_no_secrets_at_rest is this feature's
SC-006 proof: never weaken it.
"""

from __future__ import annotations

import datetime
import re

from conftest import FIXTURE_DIR, make_instinct, run_hook

STUB = str(FIXTURE_DIR / "stub-claude.sh")
STUB_GARBAGE = str(FIXTURE_DIR / "stub-claude-garbage.sh")
STUB_SLOW = str(FIXTURE_DIR / "stub-claude-slow.sh")
TRANSCRIPT = str(FIXTURE_DIR / "transcript-with-corrections.jsonl")
TRANSCRIPT_TRIVIAL = str(FIXTURE_DIR / "transcript-trivial.jsonl")

TODAY = datetime.date.today().isoformat()

# secret shapes the default stub payload plants (see stub-claude.sh)
PLANTED_SECRETS = re.compile(r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}")


def capture(cwd, *, transcript=TRANSCRIPT, stub=STUB, session_id="t2",
            env=None, timeout=60):
    full_env = {"VIBE_LEARNED_CLAUDE_CMD": stub}
    if env:
        full_env.update(env)
    return run_hook(
        "capture-learned-context.py",
        {"session_id": session_id, "cwd": str(cwd),
         "transcript_path": transcript, "reason": "other"},
        cwd=cwd, env=full_env, timeout=timeout,
    )


def store_snapshot(store) -> dict:
    return {
        str(p.relative_to(store)): p.read_bytes()
        for p in sorted(store.rglob("*")) if p.is_file()
    }


class TestSummaryAndCandidates:
    def test_summary_written_with_frontmatter(self, git_repo, store):
        result = capture(git_repo)
        assert result.returncode == 0
        summaries = list((store / "session-data").iterdir())
        assert len(summaries) == 1
        assert summaries[0].name == f"{TODAY}-t2.md"
        text = summaries[0].read_text()
        assert "session-id: t2" in text
        assert "Worked on the demo feature" in text

    def test_candidates_land_in_pending_only(self, git_repo, store):
        before_approved = store_snapshot(store / "instincts" / "approved"
                                         ) if (store / "instincts" / "approved").exists() else {}
        result = capture(git_repo)
        assert result.returncode == 0
        pending = [p.name for p in (store / "instincts" / "pending").iterdir()]
        assert "prefer-batch-writes.md" in pending
        after_approved = store_snapshot(store / "instincts" / "approved")
        assert after_approved == before_approved  # FR-003: never writes approved
        assert "pending review" in result.stdout  # one-line human status

    def test_created_pending_file_is_valid_instinct(self, git_repo, store):
        capture(git_repo)
        import learned_store as ls
        inst = ls.load_instinct(
            store / "instincts" / "pending" / "prefer-batch-writes.md"
        )
        f = inst["fields"]
        assert f["status"] == "pending"
        assert f["source"] == "session-extraction"
        assert f["created"] == TODAY
        assert len(f["evidence"]) == 2
        assert f["confidence"] == 0.5  # 2 evidence items → 0.5 heuristic

    def test_trivial_transcript_writes_nothing(self, git_repo, store):
        result = capture(git_repo, transcript=TRANSCRIPT_TRIVIAL)
        assert result.returncode == 0
        assert list((store / "session-data").iterdir()) == []
        assert list((store / "instincts" / "pending").iterdir()) == []
        assert result.stdout == ""


class TestDedup:
    def test_existing_id_in_any_state_blocks_candidate(self, git_repo, store):
        """FR-007: the rejected archive prevents re-proposal."""
        make_instinct(store, "rejected", "existing-lesson")
        capture(git_repo)
        pending = [p.name for p in (store / "instincts" / "pending").iterdir()]
        assert "existing-lesson.md" not in pending
        assert "prefer-batch-writes.md" in pending


class TestSecrets:
    def test_no_secrets_at_rest(self, git_repo, store):
        """SC-006: planted secret shapes never appear in any written file."""
        capture(git_repo)
        for path in store.rglob("*.md"):
            assert not PLANTED_SECRETS.search(path.read_text()), path
        # the scrub is a redaction, not a drop: the evidence line survives
        pending = store / "instincts" / "pending" / "prefer-batch-writes.md"
        assert "REDACTED" in pending.read_text()


class TestExclusion:
    def test_info_exclude_gains_vibe_idempotently(self, git_repo, store):
        capture(git_repo)
        exclude = git_repo / ".git" / "info" / "exclude"
        lines = exclude.read_text().splitlines()
        assert lines.count(".vibe/") == 1
        capture(git_repo)  # second run must not duplicate the entry
        lines = exclude.read_text().splitlines()
        assert lines.count(".vibe/") == 1

    def test_git_check_ignore_honors_exclusion(self, git_repo, store):
        import subprocess
        capture(git_repo)
        proc = subprocess.run(
            ["git", "check-ignore", ".vibe"], cwd=git_repo,
            capture_output=True, text=True,
        )
        assert proc.returncode == 0


class TestPrune:
    def test_stale_pending_pruned_other_states_untouched(self, git_repo, store):
        old = (datetime.date.today() - datetime.timedelta(days=31)).isoformat()
        make_instinct(store, "pending", "stale-candidate", created=old)
        make_instinct(store, "pending", "fresh-candidate", created=TODAY)
        make_instinct(store, "rejected", "old-rejected", created=old)
        make_instinct(store, "retired", "old-retired", created=old,
                      status="retired")
        # retired requires evolved-into; patch it in
        retired = store / "instincts" / "retired" / "old-retired.md"
        retired.write_text(retired.read_text().replace(
            "last-confirmed:", "evolved-into: skills/x/SKILL.md\nlast-confirmed:"))
        result = capture(git_repo)
        pending = [p.name for p in (store / "instincts" / "pending").iterdir()]
        assert "stale-candidate.md" not in pending
        assert "fresh-candidate.md" in pending
        assert (store / "instincts" / "rejected" / "old-rejected.md").exists()
        assert retired.exists()
        assert "stale-candidate" in result.stderr  # pruning is reported

    def test_summaries_keep_newest_ten(self, git_repo, store):
        for i in range(12):
            (store / "session-data" / f"2026-06-{i + 1:02d}-s{i}.md").write_text(
                f"---\nsession-id: s{i}\ndate: 2026-06-{i + 1:02d}T10:00:00\n"
                f"cwd: /x\n---\nbody {i}\n"
            )
        capture(git_repo)
        kept = sorted(p.name for p in (store / "session-data").iterdir())
        # 12 old + 1 new = 13; prune keeps 10 newest of the 12 first, then
        # capture adds today's — oldest two must be gone
        assert "2026-06-01-s0.md" not in kept
        assert "2026-06-02-s1.md" not in kept
        assert len(kept) == 11  # 10 kept + today's new summary


class TestExtractionFailure:
    def test_garbage_output_skips_visibly(self, git_repo, store):
        before = store_snapshot(store)
        result = capture(git_repo, stub=STUB_GARBAGE)
        assert result.returncode == 0
        assert "extraction" in result.stderr.lower()
        assert store_snapshot(store) == before  # store untouched

    def test_timeout_skips_visibly(self, git_repo, store):
        before = store_snapshot(store)
        result = capture(
            git_repo, stub=STUB_SLOW,
            env={"VIBE_LEARNED_EXTRACT_TIMEOUT": "2"}, timeout=30,
        )
        assert result.returncode == 0
        assert "extraction" in result.stderr.lower()
        assert store_snapshot(store) == before

    def test_missing_transcript_exits_zero(self, git_repo, store):
        result = capture(git_repo, transcript="/nonexistent/t.jsonl")
        assert result.returncode == 0
