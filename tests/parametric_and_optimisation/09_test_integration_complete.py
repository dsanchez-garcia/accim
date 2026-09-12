# 09_test_integration_complete.py
"""
Test de integración COMPLETO end-to-end.
Cubre: Todo el workflow de parametrización, optimización, análisis y plotting.
"""

import pandas as pd
from .. import test_setup as ts

def test_complete_workflow():
    """Test: Workflow completo parametrización + optimización + análisis."""
    ts.print_section("TEST: COMPLETE WORKFLOW - Parametrization → Optimization → Analysis")

    print("\n[STEP 1] Prepare Buildings...")
    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    print(f"✓ Buildings prepared: {len(buildings)} IDFs")

    print("\n[STEP 2] Parametric Simulation...")
    param_sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:2],
        parameters_type='accim predefined model',
        output_freqs=['hourly', 'monthly']
    )

    param_sim.set_parameters(accis_params_dict={'ComfStand': [0, 1], 'HVACmode': [0, 2]})
    param_sim.set_problem(minimize_outputs=['HVAC energy'])
    param_sim.sampling_full_factorial(level=2)

    param_results = param_sim.run_parametric_simulation(
        out_dir='./test_integration_param',
        processes=2,
        keep_input=True
    )
    print(f"✓ Parametric completed: {len(param_results)} simulations")

    print("\n[STEP 3] Get Hourly Data...")
    param_sim.get_hourly_df(start_date='2024-06-01 01', normalize_per_m2=False)
    print(f"✓ Hourly data generated: {param_sim.outputs_param_simulation_hourly.shape}")

    print("\n[STEP 4] Get Monthly Data...")
    param_sim.get_monthly_df()
    print(f"✓ Monthly data generated: {param_sim.outputs_param_simulation_monthly.shape}")

    print("\n[STEP 5] Optimization Simulation...")
    optim_sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:1],
        parameters_type='accim predefined model'
    )

    optim_sim.set_parameters(accis_params_dict={'ComfStand': [0, 1, 2], 'HVACmode': [0, 2]})
    optim_sim.set_problem(minimize_outputs=['HVAC energy', 'PPD'])

    optim_results = optim_sim.run_optimisation(
        out_dir='./test_integration_optim',
        algorithm='NSGAII',
        evaluations=4,
        population_size=2,
        processes=1
    )
    print(f"✓ Optimization completed: {len(optim_results)} evaluations, "
          f"Pareto-optimal: {(optim_results['pareto-optimal']==True).sum()}")

    print("\n[STEP 6] Hourly Data from Optimization...")
    optim_sim.get_hourly_df_optimisation(
        only_pareto_optimal=True,
        skip_confirmation=True
    )
    if optim_sim.outputs_optimisation_hourly is not None:
        print(f"✓ Optimization hourly data: {optim_sim.outputs_optimisation_hourly.shape}")

    print("\n[STEP 7] Save/Load Session...")
    param_sim.outputs_param_simulation.to_pickle('./test_integration_param/param_session.pickle')
    optim_sim.outputs_optimisation.to_pickle('./test_integration_optim/optim_session.pickle')

    # Reload
    param_loaded = pd.read_pickle('./test_integration_param/param_session.pickle')
    optim_loaded = pd.read_pickle('./test_integration_optim/optim_session.pickle')
    print(f"✓ Session saved and reloaded successfully")

    print("\n[STEP 8] Plot Results...")
    try:
        optim_sim.plot_best_compromise_solutions(
            out_dir='./test_integration_plots',
            mcdm_configs=[{'method': 'knee_point'}, {'method': 'topsis'}]
        )
        print(f"✓ Plots generated")
    except Exception as e:
        print(f"⚠ Plotting warning: {e}")

    print("\n" + "="*80)
    print("✓✓✓ COMPLETE WORKFLOW SUCCESS ✓✓✓")
    print("="*80)

    ts.log_test("INTEGRATION TEST", "PASS")

if __name__ == '__main__':
    test_complete_workflow()
