"""Tests for the EnergyPlus versions accepted by addAccis, runEp and the IDD lookup.

Before, the lists of versions and get_idd_path_from_ep_version stopped at EnergyPlus 25.1, so
addAccis(EnergyPlus_version='25.2') raised ValueError. runEp did not handle 'auto' (it called
IDF.setiddname('not-supported')), and when a wrong version was corrected in the prompt it kept
the IDD path of the wrong one.
"""
import builtins
from types import SimpleNamespace

import pytest

import accim.lists
import accim.sim.accim_Main as accim_Main
import accim.sim.lists
from accim.run import run
from accim.sim import accis
from accim.utils import get_idd_path_from_ep_version

IDD_25_2 = 'C:/EnergyPlusV25-2-0/Energy+.idd'

FIRST_STAGE_ARGS = dict(
    ScriptType='vrf_ac',
    SupplyAirTempInputMethod='supply air temperature',
    Output_type='standard',
    Output_freqs=['hourly'],
    Output_keep_existing=False,
    TempCtrl='temp',
)


class _ReachedAccimJob(Exception):
    """Raised by the accimJob stub: addAccis validated its arguments and started with the IDFs."""


def _stub_accim_job(*args, **kwargs):
    raise _ReachedAccimJob(kwargs.get('EnergyPlus_version'))


def _no_prompts(prompt=''):
    raise AssertionError(f'Unexpected prompt: {prompt}')


def _write_idf(path, version):
    path.write_text(f'Version,\n    {version};                    !- Version Identifier\n')


def test_version_lists_include_25_2():
    assert '25.2' in accim.lists.fullEPversionsList
    assert '25.2' in accim.lists.epvers_space_objs
    assert '25.2' in accim.sim.lists.epvers_space_objs


@pytest.mark.parametrize('version', [v for v in accim.lists.fullEPversionsList if v != 'auto'])
def test_every_listed_version_has_an_idd_path(version):
    major, minor = version.split('.')
    assert get_idd_path_from_ep_version(version) == f'C:/EnergyPlusV{major}-{minor}-0/Energy+.idd'


def test_unlisted_versions_have_no_idd_path():
    assert get_idd_path_from_ep_version('25.3') == 'not-supported'
    assert get_idd_path_from_ep_version('auto') == 'not-supported'


def test_addaccis_accepts_25_2(monkeypatch):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(_ReachedAccimJob) as reached:
        accis.addAccis(idfs=['model.idf'], EnergyPlus_version='25.2', **FIRST_STAGE_ARGS)

    assert str(reached.value) == '25.2'


def test_addaccis_rejects_unlisted_version(monkeypatch):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(ValueError, match='25.3 is not a valid EnergyPlus_version'):
        accis.addAccis(idfs=['model.idf'], EnergyPlus_version='25.3', **FIRST_STAGE_ARGS)


def test_addaccis_prompt_accepts_25_2(monkeypatch):
    answers = iter(['vrf_ac', 'supply air temperature', 'false', 'standard', 'hourly', 'false', '25.2', 'temp'])
    prompts = []

    def scripted_input(prompt=''):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', scripted_input)

    with pytest.raises(_ReachedAccimJob) as reached:
        accis.addAccis(idfs=['model.idf'])

    assert str(reached.value) == '25.2'
    assert any('(9.1 to 25.2, or auto)' in p for p in prompts)
    assert not any('EnergyPlus version was not correct' in p for p in prompts)


def test_accimjob_error_message_names_25_2(tmp_path):
    _write_idf(tmp_path / 'model.idf', '25.3')

    with pytest.raises(ValueError, match=r'EnergyPlus 25\.2 \(enter 25\.2\)'):
        accim_Main.accimJob(
            filename_temp=str(tmp_path / 'model'),
            ScriptType='vrf_ac',
            EnergyPlus_version='25.3',
            TempCtrl='temp',
            verboseMode=False,
        )


def test_get_iddfile_from_idfs_reads_the_idf_version(tmp_path):
    _write_idf(tmp_path / 'a.idf', '25.2')
    _write_idf(tmp_path / 'b.idf', '25.2.0')
    _write_idf(tmp_path / 'dsb.idf', '9.4.0.002')
    # A comment with non-ASCII characters before the Version object, in UTF-8
    (tmp_path / 'c.idf').write_text('! Oficina en Cádiz, año 2026\n  Version, 25.2;\n', encoding='utf-8')

    idfs = [str(tmp_path / name) for name in ['a.idf', 'b.idf', 'c.idf']]
    assert run.get_iddfile_from_idfs(idfs) == IDD_25_2
    assert run.get_iddfile_from_idfs([str(tmp_path / 'dsb.idf')]) == 'C:/EnergyPlusV9-4-0/Energy+.idd'


def test_get_iddfile_from_idfs_rejects_mixed_or_unsupported_versions(tmp_path):
    _write_idf(tmp_path / 'a.idf', '25.2')
    _write_idf(tmp_path / 'b.idf', '25.1')
    _write_idf(tmp_path / 'old.idf', '8.9')

    with pytest.raises(ValueError, match=r'different EnergyPlus versions \(25\.1, 25\.2\)'):
        run.get_iddfile_from_idfs([str(tmp_path / 'a.idf'), str(tmp_path / 'b.idf')])
    with pytest.raises(ValueError, match='EnergyPlus 8.9, which is not supported'):
        run.get_iddfile_from_idfs([str(tmp_path / 'old.idf')])
    (tmp_path / 'no_version.idf').write_text('Building, Office;\n')
    with pytest.raises(ValueError, match='could not be read'):
        run.get_iddfile_from_idfs([str(tmp_path / 'no_version.idf')])


class _FakeIDF:
    """Replaces eppy's IDF in runEp: records the IDD and the IDF/EPW pairs, without reading them."""
    iddname = None

    def __init__(self, idfname, epw):
        self.idfname = idfname
        self.epw = epw
        self.idfobjects = {'version': [SimpleNamespace(Version_Identifier='25.2')]}

    @classmethod
    def setiddname(cls, iddname):
        cls.iddname = iddname


@pytest.fixture
def fake_run_folder(tmp_path, monkeypatch):
    _write_idf(tmp_path / 'model[CS_INT EN16798[NS_X.idf', '25.2')
    (tmp_path / 'Seville_Present.epw').write_text('')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_FakeIDF, 'iddname', None)
    monkeypatch.setattr(run, 'IDF', _FakeIDF)
    monkeypatch.setattr(run, 'runIDFs', lambda *args, **kwargs: pytest.fail('runIDFs should not be called'))
    return tmp_path


def test_runep_auto_uses_the_idd_of_the_idf_version(fake_run_folder, monkeypatch, capsys):
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    run.runEp(runOnlyAccim=True, confirmRun=False, EnergyPlus_version='auto')

    assert _FakeIDF.iddname == IDD_25_2
    out = capsys.readouterr().out
    assert 'The EPWs we are going to run are:' in out
    assert 'sample_EPWs' not in out


def test_runep_accepts_25_2(fake_run_folder, monkeypatch):
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    run.runEp(runOnlyAccim=True, confirmRun=False, EnergyPlus_version='25.2')

    assert _FakeIDF.iddname == IDD_25_2


def test_runep_uses_the_version_corrected_in_the_prompt(fake_run_folder, monkeypatch):
    monkeypatch.setattr(builtins, 'input', lambda prompt='': '25.2')

    run.runEp(runOnlyAccim=True, confirmRun=False, EnergyPlus_version='30.1')

    assert _FakeIDF.iddname == IDD_25_2
