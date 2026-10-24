"""The optional benchmark's checks must not require an EnergyPlus installation."""

import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

BENCHMARK = runpy.run_path(str(Path(__file__).resolve().parents[2] / 'benchmarks' / 'energyplus_api.py'))
compare_csv = BENCHMARK['compare_csv']
run_case = BENCHMARK['run_case']
benchmark = BENCHMARK['benchmark']


def test_csv_comparison_checks_all_rows_and_numeric_values(tmp_path):
    reference = tmp_path / 'reference.csv'
    actual = tmp_path / 'actual.csv'
    reference.write_text('Date/Time,Power\n01/01 01:00,1\n01/01 02:00,2\n', encoding='utf-8')
    actual.write_text('Date/Time,Power\n01/01 01:00,1.0\n01/01 02:00,2.00000000001\n', encoding='utf-8')
    assert compare_csv(reference, actual) == {'rows': 2, 'numeric_cells': 2}
    actual.write_text('Date/Time,Power\n01/01 01:00,1\n01/01 02:00,3\n', encoding='utf-8')
    with pytest.raises(ValueError, match='values differ at row 3'):
        compare_csv(reference, actual)


@pytest.mark.parametrize('content', [
    '', 'Date/Time,Other\n01/01 01:00,1\n', 'Date/Time,Power\n',
    'Date/Time,Power\n01/01 01:00,nan\n', 'Date/Time,Power\n01/01 01:00,inf\n',
    'Date/Time,Power\n01/01 01:00,1\n01/01 02:00,2\n',
])
def test_csv_comparison_rejects_missing_nonfinite_or_different_data(tmp_path, content):
    reference = tmp_path / 'reference.csv'
    actual = tmp_path / 'actual.csv'
    reference.write_text('Date/Time,Power\n01/01 01:00,1\n', encoding='utf-8')
    actual.write_text(content, encoding='utf-8')
    with pytest.raises(ValueError):
        compare_csv(reference, actual)


def test_api_state_is_deleted_and_working_directory_restored_on_failure(tmp_path):
    calls = []
    original_cwd = Path.cwd()
    state = object()

    def fail(active_state, args):
        assert active_state is state
        assert Path.cwd() == tmp_path
        raise RuntimeError('simulated engine failure')

    api = SimpleNamespace(
        state_manager=SimpleNamespace(new_state=lambda: state, delete_state=calls.append),
        runtime=SimpleNamespace(set_console_output_status=lambda *args: None, run_energyplus=fail),
    )
    with pytest.raises(RuntimeError, match='simulated engine failure'):
        run_case('api', api, Path('unused'), [], tmp_path)
    assert calls == [state]
    assert Path.cwd() == original_cwd


def test_benchmark_never_reuses_or_deletes_an_existing_directory(tmp_path):
    home = tmp_path / 'engine'
    (home / 'pyenergyplus').mkdir(parents=True)
    for filename in ('energyplus', 'energyplus.exe', 'pyenergyplus/api.py'):
        (home / filename).touch()
    idf = tmp_path / 'model.idf'
    epw = tmp_path / 'weather.epw'
    idf.touch()
    epw.touch()
    output = tmp_path / 'existing'
    output.mkdir()
    sentinel = output / 'do-not-delete.txt'
    sentinel.write_text('preserve', encoding='utf-8')
    with pytest.raises(FileExistsError):
        benchmark(home, idf, epw, output)
    assert sentinel.read_text(encoding='utf-8') == 'preserve'

