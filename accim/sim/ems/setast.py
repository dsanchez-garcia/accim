# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""EMS programs that set the adaptive setpoint temperatures (SetAST).

SetAST runs SetAST_Master, which calculates CoolingSeason and runs the subprograms of the comfort
standard of SetInputData (``SetAST_CS<ComfStand>_<chunk>``). Each subprogram holds the lines of up
to 3 comfort modes, so that no program exceeds the limit of program lines of EnergyPlus; the
subprograms of the comfort standards whose setpoints do not depend on the comfort mode (ESP CTE and
INT ISO7730) set them whatever ComfMod is. Each output IDF also appends to SetAST the lines of its
comfort standard and comfort mode.
"""

import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from accim.sim.ems.setpoint_lines import ROUNDING, SETPOINT_LINES

__all__ = [
    'MODULAR_COMFORT_MODES',
    'depends_on_comfort_mode',
    'get_setpoint_lines',
    'has_setpoints',
    'master_program_lines',
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
    99: [3],
}
_CHUNK_SIZE = 3
_SETPOINT = re.compile(r'^set (ACST|AHST) = ', re.IGNORECASE)


def _own_lines(comf_stand: int, comf_mod: Number) -> Tuple[str, ...]:
    return SETPOINT_LINES.get((comf_stand, comf_mod), SETPOINT_LINES.get((comf_stand, None), ()))


def get_setpoint_lines(comf_stand: int, comf_mod: Number) -> List[str]:
    """The Erl lines that set ACST and AHST for a comfort standard and a comfort mode, with the rounding."""
    return list(_own_lines(comf_stand, comf_mod)) + list(ROUNDING)


def has_setpoints(comf_stand: int, comf_mod: Number) -> bool:
    """True if the comfort standard defines both setpoints for the comfort mode.

    Without them, EnergyPlus stops at the first timestep ('ACST' used in an expression before it is set).
    """
    found = {match.group(1).upper() for line in _own_lines(comf_stand, comf_mod) if (match := _SETPOINT.match(line))}
    return found == {'ACST', 'AHST'}


def _chunks(values: Sequence) -> List[Sequence]:
    return [values[i:i + _CHUNK_SIZE] for i in range(0, len(values), _CHUNK_SIZE)]


def master_program_lines() -> List[str]:
    """Lines of SetAST_Master: the cooling season and the subprograms of the comfort standard."""
    lines = [
        '! SetAST_Master - Evaluates Season and Routes to ComfStand-specific SetAST subprograms',
        '! Season calculation logic',
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
    ]
    for comf_stand, comf_mods in MODULAR_COMFORT_MODES.items():
        lines.append(f'if (ComfStand == {comf_stand})')
        lines.extend(f'run SetAST_CS{comf_stand}_{n}' for n in range(len(_chunks(comf_mods))))
        lines.append('endif')
    return lines


def _subprogram_lines(comf_stand: int, chunk: int, comf_mods: Sequence[Number]) -> List[str]:
    name = f'SetAST_CS{comf_stand}_{chunk}'
    if not depends_on_comfort_mode(comf_stand):
        # The static standards (ESP CTE, INT ISO7730) set the same setpoints whatever ComfMod is, so they also work
        # with the ComfMod of SetInputData when it is not 0, as in the models of the parametric module
        return [
            f'! {name}',
            f'! SetAST subprogram for ComfStand == {comf_stand}, Chunk {chunk}',
            '! The setpoints of this ComfStand do not depend on ComfMod',
            *get_setpoint_lines(comf_stand, comf_mods[0]),
        ]
    lines = [
        f'! {name}',
        f'! SetAST subprogram for ComfStand == {comf_stand}, Chunk {chunk}',
        '! ComfMod is resolved internally via if/elseif blocks',
    ]
    for n, comf_mod in enumerate(comf_mods):
        keyword = 'if' if n == 0 else 'elseif'
        text = str(int(comf_mod)) if comf_mod == int(comf_mod) else str(comf_mod)
        lines.append(f'{keyword} (ComfMod == {text})')
        lines.extend(get_setpoint_lines(comf_stand, comf_mod))
    if comf_mods:
        lines.append('endif')
    return lines


def depends_on_comfort_mode(comf_stand: int) -> bool:
    """False for the comfort standards whose setpoints are the same in every comfort mode (ESP CTE, INT ISO7730)."""
    return [mode for stand, mode in SETPOINT_LINES if stand == comf_stand] != [None]


def subprograms(comf_stands: Optional[Iterable[int]] = None) -> Dict[str, List[str]]:
    """Name and lines of each subprogram ``SetAST_CS<ComfStand>_<chunk>`` (of all the comfort standards, by default)."""
    selected = MODULAR_COMFORT_MODES if comf_stands is None else set(comf_stands)
    programs = {}
    for comf_stand, comf_mods in MODULAR_COMFORT_MODES.items():
        if comf_stand not in selected:
            continue
        for chunk, chunk_mods in enumerate(_chunks(comf_mods)):
            programs[f'SetAST_CS{comf_stand}_{chunk}'] = _subprogram_lines(comf_stand, chunk, chunk_mods)
    return programs
