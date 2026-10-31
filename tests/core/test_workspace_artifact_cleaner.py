"""Tests for accim.utils.WorkspaceArtifactCleaner, which lists and deletes the files that a workflow generates.

The cleaner compares the files of the workspace with a snapshot taken by capture_initial_state(). It took an
empty snapshot (an empty workspace) as no snapshot, so it could not be used in an empty folder ("Initial state
not captured"). Ported from the tests of the branches refactor/sim-v1 and review/refactor-sim-v1-20261024.

With remove_empty_dirs=True, delete_generated_files() also removed the empty folders inside the excluded and
hidden folders, which the cleaner does not walk: in a new git repository, .git/refs and .git/objects, without
which git no longer finds the repository. Now it only removes the empty folders that it walks.
"""
import pytest

from accim.utils import WorkspaceArtifactCleaner


def test_a_workspace_that_does_not_exist_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError, match='workspace_root does not exist'):
        WorkspaceArtifactCleaner(tmp_path / 'missing')


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


def test_allow_patterns_select_the_generated_files_to_delete(tmp_path):
    (tmp_path / 'model.idf').write_text('idf', encoding='utf-8')
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    assert cleaner.capture_initial_state() == ['model.idf']
    (tmp_path / 'results').mkdir()
    for name in ('junk.tmp', 'results/run.eso', 'keep.csv'):
        (tmp_path / name).write_text(name, encoding='utf-8')

    assert cleaner.get_generated_files() == ['junk.tmp', 'keep.csv', 'results/run.eso']
    with pytest.warns(UserWarning, match='Count: 1'):
        deleted = cleaner.delete_generated_files(allow_patterns=['*.tmp', '*.eso'], dry_run=False)

    assert deleted == ['junk.tmp', 'results/run.eso']
    assert cleaner.generated_files_not_selected_for_deletion == ['keep.csv']
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*')) == [
        'keep.csv', 'model.idf', 'results']


def test_excluded_and_hidden_folders_are_neither_tracked_nor_removed(tmp_path):
    # A new git repository has empty folders such as .git/refs/tags and .git/objects/info
    protected = ['.git/refs/tags', '.git/objects/info', 'venv/Include', '__pycache__', '.cache/empty']
    for folder in protected:
        (tmp_path / folder).mkdir(parents=True)
    cleaner = WorkspaceArtifactCleaner(tmp_path)
    assert cleaner.capture_initial_state() == []
    (tmp_path / 'results' / 'zone1').mkdir(parents=True)
    for name in ('results/zone1/output.csv', '.git/index', 'venv/new.py', '.hidden.txt'):
        (tmp_path / name).write_text(name, encoding='utf-8')

    assert cleaner.get_generated_files() == ['results/zone1/output.csv']
    assert cleaner.delete_generated_files(dry_run=False, remove_empty_dirs=True) == ['results/zone1/output.csv']

    assert not (tmp_path / 'results').exists()
    for folder in protected:
        assert (tmp_path / folder).is_dir(), f'{folder} was removed'
    for name in ('.git/index', 'venv/new.py', '.hidden.txt'):
        assert (tmp_path / name).is_file()
