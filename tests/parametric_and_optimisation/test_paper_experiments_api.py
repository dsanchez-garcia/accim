"""Offline contracts for package-owned paper workflows; never run EnergyPlus."""

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from accim.parametric_and_optimisation import paper_experiments as workflow
from accim.parametric_and_optimisation.objectives import checked_sum_results


DELIVERY = Path(__file__).resolve().parents[2] / 'llm_project_files' / 'experimentos_preparados'


def specifications():
    values = {}
    for script in sorted(DELIVERY.glob('exp_*.py')):
        tree = ast.parse(script.read_text(encoding='utf-8-sig'))
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'EXPERIMENT' for t in node.targets))
        spec = ast.literal_eval(assignment.value)
        values[spec['number']] = spec
    return values


def test_five_entries_are_configuration_only_and_import_accim():
    scripts = sorted(DELIVERY.glob('exp_*.py'))
    assert len(scripts) == 5
    for script in scripts:
        tree = ast.parse(script.read_text(encoding='utf-8-sig'))
        assert not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda))
                       for node in ast.walk(tree))
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        assert any(node.module == 'accim.parametric_and_optimisation'
                   and any(alias.name == 'run_paper_experiment' for alias in node.names) for node in imports)
        assert not any((node.module or '').startswith(('exp_', 'article_objectives')) for node in imports)
        guards = [node for node in tree.body if isinstance(node, ast.If) and '__name__' in ast.unparse(node.test)]
        assert len(guards) == 1
        assert 'freeze_support' in ast.unparse(guards[0])
        assert 'run_paper_experiment' in ast.unparse(guards[0])


def test_parameter_domains_and_forecasts_remain_unchanged():
    specs = specifications()
    assert set(specs) == {'4.1', '4.2', '4.3', '4.4', '4.5'}
    assert [specs[n]['expected_runs'] for n in sorted(specs)] == [132, 300, 36, 400, 400]
    assert specs['4.1']['parameters'] == {
        'ComfStand': [1, 2, 3, 14, 16], 'CAT': [1, 2, 3, 80, 90], 'ComfMod': [0, 3], 'HVACmode': [0, 2],
    }
    assert specs['4.1']['ScriptType'] == 'vrf_mm'
    assert specs['4.2']['parameters'] == specs['4.4']['parameters'] == {
        'CustAST_m': (0.0, 0.7), 'CustAST_n': (5.0, 22.5),
        'CustAST_ASToffset': (1.0, 5.0), 'CustAST_ASTaul': (22.0, 40.0),
    }
    assert specs['4.2']['ScriptType'] == specs['4.4']['ScriptType'] == 'vrf_ac'
    assert specs['4.2']['sampling'] == 'lhs'
    assert specs['4.3']['parameters'] == {'Adaptive cooling coefficient': [0.0, 0.1, 0.3, 0.5], 'PMV setpoint': [0.2, 0.5, 0.7]}
    assert specs['4.5']['parameters'] == {'Adaptive cooling coefficient': (0.0, 1.0), 'Adaptive heating coefficient': (-1.0, 0.0), 'PMV setpoint': (0.2, 0.9)}
    assert all(len(specs[n]['epws']) == (3 if n < '4.4' else 2) for n in specs)
    assert workflow.POPULATION == 20 and workflow.EVALUATIONS == 200
    assert workflow.REDUCER == 'accim.parametric_and_optimisation.objectives:checked_sum_results'


@pytest.mark.parametrize('values', [[], [np.nan], [np.inf], [[1, 2]], ['not a number'], [1e308, 1e308]])
def test_strict_reducer_rejects_invalid_objectives(values):
    with pytest.raises(ValueError):
        checked_sum_results(SimpleNamespace(data={'Value': values}))


def test_strict_reducer_returns_one_finite_float():
    result = checked_sum_results(SimpleNamespace(data={'Value': [0.1, 0.2, 0.3]}))
    assert isinstance(result, float) and result == pytest.approx(0.6)
    with pytest.raises(ValueError):
        checked_sum_results(None)


def test_column_resolution_handles_units_and_rejects_ambiguity():
    frame = pd.DataFrame({'Electricity:HVAC_kWh/m2': [1.0]})
    assert workflow.resolve_column(frame, ['Electricity:HVAC']) == 'Electricity:HVAC_kWh/m2'
    frame['Electricity:HVAC [J]'] = 1.0
    with pytest.raises(ValueError, match='ambiguous'):
        workflow.resolve_column(frame, ['Electricity:HVAC'])


def test_dates_handle_24h_leap_days_and_storage_resolution():
    dates = workflow.energyplus_dates(['01/01 23:00:00', '01/01 24:00:00', '01/02 01:00:00'], annual=False)
    assert dates[1] == pd.Timestamp('2001-01-02 00:00')
    assert (dates[1:] - dates[:-1] == pd.Timedelta(hours=1)).all()
    leap = workflow.energyplus_dates(['02/28 24:00:00', '02/29 01:00:00'], annual=False)
    assert leap[0] == pd.Timestamp('2000-02-29')
    with pytest.raises(ValueError, match='leap'):
        workflow.energyplus_dates(['02/29 01:00:00'], annual=False, year=2001)
    with pytest.raises(ValueError, match='discontinuous'):
        workflow.energyplus_dates(['01/01 01:00:00', '01/01 03:00:00'], annual=False)


def test_csv_reader_checks_exact_key_frequency_units_and_duplicate_headers(tmp_path):
    csv_path = tmp_path / 'eplusout.csv'
    request = {'role': 'comfort', 'kind': 'variable', 'key': 'EMS', 'variable': 'Metric', 'units': 'C-hr'}
    csv_path.write_text('Date/Time,EMS:Metric [C-hr](Hourly),Other:Metric [C-hr](Hourly)\n01/01 01:00:00,0.4,2\n', encoding='utf-8')
    frame, columns = workflow.read_hourly(csv_path, [request], annual=False)
    assert frame['comfort'].tolist() == [0.4]
    assert columns['comfort'] == 'EMS:Metric [C-hr](Hourly)'
    csv_path.write_text('Date/Time,EMS:Metric [C-hr](Hourly),EMS:Metric [C-hr](Hourly)\n01/01 01:00:00,1,2\n', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate'):
        workflow.read_hourly(csv_path, [request], annual=False)


def test_load_path_is_relative_to_entry_not_package_or_cwd(monkeypatch, tmp_path):
    entry = tmp_path / 'entry'
    entry.mkdir()
    source = entry / 'chosen.csv'
    source.write_text('dummy trusted result', encoding='utf-8')
    settings = dict(script_directory=entry, idf=Path('inputs/model.idf'), epw_dir=Path('inputs'), results_root=Path('results'))
    spec = specifications()['4.2']
    sentinel = object()

    def forbidden(*args, **kwargs):
        raise AssertionError('Load must not prepare, discover, resume or simulate')

    def fake_load(spec_arg, args):
        assert args.result == source
        assert args.idf == entry / 'inputs/model.idf'
        return sentinel, pd.DataFrame({'energy': [1.0]}), 'energy', None

    monkeypatch.setattr(workflow, 'build_session', forbidden)
    monkeypatch.setattr(workflow, 'execute_campaign', forbidden)
    monkeypatch.setattr(workflow, 'run_discovery', forbidden)
    monkeypatch.setattr(workflow, 'load_results', fake_load)
    monkeypatch.setattr(workflow, 'annual_figures', lambda *a: None)
    monkeypatch.chdir(tmp_path)
    assert workflow.run_paper_experiment(spec, settings, ['load', '--result', 'chosen.csv']) is sentinel
    assert len(list((entry / 'results/exp_4_2/postprocess').glob('*/provenance.json'))) == 1


@pytest.mark.parametrize('action', ['discover', 'new', 'resume'])
def test_energyplus_actions_require_explicit_opt_in(monkeypatch, tmp_path, action):
    def forbidden(*args, **kwargs):
        raise AssertionError('Unauthorised preparation or simulation')

    monkeypatch.setattr(workflow, 'build_session', forbidden)
    settings = dict(script_directory=tmp_path, idf=Path('model.idf'), epw_dir=Path('.'), results_root=Path('results'))
    with pytest.raises(SystemExit) as exc:
        workflow.run_paper_experiment(specifications()['4.4'], settings, [action])
    assert exc.value.code == 2
    assert not (tmp_path / 'results').exists()


def test_legacy_relative_path_uses_explicit_original_working_directory(tmp_path):
    actual = tmp_path / 'archive' / 'campaign' / 'BESOS_Output' / 'case'
    actual.mkdir(parents=True)
    resolved = workflow.rebase_path('campaign/BESOS_Output/case',
                                    old_root='D:/old-work', new_root=tmp_path / 'archive',
                                    base='D:/old-work')
    assert resolved == actual
