"""The simulations of the validation study of block F (task F3 of accim 1.2.0): the cases of the proposal
(``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 4, F3) that accim runs from a model with the ACCIS, with the
choices decided on 2026-11-12 (``notes/decisions.md``; the position of the author, to be agreed with the authors of the
causal SET model before the simulations of the study)::

    PYTHONPATH=. python tools/indoor_adaptation_study.py OUT_DIR --epw Seville_Present.epw [--epw OTHER.epw]
        [--begin 1/1] [--end 12/31] [--cases ii_en16798,iii_seasonal] [--processes 4] [--list]
        [--heating-minimum 18] [--air-speed-heating 0.1] [--fan-hours 7 19]

It makes the model of each case in ``OUT_DIR`` (``<case>.idf``), simulates it with each weather file with the backend
of the Python API of EnergyPlus (``<case>[<weather file>.csv``), and writes ``indicators.csv``, a row for each
simulation: the energy of the coils and the electricity of the VRF system, the long-term discomfort that the EMS counts
with the seasonal range of the offices of category II of EN 16798-1 (``long_term_range=('en16798_seasonal', 2,
'office')``), and the indicators of the adaptation to the indoor climate, those of the causal band with the reference
SET (that of pythermalcomfort, with the inputs of the occupants of the People objects: ``pythermalcomfort_set=
'people'``) and with the Pierce SET of EnergyPlus. The cases:

- ``i_fixed``: the static reference (b), fixed setpoints of 20 and 26 °C (EN 16798-1:2019, Table B.2, category II), as
  the static setpoints of a comfort standard defined by its data, in comfort mode 0.
- ``ii_en16798`` and ``ii_ashrae55``: the adaptive setpoints of EN 16798-1 (category II) and of ASHRAE 55 (80 %), in
  comfort mode 3.
- ``iii_seasonal`` and ``iii_dynamic``: the causal SET model (comfort standard 24) with the clothing insulation fixed
  by season (1.0 and 0.5 clo, with the cooling season from day 121 to 274) and with the dynamic clothing model of
  ASHRAE 55 (a sensitivity), at 0.1 m/s.
- ``iv_v06``, ``iv_v09`` and ``iv_v12``: the causal SET model with the dynamic clothing model and fans of 0.6, 0.9 or
  1.2 m/s (the air speeds of EN 16798-1, Table B.4, with personal control) that the occupants control, in the cooling
  season: the air velocity schedule of the People objects has the air speed of the fans in all the hours of the
  cooling season (0.1 m/s the rest of the year), with which the hook inverts the cooling setpoint, and it inverts the
  heating setpoint with still air (``air_speed_heating=0.1`` of ``apply_sun2026_setpoints``; ``--air-speed-heating``),
  since the occupants have the fans only when they need them. The reference SET of their indicators is that of such
  occupants too: without the fans while it is not above the upper limit of the causal band, and with them above it.
- ``v_<case>_r025``, ``_r05`` and ``_r10``: ``ii_en16798``, ``ii_ashrae55``, ``iii_dynamic`` (which is also case (iv)
  at 0.1 m/s) and the three cases (iv) with the limiter of the drift of the setpoints, ``drift_mode='rate'``, at 0.25,
  0.5 and 1.0 K/day.

The static reference (a) of the study, the PMV setpoints of category II (``accim.sim.apmv.apply_pmv_setpoints``), is
not a case of this script: its models have no outputs of the ACCIS, which the indicators of ``Table`` need. A year
of a case of the causal SET model takes hours (its hook inverts the SET by bisection in each timestep): try the
script with a week (``--begin 7/15 --end 7/21``). It needs EnergyPlus 24.2 or later and pythermalcomfort.

Two choices of cases (iv) and (v) were decided on 2026-11-13 (``notes/decisions.md``; the question of 2026-11-12,
after a winter and a summer week of the sample model). With one air speed for both limits of the causal band (the
hook as decided on 2026-11-10: ``--air-speed-heating -1``), the fans raise the heating setpoint as well as the cooling
one, and the heating coils work in their hours; so the heating setpoint of the cases with fans is that of still air.
And the limiter of the drift keeps the setpoints of every timestep within its rate of the mean of those of the
occupied timesteps of the day before, so an air speed of the fans in the occupied hours only (``--fan-hours 7 19``,
as first decided) makes it hold the cooling setpoint of the occupied hours all day, which is not a drift between
days; so the air speed of the fans is that of all the hours of the cooling season, and the limiter stays as it is.
With the setpoints of a hook, which follow the mean radiant temperature, the humidity and the clothing within the
day, the limiter still acts within the day: section 4.2.7 of the detailed use. The sample model (``--idf`` by default)
is a test model, for trying the script and not for the study: its VRF system does not hold the cooling setpoints in a
summer week.
"""
import argparse
import os
import shutil
import sys
import warnings
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
#: The seasonal range of the long-term discomfort of all the cases: the offices of category II
LONG_TERM_RANGE = ('en16798_seasonal', 2, 'office')
#: The comfort standard defined by its data of the fixed setpoints of 20 and 26 °C (the comfort temperature and the
#: band are those of EN 16798-1, which comfort mode 0 does not use)
FIXED_SETPOINTS = {
    'number': 120, 'label': 'EN16798 II fixed', 'title': '120 = EN 16798-1, category II, fixed setpoints',
    'citation': 'EN 16798-1:2019, Table B.2, category II (offices): 20 and 26 degC',
    'outdoor_metric': 'rmot', 'comfort_temperature': {'slope': 0.33, 'intercept': 18.8},
    'applicability': {'metric_min': 10.0, 'metric_max': 30.0},
    'categories': {2: {'cooling_offset': 3.0, 'heating_offset': -4.0, 'description': 'Category II'}},
    'comfort_modes': [0], 'static_setpoints': {'heating': 20.0, 'cooling': 26.0},
    'evidence': {'source': 'EN 16798-1:2019, Table B.2 (design values, category II)'},
}
#: The energy outputs of the indicators: output of EnergyPlus -> column
ENERGY = {'Heating Coil Heating Energy': 'Heating coils (kWh)',
          'Cooling Coil Total Cooling Energy': 'Cooling coils (kWh)',
          'VRF Heat Pump Heating Electricity Energy': 'VRF heating electricity (kWh)',
          'VRF Heat Pump Cooling Electricity Energy': 'VRF cooling electricity (kWh)'}
#: The cooling season of the clothing insulation and of the air speeds: from 1 May (day 121) to 30 September
COOLING_SEASON = ('4/30', '9/30')


def cases():
    """The cases: id -> (description, comfort standard, category, comfort mode, options)."""
    found = {
        'i_fixed': ('fixed setpoints of 20 and 26 degC', FIXED_SETPOINTS['number'], 2, 0, {}),
        'ii_en16798': ('EN 16798-1, category II', 1, 2, 3, {}),
        'ii_ashrae55': ('ASHRAE 55, 80 %', 2, 80, 3, {}),
        'iii_seasonal': ('causal SET model, 1.0 and 0.5 clo by season', 1, 2, 3, {'set': True, 'clothing': 'seasonal'}),
        'iii_dynamic': ('causal SET model, dynamic clothing model', 1, 2, 3, {'set': True, 'clothing': 'dynamic'}),
    }
    for speed in (0.6, 0.9, 1.2):
        found[f'iv_v{str(speed).replace(".", "")}'] = (
            f'causal SET model, dynamic clothing model, {speed} m/s in the cooling season', 1, 2, 3,
            {'set': True, 'clothing': 'dynamic', 'air_speed': speed})
    # Case (v): (ii) and (iv) with the limiter; iii_dynamic is also case (iv) at 0.1 m/s
    for base in ('ii_en16798', 'ii_ashrae55', 'iii_dynamic', 'iv_v06', 'iv_v09', 'iv_v12'):
        description, standard, category, mode, options = found[base]
        for rate in (0.25, 0.5, 1.0):
            found[f'v_{base}_r{str(rate).replace(".", "")}'] = (
                f'{description}, drift limited to {rate} K/day', standard, category, mode, dict(options, rate=rate))
    return found


def _compact_schedule(model, name, heating_season, cooling_season, hours=None):
    """Add a Schedule:Compact with a value in the cooling season (within some hours of the weekdays, if given) and
    another one the rest of the year."""
    fields = [f'Through: {COOLING_SEASON[0]}', 'For: AllDays', 'Until: 24:00', heating_season,
              f'Through: {COOLING_SEASON[1]}']
    if hours is None:
        fields += ['For: AllDays', 'Until: 24:00', cooling_season]
    else:
        fields += ['For: Weekdays', f'Until: {hours[0]:02d}:00', heating_season, f'Until: {hours[1]:02d}:00',
                   cooling_season, 'Until: 24:00', heating_season, 'For: AllOtherDays', 'Until: 24:00', heating_season]
    fields += ['Through: 12/31', 'For: AllDays', 'Until: 24:00', heating_season]
    model.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name='',
                       **{f'Field_{n}': value for n, value in enumerate(fields, start=1)})


def fans(spec, air_speed_heating):
    """The air speed of the heating setpoint of a case (m/s): ``air_speed_heating`` in the cases with fans, None in
    the others (and in all of them with ``--air-speed-heating -1``)."""
    return air_speed_heating if spec[4].get('air_speed') is not None else None


def build(case, spec, out, model_file, begin, end, heating_minimum, fan_hours, air_speed_heating):
    """Make the model of a case in ``out`` (``<case>.idf``); return its path and its hook (None without it)."""
    from accim.sim.accis import AddAccis, load_idf, modify_accis
    from accim.sim.comfort_hooks import apply_sun2026_setpoints
    from accim.sim.people import add_thermal_comfort_outputs, set_clothing_method
    from accim.utils.people import get_people_objects

    _, standard, category, mode, options = spec
    folder = out / '_models' / case
    folder.mkdir(parents=True)
    shutil.copy(model_file, folder / 'F3.idf')
    model = load_idf(folder / 'F3.idf')
    for run_period in model.idfobjects['RunPeriod']:
        run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
        run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    here = os.getcwd()
    os.chdir(folder)
    try:
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type='temperature', comfort_standard=[standard], category=[category], comfort_mode=[mode],
                 confirm=True, verbose=False, report_long_term_discomfort=True, long_term_range=LONG_TERM_RANGE)
    finally:
        os.chdir(here)
    [path] = folder.glob('F3[[]*.idf')
    model = load_idf(path)
    hook = None
    if options.get('clothing') == 'seasonal':
        _compact_schedule(model, 'F3 Clothing', 1.0, 0.5)
        set_clothing_method(model, 'ClothingInsulationSchedule', schedule='F3 Clothing', verbose=False)
    elif options.get('clothing') == 'dynamic':
        set_clothing_method(model, 'DynamicClothingModelASHRAE55', verbose=False)
    if options.get('air_speed') is not None:
        _compact_schedule(model, 'F3 Air Velocity', 0.1, options['air_speed'], hours=fan_hours)
        for people in get_people_objects(model):
            people.Air_Velocity_Schedule_Name = 'F3 Air Velocity'
    if options.get('rate') is not None:
        modify_accis(model, drift_mode='rate', max_drift_rate=options['rate'])
    if options.get('set'):
        if heating_minimum is not None:
            modify_accis(model, heating_setpoint_minimum=heating_minimum)
        # The fans are those that the occupants control: the heating setpoint is that of still air
        hook = apply_sun2026_setpoints(model, comfort_mode='SET band', category=80, tr_mode='zone',
                                       output_frequencies=['hourly'],
                                       air_speed_heating=fans(spec, air_speed_heating))
    # The outputs of the indicators: the Fanger and Pierce models, the inputs of the occupants of the reference SET,
    # and the energy
    add_thermal_comfort_outputs(model, ['Fanger', 'Pierce'], output_frequencies=['hourly'], occupant_inputs=True)
    for name in ENERGY:
        model.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name, Reporting_Frequency='Hourly')
    model.saveas(str(out / f'{case}.idf'))
    return out / f'{case}.idf', hook


def indicators(out, case, description, csv, air_speed_heating=None):
    """The indicators of a simulation (see the module), from its CSV file in ``out``, the current folder; with
    ``air_speed_heating``, the reference SET is that of the occupants who control their fans."""
    from accim.data.postprocessing import indoor_adaptation as ia
    from accim.data.postprocessing.main import Table

    results = pd.read_csv(csv)
    row = {'Case': case, 'Description': description, 'EPW': csv.stem.rsplit('[', 1)[1]}
    for output, title in ENERGY.items():
        columns = [c for c in results.columns if f':{output} [J]' in c]
        row[title] = results[columns].sum().sum() / 3.6e6
    # The long-term discomfort that the EMS counts, with the seasonal range of EN 16798-1 (hours and degree hours)
    for output in ('Hours Above Upper Limit', 'Hours Below Lower Limit', 'Degree Hours Above Upper Limit',
                   'Degree Hours Below Lower Limit'):
        columns = [c for c in results.columns if c.upper().startswith(f'EMS:{output}_Building ['.upper())]
        row[f'{output} (seasonal range)'] = results[columns[0]].sum() if columns else float('nan')
    table = Table(datasets=[csv.name], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
                  standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'], level_excluded_zones=[],
                  idf_path=f'{case}.idf', long_term_indicators=True)
    set_inputs = 'people' if air_speed_heating is None else {
        'met': 'people', 'clo': 'people', 'air_speed': 'people', 'air_speed_heating': air_speed_heating}
    found = ia.table_indicators(table.df, table.occupied_zone_list, pythermalcomfort_set=set_inputs).iloc[0]
    setpoints = table.long_term_indicators.iloc[0]
    row['Occupied hours (h)'] = found['Building_Occupied Hours (h)']
    row['Hours outside its own setpoints (h)'] = (setpoints['Building_Hours Above Upper Limit (h)']
                                                  + setpoints['Building_Hours Below Lower Limit (h)'])
    for title in ('Mean SET_pythermalcomfort (°C)', 'Hours In Causal Band_pythermalcomfort (%)', 'Mean SET_Pierce (°C)',
                  'Hours In Causal Band (%)', 'Overcooling Hours (h)', 'Drift Limited Hours (h)'):
        row[title] = found[f'Building_{title}']
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('out', type=Path)
    parser.add_argument('--epw', action='append', type=Path, help='a weather file (several times for several)')
    parser.add_argument('--idf', type=Path, default=SAMPLE_IDF, help='the model (the sample model of accim by default)')
    parser.add_argument('--begin', default='1/1', help='the first day of the run period (month/day)')
    parser.add_argument('--end', default='12/31', help='its last day (month/day)')
    parser.add_argument('--cases', default='all', help='the cases, separated by commas (all by default)')
    parser.add_argument('--processes', type=int, default=4, help='the simulations that run at the same time')
    parser.add_argument('--heating-minimum', type=float, default=18.0,
                        help='the minimum heating setpoint of the cases of the causal SET model (degC; none: -1)')
    parser.add_argument('--air-speed-heating', type=float, default=0.1,
                        help='the air speed of the heating setpoint of the cases with fans (m/s; that of the fans: -1)')
    parser.add_argument('--fan-hours', type=int, nargs=2, default=None,
                        help='the hours of the weekdays with the air speed of the fans (all the hours by default)')
    parser.add_argument('--list', action='store_true', help='list the cases and stop')
    arguments = parser.parse_args()
    all_cases = cases()
    if arguments.list:
        for case, (description, *_) in all_cases.items():
            print(f'{case}: {description}')
        return 0
    chosen = list(all_cases) if arguments.cases == 'all' else [name.strip() for name in arguments.cases.split(',')]
    unknown = [name for name in chosen if name not in all_cases]
    if unknown or not arguments.epw:
        parser.error(f'unknown cases {unknown}' if unknown else 'give a weather file (--epw)')

    from accim.sim.energyplus_api import run_simulations
    from accim.sim.standards import definition_from_mapping, register_comfort_standard

    register_comfort_standard(definition_from_mapping(FIXED_SETPOINTS), replace=True)
    out = arguments.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    begin, end = (tuple(int(part) for part in value.split('/')) for value in (arguments.begin, arguments.end))
    minimum = None if arguments.heating_minimum < 0 else arguments.heating_minimum
    heating_speed = None if arguments.air_speed_heating < 0 else arguments.air_speed_heating
    fan_hours = None if arguments.fan_hours is None else tuple(arguments.fan_hours)
    jobs, names = [], []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for case in chosen:
            model, hook = build(case, all_cases[case], out, arguments.idf, begin, end, minimum, fan_hours,
                                heating_speed)
            for epw in arguments.epw:
                prefix = f'{model.stem}[{epw.stem}'
                options = {'output_directory': str(out), 'output_prefix': prefix}
                if hook is not None:
                    options['before_programs'] = [hook]
                jobs.append((str(model), str(epw.resolve()), options))
                names.append((case, prefix))
        print(f'{len(jobs)} simulations ({len(chosen)} cases, {len(arguments.epw)} weather files)...')
        results = run_simulations(jobs, processes=arguments.processes)
        failed = [(prefix, result.error) for (_, prefix), result in zip(names, results) if not result.success]
        for prefix, error in failed:
            print(f'FAILED {prefix}: {error}')
        os.chdir(out)
        rows = [indicators(out, case, all_cases[case][0], out / f'{prefix}.csv', fans(all_cases[case], heating_speed))
                for (case, prefix), result in zip(names, results) if result.success]
    frame = pd.DataFrame(rows)
    frame.to_csv(out / 'indicators.csv', index=False)
    with pd.option_context('display.width', 250, 'display.max_columns', 30, 'display.float_format', '{:.1f}'.format):
        print(frame.drop(columns=['Description']).to_string(index=False))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
