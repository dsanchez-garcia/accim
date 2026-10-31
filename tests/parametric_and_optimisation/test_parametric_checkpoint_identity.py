"""Tests for the identity of the tasks of the parametric checkpoints (resume_from_checkpoint).

A resumed run skips the tasks whose signatures are in its checkpoint. The signatures had the name of the IDF, the
EPW and the parameters only, so after changing the model, the EPW or the outputs under the same names, a resumed
run reused their old results. They also have the content of the IDF (its objects, without comments or spaces) and
of the EPW, and the names of the outputs, now (notes/questions.md, the integrity block of
review/refactor-sim-v1-20261024).
"""
import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import SimulationBase

from .test_parametric_batch_checkpoint import _DummyProblem, _fake_worker, _make_lightweight_parametric

IDF_TEXT = 'Version,25.1;\nZone,\n    Block1:Zone1,  !- Name\n    0;     !- Direction of Relative North\n'


@pytest.fixture
def calls(tmp_path, monkeypatch):
    """The parameter values that the (fake) simulations run, in a working folder with the IDF and the EPW."""
    calls = []

    def _counting_worker(*args, **kwargs):
        calls.append(int(args[10]['x']))
        return _fake_worker(*args, **kwargs)

    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _counting_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    monkeypatch.chdir(tmp_path)
    # The lightweight simulation has no buildings, so its tasks read the IDF of their name
    (tmp_path / 'unknown_idf_0.idf').write_text(IDF_TEXT, encoding='latin-1')
    (tmp_path / 'Test.epw').write_text('LOCATION,Seville\n1,2,3\n', encoding='latin-1')
    return calls


def _run(sim, tmp_path):
    return sim.run_parametric_simulation(
        out_dir=str(tmp_path / 'out'), df=pd.DataFrame({'x': [1, 2]}), processes=1, batch_size=1,
        checkpoint_every_batch=True, resume_from_checkpoint=True, keep_dirs=False, keep_input=True)


def test_a_resumed_run_reuses_the_tasks_whose_files_and_outputs_did_not_change(tmp_path, calls):
    sim = _make_lightweight_parametric()
    _run(sim, tmp_path)
    assert sorted(calls) == [1, 2]
    calls.clear()
    # The same model saved again, with other comments and spaces
    (tmp_path / 'unknown_idf_0.idf').write_text(IDF_TEXT.replace('  !- Name', '').replace('    ', '  '),
                                                 encoding='latin-1')

    results = _run(sim, tmp_path)

    assert calls == []
    assert sorted(results['energy'].tolist()) == [10.0, 20.0]


@pytest.mark.parametrize('change', ['idf', 'epw', 'outputs'])
def test_a_resumed_run_simulates_again_the_tasks_whose_model_weather_or_outputs_changed(tmp_path, calls, capsys,
                                                                                        change):
    sim = _make_lightweight_parametric()
    _run(sim, tmp_path)
    calls.clear()
    if change == 'idf':
        (tmp_path / 'unknown_idf_0.idf').write_text(IDF_TEXT.replace('    0;', '    90;'), encoding='latin-1')
    elif change == 'epw':
        (tmp_path / 'Test.epw').write_text('LOCATION,Seville\n1,2,4\n', encoding='latin-1')
    else:
        sim.problem = _DummyProblem(inputs=['x'], outputs=['heating'])

    results = _run(sim, tmp_path)

    assert sorted(calls) == [1, 2]
    assert len(results) == 2
    assert '2 of the 2 tasks of the checkpoint are not tasks of this run' in capsys.readouterr().out


def test_the_digest_of_an_idf_ignores_its_comments_and_spaces(tmp_path):
    first, second, third = (tmp_path / 'a.idf', tmp_path / 'b.idf', tmp_path / 'c.idf')
    first.write_text('Version,25.1;\r\nZone,Z1,  !- Name\r\n  0;\r\n', encoding='latin-1')
    second.write_text('! A model\nVersion, 25.1;\nZone, Z1, 0;\n', encoding='latin-1')
    third.write_text('Version,25.1;\nZone,Z1;0;\n', encoding='latin-1')

    digest = SimulationBase._content_digest(str(first), idf=True)

    assert digest == SimulationBase._content_digest(str(second), idf=True)
    # The same fields in other objects are another model
    assert digest != SimulationBase._content_digest(str(third), idf=True)
    assert SimulationBase._content_digest(str(first)) != SimulationBase._content_digest(str(second))
    assert SimulationBase._content_digest(str(tmp_path / 'missing.idf'), idf=True) is None
    assert SimulationBase._content_digest(None) is None
