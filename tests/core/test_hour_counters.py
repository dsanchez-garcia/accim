"""Tests for the hour counters of the ACCIS (CountHours_<zone>, CountHoursNoApp_<zone> and the ventilation hours of
ApplyAST_<zone>), run with the rules of the EMS.

Found on 2026-11-01 (and as in accim 0.x):
- CountHoursNoApp_<zone> did not set the occupied comfortable hours when the operative temperature was out of the
  setpoints, so they kept the value of the previous timestep: after an occupied timestep within the setpoints, the
  following timesteps out of them counted as occupied and comfortable, and 'Occupied Comfortable Hours_No
  Applicability' could exceed 'Occupied Hours' (107 % of them in a week of the sample model with natural
  ventilation);
- CountHours_<zone> set nothing when the operative temperature was below the heating setpoint within the
  applicability limits (its branch for the cold hours could not be reached), so 'Discomfortable Applicable Cold
  Hours' was never counted and the counters kept the values of the previous timestep;
- CountHours_<zone> ran before SetAST, with the setpoints of the previous timestep (0 in the first timestep of each
  environment);
- in mixed mode with HVACmode 0, ApplyAST_<zone> did not set the ventilation hours, which the building average of
  make_averages reads, so EnergyPlus stopped ("used in expression has not been initialized"); likewise the occupied
  comfortable hours with EnergyPlus 26.2.
"""
from types import SimpleNamespace

import pytest

from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
from accim.sim.ems.inputs import input_lines, input_values
from accim.sim.ems.programs import accis_programs

TIMESTEP = 0.25
# INT EN16798-1, category II, adaptive, with a tolerance of 0.1: with a running mean outdoor temperature of 20 °C,
# the comfort temperature is 25.4 °C and the setpoints without tolerance are 28.4 and 21.4 °C; the applicability
# limits are 10 and 30 °C
EN16798_II = dict(comf_stand=1, cat=2, comf_mod=3, ast_tol=0.1)
APPLICABILITY = ['ComfHours', 'DiscomfAppHotHours', 'DiscomfAppColdHours', 'DiscomfNonAppHotHours',
                 'DiscomfNonAppColdHours']


def _programs(mixed_mode=False, **arguments):
    """The programs of ACCIS of one zone, at the beginning of an environment, without the variables that EnergyPlus
    initialises after running the programs once (so that a variable that is not set in a timestep is not a
    number)."""
    model = SimpleNamespace(ems_names=['Zone1'], ems_zones=['Zone1'], is_mixed_mode=mixed_mode, windows=[],
                            window_zones=[])
    programs = dict(accis_programs(model))
    arguments = dict(dict(hvac_mode=0, **EN16798_II), **arguments)
    programs['SetInputData_Zone1'] = input_lines(input_values(arguments), mixed_mode=mixed_mode)
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    erl.strict = True
    erl.run('InitASTvariables')
    return erl


def _timestep(erl, operative=24.0, occupants=1.0, outdoor=20.0):
    for name, value in dict(RMOT=outdoor, PMOT=outdoor, DayOfYear=180.0, CurrentTime=12.0, ZoneTimeStep=TIMESTEP,
                            Zone1_OpT=operative, Occ_count_Zone1=occupants, Zone1_CoolCoil=0.0, Zone1_HeatCoil=0.0,
                            Zone1_WindSpeed=1.0, Zone1_OutT=outdoor).items():
        erl.set(name, value)
    erl.run('RunACCIS_Zone1')
    return {name: erl.get(f'{name}_Zone1') for name in
            APPLICABILITY + ['ComfHoursNoApp', 'OccComfHoursNoApp', 'OccDiscomfHoursNoApp', 'OccHours']}


def _check_totals(hours):
    # Each timestep is counted once by the applicability counters, and the occupied ones once as comfortable or not
    assert sum(hours[name] for name in APPLICABILITY) == TIMESTEP
    assert hours['OccComfHoursNoApp'] + hours['OccDiscomfHoursNoApp'] == hours['OccHours']


def _counted(hours, *names):
    return {name for name, value in hours.items() if value} == set(names)


@pytest.mark.parametrize('mixed_mode', [False, True])
def test_each_timestep_is_counted_once(mixed_mode):
    erl = _programs(mixed_mode=mixed_mode)

    # Occupied and within the setpoints
    hours = _timestep(erl, operative=24.0)
    _check_totals(hours)
    assert _counted(hours, 'ComfHours', 'ComfHoursNoApp', 'OccComfHoursNoApp', 'OccHours')
    # Occupied and above the cooling setpoint: no longer comfortable (before, the occupied comfortable hours kept
    # the value of the previous timestep)
    hours = _timestep(erl, operative=29.0)
    _check_totals(hours)
    assert _counted(hours, 'DiscomfAppHotHours', 'OccDiscomfHoursNoApp', 'OccHours')
    # Occupied and below the heating setpoint: cold (before, CountHours set nothing)
    hours = _timestep(erl, operative=20.0)
    _check_totals(hours)
    assert _counted(hours, 'DiscomfAppColdHours', 'OccDiscomfHoursNoApp', 'OccHours')
    # Without occupants
    hours = _timestep(erl, operative=20.0, occupants=0.0)
    _check_totals(hours)
    assert _counted(hours, 'DiscomfAppColdHours')
    hours = _timestep(erl, operative=24.0, occupants=0.0)
    _check_totals(hours)
    assert _counted(hours, 'ComfHours', 'ComfHoursNoApp')
    # Out of the applicability limits
    hours = _timestep(erl, operative=24.0, outdoor=35.0)
    _check_totals(hours)
    assert hours['DiscomfNonAppHotHours'] == TIMESTEP
    hours = _timestep(erl, operative=24.0, outdoor=5.0)
    _check_totals(hours)
    assert hours['DiscomfNonAppColdHours'] == TIMESTEP


def test_the_hours_are_counted_with_the_setpoints_of_the_timestep():
    erl = _programs()

    # In the first timestep of an environment (before, with setpoints of 0, it was a hot hour)
    hours = _timestep(erl, operative=24.0)
    assert hours['ComfHours'] == hours['ComfHoursNoApp'] == TIMESTEP
    # With a running mean outdoor temperature of 30 °C, the setpoints without tolerance are 31.7 and 24.7 °C: 30 °C is
    # within them, but above the cooling setpoint of the previous timestep (28.4 °C)
    hours = _timestep(erl, operative=30.0, outdoor=30.0)
    assert erl.get('ACSTnoTol_Zone1') == pytest.approx(31.7)
    assert hours['ComfHours'] == hours['ComfHoursNoApp'] == TIMESTEP
    assert hours['DiscomfAppHotHours'] == 0


@pytest.mark.parametrize('hvac_mode', [0, 1, 2])
def test_the_ventilation_hours_are_set_in_every_mode(hvac_mode):
    erl = _programs(mixed_mode=True, hvac_mode=hvac_mode, vent_ctrl=0)

    _timestep(erl, operative=24.0, outdoor=20.0)

    # A number in every timestep, which the building average of make_averages can read
    assert erl.get('VentHours_Zone1') is not None
    if hvac_mode == 0:
        assert erl.get('VentHours_Zone1') == 0
