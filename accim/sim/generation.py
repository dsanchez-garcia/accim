# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Output IDFs of :class:`accim.sim.accis.AddAccis`: one for each combination of the arguments.

All the output IDFs of an input IDF are the same model, with the ACCIS, and only differ in the EMS programs
SetInputData_<zone>, with the arguments of each zone (those of the combination, or those of ``zone_arguments`` for
some zones). :func:`set_combination` sets them in the model, which eppy then saves as each output IDF.
"""

import math
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Union

import numpy as np

from accim.sim.arguments import as_list, to_day_of_year
from accim.sim.ems.inputs import input_lines, input_programs, input_values
from accim.sim.ems.programs import set_program_lines
from accim.sim.ems.setast import has_setpoints
from accim.sim.standards import COMFORT_STANDARDS

__all__ = ['Combination', 'GenerationArguments', 'OutputIdfs', 'combinations', 'output_name', 'set_combination',
           'zone_arguments_errors', 'zone_input_arguments']

Number = Union[int, float]
_STATIC_MODES = (0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5)
#: The ventilation arguments of the zones with HVACmode 0 in the output IDFs, where ventilation is not used
_NO_VENTILATION = {'ventilation_control': 0, 'ventilation_setpoint_offset': 0, 'min_outdoor_temp_offset': 7,
                   'max_wind_speed': 6}


@dataclass
class GenerationArguments:
    """Arguments of the output IDFs (the lists give one output IDF for each combination of their values)."""

    comfort_standard: List[int]
    category: List[Number]
    comfort_mode: List[Number]
    hvac_mode: List[int] = field(default_factory=lambda: [0])
    ventilation_control: List[int] = field(default_factory=lambda: [0])
    setpoint_accuracy: Number = 10000
    category_cooling_offset: Number = 0
    category_heating_offset: Number = 0
    custom_cooling_upper_limit: Number = 0
    custom_cooling_lower_limit: Number = 0
    custom_heating_upper_limit: Number = 0
    custom_heating_lower_limit: Number = 0
    custom_slope: Number = 0
    custom_intercept: Number = 0
    custom_cooling_offset: Number = 0
    custom_heating_offset: Number = 0
    cooling_season_start: int = 121
    cooling_season_end: int = 274
    opening_factor_max_temp_diff: Number = 6
    opening_factor_min_temp_diff: Number = 1
    min_opening_factor: Number = 0.25
    ventilation_setpoint_offset: List[float] = field(default_factory=lambda: [0.0])
    min_outdoor_temp_offset: List[float] = field(default_factory=lambda: [50.0])
    max_wind_speed: List[float] = field(default_factory=lambda: [50.0])
    setpoint_tolerance_start: Number = 0.1
    setpoint_tolerance_end: Number = 0.1
    setpoint_tolerance_step: Number = 0.1
    name_suffix: str = ''

    def __post_init__(self):
        self.comfort_standard = as_list(self.comfort_standard)
        self.category = as_list(self.category)
        self.comfort_mode = as_list(self.comfort_mode)
        self.hvac_mode = as_list(self.hvac_mode)
        self.ventilation_control = as_list(self.ventilation_control)
        self.ventilation_setpoint_offset = [float(v) for v in as_list(self.ventilation_setpoint_offset)]
        self.min_outdoor_temp_offset = [float(v) for v in as_list(self.min_outdoor_temp_offset)]
        self.max_wind_speed = [float(v) for v in as_list(self.max_wind_speed)]
        self.cooling_season_start = to_day_of_year(self.cooling_season_start, 'cooling_season_start')
        self.cooling_season_end = to_day_of_year(self.cooling_season_end, 'cooling_season_end')
        if self.name_suffix is None:
            self.name_suffix = ''

    @classmethod
    def air_conditioned(cls, **kwargs) -> 'GenerationArguments':
        """The arguments for full air-conditioning (no natural ventilation): HVACmode 0 only."""
        kwargs.update(hvac_mode=[0], ventilation_control=[0], ventilation_setpoint_offset=[0],
                      min_outdoor_temp_offset=[0], max_wind_speed=[0], opening_factor_max_temp_diff=1,
                      opening_factor_min_temp_diff=0, min_opening_factor=0)
        return cls(**kwargs)

    def tolerances(self) -> List[float]:
        """The setpoint tolerances, from setpoint_tolerance_start to setpoint_tolerance_end (both included) in steps
        of setpoint_tolerance_step.

        The values are those of ``numpy.arange``, but their number does not depend on the rounding of the floats
        (``numpy.arange(0.1, 0.3 + 0.1, 0.1)`` gives 0.4 too).
        """
        start, step = round(self.setpoint_tolerance_start, 2), round(self.setpoint_tolerance_step, 2)
        stop = round(self.setpoint_tolerance_end + self.setpoint_tolerance_step, 2)
        if step <= 0:
            raise ValueError(f'setpoint_tolerance_step must be greater than 0 '
                             f'(it is {self.setpoint_tolerance_step}).')
        count = math.ceil((stop - start) / step - 1e-6)
        if count <= 0:
            return []
        return np.arange(start, start + (count - 0.5) * step, step).tolist()


@dataclass(frozen=True)
class Combination:
    """The arguments of one output IDF. None is not applicable ('X' in the name of the file)."""

    comfort_standard: Optional[int]
    category: Optional[Number]
    comfort_mode: Optional[Number]
    hvac_mode: int
    ventilation_control: Optional[int]
    ventilation_setpoint_offset: Optional[float]
    min_outdoor_temp_offset: Optional[float]
    max_wind_speed: Optional[float]
    setpoint_tolerance: Optional[float]

    @property
    def is_pmv(self) -> bool:
        return self.comfort_standard is None


def _generates(comfort_standard: int, category: Number, comfort_mode: Number) -> bool:
    """The combinations of ComfStand, CAT and ComfMod that give an output IDF (as in accim 0.x)."""
    if comfort_standard in (1, 4, 5, 22):
        if comfort_standard in (1, 22) and category not in range(0, 4):
            return False
        if comfort_standard in (4, 5) and category not in (1, 2):
            return False
        if comfort_mode in _STATIC_MODES:
            return False
        return not (comfort_standard == 22 and comfort_mode != 0)
    if comfort_standard in (2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21) \
            and category not in range(80, 91, 10):
        return False
    if comfort_standard in (7, 8) and category not in range(80, 91, 5):
        return False
    if comfort_standard in (13, 14) and comfort_mode in (0, 1):
        return False
    if comfort_standard not in (13, 14) and comfort_mode in _STATIC_MODES:
        return False
    return not (comfort_standard == 21 and comfort_mode not in (2, 3))


def _ventilation(args: GenerationArguments, comfort_standard, category, comfort_mode) -> Iterator[Combination]:
    for hvac_mode in args.hvac_mode:
        if hvac_mode == 0:
            for tol in args.tolerances():
                yield Combination(comfort_standard, category, comfort_mode, hvac_mode, None, None, None, None, tol)
            continue
        for ventilation_control in args.ventilation_control:
            # Natural ventilation (HVACmode 1) only has the ventilation controls 0 and 1
            if hvac_mode == 1 and ventilation_control in (2, 3):
                continue
            for ventilation_setpoint_offset in args.ventilation_setpoint_offset:
                for min_outdoor_temp_offset in args.min_outdoor_temp_offset:
                    for max_wind_speed in args.max_wind_speed:
                        for tol in args.tolerances():
                            yield Combination(comfort_standard, category, comfort_mode, hvac_mode,
                                              ventilation_control, ventilation_setpoint_offset,
                                              min_outdoor_temp_offset, max_wind_speed, tol)


def combinations(args: GenerationArguments, setpoint_type: str = 'temperature') -> Iterator[Combination]:
    """The combinations of the arguments, in the order of the output IDFs.

    The combinations whose comfort standard has no setpoints for the comfort mode are skipped with a warning.
    """
    if setpoint_type == 'pmv':
        yield Combination(None, None, None, 0, None, None, None, None, None)
        return
    skipped = []
    for comfort_standard in args.comfort_standard:
        if comfort_standard == 0:
            yield from _ventilation(args, 0, None, None)
            continue
        if comfort_standard not in COMFORT_STANDARDS:
            continue
        for category in args.category:
            for comfort_mode in args.comfort_mode:
                if not _generates(comfort_standard, category, comfort_mode):
                    continue
                if not has_setpoints(comfort_standard, comfort_mode):
                    skipped.append((comfort_standard, comfort_mode))
                    continue
                yield from _ventilation(args, comfort_standard, category, comfort_mode)
    if skipped:
        warnings.warn(f'The combinations of (ComfStand, ComfMod) {sorted(set(skipped))} have no setpoints, so no '
                      f'output IDF has been generated for them.', UserWarning, stacklevel=3)


def _x(value) -> str:
    return 'X' if value is None else str(value)


def output_name(stem: str, combination: Combination, name_suffix: str = '') -> str:
    """The name of the output IDF of a combination, from the name of the input IDF without '.idf'."""
    suffix = '[NS_X' if name_suffix == '' else f'[NS_{name_suffix}'
    if combination.is_pmv:
        return f'{stem}[CS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X{suffix}.idf'
    c = combination
    return (f'{stem}[CS_{COMFORT_STANDARDS[c.comfort_standard].label}[CA_{_x(c.category)}[CM_{_x(c.comfort_mode)}'
            f'[HM_{c.hvac_mode}[VC_{_x(c.ventilation_control)}[VO_{_x(c.ventilation_setpoint_offset)}'
            f'[MT_{_x(c.min_outdoor_temp_offset)}[MW_{_x(c.max_wind_speed)}'
            f'[AT_{round(c.setpoint_tolerance, 2)}{suffix}.idf')


def zone_input_arguments(args: GenerationArguments, combination: Combination,
                         zone_arguments: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """The arguments of a zone in the output IDF of a combination, as those of
    :func:`accim.sim.accis.modify_accis`.

    The arguments of the combination, or those of the zone in ``zone_arguments``. With ESP CTE (ComfStand 0), the
    category is 1 and the comfort mode 0; with HVACmode 0, the ventilation arguments are those of no ventilation.
    The ventilation arguments that the combination does not have (HVACmode 0) and the zone needs (HVACmode 1 or 2
    in ``zone_arguments``) are the first values of those of AddAccis.
    """
    a = args
    c = combination
    arguments = dict(
        comfort_standard=c.comfort_standard, category=c.category, comfort_mode=c.comfort_mode,
        hvac_mode=c.hvac_mode, ventilation_control=c.ventilation_control,
        ventilation_setpoint_offset=c.ventilation_setpoint_offset,
        min_outdoor_temp_offset=c.min_outdoor_temp_offset, max_wind_speed=c.max_wind_speed,
        setpoint_tolerance=c.setpoint_tolerance, cooling_season_start=a.cooling_season_start,
        cooling_season_end=a.cooling_season_end, category_cooling_offset=a.category_cooling_offset,
        category_heating_offset=a.category_heating_offset, setpoint_accuracy=a.setpoint_accuracy,
        custom_slope=a.custom_slope, custom_intercept=a.custom_intercept, custom_cooling_offset=a.custom_cooling_offset,
        custom_heating_offset=a.custom_heating_offset, custom_cooling_upper_limit=a.custom_cooling_upper_limit,
        custom_cooling_lower_limit=a.custom_cooling_lower_limit,
        custom_heating_upper_limit=a.custom_heating_upper_limit,
        custom_heating_lower_limit=a.custom_heating_lower_limit,
        opening_factor_max_temp_diff=a.opening_factor_max_temp_diff,
        opening_factor_min_temp_diff=a.opening_factor_min_temp_diff, min_opening_factor=a.min_opening_factor,
    )
    arguments.update(zone_arguments or {})
    if arguments['comfort_standard'] == 0:
        arguments.update(category=1, comfort_mode=0)
    if arguments['hvac_mode'] == 0:
        arguments.update(_NO_VENTILATION)
    else:
        for name in _NO_VENTILATION:
            if arguments[name] is None:
                arguments[name] = getattr(args, name)[0]
    return arguments


def zone_arguments_errors(arguments: Mapping[str, Any], mixed_mode: bool) -> List[str]:
    """The reasons why the arguments of a zone (see :func:`zone_input_arguments`) give no setpoints (empty if they
    are valid)."""
    errors = []
    comfort_standard = arguments['comfort_standard']
    category, comfort_mode = arguments['category'], arguments['comfort_mode']
    if comfort_standard not in COMFORT_STANDARDS:
        errors.append(f'comfort_standard {comfort_standard!r} is not a comfort standard '
                      f'(valid: {list(COMFORT_STANDARDS)})')
    elif comfort_standard != 0:
        categories = COMFORT_STANDARDS[comfort_standard].categories
        if categories and category not in categories:
            errors.append(f'category {category!r} is not a category of comfort_standard {comfort_standard} '
                          f'(valid: {list(categories)})')
        if not has_setpoints(comfort_standard, comfort_mode):
            errors.append(f'comfort_standard {comfort_standard} has no setpoints with comfort_mode {comfort_mode!r}')
    hvac_mode = arguments['hvac_mode']
    if hvac_mode not in (0, 1, 2) or (hvac_mode != 0 and not mixed_mode):
        valid = [0, 1, 2] if mixed_mode else [0]
        errors.append(f'hvac_mode {hvac_mode!r} is not valid with this script type (valid: {valid})')
    elif arguments['ventilation_control'] not in ((0, 1) if hvac_mode == 1 else (0, 1, 2, 3)):
        errors.append(f"ventilation_control {arguments['ventilation_control']!r} is not valid with "
                      f"hvac_mode {hvac_mode}")
    return errors


def set_combination(idf, args: GenerationArguments, combination: Combination,
                    zone_arguments: Optional[Mapping[str, Mapping[str, Any]]] = None) -> None:
    """Set the arguments of the output IDF of a combination in the programs SetInputData_<zone> of a model.

    :param idf: The model, with the EMS programs of the ACCIS.
    :param args: The arguments of the output IDFs.
    :param combination: The combination of the output IDF.
    :param zone_arguments: The arguments of some zones, which are the same in all the output IDFs,
        ``{zone name in the EMS objects: {argument: value}}`` (see :func:`zone_input_arguments`).
    """
    # The models in mixed mode have the program SetVST, and the inputs of the venting opening factor
    mixed_mode = idf.getobject('EnergyManagementSystem:Program', 'SetVST') is not None
    for zone, program in input_programs(idf).items():
        if combination.is_pmv:
            # The Fanger thermostats control the zones: the inputs keep their default values, except HVACmode
            arguments = dict(hvac_mode=0, opening_factor_max_temp_diff=args.opening_factor_max_temp_diff,
                             opening_factor_min_temp_diff=args.opening_factor_min_temp_diff,
                             min_opening_factor=args.min_opening_factor)
        else:
            arguments = zone_input_arguments(args, combination, (zone_arguments or {}).get(zone))
        set_program_lines(program, input_lines(input_values(arguments), mixed_mode))


class OutputIdfs(Mapping):
    """The output IDFs by file name. Each one is read (as an IDF object of eppy) the first time it is used.

    :param paths: The path of each output IDF, by file name.
    :param idf_class: The class of the IDF objects (eppy's IDF or a subclass, with the IDD already set).
    """

    def __init__(self, paths: Dict[str, str], idf_class):
        self.paths = dict(paths)
        self._idf_class = idf_class
        self._idfs: Dict[str, object] = {}

    def __getitem__(self, name: str):
        if name not in self._idfs:
            self._idfs[name] = self._idf_class(self.paths[name])
        return self._idfs[name]

    def __iter__(self):
        return iter(self.paths)

    def __len__(self) -> int:
        return len(self.paths)

    def __repr__(self) -> str:
        return f'OutputIdfs({self.paths!r})'
