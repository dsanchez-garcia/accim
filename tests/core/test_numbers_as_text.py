"""The copies of the models that the runners of accim simulate keep the text of the numbers of the files
(:func:`accim.sim.accis.numbers_as_text`, since accim 1.2.0): eppy converts the numbers of the fields to floats when it
reads a model, and writes those wider than 18 characters with 7 significant digits, such as the coefficients of the
curves of the indoor units of the VRF systems of accim in the models of ``add_accis_to_idf``, so the results of
``run_ep`` (with both backends) differed in their last digits from those of EnergyPlus with the file itself (found on
2026-11-12 as a difference between the backends, an entry of ``TODO.md``; its cause found on 2026-11-18)."""
import contextlib
import os
import platform
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _vrf_model(folder):
    """The sample model with the ACCIS of ``add_accis_to_idf`` (its VRF system, whose curves have coefficients wider
    than 18 characters), simulated on 1 July, saved as accim writes it."""
    from accim.sim.accis import add_accis_to_idf, load_idf

    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'model.idf')
    idf = load_idf(folder / 'model.idf')
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 7, 1
    run_period.End_Month, run_period.End_Day_of_Month = 7, 1
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['timestep'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    idf.save()
    return folder / 'model.idf'


def _fields(path):
    """The fields of the objects of an IDF file, as EnergyPlus reads them (without comments and spaces)."""
    text = re.sub(r'!.*', '', Path(path).read_text(encoding='latin-1'))
    return [field.strip() for field in re.split(r'[,;]', text)]


@needs_idd
def test_eppy_keeps_the_text_of_the_numbers_in_the_context(tmp_path):
    from accim.sim.accis import load_idf, numbers_as_text

    model = _vrf_model(tmp_path)
    assert '-0.000010819418650677,' in model.read_text(encoding='latin-1')
    with numbers_as_text():
        idf = load_idf(model)
    curve = idf.getobject('Curve:Cubic', 'VRFTUCoolCapFT')
    assert curve.Coefficient3_x2 == '-0.000010819418650677' and curve.Coefficient4_x3 == '0.0000101359395177008'
    # The copy has the fields of the file, with the text of their numbers
    idf.saveas(str(tmp_path / 'copy.idf'))
    assert _fields(tmp_path / 'copy.idf') == _fields(model)
    # After the context, eppy converts the numbers again
    curve = load_idf(model).getobject('Curve:Cubic', 'VRFTUCoolCapFT')
    assert curve.Coefficient3_x2 == -1.0819418650677e-05 and isinstance(curve.Maximum_Value_of_x, float)


#: run_ep with the backend of the API, in a new process, without numbers_as_text (eppy's own reading). The library of
#: the API of EnergyPlus must stay out of the process of the tests: after it, the first call of numba of
#: pythermalcomfort in another test stopped that process with an access violation (see
#: accim.sim.energyplus_api.prepare_hooks), so the controls of the API run in a process of their own
_API_WITHOUT_NUMBERS_AS_TEXT = """
import contextlib
import accim.sim.accis as accis
from accim.run import run_ep
accis.numbers_as_text = contextlib.nullcontext
run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend='api', processes=0)
"""


@needs_energyplus
@pytest.mark.parametrize('backend', ['ems', 'api'])
def test_run_ep_simulates_the_numbers_of_the_file(tmp_path, monkeypatch, backend):
    # Measured on 2026-11-18 with EnergyPlus 25.1: with the text of the numbers of the file in the copy, the results of
    # run_ep are those of EnergyPlus with the file itself, digit by digit, with both backends (the backend of the API
    # in a process of its own, processes=1)
    import accim.sim.accis as accis
    from accim.run import run_ep

    model = _vrf_model(tmp_path / 'model')
    program = _energyplus_with_api() / ('energyplus.exe' if platform.system() == 'Windows' else 'energyplus')
    direct = subprocess.run([str(program), '-d', str(tmp_path / 'direct'), '-p', 'run', '-s', 'C', '-r', '-x', '-w',
                             str(EPW), str(model)], capture_output=True, text=True)
    assert direct.returncode == 0, direct.stdout[-3000:]
    expected = pd.read_csv(tmp_path / 'direct' / 'run.csv')
    shutil.copy(EPW, model.parent / EPW.name)
    monkeypatch.chdir(model.parent)
    outputs = model.parent / 'model[Seville_Present.csv'
    run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend=backend,
           processes=0 if backend == 'ems' else 1)
    pd.testing.assert_frame_equal(pd.read_csv(outputs), expected, check_exact=True)
    # Without it (as before accim 1.2.0), eppy writes the coefficients of the curves of the VRF system with 7
    # significant digits, and the results differ in their last digits
    outputs.unlink()
    if backend == 'ems':
        monkeypatch.setattr(accis, 'numbers_as_text', contextlib.nullcontext)
        run_ep(only_accim_idfs=False, confirm=True, energyplus_version='auto', backend=backend, processes=0)
    else:
        pythonpath = [str(REPO)] + ([os.environ['PYTHONPATH']] if os.environ.get('PYTHONPATH') else [])
        result = subprocess.run([sys.executable, '-c', _API_WITHOUT_NUMBERS_AS_TEXT], cwd=model.parent,
                                capture_output=True, text=True, timeout=900,
                                env=dict(os.environ, PYTHONPATH=os.pathsep.join(pythonpath)))
        assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    found = pd.read_csv(outputs)
    assert not found.equals(expected)
    pd.testing.assert_frame_equal(found, expected, check_exact=False, rtol=1e-6, atol=1e-6)
