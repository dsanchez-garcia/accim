# 02_test_parametric_sampling.py
"""
Test de todas las estrategias de muestreo (sampling_*).
Cubre: LHS, Sobol, Morris, Full Set, Full Factorial, Custom.
"""

from .. import test_setup as ts

def test_sampling_full_set():
    """Test: Muestreo full set (todas las combinaciones sin evaluación)."""
    ts.print_section("TEST: Sampling - Full Set")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    df_var = sim.get_output_var_df_from_idf()
    df_meter = sim.get_output_meter_df_from_idf()
    if not df_var.empty:
        df_var = df_var.rename(columns={'reporting_frequency': 'frequency'})
    if not df_meter.empty:
        df_meter = df_meter.rename(columns={'reporting_frequency': 'frequency'})
    sim.set_outputs_for_simulation(df_output_meter=df_meter, df_output_variable=df_var)
    sim.set_problem()
    sim.sampling_full_set()

    ts.log_test("Full Set Sampling", "PASS" if sim.parameters_values_df is not None else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert sim.parameters_values_df is not None

def test_sampling_lhs():
    """Test: Latin Hypercube Sampling (LHS)."""
    ts.print_section("TEST: Sampling - LHS")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [70, 90]})  # Rango
    df_var = sim.get_output_var_df_from_idf()
    df_meter = sim.get_output_meter_df_from_idf()
    if not df_var.empty:
        df_var = df_var.rename(columns={'reporting_frequency': 'frequency'})
    if not df_meter.empty:
        df_meter = df_meter.rename(columns={'reporting_frequency': 'frequency'})
    sim.set_outputs_for_simulation(df_output_meter=df_meter, df_output_variable=df_var)
    sim.set_problem()
    sim.sampling_lhs(num_samples=5)

    ts.log_test("LHS Sampling", "PASS" if len(sim.parameters_values_df) == 5 else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert len(sim.parameters_values_df) == 5

def test_sampling_sobol():
    """Test: Sobol Sensitivity Analysis."""
    ts.print_section("TEST: Sampling - Sobol")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [70, 90], 'ComfMod': [2, 4]})
    df_var = sim.get_output_var_df_from_idf()
    df_meter = sim.get_output_meter_df_from_idf()
    if not df_var.empty:
        df_var = df_var.rename(columns={'reporting_frequency': 'frequency'})
    if not df_meter.empty:
        df_meter = df_meter.rename(columns={'reporting_frequency': 'frequency'})
    sim.set_outputs_for_simulation(df_output_meter=df_meter, df_output_variable=df_var)
    sim.set_problem()
    sim.sampling_sobol(num_samples=64)

    ts.log_test("Sobol Sampling", "PASS" if len(sim.parameters_values_df) > 0 else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert len(sim.parameters_values_df) > 0

def test_sampling_morris():
    """Test: Morris Sensitivity Analysis."""
    ts.print_section("TEST: Sampling - Morris")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [70, 90], 'ComfMod': [2, 4]})
    df_var = sim.get_output_var_df_from_idf()
    df_meter = sim.get_output_meter_df_from_idf()
    if not df_var.empty:
        df_var = df_var.rename(columns={'reporting_frequency': 'frequency'})
    if not df_meter.empty:
        df_meter = df_meter.rename(columns={'reporting_frequency': 'frequency'})
    sim.set_outputs_for_simulation(df_output_meter=df_meter, df_output_variable=df_var)
    sim.set_problem()
    sim.sampling_morris(num_samples=2, num_levels=4)  # Pequeño para testing rápido

    ts.log_test("Morris Sampling", "PASS" if len(sim.parameters_values_df) > 0 else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert len(sim.parameters_values_df) > 0

def test_sampling_full_factorial():
    """Test: Full Factorial Design."""
    ts.print_section("TEST: Sampling - Full Factorial")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1], 'HVACmode': [0, 2]})
    df_var = sim.get_output_var_df_from_idf()
    df_meter = sim.get_output_meter_df_from_idf()
    if not df_var.empty:
        df_var = df_var.rename(columns={'reporting_frequency': 'frequency'})
    if not df_meter.empty:
        df_meter = df_meter.rename(columns={'reporting_frequency': 'frequency'})
    sim.set_outputs_for_simulation(df_output_meter=df_meter, df_output_variable=df_var)
    sim.set_problem()
    sim.sampling_full_factorial(level=2)

    ts.log_test("Full Factorial Sampling", "PASS" if len(sim.parameters_values_df) == 4 else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert len(sim.parameters_values_df) == 4

def test_sampling_custom_list_of_dicts():
    """Test: Custom Sampling - List of dicts."""
    ts.print_section("TEST: Sampling - Custom (List of Dicts)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    sim.set_problem()

    custom_plan = [
        {'ComfStand': 0},
        {'ComfStand': 1}
    ]
    sim.sampling_custom(custom_plan)

    ts.log_test("Custom Sampling (Dicts)", "PASS" if len(sim.parameters_values_df) == 2 else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert len(sim.parameters_values_df) == 2

def test_sampling_custom_multi_idf_epw():
    """Test: Custom Sampling - Multi-IDF/EPW mapping."""
    ts.print_section("TEST: Sampling - Custom (Multi IDF/EPW Mapping)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1]})
    sim.set_problem()

    # Mapeo personalizado: IDF_B con seville, IDF_D con madrid
    custom_plan = {
        'SF_Detached_B_min_North': ['seville_2024.epw'],
        'SF_Detached_D_min_North': ['madrid_2024.epw']
    }
    sim.sampling_custom(custom_plan)

    ts.log_test("Custom Sampling (Multi IDF/EPW)", "PASS" if len(sim.parameters_values_df) > 0 else "FAIL",
             f"Samples: {len(sim.parameters_values_df)}")
    assert len(sim.parameters_values_df) > 0

if __name__ == '__main__':
    test_sampling_full_set()
    test_sampling_lhs()
    test_sampling_sobol()
    test_sampling_morris()
    test_sampling_full_factorial()
    test_sampling_custom_list_of_dicts()
    test_sampling_custom_multi_idf_epw()
