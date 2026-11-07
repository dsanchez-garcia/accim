# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The steps that add the ACCIS to a model, shared by :class:`accim.sim.accis.AddAccis` (files) and
:func:`accim.sim.accis.add_accis_to_idf` (IDF objects)."""

import warnings
from typing import Callable, Iterable, Optional

import pandas as pd

from accim.sim import outputs
from accim.sim.ems import objects as ems_objects
from accim.sim.ems.programs import add_program_calling_managers, add_programs
from accim.sim.hvac import existing, vrf
from accim.sim.model import AccimModel
from accim.sim.people import set_comfort_models

__all__ = ['add_accis_objects', 'add_outputs']


def add_accis_objects(
    model: AccimModel,
    supply_air_temp_input_method: Optional[str] = None,
    vrf_availability_schedule: str = 'On 24/7',
    vrf_eer: float = 2,
    vrf_cop: float = 2.1,
    add_building_averages: bool = False,
    debug_ems: bool = False,
    existing_hvac_operative_temperature_control: bool = True,
    existing_hvac_availability_schedule: Optional[str] = None,
    existing_hvac_widen_outdoor_temperature_limits: bool = False,
    existing_hvac_ideal_loads_backup: bool = False,
    existing_hvac_radiant_setpoints: bool = True,
) -> None:
    """Add the HVAC systems (VRF) or adapt the existing ones, and add the EMS objects of the ACCIS.

    :param model: The model, already scanned.
    :param supply_air_temp_input_method: 'supply air temperature' or 'temperature difference' (VRF only).
    :param vrf_availability_schedule: The availability schedule of the VRF systems.
    :param vrf_eer: The energy efficiency ratio of the VRF systems.
    :param vrf_cop: The coefficient of performance of the VRF systems.
    :param add_building_averages: True to add the building averages of the hours of each zone and some outputs.
    :param debug_ems: True to make EnergyPlus write the EDD file of the EMS.
    :param existing_hvac_operative_temperature_control: With the existing HVAC systems and temperature setpoints,
        True to make the thermostat of each occupied zone control the operative temperature between the setpoints of
        the zone at all times (:func:`accim.sim.hvac.existing.set_operative_temperature_thermostats`); False to keep
        the thermostats of the model, which control the air temperature, as in accim 0.x.
    :param existing_hvac_availability_schedule: With the existing HVAC systems, the name of the schedule that makes
        them available (:func:`accim.sim.hvac.existing.make_available`), or None to keep their availability (with a
        warning if it can switch them off).
    :param existing_hvac_widen_outdoor_temperature_limits: With the existing HVAC systems, True to widen their outdoor
        temperature limits to those of the VRF systems of accim
        (:func:`accim.sim.hvac.existing.widen_outdoor_temperature_limits`); False to keep them (with a warning if
        they are narrower).
    :param existing_hvac_ideal_loads_backup: With the existing HVAC systems, True to add to each occupied zone a
        backup ideal loads air system that supplies the load that they do not meet
        (:func:`accim.sim.hvac.existing.add_ideal_loads_backups`).
    :param existing_hvac_radiant_setpoints: With the existing HVAC systems and temperature setpoints, True to make
        their radiant systems, ventilated slabs and cooling panels follow the setpoints of their zones with the
        operative temperature (:func:`accim.sim.hvac.existing.set_radiant_setpoints`); False to keep them as in the
        model (with a warning).
    """
    set_comfort_models(model)
    if model.script_type.startswith('vrf'):
        vrf.add_vrf_system(model, supply_air_temp_input_method, vrf_eer=vrf_eer, vrf_cop=vrf_cop,
                           vrf_availability_schedule=vrf_availability_schedule)
        if model.script_type == 'vrf_mm':
            vrf.check_ventilation(model)
        vrf.add_setpoint_schedules(model)
    else:
        # The radiant systems first, so that the zones whose radiant systems follow the setpoints do not get the
        # warning of the zones without a thermostat
        if existing_hvac_radiant_setpoints and model.setpoint_type == 'temperature':
            existing.set_radiant_setpoints(model)
        else:
            existing.warn_own_setpoints(model)
        if existing_hvac_operative_temperature_control and model.setpoint_type == 'temperature':
            existing.set_operative_temperature_thermostats(model)
        else:
            existing.add_setpoint_schedules(model)
            message = existing.own_thermal_comfort_warning(model)
            if message is not None and model.setpoint_type == 'temperature':
                warnings.warn(message, stacklevel=3)
        if existing_hvac_availability_schedule is None:
            existing.warn_availability(model)
        else:
            existing.make_available(model, existing_hvac_availability_schedule)
        if existing_hvac_widen_outdoor_temperature_limits:
            existing.widen_outdoor_temperature_limits(model)
        else:
            existing.warn_outdoor_temperature_limits(model)
        if existing_hvac_ideal_loads_backup:
            existing.add_ideal_loads_backups(model)

    add_programs(model)
    ems_objects.add_output_variables(model)
    ems_objects.add_global_variables(model)
    ems_objects.add_internal_variables(model)
    ems_objects.add_sensors(model)
    ems_objects.add_actuators(model)
    if model.script_type.startswith('vrf'):
        vrf.add_coil_sensors(model)
    elif model.script_type == 'ex_mm':
        existing.add_load_sensors(model)
        existing.add_design_day_sensor(model)
    add_program_calling_managers(model)
    if add_building_averages:
        ems_objects.add_building_averages(model)

    outputs.add_output_control_files(model)
    outputs.add_variable_dictionary(model)
    if debug_ems:
        outputs.add_ems_debug_output(model)


def add_outputs(
    model: AccimModel,
    output_type: str,
    output_frequencies: Iterable[str],
    keep_existing_outputs: bool,
    outputs_dataframe: Optional[pd.DataFrame] = None,
    file: Optional[str] = None,
    ask: Optional[Callable[[str], str]] = None,
) -> None:
    """Add the Output:Variable objects of an output type, or those of a DataFrame.

    :param model: The model, with the ACCIS.
    :param output_type: 'simplified', 'standard', 'detailed' or 'custom' (detailed, and then ask which to keep).
    :param output_frequencies: The reporting frequencies.
    :param keep_existing_outputs: False to remove the existing outputs first.
    :param outputs_dataframe: If given, the outputs are replaced with its rows (those of ``file``, if given).
    :param file: The name of the model in the 'file' column of ``outputs_dataframe``.
    :param ask: The function that asks the outputs to keep with output type 'custom' (by default, ``input``).
    """
    if not keep_existing_outputs:
        outputs.remove_existing_outputs(model)
    output_type = output_type.lower()
    if output_type == 'simplified':
        outputs.add_simplified_outputs(model, output_frequencies)
    else:
        outputs.add_standard_outputs(model, output_frequencies)
        if output_type in ('detailed', 'custom'):
            outputs.add_detailed_outputs(model, output_frequencies)
        if output_type == 'custom':
            outputs.select_custom_outputs(model, ask)
    if outputs_dataframe is not None:
        outputs.take_output_dataframe(model, outputs_dataframe, file)
    outputs.remove_duplicated_outputs(model)
