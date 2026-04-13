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

"""
Multi-strategy resolver that maps existing HVAC object names to zone names.

Used by ScriptType='ex_mm' and 'ex_ac' to determine which zone each HVAC
object (coil, baseboard, terminal unit, etc.) belongs to, so that the correct
EMS sensors and programs can be generated.

Four cascaded strategies are applied in order for each HVAC object:

  A – Manual map supplied by the user via ``hvac_zone_map`` argument.
  B – Reading the ``Zone_Name`` field directly from objects that carry it
      (e.g. ``ZoneHVAC:Baseboard:*``, ``AirTerminal:…:CooledBeam``).
  C1 – Traversal through ``ZoneHVAC:EquipmentList`` /
       ``ZoneHVAC:EquipmentConnections`` after locating the HVAC object
       inside a ``ZoneHVAC`` container.
  C2 – Traversal through ``AirLoopHVAC`` → ``AirLoopHVAC:ZoneSplitter`` →
       ``ZoneHVAC:EquipmentConnections`` for centrally air-handled coils.
  D  – Legacy fallback: first whitespace-separated token of the object name
       (previous behaviour). Emits a ``UserWarning``.
"""

import warnings
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# EnergyPlus object types that carry a direct Zone_Name (or equivalent) field.
# Values are the eppy field name that holds the zone.
_DIRECT_ZONE_FIELD: dict[str, str] = {
    'ZoneHVAC:Baseboard:RadiantConvective:Water': 'Zone_Name',
    'ZoneHVAC:Baseboard:RadiantConvective:Steam': 'Zone_Name',
    'ZoneHVAC:Baseboard:RadiantConvective:Electric': 'Zone_Name',
    'ZoneHVAC:CoolingPanel:RadiantConvective:Water': 'Zone_Name',
    'ZoneHVAC:Baseboard:Convective:Water': 'Zone_Name',
    'ZoneHVAC:Baseboard:Convective:Electric': 'Zone_Name',
    'AirTerminal:SingleDuct:ConstantVolume:CooledBeam': 'Zone_Name',
}

# ZoneHVAC container types whose fields may reference coil objects.
# These are searched generically (all fields scanned) in strategy C1.
_ZONE_HVAC_CONTAINERS = [
    'ZoneHVAC:PackagedTerminalAirConditioner',
    'ZoneHVAC:PackagedTerminalHeatPump',
    'ZoneHVAC:WindowAirConditioner',
    'ZoneHVAC:UnitHeater',
    'ZoneHVAC:UnitVentilator',
    'ZoneHVAC:FourPipeFanCoil',
    'ZoneHVAC:EvaporativeCoolerUnit',
    'ZoneHVAC:HybridUnitaryHVAC',
    'AirLoopHVAC:UnitarySystem',
    'AirLoopHVAC:UnitaryHeatPump:AirToAir',
    'AirLoopHVAC:UnitaryHeatPump:AirToAir:MultiSpeed',
    'AirLoopHVAC:UnitaryHeatCool:VAVChangeoverBypass',
    'CoilSystem:Cooling:DX',
    'CoilSystem:Heating:DX',
    'CoilSystem:Cooling:Water',
    'CoilSystem:Cooling:Water:HeatExchangerAssisted',
    'HeatExchanger:AirToAir:SensibleAndLatent',
    'HeatExchanger:AirToAir:FlatPlate',
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _idfobjects_safe(idf, idd_type: str):
    """Return the list of IDF objects of the given type, or [] on KeyError."""
    try:
        return idf.idfobjects[idd_type]
    except KeyError:
        return []


def _field_names(obj) -> list:
    """Return all eppy field names for an object, silently handling errors."""
    try:
        return list(obj.fieldnames)
    except Exception:
        return []


def _get_field(obj, field_name: str, default=''):
    """Safely read a field from an eppy IDF object."""
    try:
        val = getattr(obj, field_name, default)
        return val if isinstance(val, str) else default
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Strategy A – manual user map
# ---------------------------------------------------------------------------

def _strategy_a(obj_name: str, user_map: Optional[Dict]) -> Optional[List[str]]:
    """Return [zone_name] if obj_name is in the user-supplied map."""
    if user_map and obj_name in user_map:
        zone = user_map[obj_name]
        return [zone] if isinstance(zone, str) else list(zone)
    return None


# ---------------------------------------------------------------------------
# Strategy B – direct Zone_Name field
# ---------------------------------------------------------------------------

def _strategy_b(idf, hvac_type: str, obj_name: str) -> Optional[List[str]]:
    """Read the Zone_Name field directly from objects that carry it."""
    if hvac_type not in _DIRECT_ZONE_FIELD:
        return None
    field = _DIRECT_ZONE_FIELD[hvac_type]
    for obj in _idfobjects_safe(idf, hvac_type):
        if obj.Name == obj_name:
            zone = _get_field(obj, field)
            if zone:
                return [zone]
    return None


# ---------------------------------------------------------------------------
# Strategy C1 – ZoneHVAC:EquipmentList traversal
# ---------------------------------------------------------------------------

def _zone_from_equipment_connections(idf, container_name: str) -> List[str]:
    """
    Given a ZoneHVAC container object name, find the zone(s) it belongs to
    by searching ZoneHVAC:EquipmentList → ZoneHVAC:EquipmentConnections.
    """
    zones: list[str] = []
    # Find every EquipmentList that references this container
    for equiplist in _idfobjects_safe(idf, 'ZoneHVAC:EquipmentList'):
        found_in_list = False
        for fname in _field_names(equiplist):
            val = _get_field(equiplist, fname)
            if val == container_name:
                found_in_list = True
                break
        if found_in_list:
            # Find EquipmentConnections that reference this EquipmentList
            for conn in _idfobjects_safe(idf, 'ZoneHVAC:EquipmentConnections'):
                if _get_field(conn, 'Zone_Conditioning_Equipment_List_Name') == equiplist.Name:
                    zone = _get_field(conn, 'Zone_Name')
                    if zone and zone not in zones:
                        zones.append(zone)
    return zones


def _strategy_c1(idf, obj_name: str) -> Optional[List[str]]:
    """
    Search all ZoneHVAC container objects for a field that equals obj_name.
    Then traverse EquipmentList → EquipmentConnections to obtain the zone.

    Returns None if not found, or the list of zones if found.
    If more than one distinct zone is found the coil is shared across zones
    and a UserWarning is raised; the caller is expected to handle this by
    requiring the user to supply hvac_zone_map.
    """
    zones_found: List[str] = []

    for container_type in _ZONE_HVAC_CONTAINERS:
        for container_obj in _idfobjects_safe(idf, container_type):
            for fname in _field_names(container_obj):
                if _get_field(container_obj, fname) == obj_name:
                    # This container references coil obj_name
                    zones = _zone_from_equipment_connections(idf, container_obj.Name)
                    # If not found in EquipmentConnections, try to recurse
                    # (some containers are themselves inside other containers)
                    if not zones:
                        zones = _strategy_c1_recurse(idf, container_obj.Name)
                    for z in zones:
                        if z not in zones_found:
                            zones_found.append(z)
                    break  # found the obj in this container, stop scanning its fields

    if not zones_found:
        return None

    if len(zones_found) > 1:
        warnings.warn(
            f"HVAC object '{obj_name}' appears to be shared between multiple zones "
            f"{zones_found} according to ZoneHVAC:EquipmentList traversal. "
            f"Automatic mapping cannot safely pick one zone. "
            f"Please provide 'hvac_zone_map={{'{obj_name}': 'correct_zone_name'}}' "
            f"to resolve this ambiguity.",
            UserWarning,
            stacklevel=4,
        )
        return None  # Require user to resolve via hvac_zone_map

    return zones_found


def _strategy_c1_recurse(idf, container_name: str) -> List[str]:
    """
    Some containers (e.g. AirLoopHVAC:UnitarySystem) are themselves placed
    inside a ZoneHVAC:EquipmentList.  Try to look them up directly.
    """
    return _zone_from_equipment_connections(idf, container_name)


# ---------------------------------------------------------------------------
# Strategy C2 – AirLoopHVAC traversal
# ---------------------------------------------------------------------------

def _find_branch_for_object(idf, obj_name: str) -> Optional[str]:
    """Return the Branch name that contains a component called obj_name."""
    for branch in _idfobjects_safe(idf, 'Branch'):
        for fname in _field_names(branch):
            if 'Component_Name' in fname:
                if _get_field(branch, fname) == obj_name:
                    return branch.Name
    return None


def _find_branchlist_for_branch(idf, branch_name: str) -> Optional[str]:
    """Return the BranchList name that includes branch_name."""
    for bl in _idfobjects_safe(idf, 'BranchList'):
        for fname in _field_names(bl):
            if 'Branch_Name' in fname:
                if _get_field(bl, fname) == branch_name:
                    return bl.Name
    return None


def _find_airloop_for_branchlist(idf, branchlist_name: str) -> Optional[str]:
    """Return the AirLoopHVAC name whose Branch_List_Name equals branchlist_name."""
    for loop in _idfobjects_safe(idf, 'AirLoopHVAC'):
        if _get_field(loop, 'Branch_List_Name') == branchlist_name:
            return loop.Name
    return None


def _find_supply_outlet_node(idf, airloop_name: str) -> Optional[str]:
    """Return the supply-side outlet node of an AirLoopHVAC."""
    for loop in _idfobjects_safe(idf, 'AirLoopHVAC'):
        if loop.Name == airloop_name:
            return _get_field(loop, 'Supply_Side_Outlet_Node_Names')
    return None


def _find_zone_splitter_outlets(idf, supply_outlet_node: str) -> List[str]:
    """
    Follow supply outlet node → AirLoopHVAC:SupplyPath → ZoneSplitter
    and return all outlet node names of the splitter.
    """
    splitter_outlets: List[str] = []

    # Find SupplyPath whose inlet node matches the airloop's supply outlet
    for sp in _idfobjects_safe(idf, 'AirLoopHVAC:SupplyPath'):
        if _get_field(sp, 'Supply_Air_Path_Inlet_Node_Name') == supply_outlet_node:
            # Find ZoneSplitter referenced in this SupplyPath
            for fname in _field_names(sp):
                if 'Component_Object_Type' in fname:
                    obj_type = _get_field(sp, fname)
                    if obj_type.lower() == 'airloophvac:zonesplitter':
                        # Get the corresponding component name field
                        name_field = fname.replace('Component_Object_Type', 'Component_Name')
                        splitter_name = _get_field(sp, name_field)
                        # Collect all outlet nodes of this splitter
                        for splitter in _idfobjects_safe(idf, 'AirLoopHVAC:ZoneSplitter'):
                            if splitter.Name == splitter_name:
                                for sf in _field_names(splitter):
                                    if 'Outlet_Node_Name' in sf:
                                        node = _get_field(splitter, sf)
                                        if node and node not in splitter_outlets:
                                            splitter_outlets.append(node)
    return splitter_outlets


def _zones_from_splitter_outlets(idf, outlet_nodes: List[str]) -> List[str]:
    """
    Match splitter outlet nodes to ZoneHVAC:EquipmentConnections inlet nodes
    (which may be node names or NodeList names) and return the zone names.
    """
    zones: List[str] = []

    # Build a set of all nodes listed in NodeList objects for quick lookup
    node_to_nodelist: Dict[str, str] = {}
    for nl in _idfobjects_safe(idf, 'NodeList'):
        for fname in _field_names(nl):
            if 'Node_Name' in fname:
                node = _get_field(nl, fname)
                if node:
                    node_to_nodelist[node] = nl.Name

    # Check EquipmentConnections for matching inlet nodes
    for conn in _idfobjects_safe(idf, 'ZoneHVAC:EquipmentConnections'):
        inlet = _get_field(conn, 'Zone_Air_Inlet_Node_or_NodeList_Name')
        # inlet can be a single node name OR a NodeList name
        # First check direct match
        directly_matched = inlet in outlet_nodes
        # Then check via NodeList
        nodelist_matched = any(
            node_to_nodelist.get(node) == inlet
            for node in outlet_nodes
            if node in node_to_nodelist
        )
        # Also check if the NodeList itself contains one of the outlet nodes
        nodelist_contains = False
        for nl in _idfobjects_safe(idf, 'NodeList'):
            if nl.Name == inlet:
                for fname in _field_names(nl):
                    if 'Node_Name' in fname:
                        if _get_field(nl, fname) in outlet_nodes:
                            nodelist_contains = True
                            break
        if directly_matched or nodelist_matched or nodelist_contains:
            zone = _get_field(conn, 'Zone_Name')
            if zone and zone not in zones:
                zones.append(zone)

    return zones


def _strategy_c2(idf, obj_name: str) -> Optional[List[str]]:
    """
    Traverse Branch → BranchList → AirLoopHVAC → SupplyPath → ZoneSplitter →
    ZoneHVAC:EquipmentConnections to find the zone(s) served by obj_name.

    Multiple zones are allowed and returned as-is (each gets its own EMS sensor).
    """
    branch_name = _find_branch_for_object(idf, obj_name)
    if not branch_name:
        return None

    branchlist_name = _find_branchlist_for_branch(idf, branch_name)
    if not branchlist_name:
        return None

    airloop_name = _find_airloop_for_branchlist(idf, branchlist_name)
    if not airloop_name:
        return None

    supply_outlet = _find_supply_outlet_node(idf, airloop_name)
    if not supply_outlet:
        return None

    splitter_outlets = _find_zone_splitter_outlets(idf, supply_outlet)
    if not splitter_outlets:
        # Some loops have no splitter (single-zone AHU); the outlet node
        # connects directly to the zone inlet
        zones = _zones_from_splitter_outlets(idf, [supply_outlet])
    else:
        zones = _zones_from_splitter_outlets(idf, splitter_outlets)

    return zones if zones else None


# ---------------------------------------------------------------------------
# Strategy D – legacy name-parsing fallback
# ---------------------------------------------------------------------------

def _strategy_d(obj_name: str) -> List[str]:
    """Extract zone as the first whitespace token of the object name."""
    zone = obj_name.split(' ')[0]
    warnings.warn(
        f"Could not automatically determine the zone for HVAC object '{obj_name}'. "
        f"Falling back to legacy name-parsing: zone assumed to be '{zone}'. "
        f"If this is incorrect, provide the correct mapping via "
        f"``hvac_zone_map={{'{obj_name}': 'correct_zone_name'}}``.",
        UserWarning,
        stacklevel=4,
    )
    return [zone]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_hvac_zone_map(
    idf,
    hvac_type: str,
    hvac_obj_names: List[str],
    user_map: Optional[Dict] = None,
    verboseMode: bool = True,
) -> Dict[str, List[str]]:
    """
    Map each HVAC object name in *hvac_obj_names* to one or more zone names.

    Strategies are applied in cascade (A → B → C1 → C2 → D) and the first
    successful strategy wins, except for Strategy C2 which may legitimately
    return multiple zones (centralised air handler serving several zones).

    Parameters
    ----------
    idf : eppy IDF object
        The model being processed.
    hvac_type : str
        The EnergyPlus object type string (e.g. ``'Coil:Cooling:Water'``).
    hvac_obj_names : list of str
        Names of the HVAC objects of *hvac_type* present in the model.
    user_map : dict or None
        Optional override.  Format: ``{'HVAC Object Name': 'Zone Name'}``.
        May also map to a list of zone names for multi-zone explicit mappings.
    verboseMode : bool
        If True, print the strategy used for each object.

    Returns
    -------
    dict
        ``{hvac_obj_name: [zone_name, ...]}`` where the list has exactly one
        element in the common case and possibly more for C2 (AirLoop) objects.
        Objects that cannot be resolved and for which the user did not supply
        a ``hvac_zone_map`` entry are **not** included in the returned dict
        (a UserWarning is issued for them in C1, and a fallback is used in D).
    """
    result: Dict[str, List[str]] = {}

    for obj_name in hvac_obj_names:
        zones: Optional[List[str]] = None
        strategy_label: str = '?'

        # ---- Strategy A: manual user map ---------------------------------
        zones = _strategy_a(obj_name, user_map)
        if zones is not None:
            strategy_label = 'A (manual map)'

        # ---- Strategy B: direct Zone_Name field --------------------------
        if zones is None:
            zones = _strategy_b(idf, hvac_type, obj_name)
            if zones is not None:
                strategy_label = 'B (direct Zone_Name field)'

        # ---- Strategy C1: ZoneHVAC:EquipmentList traversal ---------------
        if zones is None:
            zones = _strategy_c1(idf, obj_name)
            if zones is not None:
                strategy_label = 'C1 (ZoneHVAC:EquipmentList)'
            # If C1 returned None due to multi-zone warning → stay None,
            # C2 will try next (or D as last resort)

        # ---- Strategy C2: AirLoopHVAC traversal --------------------------
        if zones is None:
            zones = _strategy_c2(idf, obj_name)
            if zones is not None:
                n = len(zones)
                strategy_label = (
                    f'C2 (AirLoopHVAC → {n} zone{"s" if n != 1 else ""})'
                )

        # ---- Strategy D: legacy name-parsing fallback --------------------
        if zones is None:
            zones = _strategy_d(obj_name)
            strategy_label = 'D (legacy name-parsing fallback)'

        if verboseMode:
            print(
                f"  ExistingHVAC resolver: '{obj_name}' "
                f"→ {zones}  [Strategy {strategy_label}]"
            )

        result[obj_name] = zones

    return result
