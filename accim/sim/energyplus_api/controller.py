# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Runs the EMS programs of a model in the callbacks of the Python API of EnergyPlus.

The controller does what the EMS of EnergyPlus does (``EMSManager.cc``) at each calling point:

1. At the beginning of each environment, the variables that have been set become 0 and the actuators
   Null. Before the first one, the variables that the programs set become 0, as after the first runs
   of the programs that EnergyPlus makes to start the simulation, without callbacks.
2. The built-in variables, internal variables and sensors are updated.
3. The programs of the calling managers of the calling point run, in the order of the IDF.
4. Each actuator is released if its variable is Null, and set to the number of its variable otherwise (0 for
   the values that are not numbers, such as the errors while sizing). The integer actuators get the number
   rounded down, and the logical ones are true only for 1, as with the EMS (the API itself would round the
   integers and accept 1 within 1e-5), so the controller finds the type of each actuator when it first finds it.
5. The global variables that EMS output variables report are written to EnergyPlus.

While EnergyPlus sizes the systems (before the first environment), the serious errors of the programs
(an uninitialised variable, a division by zero...) give error values, as in EnergyPlus; afterwards,
they stop the simulation.
"""

import datetime
import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from accim.sim.ems.erl import BUILT_IN_VARIABLES, ErlProgramSet, is_number, variables_in_programs
from accim.sim.energyplus_api.idf import EmsDefinition

__all__ = ['CALLING_POINTS', 'ErlController', 'Hook']

#: The calling points of the EMS program calling managers, and the functions of the API that register
#: callbacks at them
CALLING_POINTS = {
    'BEGINNEWENVIRONMENT': 'callback_begin_new_environment',
    'AFTERNEWENVIRONMENTWARMUPISCOMPLETE': 'callback_after_new_environment_warmup_complete',
    'BEGINZONETIMESTEPBEFOREINITHEATBALANCE': 'callback_begin_zone_timestep_before_init_heat_balance',
    'BEGINZONETIMESTEPAFTERINITHEATBALANCE': 'callback_begin_zone_timestep_after_init_heat_balance',
    'BEGINZONETIMESTEPBEFORESETCURRENTWEATHER': 'callback_begin_zone_timestep_before_set_current_weather',
    'BEGINTIMESTEPBEFOREPREDICTOR': 'callback_begin_system_timestep_before_predictor',
    'AFTERPREDICTORBEFOREHVACMANAGERS': 'callback_after_predictor_before_hvac_managers',
    'AFTERPREDICTORAFTERHVACMANAGERS': 'callback_after_predictor_after_hvac_managers',
    'INSIDEHVACSYSTEMITERATIONLOOP': 'callback_inside_system_iteration_loop',
    'ENDOFZONETIMESTEPBEFOREZONEREPORTING': 'callback_end_zone_timestep_before_zone_reporting',
    'ENDOFZONETIMESTEPAFTERZONEREPORTING': 'callback_end_zone_timestep_after_zone_reporting',
    'ENDOFSYSTEMTIMESTEPBEFOREHVACREPORTING': 'callback_end_system_timestep_before_hvac_reporting',
    'ENDOFSYSTEMTIMESTEPAFTERHVACREPORTING': 'callback_end_system_timestep_after_hvac_reporting',
    'ENDOFZONESIZING': 'callback_end_zone_sizing',
    'ENDOFSYSTEMSIZING': 'callback_end_system_sizing',
    'AFTERCOMPONENTINPUTREADIN': 'callback_after_component_get_input',
    'UNITARYSYSTEMSIZING': 'callback_unitary_system_sizing',
}
_BEGIN_NEW_ENVIRONMENT = 'BEGINNEWENVIRONMENT'
_SIZING_CALLING_POINTS = ('ENDOFZONESIZING', 'ENDOFSYSTEMSIZING')

#: A function called at a calling point before or after the programs: hook(controller, calling_point)
Hook = Callable[['ErlController', str], None]


class ErlController:
    """Runs the EMS programs of a model in the callbacks of the Python API of EnergyPlus.

    :param ems: The EMS objects of the model.
    :param before_programs: Functions called at each calling point before the programs, as
        ``hook(controller, calling_point)``; for instance, to change the value of a variable.
    :param after_programs: Functions called at each calling point after the programs, before the actuators
        are set; for instance, to read or change the setpoints.
    :ivar programs: The compiled programs and their variables (:class:`~accim.sim.ems.erl.ErlProgramSet`).
    :ivar api: The EnergyPlusAPI object, and ``state`` the state of the simulation, during the simulation.
    :ivar environments: The number of environments (sizing periods and run periods) that have begun.
    :ivar calls: The number of calling points that have run.
    :ivar error: The exception that stopped the simulation, if any.
    """

    def __init__(self, ems: EmsDefinition, before_programs: Sequence[Hook] = (),
                 after_programs: Sequence[Hook] = ()):
        if ems.unsupported:
            raise NotImplementedError(f'The Python API backend does not support the objects '
                                      f'{sorted(set(ems.unsupported))}. Run the model with the EMS backend.')
        self.ems = ems
        self.before_programs = list(before_programs)
        self.after_programs = list(after_programs)
        self.schedule: Dict[str, List[str]] = {}
        for name, calling_point, programs in ems.calling_managers:
            if calling_point not in CALLING_POINTS:
                raise NotImplementedError(f'The Python API backend does not support the calling point {calling_point} '
                                          f'of the program calling manager {name}.')
            missing = [p for p in programs if p not in ems.programs]
            if missing:
                raise ValueError(f'The program calling manager {name} runs the programs {missing}, which are not in '
                                 f'the model.')
            self.schedule.setdefault(calling_point, []).extend(programs)

        self.sensors = list(ems.sensors)
        self.actuators = list(ems.actuators)
        self.internal_variables = list(ems.internal_variables)
        global_names = (list(ems.global_variables) + [s[0] for s in self.sensors]
                        + [i[0] for i in self.internal_variables])
        self.programs = ErlProgramSet(ems.programs, global_variables=global_names,
                                      actuators=[a[0] for a in self.actuators])
        # The messages of @WarnEP, @SevereWarnEP and @FatalHaltEP go to the error file of EnergyPlus
        self.programs.on_message = self._issue_message
        # Before the first environment, EnergyPlus is sizing the systems
        self.programs.strict = False
        used = set().union(*variables_in_programs(ems.programs).values()) if ems.programs else set()
        self._built_ins = sorted(used & BUILT_IN_VARIABLES)
        self._reported = list(ems.reported_variables)

        self.api = None
        self.state = None
        self.environments = 0
        self.calls = 0
        self.error: Optional[BaseException] = None
        self._callbacks = []
        # Handles of the variables of EnergyPlus of the sensors and internal variables
        self._erl_handles: Dict[str, int] = {}
        self._actuator_handles: Dict[str, int] = {}
        self._actuator_handles_by_component: Dict[Tuple[str, str, str], int] = {}
        # The type of the variable of each actuator ('real', 'integer' or 'logical'), by handle
        self._actuator_kinds: Dict[int, str] = {}
        self._global_handles: Dict[str, int] = {}
        self._written: Dict[str, float] = {}
        self._all_resolved = False
        self._resolved_environment = None
        self._constants_set = False

    # ------------------------------------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------------------------------------

    def register(self, api, state) -> None:
        """Register the callbacks of the calling points. It must be called before running EnergyPlus with the state.
        """
        self.api = api
        self.state = state
        for calling_point in {_BEGIN_NEW_ENVIRONMENT, *self.schedule}:
            callback = self._make_callback(calling_point)
            self._callbacks.append(callback)
            getattr(api.runtime, CALLING_POINTS[calling_point])(state, callback)
        # The EMS also looks again for the objects it has not found at the end of the zone and system sizing
        for calling_point in _SIZING_CALLING_POINTS:
            if calling_point not in self.schedule:
                callback = self._make_observer()
                self._callbacks.append(callback)
                getattr(api.runtime, CALLING_POINTS[calling_point])(state, callback)

    def _make_observer(self):
        def callback(state):
            if self.error is None and not self._all_resolved and self.environments == 0:
                try:
                    self._resolve_handles(state)
                except BaseException as error:  # noqa: BLE001
                    self.error = error
        return callback

    def _make_callback(self, calling_point: str):
        def callback(state):
            if self.error is not None:
                return
            try:
                self.run_calling_point(state, calling_point)
            except BaseException as error:  # noqa: BLE001 (the API ignores the exceptions of the callbacks)
                self.error = error
                stop = getattr(self.api.runtime, 'stop_simulation', None)
                if stop is not None:
                    stop(state)
        return callback

    # ------------------------------------------------------------------------------------------------
    # Calling points
    # ------------------------------------------------------------------------------------------------

    def run_calling_point(self, state, calling_point: str) -> None:
        """Do what the EMS does at a calling point."""
        self.state = state
        self.calls += 1
        if calling_point == _BEGIN_NEW_ENVIRONMENT:
            self._begin_environment(state)
        elif not self._all_resolved:
            # While sizing, the EMS looks again for the objects it has not found at the beginning of each
            # environment (InitEMS with BeginEnvrnFlag, which is true during the first timestep)
            environment = self.api.exchange.current_environment_num(state)
            if environment != self._resolved_environment:
                self._resolved_environment = environment
                self._resolve_handles(state)
        self._update_inputs(state)
        for hook in self.before_programs:
            hook(self, calling_point)
        for program in self.schedule.get(calling_point, ()):
            self.programs.run(program)
        for hook in self.after_programs:
            hook(self, calling_point)
        self._apply_actuators(state)
        self._write_reported_variables(state)

    def _begin_environment(self, state) -> None:
        if self.environments == 0:
            self.programs.initialise_set_variables()
        self.programs.reset()
        self.programs.strict = True
        self.environments += 1
        # EnergyPlus resets its variables, so the reported variables are written again
        self._written.clear()
        self._resolve_handles(state)
        # The EMS sets the value of each actuator to 0 and releases it (some actuators, such as the setpoints
        # of the nodes, are the variables of the objects)
        exchange = self.api.exchange
        for handle in self._actuator_handles.values():
            exchange.set_actuator_value(state, handle, 0.0)
            exchange.reset_actuator(state, handle)

    def _resolve_handles(self, state) -> None:
        exchange = self.api.exchange
        unresolved = 0
        # The sensors and internal variables stay in the model, so EnergyPlus updates their variables as with
        # the EMS (when it finds their output variables, the schedules of the 'Schedule Value' sensors, the
        # resets at each new environment...), and the controller reads them
        for name in [s[0] for s in self.sensors] + [i[0] for i in self.internal_variables]:
            if name in self._erl_handles:
                continue
            handle = exchange.get_ems_global_handle(state, name)
            if handle > 0:
                self._erl_handles[name] = handle
            else:
                unresolved += 1
        for name, unique_name, component_type, control_type in self.actuators:
            if name in self._actuator_handles:
                continue
            component = (component_type.upper(), control_type.upper(), unique_name.upper())
            handle = self._actuator_handles_by_component.get(component)
            if handle is None:
                handle = exchange.get_actuator_handle(state, component_type, control_type, unique_name)
            if handle >= 0:
                self._actuator_handles[name] = handle
                self._actuator_handles_by_component[component] = handle
                if handle not in self._actuator_kinds:
                    self._actuator_kinds[handle] = self._actuator_kind(state, handle)
            else:
                unresolved += 1
        for name, _, _ in self._reported:
            if name in self._global_handles:
                continue
            handle = exchange.get_ems_global_handle(state, name)
            if handle > 0:
                self._global_handles[name] = handle
            else:
                unresolved += 1
        # The objects that do not exist after the first environment begins will not exist later
        self._all_resolved = unresolved == 0 or self.environments > 0

    def _actuator_kind(self, state, handle: int) -> str:
        """The type of the variable of an actuator: 'real', 'integer' or 'logical'.

        The API does not tell it. An integer actuator rounds 0.5 to 1, and a logical one takes it as false (0),
        so the controller writes 0.5 and reads it back. Then it writes back the value the actuator had and
        releases it, so the model does not change (no actuator of the model has been actuated before).
        """
        exchange = self.api.exchange
        original = exchange.get_actuator_value(state, handle)
        exchange.set_actuator_value(state, handle, 0.5)
        probe = exchange.get_actuator_value(state, handle)
        exchange.set_actuator_value(state, handle, original)
        exchange.reset_actuator(state, handle)
        if probe == 0.5:
            return 'real'
        return 'integer' if probe == 1.0 else 'logical'

    def _api_value(self, handle: int, value: float) -> float:
        """The value that makes the API set an actuator as the EMS does (``EMSManager.cc``).

        The EMS sets the integer actuators to the number rounded down (``std::floor``), and the logical ones to true
        only if the number is 1, while the API rounds to the nearest integer (``std::lround``) and takes as true the
        numbers within 1e-5 of 1.
        """
        kind = self._actuator_kinds.get(handle, 'real')
        if kind == 'integer':
            return float(math.floor(value)) if math.isfinite(value) else value
        if kind == 'logical':
            return 1.0 if value == 1.0 else 0.0
        return value

    def _issue_message(self, level: str, text: str) -> None:
        if self.api is None or self.state is None:
            return
        runtime = self.api.runtime
        (runtime.issue_severe if level == 'severe' else runtime.issue_warning)(self.state, text)

    def _update_inputs(self, state) -> None:
        exchange = self.api.exchange
        variables = self.programs.variables
        if not self._constants_set:
            self._set_constant_built_ins(state)
        functions = exchange.api
        for name in self._built_ins:
            getter = _DYNAMIC_BUILT_INS.get(name)
            if getter is not None:
                variables[name] = float(getter(functions, state))
        for name, handle in self._erl_handles.items():
            variables[name] = float(exchange.get_ems_global_value(state, handle))

    def _set_constant_built_ins(self, state) -> None:
        functions = self.api.exchange.api
        variables = self.programs.variables
        zone_time_step = float(functions.zoneTimeStep(state))
        steps = float(functions.numTimeStepsInHour(state))
        now = datetime.datetime.now()
        variables['TIMESTEPSPERHOUR'] = steps
        variables['ZONETIMESTEP'] = zone_time_step
        variables['ACTUALDATEANDTIME'] = float(now.year + now.month + now.day + now.hour + now.minute + now.second
                                               + now.microsecond // 1000)
        variables['ACTUALTIME'] = float(now.hour + now.minute + now.second + now.microsecond // 1000)
        # The EMS creates the variables of the sensors as numbers 0 that have been set, also those of the
        # sensors whose output variable it has not found yet
        for name, _, _ in self.sensors:
            variables.setdefault(name, 0.0)
        self._constants_set = True

    def _apply_actuators(self, state) -> None:
        exchange = self.api.exchange
        for name, handle in self._actuator_handles.items():
            value = self.programs.value(name)
            if is_number(value):
                exchange.set_actuator_value(state, handle, self._api_value(handle, value))
            elif value is None or value.type == 'Null':
                exchange.reset_actuator(state, handle)
            else:
                # EnergyPlus actuates the values that are not Null with their number, which is 0 for the errors and
                # the results of the operators whose operands are not numbers
                exchange.set_actuator_value(state, handle, 0.0)

    def _write_reported_variables(self, state) -> None:
        exchange = self.api.exchange
        for name, variable, program in self._reported:
            handle = self._global_handles.get(name)
            if handle is None:
                continue
            value = self.programs.value(variable, program or None)
            number = value if is_number(value) else 0.0
            if self._written.get(name) != number:
                exchange.set_ems_global_value(state, handle, number)
                self._written[name] = number

    # ------------------------------------------------------------------------------------------------
    # Access for the hooks
    # ------------------------------------------------------------------------------------------------

    def get(self, name: str, program: Optional[str] = None) -> Optional[float]:
        """The number of a variable (None if it is Null or has not been set)."""
        return self.programs.get(name, program)

    def set(self, name: str, value: Optional[float]) -> None:
        """Set a global variable (None sets Null; for an actuator, it releases the actuated object)."""
        self.programs.set(name, value)


def _holiday(functions, state) -> float:
    index = functions.holidayIndex(state)
    return float(index - 7) if index != 0 else 0.0


def _minute(functions, state) -> float:
    return (functions.currentTime(state) - float(functions.hour(state))) * 60.0


# The dynamic built-in variables, which the EMS updates at each calling point (InitializeRuntimeLanguage), from the
# C functions of the API, since the Python functions of some versions transform them
_DYNAMIC_BUILT_INS = {
    'YEAR': lambda f, s: f.year(s),
    'CALENDARYEAR': lambda f, s: f.calendarYear(s),
    'MONTH': lambda f, s: f.month(s),
    'DAYOFMONTH': lambda f, s: f.dayOfMonth(s),
    'DAYOFWEEK': lambda f, s: f.dayOfWeek(s),
    'DAYOFYEAR': lambda f, s: f.dayOfYear(s),
    'TIMESTEPNUM': lambda f, s: f.zoneTimeStepNum(s),
    'DAYLIGHTSAVINGS': lambda f, s: f.daylightSavingsTimeIndicator(s),
    'HOUR': lambda f, s: f.hour(s),
    'CURRENTTIME': lambda f, s: f.currentTime(s),
    'MINUTE': _minute,
    'HOLIDAY': _holiday,
    'SUNISUP': lambda f, s: f.sunIsUp(s),
    'ISRAINING': lambda f, s: f.isRaining(s),
    'SYSTEMTIMESTEP': lambda f, s: f.systemTimeStep(s),
    'CURRENTENVIRONMENT': lambda f, s: f.currentEnvironmentNum(s),
    'WARMUPFLAG': lambda f, s: f.warmupFlag(s),
}
