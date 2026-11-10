# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""EMS programs that set the adaptive setpoint temperatures (SetAST).

SetAST runs SetAST_Master, which calculates CoolingSeason and runs the subprograms of the comfort
standard of the zone being run (its program SetInputData_<zone>, ``SetAST_CS<ComfStand>_<chunk>``). Each
subprogram holds the lines of up to 3 comfort modes, so that no program exceeds the limit of program lines of
EnergyPlus; the subprograms of the comfort standards whose setpoints do not depend on the comfort mode (ESP CTE
and INT ISO7730) set them whatever ComfMod is.
"""

import re
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from accim.sim.ems.program_lines import OUTDOOR_METRIC_VARIABLE
from accim.sim.ems.setpoint_lines import ROUNDING, SETPOINT_LINES

__all__ = [
    'COOLING_SEASON_LINES',
    'CUSTOM_COMFORT_STANDARD',
    'MODULAR_COMFORT_MODES',
    'depends_on_comfort_mode',
    'get_setpoint_lines',
    'has_setpoints',
    'master_program_lines',
    'subprogram_comfort_standards',
    'subprogram_name',
    'subprograms',
]

Number = Union[int, float]

#: Comfort modes in the subprograms of each comfort standard. It must stay in sync with the valid
#: combinations of the parametric module (``funcs_for_besos.param_accis``).
MODULAR_COMFORT_MODES: Dict[int, List[Number]] = {
    0: [0],
    1: [0, 1, 2, 3],
    2: [0, 1, 2, 3],
    3: [0, 1, 2, 3],
    4: [3],
    5: [3],
    6: [0, 1, 2, 3],
    7: [0, 1, 2, 3],
    8: [0, 1, 2, 3],
    9: [0, 1, 2, 3],
    10: [0, 1, 2, 3],
    11: [0, 1, 2, 3],
    12: [0, 1, 2, 3],
    13: [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3],
    14: [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3],
    15: [0, 1, 2, 3],
    16: [0, 1, 2, 3],
    17: [0, 1, 2, 3],
    18: [0, 1, 2, 3],
    19: [0, 1, 2, 3],
    20: [0, 1, 2, 3],
    21: [2, 3],
    22: [0],
    23: [0, 1, 2, 3],
    99: [3],
}
_CHUNK_SIZE = 3
_SETPOINT = re.compile(r'^set (ACST|AHST) = ', re.IGNORECASE)
_SUBPROGRAM_NAME = re.compile(r'^SetAST_CS(\d+)_\d+$', re.IGNORECASE)
#: The comfort standard of the custom model, and the sensor of its outdoor temperature without the EMS code of its
#: outdoor metric
CUSTOM_COMFORT_STANDARD = 99
_PMOT = re.compile(r'\bPMOT\b')
#: The Erl lines that set CoolingSeason (1 in the cooling season, from CoolSeasonStart to the day before CoolSeasonEnd,
#: which can be in the next year; 0 otherwise). SetAST_Master and the aPMV setpoints run them.
COOLING_SEASON_LINES = (
    'if CoolSeasonEnd > CoolSeasonStart',
    'if (DayOfYear >= CoolSeasonStart) && (DayOfYear < CoolSeasonEnd)',
    'set CoolingSeason = 1',
    'else',
    'set CoolingSeason = 0',
    'endif',
    'elseif CoolSeasonStart > CoolSeasonEnd',
    'if (DayOfYear >= CoolSeasonStart) || (DayOfYear < CoolSeasonEnd)',
    'set CoolingSeason = 1',
    'else',
    'set CoolingSeason = 0',
    'endif',
    'endif',
)


def _own_lines(comfort_standard: int, comfort_mode: Number, outdoor_metric: bool = False) -> Tuple[str, ...]:
    lines = SETPOINT_LINES.get((comfort_standard, comfort_mode), SETPOINT_LINES.get((comfort_standard, None), ()))
    if outdoor_metric and comfort_standard == CUSTOM_COMFORT_STANDARD:
        # The custom model with the EMS code of its outdoor metric (accim.sim.ems.outdoor_metric)
        lines = tuple(_PMOT.sub(OUTDOOR_METRIC_VARIABLE, line) for line in lines)
    return lines


def get_setpoint_lines(comfort_standard: int, comfort_mode: Number, outdoor_metric: bool = False) -> List[str]:
    """The Erl lines that set ACST and AHST for a comfort standard and a comfort mode, with the rounding.

    :param outdoor_metric: True for the models with the EMS code of the outdoor metric of the custom model
        (:mod:`accim.sim.ems.outdoor_metric`), whose lines of the custom model use its outdoor metric, Tout_metric,
        instead of PMOT.
    """
    return list(_own_lines(comfort_standard, comfort_mode, outdoor_metric)) + list(ROUNDING)


def has_setpoints(comfort_standard: int, comfort_mode: Number) -> bool:
    """True if the comfort standard defines both setpoints for the comfort mode.

    Without them, EnergyPlus stops at the first timestep ('ACST' used in an expression before it is set).
    """
    found = {match.group(1).upper() for line in _own_lines(comfort_standard, comfort_mode) if (match := _SETPOINT.match(line))}
    return found == {'ACST', 'AHST'}


def _chunks(values: Sequence) -> List[Sequence]:
    return [values[i:i + _CHUNK_SIZE] for i in range(0, len(values), _CHUNK_SIZE)]


def master_program_lines(comfort_standards: Optional[Iterable[int]] = None) -> List[str]:
    """Lines of SetAST_Master: the cooling season and the subprograms of the comfort standard (of some comfort
    standards only, or of all of them by default)."""
    selected = MODULAR_COMFORT_MODES if comfort_standards is None else set(comfort_standards)
    lines = [
        '! SetAST_Master - Evaluates Season and Routes to ComfStand-specific SetAST subprograms',
        '! Season calculation logic',
        *COOLING_SEASON_LINES,
    ]
    for comfort_standard, comfort_modes in MODULAR_COMFORT_MODES.items():
        if comfort_standard not in selected:
            continue
        lines.append(f'if (ComfStand == {comfort_standard})')
        lines.extend(f'run SetAST_CS{comfort_standard}_{n}' for n in range(len(_chunks(comfort_modes))))
        lines.append('endif')
    return lines


def _subprogram_lines(comfort_standard: int, chunk: int, comfort_modes: Sequence[Number],
                      outdoor_metric: bool = False) -> List[str]:
    name = f'SetAST_CS{comfort_standard}_{chunk}'
    if not depends_on_comfort_mode(comfort_standard):
        # The static standards (ESP CTE, INT ISO7730) set the same setpoints whatever ComfMod is, so they also work
        # with the ComfMod of the zone when it is not 0, as in the models of the parametric module
        return [
            f'! {name}',
            f'! SetAST subprogram for ComfStand == {comfort_standard}, Chunk {chunk}',
            '! The setpoints of this ComfStand do not depend on ComfMod',
            *get_setpoint_lines(comfort_standard, comfort_modes[0], outdoor_metric),
        ]
    lines = [
        f'! {name}',
        f'! SetAST subprogram for ComfStand == {comfort_standard}, Chunk {chunk}',
        '! ComfMod is resolved internally via if/elseif blocks',
    ]
    for n, comfort_mode in enumerate(comfort_modes):
        keyword = 'if' if n == 0 else 'elseif'
        text = str(int(comfort_mode)) if comfort_mode == int(comfort_mode) else str(comfort_mode)
        lines.append(f'{keyword} (ComfMod == {text})')
        lines.extend(get_setpoint_lines(comfort_standard, comfort_mode, outdoor_metric))
    if comfort_modes:
        lines.append('endif')
    return lines


def depends_on_comfort_mode(comfort_standard: int) -> bool:
    """False for the comfort standards whose setpoints are the same in every comfort mode (ESP CTE, INT ISO7730)."""
    return [mode for stand, mode in SETPOINT_LINES if stand == comfort_standard] != [None]


def subprograms(comfort_standards: Optional[Iterable[int]] = None,
                outdoor_metric: bool = False) -> Dict[str, List[str]]:
    """Name and lines of each subprogram ``SetAST_CS<ComfStand>_<chunk>`` (of all the comfort standards, by default).

    :param outdoor_metric: True for the models with the EMS code of the outdoor metric of the custom model (see
        :func:`get_setpoint_lines`).
    """
    selected = MODULAR_COMFORT_MODES if comfort_standards is None else set(comfort_standards)
    programs = {}
    for comfort_standard, comfort_modes in MODULAR_COMFORT_MODES.items():
        if comfort_standard not in selected:
            continue
        for chunk, chunk_mods in enumerate(_chunks(comfort_modes)):
            programs[f'SetAST_CS{comfort_standard}_{chunk}'] = _subprogram_lines(comfort_standard, chunk, chunk_mods,
                                                                                 outdoor_metric)
    return programs


def subprogram_name(comfort_standard: int, comfort_mode: Number) -> str:
    """The name of the subprogram ``SetAST_CS<ComfStand>_<chunk>`` with the setpoints of a comfort mode (the first one
    for the comfort standards whose setpoints do not depend on the comfort mode)."""
    comfort_modes = MODULAR_COMFORT_MODES[comfort_standard]
    chunk = comfort_modes.index(comfort_mode) // _CHUNK_SIZE if comfort_mode in comfort_modes else 0
    return f'SetAST_CS{comfort_standard}_{chunk}'


def subprogram_comfort_standards(idf) -> Set[int]:
    """The comfort standards whose subprograms ``SetAST_CS<ComfStand>_<chunk>`` a model has."""
    names = (program.Name for program in idf.idfobjects['EnergyManagementSystem:Program'])
    return {int(match.group(1)) for name in names if (match := _SUBPROGRAM_NAME.match(name))}
