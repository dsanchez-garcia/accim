"""Feasibility-aware dominance must agree in history annotation and workers."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from besos.objectives import MeterReader
from besos.problem import EPProblem
from platypus import ParetoDominance, Solution

from accim.parametric_and_optimisation.main import SimulationBase
from accim.parametric_and_optimisation import patches


def make_problem(directions=(True,), bounds=('<=0',)):
    return EPProblem(
        outputs=[MeterReader(key_name=f'o{i}', name=f'o{i}') for i in range(len(directions))],
        minimize_outputs=list(directions),
        constraints=[MeterReader(key_name=f'g{i}', name=f'g{i}') for i in range(len(bounds))],
        constraint_bounds=list(bounds),
    )


def annotate(problem, data, groups=None):
    sim = SimulationBase.__new__(SimulationBase)
    sim.problem = problem
    return sim._annotate_pareto_status(data.copy(), data.copy(), group_by=groups)


def platypus_front(problem, rows):
    converted = problem.to_platypus()
    solutions = []
    for row in rows:
        solution = Solution(converted)
        solution.objectives[:] = row[:problem.num_outputs]
        solution.constraints[:] = row[problem.num_outputs:]
        solution.constraint_violation = sum(abs(bound(value)) for bound, value in zip(converted.constraints, solution.constraints))
        solutions.append(solution)
    dominance = ParetoDominance()
    return [not any(dominance.compare(other, value) < 0 for other in solutions) for value in solutions]


@pytest.mark.parametrize('directions,bounds,rows', [
    ((True,), ('<=0',), [[1, 1], [2, 0]]),
    ((False,), ('>=2',), [[100, 1], [1, 2], [2, 3]]),
    ((True,), ('<=0',), [[1, 2], [10, 1], [9, 1]]),
    ((True, False), ('<=0', '>=1'), [[1, 5, 0, 2], [2, 4, -1, 1], [0, 10, 1, 0]]),
    ((True,), ('==2',), [[1, 2], [1, 2], [0, 3]]),
    ((True,), ('<2',), [[0, 2], [1, 1]]),
    ((True,), ('!=0',), [[0, 0], [1, 1]]),
    ((True,), (), [[1], [2], [1]]),
])
def test_annotation_matches_platypus(directions, bounds, rows):
    problem = make_problem(directions, bounds)
    frame = pd.DataFrame(rows, columns=problem.names('outputs') + problem.names('constraints'))
    original = frame.copy(deep=True)
    result = annotate(problem, frame, groups=[])
    assert result['pareto-optimal'].tolist() == platypus_front(problem, rows)
    pd.testing.assert_frame_equal(frame, original)


def test_grouping_and_duplicate_indices_remain_positional():
    problem = make_problem()
    frame = pd.DataFrame({'o0': [1., 2., 3.], 'g0': [1., 0., 0.],
                          'idf': ['A', 'A', 'B'], 'epw': ['E', 'E', 'E']}, index=[0, 0, 0])
    result = annotate(problem, frame, groups=['idf', 'epw'])
    assert result['pareto-optimal'].tolist() == [False, True, True]
    assert result.index.tolist() == [0, 0, 0]


@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize('column', ['o0', 'g0'])
def test_nonfinite_data_is_rejected_before_cleanup(bad, column):
    frame = pd.DataFrame({'o0': [1.], 'g0': [0.]})
    frame.loc[0, column] = bad
    with pytest.raises(ValueError, match='(?i)finite|invalid'):
        annotate(make_problem(), frame)


def test_missing_constraint_is_not_silently_ignored():
    with pytest.raises(ValueError, match='(?i)constraint|missing'):
        annotate(make_problem(), pd.DataFrame({'o0': [1., 2.]}))


def test_worker_cleanup_preserves_feasible_optimum(tmp_path, monkeypatch):
    monkeypatch.setattr(patches, '_ensure_run_energyplus_copies_in_idf', lambda: None)
    feasible = tmp_path / 'run' / 'feasible'
    infeasible = tmp_path / 'run' / 'infeasible'
    for folder in (feasible, infeasible):
        folder.mkdir(parents=True)
        (folder / 'eplusout.csv').write_text('result', encoding='utf-8')

    class Evaluator:
        problem = make_problem()
        _keep_dirs = True
        _keep_sim_files = 'non-dominated'
        _keep_sim_files_batch_size = 2
        _store_optimisation_records_in_memory = True
        _owned_run_root = str(tmp_path / 'run')

        def __init__(self):
            self._optimisation_eval_records = []

        def __call__(self, inputs, keep_dirs):
            return [2., 0., str(feasible)] if inputs[0] == 0 else [1., 1., str(infeasible)]

        def package_for_platypus(self, results):
            return results

    evaluator = Evaluator()
    patches._patched_eval_func(evaluator, [0])
    patches._patched_eval_func(evaluator, [1])
    assert feasible.is_dir()
    assert not infeasible.exists()
    assert evaluator._optimisation_eval_records[0]['sim_dir'] == str(feasible)

