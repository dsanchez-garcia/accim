"""Task E-F1 of the review of accim 1.2.0 (``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 3): the standard
effective temperature (SET) of the Pierce two-node model of EnergyPlus against that of pythermalcomfort
(``pythermalcomfort.models.set_tmp``, which the hook of the SET of :mod:`accim.sim.comfort_hooks` uses), from the same
outputs, measured again on 2026-11-12 by activity level (findings A1 and A2 of the self-audit of 2026-11-11, decided on
2026-11-12, ``notes/decisions.md``) and on 2026-11-19, with the windows of the sample model closed on its design days
(:mod:`accim.sim.ems.design_days`).

:func:`accim.sim.people.add_thermal_comfort_model` adds the model Pierce to the People objects. The tests of the SET
simulate the sample model with the ACCIS (INT EN16798, category II, comfort mode 3, full air-conditioning) and Pierce
for a year in Seville with EnergyPlus 25.1 (6 timesteps per hour), with three activity levels of the occupants (110.7
W/person, that of the sample model, 115 and 126 W/person: about 1.05, 1.1 and 1.2 met), and compare, hour by hour, the
output ``Zone Thermal Comfort Pierce Model Standard Effective Temperature`` of each People object with the SET of
pythermalcomfort 4.8.1 of the mean air temperature, mean radiant temperature and relative humidity of its zone and of
the activity level, clothing insulation (1.0 clo until 1 April and from 1 October, 0.5 clo between them) and air
velocity (0.137 m/s) schedules of the People object, in each timestep:

- with the metabolic rate of the hooks of accim, the activity level divided by 58.2 W/m² and 1.8 m² (the body surface
  area with which the Input Output Reference of EnergyPlus gives the activity per person), and with that of the Pierce
  model of EnergyPlus, which divides it by 1.8258 m² (``BodySurfAreaPierce`` of ``ThermalComfort.cc`` of EnergyPlus
  25.1; its Fanger and KSU models take 1.8 m²): the same inputs for both models (finding A1);
- standing (the posture of EnergyPlus, and the default of ``set_tmp``, with which the SET of the ASHRAE Global Thermal
  Comfort Database II was calculated) and sitting (that of the hooks of accim with 1.2 met or less);
- and with the two-node model of pythermalcomfort without the term of the activity, 5.66·(met − 0.85)^0.39, in the
  convective coefficient of the real environment, as the Pierce model of EnergyPlus 25.1 has it (only in that of the
  standard environment): the difference between both models then does not depend on the activity level (finding A2).

The differences measured on 2026-11-10 and 2026-11-12 are in ``notes/decisions.md`` (E-F1): they were those of the
VRF systems of the sample model about 100 times too big, which EnergyPlus sized with its windows open on its winter
design day (their venting setpoint is 0 °C on that day) and whose fans kept the zones warm in winter. The tests
reproduce those measured again on 2026-11-19, with the windows closed on the design days, so they fail if EnergyPlus,
pythermalcomfort or the model change them.
"""
import importlib
import os
import shutil
import subprocess
import types
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.people import PIERCE_SET_OUTPUT, THERMAL_COMFORT_MODELS, add_thermal_comfort_model

from ._optional import pythermalcomfort_models

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
#: The People object, activity level schedule and clothing insulation schedule of each zone of the sample model
PEOPLE = {'Block1:Zone1': ('People Block1:Zone1', 'Activity Schedule 26', 'Clothing Schedule 26'),
          'Block1:Zone2': ('People Block1:Zone2', 'Activity Schedule 19', 'Clothing Schedule 19')}
AIR_VELOCITY = 'Default Air Velocity for Comfort Calculations'
STEPS = 6
#: The activity level of the occupants of the sample model (W/person), and those of about 1.1 and 1.2 met
SAMPLE_ACTIVITY = 110.7
ACTIVITIES = (SAMPLE_ACTIVITY, 115.0, 126.0)
#: The body surface area (m²) with which the activity level is converted to met: that of the hooks of accim (and of the
#: Fanger and KSU models of EnergyPlus), and that of the Pierce model of EnergyPlus 25.1
BODY_SURFACE_AREAS = {'accim': 1.8, 'pierce': 1.8258}
#: The hourly differences (SET of pythermalcomfort minus SET of EnergyPlus, K): the mean, the mean of the absolute
#: values and the maximum absolute value, of all the hours of the year, by activity level (W/person), zone, body surface
#: area of the metabolic rate and posture, measured again on 2026-11-19 with the windows of the sample model closed on
#: its design days (:mod:`accim.sim.ems.design_days`). Those of 2026-11-10 (110.7 W/person with 1.8 m², task E-F1) and
#: 2026-11-12 (``notes/decisions.md``), with its VRF systems about 100 times too big (sized with its windows open on its
#: winter design day, their fans kept the zones warm in winter), were (-0.0454, 0.0565, 0.1805) for the first one, and
#: means of -0.3248 and -0.9431 K for those of 115 and 126 W/person
MEASURED = {
    (110.7, 'Block1:Zone1', 'accim', 'standing'): (-0.0315, 0.0533, 0.1705),
    (110.7, 'Block1:Zone1', 'accim', 'sitting'): (-0.0947, 0.1020, 0.3079),
    (110.7, 'Block1:Zone1', 'pierce', 'standing'): (-0.0506, 0.0508, 0.1251),
    (110.7, 'Block1:Zone1', 'pierce', 'sitting'): (-0.1126, 0.1126, 0.2612),
    (110.7, 'Block1:Zone2', 'accim', 'standing'): (-0.0315, 0.0528, 0.1853),
    (110.7, 'Block1:Zone2', 'accim', 'sitting'): (-0.0945, 0.1013, 0.3306),
    (110.7, 'Block1:Zone2', 'pierce', 'standing'): (-0.0506, 0.0508, 0.1382),
    (110.7, 'Block1:Zone2', 'pierce', 'sitting'): (-0.1124, 0.1124, 0.2799),
    (115.0, 'Block1:Zone1', 'accim', 'standing'): (-0.3116, 0.3116, 0.5882),
    (115.0, 'Block1:Zone1', 'accim', 'sitting'): (-0.3774, 0.3774, 0.7098),
    (115.0, 'Block1:Zone1', 'pierce', 'standing'): (-0.3242, 0.3242, 0.5327),
    (115.0, 'Block1:Zone1', 'pierce', 'sitting'): (-0.3890, 0.3890, 0.6524),
    (115.0, 'Block1:Zone2', 'accim', 'standing'): (-0.3115, 0.3115, 0.6244),
    (115.0, 'Block1:Zone2', 'accim', 'sitting'): (-0.3772, 0.3772, 0.7605),
    (115.0, 'Block1:Zone2', 'pierce', 'standing'): (-0.3242, 0.3242, 0.5600),
    (115.0, 'Block1:Zone2', 'pierce', 'sitting'): (-0.3889, 0.3889, 0.6962),
    (126.0, 'Block1:Zone1', 'accim', 'standing'): (-0.9368, 0.9368, 1.4792),
    (126.0, 'Block1:Zone1', 'accim', 'sitting'): (-1.0083, 1.0083, 1.5972),
    (126.0, 'Block1:Zone1', 'pierce', 'standing'): (-0.9651, 0.9651, 1.4599),
    (126.0, 'Block1:Zone1', 'pierce', 'sitting'): (-1.0357, 1.0357, 1.5779),
    (126.0, 'Block1:Zone2', 'accim', 'standing'): (-0.9366, 0.9366, 1.5317),
    (126.0, 'Block1:Zone2', 'accim', 'sitting'): (-1.0079, 1.0079, 1.6664),
    (126.0, 'Block1:Zone2', 'pierce', 'standing'): (-0.9649, 0.9649, 1.5034),
    (126.0, 'Block1:Zone2', 'pierce', 'sitting'): (-1.0354, 1.0354, 1.6382),
}
#: The same differences (the metabolic rate of the Pierce model, standing) without the term of the activity in the
#: convective coefficient of the real environment of the two-node model of pythermalcomfort, by activity level and zone
#: (measured again on 2026-11-19, as :data:`MEASURED`; the means were -0.0583, -0.0561 and -0.0514 K in Block1:Zone1
#: until then)
MEASURED_WITHOUT_THE_ACTIVITY_TERM = {
    (110.7, 'Block1:Zone1'): (-0.0506, 0.0508, 0.1251), (110.7, 'Block1:Zone2'): (-0.0506, 0.0508, 0.1382),
    (115.0, 'Block1:Zone1'): (-0.0481, 0.0485, 0.1222), (115.0, 'Block1:Zone2'): (-0.0482, 0.0485, 0.1351),
    (126.0, 'Block1:Zone1'): (-0.0431, 0.0440, 0.1153), (126.0, 'Block1:Zone2'): (-0.0431, 0.0440, 0.1278),
}
#: The condition of the term of the activity of the convective coefficients of pythermalcomfort 4.8.1
#: (``two_nodes_gagge.py``): the first one is that of the real environment, the second one that of the standard one
ACTIVITY_TERM = 'if not calculate_ce and met > 0.85:'


def _accis_model(folder, setpoint_type='temperature'):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full
    air-conditioning, outputs at timestep frequency)."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    here = os.getcwd()
    os.chdir(folder)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['timestep'], keep_existing_outputs=False,
                     energyplus_version='auto', setpoint_type=setpoint_type, comfort_standard=[1], category=[2],
                     comfort_mode=[3], confirm=True, verbose=False)
    finally:
        os.chdir(here)
    [path] = folder.glob('TestModel[[]*.idf')
    return load_idf(path)


def _models(people):
    return [str(getattr(people, f'Thermal_Comfort_Model_{n}_Type')).strip() for n in range(1, 8)]


@needs_idd
def test_add_thermal_comfort_model(tmp_path):
    idf = _accis_model(tmp_path / 'temperature')
    for people in idf.idfobjects['People']:
        assert _models(people)[:3] == ['AdaptiveASH55', 'AdaptiveCEN15251', '']
    add_thermal_comfort_model(idf, 'pierce')
    # In the first empty field, keeping the models of the ACCIS; once
    for people in idf.idfobjects['People']:
        assert _models(people)[:4] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Pierce', '']
    add_thermal_comfort_model(idf, 'Pierce')
    add_thermal_comfort_model(idf, 'KSU')
    for people in idf.idfobjects['People']:
        assert _models(people)[:5] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Pierce', 'KSU', '']
    with pytest.raises(ValueError, match=r"comfort_model must be one of \['Fanger', 'Pierce', 'KSU', "
                                         r"'CoolingEffectASH55'\], not 'AdaptiveASH55'"):
        add_thermal_comfort_model(idf, 'AdaptiveASH55')
    # CoolingEffectASH55 since task F3 of block F (in the IDDs that have it, as that of EnergyPlus 25.1)
    assert THERMAL_COMFORT_MODELS == ('Fanger', 'Pierce', 'KSU', 'CoolingEffectASH55')
    # Without an empty field, nothing changes
    people = idf.idfobjects['People'][0]
    for n in range(5, 8):
        setattr(people, f'Thermal_Comfort_Model_{n}_Type', 'CoolingEffectASH55')
    before = [_models(p) for p in idf.idfobjects['People']]
    with pytest.raises(ValueError, match='has no empty field for the thermal comfort model'):
        add_thermal_comfort_model(idf, 'Fanger')
    assert [_models(p) for p in idf.idfobjects['People']] == before
    # With the PMV-based setpoints, after Fanger
    pmv = _accis_model(tmp_path / 'pmv', setpoint_type='pmv')
    add_thermal_comfort_model(pmv, 'Pierce')
    for people in pmv.idfobjects['People']:
        assert _models(people)[:4] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Fanger', 'Pierce']


def _energyplus():
    folder = find_energyplus('25.1', required=False)
    return folder if folder is not None and SAMPLE_IDF.exists() and EPW.exists() else None


def _model_with_activity(folder, activity):
    """The model of the comparison (the ACCIS and Pierce, only the outputs of the comparison) with an activity level of
    the occupants (W/person), saved in its folder."""
    idf = _accis_model(folder)
    add_thermal_comfort_model(idf, 'Pierce')
    schedules = {schedule for _, schedule, _ in PEOPLE.values()}
    changed = 0
    for schedule in idf.idfobjects['Schedule:Compact']:
        if schedule.Name in schedules:
            values = schedule.fieldvalues
            # The activity level of the sample model, constant all the year
            [index] = [n for n, value in enumerate(values) if str(value).strip() == str(SAMPLE_ACTIVITY)]
            values[index] = activity
            changed += 1
    assert changed == len(schedules)
    for output in list(idf.idfobjects['Output:Variable']):
        idf.removeidfobject(output)
    for name in (PIERCE_SET_OUTPUT, 'Zone Mean Air Temperature', 'Zone Mean Radiant Temperature',
                 'Zone Air Relative Humidity', 'Zone Thermal Comfort Mean Radiant Temperature'):
        idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name, Reporting_Frequency='Timestep')
    for schedule in [AIR_VELOCITY, 'Work efficiency'] + [name for _, *names in PEOPLE.values() for name in names]:
        idf.newidfobject('Output:Variable', Key_Value=schedule, Variable_Name='Schedule Value',
                         Reporting_Frequency='Timestep')
    idf.saveas(str(folder / 'model.idf'))
    return folder / 'model.idf'


def _simulate(model):
    """Run EnergyPlus in the folder of the model (ExpandObjects and ReadVarsESO write files with fixed names in the
    working folder, so each simulation has its own), and return its process and the path of its CSV file."""
    out = model.parent / 'out'
    result = subprocess.run([str(_energyplus() / 'energyplus.exe'), '-d', str(out), '-p', 'run', '-s', 'C', '-r', '-x',
                             '-w', str(EPW), str(model)], capture_output=True, text=True, cwd=str(model.parent))
    return result, out / 'run.csv'


class _Results:
    """The outputs of a simulation of the comparison, by key and name."""

    def __init__(self, csv, activity):
        self.frame = pd.read_csv(csv)
        self.activity = activity
        assert len(self.frame) == 8760 * STEPS

    def column(self, key, name):
        [found] = [c for c in self.frame.columns if c.upper().startswith(f'{key}:{name}'.upper())]
        return self.frame[found].to_numpy(dtype=float)

    def inputs(self, zone, body_surface_area):
        """The inputs of the SET of pythermalcomfort of a zone, with the metabolic rate of a body surface area."""
        _, activity, clothing = PEOPLE[zone]
        found = self.column(activity, 'Schedule Value')
        assert np.allclose(found, self.activity)
        return dict(tdb=self.column(zone, 'Zone Mean Air Temperature'),
                    tr=self.column(zone, 'Zone Mean Radiant Temperature'),
                    v=self.column(AIR_VELOCITY, 'Schedule Value'),
                    rh=self.column(zone, 'Zone Air Relative Humidity'), met=found / (58.2 * body_surface_area),
                    clo=self.column(clothing, 'Schedule Value'))

    def measured(self, zone, python):
        """The mean, the mean of the absolute values and the maximum absolute value of the hourly differences between
        a SET of each timestep and that of EnergyPlus of the People object of a zone."""
        energyplus = self.column(PEOPLE[zone][0], PIERCE_SET_OUTPUT)
        hourly = pd.Series(python - energyplus).groupby(np.arange(len(python)) // STEPS).mean()
        return hourly.mean(), hourly.abs().mean(), hourly.abs().max()


@pytest.fixture(scope='module')
def simulations(tmp_path_factory):
    """The results of a year of the sample model with each activity level of :data:`ACTIVITIES`: the three simulations
    run at the same time, once for all the tests."""
    if _energyplus() is None:
        pytest.skip('needs EnergyPlus 25.1 and the sample files of the repository')
    pythermalcomfort_models()
    folder = tmp_path_factory.mktemp('pierce_set')
    models = {activity: _model_with_activity(folder / f'activity_{activity:g}', activity) for activity in ACTIVITIES}
    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        runs = dict(zip(models, pool.map(_simulate, models.values())))
    results = {}
    for activity, (process, csv) in runs.items():
        assert process.returncode == 0, process.stdout[-3000:]
        results[activity] = _Results(csv, activity)
    return results


@pytest.mark.parametrize('activity', ACTIVITIES)
def test_the_set_of_energyplus_and_of_pythermalcomfort(simulations, capsys, activity):
    from pythermalcomfort.models import set_tmp

    results = simulations[activity]
    assert (results.column('Work efficiency', 'Schedule Value') == 0).all()
    for zone, (people, _, _) in PEOPLE.items():
        # The mean radiant temperature of the comfort models of the People object (EnclosureAveraged) is that of the
        # zone
        np.testing.assert_allclose(results.column(people, 'Zone Thermal Comfort Mean Radiant Temperature'),
                                   results.column(zone, 'Zone Mean Radiant Temperature'), rtol=0, atol=1e-9)
        for label, area in BODY_SURFACE_AREAS.items():
            inputs = results.inputs(zone, area)
            for position in ('standing', 'sitting'):
                python = set_tmp(**inputs, position=position, limit_inputs=False, round_output=False).set
                measured = results.measured(zone, python)
                print(f'{activity:g} W/person ({inputs["met"].mean():.3f} met with {area} m2), {zone} {position}: '
                      f'mean {measured[0]:+.4f} K, mean absolute {measured[1]:.4f} K, maximum absolute '
                      f'{measured[2]:.4f} K')
                np.testing.assert_allclose(measured, MEASURED[(activity, zone, label, position)], rtol=0, atol=0.001)
    assert f'{activity:g} W/person' in capsys.readouterr().out


def test_the_difference_grows_with_the_activity_level():
    # Near 1 met (the 1.04 to 1.06 met of the sample model), both models agree within 0.06 K standing; at 1.1 and 1.2
    # met, pythermalcomfort is 0.31 to 0.32 K and 0.94 to 0.97 K lower on average (finding A2 of the self-audit of
    # 2026-11-11). The ranges, 0.02, 0.02 and 0.03 K wide, are those of each body surface area of the metabolic rate
    # since the measurement of 2026-11-19 (see MEASURED), in which the conversion of the activity level changes the mean
    # difference by up to 0.028 K: no range of those widths with limits on the 0.01 K grid of these ranges holds both
    # (-0.031 and -0.051 K at 110.7 W/person, -0.937 and -0.965 K at 126 W/person). Until then, one range of each
    # activity level held both: those of the metabolic rate of the Pierce model, which still hold them
    ranges = {'accim': ((-0.04, -0.02), (-0.32, -0.30), (-0.95, -0.92)),
              'pierce': ((-0.06, -0.04), (-0.34, -0.32), (-0.97, -0.94))}
    for zone in PEOPLE:
        for label in BODY_SURFACE_AREAS:
            means = [MEASURED[(activity, zone, label, 'standing')][0] for activity in ACTIVITIES]
            for mean, (low, high) in zip(means, ranges[label]):
                assert low < mean < high
        # The body surface area of the conversion of the activity level (1.8 m² in accim, 1.8258 m² in the Pierce model
        # of EnergyPlus: finding A1) changes the mean difference by 0.01 to 0.03 K (0.012 to 0.028 K, measured again on
        # 2026-11-19; 0.006 to 0.023 K, from 0 to 0.025 K, until then)
        for activity in ACTIVITIES:
            for position in ('standing', 'sitting'):
                accim, pierce = (MEASURED[(activity, zone, label, position)][0] for label in BODY_SURFACE_AREAS)
                assert 0.01 < accim - pierce < 0.03


def _two_nodes_without_the_activity_term():
    """The two-node model of pythermalcomfort from a copy of its source in which the term of the activity of the
    convective coefficient of the real environment is left out (the first condition of :data:`ACTIVITY_TERM` never
    holds), as in the Pierce model of EnergyPlus 25.1, which only has that term in the convective coefficient of the
    standard environment; nothing else changes. The test is skipped with another source (another version of
    pythermalcomfort)."""
    # The module (pythermalcomfort.models names its function two_nodes_gagge too)
    original = importlib.import_module('pythermalcomfort.models.two_nodes_gagge')
    source = Path(original.__file__).read_text(encoding='utf-8')
    first = source.find(ACTIVITY_TERM)
    if source.count(ACTIVITY_TERM) != 2 or 'standard environment' in source[:first]:
        pytest.skip('the source of the two-node model of pythermalcomfort is not that of pythermalcomfort 4.8.1')
    # Without the cache of numba, which needs the file of the functions
    modified = (source[:first] + 'if False:' + source[first + len(ACTIVITY_TERM):]).replace('cache=True', 'cache=False')
    module = types.ModuleType('two_nodes_gagge_without_the_activity_term')
    exec(compile(modified, 'two_nodes_gagge_without_the_activity_term.py', 'exec'), module.__dict__)
    return module.two_nodes_gagge


def test_the_term_of_the_activity_of_the_convective_coefficient_is_the_difference(simulations, capsys):
    # Finding A2 of the self-audit of 2026-11-11: with the same inputs (the metabolic rate of the Pierce model,
    # standing), the SET of pythermalcomfort without that term in the real environment is 0.043 to 0.051 K below that
    # of EnergyPlus at the three activity levels, within a range of 0.01 K, instead of 0.05, 0.32 and 0.97 K (measured
    # again on 2026-11-19, see MEASURED; 0.051 to 0.058 K, from -0.06 to -0.05 K, instead of 0.06, 0.33 and 0.97 K,
    # until then)
    two_nodes = _two_nodes_without_the_activity_term()
    means = {}
    for activity in ACTIVITIES:
        results = simulations[activity]
        for zone in PEOPLE:
            inputs = results.inputs(zone, BODY_SURFACE_AREAS['pierce'])
            python = two_nodes(**inputs, wme=0.0, body_surface_area=1.8258, p_atm=101325, position='standing',
                               round_output=False).set
            measured = results.measured(zone, python)
            print(f'{activity:g} W/person, {zone}, without the term: mean {measured[0]:+.4f} K, mean absolute '
                  f'{measured[1]:.4f} K, maximum absolute {measured[2]:.4f} K')
            np.testing.assert_allclose(measured, MEASURED_WITHOUT_THE_ACTIVITY_TERM[(activity, zone)], rtol=0,
                                       atol=0.001)
            means[(activity, zone)] = measured[0]
    assert all(-0.052 < mean < -0.042 for mean in means.values())
    assert 'without the term' in capsys.readouterr().out
