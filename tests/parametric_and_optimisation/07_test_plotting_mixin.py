# 07_test_plotting_mixin.py
"""
Test de PlottingMixin.
Cubre: Plots de optimization, best compromise solutions (MCDM), etc.
"""

from .. import test_setup as ts

def test_plot_pareto_front():
    """Test: Plotear Pareto front."""
    ts.print_section("TEST: Plot Pareto Front")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1], 'HVACmode': [0, 2]})
    sim.set_problem(minimize_outputs=['HVAC energy', 'PPD'])

    sim.run_optimisation(
        out_dir='./test_plot_pareto',
        algorithm='NSGAII',
        evaluations=4,
        population_size=2,
        processes=1
    )

    try:
        sim.plot_pareto_front(out_dir='./test_plot_pareto')
        ts.log_test("Plot Pareto Front", "PASS")
    except Exception as e:
        ts.log_test("Plot Pareto Front", "FAIL", str(e))

def test_plot_best_compromise_solutions():
    """Test: Plotear soluciones best compromise (MCDM)."""
    ts.print_section("TEST: Plot Best Compromise Solutions (MCDM)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
        parameters_type='accim predefined model'
    )

    sim.set_parameters(accis_params_dict={'ComfStand': [0, 1], 'HVACmode': [0, 2]})
    sim.set_problem(minimize_outputs=['HVAC energy', 'PPD'])

    sim.run_optimisation(
        out_dir='./test_plot_best_compromise',
        algorithm='NSGAII',
        evaluations=4,
        population_size=2,
        processes=1
    )

    try:
        best_solutions = sim.plot_best_compromise_solutions(
            out_dir='./test_plot_best_compromise',
            mcdm_configs=[
                {'method': 'knee_point'},
                {'method': 'topsis'}
            ]
        )
        ts.log_test("Plot Best Compromise", "PASS" if len(best_solutions) > 0 else "FAIL",
                 f"Solutions: {len(best_solutions)}")
    except Exception as e:
        ts.log_test("Plot Best Compromise", "FAIL", str(e))

if __name__ == '__main__':
    test_plot_pareto_front()
    test_plot_best_compromise_solutions()
