"""Content identity, atomic persistence and OS locking without EnergyPlus runs."""

import copy
import functools
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pandas as pd
import pytest
from besos.objectives import MeterReader, VariableReader
from besos.parameters import FieldSelector, Parameter, RangeParameter
from besos.problem import EPProblem

from accim.parametric_and_optimisation import _checkpoint as ck
from accim.parametric_and_optimisation._execution import file_lock, owns_path, isolated_run
from accim.parametric_and_optimisation.main import ParametricSimulation


def reducer(results, factor=1):
    return results.data['Value'].sum() * factor


@pytest.fixture
def identity_inputs(tmp_path, monkeypatch):
    home = tmp_path / 'EnergyPlus'
    home.mkdir()
    for name in ['energyplus.exe', 'Energy+.idd', 'EnergyPlusAPI.dll']:
        (home / name).write_bytes(name.encode('ascii'))
    monkeypatch.setattr('besos.eplus_funcs.get_ep_path', lambda version: (str(home / 'energyplus.exe'), str(home)))
    model = tmp_path / 'model.idf'
    model.write_text('Version,9.6;\nBuilding,Example;\n', encoding='utf-8')
    weather = tmp_path / 'Test.epw'
    weather.write_text('weather original', encoding='utf-8')
    sim = ParametricSimulation()
    parameter = Parameter(
        selector=FieldSelector(class_name='Material', object_name='Wall', field_name='Thickness'),
        value_descriptors=RangeParameter(name='x', min_val=0.1, max_val=0.5),
    )
    objective = MeterReader(key_name='Electricity:Facility', name='energy', frequency='Hourly', func=reducer)
    sim.sim_outputs = [objective]
    sim.problem = EPProblem(inputs=[parameter], outputs=[objective],
                            constraints=[MeterReader(key_name='Gas:Facility', name='gas')], constraint_bounds=['<=100'])
    return sim, model, weather, home


def identity(sim, model, weather, **kwargs):
    return ck.evaluation_identity(sim, models={'model': str(model)}, epws=[str(weather)],
                                  options={'kind': 'parametric'}, **kwargs)


def test_same_identity_survives_fresh_objects_and_snapshot_paths(identity_inputs, tmp_path):
    sim, model, weather, _ = identity_inputs
    first = identity(sim, model, weather)
    copied = tmp_path / 'different_backup_name.idf'
    copied.write_bytes(model.read_bytes())
    assert identity(copy.deepcopy(sim), copied, weather) == first


@pytest.mark.parametrize('change', ['model', 'weather', 'engine', 'idd', 'library', 'domain', 'selector', 'frequency', 'reducer', 'direction', 'constraint', 'additional_output'])
def test_identity_detects_changed_evaluation(identity_inputs, change):
    sim, model, weather, home = identity_inputs
    first = identity(sim, model, weather)
    if change == 'model':
        model.write_text('Version,9.6;\nBuilding,Changed;\n', encoding='utf-8')
    elif change == 'weather':
        weather.write_text('weather changed', encoding='utf-8')
    elif change in ['engine', 'idd', 'library']:
        name = {'engine': 'energyplus.exe', 'idd': 'Energy+.idd', 'library': 'EnergyPlusAPI.dll'}[change]
        (home / name).write_bytes(b'changed')
    elif change == 'domain':
        sim.problem.parameters[0].value_descriptors[0].max = 0.9
    elif change == 'selector':
        sim.problem.parameters[0].selector.object_name = 'OtherWall'
    elif change == 'frequency':
        sim.problem.outputs[0].frequency = 'Daily'
    elif change == 'reducer':
        sim.problem.outputs[0]._process = functools.partial(reducer, factor=2)
    elif change == 'direction':
        sim.problem.minimize_outputs = [False]
    elif change == 'constraint':
        sim.problem.constraint_bounds = ['<=200']
    else:
        sim.problem.add_outputs = [VariableReader(key_value='Zone1', variable_name='Zone Mean Air Temperature', name='temperature')]
    assert identity(sim, model, weather) != first


def test_declared_external_file_is_hashed(identity_inputs, tmp_path):
    sim, model, weather, _ = identity_inputs
    schedule = tmp_path / 'schedule.txt'
    schedule.write_text('1', encoding='utf-8')
    first = identity(sim, model, weather, context={'schedule': schedule})
    schedule.write_text('2', encoding='utf-8')
    assert identity(sim, model, weather, context={'schedule': schedule}) != first


def test_closure_and_partial_arguments_are_part_of_identity():
    def make(scale):
        def local(value):
            return value * scale
        return local
    assert ck.Fingerprint().value(make(1)) != ck.Fingerprint().value(make(2))
    assert ck.Fingerprint().value(functools.partial(reducer, factor=1)) != ck.Fingerprint().value(functools.partial(reducer, factor=2))


def test_callable_objects_include_captured_behavior():
    def make(scale):
        class Reducer:
            def __call__(self, value):
                return value * scale
        return Reducer()
    assert ck.Fingerprint().value(make(1)) != ck.Fingerprint().value(make(2))


def test_notebook_cell_filenames_do_not_change_function_identity():
    scopes = []
    for filename in ['<ipython-input-1>', '<ipython-input-27>']:
        scope = {'__name__': 'synthetic_notebook'}
        exec(compile('def local(value):\n    return value * 2\n', filename, 'exec'), scope)
        scopes.append(scope)
    assert ck.Fingerprint().value(scopes[0]['local']) == ck.Fingerprint().value(scopes[1]['local'])


def test_redefined_notebook_helper_changes_callback_identity():
    scope = {'__name__': 'synthetic_notebook'}
    exec('def helper(value):\n    return value * 2\ndef reducer(value):\n    return helper(value)\n', scope)
    before = ck.Fingerprint().value(scope['reducer'])
    exec('def helper(value):\n    return value * 3\n', scope)
    assert ck.Fingerprint().value(scope['reducer']) != before


def test_empty_pythonplugin_classes_do_not_require_context(identity_inputs):
    sim, model, weather, _ = identity_inputs
    sim.buildings = [SimpleNamespace(idfobjects={'PYTHONPLUGIN:INSTANCE': []})]
    assert identity(sim, model, weather)


def test_default_parametric_checkpoint_lock_matches_explicit_path(tmp_path):
    sim = ParametricSimulation()
    checkpoint = sim._default_parametric_checkpoint_path(str(tmp_path))

    def run_parametric_simulation(self, out_dir, resume_from_checkpoint=False, accim_results_root=None):
        with pytest.raises(ValueError, match='Another execution'):
            with file_lock(checkpoint + '.lock'):
                pytest.fail('The actual checkpoint was not locked.')

    isolated_run(run_parametric_simulation)(sim, out_dir=str(tmp_path))


def test_unknown_identity_cannot_be_equated_to_another_unknown(identity_inputs):
    sim, model, weather, _ = identity_inputs
    with pytest.raises(ValueError, match='Unsupported checkpoint identity'):
        identity(sim, model, weather, context={'opaque': object()})
    with pytest.raises(ValueError, match='no model identity'):
        ck.evaluation_identity(sim, models={}, epws=[str(weather)], options={})


@pytest.mark.parametrize('payload', [pd.DataFrame({'x': [1]}), {'checkpoint_format': 'state_v2'}, {'checkpoint_format': 'future'}])
def test_legacy_and_unknown_checkpoint_formats_rejected(tmp_path, payload):
    path = tmp_path / 'checkpoint.pkl'
    pd.to_pickle(payload, path)
    original = path.read_bytes()
    for loader in [ck.load_parametric, ck.load_optimisation]:
        with pytest.raises(ValueError, match='legacy checkpoint format'):
            loader(path)
        assert path.read_bytes() == original


@pytest.mark.parametrize('failure', ['dump', 'replace'])
def test_atomic_failure_preserves_previous_checkpoint(tmp_path, monkeypatch, failure):
    path = tmp_path / 'checkpoint.pkl'
    ck.atomic_pickle({'old': True}, path)
    original = path.read_bytes()

    def fail(*args, **kwargs):
        if failure == 'dump':
            args[1].write(b'partial data')
        raise OSError('interrupted write')

    if failure == 'dump':
        monkeypatch.setattr(ck.pickle, 'dump', fail)
    else:
        monkeypatch.setattr(ck.os, 'replace', fail)
    with pytest.raises(OSError, match='interrupted write'):
        ck.atomic_pickle({'new': True}, path)
    assert path.read_bytes() == original
    assert not list(tmp_path.glob('*.tmp'))


def test_lock_rejects_another_process_then_releases(tmp_path):
    lock = tmp_path / 'run.lock'
    code = """
import sys
from accim.parametric_and_optimisation._execution import file_lock
try:
    with file_lock(sys.argv[1]):
        print('acquired')
except ValueError:
    print('blocked')
"""
    with file_lock(lock):
        blocked = subprocess.run([sys.executable, '-c', code, str(lock)], capture_output=True, text=True, timeout=90)
    acquired = subprocess.run([sys.executable, '-c', code, str(lock)], capture_output=True, text=True, timeout=90)
    assert blocked.returncode == acquired.returncode == 0, blocked.stderr + acquired.stderr
    assert blocked.stdout.strip() == 'blocked'
    assert acquired.stdout.strip() == 'acquired'


def test_backup_mapping_does_not_use_name_substrings(tmp_path):
    sim = ParametricSimulation()

    class Building:
        def __init__(self, name):
            self.idfname = name + '.idf'

        def savecopy(self, path):
            Path(path).write_text(self.idfname, encoding='utf-8')

    sim.buildings = [Building('Model_A_v2'), Building('Model_A')]
    sim._save_idf_backup(out_dir=str(tmp_path))
    first_paths = list(sim.idf_backup_path)
    sim._save_idf_backup(out_dir=str(tmp_path))
    assert not set(first_paths).intersection(sim.idf_backup_path)
    for identifier, path in sim._idf_backup_by_id.items():
        assert Path(path).read_text(encoding='utf-8') == identifier + '.idf'
    tasks = list(sim._iter_parametric_task_blueprints(
        grouped_dfs={'Model_A': pd.DataFrame({'x': [1]})}, epws=['Test.epw'], out_dir=str(tmp_path),
        problem_names_inputs=['x'], problem_names_outputs=['energy'], output_specs=[], add_output_specs=[],
        add_output_names=[], keep_dirs=False, keep_input=True,
    ))
    assert tasks[0]['worker_args'][0] == sim._idf_backup_by_id['Model_A']


def test_ownership_checks_path_boundaries_and_links(tmp_path):
    root = tmp_path / 'run'
    root.mkdir()
    other = tmp_path / 'run-other'
    other.mkdir()
    assert owns_path(root / 'case', root)
    assert not owns_path(other, root)
    link = root / 'external'
    try:
        link.symlink_to(other, target_is_directory=True)
    except OSError:
        pytest.skip('Creating symlinks is unavailable on this Windows installation.')
    assert not owns_path(link, root)
    assert not owns_path(link / 'file', root)



