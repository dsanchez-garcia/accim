"""Tests for accim.utils.WorkspaceArtifactCleaner, which lists and deletes the files that a workflow generates.

The cleaner compares the files of the workspace with a snapshot taken by capture_initial_state(). It took an
empty snapshot (an empty workspace) as no snapshot, so it could not be used in an empty folder ("Initial state
not captured"). Ported from the tests of the branches refactor/sim-v1 and review/refactor-sim-v1-20261024.
"""
import pytest

from accim.utils import WorkspaceArtifactCleaner


def test_the_snapshot_is_required_even_when_the_workspace_is_empty(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)

    with pytest.raises(RuntimeError, match='Initial state not captured'):
        cleaner.get_generated_files()


def test_an_empty_snapshot_detects_and_deletes_the_generated_files(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    assert cleaner.capture_initial_state() == []
    assert cleaner.get_generated_files() == []
    generated = tmp_path / 'output.csv'
    generated.write_text('value\n1\n', encoding='utf-8')

    assert cleaner.get_generated_files() == ['output.csv']
    assert cleaner.delete_generated_files() == ['output.csv']
    assert generated.is_file(), 'a dry run must not delete files'
    assert cleaner.delete_generated_files(dry_run=False) == ['output.csv']
    assert not generated.exists()
    assert cleaner.get_generated_files() == []


def test_the_files_of_the_snapshot_are_kept_and_deny_patterns_override_allow_patterns(tmp_path):
    baseline = tmp_path / 'original.csv'
    baseline.write_text('original', encoding='utf-8')
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    assert cleaner.capture_initial_state() == ['original.csv']
    for name in ('output.csv', 'keep.csv'):
        (tmp_path / name).write_text(name, encoding='utf-8')

    with pytest.warns(UserWarning, match='not selected for deletion'):
        deleted = cleaner.delete_generated_files(allow_patterns=['*.csv'], deny_patterns=['keep.csv'], dry_run=False)

    assert deleted == ['output.csv']
    assert baseline.read_text(encoding='utf-8') == 'original'
    assert (tmp_path / 'keep.csv').is_file()


def test_a_new_snapshot_can_be_empty(tmp_path):
    old = tmp_path / 'old.txt'
    old.write_text('old', encoding='utf-8')
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    cleaner.capture_initial_state()
    old.unlink()

    assert cleaner.capture_initial_state() == []
    assert cleaner.get_generated_files() == []
