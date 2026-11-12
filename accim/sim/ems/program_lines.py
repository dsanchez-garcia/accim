# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Erl lines of the EMS programs of ACCIS (those of accim 0.x, except that the inputs of the zones are in the programs
SetInputData_<zone>, see :mod:`accim.sim.ems.inputs`, and that the hour counters of CountHours_<zone> and
CountHoursNoApp_<zone> and the ventilation hours of ApplyAST_<zone> are set in every timestep).

The lines of the programs of each zone and window contain ``{zone}`` and ``{window}``, which
:func:`format_lines` replaces with the names of the zone or window in the EMS objects. The programs without them
(SetComfTemp, SetAppLimits, ApplyCAT, SetAST, SetASTnoTol and SetVST) are run by the program RunACCIS_<zone> of each
zone, after its inputs.

SetComfTemp, SetAppLimits, ApplyCAT and CountHours_<zone> are a chain ``if ComfStand == ... elseif ... endif`` with a
branch for each comfort standard (or group of them); :func:`for_comfort_standards` leaves out the branches of the
comfort standards that a model does not use.
"""

import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

__all__ = [
    'SET_COMF_TEMP',
    'COUNT_HOURS',
    'SET_APP_LIMITS',
    'APPLY_CAT',
    'SET_AST',
    'SET_AST_NO_TOL',
    'COUNT_HOURS_NO_APP',
    'SET_GEO_VAR',
    'SET_VST',
    'APPLY_AST_MIXED_MODE',
    'APPLY_AST_MIXED_MODE_EXISTING_HVAC',
    'SET_MY_VOF',
    'SET_WINDOW_OPERATION',
    'SET_WINDOW_OPERATION_EXISTING_HVAC',
    'APPLY_AST_AIR_CONDITIONED',
    'BUILT_IN_BRANCHES',
    'COUNT_HOURS_OUTDOOR_METRIC',
    'HVAC_OFF_FROM_COILS',
    'HVAC_OFF_FROM_LOAD',
    'OUTDOOR_METRIC_VARIABLE',
    'REGISTERED_BRANCHES',
    'SET_COMF_TEMP_OUTDOOR_METRIC',
    'SET_VST_OUTDOOR_METRIC',
    'apply_cat_lines',
    'chain_comfort_standards',
    'count_hours_lines',
    'for_comfort_standards',
    'format_lines',
    'registered_standards_in',
    'set_app_limits_lines',
    'set_comf_temp_lines',
    'set_vst_lines',
]

_COMFORT_STANDARD = re.compile(r'\(?\s*ComfStand\s*==\s*(\d+)\s*\)?', re.IGNORECASE)


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.strip('\n').split('\n'))


def _join(*texts: str) -> Tuple[str, ...]:
    """The lines of several texts, one after the other."""
    return _lines('\n'.join(text.strip('\n') for text in texts))


def format_lines(lines: Tuple[str, ...], zone: str = None, window: str = None) -> list:
    """The lines of a program of a zone or window, with its name."""
    result = list(lines)
    if zone is not None:
        result = [line.replace('{zone}', zone) for line in result]
    if window is not None:
        result = [line.replace('{window}', window) for line in result]
    return result


def _comfort_standards_of(condition: str) -> List[int]:
    """The comfort standards of a condition such as ``ComfStand == 2 || (ComfStand == 12)``."""
    matches = [_COMFORT_STANDARD.fullmatch(part.strip()) for part in condition.split('||')]
    if not all(matches):
        raise ValueError(f'The condition {condition!r} is not a condition on ComfStand only.')
    return [int(match.group(1)) for match in matches]


def _branches(lines: Iterable[str]) -> List[Tuple[Optional[str], List[str]]]:
    """The condition (None for else) and lines of each branch of a chain ``if ... elseif ... else ... endif``.

    :raises ValueError: If the lines are not one chain.
    """
    branches: List[Tuple[Optional[str], List[str]]] = []
    depth = 0
    for line in lines:
        keyword, _, condition = line.strip().partition(' ')
        keyword = keyword.upper()
        if depth == 0:
            if keyword != 'IF' or branches:
                raise ValueError('The lines are not one chain if ... endif.')
            branches.append((condition, []))
            depth = 1
        elif depth == 1 and keyword in ('ELSEIF', 'ELSE'):
            branches.append((condition if keyword == 'ELSEIF' else None, []))
        elif depth == 1 and keyword == 'ENDIF':
            depth = 0
        else:
            if keyword in ('IF', 'WHILE'):
                depth += 1
            elif keyword in ('ENDIF', 'ENDWHILE'):
                depth -= 1
            branches[-1][1].append(line)
    if depth != 0:
        raise ValueError('The chain if ... endif is not closed.')
    return branches


def for_comfort_standards(lines: Iterable[str], comfort_standards: Iterable[int]) -> List[str]:
    """The lines of a program that is a chain ``if ComfStand == ... elseif ComfStand == ... else ... endif``, with the
    branches of some comfort standards only.

    The conditions of the branches only name these comfort standards, and the branch ``else`` becomes a branch
    ``elseif`` of those that no condition names. For the comfort standards given, the lines do the same as the whole
    chain. If none of them has a branch, there are no lines.
    """
    wanted = set(comfort_standards)
    branches = _branches(lines)
    # As in the EMS, each comfort standard runs the first branch that names it, or the branch else if none does
    named = set()
    kept = []
    for condition, body in branches:
        if condition is None:
            standards = sorted(wanted - named)
        else:
            standards = [n for n in _comfort_standards_of(condition) if n not in named]
            named.update(standards)
            standards = [n for n in standards if n in wanted]
        if standards:
            kept.append((standards, body))
    result = []
    for number, (standards, body) in enumerate(kept):
        keyword = 'if' if number == 0 else 'elseif'
        result.append(f"{keyword} {' || '.join(f'ComfStand == {n}' for n in standards)}")
        result.extend(body)
    if kept:
        result.append('endif')
    return result


def chain_comfort_standards(lines: Iterable[str]) -> Optional[Set[int]]:
    """The comfort standards that the conditions of a chain ``if ComfStand == ... endif`` name, or None if it has a
    branch ``else`` (the chain of all the comfort standards; those of :func:`for_comfort_standards` have none).

    :raises ValueError: If the lines are not such a chain.
    """
    standards: Set[int] = set()
    for condition, _ in _branches(lines):
        if condition is None:
            return None
        standards.update(_comfort_standards_of(condition))
    return standards


#: Comfort (neutral) temperature of each comfort standard. That of IND IMAC R 7DRM (9) is a line of the arithmetic mean
#: of the daily means of the 7 previous days, which the EMS code of the outdoor metric calculates (Tout_metric,
#: :data:`accim.sim.ems.standard_lines.BUILT_IN_METRICS`), and that of IND IMAC R 30DRM (10), of the running mean of 30
#: days of EnergyPlus (PMOT): models A and B of Rawal et al. (2022), Building and Environment 219, 109187. Until accim
#: 1.2.0, 9 read PMOT and the setpoints of 10 read RMOT (the decisions of 2026-11-12, ``notes/decisions.md``).
SET_COMF_TEMP = _lines("""
if ComfStand == 99
set ComfTemp = PMOT*m+n
elseif ComfStand == 1
set ComfTemp = RMOT*0.33+18.8
elseif ComfStand == 2
set ComfTemp = PMOT*0.31+17.8
elseif ComfStand == 3
set ComfTemp = PMOT*0.48+14.4
elseif ComfStand == 4
set ComfTemp = 0
elseif ComfStand == 5
set ComfTemp = 0
elseif ComfStand == 6
set ComfTemp = 0
elseif ComfStand == 7
set ComfTemp = PMOT*0.54+12.83
elseif ComfStand == 8
set ComfTemp = PMOT*0.28+17.87
elseif ComfStand == 9
set ComfTemp = Tout_metric*0.39+18.42
elseif ComfStand == 10
set ComfTemp = PMOT*0.42+17.6
elseif ComfStand == 11
set ComfTemp = PMOT*0.75+5.37
elseif ComfStand == 12
set ComfTemp = PMOT*0.25+19.7
elseif ComfStand == 13
set ComfTemp = PMOT*0.26+15.9
elseif ComfStand == 14
set ComfTemp = PMOT*0.26+16.75
elseif ComfStand == 15
set ComfTemp = PMOT*0.56+12.74
elseif ComfStand == 16
set ComfTemp = PMOT*0.09+22.32
elseif ComfStand == 17
if (DayOfYear <= 121) || (DayOfYear > 295)
set ComfTemp = PMOT*0.48+13.9
else
set ComfTemp = PMOT*0.59+9.6
endif
elseif ComfStand == 18
if (DayOfYear <= 121) || (DayOfYear > 295)
set ComfTemp = PMOT*0.84+5.3
else
set ComfTemp = PMOT*0.96-3.6
endif
elseif ComfStand == 19
if (DayOfYear <= 121) || (DayOfYear > 295)
set ComfTemp = PMOT*0.27+17.9
else
set ComfTemp = PMOT*0.53+10.3
endif
elseif ComfStand == 20
if (DayOfYear <= 121) || (DayOfYear > 295)
set ComfTemp = PMOT*0.38+15.7
else
set ComfTemp = PMOT*0.47+9.07
endif
elseif ComfStand == 21
set ComfTemp = PMOT*0.678+13.51
endif
""")

_COUNT_HOURS_BODY = """
if (METRIC >= AHSTall) && (METRIC <= ACSTaul)
if ({zone}_OpT > ACSTnoTol)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 1*ZoneTimeStep
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 0
set DiscomfNonAppColdHours_{zone} = 0
elseif ({zone}_OpT < AHSTnoTol)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 1*ZoneTimeStep
set DiscomfNonAppHotHours_{zone} = 0
set DiscomfNonAppColdHours_{zone} = 0
else
set ComfHours_{zone} = 1*ZoneTimeStep
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 0
set DiscomfNonAppColdHours_{zone} = 0
endif
elseif (METRIC > ACSTaul)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 1*ZoneTimeStep
set DiscomfNonAppColdHours_{zone} = 0
elseif (METRIC < AHSTall)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 0
set DiscomfNonAppColdHours_{zone} = 1*ZoneTimeStep
endif
"""


def _count_hours_body(metric: str) -> str:
    """The lines of COUNT_HOURS for the comfort standards whose running mean is ``metric``."""
    return _COUNT_HOURS_BODY.strip('\n').replace('METRIC', metric)


#: Comfortable and discomfortable hours of a zone, within the applicability limits: in each timestep, one of the five
#: counters is the length of the timestep and the others are 0. The operative temperature is compared with the
#: setpoints without tolerance of the timestep (RunACCIS_<zone> runs it after SetASTnoTol). The running mean compared
#: with the applicability limits is RMOT for INT EN16798 (1) and PMOT for the others (also for IND IMAC R 30DRM, 10,
#: which read RMOT until accim 1.2.0); the comfort standards with another one have their own branch
#: (:data:`BUILT_IN_BRANCHES` and :data:`REGISTERED_BRANCHES`, :func:`count_hours_lines`).
COUNT_HOURS = _join('if ComfStand == 1', _count_hours_body('RMOT'), 'else', _count_hours_body('PMOT'), 'endif')

#: The variable with the outdoor metric of the custom model (ComfStand 99) in the models with the EMS code of its
#: outdoor metric (:mod:`accim.sim.ems.outdoor_metric`); the other models use PMOT, as before accim 1.2.0.
OUTDOOR_METRIC_VARIABLE = 'Tout_metric'
#: SET_COMF_TEMP in the models with the EMS code of the outdoor metric of the custom model.
SET_COMF_TEMP_OUTDOOR_METRIC = tuple(line.replace('PMOT*m+n', f'{OUTDOOR_METRIC_VARIABLE}*m+n')
                                     for line in SET_COMF_TEMP)
#: COUNT_HOURS in the models with the EMS code of the outdoor metric of the custom model: the custom model compares its
#: outdoor metric with its limits.
COUNT_HOURS_OUTDOOR_METRIC = _join('if ComfStand == 1', _count_hours_body('RMOT'),
                                   'elseif ComfStand == 99', _count_hours_body(OUTDOOR_METRIC_VARIABLE), 'else',
                                   _count_hours_body('PMOT'), 'endif')

#: Applicability limits of each comfort standard (those of the custom model are inputs of the zone).
SET_APP_LIMITS = _lines("""
if ComfStand == 99
set ACSTaul = CustAST_ACSTaul
set ACSTall = CustAST_ACSTall
set AHSTaul = CustAST_AHSTaul
set AHSTall = CustAST_AHSTall
elseif ComfStand == 1
set ACSTaul = 30
set ACSTall = 10
set AHSTaul = 30
set AHSTall = 10
elseif ComfStand == 2 || ComfStand == 12
set ACSTaul = 33.5
set ACSTall = 10
set AHSTaul = 33.5
set AHSTall = 10
elseif ComfStand == 3
set ACSTaul = 30
set ACSTall = 5
set AHSTaul = 30
set AHSTall = 5
elseif (ComfStand == 4) || (ComfStand == 5)
if CAT == 1
set ACSTaul = 28
set ACSTall = 18
set AHSTaul = 28
set AHSTall = 18
elseif CAT == 2
set ACSTaul = 30
set ACSTall = 18
set AHSTaul = 28
set AHSTall = 16
else
set ACSTaul = 50
set ACSTall = 50
set AHSTaul = 50
set AHSTall = 50
endif
elseif ComfStand == 6
set ACSTaul = 30
set ACSTall = -7
set AHSTaul = 30
set AHSTall = -7
elseif ComfStand == 7
set ACSTaul = 31
set ACSTall = 12.5
set AHSTaul = 31
set AHSTall = 12.5
elseif ComfStand == 8
set ACSTaul = 38.5
set ACSTall = 13
set AHSTaul = 38.5
set AHSTall = 13
elseif ComfStand == 9 || ComfStand == 10 || ComfStand == 11
set ACSTaul = 33
set ACSTall = 5.5
set AHSTaul = 33
set AHSTall = 5.5
elseif ComfStand == 13
set ACSTaul = 25
set ACSTall = 10
set AHSTaul = 25
set AHSTall = 10
elseif ComfStand == 14
set ACSTaul = 27
set ACSTall = 8
set AHSTaul = 27
set AHSTall = 8
elseif ComfStand == 15
set ACSTaul = 24.8
set ACSTall = 16.9
set AHSTaul = 24.8
set AHSTall = 16.9
elseif ComfStand == 16
set ACSTaul = 25.7
set ACSTall = 16.4
set AHSTaul = 25.7
set AHSTall = 16.4
elseif ComfStand == 17
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSTaul = 25.25
set ACSTall = 11.25
set AHSTaul = 25.25
set AHSTall = 11.25
else
set ACSTaul = 45
set ACSTall = 23
set AHSTaul = 45
set AHSTall = 23
endif
elseif ComfStand == 18
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSTaul = 27.5
set ACSTall = 15.5
set AHSTaul = 27.5
set AHSTall = 15.5
else
set ACSTaul = 34
set ACSTall = 23
set AHSTaul = 34
set AHSTall = 23
endif
elseif ComfStand == 19
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSTaul = 25.25
set ACSTall = 5
set AHSTaul = 25.25
set AHSTall = 5
else
set ACSTaul = 25.25
set ACSTall = 11.75
set AHSTaul = 25.25
set AHSTall = 11.75
endif
elseif ComfStand == 20
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSTaul = 29.75
set ACSTall = 13
set AHSTaul = 29.75
set AHSTall = 13
else
set ACSTaul = 45
set ACSTall = 23
set AHSTaul = 45
set AHSTall = 23
endif
elseif ComfStand == 21
set ACSTaul = 20
set ACSTall = 6.5
set AHSTaul = 20
set AHSTall = 6.5
else
set ACSTaul = 50
set ACSTall = 50
set AHSTaul = 50
set AHSTall = 50
endif
""")

#: Offsets of the setpoints from the comfort temperature for each category (those of the custom model, and the offsets
#: CATcoolOffset and CATheatOffset added to them, are inputs of the zone).
APPLY_CAT = _lines("""
if ComfStand == 99
set ACSToffset = CustAST_ACSToffset+CATcoolOffset
set AHSToffset = CustAST_AHSToffset+CATheatOffset
elseif (ComfStand == 1 )
if (CAT == 1)
set ACSToffset = 2+CATcoolOffset
set AHSToffset = -3+CATheatOffset
elseif (CAT == 2)
set ACSToffset = 3+CATcoolOffset
set AHSToffset = -4+CATheatOffset
elseif (CAT == 3)
set ACSToffset = 4+CATcoolOffset
set AHSToffset = -5+CATheatOffset
endif
elseif ComfStand == 2 || ComfStand == 3 || ComfStand == 11
if (CAT == 90)
set ACSToffset = 2.5+CATcoolOffset
set AHSToffset = -2.5+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 3.5+CATcoolOffset
set AHSToffset = -3.5+CATheatOffset
endif
elseif (ComfStand == 4 ) || (ComfStand == 5) || (ComfStand == 6)
set ACSToffset = 0+CATcoolOffset
set AHSToffset = 0+CATheatOffset
elseif (ComfStand == 7)
if (CAT == 90)
set ACSToffset = 2.4+CATcoolOffset
set AHSToffset = -2.4+CATheatOffset
elseif (CAT == 85)
set ACSToffset = 3.3+CATcoolOffset
set AHSToffset = -3.3+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 4.1+CATcoolOffset
set AHSToffset = -4.1+CATheatOffset
endif
elseif (ComfStand == 8)
if (CAT == 90)
set ACSToffset = 3.5+CATcoolOffset
set AHSToffset = -3.5+CATheatOffset
elseif (CAT == 85)
set ACSToffset = 4.8+CATcoolOffset
set AHSToffset = -4.8+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 5.9+CATcoolOffset
set AHSToffset = -5.9+CATheatOffset
endif
elseif ComfStand == 9 || ComfStand == 10
if (CAT == 90)
set ACSToffset = 2.15+CATcoolOffset
set AHSToffset = -2.15+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 3.6+CATcoolOffset
set AHSToffset = -3.6+CATheatOffset
endif
elseif ComfStand == 12
if (CAT == 90)
set ACSToffset = 1.7+CATcoolOffset
set AHSToffset = -1.7+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 2.89+CATcoolOffset
set AHSToffset = -2.89+CATheatOffset
endif
elseif ComfStand == 13
if (CAT == 90)
set ACSToffset = 3.45+CATcoolOffset
set AHSToffset = -3.45+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 4.55+CATcoolOffset
set AHSToffset = -4.55+CATheatOffset
endif
elseif ComfStand == 14
if (CAT == 90)
set ACSToffset = 3.5+CATcoolOffset
set AHSToffset = -3.5+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 4.5+CATcoolOffset
set AHSToffset = -4.5+CATheatOffset
endif
elseif ComfStand == 15
if (CAT == 90)
set ACSToffset = 2.8+CATcoolOffset
set AHSToffset = -2.8+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 3.8+CATcoolOffset
set AHSToffset = -3.8+CATheatOffset
endif
elseif ComfStand == 16
if (CAT == 90)
set ACSToffset = 1.1+CATcoolOffset
set AHSToffset = -1.1+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 2.1+CATcoolOffset
set AHSToffset = -2.1+CATheatOffset
endif
elseif (ComfStand == 17) || (ComfStand == 18)
if CAT == 90
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSToffset = 2+CATcoolOffset
set AHSToffset = -2+CATheatOffset
else
set ACSToffset = 2+CATcoolOffset
set AHSToffset = -2+CATheatOffset
endif
elseif CAT == 80
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSToffset = 3+CATcoolOffset
set AHSToffset = -3+CATheatOffset
else
set ACSToffset = 3+CATcoolOffset
set AHSToffset = -3+CATheatOffset
endif
endif
elseif ComfStand == 19
if CAT == 90
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSToffset = 2+CATcoolOffset
set AHSToffset = -2+CATheatOffset
else
set ACSToffset = 1+CATcoolOffset
set AHSToffset = -1+CATheatOffset
endif
elseif CAT == 80
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSToffset = 3+CATcoolOffset
set AHSToffset = -3+CATheatOffset
else
set ACSToffset = 2+CATcoolOffset
set AHSToffset = -2+CATheatOffset
endif
endif
elseif ComfStand == 20
if CAT == 90
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSToffset = 2+CATcoolOffset
set AHSToffset = -2+CATheatOffset
else
set ACSToffset = 5+CATcoolOffset
set AHSToffset = -5+CATheatOffset
endif
elseif CAT == 80
if (DayOfYear <= 121) || (DayOfYear > 295)
set ACSToffset = 3+CATcoolOffset
set AHSToffset = -3+CATheatOffset
else
set ACSToffset = 6+CATcoolOffset
set AHSToffset = -6+CATheatOffset
endif
endif
elseif ComfStand == 21
if (CAT == 90)
set ACSToffset = 2.5+CATcoolOffset
set AHSToffset = -2.5+CATheatOffset
elseif (CAT == 80)
set ACSToffset = 4+CATcoolOffset
set AHSToffset = -4+CATheatOffset
endif
endif
""")

#: SetAST: the setpoints of the comfort standard and comfort mode of the zone (SetpointAcc, m and n are inputs of the
#: zone).
SET_AST = _lines("""
run SetAST_Master
""")

#: Setpoints without tolerance.
SET_AST_NO_TOL = _lines("""
set ACSTnoTol = ACST-ACSTtol
set AHSTnoTol = AHST-AHSTtol
""")

#: Comfortable, discomfortable and occupied hours of a zone, regardless of the applicability limits. In each occupied
#: timestep, either the occupied comfortable or the occupied discomfortable hours are the length of the timestep, so
#: that they add up to the occupied hours.
COUNT_HOURS_NO_APP = _lines("""
if ({zone}_OpT <= ACSTnoTol) && ({zone}_OpT >= AHSTnoTol)
set ComfHoursNoApp_{zone} = 1*ZoneTimeStep
set OccDiscomfHoursNoApp_{zone} = 0
if Occ_count_{zone} > 0
set OccComfHoursNoApp_{zone} = 1*ZoneTimeStep
else
set OccComfHoursNoApp_{zone} = 0
endif
else
set ComfHoursNoApp_{zone} = 0
set OccComfHoursNoApp_{zone} = 0
if Occ_count_{zone} > 0
set OccDiscomfHoursNoApp_{zone} = 1*ZoneTimeStep
else
set OccDiscomfHoursNoApp_{zone} = 0
endif
endif
if Occ_count_{zone} > 0
set OccHours_{zone} = 1*ZoneTimeStep
else
set OccHours_{zone} = 0
endif
""")

#: Floor area and volume of a zone.
SET_GEO_VAR = _lines("""
set ZoneFloorArea_{zone} = ZFA_{zone}/2
set ZoneAirVolume_{zone} = ZAV_{zone}/2
""")

#: Ventilation setpoint temperature.
SET_VST = _lines("""
set MinOutTemp = roundedAHST - MinOToffset
if (VentCtrl == 0) || (VentCtrl==2)
if ComfStand == 0
if (CurrentTime < 7)
set VST = (roundedACST+roundedAHST)/2+VSToffset
elseif (CurrentTime < 15)
set VST = 22.5+VSToffset
elseif (CurrentTime < 23)
set VST = (roundedACST+roundedAHST)/2+VSToffset
elseif (CurrentTime < 24)
set VST = (roundedACST+roundedAHST)/2+VSToffset
endif
elseif ComfStand == 1
if (RMOT >= AHSTall) && (RMOT <= ACSTaul)
set VST = ComfTemp+VSToffset
else
set VST = (roundedACST+roundedAHST)/2+VSToffset
endif
elseif ComfStand == 4 || ComfStand == 5 || ComfStand == 6
if (PMOT >= AHSTall) && (PMOT <= ACSTaul)
set VST = (roundedACST+roundedAHST)/2+VSToffset
else
set VST = 0
endif
else
if (PMOT >= AHSTall) && (PMOT <= ACSTaul)
set VST = ComfTemp+VSToffset
else
set VST = (roundedACST+roundedAHST)/2+VSToffset
endif
endif
elseif (VentCtrl == 1) || (VentCtrl==3)
set VST = roundedAHST+VSToffset
endif
""")


def _set_vst_outdoor_metric() -> Tuple[str, ...]:
    """SET_VST with a branch of the custom model (ComfStand 99) that compares its outdoor metric with its limits,
    before the branch of the comfort standards that compare PMOT with them."""
    lines = list(SET_VST)
    branch = ['else', 'if (PMOT >= AHSTall) && (PMOT <= ACSTaul)', 'set VST = ComfTemp+VSToffset']
    index = next(n for n in range(len(lines)) if lines[n:n + len(branch)] == branch)
    custom = ['elseif ComfStand == 99',
              f'if ({OUTDOOR_METRIC_VARIABLE} >= AHSTall) && ({OUTDOOR_METRIC_VARIABLE} <= ACSTaul)',
              'set VST = ComfTemp+VSToffset', 'else', 'set VST = (roundedACST+roundedAHST)/2+VSToffset', 'endif']
    return tuple(lines[:index] + custom + lines[index:])


#: SET_VST in the models with the EMS code of the outdoor metric of the custom model.
SET_VST_OUTDOOR_METRIC = _set_vst_outdoor_metric()

#: Whether the HVAC system of a zone (or of the zone of a window) neither heats nor cools: with the VRF systems of
#: accim, from its coils, which were off in the previous timestep.
_HVAC_OFF_FROM_COILS = """
if {name}_CoolCoil==0
if {name}_HeatCoil==0
set NoH_NoC_reqs = 1
else
set NoH_NoC_reqs = 0
endif
else
set NoH_NoC_reqs = 0
endif
"""
#: The same with the existing HVAC systems (ScriptType 'ex_mm'), whatever their equipment: from the load to the
#: setpoints that the thermostat of the zone asked the HVAC system for in the previous timestep (the EnergyPlus
#: output 'Zone Predicted Sensible Load to Setpoint Heat Transfer Rate'), which is 0 when the temperature of the zone
#: is between its heating and cooling setpoints, and so when the HVAC system is off.
_HVAC_OFF_FROM_LOAD = """
if {name}_LoadToSetpoint == 0
set NoH_NoC_reqs = 1
else
set NoH_NoC_reqs = 0
endif
"""
#: The lines that set NoH_NoC_reqs (1 if the HVAC system of the zone neither heated nor cooled in the previous
#: timestep) in the programs of mixed mode of a zone: with the VRF systems of accim ('vrf_mm') and with the existing
#: HVAC systems ('ex_mm'). The regimes of the custom model with the conditions 'hvac_off' and 'hvac_on' use them too
#: (:mod:`accim.sim.ems.custom_regimes`).
HVAC_OFF_FROM_COILS = _lines(_HVAC_OFF_FROM_COILS.replace('{name}', '{zone}'))
HVAC_OFF_FROM_LOAD = _lines(_HVAC_OFF_FROM_LOAD.replace('{name}', '{zone}'))

#: Setpoints and ventilation of a zone in mixed mode (after the lines that set NoH_NoC_reqs).
_APPLY_AST_MIXED_MODE_BODY = """
if {zone}_OpT<roundedACST
if {zone}_WindSpeed <= MaxWindSpeed
if {zone}_OutT>MinOutTemp
if {zone}_OutT < {zone}_OpT
set meets_base_reqs = 1
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
if (NoH_NoC_reqs == 1) && (meets_base_reqs == 1)
if {zone}_OpT>VST
set Ventilates_HVACmode2_{zone} = 1
else
set Ventilates_HVACmode2_{zone} = 0
endif
else
set Ventilates_HVACmode2_{zone} = 0
endif
if VentCtrl == 0
if {zone}_OutT < {zone}_OpT
if {zone}_OutT>MinOutTemp
if {zone}_OpT > VST
if {zone}_WindSpeed <= MaxWindSpeed
set Ventilates_HVACmode1_{zone} = 1
else
set Ventilates_HVACmode1_{zone} = 0
endif
else
set Ventilates_HVACmode1_{zone} = 0
endif
else
set Ventilates_HVACmode1_{zone} = 0
endif
else
set Ventilates_HVACmode1_{zone} = 0
endif
elseif VentCtrl == 1
if {zone}_OutT<{zone}_OpT
if {zone}_OutT>MinOutTemp
if {zone}_OpT > ACSTnoTol
if {zone}_WindSpeed <= MaxWindSpeed
set Ventilates_HVACmode1_{zone} = 1
else
set Ventilates_HVACmode1_{zone} = 0
endif
else
set Ventilates_HVACmode1_{zone} = 0
endif
else
set Ventilates_HVACmode1_{zone} = 0
endif
else
set Ventilates_HVACmode1_{zone} = 0
endif
endif
if HVACmode == 0
set VentHours_{zone} = 0
if Occ_count_{zone} == 0
Set ACST_Act_{zone} = 100
Set AHST_Act_{zone} = -100
else
set ACST_Act_{zone} = roundedACST
set AHST_Act_{zone} = roundedAHST
endif
elseif HVACmode == 1
Set ACST_Act_{zone} = 100
Set AHST_Act_{zone} = -100
if Ventilates_HVACmode1_{zone} == 1 && Occ_count_{zone} > 0
set VentHours_{zone} = 1*ZoneTimeStep
else
set VentHours_{zone} = 0
endif
elseif HVACmode == 2
if Occ_count_{zone} == 0
Set ACST_Act_{zone} = 100
Set AHST_Act_{zone} = -100
set VentHours_{zone} = 0
else
if Ventilates_HVACmode2_{zone} == 1
set VentHours_{zone} = 1*ZoneTimeStep
elseif Ventilates_HVACmode2_{zone} == 0
set VentHours_{zone} = 0
set ACST_Act_{zone} = roundedACST
set AHST_Act_{zone} = roundedAHST
endif
endif
endif
"""
#: In mixed mode (ScriptTypes 'vrf_mm' and 'ex_mm'), on the design days (DesignDay, a sensor of the schedule
#: 'ACCIS Design Days', 1 on the days of the types SummerDesignDay and WinterDesignDay), the zones are air-conditioned
#: as with full air-conditioning, with the windows closed, whether they are occupied or not: otherwise the HVAC systems
#: are off on the design days without occupants (often the winter design day) or while the windows are open, and
#: EnergyPlus sizes them for no load or a lower one (with the existing HVAC systems, it then stopped, or they could
#: not heat or cool). At the end of the programs, without nesting the blocks IF deeper: EnergyPlus allows 5 levels of
#: nested IF blocks (IfDepthAllowed), and the mixed mode bodies already have 5.
_DESIGN_DAY_ZONE = """
if DesignDay == 1
set VentHours_{zone} = 0
set ACST_Act_{zone} = roundedACST
set AHST_Act_{zone} = roundedAHST
endif
"""
_DESIGN_DAY_WINDOW = """
if DesignDay == 1
set {window}_VentOpenFact = 0
endif
"""

#: Setpoints and ventilation of a zone in mixed mode, with the VRF systems of accim, air-conditioned on the design
#: days.
APPLY_AST_MIXED_MODE = _join(_HVAC_OFF_FROM_COILS.replace('{name}', '{zone}'), _APPLY_AST_MIXED_MODE_BODY,
                             _DESIGN_DAY_ZONE)
#: The same with the existing HVAC systems (ScriptType 'ex_mm').
APPLY_AST_MIXED_MODE_EXISTING_HVAC = _join(_HVAC_OFF_FROM_LOAD.replace('{name}', '{zone}'), _APPLY_AST_MIXED_MODE_BODY,
                                           _DESIGN_DAY_ZONE)

#: Venting opening factor of a window or door.
SET_MY_VOF = _lines("""
set slope = (1 - MultiplierVOF) / (MinTempDiffVOF - MaxTempDiffVOF)
if {window}_OutT > 0
set {window}_TempDiffVOF = {window}_OpT - {window}_OutT
else
set {window}_TempDiffVOF = {window}_OpT + {window}_OutT
endif
if {window}_OutT > {window}_OpT
set {window}_MyVOF = 0
else
if {window}_TempDiffVOF > MaxTempDiffVOF
set {window}_MyVOF = MultiplierVOF
elseif {window}_TempDiffVOF < MinTempDiffVOF
set {window}_MyVOF = 1.0
else
set {window}_MyVOF = slope*{window}_TempDiffVOF - slope*MinTempDiffVOF + 1
endif
endif
""")

#: Opening of a window or door in mixed mode (after the lines that set NoH_NoC_reqs).
_SET_WINDOW_OPERATION_BODY = """
if {window}_OpT<roundedACST
if {window}_WindSpeed <= MaxWindSpeed
if {window}_OutT>MinOutTemp
if {window}_OutT < {window}_OpT
if {window}_Occ_count > 0
set meets_base_reqs = 1
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
else
set meets_base_reqs = 0
endif
if (NoH_NoC_reqs == 1) && (meets_base_reqs == 1)
if {window}_OpT>VST
set Ventilates_HVACmode2_{window} = 1
else
set Ventilates_HVACmode2_{window} = 0
endif
else
set Ventilates_HVACmode2_{window} = 0
endif
if VentCtrl == 0
if {window}_OutT < {window}_OpT
if {window}_OutT>MinOutTemp
if {window}_OpT > VST
if {window}_WindSpeed <= MaxWindSpeed
set Ventilates_HVACmode1_{window} = 1
else
set Ventilates_HVACmode1_{window} = 0
endif
else
set Ventilates_HVACmode1_{window} = 0
endif
else
set Ventilates_HVACmode1_{window} = 0
endif
else
set Ventilates_HVACmode1_{window} = 0
endif
elseif VentCtrl == 1
if {window}_OutT<{window}_OpT
if {window}_OutT>MinOutTemp
if {window}_OpT > ACSTnoTol
if {window}_WindSpeed <= MaxWindSpeed
set Ventilates_HVACmode1_{window} = 1
else
set Ventilates_HVACmode1_{window} = 0
endif
else
set Ventilates_HVACmode1_{window} = 0
endif
else
set Ventilates_HVACmode1_{window} = 0
endif
else
set Ventilates_HVACmode1_{window} = 0
endif
endif
if HVACmode == 0
set {window}_VentOpenFact = 0
elseif HVACmode == 1
if Ventilates_HVACmode1_{window} == 1
set {window}_VentOpenFact = {window}_MyVOF
else
set {window}_VentOpenFact = 0
endif
elseif HVACmode == 2
if Ventilates_HVACmode2_{window} == 1
if (VentCtrl==0) || (VentCtrl==1)
set {window}_VentOpenFact = 1
elseif (VentCtrl==2) || (VentCtrl==3)
set {window}_VentOpenFact = {window}_MyVOF
endif
else
set {window}_VentOpenFact = 0
endif
endif
"""
#: Opening of a window or door in mixed mode, with the VRF systems of accim, closed on the design days.
SET_WINDOW_OPERATION = _join(_HVAC_OFF_FROM_COILS.replace('{name}', '{window}'), _SET_WINDOW_OPERATION_BODY,
                             _DESIGN_DAY_WINDOW)
#: The same with the existing HVAC systems (ScriptType 'ex_mm').
SET_WINDOW_OPERATION_EXISTING_HVAC = _join(_HVAC_OFF_FROM_LOAD.replace('{name}', '{window}'),
                                           _SET_WINDOW_OPERATION_BODY, _DESIGN_DAY_WINDOW)

#: Setpoints of a zone with full air-conditioning.
APPLY_AST_AIR_CONDITIONED = _lines("""
set ACST_Act_{zone} = ACST
set AHST_Act_{zone} = AHST
""")


# The comfort standards defined by their data -------------------------------------------------------------------------

#: The Erl branches of the built-in comfort standards defined by their data
#: (:func:`accim.sim.standards.built_in_definitions`), by comfort standard and program, as those of
#: :data:`REGISTERED_BRANCHES`: JPN Aqilah 2025 (23), whose comfort temperature is ``0.38·RMOT + 16.9``, applicable
#: from 5 to 30 °C, with the offsets ±2.0 K (category 80) and ±1.5 K (category 90) (Aqilah, Rijal, Yoshida & Nicol,
#: 2025, equation 8 and conclusions 5 and 6). They are added at the end of the chains above, which do not change, so
#: the output IDFs of the other comfort standards do not change either; :mod:`accim.sim.ems.standard_lines` writes the
#: same lines from the definition (tested). And the branches of CountHours and SetVST of IND IMAC R 7DRM (9), which
#: compares the outdoor metric that the EMS calculates for it (Tout_metric, the arithmetic mean of the 7 previous days,
#: :data:`accim.sim.ems.standard_lines.BUILT_IN_METRICS`) with its applicability limits; its other branches are in the
#: chains above.
BUILT_IN_BRANCHES: Dict[int, Dict[str, Tuple[str, ...]]] = {
    9: {
        'CountHours': ('elseif ComfStand == 9', *_count_hours_body(OUTDOOR_METRIC_VARIABLE).split('\n')),
        'SetVST': ('elseif ComfStand == 9',
                   f'if ({OUTDOOR_METRIC_VARIABLE} >= AHSTall) && ({OUTDOOR_METRIC_VARIABLE} <= ACSTaul)',
                   'set VST = ComfTemp+VSToffset', 'else', 'set VST = (roundedACST+roundedAHST)/2+VSToffset', 'endif'),
    },
    23: {
        'SetComfTemp': ('elseif ComfStand == 23', 'set ComfTemp = RMOT*0.38+16.9'),
        'SetAppLimits': ('elseif ComfStand == 23', 'set ACSTaul = 30', 'set ACSTall = 5', 'set AHSTaul = 30',
                         'set AHSTall = 5'),
        'ApplyCAT': ('elseif ComfStand == 23', 'if (CAT == 80)', 'set ACSToffset = 2+CATcoolOffset',
                     'set AHSToffset = -2+CATheatOffset', 'elseif (CAT == 90)', 'set ACSToffset = 1.5+CATcoolOffset',
                     'set AHSToffset = -1.5+CATheatOffset', 'endif'),
        'CountHours': ('elseif ComfStand == 23', *_count_hours_body('RMOT').split('\n')),
        'SetVST': ('elseif ComfStand == 23', 'if (RMOT >= AHSTall) && (RMOT <= ACSTaul)',
                   'set VST = ComfTemp+VSToffset', 'else', 'set VST = (roundedACST+roundedAHST)/2+VSToffset', 'endif'),
    },
}
#: The Erl branches of the comfort standards defined by their data
#: (:class:`~accim.sim.standards.ComfortStandardDefinition`, those of the registry of :mod:`accim.sim.standards`), by
#: comfort standard and program ('SetComfTemp', 'SetAppLimits', 'ApplyCAT', 'CountHours' and 'SetVST'): each one is a
#: branch ``elseif ComfStand == <n>`` of the chain of the program (none in 'CountHours' and 'SetVST' with PMOT, whose
#: branch ``else`` is that of PMOT). :mod:`accim.sim.ems.standard_lines` fills it when a comfort standard is
#: registered; the chains above are those of the built-in comfort standards, which do not change.
REGISTERED_BRANCHES: Dict[int, Dict[str, Tuple[str, ...]]] = {}
#: The first lines of the branch of SET_VST of the comfort standards that compare PMOT with their limits
_VST_GENERIC_BRANCH = ['else', 'if (PMOT >= AHSTall) && (PMOT <= ACSTaul)', 'set VST = ComfTemp+VSToffset']
_REGISTERED_CONDITION = re.compile(r'^elseif\s+ComfStand\s*==\s*(\d+)$', re.IGNORECASE)


def _all_branches() -> Dict[int, Dict[str, Tuple[str, ...]]]:
    """The branches of the built-in comfort standards defined by their data and those of the registry."""
    return {**BUILT_IN_BRANCHES, **REGISTERED_BRANCHES}


def _registered(program: str, comfort_standards: Optional[Iterable[int]] = None) -> List[str]:
    """The branches of a program of the comfort standards defined by their data, built in and registered (of some of
    them only), in the order of their numbers."""
    wanted = None if comfort_standards is None else {int(n) for n in comfort_standards}
    branches = _all_branches()
    lines: List[str] = []
    for number in sorted(branches):
        if wanted is None or number in wanted:
            lines.extend(branches[number].get(program, ()))
    return lines


def _insert_in_chain(lines: Iterable[str], branches: List[str], before_else: bool) -> Tuple[str, ...]:
    """The lines of a chain ``if ... endif`` with some branches ``elseif ...`` added at its top level: before its
    branch ``else`` (with ``before_else``, if it has one), or before its last ``endif``."""
    lines = list(lines)
    if not branches:
        return tuple(lines)
    depth, else_index, end_index = 0, None, None
    for index, line in enumerate(lines):
        keyword = line.strip().split(' ', 1)[0].upper()
        if keyword == 'ELSE' and depth == 1:
            else_index = index
        if keyword in ('IF', 'WHILE'):
            depth += 1
        elif keyword in ('ENDIF', 'ENDWHILE'):
            depth -= 1
            if depth == 0:
                end_index = index
    position = else_index if before_else and else_index is not None else end_index
    return tuple(lines[:position] + branches + lines[position:])


def set_comf_temp_lines(outdoor_metric: bool = False) -> Tuple[str, ...]:
    """SET_COMF_TEMP (SET_COMF_TEMP_OUTDOOR_METRIC with ``outdoor_metric``) with the branches of the comfort standards
    defined by their data, built in (:data:`BUILT_IN_BRANCHES`) and registered (:data:`REGISTERED_BRANCHES`), before
    its last ``endif``: the chain of all the comfort standards."""
    base = SET_COMF_TEMP_OUTDOOR_METRIC if outdoor_metric else SET_COMF_TEMP
    return _insert_in_chain(base, _registered('SetComfTemp'), before_else=False)


def set_app_limits_lines() -> Tuple[str, ...]:
    """SET_APP_LIMITS with the branches of the comfort standards defined by their data, before its branch ``else``."""
    return _insert_in_chain(SET_APP_LIMITS, _registered('SetAppLimits'), before_else=True)


def apply_cat_lines() -> Tuple[str, ...]:
    """APPLY_CAT with the branches of the comfort standards defined by their data."""
    return _insert_in_chain(APPLY_CAT, _registered('ApplyCAT'), before_else=False)


def count_hours_lines(outdoor_metric: bool = False) -> Tuple[str, ...]:
    """COUNT_HOURS (COUNT_HOURS_OUTDOOR_METRIC with ``outdoor_metric``) with the branches of the comfort standards
    defined by their data that do not compare PMOT with their limits, before its branch ``else`` (that of PMOT)."""
    base = COUNT_HOURS_OUTDOOR_METRIC if outdoor_metric else COUNT_HOURS
    return _insert_in_chain(base, _registered('CountHours'), before_else=True)


def set_vst_lines(outdoor_metric: bool = False, comfort_standards: Optional[Iterable[int]] = None) -> Tuple[str, ...]:
    """SET_VST (SET_VST_OUTDOOR_METRIC with ``outdoor_metric``) with the branches of the comfort standards defined by
    their data that do not compare PMOT with their limits (of some of them only, or of all of them), before the branch
    of those that compare PMOT."""
    lines = list(SET_VST_OUTDOOR_METRIC if outdoor_metric else SET_VST)
    branches = _registered('SetVST', comfort_standards)
    if not branches:
        return tuple(lines)
    index = next(n for n in range(len(lines)) if lines[n:n + len(_VST_GENERIC_BRANCH)] == _VST_GENERIC_BRANCH)
    return tuple(lines[:index] + branches + lines[index:])


def registered_standards_in(lines: Iterable[str]) -> Set[int]:
    """The comfort standards defined by their data, built in or registered, whose branches
    (``elseif ComfStand == <n>``) some lines have."""
    branches = _all_branches()
    found = set()
    for line in lines:
        match = _REGISTERED_CONDITION.match(str(line).strip())
        if match and int(match.group(1)) in branches:
            found.add(int(match.group(1)))
    return found
