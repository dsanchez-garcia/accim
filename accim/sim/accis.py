# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Add the Adaptive-Comfort-Control Implementation Script (ACCIS) to EnergyPlus models.

The ACCIS is an EnergyManagementSystem script that applies adaptive setpoint temperatures.

- :class:`AddAccis` adds it to the IDF files of the working folder (or those given) and writes an output
  IDF for each combination of the arguments (comfort standard, category, comfort mode, HVAC mode...).
- :func:`add_accis_to_idf` adds it to an IDF object of eppy or besos, and :func:`modify_accis` sets the
  arguments of that model.
"""

import os
import re
import warnings
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

from accim import __version__
from accim._deprecation import rename_legacy_kwargs, warn_deprecated
from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.energyplus import idd_path, read_idf_version, unsupported_version_message
from accim.sim import prompts
from accim.sim.arguments import (
    LEGACY_ARGUMENT_NAMES,
    OUTPUT_FREQUENCIES,
    OUTPUT_TYPES,
    SCRIPT_TYPES,
    SUPPLY_AIR_TEMP_INPUT_METHODS,
    as_list,
    check_choice,
    is_mixed_mode,
    normalise_energyplus_version,
    normalise_setpoint_type,
    to_bool,
    to_day_of_year,
)
from accim.sim.build import add_accis_objects, add_outputs
from accim.sim.ems.inputs import (
    check_zone_arguments,
    input_programs,
    input_values,
    resolve_zone_arguments,
    set_inputs,
    zone_names,
)
from accim.sim.ems.setast import MODULAR_COMFORT_MODES, depends_on_comfort_mode, master_program_lines, subprograms
from accim.sim.generation import (
    GenerationArguments,
    IdfWriter,
    OutputIdfs,
    combinations,
    output_name,
    zone_arguments_errors,
    zone_input_arguments,
)
from accim.sim.idf_tools import add_program, copy_idf, idf_text, replace_program_lines, set_program_lines
from accim.sim.model import AccimModel
from accim.sim.outputs import OUTPUT_DATAFRAME_COLUMNS, enable_sizing_calculations, output_variables_dataframe
from accim.sim.targets import resolve_targets

__all__ = ['AddAccis', 'add_accis_to_idf', 'addAccis', 'gen_outputs_df', 'load_idf', 'modify_accis']

Number = Union[int, float]

BANNER = (
    '\n--------------------------------------------------------'
    f'\nAdaptive-Comfort-Control-Implemented Model (ACCIM) v{__version__}'
    '\n--------------------------------------------------------'
    '\n\nThis tool allows to apply adaptive setpoint temperatures. '
    '\nFor further information, please read the documentation: '
    '\nhttps://accim.readthedocs.io/en/master/'
    '\nFor a visual understanding of the tool, please visit the following jupyter notebooks:'
    '\n-    Using AddAccis() to apply adaptive setpoint temperatures'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/addAccis/using_addAccis.html'
    '\n-    Using rename_epw_files() to rename the EPWs for proper data analysis after simulation'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/rename_epw_files/using_rename_epw_files.html'
    '\n-    Using run_ep() to directly run simulations with EnergyPlus'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/runEp/using_runEp.html'
    '\n-    Using the class Table() for data analysis'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/Table/using_Table.html'
    '\n-    Full example'
    '\nhttps://accim.readthedocs.io/en/master/jupyter_notebooks/full_example_IBPSA/full_example_IBPSA.html'
    '\n'
    '\nStarting with the process.'
)
_START_MODEL = '\n=======================START OF GENERIC IDF FILE GENERATION PROCESS=======================\n'
_END_MODEL = '\n=======================END OF GENERIC IDF FILE GENERATION PROCESS=======================\n'
_START_OUTPUTS = '\n=======================START OF OUTPUT IDF FILES GENERATION PROCESS=======================\n'
_END_OUTPUTS = '\n=======================END OF OUTPUT IDF FILES GENERATION PROCESS=======================\n'


class _Arguments(dict):
    """The arguments of an ACCIS run. The names of accim 0.x also work, with a DeprecationWarning."""

    def _new_name(self, key) -> Optional[str]:
        new = LEGACY_ARGUMENT_NAMES.get(key)
        return new if new is not None and dict.__contains__(self, new) else None

    def __missing__(self, key):
        new = self._new_name(key)
        if new is None:
            raise KeyError(key)
        warn_deprecated(f'arguments[{key!r}]', f'arguments[{new!r}]')
        return dict.__getitem__(self, new)

    def __contains__(self, key) -> bool:
        return dict.__contains__(self, key) or self._new_name(key) is not None

    def get(self, key, default=None):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        new = self._new_name(key)
        if new is None:
            return default
        warn_deprecated(f'arguments[{key!r}]', f'arguments[{new!r}]')
        return dict.__getitem__(self, new)


# ----------------------------------------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------------------------------------

def _amend_designbuilder_version(path: Union[str, os.PathLike]) -> None:
    """Replace the version of the IDF files of DesignBuilder 7 ('9.4.0.002') with '9.4'."""
    with open(path, 'rb') as file:
        data = file.read()
    if b'Version, 9.4.0.002' in data:
        with open(path, 'wb') as file:
            file.write(data.replace(b'Version, 9.4.0.002', b'Version, 9.4'))


def _set_idd(idf_class, path: str) -> None:
    """Set the IDD of eppy, which can only read the models of one EnergyPlus version in a Python session."""
    current = idf_class.iddname
    if current is None:
        idf_class.setiddname(path)
    elif Path(current).resolve() != Path(path).resolve():
        raise ValueError(
            f'eppy is already using the IDD {current} in this Python session, and it cannot read the models of '
            f'other EnergyPlus versions (whose IDD is {path}). Use a new Python session for them.'
        )


def _idd_version(idd: str) -> Optional[str]:
    """The EnergyPlus version of an IDD file ('25.1'), from its first line ('!IDD_Version 25.1.0'), or None."""
    try:
        with open(idd, encoding='latin-1') as file:
            first_line = file.readline()
    except OSError:
        return None
    match = re.match(r'\s*!IDD_Version\s+(\d+)\.(\d+)', first_line)
    return f'{match[1]}.{match[2]}' if match else None


def _check_besos_idd(path: Union[str, os.PathLike]) -> None:
    """besos reads the models with the IDD of the first model that it read in the Python session: with a model of
    another EnergyPlus version, it only warns, and objects of the model can be lost (the People:Instance objects of
    EnergyPlus 26.2, for instance). Stop instead, as with an explicit ``energyplus_version``."""
    import besos.eppy_funcs

    current = getattr(getattr(besos.eppy_funcs, 'IDF', None), 'iddname', None)
    loaded = _idd_version(current) if current else None
    if loaded is None:
        return
    try:
        version = read_idf_version(path)
    except ValueError:
        return
    if version != loaded:
        raise ValueError(
            f'besos is already using the IDD of EnergyPlus {loaded} ({current}) in this Python session, and it '
            f'cannot read {os.path.basename(os.fspath(path))}, a model of EnergyPlus {version}. Use a new Python '
            f'session for the models of other EnergyPlus versions (or update the model to EnergyPlus {loaded}).'
        )


def load_idf(path: Union[str, os.PathLike], energyplus_version: str = 'auto'):
    """Read an IDF file: with besos (which finds the IDD of its version) if ``energyplus_version`` is 'auto',
    or with eppy and the IDD of ``energyplus_version`` otherwise.

    :param path: The path of the IDF file.
    :param energyplus_version: 'auto' or an EnergyPlus version, such as '25.1'.
    :raises ValueError: If the Python session already reads the models of another EnergyPlus version (eppy can only
        use one IDD in a session).
    """
    _amend_designbuilder_version(path)
    if normalise_energyplus_version(energyplus_version) == 'auto':
        from besos.eppy_funcs import get_building
        _check_besos_idd(path)
        return get_building(str(path))
    from eppy.modeleditor import IDF
    _set_idd(IDF, idd_path(energyplus_version))
    return IDF(str(path))


def _idf_version(idf) -> str:
    return '.'.join(str(i) for i in idf.idd_version[:2])


def _input_files(idfs: Optional[Iterable[Union[str, os.PathLike]]]) -> List[str]:
    """The input IDF files: those given, or those in the working folder, without the output IDFs."""
    if idfs is None:
        candidates = sorted(os.listdir())
    else:
        candidates = [os.fspath(f) for f in ([idfs] if isinstance(idfs, (str, os.PathLike)) else idfs)]
    files = [f for f in candidates
             if f.endswith('.idf') and '[' not in os.path.basename(f) and '_pymod' not in os.path.basename(f)]
    if not files:
        raise FileNotFoundError('No idf files were found. There must be at least 1 idf file located at the path '
                                'where this script is being run.')
    return files


# ----------------------------------------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------------------------------------

def _check_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                           setpoint_type) -> Tuple:
    """Check the arguments of the models; return output_type, output_frequencies and setpoint_type normalised."""
    check_choice('script_type', script_type, SCRIPT_TYPES)
    if script_type.startswith('vrf'):
        check_choice('supply_air_temp_input_method', supply_air_temp_input_method, SUPPLY_AIR_TEMP_INPUT_METHODS)
    check_choice('output_type', output_type.lower() if isinstance(output_type, str) else output_type, OUTPUT_TYPES)
    if output_frequencies is None:
        raise ValueError(f'output_frequencies is required: a list such as {list(OUTPUT_FREQUENCIES[:2])}.')
    output_frequencies = as_list(output_frequencies)
    invalid = [f for f in output_frequencies if not isinstance(f, str) or f.lower() not in OUTPUT_FREQUENCIES]
    if invalid:
        raise ValueError(f'{invalid} are not valid output_frequencies. Valid values: {list(OUTPUT_FREQUENCIES)}.')
    return output_type.lower(), output_frequencies, normalise_setpoint_type(setpoint_type)


def _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                           energyplus_version, setpoint_type) -> None:
    print('Basic input data:')
    print(f'Script type is: {script_type}')
    if script_type.startswith('vrf'):
        print(f'Supply Air Temperature Input Method is: {supply_air_temp_input_method}')
    print(f'Output type is: {output_type}')
    print('Output frequencies are: ')
    print(output_frequencies)
    if energyplus_version != 'auto':
        print(f'EnergyPlus version is: {energyplus_version}')
    print(f'Temperature Control method is: {setpoint_type}')


def _check_version(version: str) -> None:
    if version not in SUPPORTED_ENERGYPLUS_VERSIONS:
        raise ValueError(unsupported_version_message(version))


def _to_confirmation(value: Any) -> bool:
    if value is None:
        return input('Do you still want to run ACCIS? [y/n]: ') == 'y'
    if isinstance(value, str):
        return value.lower() in ('y', 'yes', 'true')
    return bool(value)


def _check_existing_hvac_arguments(operative_temperature_control: Any, availability_schedule: Any,
                                   widen_outdoor_temperature_limits: Any, ideal_loads_backup: Any,
                                   radiant_setpoints: Any) -> Tuple[bool, ...]:
    """Check the arguments of the existing HVAC systems; return existing_hvac_operative_temperature_control,
    existing_hvac_widen_outdoor_temperature_limits, existing_hvac_ideal_loads_backup and
    existing_hvac_radiant_setpoints as booleans."""
    if availability_schedule is not None and (not isinstance(availability_schedule, str)
                                              or not availability_schedule.strip()):
        raise ValueError(f"existing_hvac_availability_schedule must be None or the name of a schedule (such as "
                         f"'On 24/7'), not {availability_schedule!r}.")
    return (to_bool(operative_temperature_control, 'existing_hvac_operative_temperature_control'),
            to_bool(widen_outdoor_temperature_limits, 'existing_hvac_widen_outdoor_temperature_limits'),
            to_bool(ideal_loads_backup, 'existing_hvac_ideal_loads_backup'),
            to_bool(radiant_setpoints, 'existing_hvac_radiant_setpoints'))


def _warn_hvac_zone_map(hvac_zone_map: Optional[Dict[str, str]]) -> None:
    """hvac_zone_map is no longer used: 'ex_mm' does not look for the HVAC equipment of each zone."""
    if hvac_zone_map is not None:
        warnings.warn(
            "hvac_zone_map is deprecated since accim 1.0.0 and has no effect: in mixed mode with the existing HVAC "
            "systems (script type 'ex_mm'), accim reads whether the HVAC system of each zone is on from the load "
            'that its thermostat asks for, whatever its equipment, so it no longer needs the zone of each HVAC '
            'object.',
            DeprecationWarning,
            stacklevel=3,
        )


# ----------------------------------------------------------------------------------------------------------
# AddAccis: files
# ----------------------------------------------------------------------------------------------------------

class AddAccis:
    """Add the ACCIS to IDF files and write an output IDF for each combination of the arguments.

    The input IDFs are those given in ``idfs`` or, by default, all the IDF files in the working folder
    (except the output IDFs, whose names contain '['). The output IDFs are written next to them, with
    names that give their arguments, such as ``Model[CS_INT EN16798[CA_1[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf``.

    The missing arguments are asked: those of the models if ``script_type``, ``output_type``,
    ``output_frequencies``, ``keep_existing_outputs``, ``setpoint_type`` or (with VRF systems)
    ``supply_air_temp_input_method`` is None, and those of the output IDFs if ``comfort_standard``, ``category``,
    ``comfort_mode`` or (in mixed mode) ``hvac_mode`` or ``ventilation_control`` is None.

    :param idfs: The IDF files. By default, those in the working folder.
    :param script_type: 'vrf_ac' (a new VRF system in each occupied zone, full air-conditioning), 'vrf_mm' (VRF
        system, mixed mode), 'ex_ac' (the existing HVAC systems, full air-conditioning) or 'ex_mm' (existing HVAC
        systems, mixed mode).
    :param supply_air_temp_input_method: 'supply air temperature' or 'temperature difference' (VRF systems only).
    :param output_type: 'standard', 'simplified', 'detailed' or 'custom' (which asks which outputs to keep).
    :param output_frequencies: The reporting frequencies of the outputs: a list of 'timestep', 'hourly', 'daily',
        'monthly' and 'runperiod'.
    :param keep_existing_outputs: True to keep the Output:Variable objects of the models.
    :param make_outputs_dataframe: True to keep a DataFrame with the Output:Variable objects in ``df_outputs``.
    :param outputs_dataframe: A DataFrame like ``df_outputs``, filtered to keep the outputs wanted, which
        replace those of the models.
    :param energyplus_version: '9.1' to '26.2', or 'auto' to read it from the models.
    :param setpoint_type: 'temperature' (or 'temp') for adaptive setpoint temperatures, or 'pmv' for setpoints based
        on the PMV of Fanger.
    :param vrf_availability_schedule: The availability schedule of the VRF systems.
    :param comfort_standard: The comfort standards (a list): 0 = ESP CTE; 1 = INT EN16798-1; 2 = INT ASHRAE55;
        3 = JPN Rijal; 4 = CHN GBT50785 Cold; 5 = CHN GBT50785 HotMild; 6 = CHN Yang; 7 = IND IMAC C NV;
        8 = IND IMAC C MM; 9 = IND IMAC R 7DRM; 10 = IND IMAC R 30DRM; 11 = IND Dhaka; 12 = ROM Udrea;
        13 = AUS Williamson; 14 = AUS DeDear; 15 = BRA Rupp NV; 16 = BRA Rupp AC; 17 = MEX Oropeza Arid;
        18 = MEX Oropeza DryTropic; 19 = MEX Oropeza Temperate; 20 = MEX Oropeza HumTropic;
        21 = CHL Perez-Fargallo; 22 = INT ISO7730; 99 = CUSTOM.
    :param category: The categories (a list): 1, 2 or 3 (CAT I, II, III), or 80, 85 or 90 (% of acceptability).
    :param category_cooling_offset: An offset summed to the cooling setpoint offset of the category.
    :param category_heating_offset: An offset summed to the heating setpoint offset of the category.
    :param comfort_mode: The comfort modes (a list): 0 or 0.X = static; 1 or 1.X = adaptive when applicable,
        otherwise the local static model; 2 = adaptive when applicable, otherwise the international static
        model; 3 = adaptive when applicable, otherwise the adaptive setpoints extended horizontally.
    :param setpoint_accuracy: The accuracy of the setpoints: 2 rounds them to every half degree, 10 to the first
        decimal...
    :param custom_cooling_upper_limit: Custom model (comfort_standard 99): upper applicability limit of the cooling
        setpoint (of the running mean outdoor temperature).
    :param custom_cooling_lower_limit: Custom model: lower applicability limit of the cooling setpoint.
    :param custom_heating_upper_limit: Custom model: upper applicability limit of the heating setpoint.
    :param custom_heating_lower_limit: Custom model: lower applicability limit of the heating setpoint.
    :param custom_slope: Custom model: slope m of the comfort temperature (m * running mean outdoor temperature + n).
    :param custom_intercept: Custom model: intercept n of the comfort temperature.
    :param custom_cooling_offset: Custom model: offset of the cooling setpoint from the comfort temperature (positive).
    :param custom_heating_offset: Custom model: offset of the heating setpoint from the comfort temperature (negative).
    :param cooling_season_start: The start of the cooling season (a date 'dd/mm' or a day of the year), used by
        some static models.
    :param cooling_season_end: The end of the cooling season.
    :param hvac_mode: The HVAC modes (a list): 0 = fully air-conditioned; 1 = naturally ventilated; 2 = mixed mode.
    :param ventilation_control: The ventilation controls (a list). With HVAC mode 1: 0 = ventilates above the comfort
        temperature; 1 = above the upper comfort limit. With HVAC mode 2: 0 = above the comfort temperature,
        opening the windows fully; 1 = above the lower comfort limit, opening them fully; 2 and 3 = like 0 and 1,
        with the customised venting opening factor.
    :param opening_factor_max_temp_diff: The maximum temperature difference (indoor minus outdoor) of the venting
        opening factor (greater than 0).
    :param opening_factor_min_temp_diff: The minimum temperature difference of the venting opening factor.
    :param min_opening_factor: The venting opening factor from the maximum temperature difference up (between 0 and
        1): with the ventilation controls 2 and 3, the opening factor goes from 1, below the minimum temperature
        difference, to this value, above the maximum one.
    :param ventilation_setpoint_offset: The offsets of the ventilation setpoint temperature (a list).
    :param min_outdoor_temp_offset: The offsets of the minimum outdoor temperature for ventilation (a list).
    :param max_wind_speed: The maximum wind speeds for ventilation (a list).
    :param setpoint_tolerance_start: The first tolerance of the setpoints.
    :param setpoint_tolerance_end: The last tolerance of the setpoints.
    :param setpoint_tolerance_step: The step between tolerances.
    :param name_suffix: A suffix for the names of the output IDFs.
    :param verbose: True to print the process.
    :param confirm: True to write the output IDFs without asking; None to ask.
    :param vrf_eer: The energy efficiency ratio of the VRF systems.
    :param vrf_cop: The coefficient of performance of the VRF systems.
    :param add_building_averages: True to add the building averages of the hours of each zone and of some outputs.
    :param debug_ems: True to make EnergyPlus write the EDD file of the EMS.
    :param hvac_zone_map: Deprecated since accim 1.0.0, without effect: 'ex_mm' reads whether the HVAC system of
        each zone is on from the load that its thermostat asks for, so it no longer needs the zone of each existing
        HVAC object.
    :param zone_arguments: The arguments of some zones, which are the same in all the output IDFs:
        ``{zone: {argument: value}}``, for instance ``{'Block1:Zone1': {'comfort_standard': 2, 'category': 80,
        'comfort_mode': 3}}``. The zones are the occupied zones, given by their names (or '<space> <people>', as in
        the dictionaries of :func:`accim.sim.apmv.apply_apmv_setpoints`); the arguments are those of
        :func:`modify_accis`, with one value each (the tolerance of the setpoints is ``setpoint_tolerance``). The other
        arguments of these zones, and the arguments of the other zones, are those of each output IDF, whose name
        does not change. Each zone needs a valid combination of comfort standard, category and comfort mode, and
        the HVAC mode and ventilation control of mixed mode only with 'vrf_mm' and 'ex_mm'. Only with temperature
        control (``setpoint_type`` 'temperature').
    :param existing_hvac_operative_temperature_control: With the existing HVAC systems ('ex_ac' and 'ex_mm') and
        ``setpoint_type`` 'temperature': True (the default) to make the thermostat of each occupied zone control the
        operative temperature of the zone between its setpoints at all times, as the thermostats of the VRF systems: it
        gets a ThermostatSetpoint:DualSetpoint object of its own with the setpoint schedules of the zone, a control
        type schedule that always selects it, and a ZoneControl:Thermostat:OperativeTemperature object (radiative
        fraction 0.5, and 0 on the design days, so that the sizing does not change) if it has none. False keeps the
        thermostats of the model, which control the air temperature, and gives the setpoints only to the setpoint
        object of the first control of each thermostat, as accim 0.x did.
    :param existing_hvac_availability_schedule: With the existing HVAC systems, the name of a schedule of the model,
        or 'On 24/7' (always 1, added if the model does not have it), that becomes the availability schedule of the
        HVAC objects that heat or cool the zones (zone equipment, air terminals, unitary systems, fans, coils...) and
        replaces the availability managers of their air and plant loops, so that, with 'On 24/7', they are always
        available. None (the default) keeps their availability, and warns if it can switch them off, since they
        cannot keep the zones between the setpoints while they are off.
    :param existing_hvac_widen_outdoor_temperature_limits: With the existing HVAC systems, True to widen the outdoor
        temperature limits of their HVAC objects (the outdoor temperatures outside which the compressors of their DX
        coils and VRF systems, or their supplemental heaters, do not work: the VRF systems do not cool above 43 °C
        and do not heat above 16 °C by default in EnergyPlus, for instance) to those of the VRF systems of accim, -20
        and 80 °C (or the bounds of the IDD, if they are narrower). False (the default) keeps them, and warns if they
        are narrower.
    :param existing_hvac_ideal_loads_backup: With the existing HVAC systems, True to add to each occupied zone a
        backup ideal loads air system ('<zone> ACCIS Backup Ideal Loads'), the last equipment of the zone, which
        supplies the load to the setpoints that the existing HVAC system does not meet, whatever its type and the
        reason (capacity, controls, operating limits, availability, no equipment that cools or heats...), so that the
        operative temperature stays between the setpoints. Its energy is reported apart, as district heating and
        cooling and in the outputs 'Zone Ideal Loads Zone Sensible Heating Rate' and 'Zone Ideal Loads Zone Sensible
        Cooling Rate'. False (the default) adds nothing.
    :param existing_hvac_radiant_setpoints: With the existing HVAC systems and ``setpoint_type`` 'temperature': True
        (the default) to make their radiant systems (``ZoneHVAC:LowTemperatureRadiant:*``,
        ``ZoneHVAC:HighTemperatureRadiant``),
        ventilated slabs and cooling panels, which heat or cool with setpoint schedules of their own, not with the
        thermostats, follow the setpoints of their zones: they get the setpoint schedules of their zones in their
        heating and cooling setpoint fields (both the high and the low control temperatures of the constant flow
        radiant systems and the ventilated slabs, which then work at full output beyond the setpoints) and the
        operative temperature as their control temperature (the cooling panels in zones with a thermostat get the
        control type ZoneTotalLoad, so that they follow the thermostat); a design object that several zones share is
        copied for each zone. False keeps them as in the model, with a warning.
    :ivar arguments: The arguments, after asking the missing ones.
    :ivar input_idfs: The input IDFs, {'input IDF name': IDF object}.
    :ivar occupied_zones: The occupied zones of each input IDF, as in the EMS objects.
    :ivar occupied_zones_original_name: The occupied zones of each input IDF.
    :ivar windows_and_doors: The windows and doors that open in each input IDF, as in the EMS objects (mixed mode).
    :ivar windows_and_doors_original_name: The windows and doors that open in each input IDF (mixed mode).
    :ivar zone_arguments: The arguments of the zones of ``zone_arguments`` in each input IDF, by the names of the
        zones in the EMS objects: ``{input IDF name: {zone: {argument: value}}}``.
    :ivar output_idfs: The output IDFs, {'output IDF file name': IDF object} (each one is read when it is used;
        ``output_idfs.paths`` has their paths).
    :ivar df_outputs: The DataFrame of Output:Variable objects (argument ``make_outputs_dataframe``).
    """

    def __init__(
        self,
        idfs: Optional[Sequence[Union[str, os.PathLike]]] = None,
        script_type: Optional[str] = None,
        supply_air_temp_input_method: Optional[str] = None,
        output_type: Optional[str] = None,
        output_frequencies: Optional[Sequence[str]] = None,
        keep_existing_outputs: Optional[bool] = None,
        make_outputs_dataframe: Optional[bool] = None,
        outputs_dataframe: Optional[pd.DataFrame] = None,
        energyplus_version: str = 'auto',
        setpoint_type: Optional[str] = None,
        vrf_availability_schedule: str = 'On 24/7',
        comfort_standard: Optional[Sequence[int]] = None,
        category: Optional[Sequence[Number]] = None,
        category_cooling_offset: Number = 0,
        category_heating_offset: Number = 0,
        comfort_mode: Optional[Sequence[Number]] = None,
        setpoint_accuracy: Number = 10000,
        custom_cooling_upper_limit: Number = 0,
        custom_cooling_lower_limit: Number = 0,
        custom_heating_upper_limit: Number = 0,
        custom_heating_lower_limit: Number = 0,
        custom_slope: Number = 0,
        custom_intercept: Number = 0,
        custom_cooling_offset: Number = 0,
        custom_heating_offset: Number = 0,
        cooling_season_start: Union[int, str] = 121,
        cooling_season_end: Union[int, str] = 274,
        hvac_mode: Optional[Sequence[int]] = None,
        ventilation_control: Optional[Sequence[int]] = None,
        opening_factor_max_temp_diff: Number = 6,
        opening_factor_min_temp_diff: Number = 1,
        min_opening_factor: Number = 0.25,
        ventilation_setpoint_offset: Sequence[Number] = (0,),
        min_outdoor_temp_offset: Sequence[Number] = (50,),
        max_wind_speed: Sequence[Number] = (50,),
        setpoint_tolerance_start: Number = 0.1,
        setpoint_tolerance_end: Number = 0.1,
        setpoint_tolerance_step: Number = 0.1,
        name_suffix: str = '',
        verbose: bool = True,
        confirm: Optional[bool] = None,
        vrf_eer: Number = 2,
        vrf_cop: Number = 2.1,
        add_building_averages: bool = False,
        debug_ems: bool = False,
        hvac_zone_map: Optional[Dict[str, str]] = None,
        zone_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
        existing_hvac_operative_temperature_control: bool = True,
        existing_hvac_availability_schedule: Optional[str] = None,
        existing_hvac_widen_outdoor_temperature_limits: bool = False,
        existing_hvac_ideal_loads_backup: bool = False,
        existing_hvac_radiant_setpoints: bool = True,
    ):
        files = _input_files(idfs)
        print(BANNER)
        _warn_hvac_zone_map(hvac_zone_map)
        self.verbose = verbose
        checked_zone_arguments = check_zone_arguments(zone_arguments)
        (existing_hvac_operative_temperature_control, existing_hvac_widen_outdoor_temperature_limits,
         existing_hvac_ideal_loads_backup, existing_hvac_radiant_setpoints) = _check_existing_hvac_arguments(
            existing_hvac_operative_temperature_control, existing_hvac_availability_schedule,
            existing_hvac_widen_outdoor_temperature_limits, existing_hvac_ideal_loads_backup,
            existing_hvac_radiant_setpoints)

        if (script_type is None or output_type is None or output_frequencies is None or keep_existing_outputs is None
                or setpoint_type is None
                or (supply_air_temp_input_method is None and script_type not in ('ex_mm', 'ex_ac'))):
            asked = prompts.ask_model_arguments()
            script_type = asked['script_type']
            supply_air_temp_input_method = asked['supply_air_temp_input_method']
            keep_existing_outputs = asked['keep_existing_outputs']
            output_type = asked['output_type']
            output_frequencies = asked['output_frequencies']
            make_outputs_dataframe = asked['make_outputs_dataframe']
            energyplus_version = asked['energyplus_version']
            setpoint_type = asked['setpoint_type']
        energyplus_version = normalise_energyplus_version(energyplus_version)
        output_type, output_frequencies, setpoint_type = _check_model_arguments(
            script_type, supply_air_temp_input_method, output_type, output_frequencies, setpoint_type)
        if checked_zone_arguments and setpoint_type == 'pmv':
            raise ValueError("zone_arguments needs setpoint_type 'temperature': with 'pmv', the Fanger thermostats "
                             "control the zones and the arguments of the ACCIS are not used.")
        if verbose:
            _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                                   energyplus_version, setpoint_type)
        keep_existing_outputs = to_bool(keep_existing_outputs, 'keep_existing_outputs')
        # The outputs chosen with 'custom' are not known before
        make_outputs_dataframe = False if output_type == 'custom' else bool(make_outputs_dataframe)

        self.arguments = _Arguments(
            script_type=script_type,
            supply_air_temp_input_method=supply_air_temp_input_method,
            output_type=output_type,
            output_frequencies=output_frequencies,
            keep_existing_outputs=keep_existing_outputs,
            make_outputs_dataframe=make_outputs_dataframe,
            outputs_dataframe=outputs_dataframe,
            energyplus_version=energyplus_version,
            setpoint_type=setpoint_type,
        )
        self.input_idfs: Dict[str, Any] = {}
        self.occupied_zones: Dict[str, List[str]] = {}
        self.occupied_zones_original_name: Dict[str, List[str]] = {}
        self.windows_and_doors: Dict[str, List[str]] = {}
        self.windows_and_doors_original_name: Dict[str, List[str]] = {}
        self.zone_arguments: Dict[str, Dict[str, Dict[str, Any]]] = {}

        models = []
        not_working = []
        dataframes = []
        idf_class = None
        found_zones = set()
        for file in files:
            stem = file[:-len('.idf')]
            self._log(_START_MODEL, 'Starting with file:', stem)
            idf0 = load_idf(file, energyplus_version)
            idf_class = type(idf0)
            self._log(f'IDD location is: {idf0.iddname}')
            version = _idf_version(idf0)
            _check_version(version)
            if self.arguments['energyplus_version'] == 'auto':
                self.arguments['energyplus_version'] = version
            idf = copy_idf(idf0)
            model = AccimModel(idf, script_type, setpoint_type, verbose=verbose,
                               hvac_zone_map=hvac_zone_map, name=stem)
            self.input_idfs[stem] = idf0
            self.occupied_zones[stem] = model.occupied_zones
            self.occupied_zones_original_name[stem] = model.occupied_zones_orig
            if model.is_mixed_mode:
                self.windows_and_doors[stem] = model.windows
                self.windows_and_doors_original_name[stem] = model.windows_orig
            names = zone_names(model.targets)
            aliases = {str(alias).upper() for zone_aliases in names.values() for alias in zone_aliases}
            found_zones.update(key for key in checked_zone_arguments if str(key).upper() in aliases)
            self.zone_arguments[stem] = resolve_zone_arguments(checked_zone_arguments, names, strict=False)
            if self.zone_arguments[stem]:
                self._log('The zones with their own arguments are:',
                          *(f'{zone}: {arguments}' for zone, arguments in self.zone_arguments[stem].items()))
            if model.not_working:
                not_working.append(stem)
                continue
            add_accis_objects(model, supply_air_temp_input_method,
                              vrf_availability_schedule=vrf_availability_schedule, vrf_eer=vrf_eer, vrf_cop=vrf_cop,
                              add_building_averages=add_building_averages, debug_ems=debug_ems,
                              existing_hvac_operative_temperature_control=existing_hvac_operative_temperature_control,
                              existing_hvac_availability_schedule=existing_hvac_availability_schedule,
                              existing_hvac_widen_outdoor_temperature_limits=(
                                  existing_hvac_widen_outdoor_temperature_limits),
                              existing_hvac_ideal_loads_backup=existing_hvac_ideal_loads_backup,
                              existing_hvac_radiant_setpoints=existing_hvac_radiant_setpoints)
            add_outputs(model, output_type, output_frequencies, keep_existing_outputs, outputs_dataframe, file=stem)
            if make_outputs_dataframe:
                dataframes.append(output_variables_dataframe(idf, file=stem))
            enable_sizing_calculations(model)
            # The text of the model is kept instead of the model, which needs much more memory
            models.append((stem, idf_text(idf)))
            self._log('Ending with file:', stem, _END_MODEL)

        missing_zones = [key for key in checked_zone_arguments if key not in found_zones]
        if missing_zones:
            raise ValueError(f'The zones {missing_zones} of zone_arguments are not occupied zones of the input IDFs. '
                             f'Their occupied zones are {self.occupied_zones_original_name}.')
        if make_outputs_dataframe:
            self.df_outputs = (pd.concat(dataframes) if dataframes
                               else pd.DataFrame(columns=['file'] + OUTPUT_DATAFRAME_COLUMNS))
        self._log('The following IDFs will not work, so no output IDFs will be generated from them:',
                  *(not_working or ['None']))
        self._log(_START_OUTPUTS)

        generation = self._generation_arguments(
            script_type, comfort_standard=comfort_standard, category=category,
            category_cooling_offset=category_cooling_offset, category_heating_offset=category_heating_offset,
            comfort_mode=comfort_mode, setpoint_accuracy=setpoint_accuracy,
            custom_cooling_upper_limit=custom_cooling_upper_limit,
            custom_cooling_lower_limit=custom_cooling_lower_limit,
            custom_heating_upper_limit=custom_heating_upper_limit,
            custom_heating_lower_limit=custom_heating_lower_limit,
            custom_slope=custom_slope, custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
            custom_heating_offset=custom_heating_offset, cooling_season_start=cooling_season_start,
            cooling_season_end=cooling_season_end, hvac_mode=hvac_mode, ventilation_control=ventilation_control,
            opening_factor_max_temp_diff=opening_factor_max_temp_diff,
            opening_factor_min_temp_diff=opening_factor_min_temp_diff, min_opening_factor=min_opening_factor,
            ventilation_setpoint_offset=ventilation_setpoint_offset, min_outdoor_temp_offset=min_outdoor_temp_offset,
            max_wind_speed=max_wind_speed, setpoint_tolerance_start=setpoint_tolerance_start,
            setpoint_tolerance_end=setpoint_tolerance_end, setpoint_tolerance_step=setpoint_tolerance_step,
            name_suffix=name_suffix)
        self.arguments.update({k: v for k, v in vars(generation).items()})
        self.arguments.update(verbose=verbose, confirm=confirm, zone_arguments=zone_arguments)

        paths = self._write_output_idfs(models, generation, setpoint_type, confirm, idf_class,
                                        is_mixed_mode(script_type))
        self.output_idfs = OutputIdfs(paths, idf_class)
        self._log(_END_OUTPUTS)

    def _log(self, *lines) -> None:
        if self.verbose:
            print(*lines, sep='\n')

    @staticmethod
    def _generation_arguments(script_type: str, **kwargs) -> GenerationArguments:
        """The arguments of the output IDFs, asking them if some are missing."""
        name_suffix = kwargs.pop('name_suffix')
        needed = ['comfort_standard', 'category', 'comfort_mode']
        if is_mixed_mode(script_type):
            needed += ['hvac_mode', 'ventilation_control']
        if any(kwargs[name] is None for name in needed):
            kwargs = prompts.ask_generation_arguments(script_type)
        if not is_mixed_mode(script_type):
            return GenerationArguments.air_conditioned(**kwargs, name_suffix=name_suffix)
        return GenerationArguments(**kwargs, name_suffix=name_suffix)

    def _check_zone_arguments(self, models, generation: GenerationArguments, combos, mixed_mode: bool) -> None:
        """Check that the zones of zone_arguments have setpoints in all the output IDFs."""
        errors = []
        for stem, _ in models:
            for zone, arguments in self.zone_arguments.get(stem, {}).items():
                for combination in combos:
                    reasons = zone_arguments_errors(zone_input_arguments(generation, combination, arguments),
                                                    mixed_mode)
                    if reasons:
                        errors.append(f'zone {zone} of {stem}, in {output_name(stem, combination)}: '
                                      f'{"; ".join(reasons)}')
        if errors:
            raise ValueError('The arguments of some zones of zone_arguments are not valid (give the comfort '
                             'standard, category and comfort mode of each of these zones):\n' + '\n'.join(errors))

    def _write_output_idfs(self, models, generation: GenerationArguments, setpoint_type: str, confirm,
                           idf_class, mixed_mode: bool) -> Dict[str, str]:
        combos = list(combinations(generation, setpoint_type))
        self._check_zone_arguments(models, generation, combos, mixed_mode)
        names = [output_name(stem, c, generation.name_suffix) for stem, _ in models for c in combos]
        self._log('The list of output IDFs is going to be:', *names,
                  f'And the total number of output IDFs is going to be {len(names)}')
        paths: Dict[str, str] = {}
        if not _to_confirmation(confirm):
            self._log('IDF generation has been shut down')
            return paths
        self._log('Generating the following output IDF files:')
        for stem, text in models:
            writer = IdfWriter(idf_class(StringIO(text)), generation, setpoint_type, self.zone_arguments.get(stem))
            for combination in combos:
                path = output_name(stem, combination, generation.name_suffix)
                self._log(path)
                writer.write(path, combination)
                paths[os.path.basename(path)] = os.path.abspath(path)
        return paths


class addAccis(AddAccis):  # noqa: N801 (the name of accim 0.x)
    """Deprecated alias of :class:`AddAccis`, which also accepts the argument names of accim 0.x
    (``ScriptType``, ``Output_type``, ``ComfStand``...)."""

    def __init__(self, *args, **kwargs):
        warn_deprecated('accim.sim.accis.addAccis', 'accim.sim.accis.AddAccis')
        super().__init__(*args, **rename_legacy_kwargs(kwargs, LEGACY_ARGUMENT_NAMES, 'addAccis'))


# ----------------------------------------------------------------------------------------------------------
# IDF objects
# ----------------------------------------------------------------------------------------------------------

def add_accis_to_idf(
    idf,
    script_type: Optional[str] = None,
    supply_air_temp_input_method: Optional[str] = None,
    output_type: Optional[str] = None,
    output_frequencies: Optional[Sequence[str]] = None,
    keep_existing_outputs: Optional[bool] = None,
    outputs_dataframe: Optional[pd.DataFrame] = None,
    energyplus_version: Optional[str] = None,
    setpoint_type: Optional[str] = None,
    vrf_availability_schedule: str = 'On 24/7',
    verbose: bool = True,
    vrf_eer: Number = 2,
    vrf_cop: Number = 2.1,
    add_building_averages: bool = False,
    debug_ems: bool = False,
    hvac_zone_map: Optional[Dict[str, str]] = None,
    existing_hvac_operative_temperature_control: bool = True,
    existing_hvac_availability_schedule: Optional[str] = None,
    existing_hvac_widen_outdoor_temperature_limits: bool = False,
    existing_hvac_ideal_loads_backup: bool = False,
    existing_hvac_radiant_setpoints: bool = True,
) -> AccimModel:
    """Add the ACCIS to an IDF object of eppy or besos (in place).

    The arguments of the ACCIS (comfort standard, category, HVAC mode...) are those of :func:`modify_accis`
    (by default, ComfStand 1, CAT 1, ComfMod 2, HVACmode 2 and VentCtrl 0, in all the zones), which can change
    them later, also for each zone. The arguments are those of :class:`AddAccis`. With the VRF systems
    (``script_type`` 'vrf_ac' and 'vrf_mm'), which are autosized, the zone, system and plant sizing calculations of
    the model are enabled, as :class:`AddAccis` does; with the existing HVAC systems, the sizing calculations do not
    change.

    :param idf: The IDF object.
    :param energyplus_version: The EnergyPlus version of the model; None or 'auto' to take that of its IDD.
    :return: The model, whose attributes give its occupied zones and windows.
    :raises ValueError: If an argument is missing or not valid.
    """
    if verbose:
        print(BANNER)
    _warn_hvac_zone_map(hvac_zone_map)
    (existing_hvac_operative_temperature_control, existing_hvac_widen_outdoor_temperature_limits,
     existing_hvac_ideal_loads_backup, existing_hvac_radiant_setpoints) = _check_existing_hvac_arguments(
        existing_hvac_operative_temperature_control, existing_hvac_availability_schedule,
        existing_hvac_widen_outdoor_temperature_limits, existing_hvac_ideal_loads_backup,
        existing_hvac_radiant_setpoints)
    if energyplus_version is None or str(energyplus_version).lower() == 'auto':
        energyplus_version = _idf_version(idf)
    output_type, output_frequencies, setpoint_type = _check_model_arguments(
        script_type, supply_air_temp_input_method, output_type, output_frequencies, setpoint_type)
    if verbose:
        _print_model_arguments(script_type, supply_air_temp_input_method, output_type, output_frequencies,
                               energyplus_version, setpoint_type)
    check_choice('energyplus_version', energyplus_version, SUPPORTED_ENERGYPLUS_VERSIONS)
    keep_existing_outputs = bool(keep_existing_outputs) if not isinstance(keep_existing_outputs, str) \
        else to_bool(keep_existing_outputs, 'keep_existing_outputs')
    if verbose:
        print(_START_MODEL)
    model = AccimModel(idf, script_type, setpoint_type, verbose=verbose, hvac_zone_map=hvac_zone_map)
    add_accis_objects(model, supply_air_temp_input_method, vrf_availability_schedule=vrf_availability_schedule,
                      vrf_eer=vrf_eer, vrf_cop=vrf_cop, add_building_averages=add_building_averages,
                      debug_ems=debug_ems,
                      existing_hvac_operative_temperature_control=existing_hvac_operative_temperature_control,
                      existing_hvac_availability_schedule=existing_hvac_availability_schedule,
                      existing_hvac_widen_outdoor_temperature_limits=existing_hvac_widen_outdoor_temperature_limits,
                      existing_hvac_ideal_loads_backup=existing_hvac_ideal_loads_backup,
                      existing_hvac_radiant_setpoints=existing_hvac_radiant_setpoints)
    add_outputs(model, output_type, output_frequencies, keep_existing_outputs, outputs_dataframe)
    if script_type.startswith('vrf'):
        # EnergyPlus cannot run the VRF systems without sizing them (they are autosized). The existing HVAC systems
        # are the user's, so their sizing does not change (in accim 0.x, this function did not change it either)
        enable_sizing_calculations(model)
    if verbose:
        print(_END_MODEL)
    return model


def gen_outputs_df(
    idf,
    script_type: Optional[str] = None,
    output_type: Optional[str] = None,
    output_frequencies: Optional[Sequence[str]] = None,
    keep_existing_outputs: Optional[bool] = None,
    setpoint_type: Optional[str] = None,
    add_building_averages: bool = False,
    verbose: bool = False,
) -> pd.DataFrame:
    """Add the ACCIS to an IDF object (in place, see :func:`add_accis_to_idf`) and return a DataFrame with its
    Output:Variable objects, which can be filtered and given as ``outputs_dataframe``."""
    add_accis_to_idf(idf, script_type=script_type, output_type=output_type, output_frequencies=output_frequencies,
                     keep_existing_outputs=keep_existing_outputs, setpoint_type=setpoint_type,
                     add_building_averages=add_building_averages,
                     supply_air_temp_input_method='temperature difference', verbose=verbose)
    return output_variables_dataframe(idf)


def _programs(idf) -> Dict[str, Any]:
    return {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}


def modify_accis(
    idf,
    comfort_standard: Optional[int] = None,
    category: Optional[Number] = None,
    category_cooling_offset: Number = 0,
    category_heating_offset: Number = 0,
    comfort_mode: Optional[Number] = None,
    setpoint_accuracy: Number = 10000,
    custom_cooling_upper_limit: Number = 0,
    custom_cooling_lower_limit: Number = 0,
    custom_heating_upper_limit: Number = 0,
    custom_heating_lower_limit: Number = 0,
    custom_slope: Number = 0,
    custom_intercept: Number = 0,
    custom_cooling_offset: Number = 0,
    custom_heating_offset: Number = 0,
    cooling_season_start: Union[int, str] = 121,
    cooling_season_end: Union[int, str] = 274,
    hvac_mode: Optional[int] = None,
    ventilation_control: Optional[int] = None,
    opening_factor_max_temp_diff: Number = 6,
    opening_factor_min_temp_diff: Number = 1,
    min_opening_factor: Number = 0.25,
    ventilation_setpoint_offset: Number = 0,
    min_outdoor_temp_offset: Number = 50,
    max_wind_speed: Number = 50,
    setpoint_tolerance: Number = 0.1,
    zone_arguments: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """Set the arguments of the ACCIS of an IDF object (one value of each argument of :class:`AddAccis`), in all
    its occupied zones or, with ``zone_arguments``, in some of them.

    Each zone has its arguments in the EMS program SetInputData_<zone>. The comfort standard, category, comfort
    mode, HVAC mode and ventilation control that are None keep their values. The setpoints are set in each timestep
    by the subprograms of the comfort standard (SetAST_Master), so these arguments can also be changed later in
    the programs SetInputData_<zone>.

    The models of earlier versions of accim, which have one program SetInputData for all the zones, can only have
    the same arguments in all the zones, and they get the subprograms of this version where they behave
    differently (those of ESP CTE and INT ISO7730 set the setpoints whatever the comfort mode is).

    :param setpoint_tolerance: The tolerance of the setpoints.
    :param zone_arguments: The arguments of some zones, which replace those of the call in these zones:
        ``{zone: {argument: value}}``, for instance
        ``{'Block1:Zone1': {'comfort_standard': 2, 'category': 80, 'comfort_mode': 3}}`` (see :class:`AddAccis`). An
        argument that is None in the call and is not given for a zone keeps its value in the zone.
    :raises ValueError: If the model has no ACCIS, setpoint_accuracy is negative, or zone_arguments is not valid (or
        is given for a model of an earlier version of accim).
    """
    arguments = dict(
        comfort_standard=comfort_standard, category=category, category_cooling_offset=category_cooling_offset,
        category_heating_offset=category_heating_offset, comfort_mode=comfort_mode,
        setpoint_accuracy=setpoint_accuracy, custom_cooling_upper_limit=custom_cooling_upper_limit,
        custom_cooling_lower_limit=custom_cooling_lower_limit, custom_heating_upper_limit=custom_heating_upper_limit,
        custom_heating_lower_limit=custom_heating_lower_limit, custom_slope=custom_slope,
        custom_intercept=custom_intercept, custom_cooling_offset=custom_cooling_offset,
        custom_heating_offset=custom_heating_offset, cooling_season_start=cooling_season_start,
        cooling_season_end=cooling_season_end, hvac_mode=hvac_mode, ventilation_control=ventilation_control,
        opening_factor_max_temp_diff=opening_factor_max_temp_diff,
        opening_factor_min_temp_diff=opening_factor_min_temp_diff, min_opening_factor=min_opening_factor,
        ventilation_setpoint_offset=ventilation_setpoint_offset, min_outdoor_temp_offset=min_outdoor_temp_offset,
        max_wind_speed=max_wind_speed, setpoint_tolerance=setpoint_tolerance,
    )
    programs = _programs(idf)
    zone_programs = input_programs(idf)
    if not zone_programs:
        if zone_arguments and 'SetInputData' in programs:
            raise ValueError('The model has the ACCIS of an earlier version of accim, whose arguments are the same in '
                             'all the zones (program SetInputData). To give the arguments of each zone, add the ACCIS '
                             'with this version of accim to the model without it.')
        _modify_accis_of_earlier_versions(idf, programs, **arguments)
        return
    missing = [n for n in ('SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits') if n not in programs]
    if missing:
        raise ValueError(f'The model has no EMS programs {missing}. Add the ACCIS first with add_accis_to_idf().')
    if setpoint_accuracy < 0:
        raise ValueError('The value for setpoint_accuracy cannot be less than 0.')
    zones = check_zone_arguments(zone_arguments)
    resolved: Dict[str, Dict[str, Any]] = {}
    if zones:
        resolved = resolve_zone_arguments(zones, zone_names(resolve_targets(idf), list(zone_programs)))
    for zone, program in zone_programs.items():
        set_inputs(program, input_values(dict(arguments, **resolved.get(zone, {}))))


def _modify_accis_of_earlier_versions(
    idf, programs: Dict[str, Any], comfort_standard, category, category_cooling_offset, category_heating_offset,
    comfort_mode, setpoint_accuracy, custom_cooling_upper_limit, custom_cooling_lower_limit,
    custom_heating_upper_limit, custom_heating_lower_limit, custom_slope, custom_intercept, custom_cooling_offset,
    custom_heating_offset, cooling_season_start, cooling_season_end, hvac_mode, ventilation_control,
    opening_factor_max_temp_diff, opening_factor_min_temp_diff, min_opening_factor, ventilation_setpoint_offset,
    min_outdoor_temp_offset, max_wind_speed, setpoint_tolerance,
) -> None:
    """:func:`modify_accis` for the models of earlier versions of accim, which have one program SetInputData for all
    the zones, and the other arguments in SetAST, ApplyCAT, SetAppLimits and SetVOFinputData."""
    missing = [n for n in ('SetInputData', 'SetAST', 'ApplyCAT', 'SetComfTemp', 'SetAppLimits') if n not in programs]
    if missing:
        raise ValueError(f'The model has no EMS programs {missing}. Add the ACCIS first with add_accis_to_idf().')
    if setpoint_accuracy < 0:
        raise ValueError('The value for setpoint_accuracy cannot be less than 0.')
    start = to_day_of_year(cooling_season_start, 'cooling_season_start')
    end = to_day_of_year(cooling_season_end, 'cooling_season_end')

    input_data = [('ComfStand', comfort_standard), ('CAT', category), ('ComfMod', comfort_mode),
                  ('HVACmode', hvac_mode), ('VentCtrl', ventilation_control),
                  ('VSToffset', ventilation_setpoint_offset), ('MinOToffset', min_outdoor_temp_offset),
                  ('MaxWindSpeed', max_wind_speed), ('ACSTtol', -setpoint_tolerance), ('AHSTtol', setpoint_tolerance),
                  ('CoolSeasonStart', start), ('CoolSeasonEnd', end)]
    for number, (name, value) in enumerate(input_data, start=1):
        if value is not None:
            setattr(programs['SetInputData'], f'Program_Line_{number}', f'set {name} = {value}')

    programs['SetComfTemp'].Program_Line_2 = f'set ComfTemp = PMOT*{custom_slope}+{custom_intercept}'
    set_program_lines(programs['SetAppLimits'], [
        f'set ACSTaul = {custom_cooling_upper_limit}', f'set ACSTall = {custom_cooling_lower_limit}',
        f'set AHSTaul = {custom_heating_upper_limit}', f'set AHSTall = {custom_heating_lower_limit}'], first=2)
    replace_program_lines(programs['SetAST'], [f'set SetpointAcc = {setpoint_accuracy}', f'set m = {custom_slope}',
                                               f'set n = {custom_intercept}', 'run SetAST_Master'])
    # The models of accim before 0.8 have no SetAST_Master
    if 'SetAST_Master' not in programs:
        add_program(idf, 'SetAST_Master', master_program_lines())
        for name, lines in subprograms().items():
            if name not in programs:
                add_program(idf, name, lines)
    else:
        # The models of accim before 1.0 only set the setpoints of ESP CTE and INT ISO7730 if ComfMod is 0
        static = [cs for cs in MODULAR_COMFORT_MODES if not depends_on_comfort_mode(cs)]
        for name, lines in subprograms(static).items():
            if name in programs:
                replace_program_lines(programs[name], lines)
    if 'SetVOFinputData' in programs:
        set_program_lines(programs['SetVOFinputData'], [
            f'set MaxTempDiffVOF = {opening_factor_max_temp_diff}',
            f'set MinTempDiffVOF = {opening_factor_min_temp_diff}',
            f'set MultiplierVOF = {min_opening_factor}'])
    set_program_lines(programs['ApplyCAT'], [f'set CATcoolOffset = {category_cooling_offset}',
                                             f'set CATheatOffset = {category_heating_offset}'])
    set_program_lines(programs['ApplyCAT'], [f'set ACSToffset = {custom_cooling_offset} + {category_cooling_offset}',
                                             f'set AHSToffset = {custom_heating_offset} + {category_heating_offset}'],
                      first=4)
