"""Tests for the baseline of AccimPredefModelsParamSim.

The wrapper sets the custom comfort model (ComfStand 99, CAT 80, ComfMod 3). In accim 0.x it did so without
its coefficients (all 0), so the heating setpoint (0.1 C) was above the cooling one (-0.1 C) and EnergyPlus
stopped in any simulation of the baseline: the test simulations of discover_available_outputs() and of
set_output_*_to_idf(validate=True), and the plans without ComfStand. Now the baseline has the default
coefficients of 'accim custom model' (those of ASHRAE 55 with 80 % acceptability).
"""
import shutil
from pathlib import Path

import pytest

from accim.parametric_and_optimisation.main import AccimPredefModelsParamSim
from accim.sim.ems.erl import ErlProgramSet, variables_in_programs

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
IDD_25_2 = Path('C:/EnergyPlusV25-2-0/Energy+.idd')

pytestmark = pytest.mark.skipif(not (IDD_25_2.exists() and SAMPLE_IDF.exists()),
                                reason='needs EnergyPlus 25.2 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path, monkeypatch):
    from besos.eppy_funcs import get_building

    monkeypatch.chdir(tmp_path)
    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    return get_building(str(tmp_path / 'model.idf'))


def _program_lines(building):
    return {p.Name: [line for line in p.obj[2:] if line != '']
            for p in building.idfobjects['EnergyManagementSystem:Program']}


def _setpoints(building, pmot):
    """ComfTemp, ACST and AHST of the EMS programs of the model in their first run, as in EnergyPlus."""
    programs = _program_lines(building)
    erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
    for name, value in dict(RMOT=pmot, PMOT=pmot, DayOfYear=180.0, CurrentTime=12.0).items():
        erl.set(name, value)
    for name in ['SetInputData', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST', 'SetASTnoTol']:
        erl.run(name)
    return erl.get('ComfTemp'), erl.get('ACST'), erl.get('AHST')


@pytest.mark.parametrize('pmot, comf_temp', [(20.0, 20 * 0.31 + 17.8), (5.0, 10 * 0.31 + 17.8)])
def test_the_baseline_is_a_valid_comfort_model(building, pmot, comf_temp):
    AccimPredefModelsParamSim(buildings=[building], epws=['Seville.epw'], output_type='simplified',
                              ScriptType='vrf_mm')

    programs = _program_lines(building)
    assert programs['SetInputData'][:5] == ['set ComfStand = 99', 'set CAT = 80', 'set ComfMod = 3',
                                            'set HVACmode = 2', 'set VentCtrl = 0']
    assert programs['SetAST'][:3] == ['set SetpointAcc = 10000', 'set m = 0.31', 'set n = 17.8']
    # Below the lower applicability limit (10 C), the setpoints of the custom model keep those of the limit
    _, acst, ahst = _setpoints(building, pmot)
    assert acst == pytest.approx(comf_temp + 3.5 - 0.1)
    assert ahst == pytest.approx(comf_temp - 3.5 + 0.1)
    assert ahst < acst
