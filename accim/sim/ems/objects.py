# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""EMS variables, sensors, actuators and output variables of ACCIS."""

from accim.sim.ems.programs import add_program, zone_variables
from accim.sim.hvac.schedules import DESIGN_DAY_SCHEDULE, add_design_day_schedule
from accim.sim.model import AccimModel

__all__ = [
    'ZONE_OUTPUT_VARIABLES',
    'ZONE_SETPOINT_OUTPUT_VARIABLES',
    'add_actuators',
    'add_building_averages',
    'add_design_day_sensor',
    'add_global_variables',
    'add_internal_variables',
    'add_output_variables',
    'add_sensor',
    'add_sensors',
]

#: EMS output variables of the whole model: name -> (EMS variable, units). Averaged at each zone timestep.
_AVERAGED_OUTPUT_VARIABLES = {
    'Comfort Temperature': ('ComfTemp', 'C'),
    'Adaptive Cooling Setpoint Temperature': ('roundedACST', 'C'),
    'Adaptive Heating Setpoint Temperature': ('roundedAHST', 'C'),
    'Adaptive Cooling Setpoint Temperature_No Tolerance': ('ACSTnoTol', 'C'),
    'Adaptive Heating Setpoint Temperature_No Tolerance': ('AHSTnoTol', 'C'),
    'z_test_ComfStand': ('ComfStand', 'NA'),
    'z_test_ACSTaul': ('ACSTaul', 'C'),
    'z_test_ACSTall': ('ACSTall', 'C'),
    'z_test_AHSTaul': ('AHSTaul', 'C'),
    'z_test_AHSTall': ('AHSTall', 'C'),
    'z_test_CAT': ('CAT', 'C'),
    'z_test_ACSToffset': ('ACSToffset', 'C'),
    'z_test_AHSToffset': ('AHSToffset', 'C'),
    'z_test_ComfMod': ('ComfMod', 'NA'),
    'z_test_ACSTtol': ('ACSTtol', 'C'),
    'z_test_SetpointAcc': ('SetpointAcc', 'NA'),
    'z_test_CustAST_m': ('m', 'NA'),
    'z_test_CustAST_n': ('n', 'NA'),
    'z_test_AHSTtol': ('AHSTtol', 'C'),
}
_AVERAGED_OUTPUT_VARIABLES_MIXED_MODE = {
    'Ventilation Setpoint Temperature': ('VST', 'C'),
    'Minimum Outdoor Temperature for ventilation': ('MinOutTemp', 'C'),
    'Minimum Outdoor Temperature Difference for ventilation': ('MinTempDiffVOF', 'C'),
    'Maximum Outdoor Temperature Difference for ventilation': ('MaxTempDiffVOF', 'C'),
    'Multiplier for Ventilation Opening Factor': ('MultiplierVOF', ''),
}
#: EMS output variables of each zone: name prefix -> (EMS variable prefix, units, type of data).
ZONE_OUTPUT_VARIABLES = {
    'Comfortable Hours_No Applicability': ('ComfHoursNoApp', 'H', 'Summed'),
    'Comfortable Hours_Applicability': ('ComfHours', 'H', 'Summed'),
    'Occupied Comfortable Hours_No Applicability': ('OccComfHoursNoApp', 'H', 'Summed'),
    'Occupied Discomfortable Hours_No Applicability': ('OccDiscomfHoursNoApp', 'H', 'Summed'),
    'Occupied Hours': ('OccHours', 'H', 'Summed'),
    'Discomfortable Applicable Hot Hours': ('DiscomfAppHotHours', 'H', 'Summed'),
    'Discomfortable Applicable Cold Hours': ('DiscomfAppColdHours', 'H', 'Summed'),
    'Discomfortable Non Applicable Hot Hours': ('DiscomfNonAppHotHours', 'H', 'Summed'),
    'Discomfortable Non Applicable Cold Hours': ('DiscomfNonAppColdHours', 'H', 'Summed'),
    'Zone Floor Area': ('ZoneFloorArea', 'm2', 'Averaged'),
    'Zone Air Volume': ('ZoneAirVolume', 'm3', 'Averaged'),
    'People Occupant Count': ('Occ_count', '', 'Summed'),
}
#: The setpoints of each zone, which can have its own arguments: name prefix -> (EMS variable prefix, units). The
#: outputs of the whole model with the same names (without '_<zone>') have the values of the last zone, the same as
#: those of every zone if all the zones have the same arguments.
ZONE_SETPOINT_OUTPUT_VARIABLES = {
    'Comfort Temperature': ('ComfTemp', 'C'),
    'Adaptive Cooling Setpoint Temperature': ('roundedACST', 'C'),
    'Adaptive Heating Setpoint Temperature': ('roundedAHST', 'C'),
    'Adaptive Cooling Setpoint Temperature_No Tolerance': ('ACSTnoTol', 'C'),
    'Adaptive Heating Setpoint Temperature_No Tolerance': ('AHSTnoTol', 'C'),
}
_ZONE_SETPOINT_OUTPUT_VARIABLES_MIXED_MODE = {
    'Ventilation Setpoint Temperature': ('VST', 'C'),
    'Minimum Outdoor Temperature for ventilation': ('MinOutTemp', 'C'),
}
_GLOBAL_VARIABLES = (
    'ACST', 'AHST', 'ACSTnoTol', 'AHSTnoTol', 'ComfStand', 'ACSTaul', 'ACSTall', 'AHSTaul', 'AHSTall', 'CAT',
    'ACSToffset', 'AHSToffset', 'ComfMod', 'ComfTemp', 'ACSTtol', 'AHSTtol', 'SetpointAcc', 'roundedACST',
    'roundedAHST', 'CoolSeasonStart', 'CoolSeasonEnd', 'm', 'n',
    # Set by SetAST_Master and read by the subprograms it runs
    'CoolingSeason',
    # Inputs of each zone (SetInputData_<zone>) read by ApplyCAT and SetAppLimits
    'CATcoolOffset', 'CATheatOffset', 'CustAST_ACSToffset', 'CustAST_AHSToffset', 'CustAST_ACSTaul', 'CustAST_ACSTall',
    'CustAST_AHSTaul', 'CustAST_AHSTall',
)
_ZONE_GLOBAL_VARIABLES = (
    'ComfHours', 'DiscomfAppHotHours', 'DiscomfAppColdHours', 'DiscomfNonAppHotHours', 'DiscomfNonAppColdHours',
    'ComfHoursNoApp', 'ZoneFloorArea', 'ZoneAirVolume', 'OccHours', 'OccComfHoursNoApp', 'OccDiscomfHoursNoApp',
) + zone_variables(mixed_mode=False)
_GLOBAL_VARIABLES_MIXED_MODE = (
    'VST', 'VSToffset', 'MaxWindSpeed', 'VentCtrl', 'HVACmode', 'MinOutTemp', 'MinOToffset', 'MaxTempDiffVOF',
    'MinTempDiffVOF', 'MultiplierVOF',
)
#: Variables of each zone in mixed mode only
_ZONE_GLOBAL_VARIABLES_MIXED_MODE = ('VentHours',) + zone_variables(mixed_mode=True)[len(zone_variables(False)):]
#: Variables of each zone whose building averages add_building_averages adds
_HOURS_TO_AVERAGE = ('ComfHours', 'DiscomfAppHotHours', 'DiscomfAppColdHours', 'DiscomfNonAppHotHours',
                     'DiscomfNonAppColdHours', 'ComfHoursNoApp', 'OccHours', 'OccComfHoursNoApp',
                     'OccDiscomfHoursNoApp', 'VentHours')
#: Outputs whose building averages add_building_averages adds:
#: output -> (sensor suffix, short name, units, type of data)
_OUTPUTS_TO_AVERAGE = {
    'Zone Operative Temperature': ('OpT', 'OpTemp', 'C', 'Averaged'),
    'AFN Zone Ventilation Air Change Rate': ('VentACR', 'VentACR', 'ach', 'Averaged'),
    'AFN Zone Infiltration Air Change Rate': ('InfACR', 'InfACR', 'ach', 'Averaged'),
}


def _add_output_variable(model: AccimModel, name: str, variable: str, data_type: str, units: str) -> None:
    """Add an EMS output variable unless the model has one with that name."""
    if model.idf.getobject('EnergyManagementSystem:OutputVariable', name) is not None:
        model.log(f'Not added - {name} Output Variable')
        return
    model.idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=variable,
                           Type_of_Data_in_Variable=data_type, Update_Frequency='ZoneTimestep',
                           EMS_Program_or_Subroutine_Name='', Units=units)
    model.log(f'Added - {name} Output Variable')


def add_output_variables(model: AccimModel) -> None:
    """Add the EMS output variables of ACCIS that the model does not have yet."""
    averaged = dict(_AVERAGED_OUTPUT_VARIABLES)
    if model.is_mixed_mode:
        averaged.update(_AVERAGED_OUTPUT_VARIABLES_MIXED_MODE)
    for name, (variable, units) in averaged.items():
        _add_output_variable(model, name, variable, 'Averaged', units)
    for name, (variable, units, data_type) in ZONE_OUTPUT_VARIABLES.items():
        for zone in model.ems_names:
            _add_output_variable(model, f'{name}_{zone}', f'{variable}_{zone}', data_type, units)
    if model.is_mixed_mode:
        for zone in model.ems_names:
            _add_output_variable(model, f'Ventilation Hours_{zone}', f'VentHours_{zone}', 'Summed', 'H')
    setpoints = dict(ZONE_SETPOINT_OUTPUT_VARIABLES)
    if model.is_mixed_mode:
        setpoints.update(_ZONE_SETPOINT_OUTPUT_VARIABLES_MIXED_MODE)
    for name, (variable, units) in setpoints.items():
        for zone in model.ems_names:
            _add_output_variable(model, f'{name}_{zone}', f'{variable}_{zone}', 'Averaged', units)


def _declared_global_variables(idf) -> set:
    """The names (in capitals) of the EMS global variables that the model declares."""
    return {str(name).strip().upper() for obj in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
            for name in obj.fieldvalues[1:] if str(name).strip()}


def _new_global_variables(model: AccimModel, names, declared: set) -> None:
    """Declare the EMS global variables that are not declared yet, in one object."""
    names = [name for name in names if name.upper() not in declared]
    if not names:
        return
    declared.update(name.upper() for name in names)
    fields = {f'Erl_Variable_{n}_Name': name for n, name in enumerate(names, start=1)}
    model.idf.newidfobject('EnergyManagementSystem:GlobalVariable', **fields)


def add_global_variables(model: AccimModel) -> None:
    """Add the EMS global variables of ACCIS that the model does not declare yet.

    Those of the model stay, since its own EMS programs (or EMS output variables) may use them."""
    declared = _declared_global_variables(model.idf)
    _new_global_variables(model, _GLOBAL_VARIABLES, declared)
    for zone in model.ems_names:
        _new_global_variables(model, [f'{name}_{zone}' for name in _ZONE_GLOBAL_VARIABLES], declared)
    if model.is_mixed_mode:
        _new_global_variables(model, _GLOBAL_VARIABLES_MIXED_MODE, declared)
        for zone in model.ems_names:
            _new_global_variables(model, [f'{name}_{zone}' for name in _ZONE_GLOBAL_VARIABLES_MIXED_MODE], declared)
        for window in model.windows:
            _new_global_variables(model, [f'{window}_MyVOF'], declared)
    model.log('Global variables objects have been added')


def add_internal_variables(model: AccimModel) -> None:
    """Add the EMS internal variables of the floor area and volume of each zone (ZFA_<zone>, ZAV_<zone>) that the
    model does not have yet.

    Those of the model stay, since its own EMS programs may use them."""
    for name, zone in zip(model.ems_names, model.ems_zones):
        for prefix, data_type in (('ZFA_', 'Zone Floor Area'), ('ZAV_', 'Zone Air Volume')):
            if model.idf.getobject('EnergyManagementSystem:InternalVariable', prefix + name) is not None:
                model.log(f'Not added - {prefix + name} Internal Variable')
                continue
            model.idf.newidfobject('EnergyManagementSystem:InternalVariable', Name=prefix + name,
                                   Internal_Data_Index_Key_Name=zone, Internal_Data_Type=data_type)
    model.log('Internal variables objects have been added')


def add_sensor(model: AccimModel, name: str, key: str, variable: str) -> None:
    """Add an EMS sensor of an output variable unless the model has one with that name."""
    if model.idf.getobject('EnergyManagementSystem:Sensor', name) is not None:
        model.log(f'Not added - {name} Sensor')
        return
    model.idf.newidfobject('EnergyManagementSystem:Sensor', Name=name,
                           OutputVariable_or_OutputMeter_Index_Key_Name=key,
                           OutputVariable_or_OutputMeter_Name=variable)
    model.log(f'Added - {name} Sensor')


def add_sensors(model: AccimModel) -> None:
    """Add the EMS sensors of ACCIS that the model does not have yet."""
    # The running mean outdoor temperatures of the comfort models of the occupants of the first target
    key = model.ems_keys[0]
    add_sensor(model, 'RMOT', key,
               'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature')
    add_sensor(model, 'PMOT', key,
               'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature')
    for name, occupancy_key, variable in zip(model.ems_names, model.occupancy_keys, model.occupancy_variables):
        add_sensor(model, f'Occ_count_{name}', occupancy_key, variable)
    for name, zone in zip(model.ems_names, model.ems_zones):
        add_sensor(model, f'{name}_OpT', zone, 'Zone Operative Temperature')
        if model.is_mixed_mode:
            add_sensor(model, f'{name}_WindSpeed', zone, 'Zone Outdoor Air Wind Speed')
            add_sensor(model, f'{name}_OutT', zone, 'Zone Outdoor Air Drybulb Temperature')
    if model.is_mixed_mode:
        for window, zone in zip(model.windows, model.window_zones):
            add_sensor(model, f'{window}_OpT', zone, 'Zone Operative Temperature')
            add_sensor(model, f'{window}_WindSpeed', zone, 'Zone Outdoor Air Wind Speed')
            add_sensor(model, f'{window}_OutT', zone, 'Zone Outdoor Air Drybulb Temperature')
            # The occupancy of the target of the zone of the window
            occupancy_key, variable = f'People {zone}', 'People Occupant Count'
            for target_zone, target_key, target_variable in zip(model.ems_zones, model.occupancy_keys,
                                                                 model.occupancy_variables):
                if target_zone.lower() == zone.lower():
                    occupancy_key, variable = target_key, target_variable
                    break
            add_sensor(model, f'{window}_Occ_count', occupancy_key, variable)
    add_sensor(model, 'OutT', 'Environment', 'Site Outdoor Air Drybulb Temperature')


def add_design_day_sensor(model: AccimModel) -> None:
    """Add the EMS sensor DesignDay, the value of the schedule of the design days (1 on the days of the types
    SummerDesignDay and WinterDesignDay, see :data:`accim.sim.hvac.schedules.DESIGN_DAY_SCHEDULE`), which the programs
    ApplyAST_<zone> and SetWindowOperation_<window> of mixed mode read (ScriptTypes 'vrf_mm' and 'ex_mm'): on the
    design days, the zones are air-conditioned with the windows closed, so that EnergyPlus sizes the HVAC systems for
    the setpoints, also on the design days without occupants."""
    add_design_day_schedule(model)
    add_sensor(model, 'DesignDay', DESIGN_DAY_SCHEDULE, 'Schedule Value')


def _add_actuator(model: AccimModel, name: str, component: str, component_type: str, control_type: str) -> None:
    """Add an EMS actuator unless the model has one with that name."""
    if model.idf.getobject('EnergyManagementSystem:Actuator', name) is not None:
        model.log(f'Not added - {name} Actuator')
        return
    model.idf.newidfobject('EnergyManagementSystem:Actuator', Name=name, Actuated_Component_Unique_Name=component,
                           Actuated_Component_Type=component_type, Actuated_Component_Control_Type=control_type)
    model.log(f'Added - {name} Actuator')


def add_actuators(model: AccimModel) -> None:
    """Add the EMS actuators of the setpoint schedules of each zone and, in mixed mode, of the windows."""
    for name in model.ems_names:
        for setpoint in ('AHST', 'ACST'):
            _add_actuator(model, f'{setpoint}_Act_{name}', f'{setpoint}_Sch_{name}', 'Schedule:Compact',
                          'Schedule Value')
    if model.is_mixed_mode:
        for window, window_orig in zip(model.windows, model.windows_orig):
            if model.natural_ventilation_type == 'Scheduled':
                _add_actuator(model, f'{window}_VentOpenFact', model.scheduled_ventilation[window_orig],
                              'Schedule:Constant', 'Schedule Value')
            else:
                _add_actuator(model, f'{window}_VentOpenFact', window_orig, 'AirFlow Network Window/Door Opening',
                              'Venting Opening Factor')


def _add_average(model: AccimModel, global_variables, key: str, terms, output_name: str, data_type: str,
                 units: str) -> None:
    idf = model.idf
    variable = f'{key}BuildAvg'
    if variable in global_variables:
        model.log(f'Not added - Make{variable} GlobalVariable')
    else:
        idf.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=variable)
        model.log(f'Added - {variable} GlobalVariable')
    program = f'Make{variable}'
    if idf.getobject('EnergyManagementSystem:ProgramCallingManager', program) is not None:
        model.log(f'Not added - {program} ProgramCallingManager')
    else:
        idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=program,
                         EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor', Program_Name_1=program)
        model.log(f'Added - {program} ProgramCallingManager')
    if idf.getobject('EnergyManagementSystem:Program', program) is not None:
        model.log(f'Not added - {program} Program')
    else:
        add_program(idf, program, [f'set {variable}Num = ' + '+'.join(terms), f'set {variable}Den = {len(terms)}',
                                   f'set {variable} = {variable}Num/{variable}Den'])
        model.log(f'Added - {program} Program')
    if output_name is None:
        return
    if idf.getobject('EnergyManagementSystem:OutputVariable', output_name) is not None:
        model.log(f'Not added - {output_name} EMS OutputVariable')
    else:
        idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=output_name, EMS_Variable_Name=variable,
                         Type_of_Data_in_Variable=data_type, Update_Frequency='ZoneTimestep', Units=units)
        model.log(f'Added - {output_name} EMS OutputVariable')


def add_building_averages(model: AccimModel) -> None:
    """Add the building averages of the hours of each zone and of some outputs (argument add_building_averages)."""
    idf = model.idf
    names = [name for obj in idf.idfobjects['EnergyManagementSystem:GlobalVariable'] for name in obj.fieldvalues[1:]]
    for key in _HOURS_TO_AVERAGE:
        terms = [name for name in names if name.split('_')[0].lower() == key.lower()]
        if not terms:
            # No zone has the variable (the ventilation hours of full air-conditioning)
            continue
        outputs = [o for o, (variable, _, _) in ZONE_OUTPUT_VARIABLES.items() if variable.lower() == key.lower()]
        _add_average(model, names, key, terms, None, '', '')
        for output in outputs:
            _add_average_output(model, output, key)
    for output, (suffix, key, units, data_type) in _OUTPUTS_TO_AVERAGE.items():
        if output.startswith('AFN') and not idf.idfobjects['AirflowNetwork:SimulationControl']:
            # EnergyPlus stops if a sensor reads an output variable that the model does not have
            model.log(f'Not added - building average of {output} (the model has no AirflowNetwork)')
            continue
        # One sensor per zone: that of the zone if the model has it (the names of EMS objects are
        # case-insensitive), or a new one
        sensors = list(idf.idfobjects['EnergyManagementSystem:Sensor'])
        all_names = {s.Name.upper() for s in sensors}
        zone_sensors = {}
        for sensor in sensors:
            if sensor.OutputVariable_or_OutputMeter_Name.lower() == output.lower():
                zone_sensors.setdefault(sensor.OutputVariable_or_OutputMeter_Index_Key_Name.upper(), sensor.Name)
        terms = []
        for zone, zone_orig in zip(model.zones, model.zones_orig):
            sensor = zone_sensors.get(zone_orig.upper())
            if sensor is not None:
                model.log(f'Not added - {sensor} Sensor')
            else:
                sensor = f'{zone}_{suffix}'
                if sensor.upper() in all_names:
                    raise ValueError(f'The EMS sensor {sensor} of the building average of {output} has the name of '
                                     f'another EMS sensor of the model.')
                idf.newidfobject('EnergyManagementSystem:Sensor', Name=sensor,
                                 OutputVariable_or_OutputMeter_Index_Key_Name=zone_orig,
                                 OutputVariable_or_OutputMeter_Name=output)
                all_names.add(sensor.upper())
                model.log(f'Added - {sensor} Sensor')
            terms.append(sensor)
        _add_average(model, names, key, terms, f'{output}_Building_Average', data_type, units)


def _add_average_output(model: AccimModel, output: str, key: str) -> None:
    name = f'{output}_Building_Average'
    if model.idf.getobject('EnergyManagementSystem:OutputVariable', name) is not None:
        model.log(f'Not added - {name} EMS OutputVariable')
        return
    model.idf.newidfobject('EnergyManagementSystem:OutputVariable', Name=name, EMS_Variable_Name=f'{key}BuildAvg',
                           Type_of_Data_in_Variable='Summed', Update_Frequency='ZoneTimestep', Units='H')
    model.log(f'Added - {name} EMS OutputVariable')
