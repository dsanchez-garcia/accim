# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Catalogue of the comfort standards (ComfStand) of accim, with their categories and comfort modes, and the registry
of the comfort standards defined by their data (proposal B3).

The built-in comfort standards (0 to 23, and the custom model, 99) have their EMS code in
:mod:`accim.sim.ems.program_lines` and :mod:`accim.sim.ems.setpoint_lines`; that of JPN Aqilah 2025 (23, proposal B4
and decisions D1 and D2 of the brief of 1.2.0), a comfort standard defined by its data (:func:`definition_of`), is
added at the end of the chains of the others, which do not change. Comfort standard 24, INT Sun2026 SET (the causal
SET model of Sun, Brager & Schiavon, 2026; task F1 of block F), has no EMS code: its setpoints are those of a hook of
the backend of the Python API of EnergyPlus (:func:`accim.sim.comfort_hooks.apply_sun2026_setpoints`), so
:class:`accim.sim.accis.AddAccis`, ``modify_accis``, the functions of the EMS code and ``compute_setpoints`` do not take
it (:data:`HOOK_COMFORT_STANDARDS`). Other comfort standards can be defined by
their data, a :class:`ComfortStandardDefinition` (a comfort temperature that is a straight line of an outdoor metric
of :mod:`accim.sim.ems.outdoor_metric`, its applicability limits, the offsets of its categories and its static
setpoints; or several comfort temperatures and applicability limits, each one under a condition, as the regimes of the
custom model), and registered with :func:`register_comfort_standard`, or read from YAML files with
:func:`load_comfort_standards`, with the numbers 100 or more (decision D1 of the brief of 1.2.0): accim then writes
their EMS code (:mod:`accim.sim.ems.standard_lines`), and :class:`accim.sim.accis.AddAccis`, ``modify_accis``,
``print_setpoint_ems_code``, ``compute_setpoints`` and the graphical user interface take them as the built-in ones.
The registry is that of the Python session: the comfort standards are registered again in each session.
"""

import math
import numbers
import os
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

__all__ = [
    'COMFORT_STANDARDS',
    'ComfortStandard',
    'ComfortStandardDefinition',
    'DEFINITION_COMFORT_MODES',
    'FIRST_REGISTRY_NUMBER',
    'HOOK_COMFORT_STANDARDS',
    'built_in_definitions',
    'comfort_standard_definition',
    'definition_from_mapping',
    'definition_of',
    'get_comfort_standard',
    'hook_comfort_standard_error',
    'load_comfort_standards',
    'register_comfort_standard',
    'registered_comfort_standards',
    'unregister_comfort_standard',
]

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
    ComfortStandard(23, 'JPN Aqilah2025', '23 = JPN Aqilah2025', _ACCEPTABILITY_80_90,
                    {0: 'Aqilah2025 Static setpoints (20 for heating and 28 for cooling, a choice of the user)',
                     1: 'Aqilah2025 Model Adaptive setpoints when applicable, otherwise Aqilah2025 Static setpoints',
                     2: f'Aqilah2025 Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
                     3: f'Aqilah2025 Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
    ComfortStandard(24, 'INT Sun2026 SET', '24 = INT Sun, Brager & Schiavon 2026 (causal SET band)',
                    {80: 'TSV within +/-0.5, the band of the paper', 90: 'TSV within +/-0.5, the band of the paper'},
                    {1: 'SET band: the setpoints whose SET is that of the limits of the band of TSV (19.1 and 28.2 '
                        'with +/-0.5)',
                     2: 'SET neutral +/- offset: the setpoints whose SET is the neutral SET (23.6) +/- an offset'}),
    ComfortStandard(99, 'CUSTOM', '99 = CUSTOM', {},
                    {3: f'Custom Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}'}),
]}


#: The comfort standards without EMS code, whose setpoints a hook of the backend of the Python API of EnergyPlus sets
#: (:mod:`accim.sim.comfort_hooks`), and the function that prepares a model for them: 24, INT Sun2026 SET (task F1 of
#: block F). :class:`accim.sim.accis.AddAccis`, ``modify_accis``, the functions of the EMS code
#: (``print_setpoint_ems_code``...) and ``compute_setpoints`` do not take them (:func:`hook_comfort_standard_error`).
HOOK_COMFORT_STANDARDS = {24: 'accim.sim.comfort_hooks.apply_sun2026_setpoints'}


def hook_comfort_standard_error(number: Any) -> Optional[str]:
    """The reason why a comfort standard has no EMS code (one of :data:`HOOK_COMFORT_STANDARDS`), for the messages of
    the functions that write or read the EMS code; None for the other comfort standards."""
    try:
        function = HOOK_COMFORT_STANDARDS.get(number)
    except TypeError:
        return None
    if function is None:
        return None
    standard = COMFORT_STANDARDS.get(number)
    return (f'comfort standard {number} ({standard.title if standard else number}) has no EMS code: its setpoints are '
            f'those of a hook of the backend of the Python API of EnergyPlus. Generate the model with another comfort '
            f'standard and prepare it with {function}')


def get_comfort_standard(number: int) -> ComfortStandard:
    """The comfort standard of a ComfStand number.

    :raises ValueError: If there is no such comfort standard.
    """
    try:
        return COMFORT_STANDARDS[number]
    except KeyError:
        raise ValueError(f'{number!r} is not a valid ComfStand. Valid values: {list(COMFORT_STANDARDS)}.') from None


# The comfort standards defined by their data (proposal B3) ------------------------------------------------------------

#: The first number of the comfort standards of the registry: the numbers 100 or more are those of the comfort
#: standards defined by their data (decision D1 of the brief of 1.2.0; 23 is JPN Aqilah 2025, built in, B4)
FIRST_REGISTRY_NUMBER = 100
#: The comfort modes of the comfort standards defined by their data: 0, static setpoints; 1, adaptive setpoints when
#: applicable, otherwise the static setpoints; 2, otherwise the static setpoints of ISO 7730 that the built-in comfort
#: standards use with the categories 80 and 90; 3, otherwise the adaptive setpoints horizontally extended
DEFINITION_COMFORT_MODES = (0, 1, 2, 3)
#: The categories with the static setpoints of ISO 7730 of comfort mode 2 (accim.sim.ems.standard_lines)
_ISO7730_CATEGORIES = (80, 90)
#: The keys of the YAML files of the comfort standards: those that must have a value, and the others
_REQUIRED_KEYS = ('number', 'label', 'title', 'citation', 'outdoor_metric', 'comfort_temperature', 'applicability',
                  'categories', 'comfort_modes', 'evidence')
_OPTIONAL_KEYS = ('alpha', 'days', 'static_setpoints', 'regimes')
#: The keys of the single regime of a comfort standard, which the key ``regimes`` replaces (task H5 of the review of
#: accim 1.2.0)
_SINGLE_REGIME_KEYS = ('comfort_temperature', 'applicability')
#: The keys of each regime of ``regimes``: the fields of :class:`accim.sim.arguments.CustomRegime` (decision 4 of
#: section 6 of the review of accim 1.2.0), whose coefficients (the first eight) are required, as in CustomRegime
_REGIME_FIELDS = ('slope', 'intercept', 'cooling_offset', 'heating_offset', 'cooling_lower_limit',
                  'cooling_upper_limit', 'heating_lower_limit', 'heating_upper_limit', 'condition', 'outdoor_metric',
                  'alpha', 'days')
_REGIME_COEFFICIENTS = _REGIME_FIELDS[:8]
#: The conditions of the regimes of the custom model that those of a comfort standard cannot have: they read the HVAC
#: system of the model (mixed mode), which is not part of a comfort model
_HVAC_CONDITIONS = ('hvac_off', 'hvac_on')
#: The characters that the labels cannot have: they name the output IDFs ('[' separates their arguments)
_LABEL_CHARACTERS = '[]\\/:*?"<>|'
_REGISTRY: Dict[int, 'ComfortStandardDefinition'] = {}
#: The built-in comfort standards defined by their data (built_in_definitions)
_BUILT_IN_DEFINITIONS: Dict[int, 'ComfortStandardDefinition'] = {}


def _is_number(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool) and math.isfinite(value)


@dataclass(frozen=True)
class ComfortStandardDefinition:
    """A comfort standard defined by its data (proposal B3), which :func:`register_comfort_standard` adds to accim.

    Its comfort temperature is a straight line of an outdoor metric (slope · metric + intercept), within the
    applicability limits of the metric; the setpoints are the comfort temperature plus the offsets of the category (and
    those of the regime, 0 in the YAML files with one regime), and, out of the applicability limits, as its comfort
    modes say (:data:`DEFINITION_COMFORT_MODES`). With several regimes, the comfort temperature, the offsets of the
    regime and the applicability limits are those of the first regime whose condition holds in each timestep.

    :ivar standard: Its number (100 or more to register it), label (in the names of the output IDFs), title,
        categories (with their descriptions) and comfort modes (with their descriptions).
    :ivar outdoor_metric: The outdoor metric of its comfort temperature and applicability, a name of
        :data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`: 'pmot' and 'rmot' are the running means of EnergyPlus,
        and the EMS calculates the others (:mod:`accim.sim.ems.outdoor_metric`).
    :ivar regimes: Its comfort temperature, offsets and applicability limits, as regimes of the custom model
        (:class:`accim.sim.arguments.CustomRegime`): one regime 'always' (``comfort_temperature`` and
        ``applicability`` of the YAML files), or several (``regimes``), in their order of priority, the last one with
        the condition 'always' (a comfort standard has no other coefficients for the timesteps in which no condition
        holds), and without the conditions 'hvac_off' and 'hvac_on', which read the HVAC system of the model. With
        several regimes, or a regime with its own outdoor metric, its EMS code selects the regime of each timestep as
        that of the regimes of the custom model (task H5 of the review of accim 1.2.0, decision 4 of its section 6:
        :func:`accim.sim.ems.standard_lines.uses_regimes`); the conditions of the outdoor metric compare that of the
        comfort standard (``outdoor_metric``).
    :ivar category_offsets: The offsets of the cooling and heating setpoints of each category, which can be
        asymmetric: ``{category: (cooling_offset, heating_offset)}``. The setpoints are the comfort temperature plus
        the offsets, so the cooling offset is usually positive or zero and the heating offset negative or zero (the
        comfort band around the comfort temperature): a warning tells otherwise (finding B3-3 of the review of accim
        1.2.0). Comfort mode 2 (out of the applicability limits, the static setpoints of ISO 7730) is only defined for
        the categories 80 and 90, those of the static setpoints of ISO 7730 that accim has: with other categories
        (such as I to IV), a ValueError (verdict 26 of the review of accim 1.2.0).
    :ivar static_setpoints: The static setpoints, ``(heating, cooling)`` (°C), of comfort modes 0 and 1.
    :ivar evidence: The statistics of the comfort model (number of votes, R², standard error, range of the metric,
        type of building, mode of operation...), which ``print_setpoint_ems_code`` prints; it cannot be empty
        (decision D11 of the brief of 1.2.0).
    :ivar citation: The source of the comfort model.
    :ivar alpha: The alpha of the outdoor metric 'rmot_alpha'.
    :ivar days: The days of the outdoor metric 'ndrm'.
    :raises ValueError: If a value is not valid.
    """

    standard: ComfortStandard
    outdoor_metric: str
    regimes: Tuple[Any, ...]
    category_offsets: Dict[Number, Tuple[float, float]]
    static_setpoints: Optional[Tuple[float, float]] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    citation: str = ''
    alpha: float = 0.8
    days: int = 30

    def __post_init__(self):
        from accim.sim.arguments import check_custom_regimes
        from accim.sim.ems.outdoor_metric import check_outdoor_metric_arguments, metric_name

        standard = self.standard
        if not isinstance(standard, ComfortStandard):
            raise ValueError(f'standard must be a ComfortStandard, not {standard!r}.')
        where = f'comfort standard {standard.number}'
        if isinstance(standard.number, bool) or not isinstance(standard.number, int):
            raise ValueError(f'The number of a comfort standard must be an integer, not {standard.number!r}.')
        if not standard.label or any(character in standard.label for character in _LABEL_CHARACTERS):
            raise ValueError(f'The label of the {where} names the output IDFs: it cannot be empty, nor have the '
                             f'characters {_LABEL_CHARACTERS} ({standard.label!r}).')
        try:
            code = check_outdoor_metric_arguments(self.outdoor_metric, self.alpha, self.days)
        except ValueError as error:
            raise ValueError(f'The outdoor metric of the {where}: {error}') from None
        object.__setattr__(self, 'outdoor_metric', metric_name(code))
        try:
            regimes = check_custom_regimes(self.regimes)
        except ValueError as error:
            raise ValueError(f'The regimes of the {where}: {error}') from None
        if not regimes or regimes[-1].condition != 'always':
            raise ValueError(f"The {where} must have at least one regime (a CustomRegime), the last one with the "
                             f"condition 'always' (a comfort standard has no other coefficients for the timesteps in "
                             f"which no condition holds), not {self.regimes!r}.")
        hvac = [number for number, regime in enumerate(regimes, start=1) if regime.condition in _HVAC_CONDITIONS]
        if hvac:
            raise ValueError(f"The regimes {hvac} of the {where} have the condition 'hvac_off' or 'hvac_on', which "
                             f"reads the HVAC system of the model (mixed mode), not the comfort model: only the "
                             f"regimes of the custom model can have it (custom_regimes).")
        object.__setattr__(self, 'regimes', regimes)
        offsets = {}
        for category, pair in dict(self.category_offsets).items():
            if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or not all(_is_number(v) for v in pair)
                    or not _is_number(category)):
                raise ValueError(f'The offsets of the category {category!r} of the {where} must be two numbers, '
                                 f'(cooling_offset, heating_offset), not {pair!r}.')
            offsets[category] = (pair[0], pair[1])
        if not offsets or set(offsets) != set(standard.categories):
            raise ValueError(f'The {where} must have the offsets of each one of its categories '
                             f'({sorted(standard.categories)}), not those of {sorted(offsets)}.')
        crossed = {category: pair for category, pair in sorted(offsets.items()) if pair[0] < 0 or pair[1] > 0}
        if crossed:
            warnings.warn(f'The offsets (cooling_offset, heating_offset) of the categories {crossed} of the {where} '
                          f'have the sign that is not usual: the setpoints are the comfort temperature plus the '
                          f'offsets, so a cooling offset below 0 puts the cooling setpoint below the comfort '
                          f'temperature, and a heating offset above 0 the heating setpoint above it.', stacklevel=3)
        object.__setattr__(self, 'category_offsets', offsets)
        modes = list(standard.comfort_modes)
        if not modes or any(mode not in DEFINITION_COMFORT_MODES for mode in modes):
            raise ValueError(f'The comfort modes of the {where} must be some of {list(DEFINITION_COMFORT_MODES)}, not '
                             f'{modes}.')
        if {0, 1} & set(modes):
            static = self.static_setpoints
            if (not isinstance(static, (list, tuple)) or len(static) != 2 or not all(_is_number(v) for v in static)
                    or not static[0] < static[1]):
                raise ValueError(f'The comfort modes 0 and 1 of the {where} need its static setpoints, (heating, '
                                 f'cooling) with the heating setpoint lower, not {static!r}.')
            object.__setattr__(self, 'static_setpoints', (static[0], static[1]))
        if 2 in modes and not set(offsets) <= set(_ISO7730_CATEGORIES):
            raise ValueError(f'The comfort mode 2 of the {where} uses the static setpoints of ISO 7730 that accim has '
                             f'for the categories {list(_ISO7730_CATEGORIES)} only, not for {sorted(offsets)}.')
        if not isinstance(self.evidence, Mapping) or not self.evidence:
            raise ValueError(f'The {where} must have its evidence: the statistics of the comfort model (decision D11 '
                             f'of the brief of 1.2.0).')
        object.__setattr__(self, 'evidence', dict(self.evidence))
        if not isinstance(self.citation, str) or not self.citation.strip():
            raise ValueError(f'The {where} must have the citation of its source.')

    @property
    def number(self) -> int:
        """The number of the comfort standard (ComfStand)."""
        return self.standard.number


def _comfort_mode_descriptions(label: str, modes: Iterable[int],
                               static: Optional[Tuple[float, float]]) -> Dict[Number, str]:
    """The descriptions of the comfort modes of a comfort standard defined by its data."""
    descriptions = {
        0: f'{label} Static setpoints ({static[0] if static else None} for heating and '
           f'{static[1] if static else None} for cooling)',
        1: f'{label} Model Adaptive setpoints when applicable, otherwise {label} Static setpoints',
        2: f'{label} Model Adaptive setpoints when applicable, otherwise {_STATIC_ISO}',
        3: f'{label} Model Adaptive setpoints when applicable, otherwise {_HORIZONTAL}',
    }
    return {mode: descriptions[mode] for mode in modes}


def definition_from_mapping(data: Any, source: str = '') -> ComfortStandardDefinition:
    """The definition of a comfort standard from a mapping with the keys of the YAML files (those of
    :func:`load_comfort_standards`).

    :param data: The mapping.
    :param source: The file (or other source) of the mapping, for the messages.
    :raises ValueError: If a key is missing or unknown, or a value is not valid; the message names the source.
    """
    from accim.sim.arguments import CustomRegime

    prefix = f'{source}: ' if source else ''

    def fail(message: str) -> ValueError:
        return ValueError(f'{prefix}{message}')

    if not isinstance(data, Mapping):
        raise fail(f'a comfort standard must be a mapping with the keys {list(_REQUIRED_KEYS)} (and optionally '
                   f'{list(_OPTIONAL_KEYS)}), not {type(data).__name__}.')
    unknown = [key for key in data if key not in _REQUIRED_KEYS + _OPTIONAL_KEYS]
    if unknown:
        raise fail(f'unknown keys {unknown}; the keys are {list(_REQUIRED_KEYS + _OPTIONAL_KEYS)}.')
    # Several regimes (the key regimes) replace the comfort temperature and the applicability of the single regime
    several = data.get('regimes') is not None
    if several:
        given = [key for key in _SINGLE_REGIME_KEYS if data.get(key) is not None]
        if given:
            raise fail(f'regimes replaces {list(_SINGLE_REGIME_KEYS)}: give the regimes, or the comfort temperature '
                       f'and the applicability of one regime, not both ({given} given).')
    missing = [key for key in _REQUIRED_KEYS if data.get(key) is None and not (several and key in _SINGLE_REGIME_KEYS)]
    if missing:
        raise fail(f'the keys {missing} are missing or empty.')

    def numbers_of(key: str, names: Tuple[str, ...]) -> List[float]:
        value = data[key]
        if not isinstance(value, Mapping) or set(value) != set(names) or not all(_is_number(value[n]) for n in names):
            raise fail(f'{key} must be a mapping with the numbers {list(names)}, not {value!r}.')
        return [value[name] for name in names]

    number = data['number']
    if isinstance(number, bool) or not isinstance(number, int) or number < FIRST_REGISTRY_NUMBER:
        raise fail(f'number must be an integer of {FIRST_REGISTRY_NUMBER} or more (decision D1), not {number!r}.')
    for key in ('label', 'title', 'citation'):
        if not isinstance(data[key], str) or not data[key].strip():
            raise fail(f'{key} must be a text, not {data[key]!r}.')
    if several:
        regimes = _regimes_from_mapping(data['regimes'], fail)
    else:
        slope, intercept = numbers_of('comfort_temperature', ('slope', 'intercept'))
        lower, upper = numbers_of('applicability', ('metric_min', 'metric_max'))
        if not lower < upper:
            raise fail(f'applicability: metric_min ({lower}) must be lower than metric_max ({upper}).')
        regimes = [CustomRegime(slope, intercept, 0, 0, lower, upper, lower, upper)]
    categories, offsets = {}, {}
    if not isinstance(data['categories'], Mapping) or not data['categories']:
        raise fail(f"categories must be a mapping {{category: {{cooling_offset: ..., heating_offset: ..., "
                   f"description: ...}}}}, not {data['categories']!r}.")
    for category, values in data['categories'].items():
        allowed = {'cooling_offset', 'heating_offset', 'description'}
        if (not _is_number(category) or not isinstance(values, Mapping) or not set(values) <= allowed
                or not all(_is_number(values.get(name)) for name in ('cooling_offset', 'heating_offset'))):
            raise fail(f'the category {category!r} must have the numbers cooling_offset and heating_offset (and '
                       f'optionally a description), not {values!r}.')
        categories[category] = str(values.get('description', category))
        offsets[category] = (values['cooling_offset'], values['heating_offset'])
    modes = data['comfort_modes']
    if (not isinstance(modes, (list, tuple)) or not modes
            or any(not _is_number(mode) or mode not in DEFINITION_COMFORT_MODES for mode in modes)
            or len(set(modes)) != len(modes)):
        raise fail(f'comfort_modes must be a list of some of {list(DEFINITION_COMFORT_MODES)}, not {modes!r}.')
    static = None
    if data.get('static_setpoints') is not None:
        static = tuple(numbers_of('static_setpoints', ('heating', 'cooling')))
    if not isinstance(data['evidence'], Mapping):
        raise fail(f"evidence must be a mapping with the statistics of the comfort model, not {data['evidence']!r}.")
    label = data['label'].strip()
    standard = ComfortStandard(number, label, data['title'].strip(), categories,
                               _comfort_mode_descriptions(label, [int(mode) for mode in modes], static))
    arguments = {name: data[name] for name in ('alpha', 'days') if data.get(name) is not None}
    try:
        return ComfortStandardDefinition(standard, data['outdoor_metric'], tuple(regimes), offsets, static,
                                         dict(data['evidence']), data['citation'].strip(), **arguments)
    except ValueError as error:
        raise fail(str(error)) from None


def _regimes_from_mapping(values: Any, fail) -> List[Any]:
    """The regimes of the key ``regimes`` of a YAML file (:func:`definition_from_mapping`): a list of mappings with
    the fields of :class:`accim.sim.arguments.CustomRegime` (:data:`_REGIME_FIELDS`), whose conditions with a value
    are lists (``[metric_below, 10]``, ``[metric_between, [10, 20]]``).

    :param values: The value of the key.
    :param fail: The function that makes the ValueError of a message (with the name of the file).
    """
    from accim.sim.arguments import CustomRegime

    if not isinstance(values, list) or not values:
        raise fail(f'regimes must be a list of regimes (mappings with the keys {list(_REGIME_FIELDS)}), not '
                   f'{values!r}.')
    regimes = []
    for number, regime in enumerate(values, start=1):
        if not isinstance(regime, Mapping) or not set(regime) <= set(_REGIME_FIELDS):
            raise fail(f'the regime {number} must be a mapping with the keys {list(_REGIME_COEFFICIENTS)} (and '
                       f'optionally {list(_REGIME_FIELDS[8:])}), not {regime!r}.')
        missing = [key for key in _REGIME_COEFFICIENTS if regime.get(key) is None]
        if missing:
            raise fail(f'the regime {number} needs {missing}.')
        fields = {key: value for key, value in regime.items() if value is not None}
        condition = fields.get('condition')
        if isinstance(condition, list):
            fields['condition'] = tuple(tuple(value) if isinstance(value, list) else value for value in condition)
        try:
            regimes.append(CustomRegime(**fields))
        except ValueError as error:
            raise fail(f'the regime {number}: {error}') from None
    return regimes


def registered_comfort_standards() -> Dict[int, ComfortStandardDefinition]:
    """The comfort standards of the registry, by number."""
    return dict(_REGISTRY)


def comfort_standard_definition(number: Any) -> Optional[ComfortStandardDefinition]:
    """The definition of a comfort standard of the registry, or None if the number is not one of them."""
    try:
        return _REGISTRY.get(int(number))
    except (TypeError, ValueError):
        return None


def built_in_definitions() -> Dict[int, ComfortStandardDefinition]:
    """The built-in comfort standards defined by their data, by number: JPN Aqilah 2025 (23).

    JPN Aqilah 2025 is the adaptive comfort model of 64 Japanese dwellings in free-running mode of Aqilah, Rijal,
    Yoshida & Nicol (2025), *Energy & Buildings* 335, 115469 (data verified in
    ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v03.md``, B4 and section 11.5): the comfort temperature
    ``Tc = 0.38·Trm + 16.9`` (equation 8), where ``Trm = α·Trm−1 + (1 − α)·Tod−1`` with α = 0.8 is the running mean
    outdoor temperature of McCartney & Nicol (equation 7), applicable from 5 to 30 °C, and the comfort bands of ±1.5 K
    (90 %) and ±2.0 K (80 %) (conclusions 5 and 6). The running mean is that of CEN 15251 that EnergyPlus calculates
    (RMOT, α = 0.8), as for INT EN16798 (1): the same definition for practical purposes (Aqilah et al. begin theirs a
    week before, equation 7; EnergyPlus sums 7 days, equation 19.82 of its Engineering Reference: verdict 30 of section
    5 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``), but the first value of RMOT in a run period is not divided by
    1 − α⁷, about 21 % lower; with the weather file of the simulation, accim uses instead the running mean of EN 16798-1
    with α = 0.8 that the EMS calculates from it (:data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`, finding
    B4-1 of the review of 1.2.0). The paper gives no static setpoints: those of comfort modes 0 and 1 are inputs of the
    zones (``static_heating_setpoint`` and ``static_cooling_setpoint``, :mod:`accim.sim.ems.static_setpoints`), 20 and
    28 °C by default, a choice of the user (decision D2 of the brief of 1.2.0), the ``static_setpoints`` of the
    definition. ``accim/sample_files/comfort_standards/jpn_aqilah2025_fr.yaml`` has the same data, as a comfort
    standard defined by its data with the running mean 'rmot_alpha' (:func:`load_comfort_standards`).
    """
    if not _BUILT_IN_DEFINITIONS:
        from accim.sim.arguments import CustomRegime

        _BUILT_IN_DEFINITIONS[23] = ComfortStandardDefinition(
            COMFORT_STANDARDS[23], 'rmot', (CustomRegime(0.38, 16.9, 0, 0, 5.0, 30.0, 5.0, 30.0),),
            {80: (2.0, -2.0), 90: (1.5, -1.5)}, static_setpoints=(20.0, 28.0),
            evidence={'N': 11566, 'R2': 0.67, 'SE': 0.003, 'p': '<0.001', 'houses': 64, 'votes_total': 32988,
                      'mode': 'FR', 'within_band': {90: 0.66, 80: 0.79}, 'comfort_temperature_range': [14.5, 30.0]},
            citation='Aqilah, Rijal, Yoshida & Nicol (2025) Energy & Buildings 335, 115469, '
                     'doi:10.1016/j.enbuild.2025.115469')
    return dict(_BUILT_IN_DEFINITIONS)


def definition_of(number: Any) -> Optional[ComfortStandardDefinition]:
    """The definition of a comfort standard defined by its data: a built-in one (:func:`built_in_definitions`) or one
    of the registry; None for the other comfort standards."""
    try:
        number = int(number)
    except (TypeError, ValueError):
        return None
    return _REGISTRY.get(number) or built_in_definitions().get(number)


def register_comfort_standard(definition: ComfortStandardDefinition, replace: bool = False) -> None:
    """Add a comfort standard defined by its data to accim, for the rest of the Python session: to
    :data:`COMFORT_STANDARDS`, and its EMS code to the programs of the ACCIS (:mod:`accim.sim.ems.standard_lines`).

    :param definition: The definition, with a number of 100 or more (decision D1 of the brief of 1.2.0).
    :param replace: True to replace a comfort standard of the registry with the same number.
    :raises ValueError: If the number is lower than 100, or that of a comfort standard already registered (without
        ``replace``), or the label is that of another comfort standard.
    """
    from accim.sim.ems.standard_lines import add_standard_lines, remove_standard_lines

    if not isinstance(definition, ComfortStandardDefinition):
        raise ValueError(f'definition must be a ComfortStandardDefinition, not {definition!r}.')
    number = definition.number
    if number < FIRST_REGISTRY_NUMBER:
        raise ValueError(f'The comfort standards defined by their data have the numbers {FIRST_REGISTRY_NUMBER} or '
                         f'more (decision D1), not {number}.')
    if number in _REGISTRY and not replace:
        raise ValueError(f'The comfort standard {number} is registered already: give replace=True to replace it.')
    if number in COMFORT_STANDARDS and number not in _REGISTRY:
        raise ValueError(f'The comfort standard {number} is a built-in comfort standard.')
    others = [s.number for s in COMFORT_STANDARDS.values()
              if s.label.upper() == definition.standard.label.upper() and s.number != number]
    if others:
        raise ValueError(f'The label {definition.standard.label!r} is that of the comfort standard {others[0]}: the '
                         f'labels name the output IDFs.')
    if number in _REGISTRY:
        remove_standard_lines(number)
    add_standard_lines(definition)
    _REGISTRY[number] = definition
    COMFORT_STANDARDS[number] = definition.standard


def unregister_comfort_standard(number: int) -> None:
    """Remove a comfort standard of the registry (and its EMS code) from accim.

    :raises ValueError: If the number is not that of a comfort standard of the registry.
    """
    from accim.sim.ems.standard_lines import remove_standard_lines

    if number not in _REGISTRY:
        raise ValueError(f'{number!r} is not a comfort standard of the registry ({sorted(_REGISTRY)}).')
    remove_standard_lines(number)
    del _REGISTRY[number]
    del COMFORT_STANDARDS[number]


def load_comfort_standards(path: Union[str, os.PathLike], register: bool = True,
                           replace: bool = False) -> List[ComfortStandardDefinition]:
    """Read the comfort standards of a YAML file, or of the YAML files (``.yaml`` and ``.yml``) of a folder, and
    register them (:func:`register_comfort_standard`).

    Each file has one comfort standard (a mapping) or a list of them, with the keys (as in
    ``accim/sample_files/comfort_standards/jpn_aqilah2025_fr.yaml``): ``number`` (100 or more), ``label`` (in the
    names of the output IDFs), ``title``, ``citation``, ``outdoor_metric`` (a name of
    :data:`accim.sim.ems.outdoor_metric.OUTDOOR_METRICS`, with ``alpha`` for 'rmot_alpha' and ``days`` for 'ndrm',
    optional), ``comfort_temperature`` (``slope`` and ``intercept``), ``applicability`` (``metric_min`` and
    ``metric_max``, the limits of the outdoor metric) or, instead of both, ``regimes`` (several comfort temperatures and
    applicability limits, in their order of priority: a list of mappings with the fields of
    :class:`accim.sim.arguments.CustomRegime`, ``slope``, ``intercept``, ``cooling_offset``, ``heating_offset``,
    ``cooling_lower_limit``, ``cooling_upper_limit``, ``heating_lower_limit`` and ``heating_upper_limit``, and
    optionally ``condition``, 'always' by default, a list such as ``[metric_below, 10]`` for the conditions with a
    value, ``outdoor_metric``, ``alpha`` and ``days``; the last one 'always'; task H5 of the review of accim 1.2.0),
    ``categories`` (``{category: {cooling_offset: ...,
    heating_offset: ..., description: ...}}``), ``comfort_modes`` (a list of 0, 1, 2 and 3, see
    :data:`DEFINITION_COMFORT_MODES`), ``static_setpoints`` (``heating`` and ``cooling``, which comfort modes 0 and 1
    need) and ``evidence`` (the statistics of the comfort model, which cannot be empty: decision D11).

    :param path: The YAML file, or a folder.
    :param register: False to read them only.
    :param replace: True to replace the comfort standards of the registry with the same numbers.
    :return: The definitions, in the order of the files.
    :raises ValueError: If a file is not valid (the message names the file and the key), or the folder has no YAML
        files.
    :raises ImportError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError('load_comfort_standards needs PyYAML: pip install pyyaml') from None

    path = os.fspath(path)
    if os.path.isdir(path):
        files = sorted(os.path.join(path, name) for name in os.listdir(path)
                       if name.lower().endswith(('.yaml', '.yml')))
        if not files:
            raise ValueError(f'The folder {path} has no YAML files (.yaml or .yml).')
    elif os.path.isfile(path):
        files = [path]
    else:
        raise ValueError(f'{path} is not a file or a folder.')
    definitions = []
    for file in files:
        with open(file, encoding='utf-8') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as error:
                raise ValueError(f'{file}: it is not a valid YAML file ({error}).') from None
        items = data if isinstance(data, list) else [data]
        definitions += [definition_from_mapping(item, os.path.basename(file)) for item in items]
    numbers_found = [definition.number for definition in definitions]
    repeated = sorted({number for number in numbers_found if numbers_found.count(number) > 1})
    if repeated:
        raise ValueError(f'The comfort standards {repeated} are defined more than once in {path}.')
    if register:
        for definition in definitions:
            register_comfort_standard(definition, replace=replace)
    return definitions
