"""Tests for the setpoints of CHN Yang (comfort standard 6) with comfort modes 2 and 3.

Until 2026-11-03, within the applicability limits, the heating setpoint of comfort mode 2 used the formula of the
cooling setpoint (PMOT*0.30+25.9 with category 80, PMOT*0.30+23.6 with 90), as in accim 0.x, so both setpoints were
equal (30.4 °C for a running mean outdoor temperature of 15 °C with category 80). The author checked the formulas of
comfort modes 2 and 3 against the source of the model of Yang and corrected the heating setpoint of comfort mode 2,
which within the limits is now that of comfort mode 3 (PMOT*0.32+14.88 with category 80, PMOT*0.31+17.14 with 90).
"""
from types import SimpleNamespace

import pytest

from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
from accim.sim.ems.inputs import input_lines, input_values
from accim.sim.ems.programs import accis_programs

TOLERANCE = 0.1
#: The formulas of CHN Yang within its applicability limits: category -> ((slope, intercept) of the cooling setpoint,
#: (slope, intercept) of the heating setpoint)
FORMULAS = {80: ((0.30, 25.9), (0.32, 14.88)), 90: ((0.30, 23.6), (0.31, 17.14))}


def _setpoints(category, comfort_mode, pmot):
    """ACST and AHST of the programs of ACCIS (CHN Yang) for a running mean outdoor temperature."""
    model = SimpleNamespace(ems_names=['Zone1'], is_mixed_mode=False, windows=[])
    programs = dict(accis_programs(model))
    programs['SetInputData_Zone1'] = input_lines(input_values(dict(
        comfort_standard=6, category=category, comfort_mode=comfort_mode, hvac_mode=0, ventilation_control=0,
        setpoint_tolerance=TOLERANCE)), mixed_mode=False)
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    for name, value in dict(RMOT=pmot, PMOT=pmot, DayOfYear=180.0, CurrentTime=12.0).items():
        erl.set(name, value)
    for name in ['SetInputData_Zone1', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST', 'SetASTnoTol']:
        erl.run(name)
    return erl.get('ACST'), erl.get('AHST')


@pytest.mark.parametrize('comfort_mode', [2, 3])
@pytest.mark.parametrize('category', [80, 90])
@pytest.mark.parametrize('pmot', [-5.0, 15.0, 28.0])
def test_within_the_applicability_limits_the_setpoints_follow_the_formulas_of_yang(comfort_mode, category, pmot):
    (cooling_slope, cooling_intercept), (heating_slope, heating_intercept) = FORMULAS[category]

    acst, ahst = _setpoints(category, comfort_mode, pmot)

    assert acst == pytest.approx(pmot * cooling_slope + cooling_intercept - TOLERANCE)
    assert ahst == pytest.approx(pmot * heating_slope + heating_intercept + TOLERANCE)
    assert ahst < acst


@pytest.mark.parametrize('category', [80, 90])
@pytest.mark.parametrize('pmot', [-5.0, 15.0, 28.0])
def test_comfort_modes_2_and_3_have_the_same_setpoints_within_the_applicability_limits(category, pmot):
    assert _setpoints(category, 2, pmot) == _setpoints(category, 3, pmot)


@pytest.mark.parametrize('category, pmot, expected', [
    # Comfort mode 2: the static setpoints outside the applicability limits (-7 to 30 °C)
    (80, -10.0, (25, 19)), (80, 32.0, (27, 22)), (90, -10.0, (24, 20)), (90, 32.0, (26, 23)),
])
def test_outside_the_applicability_limits_comfort_mode_2_has_static_setpoints(category, pmot, expected):
    acst, ahst = _setpoints(category, 2, pmot)

    assert (acst, ahst) == (pytest.approx(expected[0] - TOLERANCE), pytest.approx(expected[1] + TOLERANCE))
