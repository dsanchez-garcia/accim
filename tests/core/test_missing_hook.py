"""Tests for the models prepared for the setpoints of a hook that are simulated without it (finding A4 of the
self-audit of 2026-11-11, decided on 2026-11-12, ``notes/decisions.md``).

:func:`accim.sim.comfort_hooks.apply_athb_setpoints`, ``apply_set_setpoints`` and ``apply_sun2026_setpoints`` give a
model the programs ``ApplyHookSetpoints_<zone>`` (:mod:`accim.sim.ems.hook_setpoints`), with which a hook of the backend
of the Python API of EnergyPlus gives its setpoints to the ACCIS. Without the hook, the model runs with the setpoints of
the comfort standard of its zones, and the outputs of the hook are 0: before, without an error or a warning. Now
``run_ep`` raises a ValueError with the EMS backend, which cannot run a hook, and the backend of the API warns
(:class:`accim.sim.ems.hook_setpoints.MissingHookWarning`) when the model gets no hook before its EMS programs.
``tests/core/test_sun2026_set.py`` simulates such a model with EnergyPlus.
"""
import shutil
import warnings
from pathlib import Path

import pytest

from accim.energyplus import default_energyplus_folder
from accim.sim.ems import hook_setpoints as hs

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']


def _models(folder):
    """A folder with two models with the ACCIS: 'plain[x.idf', and 'hooked[x.idf', prepared for the setpoints of a hook
    (the EMS objects that the functions of accim.sim.comfort_hooks add), and a weather file."""
    from accim.sim.accis import add_accis_to_idf, load_idf

    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'model.idf')
    idf = load_idf(folder / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    idf.saveas(str(folder / 'plain[x.idf'))
    hs.set_hook_setpoints_code(idf, ZONES)
    idf.saveas(str(folder / 'hooked[x.idf'))
    (folder / 'model.idf').unlink()
    shutil.copy(EPW, folder / 'Seville.epw')
    return folder / 'plain[x.idf', folder / 'hooked[x.idf'


def test_the_message_names_the_models_and_the_backend_of_the_api():
    ems = hs.missing_hook_message(['a.idf', 'b.idf'], 'ems')
    assert 'which the EMS backend cannot run: a.idf, b.idf.' in ems
    api = hs.missing_hook_message(['a.idf'], 'api')
    assert 'no hook runs before their EMS programs: a.idf.' in api and 'before_programs' in api
    for message in (ems, api):
        assert 'ApplyHookSetpoints_<zone>' in message and 'apply_sun2026_setpoints' in message
        assert "run_ep(backend='api', hooks=[hook])" in message
        assert 'the outputs of the hook at 0' in message
    assert issubclass(hs.MissingHookWarning, UserWarning)


@needs_idd
def test_the_zones_of_the_hook_of_an_idf_file(tmp_path):
    from accim.sim.accis import load_idf

    plain, hooked = _models(tmp_path)
    assert hs.hook_zones_of_file(plain) == []
    # As those of the model that eppy reads
    assert hs.hook_zones_of_file(hooked) == hs.hook_zones(load_idf(hooked)) == ZONES
    assert hs.hook_zones_of_file(tmp_path / 'missing.idf') == []
    # Whatever the layout of the file: one line, capitals, spaces, and comments (the names of the EMS programs have
    # no spaces); not the programs that run them, nor the objects in comments
    text = ('ENERGYMANAGEMENTSYSTEM:PROGRAM,ApplyHookSetpoints_Zone_A,if x == 1,set y = 2,endif;\n'
            '  EnergyManagementSystem:Program ,\n    applyhooksetpoints_Zone_B ,  !- Name\n    set y = 2;\n'
            '! EnergyManagementSystem:Program, ApplyHookSetpoints_Comment, set y = 2;\n'
            'EnergyManagementSystem:Program, RunACCIS_Zone_A, run ApplyHookSetpoints_Zone_A;\n')
    (tmp_path / 'text.idf').write_text(text, encoding='utf-8')
    assert hs.hook_zones_of_file(tmp_path / 'text.idf') == ['Zone_A', 'Zone_B']


@needs_idd
def test_run_ep_with_the_ems_backend_raises_for_the_models_prepared_for_a_hook(tmp_path, monkeypatch, capsys):
    from accim.run import run_ep

    _models(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = sorted(path.name for path in tmp_path.iterdir())
    with pytest.raises(ValueError, match=r'which the EMS backend cannot run: hooked\[x\.idf\. They would be simulated '
                                         r'with the setpoints of the comfort standard of their zones'):
        run_ep(only_accim_idfs=True, confirm=True, energyplus_version='auto')
    # Before anything runs
    assert sorted(path.name for path in tmp_path.iterdir()) == before
    # The models without the programs of a hook pass the check
    (tmp_path / 'hooked[x.idf').unlink()
    assert run_ep(only_accim_idfs=True, confirm=False, energyplus_version='auto') is None
    assert 'Run has been shut down' in capsys.readouterr().out
    # hooks need the backend of the API, as before
    with pytest.raises(NotImplementedError, match="hooks need run_ep\\(backend='api'\\)"):
        run_ep(only_accim_idfs=True, confirm=True, energyplus_version='auto', hooks=[print])


def _before_hook(controller, calling_point):
    """A hook that runs before the EMS programs."""


_before_hook.runs_before_programs = True


@needs_idd
def test_the_backend_of_the_api_warns_of_the_models_without_their_hook(tmp_path, monkeypatch):
    from accim.run import run_ep
    from accim.sim.energyplus_api import runner

    plain, hooked = _models(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('error', hs.MissingHookWarning)
        runner.warn_without_setpoint_hook([plain], ())
        runner.warn_without_setpoint_hook([plain, hooked], [_before_hook])
    with pytest.warns(hs.MissingHookWarning, match=r'no hook runs before their EMS programs: hooked\[x\.idf\.'):
        runner.warn_without_setpoint_hook([plain, hooked], ())

    # run_simulations and run_ep: one warning for all the models, before the simulations (not run here)
    jobs = []

    def run_job(job):
        jobs.append(job)
        return runner.SimulationResult(job[0], job[1], str(tmp_path), 'run', 0)

    monkeypatch.setattr(runner, '_run_job', run_job)
    with pytest.warns(hs.MissingHookWarning) as caught:
        runner.run_simulations([(plain, EPW), (hooked, EPW), (hooked, None, {'before_programs': [_before_hook]})],
                               processes=0)
    assert [str(w.message) for w in caught if issubclass(w.category, hs.MissingHookWarning)] == [
        hs.missing_hook_message(['hooked[x.idf'], 'api')]
    assert len(jobs) == 3
    with warnings.catch_warnings():
        warnings.simplefilter('error', hs.MissingHookWarning)
        runner.run_simulations([(plain, EPW), (hooked, EPW)], processes=0, before_programs=[_before_hook])
        runner.run_simulations([(plain, EPW)], processes=0)
    monkeypatch.chdir(tmp_path)
    with pytest.warns(hs.MissingHookWarning, match=r'hooked\[x\.idf'):
        run_ep(only_accim_idfs=True, confirm=True, backend='api', processes=0)
    # A hook that runs after the programs does not give the setpoints
    with pytest.warns(hs.MissingHookWarning, match=r'hooked\[x\.idf'):
        run_ep(only_accim_idfs=True, confirm=True, backend='api', processes=0, hooks=[print])
    with warnings.catch_warnings():
        warnings.simplefilter('error', hs.MissingHookWarning)
        run_ep(only_accim_idfs=True, confirm=True, backend='api', processes=0, hooks=[_before_hook])


@needs_idd
def test_a_simulation_without_its_hook_does_not_warn_twice(tmp_path, monkeypatch):
    # run_simulations warns once for all its simulations: each of them (run_simulation, in its process) does not
    from accim.sim.energyplus_api import runner

    _, hooked = _models(tmp_path)
    calls = []

    def run_simulation(idf, epw, **kwargs):
        calls.append(idf)
        runner.warn_without_setpoint_hook([idf], kwargs.get('before_programs', ()))
        return runner.SimulationResult(idf, epw, str(tmp_path), 'run', 0)

    monkeypatch.setattr(runner, 'run_simulation', run_simulation)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        runner.run_simulations([(hooked, EPW)], processes=0)
    assert calls == [str(hooked)]
    assert len([w for w in caught if issubclass(w.category, hs.MissingHookWarning)]) == 1
