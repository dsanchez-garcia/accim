"""Tests for set_problem() without output readers.

set_problem() builds the besos problem from the parameters and the output readers of set_output_readers(). The
readers only existed after set_output_readers(), so set_problem() failed with an AttributeError ('sim_outputs')
when the outputs had not been set, for instance to build a problem only to sample the parameters. Ported from
the tests of the branches refactor/sim-v1 and review/refactor-sim-v1-20261024.
"""
import pandas as pd
import pytest

from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation


@pytest.mark.parametrize('simulation_type', [ParametricSimulation, OptimisationSimulation])
def test_the_problem_can_be_built_without_output_readers(simulation_type):
    simulation = simulation_type()
    assert simulation.sim_outputs is None

    simulation.set_parameters()
    simulation.set_problem()

    assert simulation.problem.outputs == []


@pytest.mark.parametrize('simulation_type', [ParametricSimulation, OptimisationSimulation])
def test_the_output_readers_are_still_the_outputs_of_the_problem(simulation_type):
    simulation = simulation_type()
    simulation.set_parameters()
    simulation.set_output_readers(df_output_meter=pd.DataFrame([{
        'key_name': 'Electricity:Facility', 'frequency': 'Hourly', 'name': 'energy',
    }]))

    simulation.set_problem(minimize_outputs=[True])

    assert simulation.problem.names('outputs') == ['energy']
    assert simulation.problem.minimize_outputs == [True]


def test_empty_output_readers_belong_to_their_instance():
    configured = ParametricSimulation()
    configured.set_output_readers()
    configured.set_parameters()
    configured.set_problem()

    assert configured.sim_outputs == []
    assert configured.problem.outputs == []
    assert ParametricSimulation().sim_outputs is None
