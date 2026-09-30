"""Independent, occupied comfort metrics for already prepared EnergyPlus models.

These are reporting-only EMS objects: no thermostat, schedule, actuator or
control program is changed. Install AFTER ACCIS/aPMV, before output discovery.
This module neither writes an IDF to disk nor invokes EnergyPlus.
"""

from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any, Sequence, cast


RMOT_VARIABLE = 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature'
PMV_VARIABLE = 'Zone Thermal Comfort Fanger Model PMV'
REPORTING_POINT = 'EndOfZoneTimestepBeforeZoneReporting'
SUPPORTED_METRICS = ('fixed_en', 'fixed_pmv')

__all__ = ['add_comfort_metrics']


def _objects(building, object_type):
    try:
        return list(building.idfobjects[object_type.upper()])
    except KeyError:
        return []


def _token(value):
    return str(value).strip().casefold()


def _fields(obj):
    names = getattr(obj, 'fieldnames', None)
    if names is None:
        names = vars(obj)
    return {name: getattr(obj, name, '') for name in names
            if name not in {'key', 'fieldnames'} and str(getattr(obj, name, '')).strip()}


def _resolve_metric_targets(building, metrics):
    # Reuse exactly the same People/Space key expansion as ACCIS and aPMV.
    # Resolving each People separately prevents silently missing one unresolved
    # People while another expands into several targets.
    from accim.sim.apmv_setpoints import _resolve_targets

    people = _objects(building, 'People')
    zones = {_token(o.Name) for o in _objects(building, 'Zone')}
    containers = set(zones)
    for key in ('Space', 'SpaceList', 'ZoneList'):
        containers.update(_token(o.Name) for o in _objects(building, key))
    if not people or not zones:
        raise ValueError('Comfort metrics require People objects and Zones.')
    targets, suffixes, sensor_keys = [], set(), set()
    for person in people:
        person_fields = _fields(person)
        reference = next((person_fields[field] for field in (
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name',
            'Zone_or_ZoneList_Name', 'Zone_Name',
        ) if field in person_fields), '')
        if _token(reference) not in containers:
            raise ValueError(f'Unresolved People container for {person.Name!r}: {reference!r}.')
        models = {_token(value) for field, value in person_fields.items()
                  if field.startswith('Thermal_Comfort_Model_') and field.endswith('_Type')}
        needed = {'AdaptiveCEN15251'} if 'fixed_en' in metrics else set()
        if 'fixed_pmv' in metrics:
            needed.add('Fanger')
        if not {_token(name) for name in needed}.issubset(models):
            raise ValueError(f'People {person.Name!r} must enable {sorted(needed)} before metrics are added.')
        mapping = dict(building.idfobjects)
        mapping['PEOPLE'] = [person]
        resolved = _resolve_targets(cast(Any, SimpleNamespace(idfobjects=mapping)))
        if not resolved:
            raise ValueError(f'People {person.Name!r} resolved to no EMS targets.')
        for target in resolved:
            suffix, sensor_key = target['ems_suffix'], target['sensor_key']
            if _token(target['zone_name']) not in zones:
                raise ValueError(f'Metric target refers to an unknown zone: {target}.')
            if not re.fullmatch(r'[A-Za-z0-9_]+', suffix) or not sensor_key.strip():
                raise ValueError(f'Invalid EMS target: {target}.')
            if _token(suffix) in suffixes or _token(sensor_key) in sensor_keys:
                raise ValueError(f'Ambiguous/sanitized duplicate comfort target: {target}.')
            suffixes.add(_token(suffix))
            sensor_keys.add(_token(sensor_key))
            targets.append(dict(target))
    return targets


def _plan_objects(target, prefix, metrics):
    base = f"{prefix}_{target['ems_suffix']}"
    if len(base) + len('_FixedPMVHours') > 100:
        raise ValueError(f'EMS metric identifier exceeds 100 characters: {base!r}.')
    plan, outputs = [], []

    def add(kind, **fields):
        plan.append((kind, fields))

    def sensor(name, key, variable):
        add('EnergyManagementSystem:Sensor', Name=name,
            OutputVariable_or_OutputMeter_Index_Key_Name=key,
            OutputVariable_or_OutputMeter_Name=variable)

    def output(role, suffix, label, units):
        variable = f'{base}_{suffix}'
        name = f"{prefix} {label}_{target['ems_suffix']}"
        add('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name=variable)
        add('EnergyManagementSystem:OutputVariable', Name=name,
            EMS_Variable_Name=variable, Type_of_Data_in_Variable='Summed',
            Update_Frequency='ZoneTimestep', Units=units)
        outputs.append(dict(metric=role, variable_name=name, key_value='EMS',
                            units=units, aggregation='sum', ems_variable=variable,
                            zone_name=target['zone_name'], sensor_key=target['sensor_key'],
                            ems_suffix=target['ems_suffix']))
        return variable

    def program(suffix, lines):
        name = f'{base}_{suffix}'
        add('EnergyManagementSystem:Program', Name=name,
            **{f'Program_Line_{i}': line for i, line in enumerate(lines, 1)})
        add('EnergyManagementSystem:ProgramCallingManager', Name=f'{name}_Manager',
            EnergyPlus_Model_Calling_Point=REPORTING_POINT, Program_Name_1=name)

    n = f'{base}_N'
    sensor(n, target['sensor_key'], 'People Occupant Count')
    occupied = output('occupied', 'Occ', 'Occupied Hours', 'hr')
    gate = f'IF (WarmupFlag == 0) && ({n} > 0)'
    program('Occupancy', [f'SET {occupied} = 0', gate,
                          f'SET {occupied} = ZoneTimeStep', 'ENDIF'])

    if 'fixed_en' in metrics:
        to, rmot = f'{base}_To', f'{base}_RMOT'
        r, neutral, lower, upper = (f'{base}_{name}' for name in ('R', 'Neutral', 'Lower', 'Upper'))
        sensor(to, target['zone_name'], 'Zone Operative Temperature')
        sensor(rmot, target['sensor_key'], RMOT_VARIABLE)
        dh = output('fixed_en', 'DH', 'EN16798 CatII Occupied Degree Hours', 'C-hr')
        program('EN', [
            f'SET {dh} = 0', gate,
            f'SET {r} = @Min {rmot} 30', f'SET {r} = @Max {r} 10',
            f'SET {neutral} = 0.33 * {r} + 18.8',
            f'SET {lower} = {neutral} - 4', f'SET {upper} = {neutral} + 3',
            f'IF {to} > {upper}', f'SET {dh} = ({to} - {upper}) * ZoneTimeStep',
            f'ELSEIF {to} < {lower}', f'SET {dh} = ({lower} - {to}) * ZoneTimeStep',
            'ENDIF', 'ENDIF',
        ])
    if 'fixed_pmv' in metrics:
        pmv, absolute = f'{base}_PMV', f'{base}_AbsValue'
        sensor(pmv, target['sensor_key'], PMV_VARIABLE)
        integral = output('pmv_integral', 'AbsPMV', 'Occupied Absolute Fanger PMV Integral', 'hr')
        hours = output('fixed_pmv_hours', 'FixedPMVHours', 'Occupied Fixed PMV Discomfort Hours', 'hr')
        program('PMV', [
            f'SET {integral} = 0', f'SET {hours} = 0', gate,
            f'SET {absolute} = @Abs {pmv}',
            f'SET {integral} = {absolute} * ZoneTimeStep',
            f'IF {absolute} > 0.5', f'SET {hours} = ZoneTimeStep', 'ENDIF', 'ENDIF',
        ])
    return plan, outputs


def _preflight_objects(building, plan):
    """Check ALL collisions before adding anything; not a simulation preflight."""
    pending = []
    symbol_types = (
        'EnergyManagementSystem:Sensor', 'EnergyManagementSystem:Actuator',
        'EnergyManagementSystem:InternalVariable', 'EnergyManagementSystem:TrendVariable',
        'EnergyManagementSystem:CurveOrTableIndexVariable',
    )
    existing_symbols = {}
    for kind in symbol_types:
        for obj in _objects(building, kind):
            existing_symbols.setdefault(_token(obj.Name), []).append((kind, obj))
    for obj in _objects(building, 'EnergyManagementSystem:GlobalVariable'):
        for field, value in _fields(obj).items():
            if field.startswith('Erl_Variable_') and field.endswith('_Name'):
                existing_symbols.setdefault(_token(value), []).append(('EnergyManagementSystem:GlobalVariable', obj))

    programs = {fields['Name']: fields for kind, fields in plan
                if kind == 'EnergyManagementSystem:Program'}
    existing_programs = {_token(obj.Name) for obj in _objects(building, 'EnergyManagementSystem:Program')}
    planned_globals = {_token(fields['Erl_Variable_1_Name']) for kind, fields in plan
                       if kind == 'EnergyManagementSystem:GlobalVariable'}
    # Scratch assignments must remain local. An unrelated global/sensor with
    # that name would otherwise bind silently and mutate controller state.
    for fields in programs.values():
        for field, line in fields.items():
            if not field.startswith('Program_Line_'):
                continue
            assignment = re.match(r'\s*SET\s+(\w+)\s*=', str(line), re.IGNORECASE)
            if assignment:
                symbol = _token(assignment.group(1))
                if symbol not in planned_globals and symbol in existing_symbols:
                    raise ValueError(f'EMS scratch-variable collision: {assignment.group(1)!r}.')
    for manager in _objects(building, 'EnergyManagementSystem:ProgramCallingManager'):
        for field, value in _fields(manager).items():
            if field.startswith('Program_Name_') and any(_token(value) == _token(name) for name in programs):
                if _token(manager.Name) != _token(f'{value}_Manager'):
                    raise ValueError(f'Metric program {value!r} has an unexpected calling manager.')

    for kind, fields in plan:
        is_global = kind == 'EnergyManagementSystem:GlobalVariable'
        name = fields['Erl_Variable_1_Name'] if is_global else fields['Name']
        if len(name) > 100:
            raise ValueError(f'EnergyPlus object/symbol name exceeds 100 characters: {name!r}.')
        if is_global or kind in symbol_types:
            same_symbol = existing_symbols.get(_token(name), [])
            if len(same_symbol) > 1 or any(other_kind != kind for other_kind, _ in same_symbol):
                raise ValueError(f'EMS symbol collision: {name!r}.')
            matches = [obj for _, obj in same_symbol]
        else:
            matches = [obj for obj in _objects(building, kind) if _token(obj.Name) == _token(name)]
        if len(matches) > 1:
            raise ValueError(f'Duplicate {kind} named {name!r}.')
        if matches:
            if is_global:
                owners = {program for program, definition in programs.items()
                          if any(re.search(r'\b' + re.escape(name) + r'\b', str(line), re.IGNORECASE)
                                 for field, line in definition.items() if field.startswith('Program_Line_'))}
                if not owners or not any(_token(owner) in existing_programs for owner in owners):
                    raise ValueError(f'Existing global {name!r} is not owned by matching metric programs.')
            else:
                actual = {_token(k): _token(v) for k, v in _fields(matches[0]).items()}
                wanted = {_token(k): _token(v) for k, v in fields.items() if str(v).strip()}
                if actual != wanted:
                    raise ValueError(f'Existing {kind} {name!r} has a different definition; use another prefix.')
        else:
            pending.append((kind, fields))
    return pending


def add_comfort_metrics(
    building: Any,
    *,
    metrics: Sequence[str] = ('fixed_en',),
    name_prefix: str = 'ACCIM_CM',
    dry_run: bool = False,
) -> dict:
    """Add independent occupied comfort-reporting EMS objects to an IDF.

    Parameters
    ----------
    building : IDF-like
        Already transformed ACCIS/aPMV model. People must enable
        ``AdaptiveCEN15251`` for ``fixed_en`` and ``Fanger`` for ``fixed_pmv``.
    metrics : sequence of str
        ``fixed_en``: degree-hours against EN Cat II, neutral=0.33*RMOT+18.8,
        upper +3/lower -4 K, RMOT clamped to [10, 30] C. Clamping is an explicit
        boundary-extension policy, not unrestricted EN adaptive applicability.
        ``fixed_pmv``: occupied integral of |Fanger PMV| and occupied hours
        with |PMV|>0.5. Divide the integral by occupied hours for the mean.
    name_prefix : str
        Separate namespace; repeated identical calls are idempotent. Conflicting
        names are rejected before mutation, not silently overwritten.
    dry_run : bool
        Validate prerequisites/collisions and return metadata without mutation.

    Returns
    -------
    dict
        ``outputs``: per-target reader specifications (metric, variable_name,
        key_value='EMS', units, aggregation and target metadata); ``targets``;
        counts ``added``, ``reused`` and ``would_add``. No readers, output
        requests or objectives are registered by this low-level function.

    Notes
    -----
    Occupied means People Occupant Count > 0; not a hard-coded office clock.
    Each increment is reset, multiplied by ZoneTimeStep and reported as Summed
    at EndOfZoneTimestepBeforeZoneReporting, excluding warmup. No extra duration
    factor is needed when summing hourly reports. Outputs remain per target:
    summing several zones gives zone-hours/zone-degree-hours, not building hours.
    Multiple legacy People in one zone with a colliding resolved suffix are
    rejected. Native aPMV counters and control logic are never modified.
    Apply AFTER all control transformations, which may otherwise erase globals
    or attach an additional predictor-time calling manager to these programs.
    Numerical/EMS validation with EnergyPlus is still required for a new model.
    """
    if isinstance(metrics, str):
        metrics = (metrics,)
    metrics = tuple(dict.fromkeys(metrics))
    if not metrics or not set(metrics).issubset(SUPPORTED_METRICS):
        raise ValueError(f'metrics must contain only {SUPPORTED_METRICS}.')
    if not isinstance(name_prefix, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name_prefix):
        raise ValueError('name_prefix must start with a letter and use ASCII letters, digits or underscores.')
    if not isinstance(dry_run, bool):
        raise TypeError('dry_run must be bool.')
    targets = _resolve_metric_targets(building, metrics)
    plan, outputs = [], []
    for target in targets:
        target_plan, target_outputs = _plan_objects(target, name_prefix, metrics)
        plan.extend(target_plan)
        outputs.extend(target_outputs)
    pending = _preflight_objects(building, plan)
    created = []
    if not dry_run:
        try:
            for kind, fields in pending:
                created.append(building.newidfobject(kind, **fields))
        except Exception:
            for obj in reversed(created):
                building.removeidfobject(obj)
            raise
    return dict(targets=targets, outputs=outputs, metrics=list(metrics),
                name_prefix=name_prefix, calling_point=REPORTING_POINT,
                added=len(created), reused=len(plan) - len(pending),
                would_add=len(pending), dry_run=dry_run)

