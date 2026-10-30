"""Tests for accim.sim.ems.erl, which runs the EMS programs (Erl) in Python with the rules of EnergyPlus.

The Python API backend runs the EMS programs of the output IDFs with this module, and its results are
those of the EMS of EnergyPlus (test_energyplus_api.py compares both backends). These tests check the
rules of RuntimeLanguageProcessor.cc that differ from Python: the order in which the operators are
grouped, the minus sign, the values Null and uninitialised, the errors, and the reset of the variables
at each new environment. An operator whose operands are not both numbers gives the number 0 without
setting it (EvaluateExpression starts with the number 0 and only sets it when the operands are numbers),
and ``^`` follows ``std::pow`` of C.
"""
import math
from types import SimpleNamespace

import pytest

from accim.sim.ems.erl import (
    NULL,
    UNINITIALISED_ERROR,
    UNINITIALISED_NULL,
    UNINITIALISED_NUMBER,
    ErlProgramSet,
    ErlRuntimeError,
    ErlSyntaxError,
    erl_round,
    is_number,
    parse_expression,
    variables_in_programs,
)
from accim.sim.ems.programs import accis_programs


def _evaluate(expression, **variables):
    programs = ErlProgramSet({'P': [f'set Result = {expression}']}, global_variables=['Result', *variables])
    for name, value in variables.items():
        programs.set(name, value)
    programs.run('P')
    return programs.value('Result')


@pytest.mark.parametrize('expression, expected', [
    ('1 + 2 * 3', 7.0),
    ('(1 + 2) * 3', 9.0),
    ('10 - 2 - 3', 5.0),
    ('8 / 2 * 2', 8.0),
    ('8 * 2 / 4', 4.0),
    # '^' is grouped after the arithmetic and comparison operators, and from left to right
    ('2 + 1 ^ 2', 9.0),
    ('2 ^ 3 ^ 2', 64.0),
    # A '-' at the beginning subtracts from 0, and is grouped as a subtraction
    ('-2 ^ 2', 4.0),
    # A '-' after an operator becomes '0 -': 5 - 0 - 2
    ('5 - -2', 3.0),
    ('1 == 1 && 2 == 2', 1.0),
    ('3 > 2 || 0', 1.0),
    # '&&' and '||' are true when their operands are 1
    ('2 && 1', 0.0),
    ('1 <> 2', 1.0),
    ('7 == 7.0', 1.0),
    ('@Round 2.5', 3.0),
    ('@Round (0 - 2.5)', -3.0),
    ('@Max 3 5', 5.0),
    ('@Min 3 5', 3.0),
    ('@Mod 7 3', 1.0),
    ('@Abs (0 - 4)', 4.0),
    ('@Exp 0', 1.0),
    ('@Ln 1', 0.0),
])
def test_expressions_follow_the_rules_of_energyplus(expression, expected):
    assert _evaluate(expression) == expected


def test_operators_of_the_same_kind_are_grouped_as_energyplus_does():
    # '-' is grouped before '+', and '/' before '*', so the results differ from Python in the last digit
    assert parse_expression('a + b - c') == ('bin', '+', ('var', 'A'), ('bin', '-', ('var', 'B'), ('var', 'C')))
    assert parse_expression('a * b / c') == ('bin', '*', ('var', 'A'), ('bin', '/', ('var', 'B'), ('var', 'C')))
    assert _evaluate('0.1 + 0.2 - 0.3') == 0.1 + (0.2 - 0.3)
    assert _evaluate('0.1 + 0.2 - 0.3') != (0.1 + 0.2) - 0.3


def test_erl_round_rounds_halves_away_from_zero():
    assert [erl_round(v) for v in (0.5, 1.5, 2.5, -0.5, -1.5, 2.4999)] == [1.0, 2.0, 3.0, -1.0, -2.0, 2.0]


def test_names_are_case_insensitive():
    programs = ErlProgramSet({'P': ['SET x = 1', 'Set Y = X + 1']}, global_variables=['x', 'y'])

    programs.run('p')

    assert programs.get('Y') == programs.get('y') == 2.0


def test_null_values():
    programs = ErlProgramSet({'P': [
        'set A = NULL',
        'set B = NULL + 1',
        'if A == NULL',
        'set C = 1',
        'else',
        'set C = 2',
        'endif',
        # The functions take Null as 0
        'set D = @Max A 2',
    ]}, global_variables=['A', 'B', 'C', 'D'])

    programs.run('P')

    assert programs.value('A') is NULL
    # An operation with Null gives the number 0, which has not been set
    assert programs.value('B') is UNINITIALISED_NUMBER
    assert programs.get('A') is None
    assert (programs.get('C'), programs.get('D')) == (1.0, 2.0)
    assert not is_number(NULL) and is_number(1.0)


def test_operators_with_null_give_the_number_0_without_setting_it():
    programs = ErlProgramSet({
        'P': [
            'set A = NULL',
            # Inside an expression, the result of an operator with Null is 0
            'set B = A + 1 + 2',
            'set C = 0',
            'if (A + 1) == 0',
            'set C = 1',
            'endif',
            # <> is not true for values that are not numbers, unlike ==
            'set D = 0',
            'if A <> 1',
            'set D = 1',
            'endif',
            'set E = (A == NULL) + (A == 0)',
        ],
        'Q': ['set X = 1 / (NULL + 1)'],
    }, global_variables=['A', 'B', 'C', 'D', 'E', 'X'])

    programs.run('P')

    assert [programs.get(name) for name in 'BCDE'] == [2.0, 1.0, 0.0, 1.0]
    # The operand is the number 0, so the division stops the simulation
    with pytest.raises(ErlRuntimeError, match='Divide By Zero'):
        programs.run('Q')


@pytest.mark.parametrize('expression, expected', [
    ('0 ^ (0 - 1)', math.inf),
    ('0 ^ (0 - 2)', math.inf),
    ('0 ^ (0 - 0.5)', math.inf),
    ('Z ^ (0 - 1)', -math.inf),
    ('10 ^ 400', math.inf),
    ('(0 - 10) ^ 401', -math.inf),
    ('2 ^ 0.5', math.sqrt(2.0)),
])
def test_raise_to_power_follows_c(expression, expected):
    # std::pow of C gives infinities for the poles and overflows, where math.pow raises an exception
    assert _evaluate(expression, Z=-0.0) == expected


def test_raise_to_power_without_a_real_result_is_an_error():
    programs = ErlProgramSet({'P': ['set R = (0 - 2) ^ 0.5']}, global_variables=['R'])

    with pytest.raises(ErlRuntimeError, match='Attempted to raise to power'):
        programs.run('P')


def test_long_expressions():
    # The building averages of make_averages sum one term per zone: Python cannot compile so many nested parentheses
    names = [f'T{n}' for n in range(300)]
    programs = ErlProgramSet({'P': [f"set S = {' + '.join(names)}", f"set D = {' - '.join(names)}"]},
                             global_variables=names + ['S', 'D'])
    for n, name in enumerate(names):
        programs.set(name, n)

    programs.run('P')

    assert programs.get('S') == sum(range(300))
    assert programs.get('D') == 0 - sum(range(1, 300))
    # Expressions nested more deeply than Python allows are evaluated with the exact rules
    expression = '1'
    for _ in range(250):
        expression = f'1 + ({expression})'
    deep = ErlProgramSet({'P': [f'set R = {expression}', 'if R > 250', 'set R = R + 1', 'endif']},
                         global_variables=['R'])
    deep.run('P')
    assert deep.get('R') == 252.0
    assert '_expression(' in deep.source['P']


def test_numbers_too_large_for_a_float_are_infinite():
    assert _evaluate('1e999') == math.inf
    assert _evaluate('1e999 + 1') == math.inf


def test_uninitialised_variables_stop_the_simulation_except_while_sizing():
    programs = ErlProgramSet({'P': ['set X = Y + 1'], 'Q': ['set A = NULL + 1', 'if A', 'set B = 1', 'endif']},
                             global_variables=['X', 'Y', 'A', 'B'])

    with pytest.raises(ErlRuntimeError, match="Variable = 'Y' used in expression has not been initialized"):
        programs.run('P')
    with pytest.raises(ErlRuntimeError, match="Variable = 'A' used in expression has not been initialized"):
        programs.run('Q')

    # While EnergyPlus sizes the systems, the expression gives an error value
    programs.strict = False
    programs.run('P')
    assert programs.value('X') is UNINITIALISED_ERROR


def test_division_by_zero():
    programs = ErlProgramSet({'P': ['set D = 1 / Z']}, global_variables=['D', 'Z'])
    programs.set('Z', 0)

    with pytest.raises(ErlRuntimeError, match='Divide By Zero'):
        programs.run('P')
    programs.strict = False
    programs.run('P')
    assert programs.value('D') is UNINITIALISED_ERROR


def test_local_variables_belong_to_their_program():
    programs = ErlProgramSet({'P': ['set Local = 5', 'set G = Local * 2'], 'Q': ['set Local = 7']},
                             global_variables=['G'])

    programs.run('P')
    programs.run('Q')

    assert programs.get('G') == 10.0
    assert programs.get('Local', 'P') == 5.0
    assert programs.get('Local', 'Q') == 7.0
    assert programs.value('Local') is None


def test_control_flow():
    programs = ErlProgramSet({
        'Loop': ['set I = 0', 'set Total = 0', 'while I < 5', 'set I = I + 1', 'set Total = Total + I', 'endwhile'],
        'Main': ['run Sub', 'set Out = SubOut + 1'],
        'Sub': ['set SubOut = 41'],
        'Branches': ['if X > 0', 'set Branch = 1', 'elseif X < 0', 'set Branch = 2', 'else', 'set Branch = 3', 'endif'],
    }, global_variables=['I', 'Total', 'Out', 'SubOut', 'X', 'Branch'])

    programs.run('Loop')
    programs.run('Main')
    branches = []
    for x in (1, -1, 0):
        programs.set('X', x)
        programs.run('Branches')
        branches.append(programs.get('Branch'))

    assert (programs.get('I'), programs.get('Total'), programs.get('Out')) == (5.0, 15.0, 42.0)
    assert branches == [1.0, 2.0, 3.0]


def test_reset_at_a_new_environment():
    programs = ErlProgramSet({'P': ['set G = 3', 'set Local = 4', 'set N = NULL', 'set U = NULL + 1']},
                             global_variables=['G', 'N', 'U'], actuators=['Act', 'Unset'])
    # EnergyPlus creates the actuators as Null
    assert programs.value('Act') is NULL
    programs.run('P')
    programs.set('Act', 3)
    programs.variables['UNSET'] = UNINITIALISED_NULL

    programs.reset()

    # The variables that have been set become 0, the actuators Null, and the constants keep their values
    assert (programs.value('G'), programs.value('N'), programs.get('Local', 'P')) == (0.0, 0.0, 0.0)
    assert programs.value('U') is UNINITIALISED_NUMBER
    assert programs.value('Act') is NULL
    assert programs.value('Unset') is UNINITIALISED_NULL
    assert programs.get('PI') == pytest.approx(3.14159265)


def test_initialise_set_variables_as_the_first_runs_of_energyplus():
    # EnergyPlus runs the programs before the first environment, so the variables they set are 0 afterwards
    programs = ErlProgramSet({'P': ['set A = B', 'set B = 1']}, global_variables=['A', 'B'])

    programs.initialise_set_variables()
    programs.run('P')

    assert (programs.get('A'), programs.get('B')) == (0.0, 1.0)


@pytest.mark.parametrize('lines, message', [
    (['set R = 2 * -1'], 'Minus sign used on the right side of multiplication sign'),
    (['set R = 2 / -1'], 'Minus sign used on the right side of division sign'),
    (['set R = @Foo 1'], 'Built-in function "@FOO" is not supported'),
    (['run Missing'], 'Program or subroutine \\[MISSING\\] not found'),
    (['if 1', 'set R = 1'], 'Missing ENDIF or ENDWHILE'),
    (['set R = (1 + 2'], 'Unbalanced parentheses'),
])
def test_syntax_errors(lines, message):
    with pytest.raises(ErlSyntaxError, match=message):
        ErlProgramSet({'P': lines}, global_variables=['R'])


def test_running_a_missing_program():
    with pytest.raises(ErlRuntimeError, match='not found'):
        ErlProgramSet({'P': ['set R = 1']}, global_variables=['R']).run('Q')


def test_variables_in_programs():
    assert variables_in_programs({'P': ['set A = B + C', 'if D', 'set E = 1', 'endif']}) == {'P': set('ABCDE')}


def test_the_programs_of_accis_give_the_setpoints_of_en16798():
    # All the programs that accim writes compile, and the comfort model INT EN16798-1, category II, adaptive
    # (ComfStand 1, CAT 2, ComfMod 3), gives Tcomf = 0.33*RMOT + 18.8, and setpoints Tcomf + 3 and Tcomf - 4
    # (with the tolerance of 0.1 towards the comfort temperature)
    model = SimpleNamespace(ems_names=['Zone1', 'Zone2'], is_mixed_mode=True, windows=['Zone1_Win'])
    programs = dict(accis_programs(model))
    programs['SetInputData'] = [
        'set ComfStand = 1', 'set CAT = 2', 'set ComfMod = 3', 'set HVACmode = 2', 'set VentCtrl = 0',
        'set VSToffset = 0', 'set MinOToffset = 50', 'set MaxWindSpeed = 50', 'set ACSTtol = -0.1',
        'set AHSTtol = 0.1', 'set CoolSeasonStart = 121', 'set CoolSeasonEnd = 274']
    names = set().union(*variables_in_programs(programs).values())
    erl = ErlProgramSet(programs, global_variables=names)
    for name, value in dict(RMOT=20.0, PMOT=20.0, DayOfYear=180.0, CurrentTime=12.0).items():
        erl.set(name, value)
    erl.initialise_set_variables()

    for name in ['SetInputData', 'SetVOFinputData', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST',
                 'SetASTnoTol']:
        erl.run(name)

    assert erl.get('ComfTemp') == pytest.approx(25.4)
    assert (erl.get('ACSTnoTol'), erl.get('AHSTnoTol')) == (pytest.approx(28.4), pytest.approx(21.4))
    assert (erl.get('ACST'), erl.get('AHST')) == (pytest.approx(28.3), pytest.approx(21.5))
    # Rounded to the setpoint accuracy (10000), the cooling setpoint down and the heating setpoint up
    assert erl.get('ACST') - 1e-4 <= erl.get('roundedACST') <= erl.get('ACST')
    assert erl.get('AHST') <= erl.get('roundedAHST') <= erl.get('AHST') + 1e-4
    assert erl.get('CoolingSeason') == 1.0
