# 04_test_optimization.py
"""
Test de run_optimisation.
Cubre: Todos los algoritmos (NSGAII, EpsMOEA, GDE3, SPEA2, MOEAD, NSGAIII,
OMOPSO, SMPSO, CMAES, IBEA, PAES, PESA2, EpsNSGAII, etc), cada uno con las
opciones que necesita, y ParticleSwarm, que no puede ejecutarse.
"""

import pytest

from .. import test_setup as ts

ALGORITHMS = [
    'GeneticAlgorithm',
    'EvolutionaryStrategy',
    'NSGAII',
    'EpsMOEA',
    'GDE3',
    'SPEA2',
    'MOEAD',
    'NSGAIII',
    'OMOPSO',
    'SMPSO',
    'CMAES',
    'IBEA',
    'PAES',
    'PESA2',
    'EpsNSGAII'
]
# Opciones sin valor por defecto en platypus (un épsilon por objetivo) y población mínima de SPEA2 (k + 2)
ALGORITHM_SETTINGS = {
    'EpsMOEA': {'algorithm_options': {'epsilons': [0.01]}},
    'OMOPSO': {'algorithm_options': {'epsilons': [0.01]}},
    'EpsNSGAII': {'algorithm_options': {'epsilons': [0.01]}},
    'NSGAIII': {'algorithm_options': {'divisions_outer': 4}},
    'SPEA2': {'population_size': 3},
}
# Solo admiten rangos numéricos, no parámetros categóricos
RANGE_ONLY_ALGORITHMS = ('OMOPSO', 'SMPSO', 'CMAES')
# IBEA se detiene ('objective with empty range') si todas las soluciones de una generación tienen los mismos
# objetivos, algo probable con tres categorías y una población de 2: también con rangos numéricos
NUMERIC_RANGES_IN_TEST = RANGE_ONLY_ALGORITHMS + ('IBEA',)

def test_optimization_basic():
    """Test: Optimization básica con NSGAII."""
    ts.print_section("TEST: Optimization - NSGAII (Basic)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [1, 2, 3], 'HVACmode': [0, 2]})
    ts.set_meter_readers(sim)
    sim.set_problem(
        minimize_outputs=[True, True],
        constraints=None
    )

    results = sim.run_optimisation(
        out_dir='./test_optim_basic',
        algorithm='NSGAII',
        evaluations=4,
        population_size=2,
        processes=1
    )

    ts.log_test("Optimization NSGAII", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows, Pareto-optimal: {(results['pareto-optimal']==True).sum()}")
    assert 'pareto-optimal' in results.columns
    assert len(results) >= 4
    assert results[ts.METERS].notna().all().all()

def _single_objective_simulation(algo):
    """Simulación de un objetivo (Electricity:HVAC): rangos del modelo custom para los algoritmos de
    NUMERIC_RANGES_IN_TEST, y categorías del modelo predefinido para los demás."""
    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    if algo in NUMERIC_RANGES_IN_TEST:
        sim = ts.OptimisationSimulation(
            buildings=buildings,
            epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
            parameters_type='accim custom model'
        )
        sim.set_parameters(accis_params_dict=dict(ts.CUSTOM_RANGES))
    else:
        sim = ts.OptimisationSimulation(
            buildings=buildings,
            epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
            parameters_type='accim predefined model'
        )
        sim.set_parameters(accis_params_dict={'CAT': [1, 2, 3]})
    ts.set_meter_readers(sim, meters=['Electricity:HVAC'])
    sim.set_problem(minimize_outputs=[True])
    return sim

def test_optimization_all_algorithms():
    """Test: Todos los algoritmos disponibles, con las opciones que necesita cada uno."""
    ts.print_section("TEST: Optimization - All Algorithms")

    failures = {}
    for algo in ALGORITHMS:
        print(f"\n  Testing {algo}...")
        # Más evaluaciones que la población inicial, para que cada algoritmo itere al menos una vez
        settings = dict(evaluations=5, population_size=2, processes=1)
        settings.update(ALGORITHM_SETTINGS.get(algo, {}))
        try:
            sim = _single_objective_simulation(algo)
            results = sim.run_optimisation(out_dir=f'./test_optim_{algo}', algorithm=algo, **settings)
            passed = len(results) > 0 and results['Electricity:HVAC'].notna().all()
            ts.log_test(f"Algorithm {algo}", "PASS" if passed else "FAIL", f"Rows: {len(results)}")
            if not passed:
                failures[algo] = f'{len(results)} rows'
        except Exception as e:
            ts.log_test(f"Algorithm {algo}", "FAIL", str(e))
            failures[algo] = repr(e)
    assert not failures, failures

def test_optimization_particle_swarm():
    """Test: ParticleSwarm (clase base abstracta de platypus) se rechaza antes de empezar."""
    ts.print_section("TEST: Optimization - ParticleSwarm")

    sim = _single_objective_simulation('ParticleSwarm')
    with pytest.raises(ValueError, match='OMOPSO'):
        sim.run_optimisation(out_dir='./test_optim_ParticleSwarm', algorithm='ParticleSwarm', evaluations=2,
                             population_size=2, processes=1)
    ts.log_test("Algorithm ParticleSwarm", "PASS", "ValueError")

def test_optimization_multi_epw():
    """Test: Optimization con múltiples EPWs."""
    ts.print_section("TEST: Optimization - Multi-EPW")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [1, 2, 3]})
    ts.set_meter_readers(sim, meters=['Electricity:HVAC'])
    sim.set_problem(minimize_outputs=[True])

    results = sim.run_optimisation(
        out_dir='./test_optim_multi_epw',
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1
    )

    ts.log_test("Optimization Multi-EPW", "PASS" if 'epw' in results.columns else "FAIL",
             f"EPWs in results: {results['epw'].nunique()}")
    assert 'epw' in results.columns
    assert results['epw'].nunique() == 2

def test_optimization_keep_sim_files():
    """Test: Options para keep_sim_files."""
    ts.print_section("TEST: Optimization - Keep Sim Files Options")

    for keep_option in ['all', 'non-dominated', 'none']:
        print(f"\n  Testing keep_sim_files={keep_option}...")
        buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
        sim = ts.OptimisationSimulation(
            buildings=buildings,
            epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
            parameters_type='accim predefined model'
        )

        sim.set_parameters(accis_params_dict={'CAT': [1, 2, 3]})
        ts.set_meter_readers(sim, meters=['Electricity:HVAC'])
        sim.set_problem(minimize_outputs=[True])

        results = sim.run_optimisation(
            out_dir=f'./test_optim_keep_{keep_option}',
            algorithm='NSGAII',
            evaluations=2,
            population_size=2,
            keep_sim_files=keep_option,
            processes=1
        )

        ts.log_test(f"Keep Files ({keep_option})", "PASS" if len(results) > 0 else "FAIL")
        assert len(results) > 0

def test_optimization_estimate_sims():
    """Test: Estimar cantidad de simulaciones."""
    ts.print_section("TEST: Optimization - Estimate Simulations")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [1, 2, 3]})
    ts.set_meter_readers(sim, meters=['Electricity:HVAC'])
    sim.set_problem(minimize_outputs=[True])

    estimate = sim.estimate_optimisation_sims(
        evaluations=10,
        population_size=5,
        epws=ts.TEST_CATEGORIES['medium']['epws']
    )

    ts.log_test("Estimate Sims", "PASS" if estimate is not None else "FAIL",
             f"Estimated sims: {estimate}")
    # NSGA-II: 5 iniciales + 6 hijos (5 redondeado a par) por EPW
    assert estimate == (5 + 6) * 2

if __name__ == '__main__':
    test_optimization_basic()
    test_optimization_all_algorithms()
    test_optimization_particle_swarm()
    test_optimization_multi_epw()
    test_optimization_keep_sim_files()
    test_optimization_estimate_sims()
