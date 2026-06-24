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
rewrite selected ``Program_Line_*`` assignments for adaptive coefficients and
PMV setpoints.

Usage
-----
Use these helpers as BESOS parameter modifiers when building parametric or
optimisation problems for APMV controls.

Examples
--------
change_adaptive_coeff_all_zones(idf, 0.3)
change_pmv_setpoint_all_zones(idf, 0.5)
"""

import besos


def _get_apmv_program_targets(idf: besos.IDF_class):
    """Collect target suffixes detected in ``set_zone_input_data_*`` programs.

    Parameters
    ----------
    idf : besos.IDF_class
        IDF object containing EMS Program objects.

    Returns
    -------
    list[str]
        Suffixes extracted from matching program names.

    Usage
    -----
    Used internally to iterate all APMV zone targets before modifying lines.

    Examples
    --------
    targets = _get_apmv_program_targets(idf)
    """
    prefix = 'set_zone_input_data_'
    targets = []
    for program in idf.idfobjects['EnergyManagementSystem:Program']:
        name = getattr(program, 'Name', '')
        if name.lower().startswith(prefix):
            targets.append(name[len(prefix):])
    return targets


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
    ppl_temp = _get_apmv_program_targets(idf)
    programs_by_target = _get_apmv_input_programs_by_target(idf)

    for zonename in ppl_temp:
        program = programs_by_target.get(zonename)
        if program is None:
            continue
        program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

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
    ppl_temp = _get_apmv_program_targets(idf)
    programs_by_target = _get_apmv_input_programs_by_target(idf)

    for zonename in ppl_temp:
        program = programs_by_target.get(zonename)
        if program is None:
            continue
        program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

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
    ppl_temp = _get_apmv_program_targets(idf)
    programs_by_target = _get_apmv_input_programs_by_target(idf)

    for zonename in ppl_temp:
        program = programs_by_target.get(zonename)
        if program is None:
            continue
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

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
    ppl_temp = _get_apmv_program_targets(idf)
    programs_by_target = _get_apmv_input_programs_by_target(idf)

    for zonename in ppl_temp:
        program = programs_by_target.get(zonename)
        if program is None:
            continue
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {-value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

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
    ppl_temp = _get_apmv_program_targets(idf)
    programs_by_target = _get_apmv_input_programs_by_target(idf)

    for zonename in ppl_temp:
        program = programs_by_target.get(zonename)
        if program is None:
            continue
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        # program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return

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
    ppl_temp = _get_apmv_program_targets(idf)
    programs_by_target = _get_apmv_input_programs_by_target(idf)

    for zonename in ppl_temp:
        program = programs_by_target.get(zonename)
        if program is None:
            continue
        # program.Program_Line_1 = f'set adap_coeff_cooling_{zonename} = {value}'
        # program.Program_Line_2 = f'set adap_coeff_heating_{zonename} = {value}'
        # program.Program_Line_3 = f'set pmv_cooling_sp_{zonename} = {value}'
        program.Program_Line_4 = f'set pmv_heating_sp_{zonename} = {value}'
        # program.Program_Line_5 = f'set tolerance_cooling_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_6 = f'set tolerance_cooling_sp_heating_season_{zonename} = {value}'
        # program.Program_Line_7 = f'set tolerance_heating_sp_cooling_season_{zonename} = {value}'
        # program.Program_Line_8 = f'set tolerance_heating_sp_heating_season_{zonename} = {value}'
    return
