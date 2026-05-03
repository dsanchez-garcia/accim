# 04_test_optimization.py
"""
Test de run_optimisation.
Cubre: Todos los algoritmos (NSGAII, EpsMOEA, GDE3, SPEA2, MOEAD, NSGAIII,
ParticleSwarm, OMOPSO, SMPSO, CMAES, IBEA, PAES, PESA2, EpsNSGAII, etc).
"""

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
    'ParticleSwarm',
    'OMOPSO',
    'SMPSO',
    'CMAES',
    'IBEA',
    'PAES',
    'PESA2',
    'EpsNSGAII'
]

def test_optimization_basic():
    """Test: Optimization básica con NSGAII."""
    ts.print_section("TEST: Optimization - NSGAII (Basic)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1], 'HVACmode': [0, 2]})
    sim.set_problem(
        minimize_outputs=['HVAC energy', 'PPD'],
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

def test_optimization_all_algorithms():
    """Test: Todos los algoritmos disponibles."""
    ts.print_section("TEST: Optimization - All Algorithms")

    for algo in ALGORITHMS:
        print(f"\n  Testing {algo}...")
        try:
            buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
            sim = ts.OptimisationSimulation(
                buildings=buildings,
                epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
                parameters_type='accim predefined model'
            )

            sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
            sim.set_problem(minimize_outputs=['HVAC energy'])

            results = sim.run_optimisation(
                out_dir=f'./test_optim_{algo}',
                algorithm=algo,
                evaluations=2,
                population_size=2,
                processes=1
            )

            ts.log_test(f"Algorithm {algo}", "PASS" if len(results) > 0 else "FAIL",
                     f"Rows: {len(results)}")
        except Exception as e:
            ts.log_test(f"Algorithm {algo}", "FAIL", str(e))

def test_optimization_multi_epw():
    """Test: Optimization con múltiples EPWs."""
    ts.print_section("TEST: Optimization - Multi-EPW")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:2],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    sim.set_problem(minimize_outputs=['HVAC energy'])

    results = sim.run_optimisation(
        out_dir='./test_optim_multi_epw',
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1
    )

    ts.log_test("Optimization Multi-EPW", "PASS" if 'epw' in results.columns else "FAIL",
             f"EPWs in results: {results['epw'].nunique()}")

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

        sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
        sim.set_problem(minimize_outputs=['HVAC energy'])

        results = sim.run_optimisation(
            out_dir=f'./test_optim_keep_{keep_option}',
            algorithm='NSGAII',
            evaluations=2,
            population_size=2,
            keep_sim_files=keep_option,
            processes=1
        )

        ts.log_test(f"Keep Files ({keep_option})", "PASS" if len(results) > 0 else "FAIL")

def test_optimization_estimate_sims():
    """Test: Estimar cantidad de simulaciones."""
    ts.print_section("TEST: Optimization - Estimate Simulations")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    sim.set_problem(minimize_outputs=['HVAC energy'])

    estimate = sim.estimate_optimisation_sims(
        evaluations=10,
        population_size=5,
        num_epws=2
    )

    ts.log_test("Estimate Sims", "PASS" if estimate is not None else "FAIL",
             f"Estimated sims: {estimate}")

if __name__ == '__main__':
    test_optimization_basic()
    test_optimization_all_algorithms()
    test_optimization_multi_epw()
    test_optimization_keep_sim_files()
    test_optimization_estimate_sims()
