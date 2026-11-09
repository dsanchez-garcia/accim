# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The columns of :class:`~accim.data.postprocessing.main.Table` of the outputs of the setpoints based on the PMV.

The setpoints of the indices derived from the PMV (:mod:`accim.sim.pmv_index`, applied by ``apply_apmv_setpoints``,
``apply_epmv_setpoints`` and ``apply_pmv_setpoints`` of :mod:`accim.sim.apmv`) report:

- for each occupied zone, the EMS outputs of :func:`accim.sim.pmv_index.zone_outputs`: the coefficient of the season
  (``Adaptive Coefficient_<zone>`` or ``Expectancy Factor_<zone>``), the index of the zone (``aPMV_<zone>``,
  ``ePMV_<zone>`` or ``PMV_<zone>``), the setpoints of the index with and without the tolerances
  (``<index> Heating Setpoint_<zone>``...) and the hour counters (``Comfortable Hours_<zone>``...);
- the PMV setpoints of the thermal comfort thermostats, the schedules ``PMV_H_SP_<zone>`` and ``PMV_C_SP_<zone>``;
- the mean air temperature of the zones (``Zone Mean Air Temperature``), with the other outputs of the comfort of the
  zones;
- with the metabolic correction of the ePMV, the factor and the corrected activity level (W/person) of each People
  object (:data:`accim.sim.pmv_index.METABOLIC_CORRECTION_OUTPUTS`), which Table attributes to the zone of the People
  object if it has one (:func:`metabolic_correction_suffixes`).

``Table`` averages them over time, except the hour counters (:func:`averaged_outputs`), keeps them with
``standard_outputs=True`` (:func:`standard_outputs`), does not take the corrected activity level for an energy
(:func:`power_outputs`), and names the outputs of the zones as its other outputs of the zones, ``<zone>_<name>``, with
block and building values (:func:`zone_columns`).
"""

from functools import lru_cache
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

__all__ = ['MEAN_AIR_TEMPERATURE', 'averaged_outputs', 'comfort_hours', 'metabolic_correction_columns',
           'metabolic_correction_suffixes', 'power_outputs', 'standard_outputs', 'zone_columns']

#: The mean air temperature of the zones, which the setpoints based on the PMV report
MEAN_AIR_TEMPERATURE = 'Zone Mean Air Temperature'
#: The names in Table of the schedules of the PMV setpoints of the thermostats (heating and cooling)
_THERMOSTAT_SETPOINTS = ('Thermostat Heating Setpoint (PMV)', 'Thermostat Cooling Setpoint (PMV)')


def _table_name(pmv_index, output: str, units: str) -> str:
    """The name in Table of an output of the zones of the setpoints of an index, or '' if it keeps its name: the index
    and its coefficient keep their names ('aPMV', 'Expectancy Factor'), the setpoints get the index as their units
    ('Heating Setpoint (aPMV)', 'Cooling Setpoint_No Tolerance (aPMV)'), so that no name contains another one, which
    the figures of Table would also take, and the hour counters their units ('Comfortable Hours (h)'). The PMV of the
    zone of the PMV setpoints and the occupied hours keep their names: <zone>_PMV is the PMV that EnergyPlus reports,
    and the occupied hours of the ACCIS have the same name (Occupied Hours_<zone>), which Table does not change."""
    name = pmv_index.name
    if output == name:
        return '' if name.upper() == 'PMV' else name
    if output == pmv_index.coefficient_output:
        return output
    for side in ('Heating', 'Cooling'):
        if output == f'{name} {side} Setpoint':
            return f'{side} Setpoint ({name})'
        if output == f'{name} {side} Setpoint No Tolerance':
            return f'{side} Setpoint_No Tolerance ({name})'
    if units == 'H' and output.upper() != 'OCCUPIED HOURS':
        return f'{output} (h)'
    return ''


@lru_cache(maxsize=None)
def _zone_outputs() -> Dict[str, Tuple[str, bool, bool]]:
    """The EMS outputs of the zones of the setpoints of all the indices, and those of the metabolic correction of the
    ePMV, which Table gives the suffix of the zone of their People object if it has one (see
    :func:`metabolic_correction_suffixes`): {output: (name in Table, or '' if it keeps its name; True if Table averages
    it over time; True if Table gives it block and building values)}."""
    from accim.sim.pmv_index import METABOLIC_CORRECTION_OUTPUTS, PMV_INDICES, zone_outputs

    outputs = {}
    for pmv_index in PMV_INDICES.values():
        for output, (_, units, data_type) in zone_outputs(pmv_index).items():
            name = _table_name(pmv_index, output, units)
            outputs[output] = (name, data_type == 'Averaged', bool(name))
    for output, units in METABOLIC_CORRECTION_OUTPUTS:
        outputs[output] = (f'{output} (W/person)' if units == 'W' else output, True, False)
    return outputs


def _other_outputs() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of the other outputs, which Table averages over time: the schedules of
    the PMV setpoints of the thermostats and the mean air temperature."""
    from accim.sim.pmv_index import PMV_SETPOINT_SCHEDULES

    return tuple(f'{schedule}_' for schedule in PMV_SETPOINT_SCHEDULES) + (MEAN_AIR_TEMPERATURE,)


def averaged_outputs() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of the outputs of the setpoints based on the PMV that Table averages
    over time (and over the occupant instances of a zone), as EnergyPlus names them in its CSV files: all but the hour
    counters, which it adds up (``frequency_agg_func``), such as ``'EMS:aPMV_'`` (``EMS:aPMV_Block1_Zone1 [](Hourly)``).
    """
    return (tuple(f'EMS:{output}_' for output, (_, averaged, _) in _zone_outputs().items() if averaged)
            + _other_outputs())


def standard_outputs() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of the outputs of the setpoints based on the PMV, which Table keeps
    with ``standard_outputs=True``."""
    return tuple(f'EMS:{output}_' for output in _zone_outputs()) + _other_outputs()


def power_outputs() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of the outputs in W of the setpoints based on the PMV that are not
    energy rates, which Table does not convert into energy (Wh, kWh, per m2): the corrected activity level
    (W/person)."""
    from accim.sim.pmv_index import METABOLIC_CORRECTION_OUTPUTS

    return tuple(f'EMS:{output}_' for output, units in METABOLIC_CORRECTION_OUTPUTS if units == 'W')


def comfort_hours() -> Tuple[str, ...]:
    """The names in Table of the hour counters of the setpoints based on the PMV (``'Comfortable Hours (h)'``...), which
    ``Table.format_table(type_of_table='comfort hours')`` takes with those of the ACCIS."""
    return tuple(name for name, _, _ in _zone_outputs().values() if name.endswith(' (h)'))


def metabolic_correction_suffixes(targets: Sequence[Mapping]) -> Dict[str, str]:
    """
    The new suffixes of the outputs of the metabolic correction of the ePMV, which are of each People object
    (``Metabolic Correction Factor_<People>``, with the name of the People object as an EMS name): the EMS suffix of
    the zone of the People object, if it is the People object of one zone (target) only, so that Table names them after
    the zone, and averages them in the zones with several People objects. Those of the People objects of several zones,
    such as a People object assigned to a SpaceList of the spaces of several zones, keep their names.

    :param targets: The targets of the EMS of accim (:func:`accim.sim.targets.resolve_targets`, as dictionaries).
    :return: A dictionary {name of the People object as an EMS name: EMS suffix of its zone}, in capitals.
    """
    from accim.sim.targets import sanitize_ems_name

    zones = {}
    for target in targets:
        for people in target['people_names']:
            zones.setdefault(sanitize_ems_name(people).upper(), set()).add(target['ems_suffix'].upper())
    return {people: next(iter(suffixes)) for people, suffixes in zones.items() if len(suffixes) == 1}


def metabolic_correction_columns() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of the outputs of the metabolic correction, in capitals
    (``'EMS:METABOLIC CORRECTION FACTOR_'``...)."""
    from accim.sim.pmv_index import METABOLIC_CORRECTION_OUTPUTS

    return tuple(f'EMS:{output.upper()}_' for output, _ in METABOLIC_CORRECTION_OUTPUTS)


def zone_columns(columns: Iterable[str], zone_of: Callable[[str], Optional[str]],
                 zones: Sequence[str]) -> Dict[str, Tuple[str, str, bool]]:
    """
    The columns of the outputs of the zones of the setpoints based on the PMV that Table renames, once it has given the
    columns the names of its zones: ``EMS:<output>_<zone>... [<units>](<frequency>)``, whose output is one of
    :func:`accim.sim.pmv_index.zone_outputs` or of the metabolic correction (exactly:
    ``EMS:COMFORTABLE HOURS_NO APPLICABILITY_<zone>``, of the ACCIS, is not ``Comfortable Hours``) and whose name
    continues with the name of the zone (in the zones named after their space, the name of the People object follows),
    and ``<PMV_H_SP or PMV_C_SP>_<zone>:Schedule Value``.

    :param columns: The names of the columns of the table (in capitals, as Table reads them, or not).
    :param zone_of: The zone of a column (the function of Table), or None.
    :param zones: The occupied zones, as Table names them.
    :return: A dictionary {column: (zone, name in Table, True if Table gives it block and building values)}, whose
        columns Table renames ``<zone>_<name in Table>``: ``EMS:APMV_BLOCK1:ZONE1 [](HOURLY)`` is
        ``Block1:Zone1_aPMV``. The schedules of the thermostats and the outputs of the metabolic correction have no
        block and building values.
    """
    from accim.sim.pmv_index import PMV_SETPOINT_SCHEDULES

    zones = list(zones)
    outputs = sorted(((output.upper(), name, levels) for output, (name, _, levels) in _zone_outputs().items() if name),
                     key=lambda item: len(item[0]), reverse=True)
    schedules = dict(zip((schedule.upper() for schedule in PMV_SETPOINT_SCHEDULES), _THERMOSTAT_SETPOINTS))
    found = {}
    for column in columns:
        zone = zone_of(column)
        if zone is None or zone not in zones:
            continue
        head = column.split(' [')[0].upper()
        for output, name, levels in outputs:
            prefix = f'EMS:{output}_'
            if head.startswith(prefix) and head[len(prefix):].startswith(zone.upper()):
                found[column] = (zone, name, levels)
                break
        else:
            if head.endswith(':SCHEDULE VALUE'):
                for schedule, name in schedules.items():
                    if head == f'{schedule}_{zone.upper()}:SCHEDULE VALUE':
                        found[column] = (zone, name, False)
    return found
