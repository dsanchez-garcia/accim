# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The Python API of EnergyPlus (the package pyenergyplus of each EnergyPlus installation)."""

import sys
from pathlib import Path
from typing import Tuple

from accim.energyplus import find_energyplus

__all__ = ['MINIMUM_API_VERSION', 'load_energyplus_api']

#: The first EnergyPlus version whose API can read and write the variables of the EMS (getEMSGlobalVariableHandle)
MINIMUM_API_VERSION = (24, 2)


def _version_tuple(version: str) -> Tuple[int, int]:
    major, minor = str(version).split('.')[:2]
    return int(major), int(minor)


def load_energyplus_api(version: str):
    """Import pyenergyplus from the installation of an EnergyPlus version and return its EnergyPlusAPI object.

    A Python process can only load the API of one EnergyPlus version, since every version has a package
    named pyenergyplus. :func:`accim.sim.energyplus_api.run_simulations` runs each simulation in its own
    process, so it can run models of different versions.

    :param version: The EnergyPlus version, such as '25.1'.
    :raises ValueError: If the version is older than 24.2, whose API cannot read and write the variables of the EMS.
    :raises FileNotFoundError: If the version is not installed.
    :raises RuntimeError: If this process has already loaded the API of another version.
    """
    if _version_tuple(version) < MINIMUM_API_VERSION:
        raise ValueError(f'The Python API backend needs EnergyPlus 24.2 or later (whose API can read and write the '
                         f'variables of the EMS), and the model is of EnergyPlus {version}. Run it with the EMS '
                         f'backend, or update it with the transition programs of EnergyPlus '
                         f'(accim.utils.update_idf_version).')
    folder = find_energyplus(version)
    loaded = sys.modules.get('pyenergyplus')
    if loaded is not None:
        loaded_folder = Path(loaded.__file__).resolve().parent.parent
        if loaded_folder != folder.resolve():
            raise RuntimeError(
                f'This Python process has already loaded the Python API of the EnergyPlus in {loaded_folder}, and a '
                f'process can only load one version. Run the models of EnergyPlus {version} in another process '
                f'(accim.sim.energyplus_api.run_simulations runs each model in its own process).'
            )
    elif str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    from pyenergyplus.api import EnergyPlusAPI
    return EnergyPlusAPI()
