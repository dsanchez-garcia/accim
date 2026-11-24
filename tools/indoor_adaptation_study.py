"""The simulations of the validation study of block F (task F3 of accim 1.2.0): the cases of the proposal
(``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 4, F3) that accim runs from a model with the ACCIS, with the
choices decided on 2026-11-12 (``notes/decisions.md``; the position of the author, to be agreed with the authors of the
causal SET model before the simulations of the study)::

    PYTHONPATH=. python tools/indoor_adaptation_study.py OUT_DIR --epw Seville_Present.epw [--epw OTHER.epw]
        [--begin 1/1] [--end 12/31] [--cases study|all|ii_en16798,iii_model] [--processes 4] [--list]
        [--script-type vrf_mm] [--hvac-mode 2] [--ventilation-control 2] [--ventilation-setpoint-offset 0]
        [--min-outdoor-temp-offset 50] [--max-wind-speed 50]
        [--heating-minimum 18] [--air-speed-heating 0.1] [--fan-hours 7 19]

It makes the model of each case in ``OUT_DIR`` (``<case>.idf``), simulates it with each weather file with the backend
of the Python API of EnergyPlus (``<case>[<weather file>.csv``), and writes ``indicators.csv``, a row for each
simulation: the energy of the coils, the electricity of the VRF system and that of the whole HVAC system, the hours in
which the zones ventilate through their windows (in mixed mode), the PMV of the occupied hours and their percentage
within -0.5 and 0.5 (with the reference PMV, that of pythermalcomfort as the hook of ``i_pmv`` calculates it, and with
that of the Fanger model of EnergyPlus), the long-term discomfort that the EMS counts
with the seasonal range of the offices of category II of EN 16798-1 (``long_term_range=('en16798_seasonal', 2,
'office')``), and the indicators of the adaptation to the indoor climate, those of the causal band with the reference
SET (that of pythermalcomfort, with the inputs of the occupants of the People objects: ``pythermalcomfort_set=
'people'``) and with the Pierce SET of EnergyPlus. The cases:

- ``i_pmv``: the static reference (a), the setpoints of the PMV of Fanger of -0.5 and 0.5 (category II of EN 16798-1)
  as setpoints of the operative temperature, which a hook inverts in each timestep with the clothing insulation, the
  activity level and the air speed of the People objects of the model, as the causal SET model
  (``accim.sim.comfort_hooks.apply_pmv_hook_setpoints``; since 2026-11-24, below).
- ``i_fixed``: the static reference (b), fixed setpoints of 20 and 26 °C (EN 16798-1:2019, Table B.2, category II), as
  the static setpoints of a comfort standard defined by its data, in comfort mode 0; its comfort temperature is their
  midpoint, 23 °C, which is the ventilation setpoint of mixed mode with the ventilation controls 0 and 2.
- ``ii_en16798`` and ``ii_ashrae55``: the adaptive setpoints of EN 16798-1 (category II) and of ASHRAE 55 (80 %), in
  comfort mode 3.
- ``iii_model``: the causal SET model (comfort standard 24, the band of 19.1 to 28.2 °C of SET all the year) with the
  clothing insulation, the activity level and the air speed of the People objects of the model, as the other cases,
  without fans and without a minimum heating setpoint (the case of the study since 2026-11-19, below).
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

The PMV setpoints of the Fanger thermostats of EnergyPlus (``accim.sim.apmv.apply_pmv_setpoints``) are not a case of
this script: their models have no outputs of the ACCIS, which the indicators of ``Table`` need, and accim does not
control their windows; they stay as the alternative to ``i_pmv`` (the decision of the author of 2026-11-24). A year
of a case with a hook (``i_pmv`` and those of the causal SET model) takes long, since the hook inverts its index by
bisection in each timestep: try the script with a week (``--begin 7/15 --end 7/21``). It needs EnergyPlus 24.2 or
later and pythermalcomfort.

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
is a test model, for trying the script and not for the study: its windows keep the venting control of the model, which
opens them above 24 °C, also in full air-conditioning (in a week of July, they are open in 74 to 105 of the 168 hours
of each zone, and with the setpoints of EN 16798-1 the heating coils work in 14 hours of each zone, all of them with
the windows open). Its VRF systems hold the cooling setpoints in a summer week since they are sized with the windows
closed on the design days (2026-11-19).

Since 2026-11-19 (the decisions of the author of that day, ``notes/decisions.md``), the cases of the causal SET model
have no minimum heating setpoint by default: the causal band is applied as published (``--heating-minimum 18`` gives
them that of 18 °C). And the validation study is narrowed to what the paper of the model specifies: it leaves aside
the limiter of the drift (case (v)), the fans (case (iv)) and the clothing insulation that cases ``iii_seasonal`` and
``iii_dynamic`` give the model, and has one case of the causal SET model, ``iii_model``, with the clothing, the
activity and the air speed of the model itself. ``--cases study`` (the default) runs the cases of the study,
``i_fixed``, ``ii_en16798``, ``ii_ashrae55`` and ``iii_model`` (:data:`STUDY_CASES`; ``--list`` marks them), and
``--cases all`` still runs all the cases, the others as sensitivities.

Since 2026-11-24 (the decisions of the author of that day, ``notes/decisions.md``), the study has five cases, ``i_pmv``,
``i_fixed``, ``ii_en16798``, ``ii_ashrae55`` and ``iii_model``, and runs in mixed mode: the script adds the ACCIS with
``--script-type vrf_mm`` (the VRF systems of accim and the control of the windows of the model), ``--hvac-mode 2`` and
``--ventilation-control 2`` by default (the windows open, with the customised opening factor, while the zone is
occupied, its HVAC system neither heats nor cools, and its operative temperature is above the ventilation setpoint and
below the cooling setpoint, with the other conditions of the EMS programs of mixed mode, section 4.1 of the detailed
use). The ventilation setpoint is the comfort temperature of the adaptive setpoints of case (ii), and the midpoint of
the setpoints in the cases without a comfort temperature of their own: 23 °C in ``i_fixed`` (the comfort temperature of
its comfort standard) and that of the setpoints of the hook in ``i_pmv`` and ``iii_model``
(``accim.sim.ems.hook_setpoints``). ``--hvac-mode 0`` keeps the windows closed (full air-conditioning), and
``--script-type vrf_ac`` gives the models of before, in which the windows keep the control of the model. With
``--script-type ex_mm`` or ``ex_ac``, the ACCIS controls the HVAC systems of the model (for the models with their own
systems, such as the prototypes of the DOE), and the occupied zones whose names have not the pattern ``block:zone`` of
DesignBuilder are given to ``Table`` as those of one block, 'Building' (the indicators of such tables work since
2026-11-24: tried with two days of July of the small office of the DOE, ``RefBldgSmallOfficeNew2004_Chicago.idf``, and
``ex_ac``). The models simulate the run period from ``--begin`` to ``--end`` of each weather file and not their sizing
periods, whatever their SimulationControl object says (:func:`simulate_run_periods`): the example files of EnergyPlus
simulate their design days only, and the results of that office were those of its two design days.
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
#: The comfort standard defined by its data of the fixed setpoints of 20 and 26 °C. Comfort mode 0 does not use its
#: comfort temperature and its band, which are the midpoint of the setpoints, 23 °C, and ±3 K since 2026-11-24 (those
#: of EN 16798-1 before): in mixed mode, with the ventilation controls 0 and 2, the ventilation setpoint is the comfort
#: temperature, and that of fixed setpoints is their midpoint, as SetVST takes it for comfort standard 0
FIXED_SETPOINTS = {
    'number': 120, 'label': 'EN16798 II fixed', 'title': '120 = EN 16798-1, category II, fixed setpoints',
    'citation': 'EN 16798-1:2019, Table B.2, category II (offices): 20 and 26 degC',
    'outdoor_metric': 'rmot', 'comfort_temperature': {'slope': 0.0, 'intercept': 23.0},
    'applicability': {'metric_min': 10.0, 'metric_max': 30.0},
    'categories': {2: {'cooling_offset': 3.0, 'heating_offset': -3.0, 'description': 'Category II'}},
    'comfort_modes': [0], 'static_setpoints': {'heating': 20.0, 'cooling': 26.0},
    'evidence': {'source': 'EN 16798-1:2019, Table B.2 (design values, category II)'},
}
#: The energy outputs of the indicators: output of EnergyPlus -> column
ENERGY = {'Heating Coil Heating Energy': 'Heating coils (kWh)',
          'Cooling Coil Total Cooling Energy': 'Cooling coils (kWh)',
          'VRF Heat Pump Heating Electricity Energy': 'VRF heating electricity (kWh)',
          'VRF Heat Pump Cooling Electricity Energy': 'VRF cooling electricity (kWh)'}
#: The script types of AddAccis: the VRF systems of accim or the HVAC systems of the model, in mixed mode (accim
#: controls the windows) or with full air-conditioning
SCRIPT_TYPES = ('vrf_mm', 'vrf_ac', 'ex_mm', 'ex_ac')
#: The limits of the PMV of the indicator of the PMV of Fanger: category II of EN 16798-1 (and B of ISO 7730)
PMV_LIMIT = 0.5
#: The cooling season of the clothing insulation and of the air speeds: from 1 May (day 121) to 30 September
COOLING_SEASON = ('4/30', '9/30')
#: The cases of the study since the decisions of the author of 2026-11-24 (``--cases study``, the default): the
#: static references (a) and (b), the adaptive setpoints of case (ii) and the causal SET model with the inputs of the
#: model (four of them, without ``i_pmv``, since 2026-11-19); the other cases stay for sensitivities (``--cases all``)
STUDY_CASES = ('i_pmv', 'i_fixed', 'ii_en16798', 'ii_ashrae55', 'iii_model')


def cases():
    """The cases: id -> (description, comfort standard, category, comfort mode, options)."""
    found = {
        # The PMV setpoints of category II as temperature setpoints, with the inputs of the occupants of the model
        'i_pmv': ('PMV setpoints of -0.5 and 0.5, the clothing, activity and air speed of the model', 1, 2, 3,
                  {'pmv': True}),
        'i_fixed': ('fixed setpoints of 20 and 26 degC', FIXED_SETPOINTS['number'], 2, 0, {}),
        'ii_en16798': ('EN 16798-1, category II', 1, 2, 3, {}),
        'ii_ashrae55': ('ASHRAE 55, 80 %', 2, 80, 3, {}),
        # The case of the causal SET model of the study since 2026-11-19: the inputs of the occupants of the model
        'iii_model': ('causal SET model, the clothing, activity and air speed of the model', 1, 2, 3, {'set': True}),
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


def accis_arguments(script_type, hvac_mode, ventilation_control, ventilation_setpoint_offset=0,
                    min_outdoor_temp_offset=50, max_wind_speed=50):
    """The arguments of AddAccis of a script type: the supply air temperature of the VRF systems of accim, and, in
    mixed mode, the HVAC mode, the ventilation control, the offset of the ventilation setpoint, that of the minimum
    outdoor temperature for ventilation (below the heating setpoint) and the maximum wind speed (those of AddAccis by
    default: no offset, and no limits that matter)."""
    arguments = {'script_type': script_type}
    if script_type.startswith('vrf'):
        arguments['supply_air_temp_input_method'] = 'temperature difference'
    if script_type.endswith('mm'):
        arguments.update(hvac_mode=[hvac_mode], ventilation_control=[ventilation_control],
                         ventilation_setpoint_offset=[ventilation_setpoint_offset],
                         min_outdoor_temp_offset=[min_outdoor_temp_offset], max_wind_speed=[max_wind_speed])
    return arguments


def simulate_run_periods(model):
    """Make a model simulate the run periods of the weather file and not its sizing periods, whose rows would be among
    those of the results (or the only ones: the example files of EnergyPlus, such as the prototypes of the DOE,
    simulate their design days only); its sizing calculations stay. A model that does so already does not change, and
    one without a SimulationControl object, which would simulate both, gets it. Return True if the model changed."""
    wanted = {'Run_Simulation_for_Sizing_Periods': 'No', 'Run_Simulation_for_Weather_File_Run_Periods': 'Yes'}
    controls = model.idfobjects['SimulationControl']
    if not controls:
        model.newidfobject('SimulationControl', **wanted)
        return True
    changed = False
    for control in controls:
        for field, value in wanted.items():
            if str(getattr(control, field)).strip().upper() != value.upper():
                setattr(control, field, value)
                changed = True
    return changed


def build(case, spec, out, model_file, begin, end, heating_minimum, fan_hours, air_speed_heating,
          accis=None):
    """Make the model of a case in ``out`` (``<case>.idf``); return its path and its hook (None without it)."""
    from accim.sim.accis import AddAccis, load_idf, modify_accis
    from accim.sim.comfort_hooks import apply_pmv_hook_setpoints, apply_sun2026_setpoints
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
    simulate_run_periods(model)
    model.save()
    here = os.getcwd()
    os.chdir(folder)
    try:
        AddAccis(output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                 energyplus_version='auto', setpoint_type='temperature', comfort_standard=[standard],
                 category=[category], comfort_mode=[mode], confirm=True, verbose=False,
                 report_long_term_discomfort=True, long_term_range=LONG_TERM_RANGE,
                 **(accis_arguments('vrf_mm', 2, 2) if accis is None else accis))
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
    elif options.get('pmv'):
        # The PMV setpoints of category II, inverted with the inputs of the People objects and the mean radiant
        # temperature of each zone, as those of the causal SET model
        hook = apply_pmv_hook_setpoints(model, pmv_cooling_setpoint=PMV_LIMIT, pmv_heating_setpoint=-PMV_LIMIT,
                                        tr_mode='zone', output_frequencies=['hourly'])
    # The outputs of the indicators: the Fanger and Pierce models, the inputs of the occupants of the reference SET,
    # and the energy
    add_thermal_comfort_outputs(model, ['Fanger', 'Pierce'], output_frequencies=['hourly'], occupant_inputs=True)
    for name in ENERGY:
        model.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name, Reporting_Frequency='Hourly')
    model.saveas(str(out / f'{case}.idf'))
    return out / f'{case}.idf', hook


def _column(results, start):
    """The first column of the results whose name begins with some text (whatever its case), or None."""
    names = [name for name in results.columns if str(name).upper().startswith(start.upper())]
    return results[names[0]] if names else None


def pmv_indicators(results, model):
    """The PMV in the occupied hours of the zones of a simulation (those of the output Occupied Hours_<zone> of the
    ACCIS), with the inputs of the People objects: its mean and the percentage of those hours within -0.5 and 0.5
    (:data:`PMV_LIMIT`). With the reference PMV, that of pythermalcomfort of the outputs of each row, as the hook of
    ``i_pmv`` calculates it (``accim.sim.comfort_hooks.set_of_results`` with a hook of the PMV), and with that of the
    Fanger model of EnergyPlus (the output Zone Thermal Comfort Fanger Model PMV of the occupants of each zone), as the
    indicators of the causal band have the reference SET and that of the Pierce model; NaN without their outputs."""
    from accim.sim.comfort_hooks import PmvSetpointHook, people_inputs, set_of_results

    people = people_inputs(model)
    hook = PmvSetpointHook(list(people), pmv_cooling_setpoint=PMV_LIMIT, pmv_heating_setpoint=-PMV_LIMIT)
    reference = set_of_results(results, hook, people=people)
    totals = {source: [0.0, 0.0, 0.0] for source in ('pythermalcomfort', 'Fanger')}
    for zone, values in people.items():
        occupied = _column(results, f'EMS:Occupied Hours_{zone} [')
        if occupied is None:
            continue
        columns = {'pythermalcomfort': reference[f'HookPMV_{zone}'],
                   'Fanger': _column(results, f"{values['occupants']}:Zone Thermal Comfort Fanger Model PMV [")}
        for source, pmv in columns.items():
            if pmv is None:
                continue
            hours = occupied[pmv.notna()]
            totals[source][0] += hours.sum()
            totals[source][1] += (pmv * occupied).sum()
            totals[source][2] += hours[pmv.abs() <= PMV_LIMIT].sum()
    found = {}
    for source, (hours, weighted, within) in totals.items():
        found[f'Mean PMV_{source}'] = weighted / hours if hours else float('nan')
        found[f'Hours In PMV Band_{source} (%)'] = 100 * within / hours if hours else float('nan')
    return found


def block_zone_hierarchy(zones):
    """The blocks of the occupied zones of a model whose names have not the pattern block:zone of DesignBuilder, for
    ``Table`` (which asks for them otherwise): one block, 'Building', with those zones; None if all the names have
    it."""
    others = [str(zone) for zone in zones if len(str(zone).split(':')) != 2]
    return {'Building': others} if others else None


def indicators(out, case, description, csv, air_speed_heating=None):
    """The indicators of a simulation (see the module), from its CSV file in ``out``, the current folder; with
    ``air_speed_heating``, the reference SET is that of the occupants who control their fans."""
    from accim.data.postprocessing import indoor_adaptation as ia
    from accim.data.postprocessing.main import Table
    from accim.sim.accis import load_idf
    from accim.sim.comfort_hooks import people_inputs

    results = pd.read_csv(csv)
    model = load_idf(f'{case}.idf')
    # The occupied zones of the model, by their names in the outputs
    occupied_zones = [values['key'] for values in people_inputs(model).values()]
    row = {'Case': case, 'Description': description, 'EPW': csv.stem.rsplit('[', 1)[1]}
    for output, title in ENERGY.items():
        columns = [c for c in results.columns if f':{output} [J]' in c]
        row[title] = results[columns].sum().sum() / 3.6e6 if columns else float('nan')
    # The electricity of the whole HVAC system (W in each hour), whatever its equipment
    demand = _column(results, 'Whole Building:Facility Total HVAC Electricity Demand Rate [W](Hourly)')
    row['HVAC electricity (kWh)'] = float('nan') if demand is None else demand.sum() / 1000
    # The hours in which the zones ventilate through their windows, which the ACCIS counts in mixed mode
    columns = [c for c in results.columns if c.upper().startswith('EMS:VENTILATION HOURS_')]
    row['Ventilation hours (h)'] = results[columns].sum().sum() if columns else float('nan')
    row.update(pmv_indicators(results, model))
    # The long-term discomfort that the EMS counts, with the seasonal range of EN 16798-1 (hours and degree hours)
    for output in ('Hours Above Upper Limit', 'Hours Below Lower Limit', 'Degree Hours Above Upper Limit',
                   'Degree Hours Below Lower Limit'):
        columns = [c for c in results.columns if c.upper().startswith(f'EMS:{output}_Building ['.upper())]
        row[f'{output} (seasonal range)'] = results[columns[0]].sum() if columns else float('nan')
    table = Table(datasets=[csv.name], source_frequency='hourly', frequency='hourly', frequency_agg_func='sum',
                  standard_outputs=True, level=['building'], level_agg_func=['sum', 'mean'], level_excluded_zones=[],
                  idf_path=f'{case}.idf', long_term_indicators=True,
                  block_zone_hierarchy=block_zone_hierarchy(occupied_zones))
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
    parser.add_argument('--cases', default='study',
                        help="the cases, separated by commas, or 'study' (those of the study, the default) or 'all'")
    parser.add_argument('--processes', type=int, default=4, help='the simulations that run at the same time')
    parser.add_argument('--script-type', default='vrf_mm', choices=SCRIPT_TYPES,
                        help='the script type of AddAccis: the VRF systems of accim (vrf) or the HVAC systems of the '
                             'model (ex), in mixed mode (mm, the default: vrf_mm) or with full air-conditioning (ac)')
    parser.add_argument('--hvac-mode', type=int, default=2, choices=(0, 2),
                        help='with the script types of mixed mode: 2, mixed mode (the default), or 0, full '
                             'air-conditioning with the windows closed')
    parser.add_argument('--ventilation-control', type=int, default=2, choices=(0, 1, 2, 3),
                        help='in mixed mode, the ventilation control of AddAccis (2 by default: above the comfort '
                             'temperature, with the customised opening factor)')
    parser.add_argument('--ventilation-setpoint-offset', type=float, default=0,
                        help='in mixed mode, the offset of the ventilation setpoint (K; 0 by default)')
    parser.add_argument('--min-outdoor-temp-offset', type=float, default=50,
                        help='in mixed mode, the windows open with the outdoor temperature above the heating setpoint '
                             'minus this offset (K; 50 by default, as AddAccis: no limit that matters)')
    parser.add_argument('--max-wind-speed', type=float, default=50,
                        help='in mixed mode, the windows open with the wind speed up to this one (m/s; 50 by default, '
                             'as AddAccis: no limit that matters)')
    parser.add_argument('--heating-minimum', type=float, default=None,
                        help='a minimum heating setpoint of the cases of the causal SET model (degC; none by default)')
    parser.add_argument('--air-speed-heating', type=float, default=0.1,
                        help='the air speed of the heating setpoint of the cases with fans (m/s; that of the fans: -1)')
    parser.add_argument('--fan-hours', type=int, nargs=2, default=None,
                        help='the hours of the weekdays with the air speed of the fans (all the hours by default)')
    parser.add_argument('--list', action='store_true', help='list the cases and stop')
    arguments = parser.parse_args()
    all_cases = cases()
    if arguments.list:
        for case, (description, *_) in all_cases.items():
            print(f'{case}: {description}' + (' (study)' if case in STUDY_CASES else ''))
        return 0
    groups = {'all': list(all_cases), 'study': list(STUDY_CASES)}
    chosen = groups.get(arguments.cases, [name.strip() for name in arguments.cases.split(',')])
    unknown = [name for name in chosen if name not in all_cases]
    if unknown or not arguments.epw:
        parser.error(f'unknown cases {unknown}' if unknown else 'give a weather file (--epw)')

    from accim.sim.energyplus_api import run_simulations
    from accim.sim.standards import definition_from_mapping, register_comfort_standard

    register_comfort_standard(definition_from_mapping(FIXED_SETPOINTS), replace=True)
    out = arguments.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    begin, end = (tuple(int(part) for part in value.split('/')) for value in (arguments.begin, arguments.end))
    # No minimum heating setpoint by default (the decision of the author of 2026-11-19); -1 is still none
    minimum = (None if arguments.heating_minimum is None or arguments.heating_minimum < 0
               else arguments.heating_minimum)
    heating_speed = None if arguments.air_speed_heating < 0 else arguments.air_speed_heating
    fan_hours = None if arguments.fan_hours is None else tuple(arguments.fan_hours)
    accis = accis_arguments(arguments.script_type, arguments.hvac_mode, arguments.ventilation_control,
                            arguments.ventilation_setpoint_offset, arguments.min_outdoor_temp_offset,
                            arguments.max_wind_speed)
    jobs, names = [], []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for case in chosen:
            model, hook = build(case, all_cases[case], out, arguments.idf, begin, end, minimum, fan_hours,
                                heating_speed, accis)
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
