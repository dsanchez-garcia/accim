# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The arguments of the ACCIS of a model, read from its EMS programs."""

from typing import Any

__all__ = [
    'get_accim_args',
    'get_accim_args_flattened',
]

#: The IDF object of a model (eppy or besos)
IDF = Any


def get_accim_args(idf_object: IDF) -> dict:
    """
    Collects all the EnergyManagementSystem:Program Program lines used to
    set the values for the arguments of ACCIS, and saves them in a dictionary.

    The models of accim 1.0.0 have the arguments of each occupied zone in a program SetInputData_<zone>: the
    dictionary has one item for each of these programs, ``{program name: {EMS variable: value}}``. The models of
    earlier versions have the items 'SetInputData', 'SetVOFinputData' (mixed mode only), 'SetAST' and 'CustAST',
    and those with aPMV setpoints one item for each program set_zone_input_data_<target>.

    :param idf_object: the IDF instance
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
    from accim.sim.ems.inputs import input_programs
    zone_programs = input_programs(idf_object)
    if zone_programs:
        for program in zone_programs.values():
            programs.update({program.Name: program_to_dict(program.obj)})
        return programs
    try:
        for p in ['SetInputData', 'SetVOFinputData']:
            matches = [i for i in idf_object.idfobjects['EnergyManagementSystem:Program']
                       if i.Name.lower() == p.lower()]
            if p == 'SetVOFinputData' and not matches:
                # Only the models with natural ventilation (mixed mode) have SetVOFinputData
                continue
            data = matches[0].obj
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
    """The arguments of :func:`get_accim_args` in one dictionary (with several zones, the values of the last one)."""
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
