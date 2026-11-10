# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""
Contains the functions to apply setpoints based on the predicted mean vote (PMV) of Fanger and on indices derived
from it: the adaptive PMV (aPMV), with :func:`apply_apmv_setpoints`, the PMV with the expectancy factor (ePMV), with
:func:`apply_epmv_setpoints`, and the PMV, with :func:`apply_pmv_setpoints`.
Unified version supporting EnergyPlus versions pre and post 23.1.

These functions call :func:`accim.sim.pmv_index.apply_pmv_index_setpoints`, which identifies the target zones or
spaces from the Global Model Hierarchy (Space > ZoneList > Zone) and generates the EnergyManagementSystem (EMS) objects
that control thermal comfort dynamically. This module also has the functions that prepare the models for these
setpoints (:func:`add_vrf_system`, :func:`set_pmv_input_parameters`...).
"""

import numbers
import warnings
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd

from accim._deprecation import accepts_legacy_kwargs
from accim.sim.pmv_index import (_resolve_targets, apply_pmv_index_setpoints, arguments_table,
                                 both_adaptive_coefficients, get_adaptive_coefficients, metabolic_correction_names,
                                 resolve_adaptive_coefficients)
from accim.sim.targets import sanitize_ems_name
from accim.utils.editing import transform_ddmm_to_int
from accim.utils.people import get_people_definition, get_people_objects, is_people_instance

__all__ = [
    'add_ems_debug_output',
    'add_vrf_system',
    'apply_apmv_setpoints',
    'apply_epmv_setpoints',
    'apply_pmv_setpoints',
    'change_adaptive_coeff',
    'generate_df_from_args',
    'get_adaptive_coefficients',
    'get_available_target_names',
    'get_input_template_dictionary',
    'set_pmv_input_parameters',
    'set_zones_always_occupied',
]

#: The eppy or besos IDF object of a model
IDF = Any
_sanitize_ems_name = sanitize_ems_name

#: The names of the arguments in accim 0.x -> their names since accim 1.0.0 (the old names keep working, with a
#: DeprecationWarning). The EMS variables keep the old names (adap_coeff_cooling_<target>...).
_LEGACY_ARGUMENTS = {
    'outputs_freq': 'output_frequencies',
    'other_PMV_related_outputs': 'other_pmv_related_outputs',
    'adap_coeff_cooling': 'adaptive_coefficient_cooling',
    'adap_coeff_heating': 'adaptive_coefficient_heating',
    'pmv_cooling_sp': 'pmv_cooling_setpoint',
    'pmv_heating_sp': 'pmv_heating_setpoint',
    'tolerance_cooling_sp_cooling_season': 'cooling_setpoint_tolerance_cooling_season',
    'tolerance_cooling_sp_heating_season': 'cooling_setpoint_tolerance_heating_season',
    'tolerance_heating_sp_cooling_season': 'heating_setpoint_tolerance_cooling_season',
    'tolerance_heating_sp_heating_season': 'heating_setpoint_tolerance_heating_season',
    'dflt_for_adap_coeff_cooling': 'default_adaptive_coefficient_cooling',
    'dflt_for_adap_coeff_heating': 'default_adaptive_coefficient_heating',
    'dflt_for_pmv_cooling_sp': 'default_pmv_cooling_setpoint',
    'dflt_for_pmv_heating_sp': 'default_pmv_heating_setpoint',
    'dflt_for_tolerance_cooling_sp_cooling_season': 'default_cooling_setpoint_tolerance_cooling_season',
    'dflt_for_tolerance_cooling_sp_heating_season': 'default_cooling_setpoint_tolerance_heating_season',
    'dflt_for_tolerance_heating_sp_cooling_season': 'default_heating_setpoint_tolerance_cooling_season',
    'dflt_for_tolerance_heating_sp_heating_season': 'default_heating_setpoint_tolerance_heating_season',
    'SupplyAirTempInputMethod': 'supply_air_temp_input_method',
    'VRFschedule': 'vrf_availability_schedule',
    'eer': 'vrf_eer',
    'cop': 'vrf_cop',
    'verbose_mode': 'verbose',
}
#: The arguments of the setpoints (the columns of the DataFrame of generate_df_from_args), accim 0.x -> 1.0.0
_LEGACY_SETPOINT_ARGUMENTS = {old: new for old, new in _LEGACY_ARGUMENTS.items()
                              if old.startswith(('adap_coeff', 'pmv_', 'tolerance_'))}
#: Decorator: the function also accepts the names of its arguments in accim 0.x
_accepts_legacy_arguments = accepts_legacy_kwargs(_LEGACY_ARGUMENTS)

#: The clothing insulation of set_pmv_input_parameters for the dynamic clothing model of ASHRAE 55 (the method
#: DynamicClothingModelASHRAE55 of the field Clothing Insulation Calculation Method of the People objects)
_DYNAMIC_CLOTHING = 'dynamic_ashrae55'
#: The keys of the dictionaries of set_pmv_input_parameters with a value for each season
_SEASONS = ('heating_season', 'cooling_season')


# ==============================================================================
# MAIN FUNCTIONS
# ==============================================================================

@_accepts_legacy_arguments
def apply_apmv_setpoints(
        building: IDF,
        output_frequencies: Sequence[str] = ('hourly',),
        other_pmv_related_outputs: bool = True,
        adaptive_coefficient_cooling: Union[float, str, dict] = 0.293,
        adaptive_coefficient_heating: Union[float, str, dict] = -0.293,
        pmv_cooling_setpoint: Union[float, dict] = 0.5,
        pmv_heating_setpoint: Union[float, dict] = -0.5,
        cooling_setpoint_tolerance_cooling_season: Union[float, dict] = -0.1,
        cooling_setpoint_tolerance_heating_season: Union[float, dict] = -0.1,
        heating_setpoint_tolerance_cooling_season: Union[float, dict] = 0.1,
        heating_setpoint_tolerance_heating_season: Union[float, dict] = 0.1,
        cooling_season_start: Union[float, str] = 121,
        cooling_season_end: Union[float, str] = 274,
        default_adaptive_coefficient_cooling: Union[float, str] = 0.4,
        default_adaptive_coefficient_heating: Union[float, str] = -0.4,
        default_pmv_cooling_setpoint: float = 0.5,
        default_pmv_heating_setpoint: float = -0.5,
        default_cooling_setpoint_tolerance_cooling_season: float = -0.1,
        default_cooling_setpoint_tolerance_heating_season: float = -0.1,
        default_heating_setpoint_tolerance_cooling_season: float = 0.1,
        default_heating_setpoint_tolerance_heating_season: float = 0.1,
        verbose: bool = True,
        adaptive_coefficient_by: str = 'season',
        adaptive_coefficients: Optional[str] = None,
        report_ppd_weighted_hours: bool = False,
) -> IDF:
    """
    Applies setpoints based on the Adaptive Predicted Mean Vote (aPMV) index.

    This function modifies the EnergyPlus IDF model to include an Energy Management System (EMS)
    control logic. It calculates the aPMV in real-time and adjusts the heating and cooling
    setpoints dynamically to maintain thermal comfort within the specified adaptive limits.

    It supports both legacy EnergyPlus versions (Zone-based) and modern versions (Space-based),
    automatically resolving the model hierarchy. It is :func:`accim.sim.pmv_index.apply_pmv_index_setpoints`
    with the index 'apmv'.

    :param building: The BESOS/eppy IDF object to be modified.
    :param output_frequencies: List of reporting frequencies for the output variables (e.g., ['hourly', 'timestep']).
    :param other_pmv_related_outputs: If True, adds additional comfort-related output variables (e.g., Fanger PMV,
        PPD).
    :param adaptive_coefficient_cooling: Adaptive coefficient (lambda) for cooling: that of the cooling season (or of
        warm sensations, PMV >= 0, with ``adaptive_coefficient_by='pmv_sign'``). Can be a single float (applied
        globally), a key of :data:`accim.constants.APMV_ADAPTIVE_COEFFICIENTS` (its ``cooling`` coefficient; see
        :func:`get_adaptive_coefficients`), or a dict {TargetName: Value} whose values are numbers or keys.
    :param adaptive_coefficient_heating: Adaptive coefficient (lambda) for heating: that of the heating season (or of
        cool sensations, PMV < 0, with ``adaptive_coefficient_by='pmv_sign'``). Float, key of the catalogue (its
        ``heating`` coefficient) or Dict {TargetName: Value}. A key sets only its own argument: give it to
        ``adaptive_coefficients`` to use the two coefficients of an entry (a key on one side with the numeric default
        on the other, which has no source, warns). The keys of the grade 'literature' warn.
    :param pmv_cooling_setpoint: Target aPMV setpoint for cooling. Float or Dict. Default is 0.5. The PMV setpoint
        applied to the thermostat is obtained with the inverse aPMV formula, PMV = aPMV/(1 - lambda*aPMV). With
        ``adaptive_coefficient_by='pmv_sign'``, it must be >= 0 (a ``ValueError`` otherwise).
    :param pmv_heating_setpoint: Target aPMV setpoint for heating. Float or Dict. Default is -0.5. Converted to PMV in
        the same way. With ``adaptive_coefficient_by='pmv_sign'``, it must be <= 0.
    :param cooling_setpoint_tolerance_cooling_season: Tolerance to widen the cooling setpoint band during cooling
        season.
    :param cooling_setpoint_tolerance_heating_season: Tolerance to widen the cooling setpoint band during heating
        season.
    :param heating_setpoint_tolerance_cooling_season: Tolerance to widen the heating setpoint band during cooling
        season.
    :param heating_setpoint_tolerance_heating_season: Tolerance to widen the heating setpoint band during heating
        season.
    :param cooling_season_start: Start day of the cooling season. Can be an integer (Day of Year) or string ('dd/mm').
        Default is 121 (1 May), as cooling_season_start in AddAccis.
    :param cooling_season_end: End day of the cooling season, which is not included in it. Can be an integer
        (Day of Year) or string ('dd/mm'). Default is 274 (1 October), as cooling_season_end in AddAccis.
    :param default_adaptive_coefficient_cooling: Default value for cooling adaptive coefficient if key is missing in
        dict input.
    :param default_adaptive_coefficient_heating: Default value for heating adaptive coefficient if key is missing in
        dict input.
    :param default_pmv_cooling_setpoint: Default value for cooling PMV setpoint if key is missing in dict input.
    :param default_pmv_heating_setpoint: Default value for heating PMV setpoint if key is missing in dict input.
    :param default_cooling_setpoint_tolerance_cooling_season: Default tolerance value if key is missing.
    :param default_cooling_setpoint_tolerance_heating_season: Default tolerance value if key is missing.
    :param default_heating_setpoint_tolerance_cooling_season: Default tolerance value if key is missing.
    :param default_heating_setpoint_tolerance_heating_season: Default tolerance value if key is missing.
    :param verbose: If True, prints detailed progress messages (added objects) and warnings to the console.
    :param adaptive_coefficient_by: How the adaptive coefficient of each timestep is chosen: 'season' (by default,
        that of the cooling or heating season of the calendar) or 'pmv_sign' (that of the side of the scale of the PMV
        of the zone of the previous timestep, the coefficient for cooling with PMV >= 0 and that for heating with
        PMV < 0, as Yao et al. (2009) and GB/T 50785-2012 define them; the heating setpoint is converted with the
        coefficient for heating, and the cooling setpoint with that for cooling).
    :param adaptive_coefficients: A key of :data:`accim.constants.APMV_ADAPTIVE_COEFFICIENTS` whose two coefficients
        are those of cooling and heating (since accim 1.2.0, verdict #3 of its review: the catalogue is made of pairs);
        None (the default) for those of ``adaptive_coefficient_cooling`` and ``adaptive_coefficient_heating``, which
        must then keep their defaults (a ``ValueError`` otherwise). An entry without one of the coefficients raises a
        ``ValueError``.
    :param report_ppd_weighted_hours: True to count the PPD-weighted hours of each zone, Method C of CEN/TR
        16798-2:2019, Annex D, with the setpoints without the tolerances as the range, on the scale of the PMV (the
        output ``PPD Weighted Hours_<zone>``, see :func:`accim.sim.pmv_index.ppd_weighted_hours_lines`); False (the
        default) for none.
    :return: The modified BESOS IDF object with EMS controls added.

    The arguments had other names before accim 1.0.0 (outputs_freq, other_PMV_related_outputs, adap_coeff_cooling,
    pmv_cooling_sp, tolerance_cooling_sp_cooling_season, dflt_for_adap_coeff_cooling, verbose_mode...), which keep
    working with a DeprecationWarning (see the migration guide). The EMS variables keep the old names.
    """
    if adaptive_coefficients is not None:
        adaptive_coefficient_cooling, adaptive_coefficient_heating = both_adaptive_coefficients(
            adaptive_coefficients, adaptive_coefficient_cooling, adaptive_coefficient_heating)
    return apply_pmv_index_setpoints(
        building,
        index='apmv',
        index_parameters=dict(
            adaptive_coefficient_cooling=adaptive_coefficient_cooling,
            adaptive_coefficient_heating=adaptive_coefficient_heating,
            default_adaptive_coefficient_cooling=default_adaptive_coefficient_cooling,
            default_adaptive_coefficient_heating=default_adaptive_coefficient_heating,
            adaptive_coefficient_by=adaptive_coefficient_by,
        ),
        output_frequencies=output_frequencies,
        other_pmv_related_outputs=other_pmv_related_outputs,
        pmv_cooling_setpoint=pmv_cooling_setpoint,
        pmv_heating_setpoint=pmv_heating_setpoint,
        cooling_setpoint_tolerance_cooling_season=cooling_setpoint_tolerance_cooling_season,
        cooling_setpoint_tolerance_heating_season=cooling_setpoint_tolerance_heating_season,
        heating_setpoint_tolerance_cooling_season=heating_setpoint_tolerance_cooling_season,
        heating_setpoint_tolerance_heating_season=heating_setpoint_tolerance_heating_season,
        cooling_season_start=cooling_season_start,
        cooling_season_end=cooling_season_end,
        default_pmv_cooling_setpoint=default_pmv_cooling_setpoint,
        default_pmv_heating_setpoint=default_pmv_heating_setpoint,
        default_cooling_setpoint_tolerance_cooling_season=default_cooling_setpoint_tolerance_cooling_season,
        default_cooling_setpoint_tolerance_heating_season=default_cooling_setpoint_tolerance_heating_season,
        default_heating_setpoint_tolerance_cooling_season=default_heating_setpoint_tolerance_cooling_season,
        default_heating_setpoint_tolerance_heating_season=default_heating_setpoint_tolerance_heating_season,
        verbose=verbose,
        report_ppd_weighted_hours=report_ppd_weighted_hours,
    )


def apply_epmv_setpoints(
        building: IDF,
        output_frequencies: Sequence[str] = ('hourly',),
        other_pmv_related_outputs: bool = True,
        expectancy_factor: Union[float, dict] = 0.8,
        pmv_cooling_setpoint: Union[float, dict] = 0.5,
        pmv_heating_setpoint: Union[float, dict] = -0.5,
        apply_to_heating: bool = False,
        metabolic_correction: bool = False,
        cooling_setpoint_tolerance_cooling_season: Union[float, dict] = -0.1,
        cooling_setpoint_tolerance_heating_season: Union[float, dict] = -0.1,
        heating_setpoint_tolerance_cooling_season: Union[float, dict] = 0.1,
        heating_setpoint_tolerance_heating_season: Union[float, dict] = 0.1,
        cooling_season_start: Union[float, str] = 121,
        cooling_season_end: Union[float, str] = 274,
        default_expectancy_factor: float = 0.8,
        default_pmv_cooling_setpoint: float = 0.5,
        default_pmv_heating_setpoint: float = -0.5,
        default_cooling_setpoint_tolerance_cooling_season: float = -0.1,
        default_cooling_setpoint_tolerance_heating_season: float = -0.1,
        default_heating_setpoint_tolerance_cooling_season: float = 0.1,
        default_heating_setpoint_tolerance_heating_season: float = 0.1,
        verbose: bool = True,
        report_ppd_weighted_hours: bool = False,
) -> IDF:
    """
    Applies setpoints based on the PMV with the expectancy factor (ePMV) of Fanger and Toftum (2002), ePMV = e·PMV,
    which extends the PMV to the buildings without air-conditioning in warm climates, whose occupants feel the warmth
    as less severe than the PMV predicts.

    The expectancy factor e of each zone applies in the cooling season, and only to the warm sensations (the upper
    limit of the comfort zone): the PMV setpoint of the cooling thermostat is ePMV/e, and the heating setpoint is a
    PMV setpoint, as in the heating season, where e is 1. The ePMV of each zone (the output ``ePMV_<zone>``) is e·PMV if
    the PMV is positive, and the PMV otherwise. Fanger and Toftum (2002, Table 1) give e between 0.9 and 1 where
    air-conditioned buildings are common and the warm periods are brief, between 0.7 and 0.9 where some buildings are
    air-conditioned and the summer is warm, and between 0.5 and 0.7 where few buildings are air-conditioned and it is
    warm all the year (:data:`accim.constants.EPMV_EXPECTANCY_RANGES`); e is 1 in air-conditioned buildings. It is
    :func:`accim.sim.pmv_index.apply_pmv_index_setpoints` with the index 'epmv'.

    :param building: The eppy or besos IDF object to be modified.
    :param output_frequencies: The reporting frequencies of the outputs (e.g., ['hourly', 'timestep']).
    :param other_pmv_related_outputs: If True, adds other outputs of the comfort of the zones (Fanger PMV and PPD,
        operative and air temperatures).
    :param expectancy_factor: The expectancy factor e, between 0.5 and 1: one number, or a dict {zone: number} (see
        :func:`get_available_target_names`). Default is 0.8.
    :param pmv_cooling_setpoint: The ePMV setpoint for cooling. Number or dict. Default is 0.5.
    :param pmv_heating_setpoint: The ePMV setpoint for heating, which is a PMV setpoint unless ``apply_to_heating``.
        Number or dict. Default is -0.5.
    :param apply_to_heating: If True, the expectancy factor also applies to the cool sensations (the heating setpoint
        is ePMV/e in the cooling season, and the ePMV of each zone is always e·PMV); Fanger and Toftum (2002) do not
        apply it to them, so a warning is issued.
    :param metabolic_correction: If True, the activity level of the occupants is reduced in the cooling season by
        6.7 % for each unit of PMV above neutral, up to 3 (:data:`accim.constants.EPMV_MET_REDUCTION_PER_PMV`), as
        Fanger and Toftum (2002) do because the occupants slow down in the warmth. EnergyPlus calculates the PMV once
        per timestep, with the activity level of the People objects, so the correction uses the PMV of the previous
        timestep, which is calculated with the corrected activity level: the corrected activity level tends to the one
        whose PMV gives it, a slightly smaller reduction than that of Fanger and Toftum, whose PMV is calculated with
        the activity level without the correction. The activity level also gives the heat gains of the occupants, which
        the correction reduces too (from the next timestep, since EnergyPlus calculates the internal gains before the
        EMS programs of the setpoints run). The activity level schedule of each People object becomes a copy of it
        that the EMS sets, and the outputs ``Metabolic Correction Factor_<people>`` and
        ``Corrected Activity Level_<people>`` report it (see :func:`accim.sim.pmv_index.metabolic_correction_names`);
        a People object that applies to several zones has one activity level, reduced with the mean PMV of its
        occupants in them. Set the activity level with :func:`set_pmv_input_parameters` before applying the
        setpoints. Default is False.
    :param cooling_setpoint_tolerance_cooling_season: The tolerance added to the cooling setpoint in the cooling
        season (and the other tolerances, to the other setpoints and seasons), on the ePMV scale. Number or dict.
    :param cooling_season_start: The first day of the cooling season: the day of the year or 'dd/mm'. Default is 121
        (1 May), as in AddAccis.
    :param cooling_season_end: The day after the last day of the cooling season: the day of the year or 'dd/mm'.
        Default is 274 (1 October).
    :param default_expectancy_factor: The expectancy factor of the zones missing in the dict of ``expectancy_factor``
        (and the other ``default_*`` arguments, for the other arguments).
    :param verbose: If True, prints the objects that are added. The warnings are always issued.
    :param report_ppd_weighted_hours: True to count the PPD-weighted hours of each zone, Method C of CEN/TR
        16798-2:2019, Annex D, with the setpoints without the tolerances as the range, on the scale of the PMV (the
        output ``PPD Weighted Hours_<zone>``, see :func:`accim.sim.pmv_index.ppd_weighted_hours_lines`); False (the
        default) for none.
    :return: The modified IDF object.
    :raises ValueError: If an expectancy factor is not between 0.5 and 1.
    """
    return apply_pmv_index_setpoints(
        building,
        index='epmv',
        index_parameters=dict(
            expectancy_factor=expectancy_factor,
            default_expectancy_factor=default_expectancy_factor,
            apply_to_heating=apply_to_heating,
            metabolic_correction=metabolic_correction,
        ),
        output_frequencies=output_frequencies,
        other_pmv_related_outputs=other_pmv_related_outputs,
        pmv_cooling_setpoint=pmv_cooling_setpoint,
        pmv_heating_setpoint=pmv_heating_setpoint,
        cooling_setpoint_tolerance_cooling_season=cooling_setpoint_tolerance_cooling_season,
        cooling_setpoint_tolerance_heating_season=cooling_setpoint_tolerance_heating_season,
        heating_setpoint_tolerance_cooling_season=heating_setpoint_tolerance_cooling_season,
        heating_setpoint_tolerance_heating_season=heating_setpoint_tolerance_heating_season,
        cooling_season_start=cooling_season_start,
        cooling_season_end=cooling_season_end,
        default_pmv_cooling_setpoint=default_pmv_cooling_setpoint,
        default_pmv_heating_setpoint=default_pmv_heating_setpoint,
        default_cooling_setpoint_tolerance_cooling_season=default_cooling_setpoint_tolerance_cooling_season,
        default_cooling_setpoint_tolerance_heating_season=default_cooling_setpoint_tolerance_heating_season,
        default_heating_setpoint_tolerance_cooling_season=default_heating_setpoint_tolerance_cooling_season,
        default_heating_setpoint_tolerance_heating_season=default_heating_setpoint_tolerance_heating_season,
        verbose=verbose,
        report_ppd_weighted_hours=report_ppd_weighted_hours,
    )


def apply_pmv_setpoints(
        building: IDF,
        output_frequencies: Sequence[str] = ('hourly',),
        other_pmv_related_outputs: bool = True,
        pmv_cooling_setpoint: Union[float, dict] = 0.5,
        pmv_heating_setpoint: Union[float, dict] = -0.5,
        cooling_setpoint_tolerance_cooling_season: Union[float, dict] = -0.1,
        cooling_setpoint_tolerance_heating_season: Union[float, dict] = -0.1,
        heating_setpoint_tolerance_cooling_season: Union[float, dict] = 0.1,
        heating_setpoint_tolerance_heating_season: Union[float, dict] = 0.1,
        cooling_season_start: Union[float, str] = 121,
        cooling_season_end: Union[float, str] = 274,
        default_pmv_cooling_setpoint: float = 0.5,
        default_pmv_heating_setpoint: float = -0.5,
        default_cooling_setpoint_tolerance_cooling_season: float = -0.1,
        default_cooling_setpoint_tolerance_heating_season: float = -0.1,
        default_heating_setpoint_tolerance_cooling_season: float = 0.1,
        default_heating_setpoint_tolerance_heating_season: float = 0.1,
        verbose: bool = True,
        report_ppd_weighted_hours: bool = False,
) -> IDF:
    """
    Applies setpoints based on the predicted mean vote (PMV) of Fanger, for instance those of the categories of
    ISO 7730 and EN 16798-1 (-0.2 and 0.2, -0.5 and 0.5, -0.7 and 0.7).

    The thermal comfort thermostats keep the PMV of each occupied zone between the heating and cooling setpoints (with
    their tolerances), as :func:`apply_apmv_setpoints` with adaptive coefficients of 0 does, with the EMS objects of
    the PMV: the programs ``apply_PMV_<zone>`` and ``count_PMV_comfort_hours_<zone>``, the setpoints
    ``PMV_H_SP_<zone>`` and ``PMV_C_SP_<zone>``, and the outputs ``PMV_<zone>``, ``PMV Heating Setpoint_<zone>``...
    It is :func:`accim.sim.pmv_index.apply_pmv_index_setpoints` with the index 'pmv'.

    :param building: The eppy or besos IDF object to be modified.
    :param output_frequencies: The reporting frequencies of the outputs (e.g., ['hourly', 'timestep']).
    :param other_pmv_related_outputs: If True, adds other outputs of the comfort of the zones (Fanger PMV and PPD,
        operative and air temperatures).
    :param pmv_cooling_setpoint: The PMV setpoint for cooling: one number, or a dict {zone: number} (see
        :func:`get_available_target_names`).
    :param pmv_heating_setpoint: The PMV setpoint for heating. Number or dict.
    :param cooling_setpoint_tolerance_cooling_season: The tolerance added to the cooling setpoint in the cooling
        season (and the other tolerances, to the other setpoints and seasons). Number or dict.
    :param cooling_season_start: The first day of the cooling season: the day of the year or 'dd/mm'. Default is 121
        (1 May), as in AddAccis.
    :param cooling_season_end: The day after the last day of the cooling season: the day of the year or 'dd/mm'.
        Default is 274 (1 October).
    :param default_pmv_cooling_setpoint: The cooling setpoint of the zones missing in the dict of
        ``pmv_cooling_setpoint`` (and the other ``default_*`` arguments, for the other arguments).
    :param verbose: If True, prints the objects that are added. The warnings are always issued.
    :param report_ppd_weighted_hours: True to count the PPD-weighted hours of each zone, Method C of CEN/TR
        16798-2:2019, Annex D, with the setpoints without the tolerances as the range, on the scale of the PMV (the
        output ``PPD Weighted Hours_<zone>``, see :func:`accim.sim.pmv_index.ppd_weighted_hours_lines`); False (the
        default) for none.
    :return: The modified IDF object.
    """
    return apply_pmv_index_setpoints(
        building,
        index='pmv',
        output_frequencies=output_frequencies,
        other_pmv_related_outputs=other_pmv_related_outputs,
        pmv_cooling_setpoint=pmv_cooling_setpoint,
        pmv_heating_setpoint=pmv_heating_setpoint,
        cooling_setpoint_tolerance_cooling_season=cooling_setpoint_tolerance_cooling_season,
        cooling_setpoint_tolerance_heating_season=cooling_setpoint_tolerance_heating_season,
        heating_setpoint_tolerance_cooling_season=heating_setpoint_tolerance_cooling_season,
        heating_setpoint_tolerance_heating_season=heating_setpoint_tolerance_heating_season,
        cooling_season_start=cooling_season_start,
        cooling_season_end=cooling_season_end,
        default_pmv_cooling_setpoint=default_pmv_cooling_setpoint,
        default_pmv_heating_setpoint=default_pmv_heating_setpoint,
        default_cooling_setpoint_tolerance_cooling_season=default_cooling_setpoint_tolerance_cooling_season,
        default_cooling_setpoint_tolerance_heating_season=default_cooling_setpoint_tolerance_heating_season,
        default_heating_setpoint_tolerance_cooling_season=default_heating_setpoint_tolerance_cooling_season,
        default_heating_setpoint_tolerance_heating_season=default_heating_setpoint_tolerance_heating_season,
        verbose=verbose,
        report_ppd_weighted_hours=report_ppd_weighted_hours,
    )


# ==============================================================================
# UTILS
# ==============================================================================

@_accepts_legacy_arguments
def generate_df_from_args(
        target_keys_input: List[str],
        ems_suffixes: List[str],
        adaptive_coefficient_cooling: Union[float, Dict[str, float]],
        adaptive_coefficient_heating: Union[float, Dict[str, float]],
        pmv_cooling_setpoint: Union[float, Dict[str, float]],
        pmv_heating_setpoint: Union[float, Dict[str, float]],
        cooling_setpoint_tolerance_cooling_season: Union[float, Dict[str, float]],
        cooling_setpoint_tolerance_heating_season: Union[float, Dict[str, float]],
        heating_setpoint_tolerance_cooling_season: Union[float, Dict[str, float]],
        heating_setpoint_tolerance_heating_season: Union[float, Dict[str, float]],
        default_adaptive_coefficient_cooling: float,
        default_adaptive_coefficient_heating: float,
        default_pmv_cooling_setpoint: float,
        default_pmv_heating_setpoint: float,
        default_cooling_setpoint_tolerance_cooling_season: float,
        default_cooling_setpoint_tolerance_heating_season: float,
        default_heating_setpoint_tolerance_cooling_season: float,
        default_heating_setpoint_tolerance_heating_season: float,
) -> pd.DataFrame:
    """
    Maps user input arguments (which can be single floats or dictionaries) to the
    resolved target keys. It creates a pandas DataFrame where each row corresponds
    to a target (Space/Zone) and columns correspond to the simulation parameters.

    :param target_keys_input: List of unique keys identifying the targets (e.g., "Space1 People").
    :param ems_suffixes: List of sanitized suffixes corresponding to the keys (e.g., "Space1_People").
    :param adaptive_coefficient_cooling: Adaptive coefficient for cooling (and adaptive_coefficient_heating, for
        heating): a number, a key of :data:`accim.constants.APMV_ADAPTIVE_COEFFICIENTS` or a dictionary of them (see
        :func:`apply_apmv_setpoints`).
    :param pmv_cooling_setpoint: aPMV setpoint for cooling (and pmv_heating_setpoint, for heating).
    :param cooling_setpoint_tolerance_cooling_season: Tolerance of the cooling setpoint in the cooling season (and
        the other tolerances, for the other setpoints and seasons).
    :param default_adaptive_coefficient_cooling: Default value to use if a specific key is missing in the dictionary
        input of adaptive_coefficient_cooling (and the other default_* arguments, for the other arguments).
    :return: A pandas DataFrame indexed by target keys, containing all parameters (a column for each argument, with
        its name) and the 'underscore_zonename'.
    """
    coefficients = resolve_adaptive_coefficients(dict(
        adaptive_coefficient_cooling=adaptive_coefficient_cooling,
        adaptive_coefficient_heating=adaptive_coefficient_heating,
        default_adaptive_coefficient_cooling=default_adaptive_coefficient_cooling,
        default_adaptive_coefficient_heating=default_adaptive_coefficient_heating,
    ))
    return arguments_table(target_keys_input, ems_suffixes, [
        ('adaptive_coefficient_cooling', coefficients['adaptive_coefficient_cooling'],
         coefficients['default_adaptive_coefficient_cooling']),
        ('adaptive_coefficient_heating', coefficients['adaptive_coefficient_heating'],
         coefficients['default_adaptive_coefficient_heating']),
        ('pmv_cooling_setpoint', pmv_cooling_setpoint, default_pmv_cooling_setpoint),
        ('pmv_heating_setpoint', pmv_heating_setpoint, default_pmv_heating_setpoint),
        ('cooling_setpoint_tolerance_cooling_season', cooling_setpoint_tolerance_cooling_season,
         default_cooling_setpoint_tolerance_cooling_season),
        ('cooling_setpoint_tolerance_heating_season', cooling_setpoint_tolerance_heating_season,
         default_cooling_setpoint_tolerance_heating_season),
        ('heating_setpoint_tolerance_cooling_season', heating_setpoint_tolerance_cooling_season,
         default_heating_setpoint_tolerance_cooling_season),
        ('heating_setpoint_tolerance_heating_season', heating_setpoint_tolerance_heating_season,
         default_heating_setpoint_tolerance_heating_season),
    ])


def get_available_target_names(building: IDF) -> List[str]:
    """
    Identifies and returns a list of valid target names (keys) for the current model.
    These keys are what the user should use in the input dictionaries (e.g., adaptive_coefficient_cooling).

    :param building: The BESOS/eppy IDF object.
    :return: A list of strings representing the valid keys (e.g., ['Space1 People', 'Space2 People']).
    """
    targets = _resolve_targets(building)
    return [t['df_key'] for t in targets]


def get_input_template_dictionary(building: IDF) -> Dict[str, str]:
    """
    Generates a template dictionary with all valid target keys and placeholder values.
    Useful for the user to know exactly which keys to populate.

    :param building: The BESOS/eppy IDF object.
    :return: A dictionary {target_name: "replace-me-with-float-value"}.
    """
    keys = get_available_target_names(building)
    return {key: "replace-me-with-float-value" for key in keys}


@_accepts_legacy_arguments
def set_zones_always_occupied(building: IDF, verbose: bool = True):
    """
    Sets the occupancy schedule of all 'People' objects (and 'People:Instance' objects, in
    EnergyPlus 26.2) to 'On' (always occupied). If the 'On' schedule does not exist, it creates it.

    :param building: The BESOS/eppy IDF object.
    :param verbose: If True, prints success messages. Warnings are always printed.
    """
    # Create 'On' schedule if missing
    if building.getobject('Schedule:Compact', 'On') is None:
        building.newidfobject(
            'Schedule:Compact',
            Name='On',
            Schedule_Type_Limits_Name="Any Number",
            Field_1='Through: 12/31',
            Field_2='For: AllDays',
            Field_3='Until: 24:00,1'
        )
        if verbose:
            print("Added Schedule: On")
    else:
        warnings.warn("Schedule 'On' already exists. Using existing schedule.")

    # Apply to all People and People:Instance objects
    for i in get_people_objects(building):
        i.Number_of_People_Schedule_Name = 'On'

    if verbose:
        print("Updated all People objects to use schedule 'On'.")


@_accepts_legacy_arguments
def add_vrf_system(
        building: IDF,
        supply_air_temp_input_method: str = 'supply air temperature',
        vrf_eer: float = 2,
        vrf_cop: float = 2.1,
        vrf_availability_schedule: str = 'On 24/7',
        verbose: bool = True,
):
    """
    Adds a Variable Refrigerant Flow (VRF) system to each occupied zone of the model, controlled by
    thermal comfort (Fanger) thermostats, on which apply_apmv_setpoints can then act. The VRF systems are
    autosized, so the zone, system and plant sizing calculations of the model are enabled, as AddAccis does.
    They replace the zone equipment of the model, so its ZoneHVAC:IdealLoadsAirSystem objects are removed.

    :param building: The BESOS/eppy IDF object.
    :param supply_air_temp_input_method: Method for supply air temperature ('supply air temperature' or
        'temperature difference').
    :param vrf_eer: Energy Efficiency Ratio for cooling.
    :param vrf_cop: Coefficient of Performance for heating.
    :param vrf_availability_schedule: Name of the availability schedule for the VRF system.
    :param verbose: If True, prints the process.

    The arguments had other names before accim 1.0.0 (SupplyAirTempInputMethod, eer, cop, VRFschedule,
    verbose_mode), which keep working with a DeprecationWarning.
    """
    from accim.sim.hvac import vrf
    from accim.sim.model import AccimModel
    from accim.sim.outputs import enable_sizing_calculations
    from accim.sim.people import set_comfort_models

    model = AccimModel(building, 'vrf_ac', 'pmv', verbose=verbose)
    set_comfort_models(model)
    vrf.add_vrf_system(model, supply_air_temp_input_method, vrf_eer=vrf_eer, vrf_cop=vrf_cop,
                       vrf_availability_schedule=vrf_availability_schedule)
    vrf.add_setpoint_schedules(model)
    enable_sizing_calculations(model)


def change_adaptive_coeff(building: IDF, df_arguments: pd.DataFrame):
    """
    Updates the adaptive coefficients in the existing EMS programs based on a new DataFrame.
    This allows modifying parameters (e.g., for optimization) without regenerating the
    entire EMS structure from scratch.

    :param building: The BESOS/eppy IDF object.
    :param df_arguments: DataFrame containing the new coefficients, indexed by target key (as that of
        :func:`generate_df_from_args`, with the columns adaptive_coefficient_cooling, adaptive_coefficient_heating
        and underscore_zonename; the names of the columns before accim 1.0.0, adap_coeff_cooling and
        adap_coeff_heating, keep working with a DeprecationWarning).
    """
    legacy = {old: new for old, new in _LEGACY_SETPOINT_ARGUMENTS.items()
              if old in df_arguments.columns and new not in df_arguments.columns}
    if legacy:
        warnings.warn(f'The names of the columns {list(legacy)} of df_arguments are deprecated since accim 1.0.0; '
                      f'use {list(legacy.values())} instead.', DeprecationWarning, stacklevel=2)
        df_arguments = df_arguments.rename(columns=legacy)
    for i in df_arguments.index:
        zonename = df_arguments.loc[i, 'underscore_zonename']

        # Find the specific program for this zone/space
        program = [p for p in building.idfobjects['EnergyManagementSystem:Program']
                   if 'set_zone_input_data' in p.Name and zonename.lower() in p.Name.lower()]

        if program:
            # Update the lines corresponding to adaptive coefficients (the EMS variables keep the names of accim 0.x)
            program[0].Program_Line_1 = (f'set adap_coeff_cooling_{zonename} = '
                                         f'{df_arguments.loc[i, "adaptive_coefficient_cooling"]}')
            program[0].Program_Line_2 = (f'set adap_coeff_heating_{zonename} = '
                                         f'{df_arguments.loc[i, "adaptive_coefficient_heating"]}')


@_accepts_legacy_arguments
def add_ems_debug_output(building: IDF, verbose: bool = True):
    """
    Adds an Output:EnergyManagementSystem object to the IDF.

    This object enables verbose reporting in the EnergyPlus output files (specifically
    the .edd file). It is essential for debugging EMS scripts, as it lists all
    available actuators, internal variables, and runtime errors.

    Configuration applied:
    - Actuator Availability: Verbose
    - Internal Variable Availability: Verbose
    - EMS Runtime Language Debug Output Level: Verbose

    :param building: The BESOS/eppy IDF object.
    :param verbose: If True, prints success messages. Warnings are always printed.
    """
    # Check if the object already exists to avoid duplicates
    output_ems_objs = [i for i in building.idfobjects['Output:EnergyManagementSystem']]

    if len(output_ems_objs) == 0:
        building.newidfobject(
            key='Output:EnergyManagementSystem',
            Actuator_Availability_Dictionary_Reporting='Verbose',
            Internal_Variable_Availability_Dictionary_Reporting='Verbose',
            EMS_Runtime_Language_Debug_Output_Level='Verbose'
        )
        if verbose:
            print("Added Output:EnergyManagementSystem object (Verbose Debugging)")
    else:
        # Warn if it already exists, as it might have different settings
        warnings.warn("Output:EnergyManagementSystem object already exists. Skipping creation.")


def _day_of_year(name: str, value: Union[float, str]) -> int:
    """A day of the cooling season as a day of the year (1 to 366); 'dd/mm' as in the setpoints ('01/05' is 121)."""
    message = f"{name} must be a day of the year (1 to 366) or a date 'dd/mm', not {value!r}."
    try:
        day = transform_ddmm_to_int(value) if isinstance(value, str) else value
    except (ValueError, IndexError):
        raise ValueError(message) from None
    if isinstance(day, bool) or not isinstance(day, numbers.Real) or day != int(day) or not 1 <= day <= 366:
        raise ValueError(message)
    return int(day)


def _seasonal_schedule_fields(heating: Any, cooling: Any, start: int, end: int) -> List[str]:
    """
    The fields of a Schedule:Compact object (after its type limits) with the value of the heating season and that of
    the cooling season, which goes from the day ``start`` to the day before ``end``, also when it goes on into the next
    year (``start > end``), as in the EMS program set_cooling_season of the PMV-based setpoints. The days are converted
    to dates with a year that is not a leap year, as the dates 'dd/mm' of the setpoints.
    """
    if start < end:
        periods = [(start - 1, heating), (end - 1, cooling), (365, heating)]
    else:
        periods = [(end - 1, cooling), (start - 1, heating), (365, cooling)]
    fields = []
    last = 0
    for last_day, value in periods:
        last_day = min(last_day, 365)
        if last_day <= last:
            continue
        day = date(2007, 1, 1) + timedelta(days=last_day - 1)
        fields += [f'Through: {day.month}/{day.day}', 'For: AllDays', f'Until: 24:00,{value}']
        last = last_day
    return fields


def _write_compact_schedule(building: IDF, name: str, fields: List[str]) -> None:
    """Adds a Schedule:Compact object with these fields (after its type limits), replacing the one with this name."""
    existing = building.getobject('Schedule:Compact', name)
    if existing is not None:
        building.removeidfobject(existing)
    building.newidfobject('Schedule:Compact', Name=name, Schedule_Type_Limits_Name='Any Number',
                          **{f'Field_{n}': field for n, field in enumerate(fields, start=1)})


@_accepts_legacy_arguments
def set_pmv_input_parameters(
        building: IDF,
        activity_level: Optional[Union[float, Dict[str, Any]]] = None,
        clothing_insulation: Optional[Union[float, str, Dict[str, Any]]] = None,
        air_velocity: Optional[Union[float, Dict[str, float]]] = None,
        work_efficiency: Optional[Union[float, Dict[str, float]]] = None,
        verbose: bool = True,
        *,
        cooling_season_start: Union[float, str] = 121,
        cooling_season_end: Union[float, str] = 274,
):
    """
    Modifies 'People' objects in the IDF to set the parameters that influence the PMV calculation.

    It writes a 'Schedule:Compact' object for each specified parameter of each People object (Sch_Act_<people>,
    Sch_Clo_<people>, Sch_Vel_<people> and Sch_Eff_<people>), replacing the one of a previous call, and assigns it to
    the People object. In models of EnergyPlus 26.2 with 'People:Instance' objects, the schedules are assigned to the
    People:Instance objects, and the Fanger model is set in the 'People:Definition' objects they reference.

    IMPORTANT: If a parameter is set to None (default), it will NOT be modified in the IDF.
    This allows you to update only specific parameters (e.g., just air velocity) without
    overwriting existing schedules for activity or clothing.

    Each parameter takes one value for all the targets, or a dictionary with a value for each target (the names of
    :func:`get_available_target_names`). Since accim 1.2.0, a value of the activity level or of the clothing
    insulation can also be a dictionary with a value for each season, such as
    ``{'heating_season': 1.0, 'cooling_season': 0.5}``: the schedule has the value of the cooling season from
    ``cooling_season_start`` to the day before ``cooling_season_end``, as the cooling season of the PMV-based setpoints
    (:func:`apply_apmv_setpoints`...), so give them the same days, and that of the heating season the rest of the year.
    The clothing insulation can also be ``'dynamic_ashrae55'``: the dynamic clothing model of ASHRAE 55 (the Clothing
    Insulation Calculation Method DynamicClothingModelASHRAE55 of EnergyPlus), with which EnergyPlus calculates the
    clothing insulation of each day from the outdoor air temperature at 6 a.m., instead of reading the clothing
    insulation schedule. A number or a dictionary by season sets the method ClothingInsulationSchedule, the default of
    EnergyPlus, if the People object had another one.

    :param building: The BESOS/eppy IDF object.
    :param activity_level: Metabolic rate in W/person, or a dictionary by season. If None, ignores this parameter.
    :param clothing_insulation: Clothing insulation in clo units, a dictionary by season, or 'dynamic_ashrae55'. If
        None, ignores this parameter.
    :param air_velocity: Air velocity in m/s. If None, ignores this parameter.
    :param work_efficiency: Work efficiency (0.0 - 1.0). If None, ignores this parameter.
    :param verbose: If True, prints created schedules to console.
    :param cooling_season_start: The first day of the cooling season of the dictionaries by season: the day of the year
        or 'dd/mm' (121, 1 May, by default, as in the setpoints).
    :param cooling_season_end: The day after the last day of the cooling season of the dictionaries by season: the day
        of the year or 'dd/mm' (274, 1 October, by default, as in the setpoints).
    :raises ValueError: If an activity level is given for a People object whose activity level has the metabolic
        correction of :func:`apply_epmv_setpoints`, which reads it from its schedule: set it before applying them.
        Also, if a dictionary by season does not have the keys 'heating_season' and 'cooling_season' only, or has a
        value that is not a number, if 'dynamic_ashrae55' is given for another parameter, or if the days of the
        cooling season are not days of the year or are the same day.
    """
    # 0. The cooling season of the values by season
    season_start = _day_of_year('cooling_season_start', cooling_season_start)
    season_end = _day_of_year('cooling_season_end', cooling_season_end)
    if season_start == season_end:
        raise ValueError('cooling_season_start and cooling_season_end must be different days: the cooling season goes '
                         'from the first one to the day before the second one.')

    # 1. Resolve targets to map People objects to Data Keys
    target_data = _resolve_targets(building)
    df_keys = [t['df_key'] for t in target_data]

    def by_season(arg_val):
        # A dictionary by season, instead of a dictionary with a value for each target
        return isinstance(arg_val, dict) and bool(arg_val) and set(arg_val) <= set(_SEASONS)

    def normalize(value, arg_name):
        # A value of the activity level or the clothing insulation for a target: None, a number,
        # 'dynamic_ashrae55' or ('season', heating, cooling)
        if isinstance(value, dict):
            if set(value) != set(_SEASONS):
                raise ValueError(f"A dictionary by season of {arg_name} must have the keys 'heating_season' and "
                                 f"'cooling_season' only, not {list(value)}.")
            wrong = {season: value[season] for season in _SEASONS
                     if isinstance(value[season], bool) or not isinstance(value[season], numbers.Real)}
            if wrong:
                raise ValueError(f'The values of the dictionary by season of {arg_name} must be numbers: {wrong}.')
            return ('season', value['heating_season'], value['cooling_season'])
        if isinstance(value, str) and value.strip().lower() == _DYNAMIC_CLOTHING:
            if arg_name != 'clothing_insulation':
                raise ValueError(f"'{_DYNAMIC_CLOTHING}' (the dynamic clothing model of ASHRAE 55) is a value of "
                                 f"clothing_insulation, not of {arg_name}.")
            return _DYNAMIC_CLOTHING
        return value

    # Helper to map input args (Float, Dict, or None) to a lookup dictionary
    def map_arg_to_lookup(arg_val, label, arg_name=None):
        # arg_name: the name of the argument if it takes values by season ('dynamic_ashrae55' for the clothing)
        data = {}
        if arg_val is None:
            return data  # Empty dict will return None on .get()

        if isinstance(arg_val, dict) and not (arg_name and by_season(arg_val)):
            # Validate keys
            dropped = [k for k in arg_val if k not in df_keys]
            if dropped:
                warnings.warn(f"Keys dropped from {label}: {dropped}")

            for k in df_keys:
                value = arg_val.get(k, None)  # None if key missing in user dict
                data[k] = normalize(value, arg_name) if arg_name and value is not None else value
        else:
            # Apply single value to all targets
            value = normalize(arg_val, arg_name) if arg_name else arg_val
            for k in df_keys:
                data[k] = value
        return data

    val_map_activity = map_arg_to_lookup(activity_level, 'activity', 'activity_level')
    val_map_clo = map_arg_to_lookup(clothing_insulation, 'clo', 'clothing_insulation')
    val_map_vel = map_arg_to_lookup(air_velocity, 'vel')
    val_map_eff = map_arg_to_lookup(work_efficiency, 'eff')

    # 2. Map each People object to the keys of the targets of its instances
    people_to_keys: Dict[str, List[str]] = {}
    for t in target_data:
        for people_name in t['people_names']:
            people_to_keys.setdefault(people_name.strip().upper(), []).append(t['df_key'])

    # The metabolic correction of the ePMV sets the activity level schedule of its People objects (a copy of their
    # schedule, which it reads), so a new activity level schedule would remove the correction
    corrected = [str(people.Name) for people in get_people_objects(building)
                 if val_map_activity.get((people_to_keys.get(people.Name.strip().upper()) or [None])[0]) is not None
                 and str(people.Activity_Level_Schedule_Name).strip().upper()
                 == metabolic_correction_names(people.Name)['schedule'].upper()]
    if corrected:
        raise ValueError(f'The activity level of the People objects {corrected} has the metabolic correction of the '
                         f'ePMV setpoints (apply_epmv_setpoints), which reads it from their schedules: set the '
                         f'activity level with set_pmv_input_parameters before applying the setpoints.')

    # 3. Iterate over People and People:Instance objects
    for people in get_people_objects(building):
        p_name = people.Name

        # --- A. Find the Target Key for this Person ---
        people_keys = people_to_keys.get(p_name.strip().upper(), [])
        if not people_keys:
            # If we can't map the person, we can't apply parameters
            continue

        # A People object has one schedule per parameter, so the value of its first target is used
        target_key = people_keys[0]
        for arg_name, val_map in [('activity_level', val_map_activity), ('clothing_insulation', val_map_clo),
                                  ('air_velocity', val_map_vel), ('work_efficiency', val_map_eff)]:
            if len({val_map.get(k) for k in people_keys}) > 1:
                warnings.warn(f"People object '{p_name}' applies to several targets ({people_keys}) with different "
                              f"values of {arg_name}. It can only have one schedule, so the value of "
                              f"'{target_key}' is used.")

        # --- B. Retrieve Values ---
        # If the user didn't provide the arg, these will be None
        act_val = val_map_activity.get(target_key)
        clo_val = val_map_clo.get(target_key)
        vel_val = val_map_vel.get(target_key)
        eff_val = val_map_eff.get(target_key)

        # Sanitized name for schedules
        p_name_san = _sanitize_ems_name(p_name)

        # --- C. Apply Changes (Only if value is not None): a schedule with the value of each parameter ---
        parameters = [
            (act_val, 'Act', 'Activity_Level_Schedule_Name', 'Activity', ' W/person'),
            (clo_val, 'Clo', 'Clothing_Insulation_Schedule_Name', 'Clothing', ' clo'),
            (vel_val, 'Vel', 'Air_Velocity_Schedule_Name', 'Air Velocity', ' m/s'),
            (eff_val, 'Eff', 'Work_Efficiency_Schedule_Name', 'Work Efficiency', ''),
        ]
        any_modified = False
        for value, short_name, field, label, unit in parameters:
            if value is None:
                continue
            any_modified = True
            if isinstance(value, str) and value == _DYNAMIC_CLOTHING:
                # EnergyPlus calculates the clothing insulation, and does not read the clothing insulation schedule
                people.Clothing_Insulation_Calculation_Method = 'DynamicClothingModelASHRAE55'
                if verbose:
                    print(f"Set Clothing for '{p_name}': the dynamic clothing model of ASHRAE 55 "
                          f"(DynamicClothingModelASHRAE55)")
                continue
            if isinstance(value, tuple):
                _, heating, cooling = value
                fields = _seasonal_schedule_fields(heating, cooling, season_start, season_end)
                message = (f"Set {label} for '{p_name}': {heating}{unit} in the heating season and "
                           f"{cooling}{unit} in the cooling season")
            else:
                fields = ['Through: 12/31', 'For: AllDays', f'Until: 24:00,{value}']
                message = f"Set {label} for '{p_name}': {value}{unit}"
            sch_name = f'Sch_{short_name}_{p_name_san}'
            _write_compact_schedule(building, sch_name, fields)
            setattr(people, field, sch_name)
            if short_name == 'Clo':
                # The clothing insulation schedule is only read with the method ClothingInsulationSchedule
                method = str(getattr(people, 'Clothing_Insulation_Calculation_Method', '') or '').strip()
                if method and method.lower() != 'clothinginsulationschedule':
                    people.Clothing_Insulation_Calculation_Method = 'ClothingInsulationSchedule'
            if verbose:
                print(message)

        # --- D. Ensure Fanger Model ---
        # Only force Fanger if we actually touched this object
        if any_modified:
            if is_people_instance(people):
                # The thermal comfort models of a People:Instance object are in its People:Definition
                definition = get_people_definition(building, people)
                if definition is None:
                    warnings.warn(f"People:Definition '{people.People_Definition_Name}' of People:Instance "
                                  f"'{p_name}' not found: the Fanger model could not be set.")
                else:
                    definition.Thermal_Comfort_Model_1_Type = 'Fanger'
            else:
                people.Thermal_Comfort_Model_1_Type = 'Fanger'
