# 03_test_parametric_run.py
"""
Test de run_parametric_simulation.
Cubre: diferentes parámetros, multi-EPW, multi-IDF, outputs, keep_dirs, keep_input.
"""

from .. import test_setup as ts

def test_parametric_basic():
    """Test: Parametric básico con 1 IDF, 1 EPW."""
    ts.print_section("TEST: Parametric - Basic (1 IDF, 1 EPW)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model',
        output_freqs=['hourly', 'monthly']
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_basic',
        processes=1,
        keep_input=True,
        keep_dirs=False
    )

    ts.log_test("Parametric Basic", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) > 0
    assert hasattr(sim, 'outputs_param_simulation')

def test_parametric_multi_epw():
    """Test: Parametric con múltiples EPWs."""
    ts.print_section("TEST: Parametric - Multi-EPW")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:2],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0]})
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_multi_epw',
        processes=1
    )

    ts.log_test("Parametric Multi-EPW", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows, EPW column present: {'epw' in results.columns}")
    assert 'epw' in results.columns

def test_parametric_multi_idf():
    """Test: Parametric con múltiples IDFs."""
    ts.print_section("TEST: Parametric - Multi-IDF")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0]})
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_multi_idf',
        processes=1
    )

    ts.log_test("Parametric Multi-IDF", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows, IDF column present: {'idf' in results.columns}")
    assert 'idf' in results.columns

def test_parametric_output_types():
    """Test: Diferentes output_type."""
    ts.print_section("TEST: Parametric - Output Types")

    for output_type in ['standard', 'detailed', 'simplified']:
        buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
        sim = ts.ParametricSimulation(
            buildings=buildings,
            epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
            parameters_type='accim predefined model',
            output_type=output_type
        )

        sim.set_parameters(accis_params_dict={'ComfStand': [0]})
        sim.set_problem()
        sim.sampling_full_set()

        results = sim.run_parametric_simulation(
            out_dir=f'./test_param_output_{output_type}',
            processes=1
        )

        ts.log_test(f"Parametric Output ({output_type})", "PASS" if len(results) > 0 else "FAIL",
                 f"Columns: {len(results.columns)}")

def test_parametric_apmv():
    """Test: Parametric con APMV setpoints."""
    ts.print_section("TEST: Parametric - APMV Setpoints")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='apmv setpoints'
    )

    sim.set_parameters(apmv_params_dict={'temp_offset': [-2, 0, 2]})
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_apmv',
        processes=1
    )

    ts.log_test("Parametric APMV", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) > 0

def test_parametric_with_custom_outputs():
    """Test: Parametric con outputs personalizados."""
    ts.print_section("TEST: Parametric - Custom Outputs")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model',
        output_type='custom'
    )

    # Get test sim outputs first
    outputs_from_testsim = sim.get_outputs_df_from_testsim(reduce_sim_time=True)
    df_meters = outputs_from_testsim['meters']
    df_vars = outputs_from_testsim['variables']

    # Filter metros
    df_meters_filtered = df_meters[df_meters['key_name'].str.contains('Heating|Cooling', na=False)]
    sim.set_outputs_for_simulation(df_output_meter=df_meters_filtered)

    sim.set_parameters(accis_params_dict={'ComfStand': [0]})
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_custom_outputs',
        processes=1
    )

    ts.log_test("Parametric Custom Outputs", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) > 0

if __name__ == '__main__':
    test_parametric_basic()
    test_parametric_multi_epw()
    test_parametric_multi_idf()
    test_parametric_output_types()
    test_parametric_apmv()
    test_parametric_with_custom_outputs()
