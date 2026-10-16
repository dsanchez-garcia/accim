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


# NSGA-II evaluates the initial population, then one generation of offspring at a time. The
# offspring come in pairs, so with an odd population each later generation evaluates one more.

def _lightweight_optimisation():
    from accim.parametric_and_optimisation.main import OptimisationSimulation
    return OptimisationSimulation(buildings=None, epws=['A.epw'], parameters_type=None, bypass_addAccis=True)


def test_estimate_counts_the_extra_offspring_of_odd_populations(capsys):
    sim = _lightweight_optimisation()

    assert sim.estimate_optimisation_sims(evaluations=6, population_size=3, epws=['A.epw', 'B.epw']) == 14
    assert 'sims per EPW   : 7' in capsys.readouterr().out
    assert sim.estimate_optimisation_sims(evaluations=8, population_size=4, epws=['A.epw']) == 8
    assert sim.estimate_optimisation_sims(evaluations=2, population_size=3, epws=['A.epw']) == 3


@pytest.mark.parametrize(('population_size', 'evaluations'), [(3, 6), (5, 12), (4, 8), (3, 2)])
def test_estimate_matches_the_evaluations_of_nsga2(population_size, evaluations, capsys):
    expected = _lightweight_optimisation().estimate_optimisation_sims(
        evaluations=evaluations, population_size=population_size, epws=['A.epw'],
    )
    reporter = OptimisationProgressReporter(
        total_cases=1, sims_per_case=expected, total_expected_sims=expected, processes=1,
    )
    evaluator = ProgressReportingEvaluator(inner=platypus.MapEvaluator(), reporter=reporter)
    reporter.start_run('NSGAII', evaluations, population_size)
    reporter.start_case(1, 'model', 'weather')
    algorithm = platypus.NSGAII(_make_problem(), population_size=population_size, evaluator=evaluator)
    algorithm.run(evaluations)
    reporter.end_case()

    out = capsys.readouterr().out
    assert algorithm.nfe == reporter.total_done == expected
    assert f'total {expected}/~{expected} (100.0%)' in out


class _DummyBuilding:
    def __init__(self, idfname):
        self.idfname = idfname
        self.idfobjects = {}

    def savecopy(self, backup_path):
        with open(backup_path, 'w', encoding='utf-8') as handle:
            handle.write('Version,9.6;\n')


class _StopBeforeSimulating(Exception):
    pass


def test_run_optimisation_progress_counts_the_extra_offspring(monkeypatch, tmp_path, capsys):
    sim = _lightweight_optimisation()
    sim.buildings = [_DummyBuilding('idf_a.idf')]
    sim.building = sim.buildings[0]

    def _set_evaluator(*args, **kwargs):
        raise _StopBeforeSimulating()

    monkeypatch.setattr(sim, 'set_evaluator', _set_evaluator)

    with pytest.raises(_StopBeforeSimulating):
        sim.run_optimisation(
            epws=['A.epw'], out_dir=str(tmp_path / 'optim'), evaluations=6, population_size=3,
            show_progress=True,
        )

    out = capsys.readouterr().out
    assert '~7 sims/case (2 generation(s): 3 initial + 1 x 4 offspring, evaluations=6)' in out
    assert '~7 sims in total' in out
    assert '~7 simulation(s) expected' in out

