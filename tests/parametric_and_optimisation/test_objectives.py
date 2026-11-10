"""Tests for the reducers of accim.parametric_and_optimisation.objectives.

checked_sum_results comes from the tag archive/feat-comfort-metrics-experiment-api (notes/branch-reviews.md, 2.2).
hours_outside_comfort and fraction_outside_comfort are the comfort objectives independent of the control that the
author chose instead of the EMS metrics of that tag (notes/decisions.md). hours_outside_range, degree_hours and
deviation_constraint_bound are the long-term comfort objectives of proposal C2 of accim 1.2.0 (Methods A and B of
CEN/TR 16798-2:2019, Annex D, which the ACCIS counts with report_long_term_discomfort, and the acceptable deviations
of its Annex E, Table E.1).
"""
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from accim.parametric_and_optimisation.objectives import (average_results, checked_sum_results, degree_hours,
                                                          deviation_constraint_bound, fraction_outside_comfort,
                                                          hours_outside_comfort, hours_outside_range,
                                                          return_time_series, sum_results)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
SAMPLE_EPW = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'Seville.epw')
ENERGYPLUS_25_1 = Path('C:/EnergyPlusV25-1-0/energyplus.exe')
CEN_II = 'Zone Thermal Comfort CEN 15251 Adaptive Model Category II Status'
ASHRAE_80 = 'Zone Thermal Comfort ASHRAE 55 Adaptive Model 80% Acceptability Status'


def _result(values):
    return SimpleNamespace(data=pd.DataFrame({'Value': values}))


@pytest.mark.parametrize('values', [[], [np.nan], [np.inf], [[1, 2]], ['not a number'], [1e308, 1e308]])
def test_checked_sum_results_rejects_invalid_objectives(values):
    with pytest.raises(ValueError):
        checked_sum_results(SimpleNamespace(data={'Value': values}))


def test_checked_sum_results_returns_one_finite_float():
    result = checked_sum_results(SimpleNamespace(data={'Value': [0.1, 0.2, 0.3]}))

    assert isinstance(result, float)
    assert result == pytest.approx(0.6)


@pytest.mark.parametrize('result', [None, SimpleNamespace(data=None), SimpleNamespace(data={'Other': [1.0]})])
def test_checked_sum_results_needs_a_value_series(result):
    with pytest.raises(ValueError, match='"Value" series'):
        checked_sum_results(result)


def test_with_missing_values_sum_results_skips_them_and_checked_sum_results_stops():
    # An empty or incomplete series must not give a valid objective (0 would look like the best energy use)
    assert sum_results(_result([1.0, np.nan, 2.0])) == 3.0
    assert sum_results(_result(pd.Series([], dtype=float))) == 0.0
    with pytest.raises(ValueError, match='finite numbers'):
        checked_sum_results(_result([1.0, np.nan, 2.0]))
    with pytest.raises(ValueError, match='finite numbers'):
        checked_sum_results(_result(pd.Series([], dtype=float)))


def test_the_reducers_of_a_dataframe_result():
    result = _result([1.0, 2.0, 4.5])

    assert checked_sum_results(result) == 7.5
    assert sum_results(result) == 7.5
    assert average_results(result) == 2.5
    assert return_time_series(result) == [1.0, 2.0, 4.5]


def _status(values, frequency='Hourly'):
    """A BESOS result (EPResults) of a comfort status variable."""
    return SimpleNamespace(data=pd.DataFrame({'Value': values}), frequency=frequency)


def test_hours_and_fraction_outside_comfort_of_hourly_values():
    # Empty, outside, inside, half the hour outside, and one sixth of it outside
    result = _status([-1, 0, 1, 0.5, 5 / 6])

    assert hours_outside_comfort(result) == pytest.approx(1 + 0.5 + 1 / 6)
    assert fraction_outside_comfort(result) == pytest.approx((1 + 0.5 + 1 / 6) / 4)
    # Without the frequency of a BESOS result, the values are taken as hourly
    assert hours_outside_comfort(SimpleNamespace(data={'Value': [0, 0, 1]})) == 2.0


def test_the_comfort_reducers_without_occupied_values_give_0():
    assert hours_outside_comfort(_status([-1, -1])) == 0.0
    assert fraction_outside_comfort(_status([-1, -1])) == 0.0


@pytest.mark.parametrize('values', [[0.0, 1.5], [21.3, 24.0], [np.nan], ['inside']])
def test_the_comfort_reducers_reject_values_that_are_not_a_comfort_status(values):
    for reducer in (hours_outside_comfort, fraction_outside_comfort):
        with pytest.raises(ValueError):
            reducer(_status(values))


def test_the_frequencies_of_the_comfort_reducers():
    assert fraction_outside_comfort(_status([0, 1, 1, 1], frequency='TimeStep')) == 0.25
    with pytest.raises(ValueError, match='frequency TimeStep; this reducer needs hourly values'):
        hours_outside_comfort(_status([0, 1], frequency='TimeStep'))
    for reducer in (hours_outside_comfort, fraction_outside_comfort):
        with pytest.raises(ValueError, match='frequency Daily'):
            reducer(_status([0.5], frequency='Daily'))
    with pytest.raises(ValueError, match='"Value" series'):
        hours_outside_comfort(SimpleNamespace(data=None))


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_comfort_reducers_with_the_status_that_energyplus_reports(tmp_path):
    from besos.eppy_funcs import get_building
    from besos.objectives import read_eso

    from accim.sim import accis

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    accis.add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                           output_type='simplified', output_frequencies=['hourly'], setpoint_type='temperature',
                           verbose=False)
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 5, 10
    run_period.End_Month, run_period.End_Day_of_Month = 5, 16
    for variable in (CEN_II, ASHRAE_80):
        for frequency in ('Timestep', 'Hourly'):
            building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=variable,
                                  Reporting_Frequency=frequency)
    building.saveas(str(tmp_path / 'model.idf'))
    subprocess.run([str(ENERGYPLUS_25_1), '-d', str(tmp_path / 'out'), '-w', str(SAMPLE_EPW),
                    str(tmp_path / 'model.idf')], capture_output=True, check=True)
    results = read_eso(str(tmp_path / 'out'))

    timesteps_per_hour = int(building.idfobjects['Timestep'][0].Number_of_Timesteps_per_Hour)
    for people in ('PEOPLE BLOCK1:ZONE1', 'PEOPLE BLOCK1:ZONE2'):
        for variable in (CEN_II, ASHRAE_80):
            each_timestep = results[(f'{people},{variable}', 'TimeStep')]
            hourly = results[(f'{people},{variable}', 'Hourly')]
            values = each_timestep.data['Value']
            assert set(values.unique()) <= {-1.0, 0.0, 1.0}
            outside, inside = int((values == 0).sum()), int((values == 1).sum())
            # The occupants of the sample model arrive and leave on the hour, so the hourly means are exact
            assert hours_outside_comfort(hourly) == pytest.approx(outside / timesteps_per_hour)
            assert fraction_outside_comfort(hourly) == pytest.approx(outside / (outside + inside))
            assert fraction_outside_comfort(each_timestep) == pytest.approx(outside / (outside + inside))


# The long-term discomfort (proposal C2) -----------------------------------------------------------------------------

def _long_term(name, values, units='H'):
    """A BESOS result (EPResults) of an output of the long-term discomfort of the ACCIS."""
    return SimpleNamespace(name=name, frequency='Hourly', units=units, data=pd.DataFrame({'Value': values}))


def test_the_long_term_reducers_sum_their_outputs():
    for name in ('EMS,Hours Above Upper Limit_Block1_Zone1', 'EMS,Hours Below Lower Limit_Block1_Zone1',
                 'EMS,Hours Above Upper Limit_Building', 'EMS,HOURS BELOW LOWER LIMIT_BLOCK1_ZONE2'):
        assert hours_outside_range(_long_term(name, [0.5, 0, 1.0])) == 1.5
    for name in ('EMS,Degree Hours Above Upper Limit_Block1_Zone1', 'EMS,Degree Hours Below Lower Limit_Building'):
        assert degree_hours(_long_term(name, [0.25, 1.5], units='KH')) == 1.75
    # Without the name of a BESOS result, only the values are checked
    assert hours_outside_range(SimpleNamespace(data={'Value': [1.0, 2.0]})) == 3.0
    assert degree_hours(SimpleNamespace(data={'Value': [0.5]})) == 0.5


def test_the_long_term_reducers_check_their_outputs():
    with pytest.raises(ValueError, match='hours_outside_range reads the outputs "Hours Above Upper Limit_<zone>" or '
                                         '"Hours Below Lower Limit_<zone>"'):
        hours_outside_range(_long_term('EMS,Degree Hours Above Upper Limit_Block1_Zone1', [1.0]))
    with pytest.raises(ValueError, match='degree_hours reads the outputs "Degree Hours Above Upper Limit_<zone>"'):
        degree_hours(_long_term('EMS,Hours Above Upper Limit_Block1_Zone1', [1.0]))
    with pytest.raises(ValueError, match='report_long_term_discomfort=True'):
        hours_outside_range(_long_term('BLOCK1:ZONE1,Zone Operative Temperature', [21.0]))
    # The values as checked_sum_results checks them: an incomplete simulation is not a valid objective
    with pytest.raises(ValueError, match='finite numbers'):
        hours_outside_range(_long_term('EMS,Hours Above Upper Limit_Building', [1.0, np.nan]))


def test_the_constraint_bounds_of_the_acceptable_deviations_of_table_e1():
    # CEN/TR 16798-2:2019, Annex E, Table E.1: with 2100 occupied hours a year, 63 h on the 3 % level and 126 h on the
    # 6 % level; 20 % or 50 % of the 40 h of a week, 8 h or 20 h; 12 % or 25 % of the 175 h of a month
    assert deviation_constraint_bound(2100) == '<=126.0'
    assert deviation_constraint_bound(2100, level='3%') == '<=63.0'
    assert deviation_constraint_bound(40, 'weekly', '3%') == '<=8.0'
    assert deviation_constraint_bound(40, 'weekly') == '<=20.0'
    assert deviation_constraint_bound(175, 'monthly', '3%') == '<=21.0'
    assert deviation_constraint_bound(175, 'monthly') == '<=43.75'
    with pytest.raises(ValueError, match='level must be one of'):
        deviation_constraint_bound(2100, level='5%')
    with pytest.raises(ValueError, match='period must be one of'):
        deviation_constraint_bound(2100, period='daily')
    # The constraints of the optimisation are those of platypus: no violation within the bound, and the hours beyond it
    import platypus

    assert platypus.Constraint(deviation_constraint_bound(2100))(126.0) == 0
    assert platypus.Constraint(deviation_constraint_bound(2100))(130.0) == pytest.approx(4.0)


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_long_term_reducers_with_the_outputs_that_energyplus_reports(tmp_path):
    from besos.eppy_funcs import get_building
    from besos.objectives import read_eso

    from accim.sim import accis

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    accis.add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                           output_type='standard', output_frequencies=['hourly'], setpoint_type='temperature',
                           verbose=False, report_long_term_discomfort=True)
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 7, 10
    run_period.End_Month, run_period.End_Day_of_Month = 7, 16
    building.saveas(str(tmp_path / 'model.idf'))
    subprocess.run([str(ENERGYPLUS_25_1), '-d', str(tmp_path / 'out'), '-w', str(SAMPLE_EPW),
                    str(tmp_path / 'model.idf')], capture_output=True, check=True)
    results = read_eso(str(tmp_path / 'out'))

    for output, reducer in (('Hours Above Upper Limit', hours_outside_range),
                            ('Hours Below Lower Limit', hours_outside_range),
                            ('Degree Hours Above Upper Limit', degree_hours),
                            ('Degree Hours Below Lower Limit', degree_hours)):
        zones = [reducer(results[(f'EMS,{output}_Block1_Zone{n}', 'Hourly')]) for n in (1, 2)]
        building_total = reducer(results[(f'EMS,{output}_Building', 'Hourly')])
        assert building_total == pytest.approx(sum(zones))
        assert building_total == pytest.approx(results[(f'EMS,{output}_Building', 'Hourly')].data['Value'].sum())
    # A week of July in Seville: hours above the cooling setpoint (without the tolerance) when occupied
    assert hours_outside_range(results[('EMS,Hours Above Upper Limit_Building', 'Hourly')]) > 0
    # Method A: the hours above and below are the discomfortable occupied hours of the ACCIS
    for n in (1, 2):
        outside = sum(hours_outside_range(results[(f'EMS,{output}_Block1_Zone{n}', 'Hourly')])
                      for output in ('Hours Above Upper Limit', 'Hours Below Lower Limit'))
        discomfortable = results[(f'EMS,Occupied Discomfortable Hours_No Applicability_Block1_Zone{n}', 'Hourly')]
        assert outside == pytest.approx(checked_sum_results(discomfortable))
    with pytest.raises(ValueError, match='degree_hours reads the outputs'):
        degree_hours(results[('EMS,Hours Above Upper Limit_Building', 'Hourly')])


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
@pytest.mark.parametrize('report', [False, True])
def test_the_parametric_module_adds_the_long_term_discomfort(tmp_path, monkeypatch, report):
    import warnings

    from accim.parametric_and_optimisation.main import ParametricSimulation
    from accim.sim.accis import load_idf
    from accim.sim.ems.long_term_discomfort import has_long_term_discomfort

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[building], epws=[str(SAMPLE_EPW)],
                                          parameters_type='accim predefined model', output_frequencies=['hourly'],
                                          verbose=False, report_long_term_discomfort=report)
    assert has_long_term_discomfort(simulation.building) is report
    names = {o.Name for o in simulation.building.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert ('Hours Above Upper Limit_Building' in names) is report