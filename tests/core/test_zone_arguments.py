"""Tests for the arguments of each zone (``zone_arguments`` of AddAccis and modify_accis).

Since accim 1.0.0, each occupied zone has the arguments of the ACCIS in its EMS program SetInputData_<zone>, and
its program RunACCIS_<zone> runs it and then the programs that calculate and apply the setpoints (SetAppLimits,
ApplyCAT, SetComfTemp, SetAST...), which are shared by all the zones. Some variables of these programs keep their
value from one timestep to the next (the setpoints of ESP CTE at the end of the day, the setpoints without tolerance
that CountHours_<zone> reads), so each zone restores and stores its own values (ACST_<zone>...); otherwise a zone
would take those of the zone that ran before it.
"""
import shutil
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import default_energyplus_folder
from accim.sim.ems.erl import ErlProgramSet, ErlRuntimeError, variables_in_programs
from accim.sim.ems.inputs import (
    INPUT_VARIABLES,
    ZONE_ARGUMENTS,
    check_zone_arguments,
    input_lines,
    input_programs,
    input_values,
    read_inputs,
    resolve_zone_arguments,
    set_inputs,
    zone_names,
)
from accim.sim.ems.programs import accis_programs
from accim.sim.generation import Combination, GenerationArguments, zone_arguments_errors, zone_input_arguments

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
# An output IDF of accim 0.x (before SetAST_Master), with one program SetInputData for all the zones
LEGACY_IDF = next((REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'runEp').glob('TestModel_V2510*.idf'), None)
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_energyplus = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                                      reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ADD_ACCIS_ARGS = dict(supply_air_temp_input_method='temperature difference', output_type='simplified',
                      output_freqs=['hourly'], output_keep_existing=False, temp_ctrl='temperature', verbose_mode=False)
EN16798_II = dict(comf_stand=1, cat=2, comf_mod=3)


# Inputs -------------------------------------------------------------------------------------------------------

class _Program:
    """An EMS program as eppy has it: the fields in ``obj``, and its lines as attributes Program_Line_<n>."""

    def __init__(self, name, lines):
        self.__dict__['obj'] = ['EnergyManagementSystem:Program', name, *lines]

    @property
    def Name(self):  # noqa: N802 (the field of eppy)
        return self.obj[1]

    def __setattr__(self, name, value):
        number = int(name.rsplit('_', 1)[1])
        self.obj[1 + number] = value


def test_the_inputs_of_a_zone_are_all_the_arguments_of_the_accis():
    lines = input_lines(mixed_mode=True)
    # The first 12 lines are those of SetInputData of accim 0.x, in the same order
    assert lines[:12] == [
        'set ComfStand = 1', 'set CAT = 1', 'set ComfMod = 2', 'set HVACmode = 2', 'set VentCtrl = 0',
        'set VSToffset = 0', 'set MinOToffset = 7', 'set MaxWindSpeed = 6', 'set ACSTtol = -0.25',
        'set AHSTtol = 0.25', 'set CoolSeasonStart = 121', 'set CoolSeasonEnd = 274']
    # Then those of ApplyCAT, SetAST and SetAppLimits, and, in mixed mode, those of SetVOFinputData
    assert lines[12:] == [
        'set CATcoolOffset = 0', 'set CATheatOffset = 0', 'set SetpointAcc = 10000', 'set m = 0.31',
        'set n = 17.8', 'set CustAST_ACSToffset = 3.5', 'set CustAST_AHSToffset = -3.5',
        'set CustAST_ACSTaul = 33.5', 'set CustAST_ACSTall = 10', 'set CustAST_AHSTaul = 33.5',
        'set CustAST_AHSTall = 10', 'set MaxTempDiffVOF = 6', 'set MinTempDiffVOF = 1', 'set MultiplierVOF = 0.25']
    assert input_lines(mixed_mode=False) == lines[:-3]
    # Every argument of modify_accis that sets an input can be given for each zone
    assert set(ZONE_ARGUMENTS) == {item.argument for item in INPUT_VARIABLES}


def test_input_values_of_the_arguments():
    values = input_values(dict(comf_stand=2, cat=None, ast_tol=0.25, cool_season_start='01/06', cust_ast_m=0.3))

    assert values == {'ComfStand': 2, 'ACSTtol': -0.25, 'AHSTtol': 0.25, 'CoolSeasonStart': 152, 'm': 0.3}
    assert input_lines(values, mixed_mode=False)[:3] == ['set ComfStand = 2', 'set CAT = 1', 'set ComfMod = 2']


def test_set_and_read_the_inputs_of_a_program():
    program = _Program('SetInputData_Zone1', input_lines(mixed_mode=False))

    missing = set_inputs(program, {'comfstand': 13, 'ComfMod': 1.2, 'MultiplierVOF': 0.5})

    # The names are case-insensitive, as in the EMS; the inputs that the program does not have are not added
    assert missing == ['MultiplierVOF']
    values = read_inputs(program)
    assert (values['ComfStand'], values['ComfMod'], values['CAT']) == (13, 1.2, 1)
    assert 'MultiplierVOF' not in values


@pytest.mark.parametrize('zone_arguments, message', [
    ([('Zone1', {'cat': 2})], 'must be a dictionary with the arguments of each zone'),
    ({'Zone1': 2}, "The arguments of the zone 'Zone1'"),
    ({'Zone1': {'colour': 2}}, "'colour' \\(zone 'Zone1'\\) cannot be given for each zone"),
    # The names of accim 0.x are not accepted, with a hint
    ({'Zone1': {'ComfStand': 2}}, "Its name is 'comf_stand'"),
    ({'Zone1': {'comf_stand': [1, 2]}}, 'must be one value'),
    ({'Zone1': {'setpoint_acc': -1}}, 'setpoint_acc cannot be less than 0'),
])
def test_wrong_zone_arguments(zone_arguments, message):
    with pytest.raises(ValueError, match=message):
        check_zone_arguments(zone_arguments)


def test_the_zones_can_be_given_by_any_of_their_names():
    targets = [SimpleNamespace(zone_name='Block1:Zone1', df_key='Block1:Zone1', ems_suffix='Block1_Zone1'),
               SimpleNamespace(zone_name='Floor 2', df_key='Bedroom People', ems_suffix='Bedroom_People')]
    names = zone_names(targets)

    resolved = resolve_zone_arguments({'block1:zone1': {'cat': 2}, 'BEDROOM PEOPLE': {'cat': 3},
                                       'Floor 2': {'comf_mod': 2}, 'Block1_Zone1': {'comf_mod': 3}}, names)

    assert resolved == {'Block1_Zone1': {'cat': 2, 'comf_mod': 3}, 'Bedroom_People': {'cat': 3, 'comf_mod': 2}}
    with pytest.raises(ValueError, match=r"zones \['Kitchen'\] of zone_arguments are not occupied zones"):
        resolve_zone_arguments({'Kitchen': {'cat': 2}}, names)
    assert resolve_zone_arguments({'Kitchen': {'cat': 2}}, names, strict=False) == {}


# Arguments of the zones in the output IDFs of AddAccis -----------------------------------------------------------

def test_the_arguments_of_a_zone_in_an_output_idf():
    args = GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[0, 2], vent_ctrl=[1],
                               vst_offset=[1], cust_ast_m=0.3)
    mixed_mode = Combination(1, 3, 3, 2, 1, 1.0, 50.0, 50.0, 0.1)
    air_conditioned = Combination(1, 3, 3, 0, None, None, None, None, 0.1)

    arguments = zone_input_arguments(args, mixed_mode)
    assert (arguments['comf_stand'], arguments['vent_ctrl'], arguments['vst_offset'], arguments['ast_tol'],
            arguments['cust_ast_m']) == (1, 1, 1.0, 0.1, 0.3)
    # ESP CTE has category 1 and comfort mode 0, and HVACmode 0 the ventilation arguments of no ventilation
    arguments = zone_input_arguments(args, mixed_mode, {'comf_stand': 0, 'hvac_mode': 0})
    assert (arguments['cat'], arguments['comf_mod'], arguments['vent_ctrl'], arguments['vst_offset'],
            arguments['min_ot_offset'], arguments['max_wind_speed']) == (1, 0, 0, 0, 7, 6)
    # A zone with natural ventilation in an output IDF without it takes the first ventilation arguments
    arguments = zone_input_arguments(args, air_conditioned, {'hvac_mode': 2})
    assert (arguments['vent_ctrl'], arguments['vst_offset'], arguments['min_ot_offset']) == (1, 1.0, 50.0)


@pytest.mark.parametrize('overrides, mixed_mode, error', [
    ({}, True, None),
    ({'comf_stand': 2}, True, 'cat 3 is not a category of comf_stand 2'),
    ({'comf_stand': 4, 'cat': 1, 'comf_mod': 0}, True, 'comf_stand 4 has no setpoints with comf_mod 0'),
    ({'comf_stand': 22, 'cat': 2}, True, None),
    ({'comf_stand': 0}, True, None),
    ({'comf_stand': 23}, True, 'comf_stand 23 is not a comfort standard'),
    ({'hvac_mode': 2}, False, 'hvac_mode 2 is not valid with this script type'),
    ({'hvac_mode': 1, 'vent_ctrl': 2}, True, 'vent_ctrl 2 is not valid with hvac_mode 1'),
])
def test_the_arguments_of_a_zone_must_give_setpoints(overrides, mixed_mode, error):
    args = GenerationArguments(comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[2], vent_ctrl=[0])
    errors = zone_arguments_errors(zone_input_arguments(args, Combination(1, 3, 3, 2, 0, 0.0, 50.0, 50.0, 0.1),
                                                        overrides), mixed_mode)
    if error is None:
        assert errors == []
    else:
        assert any(error in e for e in errors), errors


# The programs of each zone, run with the rules of the EMS ----------------------------------------------------------

def _programs(zone_arguments):
    """The programs of ACCIS of two air-conditioned zones, at the beginning of the first environment."""
    model = SimpleNamespace(ems_names=['Zone1', 'Zone2'], ems_zones=['Zone1', 'Zone2'], is_mixed_mode=False,
                            windows=[], window_zones=[])
    programs = dict(accis_programs(model))
    for zone, arguments in zone_arguments.items():
        arguments = dict(dict(hvac_mode=0, ast_tol=0.1), **arguments)
        programs[f'SetInputData_{zone}'] = input_lines(input_values(arguments), mixed_mode=False)
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    erl.initialise_set_variables()
    erl.reset()
    erl.strict = True
    erl.run('InitASTvariables')
    return erl


def _timestep(erl, current_time=12.0, outdoor=20.0):
    for name, value in dict(RMOT=outdoor, PMOT=outdoor, DayOfYear=180.0, CurrentTime=current_time,
                            ZoneTimeStep=0.25, Zone1_OpT=24.0, Zone2_OpT=24.0, Occ_count_Zone1=1.0,
                            Occ_count_Zone2=1.0).items():
        erl.set(name, value)
    for zone in ['Zone1', 'Zone2']:
        erl.run(f'RunACCIS_{zone}')


def test_zones_with_the_same_arguments_have_the_setpoints_of_the_whole_model():
    # INT EN16798-1, category II, adaptive: Tcomf = 0.33*RMOT + 18.8, setpoints Tcomf + 3 and Tcomf - 4, with the
    # tolerance of 0.1 towards the comfort temperature
    erl = _programs({'Zone1': EN16798_II, 'Zone2': EN16798_II})

    _timestep(erl)

    for zone in ['Zone1', 'Zone2']:
        assert erl.get(f'ComfTemp_{zone}') == pytest.approx(25.4)
        assert erl.get(f'roundedACST_{zone}') == erl.get('roundedACST') == pytest.approx(28.3, abs=1e-4)
        assert erl.get(f'roundedAHST_{zone}') == erl.get('roundedAHST') == pytest.approx(21.5, abs=1e-4)
        assert (erl.get(f'ACSTnoTol_{zone}'), erl.get(f'AHSTnoTol_{zone}')) == (pytest.approx(28.4),
                                                                                pytest.approx(21.4))
        assert (erl.get(f'ACST_Act_{zone}'), erl.get(f'AHST_Act_{zone}')) == (pytest.approx(28.3),
                                                                              pytest.approx(21.5))


def test_each_zone_has_the_setpoints_of_its_arguments():
    # Zone2: INT ASHRAE 55, 80 % acceptability, adaptive: Tcomf = 0.31*PMOT + 17.8, setpoints Tcomf +- 3.5
    erl = _programs({'Zone1': EN16798_II, 'Zone2': dict(comf_stand=2, cat=80, comf_mod=3)})

    _timestep(erl)

    assert (erl.get('ComfTemp_Zone1'), erl.get('ComfTemp_Zone2')) == (pytest.approx(25.4), pytest.approx(24.0))
    assert (erl.get('ACST_Act_Zone1'), erl.get('AHST_Act_Zone1')) == (pytest.approx(28.3), pytest.approx(21.5))
    assert (erl.get('ACST_Act_Zone2'), erl.get('AHST_Act_Zone2')) == (pytest.approx(27.4), pytest.approx(20.6))
    # The variables of the whole model have the values of the last zone
    assert erl.get('roundedACST') == erl.get('roundedACST_Zone2')
    assert erl.get('ComfStand') == 2


def test_each_zone_keeps_its_own_setpoints_from_one_timestep_to_the_next():
    # ESP CTE sets no setpoint at the end of the day (CurrentTime 24), when they keep their previous value: that of
    # its zone, not that of the zone that ran before it
    erl = _programs({'Zone1': dict(comf_stand=0, cat=1, comf_mod=0), 'Zone2': EN16798_II})

    _timestep(erl, current_time=23.5)
    assert (erl.get('ACST_Act_Zone1'), erl.get('AHST_Act_Zone1')) == (pytest.approx(26.9), pytest.approx(17.1))
    _timestep(erl, current_time=24.0)

    assert (erl.get('ACST_Act_Zone1'), erl.get('AHST_Act_Zone1')) == (pytest.approx(26.9), pytest.approx(17.1))
    assert (erl.get('ACST_Act_Zone2'), erl.get('AHST_Act_Zone2')) == (pytest.approx(28.3), pytest.approx(21.5))


def test_a_zone_without_setpoints_stops_the_simulation():
    # CHN GBT50785 Cold (4) has no setpoints with the comfort mode 0: the setpoints of the zone are Null, as when they
    # were not set, instead of those of the other zone
    erl = _programs({'Zone1': EN16798_II, 'Zone2': dict(comf_stand=4, cat=1, comf_mod=0)})

    with pytest.raises(ErlRuntimeError):
        _timestep(erl)


# The functions of accim ----------------------------------------------------------------------------------------

@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    return get_building(str(tmp_path / 'model.idf'))


def _inputs(building):
    return {zone: read_inputs(program) for zone, program in input_programs(building).items()}


@needs_energyplus
def test_modify_accis_sets_the_arguments_of_each_zone(building):
    from accim.sim.accis import add_accis_to_idf, modify_accis

    add_accis_to_idf(building, script_type='vrf_mm', **ADD_ACCIS_ARGS)
    modify_accis(building, hvac_mode=2, vent_ctrl=0, **EN16798_II,
                 zone_arguments={'block1:zone2': {'comf_stand': 2, 'cat': 80, 'ast_tol': 0.25}})

    inputs = _inputs(building)
    assert sorted(inputs) == ['Block1_Zone1', 'Block1_Zone2']
    assert [inputs['Block1_Zone1'][v] for v in ('ComfStand', 'CAT', 'ComfMod', 'ACSTtol')] == [1, 2, 3, -0.1]
    assert [inputs['Block1_Zone2'][v] for v in ('ComfStand', 'CAT', 'ComfMod', 'AHSTtol')] == [2, 80, 3, 0.25]

    # The arguments that are None keep the values of each zone; the zones can also be given by their EMS names
    modify_accis(building, comf_mod=2, zone_arguments={'Block1_Zone1': {'hvac_mode': 0}})
    inputs = _inputs(building)
    assert [inputs['Block1_Zone1'][v] for v in ('ComfStand', 'ComfMod', 'HVACmode')] == [1, 2, 0]
    assert [inputs['Block1_Zone2'][v] for v in ('ComfStand', 'CAT', 'ComfMod', 'HVACmode')] == [2, 80, 2, 2]

    with pytest.raises(ValueError, match='not occupied zones of the model'):
        modify_accis(building, zone_arguments={'Kitchen': {'cat': 2}})


@needs_energyplus
@pytest.mark.parametrize('script_type', ['vrf_mm', 'vrf_ac'])
def test_add_accis_to_idf_adds_the_programs_of_each_zone(building, script_type):
    from accim.sim.accis import add_accis_to_idf

    add_accis_to_idf(building, script_type=script_type, **ADD_ACCIS_ARGS)

    programs = {p.Name: p for p in building.idfobjects['EnergyManagementSystem:Program']}
    mixed_mode = script_type == 'vrf_mm'
    for zone in ['Block1_Zone1', 'Block1_Zone2']:
        assert list(programs[f'SetInputData_{zone}'].obj[2:]) == input_lines(mixed_mode=mixed_mode)
        lines = list(programs[f'RunACCIS_{zone}'].obj[2:])
        assert lines[0] == f'run SetInputData_{zone}'
        assert ('run SetVST' in lines) is mixed_mode
        # The windows of the zone, after its setpoints
        windows = [line for line in lines if line.startswith('run SetWindowOperation_')]
        assert bool(windows) is mixed_mode
        assert all(line.startswith(f'run SetWindowOperation_{zone}_') for line in windows)
    assert 'SetInputData' not in programs and 'SetVOFinputData' not in programs
    assert list(programs['SetAST'].obj[2:]) == ['run SetAST_Master']
    # Only SetGeoVar<zone>, RunACCIS_<zone> and InitASTvariables have calling managers
    managers = [m.Name for m in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]
    assert managers == ['SetGeoVarBlock1_Zone2', 'SetGeoVarBlock1_Zone1', 'RunACCIS_Block1_Zone2',
                        'RunACCIS_Block1_Zone1', 'InitASTvariables']
    outputs = {o.Name for o in building.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert {'Adaptive Cooling Setpoint Temperature', 'Adaptive Cooling Setpoint Temperature_Block1_Zone1',
            'Comfort Temperature_Block1_Zone2'} <= outputs
    assert ('Ventilation Setpoint Temperature_Block1_Zone1' in outputs) is mixed_mode


def _add_accis(tmp_path, monkeypatch, **kwargs):
    from accim.sim.accis import AddAccis

    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    monkeypatch.chdir(tmp_path)
    arguments = dict(ADD_ACCIS_ARGS, script_type='vrf_mm', energyplus_version='auto', comf_stand=[1, 2],
                     cat=[3, 80], comf_mod=[3], hvac_mode=[2], vent_ctrl=[0], confirm_gen=True)
    arguments.update(kwargs)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return AddAccis(**arguments)


@needs_energyplus
def test_add_accis_gives_the_same_arguments_to_a_zone_in_all_the_output_idfs(tmp_path, monkeypatch):
    zone2 = {'comf_stand': 99, 'cat': 80, 'comf_mod': 3, 'hvac_mode': 0, 'cust_ast_m': 0.3, 'cust_ast_n': 18}

    job = _add_accis(tmp_path, monkeypatch, zone_arguments={'Block1:Zone2': zone2})

    assert job.zone_arguments == {'TestModel': {'Block1_Zone2': zone2}}
    assert job.arguments['zone_arguments'] == {'Block1:Zone2': zone2}
    assert sorted(job.output_idfs) == [
        'TestModel[CS_INT ASHRAE55[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf',
        'TestModel[CS_INT EN16798[CA_3[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf']
    for name, comf_stand, cat in [(sorted(job.output_idfs)[0], 2, 80), (sorted(job.output_idfs)[1], 1, 3)]:
        inputs = _inputs(job.output_idfs[name])
        assert [inputs['Block1_Zone1'][v] for v in ('ComfStand', 'CAT', 'HVACmode', 'MinOToffset')] == \
               [comf_stand, cat, 2, 50]
        # The zone of zone_arguments, with the ventilation arguments of HVACmode 0
        assert [inputs['Block1_Zone2'][v] for v in ('ComfStand', 'CAT', 'HVACmode', 'MinOToffset', 'm', 'n')] == \
               [99, 80, 0, 7, 0.3, 18]


@needs_energyplus
@pytest.mark.parametrize('kwargs, message', [
    # INT ASHRAE 55 has no category 3: the zone needs its own category
    (dict(zone_arguments={'Block1:Zone2': {'comf_stand': 2}}), 'cat 3 is not a category of comf_stand 2'),
    (dict(zone_arguments={'Kitchen': {'cat': 2}}), r"zones \['Kitchen'\] of zone_arguments are not occupied zones"),
    (dict(zone_arguments={'Block1:Zone2': {'cat': 2}}, temp_ctrl='pmv'), "zone_arguments needs temp_ctrl"),
])
def test_add_accis_checks_the_arguments_of_the_zones(tmp_path, monkeypatch, kwargs, message):
    with pytest.raises(ValueError, match=message):
        _add_accis(tmp_path, monkeypatch, **kwargs)

    assert not list(tmp_path.glob('TestModel[[]*.idf'))


@needs_energyplus
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_modify_accis_keeps_working_with_the_models_of_earlier_versions(tmp_path):
    from besos.eppy_funcs import get_building

    from accim.sim.accis import modify_accis

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = get_building(str(tmp_path / 'legacy.idf'))

    modify_accis(building, hvac_mode=2, vent_ctrl=0, cust_ast_m=0.3, **EN16798_II)

    programs = {p.Name: p for p in building.idfobjects['EnergyManagementSystem:Program']}
    assert not input_programs(building)
    assert list(programs['SetInputData'].obj[2:5]) == ['set ComfStand = 1', 'set CAT = 2', 'set ComfMod = 3']
    assert list(programs['SetAST'].obj[2:]) == ['set SetpointAcc = 10000', 'set m = 0.3', 'set n = 0',
                                                 'run SetAST_Master']
    # Its programs get the subprograms of this version
    assert 'SetAST_Master' in programs and 'SetAST_CS22_0' in programs
    with pytest.raises(ValueError, match='earlier version of accim'):
        modify_accis(building, zone_arguments={'Block1:Zone1': {'cat': 3}})
