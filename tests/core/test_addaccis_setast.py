"""Tests for the EMS program SetAST of the output IDFs when addAccis generates several of them.

All output IDFs of an input IDF are saved from the same IDF object. Since the base SetAST has 4
lines (SetpointAcc, m, n and 'run SetAST_Master'), before, genIDF kept 16 lines of the previous
output IDF (len(obj) > 18) in the branches that append the lines of the comfort model, so the
second and later output IDFs had lines of the previous one. When the cut fell inside an if block,
EnergyPlus stopped ("Missing an ENDIF"). Now each output IDF has the 4 base lines followed by the
lines of its comfort model. ComfStand 0 has no ComfMod loop, so when it was the only standard,
genIDF stopped with UnboundLocalError ('ComfMod_value'); its lines do not depend on ComfMod.

With TempCtrl='pmv' the output IDF has no comfort model (the Fanger thermostat controls the zones),
so SetAST keeps only its 4 base lines. Before, genIDF stopped with UnboundLocalError, because its
PMV branch appended the lines of a comfort model with variables of the loops of the temperature branch.
"""
import re
import shutil
from pathlib import Path

import pytest

from accim.sim import accis
from accim.sim.setAST_models import get_SetAST_lines

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = Path('C:/EnergyPlusV25-1-0/Energy+.idd')
COMFSTAND_NAMES = {'ESP CTE': 0, 'INT ASHRAE55': 2, 'IND IMAC C NV': 7}


def _setast_lines(idf_path):
    """Return the program lines of SetAST in an IDF file, without comments."""
    text = idf_path.read_text(encoding='utf-8', errors='ignore')
    for block in re.split(r'\n\s*\n', text):
        lines = block.strip().splitlines()
        if len(lines) > 1 and lines[0].strip().upper() == 'ENERGYMANAGEMENTSYSTEM:PROGRAM,' \
                and re.match(r'\s*SetAST,', lines[1]):
            return [re.sub(r'\s*!-.*$', '', line).strip().rstrip(',;') for line in lines[2:]]
    raise AssertionError(f'SetAST not found in {idf_path.name}')


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
@pytest.mark.parametrize('ScriptType, extra_args, n_idfs', [
    # Fully air-conditioned: the branches that appended the lines of the comfort model
    ('vrf_ac', dict(ComfStand=[2, 7], CAT=[80], ComfMod=[0, 3], HVACmode=[0]), 4),
    # Mixed mode: the branches that wrote them from Program_Line_17
    ('vrf_mm', dict(ComfStand=[2], CAT=[80], ComfMod=[0, 3], HVACmode=[2], VentCtrl=[0]), 2),
    # ComfStand 0 as the only standard, in both branches of ComfStand 0
    ('vrf_ac', dict(ComfStand=[0], CAT=[1], ComfMod=[0], HVACmode=[0]), 1),
    ('vrf_mm', dict(ComfStand=[0], CAT=[1], ComfMod=[0], HVACmode=[2], VentCtrl=[0]), 1),
])
def test_each_output_idf_has_the_setast_lines_of_its_comfort_model(tmp_path, monkeypatch, ScriptType,
                                                                    extra_args, n_idfs):
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)

    accis.addAccis(
        ScriptType=ScriptType,
        SupplyAirTempInputMethod='temperature difference',
        Output_type='simplified',
        Output_freqs=['hourly'],
        Output_keep_existing=False,
        EnergyPlus_version='auto',
        TempCtrl='temperature',
        confirmGen=True,
        verboseMode=False,
        **extra_args,
    )

    output_idfs = sorted(tmp_path.glob('TestModel[[]*.idf'))
    assert len(output_idfs) == n_idfs
    for idf_path in output_idfs:
        comfstand = COMFSTAND_NAMES[re.search(r'\[CS_([^\[]+)', idf_path.name).group(1)]
        comfmod = re.search(r'\[CM_([^\[]+)', idf_path.name).group(1)
        # The output IDFs of ComfStand 0 have no ComfMod ('CM_X'), and SetInputData sets ComfMod = 0
        comfmod = 0 if comfmod == 'X' else float(comfmod)
        lines = _setast_lines(idf_path)

        assert lines[3] == 'run SetAST_Master', idf_path.name
        assert lines[4:] == get_SetAST_lines(comfstand, comfmod), idf_path.name
        assert sum(re.match(r'if\b', l) is not None for l in lines) == \
               sum(re.match(r'endif\b', l) is not None for l in lines), idf_path.name


@pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
def test_pmv_output_idf_has_only_the_base_lines_of_setast(tmp_path, monkeypatch):
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)

    accis.addAccis(
        ScriptType='vrf_ac',
        SupplyAirTempInputMethod='temperature difference',
        Output_type='standard',
        Output_freqs=['hourly'],
        Output_keep_existing=False,
        EnergyPlus_version='auto',
        TempCtrl='pmv',
        ComfStand=[1],
        CAT=[3],
        ComfMod=[3],
        HVACmode=[0],
        confirmGen=True,
        verboseMode=False,
    )

    output_idfs = sorted(tmp_path.glob('TestModel[[]*.idf'))
    assert [p.name for p in output_idfs] == ['TestModel[CS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X[NS_X.idf']
    assert not list(tmp_path.glob('*_pymod.idf'))
    lines = _setast_lines(output_idfs[0])
    assert [line.split(' = ')[0] for line in lines[:3]] == ['set SetpointAcc', 'set m', 'set n']
    assert lines[3:] == ['run SetAST_Master']
    # The Fanger thermostat of each occupied zone controls the HVAC system
    text = output_idfs[0].read_text(encoding='utf-8', errors='ignore')
    assert len(re.findall(r'^\s*ZoneControl:Thermostat:ThermalComfort,', text, re.IGNORECASE | re.MULTILINE)) == 2
