# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The columns of :class:`~accim.data.postprocessing.main.Table` of the optional EMS outputs of the models with the
ACCIS (proposal D2, with the outputs of B1, B2, B5, C2 and A4).

Some arguments of :class:`accim.sim.accis.AddAccis` (and of :func:`accim.sim.accis.add_accis_to_idf`) and the setpoints
of the ATHB add EMS outputs to the zones (``<output>_<zone>``, with the EMS suffix of the zone) and to the whole model:

- ``custom_outdoor_metric`` (:mod:`accim.sim.ems.outdoor_metric`): the outdoor metric of the custom model,
  ``Tout_metric`` (°C, that of the zone that runs last) and ``Tout_metric_<zone>``, averaged;
- ``custom_regimes`` (:mod:`accim.sim.ems.custom_regimes`): the number of the regime of the custom model of each zone,
  ``CustomRegime_<zone>``, averaged;
- ``report_hours_below`` (:mod:`accim.sim.ems.setpoint_limits`): the occupied hours below some temperatures,
  ``HoursBelow_<T>_<zone>`` (h; ``HoursBelow_17p5_<zone>`` for 17.5 °C), summed;
- ``report_long_term_discomfort`` (:mod:`accim.sim.ems.long_term_discomfort`): the occupied hours and degree hours
  above the upper limit and below the lower limit of each zone (``Hours Above Upper Limit_<zone>``, ``Hours Below Lower
  Limit_<zone>``, in h, ``Degree Hours Above Upper Limit_<zone>`` and ``Degree Hours Below Lower Limit_<zone>``, in Kh)
  and of the building (``..._Building``, the sums of the zones), summed;
- :func:`accim.sim.comfort_hooks.apply_athb_setpoints`: the ATHB_PMV and the adapted clothing insulation and metabolic
  rate of each zone, ``ATHB_PMV_<zone>``, ``ATHB_clo_<zone>`` (clo) and ``ATHB_met_<zone>`` (met), averaged.

``Table`` averages over time those that are averaged (:func:`averaged_outputs`) and gives ``frequency_agg_func`` to the
others, keeps them with ``standard_outputs=True`` (:func:`standard_outputs`), and names those of the zones as its other
outputs of the zones, ``<zone>_<name>`` (:func:`zone_columns`), and those of the model and of the building
``Tout_metric (°C)`` and ``Building_<name>`` (:func:`other_columns`). The outdoor metric of each zone keeps its EMS
name, as the comfort temperature and the setpoints of each zone of the ACCIS, so that ``Tout_metric (°C)`` is not part
of the name of another column (the figures of Table take the columns whose names contain the names they are given).
"""

from typing import Callable, Dict, Iterable, Optional, Sequence, Tuple

__all__ = ['BUILDING', 'HOURS_BELOW', 'LONG_TERM_OUTPUTS', 'OUTDOOR_METRIC', 'OUTDOOR_METRIC_NAME', 'ZONE_OUTPUTS',
           'averaged_outputs', 'comfort_hours', 'other_columns', 'standard_outputs', 'zone_columns']

#: The outputs of the hours and degree hours of ``report_long_term_discomfort``, which the zones and the building have:
#: EMS output -> name in Table (as the indicators of ``Table(long_term_indicators=True)``)
LONG_TERM_OUTPUTS = {
    'Hours Above Upper Limit': 'Hours Above Upper Limit (h)',
    'Hours Below Lower Limit': 'Hours Below Lower Limit (h)',
    'Degree Hours Above Upper Limit': 'Degree Hours Above Upper Limit (Kh)',
    'Degree Hours Below Lower Limit': 'Degree Hours Below Lower Limit (Kh)',
}
#: The outputs of the zones that Table renames ``<zone>_<name>``: EMS output (without ``_<zone>``) -> (name in Table,
#: True if Table averages it over time, True if Table gives it block and building values)
ZONE_OUTPUTS = {
    'CustomRegime': ('CustomRegime', True, False),
    **{output: (name, False, True) for output, name in LONG_TERM_OUTPUTS.items()},
    'ATHB_PMV': ('ATHB_PMV', True, True),
    'ATHB_clo': ('ATHB_clo (clo)', True, True),
    'ATHB_met': ('ATHB_met (met)', True, True),
}
#: The occupied hours below a temperature T of each zone, ``HoursBelow_<T>_<zone>``, are ``<zone>_HoursBelow_<T> (h)``,
#: summed over time, with block and building values
HOURS_BELOW = 'HoursBelow'
#: The outdoor metric of the custom model, ``Tout_metric`` (of the model) and ``Tout_metric_<zone>``
OUTDOOR_METRIC = 'Tout_metric'
#: The name in Table of the outdoor metric of the model
OUTDOOR_METRIC_NAME = 'Tout_metric (°C)'
#: The suffix of the outputs of the building of ``report_long_term_discomfort``
BUILDING = 'Building'


def averaged_outputs() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of these outputs that Table averages over time (and over the occupant
    instances of a zone), as EnergyPlus names them in its CSV files (``'EMS:ATHB_PMV_'`` for ``EMS:ATHB_PMV_Block1_Zone1
    [](Hourly)``): the outdoor metric, the regimes and the outputs of the ATHB; the hours and degree hours get
    ``frequency_agg_func``."""
    return (f'EMS:{OUTDOOR_METRIC}',) + tuple(f'EMS:{output}_' for output, (_, averaged, _) in ZONE_OUTPUTS.items()
                                              if averaged)


def standard_outputs() -> Tuple[str, ...]:
    """The beginnings of the names of the columns of these outputs, which Table keeps with ``standard_outputs=True``."""
    return (f'EMS:{OUTDOOR_METRIC}', f'EMS:{HOURS_BELOW}_') + tuple(f'EMS:{output}_' for output in ZONE_OUTPUTS)


def comfort_hours() -> Tuple[str, ...]:
    """The names in Table of the hours of these outputs that ``Table.format_table(type_of_table='comfort hours')`` takes
    with those of the ACCIS: those of ``report_long_term_discomfort`` (``'Hours Above Upper Limit (h)'``...); the hours
    below some temperatures are those whose names contain :data:`HOURS_BELOW` and ``'_'``."""
    return tuple(name for name in LONG_TERM_OUTPUTS.values() if name.endswith(' (h)'))


def zone_columns(columns: Iterable[str], zone_of: Callable[[str], Optional[str]],
                 zones: Sequence[str]) -> Dict[str, Tuple[str, str, bool]]:
    """
    The columns of these outputs of the zones that Table renames, once it has given the columns the names of its zones:
    ``EMS:<output>_<zone>... [<units>](<frequency>)``, whose output is one of :data:`ZONE_OUTPUTS` (exactly:
    ``EMS:DEGREE HOURS ABOVE UPPER LIMIT_<zone>`` is not ``Hours Above Upper Limit``) or ``HoursBelow_<T>``, and whose
    name continues with the name of the zone (in the zones named after their space, the name of the People object
    follows).

    :param columns: The names of the columns of the table (in capitals, as Table reads them, or not).
    :param zone_of: The zone of a column (the function of Table), or None.
    :param zones: The occupied zones, as Table names them.
    :return: A dictionary {column: (zone, name in Table, True if Table gives it block and building values)}, whose
        columns Table renames ``<zone>_<name in Table>``: ``EMS:ATHB_PMV_BLOCK1:ZONE1 [](HOURLY)`` is
        ``Block1:Zone1_ATHB_PMV``, and ``EMS:HOURSBELOW_17P5_BLOCK1:ZONE1 [H](HOURLY)`` is
        ``Block1:Zone1_HoursBelow_17p5 (h)``.
    """
    zones = list(zones)
    outputs = sorted(((output.upper(), name, levels) for output, (name, _, levels) in ZONE_OUTPUTS.items()),
                     key=lambda item: len(item[0]), reverse=True)
    hours_below = f'EMS:{HOURS_BELOW.upper()}_'
    found = {}
    for column in columns:
        zone = zone_of(column)
        if zone is None or zone not in zones:
            continue
        head = column.split(' [')[0].upper()
        if head.startswith(hours_below):
            # The temperature has no '_' (its point is 'p' and its minus sign 'm', which Table has in capitals)
            threshold, _, rest = head[len(hours_below):].partition('_')
            if threshold and rest.startswith(zone.upper()):
                found[column] = (zone, f'{HOURS_BELOW}_{threshold.lower()} (h)', True)
            continue
        for output, name, levels in outputs:
            prefix = f'EMS:{output}_'
            if head.startswith(prefix) and head[len(prefix):].startswith(zone.upper()):
                found[column] = (zone, name, levels)
                break
    return found


def other_columns(columns: Iterable[str]) -> Dict[str, str]:
    """The columns of these outputs of the model and of the building that Table renames: ``EMS:TOUT_METRIC [C](HOURLY)``
    is ``Tout_metric (°C)``, and ``EMS:HOURS ABOVE UPPER LIMIT_BUILDING [H](HOURLY)`` is ``Building_Hours Above Upper
    Limit (h)`` (the EMS sums of all the zones, whatever ``level_excluded_zones`` is).

    :return: A dictionary {column: name in Table}.
    """
    names = {f'EMS:{OUTDOOR_METRIC.upper()}': OUTDOOR_METRIC_NAME}
    names.update({f'EMS:{output.upper()}_{BUILDING.upper()}': f'{BUILDING}_{name}'
                  for output, name in LONG_TERM_OUTPUTS.items()})
    return {column: names[column.split(' [')[0].upper()] for column in columns
            if column.split(' [')[0].upper() in names}
