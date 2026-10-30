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

            sim.set_parameters(accis_params_dict={'CAT': [1, 2, 3]})
            ts.set_meter_readers(sim, meters=['Electricity:HVAC'])
            sim.set_problem(minimize_outputs=[True])

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
    test_optimization_multi_epw()
    test_optimization_keep_sim_files()
    test_optimization_estimate_sims()
