# 06_test_data_loading.py
"""
Test de load_outputs_parametric y load_outputs_optimisation.
Cubre: CSV, Pickle, JSON, hourly/pickle recovery.
"""

from .. import test_setup as ts

def test_load_parametric_csv():
    """Test: Cargar outputs parametricos desde CSV."""
    ts.print_section("TEST: Load Parametric - CSV")

    # Primero generar outputs
    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim1 = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim1.set_parameters(accis_params_dict={'category': [1, 2]})
    ts.set_meter_readers(sim1)
    sim1.set_problem()
    sim1.sampling_full_set()

    results1 = sim1.run_parametric_simulation(
        out_dir='./test_load_param_csv',
        processes=1
    )

    # Ahora cargar en una nueva instancia
    sim2 = ts.ParametricSimulation(
        buildings=ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1]),
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model',
        bypass_add_accis=True
    )

    csv_path = ts.latest_output('./test_load_param_csv', 'outputs_param_simulation', 'csv')
    results2 = sim2.load_outputs_parametric(csv_path=csv_path)

    ts.log_test("Load Parametric CSV", "PASS" if len(results2) > 0 else "FAIL",
             f"Loaded rows: {len(results2)}")
    assert len(results2) == len(results1) == 2

def test_load_parametric_pickle():
    """Test: Cargar outputs parametricos desde Pickle."""
    ts.print_section("TEST: Load Parametric - Pickle")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim1 = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim1.set_parameters(accis_params_dict={'category': [1, 2]})
    ts.set_meter_readers(sim1)
    sim1.set_problem()
    sim1.sampling_full_set()

    sim1.run_parametric_simulation(
        out_dir='./test_load_param_pickle',
        processes=1
    )

    sim2 = ts.ParametricSimulation(
        buildings=ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1]),
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model',
        bypass_add_accis=True
    )

    pickle_path = ts.latest_output('./test_load_param_pickle', 'outputs_param_simulation', 'pkl')
    results = sim2.load_outputs_parametric(pickle_path=pickle_path)

    ts.log_test("Load Parametric Pickle", "PASS" if len(results) > 0 else "FAIL",
             f"Loaded rows: {len(results)}")
    assert len(results) == 2

def test_load_optimization_csv():
    """Test: Cargar outputs optimización desde CSV."""
    ts.print_section("TEST: Load Optimization - CSV")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim1 = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim1.set_parameters(accis_params_dict={'category': [1, 2, 3]})
    ts.set_meter_readers(sim1, meters=['Electricity:HVAC'])
    sim1.set_problem(minimize_outputs=[True])

    sim1.run_optimisation(
        out_dir='./test_load_optim_csv',
        algorithm='NSGAII',
        evaluations=2,
        population_size=2,
        processes=1
    )

    sim2 = ts.OptimisationSimulation(
        buildings=ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1]),
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model',
        bypass_add_accis=True
    )

    csv_path = ts.latest_output('./test_load_optim_csv', 'outputs_optimisation', 'csv')
    results = sim2.load_outputs_optimisation(csv_path=csv_path)

    ts.log_test("Load Optimization CSV", "PASS" if len(results) > 0 else "FAIL",
             f"Loaded rows: {len(results)}")
    assert len(results) > 0

if __name__ == '__main__':
    test_load_parametric_csv()
    test_load_parametric_pickle()
    test_load_optimization_csv()
