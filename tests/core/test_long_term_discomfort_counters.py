"""Tests for the long-term discomfort that the ACCIS counts (proposal C2 of accim 1.2.0,
:mod:`accim.sim.ems.long_term_discomfort`).

CEN/TR 16798-2:2019, Annex D: Method A (the occupied hours outside the range, above its upper limit and below its lower
limit) and Method B (the degree hours, wf = abs(Θo − Θo,limit) times the time outside the range), which the functions
of proposal D1 (:mod:`accim.data.postprocessing.long_term_discomfort`) calculate from the outputs; the EMS counts them
in each timestep with the setpoints without the tolerance as the limits (``report_long_term_discomfort``), or with the
constant limits of EN 16798-1, Table B.2 (``long_term_range``, finding C2-1 of the review of accim 1.2.0). The unit
tests run the EMS programs with the Erl interpreter of accim and compare them with the functions of D1; the last tests
simulate output IDFs of AddAccis with EnergyPlus 25.1 (a winter and a summer week, verify_accim_simulation, and both
backends).
"""
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.data.postprocessing.long_term_discomfort import degree_hours, hours_outside_range
from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.ems import long_term_discomfort as ltd
from accim.sim.ems.erl import ErlProgramSet

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
# An output IDF of accim 0.x (before SetAST_Master), with one program SetInputData for all the zones
LEGACY_IDF = next((REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'runEp').glob('TestModel_V2510*.idf'), None)
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']
STEPS = 6
OUTPUTS = list(ltd.OUTPUTS)


def test_the_outputs_and_their_units():
    # Method A in hours, Method B in degree hours
    assert ltd.OUTPUTS == {
        'Hours Above Upper Limit': ('HoursAboveUpperLimit', 'H'),
        'Hours Below Lower Limit': ('HoursBelowLowerLimit', 'H'),
        'Degree Hours Above Upper Limit': ('DegreeHoursAboveUpperLimit', 'Kh'),
        'Degree Hours Below Lower Limit': ('DegreeHoursBelowLowerLimit', 'Kh'),
    }
    assert ltd.long_term_variable('Degree Hours Below Lower Limit', 'Zone1') == 'DegreeHoursBelowLowerLimit_Zone1'
    assert ltd.output_names(['Zone1']) == [f'{output}_{zone}' for zone in ('Zone1', 'Building') for output in OUTPUTS]


def _erl(zones):
    names = [ltd.long_term_variable(output, zone) for zone in list(zones) + [ltd.BUILDING] for output in OUTPUTS]
    programs = {f'{ltd.PROGRAM_PREFIX}{zone}': ltd.zone_lines(zone) for zone in zones}
    programs[ltd.BUILDING_PROGRAM] = ltd.building_lines(zones)
    variables = [f'Occ_count_{zone}' for zone in zones] + [f'{zone}_OpT' for zone in zones]
    return ErlProgramSet(programs, global_variables=variables + ['ACSTnoTol', 'AHSTnoTol'] + names)


@pytest.mark.parametrize('occupants, temperature, lower, upper', [
    (2, 27.5, 20, 26),     # above the range
    (1, 18.25, 20, 26),    # below the range
    (3, 23.0, 20, 26),     # within the range
    (1, 26.0, 20, 26),     # on the upper limit: within the range
    (1, 20.0, 20, 26),     # on the lower limit: within the range
    (0, 30.0, 20, 26),     # without occupants
    (0, 15.0, 20, 26),
    (1, 24.0, 25.5, 24.5),  # a heating setpoint above the cooling setpoint (a floor above it): both sides
])
def test_the_counters_of_a_zone_are_methods_a_and_b_of_d1(occupants, temperature, lower, upper):
    erl = _erl(['Z'])
    erl.set('ZoneTimeStep', 0.25)
    erl.set('Occ_count_Z', occupants)
    erl.set('Z_OpT', temperature)
    erl.set('AHSTnoTol', lower)
    erl.set('ACSTnoTol', upper)
    erl.run(f'{ltd.PROGRAM_PREFIX}Z')
    found = {output: erl.get(ltd.long_term_variable(output, 'Z')) for output in OUTPUTS}
    method_a = hours_outside_range([temperature], [lower], [upper], occupied=[occupants], timestep_h=0.25)
    method_b = degree_hours([temperature], [lower], [upper], occupied=[occupants], timestep_h=0.25)
    assert found['Hours Above Upper Limit'] == pytest.approx(method_a['hot_h'], abs=1e-12)
    assert found['Hours Below Lower Limit'] == pytest.approx(method_a['cold_h'], abs=1e-12)
    assert found['Degree Hours Above Upper Limit'] == pytest.approx(method_b['hot_Kh'], abs=1e-12)
    assert found['Degree Hours Below Lower Limit'] == pytest.approx(method_b['cold_Kh'], abs=1e-12)


# The constant range of EN 16798-1, Table B.2 (long_term_range) ------------------------------------------------------

@pytest.mark.parametrize('long_term_range, limits', [
    (('en16798', 1), (21.0, 25.5)),
    (('en16798', 2), (20.0, 26.0)),
    (['EN16798', 2, 'Office'], (20.0, 26.0)),
    (('en16798', 3, 'residential'), (18.0, 27.0)),
    (('en16798', 3, 'office'), (19.0, 27.0)),
    (('en16798', 4, 'residential'), (16.0, 28.0)),
    (('en16798', 4, 'office'), (18.0, 28.0)),
    (None, None),
])
def test_the_constant_limits_of_table_b2(long_term_range, limits):
    from accim.constants import EN16798_TABLE_B2

    assert ltd.long_term_limits(long_term_range) == limits
    if long_term_range is not None and len(long_term_range) == 3:
        assert limits == EN16798_TABLE_B2[long_term_range[2].lower(), long_term_range[1]]


@pytest.mark.parametrize('long_term_range, message', [
    (('en16798', 3), r"category 3 of EN 16798-1, Table B.2, depend on the building type \(residential: "
                     r"\(18.0, 27.0\), office: \(19.0, 27.0\)\)"),
    (('en16798', 4), 'category 4 of EN 16798-1, Table B.2, depend on the building type'),
    (('en16798', 0), 'The category of long_term_range must be 1, 2, 3 or 4'),
    (('en16798', 5), 'The category of long_term_range must be 1, 2, 3 or 4'),
    (('en16798', 2.0), 'The category of long_term_range must be 1, 2, 3 or 4'),
    (('en16798', True), 'The category of long_term_range must be 1, 2, 3 or 4'),
    (('en16798', 2, 'hospital'), "The building type of long_term_range must be one of \\['residential', 'office'\\]"),
    (('iso7730', 2), "The range of long_term_range must be one of \\['en16798'\\]"),
    ('en16798', 'long_term_range must be None or'),
    (('en16798',), 'long_term_range must be None or'),
    (('en16798', 2, 'office', 1), 'long_term_range must be None or'),
    (2, 'long_term_range must be None or'),
])
def test_the_constant_range_is_checked(long_term_range, message):
    with pytest.raises(ValueError, match=message):
        ltd.long_term_limits(long_term_range)


@pytest.mark.parametrize('occupants, temperature', [(2, 27.5), (1, 18.25), (3, 23.0), (1, 26.0), (1, 20.0),
                                                     (0, 30.0), (0, 15.0)])
def test_the_counters_with_a_constant_range_are_methods_a_and_b_of_d1(occupants, temperature):
    lines = ltd.zone_lines('Z', (20.0, 26.0))
    # The constants replace the setpoints without the tolerance, which the program no longer reads
    assert not any('noTol' in line for line in lines)
    assert 'if Z_OpT > 26' in lines and 'if Z_OpT < 20' in lines
    assert 'set DegreeHoursAboveUpperLimit_Z = (Z_OpT-26)*ZoneTimeStep' in lines
    assert 'set DegreeHoursBelowLowerLimit_Z = (20-Z_OpT)*ZoneTimeStep' in lines
    assert ltd.zone_lines('Z', (19.0, 25.5))[1] == 'if Z_OpT > 25.5'
    names = [ltd.long_term_variable(output, 'Z') for output in OUTPUTS]
    erl = ErlProgramSet({f'{ltd.PROGRAM_PREFIX}Z': lines}, global_variables=['Occ_count_Z', 'Z_OpT'] + names)
    erl.set('ZoneTimeStep', 0.25)
    erl.set('Occ_count_Z', occupants)
    erl.set('Z_OpT', temperature)
    erl.run(f'{ltd.PROGRAM_PREFIX}Z')
    found = {output: erl.get(ltd.long_term_variable(output, 'Z')) for output in OUTPUTS}
    method_a = hours_outside_range([temperature], [20.0], [26.0], occupied=[occupants], timestep_h=0.25)
    method_b = degree_hours([temperature], [20.0], [26.0], occupied=[occupants], timestep_h=0.25)
    assert found['Hours Above Upper Limit'] == pytest.approx(method_a['hot_h'], abs=1e-12)
    assert found['Hours Below Lower Limit'] == pytest.approx(method_a['cold_h'], abs=1e-12)
    assert found['Degree Hours Above Upper Limit'] == pytest.approx(method_b['hot_Kh'], abs=1e-12)
    assert found['Degree Hours Below Lower Limit'] == pytest.approx(method_b['cold_Kh'], abs=1e-12)


def test_the_building_adds_up_its_zones():
    zones = ['Z1', 'Z2', 'Z3']
    erl = _erl(zones)
    erl.set('ZoneTimeStep', 1 / STEPS)
    # Each zone runs its program with its own setpoints (RunACCIS_<zone> sets them before), and then the building
    cases = {'Z1': (1, 28.0, 20, 26), 'Z2': (2, 17.0, 20, 26), 'Z3': (0, 30.0, 20, 26)}
    for zone, (occupants, temperature, lower, upper) in cases.items():
        erl.set(f'Occ_count_{zone}', occupants)
        erl.set(f'{zone}_OpT', temperature)
        erl.set('AHSTnoTol', lower)
        erl.set('ACSTnoTol', upper)
        erl.run(f'{ltd.PROGRAM_PREFIX}{zone}')
    erl.run(ltd.BUILDING_PROGRAM)
    for output in OUTPUTS:
        total = sum(erl.get(ltd.long_term_variable(output, zone)) for zone in zones)
        assert erl.get(ltd.long_term_variable(output, ltd.BUILDING)) == pytest.approx(total, abs=1e-12)
    assert erl.get('HoursAboveUpperLimit_Building') == pytest.approx(1 / STEPS)
    assert erl.get('DegreeHoursBelowLowerLimit_Building') == pytest.approx(3 / STEPS)
    # One zone in each line of the building
    assert ltd.building_lines(['Z1', 'Z2'])[:3] == [
        'set HoursAboveUpperLimit_Building = 0',
        'set HoursAboveUpperLimit_Building = HoursAboveUpperLimit_Building+HoursAboveUpperLimit_Z1',
        'set HoursAboveUpperLimit_Building = HoursAboveUpperLimit_Building+HoursAboveUpperLimit_Z2']


# The model ---------------------------------------------------------------------------------------------------------

def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


def _declared(idf):
    return {str(name).strip() for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
            for name in g.fieldvalues[1:] if str(name).strip()}


def _model(tmp_path, **arguments):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type=arguments.pop('script_type', 'vrf_mm'),
                         supply_air_temp_input_method='temperature difference',
                         output_type=arguments.pop('output_type', 'standard'),
                         output_frequencies=arguments.pop('output_frequencies', ['hourly']),
                         keep_existing_outputs=False, setpoint_type=arguments.pop('setpoint_type', 'temperature'),
                         verbose=False, **arguments)
    return idf


def _check_the_objects(idf, frequencies, limits=None):
    from accim.sim.ems.inputs import input_programs

    programs = _programs(idf)
    declared = _declared(idf)
    ems_outputs = {o.Name: o for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    # The range of each zone, as verify_accim_simulation reads it
    assert ltd.model_long_term_limits(idf) == dict.fromkeys(ZONES, limits)
    for zone in ZONES:
        assert programs[f'{ltd.PROGRAM_PREFIX}{zone}'] == ltd.zone_lines(zone, limits)
        run = programs[f'RunACCIS_{zone}']
        assert run[run.index(f'run CountHoursNoApp_{zone}') + 1] == f'run {ltd.PROGRAM_PREFIX}{zone}'
    # The zones in the order of their programs SetInputData_<zone>
    assert sorted(input_programs(idf)) == ZONES
    assert programs[ltd.BUILDING_PROGRAM] == ltd.building_lines(list(input_programs(idf)))
    for zone in ZONES + [ltd.BUILDING]:
        for output, (variable, units) in ltd.OUTPUTS.items():
            name = f'{output}_{zone}'
            assert f'{variable}_{zone}' in declared
            found = ems_outputs[name]
            assert (found.EMS_Variable_Name, found.Type_of_Data_in_Variable, found.Update_Frequency,
                    found.Units) == (f'{variable}_{zone}', 'Summed', 'ZoneTimestep', units)
            assert {(name, frequency) for frequency in frequencies} <= requested
    # The building adds up the zones once they have run: its calling manager is after theirs
    managers = [m.Name for m in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
                if m.EnergyPlus_Model_Calling_Point == 'BeginTimestepBeforePredictor']
    assert managers[-1] == ltd.BUILDING_PROGRAM
    assert all(managers.index(f'RunACCIS_{zone}') < managers.index(ltd.BUILDING_PROGRAM) for zone in ZONES)


@needs_idd
@pytest.mark.parametrize('output_type', ['standard', 'simplified'])
def test_add_accis_to_idf_adds_the_long_term_discomfort(tmp_path, output_type):
    idf = _model(tmp_path, output_type=output_type, output_frequencies=['hourly', 'monthly'],
                 report_long_term_discomfort=True)
    assert ltd.has_long_term_discomfort(idf)
    _check_the_objects(idf, ['Hourly', 'Monthly'])
    # Once only
    with pytest.raises(ValueError, match='already has the long-term discomfort'):
        ltd.set_long_term_discomfort_code(idf)


@needs_idd
def test_without_the_argument_the_models_have_no_long_term_discomfort(tmp_path):
    idf = _model(tmp_path)
    assert not ltd.has_long_term_discomfort(idf)
    names = {o.Name for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert not any('Upper Limit' in name or 'Lower Limit' in name for name in names)
    # set_long_term_discomfort_code adds it to the models of add_accis_to_idf, with the Output:Variable objects given
    names = ltd.set_long_term_discomfort_code(idf, frequencies=['Daily'])
    assert names == {zone: [f'{output}_{zone}' for output in OUTPUTS] for zone in names}
    assert sorted(names) == sorted(ZONES + [ltd.BUILDING]) and list(names)[-1] == ltd.BUILDING
    _check_the_objects(idf, ['Daily'])


@needs_idd
def test_add_accis_to_idf_with_a_constant_range(tmp_path):
    idf = _model(tmp_path, output_frequencies=['hourly'], report_long_term_discomfort=True,
                 long_term_range=('en16798', 3, 'office'))
    _check_the_objects(idf, ['Hourly'], limits=(19.0, 27.0))
    # The other programs are those without the range
    for name in ('without', 'no'):
        (tmp_path / name).mkdir()
    without = _model(tmp_path / 'without', report_long_term_discomfort=True)
    assert {name: lines for name, lines in _programs(idf).items() if not name.startswith(ltd.PROGRAM_PREFIX)} == {
        name: lines for name, lines in _programs(without).items() if not name.startswith(ltd.PROGRAM_PREFIX)}
    # The range needs the long-term discomfort, and is checked
    with pytest.raises(ValueError, match='long_term_range is the range of the long-term discomfort: it needs '
                                         'report_long_term_discomfort=True'):
        _model(tmp_path / 'no', long_term_range=('en16798', 2))
    with pytest.raises(ValueError, match='depend on the building type'):
        _model(tmp_path / 'no', report_long_term_discomfort=True, long_term_range=('en16798', 4))


@needs_idd
def test_the_long_term_discomfort_needs_temperature_setpoints_and_a_boolean(tmp_path):
    with pytest.raises(ValueError, match="report_long_term_discomfort needs setpoint_type 'temperature'"):
        _model(tmp_path, setpoint_type='pmv', report_long_term_discomfort=True)
    with pytest.raises(ValueError, match="report_long_term_discomfort must be True or False, not 'yes'"):
        _model(tmp_path, report_long_term_discomfort='yes')


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_have_no_long_term_discomfort(tmp_path):
    from accim.sim.accis import load_idf

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    with pytest.raises(ValueError, match='needs the ACCIS of accim 1.0.0 or later'):
        ltd.set_long_term_discomfort_code(building)


def _add_accis(folder, monkeypatch, **arguments):
    """The output IDFs of AddAccis of the sample model in a folder."""
    from accim.sim.accis import AddAccis

    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    defaults = dict(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                    output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                    energyplus_version='auto', setpoint_type='temperature', comfort_standard=[1], category=[2],
                    comfort_mode=[3], confirm=True, verbose=False)
    defaults.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**defaults)
    return sorted(folder.glob('TestModel[[]*.idf'))


@needs_idd
@pytest.mark.parametrize('output_type', ['standard', 'simplified'])
def test_add_accis_adds_the_long_term_discomfort(tmp_path, monkeypatch, output_type):
    from accim.sim.accis import load_idf

    paths = _add_accis(tmp_path, monkeypatch, output_type=output_type, output_frequencies=['hourly', 'daily'],
                       report_long_term_discomfort=True, comfort_standard=[1, 2], category=[2, 80])
    assert len(paths) == 2
    for path in paths:
        _check_the_objects(load_idf(path), ['Hourly', 'Daily'])


@needs_idd
def test_add_accis_checks_the_long_term_discomfort(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="report_long_term_discomfort needs setpoint_type 'temperature'"):
        _add_accis(tmp_path, monkeypatch, setpoint_type='pmv', report_long_term_discomfort=True)
    with pytest.raises(ValueError, match='long_term_range is the range of the long-term discomfort'):
        _add_accis(tmp_path, monkeypatch, long_term_range=('en16798', 2))
    with pytest.raises(ValueError, match='The category of long_term_range must be 1, 2, 3 or 4'):
        _add_accis(tmp_path, monkeypatch, report_long_term_discomfort=True, long_term_range=('en16798', 'II'))
    assert not list(tmp_path.glob('TestModel[[]*.idf'))


@needs_idd
def test_add_accis_with_a_constant_range(tmp_path, monkeypatch):
    from accim.sim.accis import AddAccis, load_idf

    paths = _add_accis(tmp_path / 'two', monkeypatch, report_long_term_discomfort=True, long_term_range=['en16798', 2],
                       comfort_standard=[1, 2], category=[2, 80])
    assert len(paths) == 2
    # The same range in the models of both comfort standards
    for path in paths:
        _check_the_objects(load_idf(path), ['Hourly'], limits=(20.0, 26.0))
    # The argument of the instance
    folder = tmp_path / 'one'
    folder.mkdir()
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        accis = AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         energyplus_version='auto', setpoint_type='temperature', comfort_standard=[1], category=[2],
                         comfort_mode=[3], confirm=True, verbose=False, report_long_term_discomfort=True,
                         long_term_range=('en16798', 2))
    assert accis.arguments['long_term_range'] == ('en16798', 2)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _output_idf(folder, monkeypatch, begin, end, frequency, **arguments):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full
    air-conditioning) whose input IDF has the run period given."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=[frequency], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False, **arguments)
    [path] = folder.glob('TestModel[[]*.idf')
    return path


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


@needs_energyplus
@pytest.mark.parametrize('week, begin, end', [('winter', (1, 1), (1, 7)), ('summer', (7, 15), (7, 21))])
def test_the_long_term_discomfort_in_energyplus(tmp_path, monkeypatch, capsys, week, begin, end):
    from accim.utils.verification import verify_accim_simulation

    model = _output_idf(tmp_path / week, monkeypatch, begin, end, 'timestep', report_long_term_discomfort=True)
    results = _run_energyplus(model, tmp_path / week / 'out')
    assert len(results) == 7 * 24 * STEPS

    # Check 6 of verify_accim_simulation, for each zone and the building
    mismatches = verify_accim_simulation(str(tmp_path / week / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0
    for zone in ZONES:
        for name in OUTPUTS:
            assert f"'{zone}' Check6_{name} ({name}_{zone} from the operative temperature of the previous " \
                   f"timestep): 0 mismatch(es) in {7 * 24 * STEPS - 1} timesteps" in output
    for name in OUTPUTS:
        assert f"'Building' Check6_{name} ({name}_Building, the sum of the zones): 0 mismatch(es)" in output

    # The totals of the week are those of the functions of D1 (Methods A and B), with the operative temperature of
    # the previous timestep (that which the EMS reads), the setpoints without the tolerance and the occupied hours
    totals = dict.fromkeys(OUTPUTS, 0.0)
    for zone in ZONES:
        key = zone.replace('_', ':').upper()
        temperature = results[f'{key}:Zone Operative Temperature [C](TimeStep)']
        hours = results[f'EMS:Occupied Hours_{zone} [H](TimeStep)']
        lower = results[f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone} [C](TimeStep)']
        upper = results[f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone} [C](TimeStep)']
        previous = temperature.shift(1)
        rows = slice(1, None)
        method_a = hours_outside_range(previous[rows], lower[rows], upper[rows], occupied=hours[rows],
                                       timestep_h=hours[rows])
        method_b = degree_hours(previous[rows], lower[rows], upper[rows], occupied=hours[rows],
                                timestep_h=hours[rows])
        expected = {'Hours Above Upper Limit': method_a['hot_h'], 'Hours Below Lower Limit': method_a['cold_h'],
                    'Degree Hours Above Upper Limit': method_b['hot_Kh'],
                    'Degree Hours Below Lower Limit': method_b['cold_Kh']}
        for output, (_, units) in ltd.OUTPUTS.items():
            # EnergyPlus writes the units of the EMS output variables in capitals
            found = results[f'EMS:{output}_{zone} [{units.upper()}](TimeStep)']
            assert found.iloc[1:].sum() == pytest.approx(expected[output], abs=1e-6)
            totals[output] += found.sum()
        # Method A: the occupied hours above and below add up to the discomfortable occupied hours of the ACCIS
        discomfortable = results[f'EMS:Occupied Discomfortable Hours_No Applicability_{zone} [H](TimeStep)']
        np.testing.assert_allclose(results[f'EMS:Hours Above Upper Limit_{zone} [H](TimeStep)']
                                   + results[f'EMS:Hours Below Lower Limit_{zone} [H](TimeStep)'], discomfortable,
                                   rtol=0, atol=1e-9)
    for output, (_, units) in ltd.OUTPUTS.items():
        assert results[f'EMS:{output}_Building [{units.upper()}](TimeStep)'].sum() == pytest.approx(totals[output])
    # Some discomfort to count: the warm side in summer
    if week == 'summer':
        assert totals['Hours Above Upper Limit'] > 0 and totals['Degree Hours Above Upper Limit'] > 0


@needs_energyplus
def test_the_constant_range_in_energyplus_with_both_backends(tmp_path, monkeypatch, capsys):
    from accim.sim.energyplus_api import run_simulations
    from accim.utils.verification import verify_accim_simulation

    # A summer week at timestep frequency, with the limits of category II of EN 16798-1, Table B.2
    model = _output_idf(tmp_path / 'model', monkeypatch, (7, 15), (7, 21), 'timestep', report_long_term_discomfort=True,
                        long_term_range=('en16798', 2))
    results = _run_energyplus(model, tmp_path / 'ems')
    assert len(results) == 7 * 24 * STEPS
    api = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                          processes=1)
    assert api[0].success, api[0].error
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / 'api' / 'run.csv'), results, check_exact=True)

    # Check 6 of verify_accim_simulation, with the constant range of the programs
    mismatches = verify_accim_simulation(str(tmp_path / 'ems' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0
    for zone in ZONES:
        assert f"'{zone}': the constant range of long_term_range, 20.0 to 26.0 °C." in output
        for name in OUTPUTS:
            assert f"'{zone}' Check6_{name} ({name}_{zone} from the operative temperature of the previous " \
                   f"timestep): 0 mismatch(es) in {7 * 24 * STEPS - 1} timesteps" in output

    # The totals of the week are those of the functions of D1 with the constant limits
    for zone in ZONES:
        key = zone.replace('_', ':').upper()
        previous = results[f'{key}:Zone Operative Temperature [C](TimeStep)'].shift(1)
        hours = results[f'EMS:Occupied Hours_{zone} [H](TimeStep)']
        rows = slice(1, None)
        lower = pd.Series(20.0, index=previous.index)[rows]
        upper = pd.Series(26.0, index=previous.index)[rows]
        method_a = hours_outside_range(previous[rows], lower, upper, occupied=hours[rows], timestep_h=hours[rows])
        method_b = degree_hours(previous[rows], lower, upper, occupied=hours[rows], timestep_h=hours[rows])
        expected = {'Hours Above Upper Limit': method_a['hot_h'], 'Hours Below Lower Limit': method_a['cold_h'],
                    'Degree Hours Above Upper Limit': method_b['hot_Kh'],
                    'Degree Hours Below Lower Limit': method_b['cold_Kh']}
        for output, (_, units) in ltd.OUTPUTS.items():
            found = results[f'EMS:{output}_{zone} [{units.upper()}](TimeStep)']
            assert found.iloc[1:].sum() == pytest.approx(expected[output], abs=1e-6)
        # Above 26 °C some hours in which the operative temperature is below the cooling setpoint of the ACCIS
        assert expected['Hours Above Upper Limit'] > 0
        discomfortable = results[f'EMS:Occupied Discomfortable Hours_No Applicability_{zone} [H](TimeStep)'].sum()
        assert expected['Hours Above Upper Limit'] + expected['Hours Below Lower Limit'] != pytest.approx(
            discomfortable)


@needs_energyplus
def test_the_long_term_discomfort_does_not_change_the_simulation(tmp_path, monkeypatch):
    without = _run_energyplus(_output_idf(tmp_path / 'without', monkeypatch, (7, 15), (7, 17), 'hourly'),
                              tmp_path / 'without' / 'out')
    with_it = _run_energyplus(_output_idf(tmp_path / 'with', monkeypatch, (7, 15), (7, 17), 'hourly',
                                          report_long_term_discomfort=True), tmp_path / 'with' / 'out')
    added = [column for column in with_it.columns if column not in without.columns]
    assert len(added) == 4 * (len(ZONES) + 1)
    pd.testing.assert_frame_equal(with_it[list(without.columns)], without, check_exact=True)


@needs_energyplus
def test_the_ems_and_api_backends_give_the_same_long_term_discomfort(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    # 10 days of July, hourly
    model = _output_idf(tmp_path / 'model', monkeypatch, (7, 1), (7, 10), 'hourly', report_long_term_discomfort=True)
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    assert ems_results['EMS:Hours Above Upper Limit_Building [H](Hourly)'].sum() > 0
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
