"""Batch scratch files belong to a single invocation, never to a name pattern."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.sim import accim_Main, accis
from accim.sim.accim_IDFgeneration import genIDF
from accim.sim._workspace import batch_workspace, copy_job_input, cleanup_files


@pytest.mark.parametrize('version', ['9.4', '9.4.0.002'])
def test_failed_constructor_preserves_source_bytes(tmp_path, monkeypatch, version):
    source = tmp_path / 'model.idf'
    contents = f'Version, {version};\r\n'.encode('ascii')
    source.write_bytes(contents)

    def fail(path):
        assert Path(path) != source
        assert '9.4.0.002' not in Path(path).read_text()
        raise RuntimeError('stop at parsing')

    monkeypatch.setattr('besos.eppy_funcs.get_building', fail)
    with pytest.raises(RuntimeError, match='stop at parsing'):
        accim_Main.accimJob(str(source.with_suffix('')), ScriptType='vrf_ac', verboseMode=False)
    assert source.read_bytes() == contents
    assert not (tmp_path / 'model_pymod.idf').exists()


def test_constructor_never_overwrites_a_preexisting_scratch_file(tmp_path, monkeypatch):
    source = tmp_path / 'model.idf'
    source.write_text('Version,9.4;', encoding='utf-8')
    prior = tmp_path / 'model_pymod.idf'
    prior.write_text('prior run', encoding='utf-8')
    with pytest.raises(FileExistsError):
        accim_Main.accimJob(str(source.with_suffix('')), ScriptType='vrf_ac', verboseMode=False)
    assert prior.read_text(encoding='utf-8') == 'prior run'
    assert source.read_text(encoding='utf-8') == 'Version,9.4;'


@pytest.mark.parametrize('selection', [None, []])
def test_generator_cancel_does_not_scan_or_delete_unowned_files(tmp_path, monkeypatch, selection):
    monkeypatch.chdir(tmp_path)
    prior = tmp_path / 'unrelated_pymod.idf'
    prior.write_text('prior run', encoding='utf-8')
    owned = tmp_path / 'model_pymod.idf'
    owned.write_text('owned scratch', encoding='utf-8')
    job = SimpleNamespace(_owned_pymod_files={str(owned)}, output_idf_dict={})
    genIDF(job, ScriptType='vrf_ac', TempCtrl='temperature', ComfStand=[1], CAT=[3],
           ComfMod=[3], confirmGen=False, verboseMode=False, filelist_pymod=selection)
    assert not owned.exists()
    assert prior.read_text(encoding='utf-8') == 'prior run'


def test_batch_finalizer_covers_multiple_jobs_and_exceptions(tmp_path):
    source = tmp_path / 'source.idf'
    source.write_text('original', encoding='utf-8')
    prior = tmp_path / 'ab_pymod.idf'
    prior.write_text('prior run', encoding='utf-8')

    @batch_workspace
    def run():
        copy_job_input(SimpleNamespace(), str(source), str(tmp_path / 'a_pymod.idf'))
        copy_job_input(SimpleNamespace(), str(source), str(tmp_path / 'b_pymod.idf'))
        raise RuntimeError('preparation failed')

    with pytest.raises(RuntimeError, match='preparation failed'):
        run()
    assert sorted(p.name for p in tmp_path.glob('*_pymod.idf')) == ['ab_pymod.idf']
    assert prior.read_text(encoding='utf-8') == 'prior run'


def test_batch_does_not_delete_a_reused_name_after_job_cleanup(tmp_path):
    source = tmp_path / 'source.idf'
    source.write_text('source', encoding='utf-8')
    working = tmp_path / 'model_pymod.idf'

    @batch_workspace
    def run():
        job = SimpleNamespace()
        copy_job_input(job, str(source), str(working))
        cleanup_files(job._owned_pymod_files)
        working.write_text('a later invocation owns this', encoding='utf-8')

    run()
    assert working.read_text(encoding='utf-8') == 'a later invocation owns this'


def test_all_invalid_batch_cleans_only_its_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'a.idf').write_text('original', encoding='utf-8')
    prior = tmp_path / 'ab_pymod.idf'
    prior.write_text('prior run', encoding='utf-8')

    class InvalidJob:
        def __init__(self, filename_temp, **kwargs):
            copy_job_input(self, filename_temp + '.idf', filename_temp + '_pymod.idf')
            self.idf0 = self.idf1 = SimpleNamespace(idd_version=(9, 4, 0))
            self.occupiedZones = self.occupiedZones_orig = []
            self.ismixedmode = False
            self.accimNotWorking = True

    monkeypatch.setattr(accim_Main, 'accimJob', InvalidJob)
    result = accis.addAccis(
        idfs=['a.idf'], ScriptType='vrf_ac', SupplyAirTempInputMethod='temperature difference',
        Output_type='simplified', Output_freqs=['hourly'], Output_keep_existing=True,
        Output_gen_dataframe=True, EnergyPlus_version='auto', TempCtrl='temperature',
        ComfStand=[1], CAT=[3], ComfMod=[3], confirmGen=False, verboseMode=False,
    )
    assert result.output_idfs == {}
    assert result.df_outputs.empty
    assert sorted(p.name for p in tmp_path.glob('*_pymod.idf')) == ['ab_pymod.idf']



