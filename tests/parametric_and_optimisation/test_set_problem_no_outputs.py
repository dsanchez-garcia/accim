"""Preserve the useful sim-v1 fix without adopting its obsolete public API."""

import pandas as pd
import pytest

from accim.parametric_and_optimisation import OptimisationSimulation, ParametricSimulation


@pytest.mark.parametrize('simulation_type', [ParametricSimulation, OptimisationSimulation])
def test_problem_can_be_configured_without_output_readers(simulation_type):
    simulation = simulation_type()
    assert simulation.sim_outputs is None
    simulation.set_parameters()
    simulation.set_problem()
    assert simulation.problem.outputs == []
    # This tests problem construction, not optimisation without objectives.


@pytest.mark.parametrize('simulation_type', [ParametricSimulation, OptimisationSimulation])
def test_explicit_readers_still_define_objectives(simulation_type):
    simulation = simulation_type()
    simulation.set_parameters()
    simulation.set_output_readers(df_output_meter=pd.DataFrame([{
        'key_name': 'Electricity:Facility', 'frequency': 'Hourly', 'name': 'energy',
    }]))
    simulation.set_problem(minimize_outputs=[True])
    assert simulation.problem.names('outputs') == ['energy']
    assert simulation.problem.minimize_outputs == [True]


def test_explicit_empty_readers_are_supported_and_instance_local():
    configured = ParametricSimulation()
    configured.set_output_readers()
    configured.set_parameters()
    configured.set_problem()
    assert configured.sim_outputs == []
    assert configured.problem.outputs == []
    assert ParametricSimulation().sim_outputs is None

