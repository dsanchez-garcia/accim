"""Tests for the floor areas and the energy columns of the plotting methods.

The plotting methods convert the energy columns to kWh, or to kWh/m2 with ``normalize_per_m2=True``, with the
floor area of the IDF of each row. Before, they kept fallbacks that ``normalize_outputs`` no longer has: the rows
of an IDF without floor area were divided by 1 m2 (``fillna(1.0)``), a table without 'idf' column was divided
by the area of the first IDF, and every column whose name contained 'Heating', 'Cooling', 'Energy'... was taken
as energy, including the adaptive setpoint temperatures of accim ('EMS:Adaptive Cooling Setpoint Temperature
[C]'), which were divided by 3.6e6 and labelled kWh. The hourly plots (``HourlyPlottingMixin``) left the values
of an IDF without area out of the plot, and also took the first area without 'idf' column.
"""
import pandas as pd
import pytest

from accim.parametric_and_optimisation.hourly_plotting import HourlyPlottingMixin
from accim.parametric_and_optimisation.plotting import PlottingMixin

AREAS = {'office_a': 100.0, 'office_b': 250.0}


class _PlotSession(PlottingMixin):
    def __init__(self, building_floor_area):
        self.building_floor_area = building_floor_area
        self.outputs_normalized = False


class _HourlyPlotSession(HourlyPlottingMixin):
    def __init__(self, building_floor_area):
        self.building_floor_area = building_floor_area


@pytest.mark.parametrize('column, expected', [
    ('Heating:Electricity [J](Hourly)', True),
    ('Heating:Electricity [kWh/m2](Hourly)', True),
    ('Heating:Electricity', True),
    ('Electricity:HVAC_kWh/m2', True),
    ('EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)', False),
    ('EMS:Adaptive Heating Setpoint Temperature_No Tolerance [C](Hourly)', False),
    ('Zone Air System Sensible Cooling Rate [W](Hourly)', False),
    ('EMS:Ventilation Hours [H](Hourly)', False),
    ('Operative temperature FLOOR_1_ZONE', False),
])
def test_energy_columns_are_identified_by_their_unit_or_by_their_name_without_unit(column, expected):
    assert PlottingMixin._is_energy_like_column(column) is expected


def test_each_row_is_divided_by_the_floor_area_of_its_idf():
    df = pd.DataFrame({'idf': ['office_b', 'office_a', 'office_b'], 'Heating:Electricity': [3.6e8, 3.6e8, 7.2e8]})

    divisors = PlottingMixin._per_m2_divisors(df, AREAS, 3.6e6, 'the plotted results')

    assert list(divisors) == [3.6e6 * 250, 3.6e6 * 100, 3.6e6 * 250]
    # The labels are matched without folder, extension and backup affixes, as in normalize_outputs
    labelled = pd.DataFrame({'idf': ['office_a.IDF', 'models/office_b.idf']})
    assert list(PlottingMixin._per_m2_divisors(labelled, AREAS, 1.0, 'the plotted results')) == [100.0, 250.0]


def test_an_idf_without_floor_area_is_not_divided_by_1_m2():
    df = pd.DataFrame({'idf': ['office_a', 'office_c'], 'Heating:Electricity': [3.6e8, 3.6e8]})

    with pytest.raises(ValueError, match=r"no floor area for the IDF\(s\) \['office_c'\]"):
        PlottingMixin._per_m2_divisors(df, AREAS, 3.6e6, 'the plotted results')


def test_several_floor_areas_need_the_idf_column():
    df = pd.DataFrame({'Heating:Electricity': [3.6e8]})

    with pytest.raises(ValueError, match="has no 'idf' column"):
        PlottingMixin._per_m2_divisors(df, AREAS, 3.6e6, 'the plotted results')
    # One area, or IDFs with the same area, apply to every row
    assert PlottingMixin._per_m2_divisors(df, 50.0, 3.6e6, 'the plotted results') == 3.6e6 * 50
    assert PlottingMixin._per_m2_divisors(df, {'a': 50.0, 'b': 50.0}, 3.6e6, 'the plotted results') == 3.6e6 * 50


def test_plot_columns_convert_only_energy_to_kwh_per_m2():
    session = _PlotSession(AREAS)
    df = pd.DataFrame({
        'idf': ['office_a', 'office_b'],
        'Cooling:Electricity [J](Hourly)': [3.6e8, 3.6e8],
        'EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)': [25.0, 26.0],
    })

    (converted, units) = session._normalise_plot_columns(
        df.copy(), list(df.columns[1:]), normalize_per_m2=True, df_source='parametric_hourly')

    assert list(converted['Cooling:Electricity [J](Hourly)']) == [1.0, 0.4]
    assert list(converted['EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)']) == [25.0, 26.0]
    assert units == {'Cooling:Electricity [J](Hourly)': 'kWh/m2',
                     'EMS:Adaptive Cooling Setpoint Temperature [C](Hourly)': None}


def test_plot_columns_of_an_idf_without_floor_area_stop_with_a_clear_error():
    session = _PlotSession({'office_a': 100.0})
    df = pd.DataFrame({'idf': ['office_a', 'office_b'], 'Cooling:Electricity [J](Hourly)': [3.6e8, 3.6e8]})

    with pytest.raises(ValueError, match=r"\['office_b'\]"):
        session._normalise_plot_columns(df, ['Cooling:Electricity [J](Hourly)'], normalize_per_m2=True,
                                        df_source='parametric_hourly')


def test_hourly_plots_take_the_floor_area_of_each_idf():
    session = _HourlyPlotSession(AREAS)
    data = pd.DataFrame({'idf': ['office_b', 'office_a']})

    assert list(session._hp_floor_area(data)) == [250.0, 100.0]
    # An explicit floor area replaces that of the session
    assert session._hp_floor_area(data, floor_area=80.0) == 80.0
    # With a single IDF, its area applies to every row, as before
    assert list(_HourlyPlotSession({'model': 120.0})._hp_floor_area(data)) == [120.0, 120.0]
    assert _HourlyPlotSession(None)._hp_floor_area(data) is None


def test_hourly_plots_of_an_idf_without_floor_area_stop_with_a_clear_error():
    session = _HourlyPlotSession(AREAS)

    with pytest.raises(ValueError, match=r"\['office_c'\]"):
        session._hp_floor_area(pd.DataFrame({'idf': ['office_a', 'office_c']}))
    with pytest.raises(ValueError, match="no 'idf' column"):
        session._hp_floor_area(pd.DataFrame({'datetime': [0, 1]}))
    assert _HourlyPlotSession({'a': 60.0, 'b': 60.0})._hp_floor_area(pd.DataFrame({'datetime': [0]})) == 60.0
