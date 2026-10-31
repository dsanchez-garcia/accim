"""Tests for the Pareto status of the optimisations with constraints (accim.parametric_and_optimisation._pareto).

Adapted from the branch review/refactor-sim-v1-20261024 (notes/branch-reviews.md, section 1.3). Before, the
Pareto status of the results (_annotate_pareto_status) and the cleanup of the folders of the dominated evaluations
(keep_sim_files='non-dominated') only compared the objectives, so an evaluation that did not meet the constraints
could be marked pareto-optimal, and could make the folder of the best one that met them be removed.
"""
import numpy as np
import pandas as pd
import pytest
from besos.objectives import MeterReader
from besos.problem import EPProblem
from platypus import ParetoDominance, Solution

from accim.parametric_and_optimisation import patches
from accim.parametric_and_optimisation._pareto import constraint_violations, non_dominated_mask
from accim.parametric_and_optimisation.main import SimulationBase


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
    """Whether each row is non-dominated for the ParetoDominance of Platypus."""
    converted = problem.to_platypus()
    solutions = []
    for row in rows:
        solution = Solution(converted)
        solution.objectives[:] = row[:problem.num_outputs]
        solution.constraints[:] = row[problem.num_outputs:]
        solution.constraint_violation = sum(abs(bound(value))
                                            for bound, value in zip(converted.constraints, solution.constraints))
        solutions.append(solution)
    dominance = ParetoDominance()
    return [not any(dominance.compare(other, value) < 0 for other in solutions) for value in solutions]


@pytest.mark.parametrize('directions, bounds, rows', [
    ((True,), ('<=0',), [[1, 1], [2, 0]]),
    ((False,), ('>=2',), [[100, 1], [1, 2], [2, 3]]),
    ((True,), ('<=0',), [[1, 2], [10, 1], [9, 1]]),
    ((True, False), ('<=0', '>=1'), [[1, 5, 0, 2], [2, 4, -1, 1], [0, 10, 1, 0]]),
    ((True,), ('==2',), [[1, 2], [1, 2], [0, 3]]),
    ((True,), ('<2',), [[0, 2], [1, 1]]),
    ((True,), ('!=0',), [[0, 0], [1, 1]]),
    ((True,), (), [[1], [2], [1]]),
    ((True, True), (), [[1, 4], [2, 3], [3, 3], [0, 9]]),
])
def test_the_pareto_status_is_that_of_platypus(directions, bounds, rows):
    problem = make_problem(directions, bounds)
    frame = pd.DataFrame(rows, columns=problem.names('outputs') + problem.names('constraints'))
    original = frame.copy(deep=True)

    result = annotate(problem, frame, groups=[])

    assert result['pareto-optimal'].tolist() == platypus_front(problem, rows)
    pd.testing.assert_frame_equal(frame, original)


def test_an_evaluation_that_does_not_meet_the_constraints_does_not_dominate_one_that_does():
    # The first one has the best objective, but violates the constraint g0 <= 0
    frame = pd.DataFrame({'o0': [1.0, 2.0, 3.0], 'g0': [5.0, 0.0, -1.0]})

    assert annotate(make_problem(), frame, groups=[])['pareto-optimal'].tolist() == [False, True, False]


def test_groups_and_repeated_index_labels():
    frame = pd.DataFrame({'o0': [1., 2., 3.], 'g0': [1., 0., 0.], 'idf': ['A', 'A', 'B'], 'epw': ['E', 'E', 'E']},
                         index=[0, 0, 0])

    result = annotate(make_problem(), frame, groups=['idf', 'epw'])

    assert result['pareto-optimal'].tolist() == [False, True, True]
    assert result.index.tolist() == [0, 0, 0]


@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize('column', ['o0', 'g0'])
def test_evaluations_without_finite_values_are_not_pareto_optimal_and_do_not_dominate(bad, column):
    frame = pd.DataFrame({'o0': [1., 2.], 'g0': [0., 0.]})
    frame.loc[0, column] = bad

    assert annotate(make_problem(), frame, groups=[])['pareto-optimal'].tolist() == [False, True]


def test_without_the_columns_of_the_constraints_only_the_objectives_count():
    with pytest.warns(UserWarning, match=r"ignores the constraints \['g0'\]"):
        result = annotate(make_problem(), pd.DataFrame({'o0': [1., 2.]}), groups=[])

    assert result['pareto-optimal'].tolist() == [True, False]


def test_constraint_violations_and_their_checks():
    problem = make_problem(bounds=('<=750', '>=1'))

    assert constraint_violations(problem, [[800, 1], [700, 0], [700, 2]]).tolist() == [50.0, 1.0, 0.0]
    with pytest.raises(ValueError, match='2 constraint bounds for 1 constraints'):
        constraint_violations(problem, [[1]])
    assert non_dominated_mask(make_problem(), np.zeros((0, 1))).tolist() == []


def _evaluator(tmp_path, results_by_input):
    class Evaluator:
        problem = make_problem()
        _keep_dirs = True
        _keep_sim_files = 'non-dominated'
        _keep_sim_files_batch_size = len(results_by_input)
        _store_optimisation_records_in_memory = True

        def __init__(self):
            self._optimisation_eval_records = []

        def __call__(self, inputs, keep_dirs):
            return list(results_by_input[inputs[0]]) + [str(tmp_path / f'run{inputs[0]}')]

        def package_for_platypus(self, results):
            return results

    for key in results_by_input:
        (tmp_path / f'run{key}').mkdir()
        (tmp_path / f'run{key}' / 'eplusout.csv').write_text('result', encoding='utf-8')
    return Evaluator()


def test_the_cleanup_of_the_workers_keeps_the_best_evaluation_that_meets_the_constraints(tmp_path, monkeypatch):
    monkeypatch.setattr(patches, '_ensure_run_energyplus_copies_in_idf', lambda: None)
    # Input 0 meets the constraint (g0 = 0); input 1 has a better objective but does not (g0 = 1)
    evaluator = _evaluator(tmp_path, {0: (2., 0.), 1: (1., 1.)})

    patches._patched_eval_func(evaluator, [0])
    patches._patched_eval_func(evaluator, [1])

    assert (tmp_path / 'run0').is_dir()
    assert not (tmp_path / 'run1').exists()
    assert evaluator._optimisation_eval_records[0]['sim_dir'] == str(tmp_path / 'run0')
    assert evaluator._optimisation_eval_records[1]['sim_dir'] is None


def test_the_cleanup_of_the_workers_keeps_the_folders_of_the_evaluations_without_finite_values(tmp_path, monkeypatch):
    monkeypatch.setattr(patches, '_ensure_run_energyplus_copies_in_idf', lambda: None)
    evaluator = _evaluator(tmp_path, {0: (1., 0.), 1: (np.nan, 0.), 2: (3., 0.)})

    for key in (0, 1, 2):
        patches._patched_eval_func(evaluator, [key])

    assert (tmp_path / 'run0').is_dir()
    assert (tmp_path / 'run1').is_dir()
    assert not (tmp_path / 'run2').exists()
