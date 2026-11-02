# 03_test_parametric_run.py
"""
Test de run_parametric_simulation.
Cubre: diferentes parámetros, multi-EPW, multi-IDF, outputs, keep_dirs, keep_input.
"""

from accim.sim import apmv

from .. import test_setup as ts

def test_parametric_basic():
    """Test: Parametric básico con 1 IDF, 1 EPW."""
    ts.print_section("TEST: Parametric - Basic (1 IDF, 1 EPW)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model',
        output_frequencies=['hourly', 'monthly']
    )

    sim.set_parameters(accis_params_dict={'comfort_standard': [1, 2], 'category': [1, 80], 'comfort_mode': [3]})
    meters = ts.set_meter_readers(sim)
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
    assert len(results) == 2
    assert hasattr(sim, 'outputs_param_simulation')
    # Los dos modelos de confort dan resultados (consumo de los sistemas VRF) distintos
    assert (results[meters].notna().all().all()) and (results[meters] >= 0).all().all()
    assert results['Cooling:Electricity'].nunique() == 2

def test_parametric_multi_epw():
    """Test: Parametric con múltiples EPWs."""
    ts.print_section("TEST: Parametric - Multi-EPW")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'comfort_mode': [3]})
    ts.set_meter_readers(sim)
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_multi_epw',
        processes=1
    )

    ts.log_test("Parametric Multi-EPW", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows, EPW column present: {'epw' in results.columns}")
    assert 'epw' in results.columns
    assert len(results) == 2

def test_parametric_multi_idf():
    """Test: Parametric con múltiples IDFs."""
    ts.print_section("TEST: Parametric - Multi-IDF")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'comfort_mode': [3]})
    ts.set_meter_readers(sim)
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_multi_idf',
        processes=1
    )

    ts.log_test("Parametric Multi-IDF", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows, IDF column present: {'idf' in results.columns}")
    assert 'idf' in results.columns
    assert len(results) == 2

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

        sim.set_parameters(accis_params_dict={'comfort_mode': [3]})
        ts.set_meter_readers(sim)
        sim.set_problem()
        sim.sampling_full_set()

        results = sim.run_parametric_simulation(
            out_dir=f'./test_param_output_{output_type}',
            processes=1
        )

        ts.log_test(f"Parametric Output ({output_type})", "PASS" if len(results) > 0 else "FAIL",
                 f"Columns: {len(results.columns)}")
        assert len(results) == 1
        assert results[ts.METERS].notna().all().all()

def test_parametric_apmv():
    """Test: Parametric con APMV setpoints."""
    ts.print_section("TEST: Parametric - APMV Setpoints")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    for building in buildings:
        apmv.add_vrf_system(building=building, verbose=False)
        apmv.set_pmv_input_parameters(building, clothing_insulation=0.5, air_velocity=0.1, work_efficiency=0.0,
                                      verbose=False)
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='apmv setpoints'
    )

    sim.set_parameters(accis_params_dict={'adaptive_coefficient': [0.0, 0.9], 'pmv_setpoint': [0.5]})
    ts.set_meter_readers(sim)
    sim.set_problem()
    sim.sampling_full_set()

    results = sim.run_parametric_simulation(
        out_dir='./test_param_apmv',
        processes=1
    )

    ts.log_test("Parametric APMV", "PASS" if len(results) > 0 else "FAIL",
             f"Results: {len(results)} rows")
    assert len(results) == 2
    assert results[ts.METERS].notna().all().all()

def test_parametric_with_custom_outputs():
    """Test: Parametric con outputs personalizados."""
    ts.print_section("TEST: Parametric - Custom Outputs")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model',
    )

    # Get test sim outputs first
    outputs_from_testsim = sim.discover_available_outputs(reduce_sim_time=True)
    df_meters = outputs_from_testsim['meters']
    df_vars = outputs_from_testsim['variables']

    # Filter metros
    df_meters_filtered = df_meters[df_meters['key_name'].isin(ts.METERS)].drop_duplicates(subset=['key_name'])
    assert sorted(df_meters_filtered['key_name']) == sorted(ts.METERS)
    sim.set_output_meters_to_idf(df_output_meter=df_meters_filtered, validate=False)
    sim.set_output_readers(df_output_meter=df_meters_filtered)

    sim.set_parameters(accis_params_dict={'comfort_mode': [3]})
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
