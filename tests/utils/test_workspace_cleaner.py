"""Tests for accim.utils.WorkspaceArtifactCleaner."""

import pytest

from accim.utils import WorkspaceArtifactCleaner


def _touch(path, name):
    (path / name).write_text("x")


def test_capture_and_detect_generated(tmp_path):
    _touch(tmp_path, "keep.idf")
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    baseline = cleaner.capture_initial_state()
    assert baseline == ["keep.idf"]

    _touch(tmp_path, "a.tmp")
    _touch(tmp_path, "b.eso")
    generated = cleaner.get_generated_files()
    assert generated == ["a.tmp", "b.eso"]


def test_get_generated_requires_baseline(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    with pytest.raises(RuntimeError):
        cleaner.get_generated_files()


def test_delete_dry_run_keeps_files(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    cleaner.capture_initial_state()
    _touch(tmp_path, "a.tmp")
    planned = cleaner.delete_generated_files(dry_run=True)
    assert planned == ["a.tmp"]
    assert (tmp_path / "a.tmp").exists()  # dry run does not delete


def test_delete_with_allow_and_deny_patterns(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    cleaner.capture_initial_state()
    _touch(tmp_path, "junk.tmp")
    _touch(tmp_path, "result.eso")
    _touch(tmp_path, "keep.csv")

    # Only delete .tmp/.eso (allow), but never .csv (deny is moot here).
    deleted = cleaner.delete_generated_files(
        allow_patterns=["*.tmp", "*.eso"], deny_patterns=["*.csv"],
        dry_run=False,
    )
    assert sorted(deleted) == ["junk.tmp", "result.eso"]
    assert not (tmp_path / "junk.tmp").exists()
    assert not (tmp_path / "result.eso").exists()
    assert (tmp_path / "keep.csv").exists()


def test_missing_workspace_root_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        WorkspaceArtifactCleaner(tmp_path / "does_not_exist")
