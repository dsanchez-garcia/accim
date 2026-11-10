"""Task E-F1 of the review of accim 1.2.0 (``notes/PROPUESTA_ADAPTACION_INTERIOR_v03.md``, section 3): the standard
effective temperature (SET) of the Pierce two-node model of EnergyPlus against that of pythermalcomfort
(``pythermalcomfort.models.set_tmp``, which the hook of the SET of :mod:`accim.sim.comfort_hooks` uses), from the same
outputs.

:func:`accim.sim.people.add_thermal_comfort_model` adds the model Pierce to the People objects. The last test simulates
the sample model with the ACCIS (INT EN16798, category II, comfort mode 3, full air-conditioning) and Pierce for a year
in Seville with EnergyPlus 25.1 (6 timesteps per hour), and compares, hour by hour, the output ``Zone Thermal Comfort
Pierce Model Standard Effective Temperature`` of each People object with the SET of pythermalcomfort 4.8.1 of the mean
air temperature, mean radiant temperature and relative humidity of its zone and of the activity level (W/person, divided
by 58.2 W/m² and 1.8 m²), clothing insulation and air velocity schedules of the People object, in each timestep. The
differences measured are in ``notes/decisions.md`` (E-F1, 2026-11-10); the test reproduces them, so it fails if
EnergyPlus, pythermalcomfort or the model change them.
"""
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim.people import PIERCE_SET_OUTPUT, THERMAL_COMFORT_MODELS, add_thermal_comfort_model

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
#: The hourly differences measured on 2026-11-10 (SET of pythermalcomfort minus SET of EnergyPlus, K): the mean, the
#: mean of the absolute values and the maximum absolute value, of all the hours of the year
MEASURED = {
    ('Block1:Zone1', 'standing'): (-0.045, 0.056, 0.180), ('Block1:Zone2', 'standing'): (-0.045, 0.056, 0.196),
    ('Block1:Zone1', 'sitting'): (-0.116, 0.118, 0.324), ('Block1:Zone2', 'sitting'): (-0.116, 0.117, 0.344),
}


def _accis_model(folder, monkeypatch, setpoint_type='temperature'):
    """The output IDF of AddAccis of the sample model (INT EN16798, category II, comfort mode 3, full
    air-conditioning, outputs at timestep frequency)."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(script_type='vrf_ac', supply_air_temp_input_method='temperature difference', output_type='standard',
                 output_frequencies=['timestep'], keep_existing_outputs=False, energyplus_version='auto',
                 setpoint_type=setpoint_type, comfort_standard=[1], category=[2], comfort_mode=[3], confirm=True,
                 verbose=False)
    [path] = folder.glob('TestModel[[]*.idf')
    return load_idf(path)


def _models(people):
    return [str(getattr(people, f'Thermal_Comfort_Model_{n}_Type')).strip() for n in range(1, 8)]


@needs_idd
def test_add_thermal_comfort_model(tmp_path, monkeypatch):
    idf = _accis_model(tmp_path / 'temperature', monkeypatch)
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
    with pytest.raises(ValueError, match=r"comfort_model must be one of \['Fanger', 'Pierce', 'KSU'\], not "
                                         r"'AdaptiveASH55'"):
        add_thermal_comfort_model(idf, 'AdaptiveASH55')
    assert THERMAL_COMFORT_MODELS == ('Fanger', 'Pierce', 'KSU')
    # Without an empty field, nothing changes
    people = idf.idfobjects['People'][0]
    for n in range(5, 8):
        setattr(people, f'Thermal_Comfort_Model_{n}_Type', 'CoolingEffectASH55')
    before = [_models(p) for p in idf.idfobjects['People']]
    with pytest.raises(ValueError, match='has no empty field for the thermal comfort model'):
        add_thermal_comfort_model(idf, 'Fanger')
    assert [_models(p) for p in idf.idfobjects['People']] == before
    # With the PMV-based setpoints, after Fanger
    pmv = _accis_model(tmp_path / 'pmv', monkeypatch, setpoint_type='pmv')
    add_thermal_comfort_model(pmv, 'Pierce')
    for people in pmv.idfobjects['People']:
        assert _models(people)[:4] == ['AdaptiveASH55', 'AdaptiveCEN15251', 'Fanger', 'Pierce']


def _energyplus():
    folder = find_energyplus('25.1', required=False)
    return folder if folder is not None and SAMPLE_IDF.exists() and EPW.exists() else None


@pytest.mark.skipif(_energyplus() is None, reason='needs EnergyPlus 25.1 and the sample files of the repository')
def test_the_set_of_energyplus_and_of_pythermalcomfort(tmp_path, monkeypatch, capsys):
    set_tmp = pytest.importorskip('pythermalcomfort.models').set_tmp
    idf = _accis_model(tmp_path, monkeypatch)
    add_thermal_comfort_model(idf, 'Pierce')
    # Only the outputs of the comparison
    for output in list(idf.idfobjects['Output:Variable']):
        idf.removeidfobject(output)
    for name in (PIERCE_SET_OUTPUT, 'Zone Mean Air Temperature', 'Zone Mean Radiant Temperature',
                 'Zone Air Relative Humidity', 'Zone Thermal Comfort Mean Radiant Temperature'):
        idf.newidfobject('Output:Variable', Key_Value='*', Variable_Name=name, Reporting_Frequency='Timestep')
    for schedule in [AIR_VELOCITY, 'Work efficiency'] + [name for _, *names in PEOPLE.values() for name in names]:
        idf.newidfobject('Output:Variable', Key_Value=schedule, Variable_Name='Schedule Value',
                         Reporting_Frequency='Timestep')
    idf.saveas(str(tmp_path / 'model.idf'))
    result = subprocess.run([str(_energyplus() / 'energyplus.exe'), '-d', str(tmp_path / 'out'), '-p', 'run', '-s',
                             'C', '-r', '-x', '-w', str(EPW), str(tmp_path / 'model.idf')],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    results = pd.read_csv(tmp_path / 'out' / 'run.csv')
    assert len(results) == 8760 * STEPS

    def column(key, name):
        [found] = [c for c in results.columns if c.upper().startswith(f'{key}:{name}'.upper())]
        return results[found].to_numpy(dtype=float)

    air_velocity = column(AIR_VELOCITY, 'Schedule Value')
    assert (column('Work efficiency', 'Schedule Value') == 0).all()
    for zone, (people, activity, clothing) in PEOPLE.items():
        energyplus = column(people, PIERCE_SET_OUTPUT)
        # The mean radiant temperature of the comfort models of the People object (EnclosureAveraged) is that of the
        # zone
        np.testing.assert_allclose(column(people, 'Zone Thermal Comfort Mean Radiant Temperature'),
                                   column(zone, 'Zone Mean Radiant Temperature'), rtol=0, atol=1e-9)
        met = column(activity, 'Schedule Value') / (58.2 * 1.8)
        inputs = dict(tdb=column(zone, 'Zone Mean Air Temperature'), tr=column(zone, 'Zone Mean Radiant Temperature'),
                      v=air_velocity, rh=column(zone, 'Zone Air Relative Humidity'), met=met,
                      clo=column(clothing, 'Schedule Value'))
        for position in ('standing', 'sitting'):
            python = set_tmp(**inputs, position=position, limit_inputs=False, round_output=False).set
            hourly = (pd.Series(python - energyplus).groupby(np.arange(len(python)) // STEPS).mean())
            measured = (hourly.mean(), hourly.abs().mean(), hourly.abs().max())
            print(f'{zone} {position}: mean {measured[0]:+.4f} K, mean absolute {measured[1]:.4f} K, maximum '
                  f'absolute {measured[2]:.4f} K')
            np.testing.assert_allclose(measured, MEASURED[(zone, position)], rtol=0, atol=0.001)
    assert 'Block1:Zone2 sitting' in capsys.readouterr().out
