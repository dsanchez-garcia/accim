"""Tests for the mixed mode of the existing HVAC systems (ScriptType 'ex_mm').

Until 2026-11-01, 'ex_mm' looked for the HVAC equipment of each zone (one heating and one cooling object, through the
zone equipment, the air loops or the names of the objects) and read whether its coils heated or cooled: AddAccis
rejected the models with several kinds of coils (the sample OSM office), and the models whose zones had no cooling
equipment, such as the sample model with electric radiators, stopped EnergyPlus ("Variable = 'BLOCK1_ZONE2_COOLCOIL'
used in expression has not been initialized"). Now it reads, for each zone, the load to the setpoints that its
thermostat asks the HVAC system for ('Zone Predicted Sensible Load to Setpoint Heat Transfer Rate'), which is 0 when
the temperature of the zone is between its setpoints, and so when the HVAC system is off, whatever its equipment. With
the sample model with PTACs, the results are the same as with its coils. The design days, on which mixed mode
air-conditions the zones with the windows closed, are tested with 'vrf_mm' too.
"""
import lzma
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import default_energyplus_folder
from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
from accim.sim.ems.inputs import input_lines, input_values
from accim.sim.ems.programs import accis_programs
from accim.sim.hvac.existing import LOAD_TO_SETPOINT_OUTPUT
from accim.sim.hvac.schedules import DESIGN_DAY_SCHEDULE

REPO = Path(__file__).resolve().parents[2]
RADIATORS = REPO / 'tests' / 'core' / 'golden_master' / 'inputs' / 'exrad.idf.xz'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_energyplus = pytest.mark.skipif(not (IDD_25_1.exists() and RADIATORS.exists()),
                                      reason='needs EnergyPlus 25.1 and the input models of the golden master')
TIMESTEP = 0.25
WINDOW = 'Zone1_Win'


def _model(script_type):
    return SimpleNamespace(script_type=script_type, ems_names=['Zone1'], ems_zones=['Zone1'], is_mixed_mode=True,
                           windows=[WINDOW], window_zones=['Zone1'])


@pytest.mark.parametrize('script_type, first_line', [
    ('ex_mm', 'if {}_LoadToSetpoint == 0'),
    ('vrf_mm', 'if {}_CoolCoil==0'),
])
def test_the_programs_read_whether_the_hvac_system_is_off(script_type, first_line):
    programs = dict(accis_programs(_model(script_type)))

    assert programs['ApplyAST_Zone1'][0] == first_line.format('Zone1')
    assert programs[f'SetWindowOperation_{WINDOW}'][0] == first_line.format(WINDOW)
    coils = [line for lines in programs.values() for line in lines if 'Coil' in line]
    assert bool(coils) is (script_type == 'vrf_mm')


def _programs(script_type='ex_mm'):
    """The programs of ACCIS of one zone with a window in mixed mode (HVACmode 2, VentCtrl 0), with the existing HVAC
    systems ('ex_mm') or the VRF systems of accim ('vrf_mm'), INT EN16798-1 category II and the adaptive comfort
    mode."""
    programs = dict(accis_programs(_model(script_type)))
    arguments = dict(comfort_standard=1, category=2, comfort_mode=3, hvac_mode=2, ventilation_control=0, setpoint_tolerance=0.1)
    programs['SetInputData_Zone1'] = input_lines(input_values(arguments), mixed_mode=True)
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    erl.strict = True
    erl.run('InitASTvariables')
    return erl


def _timestep(erl, load, design_day=0.0, occupants=1.0):
    # A running mean outdoor temperature of 20 °C: setpoints of 28.3 and 21.5 °C, a ventilation setpoint of 25.4 °C
    # (the comfort temperature) and a minimum outdoor temperature of 14.5 °C. The zone, at 27 °C and occupied, is
    # warmer than the outdoor air, at 20 °C: the windows open if the HVAC system is off. A negative load to the
    # setpoints ('ex_mm') is a cooling coil that cools ('vrf_mm'), and a positive one a heating coil that heats
    for name in ('Zone1', WINDOW):
        for suffix, value in (('_OpT', 27.0), ('_OutT', 20.0), ('_WindSpeed', 1.0), ('_LoadToSetpoint', load),
                              ('_CoolCoil', max(-load, 0.0)), ('_HeatCoil', max(load, 0.0))):
            erl.set(name + suffix, value)
    for name, value in dict(RMOT=20.0, PMOT=20.0, DayOfYear=180.0, CurrentTime=12.0, ZoneTimeStep=TIMESTEP,
                            Occ_count_Zone1=occupants, Zone1_Win_Occ_count=occupants, DesignDay=design_day).items():
        erl.set(name, value)
    erl.run('RunACCIS_Zone1')
    return erl.get(f'{WINDOW}_VentOpenFact'), erl.get('VentHours_Zone1')


def test_the_windows_open_only_when_the_thermostat_asks_for_no_load():
    erl = _programs()

    # The thermostat asks for cooling (the HVAC system cools): the windows stay closed and the setpoints apply
    assert _timestep(erl, load=-500.0) == (0, 0)
    assert erl.get('ACST_Act_Zone1') == pytest.approx(28.3, abs=1e-3)
    # The temperature of the zone is between its setpoints (the HVAC system is off): the windows open
    assert _timestep(erl, load=0.0) == (1, TIMESTEP)
    # The thermostat asks for heating: the windows close
    assert _timestep(erl, load=200.0) == (0, 0)


@pytest.mark.parametrize('script_type', ['ex_mm', 'vrf_mm'])
def test_on_the_design_days_the_zones_are_air_conditioned_with_the_windows_closed(script_type):
    """On the design days (DesignDay 1), the setpoints apply also without occupants, and the windows stay closed: with
    the HVAC systems off on the design days without occupants (often the winter design day), EnergyPlus sized them
    for no load, and stopped (the furnaces of the example files House-2FurnaceAC-* with 'ex_mm': 'air flow less than
    ...'). 'vrf_mm' has the same rule since 2026-11-07, at the choice of the author: its VRF systems were also sized
    without the timesteps without occupants or with the windows open."""
    erl = _programs(script_type)

    # Not a design day: without occupants, the HVAC system is off; with them, the windows open
    assert _timestep(erl, load=0.0, occupants=0.0) == (0, 0)
    assert (erl.get('ACST_Act_Zone1'), erl.get('AHST_Act_Zone1')) == (100, -100)
    assert _timestep(erl, load=0.0) == (1, TIMESTEP)
    # A design day: the setpoints apply, with or without occupants, and the windows stay closed
    for occupants in (0.0, 1.0):
        assert _timestep(erl, load=0.0, design_day=1.0, occupants=occupants) == (0, 0)
        assert erl.get('ACST_Act_Zone1') == pytest.approx(28.3, abs=1e-3)
        assert erl.get('AHST_Act_Zone1') == pytest.approx(21.5, abs=1e-3)


@pytest.fixture
def radiators(tmp_path):
    from besos.eppy_funcs import get_building

    path = tmp_path / 'radiators.idf'
    path.write_bytes(lzma.decompress(RADIATORS.read_bytes()))
    return get_building(str(path))


@needs_energyplus
def test_ex_mm_reads_the_load_of_the_zone_of_each_zone_and_window(radiators):
    from accim.sim.accis import add_accis_to_idf

    model = add_accis_to_idf(radiators, script_type='ex_mm', output_type='simplified', output_frequencies=['hourly'],
                             keep_existing_outputs=False, setpoint_type='temperature', verbose=False)

    sensors = {s.Name: s for s in radiators.idfobjects['EnergyManagementSystem:Sensor']}
    assert not [name for name in sensors if name.endswith('_CoolCoil') or name.endswith('_HeatCoil')]
    assert 'InitExisHVACCoils' not in [p.Name for p in radiators.idfobjects['EnergyManagementSystem:Program']]
    names = [*zip(model.ems_names, model.ems_zones), *zip(model.windows, model.window_zones)]
    assert model.windows and len(names) == len(model.ems_names) + len(model.windows)
    for name, zone in names:
        sensor = sensors[f'{name}_LoadToSetpoint']
        assert sensor.OutputVariable_or_OutputMeter_Index_Key_Name == zone
        assert sensor.OutputVariable_or_OutputMeter_Name == LOAD_TO_SETPOINT_OUTPUT


@needs_energyplus
@pytest.mark.parametrize('script_type', ['ex_mm', 'vrf_mm'])
def test_mixed_mode_reads_the_design_days(radiators, script_type):
    from accim.sim.accis import add_accis_to_idf

    add_accis_to_idf(radiators, script_type=script_type, supply_air_temp_input_method='temperature difference',
                     output_type='simplified', output_frequencies=['hourly'], keep_existing_outputs=False,
                     setpoint_type='temperature', verbose=False)

    # The design days, from a schedule that is 1 on the days of the types SummerDesignDay and WinterDesignDay
    design_day = [s for s in radiators.idfobjects['EnergyManagementSystem:Sensor'] if s.Name == 'DesignDay'][0]
    assert design_day.OutputVariable_or_OutputMeter_Index_Key_Name == DESIGN_DAY_SCHEDULE
    assert design_day.OutputVariable_or_OutputMeter_Name == 'Schedule Value'
    schedule = [s for s in radiators.idfobjects['Schedule:Compact'] if s.Name == DESIGN_DAY_SCHEDULE][0]
    assert [str(v) for v in schedule.obj[3:]] == ['Through: 12/31', 'For: SummerDesignDay WinterDesignDay',
                                                  'Until: 24:00,1', 'For: AllOtherDays', 'Until: 24:00,0']
    programs = {p.Name: p.fieldvalues[2:] for p in radiators.idfobjects['EnergyManagementSystem:Program']}
    zone_programs = [name for name in programs if name.startswith('ApplyAST_')]
    window_programs = [name for name in programs if name.startswith('SetWindowOperation_')]
    assert zone_programs and window_programs
    for name in zone_programs + window_programs:
        assert 'if DesignDay == 1' in [str(line).strip() for line in programs[name]]


@needs_energyplus
def test_hvac_zone_map_is_deprecated(radiators):
    from accim.sim.accis import add_accis_to_idf

    with pytest.warns(DeprecationWarning, match='hvac_zone_map is deprecated since accim 1.0.0 and has no effect'):
        add_accis_to_idf(radiators, script_type='ex_mm', output_type='simplified', output_frequencies=['hourly'],
                         keep_existing_outputs=False, setpoint_type='temperature', verbose=False,
                         hvac_zone_map={'Block1:Zone1 Electric Baseboard': 'Block1:Zone1'})
