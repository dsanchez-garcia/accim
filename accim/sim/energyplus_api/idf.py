# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EMS objects of a model, and the model that the Python API of EnergyPlus runs without them.

The Python API backend runs the EMS programs in Python, so the model that EnergyPlus runs has no programs,
subroutines, program calling managers or actuators (EnergyPlus would set the actuators after each calling point,
overwriting the values of the API). The sensors, internal variables, global variables and output variables stay:
EnergyPlus resets the variables of the sensors at each new environment, as it does with the EMS, and reports the
global variables, which the controller updates.

The models are IDF objects of eppy (see :func:`accim.sim.accis.load_idf`).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from accim.sim.ems.erl import BUILT_IN_VARIABLES

__all__ = ['EmsDefinition', 'UNSUPPORTED_EMS_OBJECTS', 'prepare_for_api', 'read_ems']

#: EMS objects that the Python API backend does not support (with all the ExternalInterface objects)
UNSUPPORTED_EMS_OBJECTS = (
    'ENERGYMANAGEMENTSYSTEM:TRENDVARIABLE',
    'ENERGYMANAGEMENTSYSTEM:CURVEORTABLEINDEXVARIABLE',
    'ENERGYMANAGEMENTSYSTEM:CONSTRUCTIONINDEXVARIABLE',
    'EXTERNALINTERFACE',
    'PYTHONPLUGIN:INSTANCE',
)
#: EMS objects that the Python API backend runs in Python, which are removed from the model
_CONTROL_OBJECTS = (
    'EnergyManagementSystem:Program',
    'EnergyManagementSystem:Subroutine',
    'EnergyManagementSystem:ProgramCallingManager',
    'EnergyManagementSystem:Actuator',
)
#: The EMS output variables, which report an EMS variable (that of a program, if it has one)
_OUTPUT_VARIABLES = ('EnergyManagementSystem:OutputVariable', 'EnergyManagementSystem:MeteredOutputVariable')


@dataclass
class EmsDefinition:
    """The EMS objects of a model.

    :ivar sensors: (Erl name, output variable or meter key, output variable or meter name) of each sensor.
    :ivar actuators: (Erl name, component unique name, component type, control type) of each actuator.
    :ivar internal_variables: (Erl name, key, internal data type) of each internal variable.
    :ivar global_variables: The names of the global variables.
    :ivar programs: The lines of each program and subroutine, by name.
    :ivar calling_managers: (name, calling point, programs) of each program calling manager, in the order of the
        IDF, which is the order in which EnergyPlus runs them.
    :ivar reported_variables: (global variable of EnergyPlus, Erl variable, program or '') of each variable that
        EMS output variables report. The local variables of programs and the actuators (which are not in the IDF
        that the API runs) are reported through new global variables. An output variable that names a program
        reports the global variable of that name, if there is one, as in EnergyPlus.
    :ivar unsupported: The classes of the objects that the backend does not support.
    :ivar version: The EnergyPlus version of the model ('25.1').
    """

    sensors: List[Tuple[str, str, str]] = field(default_factory=list)
    actuators: List[Tuple[str, str, str, str]] = field(default_factory=list)
    internal_variables: List[Tuple[str, str, str]] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    programs: Dict[str, List[str]] = field(default_factory=dict)
    calling_managers: List[Tuple[str, str, List[str]]] = field(default_factory=list)
    reported_variables: List[Tuple[str, str, str]] = field(default_factory=list)
    unsupported: List[str] = field(default_factory=list)
    version: str = ''

    def global_names(self) -> Set[str]:
        """The names of the global Erl variables (in upper case): global variables, sensors, actuators, internal
        variables and built-in variables."""
        return (set(self.global_variables) | {s[0] for s in self.sensors} | {a[0] for a in self.actuators}
                | {i[0] for i in self.internal_variables} | set(BUILT_IN_VARIABLES))

    def reported_name(self, variable: str, program: str) -> Tuple[str, str]:
        """The global variable of EnergyPlus that reports an Erl variable, and its program ('' for the global ones).

        As ``FindEMSVariable`` of EnergyPlus, a variable named in the scope of a program is the global variable of
        that name, if there is one, and otherwise a local variable of the program, which is reported through a new
        global variable.
        """
        variable, program = variable.upper(), program.upper()
        if not program or variable in self.global_names():
            return variable, ''
        return f'ACCIMAPI_{program}_{variable}', program

    def added_global_variables(self) -> List[str]:
        """The global variables that the IDF of the API declares to report actuators and variables of programs."""
        actuators = {a[0] for a in self.actuators}
        return [name for name, variable, program in self.reported_variables if program or name in actuators]

    @property
    def has_programs(self) -> bool:
        return bool(self.calling_managers)


def read_ems(idf) -> EmsDefinition:
    """The EMS objects of a model (an IDF object of eppy), and its EnergyPlus version."""
    ems = EmsDefinition()
    for version in idf.idfobjects['Version']:
        ems.version = '.'.join(str(version.Version_Identifier).split('.')[:2])
    for sensor in idf.idfobjects['EnergyManagementSystem:Sensor']:
        ems.sensors.append((sensor.Name.upper(), sensor.OutputVariable_or_OutputMeter_Index_Key_Name,
                            sensor.OutputVariable_or_OutputMeter_Name))
    for actuator in idf.idfobjects['EnergyManagementSystem:Actuator']:
        ems.actuators.append((actuator.Name.upper(), actuator.Actuated_Component_Unique_Name,
                              actuator.Actuated_Component_Type, actuator.Actuated_Component_Control_Type))
    for variable in idf.idfobjects['EnergyManagementSystem:InternalVariable']:
        ems.internal_variables.append((variable.Name.upper(), variable.Internal_Data_Index_Key_Name,
                                       variable.Internal_Data_Type))
    for variables in idf.idfobjects['EnergyManagementSystem:GlobalVariable']:
        # The names of the variables are the values of all its fields
        ems.global_variables.extend(str(name).upper() for name in variables.fieldvalues[1:] if name)
    for object_type in ('EnergyManagementSystem:Program', 'EnergyManagementSystem:Subroutine'):
        for program in idf.idfobjects[object_type]:
            # The lines are the values of the fields after the name
            ems.programs[program.Name.upper()] = [str(line) for line in program.fieldvalues[2:]]
    for manager in idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']:
        # The programs are the values of the fields after the calling point
        ems.calling_managers.append((manager.Name, manager.EnergyPlus_Model_Calling_Point.replace(' ', '').upper(),
                                     [str(name).upper() for name in manager.fieldvalues[3:] if name]))
    for object_type in idf.idfobjects:
        if object_type.upper() in UNSUPPORTED_EMS_OBJECTS or object_type.upper().startswith('EXTERNALINTERFACE'):
            ems.unsupported.extend(object_type for _ in idf.idfobjects[object_type])
    # The scope of the reported variables needs all the global variables
    for object_type in _OUTPUT_VARIABLES:
        for output in idf.idfobjects[object_type]:
            name, program = ems.reported_name(output.EMS_Variable_Name, output.EMS_Program_or_Subroutine_Name)
            if (name, output.EMS_Variable_Name.upper(), program) not in ems.reported_variables:
                ems.reported_variables.append((name, output.EMS_Variable_Name.upper(), program))
    return ems


def prepare_for_api(idf) -> EmsDefinition:
    """Make a model (an IDF object of eppy) the one that the Python API runs, and return its EMS objects.

    The EMS programs, subroutines, program calling managers and actuators are removed, and the EMS output variables
    of actuators and of variables of programs report new global variables, which the controller updates.
    """
    ems = read_ems(idf)
    for object_type in _CONTROL_OBJECTS:
        idf.removeallidfobjects(object_type)
    for object_type in _OUTPUT_VARIABLES:
        for output in idf.idfobjects[object_type]:
            if not output.EMS_Program_or_Subroutine_Name:
                continue
            # The programs are not in the model: the output variable reports a global variable
            name, program = ems.reported_name(output.EMS_Variable_Name, output.EMS_Program_or_Subroutine_Name)
            if program:
                output.EMS_Variable_Name = name
            output.EMS_Program_or_Subroutine_Name = ''
    added = ems.added_global_variables()
    if added:
        idf.newidfobject('EnergyManagementSystem:GlobalVariable',
                         **{f'Erl_Variable_{number}_Name': name for number, name in enumerate(added, start=1)})
    return ems
