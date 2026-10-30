# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Outputs of the models (Output:Variable and Output:Meter objects) and output control objects."""

import warnings
from typing import Iterable, Optional

import pandas as pd

from accim.sim.idf_tools import remove_objects
from accim.sim.model import AccimModel

__all__ = [
    'OUTPUT_DATAFRAME_COLUMNS',
    'add_detailed_outputs',
    'add_ems_debug_output',
    'add_output_control_files',
    'add_simplified_outputs',
    'add_standard_outputs',
    'add_variable_dictionary',
    'enable_sizing_calculations',
    'output_variables_dataframe',
    'remove_duplicated_outputs',
    'remove_existing_outputs',
    'select_custom_outputs',
    'take_output_dataframe',
]

OUTPUT_DATAFRAME_COLUMNS = ['key_value', 'variable_name', 'reporting_frequency', 'schedule_name']

_STANDARD_OUTPUTS = (
    'Zone Thermostat Operative Temperature',
    'Zone Thermostat Air Temperature',
    'Zone Operative Temperature',
    'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
    'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',
    'Cooling Coil Total Cooling Rate',
    'Heating Coil Heating Rate',
    'Facility Total HVAC Electric Demand Power',
    'Facility Total HVAC Electricity Demand Rate',
    'AFN Surface Venting Window or Door Opening Factor',
    'AFN Zone Infiltration Air Change Rate',
    'AFN Zone Infiltration Volume',
    'AFN Zone Ventilation Air Change Rate',
    'AFN Zone Ventilation Volume',
    'Zone Ventilation Standard Density Air Change Rate',
)
_PMV_OUTPUTS = ('Zone Thermal Comfort Fanger Model PMV', 'Zone Thermal Comfort Fanger Model PPD')
_SIMPLIFIED_OUTPUTS = ('Zone Operative Temperature', 'Cooling Coil Total Cooling Rate', 'Heating Coil Heating Rate')
_DETAILED_OUTPUTS = ('AFN Surface Venting Window or Door Opening Factor',
                     'Zone Ventilation Standard Density Air Change Rate')
_SITE_OUTPUTS = ('Site Outdoor Air Drybulb Temperature', 'Site Wind Speed', 'Site Outdoor Air Relative Humidity')
_VRF_OUTPUTS = ('VRF Heat Pump Cooling Electricity Energy', 'VRF Heat Pump Heating Electricity Energy')
_METERS = ('EnergyTransfer:HVAC', 'Electricity:HVAC', 'DistrictHeating:Facility', 'DistrictCooling:Facility',
           'Heating:EnergyTransfer', 'Cooling:EnergyTransfer', 'Heating:Electricity', 'Cooling:Electricity')


def _new_output(model: AccimModel, key: str, variable: str, frequency: str) -> None:
    model.idf.newidfobject('Output:Variable', Key_Value=key, Variable_Name=variable,
                           Reporting_Frequency=frequency, Schedule_Name='')
    model.log(f'Added - {key} {variable} Reporting Frequency {frequency} Output:Variable data')


def _variables_of_frequency(model: AccimModel, frequency: str) -> list:
    return [o.Variable_Name for o in model.idf.idfobjects['Output:Variable'] if o.Reporting_Frequency == frequency]


def _add_scheduled_ventilation_outputs(model: AccimModel, frequency: str) -> None:
    """The values of the schedules that open the ventilation objects of the zones (scheduled natural ventilation)."""
    if model.natural_ventilation_type != 'Scheduled':
        return
    for schedule in model.scheduled_ventilation.values():
        exists = any(o.Variable_Name == 'Schedule Value' and o.Key_Value == schedule
                     for o in model.idf.idfobjects['Output:Variable'] if o.Reporting_Frequency == frequency)
        if not exists:
            _new_output(model, schedule, 'Schedule Value', frequency)


def remove_existing_outputs(model: AccimModel) -> None:
    """Remove the Output:Variable, Output:Meter and Output:EnvironmentalImpactFactors objects."""
    for object_type in ('Output:EnvironmentalImpactFactors', 'Output:Meter', 'Output:Variable'):
        remove_objects(model.idf, object_type)


def add_simplified_outputs(model: AccimModel, frequencies: Iterable[str]) -> None:
    """Add the operative temperature and the coil rates (and PMV and PPD with 'pmv' control)."""
    outputs = _SIMPLIFIED_OUTPUTS + (_PMV_OUTPUTS if model.temp_ctrl == 'pmv' else ())
    for frequency in frequencies:
        for variable in outputs:
            _new_output(model, '*', variable, frequency.capitalize())


def add_standard_outputs(model: AccimModel, frequencies: Iterable[str]) -> None:
    """Add the EMS output variables of ACCIS and the main outputs of the zones, HVAC systems, site and meters."""
    idf = model.idf
    ems_outputs = [v.Name for v in idf.idfobjects['EnergyManagementSystem:OutputVariable']]
    outputs = _STANDARD_OUTPUTS + (_PMV_OUTPUTS if model.temp_ctrl == 'pmv' else ())
    for frequency in frequencies:
        frequency = frequency.capitalize()
        existing = _variables_of_frequency(model, frequency)
        for variable in ems_outputs:
            if variable in existing or variable.startswith('WIP') \
                    or variable.startswith('Adaptive Thermal Comfort Cost Index'):
                continue
            _new_output(model, '*', variable, frequency)
        for variable in outputs:
            if variable not in existing:
                _new_output(model, '*', variable, frequency)
        for output in [o for o in idf.idfobjects['Output:Variable'] if o.Reporting_Frequency == frequency]:
            if any(variable in output.Variable_Name for variable in outputs):
                output.Schedule_Name = ''
        for variable in _SITE_OUTPUTS:
            if variable not in existing:
                _new_output(model, 'Environment', variable, frequency)
        for zone in model.ems_names:
            _new_output(model, f'AHST_Sch_{zone}', 'Schedule Value', frequency)
            _new_output(model, f'ACST_Sch_{zone}', 'Schedule Value', frequency)
        _add_scheduled_ventilation_outputs(model, frequency)
        if model.script_type.startswith('vrf'):
            for variable in _VRF_OUTPUTS:
                _new_output(model, '*', variable, frequency)
            for zone in model.zones:
                _new_output(model, f'{zone} VRF Indoor Unit DX Cooling Coil', 'Cooling Coil Total Cooling Rate',
                            frequency)
                _new_output(model, f'{zone} VRF Indoor Unit DX Heating Coil', 'Heating Coil Heating Rate', frequency)
    for frequency in frequencies:
        meters = [m.Key_Name for m in idf.idfobjects['Output:Meter'] if m.Reporting_Frequency.upper() == frequency.upper()]
        for meter in _METERS:
            if meter in meters:
                warnings.warn(f"Output:Meter '{meter}' ({frequency}) already exists. Skipping.")
                continue
            idf.newidfobject('Output:Meter', Key_Name=meter, Reporting_Frequency=frequency.capitalize())
            model.log(f'Added Output:Meter for {meter} ({frequency})')


def add_detailed_outputs(model: AccimModel, frequencies: Iterable[str]) -> None:
    """Add the opening factors of the windows and the ventilation air changes (after the standard outputs)."""
    for frequency in frequencies:
        frequency = frequency.capitalize()
        existing = _variables_of_frequency(model, frequency)
        for variable in _DETAILED_OUTPUTS:
            if variable not in existing:
                _new_output(model, '*', variable, frequency)
        _add_scheduled_ventilation_outputs(model, frequency)


def select_custom_outputs(model: AccimModel, input_function=None) -> None:
    """Ask which outputs to remove or keep, for each reporting frequency (output type 'custom').

    :param input_function: The function that asks each question and returns the answer (by default, ``input``).
    """
    input_function = input_function or input
    to_delete = []
    for frequency in ['Timestep', 'Hourly', 'Daily', 'Monthly', 'Runperiod']:
        outputs = [o for o in model.idf.idfobjects['Output:Variable'] if o.Reporting_Frequency == frequency]
        if not outputs:
            continue
        print(f'\nThe current existing outputs for {frequency} Frequency are:')
        print(*dict.fromkeys(o.Variable_Name for o in outputs), sep='\n')
        remove_or_keep = input_function(
            'Do you want to remove some input or keep it and remove all others? Please enter remove or keep:')
        names = input_function('Please enter these outputs (which must be contained in the list above) '
                               'separated by semicolon (;): ').split(';')
        if remove_or_keep.lower() == 'remove':
            to_delete += [o for o in outputs if o.Variable_Name in names]
        elif remove_or_keep.lower() == 'keep':
            to_delete += [o for o in outputs if o.Variable_Name not in names]
    for output in to_delete:
        model.idf.removeidfobject(output)


def remove_duplicated_outputs(model: AccimModel) -> None:
    """Remove the Output:Variable objects that repeat an earlier one (same key, variable, frequency and schedule)."""
    seen = set()
    for output in list(model.idf.idfobjects['Output:Variable']):
        identity = tuple(str(value).lower() for value in (output.Key_Value, output.Variable_Name,
                                                          output.Reporting_Frequency, output.Schedule_Name))
        if identity in seen:
            model.idf.removeidfobject(output)
        else:
            seen.add(identity)


def output_variables_dataframe(idf, file: Optional[str] = None) -> pd.DataFrame:
    """A DataFrame with the Output:Variable objects of a model (and the name of its file, if given)."""
    rows = [{'key_value': o.Key_Value, 'variable_name': o.Variable_Name,
             'reporting_frequency': o.Reporting_Frequency, 'schedule_name': o.Schedule_Name}
            for o in idf.idfobjects['Output:Variable']]
    df = pd.DataFrame(rows, columns=OUTPUT_DATAFRAME_COLUMNS, dtype=object)
    if file is not None:
        df.insert(0, 'file', file)
    return df


def take_output_dataframe(model: AccimModel, df_outputs: pd.DataFrame, file: Optional[str] = None) -> None:
    """Replace the Output:Variable objects with the rows of a DataFrame like the one of
    :func:`output_variables_dataframe` (only the rows of the file, if given)."""
    if 'reporting_frequency' not in df_outputs.columns and 'frequency' in df_outputs.columns:
        df_outputs = df_outputs.rename(columns={'frequency': 'reporting_frequency'})
    if file is not None:
        df_outputs = df_outputs[df_outputs['file'].str.contains(file, regex=False)]
    remove_objects(model.idf, 'Output:Variable')
    for row in df_outputs.itertuples(index=False):
        model.idf.newidfobject('Output:Variable', Key_Value=row.key_value, Variable_Name=row.variable_name,
                               Reporting_Frequency=row.reporting_frequency.capitalize(),
                               Schedule_Name=row.schedule_name)
        model.log(f'Added - {row.key_value} {row.variable_name} Output:Variable data')


def add_output_control_files(model: AccimModel) -> None:
    """Make EnergyPlus write the CSV, MTR and ESO files."""
    controls = list(model.idf.idfobjects['OutputControl:Files'])
    if not controls:
        model.idf.newidfobject('OutputControl:Files', Output_CSV='Yes', Output_MTR='Yes', Output_ESO='Yes')
        model.log('Added - OutputControl:Files object')
        return
    controls[0].Output_CSV = 'Yes'
    controls[0].Output_MTR = 'Yes'
    controls[0].Output_ESO = 'Yes'
    model.log('Not added - OutputControl:Files object - Output CSV, MTR and ESO fields set to Yes')


def add_variable_dictionary(model: AccimModel) -> None:
    """Make EnergyPlus write the RDD file (the available outputs)."""
    if list(model.idf.idfobjects['Output:VariableDictionary']):
        model.log('Not added - Output:VariableDictionary object')
        return
    model.idf.newidfobject('Output:VariableDictionary', Key_Field='IDF', Sort_Option='Unsorted')
    model.log('Added - Output:VariableDictionary object')


def add_ems_debug_output(model: AccimModel) -> None:
    """Make EnergyPlus write the EDD file with the EMS actuators, internal variables and errors (argument debugging)."""
    if list(model.idf.idfobjects['Output:EnergyManagementSystem']):
        model.log('Not added - Output:EnergyManagementSystem object')
        return
    model.idf.newidfobject('Output:EnergyManagementSystem', Actuator_Availability_Dictionary_Reporting='Verbose',
                           Internal_Variable_Availability_Dictionary_Reporting='Verbose',
                           EMS_Runtime_Language_Debug_Output_Level='Verbose')
    model.log('Added - Output:EnergyManagementSystem object')


def enable_sizing_calculations(model: AccimModel) -> None:
    """Enable the zone, system and plant sizing calculations (the VRF systems are autosized)."""
    controls = list(model.idf.idfobjects['SimulationControl'])
    if not controls:
        model.idf.newidfobject('SimulationControl', Do_Zone_Sizing_Calculation='Yes',
                               Do_System_Sizing_Calculation='Yes', Do_Plant_Sizing_Calculation='Yes',
                               Run_Simulation_for_Sizing_Periods='Yes',
                               Run_Simulation_for_Weather_File_Run_Periods='Yes')
        model.log('Added - SimulationControl object with Sizing parameters enabled')
        return
    control = controls[0]
    control.Do_Zone_Sizing_Calculation = 'Yes'
    control.Do_System_Sizing_Calculation = 'Yes'
    control.Do_Plant_Sizing_Calculation = 'Yes'
    model.log('Modified - SimulationControl object: enabled Zone, System, and Plant Sizing Calculations')
