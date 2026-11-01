"""Tests for the subprograms of SetAST of the comfort standards whose setpoints do not depend on the comfort mode.

ESP CTE (ComfStand 0) and INT ISO7730 (ComfStand 22) have the same setpoints in every comfort mode, but in
accim 0.x their subprograms (SetAST_CS0_0 and SetAST_CS22_0) only set them in the branch ``ComfMod == 0``.
The output IDFs of AddAccis set ComfMod 0 for them, but the models of the parametric module keep the
ComfMod of their baseline (3), so a plan such as ``{'ComfStand': [0, 1]}`` stopped EnergyPlus
("Variable = 'ACST' used in expression has not been initialized!" in SetASTnoTol). Now these subprograms
set the setpoints whatever ComfMod is. The other comfort standards keep their branches of ComfMod (13 and
14 use their lines without ComfMod for the comfort modes without their own lines).
"""
from types import SimpleNamespace

import pytest

from accim.sim.ems.erl import ErlProgramSet, variables_in_programs
from accim.sim.ems.inputs import input_lines, input_values
from accim.sim.ems.programs import accis_programs
from accim.sim.ems.setast import MODULAR_COMFORT_MODES, depends_on_comfort_mode, get_setpoint_lines, subprograms


def _setpoints(comf_stand, cat, comf_mod, current_time=12.0, day_of_year=180.0):
    """ACST and AHST of the programs of ACCIS in their first run, as in EnergyPlus (without initialised variables)."""
    model = SimpleNamespace(ems_names=['Zone1'], is_mixed_mode=False, windows=[])
    programs = dict(accis_programs(model))
    programs['SetInputData_Zone1'] = input_lines(input_values(dict(
        comf_stand=comf_stand, cat=cat, comf_mod=comf_mod, hvac_mode=0, vent_ctrl=0, vst_offset=0, min_ot_offset=50,
        max_wind_speed=50, ast_tol=0.1, cool_season_start=121, cool_season_end=274)), mixed_mode=False)
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    for name, value in dict(RMOT=20.0, PMOT=20.0, DayOfYear=day_of_year, CurrentTime=current_time).items():
        erl.set(name, value)
    for name in ['SetInputData_Zone1', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST', 'SetASTnoTol']:
        erl.run(name)
    return erl.get('ACST'), erl.get('AHST')


def test_only_esp_cte_and_int_iso7730_do_not_depend_on_the_comfort_mode():
    assert [cs for cs in MODULAR_COMFORT_MODES if not depends_on_comfort_mode(cs)] == [0, 22]


def test_their_subprograms_have_no_branches_of_comfort_mode():
    programs = subprograms()
    for name in ['SetAST_CS0_0', 'SetAST_CS22_0']:
        assert not any('ComfMod ==' in line for line in programs[name]), name
    assert programs['SetAST_CS0_0'][3:] == get_setpoint_lines(0, 0)
    assert programs['SetAST_CS22_0'][3:] == get_setpoint_lines(22, 0)
    # The others keep them
    for name in ['SetAST_CS1_0', 'SetAST_CS13_0', 'SetAST_CS21_0', 'SetAST_CS99_0']:
        assert any(line.startswith('if (ComfMod == ') for line in programs[name]), name


def test_subprograms_of_some_comfort_standards():
    assert list(subprograms([0, 22])) == ['SetAST_CS0_0', 'SetAST_CS22_0']
    assert list(subprograms([13])) == ['SetAST_CS13_0', 'SetAST_CS13_1', 'SetAST_CS13_2', 'SetAST_CS13_3']
    assert len(subprograms()) == sum(len(range(0, len(modes), 3)) for modes in MODULAR_COMFORT_MODES.values())


@pytest.mark.parametrize('comf_mod', [0, 1, 2, 3])
@pytest.mark.parametrize('current_time, expected', [(6.0, (26.9, 17.1)), (12.0, (24.9, 20.1)), (23.5, (26.9, 17.1))])
def test_esp_cte_sets_its_setpoints_in_every_comfort_mode(comf_mod, current_time, expected):
    acst, ahst = _setpoints(0, 1, comf_mod, current_time=current_time)
    assert (acst, ahst) == (pytest.approx(expected[0]), pytest.approx(expected[1]))


@pytest.mark.parametrize('comf_mod', [0, 2, 3])
@pytest.mark.parametrize('cat, day_of_year, expected', [
    (1, 180.0, (25.4, 23.6)), (2, 180.0, (25.9, 23.1)), (3, 180.0, (26.9, 22.1)),
    (1, 30.0, (22.9, 21.1)), (2, 30.0, (23.9, 20.1)), (3, 30.0, (24.9, 19.1)),
])
def test_int_iso7730_sets_its_setpoints_in_every_comfort_mode(comf_mod, cat, day_of_year, expected):
    acst, ahst = _setpoints(22, cat, comf_mod, day_of_year=day_of_year)
    assert (acst, ahst) == (pytest.approx(expected[0]), pytest.approx(expected[1]))


def test_the_comfort_mode_still_selects_the_setpoints_of_the_other_standards():
    # ASHRAE 55 (ComfStand 2, CAT 80) with PMOT 20: static setpoints in ComfMod 0 and adaptive ones in ComfMod 3
    static = _setpoints(2, 80, 0, day_of_year=180.0)
    adaptive = _setpoints(2, 80, 3, day_of_year=180.0)
    assert static != adaptive
    assert adaptive == (pytest.approx(20 * 0.31 + 17.8 + 3.5 - 0.1), pytest.approx(20 * 0.31 + 17.8 - 3.5 + 0.1))
