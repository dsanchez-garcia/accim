# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Functions that edit EnergyPlus models (IDF objects of eppy or besos, or IDF files)."""

import warnings
from os import fdopen, remove
from shutil import copymode, move
from tempfile import mkstemp
from typing import Any, Dict, List, Literal

from unidecode import unidecode

from accim.utils.people import get_people_objects

__all__ = [
    'amend_idf_version_from_dsb',
    'convert_standard_to_comfort_thermostats',
    'get_available_fields',
    'inspect_thermostat_objects',
    'modify_timesteps',
    'modify_timesteps_path',
    'reduce_runtime',
    'remove_accents',
    'remove_accents_in_idf',
    'set_occupancy_to_always',
    'set_occupancy_to_always_path',
    'set_operative_temp_control',
    'transform_ddmm_to_int',
]

#: The IDF object of a model (eppy or besos)
IDF = Any


def modify_timesteps(idf_object: IDF, timesteps: int) -> IDF:
    """
    Modifies the timesteps of the idf object.

    :param idf_object: the IDF class from besos or eppy
    :type idf_object: IDF
    :param timesteps: The number of timesteps.
        Allowable values include 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, and 60
    :type timesteps: int
    """
    if timesteps not in [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]:
        raise ValueError(f'{timesteps} not in allowable values: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, and 60')
    obj_timestep = [i for i in idf_object.idfobjects['Timestep']][0]
    timestep_prev = obj_timestep.Number_of_Timesteps_per_Hour
    obj_timestep.Number_of_Timesteps_per_Hour = timesteps
    print(f'Number of Timesteps per Hour was previously set to '
          f'{timestep_prev}, and it has been modified to {timesteps}.')


def modify_timesteps_path(idfpath: str, timesteps: int):
    """
    Modifies the timesteps of the idf.

    :param idfpath: the path to the idf
    :type idfpath: str
    :param timesteps: The number of timesteps.
        Allowable values include 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, and 60
    :type timesteps: int
    """
    from besos.eppy_funcs import get_building
    building = get_building(idfpath)
    modify_timesteps(idf_object=building, timesteps=timesteps)
    building.save()


def set_occupancy_to_always(idf_object: IDF) -> IDF:
    """
    Sets the occupancy to always occupied for all zones with people object
    (People objects, and the People:Instance objects of EnergyPlus 26.2).

    :param idf_object: the IDF class from besos or eppy
    :type idf_object: IDF
    """
    if 'On 24/7' in [i.Name for i in idf_object.idfobjects['Schedule:Compact']]:
        print('On 24/7 Schedule:Compact object was already in the model.')
    else:
        idf_object.newidfobject(
            key='Schedule:Compact',
            Name='On 24/7',
            Schedule_Type_Limits_Name='Any Number',
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00',
            Field_4='1'
        )

    obj_ppl = get_people_objects(idf_object)
    for ppl in obj_ppl:
        ppl.Number_of_People_Schedule_Name = 'On 24/7'
        print(f'{ppl.Name} Number of People Schedule Name has been set to always occupied.')


def set_occupancy_to_always_path(idfpath: str):
    """
    Sets the occupancy to always occupied for all zones with people object.

    :param idfpath: the path to the idf
    :type idfpath: str
    """
    from besos.eppy_funcs import get_building
    building = get_building(idfpath)
    set_occupancy_to_always(idf_object=building)
    building.save()


def reduce_runtime(
        idf_object: IDF,
        minimal_shadowing: bool = True,
        shading_calculation_update_frequency: int = 20,
        maximum_figures_in_shadow_overlap_calculations: int = 200,
        timesteps: int = 6,
        runperiod_begin_month: int = 1,
        runperiod_begin_day_of_month: int = 1,
        runperiod_end_month: int = 1,
        runperiod_end_day_of_month: int = 1,
) -> IDF:
    """
    Modifies the idf to reduce the simulation runtime.

    :param idf_object:
    :param minimal_shadowing: True or False. If True, applies minimal shadowing setting.
    :param shading_calculation_update_frequency: An integer. Sets the intervals for the shading calculation update
    :param maximum_figures_in_shadow_overlap_calculations: An integer.
        Applies the number to the maximum figures in shadow overlap calculations.
    :param timesteps: An integer. Sets the number of timesteps.
    :param runperiod_begin_day_of_month: the day of the month to start the simulation
    :param runperiod_begin_month: the month to start the simulation
    :param runperiod_end_day_of_month: the day of the month to end the simulation
    :param runperiod_end_month: the month to end the simulation
    """
    if shading_calculation_update_frequency < 1 or shading_calculation_update_frequency > 365:
        raise ValueError('shading_calculation_update_frequency cannot be smaller than 1 or larger than 365')
    if timesteps < 2 or timesteps > 60:
        raise ValueError('timesteps cannot be smaller than 2 or larger than 60')

    if minimal_shadowing:
        obj_building = [i for i in idf_object.idfobjects['Building']][0]
        if obj_building.Solar_Distribution == 'MinimalShadowing':
            print('Solar distribution is already set to MinimalShadowing, therefore no action has been performed.')
        else:
            obj_building.Solar_Distribution = 'MinimalShadowing'
            print('Solar distribution has been set to MinimalShadowing.')

    runperiod_obj = [i for i in idf_object.idfobjects['Runperiod']][0]
    runperiod_obj.Begin_Month = runperiod_begin_month
    runperiod_obj.Begin_Day_of_Month = runperiod_begin_day_of_month
    runperiod_obj.End_Month = runperiod_end_month
    runperiod_obj.End_Day_of_Month = runperiod_end_day_of_month

    try:
        obj_shadowcalc = [i for i in idf_object.idfobjects['ShadowCalculation']][0]
        shadowcalc_freq_prev = obj_shadowcalc.Shading_Calculation_Update_Frequency
        obj_shadowcalc.Shading_Calculation_Update_Frequency = shading_calculation_update_frequency
        print(f'Shading Calculation Update Frequency was previously set to '
              f'{shadowcalc_freq_prev} days, and it has been modified to {shading_calculation_update_frequency} days.')
        shadowcalc_maxfigs_prev = obj_shadowcalc.Maximum_Figures_in_Shadow_Overlap_Calculations
        obj_shadowcalc.Maximum_Figures_in_Shadow_Overlap_Calculations = maximum_figures_in_shadow_overlap_calculations
        print(f'Maximum Figures in Shadow Overlap Calculations was previously set to '
              f'{shadowcalc_maxfigs_prev}, and it has been modified to {maximum_figures_in_shadow_overlap_calculations}.')
    except IndexError:
        print('There was no ShadowCalculation object. Therefore it has not been simplified.')

    obj_timestep = [i for i in idf_object.idfobjects['Timestep']][0]
    timestep_prev = obj_timestep.Number_of_Timesteps_per_Hour
    obj_timestep.Number_of_Timesteps_per_Hour = timesteps
    print(f'Number of Timesteps per Hour was previously set to '
          f'{timestep_prev}, and it has been modified to {timesteps}.')


def amend_idf_version_from_dsb(file_path: str):
    """
    Amends the idf version of the Designbuilder-sourced idf file, for Designbuilder v7.X.
    Replaces the string 'Version, 9.4.0.002' with 'Version, 9.4'.

    :param idf_path: the path to the idf
    :type idf_path: str
    """
    pattern = 'Version, 9.4.0.002'
    subst = 'Version, 9.4'

    # Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    # Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    # Remove original file
    remove(file_path)
    # Move new file
    move(abs_path, file_path)


def transform_ddmm_to_int(string_date: str) -> int:
    """
    This function converts a date string in the format "dd/mm" to the day of the year as an integer.

    :param string_date: A string representing the date in format "dd/mm"
    :return: The day of the year as an integer
    :rtype: int
    """
    num_date = list(int(num) for num in string_date.split('/'))
    from datetime import date
    day_of_year = date(2007, num_date[1], num_date[0]).timetuple().tm_yday
    return day_of_year


def remove_accents(input_str: str) -> str:
    return unidecode(input_str)


def remove_accents_in_idf(idf_path: str):
    """
    Replaces all letters with accent with the same letter without accent.

    :type idf_path: str
    """
    with open(idf_path, 'r', encoding='utf-8') as file:
        content = file.read()

    content_without_accents = remove_accents(content)

    with open(idf_path, 'w', encoding='utf-8') as file:
        file.write(content_without_accents)


def get_available_fields(
        idf_instance: IDF,
        object_name: str,
        source: Literal['idd', 'idf'] = 'idd',
        separator: str = '_'
) -> List[str]:
    """
    Retrieves the available fields for an EnergyPlus object using an eppy IDF instance.
    It automatically removes colons (':') from field names.

    Args:
        idf_instance (IDF): The eppy IDF class instance (e.g., from besos.get_building()).
        object_name (str): The type of the object (e.g., 'Zone', 'Material').
        source (str, optional): The source of the field definitions.
            - 'idd': (Default) Extracts the full schema from the EnergyPlus dictionary.
            - 'idf': Extracts fields from the first existing instance in the model.
        separator (str, optional): Character to replace spaces with. Default is '_'.
                                   If " " is passed, the original spaces are kept.

    Returns:
        List[str]: A list of formatted field names. Returns an empty list if an error occurs.

    Raises:
        ValueError: If 'source' is not 'idd' or 'idf'.
    """

    # 1. Normalize object name to uppercase (eppy internal format)
    obj_upper = object_name.upper()
    raw_fields: List[str] = []

    # --- CASE 1: Extract from IDD (Theoretical Schema) ---
    if source == 'idd':
        # Check if the object TYPE exists in the EnergyPlus dictionary
        if obj_upper in idf_instance.model.dtls:
            idx = idf_instance.model.dtls.index(obj_upper)
            raw_info = idf_instance.idd_info[idx]
            # Extract only the items that are fields
            raw_fields = [item['field'][0] for item in raw_info if 'field' in item]
        else:
            warnings.warn(f"Object type '{object_name}' not found in the loaded IDD.")
            return []

    # --- CASE 2: Extract from IDF (Existing Instance) ---
    elif source == 'idf':
        # Check if there are any created objects of this type
        objects = idf_instance.idfobjects[obj_upper]

        if len(objects) > 0:
            # Take the first object to extract its fields
            raw_fields = objects[0].fieldnames
        else:
            warnings.warn(f"No instances of '{object_name}' found in the current IDF model.")
            return []

    else:
        raise ValueError("Parameter 'source' must be either 'idd' or 'idf'.")

    # --- FINAL FORMATTING ---
    formatted_fields: List[str] = []

    for field in raw_fields:
        # 1. Remove colons (e.g., 'Output:Variable' -> 'OutputVariable')
        clean_field = field.replace(":", "")

        # 2. Replace spaces with the specified separator
        if separator != " ":
            clean_field = clean_field.replace(" ", separator)

        formatted_fields.append(clean_field)

    return formatted_fields


def convert_standard_to_comfort_thermostats(
        idf: IDF,
        pmv_heating_schedule_name: str,
        pmv_cooling_schedule_name: str,
        comfort_control_type_schedule_name: str
) -> List[str]:
    """
    Maps and substitutes standard DualSetpoint thermostats with Thermal Comfort Fanger thermostats.

    Args:
        idf (IDF): The BESOS IDF model object.
        pmv_heating_schedule_name (str): Name of the Schedule defining the PMV lower limit for heating.
        pmv_cooling_schedule_name (str): Name of the Schedule defining the PMV upper limit for cooling.
        comfort_control_type_schedule_name (str): Name of the Schedule that defines the control type.

    Returns:
        List[str]: A list of Zone names that were successfully converted.
    """

    converted_zones = []

    thermostats_to_remove = []
    setpoints_to_remove = []

    # 1. FIND STANDARD THERMOSTATS
    standard_thermostats = idf.idfobjects['ZONECONTROL:THERMOSTAT']

    for thermostat in standard_thermostats:

        ctrl_obj_type = str(thermostat.Control_1_Object_Type).upper()

        if ctrl_obj_type == 'THERMOSTATSETPOINT:DUALSETPOINT':

            setpoint_name = thermostat.Control_1_Name

            # Find the actual Setpoint Object
            old_setpoint_obj = next(
                (sp for sp in idf.idfobjects['THERMOSTATSETPOINT:DUALSETPOINT']
                 if sp.Name.upper() == setpoint_name.upper()),
                None
            )

            if old_setpoint_obj:
                # --- DATA EXTRACTION ---
                zone_name = thermostat.Zone_or_ZoneList_Name
                heating_sch = old_setpoint_obj.Heating_Setpoint_Temperature_Schedule_Name
                cooling_sch = old_setpoint_obj.Cooling_Setpoint_Temperature_Schedule_Name

                # Generate new names
                new_setpoint_name = f"Fanger Setpoint {zone_name}"
                new_control_name = f"Comfort Control {zone_name}"

                # --- CREATION OF NEW OBJECTS ---

                # 1. Create ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint
                idf.newidfobject(
                    'THERMOSTATSETPOINT:THERMALCOMFORT:FANGER:DUALSETPOINT',
                    Name=new_setpoint_name,
                    Fanger_Thermal_Comfort_Heating_Schedule_Name=pmv_heating_schedule_name,
                    Fanger_Thermal_Comfort_Cooling_Schedule_Name=pmv_cooling_schedule_name,
                    Heating_Setpoint_Temperature_Schedule_Name=heating_sch,
                    Cooling_Setpoint_Temperature_Schedule_Name=cooling_sch
                )

                # 2. Create ZoneControl:Thermostat:ThermalComfort
                idf.newidfobject(
                    'ZONECONTROL:THERMOSTAT:THERMALCOMFORT',
                    Name=new_control_name,
                    Zone_or_ZoneList_Name=zone_name,
                    Averaging_Method='PeopleAverage',
                    Specific_People_Name='',
                    Minimum_DryBulb_Temperature_Setpoint=12.0,
                    Maximum_DryBulb_Temperature_Setpoint=40.0,
                    Thermal_Comfort_Control_Type_Schedule_Name=comfort_control_type_schedule_name,
                    Thermal_Comfort_Control_1_Object_Type='ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint',
                    Thermal_Comfort_Control_1_Name=new_setpoint_name
                )

                # --- MARK FOR DELETION ---
                thermostats_to_remove.append(thermostat)

                if old_setpoint_obj not in setpoints_to_remove:
                    setpoints_to_remove.append(old_setpoint_obj)

                converted_zones.append(zone_name)

    # 2. DELETE OLD OBJECTS
    for th in thermostats_to_remove:
        idf.removeidfobject(th)

    for sp in setpoints_to_remove:
        try:
            idf.removeidfobject(sp)
        except ValueError:
            pass

    return converted_zones


def inspect_thermostat_objects(idf: IDF) -> Dict[str, List[Dict[str, Any]]]:
    """
    Inspects and retrieves key data from thermostat and setpoint objects in the IDF.

    Target Objects:
      1. ZoneControl:Thermostat
      2. ZoneControl:Thermostat:ThermalComfort
      3. ThermostatSetpoint:DualSetpoint
      4. ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint

    Args:
        idf (IDF): The BESOS IDF model object.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary where keys are the IDF Object Types
                                         and values are lists of dictionaries containing
                                         the properties of each instance found.
    """

    # Define the specific types we want to inspect
    target_types = [
        'Zone',
        'Space',
        'ZoneList',
        'SpaceList',
        'ZoneControl:Thermostat',
        'ZoneControl:Thermostat:ThermalComfort',
        'ThermostatSetpoint:DualSetpoint',
        'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint'
    ]

    inspection_results = {}

    for obj_type in target_types:
        # Eppy keys are uppercase
        idf_objs = [i for i in idf.idfobjects[obj_type.upper()]]

        inspection_results.update({obj_type: idf_objs})
        # fields = get_available_fields(idf_instance=idf, object_name=obj_type)

        # Initialize list for this type
        # obj_list = []
        #
        # for obj in idf_objs:
        #     # Basic info common to all
        #     data = {'Name': obj.Name}
        #
        #
        #
        #
        #     # Extract specific fields based on the type for better readability
        #     if obj_type == 'ZoneControl:Thermostat':
        #         data['Zone'] = obj.Zone_or_ZoneList_Name
        #         data['Control_Type'] = obj.Control_1_Object_Type
        #         data['Control_Name'] = obj.Control_1_Name
        #
        #     elif obj_type == 'ZoneControl:Thermostat:ThermalComfort':
        #         data['Zone'] = obj.Zone_or_ZoneList_Name
        #         data['Control_Type'] = obj.Thermal_Comfort_Control_1_Object_Type
        #         data['Control_Name'] = obj.Thermal_Comfort_Control_1_Name
        #         data['Avg_Method'] = obj.Averaging_Method
        #
        #     elif obj_type == 'ThermostatSetpoint:DualSetpoint':
        #         data['Heating_Sch'] = obj.Heating_Setpoint_Temperature_Schedule_Name
        #         data['Cooling_Sch'] = obj.Cooling_Setpoint_Temperature_Schedule_Name
        #
        #     elif obj_type == 'ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint':
        #         data['PMV_Heating_Sch'] = obj.Fanger_Thermal_Comfort_Heating_Schedule_Name
        #         data['PMV_Cooling_Sch'] = obj.Fanger_Thermal_Comfort_Cooling_Schedule_Name
        #         data['Temp_Heating_Sch'] = obj.Heating_Setpoint_Temperature_Schedule_Name
        #         data['Temp_Cooling_Sch'] = obj.Cooling_Setpoint_Temperature_Schedule_Name
        #
        #     obj_list.append(data)
        #
        # # Store in master dictionary
        # inspection_results[obj_type] = obj_list

    return inspection_results


def set_operative_temp_control(idf_path: str = None, idf_object=None):
    """
    Sets the thermostat control to operative temperature for all ZoneControl:Thermostat objects.
    You can provide either the path to the IDF file or the eppy/besos IDF object.

    :param idf_path: Path to the IDF file.
    :param idf_object: eppy or besos IDF object.
    :return: The modified IDF object if idf_object was provided, otherwise None.
    """
    if idf_path is None and idf_object is None:
        raise ValueError("Either idf_path or idf_object must be provided.")

    if idf_path is not None:
        from besos.eppy_funcs import get_building
        building = get_building(idf_path)
    else:
        building = idf_object

    thermostats = [i for i in building.idfobjects['ZoneControl:Thermostat']]

    if not thermostats:
        print("No ZoneControl:Thermostat objects found in the IDF.")

    for t in thermostats:
        t_name = t.Name
        op_temps = [op for op in building.idfobjects['ZoneControl:Thermostat:OperativeTemperature'] 
                    if op.Thermostat_Name == t_name]

        if not op_temps:
            building.newidfobject(
                key='ZoneControl:Thermostat:OperativeTemperature',
                Thermostat_Name=t_name,
                Radiative_Fraction_Input_Mode='Constant',
                Fixed_Radiative_Fraction=0.5
            )
            print(f"Added ZoneControl:Thermostat:OperativeTemperature for {t_name}")
        else:
            print(f"ZoneControl:Thermostat:OperativeTemperature already exists for {t_name}")

    if idf_path is not None:
        building.save()
        return None
    else:
        return building
