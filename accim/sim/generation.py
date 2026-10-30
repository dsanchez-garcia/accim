# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Output IDFs of :class:`accim.sim.accis.AddAccis`: one for each combination of the arguments.

All the output IDFs of an input IDF share every object but a few EMS programs (SetInputData, SetAST,
ApplyCAT, SetAppLimits and SetVOFinputData). The text of the other objects is written once, and only
those programs are written for each output IDF, which gives the files that eppy would save, faster.
"""

import math
import os
import platform
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Union

import numpy as np

from accim.sim.arguments import as_list, to_day_of_year
from accim.sim.ems.setast import get_setpoint_lines, has_setpoints
from accim.sim.idf_tools import replace_program_lines, set_program_lines
from accim.sim.standards import COMFORT_STANDARDS

__all__ = ['Combination', 'GenerationArguments', 'IdfWriter', 'OutputIdfs', 'combinations', 'output_name']

Number = Union[int, float]
_STATIC_MODES = (0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5)
#: Lines 5 to 8 of SetInputData in the output IDFs with HVACmode 0, where ventilation is not used
_NO_VENTILATION_LINES = ('set VentCtrl = 0', 'set VSToffset = 0', 'set MinOToffset = 7', 'set MaxWindSpeed = 6')
_MUTABLE_PROGRAMS = ('SetInputData', 'SetAST', 'ApplyCAT', 'SetAppLimits', 'SetVOFinputData')


@dataclass
class GenerationArguments:
    """Arguments of the output IDFs (the lists give one output IDF for each combination of their values)."""

    comf_stand: List[int]
    cat: List[Number]
    comf_mod: List[Number]
    hvac_mode: List[int] = field(default_factory=lambda: [0])
    vent_ctrl: List[int] = field(default_factory=lambda: [0])
    setpoint_acc: Number = 10000
    cat_cool_offset: Number = 0
    cat_heat_offset: Number = 0
    cust_ast_acst_aul: Number = 0
    cust_ast_acst_all: Number = 0
    cust_ast_ahst_aul: Number = 0
    cust_ast_ahst_all: Number = 0
    cust_ast_m: Number = 0
    cust_ast_n: Number = 0
    cust_ast_acst_offset: Number = 0
    cust_ast_ahst_offset: Number = 0
    cool_season_start: int = 121
    cool_season_end: int = 274
    max_temp_diff_vof: Number = 6
    min_temp_diff_vof: Number = 1
    multiplier_vof: Number = 0.25
    vst_offset: List[float] = field(default_factory=lambda: [0.0])
    min_ot_offset: List[float] = field(default_factory=lambda: [50.0])
    max_wind_speed: List[float] = field(default_factory=lambda: [50.0])
    ast_tol_start: Number = 0.1
    ast_tol_end_input: Number = 0.1
    ast_tol_steps: Number = 0.1
    name_suffix: str = ''

    def __post_init__(self):
        self.comf_stand = as_list(self.comf_stand)
        self.cat = as_list(self.cat)
        self.comf_mod = as_list(self.comf_mod)
        self.hvac_mode = as_list(self.hvac_mode)
        self.vent_ctrl = as_list(self.vent_ctrl)
        self.vst_offset = [float(v) for v in as_list(self.vst_offset)]
        self.min_ot_offset = [float(v) for v in as_list(self.min_ot_offset)]
        self.max_wind_speed = [float(v) for v in as_list(self.max_wind_speed)]
        self.cool_season_start = to_day_of_year(self.cool_season_start, 'cool_season_start')
        self.cool_season_end = to_day_of_year(self.cool_season_end, 'cool_season_end')
        if self.name_suffix is None:
            self.name_suffix = ''

    @classmethod
    def air_conditioned(cls, **kwargs) -> 'GenerationArguments':
        """The arguments for full air-conditioning (no natural ventilation): HVACmode 0 only."""
        kwargs.update(hvac_mode=[0], vent_ctrl=[0], vst_offset=[0], min_ot_offset=[0], max_wind_speed=[0],
                      max_temp_diff_vof=1, min_temp_diff_vof=0, multiplier_vof=0)
        return cls(**kwargs)

    def tolerances(self) -> List[float]:
        """The setpoint tolerances, from ast_tol_start to ast_tol_end_input (both included) in steps of ast_tol_steps.

        The values are those of ``numpy.arange``, but their number does not depend on the rounding of the floats
        (``numpy.arange(0.1, 0.3 + 0.1, 0.1)`` gives 0.4 too).
        """
        start, step = round(self.ast_tol_start, 2), round(self.ast_tol_steps, 2)
        stop = round(self.ast_tol_end_input + self.ast_tol_steps, 2)
        if step <= 0:
            raise ValueError(f'ast_tol_steps must be greater than 0 (it is {self.ast_tol_steps}).')
        count = math.ceil((stop - start) / step - 1e-6)
        if count <= 0:
            return []
        return np.arange(start, start + (count - 0.5) * step, step).tolist()


@dataclass(frozen=True)
class Combination:
    """The arguments of one output IDF. None is not applicable ('X' in the name of the file)."""

    comf_stand: Optional[int]
    cat: Optional[Number]
    comf_mod: Optional[Number]
    hvac_mode: int
    vent_ctrl: Optional[int]
    vst_offset: Optional[float]
    min_ot_offset: Optional[float]
    max_wind_speed: Optional[float]
    ast_tol: Optional[float]

    @property
    def is_pmv(self) -> bool:
        return self.comf_stand is None


def _generates(comf_stand: int, cat: Number, comf_mod: Number) -> bool:
    """The combinations of ComfStand, CAT and ComfMod that give an output IDF (as in accim 0.x)."""
    if comf_stand in (1, 4, 5, 22):
        if comf_stand in (1, 22) and cat not in range(0, 4):
            return False
        if comf_stand in (4, 5) and cat not in (1, 2):
            return False
        if comf_mod in _STATIC_MODES:
            return False
        return not (comf_stand == 22 and comf_mod != 0)
    if comf_stand in (2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21) and cat not in range(80, 91, 10):
        return False
    if comf_stand in (7, 8) and cat not in range(80, 91, 5):
        return False
    if comf_stand in (13, 14) and comf_mod in (0, 1):
        return False
    if comf_stand not in (13, 14) and comf_mod in _STATIC_MODES:
        return False
    return not (comf_stand == 21 and comf_mod not in (2, 3))


def _ventilation(args: GenerationArguments, comf_stand, cat, comf_mod) -> Iterator[Combination]:
    for hvac_mode in args.hvac_mode:
        if hvac_mode == 0:
            for tol in args.tolerances():
                yield Combination(comf_stand, cat, comf_mod, hvac_mode, None, None, None, None, tol)
            continue
        for vent_ctrl in args.vent_ctrl:
            # Natural ventilation (HVACmode 1) only has the ventilation controls 0 and 1
            if hvac_mode == 1 and vent_ctrl in (2, 3):
                continue
            for vst_offset in args.vst_offset:
                for min_ot_offset in args.min_ot_offset:
                    for max_wind_speed in args.max_wind_speed:
                        for tol in args.tolerances():
                            yield Combination(comf_stand, cat, comf_mod, hvac_mode, vent_ctrl, vst_offset,
                                              min_ot_offset, max_wind_speed, tol)


def combinations(args: GenerationArguments, temp_ctrl: str = 'temperature') -> Iterator[Combination]:
    """The combinations of the arguments, in the order of the output IDFs.

    The combinations whose comfort standard has no setpoints for the comfort mode are skipped with a warning.
    """
    if temp_ctrl == 'pmv':
        yield Combination(None, None, None, 0, None, None, None, None, None)
        return
    skipped = []
    for comf_stand in args.comf_stand:
        if comf_stand == 0:
            yield from _ventilation(args, 0, None, None)
            continue
        if comf_stand not in COMFORT_STANDARDS:
            continue
        for cat in args.cat:
            for comf_mod in args.comf_mod:
                if not _generates(comf_stand, cat, comf_mod):
                    continue
                if not has_setpoints(comf_stand, comf_mod):
                    skipped.append((comf_stand, comf_mod))
                    continue
                yield from _ventilation(args, comf_stand, cat, comf_mod)
    if skipped:
        warnings.warn(f'The combinations of (ComfStand, ComfMod) {sorted(set(skipped))} have no setpoints, so no '
                      f'output IDF has been generated for them.', UserWarning, stacklevel=3)


def _x(value) -> str:
    return 'X' if value is None else str(value)


def output_name(stem: str, combination: Combination, name_suffix: str = '') -> str:
    """The name of the output IDF of a combination, from the name of the input IDF without '.idf'."""
    suffix = '[NS_X' if name_suffix == '' else f'[NS_{name_suffix}'
    if combination.is_pmv:
        return f'{stem}[CS_PMV[CA_X[CM_X[HM_0[VC_X[VO_X[MT_X[MW_X[AT_X{suffix}.idf'
    c = combination
    return (f'{stem}[CS_{COMFORT_STANDARDS[c.comf_stand].label}[CA_{_x(c.cat)}[CM_{_x(c.comf_mod)}'
            f'[HM_{c.hvac_mode}[VC_{_x(c.vent_ctrl)}[VO_{_x(c.vst_offset)}[MT_{_x(c.min_ot_offset)}'
            f'[MW_{_x(c.max_wind_speed)}[AT_{round(c.ast_tol, 2)}{suffix}.idf')


def _save_text(text: str) -> bytes:
    """The bytes that eppy writes for the text of an IDF (IDF.save with the default line endings)."""
    text = f'!- {platform.system()} Line endings \n' + text
    return os.linesep.join(text.splitlines()).encode('latin-1')


class IdfWriter:
    """Writes the output IDFs of a model, with the programs of each combination.

    :param idf: The model, with the EMS programs of ACCIS.
    :param args: The arguments of the output IDFs.
    :param temp_ctrl: 'temperature' or 'pmv'.
    """

    def __init__(self, idf, args: GenerationArguments, temp_ctrl: str = 'temperature'):
        self.idf = idf
        self.args = args
        self.temp_ctrl = temp_ctrl
        programs = {p.Name: p for p in idf.idfobjects['EnergyManagementSystem:Program']}
        self.programs = {name: programs.get(name) for name in _MUTABLE_PROGRAMS}
        mutable = {id(p) for p in self.programs.values() if p is not None}
        self._parts: List[Union[str, object]] = []
        static: List[str] = []
        for object_type in idf.model.dtls:
            for obj in idf.idfobjects[object_type]:
                if id(obj) in mutable:
                    self._parts.append(''.join(static))
                    self._parts.append(obj)
                    static = []
                else:
                    static.append(obj.__repr__())
        self._parts.append(''.join(static))
        self._set_constant_lines()

    def _set_constant_lines(self) -> None:
        """Set the lines that are the same in all the output IDFs: the venting opening factor and, with
        temperature control, the custom model and the CAT offsets."""
        a = self.args
        p = self.programs
        if p['SetVOFinputData'] is not None:
            set_program_lines(p['SetVOFinputData'], [f'set MaxTempDiffVOF = {a.max_temp_diff_vof}',
                                                     f'set MinTempDiffVOF = {a.min_temp_diff_vof}',
                                                     f'set MultiplierVOF = {a.multiplier_vof}'])
        if self.temp_ctrl == 'pmv':
            return
        if p['SetAppLimits'] is not None:
            set_program_lines(p['SetAppLimits'], [f'set ACSTaul = {a.cust_ast_acst_aul}', f'set ACSTall = {a.cust_ast_acst_all}',
                                                  f'set AHSTaul = {a.cust_ast_ahst_aul}', f'set AHSTall = {a.cust_ast_ahst_all}'],
                              first=2)
        if p['ApplyCAT'] is not None:
            set_program_lines(p['ApplyCAT'], [f'set CATcoolOffset = {a.cat_cool_offset}',
                                              f'set CATheatOffset = {a.cat_heat_offset}'])
            set_program_lines(p['ApplyCAT'], [f'set ACSToffset = {a.cust_ast_acst_offset} + {a.cat_cool_offset}',
                                              f'set AHSToffset = {a.cust_ast_ahst_offset} + {a.cat_heat_offset}'],
                              first=4)

    def _set_lines(self, combination: Combination) -> None:
        a = self.args
        p = self.programs
        if combination.is_pmv:
            # The Fanger thermostats control the zones: SetInputData and SetAST keep their base lines
            p['SetInputData'].Program_Line_4 = 'set HVACmode = 0'
            return
        c = combination
        cat = 1 if c.comf_stand == 0 else c.cat
        comf_mod = 0 if c.comf_stand == 0 else c.comf_mod
        if c.hvac_mode == 0:
            ventilation = list(_NO_VENTILATION_LINES)
        else:
            ventilation = [f'set VentCtrl = {c.vent_ctrl}', f'set VSToffset = {c.vst_offset}',
                           f'set MinOToffset = {c.min_ot_offset}', f'set MaxWindSpeed = {c.max_wind_speed}']
        set_program_lines(p['SetInputData'], [
            f'set ComfStand = {c.comf_stand}', f'set CAT = {cat}', f'set ComfMod = {comf_mod}',
            f'set HVACmode = {c.hvac_mode}', *ventilation, f'set ACSTtol = {-c.ast_tol}',
            f'set AHSTtol = {c.ast_tol}', f'set CoolSeasonStart = {a.cool_season_start}',
            f'set CoolSeasonEnd = {a.cool_season_end}'])
        # SetAST: the setpoint accuracy, the custom model, 'run SetAST_Master' and the lines of the comfort model
        replace_program_lines(p['SetAST'], [f'set SetpointAcc = {a.setpoint_acc}', f'set m = {a.cust_ast_m}',
                                            f'set n = {a.cust_ast_n}', 'run SetAST_Master',
                                            *get_setpoint_lines(c.comf_stand, comf_mod)])

    def text(self, combination: Combination) -> str:
        """The text of the output IDF of a combination (as eppy's IDF.idfstr)."""
        self._set_lines(combination)
        return ''.join(part if isinstance(part, str) else part.__repr__() for part in self._parts)

    def write(self, path: Union[str, os.PathLike], combination: Combination) -> None:
        """Write the output IDF of a combination."""
        with open(path, 'wb') as file:
            file.write(_save_text(self.text(combination)))


class OutputIdfs(Mapping):
    """The output IDFs by file name. Each one is read (as an IDF object of eppy) the first time it is used.

    :param paths: The path of each output IDF, by file name.
    :param idf_class: The class of the IDF objects (eppy's IDF or a subclass, with the IDD already set).
    """

    def __init__(self, paths: Dict[str, str], idf_class):
        self.paths = dict(paths)
        self._idf_class = idf_class
        self._idfs: Dict[str, object] = {}

    def __getitem__(self, name: str):
        if name not in self._idfs:
            self._idfs[name] = self._idf_class(self.paths[name])
        return self._idfs[name]

    def __iter__(self):
        return iter(self.paths)

    def __len__(self) -> int:
        return len(self.paths)

    def __repr__(self) -> str:
        return f'OutputIdfs({self.paths!r})'
