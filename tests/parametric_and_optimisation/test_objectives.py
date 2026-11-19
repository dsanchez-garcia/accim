"""Tests for the reducers of accim.parametric_and_optimisation.objectives.

checked_sum_results comes from the tag archive/feat-comfort-metrics-experiment-api (notes/branch-reviews.md, 2.2).
hours_outside_comfort and fraction_outside_comfort are the comfort objectives independent of the control that the
author chose instead of the EMS metrics of that tag (notes/decisions.md). hours_outside_range, degree_hours and
deviation_constraint_bound are the long-term comfort objectives of proposal C2 of accim 1.2.0 (Methods A and B of
CEN/TR 16798-2:2019, Annex D, which the ACCIS counts with report_long_term_discomfort, and the acceptable deviations
of its Annex E, Table E.1); ppd_weighted_hours is Method C, which the setpoints based on the PMV count with
report_ppd_weighted_hours (task H3 of the review of accim 1.2.0).
"""
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from accim.parametric_and_optimisation.objectives import (WorstPeriodDeviation, average_results,
                                                          checked_sum_results, degree_hours,
                                                          deviation_constraint_bound, fraction_outside_comfort,
                                                          hours_outside_comfort, hours_outside_range,
                                                          ppd_weighted_hours, return_time_series, sum_results)

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


# The worst week, month or year of Table E.1 as a constraint (proposal C2, done on 2026-11-18) -------------------------

ZONE_HOURS = ('Occupied Hours_Block1_Zone1', 'Occupied Hours_Block1_Zone2')


def _worst(rows, sizing=0, skipped=(0,), **kwargs):
    """A WorstPeriodDeviation as setup leaves it with the sample model (its two zones), the rows of some sizing periods
    and a run period of some rows (``skipped``: the days 29 February that EnergyPlus may skip)."""
    reader = WorstPeriodDeviation(**kwargs)
    reader.occupied_outputs = list(ZONE_HOURS)
    reader.sizing_rows = sizing
    reader.run_period_rows = rows
    reader.skipped_rows = skipped
    return reader


def _eso_results(frequency, outputs):
    """Results of besos (read_eso) of some outputs ('<key>,<variable>': values) at a frequency."""
    return {(name, frequency): SimpleNamespace(name=name, frequency=frequency, data=pd.DataFrame({'Value': values}))
            for name, values in outputs.items()}


def test_the_worst_period_of_table_e1_of_the_rows_of_the_run_period():
    import datetime

    from accim.data.postprocessing.long_term_discomfort import calendar_weeks, period_deviations

    # Two design days (whose rows come first) and 15 days from Thursday 20 June 2002: 4, 7 and 4 days of three weeks
    days = [datetime.date(2002, 6, 20) + datetime.timedelta(days=n) for n in range(15)]
    day_types = [9.0, 10.0] + [float(day.isoweekday() % 7 + 1) for day in days]
    zone_1 = [99.0, 99.0] + [8.0 if day.isoweekday() < 6 else 0.0 for day in days]
    zone_2 = [99.0, 99.0] + [4.0 if day.isoweekday() < 6 else 0.0 for day in days]
    above = [99.0, 0.0] + [6.0, 6.0, 0.0, 0.0] + [6.0] * 5 + [0.0] * 2 + [12.0, 0.0, 0.0, 0.0]
    results = _eso_results('Daily', {'EMS,Hours Above Upper Limit_Building': above,
                                     'EMS,Occupied Hours_Block1_Zone1': zone_1,
                                     'EMS,Occupied Hours_Block1_Zone2': zone_2})
    results.update(_eso_results('Daily', {'Environment,Site Day Type Index': day_types}))
    reader = _worst(15, sizing=2)
    # The weeks have 24, 60 and 48 occupied hours (12 h on each working day), so 12, 30 and 24 h within the deviation
    # of 50 % of the 6 % level, and 12, 30 and 12 h above the upper limit: the worst excess is 0 (the design days,
    # with 99 h, are left out)
    weeks = period_deviations(above[2:], np.add(zone_1, zone_2)[2:], calendar_weeks(day_types[2:]))
    assert weeks['occupied_h'].tolist() == [24.0, 60.0, 48.0]
    assert weeks['excess_h'].tolist() == [0.0, 0.0, 12.0 - 24.0]
    assert reader(results) == weeks['excess_h'].max() == 0.0
    # On the 3 % level, 20 % of the occupied hours of each week
    assert _worst(15, sizing=2, level='3%')(results) == pytest.approx(max(12 - 4.8, 30 - 12.0, 12 - 9.6))
    # The rows of the run period are those after the rows of the sizing periods: with other rows, a ValueError
    for rows, sizing in ((15, 1), (15, 3), (14, 2), (16, 2)):
        with pytest.raises(ValueError, match=f'not {sizing} of the sizing periods and {rows} of the run period'):
            _worst(rows, sizing=sizing)(results)
    # One more hour above in the second week is an hour beyond the deviation, the violation of the constraint '<=0'
    import platypus

    results[('EMS,Hours Above Upper Limit_Building', 'Daily')].data.loc[8, 'Value'] += 1.0
    assert reader(results) == pytest.approx(1.0)
    assert platypus.Constraint('<=0')(reader(results)) == pytest.approx(1.0)
    assert platypus.Constraint('<=0')(0.0) == 0
    # A row for each month (after the row of the design day): 25 % of the occupied hours of each one
    months = _eso_results('Monthly', {'EMS,Hours Above Upper Limit_Block1_Zone1': [50.0, 10.0, 30.0, 25.0],
                                      'EMS,Occupied Hours_Block1_Zone1': [8.0, 40.0, 100.0, 120.0]})
    reader = _worst(3, sizing=1, zone='Block1_Zone1', period='monthly')
    reader.occupied_outputs = ['Occupied Hours_Block1_Zone1']
    assert reader(months) == pytest.approx(max(10 - 10.0, 30 - 25.0, 25 - 30.0))
    # The run period ('yearly'): its row, after that of the design day
    run_period = _eso_results('RunPeriod', {'EMS,Hours Below Lower Limit_Block1_Zone1': [5.0, 130.0],
                                            'EMS,Occupied Hours_Block1_Zone1': [8.0, 2100.0]})
    reader = _worst(1, sizing=1, zone='Block1_Zone1', output='Hours Below Lower Limit', period='yearly')
    reader.occupied_outputs = ['Occupied Hours_Block1_Zone1']
    assert reader(run_period) == pytest.approx(130.0 - 126.0)


def test_the_worst_week_of_table_e1_without_the_days_29_february_that_energyplus_skips():
    # A run period of 2004 (a leap year) from Monday 23 February to Sunday 7 March, with a design day before it: with a
    # weather file without 29 February (and the weather not treated as actual), EnergyPlus skips that day, so the run
    # period has 13 rows instead of 14, and the days of the week follow each other over it (found by the review of
    # 2026-11-18: the reader took the last 14 rows, the design day among them)
    import datetime

    from accim.data.postprocessing.long_term_discomfort import calendar_weeks, period_deviations

    days = [day for day in (datetime.date(2004, 2, 23) + datetime.timedelta(days=n) for n in range(14))
            if (day.month, day.day) != (2, 29)]
    # EnergyPlus goes on with the days of the week over the day skipped: 1 March is a Sunday for it, and 7 March a
    # Saturday (the stamps of the ESO file of the review)
    weekdays = [day.isoweekday() for day in days[:6]] + [7] + [1, 2, 3, 4, 5, 6]
    day_types = [10.0] + [float(weekday % 7 + 1) for weekday in weekdays]
    occupied = [12.0] + [8.0 if weekday < 6 else 0.0 for weekday in weekdays]
    above = [12.0] + [4.0, 4.0, 4.0, 4.0, 5.0, 0.0, 0.0] + [4.0, 4.0, 4.0, 4.0, 4.0, 0.0]
    outputs = {'EMS,Hours Above Upper Limit_Block1_Zone1': above, 'EMS,Occupied Hours_Block1_Zone1': occupied}
    results = _eso_results('Daily', outputs)
    results.update(_eso_results('Daily', {'Environment,Site Day Type Index': day_types}))
    assert len(days) == 13 and len(above) == len(occupied) == len(day_types) == 14
    reader = _worst(14, sizing=1, skipped=(0, 1), zone='Block1_Zone1')
    reader.occupied_outputs = ['Occupied Hours_Block1_Zone1']
    # Two weeks of 40 occupied hours: 21 and 20 h above, 1 and 0 h beyond 50 % (the design day is left out)
    expected = period_deviations(above[1:], occupied[1:], calendar_weeks(day_types[1:]))
    assert expected['occupied_h'].tolist() == [40.0, 40.0] and expected['excess_h'].tolist() == [1.0, 0.0]
    assert reader(results) == pytest.approx(1.0)
    # With the 14 days of the run period (a weather file with 29 February, a Sunday), the rows after the design day
    week = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 1.0]
    above_14 = [12.0] + [4.0, 4.0, 4.0, 4.0, 5.0, 0.0, 0.0] + [4.0] * 5 + [0.0] * 2
    results = _eso_results('Daily', {'EMS,Hours Above Upper Limit_Block1_Zone1': above_14,
                                     'EMS,Occupied Hours_Block1_Zone1': [12.0] + ([8.0] * 5 + [0.0] * 2) * 2})
    results.update(_eso_results('Daily', {'Environment,Site Day Type Index': [10.0] + week * 2}))
    assert reader(results) == pytest.approx(1.0)
    # Without the leap day, 14 rows of the run period are needed
    with pytest.raises(ValueError, match='not 1 of the sizing periods and 14 of the run period'):
        _worst(14, sizing=1, zone='Block1_Zone1')(_eso_results('Daily', outputs))


def test_the_worst_period_of_table_e1_checks_its_arguments_and_the_results():
    reader = WorstPeriodDeviation()
    assert (reader.key_value, reader.variable_name, reader.frequency) == ('EMS', 'Hours Above Upper Limit_Building',
                                                                          'Daily')
    assert reader.name == 'Worst weekly deviation of Hours Above Upper Limit_Building (6%)'
    assert WorstPeriodDeviation(period='monthly', name='Worst month').name == 'Worst month'
    assert WorstPeriodDeviation(period='monthly').frequency == 'Monthly'
    assert WorstPeriodDeviation(period='yearly').frequency == 'RunPeriod'
    for kwargs, match in ((dict(output='Degree Hours Above Upper Limit'), 'output must be one of'),
                          (dict(period='daily'), 'period must be one of'), (dict(level='5%'), 'level must be one of'),
                          (dict(zone=' '), 'zone must be the name of a zone')):
        with pytest.raises(ValueError, match=match):
            WorstPeriodDeviation(**kwargs)
    # Without setup, it does not know the zones and the run period of the model
    with pytest.raises(ValueError, match=r'in setup\(building\)'):
        reader({})
    results = _eso_results('Daily', {'EMS,Hours Above Upper Limit_Building': [1.0, 2.0],
                                     'EMS,Occupied Hours_Block1_Zone1': [8.0, 8.0],
                                     'EMS,Occupied Hours_Block1_Zone2': [8.0, 8.0]})
    with pytest.raises(ValueError, match='no output Environment,Site Day Type Index at Daily frequency'):
        _worst(2)(results)
    results.update(_eso_results('Daily', {'Environment,Site Day Type Index': [2.0, 3.0]}))
    # The occupied hours of the building are those of its two zones, 32 h
    assert _worst(2)(results) == pytest.approx(3.0 - 0.5 * 32.0)
    # The processes of an optimisation in parallel get it with what setup read
    import pickle

    copy = pickle.loads(pickle.dumps(_worst(2)))
    assert (copy.run_period_rows, copy.occupied_outputs, copy.name) == (2, list(ZONE_HOURS), reader.name)
    assert copy(results) == pytest.approx(3.0 - 0.5 * 32.0)
    # Fewer rows than the run period of the model, or values that are not numbers (an incomplete simulation)
    with pytest.raises(ValueError, match='not 0 of the sizing periods and 3 of the run period of the model'):
        _worst(3)(results)
    results[('EMS,Occupied Hours_Block1_Zone2', 'Daily')].data.loc[0, 'Value'] = np.nan
    with pytest.raises(ValueError, match='Occupied Hours_Block1_Zone2 at Daily frequency, not 0 of the sizing periods '
                                         'and 2 of the run period of the model, as finite numbers'):
        _worst(2)(results)


def test_the_worst_period_of_table_e1_in_the_problems_of_the_parametric_module():
    # Found by the review of 2026-11-18: the parametric worker rebuilt it as a plain VariableReader (the sum of the
    # daily values), besos sets up no add_output, and one reader kept the state of the last model set up
    from besos.objectives import VariableReader

    from accim.parametric_and_optimisation.main import (SimulationBase, _problem_for_evaluator,
                                                        _readers_with_model_state)

    worst = WorstPeriodDeviation(period='monthly')
    plain = VariableReader(key_value='EMS', variable_name='Occupied Hours_Block1_Zone1', frequency='Hourly',
                           func=sum_results)
    with pytest.raises(ValueError, match='the simulations of run_parametric_simulation cannot read a '
                                         'WorstPeriodDeviation'):
        SimulationBase._serialize_output_readers([plain, worst], ['plain', worst.name])
    assert [spec['kind'] for spec in SimulationBase._serialize_output_readers([plain], ['plain'])] == ['variable']
    # A problem without such readers is that of every evaluator; with them, each evaluator gets copies of them
    problem = SimpleNamespace(outputs=[plain], constraints=[plain], add_outputs=None)
    assert _problem_for_evaluator(problem) is problem and _readers_with_model_state(problem.outputs) == []
    other = WorstPeriodDeviation(period='weekly')
    problem = SimpleNamespace(outputs=[plain], constraints=[worst, plain], add_outputs=[other])
    copies = [_problem_for_evaluator(problem) for _ in range(2)]
    for copied in copies:
        assert copied is not problem and copied.outputs is problem.outputs
        assert copied.constraints[1] is plain and copied.constraints[0] is not worst
        assert copied.add_outputs[0] is not other and copied.add_outputs[0].name == other.name
    assert copies[0].constraints[0] is not copies[1].constraints[0]
    copies[0].constraints[0].run_period_rows = 12
    assert worst.run_period_rows is None and copies[1].constraints[0].run_period_rows is None


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_worst_period_of_table_e1_in_an_evaluation_of_besos(tmp_path):
    # The constraints of an evaluation of besos against deviation_check of the hourly outputs of the evaluation, with
    # the calendar weeks and months of the dates of the run period (20 June to 10 August 2002, from a Thursday) and the
    # design days, whose rows come first in the outputs
    import datetime
    import warnings

    import platypus
    from besos.eppy_funcs import get_building
    from besos.evaluator import EvaluatorEP
    from besos.objectives import MeterReader, read_eso
    from besos.problem import EPProblem

    from accim.data.postprocessing.long_term_discomfort import deviation_check, deviation_limit
    from accim.sim import accis

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        accis.add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                               output_type='standard', output_frequencies=['hourly'], setpoint_type='temperature',
                               verbose=False, report_long_term_discomfort=True)
    run_period = building.idfobjects['RunPeriod'][0]
    assert str(run_period.Begin_Year) == '2002'
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 6, 20
    run_period.End_Month, run_period.End_Day_of_Month = 8, 10
    building.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'Yes'
    # The outdoor units of the VRF systems with a given rated cooling capacity of 1.5 kW (autosized, they have more
    # than 10 kW), too small for the warm weeks of Seville. Since 2026-11-19 the windows of the sample model are closed
    # on its design days, and its autosized VRF systems keep the building below the upper limit in these weeks
    # (before, sized with the windows open and about 100 times too big, they did not hold the setpoints)
    for unit in building.idfobjects['AirConditioner:VariableRefrigerantFlow']:
        unit.Gross_Rated_Total_Cooling_Capacity = 1500
    readers = [WorstPeriodDeviation(zone, output, period, level)
               for zone, output, level in (('Building', 'Hours Above Upper Limit', '6%'),
                                           ('Block1_Zone2', 'Hours Above Upper Limit', '3%'),
                                           ('Block1_Zone1', 'Hours Below Lower Limit', '6%'))
               for period in ('weekly', 'monthly', 'yearly')]
    problem = EPProblem(inputs=[], outputs=[MeterReader('Electricity:Facility')], constraints=readers,
                        constraint_bounds=['<=0'] * len(readers))
    evaluator = EvaluatorEP(problem=problem, building=building, epw=str(SAMPLE_EPW), out_dir=str(tmp_path / 'out'))
    # The evaluator added the outputs that the readers read to its model
    added = {(o.Key_Value, o.Variable_Name, o.Reporting_Frequency) for o in building.idfobjects['Output:Variable']}
    assert {('EMS', 'Occupied Hours_Block1_Zone1', 'Daily'), ('EMS', 'Hours Above Upper Limit_Building', 'Monthly'),
            ('Environment', 'Site Day Type Index', 'Daily'),
            ('EMS', 'Hours Below Lower Limit_Block1_Zone1', 'RunPeriod')} <= added
    assert [reader.run_period_rows for reader in readers[:3]] == [52, 3, 1]
    assert [reader.sizing_rows for reader in readers[:3]] == [4, 4, 4]
    assert sorted(readers[0].occupied_outputs) == list(ZONE_HOURS)
    assert readers[3].occupied_outputs == ['Occupied Hours_Block1_Zone2']
    *values, out_dir = evaluator.eval_single([], keep_dirs=True)
    constraints = values[1:]
    results = read_eso(out_dir)
    # The hours of the run period, the last 52 days of the hourly outputs (four design days before them)
    hours = 52 * 24
    assert len(results[('EMS,Occupied Hours_Block1_Zone1', 'Hourly')].data) == hours + 4 * 24
    dates = [datetime.date(2002, 6, 20) + datetime.timedelta(days=hour // 24) for hour in range(hours)]

    def hourly(name):
        return results[(f'EMS,{name}', 'Hourly')].data['Value'].to_numpy()[-hours:]

    for reader, constraint in zip(readers, constraints):
        occupied = sum(hourly(name) for name in (ZONE_HOURS if reader.zone == 'Building'
                                                  else (f'Occupied Hours_{reader.zone}',)))
        outside = hourly(f'{reader.output}_{reader.zone}')
        keys = {'weekly': [date.isocalendar()[1] for date in dates], 'monthly': [date.month for date in dates],
                'yearly': [0] * hours}[reader.period]
        periods = pd.DataFrame({'period': keys, 'occupied': occupied, 'outside': outside}).groupby('period').sum()
        # Weeks 25 (from Thursday 20 June) to 32 (to Saturday 10 August)
        assert len(periods) == {'weekly': 8, 'monthly': 3, 'yearly': 1}[reader.period]
        excess = [o - deviation_limit(h, reader.period, reader.level)
                  for o, h in zip(periods.outside, periods.occupied)]
        assert constraint == pytest.approx(max(excess), abs=1e-9), reader.name
        assert (constraint <= 0) == all(deviation_check(o, h, reader.period, reader.level)
                                        for o, h in zip(periods.outside, periods.occupied))
        assert reader(results) == constraint
    # The warm weeks of Seville: the building above the upper limit in more than half of the occupied hours of a week
    # (the VRF systems, with outdoor units of 1.5 kW, do not hold the setpoints), and zone 1 below the lower limit in
    # a few hours only (the first occupied hour of some mornings, after the windows of the model cooled it at night)
    assert constraints[0] > 0 and platypus.Constraint('<=0')(constraints[0]) == pytest.approx(constraints[0])
    assert all(constraint < 0 for constraint in constraints[6:])


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_worst_week_of_table_e1_in_an_evaluation_of_besos_of_a_leap_year(tmp_path):
    # Found by the review of 2026-11-18: a run period of a leap year over 29 February, which EnergyPlus skips with a
    # weather file without it (the weather file of Seville), with the design days before it in the outputs
    import warnings

    from besos.eppy_funcs import get_building
    from besos.evaluator import EvaluatorEP
    from besos.objectives import MeterReader, read_eso
    from besos.problem import EPProblem

    from accim.data.postprocessing.long_term_discomfort import deviation_limit
    from accim.sim import accis

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = get_building(str(tmp_path / 'model.idf'))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        accis.add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                               output_type='standard', output_frequencies=['hourly'], setpoint_type='temperature',
                               verbose=False, report_long_term_discomfort=True)
    run_period = building.idfobjects['RunPeriod'][0]
    # From Monday 23 February to Sunday 7 March 2004
    run_period.Begin_Year, run_period.End_Year = 2004, 2004
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 2, 23
    run_period.End_Month, run_period.End_Day_of_Month = 3, 7
    building.idfobjects['SimulationControl'][0].Run_Simulation_for_Sizing_Periods = 'Yes'
    readers = [WorstPeriodDeviation('Building', 'Hours Below Lower Limit', period, '3%')
               for period in ('weekly', 'monthly')]
    problem = EPProblem(inputs=[], outputs=[MeterReader('Electricity:Facility')], constraints=readers,
                        constraint_bounds=['<=0'] * len(readers))
    evaluator = EvaluatorEP(problem=problem, building=building, epw=str(SAMPLE_EPW), out_dir=str(tmp_path / 'out'))
    assert [(reader.sizing_rows, reader.run_period_rows, reader.skipped_rows) for reader in readers] == [
        (4, 14, (0, 1)), (4, 2, (0,))]
    *values, out_dir = evaluator.eval_single([], keep_dirs=True)
    results = read_eso(out_dir)
    # EnergyPlus simulated 13 days, after the 4 design days
    assert len(results[('EMS,Occupied Hours_Block1_Zone1', 'Daily')].data) == 4 + 13
    hours = 13 * 24

    def hourly(name):
        return results[(f'EMS,{name}', 'Hourly')].data['Value'].to_numpy()[-hours:]

    occupied = sum(hourly(name) for name in ZONE_HOURS)
    below = hourly('Hours Below Lower Limit_Building')
    days = np.arange(hours) // 24
    # The weeks of EnergyPlus: 23 February to 1 March (a Sunday for it, after the day skipped), and 2 to 7 March; the
    # months: 6 days of February and 7 of March
    for reader, constraint, periods in ((readers[0], values[1], days // 7), (readers[1], values[2], days >= 6)):
        excess = [below[periods == p].sum() - deviation_limit(occupied[periods == p].sum(), reader.period, '3%')
                  for p in np.unique(periods)]
        assert len(excess) == 2 and constraint == pytest.approx(max(excess), abs=1e-9), reader.name
        assert reader(results) == constraint


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_worst_period_of_table_e1_as_a_constraint_of_an_optimisation(tmp_path, monkeypatch):
    # The readers as the constraints of an OptimisationSimulation of accim (its evaluator of besos, the model with its
    # outputs, and the Pareto status with the constraints)
    import warnings

    from besos.eppy_funcs import get_building

    from accim.parametric_and_optimisation.main import OptimisationSimulation

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    building = get_building(str(tmp_path / 'model.idf'))
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 7, 1
    run_period.End_Month, run_period.End_Day_of_Month = 7, 14
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        optimisation = OptimisationSimulation(buildings=[building], epws=[str(SAMPLE_EPW)],
                                              parameters_type='accim predefined model',
                                              output_frequencies=['hourly'], verbose=False,
                                              report_long_term_discomfort=True)
    selection = optimisation.select_outputs(meters=['Electricity:HVAC'], on_missing='raise')
    optimisation.apply_outputs_preflight(df_meters_sel=selection['meters'], clean_mode='all')
    readers = selection['meters'].copy()
    readers['func'] = [sum_results] * len(readers)
    optimisation.set_output_readers(df_output_meter=readers)
    optimisation.set_parameters(accis_params_dict={'category': [1, 3]})
    constraints = [WorstPeriodDeviation(period='weekly'),
                   WorstPeriodDeviation('Block1_Zone1', period='monthly', level='3%')]
    # Also as an add_output, which besos does not set up (the evaluators of accim do, since the review of 2026-11-18)
    reported = WorstPeriodDeviation(period='weekly', name='Reported worst week')
    optimisation.set_problem(minimize_outputs=[True], constraints=constraints, constraint_bounds=['<=0', '<=0'],
                             add_outputs=[reported])
    results = optimisation.run_optimisation(out_dir=str(tmp_path / 'optim'), algorithm='NSGAII', evaluations=2,
                                            population_size=2, processes=1)
    assert len(results) == 2 and 'pareto-optimal' in results.columns
    for reader in constraints + [reported]:
        assert np.isfinite(results[reader.name].to_numpy(dtype=float)).all()
    np.testing.assert_array_equal(results['Reported worst week'].to_numpy(dtype=float),
                                  results[constraints[0].name].to_numpy(dtype=float))
    # The evaluator set up its own copies of the readers with its model; those of the problem keep no state
    [evaluator] = [value for value in optimisation.evaluators.values() if value is not None]
    copies = list(evaluator.problem.constraints) + list(evaluator.problem.add_outputs)
    assert [reader.run_period_rows for reader in copies] == [14, 1, 14]
    assert [reader.sizing_rows for reader in copies] == [0, 0, 0]
    assert all(reader.run_period_rows is None for reader in constraints + [reported])


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists()),
                    reason='needs EnergyPlus 25.1 (its IDD) and the sample files of the repository')
def test_the_worst_period_of_table_e1_checks_the_model(tmp_path):
    import warnings

    from besos.eppy_funcs import get_building

    from accim.sim import accis

    def model(report=True):
        shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
        building = get_building(str(tmp_path / 'model.idf'))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            accis.add_accis_to_idf(building, script_type='vrf_ac',
                                   supply_air_temp_input_method='temperature difference', output_type='standard',
                                   output_frequencies=['hourly'], setpoint_type='temperature', verbose=False,
                                   report_long_term_discomfort=report)
        return building

    with pytest.raises(ValueError, match=r'no output Hours Above Upper Limit_Building of the long-term discomfort of '
                                         r'the ACCIS \(report_long_term_discomfort=True\); its zones are \[\]'):
        WorstPeriodDeviation().setup(model(report=False))
    building = model()
    with pytest.raises(ValueError, match=r"no output Hours Below Lower Limit_Block1_Zone3 .*its zones are "
                                         r"\['Block1_Zone1', 'Block1_Zone2'\]"):
        WorstPeriodDeviation('Block1_Zone3', 'Hours Below Lower Limit').setup(building)
    # The zone as in the names of the outputs of the model, whatever its case
    reader = WorstPeriodDeviation('block1_zone1', period='monthly')
    reader.setup(building)
    assert (reader.variable_name, reader.occupied_outputs) == ('Hours Above Upper Limit_Block1_Zone1',
                                                               ['Occupied Hours_Block1_Zone1'])
    # One run period
    building.copyidfobject(building.idfobjects['RunPeriod'][0])
    with pytest.raises(ValueError, match='needs a model that simulates one run period .* not 2'):
        WorstPeriodDeviation().setup(building)
    building.removeidfobject(building.idfobjects['RunPeriod'][1])
    building.idfobjects['SimulationControl'][0].Run_Simulation_for_Weather_File_Run_Periods = 'No'
    with pytest.raises(ValueError, match='not 0'):
        WorstPeriodDeviation().setup(building)


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
    # The outdoor units of the VRF systems with a given rated cooling capacity of 1.5 kW, too small for the zones in
    # the afternoons of July (autosized, they have more than 10 kW and keep them below the upper limit in this week
    # since 2026-11-19, when the windows of the sample model were closed on its design days)
    for unit in building.idfobjects['AirConditioner:VariableRefrigerantFlow']:
        unit.Gross_Rated_Total_Cooling_Capacity = 1500
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
    # A week of July in Seville with the outdoor units of 1.5 kW: hours above the cooling setpoint (without the
    # tolerance) when occupied
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


def test_the_ppd_weighted_hours_reducer():
    for name in ('EMS,PPD Weighted Hours_Block1_Zone1', 'EMS,PPD WEIGHTED HOURS_BLOCK1_ZONE2'):
        assert ppd_weighted_hours(_long_term(name, [0.25, 0, 1.5])) == 1.75
    assert ppd_weighted_hours(SimpleNamespace(data={'Value': [2.0]})) == 2.0
    with pytest.raises(ValueError, match='ppd_weighted_hours reads the outputs "PPD Weighted Hours_<zone>" of the '
                                         'setpoints based on the PMV'):
        ppd_weighted_hours(_long_term('EMS,Hours Above Upper Limit_Block1_Zone1', [1.0]))
    with pytest.raises(ValueError, match='finite numbers'):
        ppd_weighted_hours(_long_term('EMS,PPD Weighted Hours_Block1_Zone1', [np.nan]))
    # The reducers of Methods A and B do not take it
    with pytest.raises(ValueError, match='hours_outside_range reads the outputs'):
        hours_outside_range(_long_term('EMS,PPD Weighted Hours_Block1_Zone1', [1.0]))


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
@pytest.mark.parametrize('parameters_type', ['apmv setpoints', 'epmv setpoints'])
@pytest.mark.parametrize('report', [False, True])
def test_the_parametric_module_adds_the_ppd_weighted_hours(tmp_path, monkeypatch, parameters_type, report):
    import warnings

    from accim.parametric_and_optimisation.main import ParametricSimulation
    from accim.sim.accis import load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[building], epws=[str(SAMPLE_EPW)],
                                          parameters_type=parameters_type, output_frequencies=['hourly'],
                                          verbose=False, report_long_term_discomfort=report)
    # With the setpoints based on the PMV, the long-term discomfort is Method C (task H3 of the review of 1.2.0)
    programs = {p.Name for p in simulation.building.idfobjects['EnergyManagementSystem:Program']}
    names = {o.Name for o in simulation.building.idfobjects['EnergyManagementSystem:OutputVariable']}
    assert ('count_ppd_weighted_hours_Block1_Zone1' in programs) is report
    assert ('PPD Weighted Hours_Block1_Zone2' in names) is report
    assert not any(name.startswith('Hours Above Upper Limit') for name in names)


@pytest.mark.skipif(not (ENERGYPLUS_25_1.exists() and SAMPLE_IDF.exists() and SAMPLE_EPW.exists()),
                    reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_parametric_module_forwards_the_long_term_range(tmp_path, monkeypatch):
    import warnings

    from accim.parametric_and_optimisation.main import ParametricSimulation
    from accim.sim.accis import load_idf
    from accim.sim.ems.long_term_discomfort import model_long_term_limits

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[load_idf(tmp_path / 'model.idf')], epws=[str(SAMPLE_EPW)],
                                          parameters_type='accim predefined model', output_frequencies=['hourly'],
                                          verbose=False, report_long_term_discomfort=True,
                                          long_term_range=('en16798', 2))
        assert model_long_term_limits(simulation.building) == {'Block1_Zone1': (20.0, 26.0),
                                                               'Block1_Zone2': (20.0, 26.0)}
        # The setpoints based on the PMV have their own range
        with pytest.raises(ValueError, match='long_term_range is the range of the temperature setpoints of the ACCIS'):
            ParametricSimulation(buildings=[load_idf(tmp_path / 'model.idf')], epws=[str(SAMPLE_EPW)],
                                 parameters_type='apmv setpoints', output_frequencies=['hourly'], verbose=False,
                                 report_long_term_discomfort=True, long_term_range=('en16798', 2))
