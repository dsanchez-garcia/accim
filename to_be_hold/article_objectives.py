# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Companion objectives module for the accim article experiments (Section 4).

This is a small, self-contained helper (NOT part of the installable ``accim``
package) used by ``exp_4_4_optimisation_custom_model_w-figs.py`` (imported)
and referenced in the docstring of ``exp_4_5_optimisation_apmv_v2_w-figs.py``
(as an alternative metric).

Rationale (paper Section 2.3): when optimising adaptive/aPMV setpoints, using
an ACCIS-based discomfort count as objective D is degenerate, because the
comfort reference (the setpoints) moves together with the very parameters
being optimised - the algorithm can "win" by widening the band instead of
truly improving comfort. Both metrics below are computed by an EMS program
injected directly into the IDF, against a FIXED reference that does not
depend on any optimised/sampled parameter:

- :func:`add_en16798_discomfort_ems`: annual EN 16798-1 adaptive-model
  discomfort degree-hours (zone-averaged operative temperature vs FIXED
  Category I/II/III limits, RMOT clamped to the standard's 10-30 C
  applicability range). This is the objective D used in exp_4.4.
- :func:`add_mean_abs_pmv_ems`: alternative metric mentioned in exp_4.5's
  docstring, based on the time-weighted mean of |PMV| (Fanger), independent
  from any optimised aPMV setpoint.

Both functions inject plain EnergyManagementSystem:* objects (Sensor,
GlobalVariable, Program, ProgramCallingManager, OutputVariable) following the
same eppy/besos patterns used internally by ``accim.sim.accim_Base_EMS`` and
``accim.sim.apmv_setpoints``, and reuse ``accim.sim.apmv_setpoints._resolve_targets``
to robustly identify the target zones (Zone/ZoneList/Space/SpaceList - aware).

Usage
-----
>>> from besos import eppy_funcs as ef
>>> from article_objectives import add_en16798_discomfort_ems, EN16798_DH_OUTPUT
>>> building = ef.get_building('model.idf')
>>> add_en16798_discomfort_ems(building, category=2)
'EN16798 CatII Discomfort Degree-Hours'
"""

from typing import Dict, List

from besos.IDF_class import IDF

from accim.sim.apmv_setpoints import _resolve_targets, _sanitize_ems_name

__all__ = [
    'EN16798_DH_OUTPUT',
    'MEAN_ABS_PMV_SUM_OUTPUT',
    'add_en16798_discomfort_ems',
    'add_mean_abs_pmv_ems',
]

# Output:Variable / EnergyManagementSystem:OutputVariable names (used as the
# 'variable_name' in accim's output DataFrames, with key_value='EMS').
EN16798_DH_OUTPUT = 'EN16798 CatII Discomfort Degree-Hours'
MEAN_ABS_PMV_SUM_OUTPUT = 'Mean Abs PMV Weighted Sum'

# EN 16798-1 adaptive comfort category offsets around the neutral temperature.
_CATEGORY_OFFSET = {1: 2.0, 2: 3.0, 3: 4.0}
# Applicability range of the EN 16798-1 / CEN 15251 adaptive method: outside
# this RMOT range the standard does not apply, so the limits are clamped at
# the boundary values (same clamping principle as accim's setAST_models.py,
# but here with the FIXED standard bounds, not the optimised AST parameters).
_RMOT_LOWER_BOUND = 10.0
_RMOT_UPPER_BOUND = 30.0


def _unique_target_zones(building: IDF) -> List[Dict[str, str]]:
    """Resolve People objects to target zones and drop duplicate zones.

    :param building: The BESOS/eppy IDF object.
    :return: A list of target dicts (see ``accim.sim.apmv_setpoints._resolve_targets``),
        one per unique zone name.
    """
    targets = _resolve_targets(building)
    if not targets:
        raise ValueError(
            'No People objects were found in the model; cannot resolve target '
            'zones for the fixed discomfort/PMV EMS metric.'
        )
    seen = set()
    unique_targets = []
    for target in targets:
        key = target['zone_name'].strip().upper()
        if key in seen:
            continue
        seen.add(key)
        unique_targets.append(target)
    return unique_targets


def _existing_names(building: IDF, object_type: str, name_field: str = 'Name') -> set:
    """Return the set of existing object names of a given EMS object type."""
    return {getattr(obj, name_field) for obj in building.idfobjects[object_type]}


def add_en16798_discomfort_ems(
        building: IDF,
        category: int = 2,
        occupied_only: bool = True,
        verbose_mode: bool = False,
) -> str:
    """Inject a FIXED, EMS-computed EN 16798-1 adaptive discomfort metric.

    Computes annual discomfort degree-hours of the zone-averaged operative
    temperature against FIXED EN 16798-1 Category I/II/III adaptive limits
    (offsets +-2/+-3/+-4 C around ``Tn = 0.33*RMOT + 18.8``, with RMOT
    clamped to the standard's 10-30 C applicability range). The reference is
    independent from any ACCIS/optimised setpoint, so it cannot be gamed by
    the parameters being optimised (see module docstring, paper Section 2.3).

    Reuses the global 'RMOT' EMS sensor already injected by ACCIS
    (``accim.sim.accim_Base_EMS.addEMSSensorsBase``) when present, and creates
    it otherwise. Injects its own per-zone Operative Temperature / Occupant
    Count sensors (own 'dh_' namespace) to stay independent from ACCIS's
    internal zone-suffix conventions.

    :param building: The BESOS/eppy IDF object (already transformed, i.e.
        after instantiating ``ParametricSimulation``/``OptimisationSimulation``).
    :param category: EN 16798-1 category, one of 1 (+-2 C), 2 (+-3 C, default)
        or 3 (+-4 C).
    :param occupied_only: If True (default), only accumulate degree-hours
        while at least one target zone is occupied (People Occupant Count > 0).
    :param verbose_mode: If True, prints a message for each object created.
    :return: The ``Name``/``variable_name`` of the injected
        ``EnergyManagementSystem:OutputVariable``, i.e. ``EN16798_DH_OUTPUT``.
        Request it for reporting with ``key_value='EMS'``.

    Usage
    -----
    >>> add_en16798_discomfort_ems(building, category=2)
    'EN16798 CatII Discomfort Degree-Hours'
    """
    if category not in _CATEGORY_OFFSET:
        raise ValueError(f'category must be one of {sorted(_CATEGORY_OFFSET)}; got {category!r}.')
    offset = _CATEGORY_OFFSET[category]

    zones = _unique_target_zones(building)
    sensor_names = _existing_names(building, 'EnergyManagementSystem:Sensor')

    # --- RMOT sensor: reuse ACCIS's global sensor if it already exists ---
    rmot_name = 'RMOT'
    if rmot_name not in sensor_names:
        building.newidfobject(
            'EnergyManagementSystem:Sensor',
            Name=rmot_name,
            OutputVariable_or_OutputMeter_Index_Key_Name=zones[0]['sensor_key'],
            OutputVariable_or_OutputMeter_Name=(
                'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature'
            ),
        )
        sensor_names.add(rmot_name)
        if verbose_mode:
            print(f'[article_objectives] Added - {rmot_name} Sensor')

    # --- per-zone Operative Temperature (+ Occupant Count) sensors ---
    op_t_vars: List[str] = []
    occ_vars: List[str] = []
    for target in zones:
        zone_name = target['zone_name']
        suffix = _sanitize_ems_name(zone_name)

        opt_sensor = f'dh_OpT_{suffix}'
        if opt_sensor not in sensor_names:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=opt_sensor,
                OutputVariable_or_OutputMeter_Index_Key_Name=zone_name,
                OutputVariable_or_OutputMeter_Name='Zone Operative Temperature',
            )
            sensor_names.add(opt_sensor)
            if verbose_mode:
                print(f'[article_objectives] Added - {opt_sensor} Sensor')
        op_t_vars.append(opt_sensor)

        if occupied_only:
            occ_sensor = f'dh_Occ_{suffix}'
            if occ_sensor not in sensor_names:
                building.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=occ_sensor,
                    # NOTE: 'People Occupant Count' is reported per People object,
                    # NOT per zone - the Index Key Name must be the People
                    # object's (sensor) key, never the raw zone name, or
                    # EnergyPlus aborts with 'Invalid ... Index Key Name' /
                    # 'Unique Key Name not found' (fatal EMS input error).
                    OutputVariable_or_OutputMeter_Index_Key_Name=target['sensor_key'],
                    OutputVariable_or_OutputMeter_Name='People Occupant Count',
                )
                sensor_names.add(occ_sensor)
                if verbose_mode:
                    print(f'[article_objectives] Added - {occ_sensor} Sensor')
            occ_vars.append(occ_sensor)

    # --- internal ERL variable ('set' target inside the Program below) ---
    internal_var = f'en16798_cat{category}_dh_incr'
    existing_globals = {
        gv.Erl_Variable_1_Name for gv in building.idfobjects['EnergyManagementSystem:GlobalVariable']
    }
    if internal_var not in existing_globals:
        building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=internal_var)
        if verbose_mode:
            print(f'[article_objectives] Added - GlobalVariable {internal_var}')

    # --- Program: FIXED EN16798-1 adaptive limits + zone-averaged OpT ---
    prog_name = f'compute_en16798_cat{category}_discomfort_dh'
    existing_programs = _existing_names(building, 'EnergyManagementSystem:Program')
    if prog_name not in existing_programs:
        opt_avg_expr = f"({' + '.join(op_t_vars)}) / {len(op_t_vars)}"

        lines: Dict[str, str] = {}
        line_no = 1

        def add_line(text: str) -> None:
            nonlocal line_no
            lines[f'Program_Line_{line_no}'] = text
            line_no += 1

        # 1. Clamp RMOT to the standard's applicability range [10, 30] C.
        add_line(f'if RMOT < {_RMOT_LOWER_BOUND}')
        add_line(f'set en16798_rmot_clamped_cat{category} = {_RMOT_LOWER_BOUND}')
        add_line(f'elseif RMOT > {_RMOT_UPPER_BOUND}')
        add_line(f'set en16798_rmot_clamped_cat{category} = {_RMOT_UPPER_BOUND}')
        add_line('else')
        add_line(f'set en16798_rmot_clamped_cat{category} = RMOT')
        add_line('endif')

        # 2. Neutral temperature and FIXED category limits.
        add_line(f'set en16798_tn_cat{category} = 0.33*en16798_rmot_clamped_cat{category} + 18.8')
        add_line(f'set en16798_upper_cat{category} = en16798_tn_cat{category} + {offset}')
        add_line(f'set en16798_lower_cat{category} = en16798_tn_cat{category} - {offset}')

        # 3. Zone-averaged operative temperature and exceedance (C).
        add_line(f'set en16798_opt_avg_cat{category} = {opt_avg_expr}')
        add_line(f'if en16798_opt_avg_cat{category} > en16798_upper_cat{category}')
        add_line(f'set en16798_exceed_cat{category} = en16798_opt_avg_cat{category} - en16798_upper_cat{category}')
        add_line(f'elseif en16798_opt_avg_cat{category} < en16798_lower_cat{category}')
        add_line(f'set en16798_exceed_cat{category} = en16798_lower_cat{category} - en16798_opt_avg_cat{category}')
        add_line('else')
        add_line(f'set en16798_exceed_cat{category} = 0')
        add_line('endif')

        # 4. Per-timestep degree-hours increment (Type='Summed' accumulates
        #    this into annual degree-hours when reported/reduced with sum).
        if occupied_only:
            occ_sum_expr = ' + '.join(occ_vars)
            add_line(f'set en16798_occ_sum_cat{category} = ({occ_sum_expr})')
            add_line(f'if en16798_occ_sum_cat{category} > 0')
            add_line(f'set {internal_var} = en16798_exceed_cat{category}*ZoneTimeStep')
            add_line('else')
            add_line(f'set {internal_var} = 0')
            add_line('endif')
        else:
            add_line(f'set {internal_var} = en16798_exceed_cat{category}*ZoneTimeStep')

        building.newidfobject('EnergyManagementSystem:Program', Name=prog_name, **lines)
        if verbose_mode:
            print(f'[article_objectives] Added Program: {prog_name}')

    # --- Calling manager ---
    existing_pcms = _existing_names(building, 'EnergyManagementSystem:ProgramCallingManager')
    if prog_name not in existing_pcms:
        building.newidfobject(
            'EnergyManagementSystem:ProgramCallingManager',
            Name=prog_name,
            EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
            Program_Name_1=prog_name,
        )
        if verbose_mode:
            print(f'[article_objectives] Added ProgramCallingManager: {prog_name}')

    # --- EMS Output Variable requested by the experiment scripts ---
    existing_outvars = _existing_names(building, 'EnergyManagementSystem:OutputVariable')
    if EN16798_DH_OUTPUT not in existing_outvars:
        building.newidfobject(
            'EnergyManagementSystem:OutputVariable',
            Name=EN16798_DH_OUTPUT,
            EMS_Variable_Name=internal_var,
            Type_of_Data_in_Variable='Summed',
            Update_Frequency='ZoneTimestep',
            Units='C-hr',
        )
        if verbose_mode:
            print(f'[article_objectives] Added EMS Output Variable: {EN16798_DH_OUTPUT}')

    return EN16798_DH_OUTPUT


def add_mean_abs_pmv_ems(building: IDF, verbose_mode: bool = False) -> str:
    """Inject a FIXED, EMS-computed mean |PMV| (Fanger) discomfort metric.

    Alternative external metric mentioned in exp_4.5's docstring caveat: the
    time-weighted sum of |PMV| (zone-averaged Fanger PMV) during occupied
    hours, independent from any optimised aPMV setpoint. Requires the
    People object(s) to have the Fanger thermal comfort model enabled (e.g.
    via ``accim.sim.apmv_setpoints.add_vrf_system``, which sets ``TempCtrl='pmv'``).

    The returned Output:Variable reports, per hour, the occupied-weighted
    |PMV| increment (Type='Summed'); dividing its annual sum by the annual
    sum of occupied hours yields the mean |PMV| over occupied hours.

    :param building: The BESOS/eppy IDF object (with Fanger comfort enabled).
    :param verbose_mode: If True, prints a message for each object created.
    :return: The ``Name``/``variable_name`` of the injected
        ``EnergyManagementSystem:OutputVariable``, i.e. ``MEAN_ABS_PMV_SUM_OUTPUT``.
        Request it for reporting with ``key_value='EMS'``.
    """
    zones = _unique_target_zones(building)
    sensor_names = _existing_names(building, 'EnergyManagementSystem:Sensor')

    pmv_vars: List[str] = []
    occ_vars: List[str] = []
    for target in zones:
        zone_name = target['zone_name']
        sensor_key = target['sensor_key']
        suffix = _sanitize_ems_name(zone_name)

        pmv_sensor = f'map_PMV_{suffix}'
        if pmv_sensor not in sensor_names:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=pmv_sensor,
                OutputVariable_or_OutputMeter_Index_Key_Name=sensor_key,
                OutputVariable_or_OutputMeter_Name='Zone Thermal Comfort Fanger Model PMV',
            )
            sensor_names.add(pmv_sensor)
            if verbose_mode:
                print(f'[article_objectives] Added - {pmv_sensor} Sensor')
        pmv_vars.append(pmv_sensor)

        occ_sensor = f'map_Occ_{suffix}'
        if occ_sensor not in sensor_names:
            building.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=occ_sensor,
                # Same fix as in add_en16798_discomfort_ems: 'People Occupant
                # Count' is keyed by the People object, not the zone name.
                OutputVariable_or_OutputMeter_Index_Key_Name=sensor_key,
                OutputVariable_or_OutputMeter_Name='People Occupant Count',
            )
            sensor_names.add(occ_sensor)
            if verbose_mode:
                print(f'[article_objectives] Added - {occ_sensor} Sensor')
        occ_vars.append(occ_sensor)

    internal_var = 'map_abs_pmv_incr'
    existing_globals = {
        gv.Erl_Variable_1_Name for gv in building.idfobjects['EnergyManagementSystem:GlobalVariable']
    }
    if internal_var not in existing_globals:
        building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=internal_var)
        if verbose_mode:
            print(f'[article_objectives] Added - GlobalVariable {internal_var}')

    prog_name = 'compute_mean_abs_pmv'
    existing_programs = _existing_names(building, 'EnergyManagementSystem:Program')
    if prog_name not in existing_programs:
        pmv_avg_expr = f"({' + '.join(pmv_vars)}) / {len(pmv_vars)}"
        occ_sum_expr = ' + '.join(occ_vars)
        building.newidfobject(
            'EnergyManagementSystem:Program',
            Name=prog_name,
            Program_Line_1=f'set map_pmv_avg = {pmv_avg_expr}',
            Program_Line_2='if map_pmv_avg < 0',
            Program_Line_3='set map_abs_pmv = 0 - map_pmv_avg',
            Program_Line_4='else',
            Program_Line_5='set map_abs_pmv = map_pmv_avg',
            Program_Line_6='endif',
            Program_Line_7=f'set map_occ_sum = ({occ_sum_expr})',
            Program_Line_8='if map_occ_sum > 0',
            Program_Line_9=f'set {internal_var} = map_abs_pmv*ZoneTimeStep',
            Program_Line_10='else',
            Program_Line_11=f'set {internal_var} = 0',
            Program_Line_12='endif',
        )
        if verbose_mode:
            print(f'[article_objectives] Added Program: {prog_name}')

    existing_pcms = _existing_names(building, 'EnergyManagementSystem:ProgramCallingManager')
    if prog_name not in existing_pcms:
        building.newidfobject(
            'EnergyManagementSystem:ProgramCallingManager',
            Name=prog_name,
            EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
            Program_Name_1=prog_name,
        )
        if verbose_mode:
            print(f'[article_objectives] Added ProgramCallingManager: {prog_name}')

    existing_outvars = _existing_names(building, 'EnergyManagementSystem:OutputVariable')
    if MEAN_ABS_PMV_SUM_OUTPUT not in existing_outvars:
        building.newidfobject(
            'EnergyManagementSystem:OutputVariable',
            Name=MEAN_ABS_PMV_SUM_OUTPUT,
            EMS_Variable_Name=internal_var,
            Type_of_Data_in_Variable='Summed',
            Update_Frequency='ZoneTimestep',
            Units='hr',
        )
        if verbose_mode:
            print(f'[article_objectives] Added EMS Output Variable: {MEAN_ABS_PMV_SUM_OUTPUT}')

    return MEAN_ABS_PMV_SUM_OUTPUT



