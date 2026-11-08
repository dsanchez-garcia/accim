"""Tests for accim.utils.ems_code: the EMS code with which the ACCIS calculates the setpoints of a comfort standard,
category and comfort mode, which the author wanted users to be able to read before adding the ACCIS to a model (which
setpoints apply, and what happens out of the applicability limits).

The code must be that of the output IDFs: each section is compared with the functions that write the programs of the
output IDFs, and the lines of each comfort mode with its branch in its subprogram SetAST_CS<n>_<chunk>.
"""
import pytest

from accim.sim.ems import program_lines as pl
from accim.sim.ems.programs import indent_lines
from accim.sim.ems.setast import MODULAR_COMFORT_MODES, get_setpoint_lines, has_setpoints, subprograms
from accim.utils import get_setpoint_ems_code, print_setpoint_ems_code


def _sections(text):
    """The lines of each section of the code, by the name of its program (the beginning of its title)."""
    sections, name = {}, None
    for line in text.splitlines():
        if line.startswith('! --- '):
            name = line[len('! --- '):].split(':')[0].split(',')[0]
            sections[name] = []
        elif name is not None and line:
            sections[name].append(line)
    return sections


def _number(value):
    return str(int(value)) if value == int(value) else str(value)


def test_the_code_of_a_comfort_standard_category_and_comfort_mode():
    text = get_setpoint_ems_code(comfort_standard=1, category=2, comfort_mode=3, setpoint_tolerance=0.25)
    sections = _sections(text)

    assert '! Category (CAT): 2 = EN16798 Category II' in text.splitlines()
    assert ('! Comfort mode (ComfMod): 3 = EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive '
            'setpoints horizontally extended') in text.splitlines()
    assert list(sections) == ['SetInputData_<zone>', 'SetAppLimits', 'ApplyCAT', 'SetComfTemp', 'SetAST',
                              'SetAST_Master', 'SetAST_CS1_1', 'SetASTnoTol']
    assert sections['SetInputData_<zone>'] == [
        'set ComfStand = 1', 'set CAT = 2', 'set ComfMod = 3', 'set ACSTtol = -0.25', 'set AHSTtol = 0.25',
        'set CoolSeasonStart = 121', 'set CoolSeasonEnd = 274', 'set CATcoolOffset = 0', 'set CATheatOffset = 0',
        'set SetpointAcc = 10000']
    # The programs of the output IDFs, with the code of the comfort standard only, indented
    assert sections['SetAppLimits'] == indent_lines(pl.for_comfort_standards(pl.SET_APP_LIMITS, [1]))
    assert sections['ApplyCAT'] == indent_lines(pl.for_comfort_standards(pl.APPLY_CAT, [1]))
    assert sections['SetComfTemp'] == ['if ComfStand == 1', '    set ComfTemp = RMOT*0.33+18.8', 'endif']
    assert 'run SetAST_CS1_1' in [line.strip() for line in sections['SetAST_Master']]
    assert sections['SetASTnoTol'] == list(pl.SET_AST_NO_TOL)
    # Out of the applicability limits, with comfort mode 3, the setpoints are those of the limits
    assert sections['SetAST_CS1_1'] == indent_lines(get_setpoint_lines(1, 3))
    assert sections['SetAST_CS1_1'][:4] == ['if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
                                            '    set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
                                            'elseif RMOT < ACSTall',
                                            '    set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol']


@pytest.mark.parametrize('comfort_standard', sorted(MODULAR_COMFORT_MODES))
def test_the_lines_of_each_comfort_mode_are_those_of_its_subprogram(comfort_standard):
    programs = {name: [line.strip() for line in lines] for name, lines in subprograms([comfort_standard]).items()}

    for comfort_mode in MODULAR_COMFORT_MODES[comfort_standard]:
        if not has_setpoints(comfort_standard, comfort_mode):
            continue
        sections = _sections(get_setpoint_ems_code(comfort_standard, comfort_mode=comfort_mode))
        [(name, lines)] = [(name, lines) for name, lines in sections.items() if name.startswith('SetAST_CS')]
        lines = [line.strip() for line in lines]
        subprogram = programs[name]
        if subprogram[2] == '! The setpoints of this ComfStand do not depend on ComfMod':
            # ESP CTE and INT ISO7730: the subprogram, whole
            assert lines == subprogram
            continue
        text = _number(comfort_mode)
        branch = next(n for n, line in enumerate(subprogram)
                      if line in (f'if (ComfMod == {text})', f'elseif (ComfMod == {text})'))
        assert subprogram[branch + 1:branch + 1 + len(lines)] == lines


def test_without_a_category_and_a_comfort_mode_all_of_them_are_shown():
    text = get_setpoint_ems_code(comfort_standard=2)
    sections = _sections(text)

    assert '!     80 = ASHRAE 55 80% acceptability' in text.splitlines()
    assert '!     3 = ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints ' \
           'horizontally extended' in text.splitlines()
    assert sections['SetInputData_<zone>'][:3] == ['set ComfStand = 2', '! set CAT = <the category>',
                                                    '! set ComfMod = <the comfort mode>']
    # The subprograms of the comfort standard, whole
    assert {name: lines for name, lines in sections.items() if name.startswith('SetAST_CS')} == {
        name: indent_lines(lines) for name, lines in subprograms([2]).items()}


@pytest.mark.parametrize('comfort_standard', [0, 22])
def test_the_programs_without_code_for_the_static_comfort_standards_only_return(comfort_standard):
    sections = _sections(get_setpoint_ems_code(comfort_standard, category=2 if comfort_standard == 22 else None))

    assert sections['SetComfTemp'] == sections['ApplyCAT'] == ['return']
    assert [name for name in sections if name.startswith('SetAST_CS')] == [f'SetAST_CS{comfort_standard}_0']


def test_the_inputs_of_the_custom_model():
    inputs = _sections(get_setpoint_ems_code(99, comfort_mode=3, custom_slope=0.33, custom_intercept=18.8,
                                             custom_cooling_upper_limit=30, cooling_season_start='01/06'))
    inputs = inputs['SetInputData_<zone>']

    assert {'set m = 0.33', 'set n = 18.8', 'set CustAST_ACSTaul = 30', 'set CoolSeasonStart = 152'} <= set(inputs)
    # The other comfort standards do not use them
    others = _sections(get_setpoint_ems_code(1, 2, 3))['SetInputData_<zone>']
    assert not [line for line in others if 'CustAST' in line or line.startswith(('set m ', 'set n '))]


@pytest.mark.parametrize('arguments, message', [
    (dict(comfort_standard=23), 'comfort_standard 23 is not a comfort standard'),
    (dict(comfort_standard=1, category=80),
     r'category 80 is not a category of comfort_standard 1 \(valid: \[1, 2, 3\]\)'),
    (dict(comfort_standard=4, comfort_mode=1),
     r'comfort_standard 4 has no setpoints with comfort_mode 1 \(valid: \[3\]\)'),
])
def test_the_arguments_that_give_no_setpoints_are_rejected(arguments, message):
    with pytest.raises(ValueError, match=message):
        get_setpoint_ems_code(**arguments)


def test_print_setpoint_ems_code(capsys):
    print_setpoint_ems_code(comfort_standard=1, category=2, comfort_mode=3, setpoint_tolerance=0.25)

    assert capsys.readouterr().out == get_setpoint_ems_code(1, 2, 3, setpoint_tolerance=0.25) + '\n'
