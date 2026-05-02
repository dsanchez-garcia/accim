"""
Parametric and Optimization Module

This module provides classes for running parametric simulations and multi-objective
optimization on EnergyPlus building energy models with adaptive thermal comfort setpoints.

Main Classes:
- ParametricSimulation: For parameter sampling and multi-run simulations
- OptimizationSimulation: For multi-objective optimization
- OptimParamSimulation: Backward-compatibility alias (deprecated, use ParametricSimulation)
- AccimPredefModelsParamSim: Convenience wrapper for ACCIM predefined models

Usage Examples:

    # Parametric simulation
    from accim.parametric_and_optimisation.main import ParametricSimulation

    parametric = ParametricSimulation(
        building=my_idf,
        epws=['weather.epw'],
        parameters_type='accim custom model'
    )
    parametric.set_parameters(accis_params_dict={'ComfStand': [0, 1, 2]})
    parametric.sampling_lhs(num_samples=10)
    results = parametric.run_parametric_simulation()

    # Multi-objective optimization
    from accim.parametric_and_optimisation.main import OptimizationSimulation

    optim = OptimizationSimulation(
        building=my_idf,
        epws=['weather.epw'],
        parameters_type='accim custom model'
    )
    optim.set_parameters(accis_params_dict={'ComfStand': (0, 2), 'HVACmode': (0, 2)})
    optim.set_problem(minimize_outputs=[True, False])
    results = optim.run_optimisation(algorithm='NSGAII', evaluations=50)

.. versionadded:: 0.8.0
    Split OptimParamSimulation into ParametricSimulation and OptimizationSimulation
    for improved code organization and clarity.
"""

from .main import (
    ParametricSimulation,
    OptimizationSimulation,
    OptimParamSimulation,  # Backward compatibility
    AccimPredefModelsParamSim,
    SimulationBase,
)

__all__ = [
    'ParametricSimulation',
    'OptimizationSimulation',
    'OptimParamSimulation',
    'AccimPredefModelsParamSim',
    'SimulationBase',
]
