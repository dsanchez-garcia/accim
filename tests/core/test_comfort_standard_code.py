"""Tests for the EMS code of the comfort standards in the models, and for the indentation of the EMS programs.

The programs SetComfTemp, SetAppLimits, ApplyCAT, CountHours_<zone> and SetAST_Master, and the subprograms of
SetAST, have the code of every comfort standard in the models of add_accis_to_idf, so that the comfort standard of
a zone can be changed in its program SetInputData_<zone> (as the parametric module does). Since accim 1.1.0, the
output IDFs of AddAccis only have the code of the comfort standards of their zones: with the sample model of two
zones in mixed mode, an output IDF went from 78 programs with 6851 lines (645 KB), 5166 of them in the subprograms of
the 24 comfort standards, to 34 programs with 1393 lines (357 KB), with the same results in EnergyPlus 25.1. The
lines of the programs are indented inside the blocks IF and WHILE, which EnergyPlus ignores (the same results too).
"""
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from accim.energyplus import find_energyplus
from accim.sim.accis import load_idf, modify_accis
from accim.sim.ems import program_lines as pl
from accim.sim.ems.erl import ErlProgramSet, ErlRuntimeError, variables_in_programs
from accim.sim.ems.inputs import input_lines, input_values, zone_comfort_standards
from accim.sim.ems.programs import (
    INDENTATION,
    accis_programs,
    add_program,
    indent_lines,
    indent_programs,
    set_comfort_standard_code,
    set_program_lines,
)
from accim.sim.ems.setast import (
    MODULAR_COMFORT_MODES,
    has_setpoints,
    master_program_lines,
    subprogram_comfort_standards,
)
from accim.sim.standards import COMFORT_STANDARDS

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
CHAIN = ['if ComfStand == 1', 'set A = 1', 'elseif ComfStand == 2 || (ComfStand == 12)', 'if CAT == 1', 'set A = 2',
         'endif', 'else', 'set A = 3', 'endif']
#: The inputs of the zones with full air-conditioning (the EMS variables of SetInputData_<zone>).
INPUTS = [line[len('set '):].split(' = ')[0] for line in input_lines(mixed_mode=False)]
#: The timesteps run with each comfort standard, category and comfort mode (RMOT and PMOT differ, as the branches that
#: use one or the other).
TIMESTEPS = [dict(RMOT=t, PMOT=t - 1.5, DayOfYear=d, CurrentTime=h, Zone1_OpT=op, Zone2_OpT=op, ZoneTimeStep=0.25,
                  Occ_count_Zone1=1.0, Occ_count_Zone2=1.0)
             for t in (2.0, 21.0, 37.0) for d in (30.0, 200.0) for h in (6.0, 12.0, 24.0) for op in (17.0, 31.0)]


def _idf(text='Version,25.1;'):
    """An IDF object of eppy of a model of EnergyPlus 25.1."""
    if find_energyplus('25.1', required=False) is None:
        pytest.skip('needs EnergyPlus 25.1 (its IDD)')
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'model.idf'
        path.write_text(text, encoding='latin-1')
        return load_idf(path)


def _lines(idf, name):
    return [str(line) for line in idf.getobject('EnergyManagementSystem:Program', name).fieldvalues[2:]]


# Indentation ---------------------------------------------------------------------------------------------------

def test_the_lines_are_indented_inside_the_blocks():
    lines = ['set A = 1', 'IF A > 0', 'if B', 'set C = 1', 'ElseIf B > 1', 'set C = 2', 'else', 'set C = 3', 'endif',
             'WHILE C < 5', 'set C = C + 1', 'ENDWHILE', 'ENDIF', 'run P']
    indented = indent_lines(lines)

    assert indented == ['set A = 1', 'IF A > 0', '    if B', '        set C = 1', '    ElseIf B > 1',
                        '        set C = 2', '    else', '        set C = 3', '    endif', '    WHILE C < 5',
                        '        set C = C + 1', '    ENDWHILE', 'ENDIF', 'run P']
    assert INDENTATION == '    '
    # The spaces that the lines had are replaced
    assert indent_lines(indented) == indented
    assert indent_lines(['  set A = 1', '      if A', 'set B = 1', 'endif']) == ['set A = 1', 'if A', '    set B = 1',
                                                                                'endif']


def test_eppy_removes_the_indentation_and_accim_writes_it():
    idf = _idf('Version,25.1;\n'
               'EnergyManagementSystem:Program, P, if A > 0,    set B = 1, endif;\n'
               'EnergyManagementSystem:Subroutine, S, while A < 3,      set A = A + 1, endwhile;\n')
    assert _lines(idf, 'P') == ['if A > 0', 'set B = 1', 'endif']

    indent_programs(idf)

    assert _lines(idf, 'P') == ['if A > 0', '    set B = 1', 'endif']
    subroutine = idf.idfobjects['EnergyManagementSystem:Subroutine'][0]
    assert list(subroutine.fieldvalues[2:]) == ['while A < 3', '    set A = A + 1', 'endwhile']
    # add_program and set_program_lines indent the lines they write, and eppy writes the spaces
    add_program(idf, 'Q', ['if A', 'set B = 2', 'endif'])
    assert _lines(idf, 'Q') == ['if A', '    set B = 2', 'endif']
    set_program_lines(idf.getobject('EnergyManagementSystem:Program', 'Q'),
                      ['if A', 'if B', 'set C = 1', 'endif', 'endif'])
    assert _lines(idf, 'Q') == ['if A', '    if B', '        set C = 1', '    endif', 'endif']
    assert '\n            set C = 1,' in idf.idfstr()


# Chains on the comfort standard --------------------------------------------------------------------------------

def test_a_chain_keeps_the_branches_of_some_comfort_standards():
    assert pl.for_comfort_standards(CHAIN, [12]) == ['if ComfStand == 12', 'if CAT == 1', 'set A = 2', 'endif',
                                                     'endif']
    assert pl.for_comfort_standards(CHAIN, [12, 1]) == ['if ComfStand == 1', 'set A = 1', 'elseif ComfStand == 12',
                                                        'if CAT == 1', 'set A = 2', 'endif', 'endif']
    # The branch else is that of the comfort standards that no condition names
    assert pl.for_comfort_standards(CHAIN, [5, 2, 0]) == ['if ComfStand == 2', 'if CAT == 1', 'set A = 2', 'endif',
                                                          'elseif ComfStand == 0 || ComfStand == 5', 'set A = 3',
                                                          'endif']
    # Without branches, there are no lines
    assert pl.for_comfort_standards(['if ComfStand == 1', 'set A = 1', 'endif'], [3]) == []


@pytest.mark.parametrize('lines', [
    ['set A = 1'],
    ['if ComfStand == 1', 'set A = 1'],
    ['if CAT == 1', 'set A = 1', 'endif'],
    ['if ComfStand == 1 && CAT == 1', 'set A = 1', 'endif'],
    ['if ComfStand == 1', 'set A = 1', 'endif', 'set B = 1'],
])
def test_only_chains_on_the_comfort_standard_are_cut(lines):
    with pytest.raises(ValueError):
        pl.for_comfort_standards(lines, [1])


def test_set_ast_master_runs_the_subprograms_of_some_comfort_standards():
    lines = master_program_lines([13, 1])

    assert [line for line in lines if line.startswith('if (ComfStand')] == ['if (ComfStand == 1)',
                                                                            'if (ComfStand == 13)']
    assert [line for line in lines if line.startswith('run ')] == ['run SetAST_CS1_0', 'run SetAST_CS1_1'] + [
        f'run SetAST_CS13_{n}' for n in range(4)]
    assert master_program_lines() == master_program_lines(MODULAR_COMFORT_MODES)


# The programs with the code of some comfort standards, run with the rules of the EMS ------------------------------

def _accis_model(zones):
    """An IDF object with the programs of ACCIS of some zones with full air-conditioning."""
    model = SimpleNamespace(ems_names=zones, ems_zones=zones, is_mixed_mode=False, windows=[], window_zones=[])
    idf = _idf()
    for name, lines in accis_programs(model):
        add_program(idf, name, lines)
    return idf


class _Erl:
    """The programs of a model, compiled once: their programs SetInputData_<zone> set the inputs of each zone from the
    variables In_<input>_<zone>, which each run from the beginning of an environment sets."""

    def __init__(self, idf, zones):
        programs = {p.Name: [str(line) for line in p.fieldvalues[2:]]
                    for p in idf.idfobjects['EnergyManagementSystem:Program']}
        for zone in zones:
            programs[f'SetInputData_{zone}'] = [f'set {name} = In_{name}_{zone}' for name in INPUTS]
        self.zones = zones
        self.erl = ErlProgramSet(programs, global_variables=set().union(*variables_in_programs(programs).values()))
        self.erl.strict = True
        self.initial = dict(self.erl.variables)

    def start(self, zone_arguments):
        self.erl.variables.clear()
        self.erl.variables.update(self.initial)
        for store in self.erl.local_variables.values():
            store.clear()
        for zone, arguments in zone_arguments.items():
            values = input_values(dict(arguments, hvac_mode=0, setpoint_tolerance=0.1))
            for line in input_lines(values, mixed_mode=False):
                name, value = line[len('set '):].split(' = ')
                self.erl.set(f'In_{name}_{zone}', float(value))
        self.erl.run('InitASTvariables')

    def timestep(self, values):
        """Run the zones in a timestep: the variables (special values by name), or the error that stops EnergyPlus."""
        for name, value in values.items():
            self.erl.set(name, value)
        try:
            for zone in self.zones:
                self.erl.run(f'RunACCIS_{zone}')
        except ErlRuntimeError as error:
            return type(error)
        return {name: value if value.__class__ is float else repr(value) for name, value in self.erl.variables.items()}


def _cases(comfort_standard):
    """The categories and comfort modes of a comfort standard that give setpoints."""
    for category in list(COMFORT_STANDARDS[comfort_standard].categories) or [1]:
        for comfort_mode in MODULAR_COMFORT_MODES[comfort_standard]:
            if has_setpoints(comfort_standard, comfort_mode):
                yield dict(comfort_standard=comfort_standard, category=category, comfort_mode=comfort_mode)


def _check_same_results(full, pruned, zone_arguments):
    full.start(zone_arguments)
    pruned.start(zone_arguments)
    for values in TIMESTEPS:
        expected = full.timestep(values)
        assert expected is not ErlRuntimeError, (zone_arguments, values)
        assert pruned.timestep(values) == expected, (zone_arguments, values)


@pytest.fixture(scope='module')
def one_zone():
    idf = _accis_model(['Zone1'])
    return idf, _Erl(idf, ['Zone1'])


def test_the_code_of_a_comfort_standard_gives_the_same_setpoints_and_hours(one_zone):
    idf, full = one_zone

    for comfort_standard in MODULAR_COMFORT_MODES:
        set_comfort_standard_code(idf, [comfort_standard])
        pruned = _Erl(idf, ['Zone1'])
        cases = list(_cases(comfort_standard))
        assert cases, comfort_standard
        for arguments in cases:
            _check_same_results(full, pruned, {'Zone1': arguments})

    # The model only has the code of the last comfort standard
    assert subprogram_comfort_standards(idf) == {99}
    assert _lines(idf, 'SetComfTemp') == ['if ComfStand == 99', '    set ComfTemp = PMOT*m+n', 'endif']


def test_the_programs_without_code_for_a_comfort_standard_only_return(one_zone):
    idf, _ = one_zone

    set_comfort_standard_code(idf, [22])

    # INT ISO7730 uses neither the comfort temperature nor the offsets of the categories
    assert _lines(idf, 'SetComfTemp') == _lines(idf, 'ApplyCAT') == ['return']
    # The applicability limits of the comfort standards without their own branch, and the hours with PMOT
    assert _lines(idf, 'SetAppLimits')[0] == 'if ComfStand == 22'
    assert _lines(idf, 'CountHours_Zone1')[:2] == ['if ComfStand == 22',
                                                   '    if (PMOT >= AHSTall) && (PMOT <= ACSTaul)']


def test_a_comfort_standard_without_its_code_stops_the_simulation(one_zone):
    idf, _ = one_zone
    set_comfort_standard_code(idf, [1])
    pruned = _Erl(idf, ['Zone1'])

    pruned.start({'Zone1': dict(comfort_standard=2, category=80, comfort_mode=3)})

    assert pruned.timestep(TIMESTEPS[0]) is ErlRuntimeError


def test_the_zones_get_the_code_of_their_comfort_standards():
    zones = ['Zone1', 'Zone2']
    idf = _accis_model(zones)
    full = _Erl(idf, zones)
    zone_arguments = {'Zone1': dict(comfort_standard=1, category=2, comfort_mode=3),
                      'Zone2': dict(comfort_standard=13, category=80, comfort_mode=1.2)}

    set_comfort_standard_code(idf, [1, 13])

    _check_same_results(full, _Erl(idf, zones), zone_arguments)
    assert subprogram_comfort_standards(idf) == {1, 13}
    assert _lines(idf, 'SetComfTemp') == ['if ComfStand == 1', '    set ComfTemp = RMOT*0.33+18.8',
                                          'elseif ComfStand == 13', '    set ComfTemp = PMOT*0.26+15.9', 'endif']
    # With None, the programs have the code of all the comfort standards again
    set_comfort_standard_code(idf)
    assert subprogram_comfort_standards(idf) == set(MODULAR_COMFORT_MODES)
    assert _lines(idf, 'SetAppLimits') == indent_lines(pl.SET_APP_LIMITS)
    assert _lines(idf, 'CountHours_Zone2') == indent_lines(pl.format_lines(pl.COUNT_HOURS, zone='Zone2'))


# modify_accis --------------------------------------------------------------------------------------------------

@pytest.mark.skipif(not SAMPLE_IDF.exists(), reason='needs the sample IDF of the repository')
def test_modify_accis_adds_the_code_of_the_comfort_standards_that_it_sets():
    from accim.sim.accis import add_accis_to_idf

    idf = _idf(SAMPLE_IDF.read_text(encoding='latin-1'))
    add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='simplified', output_frequencies=['hourly'], keep_existing_outputs=False,
                     setpoint_type='temperature', verbose=False)
    # The models of add_accis_to_idf have the code of all the comfort standards, which modify_accis keeps
    modify_accis(idf, comfort_standard=2, category=80, comfort_mode=3, hvac_mode=0)
    assert subprogram_comfort_standards(idf) == set(MODULAR_COMFORT_MODES)
    # An output IDF of AddAccis, read from its file
    set_comfort_standard_code(idf, zone_comfort_standards(idf))
    idf = _idf(idf.idfstr())
    assert subprogram_comfort_standards(idf) == {2}
    assert _lines(idf, 'CountHoursNoApp_Block1_Zone1')[1] == 'set ComfHoursNoApp_Block1_Zone1 = 1*ZoneTimeStep'

    modify_accis(idf, comfort_standard=1, category=3,
                 zone_arguments={'Block1:Zone2': {'comfort_standard': 13, 'category': 80}})

    assert zone_comfort_standards(idf) == {1, 13}
    assert subprogram_comfort_standards(idf) == {1, 2, 13}
    assert _lines(idf, 'SetComfTemp')[::2] == ['if ComfStand == 1', 'elseif ComfStand == 2', 'elseif ComfStand == 13',
                                               'endif']
    # The programs that eppy read get their indentation again
    assert _lines(idf, 'CountHoursNoApp_Block1_Zone1')[1] == '    set ComfHoursNoApp_Block1_Zone1 = 1*ZoneTimeStep'


def test_the_parametric_module_adds_the_code_of_the_comfort_standard_that_it_sets():
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis

    idf = _accis_model(['Zone1'])
    set_comfort_standard_code(idf, [1])

    param_accis.modify_ComfStand(idf, 13.0)

    assert zone_comfort_standards(idf) == {13}
    assert subprogram_comfort_standards(idf) == {1, 13}
    assert _lines(idf, 'SetComfTemp')[2] == 'elseif ComfStand == 13'
