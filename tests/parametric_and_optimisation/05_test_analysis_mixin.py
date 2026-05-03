# 05_test_analysis_mixin.py
"""
Test de AnalysisMixin.
Cubre: Sensitivity Analysis (Morris, Sobol), MCDM,
building floor area, hourly/monthly df generation.
"""

from .. import test_setup as ts

def test_set_building_floor_area():
    """Test: Set floor area para normalización."""
    ts.print_section("TEST: Set Building Floor Area")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    # Test mode='all'
    area_all = sim.set_building_floor_area(mode='all')
    ts.log_test("Floor Area (mode='all')", "PASS" if area_all > 0 else "FAIL",
             f"Area: {area_all} m²")

    # Test mode='custom'
    area_custom = sim.set_building_floor_area(mode='custom', custom_area=500.0)
    ts.log_test("Floor Area (mode='custom')", "PASS" if area_custom == 500.0 else "FAIL",
             f"Area: {area_custom} m²")

def test_get_hourly_df():
    """Test: Generar DataFrame horario."""
    ts.print_section("TEST: Get Hourly DataFrame")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0]})
    sim.set_problem()
    sim.sampling_full_set()

    sim.run_parametric_simulation(
        out_dir='./test_hourly_df',
        processes=1
    )

    sim.get_hourly_df()

    ts.log_test("Get Hourly DF", "PASS" if sim.outputs_param_simulation_hourly is not None else "FAIL",
             f"Shape: {sim.outputs_param_simulation_hourly.shape if sim.outputs_param_simulation_hourly is not None else 'N/A'}")

def test_get_monthly_df():
    """Test: Generar DataFrame mensual."""
    ts.print_section("TEST: Get Monthly DataFrame")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0]})
    sim.set_problem()
    sim.sampling_full_set()

    sim.run_parametric_simulation(
        out_dir='./test_monthly_df',
        processes=1
    )

    sim.get_monthly_df()

    ts.log_test("Get Monthly DF", "PASS" if sim.outputs_param_simulation_monthly is not None else "FAIL",
             f"Shape: {sim.outputs_param_simulation_monthly.shape if sim.outputs_param_simulation_monthly is not None else 'N/A'}")

def test_sensitivity_analysis_morris():
    """Test: Análisis de sensibilidad Morris."""
    ts.print_section("TEST: Sensitivity Analysis - Morris")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [[70, 90]], 'ComfMod': [[2, 4]]})
    sim.set_problem(minimize_outputs=['HVAC energy'])
    sim.sampling_morris(num_samples=2, num_levels=4)

    sim.run_parametric_simulation(
        out_dir='./test_sa_morris',
        processes=1
    )

    sim.run_sensitivity_analysis_by_epw(method='morris', out_dir='./test_sa_morris_results')

    ts.log_test("SA Morris", "PASS" if hasattr(sim, 'sa_results') else "FAIL")

def test_sensitivity_analysis_sobol():
    """Test: Análisis de sensibilidad Sobol."""
    ts.print_section("TEST: Sensitivity Analysis - Sobol")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'CAT': [[70, 90]], 'ComfMod': [[2, 4]]})
    sim.set_problem(minimize_outputs=['HVAC energy'])
    sim.sampling_sobol(num_samples=32)

    sim.run_parametric_simulation(
        out_dir='./test_sa_sobol',
        processes=1
    )

    sim.run_sensitivity_analysis_by_epw(method='sobol', out_dir='./test_sa_sobol_results')

    ts.log_test("SA Sobol", "PASS" if hasattr(sim, 'sa_results') else "FAIL")

if __name__ == '__main__':
    test_set_building_floor_area()
    test_get_hourly_df()
    test_get_monthly_df()
    test_sensitivity_analysis_morris()
    test_sensitivity_analysis_sobol()
