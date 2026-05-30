# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""In-memory (single-IDF) entry point for the ACCIS engine.

This module used to carry a full standalone copy of ``AccimJob.__init__`` that
had drifted behind the batch one in ``accim.sim.accim_Main`` (it lacked the
scheduled-ventilation detection, the ``ems_zonenames`` matching and the
SPACE-fallback guard, which caused an ``IndexError`` on existing-HVAC models
without 1:1 Space/zone mapping).

It is now a thin in-memory constructor over the unified engine: it skips all
disk I/O and reuses the shared, maintained ``_scan_and_setup_zones`` logic, so
the single (in-memory) path behaves exactly like the batch path. All injection
methods are inherited from the engine class.
"""

from accim.sim.engine import AccimJob as _AccimJob


class AccimJob(_AccimJob):
    """In-memory variant of the ACCIS engine.

    Takes an already-loaded eppy/besos IDF object instead of a filename and runs
    the same scanning/zone-setup as the batch path, without touching disk.
    """

    def __init__(self,
                 idf_class_instance,
                 script_type: str = None,
                 energyplus_version: str = None,
                 temp_control: str = None,
                 verbose: bool = True,
                 hvac_zone_map: dict = None):
        self.accimNotWorking = False
        self.idf1 = idf_class_instance
        self.output_idf_dict = {}
        self._scan_and_setup_zones(
            script_type=script_type,
            verbose=verbose,
            hvac_zone_map=hvac_zone_map,
            model_label=getattr(idf_class_instance, 'idfname', '') or 'in-memory IDF',
        )
