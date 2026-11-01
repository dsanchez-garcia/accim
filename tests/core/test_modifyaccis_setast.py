"""Tests for modify_accis (modifyAccis in accim 0.x), which sets the arguments of the ACCIS of an IDF object.

- accim.sim.accis_single_idf_funcs.modifyAccis (used by AccimPredefModelsParamSim) trimmed SetAST
  to len(obj) > 3, that is, to its first line, so it deleted 'set m' and 'set n' and left
  'run SetAST_Master' in line 2, where the parametric setter of m then wrote over it.
- The method modifyAccis of accim.sim.accis_single_idf.addAccis trimmed SetAST to 16 lines,
  so a second call kept lines of the comfort model of the first one.

Since accim 1.0.0, each zone has all its arguments (also SetpointAcc, m and n, which were in SetAST) in its
program SetInputData_<zone>, and SetAST only runs SetAST_Master, which runs the subprograms of the comfort standard
and comfort mode of the zone, so the parametric setters that change them later work. The models of earlier versions
keep their programs (one SetInputData for all the zones), which modify_accis still sets.
"""
import shutil
from pathlib import Path

import pytest

from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.sim import accis, accis_single_idf, accis_single_idf_funcs
from accim.sim.ems.inputs import input_programs, read_inputs
from accim.sim.ems.setast import get_setpoint_lines, subprograms
from accim.sim.idf_tools import replace_program_lines

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
# An output IDF of accim 0.x (before SetAST_Master), with one program SetInputData for all the zones
LEGACY_IDF = next((REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'runEp').glob('TestModel_V2510*.idf'), None)
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


def _zone_inputs(building):
    """The inputs of each zone, {zone: {EMS variable: value}}."""
    return {zone: read_inputs(program) for zone, program in input_programs(building).items()}


def test_modify_accis_sets_m_and_n_in_the_inputs_of_each_zone(building):
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)

    accis.modify_accis(building, comf_stand=99, comf_mod=3, cat=80, hvac_mode=2, vent_ctrl=0, cust_ast_m=0.3,
                       cust_ast_n=18)
    assert _setast_lines(building) == ['run SetAST_Master']
    inputs = _zone_inputs(building)
    assert len(inputs) == 2
    assert {(i['SetpointAcc'], i['m'], i['n']) for i in inputs.values()} == {(10000, 0.3, 18)}

    # The parametric setters of m and n set them in all the zones
    param_accis.modify_CustAST_m(building, 0.25)
    param_accis.modify_CustAST_n(building, 17.5)
    assert {(i['m'], i['n']) for i in _zone_inputs(building).values()} == {(0.25, 17.5)}
    assert _setast_lines(building) == ['run SetAST_Master']


def test_modify_accis_sets_the_input_data_and_none_keeps_it(building):
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)

    accis.modify_accis(building, comf_stand=2, cat=80, comf_mod=3, hvac_mode=2, vent_ctrl=1,
                       cool_season_start='01/06', cool_season_end=250, ast_tol=0.2)
    for zone in input_programs(building):
        assert _program_lines(building, f'SetInputData_{zone}') == [
            'set ComfStand = 2', 'set CAT = 80', 'set ComfMod = 3', 'set HVACmode = 2', 'set VentCtrl = 1',
            'set VSToffset = 0', 'set MinOToffset = 50', 'set MaxWindSpeed = 50', 'set ACSTtol = -0.2',
            'set AHSTtol = 0.2', 'set CoolSeasonStart = 152', 'set CoolSeasonEnd = 250', 'set CATcoolOffset = 0',
            'set CATheatOffset = 0', 'set SetpointAcc = 10000', 'set m = 0', 'set n = 0', 'set CustAST_ACSToffset = 0',
            'set CustAST_AHSToffset = 0', 'set CustAST_ACSTaul = 0', 'set CustAST_ACSTall = 0',
            'set CustAST_AHSTaul = 0', 'set CustAST_AHSTall = 0', 'set MaxTempDiffVOF = 6',
            'set MinTempDiffVOF = 1', 'set MultiplierVOF = 0.25']

    accis.modify_accis(building, comf_stand=1)
    for zone in input_programs(building):
        assert _program_lines(building, f'SetInputData_{zone}')[:5] == [
            'set ComfStand = 1', 'set CAT = 80', 'set ComfMod = 3', 'set HVACmode = 2', 'set VentCtrl = 1']


def test_parametric_setters_set_the_inputs_of_all_the_zones(building):
    accis.add_accis_to_idf(building, **ADD_ACCIS_ARGS)

    param_accis.modify_ComfStand(building, 2)
    param_accis.modify_CAT(building, 90)
    param_accis.modify_ASTtol(building, 0.3)
    param_accis.modify_CoolSeasonStart(building, '01/06')
    param_accis.modify_CustAST_ASToffset(building, 2.5)
    param_accis.modify_MultiplierVOF(building, 0.5)

    for inputs in _zone_inputs(building).values():
        assert (inputs['ComfStand'], inputs['CAT'], inputs['ACSTtol'], inputs['AHSTtol']) == (2, 90, -0.3, 0.3)
        assert (inputs['CoolSeasonStart'], inputs['CustAST_ACSToffset'], inputs['CustAST_AHSToffset']) == \
               (152, 2.5, -2.5)
        assert inputs['MultiplierVOF'] == 0.5
    assert param_accis.get_custom_model_arguments(building) == {
        'm': 0.31, 'n': 17.8, 'ACSToffset': 2.5, 'AHSToffset': -2.5, 'ACSTaul': 33.5, 'ACSTall': 10,
        'AHSTaul': 33.5, 'AHSTall': 10}


def test_parametric_setters_need_the_inputs_of_the_model(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    accis.add_accis_to_idf(building, **dict(ADD_ACCIS_ARGS, script_type='vrf_ac'))

    # The models without natural ventilation have no inputs of the venting opening factor
    with pytest.raises(ValueError, match='no inputs'):
        param_accis.modify_MultiplierVOF(building, 0.5)


def test_modify_accis_needs_the_accis(building):
    with pytest.raises(ValueError, match='Add the ACCIS first'):
        accis.modify_accis(building, comf_stand=1)


@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_modify_accis_updates_the_subprograms_of_esp_cte_and_int_iso7730_of_earlier_versions(tmp_path):
    # In the models of accim 0.x, these subprograms only set the setpoints if ComfMod is 0, so the parametric
    # models (ComfMod 3) with ComfStand 0 or 22 stopped EnergyPlus. The model of accim 0.x of the repository is
    # older than SetAST_Master, which modify_accis adds with the subprograms of this version, so they are
    # replaced with those of accim 0.8 first.
    from besos.eppy_funcs import get_building

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = get_building(str(tmp_path / 'legacy.idf'))
    accis.modify_accis(building, comf_stand=1, cat=3, comf_mod=3, hvac_mode=2, vent_ctrl=0)
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
    assert _program_lines(building, 'SetInputData')[:3] == ['set ComfStand = 0', 'set CAT = 3', 'set ComfMod = 3']


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


def test_deprecated_modifyaccis_sets_m_and_n(building):
    with pytest.warns(DeprecationWarning, match='addAccis is deprecated'):
        accis_single_idf_funcs.addAccis(idf=building, **LEGACY_ADD_ACCIS_ARGS)

    with pytest.warns(DeprecationWarning, match='modifyAccis is deprecated'):
        accis_single_idf_funcs.modifyAccis(idf=building, ComfStand=99, ComfMod=3, CAT=80, HVACmode=2, VentCtrl=0,
                                           CustAST_m=0.3, CustAST_n=18)
    assert _setast_lines(building) == ['run SetAST_Master']
    assert {(i['m'], i['n']) for i in _zone_inputs(building).values()} == {(0.3, 18)}


def test_deprecated_class_sets_the_arguments_of_all_the_zones(building):
    # In accim 0.x, the method modifyAccis of the deprecated class also appended the lines of the comfort model to
    # SetAST; now each zone runs SetAST with its own arguments
    with pytest.warns(DeprecationWarning, match='addAccis is deprecated'):
        job = accis_single_idf.addAccis(idf=building, **LEGACY_ADD_ACCIS_ARGS)

    job.modifyAccis(ComfStand=2, CAT=80, ComfMod=0, HVACmode=2, VentCtrl=0)
    job.modifyAccis(ComfStand=2, CAT=80, ComfMod=3, HVACmode=2, VentCtrl=0)

    assert _setast_lines(building) == ['run SetAST_Master']
    assert job.occupied_zones and job.windows_and_doors
    # The EMS programs, as attributes of the object
    assert list(job.SetAST.obj[2:]) == ['run SetAST_Master']
    assert job.SetInputData is None and job.SetVOFinputData is None
    assert len(job.zone_input_programs) == len(job.occupied_zones) == 2
    for program in job.zone_input_programs.values():
        assert program.Program_Line_1 == 'set ComfStand = 2' and program.Program_Line_3 == 'set ComfMod = 3'
