"""Tests for the optimisation progress reporting evaluator."""

import pytest

platypus = pytest.importorskip('platypus')

from accim.parametric_and_optimisation.optimisation_progress import (
    OptimisationProgressReporter,
    ProgressReportingEvaluator,
    _format_seconds,
)


def _schaffer(x):
    return [x[0] ** 2, (x[0] - 2) ** 2]


def _make_problem():
    problem = platypus.Problem(1, 2)
    problem.types[:] = platypus.Real(-10, 10)
    problem.function = _schaffer
    return problem


def _run(inner, evaluations=20, population_size=10):
    reporter = OptimisationProgressReporter(
        total_cases=1, sims_per_case=20, total_expected_sims=20, processes=1,
    )
    evaluator = ProgressReportingEvaluator(inner=inner, reporter=reporter)
    reporter.start_run('NSGAII', evaluations, population_size)
    reporter.start_case(1, 'model', 'weather')
    algorithm = platypus.NSGAII(_make_problem(), population_size=population_size, evaluator=evaluator)
    algorithm.run(evaluations)
    reporter.end_case()
    return reporter, algorithm


def test_sequential_progress(capsys):
    reporter, algorithm = _run(platypus.MapEvaluator())
    out = capsys.readouterr().out
    assert reporter.total_done == algorithm.nfe == 20
    assert reporter.generation == 2
    assert 'total 20/~20 (100.0%)' in out
    assert all(s.evaluated for s in algorithm.result)


def test_process_pool_progress(capsys):
    inner = platypus.ProcessPoolEvaluator(2)
    try:
        reporter, algorithm = _run(inner)
    finally:
        inner.close()
    out = capsys.readouterr().out
    assert reporter.total_done == algorithm.nfe == 20
    assert 'gen 2 sim 10/10' in out
    assert all(s.evaluated for s in algorithm.result)


def test_format_seconds():
    assert _format_seconds(3725) == '1:02:05'
    assert _format_seconds(-3) == '0:00:00'

