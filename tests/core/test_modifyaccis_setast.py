"""Tests for the EMS program SetAST after modifyAccis.

- accim.sim.accis_single_idf_funcs.modifyAccis (used by AccimPredefModelsParamSim) trimmed SetAST
  to len(obj) > 3, that is, to its first line, so it deleted 'set m' and 'set n' and left
  'run SetAST_Master' in line 2, where the parametric setter of m then wrote over it.
- The method modifyAccis of accim.sim.accis_single_idf.addAccis trimmed SetAST to 16 lines,
  so a second call kept lines of the comfort model of the first one.
"""
import shutil
from pathlib import Path

import pytest

from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.sim import accis_single_idf, accis_single_idf_funcs
from accim.sim.setAST_models import get_SetAST_lines

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
IDD_25_2 = Path('C:/EnergyPlusV25-2-0/Energy+.idd')

ADDACCIS_ARGS = dict(
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_type='simplified',
    Output_freqs=['hourly'],
    Output_keep_existing=True,
    TempCtrl='temperature',
    verboseMode=False,
)

pytestmark = pytest.mark.skipif(not (IDD_25_2.exists() and SAMPLE_IDF.exists()),
                                reason='needs EnergyPlus 25.2 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    return get_building(str(tmp_path / 'model.idf'))


def _setast_lines(building):
    setast = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if p.Name == 'SetAST'][0]
    return list(setast.obj[2:])


def test_modifyaccis_keeps_m_and_n(building):
    accis_single_idf_funcs.addAccis(idf=building, **ADDACCIS_ARGS)

    accis_single_idf_funcs.modifyAccis(idf=building, ComfStand=99, ComfMod=3, CAT=80, HVACmode=2, VentCtrl=0,
                                       CustAST_m=0.3, CustAST_n=18)
    assert _setast_lines(building) == ['set SetpointAcc = 10000', 'set m = 0.3', 'set n = 18', 'run SetAST_Master']

    # The parametric setters of m and n replace their own lines and keep the call to SetAST_Master.
    param_accis.modify_CustAST_m(building, 0.25)
    param_accis.modify_CustAST_n(building, 17.5)
    assert _setast_lines(building) == ['set SetpointAcc = 10000', 'set m = 0.25', 'set n = 17.5', 'run SetAST_Master']


def test_second_modifyaccis_call_has_only_the_lines_of_its_comfort_model(building):
    job = accis_single_idf.addAccis(idf=building, **ADDACCIS_ARGS)

    job.modifyAccis(ComfStand=2, CAT=80, ComfMod=0, HVACmode=2, VentCtrl=0)
    job.modifyAccis(ComfStand=2, CAT=80, ComfMod=3, HVACmode=2, VentCtrl=0)

    lines = _setast_lines(building)
    assert lines[3] == 'run SetAST_Master'
    assert lines[4:] == get_SetAST_lines(2, 3)
