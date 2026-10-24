"""Automatic cleanup is restricted to directories created by this invocation."""

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import accim.utils as utils
import accim.parametric_and_optimisation.main as main
from .test_optimisation_checkpoint_resume import (
    _fake_set_evaluator, _make_lightweight_optimisation, _make_fake_nsgaii,
)
from .test_sim_file_cleanup import _fake_build_optim_full_outputs_df


@pytest.mark.parametrize('policy', ['none', 'non-dominated', 'all'])
def test_optimisation_preserves_previous_run_files(tmp_path, monkeypatch, policy):
    old_dir = tmp_path / 'BESOS_Output_previous'
    old_dir.mkdir()
    sentinel = old_dir / 'eplusout.csv'
    sentinel.write_text('old simulation', encoding='utf-8')
    old_log = tmp_path / 'optim_eval_log_previous.jsonl'
    old_log.write_text('old log', encoding='utf-8')
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda *args, **kwargs: None)
    monkeypatch.setattr(main.OptimisationSimulation, 'set_evaluator', _fake_set_evaluator)
    monkeypatch.setattr(main.OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_optim_full_outputs_df)
    monkeypatch.setattr(main.optimizer, 'NSGAII', _make_fake_nsgaii([]))
    sim = _make_lightweight_optimisation(['A.epw'])
    sim.run_optimisation(out_dir=str(tmp_path), keep_sim_files=policy, show_progress=False)
    assert sentinel.read_text(encoding='utf-8') == 'old simulation'
    assert old_log.read_text(encoding='utf-8') == 'old log'


@pytest.mark.parametrize('keep', [False, True])
@pytest.mark.parametrize('fail', [False, True])
def test_output_discovery_owns_only_its_new_directory(tmp_path, monkeypatch, keep, fail):
    base = tmp_path / 'available_outputs'
    base.mkdir()
    sentinel = base / 'eplusout.csv'
    sentinel.write_text('previous results', encoding='utf-8')
    calls = []

    def run(building, out_dir, **kwargs):
        folder = Path(out_dir)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'eplusout.csv').write_text('new results', encoding='utf-8')
        calls.append(folder)
        if fail:
            raise RuntimeError('test discovery failure')
        return {('Electricity:Facility', 'Hourly'): object()}

    monkeypatch.setattr(utils, 'run_building', run)
    if fail:
        with pytest.raises(RuntimeError, match='test discovery failure'):
            utils.print_available_outputs_mod(object(), out_dir=str(base), keep_out_dir=keep)
    else:
        output = utils.print_available_outputs_mod(object(), out_dir=str(base), keep_out_dir=keep)
        assert output.meterreaderlist == [['Electricity:Facility', 'Hourly']]
        assert Path(output.out_dir) == calls[0]
    assert calls and calls[0] != base
    assert sentinel.read_text(encoding='utf-8') == 'previous results'
    assert calls[0].exists() is keep


def test_reduced_discovery_input_does_not_overwrite_a_previous_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    original = tmp_path / 'temp_reduced_runtime_0_model.idf'
    original.write_text('previous input', encoding='utf-8')
    written = []

    def savecopy(path):
        written.append(Path(path).absolute())
        Path(path).write_text('new input', encoding='utf-8')

    model = SimpleNamespace(idfname='model.idf', savecopy=savecopy)
    monkeypatch.setattr('besos.eppy_funcs.get_building', lambda path: model)
    sim = main.SimulationBase.__new__(main.SimulationBase)
    prepared, path = sim._prepare_reduced_testsim_building(0, model, reduce_sim_time=False, force_temp_copy=True)
    try:
        assert prepared is model
        assert path is not None
        assert Path(path).absolute() != original
        assert original.read_text(encoding='utf-8') == 'previous input'
    finally:
        for artifact in written:
            if artifact != original:
                artifact.unlink(missing_ok=True)


def test_rdd_refresh_preserves_existing_discovery_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    old = tmp_path / 'available_outputs'
    old.mkdir()
    sentinel = old / 'notes.txt'
    sentinel.write_text('preserve', encoding='utf-8')
    sim = _make_lightweight_optimisation(['A.epw'])
    monkeypatch.setattr(sim, '_prepare_reduced_testsim_building', lambda **kwargs: (object(), None))
    monkeypatch.setattr(sim, '_ensure_output_variable_dictionary_for_building', lambda **kwargs: None)
    calls = []

    def run(building, out_dir, **kwargs):
        folder = Path(out_dir)
        folder.mkdir(parents=True, exist_ok=True)
        calls.append(folder)
        (folder / 'eplusout.rdd').write_text('! header\n! header\nOutput:Variable,*,Zone Mean Air Temperature,Hourly,C\n', encoding='utf-8')
        (folder / 'eplusout.mdd').write_text('! header\n! header\nOutput:Meter,Electricity:Facility,Hourly,J\n', encoding='utf-8')

    monkeypatch.setattr('besos.eplus_funcs.run_building', run)
    result = sim.discover_available_outputs(prefer='rdd_mdd', refresh=True)
    assert result['variables']['variable_name'].tolist() == ['Zone Mean Air Temperature']
    assert calls[0].absolute() != old
    assert sentinel.read_text(encoding='utf-8') == 'preserve'
    assert not calls[0].exists()


