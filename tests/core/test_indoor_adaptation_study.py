"""Tests of the cases of the script of the validation study of F3 (``tools/indoor_adaptation_study.py``), without
simulations. Since the decisions of the author of 2026-11-19 (``notes/decisions.md``), the study is narrowed to what
the paper of the causal SET model specifies: one case of that model with the clothing insulation, the activity level
and the air speed of the People objects of the model (``iii_model``), besides the static reference (b) and the adaptive
setpoints of case (ii); the script runs the cases of the study by default (``--cases study``), and ``--cases all``
still runs all of them."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'tools' / 'indoor_adaptation_study.py'


def _script():
    spec = importlib.util.spec_from_file_location('indoor_adaptation_study', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_cases_of_the_study():
    study = _script()
    cases = study.cases()

    assert study.STUDY_CASES == ('i_fixed', 'ii_en16798', 'ii_ashrae55', 'iii_model')
    assert set(study.STUDY_CASES) <= set(cases)
    # The causal SET model with the inputs of the occupants of the model: no options that change the clothing or the air
    # speed (fans), nor the limiter of the drift; the hook reads them from the People objects
    assert cases['iii_model'][1:] == (1, 2, 3, {'set': True})
    assert study.fans(cases['iii_model'], 0.1) is None
    # The other cases stay, for sensitivities
    assert {'iii_seasonal', 'iii_dynamic', 'iv_v12', 'v_iii_dynamic_r025'} <= set(cases)


def test_list_marks_the_cases_of_the_study(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path), '--list'], capture_output=True, text=True,
                            env={**os.environ, 'PYTHONPATH': str(REPO)})

    assert result.returncode == 0, result.stderr
    assert [line.split(':')[0] for line in result.stdout.splitlines() if line.endswith('(study)')] == [
        'i_fixed', 'ii_en16798', 'ii_ashrae55', 'iii_model']
