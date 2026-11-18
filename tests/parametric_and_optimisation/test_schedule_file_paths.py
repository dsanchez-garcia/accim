"""The parametric module and ``accim.utils.identify_variable_key_pattern`` with a model whose Schedule:File objects have
paths relative to its folder (:func:`accim.sim.schedule_files.relative_schedule_files`, since accim 1.2.0): besos
simulates copies of the models in other folders, where EnergyPlus would not find the files, so the models get the
absolute paths of the files (the parametric module, when it gets them)."""
import os
import shutil
import warnings
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip('besos')

from accim.energyplus import find_energyplus  # noqa: E402
from accim.sim import schedule_files as sf  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
METERS = ['Heating:Electricity', 'Cooling:Electricity']
needs_energyplus = pytest.mark.skipif(
    find_energyplus('25.1', required=False) is None or not (SAMPLE_IDF.exists() and EPW.exists()),
    reason='needs EnergyPlus 25.1 and the sample files of the repository')


def _moved_model(tmp_path):
    """The sample model with the ACCIS of the custom model, whose outdoor metric 'te_ref_nl' reads T0 from the
    Schedule:File object of the weather file (its CSV file in the folder of the model), simulated on 1 and 2 January,
    with the path of the CSV file relative to its folder, moved with that file to another folder."""
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis

    (tmp_path / 'A').mkdir()
    shutil.copy(SAMPLE_IDF, tmp_path / 'A' / 'model.idf')
    building = load_idf(tmp_path / 'A' / 'model.idf')
    run_period = building.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 1, 1
    run_period.End_Month, run_period.End_Day_of_Month = 1, 2
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
        modify_accis(building, comfort_standard=99, category=80, comfort_mode=3, custom_outdoor_metric='te_ref_nl',
                     epw=str(EPW))
    [(name, relative)] = sf.relative_schedule_files(building).items()
    assert name == 'ACCIS Outdoor Mid Range' and '/' not in relative and relative.endswith('.csv')
    building.save()
    shutil.copytree(tmp_path / 'A', tmp_path / 'B')
    shutil.rmtree(tmp_path / 'A')
    return tmp_path / 'B' / 'model.idf', relative


def _simulate(path, out_dir):
    """A parametric simulation of the model of ``path`` (one sample), and the model as the module has it."""
    from accim.parametric_and_optimisation.main import ParametricSimulation
    from accim.sim.accis import load_idf

    building = load_idf(path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[building], epws=[str(EPW)], parameters_type='accim custom model',
                                          output_frequencies=['hourly'], bypass_add_accis=True, verbose=False)
    simulation.set_output_meters_to_idf(output_meters=METERS, validate=False)
    simulation.set_output_readers(df_output_meter=pd.DataFrame({'key_name': METERS, 'frequency': ['Hourly'] * 2}))
    simulation.set_parameters(accis_params_dict={'custom_intercept': [18.8]})
    simulation.set_problem()
    simulation.sampling_full_set()
    results = simulation.run_parametric_simulation(out_dir=str(out_dir), processes=1, keep_dirs=False,
                                                   keep_input=True)
    return results, building


@needs_energyplus
def test_the_parametric_module_simulates_a_model_moved_with_its_schedule_files(tmp_path, monkeypatch, capfd):
    import subprocess

    path, relative = _moved_model(tmp_path)
    monkeypatch.chdir(tmp_path)
    results, building = _simulate(path, tmp_path / 'param')
    # The model of the module has the absolute path of the file (the IDF file keeps the relative one)
    schedule = building.getobject('Schedule:File', 'ACCIS Outdoor Mid Range')
    assert os.path.isabs(schedule.File_Name) and os.path.samefile(schedule.File_Name, path.parent / relative)
    assert f'{relative},' in path.read_text(encoding='latin-1')
    assert len(results) == 1 and results[METERS].notna().all().all() and (results[METERS] >= 0).all().all()
    assert results[METERS].to_numpy().sum() > 0
    # Without the absolute path (as before accim 1.2.0), besos simulates the model in a folder of its own, where
    # EnergyPlus does not find the file (measured on 2026-11-18)
    monkeypatch.setattr(sf, 'absolute_schedule_files', lambda idf, folders=None: {})
    capfd.readouterr()
    with pytest.raises(subprocess.CalledProcessError):
        _simulate(path, tmp_path / 'param_without')
    output = ''.join(capfd.readouterr())
    assert f'Schedule:File="ACCIS OUTDOOR MID RANGE", File Name: "{relative}" not found' in output


@needs_energyplus
def test_identify_variable_key_pattern_with_a_model_moved_with_its_schedule_files(tmp_path, monkeypatch, capfd):
    # identify_variable_key_pattern simulates a day of the model with besos, in a temporary folder
    from accim.sim.accis import load_idf
    from accim.utils import identify_variable_key_pattern

    (tmp_path / 'A').mkdir()
    shutil.copy(SAMPLE_IDF, tmp_path / 'A' / 'model.idf')
    building = load_idf(tmp_path / 'A' / 'model.idf')
    sf.write_schedule_file(building, 'Probe', [float(hour) for hour in range(8760)], 'probe.csv')
    assert sf.relative_schedule_files(building) == {'Probe': 'probe.csv'}
    building.save()
    shutil.copytree(tmp_path / 'A', tmp_path / 'B')
    shutil.rmtree(tmp_path / 'A')
    monkeypatch.chdir(tmp_path)
    path = str(tmp_path / 'B' / 'model.idf')
    assert identify_variable_key_pattern(path, 'Zone Mean Air Temperature', str(EPW)) == '[Zone Name]'
    # Without the absolute path, EnergyPlus does not find the file, and stops while it reads the schedules
    monkeypatch.setattr(sf, 'absolute_schedule_files', lambda idf, folders=None: {})
    capfd.readouterr()
    assert identify_variable_key_pattern(path, 'Zone Mean Air Temperature', str(EPW)).startswith('Error')
    assert 'ProcessScheduleInput: Preceding Errors cause termination' in ''.join(capfd.readouterr())
