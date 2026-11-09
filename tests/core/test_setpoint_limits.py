"""Tests for the floor and ceiling of the setpoints and the occupied hours below some temperatures (proposal B5,
:mod:`accim.sim.ems.setpoint_limits`).

EN 16798-1:2019, Annex B: Table B.2 gives the default design values of the indoor operative temperature (the minimum
for heating and the maximum for cooling, by type of building and category), which B.2.2 applies in winter also to the
buildings without mechanical cooling. ``heating_setpoint_floor`` and ``cooling_setpoint_ceiling`` bound the setpoints of
the ACCIS before their rounding, whatever the comfort standard and the comfort mode, and ``report_hours_below`` adds the
occupied hours below some temperatures (section 5, B5, of the proposals of 1.2.0). The setpoints based on the PMV have
neither floor nor ceiling (decision D5). The unit tests run the EMS programs with the Erl interpreter of accim
(compute_setpoints); the last tests simulate output IDFs of AddAccis with EnergyPlus 25.1 (a winter and a summer week,
verify_accim_simulation, and both backends).
"""
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.constants import EN16798_TABLE_B2
from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.ems import setpoint_limits as sl
from accim.sim.ems.erl import ErlProgramSet
from accim.sim.ems.setpoint_lines import ROUNDING
from accim.sim.preview import compute_setpoints
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

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


def test_the_values_of_table_b2_of_en16798_1():
    # EN 16798-1:2019 (UNE-EN 16798-1:2020, page 49), Table B.2: living spaces of residential buildings and offices
    assert EN16798_TABLE_B2 == {
        ('residential', 1): (21.0, 25.5), ('residential', 2): (20.0, 26.0), ('residential', 3): (18.0, 27.0),
        ('residential', 4): (16.0, 28.0), ('office', 1): (21.0, 25.5), ('office', 2): (20.0, 26.0),
        ('office', 3): (19.0, 27.0), ('office', 4): (18.0, 28.0)}
    for floor, ceiling in EN16798_TABLE_B2.values():
        sl.check_setpoint_limits(floor, ceiling)


def test_the_floor_and_ceiling_are_checked():
    sl.check_setpoint_limits(None, None)
    sl.check_setpoint_limits(20, None)
    sl.check_setpoint_limits(None, 26.5)
    sl.check_setpoint_limits(np.float64(20), np.int64(26))
    with pytest.raises(ValueError, match=r'heating_setpoint_floor must be a number \(°C\) or None, not \'20\''):
        sl.check_setpoint_limits('20', None)
    with pytest.raises(ValueError, match='cooling_setpoint_ceiling must be a number'):
        sl.check_setpoint_limits(None, True)
    with pytest.raises(ValueError, match=r"heating_setpoint_floor \(26\) must be lower than cooling_setpoint_ceiling "
                                         r"\(26\) \(zone 'Zone1'\)"):
        sl.check_setpoint_limits(26, 26, where='Zone1')


def test_the_temperatures_of_the_hours_below_are_checked():
    assert sl.check_hours_below(None) == [] and sl.check_hours_below([]) == []
    assert sl.check_hours_below(18) == [18]
    assert sl.check_hours_below((18, 17.5, -2)) == [18, 17.5, -2]
    for value in ('18', [18, 'x'], [True], {'T': 18}):
        with pytest.raises(ValueError, match='report_hours_below must be a list of temperatures'):
            sl.check_hours_below(value)
    with pytest.raises(ValueError, match='repeated temperatures'):
        sl.check_hours_below([18, 18.0])


def test_the_names_of_the_hours_below():
    assert sl.hours_below_variable(18, 'Zone1') == 'HoursBelow_18_Zone1'
    assert sl.hours_below_variable(18.0, 'Zone1') == 'HoursBelow_18_Zone1'
    assert sl.hours_below_variable(17.5, 'Zone1') == 'HoursBelow_17p5_Zone1'
    assert sl.hours_below_variable(-2.25, 'Zone1') == 'HoursBelow_m2p25_Zone1'


def test_the_lines_of_the_program_of_the_limits():
    floor = ['if AHST < AHSTfloor', 'set AHST = AHSTfloor', 'endif']
    ceiling = ['if ACST > ACSTceil', 'set ACST = ACSTceil', 'endif']
    # The bounds, and the rounding of the subprograms of SetAST again
    assert sl.limit_program_lines(True, False) == floor + list(ROUNDING)
    assert sl.limit_program_lines(False, True) == ceiling + list(ROUNDING)
    assert sl.limit_program_lines(True, True) == floor + ceiling + list(ROUNDING)


def test_the_hours_below_in_the_erl_interpreter():
    lines = sl.hours_below_lines('Z', [18, 17.5])
    erl = ErlProgramSet({'CountHoursBelow_Z': lines}, global_variables=['Occ_count_Z', 'Z_OpT', 'HoursBelow_18_Z',
                                                                          'HoursBelow_17p5_Z'])
    erl.set('ZoneTimeStep', 0.25)
    for occupants, temperature, expected in ((2, 17, (0.25, 0.25)), (2, 17.5, (0.25, 0)), (2, 18, (0, 0)),
                                             (0, 17, (0, 0)), (1, -5, (0.25, 0.25))):
        erl.set('Occ_count_Z', occupants)
        erl.set('Z_OpT', temperature)
        erl.run('CountHoursBelow_Z')
        assert (erl.get('HoursBelow_18_Z'), erl.get('HoursBelow_17p5_Z')) == expected


# The setpoints ------------------------------------------------------------------------------------------------------

def _rounded_up(values, accuracy):
    """The heating setpoints as ROUNDING rounds them: up, to the accuracy."""
    return np.ceil(values * accuracy) / accuracy


def _rounded_down(values, accuracy):
    """The cooling setpoints as ROUNDING rounds them: down, strictly, to the accuracy."""
    return (np.ceil(values * accuracy) - 1) / accuracy


@pytest.mark.parametrize('comfort_standard, category, comfort_mode, floor, ceiling', [
    (1, 2, 3, 20, 26),      # INT EN16798, adaptive, both
    (2, 80, 2, 21.5, None),  # INT ASHRAE55, the floor only
    (0, None, None, None, 24.5),  # ESP CTE, static setpoints, the ceiling only
])
def test_the_setpoints_are_bounded_before_their_rounding(comfort_standard, category, comfort_mode, floor, ceiling):
    # Without tolerance, the setpoints without the tolerance are those that SetAST calculates, before their rounding
    arguments = dict(frequency='timestep', start_date='01/07', setpoint_tolerance=0, setpoint_accuracy=10)
    reference = compute_setpoints(EPW, comfort_standard, category, comfort_mode, **arguments)
    bounded = compute_setpoints(EPW, comfort_standard, category, comfort_mode, heating_setpoint_floor=floor,
                                cooling_setpoint_ceiling=ceiling, **arguments)
    heating = reference['AHSTnoTol'].to_numpy()
    cooling = reference['ACSTnoTol'].to_numpy()
    assert np.array_equal(reference['AHST'], _rounded_up(heating, 10))
    assert np.array_equal(reference['ACST'], _rounded_down(cooling, 10))
    if floor is not None:
        heating = np.maximum(heating, floor)
        assert (reference['AHSTnoTol'] < floor).any()
    if ceiling is not None:
        cooling = np.minimum(cooling, ceiling)
        assert (reference['ACSTnoTol'] > ceiling).any()
    # The setpoints of the zone are those of bounding AHST and ACST before their rounding (as at the end of SetAST)
    assert np.array_equal(bounded['AHSTnoTol'], heating) and np.array_equal(bounded['ACSTnoTol'], cooling)
    assert np.array_equal(bounded['AHST'], _rounded_up(heating, 10))
    assert np.array_equal(bounded['ACST'], _rounded_down(cooling, 10))
    if floor is not None:
        assert bounded['AHST'].min() == floor
    if ceiling is not None:
        # The cooling setpoint is rounded down, below the ceiling
        assert bounded['ACST'].max() == pytest.approx(ceiling - 0.1, rel=0, abs=1e-12)
    # The other values do not change
    others = [column for column in reference.columns if column not in ('AHST', 'ACST', 'AHSTnoTol', 'ACSTnoTol')]
    pd.testing.assert_frame_equal(bounded[others], reference[others])


def test_the_setpoint_ems_code_with_the_floor_and_ceiling():
    code = get_setpoint_ems_code(1, 2, 3)
    assert 'AHSTfloor' not in code and 'ApplySetpointLimits' not in code
    code = get_setpoint_ems_code(1, 2, 3, heating_setpoint_floor=20)
    assert 'set AHSTfloor = 20' in code and 'if AHST < AHSTfloor' in code
    assert 'set ACSTceil' not in code and 'if ACST > ACSTceil' not in code
    assert '! --- ApplySetpointLimits_<zone>: after SetAST, the floor of the heating setpoint' in code
    assert code.index('! --- ApplySetpointLimits_<zone>') < code.index('! --- SetASTnoTol')
    programs = get_setpoint_ems_programs(1, 2, 3, heating_setpoint_floor=20, cooling_setpoint_ceiling=26.5)
    names = list(programs)
    assert names[names.index('ApplySetpointLimits_<zone>') + 1] == 'SetASTnoTol'
    assert programs['ApplySetpointLimits_<zone>'] == sl.limit_program_lines(True, True)
    assert {'set AHSTfloor = 20', 'set ACSTceil = 26.5'} <= set(programs['SetInputData_<zone>'])
    with pytest.raises(ValueError, match='must be lower than'):
        get_setpoint_ems_code(1, 2, 3, heating_setpoint_floor=27, cooling_setpoint_ceiling=26)


# The models ---------------------------------------------------------------------------------------------------------

def _add_accis(folder, monkeypatch, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                  output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                  setpoint_type='temperature', comfort_standard=[1, 2], category=[1, 80], comfort_mode=[3],
                  hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    return {path.name: path for path in folder.glob('TestModel[[]*.idf')}


def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


def _global_variables(idf):
    return [[str(name).strip() for name in g.fieldvalues[1:] if str(name).strip()]
            for g in idf.idfobjects['EnergyManagementSystem:GlobalVariable']]


@needs_idd
def test_add_accis_adds_the_floor_and_ceiling(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf

    reference = _add_accis(tmp_path / 'reference', monkeypatch)
    # With None, the output IDFs are those without the arguments (those of 1.1.0)
    same = _add_accis(tmp_path / 'none', monkeypatch, heating_setpoint_floor=None, cooling_setpoint_ceiling=None,
                      report_hours_below=None)
    assert sorted(same) == sorted(reference) and len(reference) == 2
    assert all(same[name].read_bytes() == reference[name].read_bytes() for name in reference)
    outputs = _add_accis(tmp_path / 'limits', monkeypatch, heating_setpoint_floor=20, cooling_setpoint_ceiling=26)
    assert sorted(outputs) == sorted(reference)
    for name in reference:
        idf, before = load_idf(outputs[name]), load_idf(reference[name])
        programs, programs_before = _programs(idf), _programs(before)
        added = [f'ApplySetpointLimits_{zone}' for zone in ZONES]
        assert set(programs) - set(programs_before) == set(added)
        # The same programs, in the same order, but the inputs of the zones and the lines that run the new programs
        assert [p for p in programs if p not in added] == list(programs_before)
        for zone in ZONES:
            assert programs[f'ApplySetpointLimits_{zone}'] == sl.limit_program_lines(True, True)
            # The inputs, in the order of accim.sim.ems.inputs.INPUT_VARIABLES
            inputs = programs[f'SetInputData_{zone}']
            new = ['set AHSTfloor = 20', 'set ACSTceil = 26']
            assert inputs[inputs.index(new[0]):inputs.index(new[0]) + 2] == new
            assert [line for line in inputs if line not in new] == programs_before[f'SetInputData_{zone}']
            run = programs[f'RunACCIS_{zone}']
            assert run[run.index('run SetAST') + 1] == f'run ApplySetpointLimits_{zone}'
            assert [line for line in run if line != f'run ApplySetpointLimits_{zone}'] == programs_before[
                f'RunACCIS_{zone}']
        changed = {f'SetInputData_{zone}' for zone in ZONES} | {f'RunACCIS_{zone}' for zone in ZONES} | set(added)
        assert all(programs[p] == programs_before[p] for p in programs if p not in changed)
        assert _global_variables(idf) == _global_variables(before) + [['AHSTfloor', 'ACSTceil']]
        assert sl.zone_limits(idf) == {zone: {'AHSTfloor': 20, 'ACSTceil': 26} for zone in ZONES}


@needs_idd
def test_the_floor_and_ceiling_of_some_zones(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf

    outputs = _add_accis(tmp_path, monkeypatch, comfort_standard=[1], category=[1],
                         zone_arguments={'Block1:Zone2': {'heating_setpoint_floor': 21}})
    [idf] = [load_idf(path) for path in outputs.values()]
    programs = _programs(idf)
    assert 'ApplySetpointLimits_Block1_Zone1' not in programs
    assert programs['ApplySetpointLimits_Block1_Zone2'] == sl.limit_program_lines(True, False)
    assert 'run ApplySetpointLimits_Block1_Zone1' not in programs['RunACCIS_Block1_Zone1']
    assert sl.zone_limits(idf) == {'Block1_Zone1': {'AHSTfloor': None, 'ACSTceil': None},
                                   'Block1_Zone2': {'AHSTfloor': 21, 'ACSTceil': None}}
    # The zone takes the ceiling of all the zones, and its own floor
    outputs = _add_accis(tmp_path / 'both', monkeypatch, comfort_standard=[1], category=[1],
                         cooling_setpoint_ceiling=26, zone_arguments={'Block1:Zone2': {'heating_setpoint_floor': 21}})
    [idf] = [load_idf(path) for path in outputs.values()]
    assert sl.zone_limits(idf) == {'Block1_Zone1': {'AHSTfloor': None, 'ACSTceil': 26},
                                   'Block1_Zone2': {'AHSTfloor': 21, 'ACSTceil': 26}}


@needs_idd
def test_add_accis_checks_the_floor_and_ceiling(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='must be lower than'):
        _add_accis(tmp_path, monkeypatch, heating_setpoint_floor=26, cooling_setpoint_ceiling=25)
    with pytest.raises(ValueError, match=r"must be lower than cooling_setpoint_ceiling \(21\) \(zone 'Block1:Zone1'\)"):
        _add_accis(tmp_path, monkeypatch, heating_setpoint_floor=22,
                   zone_arguments={'Block1:Zone1': {'cooling_setpoint_ceiling': 21}})
    with pytest.raises(ValueError, match='must be a number'):
        _add_accis(tmp_path, monkeypatch, cooling_setpoint_ceiling='26')
    # The PMV-based setpoints have neither floor nor ceiling (decision D5)
    with pytest.raises(ValueError, match="need setpoint_type 'temperature'"):
        _add_accis(tmp_path, monkeypatch, setpoint_type='pmv', heating_setpoint_floor=20)
    with pytest.raises(ValueError, match='report_hours_below must be a list of temperatures'):
        _add_accis(tmp_path, monkeypatch, report_hours_below='18')
    assert not list(tmp_path.glob('TestModel[[]*.idf'))


@needs_idd
@pytest.mark.parametrize('output_type', ['standard', 'simplified'])
def test_add_accis_adds_the_hours_below(tmp_path, monkeypatch, output_type):
    from accim.sim.accis import load_idf

    outputs = _add_accis(tmp_path, monkeypatch, comfort_standard=[1], category=[1], output_type=output_type,
                         output_frequencies=['hourly', 'daily'], report_hours_below=[18, 17.5])
    [idf] = [load_idf(path) for path in outputs.values()]
    programs = _programs(idf)
    ems_outputs = {o.Name: o for o in idf.idfobjects['EnergyManagementSystem:OutputVariable']}
    requested = {(o.Variable_Name, o.Reporting_Frequency) for o in idf.idfobjects['Output:Variable']}
    declared = {name for names in _global_variables(idf) for name in names}
    for zone in ZONES:
        assert programs[f'CountHoursBelow_{zone}'] == sl.hours_below_lines(zone, [18, 17.5])
        run = programs[f'RunACCIS_{zone}']
        assert run[run.index(f'run CountHoursNoApp_{zone}') + 1] == f'run CountHoursBelow_{zone}'
        for name in (f'HoursBelow_18_{zone}', f'HoursBelow_17p5_{zone}'):
            assert name in declared
            output = ems_outputs[name]
            assert (output.EMS_Variable_Name, output.Type_of_Data_in_Variable, output.Update_Frequency,
                    output.Units) == (name, 'Summed', 'ZoneTimestep', 'H')
            assert {(name, 'Hourly'), (name, 'Daily')} <= requested
    # Without setpoints of the temperature too (the counters only need the occupants and the operative temperature)
    outputs = _add_accis(tmp_path / 'pmv', monkeypatch, setpoint_type='pmv', report_hours_below=[20])
    [idf] = [load_idf(path) for path in outputs.values()]
    assert 'set HoursBelow_20_Block1_Zone1 = 1*ZoneTimeStep' in _programs(idf)['CountHoursBelow_Block1_Zone1']


@needs_idd
def test_modify_accis_adds_and_keeps_the_floor_and_ceiling(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis

    def model():
        shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
        idf = load_idf(tmp_path / 'model.idf')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            add_accis_to_idf(idf, script_type='vrf_mm', supply_air_temp_input_method='temperature difference',
                             output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                             setpoint_type='temperature', verbose=False)
        return idf

    idf = model()
    modify_accis(idf, heating_setpoint_floor=20)
    assert sl.zone_limits(idf) == {zone: {'AHSTfloor': 20, 'ACSTceil': None} for zone in ZONES}
    assert _programs(idf)['ApplySetpointLimits_Block1_Zone1'] == sl.limit_program_lines(True, False)
    # The arguments that are None keep their values
    modify_accis(idf, cooling_setpoint_ceiling=26.5, zone_arguments={'Block1:Zone2': {'heating_setpoint_floor': 18}})
    modify_accis(idf, setpoint_tolerance=0.2)
    assert sl.zone_limits(idf) == {'Block1_Zone1': {'AHSTfloor': 20, 'ACSTceil': 26.5},
                                   'Block1_Zone2': {'AHSTfloor': 18, 'ACSTceil': 26.5}}
    programs = _programs(idf)
    for zone in ZONES:
        assert programs[f'ApplySetpointLimits_{zone}'] == sl.limit_program_lines(True, True)
        assert programs[f'RunACCIS_{zone}'].count(f'run ApplySetpointLimits_{zone}') == 1
    assert _global_variables(idf).count(['AHSTfloor', 'ACSTceil']) == 1
    with pytest.raises(ValueError, match=r"heating_setpoint_floor \(27\) must be lower than cooling_setpoint_ceiling "
                                         r"\(26.5\)"):
        modify_accis(idf, heating_setpoint_floor=27)
    # The parametric module sets them in all the zones, as modify_accis does
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis

    other = model()
    param_accis.modify_AHSTfloor(other, 20)
    param_accis.modify_ACSTceil(other, 26.5)
    reference = model()
    modify_accis(reference, heating_setpoint_floor=20, cooling_setpoint_ceiling=26.5)
    assert sl.zone_limits(other) == sl.zone_limits(reference)
    programs, reference_programs = _programs(other), _programs(reference)
    for zone in ZONES:
        for name in (f'ApplySetpointLimits_{zone}', f'RunACCIS_{zone}'):
            assert programs[name] == reference_programs[name]
    assert _global_variables(other) == _global_variables(reference)
    with pytest.raises(ValueError, match=r"heating_setpoint_floor \(27\) must be lower than cooling_setpoint_ceiling"):
        param_accis.modify_AHSTfloor(other, 27)


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_have_no_floor_nor_ceiling(tmp_path):
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis
    from accim.sim.accis import load_idf, modify_accis

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    with pytest.raises(ValueError, match='whose setpoints have neither floor nor ceiling'):
        modify_accis(building, heating_setpoint_floor=20)
    with pytest.raises(ValueError, match='whose setpoints have neither floor\\s+nor ceiling'):
        param_accis.modify_ACSTceil(building, 26)
    modify_accis(building, comfort_standard=99, comfort_mode=3)
    assert not sl.has_setpoint_limits(building)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
THRESHOLDS = [26, 25, 24.5]


def _output_idf(folder, monkeypatch, begin, end, frequency, **arguments):
    """An output IDF of AddAccis of the sample model (INT EN16798, category II, full air-conditioning), whose input
    IDF has the run period given, with the operative temperature and the occupants of the zones as outputs."""
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
    idf = load_idf(path)
    for variable in ('Zone Operative Temperature', 'Zone People Occupant Count'):
        idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=variable,
                         Reporting_Frequency=frequency.capitalize())
    idf.saveas(str(folder / 'model.idf'))
    return folder / 'model.idf'


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


@needs_energyplus
@pytest.mark.parametrize('week, begin, end', [('winter', (1, 1), (1, 7)), ('summer', (7, 15), (7, 21))])
def test_the_floor_ceiling_and_hours_below_in_energyplus(tmp_path, monkeypatch, capsys, week, begin, end):
    from accim.utils.verification import verify_accim_simulation

    model = _output_idf(tmp_path / week, monkeypatch, begin, end, 'timestep', heating_setpoint_floor=20,
                        cooling_setpoint_ceiling=26, report_hours_below=THRESHOLDS)
    results = _run_energyplus(model, tmp_path / week / 'out')
    assert len(results) == 7 * 24 * STEPS

    # The setpoints are those of compute_setpoints (check 4), within the floor and the ceiling (check 5)
    mismatches = verify_accim_simulation(str(tmp_path / week / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check[45]').any()
    for zone in ZONES:
        for check in ('Check5_AHSTfloor', 'Check5_ACSTceil', 'Check4_AHST', 'Check4_ACST'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 1008 timesteps", output), (zone, check)
        heating = results[f'EMS:Adaptive Heating Setpoint Temperature_{zone} [C](TimeStep)']
        cooling = results[f'EMS:Adaptive Cooling Setpoint Temperature_{zone} [C](TimeStep)']
        assert heating.min() >= 20 and cooling.max() <= 26
        # The floor in winter and the ceiling in summer bound the setpoints (the cooling setpoint rounded down)
        if week == 'winter':
            assert (heating == 20).all()
        else:
            assert np.isclose(cooling, 25.9999, rtol=0, atol=1e-9).sum() > 0.9 * len(cooling)

        # The occupied hours below each temperature: the length of the timestep when the zone has occupants and its
        # operative temperature of the previous timestep (that which the EMS reads) is below the temperature
        key = zone.replace('_', ':').upper()
        temperature = results[f'{key}:Zone Operative Temperature [C](TimeStep)'].to_numpy()
        occupied = results[f'{key}:Zone People Occupant Count [](TimeStep)'].to_numpy() > 0
        previous = np.r_[np.nan, temperature[:-1]]
        totals = []
        for threshold in THRESHOLDS:
            found = results[f'EMS:{sl.hours_below_variable(threshold, zone)} [H](TimeStep)'].to_numpy()
            expected = np.where(occupied & (previous < threshold), 1 / STEPS, 0.0)
            np.testing.assert_allclose(found[1:], expected[1:], rtol=0, atol=1e-12)
            totals.append(found.sum())
        # Fewer hours below a lower temperature, and some hours below the highest one
        assert totals == sorted(totals, reverse=True) and totals[0] > 0


@needs_energyplus
def test_the_ems_and_api_backends_give_the_same_floor_ceiling_and_hours_below(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    # 10 days of January, the floor of each zone and the ceiling of zone 2, hourly
    model = _output_idf(tmp_path / 'model', monkeypatch, (1, 1), (1, 10), 'hourly', heating_setpoint_floor=21,
                        zone_arguments={'Block1:Zone2': {'cooling_setpoint_ceiling': 24}},
                        report_hours_below=THRESHOLDS)
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    assert any(column.startswith('EMS:HoursBelow_24p5_Block1_Zone2 [') for column in ems_results.columns)
    assert (ems_results['EMS:Adaptive Heating Setpoint Temperature_Block1_Zone1 [C](Hourly)'] >= 21).all()
    assert (ems_results['EMS:Adaptive Cooling Setpoint Temperature_Block1_Zone2 [C](Hourly)'] < 24).all()
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
