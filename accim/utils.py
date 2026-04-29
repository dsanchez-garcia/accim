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

import os, shutil, tempfile
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove, rename

import besos.IDF_class
from besos.IDF_class import IDF
import besos
from os import PathLike
from unidecode import unidecode
from typing import List, Literal, Dict, Any, Union, Tuple

from accim import lists

import subprocess
import platform
import re
import numpy as np
from typing import Dict, Optional

import pandas as pd
import warnings
from besos import eppy_funcs as ef
from besos.eplus_funcs import get_idf_version, run_building
from besos.eppy_funcs import get_building

def modify_timesteps(idf_object: besos.IDF_class.IDF, timesteps: int) -> besos.IDF_class.IDF:
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
          f'{timestep_prev} days, and it has been modified to {timesteps} days.')


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


def set_occupancy_to_always(idf_object: besos.IDF_class.IDF) -> besos.IDF_class.IDF:
    """
    Sets the occupancy to always occupied for all zones with people object.

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

    obj_ppl = [i for i in idf_object.idfobjects['people']]
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
        idf_object: besos.IDF_class.IDF,
        minimal_shadowing: bool = True,
        shading_calculation_update_frequency: int = 20,
        maximum_figures_in_shadow_overlap_calculations: int = 200,
        timesteps: int = 6,
        runperiod_begin_month: int = 1,
        runperiod_begin_day_of_month: int = 1,
        runperiod_end_month: int = 1,
        runperiod_end_day_of_month: int = 1,
) -> besos.IDF_class.IDF:
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
              f'{shadowcalc_maxfigs_prev} days, and it has been modified to {maximum_figures_in_shadow_overlap_calculations} days.')
    except IndexError:
        print('There was no ShadowCalculation object. Therefore it has not been simplified.')

    obj_timestep = [i for i in idf_object.idfobjects['Timestep']][0]
    timestep_prev = obj_timestep.Number_of_Timesteps_per_Hour
    obj_timestep.Number_of_Timesteps_per_Hour = timesteps
    print(f'Number of Timesteps per Hour was previously set to '
          f'{timestep_prev} days, and it has been modified to {timesteps} days.')


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


class print_available_outputs_mod:
    def __init__(
            self,
            building,
            version=None,
            name=None,
            frequency=None,
    ):
        """
        A modified version of besos' print_available_outputs function.

        :param building: The besos or eppy idf class instance.
        :param version: Deprecated.
        :param name:
        :param frequency:
        """
        # backwards compatibility
        if version:
            warnings.warn(
                "the version argument is deprecated for print_available_outputs,"
                " and will be removed in the future",
                FutureWarning,
            )
            assert version == get_idf_version(building), "Incorrect version"

        if name is not None:
            name = name.lower()
        if frequency is not None:
            frequency = frequency.lower()
        results = run_building(building, stdout_mode="Verbose", out_dir='available_outputs')
        outputlist = []
        for key in results.keys():
            if name is not None:
                if name not in key[0].lower():
                    continue
                if frequency is not None and key[1].lower() != frequency:
                    continue
            elif frequency is not None:
                if key[1].lower() != frequency:
                    continue
            # print(list(key))
            outputlist.append(list(key))

        self.variablereaderlist = []
        self.meterreaderlist = []
        for i in range(len(outputlist)):
            if ',' in outputlist[i][0]:
                outputlist[i] = [
                    outputlist[i][0].split(',')[0],
                    outputlist[i][0].split(',')[1],
                    outputlist[i][1]
                ]
                self.variablereaderlist.append(outputlist[i])
            else:
                self.meterreaderlist.append(outputlist[i])
        # return outputlist, self.meterreaderlist, self.variablereaderlist


# available_outputs = print_available_outputs_mod(building)

# for i in range(len(available_outputs)):
#     if ',' in available_outputs[i][0]:
#         available_outputs[i] = [
#             available_outputs[i][0].split(',')[0],
#             available_outputs[i][0].split(',')[1],
#             available_outputs[i][1]
#         ]

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

def get_accim_args(idf_object: besos.IDF_class) -> dict:
    """
    Collects all the EnergyManagementSystem:Program Program lines used to
    set the values for the arguments of ACCIS, and saves them in a dictionary.

    :param idf_object: the besos.IDF_class instance
    :return: a dictionary
    """
    # set_input_data = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setinputdata'][0]
    # set_vof_input_data = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setvofinputdata'][0]
    # applycat = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'applycat'][0]
    # setast = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setast'][0]
    # setapplimits = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setapplimits'][0]
    # other_args = {'SetpointAcc': setast.Program_Line_1}
    # cust_ast_args = {
    #     'ACSToffset': applycat.Program_Line_4,
    #     'AHSToffset': applycat.Program_Line_5,
    #     'm': setast.Program_Line_2,
    #     'n': setast.Program_Line_3,
    #     'ACSTaul': setapplimits.Program_Line_2,
    #     'ACSTall': setapplimits.Program_Line_3,
    #     'AHSTaul': setapplimits.Program_Line_4,
    #     'AHSTall': setapplimits.Program_Line_5,
    # }
    # accim_args = {
    #     'SetInputData': set_input_data,
    #     'SetVOFinputData': set_vof_input_data,
    #     'CustAST': cust_ast_args,
    #     'other': other_args
    # }
    # return accim_args

    # Remove the first two lines and the last line with an empty string
    def program_to_dict(program):
        program = program[2:]

        # Initialize an empty dictionary
        parameters = {}

        # Iterate over each line and extract the parameter name and value
        for line in program:
            line = line.strip()
            if line.startswith("set"):
                parts = line.split("=", 1)  # Split only at the first occurrence of "="
                # key = parts[0].replace("set", "").strip()
                key = parts[0][4:].strip()
                value = parts[1].replace(",", "").strip()
                try:
                    # Evaluate the expression to get the actual value
                    value = eval(value)
                except:
                    pass
                parameters[key] = value

        return parameters

    programs = {}
    try:
        for p in ['SetInputData', 'SetVOFinputData']:
            data = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == p.lower()][0].obj
            programs.update({p: program_to_dict(data)})

        setast = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setast'.lower()][0].obj[:3]
        programs.update({'SetAST': program_to_dict(setast)})

        applycat = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'applycat'][0]
        setast = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setast'][0]
        setapplimits = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if i.Name.lower() == 'setapplimits'][0]

        cust_ast_args = [
            'x',
            'x',
            applycat.Program_Line_4,
            applycat.Program_Line_5,
            setast.Program_Line_2,
            setast.Program_Line_3,
            setapplimits.Program_Line_2,
            setapplimits.Program_Line_3,
            setapplimits.Program_Line_4,
            setapplimits.Program_Line_5,
        ]
        programs.update({'CustAST': program_to_dict(cust_ast_args)})
    except IndexError:
        ems_programs = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program'] if 'set_zone_input_data' in i.Name.lower()]
        for p in ems_programs:
            programs.update({p.Name: program_to_dict(p.obj)})

    return programs

def get_accim_args_flattened(idf_object):
    from accim.utils import get_accim_args
    accim_args = get_accim_args(idf_object=idf_object)
    def flatten_dict(d):
        flat_dict = {}

        def _flatten(d, parent_key=''):
            for k, v in d.items():
                if isinstance(v, dict):
                    _flatten(v)
                else:
                    flat_dict[k] = v

        _flatten(d)
        return flat_dict

    flattened_dict = flatten_dict(accim_args)
    # print(flattened_dict)
    return flattened_dict


def get_idd_path_from_ep_version(EnergyPlus_version: str):
    if EnergyPlus_version.lower() == '9.1':
        iddfile = 'C:/EnergyPlusV9-1-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '9.2':
        iddfile = 'C:/EnergyPlusV9-2-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '9.3':
        iddfile = 'C:/EnergyPlusV9-3-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '9.4':
        iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '9.5':
        iddfile = 'C:/EnergyPlusV9-5-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '9.6':
        iddfile = 'C:/EnergyPlusV9-6-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '22.1':
        iddfile = 'C:/EnergyPlusV22-1-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '22.2':
        iddfile = 'C:/EnergyPlusV22-2-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '23.1':
        iddfile = 'C:/EnergyPlusV23-1-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '23.2':
        iddfile = 'C:/EnergyPlusV23-2-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '24.1':
        iddfile = 'C:/EnergyPlusV24-1-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '24.2':
        iddfile = 'C:/EnergyPlusV24-2-0/Energy+.idd'
    elif EnergyPlus_version.lower() == '25.1':
        iddfile = 'C:/EnergyPlusV25-1-0/Energy+.idd'
    else:
        iddfile = 'not-supported'

    return iddfile


def get_available_fields(
        idf_instance: besos.IDF_class.IDF,
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


def get_people_hierarchy(idf: besos.IDF_class.IDF) -> Dict[str, Any]:
    """
    Extracts the relationship between People objects and the physical Spaces they occupy.

    Since a 'People' object can reference a Zone, a ZoneList, a Space, or a SpaceList,
    this function resolves all these references down to a list of specific Space names.

    Args:
        idf (Union[IDF, IDF_class]): The IDF model object.

    Returns:
        Dict[str, Any]: A dictionary where keys are People object names and values
                        contain the target reference and the resolved list of spaces.
                        Example:
                        {
                            "Residential Living Occupants": {
                                "target_ref": "Residential - Living Space",
                                "target_type": "SpaceList",  (inferred)
                                "affected_spaces": ["Floor_1", "Floor_2"]
                            }
                        }
    """

    # 1. BUILD A RESOLVER MAP (Key: UpperName -> Value: List of Space Names)
    # We need a unified dictionary to look up any name (Zone, Space, List)
    # and immediately get the list of spaces it represents.
    resolver_map: Dict[str, List[str]] = {}

    # Helper to track what type the name refers to (for info purposes)
    type_map: Dict[str, str] = {}

    # --- A. Index Single SPACES ---
    # A Space references itself.
    spaces = idf.idfobjects['SPACE']
    for s in spaces:
        s_upper = s.Name.upper()
        resolver_map[s_upper] = [s.Name]
        type_map[s_upper] = "Space"

    # --- B. Index ZONES (Zone -> Spaces) ---
    # We map Zones to the Spaces they contain.
    # We iterate through spaces to find their parent Zone.
    zone_to_spaces_temp: Dict[str, List[str]] = {}

    for s in spaces:
        z_ref_upper = str(s.Zone_Name).upper()
        if z_ref_upper not in zone_to_spaces_temp:
            zone_to_spaces_temp[z_ref_upper] = []
        zone_to_spaces_temp[z_ref_upper].append(s.Name)

    # Add to main resolver
    for z_upper, s_list in zone_to_spaces_temp.items():
        resolver_map[z_upper] = s_list
        type_map[z_upper] = "Zone"

    # --- C. Index SPACELISTS ---
    for sl in idf.idfobjects['SPACELIST']:
        sl_upper = sl.Name.upper()
        # Get members (fields starting from index 2)
        members = [m for m in sl.obj[2:]]
        resolver_map[sl_upper] = members
        type_map[sl_upper] = "SpaceList"

    # --- D. Index ZONELISTS ---
    # A ZoneList contains Zones, which contain Spaces. We need to chain this.
    for zl in idf.idfobjects['ZONELIST']:
        zl_upper = zl.Name.upper()
        z_members = [m.upper() for m in zl.obj[2:]]

        # Collect all spaces from all zones in this list
        all_spaces_in_list = []
        for z_name in z_members:
            if z_name in zone_to_spaces_temp:
                all_spaces_in_list.extend(zone_to_spaces_temp[z_name])

        resolver_map[zl_upper] = all_spaces_in_list
        type_map[zl_upper] = "ZoneList"

    # 2. PROCESS PEOPLE OBJECTS
    people_hierarchy = {}

    for person in idf.idfobjects['PEOPLE']:
        p_name = person.Name
        # The critical field that links People to Geometry
        target_name = person.Zone_or_ZoneList_or_Space_or_SpaceList_Name
        target_upper = str(target_name).upper()

        # Resolve the spaces using our map
        # Default to empty list if target is invalid/missing
        affected_spaces = resolver_map.get(target_upper, [])
        inferred_type = type_map.get(target_upper, "Unknown")

        people_hierarchy[p_name] = {
            "target_ref": target_name,
            "inferred_type": inferred_type,
            "affected_spaces": affected_spaces
        }

    return people_hierarchy


def get_people_names_for_ems(
        idf: besos.IDF_class.IDF,
        output_format: str = 'list'
) -> Union[List[str], Dict[str, List[str]]]:
    """
    Generates unique instance names for People objects applied to spaces.

    Naming Pattern: "{SpaceName} {PeopleName}"
    Example: "Floor_1 Residential Living Occupants"

    Args:
        idf (besos.IDF_class.IDF): The BESOS IDF model object.
        output_format (str): Controls the structure of the return value.
                             - 'list' (Default): Returns a flat list of all generated names.
                             - 'dict': Returns a dictionary {PeopleName: [GeneratedNames]}.

    Returns:
        Union[List[str], Dict[str, List[str]]]: A flat list or a dictionary depending on output_format.
    """

    # 1. Get the raw hierarchy data
    hierarchy_data = get_people_hierarchy(idf)

    # Initialize containers
    expanded_names_dict: Dict[str, List[str]] = {}
    flat_list: List[str] = []

    # 2. Iterate and generate names
    for people_name, data in hierarchy_data.items():
        affected_spaces = data.get("affected_spaces", [])

        # Generate names: Space Name + People Name
        generated_names = [f"{space.strip()} {people_name.strip()}" for space in affected_spaces]

        if output_format == 'dict':
            expanded_names_dict[people_name] = generated_names
        else:
            # If list mode, extend the master list
            flat_list.extend(generated_names)

    # 3. Return based on requested format
    if output_format == 'dict':
        return expanded_names_dict
    else:
        return flat_list

def get_idf_hierarchy(idf: besos.IDF_class) -> Dict[str, Any]:
    """
    Parses an EnergyPlus IDF model object (from eppy or besos) to extract the
    hierarchical relationship between Zones and Spaces, as well as grouping lists.

    This function is designed to be Case-Preserving for output keys (keeping the
    original IDF capitalization) while remaining Case-Insensitive for internal
    logic (robustly linking Spaces to Zones regardless of capitalization).

    Args:
        idf (Union[IDF, IDF_class]): The IDF model object to be parsed.
                                     Accepts both eppy's IDF and besos's IDF_class.

    Returns:
        Dict[str, Any]: A dictionary representing the model structure:
            {
                "zones": {
                    "ZoneName_Original": {
                        "object_type": "Zone",
                        "spaces": ["Space1", "Space2"]
                    },
                    ...
                },
                "groups": {
                    "zone_lists": { "ListName": ["Zone1", "Zone2"] },
                    "space_lists": { "ListName": ["Space1", "Space2"] }
                }
            }
    """

    # Initialize the master dictionary structure to hold the results
    hierarchy: Dict[str, Any] = {
        "zones": {},
        "groups": {
            "zone_lists": {},
            "space_lists": {}
        }
    }

    # Internal lookup map to handle EnergyPlus case-insensitivity.
    # Structure: { "UPPERCASE_NAME": "Original_Name" }
    zone_lookup_map: Dict[str, str] = {}

    # --- 1. Process ZONES (Parent Objects) ---
    # Both eppy and besos allow accessing objects via .idfobjects['TYPE']
    zones = idf.idfobjects['ZONE']

    for zone in zones:
        z_name_original = zone.Name

        # We store the UPPERCASE version to allow robust searching later,
        # ensuring "Zone1" matches "zone1" as EnergyPlus expects.
        z_name_upper = str(z_name_original).upper()
        zone_lookup_map[z_name_upper] = z_name_original

        # Initialize the entry in the result dict using the ORIGINAL name for readability
        hierarchy["zones"][z_name_original] = {
            "object_type": "Zone",
            "spaces": []  # List to hold children (Spaces)
        }

    # --- 2. Process SPACES (Child Objects) ---
    spaces = idf.idfobjects['SPACE']

    # Note: If 'spaces' is empty, it might be a legacy IDF (pre-v9.6) or a simplified model.
    for space in spaces:
        s_name = space.Name

        # Get the reference to the parent Zone.
        # We convert to string and uppercase to query our lookup map safely.
        parent_ref_upper = str(space.Zone_Name).upper()

        # Link Space to Zone using the lookup map
        if parent_ref_upper in zone_lookup_map:
            # Retrieve the correct original casing of the zone name
            real_zone_name = zone_lookup_map[parent_ref_upper]

            # Append the space name to the correct zone entry
            hierarchy["zones"][real_zone_name]["spaces"].append(s_name)
        else:
            # Log warning for orphan spaces (spaces pointing to non-existent zones)
            print(f"WARNING: Space '{s_name}' references an unknown Zone: '{space.Zone_Name}'")

    # --- 3. Process Grouping Lists (ZoneList & SpaceList) ---

    # Process ZoneList
    for z_list in idf.idfobjects['ZONELIST']:
        # In eppy/besos, the .obj property is a list: ['ZoneList', 'Name', 'Member1', 'Member2'...]
        # Slicing from index 2 ([2:]) retrieves all members dynamically, regardless of list length.
        members: List[str] = [m for m in z_list.obj[2:]]
        hierarchy["groups"]["zone_lists"][z_list.Name] = members

    # Process SpaceList
    for s_list in idf.idfobjects['SPACELIST']:
        # Same logic applied to SpaceLists
        members: List[str] = [m for m in s_list.obj[2:]]
        hierarchy["groups"]["space_lists"][s_list.Name] = members

    return hierarchy


def get_idf_hierarchy_with_people(idf: besos.IDF_class.IDF) -> Dict[str, Any]:
    """
    Parses an EnergyPlus IDF model to extract the hierarchy of Zones and Spaces.

    Structure changes in this version:
    - 'spaces' is a list of dictionaries.
    - Each space dictionary contains:
        - "name": The name of the space (str).
        - "people": The name of the associated People object (str) or None.

    The function resolves the 'People' object assignment regardless of whether
    it is assigned to a Space, a Zone, a SpaceList, or a ZoneList.

    Args:
        idf (besos.IDF_class.IDF): The BESOS IDF model object.

    Returns:
        Dict[str, Any]: Structure:
            {
                "zones": {
                    "ZoneName": {
                        "object_type": "Zone",
                        "spaces": [
                            {
                                "name": "SpaceName",
                                "people": "PeopleObjectName" (or None)
                            },
                            ...
                        ]
                    }
                },
                "groups": { ... }
            }
    """

    hierarchy: Dict[str, Any] = {
        "zones": {},
        "groups": {
            "zone_lists": {},
            "space_lists": {}
        }
    }

    # --- LOOKUP MAPS (For internal logic) ---
    # 1. Map UPPERCASE Zone Name -> Original Name
    zone_name_map: Dict[str, str] = {}

    # 2. Map UPPERCASE Zone Name -> List of Space Dictionaries
    zone_to_space_objs: Dict[str, List[Dict[str, Any]]] = {}

    # 3. Map UPPERCASE Space Name -> The specific Space Dictionary
    space_obj_map: Dict[str, Dict[str, Any]] = {}

    # --- STEP 1: PROCESS ZONES ---
    zones = idf.idfobjects['ZONE']
    for zone in zones:
        z_name_original = zone.Name
        z_name_upper = str(z_name_original).upper()

        zone_name_map[z_name_upper] = z_name_original
        zone_to_space_objs[z_name_upper] = []

        hierarchy["zones"][z_name_original] = {
            "object_type": "Zone",
            "spaces": []
        }

    # --- STEP 2: PROCESS SPACES ---
    spaces = idf.idfobjects['SPACE']
    for space in spaces:
        s_name = space.Name
        s_name_upper = str(s_name).upper()

        # Create the Space Dictionary
        # 'people' is initialized as None. It will be a string if found later.
        space_dict = {
            "name": s_name,
            "people": None
        }

        # Index it for direct access later
        space_obj_map[s_name_upper] = space_dict

        # Link to Parent Zone
        parent_ref_upper = str(space.Zone_Name).upper()

        if parent_ref_upper in zone_name_map:
            real_zone_name = zone_name_map[parent_ref_upper]

            # Add to the main hierarchy
            hierarchy["zones"][real_zone_name]["spaces"].append(space_dict)

            # Add to our internal index
            zone_to_space_objs[parent_ref_upper].append(space_dict)
        else:
            print(f"WARNING: Space '{s_name}' references unknown Zone: '{space.Zone_Name}'")

    # --- STEP 3: PROCESS LISTS (For resolving references) ---

    # Map SpaceList Name (Upper) -> List of Space Names (Upper)
    spacelist_map: Dict[str, List[str]] = {}
    for sl in idf.idfobjects['SPACELIST']:
        members = [str(m).upper() for m in sl.obj[2:]]
        spacelist_map[sl.Name.upper()] = members
        hierarchy["groups"]["space_lists"][sl.Name] = [m for m in sl.obj[2:]]

    # Map ZoneList Name (Upper) -> List of Zone Names (Upper)
    zonelist_map: Dict[str, List[str]] = {}
    for zl in idf.idfobjects['ZONELIST']:
        members = [str(m).upper() for m in zl.obj[2:]]
        zonelist_map[zl.Name.upper()] = members
        hierarchy["groups"]["zone_lists"][zl.Name] = [m for m in zl.obj[2:]]

    # --- STEP 4: PROCESS PEOPLE (Inject into Space Dicts) ---
    people_objs = idf.idfobjects['PEOPLE']

    for person in people_objs:
        p_name = person.Name
        target_name = person.Zone_or_ZoneList_or_Space_or_SpaceList_Name
        target_upper = str(target_name).upper()

        affected_space_dicts = []

        # LOGIC: Determine what the target is and collect affected space dictionaries

        # Case A: Target is a direct SPACE
        if target_upper in space_obj_map:
            affected_space_dicts.append(space_obj_map[target_upper])

        # Case B: Target is a ZONE (Add all spaces in that zone)
        elif target_upper in zone_to_space_objs:
            affected_space_dicts.extend(zone_to_space_objs[target_upper])

        # Case C: Target is a SPACELIST
        elif target_upper in spacelist_map:
            for member_space_upper in spacelist_map[target_upper]:
                if member_space_upper in space_obj_map:
                    affected_space_dicts.append(space_obj_map[member_space_upper])

        # Case D: Target is a ZONELIST
        elif target_upper in zonelist_map:
            for member_zone_upper in zonelist_map[target_upper]:
                if member_zone_upper in zone_to_space_objs:
                    affected_space_dicts.extend(zone_to_space_objs[member_zone_upper])

        # --- INJECT PEOPLE NAME ---
        for s_dict in affected_space_dicts:
            # We assign the string directly.
            # If multiple people objects point to the same space, the last one processed wins.
            s_dict["people"] = p_name

    return hierarchy

def get_spaces_from_spacelist(idf: besos.IDF_class.IDF, spacelist_name: str) -> List[str]:
    """
    Retrieves the list of Space names belonging to a specific SpaceList object.

    Performs a case-insensitive search for the SpaceList name to ensure robustness.

    Args:
        idf (Union[IDF, IDF_class]): The IDF model object.
        spacelist_name (str): The name of the SpaceList to query (e.g. "Residential - Living Space").

    Returns:
        List[str]: A list of space names contained in that SpaceList.
                   Returns an empty list [] if the SpaceList is not found.
    """

    # Normalize the target name to uppercase for case-insensitive comparison
    target_name_upper = spacelist_name.upper()

    # Iterate through all SPACELIST objects in the IDF
    for s_list in idf.idfobjects['SPACELIST']:

        # Check if this is the list we are looking for
        if s_list.Name.upper() == target_name_upper:
            # In eppy/besos, .obj is a list: ['SpaceList', 'Name', 'Space1', 'Space2'...]
            # Slicing from index 2 ([2:]) retrieves only the members (the spaces).
            members = [space_name for space_name in s_list.obj[2:]]

            return members

    # If the loop finishes without finding the list, return an empty list or handle error
    print(f"WARNING: SpaceList '{spacelist_name}' not found in the IDF.")
    return []


def convert_standard_to_comfort_thermostats(
        idf: besos.IDF_class.IDF,
        pmv_heating_schedule_name: str,
        pmv_cooling_schedule_name: str,
        comfort_control_type_schedule_name: str
) -> List[str]:
    """
    Maps and substitutes standard DualSetpoint thermostats with Thermal Comfort Fanger thermostats.

    Args:
        idf (besos.IDF_class.IDF): The BESOS IDF model object.
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


def inspect_thermostat_objects(idf: besos.IDF_class.IDF) -> Dict[str, List[Dict[str, Any]]]:
    """
    Inspects and retrieves key data from thermostat and setpoint objects in the IDF.

    Target Objects:
      1. ZoneControl:Thermostat
      2. ZoneControl:Thermostat:ThermalComfort
      3. ThermostatSetpoint:DualSetpoint
      4. ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint

    Args:
        idf (besos.IDF_class.IDF): The BESOS IDF model object.

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


def read_eso_using_readvarseso(
        eso_file_path: str = 'eplusout.eso',
        eplus_install_dir: Optional[str] = None,
        only_run_period: bool = True,
        cleanup: bool = True
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Lee el archivo .eso usando ReadVarsESO y parsea correctamente los nombres de objetos
    que contienen dos puntos (ej: Nombres de Zonas o Equipos VRF).
    """

    # --- 1. ENCONTRAR EJECUTABLE READVARSESO ---
    exe_name = 'ReadVarsESO'
    if platform.system() == 'Windows':
        exe_name += '.exe'

    readvars_path = None

    # A. Verificar si el usuario dio una ruta específica
    if eplus_install_dir:
        paths_to_check = [
            eplus_install_dir,
            os.path.join(eplus_install_dir, exe_name),
            os.path.join(eplus_install_dir, 'PostProcess', exe_name)
        ]
        for p in paths_to_check:
            if os.path.isfile(p) and p.endswith(exe_name):
                readvars_path = p
                break

    # B. Búsqueda automática en rutas por defecto
    if not readvars_path:
        common_paths = [
            r'C:\EnergyPlusV25-1-0', r'C:\EnergyPlusV24-2-0', r'C:\EnergyPlusV24-1-0',
            r'C:\EnergyPlusV23-2-0', r'C:\EnergyPlusV23-1-0',
            r'C:\EnergyPlusV22-2-0', r'C:\EnergyPlusV22-1-0',
            r'C:\EnergyPlusV9-6-0', r'C:\EnergyPlusV9-5-0', r'C:\EnergyPlusV9-4-0',
            '/usr/local/bin', '/Applications/EnergyPlus-23-1-0'
        ]

        for base_path in common_paths:
            potential_paths = [
                os.path.join(base_path, 'PostProcess', exe_name),
                os.path.join(base_path, exe_name)
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    readvars_path = p
                    break
            if readvars_path: break

    if not readvars_path:
        raise FileNotFoundError(
            f"No se pudo encontrar '{exe_name}'. Por favor, especifica 'eplus_install_dir'."
        )

    # --- 2. PREPARAR ARCHIVOS ---
    abs_eso_path = os.path.abspath(eso_file_path)
    if not os.path.exists(abs_eso_path):
        raise FileNotFoundError(f"No se encuentra el archivo .eso: {abs_eso_path}")

    work_dir = os.path.dirname(abs_eso_path)
    eso_filename = os.path.basename(abs_eso_path)

    csv_filename = os.path.splitext(eso_filename)[0] + '.csv'
    csv_output_path = os.path.join(work_dir, csv_filename)
    rvi_filename = 'temp_readvars.rvi'
    rvi_path = os.path.join(work_dir, rvi_filename)

    with open(rvi_path, 'w') as f:
        f.write(f"{eso_filename}\n")
        f.write(f"{csv_filename}\n")

    # --- 3. EJECUTAR READVARSESO ---
    cmd = [readvars_path, rvi_filename]
    try:
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if e.stderr else "Sin mensaje de error."
        raise RuntimeError(f"ReadVarsESO falló.\nError: {err_msg}")

    # --- 4. LEER CSV ---
    if not os.path.exists(csv_output_path):
        raise FileNotFoundError(f"No se generó el archivo CSV.")

    try:
        # utf-8-sig para evitar problemas con BOM
        df_all = pd.read_csv(csv_output_path, encoding='utf-8-sig')
        df_all.columns = df_all.columns.str.strip()  # Limpiar espacios en headers
    except Exception as e:
        raise RuntimeError(f"Fallo al leer el CSV generado: {e}")

    # --- 5. FILTRAR DÍAS DE DISEÑO ---
    date_col = 'Date/Time'
    if only_run_period and date_col in df_all.columns:
        def parse_date_value(date_str):
            try:
                s = str(date_str).strip()
                match = re.search(r'(\d{1,2})/(\d{1,2})', s)
                if match:
                    m, d = int(match.group(1)), int(match.group(2))
                    return m * 100 + d
                return 0
            except:
                return 0

        time_values = df_all[date_col].apply(parse_date_value).values
        diffs = np.diff(time_values)
        reset_indices = np.where(diffs < -100)[0]

        if len(reset_indices) > 0:
            start_idx = reset_indices[-1] + 1
            df_all = df_all.iloc[start_idx:].reset_index(drop=True)
        elif len(df_all) > 8800:
            df_all = df_all.tail(8760).reset_index(drop=True)

    # --- 6. SEPARAR POR FRECUENCIA Y CREAR METADATA ---
    data_dict = {}
    metadata_dict = {}

    freq_pattern = re.compile(r'\((Hourly|Daily|Monthly|RunPeriod|Annual|TimeStep)\)$', re.IGNORECASE)
    cols_by_freq = {}

    for col in df_all.columns:
        if col == date_col: continue
        match = freq_pattern.search(col)
        if match:
            raw_freq = match.group(1).capitalize()
            if raw_freq == "Timestep": raw_freq = "Timestep"
            if raw_freq not in cols_by_freq: cols_by_freq[raw_freq] = []
            cols_by_freq[raw_freq].append(col)
        else:
            if 'Other' not in cols_by_freq: cols_by_freq['Other'] = []
            cols_by_freq['Other'].append(col)

    # --- FUNCIÓN DE PARSEO CORREGIDA ---
    def parse_column_metadata(raw_col_name: str) -> Tuple[str, str, str]:
        """
        Parsea 'Object:Variable [Units](Freq)' usando rsplit para manejar
        nombres de objetos que contienen dos puntos.
        """
        # 1. Quitar sufijo de frecuencia
        clean_col = re.sub(r'\([a-zA-Z]+\)$', '', raw_col_name).strip()

        # 2. Extraer Unidades
        units = "-"
        unit_match = re.search(r'\[(.*?)\]', clean_col)
        if unit_match:
            units = unit_match.group(1)
            clean_col = re.sub(r'\s*\[.*?\]', '', clean_col).strip()

        # 3. Extraer Area y Variable
        # CORRECCIÓN AQUÍ: Usar rsplit en lugar de split
        if ':' in clean_col:
            # Divide por el ÚLTIMO dos puntos encontrado
            parts = clean_col.rsplit(':', 1)
            area = parts[0].strip()
            variable = parts[1].strip()
        else:
            area = "Environment"  # O EMS, dependiendo del caso, pero Environment es el default seguro
            variable = clean_col.strip()

        return area, variable, units

    # Procesar dataframes
    for freq, cols in cols_by_freq.items():
        extract_cols = [date_col] + cols if date_col in df_all.columns else cols
        df_subset = df_all[extract_cols].copy()
        df_subset.dropna(how='all', subset=cols, inplace=True)

        if date_col in df_subset.columns:
            df_subset.set_index(date_col, inplace=True)

        new_columns = []
        for col in cols:
            area, variable, units = parse_column_metadata(col)
            new_columns.append((area, variable, units))

        if not df_subset.empty:
            df_subset.columns = pd.MultiIndex.from_tuples(
                new_columns,
                names=['Area', 'Variable', 'Units']
            )

        data_dict[freq] = df_subset

        meta_df = pd.DataFrame(new_columns, columns=['Area', 'Report Type', 'Units'])
        meta_df = meta_df[['Report Type', 'Area', 'Units']]
        meta_df.sort_values(by=['Report Type', 'Area'], inplace=True)
        metadata_dict[freq] = meta_df.reset_index(drop=True)

    # --- 7. LIMPIEZA ---
    if cleanup:
        try:
            if os.path.exists(csv_output_path): os.remove(csv_output_path)
            if os.path.exists(rvi_path): os.remove(rvi_path)
            audit_file = os.path.join(work_dir, 'readvars.audit')
            if os.path.exists(audit_file): os.remove(audit_file)
        except OSError:
            pass

    return {'data': data_dict, 'metadata': metadata_dict}

def identify_variable_key_pattern(
        idf_path: str,
        variable_name: str,
        epw_path: str,
        eplus_install_dir: Optional[str] = None
) -> str:
    """
    Identifies the naming pattern (Key Index) used by EnergyPlus for a specific Report Variable.

    This function performs a quick simulation to generate the .eso output file, extracts the
    actual 'Key Value' (Area) generated by EnergyPlus, and compares it against the IDF objects
    to determine the naming convention.

    It uses a two-level search strategy:
    1. **Direct Object Match:** Checks the first field of every object in the IDF (obj.obj[1])
       to see if it matches the ESO Key. This handles systems like VRF, Boilers, Chillers, etc.
    2. **Hierarchy Match:** If no direct object is found, it analyzes the Zone/Space/People
       hierarchy to detect composite patterns (e.g., '[Space Name] [People Name]').

    :param idf_path: Path to the input .idf file.
    :param variable_name: The name of the Output:Variable to analyze (e.g., 'VRF Heat Pump Cooling Electricity Energy').
    :param epw_path: Path to the weather file (.epw) required for simulation.
    :param eplus_install_dir: (Optional) Path to the EnergyPlus installation directory.
    :return: A string representing the pattern with placeholders (e.g., '[AirConditioner:VariableRefrigerantFlow Name]').
    """

    # --- 1. SETUP AND PREPARATION ---
    # Load the building model using BESOS/Eppy
    building = get_building(idf_path)

    # Check if the requested Output:Variable exists in the IDF.
    # We check for Key_Value='*' to ensure we capture all instances.
    exists = any(
        v.Variable_Name.lower() == variable_name.lower() and v.Key_Value == '*'
        for v in building.idfobjects['Output:Variable']
    )

    # If it doesn't exist, add it to the model to ensure it appears in the output.
    if not exists:
        building.newidfobject(
            'Output:Variable',
            Key_Value='*',
            Variable_Name=variable_name,
            Reporting_Frequency='Hourly'
        )

    # Apply settings to drastically reduce simulation runtime.
    # We only need 1 day of simulation to generate the headers in the ESO file.
    reduce_runtime(
        idf_object=building,
        minimal_shadowing=True,
        shading_calculation_update_frequency=20,
        timesteps=2,
        runperiod_begin_month=1,
        runperiod_begin_day_of_month=1,
        runperiod_end_month=1,
        runperiod_end_day_of_month=1
    )

    # Create a temporary directory for simulation outputs to avoid cluttering the workspace.
    temp_dir = tempfile.mkdtemp()
    out_dir = os.path.join(temp_dir, 'output')

    try:
        print(f"Running quick simulation to trace variable: '{variable_name}'...")

        # --- RUN SIMULATION (Robust Mode) ---
        # BESOS run_building tries to parse the ESO file automatically and fails on some lines.
        # We wrap it in try/except to ignore BESOS parsing errors, as we use our own parser later.
        try:
            run_building(building, out_dir=out_dir, epw=epw_path, stdout_mode='Verbose')
        except ValueError as e:
            # If BESOS complains about "could not match", it means E+ finished but BESOS parser failed.
            # We can safely ignore this if the .eso file exists.
            if "could not match" in str(e):
                print("Warning: BESOS internal parser failed (ignored). Proceeding with custom parser.")
            else:
                # If it's another ValueError, re-raise it just in case.
                raise e
        except Exception as e:
            print(f"Warning: Simulation execution raised an exception: {e}")

        # Check if the ESO file was actually generated
        eso_path = os.path.join(out_dir, 'eplusout.eso')
        if not os.path.exists(eso_path):
            return "Error: eplusout.eso was not generated. Simulation failed."

        # --- 2. READ ESO AND EXTRACT TARGET KEY ---
        # Parse the ESO file to get metadata using the modified read_eso_using_readvarseso
        eso_data = read_eso_using_readvarseso(
            eso_file_path=eso_path,
            eplus_install_dir=eplus_install_dir,
            cleanup=False
        )

        # Try to get metadata from 'Hourly' frequency, or fallback to the first available one.
        metadata = None
        for freq in eso_data['metadata']:
            metadata = eso_data['metadata'][freq]
            break

        if metadata is None:
            return "Error: No metadata found in ESO file."

        # Filter rows matching the requested variable name.
        target_rows = metadata[metadata['Report Type'].str.lower() == variable_name.lower()]

        if target_rows.empty:
            return f"Error: Variable '{variable_name}' was not found in the simulation output."

        # Extract the 'Area' (Key Index) generated by EnergyPlus.
        # This is the string we need to match against the IDF (e.g., "VRF SYSTEM 1").
        eso_key_raw = str(target_rows.iloc[0]['Area'])

        # Crucial cleaning: remove leading/trailing spaces and convert to uppercase for comparison.
        eso_key_clean = eso_key_raw.strip().upper()

        # Handle global variables (Environment)
        if eso_key_clean == 'ENVIRONMENT':
            return "[Environment]"

        print(f"Target Key Index found in ESO: '{eso_key_raw}'")

        # --- 3. LEVEL 1 SEARCH: DIRECT OBJECT MATCH (obj.obj[1]) ---
        # This step checks if the Key Index corresponds exactly to the name of an object in the IDF.

        # List of object types to exclude to optimize performance (irrelevant for output keys).
        exclude_objs = [
            'VERSION', 'SIMULATIONCONTROL', 'BUILDING', 'GLOBALGEOMETRYRULES',
            'SITE:LOCATION', 'DESIGNDAY', 'RUNPERIOD', 'OUTPUT:VARIABLE',
            'SCHEDULE:COMPACT', 'SCHEDULE:YEAR', 'MATERIAL', 'CONSTRUCTION',
            'OUTPUT:TABLE:SUMMARYREPORTS', 'OUTPUTCONTROL:TABLE:STYLE'
        ]

        found_obj_key = None

        # Iterate over all object types present in the IDF
        for obj_type in building.idfobjects:
            if obj_type in exclude_objs:
                continue

            # Iterate over each instance of the object type
            for obj in building.idfobjects[obj_type]:
                try:
                    # In Eppy, obj.obj is the raw list of fields from the IDF line.
                    # obj.obj[0] is the Object Type (Key).
                    # obj.obj[1] is the First Field (usually Name, Heat_Pump_Name, Zone_Name, etc.).

                    # Skip if the object doesn't have at least one field after the key
                    if len(obj.obj) < 2:
                        continue

                        # Access the raw value of the first field directly.
                    # We do not rely on .Name because the field name varies in the IDD.
                    obj_name_val = str(obj.obj[1])

                    # Clean and compare
                    if obj_name_val.strip().upper() == eso_key_clean:
                        found_obj_key = obj.key  # This holds the object type (e.g., AirConditioner:VariableRefrigerantFlow)
                        break

                except Exception:
                    continue

            if found_obj_key: break

        if found_obj_key:
            # Return the formatted placeholder string using the Object Type found.
            # Example: [AirConditioner:VariableRefrigerantFlow Name]
            return f"[{found_obj_key} Name]"

        # --- 4. LEVEL 2 SEARCH: COMPOSITE HIERARCHY ---
        # If no direct object match is found, the Key Index might be a composite name
        # generated by EnergyPlus (e.g., Space Name + People Name).

        print("Direct object match not found. Analyzing Zone/Space/People hierarchy...")

        # Get the hierarchy structure (Zones -> Spaces -> People)
        hierarchy = get_idf_hierarchy_with_people(building)

        for zone_name, zone_data in hierarchy['zones'].items():

            # Check Zone Name (Fallback, though usually caught in Level 1)
            if str(zone_name).strip().upper() == eso_key_clean:
                return "[Zone Name]"

            for space in zone_data['spaces']:
                s_name = str(space['name']).strip()
                p_name = space['people']

                # 1. Check Space Name
                if s_name.upper() == eso_key_clean:
                    return "[Space Name]"

                if p_name:
                    p_name_clean = str(p_name).strip()

                    # 2. Check People Name
                    if p_name_clean.upper() == eso_key_clean:
                        return "[People Name]"

                    # 3. Check Composite: Space Name + People Name
                    if f"{s_name} {p_name_clean}".upper() == eso_key_clean:
                        return "[Space Name] [People Name]"

                    # 4. Check Composite: Zone Name + People Name
                    if f"{str(zone_name).strip()} {p_name_clean}".upper() == eso_key_clean:
                        return "[Zone Name] [People Name]"

        return f"Pattern not identified automatically for key: '{eso_key_raw}'"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"

    finally:
        # Cleanup temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def update_idf_version(
        input_idf_path: str,
        ep_version_target: str,
        output_idf_name: Optional[str] = None,
        intermediate_idf_pattern: Optional[str] = None
) -> None:
    """
    Updates an EnergyPlus IDF file to a target version by sequentially running
    the native EnergyPlus Transition tools.

    This function operates inside an isolated temporary directory. This guarantees
    that all required EnergyPlus .idd files are present during execution, prevents
    legacy Fortran path/space bugs, and ensures your project directory isn't
    littered with junk files (.idfold, .VCpErr, etc.).

    Args:
        input_idf_path (str): Absolute or relative path to the source .idf file.
        ep_version_target (str): The desired target EnergyPlus version (e.g., "25.1" or "25.1.0").
        output_idf_name (str, optional): The filename for the final updated IDF.
            Can optionally include the '{version}' placeholder (e.g., "model_v{version}.idf").
            If not provided, the script will overwrite the original input file.
        intermediate_idf_pattern (str, optional): The naming pattern for saving
            intermediate versions. MUST include the '{version}' placeholder
            (e.g., "backup_step_{version}.idf"). If None, no intermediate files are saved.

    Raises:
        ValueError: If intermediate_idf_pattern lacks the '{version}' placeholder,
                    or if the initial IDF version cannot be read.
        FileNotFoundError: If the target EnergyPlus transition directory cannot be found.
        RuntimeError: If there is a missing transition tool to complete the chain.
        subprocess.CalledProcessError: If the native EnergyPlus executable fails.
    """

    # =========================================================================
    # 0. ARGUMENT VALIDATION
    # =========================================================================
    if intermediate_idf_pattern and "{version}" not in intermediate_idf_pattern:
        raise ValueError(
            "The 'intermediate_idf_pattern' argument must contain the '{version}' "
            "placeholder to prevent intermediate files from overwriting each other. "
            "Example: 'my_model_{version}.idf'"
        )

    # =========================================================================
    # 1. PARSE AND NORMALIZE TARGET VERSION
    # =========================================================================
    target_parts = re.findall(r'\d+', ep_version_target)
    while len(target_parts) < 3:
        target_parts.append('0')
    target_str = "-".join(target_parts)

    ep_dir = rf"C:\EnergyPlusV{target_str}"
    updater_dir = os.path.join(ep_dir, "PreProcess", "IDFVersionUpdater")

    if not os.path.exists(updater_dir):
        raise FileNotFoundError(
            f"Could not find the updater directory: {updater_dir}\n"
            f"Please ensure EnergyPlus {ep_version_target} is installed on the C: drive."
        )

    # =========================================================================
    # 2. DETECT INITIAL VERSION OF THE IDF FILE
    # =========================================================================
    with open(input_idf_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    match_version = re.search(r'Version,\s*(\d+(?:\.\d+)+)\s*;', content, re.IGNORECASE)
    if not match_version:
        raise ValueError("Could not detect the initial version inside the IDF file.")

    current_parts = re.findall(r'\d+', match_version.group(1))
    while len(current_parts) < 3:
        current_parts.append('0')
    current_v_str = "-".join(current_parts)

    # =========================================================================
    # 3. MAP AVAILABLE TRANSITION TOOLS
    # =========================================================================
    transitions = {}
    for file_name in os.listdir(updater_dir):
        if file_name.startswith("Transition-") and file_name.endswith(".exe"):
            match_exe = re.match(r'Transition-V(.*)-to-V(.*)\.exe', file_name, re.IGNORECASE)
            if match_exe:
                transitions[match_exe.group(1)] = {
                    "v_to": match_exe.group(2),
                    "exe_path": os.path.join(updater_dir, file_name)
                }

    # =========================================================================
    # 4. BUILD THE TRANSITION CHAIN
    # =========================================================================
    paths_to_execute = []
    versions_route = []

    temp_v = current_v_str
    while temp_v != target_str:
        if temp_v not in transitions:
            raise RuntimeError(
                f"Broken transition chain: No tool found to upgrade from version {temp_v}."
            )
        next_step = transitions[temp_v]
        paths_to_execute.append(next_step["exe_path"])
        versions_route.append(temp_v)
        temp_v = next_step["v_to"]

    if not paths_to_execute:
        print(f"The IDF file is already at the target version ({ep_version_target}).")
        return

    # =========================================================================
    # 5. EXECUTION IN ISOLATED TEMPORARY WORKSPACE
    # =========================================================================
    base_dir = os.path.dirname(os.path.abspath(input_idf_path))
    original_idf_filename = os.path.basename(input_idf_path)
    original_cwd = os.getcwd()

    # Use a temporary directory. It automatically cleans up all junk files when done.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_idf_path = os.path.join(temp_dir, original_idf_filename)
        shutil.copy2(input_idf_path, temp_idf_path)

        # FIX: Copy ALL .idd files into the temp directory so the Fortran tools find them
        for item in os.listdir(updater_dir):
            if item.lower().endswith('.idd'):
                shutil.copy2(os.path.join(updater_dir, item), temp_dir)

        try:
            # Change working directory to the temporary environment
            os.chdir(temp_dir)

            for i, exe_path in enumerate(paths_to_execute):
                current_loop_v = versions_route[i]
                next_loop_v = transitions[current_loop_v]["v_to"]
                clean_current_v = current_loop_v.replace('-', '.')

                # Copy intermediate backup to the user's project folder BEFORE transition
                if intermediate_idf_pattern:
                    intermediate_name = intermediate_idf_pattern.format(version=clean_current_v)
                    shutil.copy2(original_idf_filename, os.path.join(base_dir, intermediate_name))

                print(f"Transitioning: {clean_current_v} -> {next_loop_v.replace('-', '.')} ...")

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                # Run transition on the local file. The tool automatically overwrites it.
                subprocess.run([exe_path, original_idf_filename],
                               check=True,
                               capture_output=True,
                               text=True,
                               startupinfo=startupinfo
                               )

            # =================================================================
            # 6. HANDLE FINAL OUTPUT NAME AND EXPORT
            # =================================================================
            clean_target_v = target_str.replace('-', '.')

            if output_idf_name:
                final_filename = output_idf_name.format(version=clean_target_v)
            else:
                final_filename = original_idf_filename

            final_output_path = os.path.join(base_dir, final_filename)

            # Move the final updated file from the temp space back to the user's folder
            shutil.copy2(original_idf_filename, final_output_path)
            print(f"Success! Final IDF saved as: {final_output_path}")

        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Transition failed.")
            print("Standard Output:", e.stdout)
            print("Standard Error:", e.stderr)
            raise

        finally:
            # Revert to the original working directory so the rest of your app works normally
            os.chdir(original_cwd)


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


def verify_accim_simulation(
        eso_file_path: str,
        idf_path: str,
        eplus_install_dir: Optional[str] = None,
        tolerance: float = 0.1,
) -> pd.DataFrame:
    """
    Reads EnergyPlus simulation output and verifies that the ACCIS EMS scripts
    added by AddAccis are working correctly.

    The function performs two categories of checks:

    **Check 1 – HVAC Setpoint Adherence (per zone):**
    - If cooling is active (CoolCoil > 0): Zone Operative Temperature <= ACST_Sch + tolerance
    - If heating is active (HeatCoil > 0): Zone Operative Temperature >= AHST_Sch - tolerance

    **Check 2 – Window Operation Logic (per window in mixed-mode models):**
    Replicates the explicit conditions of the EMS program ``SetWindowOperation_<windowname>``:

    *HVACmode = 0 (HVAC only):*
      Window must be closed (VentOpenFact == 0).

    *HVACmode = 1 (Natural Ventilation priority — HVAC as backup):*
      Window may open only when ALL of the following:
      - HVAC coils are inactive (NoH_NoC_reqs == 1)
      - OpT < ACST (cooling need)
      - WindSpeed <= MaxWindSpeed
      - OutT > MinOutTemp
      - OutT < OpT
      - Occupancy > 0

      And the VentCtrl sub-condition (for Ventilates_HVACmode1):

      - VentCtrl = 0: OutT < OpT, OutT > MinOutTemp, OpT > VST, WindSpeed <= MaxWindSpeed
      - VentCtrl = 1: OutT < OpT, OutT > MinOutTemp, OpT > ACSTnoTol, WindSpeed <= MaxWindSpeed

    *HVACmode = 2 (Changeover / Free-running):*
      Window may open when:
      NoH_NoC_reqs == 1 AND meets_base_reqs == 1 AND OpT > VST

    :param eso_file_path: Path to the eplusout.eso file.
    :type eso_file_path: str
    :param idf_path: Path to the IDF file used for simulation (to read accim args and window names).
    :type idf_path: str
    :param eplus_install_dir: Path to EnergyPlus installation directory (for ReadVarsESO).
    :type eplus_install_dir: str, optional
    :param tolerance: Temperature tolerance in °C for setpoint checks. Default is 0.1 °C.
    :type tolerance: float
    :return: DataFrame with all detected mismatch timesteps, with columns
        ['timestep', 'zone_or_window', 'check', 'description', 'value_found', 'value_expected'].
        Empty DataFrame means all checks passed.
    :rtype: pd.DataFrame
    """

    # ─────────────────────────────────────────────
    # 1. READ SIMULATION OUTPUTS
    # ─────────────────────────────────────────────
    print(f"Reading ESO file: {eso_file_path}")
    eso = read_eso_using_readvarseso(
        eso_file_path=eso_file_path,
        eplus_install_dir=eplus_install_dir,
        only_run_period=True,
        cleanup=False,
    )

    # Gather all data into one flat df to make column lookup easier
    all_dfs = []
    for freq, df in eso['data'].items():
        if df.empty:
            continue
        df_flat = df.copy()
        # Flatten MultiIndex columns to "Area:Variable" strings
        df_flat.columns = [
            f"{a}:{v}" if a != 'Environment' else f"Environment:{v}"
            for (a, v, u) in df_flat.columns
        ]
        df_flat['_freq'] = freq
        all_dfs.append(df_flat)

    if not all_dfs:
        warnings.warn("No simulation output data found in the ESO file.")
        return pd.DataFrame()

    # Use hourly if present, else first available frequency
    freq_order = ['Hourly', 'Timestep', 'Daily', 'Monthly']
    chosen_df = None
    chosen_freq = None
    for fq in freq_order:
        for df_temp in all_dfs:
            if df_temp['_freq'].iloc[0] == fq:
                chosen_df = df_temp.drop(columns=['_freq'])
                chosen_freq = fq
                break
        if chosen_df is not None:
            break

    if chosen_df is None:
        chosen_df = all_dfs[0].drop(columns=['_freq'])
        chosen_freq = all_dfs[0]['_freq'].iloc[0]

    print(f"Using output frequency: {chosen_freq} ({len(chosen_df)} time steps)")

    # ─────────────────────────────────────────────
    # 2. READ ACCIM ARGS FROM IDF
    # ─────────────────────────────────────────────
    print(f"Reading IDF: {idf_path}")
    building = get_building(idf_path)

    try:
        accim_args = get_accim_args_flattened(building)
    except Exception as e:
        warnings.warn(f"Could not read accim args from IDF: {e}. Skipping window checks.")
        accim_args = {}

    # Global EMS scalar parameters (set once per simulation, not per timestep)
    MaxWindSpeed = float(accim_args.get('MaxWindSpeed', 5.0))
    MinOutTemp   = float(accim_args.get('MinOutTemp', 6.0))
    VentCtrl     = int(float(accim_args.get('VentCtrl', 0)))
    HVACmode     = int(float(accim_args.get('HVACmode', 1)))
    VST          = float(accim_args.get('VST', 20.0))

    # ─────────────────────────────────────────────
    # HELPER: case-insensitive column searcher
    # ─────────────────────────────────────────────
    def find_col(df, area_fragment: str, variable_fragment: str) -> Optional[str]:
        """Return the first column whose 'area:variable' pattern (case-insensitive)
        contains both fragments."""
        area_frag_up = area_fragment.upper()
        var_frag_up  = variable_fragment.upper()
        for col in df.columns:
            col_up = col.upper()
            parts = col_up.split(':', 1)
            if len(parts) == 2:
                if area_frag_up in parts[0] and var_frag_up in parts[1]:
                    return col
            else:
                if var_frag_up in col_up:
                    return col
        return None

    def find_cols_by_variable(df, variable_fragment: str) -> List[str]:
        """Return all columns whose variable part contains the fragment (case-insensitive)."""
        var_frag_up = variable_fragment.upper()
        matches = []
        for col in df.columns:
            col_up = col.upper()
            parts = col_up.split(':', 1)
            var_part = parts[1] if len(parts) == 2 else col_up
            if var_frag_up in var_part:
                matches.append(col)
        return matches

    def find_cols_by_area(df, area_fragment: str) -> List[str]:
        """Return all columns whose area part contains the fragment (case-insensitive)."""
        area_frag_up = area_fragment.upper()
        matches = []
        for col in df.columns:
            col_up = col.upper()
            parts = col_up.split(':', 1)
            if len(parts) == 2 and area_frag_up in parts[0]:
                matches.append(col)
        return matches

    # ─────────────────────────────────────────────
    # 3. DETECT ZONES AND WINDOWS FROM EMS OBJECTS
    # ─────────────────────────────────────────────
    # Build a map {ems_name: actual_ep_key} from _OpT sensors.
    # 'ems_name'     = sensor Name without '_OpT'  (e.g. 'Floor_1_Residential_Living_Occupants')
    #                  matches schedule keys ACST_Sch_{ems_name}, AHST_Sch_{ems_name}
    # 'actual_ep_key'= OutputVariable_or_OutputMeter_Index_Key_Name  (e.g. 'Floor_1_Zone')
    #                  matches EnergyPlus output column areas (Zone Operative Temperature, coils …)
    ems_zone_map: Dict[str, str] = {}  # {ems_name: actual_ep_key}
    for sc in building.idfobjects['EnergyManagementSystem:Sensor']:
        if sc.Name.endswith('_OpT'):
            ems_name   = sc.Name[:-4]  # strip '_OpT'
            actual_key = str(sc.OutputVariable_or_OutputMeter_Index_Key_Name)
            ems_zone_map[ems_name] = actual_key

    ems_zone_names: List[str] = list(ems_zone_map.keys())

    # Window names (from SetWindowOperation programs)
    window_names: List[str] = []
    for prog in building.idfobjects['EnergyManagementSystem:Program']:
        if prog.Name.upper().startswith('SETWINDOWOPERATION_'):
            w = prog.Name[len('SetWindowOperation_'):]
            window_names.append(w)

    # Comfort zones = all EMS zones that are NOT window zones
    # (window zones have no ACST/AHST schedules)
    comfort_zone_names: List[str] = [z for z in ems_zone_names if z not in window_names]

    # Build map {window_ems_name: ventilation_schedule_name} for non-AFN models
    # by scanning EMS actuators whose name contains the window name
    window_vent_sch_map: Dict[str, str] = {}
    for act in building.idfobjects['EnergyManagementSystem:Actuator']:
        act_name_up = act.Name.upper()
        for wname in window_names:
            if wname.upper() in act_name_up:
                comp_id = str(act.Actuated_Component_Unique_Name)
                if comp_id and comp_id not in ('', 'None'):
                    window_vent_sch_map[wname] = comp_id
                break

    is_mixed_mode = len(window_names) > 0
    print(f"Detected {len(ems_zone_names)} EMS zone(s): {ems_zone_names}")
    print(f"  EMS→EP key map: { {k: v for k, v in ems_zone_map.items()} }")
    print(f"Mixed-mode model: {is_mixed_mode}  |  Windows detected: {window_names}")
    if window_vent_sch_map:
        print(f"  Window→VentSchedule map: {window_vent_sch_map}")
    print(f"EMS params — HVACmode={HVACmode}, VentCtrl={VentCtrl}, "
          f"MaxWindSpeed={MaxWindSpeed}, MinOutTemp={MinOutTemp}, VST={VST}")

    # ─────────────────────────────────────────────
    # 4. BUILD RESULTS ACCUMULATOR
    # ─────────────────────────────────────────────
    mismatch_rows: List[dict] = []

    def add_mismatch(timestep, zone_or_window: str, check: str,
                     description: str, value_found, value_expected):
        mismatch_rows.append({
            'timestep':       timestep,
            'zone_or_window': zone_or_window,
            'check':          check,
            'description':    description,
            'value_found':    round(float(value_found), 4) if isinstance(value_found, (int, float)) else value_found,
            'value_expected': value_expected,
        })

    # ─────────────────────────────────────────────
    # 5.A CHECK 1 – HVAC SETPOINT ADHERENCE
    # ─────────────────────────────────────────────
    print("\n--- Check 1: HVAC Setpoint Adherence ---")

    # Only run setpoint checks for comfort zones (not raw window zones)
    for zone in comfort_zone_names:
        actual_ep_key = ems_zone_map.get(zone, zone)

        # ── Operative temperature: use the actual EnergyPlus zone key in the column area
        opt_col = find_col(chosen_df, actual_ep_key, 'Operative Temperature')
        if opt_col is None:
            opt_col = find_col(chosen_df, actual_ep_key, 'Zone Operative Temperature')
        if opt_col is None:
            warnings.warn(
                f"Zone '{zone}' (EP key '{actual_ep_key}'): "
                f"No 'Operative Temperature' column found. Skipping setpoint check."
            )
            continue

        # ── ACST / AHST schedules: key uses the EMS name (not the actual zone key)
        acst_col = find_col(chosen_df, f'ACST_Sch_{zone}', 'Schedule Value')
        ahst_col = find_col(chosen_df, f'AHST_Sch_{zone}', 'Schedule Value')

        if acst_col is None or ahst_col is None:
            warnings.warn(
                f"Zone '{zone}': ACST_Sch or AHST_Sch column not found "
                f"(acst_col={acst_col}, ahst_col={ahst_col}). Skipping setpoint check."
            )
            continue

        # ── Cooling / heating rate: use actual_ep_key (the area in the output)
        cool_col = (
            find_col(chosen_df, actual_ep_key, 'Cooling Coil Total Cooling Rate')
            or find_col(chosen_df, actual_ep_key, 'VRF Heat Pump Cooling Electricity')
            or find_col(chosen_df, actual_ep_key, 'Cooling Rate')
        )
        heat_col = (
            find_col(chosen_df, actual_ep_key, 'Heating Coil Heating Rate')
            or find_col(chosen_df, actual_ep_key, 'VRF Heat Pump Heating Electricity')
            or find_col(chosen_df, actual_ep_key, 'Heating Rate')
        )

        if cool_col is None and heat_col is None:
            warnings.warn(
                f"Zone '{zone}' (EP key '{actual_ep_key}'): No cooling or heating rate column found. "
                "Setpoint check will be skipped for this zone."
            )
            continue

        print(f"  Zone '{zone}': OpT col='{opt_col}', ACST col='{acst_col}', "
              f"cool col='{cool_col}', heat col='{heat_col}'")

        opt    = chosen_df[opt_col].astype(float)
        acst   = chosen_df[acst_col].astype(float)
        ahst   = chosen_df[ahst_col].astype(float)

        for pos, idx in enumerate(chosen_df.index):
            opt_val  = float(opt.iat[pos])
            acst_val = float(acst.iat[pos])
            ahst_val = float(ahst.iat[pos])

            # Cooling check
            if cool_col is not None:
                cool_rate = float(chosen_df[cool_col].iat[pos])
                if cool_rate > 0 and opt_val > acst_val + tolerance:
                    add_mismatch(
                        timestep       = idx,
                        zone_or_window = zone,
                        check          = 'Check1_Cooling',
                        description    = (
                            f"Cooling active (rate={cool_rate:.2f} W) but OpT ({opt_val:.2f} °C) "
                            f"> ACST ({acst_val:.2f} °C) + tolerance ({tolerance} °C)"
                        ),
                        value_found    = opt_val,
                        value_expected = f"<= {acst_val + tolerance:.2f} °C",
                    )

            # Heating check
            if heat_col is not None:
                heat_rate = float(chosen_df[heat_col].iat[pos])
                if heat_rate > 0 and opt_val < ahst_val - tolerance:
                    add_mismatch(
                        timestep       = idx,
                        zone_or_window = zone,
                        check          = 'Check1_Heating',
                        description    = (
                            f"Heating active (rate={heat_rate:.2f} W) but OpT ({opt_val:.2f} °C) "
                            f"< AHST ({ahst_val:.2f} °C) - tolerance ({tolerance} °C)"
                        ),
                        value_found    = opt_val,
                        value_expected = f">= {ahst_val - tolerance:.2f} °C",
                    )

        # Summary per zone
        cool_fails = sum(1 for r in mismatch_rows
                         if r['zone_or_window'] == zone and r['check'] == 'Check1_Cooling')
        heat_fails = sum(1 for r in mismatch_rows
                         if r['zone_or_window'] == zone and r['check'] == 'Check1_Heating')
        total_ts = len(chosen_df)
        print(f"  Zone '{zone}': Cooling mismatches: {cool_fails}/{total_ts} | "
              f"Heating mismatches: {heat_fails}/{total_ts}")

    # ─────────────────────────────────────────────
    # 5.B CHECK 2 – WINDOW OPERATION LOGIC
    # ─────────────────────────────────────────────
    if is_mixed_mode:
        print("\n--- Check 2: Window Operation Logic (SetWindowOperation) ---")

        # Outdoor temperature and wind speed (Environment-level sensors)
        out_t_col  = (find_col(chosen_df, 'Environment', 'Site Outdoor Air Drybulb Temperature')
                      or find_col(chosen_df, 'ENVIRONMENT', 'Drybulb'))
        wind_col   = (find_col(chosen_df, 'Environment', 'Site Wind Speed')
                      or find_col(chosen_df, 'ENVIRONMENT', 'Wind Speed'))

        if out_t_col is None:
            warnings.warn("'Site Outdoor Air Drybulb Temperature' column not found. "
                          "Window checks requiring OutT will be skipped.")
        if wind_col is None:
            warnings.warn("'Site Wind Speed' column not found. "
                          "Window checks requiring WindSpeed will be skipped.")

        for wname in window_names:
            # Actual EnergyPlus key for the window zone (e.g. 'Floor_1_Zone')
            actual_win_key = ems_zone_map.get(wname, wname)

            # ── Opening factor
            # 1. Try AFN surface opening factor
            vof_col = (
                find_col(chosen_df, wname, 'AFN Surface Venting Window or Door Opening Factor')
                or find_col(chosen_df, actual_win_key, 'AFN Surface Venting Window or Door Opening Factor')
                or find_col(chosen_df, wname, 'Opening Factor')
            )
            if vof_col is None:
                # 2. Scheduled ventilation: look up schedule from the actuator map built earlier
                vent_sch_name = window_vent_sch_map.get(wname)
                if vent_sch_name:
                    vof_col = find_col(chosen_df, vent_sch_name, 'Schedule Value')
            if vof_col is None:
                # 3. Derive schedule name from actual EnergyPlus zone key: Vent_Sch_{actual_win_key}
                vof_col = find_col(chosen_df, f'Vent_Sch_{actual_win_key}', 'Schedule Value')
            if vof_col is None:
                warnings.warn(
                    f"Window '{wname}' (EP key '{actual_win_key}'): "
                    f"No opening factor / ventilation schedule column found. Skipping window check."
                )
                continue

            print(f"  Window '{wname}': opening-factor col='{vof_col}'")

            # ── Per-window operative temperature: use actual EP key
            opt_w_col = (
                find_col(chosen_df, actual_win_key, 'Operative Temperature')
                or find_col(chosen_df, actual_win_key, 'Zone Operative Temperature')
                or find_col(chosen_df, wname, 'Operative Temperature')
            )

            # ── Cooling / heating coils: use actual EP key
            cool_w_col = (
                find_col(chosen_df, actual_win_key, 'Cooling Coil Total Cooling Rate')
                or find_col(chosen_df, actual_win_key, 'Cooling Rate')
                or find_col(chosen_df, wname, 'Cooling Coil Total Cooling Rate')
            )
            heat_w_col = (
                find_col(chosen_df, actual_win_key, 'Heating Coil Heating Rate')
                or find_col(chosen_df, actual_win_key, 'Heating Rate')
                or find_col(chosen_df, wname, 'Heating Coil Heating Rate')
            )

            # ── Occupancy: try window zone first, then fall back to any EMS occ column
            occ_col = (
                find_col(chosen_df, actual_win_key, 'People Occupant Count')
                or find_col(chosen_df, wname, 'People Occupant Count')
            )
            # Last resort: use any EMS occupancy output (first comfort zone)
            if occ_col is None:
                for cz in comfort_zone_names:
                    occ_col = find_col(chosen_df, 'EMS', f'People Occupant Count_{cz}')
                    if occ_col:
                        break

            # ── ACST reference for window zone: take from first comfort zone
            # (ACSTnoTol is a global EMS variable, approximated here by the schedule value)
            acst_no_tol_col = None
            for cz in comfort_zone_names:
                cand = find_col(chosen_df, f'ACST_Sch_{cz}', 'Schedule Value')
                if cand:
                    acst_no_tol_col = cand
                    break
            acst_w_col = acst_no_tol_col

            vof    = chosen_df[vof_col].astype(float)
            out_t  = chosen_df[out_t_col].astype(float) if out_t_col else None
            wind   = chosen_df[wind_col].astype(float)  if wind_col  else None

            prev_checks = len(mismatch_rows)

            for pos, idx in enumerate(chosen_df.index):
                vof_val = float(vof.iat[pos])
                window_open = vof_val > 0.0

                # Retrieve optional per-timestep variables safely
                opt_val   = float(chosen_df[opt_w_col].iat[pos])   if opt_w_col   else None
                cool_val  = float(chosen_df[cool_w_col].iat[pos])  if cool_w_col  else 0.0
                heat_val  = float(chosen_df[heat_w_col].iat[pos])  if heat_w_col  else 0.0
                occ_val   = float(chosen_df[occ_col].iat[pos])     if occ_col     else 1.0
                out_t_val = float(out_t.iat[pos])                  if out_t  is not None else None
                wind_val  = float(wind.iat[pos])                   if wind   is not None else 0.0
                acst_val  = float(chosen_df[acst_w_col].iat[pos])  if acst_w_col  else None

                # ── Derive NoH_NoC_reqs
                no_h_no_c = (cool_val == 0.0) and (heat_val == 0.0)

                # ───────────────────────────────────────────────────
                # HVACmode = 0: window must NEVER open
                # ───────────────────────────────────────────────────
                if HVACmode == 0:
                    if window_open:
                        add_mismatch(
                            timestep       = idx,
                            zone_or_window = wname,
                            check          = 'Check2_HVACmode0',
                            description    = (
                                f"HVACmode=0 (HVAC-only) but window is open "
                                f"(VentOpenFact={vof_val:.3f})"
                            ),
                            value_found    = vof_val,
                            value_expected = 0.0,
                        )

                # ───────────────────────────────────────────────────
                # HVACmode = 1: window opens only when all conditions met
                # ───────────────────────────────────────────────────
                elif HVACmode == 1:
                    if window_open:
                        # Condition: noH_noC_reqs must be True
                        if not no_h_no_c:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_NoHNoC',
                                description    = (
                                    f"HVACmode=1: Window open but HVAC is active "
                                    f"(CoolCoil={cool_val:.2f}, HeatCoil={heat_val:.2f})"
                                ),
                                value_found    = f"cool={cool_val:.2f}, heat={heat_val:.2f}",
                                value_expected = "CoolCoil=0 AND HeatCoil=0",
                            )

                        # Condition: OpT < roundedACST (cooling need)
                        if opt_val is not None and acst_val is not None:
                            if opt_val >= acst_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode1_OpT_lt_ACST',
                                    description    = (
                                        f"HVACmode=1: Window open but OpT ({opt_val:.2f} °C) "
                                        f">= ACST ({acst_val:.2f} °C) — no cooling need"
                                    ),
                                    value_found    = opt_val,
                                    value_expected = f"< {acst_val:.2f} °C",
                                )

                        # Condition: WindSpeed <= MaxWindSpeed
                        if wind_val > MaxWindSpeed:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_WindSpeed',
                                description    = (
                                    f"HVACmode=1: Window open but WindSpeed ({wind_val:.2f} m/s) "
                                    f"> MaxWindSpeed ({MaxWindSpeed} m/s)"
                                ),
                                value_found    = wind_val,
                                value_expected = f"<= {MaxWindSpeed} m/s",
                            )

                        # Condition: OutT > MinOutTemp
                        if out_t_val is not None and out_t_val <= MinOutTemp:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_MinOutTemp',
                                description    = (
                                    f"HVACmode=1: Window open but OutT ({out_t_val:.2f} °C) "
                                    f"<= MinOutTemp ({MinOutTemp} °C)"
                                ),
                                value_found    = out_t_val,
                                value_expected = f"> {MinOutTemp} °C",
                            )

                        # Condition: OutT < OpT (outdoor cooler than indoor)
                        if out_t_val is not None and opt_val is not None:
                            if out_t_val >= opt_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode1_OutT_lt_OpT',
                                    description    = (
                                        f"HVACmode=1: Window open but OutT ({out_t_val:.2f} °C) "
                                        f">= OpT ({opt_val:.2f} °C)"
                                    ),
                                    value_found    = out_t_val,
                                    value_expected = f"< OpT ({opt_val:.2f} °C)",
                                )

                        # Condition: Occupancy > 0
                        if occ_val <= 0:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode1_Occupancy',
                                description    = (
                                    f"HVACmode=1: Window open but zone is unoccupied "
                                    f"(Occ_count={occ_val})"
                                ),
                                value_found    = occ_val,
                                value_expected = "> 0",
                            )

                        # VentCtrl sub-condition for Ventilates_HVACmode1
                        if VentCtrl == 0:
                            # OpT > VST
                            if opt_val is not None and opt_val <= VST:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode1_VentCtrl0_OpT_gt_VST',
                                    description    = (
                                        f"VentCtrl=0: Window open but OpT ({opt_val:.2f} °C) "
                                        f"<= VST ({VST} °C)"
                                    ),
                                    value_found    = opt_val,
                                    value_expected = f"> {VST} °C",
                                )

                        elif VentCtrl == 1:
                            # OpT > ACSTnoTol (≈ ACST without offset)
                            if opt_val is not None and acst_val is not None:
                                if opt_val <= acst_val:
                                    add_mismatch(
                                        timestep       = idx,
                                        zone_or_window = wname,
                                        check          = 'Check2_HVACmode1_VentCtrl1_OpT_gt_ACSTnoTol',
                                        description    = (
                                            f"VentCtrl=1: Window open but OpT ({opt_val:.2f} °C) "
                                            f"<= ACSTnoTol ({acst_val:.2f} °C)"
                                        ),
                                        value_found    = opt_val,
                                        value_expected = f"> {acst_val:.2f} °C",
                                    )

                # ───────────────────────────────────────────────────
                # HVACmode = 2: changeover / free-running
                # Window can open when: NoH_NoC_reqs AND meets_base_reqs AND OpT > VST
                # meets_base_reqs: OpT < ACST, WindSpeed <= MaxWind, OutT > MinOutTemp,
                #                  OutT < OpT, Occ > 0
                # ───────────────────────────────────────────────────
                elif HVACmode == 2:
                    if window_open:
                        # NoH_NoC_reqs: HVAC must be off
                        if not no_h_no_c:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_NoHNoC',
                                description    = (
                                    f"HVACmode=2: Window open but HVAC is active "
                                    f"(CoolCoil={cool_val:.2f}, HeatCoil={heat_val:.2f})"
                                ),
                                value_found    = f"cool={cool_val:.2f}, heat={heat_val:.2f}",
                                value_expected = "CoolCoil=0 AND HeatCoil=0",
                            )

                        # meets_base_reqs: OpT < ACST
                        if opt_val is not None and acst_val is not None:
                            if opt_val >= acst_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode2_OpT_lt_ACST',
                                    description    = (
                                        f"HVACmode=2: Window open but OpT ({opt_val:.2f} °C) "
                                        f">= ACST ({acst_val:.2f} °C)"
                                    ),
                                    value_found    = opt_val,
                                    value_expected = f"< {acst_val:.2f} °C",
                                )

                        # meets_base_reqs: WindSpeed <= MaxWindSpeed
                        if wind_val > MaxWindSpeed:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_WindSpeed',
                                description    = (
                                    f"HVACmode=2: Window open but WindSpeed ({wind_val:.2f} m/s) "
                                    f"> MaxWindSpeed ({MaxWindSpeed} m/s)"
                                ),
                                value_found    = wind_val,
                                value_expected = f"<= {MaxWindSpeed} m/s",
                            )

                        # meets_base_reqs: OutT > MinOutTemp
                        if out_t_val is not None and out_t_val <= MinOutTemp:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_MinOutTemp',
                                description    = (
                                    f"HVACmode=2: Window open but OutT ({out_t_val:.2f} °C) "
                                    f"<= MinOutTemp ({MinOutTemp} °C)"
                                ),
                                value_found    = out_t_val,
                                value_expected = f"> {MinOutTemp} °C",
                            )

                        # meets_base_reqs: OutT < OpT
                        if out_t_val is not None and opt_val is not None:
                            if out_t_val >= opt_val:
                                add_mismatch(
                                    timestep       = idx,
                                    zone_or_window = wname,
                                    check          = 'Check2_HVACmode2_OutT_lt_OpT',
                                    description    = (
                                        f"HVACmode=2: Window open but OutT ({out_t_val:.2f} °C) "
                                        f">= OpT ({opt_val:.2f} °C)"
                                    ),
                                    value_found    = out_t_val,
                                    value_expected = f"< OpT ({opt_val:.2f} °C)",
                                )

                        # meets_base_reqs: Occupancy > 0
                        if occ_val <= 0:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_Occupancy',
                                description    = (
                                    f"HVACmode=2: Window open but zone is unoccupied "
                                    f"(Occ_count={occ_val})"
                                ),
                                value_found    = occ_val,
                                value_expected = "> 0",
                            )

                        # Ventilates_HVACmode2: OpT > VST
                        if opt_val is not None and opt_val <= VST:
                            add_mismatch(
                                timestep       = idx,
                                zone_or_window = wname,
                                check          = 'Check2_HVACmode2_OpT_gt_VST',
                                description    = (
                                    f"HVACmode=2: Window open but OpT ({opt_val:.2f} °C) "
                                    f"<= VST ({VST} °C)"
                                ),
                                value_found    = opt_val,
                                value_expected = f"> {VST} °C",
                            )

            new_fails = len(mismatch_rows) - prev_checks
            open_ts   = int((vof > 0.0).sum())
            print(f"  Window '{wname}': {open_ts}/{len(chosen_df)} timesteps open | "
                  f"Condition violations: {new_fails}")

    # ─────────────────────────────────────────────
    # 6. RETURN RESULTS
    # ─────────────────────────────────────────────
    result_df = pd.DataFrame(mismatch_rows)

    if result_df.empty:
        print("\n✓ All checks passed. No mismatches detected.")
    else:
        print(f"\n✗ {len(result_df)} mismatch(es) detected across "
              f"{result_df['check'].nunique()} check type(s).")
        print(result_df.groupby(['zone_or_window', 'check']).size()
              .rename('count').reset_index().to_string(index=False))

    return result_df


class AccimSimulationVerifier:
    """
    Object-oriented utility to verify ACCIM EMS simulation results.

    This class reads an EnergyPlus simulation output (either ``.csv`` or ``.eso``) and
    evaluates two primary checks to ensure adaptive comfort setups function correctly:

    - **Check 1**: Operative Temperature adherence within adjusted setpoint bounds (all timesteps).
    - **Check 2**: Window operation conditional logic for Mixed-Mode models (HVACmode = 2).

    Parameters
    ----------
    eso_file_path : str
        Absolute or relative path to the EnergyPlus output data. If an ``eplusout.csv``
        file exists alongside the ``.eso``, it is read directly to avoid the overhead of
        running ``ReadVarsESO``. Otherwise the ESO is parsed via besos.
    idf_path : str
        Path to the corresponding IDF model. Used to auto-discover EMS sensor names,
        window names, zone names, and control parameters (HVACmode, MaxWindSpeed,
        ACSTtol, AHSTtol) from the ``SetInputData`` EMS program.
    eplus_install_dir : Optional[str], default None
        EnergyPlus installation directory, required by ``ReadVarsESO`` when falling back
        to ``.eso`` parsing.

    Attributes
    ----------
    summary : str
        Human-readable string summarising violation counts for Check 1 and Check 2.
    violations : Dict[str, pd.DataFrame]
        Raw violation rows, one per flagged timestep. Keys are ``'setpoint'`` and
        ``'window'``. Each DataFrame has columns:
        ``['timestep', 'zone_or_window', 'check', 'description', 'value_found',
        'value_expected']``.
    summary_table_setpoint : pd.DataFrame
        Aggregated count table for Check 1 violations, grouped by zone and check type.
        Columns: ``['zone_or_window', 'check', 'count']``. Empty if no violations.
    summary_table_window : pd.DataFrame
        Aggregated count table for Check 2 violations, grouped by window and condition.
        Columns: ``['zone_or_window', 'check', 'count']``. Empty if no violations.

    Check Identifiers
    -----------------
    The ``check`` column in the violation DataFrames uses the following identifiers:

    **Check 1 -- Setpoint Adherence**

    ``Check1_TooHot``
        The zone Operative Temperature (OpT) exceeds the **adjusted cooling setpoint**,
        defined as ``ACST_Sch - ACSTtol``. ``ACST_Sch`` is the per-timestep adaptive
        cooling setpoint schedule computed by the EMS; ``ACSTtol`` is the tolerance
        margin subtracted to give the effective upper comfort band limit.
        EnergyPlus columns: ``Zone Operative Temperature``,
        ``Schedule Value`` for ``ACST_Sch_<zone>``.
        A single isolated spike (one timestep violated with no violation immediately
        before or after) is **pardoned** to absorb transient thermal shocks (e.g. a brief
        window opening that lets in cold/hot air).

    ``Check1_TooCold``
        The zone Operative Temperature (OpT) falls below the **adjusted heating setpoint**,
        defined as ``AHST_Sch - AHSTtol``. ``AHST_Sch`` is the per-timestep adaptive
        heating setpoint schedule; ``AHSTtol`` is the tolerance margin subtracted to give
        the effective lower comfort band limit.
        EnergyPlus columns: ``Zone Operative Temperature``,
        ``Schedule Value`` for ``AHST_Sch_<zone>``.
        Same single-spike pardon applies as for ``Check1_TooHot``.

    **Check 2 -- Window Operation Logic (Mixed-Mode, HVACmode = 2)**

    In Mixed-Mode the EMS program ``SetWindowOperation_<window>`` controls the ventilation
    opening fraction every timestep. All seven conditions below must hold simultaneously
    for the window to be legitimately open. A violation is flagged whenever the window is
    open but any condition is not satisfied.

    Automatic pardons are applied to account for the inherent one-timestep EMS actuation lag:

    - ``close_transit``: the **last open timestep** before a window closing event is pardoned,
      because the EMS detects the condition violation at timestep t but the close command only
      takes effect at timestep t+1.
    - ``just_turned_on``: the **first timestep of HVAC activation** is pardoned for the same
      reason: the window was still open when the HVAC came on, and the EMS closes it at t+1.
    - ``open_transit`` *(Hourly frequency only)*: the **first hour of a window opening block**
      is also pardoned, because hourly averaging of mixed on/off states within the hour produces
      artificial condition overlaps that do not represent true violations.

    ``Check2_Cond1_HVACidle``
        The mechanical system must not be active while the window is open. Mixed-Mode logic
        prohibits simultaneous HVAC and natural ventilation to prevent energy waste (e.g.
        conditioned air escaping through open windows).
        EnergyPlus columns: ``Cooling Coil Total Cooling Rate``, ``Heating Coil Heating Rate``.
        Condition: CoolingRate == 0 AND HeatingRate == 0.

    ``Check2_Cond2_Occupied``
        The zone must be occupied for natural ventilation to activate. The EMS suppresses window
        opening when the zone is unoccupied to avoid unnecessary air infiltration.
        EnergyPlus column: ``People Occupant Count``.
        Condition: OccupantCount > 0.

    ``Check2_Cond3_OpT_lt_ACST``
        The zone Operative Temperature must be **below** the adaptive cooling setpoint. This
        ensures natural ventilation is only triggered when there is a genuine cooling need,
        i.e. indoor temperature has not yet reached the comfort upper limit.
        EnergyPlus columns: ``Zone Operative Temperature``,
        ``Schedule Value`` for ``ACST_Sch_<zone>`` (minus ACSTtol).
        Condition: OpT < ACST_Sch - ACSTtol.

    ``Check2_Cond4_OpT_gt_VST``
        The zone Operative Temperature must be **above** the Ventilation Setpoint Temperature
        (VST). VST is the lower thermal comfort bound: below it, natural ventilation would cause
        overcooling discomfort, so the window must stay closed.
        EnergyPlus column: EMS output ``Ventilation Setpoint Temperature`` -- a **per-timestep
        series** computed dynamically by the EMS, not a static value.
        Condition: OpT > VST.

    ``Check2_Cond5_OutT_lt_OpT``
        The outdoor air temperature must be **lower** than the indoor Operative Temperature for
        natural ventilation to be thermally effective. If outdoor air is warmer than indoors,
        opening windows would heat the space rather than cool it.
        EnergyPlus columns: ``Site Outdoor Air Drybulb Temperature``, ``Zone Operative Temperature``.
        Condition: OutdoorT < OpT.

    ``Check2_Cond6_MinOutTemp``
        The outdoor air temperature must **exceed** the Minimum Outdoor Temperature threshold.
        This prevents natural ventilation when outdoor conditions are too cold, which could cause
        thermal discomfort or damage HVAC equipment.
        EnergyPlus column: EMS output ``Minimum Outdoor Temperature for ventilation`` -- a
        **per-timestep series** computed dynamically by the EMS, not a static value.
        Condition: OutdoorT > MinOutTemp.

    ``Check2_Cond7_MaxWindSpeed``
        The outdoor wind speed must not exceed the maximum allowed threshold. High wind speeds
        can cause excessive infiltration rates, draughts, or structural concerns.
        EnergyPlus column: ``Site Wind Speed``.
        Condition: WindSpeed <= MaxWindSpeed, where MaxWindSpeed is a static scalar extracted
        from the ``SetInputData`` EMS program in the IDF.

    Notes
    -----
    **Hourly frequency warning**: Hourly outputs are averaged over the full hour, so a window
    that opens for only 10 minutes shows a fractional opening factor. Conditions that were
    mutually exclusive within the hour (e.g. HVAC active for 10 min, window open for 50 min)
    can appear to overlap in the hourly average, causing false positives. Sub-hourly (Timestep)
    output frequency is strongly recommended for accurate verification.

    **Required EnergyPlus outputs**: All relevant ``Output:Variable`` objects must be present in
    the IDF. If any required column is missing from the CSV/ESO, a ``ValueError`` is raised
    identifying exactly which output is absent.
    """
    def __init__(
            self,
            eso_file_path: str,
            idf_path: str,
            eplus_install_dir: Optional[str] = None,
    ):
        self.eso_file_path = eso_file_path
        self.idf_path = idf_path
        self.eplus_install_dir = eplus_install_dir

        self.summary: str = ""
        self.violations: Dict[str, pd.DataFrame] = {
            "setpoint": pd.DataFrame(),
            "window": pd.DataFrame()
        }
        self.summary_table_setpoint: Optional[pd.DataFrame] = None
        self.summary_table_window: Optional[pd.DataFrame] = None

        self._evaluate()

    def _evaluate(self):
        # ─────────────────────────────────────────────────────────────────────────
        # 1. READ CSV/ESO → FLAT DATAFRAME
        # ─────────────────────────────────────────────────────────────────────────
        csv_path = self.eso_file_path.replace('.eso', '.csv')
        if os.path.exists(csv_path):
            print(f"Reading CSV file directly: {csv_path}")
            chosen_df = pd.read_csv(csv_path)
            
            if 'Date/Time' in chosen_df.columns:
                _timestamps = chosen_df['Date/Time'].astype(str)
            else:
                _timestamps = pd.Series(chosen_df.index, dtype=str)
                
            # Deduce frequency dynamically to correctly initialize chosen_freq
            chosen_freq = 'Unknown'
            dt_str = _timestamps.str.strip().str.slice(0, 5)
            if len(dt_str) > 0 and "/" in dt_str.iloc[0]:
                ts_per_day = dt_str.value_counts().mode().iloc[0]
                if ts_per_day == 24:
                    chosen_freq = 'Hourly'
                elif ts_per_day > 24:
                    chosen_freq = 'Timestep'
                elif ts_per_day == 1:
                    chosen_freq = 'Daily'
        else:
            print(f"Reading ESO file: {self.eso_file_path}")
            eso = read_eso_using_readvarseso(
                eso_file_path=self.eso_file_path,
                eplus_install_dir=self.eplus_install_dir,
                only_run_period=True,  # Note: 8832 hours often means EnergyPlus included 3 Design Days in the ESO
                cleanup=False,
            )

            all_dfs = []
            for freq, df in eso['data'].items():
                if df.empty:
                    continue
                df_flat = df.copy()
                df_flat.columns = [f"{a}:{v}" for (a, v, u) in df_flat.columns]
                df_flat['_freq'] = freq
                all_dfs.append(df_flat)

            if not all_dfs:
                warnings.warn("No simulation output data found in the ESO file.")
                self.summary = "Verification failed: No simulation output data found."
                return

            # Prefer the finest available frequency so window checks are accurate
            for fq in ('Timestep', 'Hourly', 'Daily', 'Monthly'):
                match = next((d for d in all_dfs if d['_freq'].iloc[0] == fq), None)
                if match is not None:
                    chosen_df = match.drop(columns=['_freq'])
                    chosen_freq = fq
                    break
            else:
                chosen_df = all_dfs[0].drop(columns=['_freq'])
                chosen_freq = all_dfs[0]['_freq'].iloc[0]

            _timestamps = pd.Series(chosen_df.index, dtype=object)

        print(f"Using output frequency: {chosen_freq} ({len(chosen_df)} timesteps total)")
        
        # Print warning if Hourly is selected because averaging behavior
        # can mask instantaneous states and produce artificial logic conflicts.
        if chosen_freq == 'Hourly':
            warn_msg = (
                "Warning: Hourly frequency selected. Results may be mathematically "
                "inconsistent because hourly outputs average the window openings "
                "and HVAC active states. Mid-hour transitions generally trigger "
                "false-positive overlaps. Timestep frequency is highly recommended."
            )
            print(f"[{chosen_freq}] {warn_msg}")
            warnings.warn(warn_msg)

        # ─── Remove Design Days (Sizing Period) ──────────────────────────────────
        dt_str = _timestamps.str.strip().str.slice(0, 5)
        if len(dt_str) > 0 and "/" in dt_str.iloc[0]:
            ts_per_day = dt_str.value_counts().mode().iloc[0]
            expected_annual = ts_per_day * (366 if "02/29" in dt_str.values else 365)
            
            if len(chosen_df) > expected_annual:
                drop_count = len(chosen_df) - expected_annual
                chosen_df = chosen_df.iloc[drop_count:].copy()
                _timestamps = _timestamps.iloc[drop_count:].copy()
                print(f"Dropped {drop_count} design/warm-up timesteps. Kept {len(chosen_df)} run-period timesteps.")

        chosen_df = chosen_df.reset_index(drop=True)
        _timestamps = _timestamps.reset_index(drop=True)

        def _find(area_frag: str, var_frag: str) -> Optional[str]:
            au, vu = area_frag.upper(), var_frag.upper()
            for col in chosen_df.columns:
                parts = col.upper().split(':', 1)
                if len(parts) == 2 and au in parts[0] and vu in parts[1]:
                    return col
            return None

        # ─────────────────────────────────────────────────────────────────────────
        # 2. READ IDF — zone names, window names, EMS params
        # ─────────────────────────────────────────────────────────────────────────
        print(f"Reading IDF: {self.idf_path}")
        building = get_building(self.idf_path)

        ems_zone_map: Dict[str, str] = {}
        for sc in building.idfobjects['EnergyManagementSystem:Sensor']:
            if sc.Name.endswith('_OpT'):
                ems_zone_map[sc.Name[:-4]] = str(sc.OutputVariable_or_OutputMeter_Index_Key_Name)

        window_names: List[str] = [
            prog.Name[len('SetWindowOperation_'):]
            for prog in building.idfobjects['EnergyManagementSystem:Program']
            if prog.Name.upper().startswith('SETWINDOWOPERATION_')
        ]
        comfort_zones = [z for z in ems_zone_map if z not in window_names]

        try:
            accim_args = get_accim_args_flattened(building)
        except Exception:
            accim_args = {}

        if 'HVACmode' not in accim_args:
            raise ValueError("Required 'HVACmode' parameter not found in IDF.")
        if 'MaxWindSpeed' not in accim_args:
            raise ValueError("Required 'MaxWindSpeed' parameter not found in IDF.")

        HVACmode    = int(float(accim_args['HVACmode']))
        MaxWindSpeed= float(accim_args['MaxWindSpeed'])

        window_vent_sch_map: Dict[str, str] = {}
        for act in building.idfobjects['EnergyManagementSystem:Actuator']:
            act_name_up = act.Name.upper()
            for wname in window_names:
                if wname.upper() in act_name_up:
                    comp_id = str(act.Actuated_Component_Unique_Name)
                    if comp_id and comp_id not in ('', 'None'):
                        window_vent_sch_map[wname] = comp_id
                    break

        _acst_tol_col = _find('EMS', 'z_test_ACSTtol')
        _ahst_tol_col = _find('EMS', 'z_test_AHSTtol')
        
        acst_tol_val = float(chosen_df[_acst_tol_col].iat[0]) if _acst_tol_col else None
        ahst_tol_val = float(chosen_df[_ahst_tol_col].iat[0]) if _ahst_tol_col else None

        if acst_tol_val is None or ahst_tol_val is None:
            # Fallback securely to the SetInputData Program embedded in the IDF model
            for prog in building.idfobjects['EnergyManagementSystem:Program']:
                if prog.Name.upper() == 'SETINPUTDATA':
                    for i in range(1, 40):
                        field = f"Program_Line_{i}"
                        if hasattr(prog, field):
                            val = getattr(prog, field)
                            if not val: continue
                            val_str = str(val).upper().replace(' ', '')
                            if val_str.startswith('SETACSTTOL='):
                                acst_tol_val = float(val_str.split('=')[1])
                            elif val_str.startswith('SETAHSTTOL='):
                                ahst_tol_val = float(val_str.split('=')[1])
                    break

        if acst_tol_val is None or ahst_tol_val is None:
            raise ValueError("Required ACSTtol or AHSTtol variable not found in EMS output columns or SetInputData program.")
            
        acst_tol = float(acst_tol_val)
        ahst_tol = float(ahst_tol_val)

        print(f"ACSTtol={acst_tol} °C  |  AHSTtol={ahst_tol} °C")
        print(f"HVACmode={HVACmode}  |  MaxWindSpeed={MaxWindSpeed} m/s")

        # ─────────────────────────────────────────────────────────────────────────
        # 3. ACCUMULATE VIOLATIONS
        # ─────────────────────────────────────────────────────────────────────────
        violations_setpoint: List[dict] = []
        violations_window: List[dict] = []
        summary_lines = [f"Checked {len(chosen_df)} timesteps."]

        def _add(pos_array, target_list: List[dict], zone_or_window: str, check: str,
                 desc_fn, found_fn, expected_fn):
            for p in pos_array:
                target_list.append({
                    'timestep':       _timestamps.iat[p],
                    'zone_or_window': zone_or_window,
                    'check':          check,
                    'description':    desc_fn(p),
                    'value_found':    found_fn(p),
                    'value_expected': expected_fn(p),
                })

        # ─── CHECK 1: SETPOINTS ──────────────────────────────────────────────────
        print("\n--- Check 1: Temperature within adjusted setpoint bounds ---")
        summary_lines.append("\n[Check 1: Setpoints]")

        for zone in comfort_zones:
            actual_key = ems_zone_map.get(zone, zone)

            opt_col  = _find(actual_key, 'Operative Temperature') or _find(actual_key, 'Zone Operative Temperature')
            acst_col = _find(f'ACST_Sch_{zone}', 'Schedule Value')
            ahst_col = _find(f'AHST_Sch_{zone}', 'Schedule Value')

            if not opt_col: raise ValueError(f"Required 'Operative Temperature' output not found for zone '{zone}'.")
            if not acst_col: raise ValueError(f"Required 'ACST_Sch_{zone}' output not found.")
            if not ahst_col: raise ValueError(f"Required 'AHST_Sch_{zone}' output not found.")

            opt          = chosen_df[opt_col].astype(float)
            acst_limit   = chosen_df[acst_col].astype(float) - acst_tol   # ACST_SCH − ACSTtol
            ahst_limit   = chosen_df[ahst_col].astype(float) - ahst_tol   # AHST_SCH − AHSTtol

            # Too hot (pardon isolated 1-timestep spikes)
            hot_mask = (opt > acst_limit).values
            hot_prev = pd.Series(hot_mask).shift(1, fill_value=False).values
            hot_next = pd.Series(hot_mask).shift(-1, fill_value=False).values
            valid_hot = hot_mask & ~(hot_mask & ~hot_prev & ~hot_next)
            hot_pos = valid_hot.nonzero()[0]
            
            _add(hot_pos, violations_setpoint, zone, 'Check1_TooHot',
                 lambda p: f"OpT ({opt.iat[p]:.2f}°C) > ACST_SCH−ACSTtol ({acst_limit.iat[p]:.2f}°C)",
                 lambda p: round(float(opt.iat[p]), 4),
                 lambda p: f"<= {acst_limit.iat[p]:.2f}°C")

            # Too cold (pardon isolated 1-timestep spikes)
            cold_mask = (opt < ahst_limit).values
            cold_prev = pd.Series(cold_mask).shift(1, fill_value=False).values
            cold_next = pd.Series(cold_mask).shift(-1, fill_value=False).values
            valid_cold = cold_mask & ~(cold_mask & ~cold_prev & ~cold_next)
            cold_pos = valid_cold.nonzero()[0]
            
            _add(cold_pos, violations_setpoint, zone, 'Check1_TooCold',
                 lambda p: f"OpT ({opt.iat[p]:.2f}°C) < AHST_SCH−AHSTtol ({ahst_limit.iat[p]:.2f}°C)",
                 lambda p: round(float(opt.iat[p]), 4),
                 lambda p: f">= {ahst_limit.iat[p]:.2f}°C")

            n_hot, n_cold, total = len(hot_pos), len(cold_pos), len(chosen_df)
            msg = f"  Zone '{zone}': too-hot={n_hot}/{total}  |  too-cold={n_cold}/{total}"
            print(msg)
            summary_lines.append(msg)

        # ─── CHECK 2: WINDOW OPERATION ───────────────────────────────────────────
        if HVACmode == 2 and window_names:
            print("\n--- Check 2: Window operation conditions (HVACmode=2) ---")
            summary_lines.append("\n[Check 2: Windows]")

            out_t_col = _find('Environment', 'Site Outdoor Air Drybulb Temperature')
            if not out_t_col: raise ValueError("Required 'Site Outdoor Air Drybulb Temperature' column not found in output.")
            wind_col  = _find('Environment', 'Site Wind Speed')
            if not wind_col: raise ValueError("Required 'Site Wind Speed' column not found in output.")

            out_t = chosen_df[out_t_col].astype(float)
            wind  = chosen_df[wind_col].astype(float)
            
            min_out_t_col = _find('EMS', 'Minimum Outdoor Temperature for ventilation')
            if not min_out_t_col: raise ValueError("Required 'Minimum Outdoor Temperature for ventilation' EMS output not found.")
            vst_col       = _find('EMS', 'Ventilation Setpoint Temperature')
            if not vst_col: raise ValueError("Required 'Ventilation Setpoint Temperature' EMS output not found.")
            
            min_out_t_series = chosen_df[min_out_t_col].astype(float)
            vst_series = chosen_df[vst_col].astype(float)

            for wname in window_names:
                actual_win_key = ems_zone_map.get(wname, wname)

                vof_col = (
                    _find(wname, 'AFN Surface Venting Window or Door Opening Factor')
                    or _find(actual_win_key, 'AFN Surface Venting Window or Door Opening Factor')
                )
                if not vof_col:
                    sch_name = window_vent_sch_map.get(wname)
                    if sch_name: vof_col = _find(sch_name, 'Schedule Value')
                if not vof_col:
                    vof_col = _find(f'Vent_Sch_{actual_win_key}', 'Schedule Value')
                if not vof_col:
                    raise ValueError(f"Required 'Opening Factor' or 'Schedule Value' output not found for window '{wname}'.")

                opt_w_col  = _find(actual_win_key, 'Operative Temperature') or _find(actual_win_key, 'Zone Operative Temperature')
                if not opt_w_col: raise ValueError(f"Required 'Operative Temperature' output not found for zone '{actual_win_key}'.")
                
                cool_w_col = _find(actual_win_key, 'Cooling Coil Total Cooling Rate') or _find(actual_win_key, 'Cooling Rate')
                if not cool_w_col: raise ValueError(f"Required 'Cooling Rate' output not found for zone '{actual_win_key}'.")
                
                heat_w_col = _find(actual_win_key, 'Heating Coil Heating Rate') or _find(actual_win_key, 'Heating Rate')
                if not heat_w_col: raise ValueError(f"Required 'Heating Rate' output not found for zone '{actual_win_key}'.")
                
                occ_col    = _find(actual_win_key, 'People Occupant Count') or _find(wname, 'People Occupant Count')
                if not occ_col:
                    for cz in comfort_zones:
                        occ_col = _find('EMS', f'People Occupant Count_{cz}')
                        if occ_col: break
                if not occ_col: raise ValueError(f"Required 'People Occupant Count' output not found for zone '{actual_win_key}'.")

                acst_ref = None
                for cz in comfort_zones:
                    cz_col = _find(f'ACST_Sch_{cz}', 'Schedule Value')
                    if cz_col:
                        acst_ref = chosen_df[cz_col].astype(float) - acst_tol
                        break
                if acst_ref is None: raise ValueError("Required 'ACST_Sch' column not found for computing window checks.")

                vof   = chosen_df[vof_col].astype(float)
                opt_w = chosen_df[opt_w_col].astype(float)
                cool  = chosen_df[cool_w_col].astype(float)
                heat  = chosen_df[heat_w_col].astype(float)
                occ   = chosen_df[occ_col].astype(float)

                # Identify 1-timestep delay where HVAC just turned on
                hvac_now = (cool.values > 0) | (heat.values > 0)
                hvac_prev = pd.Series(hvac_now).shift(1, fill_value=False).values
                just_turned_on = hvac_now & ~hvac_prev
                
                # Identify 1-timestep delay where Window closes in the NEXT timestep.
                # This pardons transient limits (e.g. OpT falling below VST, Wind crossing MaxWindSpeed)
                # because the EMS takes 1 timestep to fully actuate the window closure.
                open_mask = (vof > 0.0).values
                open_next = pd.Series(open_mask).shift(-1, fill_value=False).values
                close_transit = open_mask & ~open_next

                # Examine timesteps where window is open AND we are not in the transit delays
                valid_open_mask = open_mask & ~just_turned_on & ~close_transit
                
                # For Hourly frequencies, averaging causes false positives when the 
                # state toggles mid-hour (e.g. window opened or HVAC activated for just 10 mins).
                # We extend the pardon to include the opening transit hour too.
                if chosen_freq == 'Hourly':
                    open_prev = pd.Series(open_mask).shift(1, fill_value=False).values
                    open_transit = open_mask & ~open_prev
                    valid_open_mask = valid_open_mask & ~open_transit

                open_pos  = valid_open_mask.nonzero()[0]
                n_open    = len(open_pos)

                if n_open == 0:
                    msg = f"  Window '{wname}': never open."
                    print(msg); summary_lines.append(msg)
                    continue

                prev = len(violations_window)

                bad = open_pos[(cool.iloc[open_pos].values > 0) | (heat.iloc[open_pos].values > 0)]
                _add(bad, violations_window, wname, 'Check2_Cond1_HVACidle',
                     lambda p: f"Window open but HVAC already active (cool={cool.iat[p]:.1f} W, heat={heat.iat[p]:.1f} W)",
                     lambda p: f"cool={cool.iat[p]:.1f}, heat={heat.iat[p]:.1f}",
                     lambda p: "Cool==0 AND Heat==0")

                bad = open_pos[occ.iloc[open_pos].values <= 0]
                _add(bad, violations_window, wname, 'Check2_Cond2_Occupied',
                     lambda p: f"Window open but zone unoccupied (Occ={occ.iat[p]:.0f})",
                     lambda p: round(float(occ.iat[p]), 4),
                     lambda p: "> 0")

                bad = open_pos[opt_w.iloc[open_pos].values >= acst_ref.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond3_OpT_lt_ACST',
                     lambda p: f"Window open but OpT ({opt_w.iat[p]:.2f}°C) >= roundedACST ({acst_ref.iat[p]:.2f}°C)",
                     lambda p: round(float(opt_w.iat[p]), 4),
                     lambda p: f"< {acst_ref.iat[p]:.2f}°C")

                bad = open_pos[opt_w.iloc[open_pos].values <= vst_series.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond4_OpT_gt_VST',
                     lambda p: f"Window open but OpT ({opt_w.iat[p]:.2f}°C) <= VST ({vst_series.iat[p]:.2f}°C)",
                     lambda p: round(float(opt_w.iat[p]), 4),
                     lambda p: f"> {vst_series.iat[p]:.2f}°C")

                bad = open_pos[out_t.iloc[open_pos].values >= opt_w.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond5_OutT_lt_OpT',
                     lambda p: f"Window open but OutT ({out_t.iat[p]:.2f}°C) >= OpT ({opt_w.iat[p]:.2f}°C)",
                     lambda p: round(float(out_t.iat[p]), 4),
                     lambda p: f"< OpT ({opt_w.iat[p]:.2f}°C)")

                bad = open_pos[out_t.iloc[open_pos].values <= min_out_t_series.iloc[open_pos].values]
                _add(bad, violations_window, wname, 'Check2_Cond6_MinOutTemp',
                     lambda p: f"Window open but OutT ({out_t.iat[p]:.2f}°C) <= MinOutTemp ({min_out_t_series.iat[p]:.2f}°C)",
                     lambda p: round(float(out_t.iat[p]), 4),
                     lambda p: f"> {min_out_t_series.iat[p]:.2f}°C")

                bad = open_pos[wind.iloc[open_pos].values > MaxWindSpeed]
                _add(bad, violations_window, wname, 'Check2_Cond7_MaxWindSpeed',
                     lambda p: f"Window open but WindSpeed ({wind.iat[p]:.2f} m/s) > MaxWindSpeed ({MaxWindSpeed} m/s)",
                     lambda p: round(float(wind.iat[p]), 4),
                     lambda p: f"<= {MaxWindSpeed} m/s")

                n_new = len(violations_window) - prev
                msg = f"  Window '{wname}': 7-condition violations = {n_new} (out of {n_open} open steps)."
                print(msg); summary_lines.append(msg)

        # ─────────────────────────────────────────────────────────────────────────
        # 4. STORE RESULTS
        # ─────────────────────────────────────────────────────────────────────────
        df_setpoint = pd.DataFrame(violations_setpoint)
        df_window = pd.DataFrame(violations_window)
        
        self.violations["setpoint"] = df_setpoint
        self.violations["window"] = df_window
        self.summary = "\n".join(summary_lines)

        n_s = len(df_setpoint)
        n_w = len(df_window)
        
        if n_s > 0:
            self.summary_table_setpoint = df_setpoint.groupby(['zone_or_window', 'check']).size().rename('count').reset_index()
        else:
            self.summary_table_setpoint = pd.DataFrame(columns=['zone_or_window', 'check', 'count'])
            
        if n_w > 0:
            self.summary_table_window = df_window.groupby(['zone_or_window', 'check']).size().rename('count').reset_index()
        else:
            self.summary_table_window = pd.DataFrame(columns=['zone_or_window', 'check', 'count'])

        n_s = len(self.violations['setpoint'])
        n_w = len(self.violations['window'])
        if n_s == 0 and n_w == 0:
            msg = "\n[PASS] All checks passed — no violations detected."
            print(msg); self.summary += msg
        else:
            msg = f"\n[FAIL] {n_s} setpoint violation(s), {n_w} window violation(s)."
            print(msg); self.summary += msg

