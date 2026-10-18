"""Tests for the EnergyPlus versions accepted by addAccis, runEp and the IDD lookup.

Before, the lists of versions and get_idd_path_from_ep_version stopped at EnergyPlus 25.1, so
addAccis(EnergyPlus_version='25.2') raised ValueError. runEp did not handle 'auto' (it called
IDF.setiddname('not-supported')), and when a wrong version was corrected in the prompt it kept
the IDD path of the wrong one.

EnergyPlus 26.1 and 26.2 were added later in the same places. Before, addAccis rejected them,
runEp with 'auto' stopped because they were not supported, the addAccis of
accis_single_idf_funcs (used by the parametric module) rejected the IDFs of 26.x even with
EnergyPlus_version=None, and read_eso_using_readvarseso did not look for ReadVarsESO in their
installation folders. A model without People objects now stops with a clear error.
Since EnergyPlus 26.1, a variable that a program reads before another one sets it stops the
simulation in the first timestep of each environment, which stopped the custom model; the program
InitASTvariables now sets those variables at BeginNewEnvironment.

accim also reads the People:Definition and People:Instance objects of EnergyPlus 26.2, which it
rejected before (see test_people_instance.py): the sample model converted to these objects gives the
same results as with People objects, with addAccis and with aPMV setpoints.

In models with Space objects, the EMS sensors now read the names that EnergyPlus gives the occupant
instances, and a zone with several instances is one target (see test_space_instance_names.py): the sample
model with People assigned to a Space, to Zones of one and two spaces and to a SpaceList now simulates.
"""
import builtins
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import accim.lists
import accim.sim.accim_Main as accim_Main
import accim.sim.accim_Main_single_idf as accim_Main_single_idf
import accim.sim.lists
import accim.utils
from accim.run import run
from accim.sim import accis, accis_single_idf_funcs
from accim.sim.accim_Base_EMS import addEMSPCMBase
from accim.sim.utils import scan_zones
from accim.utils import get_idd_path_from_ep_version

IDD_25_2 = 'C:/EnergyPlusV25-2-0/Energy+.idd'
IDD_26_2 = 'C:/EnergyPlusV26-2-0/Energy+.idd'
LATEST_VERSIONS = ['25.2', '26.1', '26.2']

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
UPDATER_26_2 = Path('C:/EnergyPlusV26-2-0/PreProcess/IDFVersionUpdater')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')

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


def _idd_path(version):
    major, minor = version.split('.')
    return f'C:/EnergyPlusV{major}-{minor}-0/Energy+.idd'


@pytest.mark.parametrize('version', LATEST_VERSIONS)
def test_version_lists_include_the_latest_versions(version):
    assert version in accim.lists.fullEPversionsList
    assert version in accim.lists.epvers_space_objs
    assert version in accim.sim.lists.epvers_space_objs


@pytest.mark.parametrize('version', [v for v in accim.lists.fullEPversionsList if v != 'auto'])
def test_every_listed_version_has_an_idd_path(version):
    assert get_idd_path_from_ep_version(version) == _idd_path(version)


def test_unlisted_versions_have_no_idd_path():
    assert get_idd_path_from_ep_version('26.3') == 'not-supported'
    assert get_idd_path_from_ep_version('auto') == 'not-supported'


@pytest.mark.parametrize('version', LATEST_VERSIONS)
def test_addaccis_accepts_the_latest_versions(monkeypatch, version):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(_ReachedAccimJob) as reached:
        accis.addAccis(idfs=['model.idf'], EnergyPlus_version=version, **FIRST_STAGE_ARGS)

    assert str(reached.value) == version


def test_addaccis_rejects_unlisted_version(monkeypatch):
    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    with pytest.raises(ValueError, match='26.3 is not a valid EnergyPlus_version'):
        accis.addAccis(idfs=['model.idf'], EnergyPlus_version='26.3', **FIRST_STAGE_ARGS)


def test_addaccis_prompt_accepts_26_2(monkeypatch):
    answers = iter(['vrf_ac', 'supply air temperature', 'false', 'standard', 'hourly', 'false', '26.2', 'temp'])
    prompts = []

    def scripted_input(prompt=''):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(accim_Main, 'accimJob', _stub_accim_job)
    monkeypatch.setattr(builtins, 'input', scripted_input)

    with pytest.raises(_ReachedAccimJob) as reached:
        accis.addAccis(idfs=['model.idf'])

    assert str(reached.value) == '26.2'
    assert any('(9.1 to 26.2, or auto)' in p for p in prompts)
    assert not any('EnergyPlus version was not correct' in p for p in prompts)


def test_accimjob_error_message_names_26_2(tmp_path):
    _write_idf(tmp_path / 'model.idf', '26.3')

    with pytest.raises(ValueError, match=r'EnergyPlus 26\.2 \(enter 26\.2\)'):
        accim_Main.accimJob(
            filename_temp=str(tmp_path / 'model'),
            ScriptType='vrf_ac',
            EnergyPlus_version='26.3',
            TempCtrl='temp',
            verboseMode=False,
        )


@pytest.mark.parametrize('idd_version, EnergyPlus_version, expected', [
    ((26, 1, 0), None, '26.1'),
    ((26, 2, 0), None, '26.2'),
    ((26, 2, 0), 'auto', '26.2'),
    ((26, 2, 0), '26.2', '26.2'),
])
def test_single_idf_addaccis_accepts_26_x(monkeypatch, idd_version, EnergyPlus_version, expected):
    monkeypatch.setattr(accim_Main_single_idf, 'accimJob', _stub_accim_job)

    with pytest.raises(_ReachedAccimJob) as reached:
        accis_single_idf_funcs.addAccis(idf=SimpleNamespace(idd_version=idd_version),
                                        EnergyPlus_version=EnergyPlus_version, verboseMode=False,
                                        **FIRST_STAGE_ARGS)

    assert str(reached.value) == expected


def test_single_idf_addaccis_rejects_unlisted_version(monkeypatch):
    monkeypatch.setattr(accim_Main_single_idf, 'accimJob', _stub_accim_job)

    with pytest.raises(ValueError, match='26.3 is not a valid EnergyPlus_version'):
        accis_single_idf_funcs.addAccis(idf=SimpleNamespace(idd_version=(26, 3, 0)), verboseMode=False,
                                        **FIRST_STAGE_ARGS)


def test_get_iddfile_from_idfs_reads_the_idf_version(tmp_path):
    _write_idf(tmp_path / 'a.idf', '25.2')
    _write_idf(tmp_path / 'b.idf', '25.2.0')
    _write_idf(tmp_path / 'dsb.idf', '9.4.0.002')
    _write_idf(tmp_path / 'new.idf', '26.2')
    # A comment with non-ASCII characters before the Version object, in UTF-8
    (tmp_path / 'c.idf').write_text('! Oficina en Cádiz, año 2026\n  Version, 25.2;\n', encoding='utf-8')

    idfs = [str(tmp_path / name) for name in ['a.idf', 'b.idf', 'c.idf']]
    assert run.get_iddfile_from_idfs(idfs) == IDD_25_2
    assert run.get_iddfile_from_idfs([str(tmp_path / 'dsb.idf')]) == 'C:/EnergyPlusV9-4-0/Energy+.idd'
    assert run.get_iddfile_from_idfs([str(tmp_path / 'new.idf')]) == IDD_26_2


def test_get_iddfile_from_idfs_rejects_mixed_or_unsupported_versions(tmp_path):
    _write_idf(tmp_path / 'a.idf', '25.2')
    _write_idf(tmp_path / 'b.idf', '25.1')
    _write_idf(tmp_path / 'old.idf', '8.9')
    _write_idf(tmp_path / 'future.idf', '26.3')

    with pytest.raises(ValueError, match=r'different EnergyPlus versions \(25\.1, 25\.2\)'):
        run.get_iddfile_from_idfs([str(tmp_path / 'a.idf'), str(tmp_path / 'b.idf')])
    with pytest.raises(ValueError, match='EnergyPlus 8.9, which is not supported'):
        run.get_iddfile_from_idfs([str(tmp_path / 'old.idf')])
    with pytest.raises(ValueError, match='EnergyPlus 26.3, which is not supported'):
        run.get_iddfile_from_idfs([str(tmp_path / 'future.idf')])
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


def test_runep_auto_accepts_idfs_of_26_2(fake_run_folder, monkeypatch):
    _write_idf(fake_run_folder / 'model[CS_INT EN16798[NS_X.idf', '26.2')
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    run.runEp(runOnlyAccim=True, confirmRun=False, EnergyPlus_version='auto')

    assert _FakeIDF.iddname == IDD_26_2


@pytest.mark.parametrize('version', LATEST_VERSIONS)
def test_runep_accepts_the_latest_versions(fake_run_folder, monkeypatch, version):
    monkeypatch.setattr(builtins, 'input', _no_prompts)

    run.runEp(runOnlyAccim=True, confirmRun=False, EnergyPlus_version=version)

    assert _FakeIDF.iddname == _idd_path(version)


def test_runep_uses_the_version_corrected_in_the_prompt(fake_run_folder, monkeypatch):
    monkeypatch.setattr(builtins, 'input', lambda prompt='': '26.2')

    run.runEp(runOnlyAccim=True, confirmRun=False, EnergyPlus_version='30.1')

    assert _FakeIDF.iddname == IDD_26_2


def test_scan_zones_rejects_models_without_people():
    # The IDDs before EnergyPlus 26.2 have no People:Instance objects
    idf = SimpleNamespace(idfobjects={'PEOPLE': []})

    with pytest.raises(ValueError, match='The model has no People objects'):
        scan_zones(SimpleNamespace(idf1=idf))


class _FakeEMSModel:
    """Minimal IDF for addEMSPCMBase: the EMS programs and the calling managers it creates."""

    def __init__(self, program_names):
        self.idfobjects = {
            'EnergyManagementSystem:Program': [SimpleNamespace(Name=name) for name in program_names],
            'EnergyManagementSystem:ProgramCallingManager': [],
        }

    def newidfobject(self, key, **fields):
        obj = SimpleNamespace(**fields)
        self.idfobjects[key].append(obj)
        return obj


def test_pcm_of_the_initialisation_program_runs_at_begin_new_environment():
    # Since EnergyPlus 26.1, a variable read before it is set in the first timestep of an environment
    # stops the simulation. SetComfTemp (custom model) reads m and n before SetAST sets them, so
    # InitASTvariables sets them at BeginNewEnvironment.
    model = _FakeEMSModel(['SetComfTemp', 'SetAST_Master', 'SetAST', 'SetASTnoTol', 'InitASTvariables',
                           'SetInputData'])

    addEMSPCMBase(SimpleNamespace(idf1=model), verboseMode=False)

    points = {pcm.Name: pcm.EnergyPlus_Model_Calling_Point
              for pcm in model.idfobjects['EnergyManagementSystem:ProgramCallingManager']}
    assert points.pop('InitASTvariables') == 'BeginNewEnvironment'
    assert 'SetAST_Master' not in points
    assert set(points.values()) == {'BeginTimestepBeforePredictor'}
    order = list(points)
    assert order.index('SetInputData') < order.index('SetComfTemp') < order.index('SetAST')


class _ReachedReadVarsESO(Exception):
    """Raised by the subprocess.run stub: read_eso_using_readvarseso found ReadVarsESO."""


def test_read_eso_using_readvarseso_prefers_the_newest_installation(tmp_path, monkeypatch):
    eso = tmp_path / 'eplusout.eso'
    eso.write_text('')
    installed = {
        os.path.join(r'C:\EnergyPlusV25-2-0', 'PostProcess', 'ReadVarsESO.exe'),
        os.path.join(r'C:\EnergyPlusV26-2-0', 'PostProcess', 'ReadVarsESO.exe'),
    }
    real_exists = os.path.exists
    calls = []

    def fake_exists(path):
        if str(path).startswith('C:\\EnergyPlusV'):
            return str(path) in installed
        return real_exists(path)

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        raise _ReachedReadVarsESO

    monkeypatch.setattr(accim.utils.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(accim.utils.os.path, 'exists', fake_exists)
    monkeypatch.setattr(accim.utils.subprocess, 'run', fake_run)

    with pytest.raises(_ReachedReadVarsESO):
        accim.utils.read_eso_using_readvarseso(str(eso))

    assert calls[0][0] == os.path.join(r'C:\EnergyPlusV26-2-0', 'PostProcess', 'ReadVarsESO.exe')


needs_26_2 = pytest.mark.skipif(
    not (Path(IDD_26_2).exists() and UPDATER_26_2.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
    reason='needs EnergyPlus 26.2 and the sample files of the repository')


@pytest.fixture(scope='module')
def idf_26_2(tmp_path_factory):
    """The sample IDF of EnergyPlus 25.1, updated to 26.2 with the transition programs of EnergyPlus."""
    folder = tmp_path_factory.mktemp('idf_26_2')
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    accim.utils.update_idf_version(str(folder / 'TestModel.idf'), '26.2')
    return folder / 'TestModel.idf'


def _run_in_new_process(script, folder):
    # eppy only sets one IDD per process, and the other tests of the session may have set the IDD of
    # EnergyPlus 25.1 or 25.2. PYTHONPATH makes the new process import accim from this repository
    # instead of the installed accim (an editable installation may point to another checkout).
    pythonpath = [str(REPO)] + ([os.environ['PYTHONPATH']] if os.environ.get('PYTHONPATH') else [])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(pythonpath))
    result = subprocess.run([sys.executable, '-c', script, str(folder)], capture_output=True, text=True, timeout=900,
                            env=env)
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    return result


def _ems_objects(text, object_type):
    """Return the fields of each object of an EMS type in an IDF text, without comments."""
    objects = []
    for block in text.split(';'):
        fields = [line.split('!')[0].strip().rstrip(',').strip() for line in block.splitlines()]
        fields = [f for f in fields if f]
        if fields and fields[0].upper() == object_type.upper():
            objects.append(fields[1:])
    return objects


_ADDACCIS_VRF_MM_SCRIPT = """
import os, sys
os.chdir(sys.argv[1])
from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_mm', SupplyAirTempInputMethod='temperature difference', Output_type='standard',
    Output_freqs=['hourly'], Output_keep_existing=False, EnergyPlus_version='auto', TempCtrl='temperature',
    ComfStand=[1], CAT=[3], ComfMod=[3], HVACmode=[2], VentCtrl=[0], confirmGen=True, verboseMode=False,
)
"""


@needs_26_2
def test_addaccis_on_an_idf_updated_to_26_2(idf_26_2, tmp_path):
    shutil.copy(idf_26_2, tmp_path / 'TestModel.idf')

    _run_in_new_process(_ADDACCIS_VRF_MM_SCRIPT, tmp_path)

    output_idfs = sorted(tmp_path.glob('TestModel[[]*.idf'))
    assert len(output_idfs) == 1
    text = output_idfs[0].read_text(encoding='utf-8', errors='ignore')
    assert re.search(r'^\s*Version\s*,\s*26\.2\s*;', text, re.IGNORECASE | re.MULTILINE)
    programs = {fields[0]: fields[1:] for fields in _ems_objects(text, 'EnergyManagementSystem:Program')}
    for name in ['SetComfTemp', 'SetAppLimits', 'ApplyCAT', 'SetAST', 'SetVOFinputData']:
        assert name in programs, name
    assert any(p.startswith('ApplyAST_') for p in programs)
    assert any(p.startswith('SetWindowOperation_') for p in programs)
    assert programs['InitASTvariables'] == ['set m = 0', 'set n = 0', 'set ACSTnoTol = 0', 'set AHSTnoTol = 0']
    pcms = {fields[0]: fields[1] for fields in _ems_objects(text, 'EnergyManagementSystem:ProgramCallingManager')}
    assert pcms['InitASTvariables'] == 'BeginNewEnvironment'


# The custom model (ComfStand 99), simulated for 1 day with EnergyPlus 26.2. Before, SetComfTemp read
# m and n before SetAST set them, and EnergyPlus 26.2 stopped in the first timestep with
# "Variable = 'N' used in expression has not been initialized".
_SIMULATE_CUSTOM_MODEL_SCRIPT = """
import os, subprocess, sys
os.chdir(sys.argv[1])
from pathlib import Path
from accim.sim import accis
from accim.utils import reduce_runtime
from besos.eppy_funcs import get_building
accis.addAccis(
    ScriptType='vrf_ac', SupplyAirTempInputMethod='temperature difference', Output_type='simplified',
    Output_freqs=['hourly'], Output_keep_existing=False, EnergyPlus_version='auto', TempCtrl='temperature',
    ComfStand=[99], CAT=[80], ComfMod=[3], HVACmode=[0],
    CustAST_m=0.31, CustAST_n=17.8, CustAST_ACSToffset=3.5, CustAST_AHSToffset=-3.5,
    CustAST_ACSTaul=33.5, CustAST_ACSTall=10, CustAST_AHSTaul=33.5, CustAST_AHSTall=10,
    confirmGen=True, verboseMode=False,
)
output_idf = [p for p in Path('.').glob('TestModel[[]*.idf')][0]
building = get_building(str(output_idf))
reduce_runtime(idf_object=building)
building.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'No'
building.saveas('custom_model_1_day.idf')
subprocess.run(['C:/EnergyPlusV26-2-0/energyplus.exe', '-w', 'Seville.epw', '-d', 'out',
                'custom_model_1_day.idf'], capture_output=True)
"""


@needs_26_2
def test_custom_model_simulates_with_26_2(idf_26_2, tmp_path):
    shutil.copy(idf_26_2, tmp_path / 'TestModel.idf')
    shutil.copy(SAMPLE_EPW, tmp_path / 'Seville.epw')

    _run_in_new_process(_SIMULATE_CUSTOM_MODEL_SCRIPT, tmp_path)

    err = (tmp_path / 'out' / 'eplusout.err').read_text(encoding='utf-8', errors='ignore')
    assert 'has not been initialized' not in err
    assert 'EnergyPlus Completed Successfully' in err, err[-3000:]


# The sample model in people/ (People objects) and the same model in instances/, where each People object
# becomes a People:Definition named '<name> Definition' and a People:Instance with the name of the People
# object and the values of its fields. Both are simulated for one summer day with EnergyPlus 26.2.
_PEOPLE_AND_INSTANCES_SCRIPT = """
import os, subprocess, sys
from pathlib import Path
from besos.eppy_funcs import get_building
from accim.utils import reduce_runtime
root = Path(sys.argv[1]).resolve()
building = get_building(str(root / 'instances' / 'TestModel.idf'))
for people in list(building.idfobjects['PEOPLE']):
    definition = building.newidfobject('PEOPLE:DEFINITION', Name=people.Name + ' Definition')
    instance = building.newidfobject('PEOPLE:INSTANCE', Name=people.Name, People_Definition_Name=definition.Name)
    for obj in (definition, instance):
        for field in obj.fieldnames[2:]:
            if field in people.fieldnames:
                obj[field] = people[field]
    building.removeidfobject(people)
building.save()


def simulate_1_summer_day(model):
    reduce_runtime(idf_object=model, runperiod_begin_month=7, runperiod_begin_day_of_month=15,
                   runperiod_end_month=7, runperiod_end_day_of_month=15)
    model.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'No'
    model.saveas('model_1_day.idf')
    subprocess.run(['C:/EnergyPlusV26-2-0/energyplus.exe', '-w', str(root / 'Seville.epw'), '-d', 'out',
                    'model_1_day.idf'], capture_output=True)
"""

_ADDACCIS_PEOPLE_AND_INSTANCES_SCRIPT = _PEOPLE_AND_INSTANCES_SCRIPT + """
from accim.sim import accis
for folder in ['people', 'instances']:
    os.chdir(root / folder)
    accis.addAccis(
        ScriptType='vrf_mm', SupplyAirTempInputMethod='temperature difference', Output_type='standard',
        Output_freqs=['hourly'], Output_keep_existing=False, EnergyPlus_version='auto', TempCtrl='temperature',
        ComfStand=[1], CAT=[3], ComfMod=[3], HVACmode=[2], VentCtrl=[0], confirmGen=True, verboseMode=False,
    )
    output_idf = [p for p in Path('.').glob('TestModel[[]*.idf')][0]
    simulate_1_summer_day(get_building(str(output_idf)))
"""

_APMV_PEOPLE_AND_INSTANCES_SCRIPT = _PEOPLE_AND_INSTANCES_SCRIPT + """
from accim.sim.apmv_setpoints import add_vrf_system, apply_apmv_setpoints, set_pmv_input_parameters
for folder in ['people', 'instances']:
    os.chdir(root / folder)
    building = get_building('TestModel.idf')
    add_vrf_system(building, verbose_mode=False)
    apply_apmv_setpoints(
        building, outputs_freq=['hourly'], adap_coeff_cooling=0.293, adap_coeff_heating=-0.293,
        pmv_cooling_sp=0.5, pmv_heating_sp=-0.5, cooling_season_start='01/05', cooling_season_end='01/10',
        verbose_mode=False,
    )
    set_pmv_input_parameters(building, air_velocity=0.1, work_efficiency=0.0, verbose_mode=False)
    simulate_1_summer_day(building)
"""

PEOPLE_NAMES = {'People Block1:Zone1', 'People Block1:Zone2'}


def _idf_objects(text, object_type):
    """Return the fields of each object of a type in an IDF text, without comments, with the empty ones."""
    objects = []
    for block in text.split(';'):
        fields = [f.strip() for f in ''.join(line.split('!')[0] for line in block.splitlines()).split(',')]
        if fields[0].upper() == object_type.upper():
            objects.append(fields[1:])
    return objects


def _people_and_instances_folders(idf_26_2, tmp_path):
    for folder in ['people', 'instances']:
        (tmp_path / folder).mkdir()
        shutil.copy(idf_26_2, tmp_path / folder / 'TestModel.idf')
    shutil.copy(SAMPLE_EPW, tmp_path / 'Seville.epw')


def _simulated_idfs(tmp_path):
    return {folder: (tmp_path / folder / 'model_1_day.idf').read_text(encoding='utf-8', errors='ignore')
            for folder in ['people', 'instances']}


def _hourly_results(folder):
    err = (folder / 'out' / 'eplusout.err').read_text(encoding='utf-8', errors='ignore')
    assert 'EnergyPlus Completed Successfully' in err, err[-3000:]
    return pd.read_csv(folder / 'out' / 'eplusout.csv')


@needs_26_2
def test_people_instances_simulate_as_people_with_addaccis_and_26_2(idf_26_2, tmp_path):
    # Before, addAccis stopped in scan_zones with a ValueError for the model with People:Instance objects
    _people_and_instances_folders(idf_26_2, tmp_path)

    _run_in_new_process(_ADDACCIS_PEOPLE_AND_INSTANCES_SCRIPT, tmp_path)

    idfs = _simulated_idfs(tmp_path)
    assert _idf_objects(idfs['instances'], 'People') == []
    assert {fields[0] for fields in _idf_objects(idfs['instances'], 'People:Instance')} == PEOPLE_NAMES
    definitions = _idf_objects(idfs['instances'], 'People:Definition')
    assert [fields[10:12] for fields in definitions] == [['AdaptiveASH55', 'AdaptiveCEN15251']] * 2
    # The EMS sensors read the outputs of the instances, named after the People:Instance objects
    sensors = _ems_objects(idfs['instances'], 'EnergyManagementSystem:Sensor')
    assert sensors == _ems_objects(idfs['people'], 'EnergyManagementSystem:Sensor')
    assert {key for name, key, variable in sensors if variable == 'People Occupant Count'} == PEOPLE_NAMES
    pd.testing.assert_frame_equal(_hourly_results(tmp_path / 'instances'), _hourly_results(tmp_path / 'people'))


@needs_26_2
def test_people_instances_simulate_as_people_with_apmv_setpoints_and_26_2(idf_26_2, tmp_path):
    # Before, add_vrf_system stopped in scan_zones with a ValueError for the model with People:Instance objects
    _people_and_instances_folders(idf_26_2, tmp_path)

    _run_in_new_process(_APMV_PEOPLE_AND_INSTANCES_SCRIPT, tmp_path)

    idfs = _simulated_idfs(tmp_path)
    # set_pmv_input_parameters sets the schedules of the instances and the Fanger model of their definitions
    instances = {fields[0]: (fields[6], fields[10]) for fields in _idf_objects(idfs['instances'], 'People:Instance')}
    assert instances == {
        'People Block1:Zone1': ('Sch_Eff_People_Block1_Zone1', 'Sch_Vel_People_Block1_Zone1'),
        'People Block1:Zone2': ('Sch_Eff_People_Block1_Zone2', 'Sch_Vel_People_Block1_Zone2'),
    }
    definitions = _idf_objects(idfs['instances'], 'People:Definition')
    assert [fields[10:13] for fields in definitions] == [['Fanger', 'AdaptiveCEN15251', 'Fanger']] * 2
    sensors = _ems_objects(idfs['instances'], 'EnergyManagementSystem:Sensor')
    assert sensors == _ems_objects(idfs['people'], 'EnergyManagementSystem:Sensor')
    assert {key for name, key, variable in sensors if variable == 'Zone Thermal Comfort Fanger Model PMV'} == PEOPLE_NAMES
    pd.testing.assert_frame_equal(_hourly_results(tmp_path / 'instances'), _hourly_results(tmp_path / 'people'))


# Models with Space objects, built from the sample model in models/: People assigned to a Space and to a
# Zone of one space, to a Zone of two spaces (the floor of Block1:Zone1 split in two), and to a SpaceList
# of the three spaces. addAccis and the aPMV setpoints (in the zone of two spaces) are simulated for one
# day with EnergyPlus 26.2.
_SPACE_MODELS_SCRIPT = """
import os, subprocess, sys
from pathlib import Path
from besos.eppy_funcs import get_building
from accim.utils import reduce_runtime
root = Path(sys.argv[1]).resolve()
os.chdir(root / 'models')


def surfaces(building, zone):
    return [s for s in building.idfobjects['BUILDINGSURFACE:DETAILED'] if s.Zone_Name == zone]


def add_space(building, name, zone, zone_surfaces):
    building.newidfobject('SPACE', Name=name, Zone_Name=zone)
    for surface in zone_surfaces:
        surface.Space_Name = name


def people(building, zone):
    return [p for p in building.idfobjects['PEOPLE'] if p.Name == f'People {zone}'][0]


def split_floor_of_zone_1(building):
    floor = [s for s in surfaces(building, 'Block1:Zone1') if s.Surface_Type.upper() == 'FLOOR'][0]
    half = building.copyidfobject(floor)
    half.Name = 'Block1:Zone1_GroundFloor_B'
    ys = sorted({float(floor[f'Vertex_{n}_Ycoordinate']) for n in range(1, 5)})
    middle = (ys[0] + ys[-1]) / 2
    for n in range(1, 5):
        if float(floor[f'Vertex_{n}_Ycoordinate']) == ys[-1]:
            floor[f'Vertex_{n}_Ycoordinate'] = middle
        if float(half[f'Vertex_{n}_Ycoordinate']) == ys[0]:
            half[f'Vertex_{n}_Ycoordinate'] = middle
    return half


def simulate_1_day(model, name):
    reduce_runtime(idf_object=model)
    model.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'No'
    model.saveas(f'{name}_1_day.idf')
    subprocess.run(['C:/EnergyPlusV26-2-0/energyplus.exe', '-w', str(root / 'Seville.epw'), '-d', f'out_{name}',
                    f'{name}_1_day.idf'], capture_output=True)


building = get_building('TestModel.idf')
add_space(building, 'Space 1', 'Block1:Zone1', surfaces(building, 'Block1:Zone1'))
add_space(building, 'Space 2', 'Block1:Zone2', surfaces(building, 'Block1:Zone2'))
people(building, 'Block1:Zone1').Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'Space 1'
building.saveas('SpaceAndZoneOfOneSpace.idf')

building = get_building('TestModel.idf')
half = split_floor_of_zone_1(building)
add_space(building, 'Space 1a', 'Block1:Zone1', [s for s in surfaces(building, 'Block1:Zone1') if s.Name != half.Name])
add_space(building, 'Space 1b', 'Block1:Zone1', [half])
add_space(building, 'Space 2', 'Block1:Zone2', surfaces(building, 'Block1:Zone2'))
building.saveas('ZoneOfTwoSpaces.idf')
building.removeidfobject(people(building, 'Block1:Zone2'))
building.newidfobject('SPACELIST', Name='All spaces', Space_1_Name='Space 1a', Space_2_Name='Space 1b',
                      Space_3_Name='Space 2')
people(building, 'Block1:Zone1').Zone_or_ZoneList_or_Space_or_SpaceList_Name = 'All spaces'
building.saveas('SpaceList.idf')
os.remove('TestModel.idf')

from accim.sim import accis
accis.addAccis(
    ScriptType='vrf_ac', SupplyAirTempInputMethod='supply air temperature', Output_type='standard',
    Output_freqs=['hourly'], Output_keep_existing=False, EnergyPlus_version='auto', TempCtrl='temperature',
    ComfStand=[1], CAT=[3], ComfMod=[3], HVACmode=[0], confirmGen=True, verboseMode=False,
)
for output_idf in sorted(Path('.').glob('*[[]*.idf')):
    simulate_1_day(get_building(str(output_idf)), output_idf.name.split('[')[0])

from accim.sim.apmv_setpoints import add_vrf_system, apply_apmv_setpoints
building = get_building('ZoneOfTwoSpaces.idf')
add_vrf_system(building, verbose_mode=False)
apply_apmv_setpoints(building, outputs_freq=['hourly'], verbose_mode=False)
simulate_1_day(building, 'aPMV_ZoneOfTwoSpaces')
"""


@needs_26_2
def test_models_with_space_objects_simulate_with_26_2(idf_26_2, tmp_path):
    # Before, the sensors of the People assigned to a Space or to a Zone of one space read keys that EnergyPlus
    # does not create ('Space 1 People Block1:Zone1'), and addAccis and add_vrf_system created
    # 'Block1:Zone1 Dual SP' once per space in the zone of two spaces, so EnergyPlus stopped.
    (tmp_path / 'models').mkdir()
    shutil.copy(idf_26_2, tmp_path / 'models' / 'TestModel.idf')
    shutil.copy(SAMPLE_EPW, tmp_path / 'Seville.epw')

    _run_in_new_process(_SPACE_MODELS_SCRIPT, tmp_path)

    for name in ['SpaceAndZoneOfOneSpace', 'ZoneOfTwoSpaces', 'SpaceList', 'aPMV_ZoneOfTwoSpaces']:
        err = (tmp_path / 'models' / f'out_{name}' / 'eplusout.err').read_text(encoding='utf-8', errors='ignore')
        assert 'Index Key Name' not in err and 'Duplicate name found' not in err, (name, err[-3000:])
        assert 'EnergyPlus Completed Successfully' in err, (name, err[-3000:])
    sensors = {name: (key, variable) for name, key, variable in _ems_objects(
        (tmp_path / 'models' / 'ZoneOfTwoSpaces_1_day.idf').read_text(encoding='utf-8', errors='ignore'),
        'EnergyManagementSystem:Sensor')}
    assert sensors['Occ_count_Block1_Zone1'] == ('Block1:Zone1', 'Zone People Occupant Count')
    assert sensors['Occ_count_Space_2_People_Block1_Zone2'] == ('People Block1:Zone2', 'People Occupant Count')
