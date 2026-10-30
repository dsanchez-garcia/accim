# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""accim: Adaptive-Comfort-Control-Implemented Model.

accim transforms EnergyPlus building energy models with fixed setpoint temperatures into models with
adaptive setpoint temperatures, runs their simulations and analyses their results. See
https://accim.readthedocs.io/.

- :mod:`accim.sim`: adds the ACCIS (Adaptive-Comfort-Control Implementation Script) to the models.
- :mod:`accim.run`: runs the simulations, with the EMS of EnergyPlus or with its Python API.
- :mod:`accim.data`: analyses the results.
- :mod:`accim.parametric_and_optimisation`: parametric simulations and optimisations with besos.
"""

__version__ = '1.0.0'
