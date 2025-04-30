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

import os
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove, rename

import besos.IDF_class
from besos.IDF_class import IDF
import besos
from os import PathLike
from unidecode import unidecode


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

    obj_shadowcalc = [i for i in idf_object.idfobjects['ShadowCalculation']][0]
    shadowcalc_freq_prev = obj_shadowcalc.Shading_Calculation_Update_Frequency
    obj_shadowcalc.Shading_Calculation_Update_Frequency = shading_calculation_update_frequency
    print(f'Shading Calculation Update Frequency was previously set to '
          f'{shadowcalc_freq_prev} days, and it has been modified to {shading_calculation_update_frequency} days.')
    shadowcalc_maxfigs_prev = obj_shadowcalc.Maximum_Figures_in_Shadow_Overlap_Calculations
    obj_shadowcalc.Maximum_Figures_in_Shadow_Overlap_Calculations = maximum_figures_in_shadow_overlap_calculations
    print(f'Maximum Figures in Shadow Overlap Calculations was previously set to '
          f'{shadowcalc_maxfigs_prev} days, and it has been modified to {maximum_figures_in_shadow_overlap_calculations} days.')

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


import pandas as pd
import warnings
from besos import eppy_funcs as ef
from besos.eplus_funcs import get_idf_version, run_building


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