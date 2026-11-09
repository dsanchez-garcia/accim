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

"""Helpers to modify APMV EMS program lines across all zones.

These functions locate ``set_zone_input_data_*`` EMS programs in an IDF and
rewrite the lines that set the adaptive coefficients, the expectancy factors
and the PMV setpoints, found by the names of their variables, so that the PMV
setpoints can be changed in the models with the setpoints of any index derived
from the PMV (:mod:`accim.sim.pmv_index`). Since accim 1.2.0, they also set the
inputs of the PMV of the occupants (the clothing insulation, the activity level
and the air velocity, with :func:`accim.sim.apmv.set_pmv_input_parameters`).

Usage
-----
Use these helpers as BESOS parameter modifiers when building parametric or
optimisation problems for APMV and ePMV controls.

Examples
--------
change_adaptive_coeff_all_zones(idf, 0.3)
change_pmv_setpoint_all_zones(idf, 0.5)
change_expectancy_factor_all_zones(idf, 0.7)
change_clothing_insulation_all_zones(idf, 0.5)
"""

import re

import besos


def _get_apmv_input_programs_by_target(idf: besos.IDF_class):
    """Build a ``{suffix: program}`` mapping for APMV input EMS programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object containing EMS Program objects.

    Returns
    -------
    dict[str, Any]
        Mapping from target suffix to EMS program object.

    Usage
    -----
    Used by modifier functions to access a program directly by zone suffix.

    Examples
    --------
    programs = _get_apmv_input_programs_by_target(idf)
    """
    prefix = 'set_zone_input_data_'
    programs = {}
    for program in idf.idfobjects['EnergyManagementSystem:Program']:
        name = getattr(program, 'Name', '')
        if name.lower().startswith(prefix):
            programs[name[len(prefix):]] = program
    return programs


def _set_input_line(program, variable: str, value) -> None:
    """Replace the line ``set <variable> = ...`` of a ``set_zone_input_data_*`` program.

    Parameters
    ----------
    program : Any
        EMS program object (eppy).
    variable : str
        Name of the EMS variable (e.g. ``adap_coeff_cooling_Block1_Zone1``).
    value : float
        Value assigned to the variable.

    Raises
    ------
    ValueError
        If the program has no line that sets the variable (for instance, the
        adaptive coefficients of a model without aPMV setpoints).
    """
    pattern = re.compile(rf'^\s*set\s+{re.escape(variable)}\s*=', re.IGNORECASE)
    for number, line in enumerate(program.fieldvalues[2:], start=1):
        if pattern.match(str(line)):
            program[f'Program_Line_{number}'] = f'set {variable} = {value}'
            return
    raise ValueError(f'The EMS program {program.Name} has no line "set {variable} = ...": the model does not have '
                     f'the setpoints that this parameter changes.')


def change_adaptive_coeff_all_zones(idf: besos.IDF_class, value: float):
    """Set both adaptive coefficients for all detected APMV zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object where EMS program lines will be updated.
    value : float
        Value assigned to ``adap_coeff_cooling_*`` and
        ``adap_coeff_heating_*``.

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use when cooling and heating adaptive coefficients must be synchronized
    across all zones.

    Examples
    --------
    change_adaptive_coeff_all_zones(idf, 0.4)
    """
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'adap_coeff_cooling_{zonename}', value)
        _set_input_line(program, f'adap_coeff_heating_{zonename}', value)


def change_adaptive_coeff_cooling_all_zones(idf: besos.IDF_class, value: float):
    """Set cooling adaptive coefficient for all detected APMV zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object where EMS program lines will be updated.
    value : float
        Value assigned to ``adap_coeff_cooling_*`` lines.

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use when only cooling adaptation should be tuned globally.

    Examples
    --------
    change_adaptive_coeff_cooling_all_zones(idf, 0.35)
    """
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'adap_coeff_cooling_{zonename}', value)


def change_adaptive_coeff_heating_all_zones(idf: besos.IDF_class, value: float):
    """Set heating adaptive coefficient for all detected APMV zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object where EMS program lines will be updated.
    value : float
        Value assigned to ``adap_coeff_heating_*`` lines.

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use when only heating adaptation should be tuned globally.

    Examples
    --------
    change_adaptive_coeff_heating_all_zones(idf, 0.25)
    """
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'adap_coeff_heating_{zonename}', value)


def change_pmv_setpoint_all_zones(idf: besos.IDF_class, value: float):
    """Set symmetric PMV cooling/heating setpoints for all zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object where EMS program lines will be updated.
    value : float
        Absolute PMV target. Cooling setpoint receives ``value`` and heating
        setpoint receives ``-value``.

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use when PMV setpoints should remain symmetric around zero across zones.

    Examples
    --------
    change_pmv_setpoint_all_zones(idf, 0.6)
    """
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'pmv_cooling_sp_{zonename}', value)
        _set_input_line(program, f'pmv_heating_sp_{zonename}', -value)


def change_pmv_cooling_setpoint_all_zones(idf: besos.IDF_class, value: float):
    """Set PMV cooling setpoint for all detected APMV zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object where EMS program lines will be updated.
    value : float
        Value assigned to ``pmv_cooling_sp_*`` lines.

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use when only cooling PMV thresholds should be changed.

    Examples
    --------
    change_pmv_cooling_setpoint_all_zones(idf, 0.7)
    """
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'pmv_cooling_sp_{zonename}', value)


def change_pmv_heating_setpoint_all_zones(idf: besos.IDF_class, value: float):
    """Set PMV heating setpoint for all detected APMV zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object where EMS program lines will be updated.
    value : float
        Value assigned to ``pmv_heating_sp_*`` lines.

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use when only heating PMV thresholds should be changed.

    Examples
    --------
    change_pmv_heating_setpoint_all_zones(idf, -0.7)
    """
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'pmv_heating_sp_{zonename}', value)


def change_expectancy_factor_all_zones(idf: besos.IDF_class, value: float):
    """Set the expectancy factor of the ePMV setpoints for all detected zone programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object with the ePMV setpoints (:func:`accim.sim.apmv.apply_epmv_setpoints`), whose EMS program lines
        will be updated.
    value : float
        Value assigned to ``expectancy_factor_*`` lines, between 0.5 and 1 (Fanger and Toftum, 2002).

    Returns
    -------
    None
        The IDF is modified in place.

    Raises
    ------
    ValueError
        If the value is not between 0.5 and 1, or the model has no ePMV setpoints.

    Usage
    -----
    Use as the modifier of the parameter ``expectancy_factor`` of the parameters type ``'epmv setpoints'``.

    Examples
    --------
    change_expectancy_factor_all_zones(idf, 0.7)
    """
    from accim.constants import EPMV_EXPECTANCY_RANGES

    low = min(limits[0] for limits in EPMV_EXPECTANCY_RANGES.values())
    high = max(limits[1] for limits in EPMV_EXPECTANCY_RANGES.values())
    if not low <= float(value) <= high:
        raise ValueError(f'The expectancy factor must be between {low} and {high}, not {value}.')
    for zonename, program in _get_apmv_input_programs_by_target(idf).items():
        _set_input_line(program, f'expectancy_factor_{zonename}', value)


_PMV_INPUT_UNITS = {'activity_level': 'W/person', 'clothing_insulation': 'clo', 'air_velocity': 'm/s'}


def _check_pmv_input(name: str, value) -> float:
    """Check the value of a parameter of the inputs of the PMV (a number), and warn if it is outside the range in which
    ISO 7730:2025 (section 4) uses the PMV (:data:`accim.constants.PMV_INPUT_RANGES`), or, for the clothing
    insulation, above the limit of ASHRAE 55-2020 (:data:`accim.constants.ASHRAE55_MAX_CLOTHING_INSULATION`).

    :raises ValueError: If the value is not a number, or is negative.
    """
    import numbers
    import warnings

    from accim.constants import ASHRAE55_MAX_CLOTHING_INSULATION, PMV_INPUT_RANGES

    if isinstance(value, bool) or not isinstance(value, numbers.Real) or value < 0:
        raise ValueError(f'{name} must be a number of at least 0, not {value!r}.')
    low, high = PMV_INPUT_RANGES[name]
    units = _PMV_INPUT_UNITS[name]
    if not low <= value <= high:
        warnings.warn(f'{name} {value} {units} is outside {round(low, 1)} to {round(high, 1)} {units}, the range in '
                      f'which ISO 7730:2025 (section 4) uses the PMV.')
    elif name == 'clothing_insulation' and value > ASHRAE55_MAX_CLOTHING_INSULATION:
        warnings.warn(f'clothing_insulation {value} clo is above {ASHRAE55_MAX_CLOTHING_INSULATION} clo, with which '
                      f'ASHRAE 55-2020 does not use the PMV.')
    return float(value)


def change_clothing_insulation_all_zones(idf: besos.IDF_class, value: float):
    """Set the clothing insulation of all the People objects (the schedules ``Sch_Clo_<people>`` of
    :func:`accim.sim.apmv.set_pmv_input_parameters`).

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object with the setpoints based on the PMV, whose People objects will be updated.
    value : float
        The clothing insulation (clo). It warns outside 0 to 2 clo (ISO 7730:2025, section 4) and above 1.5 clo
        (ASHRAE 55-2020).

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use as the modifier of the parameter ``clothing_insulation`` of the parameters types ``'apmv setpoints'`` and
    ``'epmv setpoints'``.

    Examples
    --------
    change_clothing_insulation_all_zones(idf, 0.5)
    """
    from accim.sim.apmv import set_pmv_input_parameters

    set_pmv_input_parameters(idf, clothing_insulation=_check_pmv_input('clothing_insulation', value), verbose=False)


def change_activity_level_all_zones(idf: besos.IDF_class, value: float):
    """Set the activity level of all the People objects (the schedules ``Sch_Act_<people>`` of
    :func:`accim.sim.apmv.set_pmv_input_parameters`).

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object with the setpoints based on the PMV, whose People objects will be updated (not those with the
        metabolic correction of the ePMV, whose activity level is set before the setpoints).
    value : float
        The activity level (W/person, as in EnergyPlus). It warns outside 82.8 to 417.6 W/person: the metabolic rates
        of 46 to 232 W/m² (0.8 to 4 met) of ISO 7730:2025 (section 4), with a body surface area of 1.8 m².

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use as the modifier of the parameter ``activity_level`` of the parameters types ``'apmv setpoints'`` and
    ``'epmv setpoints'``.

    Examples
    --------
    change_activity_level_all_zones(idf, 126)
    """
    from accim.sim.apmv import set_pmv_input_parameters

    set_pmv_input_parameters(idf, activity_level=_check_pmv_input('activity_level', value), verbose=False)


def change_air_velocity_all_zones(idf: besos.IDF_class, value: float):
    """Set the air velocity of all the People objects (the schedules ``Sch_Vel_<people>`` of
    :func:`accim.sim.apmv.set_pmv_input_parameters`).

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object with the setpoints based on the PMV, whose People objects will be updated.
    value : float
        The air velocity (m/s). It warns outside 0 to 1 m/s (ISO 7730:2025, section 4).

    Returns
    -------
    None
        The IDF is modified in place.

    Usage
    -----
    Use as the modifier of the parameter ``air_velocity`` of the parameters types ``'apmv setpoints'`` and
    ``'epmv setpoints'``.

    Examples
    --------
    change_air_velocity_all_zones(idf, 0.2)
    """
    from accim.sim.apmv import set_pmv_input_parameters

    set_pmv_input_parameters(idf, air_velocity=_check_pmv_input('air_velocity', value), verbose=False)
