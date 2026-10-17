"""
Parametric and Optimization Module

This module provides classes for running parametric simulations and multi-objective
optimization on EnergyPlus building energy models with adaptive thermal comfort setpoints.

Main Classes:

- ParametricSimulation: For parameter sampling and multi-run simulations
- OptimisationSimulation: For multi-objective optimization
- AccimPredefModelsParamSim: Convenience wrapper for ACCIM predefined models

The page "Overview of parametric simulation and optimisation" of the documentation
explains each step. Usage Examples::

    from besos import eppy_funcs as ef
    from accim.parametric_and_optimisation.objectives import sum_results

    building = ef.get_building('my_model.idf')

    # Parametric simulation
    from accim.parametric_and_optimisation.main import ParametricSimulation

    parametric = ParametricSimulation(
        buildings=[building],
        epws=['weather.epw'],
        parameters_type='accim custom model',
    )
    meters = parametric.select_outputs(meters=['Electricity:HVAC'])['meters']
    parametric.apply_outputs_preflight(df_meters_sel=meters, clean_mode='all')
    meters['func'] = [sum_results] * len(meters)
    parametric.set_output_readers(df_output_meter=meters)
    parametric.set_parameters(accis_params_dict={'CustAST_m': (0.2, 0.6), 'CustAST_n': (15, 21)})
    parametric.set_problem()
    parametric.sampling_lhs(num_samples=10)
    results = parametric.run_parametric_simulation(out_dir='param_results', processes=2)

    # Multi-objective optimization (outputs and readers set as above,
    # one reader per objective)
    from accim.parametric_and_optimisation.main import OptimisationSimulation

    optim = OptimisationSimulation(
        buildings=[building],
        epws=['weather.epw'],
        parameters_type='accim custom model',
    )
    ...
    optim.set_parameters(accis_params_dict={'CustAST_m': (0.2, 0.6), 'CustAST_ASToffset': (2, 4)})
    optim.set_problem(minimize_outputs=[True, True])
    results = optim.run_optimisation(algorithm='NSGAII', population_size=20, evaluations=60)

.. versionadded:: 0.8.0
    Introduced dedicated ParametricSimulation and OptimisationSimulation
    classes for improved code organization and clarity.
"""

from .main import (
    ParametricSimulation,
    OptimisationSimulation,
    AccimPredefModelsParamSim,
    SimulationBase,
    SimulationComparisonSession,
    compare_simulation_instances,
    compare_latest_pickles_in_folders,
    compare_multiple_pickles_with_reference,
    preflight_report,
)
from .hourly_plotting import (
    HourlyPlottingMixin,
    adaptive_comfort_band,
    comfort_categories,
    read_epw_dry_bulb,
    running_mean_outdoor_temperature,
)

__all__ = [
    'ParametricSimulation',
    'OptimisationSimulation',
    'AccimPredefModelsParamSim',
    'SimulationBase',
    'SimulationComparisonSession',
    'compare_simulation_instances',
    'compare_latest_pickles_in_folders',
    'compare_multiple_pickles_with_reference',
    'preflight_report',
    'HourlyPlottingMixin',
    'adaptive_comfort_band',
    'comfort_categories',
    'read_epw_dry_bulb',
    'running_mean_outdoor_temperature',
]
