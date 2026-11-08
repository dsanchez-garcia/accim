# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Setpoints based on indices derived from the predicted mean vote (PMV) of Fanger.

The thermal comfort thermostats of EnergyPlus (``ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint``) keep the PMV
of each zone between a heating and a cooling setpoint. :func:`apply_pmv_index_setpoints` adds these thermostats and the
EMS programs that, at each timestep, convert the setpoints of an index derived from the PMV into the PMV setpoints of
the thermostats, and report the index of each zone and the hours within its setpoints. The indices of
:data:`PMV_INDICES` share all the EMS objects; only these lines depend on the index (:class:`PmvIndex`): the
coefficient of the season, the inverse of the index (the PMV whose index is the setpoint) and the monitor (the index of
the PMV of the zone).

- ``'apmv'``: the adaptive PMV of Yao et al. (2009), aPMV = PMV/(1 + λ·PMV), with the adaptive coefficient λ of the
  season; the PMV setpoint is aPMV/(1 − λ·aPMV).
- ``'pmv'``: the PMV itself; the setpoints are PMV setpoints.

:func:`accim.sim.apmv.apply_apmv_setpoints` and :func:`accim.sim.apmv.apply_pmv_setpoints` apply them with the
arguments of each index.
"""

import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import pandas as pd

from accim.sim.ems.programs import add_program
from accim.sim.ems.setast import COOLING_SEASON_LINES
from accim.sim.targets import resolve_targets
from accim.utils.editing import transform_ddmm_to_int

__all__ = [
    'IndexParameter',
    'PMV_INDICES',
    'PmvIndex',
    'apply_pmv_index_setpoints',
    'arguments_table',
    'get_pmv_index',
    'program_names',
]

#: The eppy or besos IDF object of a model
IDF = Any
#: The value of an argument of the setpoints: one number for all the zones, or a dictionary {zone: number}
ZoneValue = Union[float, Dict[str, float]]

#: The tolerances of the setpoints: the argument, the prefix of its EMS variable, and its default value
_TOLERANCES = (
    ('cooling_setpoint_tolerance_cooling_season', 'tolerance_cooling_sp_cooling_season', -0.1),
    ('cooling_setpoint_tolerance_heating_season', 'tolerance_cooling_sp_heating_season', -0.1),
    ('heating_setpoint_tolerance_cooling_season', 'tolerance_heating_sp_cooling_season', 0.1),
    ('heating_setpoint_tolerance_heating_season', 'tolerance_heating_sp_heating_season', 0.1),
)
#: The hour counters of each zone: the name of the EMS output variable and the prefix of its EMS variable
_COUNTERS = (
    ('Comfortable Hours', 'comfhour'),
    ('Discomfortable Hot Hours', 'discomfhour_heat'),
    ('Discomfortable Cold Hours', 'discomfhour_cold'),
    ('Discomfortable Total Hours', 'discomfhour'),
    ('Occupied hours', 'occupied_hour'),
)


@dataclass(frozen=True)
class IndexParameter:
    """An argument of an index with a value for each zone, which the EMS program ``set_zone_input_data_<zone>`` sets.

    :ivar argument: The name of the argument (and of its column in :func:`arguments_table`).
    :ivar variable: The prefix of its EMS global variable (``<variable>_<zone>``).
    :ivar default: Its default value.
    :ivar default_for_missing: Its default value for the zones missing in a dictionary (the argument
        ``default_<argument>``).
    """

    argument: str
    variable: str
    default: float
    default_for_missing: float


def _identity(side: str, setpoint: str, suffix: str, options: Mapping[str, Any]) -> str:
    return setpoint


@dataclass(frozen=True)
class PmvIndex:
    """An index derived from the PMV, and the Erl code that depends on it.

    :ivar key: The key of the index in :data:`PMV_INDICES` ('apmv').
    :ivar name: Its name in the EMS objects ('aPMV'): ``<name>_<zone>`` is the index of the zone, ``<name>_H_SP_<zone>``
        and ``<name>_C_SP_<zone>`` its setpoints, and ``apply_<name>_<zone>``, ``monitor_<name>_<zone>`` and
        ``count_<name>_comfort_hours_<zone>`` its programs.
    :ivar description: What the index is, with its source.
    :ivar parameters: Its arguments with a value for each zone.
    :ivar coefficient: The EMS variable of the coefficient of the current season (``<coefficient>_<zone>``), if the
        index has one, and ``coefficient_output`` the name of its EMS output variable.
    :ivar cooling_season_coefficient: The value of the coefficient in the cooling season, an Erl expression in which
        ``{s}`` is the suffix of the zone; and ``heating_season_coefficient``, in the heating season.
    :ivar global_variables: The prefixes of the EMS global variables of the coefficient and the parameters, in the
        order in which they are declared.
    :ivar inverse: The Erl expression of the PMV setpoint of the thermostat from a setpoint of the index,
        ``inverse(side, setpoint, suffix, options)``: ``side`` is 'H' (heating) or 'C' (cooling), and ``setpoint`` the
        Erl variable of the setpoint of the index.
    :ivar monitor: The Erl lines that set the index of the zone (``<name>_<zone>``) from its PMV (``PMV_<zone>``),
        ``monitor(suffix, options)``; None if the index is the PMV.
    :ivar options: The other parameters of the index (one value for all the zones), with their default values.
    :ivar validate: A function that checks the parameters and options, ``validate(values, options)``, where
        ``values`` has the value of each parameter and of its ``default_<argument>``.
    """

    key: str
    name: str
    description: str
    parameters: Tuple[IndexParameter, ...] = ()
    coefficient: Optional[str] = None
    coefficient_output: Optional[str] = None
    cooling_season_coefficient: Optional[str] = None
    heating_season_coefficient: Optional[str] = None
    global_variables: Tuple[str, ...] = ()
    inverse: Callable[[str, str, str, Mapping[str, Any]], str] = _identity
    monitor: Optional[Callable[[str, Mapping[str, Any]], List[str]]] = None
    options: Mapping[str, Any] = field(default_factory=dict)
    validate: Optional[Callable[[Mapping[str, Any], Mapping[str, Any]], None]] = None


def _apmv_inverse(side: str, setpoint: str, suffix: str, options: Mapping[str, Any]) -> str:
    # The PMV whose aPMV = PMV/(1 + lambda*PMV) is the setpoint
    return f'{setpoint}/(1-adap_coeff_{suffix}*{setpoint})'


def _apmv_monitor(suffix: str, options: Mapping[str, Any]) -> List[str]:
    return [f'set aPMV_{suffix} = PMV_{suffix}/(1+adap_coeff_{suffix}*PMV_{suffix})']


#: The indices derived from the PMV, by key.
PMV_INDICES: Dict[str, PmvIndex] = {
    'apmv': PmvIndex(
        key='apmv',
        name='aPMV',
        description='adaptive predicted mean vote (Yao et al., 2009): aPMV = PMV/(1 + lambda*PMV)',
        parameters=(
            IndexParameter('adaptive_coefficient_cooling', 'adap_coeff_cooling', 0.293, 0.4),
            IndexParameter('adaptive_coefficient_heating', 'adap_coeff_heating', -0.293, -0.4),
        ),
        coefficient='adap_coeff',
        coefficient_output='Adaptive Coefficient',
        cooling_season_coefficient='adap_coeff_cooling_{s}',
        heating_season_coefficient='adap_coeff_heating_{s}',
        global_variables=('adap_coeff', 'adap_coeff_heating', 'adap_coeff_cooling'),
        inverse=_apmv_inverse,
        monitor=_apmv_monitor,
    ),
    'pmv': PmvIndex(
        key='pmv',
        name='PMV',
        description='predicted mean vote (Fanger, 1970), as ISO 7730 and EN 16798-1',
    ),
}


def get_pmv_index(index: str) -> PmvIndex:
    """The index derived from the PMV of a key of :data:`PMV_INDICES` (in upper or lower case).

    :raises ValueError: If the key is not that of an index.
    """
    pmv_index = PMV_INDICES.get(str(index).lower())
    if pmv_index is None:
        raise ValueError(f'{index!r} is not an index derived from the PMV; the indices are {list(PMV_INDICES)}.')
    return pmv_index


def _resolve_targets(building: IDF) -> List[Dict[str, Any]]:
    """The targets of the EMS (see :func:`accim.sim.targets.resolve_targets`), as dictionaries."""
    return [target.as_dict() for target in resolve_targets(building)]


def _index_values(pmv_index: PmvIndex, index_parameters: Optional[Mapping[str, Any]]
                  ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """The values of the parameters of an index (with their ``default_<argument>``) and of its options."""
    given = dict(index_parameters or {})
    valid = ([p.argument for p in pmv_index.parameters] + [f'default_{p.argument}' for p in pmv_index.parameters]
             + list(pmv_index.options))
    unknown = [name for name in given if name not in valid]
    if unknown:
        raise ValueError(f'{unknown} are not parameters of the index {pmv_index.key!r}, whose parameters are '
                         f'{valid or "none"}.')
    values = {}
    for parameter in pmv_index.parameters:
        values[parameter.argument] = given.get(parameter.argument, parameter.default)
        values[f'default_{parameter.argument}'] = given.get(f'default_{parameter.argument}',
                                                             parameter.default_for_missing)
    options = {name: given.get(name, default) for name, default in pmv_index.options.items()}
    if pmv_index.validate is not None:
        pmv_index.validate(values, options)
    return values, options


def _check_other_indices(building: IDF, pmv_index: PmvIndex, suffixes: Sequence[str]) -> None:
    """Stop if the model has the setpoints of another index: both would actuate the same thermostats."""
    programs = {str(p.Name).upper() for p in building.idfobjects['EnergyManagementSystem:Program']}
    for other in PMV_INDICES.values():
        if other.key == pmv_index.key:
            continue
        zones = [suffix for suffix in suffixes if f'APPLY_{other.name}_{suffix}'.upper() in programs]
        if zones:
            raise ValueError(f'The model already has the setpoints of the {other.name} in {zones}: the setpoints of '
                             f'the {pmv_index.name} would actuate the same thermostats. Apply them to a model without '
                             f'the setpoints of other indices.')


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================

def apply_pmv_index_setpoints(
        building: IDF,
        index: str = 'apmv',
        index_parameters: Optional[Mapping[str, Any]] = None,
        output_frequencies: Sequence[str] = ('hourly',),
        other_pmv_related_outputs: bool = True,
        pmv_cooling_setpoint: ZoneValue = 0.5,
        pmv_heating_setpoint: ZoneValue = -0.5,
        cooling_setpoint_tolerance_cooling_season: ZoneValue = -0.1,
        cooling_setpoint_tolerance_heating_season: ZoneValue = -0.1,
        heating_setpoint_tolerance_cooling_season: ZoneValue = 0.1,
        heating_setpoint_tolerance_heating_season: ZoneValue = 0.1,
        cooling_season_start: Union[float, str] = 121,
        cooling_season_end: Union[float, str] = 274,
        default_pmv_cooling_setpoint: float = 0.5,
        default_pmv_heating_setpoint: float = -0.5,
        default_cooling_setpoint_tolerance_cooling_season: float = -0.1,
        default_cooling_setpoint_tolerance_heating_season: float = -0.1,
        default_heating_setpoint_tolerance_cooling_season: float = 0.1,
        default_heating_setpoint_tolerance_heating_season: float = 0.1,
        verbose: bool = True,
) -> IDF:
    """
    Applies setpoints based on an index derived from the PMV of Fanger (see :data:`PMV_INDICES`).

    Each occupied zone gets a thermal comfort thermostat (Fanger, dual setpoint) whose PMV setpoints are schedules
    (``PMV_H_SP_<zone>`` and ``PMV_C_SP_<zone>``) that EMS programs set at each timestep: while the zone is occupied,
    the PMV whose index is the setpoint of the index (with its tolerance), and -100 and 100 otherwise. The EMS programs
    also report the index of each zone and count the hours within its setpoints. The model needs an HVAC system in
    each zone (see :func:`accim.sim.apmv.add_vrf_system`).

    It supports both legacy EnergyPlus versions (Zone-based) and modern versions (Space-based), resolving the
    hierarchy of the model (see :func:`accim.sim.targets.resolve_targets`); a zone with several occupant instances
    is controlled as a whole, with the PMV of its occupants averaged (weighted by their number).

    :param building: The eppy or besos IDF object to be modified.
    :param index: The key of the index in :data:`PMV_INDICES`: 'apmv' or 'pmv'.
    :param index_parameters: The parameters of the index (:attr:`PmvIndex.parameters`, each with its
        ``default_<argument>``, and :attr:`PmvIndex.options`); those not given take their default values.
    :param output_frequencies: The reporting frequencies of the outputs (e.g., ['hourly', 'timestep']).
    :param other_pmv_related_outputs: If True, adds other outputs of the comfort of the zones (Fanger PMV and PPD,
        operative and air temperatures).
    :param pmv_cooling_setpoint: The cooling setpoint, on the scale of the index: one number, or a dict
        {zone: number} (see :func:`accim.sim.apmv.get_available_target_names`).
    :param pmv_heating_setpoint: The heating setpoint, on the scale of the index. Number or dict.
    :param cooling_setpoint_tolerance_cooling_season: The tolerance added to the cooling setpoint in the cooling
        season. Number or dict.
    :param cooling_setpoint_tolerance_heating_season: The tolerance added to the cooling setpoint in the heating
        season. Number or dict.
    :param heating_setpoint_tolerance_cooling_season: The tolerance added to the heating setpoint in the cooling
        season. Number or dict.
    :param heating_setpoint_tolerance_heating_season: The tolerance added to the heating setpoint in the heating
        season. Number or dict.
    :param cooling_season_start: The first day of the cooling season: the day of the year or 'dd/mm'.
    :param cooling_season_end: The day after the last day of the cooling season: the day of the year or 'dd/mm'.
    :param default_pmv_cooling_setpoint: The cooling setpoint of the zones missing in the dict of
        ``pmv_cooling_setpoint`` (and the other ``default_*`` arguments, for the other arguments).
    :param verbose: If True, prints the objects that are added. The warnings are always issued.
    :return: The modified IDF object.
    :raises ValueError: If the index or its parameters are not valid, or the model has the setpoints of another index.
    """
    pmv_index = get_pmv_index(index)
    values, options = _index_values(pmv_index, index_parameters)

    # --- 1. RESOLVE TARGETS ---
    # The zones that the EMS controls, from the People objects of the model (and its People:Instance objects, in
    # EnergyPlus 26.2):
    # - ems_suffixes: the names of the zones in the EMS objects (e.g., "Space1_People1").
    # - df_keys: the names of the zones in the dictionaries of arguments (e.g., "Space1 People1").
    # - instance_counts: the number of occupant instances of the zones with several, whose PMV is averaged.
    target_data = _resolve_targets(building)
    ems_suffixes = [t['ems_suffix'] for t in target_data]
    df_keys = [t['df_key'] for t in target_data]
    instance_counts = {t['ems_suffix']: len(t['instance_keys']) for t in target_data if len(t['instance_keys']) > 1}
    # The schedules and thermostats belong to the zones, even if the comfort is calculated for each space
    unique_zones = list(dict.fromkeys(t['zone_name'] for t in target_data))
    _check_other_indices(building, pmv_index, ems_suffixes)

    # --- 2. PREPARE DATA ---
    # The dates 'dd/mm' as days of the year (e.g., "01/05" is 121)
    if isinstance(cooling_season_start, str):
        cooling_season_start = transform_ddmm_to_int(cooling_season_start)
    if isinstance(cooling_season_end, str):
        cooling_season_end = transform_ddmm_to_int(cooling_season_end)

    # --- 3. ENSURE INFRASTRUCTURE ---
    # The setpoint schedules that the EMS actuates, and the thermal comfort thermostats (Fanger, dual setpoint)
    _ensure_infrastructure(building, unique_zones, verbose)

    # --- 4. ARGUMENTS OF EACH ZONE ---
    # A table with a row for each zone and a column for each argument
    arguments = [(p.argument, values[p.argument], values[f'default_{p.argument}']) for p in pmv_index.parameters]
    arguments += [
        ('pmv_cooling_setpoint', pmv_cooling_setpoint, default_pmv_cooling_setpoint),
        ('pmv_heating_setpoint', pmv_heating_setpoint, default_pmv_heating_setpoint),
        ('cooling_setpoint_tolerance_cooling_season', cooling_setpoint_tolerance_cooling_season,
         default_cooling_setpoint_tolerance_cooling_season),
        ('cooling_setpoint_tolerance_heating_season', cooling_setpoint_tolerance_heating_season,
         default_cooling_setpoint_tolerance_heating_season),
        ('heating_setpoint_tolerance_cooling_season', heating_setpoint_tolerance_cooling_season,
         default_heating_setpoint_tolerance_cooling_season),
        ('heating_setpoint_tolerance_heating_season', heating_setpoint_tolerance_heating_season,
         default_heating_setpoint_tolerance_heating_season),
    ]
    df_arguments = arguments_table(df_keys, ems_suffixes, arguments)

    # --- 5. EMS OBJECTS ---
    # A. Sensors: the PMV ('Zone Thermal Comfort Fanger Model PMV') and the occupants ('People Occupant Count').
    _add_sensors(building, target_data, verbose)
    # B. Global variables: the arguments, the setpoints, the index, the hour counters...
    _add_global_variables(building, pmv_index, ems_suffixes, verbose, list(instance_counts))
    # C. Actuators: the values of the setpoint schedules of each zone.
    _add_actuators(building, target_data, verbose)
    # D. Programs: the cooling season, the arguments of each zone, its setpoints, its index and its hours.
    _add_programs(building, pmv_index, options, ems_suffixes, df_arguments, cooling_season_start, cooling_season_end,
                  verbose, instance_counts)
    # E. Program calling managers: the programs run at the beginning of each timestep (BeginTimestepBeforePredictor).
    _add_program_calling_managers(building, verbose, program_names(pmv_index, ems_suffixes, instance_counts))
    # F. Outputs: the EMS variables and the standard variables.
    _add_outputs(building, pmv_index, output_frequencies, other_pmv_related_outputs, ems_suffixes, unique_zones,
                 verbose)

    return building


# ==============================================================================
# ARGUMENTS
# ==============================================================================

def arguments_table(target_keys: Sequence[str], ems_suffixes: Sequence[str],
                    arguments: Sequence[Tuple[str, Any, Any]]) -> pd.DataFrame:
    """
    The value of each argument of the setpoints in each zone: a table with a row for each zone (indexed by its key)
    and a column for each argument, and the column 'underscore_zonename' with the suffix of the zone in the EMS
    objects.

    :param target_keys: The keys of the zones (see :func:`accim.sim.apmv.get_available_target_names`).
    :param ems_suffixes: The suffixes of the zones in the EMS objects, in the same order.
    :param arguments: (name, value, default) of each argument: the value is one number for all the zones, or a dict
        {zone key: number} whose missing zones take the default. The keys that are not zones of the model are
        ignored, with a warning.
    :return: The table, as a pandas DataFrame.
    """
    space_ppl_names = list(target_keys)

    def process_arg(arg_val, arg_name, default_val):
        """Normalise a number or a dict into a Series indexed by the keys of the zones."""
        data = {}
        if isinstance(arg_val, dict):
            dropped = [k for k in arg_val if k not in space_ppl_names]
            if dropped:
                warnings.warn(f"The following keys in '{arg_name}' were not found in the model and will be "
                              f"ignored: {dropped}")
            for k in space_ppl_names:
                data[k] = arg_val.get(k, default_val)
        else:
            for k in space_ppl_names:
                data[k] = arg_val
        return pd.Series(data, name=arg_name)

    df_arguments = pd.concat([process_arg(value, name, default) for name, value, default in arguments], axis=1)
    suffix_map = dict(zip(target_keys, ems_suffixes))
    df_arguments['underscore_zonename'] = df_arguments.index.map(suffix_map)
    return df_arguments


# ==============================================================================
# INFRASTRUCTURE HELPERS
# ==============================================================================

def _ensure_infrastructure(building: IDF, unique_zones: List[str], verbose: bool):
    """
    Ensures that the necessary standard EnergyPlus objects exist for the target zones.
    Specifically, it creates or verifies:
    1. Schedule:Compact objects for Heating and Cooling setpoints.
    2. ZoneControl:Thermostat objects configured for 'ThermalComfort' control.

    IMPORTANT: These objects must use the RAW Zone Name (e.g., "Zone 1") to correctly
    link with the Zone object in the IDF.

    :param building: The BESOS/eppy IDF object to be modified.
    :param unique_zones: A list of RAW zone names (strings) derived from the targets.
    :param verbose: If True, prints success messages for created objects. Warnings are always printed.
    """
    # 1. Create Schedules (Using RAW Zone Name)
    # These are the "dummy" schedules that EMS will overwrite (Actuate) at every timestep.
    # We create one for Heating (PMV_H_SP) and one for Cooling (PMV_C_SP).
    for i in ['PMV_H_SP', 'PMV_C_SP']:
        for zone in unique_zones:
            sch_name = f'{i}_{zone}'
            if building.getobject('Schedule:Compact', sch_name) is None:
                building.newidfobject(
                    'Schedule:Compact',
                    Name=sch_name,
                    Schedule_Type_Limits_Name="Any Number",
                    Field_1='Through: 12/31',
                    Field_2='For: AllDays',
                    Field_3='Until: 24:00,1'  # Default value (will be overwritten by EMS)
                )
                if verbose:
                    print(f"Added Schedule: {sch_name}")
            else:
                # Warning is issued regardless of verbose
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
            _create_tc_thermostat(building, zone, verbose)

        # Case B: A Standard Thermostat exists (e.g., DualSetpoint).
        # Action: Remove the old standard thermostat and replace it with a Thermal Comfort one.
        # We replace it because a zone cannot have two active thermostat objects.
        elif z_upper in existing_thermostats and z_upper not in existing_tc_thermostats:
            old_t = existing_thermostats[z_upper]
            building.removeidfobject(old_t)
            if verbose:
                print(f"Removed existing Standard Thermostat for zone: {zone}")
            _create_tc_thermostat(building, zone, verbose)

        # Case C: A Thermal Comfort Thermostat already exists.
        # Action: Ensure it points to a Fanger DualSetpoint object and update that object
        # to use our new EMS-controlled schedules.
        elif z_upper in existing_tc_thermostats:
            tc_t = existing_tc_thermostats[z_upper]
            # Warning is issued regardless of verbose
            warnings.warn(f"Thermal Comfort Thermostat already exists for zone '{zone}'. Updating configuration.")

            # Ensure the control type schedule exists and is linked correctly.
            sch_name = _ensure_tc_control_schedule(building, zone, verbose)
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
            _update_fanger_object(building, fanger_name, zone, verbose)


def _create_tc_thermostat(building: IDF, zone: str, verbose: bool):
    """
    Creates a new ZoneControl:Thermostat:ThermalComfort object and its dependencies.

    :param building: The BESOS/eppy IDF object.
    :param zone: The RAW zone name.
    :param verbose: If True, prints success messages.
    """
    # 1. Create the Control Type Schedule (Type 4 = Thermal Comfort)
    sch_name = _ensure_tc_control_schedule(building, zone, verbose)

    # 2. Create the Thermostat Object linking the zone to the Fanger object
    building.newidfobject(
        'ZoneControl:Thermostat:ThermalComfort',
        Name=f'Thermostat Setpoint Dual Setpoint {zone}',
        Zone_or_ZoneList_Name=zone,
        Thermal_Comfort_Control_Type_Schedule_Name=sch_name,
        Thermal_Comfort_Control_1_Object_Type='ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
        Thermal_Comfort_Control_1_Name=f'Fanger Setpoint {zone}'
    )
    if verbose:
        print(f"Added Thermal Comfort Thermostat for zone: {zone}")

    # 3. Create the Fanger Setpoint object
    _update_fanger_object(building, f'Fanger Setpoint {zone}', zone, verbose)


def _ensure_tc_control_schedule(building: IDF, zone: str, verbose: bool) -> str:
    """Ensure thermal comfort control schedule exists for a zone and return its name."""
    sch_name = f'Thermal Comfort Control Type Schedule Name {zone}'
    if building.getobject('Schedule:Compact', sch_name) is None:
        building.newidfobject(
            'Schedule:Compact',
            Name=sch_name,
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,4'  # 4 maps to 'Thermal Comfort' control type in E+
        )
        if verbose:
            print(f"Added Control Type Schedule: {sch_name}")
    return sch_name


def _update_fanger_object(building: IDF, obj_name: str, zone: str, verbose: bool):
    """
    Creates or updates the 'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint' object.
    This object links the thermostat logic to the specific Heating/Cooling schedules.

    :param building: The BESOS/eppy IDF object.
    :param obj_name: Name of the Fanger object.
    :param zone: The RAW zone name used to find the correct schedules.
    :param verbose: If True, prints success messages.
    """
    # Create the object if it is not in the model
    fanger_obj = building.getobject('ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint', obj_name)
    if fanger_obj is None:
        fanger_obj = building.newidfobject(
            'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
            Name=obj_name
        )
        if verbose:
            print(f"Added Fanger DualSetpoint Object: {obj_name}")

    # Link the object to the EMS-controlled schedules we created in _ensure_infrastructure
    fanger_obj.Fanger_Thermal_Comfort_Heating_Schedule_Name = f'PMV_H_SP_{zone}'
    fanger_obj.Fanger_Thermal_Comfort_Cooling_Schedule_Name = f'PMV_C_SP_{zone}'


# ==============================================================================
# EMS GENERATORS
# ==============================================================================

def _add_sensors(building: IDF, target_data: List[Dict], verbose: bool):
    """
    Adds EnergyManagementSystem:Sensor objects to the IDF.
    Sensors allow the EMS to read data from EnergyPlus Output:Variables during the simulation.

    We need two sensors per target:
    1. PMV: To read the current 'Zone Thermal Comfort Fanger Model PMV'.
    2. Occupant Count: To determine if the space is occupied ('People Occupant Count').

    In a zone with several occupant instances, the Occupant Count sensor reads the
    'Zone People Occupant Count' of the zone, and each instance gets a PMV sensor and an
    Occupant Count sensor, numbered after the target suffix (e.g., "PMV_Zone1_2"), from which a
    program calculates the PMV of the zone (see _add_programs).

    :param building: The BESOS/eppy IDF object.
    :param target_data: List of target dictionaries resolved earlier.
    :param verbose: If True, prints success messages. Warnings are always printed.
    """
    def add_sensor(name, key, variable):
        if building.getobject('EnergyManagementSystem:Sensor', name) is None:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=name,
                OutputVariable_or_OutputMeter_Index_Key_Name=key,
                OutputVariable_or_OutputMeter_Name=variable
            )
            if verbose:
                print(f"Added Sensor: {name}")
        else:
            warnings.warn(f"Sensor '{name}' already exists. Skipping.")

    for target in target_data:
        suffix = target['ems_suffix']
        instance_keys = target['instance_keys']

        # 1. PMV Sensor (in zones with several instances, one per instance, with its occupant count)
        if len(instance_keys) == 1:
            add_sensor(f'PMV_{suffix}', target['sensor_key'], 'Zone Thermal Comfort Fanger Model PMV')
        else:
            for n, key in enumerate(instance_keys, start=1):
                add_sensor(f'PMV_{suffix}_{n}', key, 'Zone Thermal Comfort Fanger Model PMV')
                add_sensor(f'People_Occupant_Count_{suffix}_{n}', key, 'People Occupant Count')

        # 2. Occupant Count Sensor
        add_sensor(f'People_Occupant_Count_{suffix}', target['occupancy_key'], target['occupancy_variable'])


def _add_actuators(building: IDF, target_data: List[Dict], verbose: bool):
    """
    Adds EnergyManagementSystem:Actuator objects.

    The Actuator is the bridge between the EMS logic (which might run per Space/People)
    and the physical HVAC control (which runs per Zone Schedule). It allows the EMS
    to overwrite the value of the Schedule:Compact objects created in the infrastructure step.

    :param building: The BESOS/eppy IDF object.
    :param target_data: List of target dictionaries resolved earlier.
    :param verbose: If True, prints success messages. Warnings are always printed.
    """
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

            if building.getobject('EnergyManagementSystem:Actuator', act_name) is None:
                building.newidfobject(
                    'EnergyManagementSystem:Actuator',
                    Name=act_name,
                    # We actuate the 'Schedule Value' of the 'Schedule:Compact' object
                    Actuated_Component_Unique_Name=sch_name,
                    Actuated_Component_Type='Schedule:Compact',
                    Actuated_Component_Control_Type='Schedule Value',
                )
                if verbose:
                    print(f"Added Actuator: {act_name}")
            else:
                warnings.warn(f"Actuator '{act_name}' already exists. Skipping creation.")


def _add_global_variables(building: IDF, pmv_index: PmvIndex, suffixes: List[str], verbose: bool,
                          averaged_suffixes: Optional[List[str]] = None):
    """
    Adds EnergyManagementSystem:GlobalVariable objects.
    These variables store intermediate calculation results (like the index of each zone)
    and parameters (like tolerance or adaptive coefficients) that change dynamically.

    :param building: The BESOS/eppy IDF object.
    :param pmv_index: The index of the setpoints.
    :param suffixes: List of sanitized suffixes for unique naming per target.
    :param verbose: If True, prints success messages. Warnings are always printed.
    :param averaged_suffixes: Suffixes of the targets of zones with several occupant instances,
        whose PMV is a global variable calculated from the PMV of the instances.
    """
    # The prefixes of the variables of each zone (the names of the EMS variables of the aPMV keep those of accim 0.x).
    # The index of the zone is a global variable unless it is the PMV, which is the sensor PMV_<zone>.
    name = pmv_index.name
    prefixes = [
        'tolerance_cooling_sp', 'tolerance_cooling_sp_cooling_season', 'tolerance_cooling_sp_heating_season',
        'tolerance_heating_sp', 'tolerance_heating_sp_cooling_season', 'tolerance_heating_sp_heating_season',
        *pmv_index.global_variables,
        'pmv_heating_sp', 'pmv_cooling_sp', *([name] if pmv_index.monitor is not None else []),
        'comfhour', 'discomfhour', 'discomfhour_heat', 'discomfhour_cold', 'occupied_hour',
        f'{name}_H_SP', f'{name}_C_SP', f'{name}_H_SP_noTol', f'{name}_C_SP_noTol'
    ]

    existing = {gv.Erl_Variable_1_Name for gv in building.idfobjects['EnergyManagementSystem:GlobalVariable']}

    # 1. Global Season Variables (Shared across the whole building)
    for gv in ['CoolingSeason', 'CoolSeasonEnd', 'CoolSeasonStart']:
        if gv not in existing:
            building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=gv)
            if verbose:
                print(f"Added Global Variable: {gv}")
        else:
            warnings.warn(f"Global Variable '{gv}' already exists. Skipping.")

    # 2. Per-Target Variables (Specific to each Zone/Space), and the PMV of the zones with several instances
    per_target = [f'{prefix}_{suffix}' for prefix in prefixes for suffix in suffixes]
    per_target += [f'PMV_{suffix}' for suffix in (averaged_suffixes or [])]
    for gv in per_target:
        if gv not in existing:
            building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=gv)
            if verbose:
                print(f"Added Global Variable: {gv}")
        else:
            warnings.warn(f"Global Variable '{gv}' already exists. Skipping.")


def _add_programs(building: IDF, pmv_index: PmvIndex, options: Mapping[str, Any], suffixes: List[str],
                  df_arguments: pd.DataFrame, cool_start: int, cool_end: int, verbose: bool,
                  instance_counts: Optional[Dict[str, int]] = None):
    """
    Adds EnergyManagementSystem:Program objects.
    This contains the actual Erl (EnergyPlus Runtime Language) code that executes the control logic.

    :param building: The BESOS/eppy IDF object.
    :param pmv_index: The index of the setpoints, which gives the lines that depend on it.
    :param options: The options of the index.
    :param suffixes: List of sanitized suffixes.
    :param df_arguments: DataFrame containing user inputs (coeffs, setpoints) mapped to targets.
    :param cool_start: Integer representing the start day of cooling season.
    :param cool_end: Integer representing the end day of cooling season.
    :param verbose: If True, prints success messages. Warnings are always printed.
    :param instance_counts: Number of occupant instances of the targets of zones with several
        ({suffix: number}). The PMV of these zones is the average of the PMV of their instances,
        weighted by their occupants (the simple average while the zone is unoccupied), as the
        PeopleAverage method of the Fanger thermostats.
    """
    instance_counts = instance_counts or {}
    name = pmv_index.name

    def add(program_name: str, lines: Sequence[str]) -> None:
        if building.getobject('EnergyManagementSystem:Program', program_name) is not None:
            warnings.warn(f"Program '{program_name}' already exists. Skipping.")
            return
        add_program(building, program_name, lines)
        if verbose:
            print(f"Added Program: {program_name}")

    # --- PROGRAM 1: Initialize Season Dates ---
    add('set_cooling_season_input_data', [f'set CoolSeasonStart = {cool_start}', f'set CoolSeasonEnd = {cool_end}'])

    # --- PROGRAM 2: Determine Current Season (also when it goes on into the next year, e.g., Dec to Feb) ---
    add('set_cooling_season', COOLING_SEASON_LINES)

    # --- PER-TARGET PROGRAMS ---
    for suffix in suffixes:
        # Retrieve parameters for this specific target from the DataFrame
        try:
            row_idx = df_arguments[df_arguments['underscore_zonename'] == suffix].index[0]
        except IndexError:
            continue  # Skip if data not found
        row = df_arguments.loc[row_idx]

        # --- PROGRAM 3: Initialize Zone Parameters (the EMS variables keep the names of the arguments in accim 0.x) ---
        add(f'set_zone_input_data_{suffix}', [
            *[f'set {p.variable}_{suffix} = {row[p.argument]}' for p in pmv_index.parameters],
            f'set pmv_cooling_sp_{suffix} = {row["pmv_cooling_setpoint"]}',
            f'set pmv_heating_sp_{suffix} = {row["pmv_heating_setpoint"]}',
            *[f'set {variable}_{suffix} = {row[argument]}' for argument, variable, _ in _TOLERANCES],
        ])

        # --- PROGRAM 4: Apply the setpoints of the index (The Core Logic) ---
        act_h = f'PMV_H_SP_act_{suffix}'  # Actuator for Heating Schedule
        act_c = f'PMV_C_SP_act_{suffix}'  # Actuator for Cooling Schedule
        sp_h = f'{name}_H_SP_{suffix}'
        sp_c = f'{name}_C_SP_{suffix}'
        cooling_coefficient, heating_coefficient = [], []
        if pmv_index.coefficient is not None:
            cooling_coefficient = [f'set {pmv_index.coefficient}_{suffix} = '
                                   f'{pmv_index.cooling_season_coefficient.format(s=suffix)}']
            heating_coefficient = [f'set {pmv_index.coefficient}_{suffix} = '
                                   f'{pmv_index.heating_season_coefficient.format(s=suffix)}']
        add(f'apply_{name}_{suffix}', [
            # 1. Select coefficients based on season
            'if CoolingSeason == 1',
            *cooling_coefficient,
            f'set tolerance_cooling_sp_{suffix} = tolerance_cooling_sp_cooling_season_{suffix}',
            f'set tolerance_heating_sp_{suffix} = tolerance_heating_sp_cooling_season_{suffix}',
            'elseif CoolingSeason == 0',
            *heating_coefficient,
            f'set tolerance_cooling_sp_{suffix} = tolerance_cooling_sp_heating_season_{suffix}',
            f'set tolerance_heating_sp_{suffix} = tolerance_heating_sp_heating_season_{suffix}',
            'endif',
            # 2. The setpoints: pmv_heating_sp and pmv_cooling_sp are on the scale of the index
            f'set {name}_H_SP_noTol_{suffix} = pmv_heating_sp_{suffix}',
            f'set {name}_C_SP_noTol_{suffix} = pmv_cooling_sp_{suffix}',
            # 3. Apply Tolerance
            f'set {sp_h} = {name}_H_SP_noTol_{suffix}+tolerance_heating_sp_{suffix}',
            f'set {sp_c} = {name}_C_SP_noTol_{suffix}+tolerance_cooling_sp_{suffix}',
            # 4. Actuate Schedules (Only if occupied). The Fanger thermostat controls the PMV, so each setpoint is
            # converted with the inverse of the index: the PMV whose index is the setpoint.
            f'if People_Occupant_Count_{suffix} > 0',
            # Heating Logic
            f'if {sp_h} < 0',
            f'set {act_h} = {pmv_index.inverse("H", sp_h, suffix, options)}',
            'else',
            f'set {act_h} = 0',
            'endif',
            # Cooling Logic
            f'if {sp_c} > 0',
            f'set {act_c} = {pmv_index.inverse("C", sp_c, suffix, options)}',
            'else',
            f'set {act_c} = 0',
            'endif',
            # 5. Unoccupied Logic
            'else',
            f'set {act_h} = -100',
            f'set {act_c} = 100',
            'endif',
        ])

        # --- PROGRAM 5a: PMV of a zone with several occupant instances ---
        if suffix in instance_counts:
            n_instances = instance_counts[suffix]
            lines = [f'set PMV_wsum_{suffix} = 0', f'set Occ_sum_{suffix} = 0', f'set PMV_sum_{suffix} = 0']
            for n in range(1, n_instances + 1):
                lines += [
                    f'set PMV_wsum_{suffix} = PMV_wsum_{suffix} + PMV_{suffix}_{n}*People_Occupant_Count_{suffix}_{n}',
                    f'set Occ_sum_{suffix} = Occ_sum_{suffix} + People_Occupant_Count_{suffix}_{n}',
                    f'set PMV_sum_{suffix} = PMV_sum_{suffix} + PMV_{suffix}_{n}',
                ]
            lines += [
                f'if Occ_sum_{suffix} > 0',
                f'set PMV_{suffix} = PMV_wsum_{suffix}/Occ_sum_{suffix}',
                'else',
                f'set PMV_{suffix} = PMV_sum_{suffix}/{n_instances}',
                'endif',
            ]
            add(f'average_PMV_{suffix}', lines)

        # --- PROGRAM 5: Monitor the index (the PMV needs none) ---
        if pmv_index.monitor is not None:
            add(f'monitor_{name}_{suffix}', pmv_index.monitor(suffix, options))

        # --- PROGRAM 6: Count Comfort Hours ---
        add(f'count_{name}_comfort_hours_{suffix}', [
            f'if {name}_{suffix} < {name}_H_SP_noTol_{suffix}',
            f'set comfhour_{suffix} = 0',
            f'set discomfhour_cold_{suffix} = 1*ZoneTimeStep',
            f'set discomfhour_heat_{suffix} = 0',
            f'elseif {name}_{suffix} > {name}_C_SP_noTol_{suffix}',
            f'set comfhour_{suffix} = 0',
            f'set discomfhour_cold_{suffix} = 0',
            f'set discomfhour_heat_{suffix} = 1*ZoneTimeStep',
            'else',
            f'set comfhour_{suffix} = 1*ZoneTimeStep',
            f'set discomfhour_cold_{suffix} = 0',
            f'set discomfhour_heat_{suffix} = 0',
            'endif',
            f'if People_Occupant_Count_{suffix} > 0',
            f'set occupied_hour_{suffix} = 1*ZoneTimeStep',
            'else',
            f'set occupied_hour_{suffix} = 0',
            'endif',
            f'set discomfhour_{suffix} = discomfhour_cold_{suffix} + discomfhour_heat_{suffix}',
        ])


def program_names(pmv_index: PmvIndex, suffixes: Sequence[str],
                  instance_counts: Optional[Mapping[str, int]] = None) -> List[str]:
    """The names of the EMS programs of the setpoints of an index (those of :func:`apply_pmv_index_setpoints`).

    :param pmv_index: The index (see :func:`get_pmv_index`).
    :param suffixes: The suffixes of the zones in the EMS objects.
    :param instance_counts: The number of occupant instances of the zones with several, by suffix.
    """
    name = pmv_index.name
    names = ['set_cooling_season_input_data', 'set_cooling_season']
    for suffix in suffixes:
        names += [f'set_zone_input_data_{suffix}', f'apply_{name}_{suffix}']
        if suffix in (instance_counts or {}):
            names.append(f'average_PMV_{suffix}')
        if pmv_index.monitor is not None:
            names.append(f'monitor_{name}_{suffix}')
        names.append(f'count_{name}_comfort_hours_{suffix}')
    return names


def _add_program_calling_managers(building: IDF, verbose: bool, index_programs: Sequence[str]):
    """
    Adds EnergyManagementSystem:ProgramCallingManager objects.
    These objects tell EnergyPlus WHEN to execute the programs defined above.

    :param building: The BESOS/eppy IDF object.
    :param verbose: If True, prints success messages. Warnings are always printed.
    :param index_programs: The names of the programs of the setpoints: only these get a calling manager, in the
        order of the programs of the IDF (before, every program of the model without a calling manager of its name,
        the user's ones included, got one).
    """
    index_programs = set(index_programs)
    programlist = [p.Name for p in building.idfobjects['EnergyManagementSystem:Program'] if p.Name in index_programs]
    pcmlist = [pcm.Name for pcm in building.idfobjects['EnergyManagementSystem:ProgramCallingManager']]

    for prog in programlist:
        if prog not in pcmlist:
            building.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=prog,
                                  EnergyPlus_Model_Calling_Point="BeginTimestepBeforePredictor", Program_Name_1=prog)
            if verbose:
                print(f"Added ProgramCallingManager for: {prog}")
        else:
            warnings.warn(f"ProgramCallingManager for '{prog}' already exists. Skipping.")


def _add_outputs(building: IDF, pmv_index: PmvIndex, output_frequencies: Sequence[str],
                 other_pmv_related_outputs: bool, suffixes: List[str], unique_zones: List[str], verbose: bool):
    """
    Adds Output:Variable objects to report EMS calculations and standard results.

    :param building: The BESOS/eppy IDF object.
    :param pmv_index: The index of the setpoints.
    :param output_frequencies: List of frequencies (e.g., ['hourly']).
    :param other_pmv_related_outputs: Boolean to add extra comfort outputs.
    :param suffixes: List of sanitized suffixes for EMS variables.
    :param unique_zones: List of RAW zone names for Schedule outputs.
    :param verbose: If True, prints success messages. Warnings are always printed.
    """
    # 1. Define EMS Output Variables (Mapping internal vars to output names)
    name = pmv_index.name
    EMSOutputVariableZone_dict = {}
    if pmv_index.coefficient is not None:
        EMSOutputVariableZone_dict[pmv_index.coefficient_output] = [pmv_index.coefficient, '', 'Averaged']
    EMSOutputVariableZone_dict.update({
        name: [name, '', 'Averaged'],
        f'{name} Heating Setpoint': [f'{name}_H_SP', '', 'Averaged'],
        f'{name} Cooling Setpoint': [f'{name}_C_SP', '', 'Averaged'],
        f'{name} Heating Setpoint No Tolerance': [f'{name}_H_SP_noTol', '', 'Averaged'],
        f'{name} Cooling Setpoint No Tolerance': [f'{name}_C_SP_noTol', '', 'Averaged'],
    })
    EMSOutputVariableZone_dict.update({output: [variable, 'H', 'Summed'] for output, variable in _COUNTERS})

    for key, val in EMSOutputVariableZone_dict.items():
        for suffix in suffixes:
            out_name = f'{key}_{suffix}'
            if building.getobject('EnergyManagementSystem:OutputVariable', out_name) is None:
                building.newidfobject('EnergyManagementSystem:OutputVariable', Name=out_name,
                                      EMS_Variable_Name=f'{val[0]}_{suffix}', Type_of_Data_in_Variable=val[2],
                                      Update_Frequency='ZoneTimestep', Units=val[1])
                if verbose:
                    print(f"Added EMS Output Variable: {out_name}")
            else:
                warnings.warn(f"EMS Output Variable '{out_name}' already exists. Skipping.")

    def _norm(value: Any) -> str:
        return '' if value is None else str(value).strip().upper()

    def _var_key(key_value: Any, variable_name: Any, frequency: Any) -> Tuple[str, str, str]:
        return (_norm(key_value), _norm(variable_name), _norm(frequency))

    # 2. Add Standard Output:Variables for reporting
    for freq in output_frequencies:
        freq_cap = str(freq).capitalize()
        existing_output_keys = {
            _var_key(getattr(o, 'Key_Value', ''), getattr(o, 'Variable_Name', ''), getattr(o, 'Reporting_Frequency', ''))
            for o in building.idfobjects['Output:Variable']
        }

        # Add all EMS variables created above
        for outvar in [v.Name for v in building.idfobjects['EnergyManagementSystem:OutputVariable']]:
            key = _var_key('*', outvar, freq_cap)
            if key not in existing_output_keys and not outvar.startswith("WIP"):
                building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=outvar,
                                      Reporting_Frequency=freq_cap)
                existing_output_keys.add(key)
                if verbose:
                    print(f"Added Output:Variable for {outvar} ({freq})")
            elif key in existing_output_keys:
                warnings.warn(f"Output:Variable already exists for '{outvar}' ({freq_cap}). Skipping.")

        # Add Schedule Values (using RAW zone names)
        for i in ['PMV_H_SP', 'PMV_C_SP']:
            for zone in unique_zones:
                sch_name = f'{i}_{zone}'
                key = _var_key(sch_name, 'Schedule Value', freq_cap)
                if key not in existing_output_keys:
                    building.newidfobject('Output:Variable', Key_Value=sch_name, Variable_Name='Schedule Value',
                                          Reporting_Frequency=freq_cap)
                    existing_output_keys.add(key)
                    if verbose:
                        print(f"Added Output:Variable for Schedule {sch_name} ({freq})")
                else:
                    warnings.warn(f"Output:Variable already exists for Schedule '{sch_name}' ({freq_cap}). Skipping.")

        # Add additional comfort outputs if requested
        if other_pmv_related_outputs:
            additional = ['Zone Operative Temperature', 'Zone Thermal Comfort Fanger Model PMV',
                          'Zone Thermal Comfort Fanger Model PPD', 'Zone Mean Air Temperature']
            for item in additional:
                key = _var_key('*', item, freq_cap)
                if key not in existing_output_keys:
                    building.newidfobject('Output:Variable', Key_Value='*', Variable_Name=item,
                                          Reporting_Frequency=freq_cap)
                    existing_output_keys.add(key)
                    if verbose:
                        print(f"Added Output:Variable for {item} ({freq})")
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

        for freq in output_frequencies:
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
                    if verbose:
                        print(f"Added Output:Meter for {meter} ({freq})")
                else:
                    warnings.warn(f"Output:Meter '{meter}' ({freq}) already exists. Skipping.")

    # 4. Ensure OutputControl:Files is present
    if not building.idfobjects['OutputControl:Files']:
        building.newidfobject('OutputControl:Files', Output_CSV='Yes', Output_MTR='Yes', Output_ESO='Yes')
        if verbose:
            print("Added OutputControl:Files object")
    else:
        # Update existing object
        obj = building.idfobjects['OutputControl:Files'][0]
        obj.Output_CSV = 'Yes'
        obj.Output_MTR = 'Yes'
        obj.Output_ESO = 'Yes'
        if verbose:
            print("Updated existing OutputControl:Files object")
