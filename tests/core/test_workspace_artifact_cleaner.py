"""Safety regressions adapted from the historical sim-v1 utility tests."""

import pytest

from accim.utils import WorkspaceArtifactCleaner


def test_capture_is_required_even_when_workspace_is_empty(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    with pytest.raises(RuntimeError, match='Initial state not captured'):
        cleaner.get_generated_files()


def test_empty_snapshot_can_detect_and_delete_generated_files(tmp_path):
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    assert cleaner.capture_initial_state() == []
    assert cleaner.get_generated_files() == []
    generated = tmp_path / 'output.csv'
    generated.write_text('value\n1\n', encoding='utf-8')

    assert cleaner.get_generated_files() == ['output.csv']
    assert cleaner.delete_generated_files() == ['output.csv']
    assert generated.is_file(), 'Dry-run must not delete artifacts.'
    assert cleaner.delete_generated_files(dry_run=False) == ['output.csv']
    assert not generated.exists()
    assert cleaner.get_generated_files() == []


def test_cleanup_preserves_baseline_and_deny_overrides_allow(tmp_path):
    baseline = tmp_path / 'original.csv'
    baseline.write_text('original', encoding='utf-8')
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    assert cleaner.capture_initial_state() == ['original.csv']
    for name in ('output.csv', 'keep.csv'):
        (tmp_path / name).write_text(name, encoding='utf-8')

    with pytest.warns(UserWarning, match='not selected for deletion'):
        deleted = cleaner.delete_generated_files(
            allow_patterns=['*.csv'], deny_patterns=['keep.csv'], dry_run=False,
        )
    assert deleted == ['output.csv']
    assert baseline.read_text(encoding='utf-8') == 'original'
    assert (tmp_path / 'keep.csv').is_file()


def test_recapture_can_replace_nonempty_snapshot_with_empty_one(tmp_path):
    baseline = tmp_path / 'old.txt'
    baseline.write_text('old', encoding='utf-8')
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    cleaner.capture_initial_state()
    baseline.unlink()
    assert cleaner.capture_initial_state() == []
    assert cleaner.get_generated_files() == []

