# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The windows and doors of the models in full air-conditioning on the design days.

In full air-conditioning (ScriptTypes 'vrf_ac' and 'ex_ac', and the VRF systems of
:func:`accim.sim.apmv.add_vrf_system`), the windows and doors of the model keep its own control, its natural
ventilation, except on the design days (the decision of 2026-11-19, ``notes/decisions.md``): there, those that the EMS
of mixed mode would open and close (see :mod:`accim.sim.windows`) are closed, as mixed mode does, so that EnergyPlus
sizes the HVAC systems for the setpoints with the windows closed. Before, the windows that the model opens on its design
days were open while EnergyPlus sized the systems: the venting setpoint of the windows of the sample model of accim is
0 °C on its winter design day, so its VRF systems were sized for the outdoor air at −4 °C through its open windows,
about 100 times too big (design heating loads of 303 and 357 kW, which are 1.5 and 1.7 kW with the windows closed).

The program ``CloseWindowsOnDesignDays``, which EnergyPlus runs at the beginning of each timestep
(``BeginTimestepBeforePredictor``, also while it sizes the systems), sets an actuator of each window or door to 0 on the
design days (the sensor ``DesignDay`` of :data:`accim.sim.hvac.schedules.DESIGN_DAY_SCHEDULE`) and to Null on the other
days, which gives the window back to the control of the model: EnergyPlus does not release the actuators between the
sizing periods while it sizes the zones, so the program releases them itself. The actuators are:

- with an AirflowNetwork that simulates the multizone airflows (:func:`accim.sim.windows.uses_airflow_network`), the
  venting opening factor (``AirFlow Network Window/Door Opening``, ``Venting Opening Factor``) of each window, door and
  glass door of the exterior surfaces of the zones with an opening (:func:`accim.sim.windows.afn_openings`),
  ``<window>_DesignDayVOF``, which replaces its venting control and its availability schedule;
- otherwise, the flow rate (``Zone Ventilation``, ``Air Exchange Flow Rate``) of each instance of the natural
  ventilation objects of the zones (:func:`accim.sim.windows.ventilation_instances`), ``<instance>_DesignDayFlow``,
  which replaces their schedules and limits.

The zones are the occupied ones, those of mixed mode, and with the existing HVAC systems ('ex_ac') also the zones with
thermostats without occupants, whose systems EnergyPlus also sizes. The names of the actuators that would not begin
with a letter (a window named '3F South Win') begin with ``Win_`` or ``Vent_``, since EnergyPlus stops with such names
of EMS variables; the sensor is ``DesignDay_2``... if the model has another EMS variable named ``DesignDay``.

The model is not changed otherwise. The EMS cannot close the windows and doors that an occupant ventilation control
opens and closes (AirflowNetwork:OccupantVentilationControl, which overrides it; mixed mode removes these controls),
and would release on the other days those that the EMS of the model actuates (EnergyPlus applies the actuators of a
window one after the other, and that of accim is the last one): they keep the control of the model also on the design
days, with a warning. EnergyPlus also applies the EMS actuators after the Python plugins and the external interfaces,
whose actuators accim cannot see, so a model with PythonPlugin:Instance objects or actuators of external interfaces
gets no program, with a warning (the windows that a script of the user with the Python API of EnergyPlus actuates
would be released too: accim cannot know them). The design days are the days of the types SummerDesignDay and
WinterDesignDay, as in mixed mode: in the sizing periods of the weather file of other types of day
(SizingPeriod:WeatherFileDays and SizingPeriod:WeatherFileConditionType), the windows keep the control of the model.
"""

import re
import warnings
from typing import List, Set, Tuple

from accim.sim.ems.objects import _add_actuator, add_sensor
from accim.sim.ems.programs import add_program
from accim.sim.hvac.schedules import DESIGN_DAY_SCHEDULE, add_design_day_schedule
from accim.sim.model import AccimModel
from accim.sim.targets import sanitize_ems_name
from accim.sim.windows import afn_openings, occupant_controlled_surfaces, uses_airflow_network, ventilation_instances

__all__ = ['PROGRAM', 'close_windows_on_design_days', 'design_day_actuators']

#: The EMS program that closes the windows and doors on the design days, and its program calling manager.
PROGRAM = 'CloseWindowsOnDesignDays'
#: (component type, control type, prefix of the names that do not begin with a letter, suffix of the names) of the
#: actuators of the windows and doors of an AirflowNetwork, and of the instances of the natural ventilation objects.
_AFN_ACTUATOR = ('AirFlow Network Window/Door Opening', 'Venting Opening Factor', 'Win_', '_DesignDayVOF')
_VENTILATION_ACTUATOR = ('Zone Ventilation', 'Air Exchange Flow Rate', 'Vent_', '_DesignDayFlow')
#: The name of the sensor of the schedule of the design days (that of mixed mode), unless the model has another EMS
#: variable with that name.
_SENSOR = 'DesignDay'


def _external_controls(idf) -> List[str]:
    """The classes of the objects of a model that actuate its components outside the EMS programs: Python plugins
    (PythonPlugin:Instance) and the actuators of the external interfaces (ExternalInterface:Actuator and those of the
    FMUs). EnergyPlus applies the EMS actuators after them, so an actuator of accim, Null on the days that are not
    design days, would release the windows that they open."""
    classes = []
    for key, objects in idf.idfobjects.items():
        name = str(key).upper()
        if len(objects) and (name == 'PYTHONPLUGIN:INSTANCE'
                             or (name.startswith('EXTERNALINTERFACE') and name.endswith('ACTUATOR'))):
            classes.append(objects[0].key if hasattr(objects[0], 'key') else str(key))
    return classes


def _erl_names(idf) -> Set[str]:
    """The names of the EMS sensors, actuators, internal variables and global variables of a model, in upper case."""
    names = set()
    for object_type in ('EnergyManagementSystem:Sensor', 'EnergyManagementSystem:Actuator',
                        'EnergyManagementSystem:InternalVariable'):
        names.update(str(obj.Name).strip().upper() for obj in idf.idfobjects[object_type])
    for variables in idf.idfobjects['EnergyManagementSystem:GlobalVariable']:
        names.update(str(name).strip().upper() for name in variables.fieldvalues[1:] if str(name).strip())
    return names


def design_day_actuators(model: AccimModel) -> List[Tuple[str, str, str, str]]:
    """The EMS actuators that close the windows and doors of a model in full air-conditioning on the design days: (name,
    component unique name, component type, control type) of each window, door or instance of a natural ventilation
    object, in their order (see the module).

    The windows and doors are those of the occupied zones and, with the existing HVAC systems ('ex_ac'), also those of
    the zones with thermostats without occupants, which EnergyPlus also sizes. The windows and doors with an occupant
    ventilation control and those that the EMS of the model actuates are left out, with a warning; and all of them if
    the model has Python plugins or actuators of external interfaces (see :func:`_external_controls`), which accim
    cannot see. The names of the actuators are valid names of the EMS (``Win_`` or ``Vent_`` before those that do not
    begin with a letter) that no other EMS object of the model has (with '_2', '_3'... if needed)."""
    idf = model.idf
    external = _external_controls(idf)
    if external:
        warnings.warn(f'The model {model.name} has objects that can open and close its windows outside the EMS '
                      f'({sorted(set(external))}), which an actuator of accim would release on the days that are not '
                      f'design days, so accim does not close its windows on the design days: EnergyPlus sizes the HVAC '
                      f'systems with them as the model opens them.', stacklevel=4)
        return []
    zones = list(model.occupied_zones_orig)
    if not model.script_type.startswith('vrf'):
        # The existing HVAC systems also condition the zones with thermostats without occupants
        known = {zone.upper() for zone in zones}
        zones += [zone for zone in getattr(model, 'zones_orig', []) if zone.upper() not in known]
    if uses_airflow_network(idf):
        component_type, control_type, prefix, suffix = _AFN_ACTUATOR
        openings = [surface for surface, _ in afn_openings(idf, zones)]
        controlled = occupant_controlled_surfaces(idf, openings)
        if controlled:
            warnings.warn(f'The windows and doors {controlled} of the model {model.name} have an occupant ventilation '
                          f'control (AirflowNetwork:OccupantVentilationControl), which overrides the EMS, so accim '
                          f'cannot close them on the design days: EnergyPlus sizes the HVAC systems with them as the '
                          f'control opens them.', stacklevel=4)
            skipped = {surface.upper() for surface in controlled}
            openings = [surface for surface in openings if surface.upper() not in skipped]
    else:
        component_type, control_type, prefix, suffix = _VENTILATION_ACTUATOR
        openings = [instance for instance, _, _ in ventilation_instances(idf, zones)]
    # The actuators of the model on the same windows: that of accim would release them on the other days
    own = {str(actuator.Actuated_Component_Unique_Name).strip().upper(): str(actuator.Name)
           for actuator in idf.idfobjects['EnergyManagementSystem:Actuator']
           if str(actuator.Actuated_Component_Type).strip().upper() == component_type.upper()
           and str(actuator.Actuated_Component_Control_Type).strip().upper() == control_type.upper()}
    actuated = [opening for opening in openings if opening.upper() in own]
    if actuated:
        warnings.warn(f'The EMS actuators {[own[opening.upper()] for opening in actuated]} of the model {model.name} '
                      f'give the opening of the windows and doors (or the flow rate of the ventilation objects) '
                      f'{actuated}, so accim does not close them on the design days: they keep the control of the EMS '
                      f'of the model.', stacklevel=4)
        openings = [opening for opening in openings if opening.upper() not in own]
    used = _erl_names(idf)
    actuators = []
    for opening in openings:
        base = sanitize_ems_name(opening)
        # EnergyPlus stops with the names of EMS variables that do not begin with a letter
        base = (base if re.match('[A-Za-z]', base) else prefix + base) + suffix
        name, number = base, 1
        while name.upper() in used:
            number += 1
            name = f'{base}_{number}'
        used.add(name.upper())
        actuators.append((name, opening, component_type, control_type))
    return actuators


def _design_day_sensor(model: AccimModel) -> str:
    """Add the schedule of the design days and the EMS sensor of its value, unless the model has one; return the name
    of the sensor: that of a sensor of the model that reads the schedule (``DesignDay``, as in mixed mode), or
    ``DesignDay`` if no other EMS variable of the model has that name, or ``DesignDay_2``, ``DesignDay_3``...
    otherwise."""
    idf = model.idf
    add_design_day_schedule(model)
    for sensor in idf.idfobjects['EnergyManagementSystem:Sensor']:
        if (str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name).strip().upper() == DESIGN_DAY_SCHEDULE.upper()
                and str(sensor.OutputVariable_or_OutputMeter_Name).strip().upper() == 'SCHEDULE VALUE'):
            return str(sensor.Name)
    used = _erl_names(idf)
    name, number = _SENSOR, 1
    while name.upper() in used:
        number += 1
        name = f'{_SENSOR}_{number}'
    add_sensor(model, name, DESIGN_DAY_SCHEDULE, 'Schedule Value')
    return name


def close_windows_on_design_days(model: AccimModel) -> List[str]:
    """Add to a model in full air-conditioning the EMS objects that close its windows and doors on the design days (see
    the module): the sensor ``DesignDay`` (and its schedule; see :func:`_design_day_sensor`), the actuators of
    :func:`design_day_actuators`, the program ``CloseWindowsOnDesignDays`` and its program calling manager. A model
    without such windows and doors does not change, nor does one that already has the program.

    :return: The windows and doors (or the instances of the ventilation objects) that the program closes.
    """
    idf = model.idf
    if idf.getobject('EnergyManagementSystem:Program', PROGRAM) is not None:
        model.log(f'Not added - {PROGRAM} Program')
        return []
    actuators = design_day_actuators(model)
    if not actuators:
        return []
    sensor = _design_day_sensor(model)
    for name, component, component_type, control_type in actuators:
        _add_actuator(model, name, component, component_type, control_type)
    names = [actuator[0] for actuator in actuators]
    add_program(idf, PROGRAM, [f'if {sensor} == 1', *(f'set {name} = 0' for name in names), 'else',
                               *(f'set {name} = Null' for name in names), 'endif'])
    model.log(f'Added - {PROGRAM} Program')
    idf.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name=PROGRAM,
                     EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor', Program_Name_1=PROGRAM)
    model.log(f'Added - {PROGRAM} Program Calling Manager')
    closed = [actuator[1] for actuator in actuators]
    model.log(f'The windows and doors that are closed on the design days in the model {model.name} are:', *closed)
    return closed
