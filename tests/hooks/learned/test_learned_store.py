"""Unit tests for hooks/learned/lib/learned_store.py.

Covers store resolution (worktree-shared, non-git fallback), the flat-YAML
frontmatter parser + instinct validation, and atomic writes. Backup tests
live at the bottom (US3). Process-level hook tests live in the
test_load_/test_capture_ modules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import learned_store as ls
from conftest import FIXTURE_DIR, make_instinct


# --- Store resolution (contracts/store-layout.md, research.md D6) -----------


class TestResolveStore:
    def test_main_checkout(self, git_repo):
        store, notice = ls.resolve_store(git_repo)
        assert store == git_repo / ".vibe" / "learned"
        assert notice is None

    def test_subdirectory_resolves_to_repo_root(self, git_repo):
        sub = git_repo / "src" / "deep"
        sub.mkdir(parents=True)
        store, _ = ls.resolve_store(sub)
        assert store == git_repo / ".vibe" / "learned"

    def test_worktree_shares_main_store(self, git_repo, worktree):
        """FR-010: a worktree under .vibe/worktrees/ must NOT get its own store."""
        store, notice = ls.resolve_store(worktree)
        assert store == git_repo / ".vibe" / "learned"
        assert notice is None

    def test_non_git_fallback_with_notice(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        store, notice = ls.resolve_store(plain)
        assert store == plain / ".vibe" / "learned"
        assert notice is not None and "non-git fallback" in notice

    def test_resolution_never_creates_directories(self, git_repo):
        store, _ = ls.resolve_store(git_repo)
        assert not store.exists()


# --- Frontmatter parsing + validation (contracts/instinct-file.md) ----------


class TestParseInstinct:
    def test_canonical_fixture_parses(self, tmp_path):
        path = tmp_path / "prefer-named-exports.md"
        path.write_text((FIXTURE_DIR / "instinct-valid-canonical.md").read_text())
        inst = ls.load_instinct(path)
        f = inst["fields"]
        assert f["id"] == "prefer-named-exports"
        assert f["trigger"] == "when creating a new TypeScript module"
        assert f["confidence"] == pytest.approx(0.7)
        assert len(f["evidence"]) == 2
        assert f["sessions"] == ["3f2a"]
        assert "named exports" in inst["action"]

    def test_round_trip(self, tmp_path):
        fields = {
            "id": "round-trip-check",
            "status": "pending",
            "trigger": "when round-tripping",
            "domain": "testing",
            "scope": "project",
            "source": "session-extraction",
            "confidence": 0.5,
            "evidence": ["2026-07-23 session t9: evidence one"],
            "created": "2026-07-23",
            "last-confirmed": "2026-07-23",
        }
        text = ls.render_instinct(fields, "Always round-trip cleanly.")
        path = tmp_path / "round-trip-check.md"
        path.write_text(text)
        inst = ls.load_instinct(path)
        assert inst["fields"]["id"] == fields["id"]
        assert inst["fields"]["evidence"] == fields["evidence"]
        assert inst["fields"]["confidence"] == pytest.approx(0.5)
        assert inst["action"] == "Always round-trip cleanly."

    @pytest.mark.parametrize(
        "fixture, defect",
        [
            ("instinct-malformed-missing-field.md", "trigger"),
            ("instinct-malformed-bad-yaml.md", "yaml"),
            ("instinct-malformed-empty-action.md", "action"),
        ],
    )
    def test_malformed_fixtures_rejected_with_reason(self, tmp_path, fixture, defect):
        src = FIXTURE_DIR / fixture
        # keep filename == id so the mismatch check doesn't mask the real defect
        text = src.read_text()
        stem = next(
            line.split(":", 1)[1].strip()
            for line in text.splitlines()
            if line.startswith("id:")
        )
        path = tmp_path / f"{stem}.md"
        path.write_text(text)
        with pytest.raises(ls.MalformedInstinct) as exc:
            ls.load_instinct(path)
        assert defect.lower() in str(exc.value).lower()

    def test_filename_id_mismatch_is_malformed(self, tmp_path):
        path = tmp_path / "other-name.md"
        path.write_text((FIXTURE_DIR / "instinct-valid-canonical.md").read_text())
        with pytest.raises(ls.MalformedInstinct):
            ls.load_instinct(path)

    def test_oversize_file_is_malformed(self, tmp_path, git_repo):
        store = git_repo / ".vibe" / "learned"
        path = make_instinct(store, "approved", "huge-essay", action="x" * 11_000)
        with pytest.raises(ls.MalformedInstinct) as exc:
            ls.load_instinct(path)
        assert "10" in str(exc.value)  # names the size guard

    def test_bad_id_shape_is_malformed(self, tmp_path, git_repo):
        store = git_repo / ".vibe" / "learned"
        path = make_instinct(store, "pending", "ab")  # under 3 chars
        with pytest.raises(ls.MalformedInstinct):
            ls.load_instinct(path)

    def test_confidence_out_of_range_is_malformed(self, tmp_path):
        text = (FIXTURE_DIR / "instinct-valid-canonical.md").read_text().replace(
            "confidence: 0.7", "confidence: 1.7"
        )
        path = tmp_path / "prefer-named-exports.md"
        path.write_text(text)
        with pytest.raises(ls.MalformedInstinct):
            ls.load_instinct(path)


# --- Atomic writes (contracts/store-layout.md Concurrency) ------------------


# --- Backup (US3 — contracts/store-layout.md, research.md D7) ---------------


class TestBackup:
    def test_project_id_from_normalized_remote(self, git_repo):
        import hashlib
        import subprocess

        subprocess.run(
            ["git", "remote", "add", "origin",
             "https://EXample.com/Org/Repo.git"],
            cwd=git_repo, check=True,
        )
        expected = hashlib.sha256(
            b"https://example.com/org/repo").hexdigest()[:12]
        assert ls.project_id(git_repo) == expected

    def test_project_id_path_fallback_without_remote(self, git_repo):
        import hashlib

        expected = hashlib.sha256(
            str(git_repo.resolve()).encode()).hexdigest()[:12]
        assert ls.project_id(git_repo) == expected

    def test_backup_mirrors_approved_and_retired(
        self, git_repo, store, monkeypatch, tmp_path
    ):
        backup_root = tmp_path / "xdg-data"
        monkeypatch.setenv("XDG_DATA_HOME", str(backup_root))
        make_instinct(store, "approved", "approved-to-mirror")
        make_instinct(store, "retired", "retired-to-mirror", status="retired")
        make_instinct(store, "pending", "pending-not-mirrored")
        dest = ls.backup_store(store)
        assert (dest / "instincts" / "approved" / "approved-to-mirror.md").exists()
        assert (dest / "instincts" / "retired" / "retired-to-mirror.md").exists()
        # pending is expendable by spec assumption — never mirrored
        assert not (dest / "instincts" / "pending").exists()
        assert dest.is_relative_to(backup_root / "vibe" / "backup")

    def test_backup_is_append_favoring(
        self, git_repo, store, monkeypatch, tmp_path
    ):
        """Store deletions must NOT propagate — recovery beats symmetry."""
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
        path = make_instinct(store, "approved", "kept-in-backup")
        dest = ls.backup_store(store)
        path.unlink()
        ls.backup_store(store)
        assert (dest / "instincts" / "approved" / "kept-in-backup.md").exists()

    def test_cli_backup_and_check(self, git_repo, store, tmp_path):
        import subprocess
        import sys

        make_instinct(store, "approved", "cli-mirrored-lesson")
        # a status/directory mismatch `check` must warn about, never silently fix
        make_instinct(store, "pending", "claims-approved", status="approved")
        env = dict(**__import__("os").environ,
                   XDG_DATA_HOME=str(tmp_path / "xdg-data"))
        lib = Path(ls.__file__)
        backup = subprocess.run(
            [sys.executable, str(lib), "backup"], cwd=git_repo,
            capture_output=True, text=True, env=env,
        )
        assert backup.returncode == 0
        assert "1 file" in backup.stdout
        check = subprocess.run(
            [sys.executable, str(lib), "check"], cwd=git_repo,
            capture_output=True, text=True, env=env,
        )
        assert check.returncode == 0
        assert "claims-approved" in check.stdout
        assert "mismatch" in check.stdout


class TestAtomicWrite:
    def test_creates_parents_and_writes(self, tmp_path):
        target = tmp_path / "a" / "b" / "file.md"
        ls.atomic_write(target, "content\n")
        assert target.read_text() == "content\n"

    def test_no_tmp_leftover(self, tmp_path):
        target = tmp_path / "file.md"
        ls.atomic_write(target, "x")
        leftovers = [p for p in tmp_path.iterdir() if p.name != "file.md"]
        assert leftovers == []

    def test_overwrites_existing(self, tmp_path):
        target = tmp_path / "file.md"
        target.write_text("old")
        ls.atomic_write(target, "new")
        assert target.read_text() == "new"

    def test_list_state_tolerates_missing_dir(self, tmp_path):
        assert ls.list_state(tmp_path / "nope", "approved") == []
