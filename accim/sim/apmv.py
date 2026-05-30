# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""
Contains the functions to apply setpoints based on the Adaptive Predicted Mean Vote (aPMV) index.
Unified version supporting EnergyPlus versions pre and post 23.1.

This module implements a robust logic to identify target zones or spaces based on the
Global Model Hierarchy (Space > ZoneList > Zone) and generates the necessary
EnergyManagementSystem (EMS) objects to control thermal comfort dynamically.
"""

import warnings
import os
import re
from typing import Dict, Any, List, Union, Optional
import pandas as pd
from besos.IDF_class import IDF
import besos.objectives
import eppy
from accim.utils import transform_ddmm_to_int
import accim.sim.engine as accim_Main

# ==============================================================================
# MONKEY PATCH FOR BESOS (Suppress Errors Only)
# ==============================================================================
# Rationale:
# BESOS uses a strict regex parser to read the EnergyPlus output file (.eso).
# However, EnergyPlus outputs can sometimes contain formats that break this parser,
# such as:
#   1. Empty units "[]" (common for dimensionless variables like PMV).
#   2. Duplicate variable definitions (if multiple objects request the same variable).
#   3. Trailing schedule names in the variable definition line.
#
# Instead of modifying the .eso file (which risks corrupting the dictionary index
# used by other tools like ESOView), this patch wraps the read function.
# It attempts to read the file, and if BESOS raises an exception, it catches it,
# issues a warning, and returns None. This allows the simulation script to continue
# executing (e.g., generating the IDF) even if the results parsing fails.

try:
    # 1. Store the reference to the original, unmodified function from BESOS.
    _original_read_eso = besos.objectives.read_eso

    def _silent_read_eso(out_dir: str, file_name: str = 'eplusout.eso') -> Optional[Any]:
        """
        A wrapper around besos.objectives.read_eso that catches parsing exceptions.

        :param out_dir: The directory path where the simulation output is located.
        :param file_name: The name of the results file (default: 'eplusout.eso').
        :return: The parsed results object if successful, or None if parsing fails.
        """
        try:
            # Attempt to execute the original BESOS reading function.
            return _original_read_eso(out_dir, file_name)
        except Exception as e:
            # If ANY error occurs during reading (ValueError, AssertionError, etc.),
            # we catch it here to prevent the entire script from crashing.
            warnings.warn(
                f"BESOS failed to read the results file '{file_name}' due to error: {e}. "
                f"The simulation completed, but results could not be parsed by BESOS. "
                f"Execution continues without output data."
            )
            return None

    # 2. Apply the patch: Replace the library function with our safe wrapper.
    besos.objectives.read_eso = _silent_read_eso

except ImportError:
    # If BESOS is not installed or the structure has changed, skip the patch.
    pass


# ==============================================================================
# CORE RESOLUTION LOGIC
# ==============================================================================

def _sanitize_ems_name(name: str) -> str:
    """
    Sanitizes a string to be used as a valid EnergyManagementSystem (EMS) variable name.

    EnergyPlus EMS variable names have strict requirements:
    - They must be unique.
    - They cannot contain spaces, colons (:), hyphens (-), dots (.), slashes (/),
      parentheses, or special characters.
    - Only alphanumeric characters (A-Z, 0-9) and underscores (_) are allowed.

    :param name: The original name string from the IDF object (e.g., "Zone 1: Space-A").
    :return: A sanitized string safe for EMS usage (e.g., "Zone_1__Space_A").
    """
    # Use Regular Expression to replace ANY character that is NOT
    # a letter (a-z, A-Z), a number (0-9), or an underscore (_) with an underscore.
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def _resolve_targets(building: IDF) -> List[Dict[str, str]]:
    """
    Analyzes the IDF to find all 'People' objects and resolves their target Zones or Spaces
    for EMS application. It follows a strict Global Hierarchy to determine the target level.

    The logic is based on the presence of specific object types in the model to ensure
    compatibility with both legacy (Zone-based) and modern (Space-based) EnergyPlus versions.

    LOGIC HIERARCHY (3 Levels):
    1. GLOBAL CHECK: Are there SPACE or SPACELIST objects in the model?
       - YES: The model is "Modern" (v23.1+ with Spaces).
         ALL targets resolve to the pattern 'SpaceName PeopleName'.
         (Even if People are assigned to a ZoneList, we find the spaces inside those zones).

    2. ELSE: Are there ZONELIST objects in the model?
       - YES: The model uses ZoneLists for grouping.
         If People assigned to ZoneList -> Expand to 'ZoneName PeopleName'.
         If People assigned to Zone     -> Use 'ZoneName' (Sensor uses PeopleName).

    3. ELSE:
       - The model is simple (Zones only).
         Target resolves to 'ZoneName' (Sensor uses PeopleName).

    :param building: The BESOS/eppy IDF object representing the building model.
    :return: A list of dictionaries, where each dictionary represents a target control unit:
             - 'df_key': Unique identifier for user input DataFrames (e.g., "Space1 People1").
             - 'ems_suffix': Sanitized string for EMS variable naming (e.g., "Space1_People1").
             - 'sensor_key': The exact key E+ expects for the Sensor object (e.g., "Space1 People1").
             - 'zone_name': The raw name of the Zone (used for Schedules/Thermostats, which are always Zone-based).
    """
    targets = []

    # --- 1. BUILD LOOKUP DICTIONARIES ---
    # We pre-fetch all relevant objects to avoid repeated searches during iteration.
    # We use try-except blocks to handle different EnergyPlus versions safely.

    # Check for Spaces (Modern versions)
    has_spaces = False
    try:
        if len(building.idfobjects['SPACE']) > 0 or len(building.idfobjects['SPACELIST']) > 0:
            has_spaces = True
    except KeyError:
        # KeyError means the IDD version doesn't support SPACE objects (Legacy versions)
        pass

    # Check for ZoneLists (All versions)
    has_zonelists = False
    try:
        if len(building.idfobjects['ZONELIST']) > 0:
            has_zonelists = True
    except KeyError:
        pass

    # Initialize lookup dictionaries
    zone_lists = {}  # Map: ZoneList Name -> ZoneList Object
    space_lists = {}  # Map: SpaceList Name -> SpaceList Object
    space_to_zone = {}  # Map: Space Name -> Parent Zone Name
    zone_to_spaces = {}  # Map: Zone Name -> List of Child Space Names

    # Populate ZoneLists dictionary
    if has_zonelists:
        for zl in building.idfobjects['ZONELIST']:
            # Store keys in UPPERCASE and stripped for robust matching
            zone_lists[zl.Name.upper().strip()] = zl

    # Populate Space dictionaries (only if spaces exist)
    if has_spaces:
        try:
            # Map SpaceLists
            for sl in building.idfobjects['SPACELIST']:
                space_lists[sl.Name.upper().strip()] = sl

            # Map Spaces and their relationships to Zones
            for s in building.idfobjects['SPACE']:
                s_name = s.Name.strip()
                s_key = s_name.upper()
                z_name = s.Zone_Name.strip()

                # Forward map: Space -> Zone
                space_to_zone[s_key] = z_name

                # Reverse map: Zone -> [Space1, Space2, ...]
                z_key = z_name.upper()
                if z_key not in zone_to_spaces:
                    zone_to_spaces[z_key] = []
                zone_to_spaces[z_key].append(s_name)
        except KeyError:
            pass

    # Helper function to extract items from extensible lists (ZoneList or SpaceList)
    # Eppy handles extensible fields (Zone_1_Name, Zone_2_Name...) dynamically.
    def get_items_from_list(obj, field_prefix):
        items = []
        # Arbitrary limit of 500 items per list to prevent infinite loops.
        for i in range(1, 500):
            try:
                # Construct field name: e.g., "Zone_1_Name" or "Space_1_Name"
                val = obj[f"{field_prefix}_{i}_Name"]
                if val:
                    items.append(val)
                else:
                    # Stop if we hit an empty field
                    break
            except:
                # Stop if the field doesn't exist in the IDD
                break
        return items

    # --- 2. ITERATE PEOPLE OBJECTS ---
    # We process every 'People' object in the model to determine what it controls.
    for people in building.idfobjects['PEOPLE']:

        # Robustly find the container name (the field name varies by E+ version)
        container_name = ""
        try:
            container_name = people.Zone_or_ZoneList_Name
        except:
            try:
                container_name = people.Zone_or_ZoneList_or_Space_or_SpaceList_Name
            except:
                container_name = people.Zone_Name

        if not container_name:
            continue  # Skip if unassigned

        p_name = people.Name.strip()
        c_name_upper = container_name.upper().strip()

        # ======================================================================
        # LEVEL 1: SPACE or SPACELIST (The "Modern" Path)
        # ======================================================================
        # If the model contains Spaces, we MUST resolve everything down to the Space level.
        if has_spaces:
            target_spaces = []  # List of tuples: (SpaceName, ParentZoneName)

            # A. Assigned to SPACELIST -> Expand to individual Spaces
            if c_name_upper in space_lists:
                sl_obj = space_lists[c_name_upper]
                s_names = get_items_from_list(sl_obj, "Space")
                for s in s_names:
                    # Find the parent zone for this space
                    z = space_to_zone.get(s.upper().strip(), s)  # Fallback to space name if orphan
                    target_spaces.append((s, z))

            # B. Assigned to SPACE -> Direct mapping
            elif c_name_upper in space_to_zone:
                # container_name is the space name
                z = space_to_zone[c_name_upper]
                target_spaces.append((container_name, z))

            # C. Assigned to ZONELIST -> Find all spaces within those zones
            elif c_name_upper in zone_lists:
                zl_obj = zone_lists[c_name_upper]
                z_names = get_items_from_list(zl_obj, "Zone")
                for z in z_names:
                    # Look up the spaces belonging to this zone
                    spaces_in_z = zone_to_spaces.get(z.upper().strip(), [])
                    for s in spaces_in_z:
                        target_spaces.append((s, z))

            # D. Assigned to ZONE -> Find all spaces within that zone
            else:
                # Look up the spaces belonging to this zone
                spaces_in_z = zone_to_spaces.get(c_name_upper, [])
                for s in spaces_in_z:
                    target_spaces.append((s, container_name))

            # GENERATE TARGETS FOR RESOLVED SPACES
            for s_name, z_name in target_spaces:
                # In modern E+, internal objects are named "SpaceName PeopleName"
                full_key = f"{s_name} {p_name}"
                targets.append({
                    'df_key': full_key,
                    'ems_suffix': _sanitize_ems_name(f"{s_name}_{p_name}"),
                    'sensor_key': full_key,
                    'zone_name': z_name  # Important: Actuators act on the Zone Schedule
                })

        # ======================================================================
        # LEVEL 2: ZONELIST (Only if not Space/SpaceList)
        # ======================================================================
        elif has_zonelists and c_name_upper in zone_lists:
            # Assigned to ZONELIST -> Expand to individual Zones
            # E+ creates internal objects named "ZoneName PeopleName"
            zl_obj = zone_lists[c_name_upper]
            z_names = get_items_from_list(zl_obj, "Zone")

            for z in z_names:
                full_key = f"{z} {p_name}"
                targets.append({
                    'df_key': full_key,
                    'ems_suffix': _sanitize_ems_name(f"{z}_{p_name}"),
                    'sensor_key': full_key,
                    'zone_name': z
                })

        # ======================================================================
        # LEVEL 3: ZONE (Default/Legacy)
        # ======================================================================
        else:
            # Assigned directly to ZONE (and no spaces involved).
            # E+ does NOT rename the People object internally.
            targets.append({
                'df_key': container_name,  # User identifies by Zone Name
                'ems_suffix': _sanitize_ems_name(container_name),
                'sensor_key': p_name,  # Sensor must point to the original People Name
                'zone_name': container_name
            })

    return targets


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================

def apply_apmv_setpoints(
        building: IDF,
        outputs_freq: List[str] = ['hourly'],
        other_PMV_related_outputs: bool = True,
        adap_coeff_cooling: Union[float, dict] = 0.293,
        adap_coeff_heating: Union[float, dict] = -0.293,
        pmv_cooling_sp: Union[float, dict] = -0.5,
        pmv_heating_sp: Union[float, dict] = 0.5,
        tolerance_cooling_sp_cooling_season: Union[float, dict] = -0.1,
        tolerance_cooling_sp_heating_season: Union[float, dict] = -0.1,
        tolerance_heating_sp_cooling_season: Union[float, dict] = 0.1,
        tolerance_heating_sp_heating_season: Union[float, dict] = 0.1,
        cooling_season_start: Union[float, str] = 120,
        cooling_season_end: Union[float, str] = 210,
        dflt_for_adap_coeff_cooling: float = 0.4,
        dflt_for_adap_coeff_heating: float = -0.4,
        dflt_for_pmv_cooling_sp: float = 0.5,
        dflt_for_pmv_heating_sp: float = -0.5,
        dflt_for_tolerance_cooling_sp_cooling_season: float = -0.1,
        dflt_for_tolerance_cooling_sp_heating_season: float = -0.1,
        dflt_for_tolerance_heating_sp_cooling_season: float = 0.1,
        dflt_for_tolerance_heating_sp_heating_season: float = 0.1,
        verbose_mode: bool = True,
) -> IDF:
    """
    Applies setpoints based on the Adaptive Predicted Mean Vote (aPMV) index.

    This function modifies the EnergyPlus IDF model to include an Energy Management System (EMS)
    control logic. It calculates the aPMV in real-time and adjusts the heating and cooling
    setpoints dynamically to maintain thermal comfort within the specified adaptive limits.

    It supports both legacy EnergyPlus versions (Zone-based) and modern versions (Space-based),
    automatically resolving the model hierarchy.

    :param building: The BESOS/eppy IDF object to be modified.
    :param outputs_freq: List of reporting frequencies for the output variables (e.g., ['hourly', 'timestep']).
    :param other_PMV_related_outputs: If True, adds additional comfort-related output variables (e.g., Fanger PMV, PPD).
    :param adap_coeff_cooling: Adaptive coefficient (lambda) for cooling. Can be a single float (applied globally) or a dict {TargetName: Value}.
    :param adap_coeff_heating: Adaptive coefficient (lambda) for heating. Float or Dict {TargetName: Value}.
    :param pmv_cooling_sp: Target PMV setpoint for cooling (e.g., 0.5). Float or Dict.
    :param pmv_heating_sp: Target PMV setpoint for heating (e.g., -0.5). Float or Dict.
    :param tolerance_cooling_sp_cooling_season: Tolerance to widen the cooling setpoint band during cooling season.
    :param tolerance_cooling_sp_heating_season: Tolerance to widen the cooling setpoint band during heating season.
    :param tolerance_heating_sp_cooling_season: Tolerance to widen the heating setpoint band during cooling season.
    :param tolerance_heating_sp_heating_season: Tolerance to widen the heating setpoint band during heating season.
    :param cooling_season_start: Start day of the cooling season. Can be an integer (Day of Year) or string ('dd/mm').
    :param cooling_season_end: End day of the cooling season. Can be an integer (Day of Year) or string ('dd/mm').
    :param dflt_for_adap_coeff_cooling: Default value for cooling adaptive coefficient if key is missing in dict input.
    :param dflt_for_adap_coeff_heating: Default value for heating adaptive coefficient if key is missing in dict input.
    :param dflt_for_pmv_cooling_sp: Default value for cooling PMV setpoint if key is missing in dict input.
    :param dflt_for_pmv_heating_sp: Default value for heating PMV setpoint if key is missing in dict input.
    :param dflt_for_tolerance_cooling_sp_cooling_season: Default tolerance value if key is missing.
    :param dflt_for_tolerance_cooling_sp_heating_season: Default tolerance value if key is missing.
    :param dflt_for_tolerance_heating_sp_cooling_season: Default tolerance value if key is missing.
    :param dflt_for_tolerance_heating_sp_heating_season: Default tolerance value if key is missing.
    :param verbose_mode: If True, prints detailed progress messages (added objects) and warnings to the console.
    :return: The modified BESOS IDF object with EMS controls added.
    """

    # --- 1. RESOLVE TARGETS ---
    # Identify all zones or spaces that need EMS control based on the 'People' objects present in the model.
    # This step abstracts away the complexity of ZoneLists, SpaceLists, and Spaces.
    target_data = _resolve_targets(building)

    # Extract lists for internal processing:
    # - ems_target_suffixes: Sanitized names for EMS variables (e.g., "Space1_People1").
    # - ems_sensor_keys: The exact keys to read data from EnergyPlus (e.g., "Space1 People1").
    # - df_keys: Keys used to map user input arguments (e.g., "Space1 People1").
    # - target_zones: The raw Zone names associated with each target.
    ems_target_suffixes = [t['ems_suffix'] for t in target_data]
    ems_sensor_keys = [t['sensor_key'] for t in target_data]
    df_keys = [t['df_key'] for t in target_data]
    target_zones = [t['zone_name'] for t in target_data]

    # Get a unique list of zones. This is crucial because Schedules and Thermostats
    # are assigned at the Zone level, even if we calculate comfort at the Space level.
    unique_zones = list(set(target_zones))

    # --- 2. PREPARE DATA ---
    # Convert date strings (e.g., "01/05") to Day of Year integers (e.g., 121) if necessary.
    if isinstance(cooling_season_start, str):
        cooling_season_start = transform_ddmm_to_int(cooling_season_start)
    if isinstance(cooling_season_end, str):
        cooling_season_end = transform_ddmm_to_int(cooling_season_end)

    # --- 3. ENSURE INFRASTRUCTURE ---
    # Before adding EMS controls, we must ensure the model has the necessary standard objects:
    # - Schedule:Compact objects for Heating and Cooling setpoints (which EMS will write to).
    # - ZoneControl:Thermostat objects configured for 'ThermalComfort' control type.
    # - ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint objects linked to the schedules.
    _ensure_infrastructure(building, unique_zones, verbose_mode)

    # --- 4. GENERATE ARGUMENTS DATAFRAME ---
    # Map the user's input arguments (which might be single floats or dictionaries)
    # to the specific targets resolved in step 1.
    # This creates a pandas DataFrame where each row corresponds to a target (Space/Zone)
    # and columns correspond to parameters (coeffs, setpoints, tolerances).
    df_arguments = generate_df_from_args(
        target_keys_input=df_keys,
        ems_suffixes=ems_target_suffixes,
        adap_coeff_heating=adap_coeff_heating,
        adap_coeff_cooling=adap_coeff_cooling,
        pmv_heating_sp=pmv_heating_sp,
        pmv_cooling_sp=pmv_cooling_sp,
        tolerance_cooling_sp_cooling_season=tolerance_cooling_sp_cooling_season,
        tolerance_cooling_sp_heating_season=tolerance_cooling_sp_heating_season,
        tolerance_heating_sp_cooling_season=tolerance_heating_sp_cooling_season,
        tolerance_heating_sp_heating_season=tolerance_heating_sp_heating_season,
        dflt_for_adap_coeff_cooling=dflt_for_adap_coeff_cooling,
        dflt_for_adap_coeff_heating=dflt_for_adap_coeff_heating,
        dflt_for_pmv_cooling_sp=dflt_for_pmv_cooling_sp,
        dflt_for_pmv_heating_sp=dflt_for_pmv_heating_sp,
        dflt_for_tolerance_cooling_sp_cooling_season=dflt_for_tolerance_cooling_sp_cooling_season,
        dflt_for_tolerance_cooling_sp_heating_season=dflt_for_tolerance_cooling_sp_heating_season,
        dflt_for_tolerance_heating_sp_cooling_season=dflt_for_tolerance_heating_sp_cooling_season,
        dflt_for_tolerance_heating_sp_heating_season=dflt_for_tolerance_heating_sp_heating_season,
    )

    # --- 5. EMS GENERATION ---
    # Now we generate the actual EMS code blocks in the IDF.

    # A. Sensors: To read 'Zone Thermal Comfort Fanger Model PMV' and 'People Occupant Count'.
    _add_apmv_sensors(building, ems_sensor_keys, ems_target_suffixes, verbose_mode)

    # B. Global Variables: To store intermediate calculations (aPMV, comfort hours, etc.).
    _add_apmv_global_variables(building, ems_target_suffixes, verbose_mode)

    # C. Actuators: To overwrite the values of the Schedule:Compact objects created in step 3.
    # Note: Actuators link the specific EMS logic (Space/People level) to the Zone Schedule.
    _add_apmv_actuators(building, target_data, verbose_mode)

    # D. Programs: The Erl code that performs the logic (If Season -> Calc aPMV -> Set Actuator).
    _add_apmv_programs(building, ems_target_suffixes, df_arguments, cooling_season_start, cooling_season_end, verbose_mode)

    # E. Program Calling Managers: To tell EnergyPlus WHEN to run these programs (BeginTimestepBeforePredictor).
    _add_apmv_program_calling_managers(building, verbose_mode)

    # F. Outputs: To report the EMS variables and standard variables to the .eso file.
    _add_apmv_outputs(building, outputs_freq, other_PMV_related_outputs, ems_target_suffixes, unique_zones, verbose_mode)

    return building


# ==============================================================================
# INFRASTRUCTURE HELPERS
# ==============================================================================

def _ensure_infrastructure(building: IDF, unique_zones: List[str], verbose_mode: bool):
    """
    Ensures that the necessary standard EnergyPlus objects exist for the target zones.
    Specifically, it creates or verifies:
    1. Schedule:Compact objects for Heating and Cooling setpoints.
    2. ZoneControl:Thermostat objects configured for 'ThermalComfort' control.

    IMPORTANT: These objects must use the RAW Zone Name (e.g., "Zone 1") to correctly
    link with the Zone object in the IDF.

    :param building: The BESOS/eppy IDF object to be modified.
    :param unique_zones: A list of RAW zone names (strings) derived from the targets.
    :param verbose_mode: If True, prints success messages for created objects. Warnings are always printed.
    """
    # Get list of existing schedules to avoid duplicates
    sch_comp_objs = [i.Name for i in building.idfobjects['Schedule:Compact']]

    # 1. Create Schedules (Using RAW Zone Name)
    # These are the "dummy" schedules that EMS will overwrite (Actuate) at every timestep.
    # We create one for Heating (PMV_H_SP) and one for Cooling (PMV_C_SP).
    for i in ['PMV_H_SP', 'PMV_C_SP']:
        for zone in unique_zones:
            sch_name = f'{i}_{zone}'
            if sch_name not in sch_comp_objs:
                building.newidfobject(
                    'Schedule:Compact',
                    Name=sch_name,
                    Schedule_Type_Limits_Name="Any Number",
                    Field_1='Through: 12/31',
                    Field_2='For: AllDays',
                    Field_3='Until: 24:00,1'  # Default value (will be overwritten by EMS)
                )
                if verbose_mode:
                    print(f"Added Schedule: {sch_name}")
            else:
                # Warning is issued regardless of verbose_mode
                warnings.warn(f"Schedule '{sch_name}' already exists. Skipping creation.")

    # 2. Ensure Thermostats
    # We need to ensure every target zone has a thermostat capable of Fanger PMV control.

    # Map existing thermostats for quick lookup
    existing_thermostats = {}
    for t in building.idfobjects['ZoneControl:Thermostat']:
        existing_thermostats[t.Zone_or_ZoneList_Name.upper()] = t

    existing_tc_thermostats = {}
    for t in building.idfobjects['ZoneControl:Thermostat:ThermalComfort']:
        existing_tc_thermostats[t.Zone_or_ZoneList_Name.upper()] = t

    for zone in unique_zones:
        z_upper = zone.upper()

        # Case A: No thermostat exists at all.
        # Action: Create a new Thermal Comfort Thermostat.
        if z_upper not in existing_thermostats and z_upper not in existing_tc_thermostats:
            _create_tc_thermostat(building, zone, verbose_mode)

        # Case B: A Standard Thermostat exists (e.g., DualSetpoint).
        # Action: Remove the old standard thermostat and replace it with a Thermal Comfort one.
        # We replace it because a zone cannot have two active thermostat objects.
        elif z_upper in existing_thermostats and z_upper not in existing_tc_thermostats:
            old_t = existing_thermostats[z_upper]
            building.removeidfobject(old_t)
            if verbose_mode:
                print(f"Removed existing Standard Thermostat for zone: {zone}")
            _create_tc_thermostat(building, zone, verbose_mode)

        # Case C: A Thermal Comfort Thermostat already exists.
        # Action: Ensure it points to a Fanger DualSetpoint object and update that object
        # to use our new EMS-controlled schedules.
        elif z_upper in existing_tc_thermostats:
            tc_t = existing_tc_thermostats[z_upper]
            # Warning is issued regardless of verbose_mode
            warnings.warn(f"Thermal Comfort Thermostat already exists for zone '{zone}'. Updating configuration.")

            # Ensure the control type schedule exists and is linked correctly.
            sch_name = _ensure_tc_control_schedule(building, zone, verbose_mode)
            tc_t.Thermal_Comfort_Control_Type_Schedule_Name = sch_name

            # Ensure the control type is Fanger DualSetpoint
            if tc_t.Thermal_Comfort_Control_1_Object_Type != 'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint':
                tc_t.Thermal_Comfort_Control_1_Object_Type = 'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint'

            # Reuse the currently referenced Fanger object when present.
            # Some input files use names like "<Zone> Dual Comfort Setpoint",
            # and updating a different object would leave active control unchanged.
            fanger_name = getattr(tc_t, 'Thermal_Comfort_Control_1_Name', '') or f'Fanger Setpoint {zone}'
            tc_t.Thermal_Comfort_Control_1_Name = fanger_name

            # Update the referenced Fanger object
            _update_fanger_object(building, fanger_name, zone, verbose_mode)


def _create_tc_thermostat(building: IDF, zone: str, verbose_mode: bool):
    """
    Creates a new ZoneControl:Thermostat:ThermalComfort object and its dependencies.

    :param building: The BESOS/eppy IDF object.
    :param zone: The RAW zone name.
    :param verbose_mode: If True, prints success messages.
    """
    # 1. Create the Control Type Schedule (Type 4 = Thermal Comfort)
    sch_name = _ensure_tc_control_schedule(building, zone, verbose_mode)

    # 2. Create the Thermostat Object linking the zone to the Fanger object
    building.newidfobject(
        'ZoneControl:Thermostat:ThermalComfort',
        Name=f'Thermostat Setpoint Dual Setpoint {zone}',
        Zone_or_ZoneList_Name=zone,
        Thermal_Comfort_Control_Type_Schedule_Name=sch_name,
        Thermal_Comfort_Control_1_Object_Type='ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
        Thermal_Comfort_Control_1_Name=f'Fanger Setpoint {zone}'
    )
    if verbose_mode:
        print(f"Added Thermal Comfort Thermostat for zone: {zone}")

    # 3. Create the Fanger Setpoint object
    _update_fanger_object(building, f'Fanger Setpoint {zone}', zone, verbose_mode)


def _ensure_tc_control_schedule(building: IDF, zone: str, verbose_mode: bool) -> str:
    """Ensure thermal comfort control schedule exists for a zone and return its name."""
    sch_name = f'Thermal Comfort Control Type Schedule Name {zone}'
    if not any(s.Name == sch_name for s in building.idfobjects['Schedule:Compact']):
        building.newidfobject(
            'Schedule:Compact',
            Name=sch_name,
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,4'  # 4 maps to 'Thermal Comfort' control type in E+
        )
        if verbose_mode:
            print(f"Added Control Type Schedule: {sch_name}")
    return sch_name


def _update_fanger_object(building: IDF, obj_name: str, zone: str, verbose_mode: bool):
    """
    Creates or updates the 'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint' object.
    This object links the thermostat logic to the specific Heating/Cooling schedules.

    :param building: The BESOS/eppy IDF object.
    :param obj_name: Name of the Fanger object.
    :param zone: The RAW zone name used to find the correct schedules.
    :param verbose_mode: If True, prints success messages.
    """
    # Check if the object already exists
    fanger_obj = None
    for f in building.idfobjects['ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint']:
        if f.Name == obj_name:
            fanger_obj = f
            break

    # If not, create it
    if not fanger_obj:
        fanger_obj = building.newidfobject(
            'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
            Name=obj_name
        )
        if verbose_mode:
            print(f"Added Fanger DualSetpoint Object: {obj_name}")

    # Link the object to the EMS-controlled schedules we created in _ensure_infrastructure
    fanger_obj.Fanger_Thermal_Comfort_Heating_Schedule_Name = f'PMV_H_SP_{zone}'
    fanger_obj.Fanger_Thermal_Comfort_Cooling_Schedule_Name = f'PMV_C_SP_{zone}'


# ==============================================================================
# EMS GENERATORS
# ==============================================================================

def _add_apmv_sensors(building: IDF, sensor_keys: List[str], suffixes: List[str], verbose_mode: bool):
    """
    Adds EnergyManagementSystem:Sensor objects to the IDF.
    Sensors allow the EMS to read data from EnergyPlus Output:Variables during the simulation.

    We need two sensors per target:
    1. PMV: To read the current 'Zone Thermal Comfort Fanger Model PMV'.
    2. Occupant Count: To determine if the space is occupied ('People Occupant Count').

    :param building: The BESOS/eppy IDF object.
    :param sensor_keys: List of exact keys (e.g., "Space1 People") to identify the output variable.
    :param suffixes: List of sanitized suffixes (e.g., "Space1_People") for unique EMS naming.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    # Get existing sensors to avoid duplicates
    sensornamelist = [s.Name for s in building.idfobjects['EnergyManagementSystem:Sensor']]

    for i in range(len(suffixes)):
        # 1. PMV Sensor
        pmv_sensor_name = f'PMV_{suffixes[i]}'
        if pmv_sensor_name not in sensornamelist:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=pmv_sensor_name,
                OutputVariable_or_OutputMeter_Index_Key_Name=sensor_keys[i],
                OutputVariable_or_OutputMeter_Name='Zone Thermal Comfort Fanger Model PMV'
            )
            if verbose_mode:
                print(f"Added Sensor: {pmv_sensor_name}")
        else:
            warnings.warn(f"Sensor '{pmv_sensor_name}' already exists. Skipping.")

        # 2. Occupant Count Sensor
        occ_sensor_name = f'People_Occupant_Count_{suffixes[i]}'
        if occ_sensor_name not in sensornamelist:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=occ_sensor_name,
                OutputVariable_or_OutputMeter_Index_Key_Name=sensor_keys[i],
                OutputVariable_or_OutputMeter_Name='People Occupant Count'
            )
            if verbose_mode:
                print(f"Added Sensor: {occ_sensor_name}")
        else:
            warnings.warn(f"Sensor '{occ_sensor_name}' already exists. Skipping.")


def _add_apmv_actuators(building: IDF, target_data: List[Dict], verbose_mode: bool):
    """
    Adds EnergyManagementSystem:Actuator objects.

    The Actuator is the bridge between the EMS logic (which might run per Space/People)
    and the physical HVAC control (which runs per Zone Schedule). It allows the EMS
    to overwrite the value of the Schedule:Compact objects created in the infrastructure step.

    :param building: The BESOS/eppy IDF object.
    :param target_data: List of target dictionaries resolved earlier.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    actuatornamelist = [actuator.Name for actuator in building.idfobjects['EnergyManagementSystem:Actuator']]

    for target in target_data:
        suffix = target['ems_suffix']  # Sanitized name (e.g., "Space1_People1")
        zone = target['zone_name']  # Raw name (e.g., "Zone 1")

        for i in ['H', 'C']:
            # Actuator Name: Must be unique and sanitized for EMS.
            # We use the suffix derived from the specific target (Space/People).
            act_name = f'PMV_{i}_SP_act_{suffix}'

            # Target Object: The Schedule we want to overwrite.
            # This schedule is named using the RAW Zone Name.
            sch_name = f'PMV_{i}_SP_{zone}'

            if act_name not in actuatornamelist:
                building.newidfobject(
                    'EnergyManagementSystem:Actuator',
                    Name=act_name,
                    # We actuate the 'Schedule Value' of the 'Schedule:Compact' object
                    Actuated_Component_Unique_Name=sch_name,
                    Actuated_Component_Type='Schedule:Compact',
                    Actuated_Component_Control_Type='Schedule Value',
                )
                if verbose_mode:
                    print(f"Added Actuator: {act_name}")
            else:
                warnings.warn(f"Actuator '{act_name}' already exists. Skipping creation.")


def _add_apmv_global_variables(building: IDF, suffixes: List[str], verbose_mode: bool):
    """
    Adds EnergyManagementSystem:GlobalVariable objects.
    These variables store intermediate calculation results (like the calculated aPMV)
    and parameters (like tolerance or adaptive coefficients) that change dynamically.

    :param building: The BESOS/eppy IDF object.
    :param suffixes: List of sanitized suffixes for unique naming per target.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    # List of variable prefixes needed for the logic
    prefixes = [
        'tolerance_cooling_sp', 'tolerance_cooling_sp_cooling_season', 'tolerance_cooling_sp_heating_season',
        'tolerance_heating_sp', 'tolerance_heating_sp_cooling_season', 'tolerance_heating_sp_heating_season',
        'adap_coeff', 'adap_coeff_heating', 'adap_coeff_cooling',
        'pmv_heating_sp', 'pmv_cooling_sp', 'aPMV',
        'comfhour', 'discomfhour', 'discomfhour_heat', 'discomfhour_cold', 'occupied_hour',
        'aPMV_H_SP', 'aPMV_C_SP', 'aPMV_H_SP_noTol', 'aPMV_C_SP_noTol'
    ]

    existing = {gv.Erl_Variable_1_Name for gv in building.idfobjects['EnergyManagementSystem:GlobalVariable']}

    # 1. Global Season Variables (Shared across the whole building)
    for gv in ['CoolingSeason', 'CoolSeasonEnd', 'CoolSeasonStart']:
        if gv not in existing:
            building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=gv)
            if verbose_mode:
                print(f"Added Global Variable: {gv}")
        else:
            warnings.warn(f"Global Variable '{gv}' already exists. Skipping.")

    # 2. Per-Target Variables (Specific to each Zone/Space)
    for prefix in prefixes:
        for suffix in suffixes:
            gv = f'{prefix}_{suffix}'
            if gv not in existing:
                building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=gv)
                if verbose_mode:
                    print(f"Added Global Variable: {gv}")
            else:
                warnings.warn(f"Global Variable '{gv}' already exists. Skipping.")


def _add_apmv_programs(building: IDF, suffixes: List[str], df_arguments: pd.DataFrame, cool_start: int, cool_end: int, verbose_mode: bool):
    """
    Adds EnergyManagementSystem:Program objects.
    This contains the actual Erl (EnergyPlus Runtime Language) code that executes the control logic.

    :param building: The BESOS/eppy IDF object.
    :param suffixes: List of sanitized suffixes.
    :param df_arguments: DataFrame containing user inputs (coeffs, setpoints) mapped to targets.
    :param cool_start: Integer representing the start day of cooling season.
    :param cool_end: Integer representing the end day of cooling season.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    programlist = [p.Name for p in building.idfobjects['EnergyManagementSystem:Program']]

    # --- PROGRAM 1: Initialize Season Dates ---
    prog_name = 'set_cooling_season_input_data'
    if prog_name not in programlist:
        building.newidfobject('EnergyManagementSystem:Program', Name=prog_name,
                              Program_Line_1=f'set CoolSeasonStart = {cool_start}',
                              Program_Line_2=f'set CoolSeasonEnd = {cool_end}')
        if verbose_mode: print(f"Added Program: {prog_name}")
    else:
        warnings.warn(f"Program '{prog_name}' already exists. Skipping.")

    # --- PROGRAM 2: Determine Current Season ---
    prog_name = 'set_cooling_season'
    if prog_name not in programlist:
        building.newidfobject('EnergyManagementSystem:Program', Name=prog_name,
                              Program_Line_1='if CoolSeasonEnd > CoolSeasonStart',  # Normal case (e.g., May to Sept)
                              Program_Line_2='if (DayOfYear >= CoolSeasonStart) && (DayOfYear < CoolSeasonEnd)',
                              Program_Line_3='set CoolingSeason = 1',
                              Program_Line_4='else', Program_Line_5='set CoolingSeason = 0', Program_Line_6='endif',
                              Program_Line_7='elseif CoolSeasonStart > CoolSeasonEnd',  # Cross-year case (e.g., Dec to Feb)
                              Program_Line_8='if (DayOfYear >= CoolSeasonStart) || (DayOfYear < CoolSeasonEnd)',
                              Program_Line_9='set CoolingSeason = 1',
                              Program_Line_10='else', Program_Line_11='set CoolingSeason = 0', Program_Line_12='endif',
                              Program_Line_13='endif')
        if verbose_mode: print(f"Added Program: {prog_name}")
    else:
        warnings.warn(f"Program '{prog_name}' already exists. Skipping.")

    # --- PER-TARGET PROGRAMS ---
    for suffix in suffixes:
        # Retrieve parameters for this specific target from the DataFrame
        try:
            row_idx = df_arguments[df_arguments['underscore_zonename'] == suffix].index[0]
        except IndexError:
            continue  # Skip if data not found

        # --- PROGRAM 3: Initialize Zone Parameters ---
        prog_name = f'set_zone_input_data_{suffix}'
        if prog_name not in programlist:
            building.newidfobject('EnergyManagementSystem:Program', Name=prog_name,
                                  Program_Line_1=f'set adap_coeff_cooling_{suffix} = {df_arguments.loc[row_idx, "adap_coeff_cooling"]}',
                                  Program_Line_2=f'set adap_coeff_heating_{suffix} = {df_arguments.loc[row_idx, "adap_coeff_heating"]}',
                                  Program_Line_3=f'set pmv_cooling_sp_{suffix} = {df_arguments.loc[row_idx, "pmv_cooling_sp"]}',
                                  Program_Line_4=f'set pmv_heating_sp_{suffix} = {df_arguments.loc[row_idx, "pmv_heating_sp"]}',
                                  Program_Line_5=f'set tolerance_cooling_sp_cooling_season_{suffix} = {df_arguments.loc[row_idx, "tolerance_cooling_sp_cooling_season"]}',
                                  Program_Line_6=f'set tolerance_cooling_sp_heating_season_{suffix} = {df_arguments.loc[row_idx, "tolerance_cooling_sp_heating_season"]}',
                                  Program_Line_7=f'set tolerance_heating_sp_cooling_season_{suffix} = {df_arguments.loc[row_idx, "tolerance_heating_sp_cooling_season"]}',
                                  Program_Line_8=f'set tolerance_heating_sp_heating_season_{suffix} = {df_arguments.loc[row_idx, "tolerance_heating_sp_heating_season"]}')
            if verbose_mode: print(f"Added Program: {prog_name}")
        else:
            warnings.warn(f"Program '{prog_name}' already exists. Skipping.")

        # --- PROGRAM 4: Apply aPMV Logic (The Core Logic) ---
        prog_name = f'apply_aPMV_{suffix}'
        if prog_name not in programlist:
            act_h = f'PMV_H_SP_act_{suffix}'  # Actuator for Heating Schedule
            act_c = f'PMV_C_SP_act_{suffix}'  # Actuator for Cooling Schedule

            building.newidfobject('EnergyManagementSystem:Program', Name=prog_name,
                                  # 1. Select coefficients based on season
                                  Program_Line_1='if CoolingSeason == 1',
                                  Program_Line_2=f'set adap_coeff_{suffix} = adap_coeff_cooling_{suffix}',
                                  Program_Line_3=f'set tolerance_cooling_sp_{suffix} = tolerance_cooling_sp_cooling_season_{suffix}',
                                  Program_Line_4=f'set tolerance_heating_sp_{suffix} = tolerance_heating_sp_cooling_season_{suffix}',
                                  Program_Line_5='elseif CoolingSeason == 0',
                                  Program_Line_6=f'set adap_coeff_{suffix} = adap_coeff_heating_{suffix}',
                                  Program_Line_7=f'set tolerance_cooling_sp_{suffix} = tolerance_cooling_sp_heating_season_{suffix}',
                                  Program_Line_8=f'set tolerance_heating_sp_{suffix} = tolerance_heating_sp_heating_season_{suffix}',
                                  Program_Line_9='endif',

                                  # 2. Calculate aPMV Setpoints (Inverse aPMV formula)
                                  Program_Line_10=f'set aPMV_H_SP_noTol_{suffix} = pmv_heating_sp_{suffix}/(1+adap_coeff_{suffix}*pmv_heating_sp_{suffix})',
                                  Program_Line_11=f'set aPMV_C_SP_noTol_{suffix} = pmv_cooling_sp_{suffix}/(1+adap_coeff_{suffix}*pmv_cooling_sp_{suffix})',

                                  # 3. Apply Tolerance
                                  Program_Line_12=f'set aPMV_H_SP_{suffix} = aPMV_H_SP_noTol_{suffix}+tolerance_heating_sp_{suffix}',
                                  Program_Line_13=f'set aPMV_C_SP_{suffix} = aPMV_C_SP_noTol_{suffix}+tolerance_cooling_sp_{suffix}',

                                  # 4. Actuate Schedules (Only if occupied)
                                  Program_Line_14=f'if People_Occupant_Count_{suffix} > 0',
                                  # Heating Logic
                                  Program_Line_15=f'if aPMV_H_SP_{suffix} < 0',
                                  Program_Line_16=f'set {act_h} = aPMV_H_SP_{suffix}',
                                  Program_Line_17='else',
                                  Program_Line_18=f'set {act_h} = 0',
                                  Program_Line_19='endif',

                                  # Cooling Logic
                                  Program_Line_20=f'if aPMV_C_SP_{suffix} > 0',
                                  Program_Line_21=f'set {act_c} = aPMV_C_SP_{suffix}',
                                  Program_Line_22='else',
                                  Program_Line_23=f'set {act_c} = 0',
                                  Program_Line_24='endif',

                                  # 5. Unoccupied Logic
                                  Program_Line_25='else',
                                  Program_Line_26=f'set {act_h} = -100',
                                  Program_Line_27=f'set {act_c} = 100',
                                  Program_Line_28='endif')
            if verbose_mode: print(f"Added Program: {prog_name}")
        else:
            warnings.warn(f"Program '{prog_name}' already exists. Skipping.")

        # --- PROGRAM 5: Monitor aPMV ---
        prog_name = f'monitor_aPMV_{suffix}'
        if prog_name not in programlist:
            building.newidfobject('EnergyManagementSystem:Program', Name=prog_name,
                                  Program_Line_1=f'set aPMV_{suffix} = PMV_{suffix}/(1+adap_coeff_{suffix}*PMV_{suffix})')
            if verbose_mode: print(f"Added Program: {prog_name}")
        else:
            warnings.warn(f"Program '{prog_name}' already exists. Skipping.")

        # --- PROGRAM 6: Count Comfort Hours ---
        prog_name = f'count_aPMV_comfort_hours_{suffix}'
        if prog_name not in programlist:
            building.newidfobject('EnergyManagementSystem:Program', Name=prog_name,
                                  Program_Line_1=f'if aPMV_{suffix} < aPMV_H_SP_noTol_{suffix}',
                                  Program_Line_2=f'set comfhour_{suffix} = 0',
                                  Program_Line_3=f'set discomfhour_cold_{suffix} = 1*ZoneTimeStep',
                                  Program_Line_4=f'set discomfhour_heat_{suffix} = 0',
                                  Program_Line_5=f'elseif aPMV_{suffix} > aPMV_C_SP_noTol_{suffix}',
                                  Program_Line_6=f'set comfhour_{suffix} = 0',
                                  Program_Line_7=f'set discomfhour_cold_{suffix} = 0',
                                  Program_Line_8=f'set discomfhour_heat_{suffix} = 1*ZoneTimeStep',
                                  Program_Line_9='else',
                                  Program_Line_10=f'set comfhour_{suffix} = 1*ZoneTimeStep',
                                  Program_Line_11=f'set discomfhour_cold_{suffix} = 0',
                                  Program_Line_12=f'set discomfhour_heat_{suffix} = 0',
                                  Program_Line_13='endif',
                                  Program_Line_14=f'if People_Occupant_Count_{suffix} > 0',
                                  Program_Line_15=f'set occupied_hour_{suffix} = 1*ZoneTimeStep',
                                  Program_Line_16='else', Program_Line_17=f'set occupied_hour_{suffix} = 0', Program_Line_18='endif',
                                  Program_Line_19=f'set discomfhour_{suffix} = discomfhour_cold_{suffix} + discomfhour_heat_{suffix}')
            if verbose_mode: print(f"Added Program: {prog_name}")
        else:
            warnings.warn(f"Program '{prog_name}' already exists. Skipping.")


def _add_apmv_program_calling_managers(building: IDF, verbose_mode: bool):
    """
    Adds EnergyManagementSystem:ProgramCallingManager objects.
    These objects tell EnergyPlus WHEN to execute the programs defined above.

    :param building: The BESOS/eppy IDF object.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    programlist = [p.Name for p in building.idfobjects['EnergyManagementSystem:Program']]
    pcmlist = [pcm.Name for pcm in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]

    for prog in programlist:
        if prog not in pcmlist:
            building.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=prog,
                                  EnergyPlus_Model_Calling_Point="BeginTimestepBeforePredictor", Program_Name_1=prog)
            if verbose_mode: print(f"Added ProgramCallingManager for: {prog}")
        else:
            warnings.warn(f"ProgramCallingManager for '{prog}' already exists. Skipping.")


def _add_apmv_outputs(building: IDF, outputs_freq: List[str], other_PMV_related_outputs: bool, suffixes: List[str], unique_zones: List[str], verbose_mode: bool):
    """
    Adds Output:Variable objects to report EMS calculations and standard results.

    :param building: The BESOS/eppy IDF object.
    :param outputs_freq: List of frequencies (e.g., ['hourly']).
    :param other_PMV_related_outputs: Boolean to add extra comfort outputs.
    :param suffixes: List of sanitized suffixes for EMS variables.
    :param unique_zones: List of RAW zone names for Schedule outputs.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    outputvariablelist = [v.Name for v in building.idfobjects['EnergyManagementSystem:OutputVariable']]

    # 1. Define EMS Output Variables (Mapping internal vars to output names)
    EMSOutputVariableZone_dict = {
        'Adaptive Coefficient': ['adap_coeff', '', 'Averaged'],
        'aPMV': ['aPMV', '', 'Averaged'],
        'aPMV Heating Setpoint': ['aPMV_H_SP', '', 'Averaged'],
        'aPMV Cooling Setpoint': ['aPMV_C_SP', '', 'Averaged'],
        'aPMV Heating Setpoint No Tolerance': ['aPMV_H_SP_noTol', '', 'Averaged'],
        'aPMV Cooling Setpoint No Tolerance': ['aPMV_C_SP_noTol', '', 'Averaged'],
        'Comfortable Hours': ['comfhour', 'H', 'Summed'],
        'Discomfortable Hot Hours': ['discomfhour_heat', 'H', 'Summed'],
        'Discomfortable Cold Hours': ['discomfhour_cold', 'H', 'Summed'],
        'Discomfortable Total Hours': ['discomfhour', 'H', 'Summed'],
        'Occupied hours': ['occupied_hour', 'H', 'Summed'],
    }

    for key, val in EMSOutputVariableZone_dict.items():
        for suffix in suffixes:
            out_name = f'{key}_{suffix}'
            if out_name not in outputvariablelist:
                building.newidfobject('EnergyManagementSystem:OutputVariable', Name=out_name,
                                      EMS_Variable_Name=f'{val[0]}_{suffix}', Type_of_Data_in_Variable=val[2],
                                      Update_Frequency='ZoneTimestep', Units=val[1])
                if verbose_mode: print(f"Added EMS Output Variable: {out_name}")
            else:
                warnings.warn(f"EMS Output Variable '{out_name}' already exists. Skipping.")

    def _norm(value: Any) -> str:
        return '' if value is None else str(value).strip().upper()

    def _var_key(key_value: Any, variable_name: Any, frequency: Any) -> tuple[str, str, str]:
        return (_norm(key_value), _norm(variable_name), _norm(frequency))

    # 2. Add Standard Output:Variables for reporting
    for freq in outputs_freq:
        freq_cap = str(freq).capitalize()
        existing_output_keys = {
            _var_key(getattr(o, 'Key_Value', ''), getattr(o, 'Variable_Name', ''), getattr(o, 'Reporting_Frequency', ''))
            for o in building.idfobjects['Output:Variable']
        }

        # Add all EMS variables created above
        for outvar in [v.Name for v in building.idfobjects['EnergyManagementSystem:OutputVariable']]:
            key = _var_key('*', outvar, freq_cap)
            if key not in existing_output_keys and not outvar.startswith("WIP"):
                building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=outvar, Reporting_Frequency=freq_cap)
                existing_output_keys.add(key)
                if verbose_mode: print(f"Added Output:Variable for {outvar} ({freq})")
            elif key in existing_output_keys:
                warnings.warn(f"Output:Variable already exists for '{outvar}' ({freq_cap}). Skipping.")

        # Add Schedule Values (using RAW zone names)
        for i in ['PMV_H_SP', 'PMV_C_SP']:
            for zone in unique_zones:
                sch_name = f'{i}_{zone}'
                key = _var_key(sch_name, 'Schedule Value', freq_cap)
                if key not in existing_output_keys:
                    building.newidfobject('Output:Variable', Key_Value=sch_name, Variable_Name='Schedule Value', Reporting_Frequency=freq_cap)
                    existing_output_keys.add(key)
                    if verbose_mode: print(f"Added Output:Variable for Schedule {sch_name} ({freq})")
                else:
                    warnings.warn(f"Output:Variable already exists for Schedule '{sch_name}' ({freq_cap}). Skipping.")

        # Add additional comfort outputs if requested
        if other_PMV_related_outputs:
            additional = ['Zone Operative Temperature', 'Zone Thermal Comfort Fanger Model PMV', 'Zone Thermal Comfort Fanger Model PPD', 'Zone Mean Air Temperature']
            for item in additional:
                key = _var_key('*', item, freq_cap)
                if key not in existing_output_keys:
                    building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=item, Reporting_Frequency=freq_cap)
                    existing_output_keys.add(key)
                    if verbose_mode: print(f"Added Output:Variable for {item} ({freq})")
                else:
                    warnings.warn(f"Output:Variable already exists for '{item}' ({freq_cap}). Skipping.")

        # 3. Add Output:Meter objects
        meter_objects = [
            'EnergyTransfer:HVAC',
            'Heating:EnergyTransfer',
            'Cooling:EnergyTransfer',
            'Heating:Electricity',
            'Cooling:Electricity',
            'Electricity:HVAC',
            'DistrictHeating:Facility',
            'DistrictCooling:Facility'
        ]

        for freq in outputs_freq:
            # Get existing meters for this frequency to avoid duplicates
            # Note: Key_Name is the field for the meter name
            current_meters = [
                m.Key_Name for m in building.idfobjects['Output:Meter']
                if m.Reporting_Frequency.upper() == freq.upper()
            ]

            for meter in meter_objects:
                if meter not in current_meters:
                    building.newidfobject(
                        'Output:Meter',
                        Key_Name=meter,
                        Reporting_Frequency=freq.capitalize()
                    )
                    if verbose_mode:
                        print(f"Added Output:Meter for {meter} ({freq})")
                else:
                    warnings.warn(f"Output:Meter '{meter}' ({freq}) already exists. Skipping.")

    # 4. Ensure OutputControl:Files is present
    if not building.idfobjects['OutputControl:Files']:
        building.newidfobject('OutputControl:Files', Output_CSV='Yes', Output_MTR='Yes', Output_ESO='Yes')
        if verbose_mode: print("Added OutputControl:Files object")
    else:
        # Update existing object
        obj = building.idfobjects['OutputControl:Files'][0]
        obj.Output_CSV = 'Yes'
        obj.Output_MTR = 'Yes'
        obj.Output_ESO = 'Yes'
        if verbose_mode: print("Updated existing OutputControl:Files object")


# ==============================================================================
# UTILS
# ==============================================================================

def generate_df_from_args(
        target_keys_input: List[str],
        ems_suffixes: List[str],
        adap_coeff_cooling: Union[float, Dict[str, float]],
        adap_coeff_heating: Union[float, Dict[str, float]],
        pmv_cooling_sp: Union[float, Dict[str, float]],
        pmv_heating_sp: Union[float, Dict[str, float]],
        tolerance_cooling_sp_cooling_season: Union[float, Dict[str, float]],
        tolerance_cooling_sp_heating_season: Union[float, Dict[str, float]],
        tolerance_heating_sp_cooling_season: Union[float, Dict[str, float]],
        tolerance_heating_sp_heating_season: Union[float, Dict[str, float]],
        dflt_for_adap_coeff_cooling: float,
        dflt_for_adap_coeff_heating: float,
        dflt_for_pmv_cooling_sp: float,
        dflt_for_pmv_heating_sp: float,
        dflt_for_tolerance_cooling_sp_cooling_season: float,
        dflt_for_tolerance_cooling_sp_heating_season: float,
        dflt_for_tolerance_heating_sp_cooling_season: float,
        dflt_for_tolerance_heating_sp_heating_season: float,
) -> pd.DataFrame:
    """
    Maps user input arguments (which can be single floats or dictionaries) to the
    resolved target keys. It creates a pandas DataFrame where each row corresponds
    to a target (Space/Zone) and columns correspond to the simulation parameters.

    :param target_keys_input: List of unique keys identifying the targets (e.g., "Space1 People").
    :param ems_suffixes: List of sanitized suffixes corresponding to the keys (e.g., "Space1_People").
    :param adap_coeff_*: Adaptive coefficients for cooling/heating.
    :param pmv_*_sp: PMV setpoints for cooling/heating.
    :param tolerance_*: Tolerance bands for different seasons and modes.
    :param dflt_*: Default values to use if a specific key is missing in the dictionary inputs.
    :return: A pandas DataFrame indexed by target keys, containing all parameters and the 'underscore_zonename'.
    """

    space_ppl_names = target_keys_input

    def process_arg(arg_val, arg_name, default_val):
        """Internal helper to normalize float/dict inputs into a Series."""
        data = {}
        if isinstance(arg_val, dict):
            # Validate keys
            valid_keys = [k for k in arg_val if k in space_ppl_names]
            dropped = [k for k in arg_val if k not in space_ppl_names]

            if dropped:
                warnings.warn(f"The following keys in '{arg_name}' were not found in the model and will be ignored: {dropped}")

            # Fill data, using default if key is missing
            for k in space_ppl_names:
                data[k] = arg_val.get(k, default_val)
        else:
            # Apply single float value to all targets
            for k in space_ppl_names:
                data[k] = arg_val
        return pd.Series(data, name=arg_name)

    # Process all arguments into Series
    series_list = [
        process_arg(adap_coeff_cooling, 'adap_coeff_cooling', dflt_for_adap_coeff_cooling),
        process_arg(adap_coeff_heating, 'adap_coeff_heating', dflt_for_adap_coeff_heating),
        process_arg(pmv_cooling_sp, 'pmv_cooling_sp', dflt_for_pmv_cooling_sp),
        process_arg(pmv_heating_sp, 'pmv_heating_sp', dflt_for_pmv_heating_sp),
        process_arg(tolerance_cooling_sp_cooling_season, 'tolerance_cooling_sp_cooling_season', dflt_for_tolerance_cooling_sp_cooling_season),
        process_arg(tolerance_cooling_sp_heating_season, 'tolerance_cooling_sp_heating_season', dflt_for_tolerance_cooling_sp_heating_season),
        process_arg(tolerance_heating_sp_cooling_season, 'tolerance_heating_sp_cooling_season', dflt_for_tolerance_heating_sp_cooling_season),
        process_arg(tolerance_heating_sp_heating_season, 'tolerance_heating_sp_heating_season', dflt_for_tolerance_heating_sp_heating_season),
    ]

    # Concatenate into a single DataFrame
    df_arguments = pd.concat(series_list, axis=1)

    # Map the sanitized suffixes to the DataFrame for easy access later
    suffix_map = dict(zip(target_keys_input, ems_suffixes))
    df_arguments['underscore_zonename'] = df_arguments.index.map(suffix_map)

    return df_arguments


def get_available_target_names(building: IDF) -> List[str]:
    """
    Identifies and returns a list of valid target names (keys) for the current model.
    These keys are what the user should use in the input dictionaries (e.g., adap_coeff_cooling).

    :param building: The BESOS/eppy IDF object.
    :return: A list of strings representing the valid keys (e.g., ['Space1 People', 'Space2 People']).
    """
    targets = _resolve_targets(building)
    return [t['df_key'] for t in targets]


def get_input_template_dictionary(building: IDF) -> Dict[str, str]:
    """
    Generates a template dictionary with all valid target keys and placeholder values.
    Useful for the user to know exactly which keys to populate.

    :param building: The BESOS/eppy IDF object.
    :return: A dictionary {target_name: "replace-me-with-float-value"}.
    """
    keys = get_available_target_names(building)
    return {key: "replace-me-with-float-value" for key in keys}


def set_zones_always_occupied(building: IDF, verbose_mode: bool = True):
    """
    Sets the occupancy schedule of all 'People' objects to 'On' (always occupied).
    If the 'On' schedule does not exist, it creates it.

    :param building: The BESOS/eppy IDF object.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    sch_comp_objs = [i.Name for i in building.idfobjects['schedule:compact']]

    # Create 'On' schedule if missing
    if 'On' not in sch_comp_objs:
        building.newidfobject(
            'Schedule:Compact',
            Name='On',
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,1'
        )
        if verbose_mode:
            print("Added Schedule: On")
    else:
        warnings.warn("Schedule 'On' already exists. Using existing schedule.")

    # Apply to all People objects
    for i in building.idfobjects['people']:
        i.Number_of_People_Schedule_Name = 'On'

    if verbose_mode:
        print("Updated all People objects to use schedule 'On'.")


def add_vrf_system(
        building: IDF,
        supply_air_temp_method: str = 'supply air temperature',
        eer: float = 2,
        cop: float = 2.1,
        vrf_schedule: str = 'On 24/7',
        verbose_mode: bool = True,
):
    """
    Adds a Variable Refrigerant Flow (VRF) system to the model using the accim_Main module.
    This is a helper wrapper to facilitate HVAC integration.

    :param building: The BESOS/eppy IDF object.
    :param SupplyAirTempInputMethod: Method for supply air temperature ('supply air temperature' or 'temperature difference').
    :param eer: Energy Efficiency Ratio for cooling.
    :param cop: Coefficient of Performance for heating.
    :param VRFschedule: Name of the availability schedule for the VRF system.
    :param verbose_mode: If True, prints progress from the accim_Main job.
    """
    energyplus_version = f'{building.idd_version[0]}.{building.idd_version[1]}'

    z = accim_Main.AccimJobInMemory(
        idf_class_instance=building,
        script_type='vrf_ac',
        energyplus_version=energyplus_version,
        temp_control='pmv',
        verbose=verbose_mode
    )

    z.set_comfort_fields_people(energyplus_version=energyplus_version, temp_control='pmv', verbose=verbose_mode)
    z.set_pmv_setpoint(verbose=verbose_mode)
    z.add_base_schedules(verbose=verbose_mode)
    z.set_availability_schedule_on(verbose=verbose_mode)
    z.add_vrf_system_schedule(verbose=verbose_mode)
    z.add_curve_objects(verbose=verbose_mode)
    z.add_detailed_hvac_objects(
        energyplus_version=energyplus_version,
        verbose=verbose_mode,
        supply_air_temp_method=supply_air_temp_method,
        eer=eer,
        cop=cop,
        vrf_schedule=vrf_schedule
    )
    z.add_forscript_schedule_vrf(verbose=verbose_mode)


def change_adaptive_coeff(building: IDF, df_arguments: pd.DataFrame):
    """
    Updates the adaptive coefficients in the existing EMS programs based on a new DataFrame.
    This allows modifying parameters (e.g., for optimization) without regenerating the
    entire EMS structure from scratch.

    :param building: The BESOS/eppy IDF object.
    :param df_arguments: DataFrame containing the new coefficients, indexed by target key.
    """
    for i in df_arguments.index:
        zonename = df_arguments.loc[i, 'underscore_zonename']

        # Find the specific program for this zone/space
        program = [p for p in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name and zonename.lower() in p.Name.lower()]

        if program:
            # Update the lines corresponding to adaptive coefficients
            program[0].Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {df_arguments.loc[i, "adap_coeff_cooling"]}'
            program[0].Program_Line_2 = f'set adap_coeff_heating_{zonename} = {df_arguments.loc[i, "adap_coeff_heating"]}'


def add_ems_debug_output(building: IDF, verbose_mode: bool = True):
    """
    Adds an Output:EnergyManagementSystem object to the IDF.

    This object enables verbose reporting in the EnergyPlus output files (specifically
    the .edd file). It is essential for debugging EMS scripts, as it lists all
    available actuators, internal variables, and runtime errors.

    Configuration applied:
    - Actuator Availability: Verbose
    - Internal Variable Availability: Verbose
    - EMS Runtime Language Debug Output Level: Verbose

    :param building: The BESOS/eppy IDF object.
    :param verbose_mode: If True, prints success messages. Warnings are always printed.
    """
    # Check if the object already exists to avoid duplicates
    output_ems_objs = [i for i in building.idfobjects['Output:EnergyManagementSystem']]

    if len(output_ems_objs) == 0:
        building.newidfobject(
            key='Output:EnergyManagementSystem',
            Actuator_Availability_Dictionary_Reporting='Verbose',
            Internal_Variable_Availability_Dictionary_Reporting='Verbose',
            EMS_Runtime_Language_Debug_Output_Level='Verbose'
        )
        if verbose_mode:
            print("Added Output:EnergyManagementSystem object (Verbose Debugging)")
    else:
        # Warn if it already exists, as it might have different settings
        warnings.warn("Output:EnergyManagementSystem object already exists. Skipping creation.")


def set_pmv_input_parameters(
        building: besos.IDF_class,
        activity_level: Optional[Union[float, Dict[str, float]]] = None,
        clothing_insulation: Optional[Union[float, Dict[str, float]]] = None,
        air_velocity: Optional[Union[float, Dict[str, float]]] = None,
        work_efficiency: Optional[Union[float, Dict[str, float]]] = None,
        verbose_mode: bool = True
):
    """
    Modifies 'People' objects in the IDF to set the parameters that influence the PMV calculation.

    It creates 'Schedule:Compact' objects for the specified parameters and assigns them
    to the People objects.

    IMPORTANT: If a parameter is set to None (default), it will NOT be modified in the IDF.
    This allows you to update only specific parameters (e.g., just air velocity) without
    overwriting existing schedules for activity or clothing.

    :param building: The BESOS/eppy IDF object.
    :param activity_level: Metabolic rate in W/person. If None, ignores this parameter.
    :param clothing_insulation: Clothing insulation in clo units. If None, ignores this parameter.
    :param air_velocity: Air velocity in m/s. If None, ignores this parameter.
    :param work_efficiency: Work efficiency (0.0 - 1.0). If None, ignores this parameter.
    :param verbose_mode: If True, prints created schedules to console.
    """

    # 1. Resolve targets to map People objects to Data Keys
    target_data = _resolve_targets(building)
    df_keys = [t['df_key'] for t in target_data]

    # Helper to map input args (Float, Dict, or None) to a lookup dictionary
    def map_arg_to_lookup(arg_val, arg_name):
        data = {}
        if arg_val is None:
            return data  # Empty dict will return None on .get()

        if isinstance(arg_val, dict):
            # Validate keys
            valid_keys = [k for k in arg_val if k in df_keys]
            dropped = [k for k in arg_val if k not in df_keys]
            if dropped:
                warnings.warn(f"Keys dropped from {arg_name}: {dropped}")

            for k in df_keys:
                data[k] = arg_val.get(k, None)  # None if key missing in user dict
        else:
            # Apply single float value to all targets
            for k in df_keys:
                data[k] = arg_val
        return data

    val_map_activity = map_arg_to_lookup(activity_level, 'activity')
    val_map_clo = map_arg_to_lookup(clothing_insulation, 'clo')
    val_map_vel = map_arg_to_lookup(air_velocity, 'vel')
    val_map_eff = map_arg_to_lookup(work_efficiency, 'eff')

    # 2. Prepare Lookups for People -> Key matching
    # (Re-using logic to identify where the person is located)
    zone_lists = {zl.Name.upper().strip(): zl for zl in building.idfobjects['ZONELIST']}
    space_lists = {}
    space_to_zone = {}
    try:
        space_lists = {sl.Name.upper().strip(): sl for sl in building.idfobjects['SPACELIST']}
        for s in building.idfobjects['SPACE']:
            space_to_zone[s.Name.upper().strip()] = s.Zone_Name
    except KeyError:
        pass

    def get_first_item_from_list(obj, field_prefix):
        try:
            return obj[f"{field_prefix}_1_Name"]
        except:
            return None

    sch_comp_objs = [s.Name for s in building.idfobjects['Schedule:Compact']]

    # 3. Iterate over People objects
    for people in building.idfobjects['PEOPLE']:
        p_name = people.Name

        # --- A. Find the Target Key for this Person ---
        container_name = ""
        try:
            container_name = people.Zone_or_ZoneList_Name
        except:
            try:
                container_name = people.Zone_or_ZoneList_or_Space_or_SpaceList_Name
            except:
                container_name = people.Zone_Name

        if not container_name: continue
        c_name_upper = container_name.upper().strip()

        target_key = None

        # Logic to find ONE valid key to retrieve the value
        if c_name_upper in space_lists:
            first_space = get_first_item_from_list(space_lists[c_name_upper], "Space")
            if first_space: target_key = f"{first_space} {p_name}"
        elif c_name_upper in space_to_zone:
            target_key = f"{container_name} {p_name}"
        elif c_name_upper in zone_lists:
            first_zone = get_first_item_from_list(zone_lists[c_name_upper], "Zone")
            if first_zone: target_key = f"{first_zone} {p_name}"
        else:
            # Direct Zone: Try both patterns
            candidate_1 = f"{container_name} {p_name}"
            candidate_2 = container_name
            if candidate_1 in df_keys:
                target_key = candidate_1
            elif candidate_2 in df_keys:
                target_key = candidate_2

        if not target_key:
            # If we can't map the person, we can't apply parameters
            continue

        # --- B. Retrieve Values ---
        # If the user didn't provide the arg, these will be None
        act_val = val_map_activity.get(target_key)
        clo_val = val_map_clo.get(target_key)
        vel_val = val_map_vel.get(target_key)
        eff_val = val_map_eff.get(target_key)

        # Sanitized name for schedules
        p_name_san = _sanitize_ems_name(p_name)
        any_modified = False

        # --- C. Apply Changes (Only if value is not None) ---

        # 1. Activity Level
        if act_val is not None:
            sch_name = f"Sch_Act_{p_name_san}"
            if sch_name not in sch_comp_objs:
                building.newidfobject('Schedule:Compact', Name=sch_name, Schedule_Type_Limits_Name="Any Number",
                                      Field_1='Through: 12/31', Field_2='For: AllDays', Field_3=f'Until: 24:00,{act_val}')
                sch_comp_objs.append(sch_name)
                if verbose_mode: print(f"Set Activity for '{p_name}': {act_val} W/person")

            people.Activity_Level_Schedule_Name = sch_name
            any_modified = True

        # 2. Clothing Insulation
        if clo_val is not None:
            sch_name = f"Sch_Clo_{p_name_san}"
            if sch_name not in sch_comp_objs:
                building.newidfobject('Schedule:Compact', Name=sch_name, Schedule_Type_Limits_Name="Any Number",
                                      Field_1='Through: 12/31', Field_2='For: AllDays', Field_3=f'Until: 24:00,{clo_val}')
                sch_comp_objs.append(sch_name)
                if verbose_mode: print(f"Set Clothing for '{p_name}': {clo_val} clo")

            # people.Clothing_Insulation_Calculation_Method = 'Schedule'
            # people.Clothing_Insulation_Calculation_Method_Schedule_Name = sch_name
            people.Clothing_Insulation_Schedule_Name = sch_name  # Some versions use this field
            any_modified = True

        # 3. Air Velocity
        if vel_val is not None:
            sch_name = f"Sch_Vel_{p_name_san}"
            if sch_name not in sch_comp_objs:
                building.newidfobject('Schedule:Compact', Name=sch_name, Schedule_Type_Limits_Name="Any Number",
                                      Field_1='Through: 12/31', Field_2='For: AllDays', Field_3=f'Until: 24:00,{vel_val}')
                sch_comp_objs.append(sch_name)
                if verbose_mode: print(f"Set Air Velocity for '{p_name}': {vel_val} m/s")

            people.Air_Velocity_Schedule_Name = sch_name
            any_modified = True

        # 4. Work Efficiency
        if eff_val is not None:
            sch_name = f"Sch_Eff_{p_name_san}"
            if sch_name not in sch_comp_objs:
                building.newidfobject('Schedule:Compact', Name=sch_name, Schedule_Type_Limits_Name="Any Number",
                                      Field_1='Through: 12/31', Field_2='For: AllDays', Field_3=f'Until: 24:00,{eff_val}')
                sch_comp_objs.append(sch_name)
                if verbose_mode: print(f"Set Work Efficiency for '{p_name}': {eff_val}")

            people.Work_Efficiency_Schedule_Name = sch_name
            any_modified = True

        # --- D. Ensure Fanger Model ---
        # Only force Fanger if we actually touched this object
        if any_modified:
            people.Thermal_Comfort_Model_1_Type = 'Fanger'