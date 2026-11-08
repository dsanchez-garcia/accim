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
rewrite the lines that set the adaptive coefficients and the PMV setpoints,
found by the names of their variables, so that the PMV setpoints can be changed
in the models with the setpoints of any index derived from the PMV
(:mod:`accim.sim.pmv_index`).

Usage
-----
Use these helpers as BESOS parameter modifiers when building parametric or
optimisation problems for APMV controls.

Examples
--------
change_adaptive_coeff_all_zones(idf, 0.3)
change_pmv_setpoint_all_zones(idf, 0.5)
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
