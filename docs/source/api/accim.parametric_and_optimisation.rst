accim.parametric\_and\_optimisation package
===========================================

Choosing an API
---------------

Use ``ParametricSimulation`` or ``OptimisationSimulation`` for general studies.
Their inherited :meth:`~accim.parametric_and_optimisation.main.SimulationBase.add_comfort_metrics`
method adds independent reporting outputs, not optimisation objectives;
readers and reducers remain explicit choices. The strict reducer is
:func:`~accim.parametric_and_optimisation.objectives.checked_sum_results`.

:func:`~accim.parametric_and_optimisation.paper_experiments.run_paper_experiment`
is a separate, paper-specific convenience API for five single-zone workflows,
with its own CLI opt-in and campaign-review requirements. Those gates are not
defaults of the general run methods. See :doc:`../comfort_metrics` for exact
signatures, return types, metric definitions and load/resume boundaries.

Subpackages
-----------

.. toctree::
   :maxdepth: 4

   accim.parametric_and_optimisation.funcs_for_besos

Submodules
----------

accim.parametric\_and\_optimisation.analysis module
---------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.analysis
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.main module
-----------------------------------------------

.. automodule:: accim.parametric_and_optimisation.main
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.objectives module
-----------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.objectives
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.paper\_experiments module
-------------------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.paper_experiments
   :members: run_paper_experiment

accim.parametric\_and\_optimisation.parameters module
-----------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.parameters
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.params\_dicts module
--------------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.params_dicts
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.patches module
--------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.patches
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.plotting module
---------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.plotting
   :members:
   :show-inheritance:
   :undoc-members:

accim.parametric\_and\_optimisation.utils module
------------------------------------------------

.. automodule:: accim.parametric_and_optimisation.utils
   :members:
   :show-inheritance:
   :undoc-members:

Module contents
---------------

.. automodule:: accim.parametric_and_optimisation
   :members:
   :show-inheritance:
   :undoc-members:
