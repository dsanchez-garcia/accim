# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EMS objects of an IDF file, and the IDF that the Python API of EnergyPlus runs without them.

The Python API backend runs the EMS programs in Python, so the IDF that EnergyPlus runs has no
programs, subroutines, program calling managers or actuators (EnergyPlus would set the actuators
after each calling point, overwriting the values of the API). The sensors, internal variables,
global variables and output variables stay: EnergyPlus resets the variables of the sensors at each
new environment, as it does with the EMS, and reports the global variables, which the controller
updates.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Union

from accim.sim.ems.erl import BUILT_IN_VARIABLES

__all__ = ['EmsDefinition', 'IdfObject', 'UNSUPPORTED_EMS_OBJECTS', 'objects_for_api', 'parse_idf', 'read_ems',
           'read_idf', 'render_idf']

#: EMS objects that the Python API backend does not support
UNSUPPORTED_EMS_OBJECTS = (
    'ENERGYMANAGEMENTSYSTEM:TRENDVARIABLE',
    'ENERGYMANAGEMENTSYSTEM:CURVEORTABLEINDEXVARIABLE',
    'ENERGYMANAGEMENTSYSTEM:CONSTRUCTIONINDEXVARIABLE',
    'EXTERNALINTERFACE',
    'PYTHONPLUGIN:INSTANCE',
)
#: EMS objects that the Python API backend runs in Python, which are removed from the IDF
_CONTROL_OBJECTS = (
    'ENERGYMANAGEMENTSYSTEM:PROGRAM',
    'ENERGYMANAGEMENTSYSTEM:SUBROUTINE',
    'ENERGYMANAGEMENTSYSTEM:PROGRAMCALLINGMANAGER',
    'ENERGYMANAGEMENTSYSTEM:ACTUATOR',
)
#: The EMS output variables, and the index of their field 'EMS Program or Subroutine Name'
_OUTPUT_VARIABLES = {
    'ENERGYMANAGEMENTSYSTEM:OUTPUTVARIABLE': 4,
    'ENERGYMANAGEMENTSYSTEM:METEREDOUTPUTVARIABLE': 3,
}
_COMMENT = re.compile(r'!.*')


@dataclass
class IdfObject:
    """An object of an IDF file: its class and its fields (without comments)."""

    type: str
    fields: List[str]

    @property
    def key(self) -> str:
        """The class in upper case."""
        return self.type.upper()

    def field(self, index: int) -> str:
        """The field ``index`` (0 is the first field after the class), or '' if the object has fewer fields."""
        return self.fields[index] if index < len(self.fields) else ''


def parse_idf(text: str) -> List[IdfObject]:
    """The objects of the text of an IDF file."""
    text = _COMMENT.sub('', text)
    objects = []
    for block in text.split(';'):
        if not block.strip():
            continue
        fields = [f.strip() for f in block.split(',')]
        objects.append(IdfObject(fields[0], fields[1:]))
    return objects


def read_idf(path: Union[str, os.PathLike]) -> List[IdfObject]:
    """The objects of an IDF file."""
    with open(path, 'rb') as file:
        return parse_idf(file.read().decode('latin-1'))


def render_idf(objects: List[IdfObject]) -> str:
    """The text of an IDF file with the objects."""
    parts = []
    for obj in objects:
        fields = [obj.type] + obj.fields
        parts.append(',\n    '.join(fields) + ';\n')
    return '\n'.join(parts)


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


def read_ems(objects: List[IdfObject]) -> EmsDefinition:
    """The EMS objects of a model, and its EnergyPlus version."""
    ems = EmsDefinition()
    outputs = []
    for obj in objects:
        key = obj.key
        if key == 'VERSION':
            parts = obj.field(0).split('.')
            ems.version = '.'.join(parts[:2])
        elif key == 'ENERGYMANAGEMENTSYSTEM:SENSOR':
            ems.sensors.append((obj.field(0).upper(), obj.field(1), obj.field(2)))
        elif key == 'ENERGYMANAGEMENTSYSTEM:ACTUATOR':
            ems.actuators.append((obj.field(0).upper(), obj.field(1), obj.field(2), obj.field(3)))
        elif key == 'ENERGYMANAGEMENTSYSTEM:INTERNALVARIABLE':
            ems.internal_variables.append((obj.field(0).upper(), obj.field(1), obj.field(2)))
        elif key == 'ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE':
            ems.global_variables.extend(name.upper() for name in obj.fields if name)
        elif key in ('ENERGYMANAGEMENTSYSTEM:PROGRAM', 'ENERGYMANAGEMENTSYSTEM:SUBROUTINE'):
            ems.programs[obj.field(0).upper()] = obj.fields[1:]
        elif key == 'ENERGYMANAGEMENTSYSTEM:PROGRAMCALLINGMANAGER':
            ems.calling_managers.append((obj.field(0), obj.field(1).replace(' ', '').upper(),
                                         [name.upper() for name in obj.fields[2:] if name]))
        elif key in _OUTPUT_VARIABLES:
            outputs.append((obj.field(1), obj.field(_OUTPUT_VARIABLES[key])))
        elif key in UNSUPPORTED_EMS_OBJECTS or key.startswith('EXTERNALINTERFACE'):
            ems.unsupported.append(obj.type)
    # The scope of the reported variables needs all the global variables, which may come after the output variables
    for variable, program in outputs:
        name, program = ems.reported_name(variable, program)
        if (name, variable.upper(), program) not in ems.reported_variables:
            ems.reported_variables.append((name, variable.upper(), program))
    return ems


def objects_for_api(objects: List[IdfObject]) -> List[IdfObject]:
    """The objects of the IDF that the Python API runs: those of the model without the EMS programs, subroutines,
    program calling managers and actuators, and with global variables for the EMS output variables of actuators
    and variables of programs."""
    ems = read_ems(objects)
    result = []
    for obj in objects:
        if obj.key in _CONTROL_OBJECTS:
            continue
        if obj.key in _OUTPUT_VARIABLES and obj.field(_OUTPUT_VARIABLES[obj.key]):
            # The programs are not in the IDF: the output variable reports a global variable
            fields = list(obj.fields)
            program_field = _OUTPUT_VARIABLES[obj.key]
            name, program = ems.reported_name(obj.field(1), obj.field(program_field))
            if program:
                fields[1] = name
            fields[program_field] = ''
            obj = IdfObject(obj.type, fields)
        result.append(obj)
    added = ems.added_global_variables()
    if added:
        result.append(IdfObject('EnergyManagementSystem:GlobalVariable', added))
    return result
