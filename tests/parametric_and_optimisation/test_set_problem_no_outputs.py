"""Regression test for the set_problem() / sim_outputs bug.

Before the fix, calling ``set_problem()`` without first calling
``set_outputs_for_simulation()`` raised a cryptic
``AttributeError: 'AccimPredefModelsParamSim' object has no attribute 'sim_outputs'``.

``sim_outputs`` now defaults to ``None`` in ``SimulationBase.__init__``, which
produces a besos ``EPProblem`` with no objectives. That is valid for a pure
parametric sweep (``run_parametric_simulation``); optimisation runs still need
``set_outputs_for_simulation()`` to define objectives.
"""

from .. import test_setup as ts


def test_set_problem_without_outputs_uses_no_objectives():
    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'][:1])
    sim = ts.AccimPredefModelsParamSim(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'][:1],
    )

    # sim_outputs must exist (and default to None) right after construction.
    assert sim.sim_outputs is None

    sim.set_parameters()
    # This call used to raise AttributeError before the fix.
    sim.set_problem()

    assert sim.problem is not None
    # No objectives were configured, so the problem has zero outputs.
    assert len(sim.problem.outputs) == 0
