"""Tests for the optimisation algorithms of run_optimisation.

run_optimisation runs the algorithms of platypus (through besos.optimizer) with ``population_size`` and
``algorithm_options``. Before, two of them could never run: PAES evolves one solution and has no population
size (platypus 1.4: "got multiple values for argument 'population_size'"), and ParticleSwarm is the abstract
base class of the particle swarms of platypus, without a fitness function ("'NoneType' object is not
callable"). Now PAES runs without population_size, PAES and EvolutionaryStrategy (one parent for each solution)
get a mutation as their variator instead of the crossover of besos, ParticleSwarm is rejected with a clear
error, and the settings that the others need are checked before the
optimisation starts (before, they failed in the first case, with the errors of platypus). Also, platypus
ignored population_size for OMOPSO, SMPSO and CMAES, and GeneticAlgorithm and EvolutionaryStrategy took it only
as the initial population, so they evaluated 100 solutions in each generation; now it is their swarm or
offspring.
"""
import platypus
import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import OptimisationSimulation, _check_optimisation_algorithm

from .test_optimisation_checkpoint_resume import (
    _DummyEvaluator,
    _fake_build_full_outputs_df,
    _make_lightweight_optimisation,
)


class _Problem:
    """A besos problem with the objectives and the platypus types of its parameters."""

    def __init__(self, n_objectives=2, types=None, directions=None):
        self.n_objectives = len(directions) if directions else n_objectives
        self.types = types or [platypus.Real(0, 1)]
        self.directions = directions

    def to_platypus(self):
        problem = platypus.Problem(len(self.types), self.n_objectives)
        problem.types[:] = self.types
        if self.directions:
            problem.directions[:] = self.directions
        return problem


class _Category(platypus.Subset):
    """The platypus type of the categorical parameters of besos."""

    def __init__(self, options):
        super().__init__(options, 1)


@pytest.mark.parametrize('algorithm, options, population_size', [
    ('NSGAII', {}, 2), ('GDE3', {}, 2), ('MOEAD', {}, 2), ('IBEA', {}, 2), ('PESA2', {}, 2), ('PAES', {}, 2),
    ('EpsMOEA', {'epsilons': [0.01, 0.01]}, 2), ('OMOPSO', {'epsilons': [0.01, 0.01]}, 2),
    ('EpsNSGAII', {'epsilons': [0.01, 0.01]}, 2), ('NSGAIII', {'divisions_outer': 4}, 2), ('SPEA2', {}, 3),
    ('SPEA2', {'k': 2}, 4), ('SMPSO', {}, 2), ('CMAES', {}, 2),
])
def test_valid_settings(algorithm, options, population_size):
    _check_optimisation_algorithm(algorithm, options, population_size, _Problem())


@pytest.mark.parametrize('algorithm, options, population_size, error, match', [
    ('ParticleSwarm', {}, 2, ValueError, 'use OMOPSO'),
    ('Simplex', {}, 2, KeyError, 'not found'),
    ('EpsMOEA', {}, 2, ValueError, "'epsilons'"),
    ('OMOPSO', {}, 2, ValueError, "'epsilons'"),
    ('EpsNSGAII', {}, 2, ValueError, "'epsilons'"),
    ('NSGAIII', {}, 2, ValueError, "'divisions_outer'"),
    ('SPEA2', {}, 2, ValueError, 'at least 3'),
    ('SPEA2', {'k': 2}, 3, ValueError, 'at least 4'),
])
def test_invalid_settings(algorithm, options, population_size, error, match):
    with pytest.raises(error, match=match):
        _check_optimisation_algorithm(algorithm, options, population_size, _Problem())


def test_settings_that_depend_on_the_problem():
    categorical = _Problem(types=[_Category([1, 2, 3]), platypus.Real(0, 1)])
    for algorithm, options in [('OMOPSO', {'epsilons': [0.01, 0.01]}), ('SMPSO', {}), ('CMAES', {})]:
        with pytest.raises(ValueError, match='numeric ranges'):
            _check_optimisation_algorithm(algorithm, options, 2, categorical)
    _check_optimisation_algorithm('NSGAII', {}, 2, categorical)

    for algorithm in ['GeneticAlgorithm', 'EvolutionaryStrategy']:
        with pytest.raises(ValueError, match='single-objective'):
            _check_optimisation_algorithm(algorithm, {}, 2, _Problem(n_objectives=2))
        _check_optimisation_algorithm(algorithm, {}, 2, _Problem(n_objectives=1))

    maximised = _Problem(directions=[platypus.Problem.MINIMIZE, platypus.Problem.MAXIMIZE])
    with pytest.raises(ValueError, match='only minimises'):
        _check_optimisation_algorithm('NSGAIII', {'divisions_outer': 4}, 2, maximised)
    _check_optimisation_algorithm('NSGAII', {}, 2, maximised)

    # Without a problem that platypus can take (such as a loaded one), the settings of the problem are not checked
    _check_optimisation_algorithm('SMPSO', {}, 2, None)


class _EvaluatorWithProblem(_DummyEvaluator):
    def to_platypus(self):
        return _Problem(types=[_Category([1, 2, 3]), platypus.Real(0, 1)]).to_platypus()


def _run(monkeypatch, tmp_path, algorithm, fake, **kwargs):
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kw: None, raising=False)
    monkeypatch.setattr(OptimisationSimulation, 'set_evaluator',
                        lambda self, epw, out_dir, building=None: _EvaluatorWithProblem(epw=epw, out_dir=out_dir))
    monkeypatch.setattr(OptimisationSimulation, '_build_full_optimisation_outputs_df', _fake_build_full_outputs_df)
    if fake is not None:
        monkeypatch.setattr(main_module.optimizer, algorithm, fake)
    sim = _make_lightweight_optimisation(epws=['A.epw'])
    return sim.run_optimisation(out_dir=str(tmp_path / 'optim'), algorithm=algorithm, evaluations=2,
                                population_size=2, processes=1, show_progress=False, **kwargs)


def _recorder(calls):
    def fake(evaluator, evaluations, **kwargs):
        calls.append(kwargs)
        return pd.DataFrame([{'x': 1.0, 'obj': 1.0}])

    return fake


@pytest.mark.parametrize('algorithm, size_options', [
    ('PAES', {}), ('EvolutionaryStrategy', {'population_size': 2, 'offspring_size': 2}),
])
def test_one_parent_algorithms_get_a_mutation_as_their_variator(tmp_path, monkeypatch, algorithm, size_options):
    # PAES evolves one solution (it has no population size) and EvolutionaryStrategy each solution from one parent;
    # besos gives every algorithm a crossover, which takes two ("unexpected number of offspring, expected 2,
    # received 1" once they iterate)
    calls = []
    results = _run(monkeypatch, tmp_path, algorithm, _recorder(calls))

    assert len(results) == 1
    variator = calls[0].pop('variator')
    assert calls[0] == size_options
    # The categorical parameter is mutated with Replace, and the numeric one with PM
    assert isinstance(variator, platypus.CompoundMutation)
    assert variator.arity == 1


def test_one_parent_algorithms_keep_the_variator_of_the_algorithm_options(tmp_path, monkeypatch):
    calls = []
    variator = platypus.CompoundMutation(platypus.Replace(), platypus.PM())
    _run(monkeypatch, tmp_path, 'PAES', _recorder(calls), algorithm_options={'variator': variator, 'capacity': 50})

    assert calls[0] == {'variator': variator, 'capacity': 50}


def test_the_other_algorithms_get_the_population_size(tmp_path, monkeypatch):
    calls = []
    _run(monkeypatch, tmp_path, 'GDE3', _recorder(calls))

    assert calls == [{'population_size': 2}]


@pytest.mark.parametrize('algorithm, options, size_option', [
    ('GeneticAlgorithm', {}, 'offspring_size'), ('EvolutionaryStrategy', {}, 'offspring_size'),
    ('OMOPSO', {'epsilons': [0.01]}, 'swarm_size'), ('SMPSO', {}, 'swarm_size'), ('CMAES', {}, 'offspring_size'),
])
def test_the_population_size_is_the_size_of_each_generation(tmp_path, monkeypatch, algorithm, options, size_option):
    # platypus ignores population_size for the swarms and CMA-ES, and these algorithms evaluated 100 solutions in
    # each generation (the default of their own option), whatever the population_size of run_optimisation
    calls = []
    _run(monkeypatch, tmp_path, algorithm, _recorder(calls), algorithm_options=options)
    calls[0].pop('variator', None)  # EvolutionaryStrategy also gets a mutation
    assert calls == [{'population_size': 2, size_option: 2, **options}]

    # Unless the algorithm options give it
    calls.clear()
    _run(monkeypatch, tmp_path, algorithm, _recorder(calls), algorithm_options={**options, size_option: 10})
    calls[0].pop('variator', None)
    assert calls == [{'population_size': 2, size_option: 10, **options}]


@pytest.mark.parametrize('algorithm, error', [('ParticleSwarm', ValueError), ('Simplex', KeyError),
                                              ('NSGAIII', ValueError)])
def test_invalid_algorithms_stop_before_the_optimisation(tmp_path, monkeypatch, algorithm, error):
    with pytest.raises(error):
        _run(monkeypatch, tmp_path, algorithm, None)

    # Nothing was written (before, the folder and the backup of the IDF were)
    assert not (tmp_path / 'optim').exists()
