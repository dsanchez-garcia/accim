"""Tests for Table with the optional EMS outputs of the models with the ACCIS (D2, with the outputs of B1, B2, B5, C2
and A4): the outdoor metric of the custom model (Tout_metric and Tout_metric_<zone>), its regimes (CustomRegime_<zone>),
the occupied hours below some temperatures (HoursBelow_<T>_<zone>), the long-term discomfort of the zones and of the
building (Hours Above Upper Limit_<zone>..., Degree Hours ..._Building) and the outputs of the ATHB (ATHB_PMV_<zone>,
ATHB_clo_<zone>, ATHB_met_<zone>).

Before (checked on 2026-11-10 with a simulation of 3 days of the sample model with all of them, EnergyPlus 25.1 and
the backend of the Python API), Table dropped them all with standard_outputs=True; without it, they kept their EMS names
in capitals ('EMS:ATHB_PMV_BLOCK1:ZONE1 [](HOURLY)'), without block and building values, and, with daily values and
frequency_agg_func='sum', it added up the ATHB_PMV (6.36 instead of 0.265), the clothing and the metabolic rate.

The CSV files have the names of the columns that EnergyPlus gives the outputs (those of that simulation), and made-up
values; a fake IDF replaces the IDF that Table reads (see test_table_pmv_index.py). The last test simulates them.
"""
import builtins
import shutil
import warnings
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import pytest

from accim.data.postprocessing import optional_output_columns as ooc
from accim.sim.targets import resolve_targets

from .test_table_pmv_index import DESIGNBUILDER, RESIDENTIAL, TWO_PEOPLE, _table, _values, _write_csv

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
MODELS = pytest.mark.parametrize('model', [DESIGNBUILDER, RESIDENTIAL, TWO_PEOPLE],
                                 ids=['designbuilder', 'residential', 'two_people'])
#: The optional outputs of each zone, with the units of the columns of EnergyPlus and their values in two hours, and
#: their names in Table ('' if they keep their EMS names)
ZONE_OUTPUTS = {
    'CustomRegime': ('', [1.0, 2.0], 'CustomRegime'),
    'HoursBelow_18': ('H', [1.0, 0.0], 'HoursBelow_18 (h)'),
    'HoursBelow_17p5': ('H', [0.5, 0.0], 'HoursBelow_17p5 (h)'),
    'HoursBelow_m2': ('H', [0.0, 0.25], 'HoursBelow_m2 (h)'),
    'Hours Above Upper Limit': ('H', [0.0, 1.0], 'Hours Above Upper Limit (h)'),
    'Hours Below Lower Limit': ('H', [1.0, 0.0], 'Hours Below Lower Limit (h)'),
    'Degree Hours Above Upper Limit': ('KH', [0.0, 1.5], 'Degree Hours Above Upper Limit (Kh)'),
    'Degree Hours Below Lower Limit': ('KH', [2.0, 0.0], 'Degree Hours Below Lower Limit (Kh)'),
    'ATHB_PMV': ('', [0.1, 0.3], 'ATHB_PMV'),
    'ATHB_clo': ('clo', [0.6, 0.7], 'ATHB_clo (clo)'),
    'ATHB_met': ('MET', [1.05, 1.07], 'ATHB_met (met)'),
    'ATHB_saturated': ('H', [0.0, 0.5], 'ATHB_saturated (h)'),
    'Tout_metric': ('C', [15.0, 16.0], ''),
}
SUMMED = [output for output, (units, _, _) in ZONE_OUTPUTS.items() if units in ('H', 'KH')]
WITH_LEVELS = SUMMED + ['ATHB_PMV', 'ATHB_clo', 'ATHB_met']
LONG_TERM = list(ooc.LONG_TERM_OUTPUTS)


def _outputs(model):
    """The columns of the CSV file of a simulation with all the optional outputs, and their values in two hours of a
    day: {column: [first hour, second hour]}, and the column of each output of each zone, {(zone, output): column}
    (the second zone has its values plus 1, and the building those of the sums of the zones)."""
    columns, of_zone = {}, {}
    targets = resolve_targets(model['building'])
    for number, (zone, target) in enumerate(zip(model['zone_names'], targets)):
        for output, (units, values, _) in ZONE_OUTPUTS.items():
            column = f'EMS:{output}_{target.ems_suffix} [{units}](Hourly)'
            columns[column] = [value + number for value in values]
            of_zone[zone, output] = column
        columns[f'{target.zone_name.upper()}:Zone Operative Temperature [C](Hourly)'] = [26.0 + number, 27.0 + number]
        for key in target.instance_keys:
            columns[f'{key.upper()}:Zone Thermal Comfort Fanger Model PMV [](Hourly)'] = [0.5, 0.7]
    for output in LONG_TERM:
        units = ZONE_OUTPUTS[output][0]
        zone_values = [columns[of_zone[zone, output]] for zone in model['zone_names']]
        columns[f'EMS:{output}_Building [{units}](Hourly)'] = [sum(hour) for hour in zip(*zone_values)]
    columns['EMS:Tout_metric [C](Hourly)'] = [15.5, 16.5]
    return columns, of_zone


def test_the_optional_outputs_are_those_of_accim_sim():
    # A new optional output of accim.sim needs a name in Table (or to keep its EMS name on purpose)
    from accim.sim import comfort_hooks
    from accim.sim.ems import custom_regimes, long_term_discomfort, outdoor_metric, setpoint_limits

    units = {'H': 'h', 'Kh': 'Kh'}
    assert {output: f'{output} ({units[unit]})' for output, (_, unit) in long_term_discomfort.OUTPUTS.items()} == \
        ooc.LONG_TERM_OUTPUTS
    assert long_term_discomfort.BUILDING == ooc.BUILDING
    athb = {name[:-len('_Z')]: unit for name, unit in zip(comfort_hooks.zone_outputs('Z'),
                                                          comfort_hooks._OUTPUTS.values())}
    assert {output: ooc.ZONE_OUTPUTS[output][0] for output in athb} == \
        {output: f'{output} ({unit})' if unit else output for output, unit in athb.items()}
    # The hours of the setpoints of the ATHB at the limits of their range (task H4 of the review of 1.2.0), summed
    assert comfort_hooks.zone_outputs('Z')[-1] == f'{comfort_hooks.ATHB_SATURATED}_Z'
    assert comfort_hooks._SUMMED_OUTPUTS == {comfort_hooks.ATHB_SATURATED: 'H'}
    assert ooc.ZONE_OUTPUTS[comfort_hooks.ATHB_SATURATED] == ('ATHB_saturated (h)', False, True)
    # The SET of the zones of the hook of the SET by bisection (task G3 of the review of 1.2.0), in °C
    assert comfort_hooks.set_zone_outputs('Z') == ['SET_Z'] and comfort_hooks._SET_OUTPUTS == {'SET': 'C'}
    assert ooc.ZONE_OUTPUTS['SET'] == ('SET (°C)', True, True)
    # The causal TSV and the occupied hours within its band of comfort standard 24 (task F1 of block F)
    assert comfort_hooks.sun2026_zone_outputs('Z') == ['SET_Z', 'TSV_causal_Z', 'HoursInCausalBand_Z']
    assert comfort_hooks._SUN2026_OUTPUTS == {'TSV_causal': ''} and comfort_hooks._SUN2026_HOURS == 'HoursInCausalBand'
    assert ooc.ZONE_OUTPUTS['TSV_causal'] == ('TSV_causal', True, True)
    assert ooc.ZONE_OUTPUTS['HoursInCausalBand'] == ('HoursInCausalBand (h)', False, True)
    assert custom_regimes.OUTPUT_PREFIX == 'CustomRegime_' and 'CustomRegime' in ooc.ZONE_OUTPUTS
    assert outdoor_metric.OUTPUT_PREFIX == f'{ooc.OUTDOOR_METRIC}_'
    assert setpoint_limits.HOURS_BELOW_PREFIX == f'{ooc.HOURS_BELOW}_'
    assert [setpoint_limits.hours_below_variable(t, 'Z') for t in (18, 17.5, -2)] == \
        ['HoursBelow_18_Z', 'HoursBelow_17p5_Z', 'HoursBelow_m2_Z']
    # The outputs that are added up, and those that are averaged (see the docstring of the module)
    assert [output for output, (_, averaged, _) in ooc.ZONE_OUTPUTS.items() if not averaged] == LONG_TERM + [
        'ATHB_saturated', 'HoursInCausalBand', 'DriftLimitedHours']
    # The outputs of the limiter of the drift of the setpoints (task F2 of block F), with their units
    from accim.sim.ems import drift_limiter

    assert {output: ooc.ZONE_OUTPUTS[output][0] for output in drift_limiter.OUTPUTS} == {
        output: f"{output} ({'h' if units == 'H' else '°C'})" for output, (units, _) in drift_limiter.OUTPUTS.items()}
    assert [output for output, (_, kind) in drift_limiter.OUTPUTS.items() if kind == 'Summed'] == ['DriftLimitedHours']


@MODELS
def test_the_optional_outputs_are_named_after_their_zones(tmp_path, monkeypatch, model):
    columns, of_zone = _outputs(model)
    table = _table(tmp_path, monkeypatch, model, columns)

    assert table.occupied_zone_list == model['zone_names']
    for zone in model['zone_names']:
        for output, (_, _, name) in ZONE_OUTPUTS.items():
            if name:
                assert _values(table, f'{zone}_{name}') == columns[of_zone[zone, output]], (zone, output)
    for output, name in ooc.LONG_TERM_OUTPUTS.items():
        units = ZONE_OUTPUTS[output][0]
        assert _values(table, f'Building_{name}') == columns[f'EMS:{output}_Building [{units}](Hourly)']
    assert _values(table, 'Tout_metric (°C)') == [15.5, 16.5]
    # The outdoor metric of each zone keeps its EMS name, as the comfort temperature and the setpoints of the zones
    kept = [c for c in table.df.columns if c.startswith('EMS:')]
    assert len(kept) == len(model['zone_names']) and all(c.startswith('EMS:TOUT_METRIC_') for c in kept), kept
    assert not table.df.columns.duplicated().any()


@MODELS
def test_no_name_contains_another_one(tmp_path, monkeypatch, model):
    # The figures of Table take the columns whose names contain the names they are given
    columns, _ = _outputs(model)
    table = _table(tmp_path, monkeypatch, model, columns)
    names = [c for c in table.df.columns if c.startswith(tuple(f'{zone}_' for zone in model['zone_names']))
             or c.startswith(('Block', 'Building', model['block'])) or c == 'Tout_metric (°C)']
    for name in names:
        assert [other for other in table.df.columns if name.lower() in str(other).lower()] == [name], name


@MODELS
def test_the_optional_outputs_are_averaged_over_time_but_the_hours(tmp_path, monkeypatch, model):
    columns, of_zone = _outputs(model)
    table = _table(tmp_path, monkeypatch, model, columns, frequency='daily', frequency_agg_func='sum')

    assert len(table.df) == 1
    for zone in model['zone_names']:
        for output, (_, _, name) in ZONE_OUTPUTS.items():
            column = f'{zone}_{name}' if name else next(c for c in table.df.columns
                                                         if c.startswith(f'EMS:TOUT_METRIC_{zone.upper()}'))
            values = columns[of_zone[zone, output]]
            expected = sum(values) if output in SUMMED else sum(values) / 2
            assert _values(table, column) == [pytest.approx(expected)], (zone, output)
    for output, name in ooc.LONG_TERM_OUTPUTS.items():
        expected = sum(columns[f'EMS:{output}_Building [{ZONE_OUTPUTS[output][0]}](Hourly)'])
        assert _values(table, f'Building_{name}') == [pytest.approx(expected)]
    assert _values(table, 'Tout_metric (°C)') == [pytest.approx(16.0)]


@MODELS
def test_block_and_building_values(tmp_path, monkeypatch, model):
    columns, of_zone = _outputs(model)
    table = _table(tmp_path, monkeypatch, model, columns)
    zones, block = model['zone_names'], model['block']

    for output in WITH_LEVELS:
        name = ZONE_OUTPUTS[output][2]
        summed = [sum(hour) for hour in zip(*[columns[of_zone[zone, output]] for zone in zones])]
        for group in (block, 'Building'):
            assert _values(table, f'{group}_Total_{name} (summed)') == pytest.approx(summed), (group, output)
            assert _values(table, f'{group}_Total_{name} (mean)') == pytest.approx([v / 2 for v in summed])
    # The building values of the hours and degree hours are the sums of the EMS (those of all the zones)
    for name in ooc.LONG_TERM_OUTPUTS.values():
        assert _values(table, f'Building_Total_{name} (summed)') == _values(table, f'Building_{name}')
    # The regime and the outdoor metric of the zones have none
    assert not [c for c in table.df.columns if c.startswith(('Building_Total_', f'{block}_Total_'))
                and ('CustomRegime' in c or 'TOUT_METRIC' in c.upper())]

    # Without the excluded zones (the EMS building sums keep them)
    excluded = _table(tmp_path, monkeypatch, model, columns, level_excluded_zones=[zones[1]])
    assert _values(excluded, 'Building_Total_ATHB_PMV (mean)') == columns[of_zone[zones[0], 'ATHB_PMV']]
    assert _values(excluded, 'Building_Total_HoursBelow_18 (h) (summed)') == \
        columns[of_zone[zones[0], 'HoursBelow_18']]
    assert _values(excluded, 'Building_Hours Above Upper Limit (h)') == \
        _values(table, 'Building_Hours Above Upper Limit (h)')


def test_rename_cols_false_keeps_the_ems_names(tmp_path, monkeypatch):
    columns, of_zone = _outputs(DESIGNBUILDER)
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, rename_cols=False)

    assert _values(table, 'EMS:ATHB_PMV_BLOCK1:ZONE1 [](HOURLY)') == columns[of_zone['Block1:Zone1', 'ATHB_PMV']]
    assert _values(table, 'EMS:HOURSBELOW_17P5_BLOCK1:ZONE1 [H](HOURLY)') == \
        columns[of_zone['Block1:Zone1', 'HoursBelow_17p5']]
    assert 'EMS:TOUT_METRIC [C](HOURLY)' in table.df.columns
    assert not [c for c in table.df.columns if c.startswith(('Block1:Zone1_', 'Building_Hours', 'Tout_metric'))]
    # The block and building values have the names of Table, as those of the other outputs
    assert 'Building_Total_ATHB_PMV (mean)' in table.df.columns
    assert 'Building_Total_HoursBelow_17p5 (h) (summed)' in table.df.columns


def test_standard_outputs_keep_the_optional_outputs(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER)
    columns['ELECTRICITY:HVAC [J](Hourly)'] = [1.0, 2.0]
    standard = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, standard_outputs=True)
    everything = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, standard_outputs=False)

    assert set(everything.df.columns) - set(standard.df.columns) == {'ELECTRICITY:HVAC [J](HOURLY)'}


def test_comfort_hours_table_takes_the_optional_hours(tmp_path, monkeypatch):
    columns, _ = _outputs(DESIGNBUILDER)
    # The hours at the limits of the range of the setpoints of the ATHB (task H4) are not comfort hours
    hours = [output for output, (units, _, _) in ZONE_OUTPUTS.items() if units == 'H' and not output.startswith('ATHB')]
    for rename_cols in (True, False):
        table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, rename_cols=rename_cols)
        table.format_table(type_of_table='comfort hours')
        of_zones = [c for c in table.val_cols if 'ZONE' in c.upper()]
        # The hours below the 3 temperatures and above and below the limits of the 2 zones, and their block and
        # building values (summed and mean), and the EMS building values of the hours above and below the limits; not
        # the degree hours, nor the outputs of the ATHB
        assert len(of_zones) == 2 * len(hours), (rename_cols, of_zones)
        assert len(table.val_cols) == 2 * len(hours) + 2 * 2 * len(hours) + 2, (rename_cols, table.val_cols)
        assert not [c for c in table.val_cols if 'DEGREE' in c.upper() or 'ATHB' in c.upper()]


def test_time_plot_and_wrangled_table_of_the_optional_outputs(tmp_path, monkeypatch):
    columns, of_zone = _outputs(DESIGNBUILDER)
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': 'n')
    data = ['Block1:Zone1_ATHB_PMV', 'Block1:Zone1_ATHB_clo (clo)', 'Block1:Zone1_ATHB_met (met)']

    table.time_plot(vars_to_gather_rows=['Model'], vars_to_gather_cols=['EPW'],
                    data_on_y_main_axis=[['ATHB', data]], colorlist_y_main_axis=[['ATHB', ['k', 'b', 'r']]],
                    figname='time_plot_athb', figsize=2, dpi=50, confirm_graph=True)
    # One column for each name
    frames = table.y_list_main[0][0][0]['dataframe']
    assert [len(frame.columns) for frame in frames] == [1, 1, 1]
    assert (tmp_path / 'time_plot_athb.png').exists()

    # Two models (the second with twice the values of the first) in two cities, in a table of the run period
    datasets = []
    for scale, model in ((1.0, 'TestModel_a'), (2.0, 'TestModel_b')):
        for city in ('Seville', 'Madrid'):
            datasets.append(f'{model}[{city}.csv')
            _write_csv(tmp_path / datasets[-1], {c: [v * scale for v in values] for c, values in columns.items()})
    table = _table(tmp_path, monkeypatch, DESIGNBUILDER, columns, datasets=datasets, frequency='runperiod')
    values = ['Block1:Zone1_HoursBelow_18 (h)', 'Tout_metric (°C)', 'Building_Hours Above Upper Limit (h)']
    table.format_table(type_of_table='custom', custom_cols=values)
    assert table.val_cols == values
    table.wrangled_table(reshaping='unstack', vars_to_gather=['Model'], baseline='TestModel_a',
                         comparison_mode=['others compared to baseline'], comparison_cols=['absolute'])
    unstacked = table.wrangled_df_unstacked
    assert sorted(unstacked.index) == ['Madrid', 'Seville']
    hours = sum(columns[of_zone['Block1:Zone1', 'HoursBelow_18']])
    assert unstacked[(values[0], 'TestModel_b')].tolist() == [pytest.approx(2 * hours)] * 2
    assert unstacked[(values[1], 'TestModel_a')].tolist() == [pytest.approx(16.0)] * 2
    assert unstacked[(values[2], 'TestModel_a - TestModel_b')].tolist() == \
        [pytest.approx(-sum(columns['EMS:Hours Above Upper Limit_Building [H](Hourly)']))] * 2


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus():
    from accim.energyplus import find_energyplus

    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


@pytest.mark.skipif(_energyplus() is None,
                    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')
def test_the_optional_outputs_of_a_simulation(tmp_path, monkeypatch):
    pytest.importorskip('pythermalcomfort')
    from accim.data.postprocessing.main import Table
    from accim.run import run_ep
    from accim.sim import comfort_hooks
    from accim.sim.accis import AddAccis, load_idf
    from accim.sim.arguments import CustomRegime

    # The sample model with the custom model, its outdoor metric and two regimes, the hours below 18 and 17.5 °C, the
    # long-term discomfort and the setpoints of the ATHB, for 2 days of January. A model prepared for the hook of the
    # ATHB runs with the backend of the API and the hook: the EMS backend, with which this test ran it until finding A4
    # of the self-audit of 2026-11-11 (the outputs of the ATHB were 0), does not simulate it
    shutil.copy(SAMPLE_IDF, tmp_path / 'TestModel.idf')
    model = load_idf(tmp_path / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 1, 8
    run_period.End_Month, run_period.End_Day_of_Month = 1, 9
    model.save()
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[99], category=[1], comfort_mode=[3], confirm=True,
                 verbose=False, custom_slope=0.31, custom_intercept=17.8, custom_cooling_offset=3.5,
                 custom_heating_offset=-3.5, custom_cooling_lower_limit=10, custom_cooling_upper_limit=33.5,
                 custom_heating_lower_limit=10, custom_heating_upper_limit=33.5, custom_outdoor_metric='rmot_7day',
                 epw=str(EPW), custom_regimes=[CustomRegime(0.5, 12, 2, -2, 5, 40, 5, 40, ('metric_below', 12)),
                                               CustomRegime(0.33, 18.8, 2, -3, 10, 30, 10, 30)],
                 report_hours_below=[18, 17.5], report_long_term_discomfort=True)
    (tmp_path / 'TestModel.idf').unlink()
    [path] = tmp_path.glob('TestModel[[]*.idf')
    idf = load_idf(path)
    hook = comfort_hooks.apply_athb_setpoints(idf, output_frequencies=['hourly'])
    idf.save()
    shutil.copy(EPW, tmp_path / 'Seville.epw')
    with pytest.raises(ValueError, match='which the EMS backend cannot run'):
        run_ep(only_accim_idfs=True, confirm=True, processes=1, energyplus_version='25.1')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        [result] = run_ep(only_accim_idfs=True, confirm=True, processes=1, backend='api', hooks=[hook])
    assert result.success, result.error
    [csv] = [p for p in tmp_path.glob('TestModel[[]*.csv') if not p.stem.endswith(('Meter', 'Table', 'Zsz'))]
    results = pd.read_csv(csv)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        table = Table(datasets=[csv.name], source_frequency='hourly', frequency='daily', frequency_agg_func='sum',
                      standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'],
                      level_excluded_zones=[], idf_path=str(path))

    assert len(table.df) == 2
    days = results.index // 24
    for zone, suffix in (('Block1:Zone1', 'Block1_Zone1'), ('Block1:Zone2', 'Block1_Zone2')):
        for output, (_, _, name) in ZONE_OUTPUTS.items():
            if output == 'HoursBelow_m2':
                continue
            [column] = [c for c in results.columns if c.startswith(f'EMS:{output}_{suffix} [')]
            daily = results[column].groupby(days)
            expected = daily.sum() if output in SUMMED else daily.mean()
            renamed = f'{zone}_{name}' if name else next(c for c in table.df.columns
                                                         if c.startswith(f'EMS:TOUT_METRIC_{zone.upper()} ['))
            assert _values(table, renamed) == pytest.approx(expected.tolist()), (zone, output)
        # The hook ran: without it, the outputs of the ATHB are 0
        assert (table.df[f'{zone}_ATHB_PMV'] != 0).all()
    for name in ooc.LONG_TERM_OUTPUTS.values():
        assert _values(table, f'Building_{name}') == pytest.approx(_values(table, f'Building_Total_{name} (summed)'))
    [metric] = [c for c in results.columns if c.startswith('EMS:Tout_metric [')]
    assert _values(table, 'Tout_metric (°C)') == pytest.approx(results[metric].groupby(days).mean().tolist())
    assert table.df['Block1:Zone1_CustomRegime'].between(1, 2).all()
