"""Tests for accim.sim.accis.load_idf with energyplus_version='auto' and models of several EnergyPlus versions.

eppy can only use one IDD in a Python session. Before accim 1.1.0, load_idf read the models with besos with 'auto',
which read a model of another version with the IDD that it already had, and only warned, so objects of the model
could be lost (found on 2026-10-31: after a model of 25.1, the People:Instance objects of a model of 26.2, and
AddAccis stopped with "The model has no People objects"). load_idf reads all the models with eppy, and stops with a
clear error for the models of another version. The test runs in a new Python process, so that the IDD of the other
tests does not matter.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from accim.energyplus import idd_path

REPO = Path(__file__).resolve().parents[2]
MODEL_25_1 = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
MODEL_25_2 = (REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'parametric_and_optimisation_examples'
              / 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf')
SCRIPT = '''
import sys
from accim.sim.accis import load_idf

first = load_idf(sys.argv[1])
try:
    load_idf(sys.argv[2])
except ValueError as error:
    print('ERROR:', error)
else:
    print('NO ERROR')
print('Zones of the first model again:', len(load_idf(sys.argv[1]).idfobjects['ZONE']))
'''

pytestmark = pytest.mark.skipif(
    not all(Path(f'C:/EnergyPlusV{v}-0/Energy+.idd').exists() for v in ('25-1', '25-2')),
    reason='needs EnergyPlus 25.1 and 25.2')


def test_a_model_of_another_version_is_not_read_with_the_idd_of_the_first_one(tmp_path):
    pythonpath = [str(REPO)] + ([os.environ['PYTHONPATH']] if os.environ.get('PYTHONPATH') else [])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(pythonpath), PYTHONIOENCODING='utf-8')
    result = subprocess.run([sys.executable, '-c', SCRIPT, str(MODEL_25_1), str(MODEL_25_2)], capture_output=True,
                            text=True, encoding='utf-8', timeout=600, env=env, cwd=tmp_path)

    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    assert (f'ERROR: eppy is already using the IDD {idd_path("25.1")}' in result.stdout
            and f'cannot read {MODEL_25_2.name}, a model of EnergyPlus 25.2' in result.stdout), result.stdout[-3000:]
    # The models of the version of the session are still read
    assert 'Zones of the first model again: 2' in result.stdout


def test_load_idf_reads_the_models_with_eppy(tmp_path):
    script = ('import sys\n'
              'from eppy.modeleditor import IDF\n'
              'from accim.sim.accis import load_idf\n'
              'idf = load_idf(sys.argv[1])\n'
              'print(type(idf) is IDF, IDF.getiddname())\n')
    pythonpath = [str(REPO)] + ([os.environ['PYTHONPATH']] if os.environ.get('PYTHONPATH') else [])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(pythonpath), PYTHONIOENCODING='utf-8')
    result = subprocess.run([sys.executable, '-c', script, str(MODEL_25_2)], capture_output=True, text=True,
                            encoding='utf-8', timeout=600, env=env, cwd=tmp_path)

    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    assert result.stdout.strip() == f'True {idd_path("25.2")}'
