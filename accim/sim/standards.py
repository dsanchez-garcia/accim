# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Catalogue of the comfort standards (ComfStand) of accim, with their categories and comfort modes."""

from dataclasses import dataclass, field
from typing import Dict, Union

__all__ = ['COMFORT_STANDARDS', 'ComfortStandard', 'get_comfort_standard']

Number = Union[int, float]

_STATIC_ISO = 'ISO 7730 Static setpoints'
_HORIZONTAL = 'Adaptive setpoints horizontally extended'
_ACCEPTABILITY_80_90 = {80: '80% acceptability', 90: '90% acceptability'}
_ACCEPTABILITY_80_85_90 = {80: '80% acceptability', 85: '85% acceptability', 90: '90% acceptability'}


@dataclass(frozen=True)
class ComfortStandard:
    """A comfort standard (ComfStand) of accim.

    :ivar number: The ComfStand number.
    :ivar label: The name in the names of the output IDFs (for instance '[CS_INT EN16798').
    :ivar title: The name in the messages (for instance '1 = INT EN16798').
    :ivar categories: The categories (CAT) and their descriptions; empty if the standard has none.
    :ivar comfort_modes: The comfort modes (ComfMod) and their descriptions.
    """

    number: int
    label: str
    title: str
    categories: Dict[Number, str] = field(default_factory=dict)
    comfort_modes: Dict[Number, str] = field(default_factory=dict)


def _adaptive_modes(model: str, local_static: str) -> Dict[Number, str]:
    return {
        0: f'{local_static} Static setpoints',
        1: f'{model} Model Adaptive setpoints when applicable, otherwise {local_static} Static setpoints',
        2: f'{model} Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
        3: f'{model} Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}',
    }


def _australian_modes(model: str) -> Dict[Number, str]:
    zones = {1: 'climate zones 1, 2 and 3', 2: 'climate zone 4', 3: 'climate zone 5', 4: 'climate zones 6 and 7',
             5: 'climate zone 8'}
    modes: Dict[Number, str] = {}
    for n, zone in zones.items():
        modes[round(0.1 * n, 1)] = f'Australian Building Code Static setpoints for {zone}'
    for n, zone in zones.items():
        modes[round(1 + 0.1 * n, 1)] = (f'{model} Model Adaptive setpoints when applicable, otherwise '
                                        f'Australian Building Code Static setpoints for {zone}')
    modes[2] = f'{model} Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}'
    modes[3] = f'{model} Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'
    return modes


def _mexican_modes(model: str) -> Dict[Number, str]:
    static = 'Relevant Static setpoints for Mexico'
    return {
        0: f'{static}: 20 for heating and 25 for cooling',
        1: f'{model} Model Adaptive setpoints when applicable, otherwise {static}',
        2: f'{model} Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
        3: f'{model} Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}',
    }


def _only_adaptive_modes(model: str, modes=(2, 3)) -> Dict[Number, str]:
    descriptions = {
        2: f'{model} Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
        3: f'{model} Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}',
    }
    return {m: descriptions[m] for m in modes}


_BRAZILIAN_STATIC = 'Brazilian Building Code Static setpoints (ABNT NBR 16401-2 Standard (2008))'

#: The comfort standards, by ComfStand number.
COMFORT_STANDARDS: Dict[int, ComfortStandard] = {s.number: s for s in [
    ComfortStandard(0, 'ESP CTE', '0 = ESP CTE'),
    ComfortStandard(1, 'INT EN16798', '1 = INT EN16798',
                    {1: 'EN16798 Category I', 2: 'EN16798 Category II', 3: 'EN16798 Category III'},
                    {0: 'EN16798 Static setpoints',
                     1: 'EN16798 Adaptive setpoints when applicable, otherwise CTE',
                     2: 'EN16798 Adaptive setpoints when applicable, otherwise EN16798 Static setpoints',
                     3: 'EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive setpoints '
                        'horizontally extended'}),
    ComfortStandard(2, 'INT ASHRAE55', '2 = INT ASHRAE55',
                    {80: 'ASHRAE 55 80% acceptability', 90: 'ASHRAE 55 90% acceptability'},
                    {0: _STATIC_ISO,
                     1: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise CTE',
                     2: f'ASHRAE 55 Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
                     3: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints '
                        'horizontally extended'}),
    ComfortStandard(3, 'JPN Rijal', '3 = JPN Rijal', _ACCEPTABILITY_80_90,
                    {0: 'COOLBIZ Static setpoints',
                     1: 'Rijal Model Adaptive setpoints when applicable, otherwise COOLBIZ Static setpoints',
                     2: f'Rijal Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
                     3: f'Rijal Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
    ComfortStandard(4, 'CHN GBT50785 Cold', '4 = CHN GBT50785 Cold',
                    {1: '90% acceptability', 2: '75-90% acceptability'},
                    {3: f'GBT50785 Cold Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
    ComfortStandard(5, 'CHN GBT50785 HotMild', '5 = CHN GBT50785 HotMild',
                    {1: '90% acceptability', 2: '75-90% acceptability'},
                    {3: f'GBT50785 HotMild Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
    ComfortStandard(6, 'CHN Yang', '6 = CHN Yang', _ACCEPTABILITY_80_90, _only_adaptive_modes('Yang')),
    ComfortStandard(7, 'IND IMAC C NV', '7 = IND IMAC C NV', _ACCEPTABILITY_80_85_90,
                    _adaptive_modes('IMAC C NV', 'Indian Building Code')),
    ComfortStandard(8, 'IND IMAC C MM', '8 = IND IMAC C MM', _ACCEPTABILITY_80_85_90,
                    _adaptive_modes('IMAC C MM', 'Indian Building Code')),
    ComfortStandard(9, 'IND IMAC R 7DRM', '9 = IND IMAC R 7DRM', _ACCEPTABILITY_80_90,
                    _adaptive_modes('IMAC R 7DRM', 'Indian Building Code')),
    ComfortStandard(10, 'IND IMAC R 30DRM', '10 = IND IMAC R 30DRM', _ACCEPTABILITY_80_90,
                    _adaptive_modes('IMAC R 30DRM', 'Indian Building Code')),
    ComfortStandard(11, 'IND Dhaka', '11 = IND Dhaka', _ACCEPTABILITY_80_90,
                    {m: d for m, d in _adaptive_modes('Dhaka', 'Indian Building Code').items() if m != 0}),
    ComfortStandard(12, 'ROU Udrea', '12 = ROM Udrea', _ACCEPTABILITY_80_90,
                    _adaptive_modes('Udrea', 'Romanian Building Code')),
    ComfortStandard(13, 'AUS Williamson', '13 = AUS Williamson', _ACCEPTABILITY_80_90,
                    _australian_modes('Williamson')),
    ComfortStandard(14, 'AUS DeDear', '14 = AUS DeDear', _ACCEPTABILITY_80_90, _australian_modes('DeDear')),
    ComfortStandard(15, 'BRA Rupp NV', '15 = BRA Rupp NV', _ACCEPTABILITY_80_90,
                    {0: _BRAZILIAN_STATIC,
                     1: 'Rupp NV Model Adaptive setpoints when applicable, otherwise Brazilian Building Code Static '
                        'setpoints',
                     2: f'Rupp NV Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
                     3: f'Rupp NV Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
    ComfortStandard(16, 'BRA Rupp AC', '16 = BRA Rupp AC', _ACCEPTABILITY_80_90,
                    {0: _BRAZILIAN_STATIC,
                     1: 'Rupp AC Model Adaptive setpoints when applicable, otherwise Brazilian Building Code Static '
                        'setpoints',
                     2: f'Rupp AC Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
                     3: f'Rupp AC Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
    ComfortStandard(17, 'MEX Oropeza Arid', '17 = MEX Oropeza Arid', _ACCEPTABILITY_80_90,
                    _mexican_modes('Oropeza Arid')),
    ComfortStandard(18, 'MEX Oropeza DryTropic', '18 = MEX Oropeza DryTropic', _ACCEPTABILITY_80_90,
                    _mexican_modes('Oropeza DryTropic')),
    ComfortStandard(19, 'MEX Oropeza Temperate', '19 = MEX Oropeza Temperate', _ACCEPTABILITY_80_90,
                    _mexican_modes('Oropeza Temperate')),
    ComfortStandard(20, 'MEX Oropeza HumTropic', '20 = MEX Oropeza HumTropic', _ACCEPTABILITY_80_90,
                    _mexican_modes('Oropeza HumTropic')),
    ComfortStandard(21, 'CHL Perez-Fargallo', '21 = CHL Perez-Fargallo', _ACCEPTABILITY_80_90,
                    _only_adaptive_modes('Perez-Fargallo')),
    ComfortStandard(22, 'INT ISO7730', '22 = INT ISO7730',
                    {1: 'Cat A: -0.2 < PMV < 0.2; PPD < 6%', 2: 'Cat B: -0.5 < PMV < 0.5; PPD < 10%',
                     3: 'Cat C: -0.7 < PMV < 0.7; PPD < 15%'},
                    {0: _STATIC_ISO}),
    ComfortStandard(99, 'CUSTOM', '99 = CUSTOM', {},
                    {3: f'Custom Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
]}


def get_comfort_standard(number: int) -> ComfortStandard:
    """The comfort standard of a ComfStand number.

    :raises ValueError: If there is no such comfort standard.
    """
    try:
        return COMFORT_STANDARDS[number]
    except KeyError:
        raise ValueError(f'{number!r} is not a valid ComfStand. Valid values: {list(COMFORT_STANDARDS)}.') from None
