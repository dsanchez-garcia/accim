"""Tests for modify_accis (modifyAccis in accim 0.x), which sets the arguments of the ACCIS of an IDF object.

- accim.sim.accis_single_idf_funcs.modifyAccis (used by AccimPredefModelsParamSim) trimmed SetAST
  to len(obj) > 3, that is, to its first line, so it deleted 'set m' and 'set n' and left
  'run SetAST_Master' in line 2, where the parametric setter of m then wrote over it.
- The method modifyAccis of accim.sim.accis_single_idf.addAccis trimmed SetAST to 16 lines,
  so a second call kept lines of the comfort model of the first one.

modify_accis leaves the 4 base lines of SetAST: 'run SetAST_Master' runs the subprograms of the comfort
standard and comfort mode of SetInputData, so the parametric setters that change them later work.
"""
import shutil
from pathlib import Path

import pytest

from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.sim import accis, accis_single_idf, accis_single_idf_funcs
from accim.sim.ems.setast import get_setpoint_lines, subprograms
from accim.sim.idf_tools import replace_program_lines

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
IDD_25_2 = Path('C:/EnergyPlusV25-2-0/Energy+.idd')

ADD_ACCIS_ARGS = dict(
    script_type='vrf_mm',
    supply_air_temp_input_method='temperature difference',
    output_type='simplified',
    output_freqs=['hourly'],
    output_keep_existing=True,
    temp_ctrl='temperature',
    verbose_mode=False,
)
# The names of accim 0.x, which the deprecated functions accept
LEGACY_ADD_ACCIS_ARGS = dict(
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


def _program_lines(building, name):
    program = [p for p in building.idfobjects['EnergyManagementSystem:Program'] if p.Name == name][0]
    return list(program.obj[2:])


def _setast_lines(building):
    return _program_lines(building, 'SetAST')


def test_modify_accis_keeps_m_and_n(building):
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)

    accis.modify_accis(building, comf_stand=99, comf_mod=3, cat=80, hvac_mode=2, vent_ctrl=0, cust_ast_m=0.3,
                       cust_ast_n=18)
    assert _setast_lines(building) == ['set SetpointAcc = 10000', 'set m = 0.3', 'set n = 18', 'run SetAST_Master']

    # The parametric setters of m and n replace their own lines and keep the call to SetAST_Master.
    param_accis.modify_CustAST_m(building, 0.25)
    param_accis.modify_CustAST_n(building, 17.5)
    assert _setast_lines(building) == ['set SetpointAcc = 10000', 'set m = 0.25', 'set n = 17.5', 'run SetAST_Master']


def test_modify_accis_sets_the_input_data_and_none_keeps_it(building):
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)

    accis.modify_accis(building, comf_stand=2, cat=80, comf_mod=3, hvac_mode=2, vent_ctrl=1,
                       cool_season_start='01/06', cool_season_end=250, ast_tol=0.2)
    assert _program_lines(building, 'SetInputData') == [
        'set ComfStand = 2', 'set CAT = 80', 'set ComfMod = 3', 'set HVACmode = 2', 'set VentCtrl = 1',
        'set VSToffset = 0', 'set MinOToffset = 50', 'set MaxWindSpeed = 50', 'set ACSTtol = -0.2',
        'set AHSTtol = 0.2', 'set CoolSeasonStart = 152', 'set CoolSeasonEnd = 250']

    accis.modify_accis(building, comf_stand=1)
    assert _program_lines(building, 'SetInputData')[:5] == [
        'set ComfStand = 1', 'set CAT = 80', 'set ComfMod = 3', 'set HVACmode = 2', 'set VentCtrl = 1']


def test_modify_accis_needs_the_accis(building):
    with pytest.raises(ValueError, match='Add the ACCIS first'):
        accis.modify_accis(building, comf_stand=1)


def test_modify_accis_updates_the_subprograms_of_esp_cte_and_int_iso7730(building):
    # In the models of accim 0.x, these subprograms only set the setpoints if ComfMod is 0, so the parametric
    # models (ComfMod 3) with ComfStand 0 or 22 stopped EnergyPlus
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)
    programs = {p.Name: p for p in building.idfobjects['EnergyManagementSystem:Program']}
    for name, comf_stand in [('SetAST_CS0_0', 0), ('SetAST_CS22_0', 22)]:
        replace_program_lines(programs[name], [f'! {name}', 'if (ComfMod == 0)',
                                               *get_setpoint_lines(comf_stand, 0), 'endif'])
    others = {name: _program_lines(building, name) for name in ['SetAST_Master', 'SetAST_CS1_0', 'SetAST_CS13_0']}

    accis.modify_accis(building, comf_stand=0, comf_mod=3)

    for name, lines in subprograms([0, 22]).items():
        assert _program_lines(building, name) == lines
        assert not any('ComfMod ==' in line for line in lines)
    assert {name: _program_lines(building, name) for name in others} == others


def test_add_accis_to_idf_controls_the_scheduled_ventilation(building):
    # The model ventilates through ZoneVentilation objects, without AirflowNetwork. In mixed mode, the programs
    # of the windows actuate a schedule Vent_Sch_<zone> of each one, as AddAccis does (in accim 0.x, the
    # in-memory functions, which the parametric module uses, left the ventilation uncontrolled)
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)

    ventilation = building.idfobjects['ZoneVentilation:WindandStackOpenArea']
    assert ventilation
    schedules = {s.Name for s in building.idfobjects['Schedule:Constant']}
    actuated = {a.Actuated_Component_Unique_Name for a in building.idfobjects['EnergyManagementSystem:Actuator']}
    programs = {p.Name for p in building.idfobjects['EnergyManagementSystem:Program']}
    for vent in ventilation:
        zone = vent.Zone_or_Space_Name
        assert vent.Opening_Area_Fraction_Schedule_Name == f'Vent_Sch_{zone}'
        assert f'Vent_Sch_{zone}' in schedules
        assert f'Vent_Sch_{zone}' in actuated
        assert f'SetWindowOperation_{zone}_Win'.replace(':', '_') in programs


def test_deprecated_modifyaccis_keeps_m_and_n(building):
    with pytest.warns(DeprecationWarning, match='addAccis is deprecated'):
        accis_single_idf_funcs.addAccis(idf=building, **LEGACY_ADD_ACCIS_ARGS)

    with pytest.warns(DeprecationWarning, match='modifyAccis is deprecated'):
        accis_single_idf_funcs.modifyAccis(idf=building, ComfStand=99, ComfMod=3, CAT=80, HVACmode=2, VentCtrl=0,
                                           CustAST_m=0.3, CustAST_n=18)
    assert _setast_lines(building) == ['set SetpointAcc = 10000', 'set m = 0.3', 'set n = 18', 'run SetAST_Master']


def test_second_modifyaccis_call_has_only_the_lines_of_its_comfort_model(building):
    # As in accim 0.x, the method modifyAccis of the deprecated class also appends the lines of the comfort model
    with pytest.warns(DeprecationWarning, match='addAccis is deprecated'):
        job = accis_single_idf.addAccis(idf=building, **LEGACY_ADD_ACCIS_ARGS)

    job.modifyAccis(ComfStand=2, CAT=80, ComfMod=0, HVACmode=2, VentCtrl=0)
    job.modifyAccis(ComfStand=2, CAT=80, ComfMod=3, HVACmode=2, VentCtrl=0)

    lines = _setast_lines(building)
    assert lines[3] == 'run SetAST_Master'
    assert lines[4:] == get_setpoint_lines(2, 3)
    assert job.occupied_zones and job.windows_and_doors
    # The EMS programs, as attributes of the object
    assert list(job.SetAST.obj[2:]) == lines
    assert job.SetInputData.Program_Line_1 == 'set ComfStand = 2'
    assert job.SetVOFinputData.Name == 'SetVOFinputData'
