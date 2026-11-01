"""Tests for the EMS programs SetAST and SetInputData_<zone> of the output IDFs when AddAccis (addAccis in accim 0.x)
generates several of them.

All output IDFs of an input IDF are written from the same model. In accim 0.x, each output IDF appended to SetAST
the lines of its comfort model, after its 4 base lines, and genIDF kept 16 lines of the previous output IDF
(len(obj) > 18) in the branches that appended them, so the second and later output IDFs had lines of the previous
one; when the cut fell inside an if block, EnergyPlus stopped ("Missing an ENDIF"). ComfStand 0 has no ComfMod
loop, so when it was the only standard, genIDF stopped with UnboundLocalError ('ComfMod_value'), and the PMV branch
stopped likewise. Since accim 1.0.0, the arguments of each zone are in its program SetInputData_<zone>, and SetAST
only runs SetAST_Master, which runs the subprograms of the comfort standard and comfort mode of the zone, so the
output IDFs only differ in the programs SetInputData_<zone>.

With temp_ctrl='pmv' the output IDF has no comfort model (the Fanger thermostat controls the zones), so the inputs
of the zones keep their default values, except HVACmode 0.
"""
import re
import shutil
from pathlib import Path

import pytest

from accim.sim import accis

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = Path('C:/EnergyPlusV25-1-0/Energy+.idd')
COMFSTAND_NAMES = {'ESP CTE': 0, 'INT ASHRAE55': 2, 'IND IMAC C NV': 7}
ZONES = ['Block1_Zone1', 'Block1_Zone2']


def _programs(idf_path):
    """The lines of the EMS programs of an IDF file, without comments, by program name."""
    text = idf_path.read_text(encoding='utf-8', errors='ignore')
    programs = {}
    for block in re.split(r'\n\s*\n', text):
        lines = block.strip().splitlines()
        if len(lines) > 1 and lines[0].strip().upper() == 'ENERGYMANAGEMENTSYSTEM:PROGRAM,':
            fields = [re.sub(r'\s*!-.*$', '', line).strip().rstrip(',;') for line in lines[1:]]
            programs[fields[0]] = fields[1:]
    return programs


def _inputs(lines):
    return {line.split(' = ')[0][len('set '):]: line.split(' = ')[1] for line in lines}


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
@pytest.mark.parametrize('script_type, extra_args, n_idfs', [
    ('vrf_ac', dict(comf_stand=[2, 7], cat=[80], comf_mod=[0, 3], hvac_mode=[0]), 4),
    ('vrf_mm', dict(comf_stand=[2], cat=[80], comf_mod=[0, 3], hvac_mode=[2], vent_ctrl=[0]), 2),
    # ComfStand 0 as the only standard
    ('vrf_ac', dict(comf_stand=[0], cat=[1], comf_mod=[0], hvac_mode=[0]), 1),
    ('vrf_mm', dict(comf_stand=[0], cat=[1], comf_mod=[0], hvac_mode=[2], vent_ctrl=[0]), 1),
])
def test_each_output_idf_has_the_inputs_of_its_comfort_model(tmp_path, monkeypatch, script_type, extra_args,
                                                             n_idfs):
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)

    job = accis.AddAccis(
        script_type=script_type,
        supply_air_temp_input_method='temperature difference',
        output_type='simplified',
        output_freqs=['hourly'],
        output_keep_existing=False,
        energyplus_version='auto',
        temp_ctrl='temperature',
        confirm_gen=True,
        verbose_mode=False,
        **extra_args,
    )

    output_idfs = sorted(tmp_path.glob('TestModel[[]*.idf'))
    assert len(output_idfs) == n_idfs
    assert sorted(job.output_idfs) == [p.name for p in output_idfs]
    for idf_path in output_idfs:
        comfstand = COMFSTAND_NAMES[re.search(r'\[CS_([^\[]+)', idf_path.name).group(1)]
        comfmod = re.search(r'\[CM_([^\[]+)', idf_path.name).group(1)
        # The output IDFs of ComfStand 0 have no ComfMod ('CM_X'), and their zones have ComfMod 0
        comfmod = 0 if comfmod == 'X' else float(comfmod)
        programs = _programs(idf_path)

        assert programs['SetAST'] == ['run SetAST_Master'], idf_path.name
        assert 'SetInputData' not in programs and 'SetVOFinputData' not in programs
        for zone in ZONES:
            inputs = _inputs(programs[f'SetInputData_{zone}'])
            assert (int(inputs['ComfStand']), float(inputs['ComfMod'])) == (comfstand, comfmod), idf_path.name
            assert ('MultiplierVOF' in inputs) is (script_type == 'vrf_mm')


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
def test_pmv_output_idf_has_the_default_inputs_and_hvac_mode_0(tmp_path, monkeypatch):
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)

    accis.AddAccis(
        script_type='vrf_ac',
        supply_air_temp_input_method='temperature difference',
        output_type='standard',
        output_freqs=['hourly'],
        output_keep_existing=False,
        energyplus_version='auto',
        temp_ctrl='pmv',
        comf_stand=[1],
        cat=[3],
        comf_mod=[3],
        hvac_mode=[0],
        confirm_gen=True,
        verbose_mode=False,
    )

    output_idfs = sorted(tmp_path.glob('TestModel[[]*.idf'))
    assert [p.name for p in output_idfs] == ['TestModel[CS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_X.idf']
    assert not list(tmp_path.glob('*_pymod.idf'))
    programs = _programs(output_idfs[0])
    assert programs['SetAST'] == ['run SetAST_Master']
    for zone in ZONES:
        inputs = _inputs(programs[f'SetInputData_{zone}'])
        assert (inputs['ComfStand'], inputs['CAT'], inputs['ComfMod'], inputs['HVACmode']) == ('1', '1', '2', '0')
        assert (inputs['SetpointAcc'], inputs['m'], inputs['n']) == ('10000', '0.31', '17.8')
    # The Fanger thermostat of each occupied zone controls the HVAC system
    text = output_idfs[0].read_text(encoding='utf-8', errors='ignore')
    assert len(re.findall(r'^\s*ZoneControl:Thermostat:ThermalComfort,', text, re.IGNORECASE | re.MULTILINE)) == 2
