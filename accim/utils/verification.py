# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Verification of the simulations of the models of accim: checks of the outputs against the arguments of
the ACCIS, and of the values that the EMS calculates (the indices derived from the PMV, the metabolic correction of
the ePMV and the setpoints of :func:`accim.sim.preview.compute_setpoints`)."""

import os
import re
import warnings
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from accim.utils.accim_args import get_accim_args_flattened
from accim.utils.outputs import read_csv_outputs, read_eso_using_readvarseso

__all__ = [
    'AccimSimulationVerifier',
    'verify_accim_simulation',
]

#: The units and the frequency after the variable in the columns of the CSV files of EnergyPlus: ' [C](Hourly)'
_UNITS_AND_FREQUENCY = re.compile(r'\s*\[[^\]]*\]\s*(\([A-Za-z]+\))?\s*$')


def _key_and_variable(column: Any) -> Tuple[str, str]:
    """The key and the variable of a column of the outputs, ``'<key>:<variable>'`` (with or without the units and the
    frequency of the CSV files of EnergyPlus after the variable), in upper case.

    The key is all the text before the last ':', as :func:`accim.utils.outputs.read_eso_using_readvarseso` reads it:
    the names of the output variables of EnergyPlus have no ':', and the keys can have them (the zones
    ``Block1:Zone1`` of the models of DesignBuilder, and their coils, surfaces and People objects). A name without
    ':' has no key (``''``)."""
    key, separator, variable = str(column).upper().rpartition(':')
    variable = _UNITS_AND_FREQUENCY.sub('', variable).strip()
    return (key.strip(), variable) if separator else ('', variable)


def _fragment_rank(name: str, fragment: str) -> Optional[int]:
    """How a name contains a fragment (both in upper case): 0, it is the fragment; 1, it has it as whole words
    ('BLOCK1:ZONE1' in 'BLOCK1:ZONE1 VRF INDOOR UNIT DX COOLING COIL', but not in 'BLOCK1:ZONE10'); 2, it has it
    within a longer word or number; None, it does not have it."""
    if fragment not in name:
        return None
    if name == fragment:
        return 0
    # Whole words: no letter or digit right before or after the fragment
    return 1 if re.search(r'(?<![^\W_])' + re.escape(fragment) + r'(?![^\W_])', name) else 2


def _find_column(columns, key_fragment: Any, variable_fragment: Any, keyless: bool = False) -> Optional[Any]:
    """The column of the outputs whose key contains ``key_fragment`` and whose variable contains
    ``variable_fragment`` (not case-sensitive), or None.

    Of several, the one whose key is closest to the fragment (the fragment itself, then with it as whole words, then
    with it within a longer name), then the one whose variable is, then the first one: the outputs of the zone
    ``Block1:Zone1`` are not taken from those of ``Block1:Zone10``. The keys keep their ':' (see
    :func:`_key_and_variable`). With ``keyless``, a column without a key is taken by its variable alone if no column
    with a key has both fragments."""
    wanted_key, wanted_variable = str(key_fragment).upper().strip(), str(variable_fragment).upper().strip()
    best, best_rank = None, None
    for column in columns:
        key, variable = _key_and_variable(column)
        variable_rank = _fragment_rank(variable, wanted_variable)
        if variable_rank is None:
            continue
        if key:
            key_rank = _fragment_rank(key, wanted_key)
        else:
            key_rank = 3 if keyless else None
        if key_rank is None:
            continue
        if best_rank is None or (key_rank, variable_rank) < best_rank:
            best, best_rank = column, (key_rank, variable_rank)
    return best


def verify_accim_simulation(
        eso_file_path: str,
        idf_path: str,
        eplus_install_dir: Optional[str] = None,
        tolerance: float = 0.1,
        epw: Optional[str] = None,
        calculation_tolerance: float = 1e-3,
        setpoints_not_met: bool = False,
) -> pd.DataFrame:
    """
    Reads EnergyPlus simulation output and verifies that the ACCIS EMS scripts
    added by AddAccis are working correctly.

    The function performs six categories of checks:

    **Check 1 – The setpoints while the HVAC systems are on (per zone):**
    The timesteps in which the HVAC system of a zone is on and the zone is beyond its setpoint (``Check1_Cooling``
    and ``Check1_Heating``):

    - It cools (CoolCoil > 0) and Zone Operative Temperature > ACST_Sch + tolerance
    - It heats (HeatCoil > 0) and Zone Operative Temperature < AHST_Sch - tolerance

    They are not mismatches of the EMS: they tell of the HVAC system, whose capacity or response does not hold the
    setpoint. So they are not rows of the result: its attribute ``attrs['setpoints_not_met']`` has them (a table with
    the columns of the result), the summary counts them, and ``setpoints_not_met=True`` adds them to the result, as
    until accim 1.2.0. With the outputs at timestep frequency, or else hourly.

    **Check 2 – The operation of the windows (per window or door, in mixed mode):**
    The opening factor of each window (``Check2_OpeningFactor``) is that of its EMS programs, ``SetMyVOF_<window>``
    and ``SetWindowOperation_<window>``, with the values that they read at the beginning of each timestep: the
    operative temperature of its zone and what its HVAC system cooled and heated (with the existing HVAC systems, the
    load to the setpoints of its thermostat), of the previous timestep; and the outdoor air temperature and the wind
    speed of its zone, its occupants, and the cooling setpoint, the ventilation setpoint and the minimum outdoor
    temperature that the EMS calculates for its zone, of the timestep itself:

    *HVACmode = 0 (full air-conditioning):* the window is closed.

    *HVACmode = 1 (naturally ventilated):* the window is open, with the opening factor of ``SetMyVOF_<window>``, when
    OutT < OpT, OutT > MinOutTemp, WindSpeed <= MaxWindSpeed, and OpT > VST (VentCtrl = 0) or OpT > ACSTnoTol
    (VentCtrl = 1).

    *HVACmode = 2 (mixed mode):* the window is open (fully with VentCtrl 0 or 1; with the opening factor of
    ``SetMyVOF_<window>`` with VentCtrl 2 or 3) when its HVAC system neither cooled nor heated, OpT < ACST,
    WindSpeed <= MaxWindSpeed, OutT > MinOutTemp, OutT < OpT, its zone is occupied and OpT > VST.

    It needs the outputs at timestep frequency, and does not check the first timestep of each environment. The
    outdoor air temperature and the wind speed that the programs read are those of the zone (*Zone Outdoor Air
    Drybulb Temperature* and *Zone Outdoor Air Wind Speed*, at the height of its centroid), which the standard outputs
    lack: ``output_type='detailed'`` adds them. Without them, those of the site are taken and the summary says so: a
    mismatch may then be the difference between them (in the sample model, 0.0016 K, and a wind speed of 49 % of that
    of the site, which matters where the maximum wind speed is reached). Until accim 1.2.0 this check compared the
    conditions with the outputs of the same timestep, and with constants for the ventilation setpoint and the minimum
    outdoor temperature, so it reported timesteps that were not mismatches; and checks 1 and 2 skipped the zones and
    the windows whose names have ':' (those of the models of DesignBuilder).

    **Check 3 – Setpoints based on the PMV (per zone, models of** :func:`accim.sim.pmv_index.apply_pmv_index_setpoints`,
    **such as those of** :func:`accim.sim.apmv.apply_apmv_setpoints` **and** :func:`accim.sim.apmv.apply_epmv_setpoints`
    **):**
    The EMS calculates the index of each zone at the beginning of each timestep from the PMV of its occupants of the
    previous timestep (*Zone Thermal Comfort Fanger Model PMV* of each People object; in a zone with several, their
    mean weighted by their *People Occupant Count* of the timestep), so these checks need the outputs at timestep
    frequency; the first timestep of each environment (sizing period or run period) is not checked:

    - ``Check3_aPMV``: aPMV = PMV/(1 + λ·PMV) (Yao et al., 2009), with the adaptive coefficient λ of the output
      ``Adaptive Coefficient_<zone>``.
    - ``Check3_ePMV``: ePMV = e·PMV if PMV > 0, and PMV otherwise (Fanger and Toftum, 2002, as accim applies it: on
      the warm side of the scale; on both sides with ``apply_to_heating``), with the expectancy factor e of the output
      ``Expectancy Factor_<zone>`` (1 in the heating season).
    - ``Check3_PMV``: the PMV of the zone of the PMV setpoints is that of the previous timestep.
    - ``Check3_MetabolicFactor`` (ePMV setpoints with ``metabolic_correction=True``, each People object):
      Metabolic Correction Factor = 1 − 0.067·PMV in the cooling season (Fanger and Toftum, 2002), with the PMV of the
      previous timestep between 0 and 3 (the mean of the zones of the People object, weighted by their occupants), and
      1 in the heating season.
    - ``Check3_CorrectedActivity``: Corrected Activity Level = the activity level without the correction (the output
      *Schedule Value* of its schedule, which must be added to the model to check it) times that factor.
    - ``Check3_PpdWeightedHours`` (``report_ppd_weighted_hours=True``, each zone): the PPD-weighted hours of Method C
      of CEN/TR 16798-2:2019, Annex D, ``PPD Weighted Hours_<zone>``: in each occupied timestep (the output
      ``Occupied hours_<zone>``, its length), PPD(PMV)/PPD(PMVlimit) (ISO 7730:2025, formula (5)) if the PMV of the
      previous timestep is at or above the upper limit, or below the lower limit, and 0 otherwise; the limits are the
      setpoints of the index without the tolerances (``<index> Heating Setpoint No Tolerance_<zone>``...) on the scale
      of the PMV: those of the PMV, aPMV/(1 − λ·aPMV) with the λ of the output ``Adaptive Coefficient_<zone>`` (or,
      with ``adaptive_coefficient_by='pmv_sign'``, read from the monitor of the zone, the λ of each side of the scale
      of the program ``set_zone_input_data_<zone>``), and ePMV/e on the side of the scale where the monitor of the
      zone applies the expectancy factor e of the output ``Expectancy Factor_<zone>``.

    **Check 4 – Setpoints against** :func:`accim.sim.preview.compute_setpoints` **(per zone, output IDFs of AddAccis,
    only with** ``epw`` **):**
    The comfort temperature and the setpoints that the EMS of each zone reports (``Comfort Temperature_<zone>``,
    ``Adaptive Cooling Setpoint Temperature_<zone>``... with and without the tolerance) are those that
    ``compute_setpoints`` calculates with the arguments of the zone (its program ``SetInputData_<zone>``), the weather
    file ``epw``, the first day of the RunPeriod and the timesteps per hour of the model; and the running mean outdoor
    temperatures of EnergyPlus (*Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air
    Temperature* and *... ASHRAE 55 ...*) are those of :func:`accim.sim.preview.energyplus_running_means`
    (``Check4_RMOT``, ``Check4_PMOT``, ``Check4_ComfTemp``, ``Check4_ACST``, ``Check4_AHST``, ``Check4_ACSTnoTol``
    and ``Check4_AHSTnoTol``). With the custom model and an outdoor metric other than 'pmot'
    (:mod:`accim.sim.ems.outdoor_metric`), and with JPN Aqilah 2025 in a model whose programs of the outdoor metric
    begin with the values of a weather file (its running mean of EN 16798-1 with α = 0.8,
    :data:`accim.sim.ems.standard_lines.WEATHER_FILE_METRICS`), the outdoor metric that the EMS of each zone calculates
    (``Tout_metric_<zone>``) is that of ``compute_setpoints`` too (``Check4_Tout_metric``), which begins as the programs
    of the model do (with the values of the weather file given to AddAccis, or with PMOT; with them, T0 of
    'te_ref_nl' is that of the Schedule:File object of that weather file). The static setpoints of JPN
    Aqilah 2025 are those of the inputs StaticAHST and StaticACST of each zone. With the regimes of the
    custom model (:mod:`accim.sim.ems.custom_regimes`), ``compute_setpoints`` gets those of the program
    ``SelectCustomRegime_<zone>`` of each zone, and the number of the regime that the EMS reports
    (``CustomRegime_<zone>``) is that of ``compute_setpoints`` (``Check4_custom_regime``); the zones whose regimes have
    the conditions 'hvac_off' or 'hvac_on', which depend on the HVAC system, are not checked. They are checked with the
    outputs at timestep frequency, or else hourly, of the last environment of the outputs (the run period). The zones
    whose setpoints a hook of the API backend sets (the setpoints of the ATHB and of the SET of
    :mod:`accim.sim.comfort_hooks`, with the program ``ApplyHookSetpoints_<zone>``) are not checked. In the zones with
    the limiter of the drift of the setpoints (:mod:`accim.sim.ems.drift_limiter`), the setpoints applied depend on the
    indoor temperatures of the simulation, so its targets (``DriftTargetAHST_<zone>`` and ``DriftTargetACST_<zone>``,
    the setpoints of the comfort standard without the tolerance, before the minimum and maximum of the setpoints) are
    those of ``compute_setpoints`` without the minimum and maximum (``Check4_DriftTargetAHST`` and
    ``Check4_DriftTargetACST``), and the setpoints applied are not checked. The running mean
    of ASHRAE 55 of a run period that begins between the 2nd and the 30th of January is that of EnergyPlus 25.1 (with
    the mean of 31 December in place of that of the day before the run period, see
    :func:`accim.sim.preview.energyplus_running_means`); with a .stat file next to the weather file, EnergyPlus takes it
    from the monthly means of the .stat file, which check 4 does not reproduce (its summary says so).

    **Check 5 – The minimum and maximum of the setpoints (per zone, output IDFs of AddAccis):**
    The heating setpoint of the thermostat of each zone with a minimum (``heating_setpoint_minimum``, the input
    ``AHSTmin`` of its program ``SetInputData_<zone>``, see :mod:`accim.sim.ems.setpoint_limits`) is not below the
    minimum plus the tolerance of the setpoints of the zone (``Check5_AHSTmin``), and the cooling setpoint of each zone
    with a maximum (``cooling_setpoint_maximum``, ``ACSTmax``) is not above the maximum minus that tolerance
    (``Check5_ACSTmax``), in the outputs at timestep frequency, or else hourly: the thermostats get the minimum and
    the maximum with the tolerance (finding A19 of the self-audit of 2026-11-11, decided on 2026-11-12). The setpoints
    without the tolerance (the outputs ``..._No Tolerance``, the limits of the comfort band of the hour counters) are
    checked against the minimum and the maximum themselves (``Check5_AHSTmin_noTol`` and ``Check5_ACSTmax_noTol``):
    since finding B5-1 of the review of accim 1.2.0, the minimum and the maximum bound them as well.

    **Check 6 – The long-term discomfort (per zone and building, output IDFs of AddAccis with**
    ``report_long_term_discomfort=True`` **, see** :mod:`accim.sim.ems.long_term_discomfort` **):**
    In each timestep with occupants (the output ``Occupied Hours_<zone>``, the length of the timestep), the outputs
    ``Hours Above Upper Limit_<zone>`` and ``Hours Below Lower Limit_<zone>`` are the length of the timestep if the
    operative temperature of the zone of the previous timestep (that which the EMS reads) is above the cooling setpoint
    without the tolerance (``Adaptive Cooling Setpoint Temperature_No Tolerance_<zone>``), or below the heating
    setpoint without the tolerance (or above and below the limits of ``long_term_range`` that the program of the zone
    has: the constant ones of EN 16798-1, Table B.2, or those of the season of its Table B.5, by the running mean
    outdoor temperature of CEN 15251 of the previous timestep, which needs its output), and ``Degree Hours Above Upper
    Limit_<zone>`` and
    ``Degree Hours Below Lower Limit_<zone>`` are the difference times that length (Methods A and B of CEN/TR
    16798-2:2019, Annex D); in the timesteps without occupants, they are 0 (``Check6_<output>``). The outputs of the
    building (``..._Building``) are the sums of those of the zones. They are checked with the outputs at timestep
    frequency; the first timestep of each environment is not checked.

    :param eso_file_path: Path to the eplusout.eso file.
    :type eso_file_path: str
    :param idf_path: Path to the IDF file used for simulation (to read accim args and window names).
    :type idf_path: str
    :param eplus_install_dir: Path to EnergyPlus installation directory (for ReadVarsESO).
    :type eplus_install_dir: str, optional
    :param tolerance: Temperature tolerance in °C for setpoint checks. Default is 0.1 °C.
    :type tolerance: float
    :param epw: The weather file of the simulation, for check 4 (not done without it).
    :type epw: str, optional
    :param calculation_tolerance: The largest difference between the values that the EMS calculates and those of
        checks 2 to 6 (in °C for the temperatures). Default is 0.001.
    :type calculation_tolerance: float
    :param setpoints_not_met: True to add the timesteps of check 1 to the result. By default they are only in its
        attribute ``attrs['setpoints_not_met']``, since they are not mismatches of the EMS.
    :type setpoints_not_met: bool
    :return: DataFrame with all detected mismatch timesteps, with columns
        ['timestep', 'zone_or_window', 'check', 'description', 'value_found', 'value_expected'].
        Empty DataFrame means all checks passed.
        Its attribute ``attrs['setpoints_not_met']`` is a DataFrame with those columns and the timesteps of
        check 1.
    :rtype: pd.DataFrame
    """

    # ─────────────────────────────────────────────
    # 1. READ THE OUTPUTS OF THE SIMULATION AND THE MODEL
    # ─────────────────────────────────────────────
    print(f"Reading ESO file: {eso_file_path}")
    eso = read_eso_using_readvarseso(
        eso_file_path=eso_file_path,
        eplus_install_dir=eplus_install_dir,
        only_run_period=True,
        cleanup=False,
    )
    if all(frame.empty for frame in eso['data'].values()):
        warnings.warn("No simulation output data found in the ESO file.")
        return pd.DataFrame()

    print(f"Reading IDF: {idf_path}")
    from accim.sim.accis import load_idf
    building = load_idf(idf_path)

    mismatch_rows: List[dict] = []

    # ─────────────────────────────────────────────
    # 5.A CHECK 1 – THE SETPOINTS WHILE THE HVAC SYSTEMS ARE ON
    # ─────────────────────────────────────────────
    not_met, messages = _setpoints_not_met(building, eso['data'], tolerance)
    if messages:
        print("\n--- Check 1: The setpoints of the zones while their HVAC systems are on ---")
        print('\n'.join(messages))
    if setpoints_not_met:
        mismatch_rows.extend(not_met)

    # ─────────────────────────────────────────────
    # 5.B CHECK 2 – THE OPERATION OF THE WINDOWS
    # ─────────────────────────────────────────────
    rows, messages = _window_mismatches(building, eso['data'], calculation_tolerance)
    if messages:
        print("\n--- Check 2: The operation of the windows (SetWindowOperation_<window>) ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.C CHECK 3 – SETPOINTS BASED ON THE PMV
    # ─────────────────────────────────────────────
    timestep_data = eso['data'].get('Timestep')
    rows, messages = _pmv_index_mismatches(building, timestep_data, calculation_tolerance)
    if messages:
        print("\n--- Check 3: Setpoints based on the PMV (the index of the PMV of the previous timestep) ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.D CHECK 4 – SETPOINTS AGAINST compute_setpoints
    # ─────────────────────────────────────────────
    if epw is not None:
        print("\n--- Check 4: Setpoints and running means against accim.sim.preview.compute_setpoints ---")
        rows, messages = _setpoint_mismatches(building, eso['data'], epw, calculation_tolerance)
        print('\n'.join(messages))
        mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.E CHECK 5 – THE MINIMUM AND MAXIMUM OF THE SETPOINTS
    # ─────────────────────────────────────────────
    rows, messages = _setpoint_limit_mismatches(building, eso['data'], calculation_tolerance)
    if messages:
        print("\n--- Check 5: The minimum heating setpoint and the maximum cooling setpoint ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 5.F CHECK 6 – THE LONG-TERM DISCOMFORT
    # ─────────────────────────────────────────────
    rows, messages = _long_term_mismatches(building, eso['data'], calculation_tolerance)
    if messages:
        print("\n--- Check 6: The long-term discomfort of the occupied hours ---")
        print('\n'.join(messages))
    mismatch_rows.extend(rows)

    # ─────────────────────────────────────────────
    # 6. RETURN RESULTS
    # ─────────────────────────────────────────────
    result_df = pd.DataFrame(mismatch_rows)
    # The timesteps of check 1, which are not mismatches of the EMS (unless setpoints_not_met asks for them)
    result_df.attrs['setpoints_not_met'] = pd.DataFrame(not_met, columns=_MISMATCH_COLUMNS)

    if result_df.empty:
        print("\nAll checks passed. No mismatches detected.")
    else:
        print(f"\n{len(result_df)} mismatch(es) detected across "
              f"{result_df['check'].nunique()} check type(s).")
        print(result_df.groupby(['zone_or_window', 'check']).size()
              .rename('count').reset_index().to_string(index=False))
    if not_met and not setpoints_not_met:
        print(f"{len(not_met)} timestep(s) with the HVAC system of a zone on and the zone beyond its setpoint "
              f"(check 1): they are not mismatches of the EMS, and they are in attrs['setpoints_not_met'] of the "
              f"result.")

    return result_df


# ─────────────────────────────────────────────────────────────────────────────
# CHECKS 3 AND 4: THE VALUES THAT THE EMS CALCULATES
# ─────────────────────────────────────────────────────────────────────────────

#: The date and time of a row of the outputs of EnergyPlus: 'MM/DD  HH:MM:SS'
_DATE_TIME = re.compile(r'(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})')
#: The program that applies the setpoints of an index of accim.sim.pmv_index to a zone: apply_<index>_<zone>
_PMV_INDEX_PROGRAM = re.compile(r'apply_(aPMV|ePMV|PMV)_(.+)$', re.IGNORECASE)
#: The running mean outdoor temperatures of EnergyPlus, by their columns in accim.sim.preview
_RUNNING_MEANS = {
    'RMOT': 'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
    'PMOT': 'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',
}


def _dates_and_times(timestamps: Sequence[str]) -> Tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """The date and time of the end of each row of the outputs of EnergyPlus (``'MM/DD  HH:MM:SS'``; ``24:00:00`` is
    the end of the day, the midnight of the next day), and the date of each row (that of the timestamp, also at
    24:00:00), in the year of :func:`accim.sim.preview.compute_setpoints` (2007, or 2008 if there is a 29 February).

    :raises ValueError: If a timestamp has another format.
    """
    parts = []
    for timestamp in timestamps:
        match = _DATE_TIME.search(str(timestamp))
        if match is None:
            raise ValueError(f'{timestamp!r} is not a date and time of the outputs of EnergyPlus (MM/DD  HH:MM:SS).')
        parts.append([int(value) for value in match.groups()])
    parts = np.array(parts, dtype=np.int64).reshape(-1, 5)
    year = 2008 if ((parts[:, 0] == 2) & (parts[:, 1] == 29)).any() else 2007
    dates = pd.DatetimeIndex(pd.to_datetime(pd.DataFrame({'year': np.full(len(parts), year), 'month': parts[:, 0],
                                                          'day': parts[:, 1]})))
    seconds = parts[:, 2] * 3600 + parts[:, 3] * 60 + parts[:, 4]
    return dates + pd.to_timedelta(seconds, unit='s'), dates


def _environment_starts(datetimes: pd.DatetimeIndex) -> np.ndarray:
    """Whether each row of the outputs is the first one of an environment (a sizing period or a run period): its time
    is not that of the previous row plus one step (the most frequent difference between rows)."""
    starts = np.ones(len(datetimes), dtype=bool)
    if len(datetimes) > 1:
        differences = np.diff(datetimes.asi8)
        starts[1:] = differences != pd.Series(differences).mode().iloc[0]
    return starts


class _Outputs:
    """The outputs of one frequency of :func:`accim.utils.outputs.read_eso_using_readvarseso` (a DataFrame with the
    columns (key, variable, units) and the date and time of each row as its index): their values by key and variable
    (in any case), the date and time of the end of each row, its date, and the first rows of the environments."""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame
        self.timestamps = [str(timestamp).strip() for timestamp in frame.index]
        self.datetimes, self.dates = _dates_and_times(self.timestamps)
        self.starts = _environment_starts(self.datetimes)
        self._columns = {(str(column[0]).strip().upper(), str(column[1]).strip().upper()): column
                         for column in frame.columns}

    def get(self, key: str, variable: str) -> Optional[np.ndarray]:
        """The values of an output (None if it is not in the outputs)."""
        column = self._columns.get((str(key).strip().upper(), str(variable).strip().upper()))
        return None if column is None else self.frame[column].to_numpy(dtype=float)

    def keys(self, variable: str) -> List[str]:
        """The keys of an output variable."""
        return [str(column[0]) for (_, name), column in self._columns.items() if name == variable.strip().upper()]

    def previous(self, values: np.ndarray) -> np.ndarray:
        """The values of the previous row (NaN in the first row of each environment)."""
        result = np.r_[np.nan, values[:-1]]
        result[self.starts] = np.nan
        return result


def _program_lines(program) -> List[str]:
    return [str(line).strip() for line in program.fieldvalues[2:] if str(line).strip()]


def _weighted_mean(values: Sequence[np.ndarray], weights: Sequence[np.ndarray]) -> np.ndarray:
    """The mean of some values weighted by the occupants, or their simple mean where there are none, as the EMS
    programs of accim.sim.pmv_index calculate the PMV of a zone with several People objects."""
    total = sum(weights)
    weighted = sum(value * weight for value, weight in zip(values, weights))
    return np.where(total > 0, weighted / np.where(total > 0, total, 1), sum(values) / len(values))


def _mismatch_rows(timestamps: Sequence[str], found: np.ndarray, expected: np.ndarray, zone: str, check: str,
                   description: str, tolerance: float) -> Tuple[List[dict], str]:
    """The mismatches (the rows whose value differs from the expected one by more than the tolerance; the rows without
    an expected value are not checked), and a line of the summary."""
    difference = np.abs(found - expected)
    checked = np.isfinite(difference)
    bad = np.flatnonzero(checked & (np.where(checked, difference, 0) > tolerance))
    rows = [{
        'timestep': timestamps[position],
        'zone_or_window': zone,
        'check': check,
        'description': f'{description}: {found[position]:.6f} instead of {expected[position]:.6f}',
        'value_found': round(float(found[position]), 6),
        'value_expected': round(float(expected[position]), 6),
    } for position in bad]
    return rows, f"  '{zone}' {check} ({description}): {len(bad)} mismatch(es) in {int(checked.sum())} timesteps"


def _pmv_index_mismatches(building, frame: Optional[pd.DataFrame], tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 3 of :func:`verify_accim_simulation`: the indices derived from the PMV of the setpoints of
    :mod:`accim.sim.pmv_index`, and the metabolic correction of the ePMV, from the PMV of the previous timestep.

    :param building: The model (eppy).
    :param frame: The outputs at timestep frequency of :func:`accim.utils.outputs.read_eso_using_readvarseso` (None
        if there are none).
    :param tolerance: The largest difference allowed.
    :return: The mismatches, and the lines of the summary (none if the model has no setpoints based on the PMV).
    """
    from accim.constants import EPMV_MET_REDUCTION_PER_PMV
    from accim.data.postprocessing.long_term_discomfort import ppd_from_pmv
    from accim.sim.ems.erl import ErlProgramSet
    from accim.sim.pmv_index import (_MAX_METABOLIC_PMV, PMV_INDICES, PPD_WEIGHTED_HOURS_PROGRAM,
                                     metabolic_correction_names)
    from accim.sim.targets import resolve_targets, sanitize_ems_name
    from accim.utils.people import get_people_objects

    indices = {pmv_index.name.upper(): pmv_index for pmv_index in PMV_INDICES.values()}
    programs = {str(program.Name).upper(): program for program in building.idfobjects['EnergyManagementSystem:Program']}
    zones = []
    for program in building.idfobjects['EnergyManagementSystem:Program']:
        match = _PMV_INDEX_PROGRAM.match(str(program.Name))
        if match is not None and match.group(1).upper() in indices:
            zones.append((indices[match.group(1).upper()], match.group(2)))
    if not zones:
        return [], []
    if frame is None or frame.empty:
        message = ("The setpoints based on the PMV are checked with the outputs at timestep frequency, since the EMS "
                   "calculates the index of each timestep from the PMV of the previous one: add 'timestep' to the "
                   "output_frequencies of the setpoints to check them.")
        warnings.warn(message)
        return [], [f'  Not checked. {message}']
    outputs = _Outputs(frame)
    sensors = {str(sensor.Name).upper(): (str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name),
                                          str(sensor.OutputVariable_or_OutputMeter_Name))
               for sensor in building.idfobjects['EnergyManagementSystem:Sensor']}

    def sensor_values(name: str) -> Tuple[Optional[np.ndarray], str]:
        """The values of the output that an EMS sensor reads, and what is missing if they are not in the outputs."""
        if name.upper() not in sensors:
            return None, f'the EMS sensor {name}'
        key, variable = sensors[name.upper()]
        values = outputs.get(key, variable)
        return values, ('' if values is not None else f"the output '{variable}' of '{key}' at timestep frequency")

    def zone_pmv(suffix: str) -> Tuple[Optional[np.ndarray], str]:
        """The PMV of a zone that the EMS reads at each timestep: that of its People object of the previous timestep
        (with several People objects, their mean weighted by their occupants of the timestep)."""
        if f'PMV_{suffix}'.upper() in sensors:
            pmv, missing = sensor_values(f'PMV_{suffix}')
            return (None, missing) if pmv is None else (outputs.previous(pmv), '')
        values, weights = [], []
        number = 1
        while f'PMV_{suffix}_{number}'.upper() in sensors:
            pmv, missing = sensor_values(f'PMV_{suffix}_{number}')
            occupants, missing_occupants = sensor_values(f'People_Occupant_Count_{suffix}_{number}')
            if pmv is None or occupants is None:
                return None, missing or missing_occupants
            values.append(outputs.previous(pmv))
            weights.append(occupants)
            number += 1
        if not values:
            return None, f'the EMS sensor PMV_{suffix}'
        return _weighted_mean(values, weights), ''

    rows: List[dict] = []
    lines: List[str] = []

    def check(found, expected, zone, name, description):
        new_rows, line = _mismatch_rows(outputs.timestamps, found, expected, zone, name, description, tolerance)
        rows.extend(new_rows)
        lines.append(line)

    with np.errstate(invalid='ignore'):
        pmv_of_zones: Dict[str, np.ndarray] = {}
        for pmv_index, suffix in zones:
            name = pmv_index.name
            pmv, missing = zone_pmv(suffix)
            found = outputs.get('EMS', f'{name}_{suffix}')
            coefficient = (outputs.get('EMS', f'{pmv_index.coefficient_output}_{suffix}')
                           if pmv_index.coefficient_output else None)
            if found is None:
                missing = f"the output '{name}_{suffix}' at timestep frequency"
            elif pmv_index.coefficient_output and coefficient is None:
                missing = f"the output '{pmv_index.coefficient_output}_{suffix}' at timestep frequency"
            if pmv is not None:
                pmv_of_zones[suffix] = pmv
            if pmv is None or missing:
                lines.append(f"  '{suffix}' Check3_{name}: not checked, without {missing}.")
                continue
            if pmv_index.key == 'apmv':
                # Yao et al. (2009)
                check(found, pmv / (1 + coefficient * pmv), suffix, 'Check3_aPMV', 'aPMV = PMV/(1 + lambda*PMV)')
            elif pmv_index.key == 'epmv':
                # Fanger and Toftum (2002): on the warm side of the scale, unless the monitor of the zone applies the
                # expectancy factor to every PMV (apply_to_heating). The argument is not stored in the model: it is
                # read from the lines of the program monitor_ePMV_<zone> of accim.sim.pmv_index, which has an 'if'
                # (e*PMV if PMV > 0) without apply_to_heating and none with it, so this check depends on those lines
                # (finding E2 of section 3.5 of the review of accim 1.2.0)
                monitor = programs.get(f'MONITOR_{name}_{suffix}'.upper())
                both_sides = monitor is not None and not any(
                    line.lower().startswith('if') for line in _program_lines(monitor))
                check(found, np.where((pmv > 0) | both_sides, coefficient * pmv, pmv), suffix, 'Check3_ePMV',
                      'ePMV = e*PMV' if both_sides else 'ePMV = e*PMV if PMV > 0')
            elif pmv_index.key == 'pmv':
                check(found, pmv, suffix, 'Check3_PMV', 'PMV of the previous timestep')
            else:
                lines.append(f"  '{suffix}': no check for the index {name}.")

        # The PPD-weighted hours of Method C of CEN/TR 16798-2 (report_ppd_weighted_hours), of each zone with them
        for pmv_index, suffix in zones:
            if f'{PPD_WEIGHTED_HOURS_PROGRAM}{suffix}'.upper() not in programs:
                continue
            name = pmv_index.name
            found = outputs.get('EMS', f'PPD Weighted Hours_{suffix}')
            hours = outputs.get('EMS', f'Occupied hours_{suffix}')
            lower, upper = (outputs.get('EMS', f'{name} {side} Setpoint No Tolerance_{suffix}')
                            for side in ('Heating', 'Cooling'))
            pmv = pmv_of_zones.get(suffix)
            monitor = programs.get(f'MONITOR_{name}_{suffix}'.upper())
            # The monitor of the aPMV has an 'if' with adaptive_coefficient_by='pmv_sign' (that of the ePMV, without
            # apply_to_heating), as in the checks of the indices above
            monitor_if = monitor is not None and any(line.lower().startswith('if') for line in _program_lines(monitor))
            missing = ''
            if found is None:
                missing = f"the output 'PPD Weighted Hours_{suffix}' at timestep frequency"
            elif hours is None or lower is None or upper is None:
                missing = (f"the outputs 'Occupied hours_{suffix}' and '{name} Heating (and Cooling) Setpoint No "
                           f"Tolerance_{suffix}' at timestep frequency")
            elif pmv is None:
                missing = 'the PMV of the zone'
            elif pmv_index.key == 'apmv' and monitor_if:
                inputs = programs.get(f'SET_ZONE_INPUT_DATA_{suffix}'.upper())
                values = {}
                for line in (_program_lines(inputs) if inputs is not None else []):
                    target, _, value = line[len('set '):].partition('=')
                    values[target.strip().upper()] = value.strip()
                try:
                    coefficients = [float(values[f'ADAP_COEFF_{side}_{suffix}'.upper()])
                                    for side in ('HEATING', 'COOLING')]
                except (KeyError, ValueError):
                    missing = f'the adaptive coefficients of the program set_zone_input_data_{suffix}'
            elif pmv_index.coefficient_output and outputs.get(
                    'EMS', f'{pmv_index.coefficient_output}_{suffix}') is None:
                missing = f"the output '{pmv_index.coefficient_output}_{suffix}' at timestep frequency"
            if missing:
                lines.append(f"  '{suffix}' Check3_PpdWeightedHours: not checked, without {missing}.")
                continue
            if pmv_index.key == 'apmv':
                # The PMV whose aPMV = PMV/(1 + lambda*PMV) is the setpoint (Yao et al., 2009)
                if monitor_if:
                    heating, cooling = coefficients
                else:
                    heating = cooling = outputs.get('EMS', f'{pmv_index.coefficient_output}_{suffix}')
                lower, upper = lower / (1 - heating * lower), upper / (1 - cooling * upper)
            elif pmv_index.key == 'epmv':
                # ePMV = e*PMV on the warm side (on both sides with apply_to_heating, whose monitor has no 'if')
                factor = outputs.get('EMS', f'{pmv_index.coefficient_output}_{suffix}')
                lower, upper = (lower if monitor_if else lower / factor), upper / factor
            ppd = ppd_from_pmv(pmv)
            weight = (np.where(pmv >= upper, ppd / ppd_from_pmv(upper), 0.0)
                      + np.where(pmv < lower, ppd / ppd_from_pmv(lower), 0.0))
            check(found, np.where(np.isnan(pmv), np.nan, weight * hours), suffix, 'Check3_PpdWeightedHours',
                  'PPD(PMV)/PPD(PMV limit) times the occupied hours, Method C of CEN/TR 16798-2')

        # The metabolic correction of the ePMV, of each People object
        corrected_people = []
        for people in get_people_objects(building):
            names = metabolic_correction_names(str(people.Name))
            if names['program'].upper() in programs:
                corrected_people.append((people, names))
        if corrected_people:
            season = None
            inputs_program = programs.get('SET_COOLING_SEASON_INPUT_DATA')
            season_program = programs.get('SET_COOLING_SEASON')
            if inputs_program is not None and season_program is not None:
                # CoolingSeason of each day, with the programs of the model
                erl = ErlProgramSet({'inputs': _program_lines(inputs_program),
                                     'season': _program_lines(season_program)},
                                    global_variables=['CoolingSeason', 'CoolSeasonStart', 'CoolSeasonEnd'])
                erl.run('inputs')
                seasons = {}
                for day in np.unique(outputs.dates.dayofyear):
                    erl.set('DayOfYear', float(day))
                    erl.run('season')
                    seasons[day] = erl.get('CoolingSeason')
                season = np.array([seasons[day] for day in outputs.dates.dayofyear], dtype=float)
            suffixes_of_people: Dict[str, List[str]] = {}
            for target in resolve_targets(building):
                for people_name in target.people_names:
                    suffixes_of_people.setdefault(str(people_name).upper(), []).append(target.ems_suffix)
            for people, names in corrected_people:
                suffix = sanitize_ems_name(str(people.Name))
                factor = outputs.get('EMS', f'Metabolic Correction Factor_{suffix}')
                zone_suffixes = suffixes_of_people.get(str(people.Name).upper(), [])
                pmvs, missing = [], ''
                for zone_suffix in zone_suffixes:
                    pmv = pmv_of_zones.get(zone_suffix)
                    if pmv is None:
                        pmv, missing = zone_pmv(zone_suffix)
                    pmvs.append(pmv)
                weights = []
                if len(zone_suffixes) > 1:
                    for zone_suffix in zone_suffixes:
                        occupants, missing_occupants = sensor_values(f'People_Occupant_Count_{zone_suffix}')
                        weights.append(occupants)
                        missing = missing or missing_occupants
                if factor is None:
                    missing = f"the output 'Metabolic Correction Factor_{suffix}' at timestep frequency"
                elif season is None:
                    missing = 'the EMS programs set_cooling_season_input_data and set_cooling_season'
                elif not zone_suffixes:
                    missing = 'the zones of the People object'
                if missing or any(pmv is None for pmv in pmvs) or any(weight is None for weight in weights):
                    lines.append(f"  '{suffix}' Check3_MetabolicFactor: not checked, without "
                                 f"{missing or 'the PMV of its zones'}.")
                    continue
                mean = pmvs[0] if len(pmvs) == 1 else _weighted_mean(pmvs, weights)
                # Fanger and Toftum (2002): 6.7 % less for each unit of PMV, in the cooling season, between 0 and 3
                expected = 1 - EPMV_MET_REDUCTION_PER_PMV * np.clip(np.where(season == 1, mean, 0), 0,
                                                                    _MAX_METABOLIC_PMV)
                check(factor, expected, suffix, 'Check3_MetabolicFactor',
                      f'1 - {EPMV_MET_REDUCTION_PER_PMV}*PMV in the cooling season')
                base, missing = sensor_values(names['base'])
                corrected = outputs.get('EMS', f'Corrected Activity Level_{suffix}')
                if base is None or corrected is None:
                    missing = missing or f"the output 'Corrected Activity Level_{suffix}' at timestep frequency"
                    lines.append(f"  '{suffix}' Check3_CorrectedActivity: not checked, without {missing}.")
                    continue
                check(corrected, base * expected, suffix, 'Check3_CorrectedActivity',
                      f'activity level*(1 - {EPMV_MET_REDUCTION_PER_PMV}*PMV)')
    return rows, lines


def _timesteps_per_hour(building, outputs: Optional[_Outputs]) -> Optional[int]:
    """The timesteps per hour of a model: those of its Timestep object (6, the default of its field in the IDD, if it
    is empty), or else those of its outputs at timestep frequency (None if it has neither)."""
    timesteps = building.idfobjects['Timestep']
    if timesteps:
        value = str(timesteps[0].Number_of_Timesteps_per_Hour).strip()
        return int(float(value)) if value else 6
    if outputs is not None and len(outputs.datetimes) > 1:
        minutes = pd.Series(np.diff(outputs.datetimes.asi8)).mode().iloc[0] / 6e10
        if minutes > 0 and 60 % minutes == 0:
            return int(60 // minutes)
    return None


def _compute_setpoints_arguments(values: Mapping[str, Any]) -> Dict[str, Any]:
    """The arguments of :func:`accim.sim.preview.compute_setpoints` of a zone, from the values of the variables of its
    program SetInputData_<zone> (``accim.sim.ems.inputs.INPUT_VARIABLES``).

    :raises ValueError: If the tolerances of the cooling and heating setpoints are not opposite, as
        ``setpoint_tolerance`` sets them.
    """
    import inspect
    import math

    from accim.sim.ems.drift_limiter import INPUTS as DRIFT_INPUTS
    from accim.sim.ems.inputs import INPUT_VARIABLES
    from accim.utils.ems_code import get_setpoint_ems_code

    accepted = set(inspect.signature(get_setpoint_ems_code).parameters)
    arguments = {}
    for item in INPUT_VARIABLES:
        # setpoint_tolerance is AHSTtol, and ACSTtol its opposite; compute_setpoints cannot calculate the limiter of the
        # drift of the setpoints, whose targets are its setpoints
        if (item.argument in accepted and item.variable in values and item.variable != 'ACSTtol'
                and item.variable not in DRIFT_INPUTS):
            arguments[item.argument] = values[item.variable]
    if 'ACSTtol' in values and 'AHSTtol' in values and not math.isclose(values['ACSTtol'], -values['AHSTtol']):
        raise ValueError(f"ACSTtol ({values['ACSTtol']}) is not the opposite of AHSTtol ({values['AHSTtol']})")
    return arguments


def _setpoint_mismatches(building, data: Mapping[str, pd.DataFrame], epw: str,
                         tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 4 of :func:`verify_accim_simulation`: the setpoints of each zone of an output IDF of AddAccis against
    :func:`accim.sim.preview.compute_setpoints`, and the running mean outdoor temperatures of EnergyPlus against
    :func:`accim.sim.preview.energyplus_running_means`, in the last environment of the outputs (the run period).

    :param building: The model (eppy).
    :param data: The outputs of :func:`accim.utils.outputs.read_eso_using_readvarseso`, by frequency.
    :param epw: The weather file of the simulation.
    :param tolerance: The largest difference allowed.
    :return: The mismatches, and the lines of the summary.
    """
    from accim.sim.ems.custom_regimes import OUTPUT_PREFIX as REGIME_OUTPUT_PREFIX, PROGRAM_PREFIX, parse_regime_program
    from accim.sim.ems.hook_setpoints import PROGRAM_PREFIX as HOOK_PROGRAM_PREFIX, hook_zones
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.objects import ZONE_SETPOINT_OUTPUT_VARIABLES
    from accim.sim.ems.outdoor_metric import (OUTPUT_PREFIX, begins_with_weather_file, metric_code,
                                              metric_comfort_standards)
    from accim.sim.ems.standard_lines import WEATHER_FILE_METRICS
    from accim.sim.preview import SETPOINT_EMS_VARIABLES, compute_setpoints, energyplus_running_means

    zone_programs = input_programs(building)
    if not zone_programs:
        return [], ['  Not checked: the model has no programs SetInputData_<zone> (output IDFs of AddAccis).']
    columns_of_variables = {variable: column for column, variable in SETPOINT_EMS_VARIABLES.items()}
    outputs_of_columns = {columns_of_variables[variable]: output
                          for output, (variable, _) in ZONE_SETPOINT_OUTPUT_VARIABLES.items()
                          if variable in columns_of_variables}
    chosen = None
    for frequency in ('Timestep', 'Hourly'):
        frame = data.get(frequency)
        if frame is None or frame.empty:
            continue
        outputs = _Outputs(frame)
        if any(outputs.get('EMS', f'{output}_{zone}') is not None
               for zone in zone_programs for output in outputs_of_columns.values()):
            chosen = frequency, outputs
            break
    if chosen is None:
        return [], ['  Not checked: no setpoints of the zones (Comfort Temperature_<zone>...) at timestep or hourly '
                    'frequency.']
    frequency, outputs = chosen
    run_periods = building.idfobjects['RunPeriod']
    timesteps_per_hour = _timesteps_per_hour(building, outputs if frequency == 'Timestep' else None)
    if not run_periods or timesteps_per_hour is None:
        return [], ['  Not checked: the model has no RunPeriod, or no Timestep object.']
    month, day = int(run_periods[0].Begin_Month), int(run_periods[0].Begin_Day_of_Month)
    start_date = f'{day:02d}/{month:02d}'
    environment = np.cumsum(outputs.starts)
    rows = np.flatnonzero(environment == environment[-1])
    first = outputs.dates[rows[0]]
    if (first.month, first.day) != (month, day):
        return [], [f'  Not checked: the last environment of the outputs begins on {first.day:02d}/{first.month:02d}, '
                    f'not on the first day of the RunPeriod ({start_date}).']
    timestamps = [outputs.timestamps[row] for row in rows]
    datetimes = outputs.datetimes[rows]
    mismatches: List[dict] = []
    lines = [f'  {frequency} outputs from {start_date}, {timesteps_per_hour} timesteps per hour, weather file {epw}']
    stat_file = os.path.splitext(str(epw))[0] + '.stat'
    if os.path.isfile(stat_file):
        lines.append(f'  Note: {os.path.basename(stat_file)} is next to the weather file: if it was next to the weather '
                     f'file of the simulation, EnergyPlus took the running mean of ASHRAE 55 (PMOT) from its monthly '
                     f'means, which energyplus_running_means does not reproduce (Check4_PMOT, and the setpoints with '
                     f'PMOT).')
    # The running means, those of the first People object (all have the same)
    try:
        running_means = energyplus_running_means(epw, timesteps_per_hour, start_date).set_index('date')
    except ValueError as error:
        return [], lines + [f'  Not checked: {error}']
    for column, variable in _RUNNING_MEANS.items():
        keys = outputs.keys(variable)
        if not keys:
            continue
        expected = running_means[column].reindex(outputs.dates[rows]).to_numpy(dtype=float)
        new_rows, line = _mismatch_rows(timestamps, outputs.get(keys[0], variable)[rows], expected, keys[0],
                                        f'Check4_{column}', f'{column} of energyplus_running_means', tolerance)
        mismatches.extend(new_rows)
        lines.append(line)
    previews: Dict[Tuple, pd.DataFrame] = {}
    # The outdoor metric of the custom model begins with the values of the weather file of AddAccis, or with PMOT
    metric_start = 'epw' if begins_with_weather_file(building) else 'pmot'
    # The setpoints of the zones whose setpoints a hook of the API backend sets (accim.sim.ems.hook_setpoints) are not
    # those of compute_setpoints
    hooked = {zone.upper() for zone in hook_zones(building)}
    for zone, program in zone_programs.items():
        if zone.upper() in hooked:
            lines.append(f"  '{zone}': not checked (its setpoints are those of a hook of the API backend, "
                         f"{HOOK_PROGRAM_PREFIX}{zone}).")
            continue
        try:
            inputs = read_inputs(program)
            arguments = _compute_setpoints_arguments(inputs)
            # The limiter of the drift (accim.sim.ems.drift_limiter): its targets are the setpoints of the comfort
            # standard before the minimum and maximum of the setpoints
            drift = 'DriftMode' in inputs
            if drift:
                arguments.pop('heating_setpoint_minimum', None)
                arguments.pop('cooling_setpoint_maximum', None)
            # The regimes of the custom model of the zone (accim.sim.ems.custom_regimes); those of a comfort standard
            # with regimes are those of its definition, and the other comfort standards do not use them
            regime_program = building.getobject('EnergyManagementSystem:Program', f'{PROGRAM_PREFIX}{zone}')
            if regime_program is not None and arguments.get('comfort_standard') == 99:
                arguments['custom_regimes'] = parse_regime_program(regime_program.fieldvalues[2:], zone)
            key = tuple(sorted(arguments.items()))
            if key not in previews:
                previews[key] = compute_setpoints(epw, timesteps_per_hour=timesteps_per_hour, start_date=start_date,
                                                  frequency='timestep' if frequency == 'Timestep' else 'hourly',
                                                  outdoor_metric_start=metric_start, **arguments).set_index('datetime')
        except (ValueError, TypeError) as error:
            lines.append(f"  '{zone}': not checked ({error}).")
            continue
        preview = previews[key].reindex(datetimes)
        inside = preview['Tout'].notna().to_numpy()
        if drift:
            lines.append(f"  '{zone}': the limiter of the drift of the setpoints: its targets are checked, not the "
                         f"setpoints applied.")
            for column, target in (('AHSTnoTol', 'DriftTargetAHST'), ('ACSTnoTol', 'DriftTargetACST')):
                found = outputs.get('EMS', f'{target}_{zone}')
                if found is None:
                    continue
                expected = np.where(inside, preview[column].to_numpy(dtype=float), np.nan)
                new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, f'Check4_{target}',
                                                f'{column} of compute_setpoints', tolerance)
                mismatches.extend(new_rows)
                lines.append(line)
        for column, output in outputs_of_columns.items():
            if drift and column in ('ACST', 'AHST', 'ACSTnoTol', 'AHSTnoTol'):
                continue
            found = outputs.get('EMS', f'{output}_{zone}')
            if found is None:
                continue
            # A null value (the comfort temperature of static setpoints) is reported as 0
            expected = np.where(inside, np.nan_to_num(preview[column].to_numpy(dtype=float)), np.nan)
            new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, f'Check4_{column}',
                                            f'{output} of compute_setpoints', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
        # The outdoor metric that the EMS programs calculate (not with 'pmot', which is PMOT): that of the custom
        # model, that of a comfort standard defined by its data (accim.sim.standards), or that of JPN Aqilah 2025 with
        # the values of a weather file (accim.sim.ems.standard_lines.WEATHER_FILE_METRICS)
        found = outputs.get('EMS', f'{OUTPUT_PREFIX}{zone}')
        standard = arguments.get('comfort_standard')
        if found is not None and ((standard in metric_comfort_standards()
                                   and metric_code(arguments.get('custom_outdoor_metric', 0)) != 0)
                                  or (standard in WEATHER_FILE_METRICS and metric_start == 'epw')):
            expected = np.where(inside, preview['Tout_metric'].to_numpy(dtype=float), np.nan)
            new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, 'Check4_Tout_metric',
                                            f'{OUTPUT_PREFIX}{zone} of compute_setpoints', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
        # The regime of the custom model of each timestep
        found = outputs.get('EMS', f'{REGIME_OUTPUT_PREFIX}{zone}')
        if found is not None and 'custom_regime' in preview:
            expected = np.where(inside, preview['custom_regime'].to_numpy(dtype=float), np.nan)
            new_rows, line = _mismatch_rows(timestamps, found[rows], expected, zone, 'Check4_custom_regime',
                                            f'{REGIME_OUTPUT_PREFIX}{zone} of compute_setpoints', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
    return mismatches, lines


def _setpoint_limit_mismatches(building, data: Mapping[str, pd.DataFrame],
                               tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 5 of :func:`verify_accim_simulation`: the heating setpoint without the tolerance of each zone with a
    minimum (``AHSTmin`` in its program SetInputData_<zone>, :mod:`accim.sim.ems.setpoint_limits`) is not below it, and
    the cooling setpoint without the tolerance of each zone with a maximum (``ACSTmax``) is not above it; and the
    setpoints of its thermostats (with the tolerance) are not below the minimum plus the tolerance of the setpoints of
    the zone, nor above the maximum minus it (:func:`accim.sim.ems.setpoint_limits.thermostat_limits`: finding A19 of
    the self-audit of 2026-11-11, decided on 2026-11-12), in the outputs of the setpoints of the zone at timestep
    frequency, or else hourly (whose means keep the limits too).

    :return: The mismatches, and the lines of the summary (none if no zone has a minimum or a maximum).
    """
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.setpoint_limits import thermostat_limits, zone_limits

    limits = {zone: values for zone, values in zone_limits(building).items()
              if any(value is not None for value in values.values())}
    if not limits:
        return [], []
    # The limits of the thermostats: with the tolerance of the setpoints of each zone
    for zone, program in input_programs(building).items():
        if zone in limits:
            inputs = read_inputs(program)
            heating, cooling = thermostat_limits(limits[zone]['AHSTmin'], limits[zone]['ACSTmax'],
                                                 inputs.get('AHSTtol', 0), inputs.get('ACSTtol', 0))
            limits[zone] = dict(limits[zone], AHSTmin_thermostat=heating, ACSTmax_thermostat=cooling)
    outputs_of_limits = {
        'AHSTmin': ('AHSTmin_thermostat', 'Adaptive Heating Setpoint Temperature', np.maximum,
                    'minimum plus the tolerance'),
        'AHSTmin_noTol': ('AHSTmin', 'Adaptive Heating Setpoint Temperature_No Tolerance', np.maximum, 'minimum'),
        'ACSTmax': ('ACSTmax_thermostat', 'Adaptive Cooling Setpoint Temperature', np.minimum,
                    'maximum minus the tolerance'),
        'ACSTmax_noTol': ('ACSTmax', 'Adaptive Cooling Setpoint Temperature_No Tolerance', np.minimum, 'maximum'),
    }
    chosen = None
    for frequency in ('Timestep', 'Hourly'):
        frame = data.get(frequency)
        if frame is not None and not frame.empty:
            outputs = _Outputs(frame)
            if any(outputs.get('EMS', f'{output}_{zone}') is not None
                   for zone in limits for _, output, _, _ in outputs_of_limits.values()):
                chosen = frequency, outputs
                break
    if chosen is None:
        return [], ['  Not checked: no setpoints of the zones (Adaptive Heating Setpoint Temperature_<zone>...) at '
                    'timestep or hourly frequency.']
    frequency, outputs = chosen
    mismatches: List[dict] = []
    lines = [f'  {frequency} outputs']
    for zone, values in limits.items():
        for check, (variable, output, bound, side) in outputs_of_limits.items():
            limit = values.get(variable)
            found = outputs.get('EMS', f'{output}_{zone}')
            if limit is None or found is None:
                continue
            new_rows, line = _mismatch_rows(outputs.timestamps, found, bound(found, float(limit)), zone,
                                            f'Check5_{check}', f'{output}_{zone} within the {side} '
                                            f'{round(float(limit), 10):g}', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
    return mismatches, lines


def _long_term_mismatches(building, data: Mapping[str, pd.DataFrame],
                          tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 6 of :func:`verify_accim_simulation`: the long-term discomfort of each zone with the program
    CountLongTermDiscomfort_<zone> (:mod:`accim.sim.ems.long_term_discomfort`), from its occupied hours, its operative
    temperature of the previous timestep and its setpoints without the tolerance (or the constant limits of its
    program, ``long_term_range``), and that of the building, the sums of the zones, in the outputs at timestep
    frequency.

    :return: The mismatches, and the lines of the summary (none if the model has no long-term discomfort).
    """
    from accim.sim.ems.long_term_discomfort import (BUILDING, BUILDING_PROGRAM, OUTPUTS, PROGRAM_PREFIX, RUNNING_MEAN,
                                                    SeasonalRange, model_long_term_limits)

    zones = [str(p.Name)[len(PROGRAM_PREFIX):] for p in building.idfobjects['EnergyManagementSystem:Program']
             if str(p.Name).upper().startswith(PROGRAM_PREFIX.upper())
             and str(p.Name).upper() != BUILDING_PROGRAM.upper()]
    if not zones:
        return [], []
    frame = data.get('Timestep')
    if frame is None or frame.empty:
        return [], ['  Not checked: it needs the outputs at timestep frequency.']
    outputs = _Outputs(frame)
    sensors = {str(sensor.Name).upper(): (str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name),
                                          str(sensor.OutputVariable_or_OutputMeter_Name))
               for sensor in building.idfobjects['EnergyManagementSystem:Sensor']}
    mismatches: List[dict] = []
    lines = ['  Timestep outputs']
    totals: Dict[str, List[np.ndarray]] = {output: [] for output in OUTPUTS}
    constant_limits = model_long_term_limits(building)
    for zone in zones:
        hours = outputs.get('EMS', f'Occupied Hours_{zone}')
        limits = constant_limits.get(zone)
        if limits is None:
            upper = outputs.get('EMS', f'Adaptive Cooling Setpoint Temperature_No Tolerance_{zone}')
            lower = outputs.get('EMS', f'Adaptive Heating Setpoint Temperature_No Tolerance_{zone}')
        elif isinstance(limits, SeasonalRange):
            # The seasonal range (finding A15 of the self-audit of 2026-11-11): the limits of each timestep are those
            # of the running mean outdoor temperature that the EMS reads at its beginning, that of the previous one
            lines.append(f"  '{zone}': the seasonal range of long_term_range, {limits.heating[0]} to "
                         f"{limits.heating[1]} °C with a running mean outdoor temperature below "
                         f"{limits.heating_below} °C, {limits.cooling[0]} to {limits.cooling[1]} °C above "
                         f"{limits.cooling_above} °C, and {limits.heating[0]} to {limits.cooling[1]} °C between them.")
            sensor = sensors.get(RUNNING_MEAN.upper())
            running_mean = None if sensor is None else outputs.get(*sensor)
            if running_mean is None:
                lower = upper = None
            else:
                season = outputs.previous(running_mean)
                lower = np.where(season < limits.heating_below, limits.heating[0],
                                 np.where(season > limits.cooling_above, limits.cooling[0], limits.heating[0]))
                upper = np.where(season < limits.heating_below, limits.heating[1],
                                 np.where(season > limits.cooling_above, limits.cooling[1], limits.cooling[1]))
                # No limits in the first timestep of each environment, whose running mean is that of the warm-up days
                lower, upper = (np.where(np.isnan(season), np.nan, values) for values in (lower, upper))
        else:
            lower, upper = limits
            lines.append(f"  '{zone}': the constant range of long_term_range, {lower} to {upper} °C.")
        sensor = sensors.get(f'{zone}_OpT'.upper())
        temperature = None if sensor is None else outputs.get(*sensor)
        found = {output: outputs.get('EMS', f'{output}_{zone}') for output in OUTPUTS}
        for output, values in found.items():
            totals[output].append(values)
        if any(values is None for values in (hours, upper, lower, temperature)):
            lines.append(f"  '{zone}': not checked, without its occupied hours, setpoints without the tolerance (or "
                         f"the running mean outdoor temperature of its seasonal range) or operative temperature at "
                         f"timestep frequency.")
            continue
        previous = outputs.previous(temperature)
        occupied = hours > 0
        above = occupied & (previous > upper)
        below = occupied & (previous < lower)
        expected = {
            'Hours Above Upper Limit': np.where(above, hours, 0.0),
            'Hours Below Lower Limit': np.where(below, hours, 0.0),
            'Degree Hours Above Upper Limit': np.where(above, (previous - upper) * hours, 0.0),
            'Degree Hours Below Lower Limit': np.where(below, (lower - previous) * hours, 0.0),
        }
        for output, values in found.items():
            if values is None:
                lines.append(f"  '{zone}' Check6_{output}: not checked, without the output {output}_{zone}.")
                continue
            # The first timestep of each environment, whose previous temperature is that of the warm-up days
            reference = np.where(np.isnan(previous), np.nan, expected[output])
            new_rows, line = _mismatch_rows(outputs.timestamps, values, reference, zone, f'Check6_{output}',
                                            f'{output}_{zone} from the operative temperature of the previous '
                                            f'timestep', tolerance)
            mismatches.extend(new_rows)
            lines.append(line)
    for output, values in totals.items():
        found = outputs.get('EMS', f'{output}_{BUILDING}')
        if found is None or any(value is None for value in values):
            lines.append(f"  '{BUILDING}' Check6_{output}: not checked, without the outputs of the building and of "
                         f"all the zones.")
            continue
        new_rows, line = _mismatch_rows(outputs.timestamps, found, sum(values), BUILDING, f'Check6_{output}',
                                        f'{output}_{BUILDING}, the sum of the zones', tolerance)
        mismatches.extend(new_rows)
        lines.append(line)
    return mismatches, lines


# ─────────────────────────────────────────────────────────────────────────────
# CHECKS 1 AND 2: THE SETPOINTS WHILE THE SYSTEMS ARE ON, AND THE OPERATION OF THE WINDOWS
# ─────────────────────────────────────────────────────────────────────────────

#: The columns of the tables of :func:`verify_accim_simulation`
_MISMATCH_COLUMNS = ['timestep', 'zone_or_window', 'check', 'description', 'value_found', 'value_expected']
#: The program of a window or door in mixed mode is this prefix and its name in the EMS
_WINDOW_PROGRAM_PREFIX = 'SetWindowOperation_'
#: The EMS actuator of the opening of a window or door is its name in the EMS and this suffix
_WINDOW_ACTUATOR_SUFFIX = '_VentOpenFact'
#: Without EMS sensors of the coils of a zone (those of the VRF systems of accim), the outputs that tell whether its
#: system cools or heats: fragments of their variables, of the keys that have that of the zone, in this order
_COOLING_OUTPUTS = ('Cooling Coil Total Cooling Rate', 'VRF Heat Pump Cooling Electricity', 'Cooling Rate')
_HEATING_OUTPUTS = ('Heating Coil Heating Rate', 'VRF Heat Pump Heating Electricity', 'Heating Rate')
#: The outputs of the zone that the programs of the windows read and the standard outputs lack, and those of the site
#: that check 2 takes instead of them
_SITE_OUTPUTS = {'Zone Outdoor Air Drybulb Temperature': 'Site Outdoor Air Drybulb Temperature',
                 'Zone Outdoor Air Wind Speed': 'Site Wind Speed'}


def _ems_sensors(building) -> Dict[str, Tuple[str, str]]:
    """The output that each EMS sensor of a model reads (its key and its variable), by the name of the sensor in
    upper case."""
    return {str(sensor.Name).upper(): (str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name),
                                       str(sensor.OutputVariable_or_OutputMeter_Name))
            for sensor in building.idfobjects['EnergyManagementSystem:Sensor']}


def _window_names(building) -> List[str]:
    """The windows and doors of a model in mixed mode, by their names in the EMS: those of their programs
    SetWindowOperation_<window>."""
    prefix = _WINDOW_PROGRAM_PREFIX.upper()
    return [str(program.Name)[len(prefix):] for program in building.idfobjects['EnergyManagementSystem:Program']
            if str(program.Name).upper().startswith(prefix)]


def _zones_with_accis(building) -> Dict[str, str]:
    """The zones with the ACCIS, by their names in the EMS (those of their sensors <zone>_OpT, without those of the
    windows): the key of their outputs, which can have ':' (``Block1:Zone1`` for the zone ``Block1_Zone1``)."""
    windows = {name.upper() for name in _window_names(building)}
    return {str(sensor.Name)[:-4]: str(sensor.OutputVariable_or_OutputMeter_Index_Key_Name)
            for sensor in building.idfobjects['EnergyManagementSystem:Sensor']
            if str(sensor.Name).endswith('_OpT') and str(sensor.Name)[:-4].upper() not in windows}


def _setpoints_not_met(building, data: Mapping[str, pd.DataFrame],
                       tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 1 of :func:`verify_accim_simulation`: the timesteps in which the HVAC system of a zone cools and the
    operative temperature of the zone is above its cooling setpoint (that of its thermostat, the schedule
    ``ACST_Sch_<zone>``) by more than the tolerance, or heats and it is below its heating setpoint
    (``AHST_Sch_<zone>``) by more than it, in the outputs at timestep frequency, or else hourly.

    They are not mismatches of the EMS: the system is on and does not hold the setpoint (its capacity, or its
    response to a change of the setpoint or of the loads). Whether the system cools or heats is read in the outputs of
    the EMS sensors of its coils (``<zone>_CoolCoil`` and ``<zone>_HeatCoil``, those of the VRF systems of accim), or
    else in the first output whose key has that of the zone and whose variable has one of :data:`_COOLING_OUTPUTS`
    (:data:`_HEATING_OUTPUTS`).

    :param building: The model (eppy).
    :param data: The outputs of :func:`accim.utils.outputs.read_eso_using_readvarseso`, by frequency.
    :param tolerance: The difference between the operative temperature and the setpoint that is allowed (°C).
    :return: The rows of those timesteps (with the columns of the mismatches), and the lines of the summary (none if
        the model has no zones with the ACCIS).
    """
    zones = _zones_with_accis(building)
    if not zones:
        return [], []
    sensors = _ems_sensors(building)
    chosen = None
    for frequency in ('Timestep', 'Hourly'):
        frame = data.get(frequency)
        if frame is not None and not frame.empty:
            outputs = _Outputs(frame)
            if any(outputs.get(*sensors[f'{zone}_OPT'.upper()]) is not None for zone in zones):
                chosen = frequency, outputs
                break
    if chosen is None:
        return [], ['  Not checked: no operative temperature of the zones (Zone Operative Temperature) at timestep or '
                    'hourly frequency.']
    frequency, outputs = chosen
    unit = 'timesteps' if frequency == 'Timestep' else 'hours'
    names = {f'{column[0]}:{column[1]}': column for column in outputs.frame.columns}

    def rate(zone: str, key: str, sensor: str, fragments: Sequence[str]) -> Optional[np.ndarray]:
        """What the system of a zone cools or heats: the output of its EMS sensor, or else the first output whose key
        has that of the zone and whose variable has one of the fragments."""
        if f'{zone}_{sensor}'.upper() in sensors:
            values = outputs.get(*sensors[f'{zone}_{sensor}'.upper()])
            if values is not None:
                return values
        for fragment in fragments:
            name = _find_column(names, key, fragment)
            if name is not None:
                return outputs.frame[names[name]].to_numpy(dtype=float)
        return None

    rows: List[dict] = []
    lines = [f'  {frequency} outputs']
    for zone, key in zones.items():
        temperature = outputs.get(*sensors[f'{zone}_OPT'.upper()])
        cooling_setpoint = outputs.get(f'ACST_Sch_{zone}', 'Schedule Value')
        heating_setpoint = outputs.get(f'AHST_Sch_{zone}', 'Schedule Value')
        cooling, heating = rate(zone, key, 'CoolCoil', _COOLING_OUTPUTS), rate(zone, key, 'HeatCoil', _HEATING_OUTPUTS)
        missing = []
        if temperature is None:
            missing.append(f"the operative temperature of '{key}'")
        if cooling_setpoint is None or heating_setpoint is None:
            missing.append(f'the setpoints of its thermostat (the Schedule Value of ACST_Sch_{zone} and '
                           f'AHST_Sch_{zone})')
        if cooling is None and heating is None:
            missing.append('an output of what its HVAC system cools or heats (the rates of its coils)')
        if missing:
            lines.append(f"  '{zone}': not checked, without {' and '.join(missing)}.")
            continue
        found: List[Tuple[int, int, dict]] = []
        for order, (check, active, setpoint, word, name, above) in enumerate((
                ('Check1_Cooling', cooling, cooling_setpoint, 'Cooling', 'ACST', True),
                ('Check1_Heating', heating, heating_setpoint, 'Heating', 'AHST', False))):
            if active is None:
                lines.append(f"  '{zone}' {check}: not checked, without an output of what its HVAC system "
                             f"{'cools' if above else 'heats'}.")
                continue
            with np.errstate(invalid='ignore'):
                beyond = (temperature > setpoint + tolerance) if above else (temperature < setpoint - tolerance)
                positions = np.flatnonzero((active > 0) & beyond)
            for position in positions:
                limit = setpoint[position] + tolerance if above else setpoint[position] - tolerance
                found.append((int(position), order, {
                    'timestep': outputs.timestamps[position],
                    'zone_or_window': zone,
                    'check': check,
                    'description': (f"{word} active (rate={active[position]:.2f} W) but OpT "
                                    f"({temperature[position]:.2f} °C) {'>' if above else '<'} {name} "
                                    f"({setpoint[position]:.2f} °C) {'+' if above else '-'} tolerance "
                                    f"({tolerance} °C)"),
                    'value_found': round(float(temperature[position]), 4),
                    'value_expected': f"{'<=' if above else '>='} {limit:.2f} °C",
                }))
            state = 'cooled and above its cooling' if above else 'heated and below its heating'
            lines.append(f"  '{zone}' {check} ({state} setpoint by more than {tolerance:g} °C): {len(positions)} of "
                         f"{len(temperature)} {unit}")
        rows.extend(row for _, _, row in sorted(found, key=lambda item: item[:2]))
    return rows, lines


def _window_opening(hvac_mode: int, vent_ctrl: int, values: Mapping[str, np.ndarray]) -> Optional[np.ndarray]:
    """The opening factor that the programs SetMyVOF_<window> and SetWindowOperation_<window> of a window give in
    each timestep (:data:`accim.sim.ems.program_lines.SET_MY_VOF` and ``SET_WINDOW_OPERATION``), from the values that
    they read: ``operative`` (the operative temperature of the zone, of the previous timestep), ``hvac_off`` (whether
    its HVAC system neither heated nor cooled in the previous timestep), ``outdoor`` and ``wind`` (the outdoor air
    temperature and the wind speed of the zone), ``occupants``, ``cooling_setpoint`` (roundedACST),
    ``cooling_setpoint_no_tolerance`` (ACSTnoTol), ``ventilation_setpoint`` (VST), ``minimum_outdoor`` (MinOutTemp),
    ``design_day`` and the inputs of the zone ``MaxWindSpeed``, ``MultiplierVOF``, ``MinTempDiffVOF`` and
    ``MaxTempDiffVOF``. None with a ventilation control that the program of the HVAC mode does not have.
    """
    if (hvac_mode, vent_ctrl) not in ((0, vent_ctrl), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)):
        return None
    operative, outdoor, wind = values['operative'], values['outdoor'], values['wind']
    with np.errstate(invalid='ignore', divide='ignore'):
        # SetMyVOF_<window>: the opening factor by the difference between the indoor and outdoor temperatures
        slope = (1 - values['MultiplierVOF']) / (values['MinTempDiffVOF'] - values['MaxTempDiffVOF'])
        difference = np.where(outdoor > 0, operative - outdoor, operative + outdoor)
        my_vof = np.where(outdoor > operative, 0.0,
                          np.where(difference > values['MaxTempDiffVOF'], values['MultiplierVOF'],
                                   np.where(difference < values['MinTempDiffVOF'], 1.0,
                                            slope * difference - slope * values['MinTempDiffVOF'] + 1)))
        # SetWindowOperation_<window>
        calm = wind <= values['MaxWindSpeed']
        if hvac_mode == 0:
            opening = np.zeros(len(operative))
        elif hvac_mode == 1:
            threshold = values['ventilation_setpoint'] if vent_ctrl == 0 else values['cooling_setpoint_no_tolerance']
            ventilates = ((outdoor < operative) & (outdoor > values['minimum_outdoor']) & (operative > threshold)
                          & calm)
            opening = np.where(ventilates, my_vof, 0.0)
        else:
            base = ((operative < values['cooling_setpoint']) & calm & (outdoor > values['minimum_outdoor'])
                    & (outdoor < operative) & (values['occupants'] > 0))
            ventilates = values['hvac_off'] & base & (operative > values['ventilation_setpoint'])
            opening = np.where(ventilates, 1.0 if vent_ctrl in (0, 1) else my_vof, 0.0)
        opening = np.where(values['design_day'] == 1, 0.0, opening)
    # Not checked without the values of the previous timestep (the first timestep of each environment)
    return np.where(np.isnan(operative), np.nan, opening)


def _window_mismatches(building, data: Mapping[str, pd.DataFrame], tolerance: float) -> Tuple[List[dict], List[str]]:
    """Check 2 of :func:`verify_accim_simulation`: the opening factor of each window or door in mixed mode is that of
    its EMS programs, SetMyVOF_<window> and SetWindowOperation_<window>, with the values that they read at the
    beginning of each timestep (measured with simulations of the sample model, 2026-11-13): the operative temperature
    of its zone and what its HVAC system cooled and heated, of the previous timestep; and the outdoor air temperature
    and the wind speed of its zone, its occupants, and the cooling setpoint, the ventilation setpoint and the minimum
    outdoor temperature that the EMS calculates for its zone (their outputs), of the timestep itself. In the outputs
    at timestep frequency; the first timestep of each environment is not checked.

    The outdoor air temperature and the wind speed that the programs read are those of the zone (*Zone Outdoor Air
    Drybulb Temperature* and *Zone Outdoor Air Wind Speed*, at the height of its centroid), which the standard outputs
    lack (``output_type='detailed'`` adds them): without them, those of the site are taken (:data:`_SITE_OUTPUTS`) and
    the summary says so, since a mismatch may then be the difference between them (in the sample model, 0.0016 K and
    a wind speed of 49 % of that of the site).

    :return: The mismatches, and the lines of the summary (none if the model has no windows in mixed mode).
    """
    from accim.sim.ems.inputs import input_programs, read_inputs

    windows = _window_names(building)
    if not windows:
        return [], []
    frame = data.get('Timestep')
    if frame is None or frame.empty:
        return [], ['  Not checked: it needs the outputs at timestep frequency, since the EMS opens and closes each '
                    'window with the operative temperature and the HVAC system of the previous timestep.']
    outputs = _Outputs(frame)
    sensors = _ems_sensors(building)
    zone_of_key = {key.upper(): zone for zone, key in _zones_with_accis(building).items()}
    programs = input_programs(building)
    actuators = {str(actuator.Name).upper(): actuator
                 for actuator in building.idfobjects['EnergyManagementSystem:Actuator']}
    try:
        model_inputs = get_accim_args_flattened(building)
    except Exception:  # noqa: BLE001 (a model without the arguments of the ACCIS)
        model_inputs = {}
    mismatches: List[dict] = []
    lines = ['  Timestep outputs']
    site_outputs = False

    def sensor_values(name: str) -> Tuple[Optional[np.ndarray], str]:
        """The values of the output that an EMS sensor reads, and what is missing if they are not in the outputs."""
        if name.upper() not in sensors:
            return None, f'the EMS sensor {name}'
        key, variable = sensors[name.upper()]
        values = outputs.get(key, variable)
        return values, ('' if values is not None else f"the output '{variable}' of '{key}'")

    def zone_output(output: str, zone: str) -> Tuple[Optional[np.ndarray], str]:
        """An output of the EMS of a zone (or that of the whole model, in the models of earlier versions of accim)."""
        values = outputs.get('EMS', f'{output}_{zone}')
        if values is None:
            values = outputs.get('EMS', output)
        return values, ('' if values is not None else f"the output '{output}_{zone}'")

    for window in windows:
        temperature, missing = sensor_values(f'{window}_OpT')
        zone = None if temperature is None else zone_of_key.get(sensors[f'{window}_OPT'.upper()][0].upper())
        if temperature is not None and zone is None:
            missing = 'the ACCIS in its zone'
        actuator = actuators.get(f'{window}{_WINDOW_ACTUATOR_SUFFIX}'.upper())
        if not missing and actuator is None:
            missing = f'the EMS actuator {window}{_WINDOW_ACTUATOR_SUFFIX}'
        if missing:
            lines.append(f"  '{window}': not checked, without {missing}.")
            continue
        # The opening factor that EnergyPlus reports: that of the surface of the window (AirflowNetwork), or the
        # value of its ventilation schedule
        component = str(actuator.Actuated_Component_Unique_Name)
        scheduled = 'SCHEDULE' in str(actuator.Actuated_Component_Type).upper()
        variable = 'Schedule Value' if scheduled else 'AFN Surface Venting Window or Door Opening Factor'
        found = outputs.get(component, variable)
        if found is None:
            lines.append(f"  '{window}': not checked, without the output '{variable}' of '{component}'.")
            continue
        # The inputs of its zone (those of the model, in the models of earlier versions of accim)
        inputs = dict(model_inputs)
        if zone in programs:
            inputs.update(read_inputs(programs[zone]))
        names = ('HVACmode', 'VentCtrl', 'MaxWindSpeed', 'MultiplierVOF', 'MinTempDiffVOF', 'MaxTempDiffVOF')
        without = [name for name in names if not isinstance(inputs.get(name), (int, float))]
        if without:
            lines.append(f"  '{window}': not checked, without the inputs {', '.join(without)} of its zone.")
            continue
        values: Dict[str, Any] = {name: float(inputs[name]) for name in names[2:]}
        hvac_mode, vent_ctrl = int(inputs['HVACmode']), int(inputs['VentCtrl'])
        # What the programs read, of the previous timestep: the operative temperature of the zone, and what its HVAC
        # system cooled and heated (the VRF systems of accim) or the load that its thermostat asked for (the existing
        # HVAC systems)
        values['operative'] = outputs.previous(temperature)
        absent = []
        if hvac_mode != 2:
            # Only the program of HVACmode 2 reads whether the HVAC system is off
            values['hvac_off'] = np.ones(len(found), dtype=bool)
        elif f'{window}_CoolCoil'.upper() in sensors and f'{window}_HeatCoil'.upper() in sensors:
            cooling, missing_cooling = sensor_values(f'{window}_CoolCoil')
            heating, missing_heating = sensor_values(f'{window}_HeatCoil')
            absent += [text for text in (missing_cooling, missing_heating) if text]
            if not absent:
                values['hvac_off'] = (outputs.previous(cooling) == 0) & (outputs.previous(heating) == 0)
        elif f'{window}_LoadToSetpoint'.upper() in sensors:
            load, missing_load = sensor_values(f'{window}_LoadToSetpoint')
            absent += [missing_load] if missing_load else []
            if not absent:
                values['hvac_off'] = outputs.previous(load) == 0
        else:
            absent.append(f'the EMS sensors of its HVAC system ({window}_CoolCoil and {window}_HeatCoil, or '
                          f'{window}_LoadToSetpoint)')
        # Of the timestep itself: the outdoor air temperature and the wind speed of the zone (or of the site), the
        # occupants, and the setpoints that the EMS calculates for the zone
        from_site = []
        for name, sensor in (('outdoor', f'{window}_OutT'), ('wind', f'{window}_WindSpeed')):
            found_values, missing_output = sensor_values(sensor)
            if found_values is None and sensor.upper() in sensors and sensors[sensor.upper()][1] in _SITE_OUTPUTS:
                site = _SITE_OUTPUTS[sensors[sensor.upper()][1]]
                found_values = outputs.get('Environment', site)
                if found_values is not None:
                    from_site.append(site)
                    missing_output = ''
                else:
                    missing_output += f" (or '{site}')"
            values[name] = found_values
            absent += [missing_output] if missing_output else []
        occupants, missing_occupants = zone_output('People Occupant Count', zone)
        if occupants is None:
            occupants, missing_occupants = sensor_values(f'{window}_Occ_count')
        values['occupants'] = occupants
        absent += [missing_occupants] if missing_occupants else []
        for name, output in (('cooling_setpoint', 'Adaptive Cooling Setpoint Temperature'),
                             ('cooling_setpoint_no_tolerance', 'Adaptive Cooling Setpoint Temperature_No Tolerance'),
                             ('ventilation_setpoint', 'Ventilation Setpoint Temperature'),
                             ('minimum_outdoor', 'Minimum Outdoor Temperature for ventilation')):
            values[name], missing_output = zone_output(output, zone)
            absent += [missing_output] if missing_output else []
        # The design days, on which the windows stay closed: none in the run period, without the output of their
        # schedule
        design_day = sensor_values('DesignDay')[0]
        values['design_day'] = np.zeros(len(found)) if design_day is None else design_day
        if absent:
            lines.append(f"  '{window}': not checked, without {', '.join(absent)} at timestep frequency.")
            continue
        expected = _window_opening(hvac_mode, vent_ctrl, values)
        if expected is None:
            lines.append(f"  '{window}': not checked, with HVACmode {hvac_mode} and VentCtrl {vent_ctrl}.")
            continue
        site_outputs = site_outputs or bool(from_site)
        description = 'its opening factor against that of its EMS programs'
        difference = np.abs(found - expected)
        checked = np.isfinite(difference)
        bad = np.flatnonzero(checked & (np.where(checked, difference, 0) > tolerance))
        for position in bad:
            state = (f"operative temperature of the previous timestep {values['operative'][position]:.2f} °C, cooling "
                     f"setpoint {values['cooling_setpoint'][position]:.2f} °C, ventilation setpoint "
                     f"{values['ventilation_setpoint'][position]:.2f} °C, outdoor air {values['outdoor'][position]:.2f}"
                     f" °C (minimum {values['minimum_outdoor'][position]:.2f} °C), wind speed "
                     f"{values['wind'][position]:.2f} m/s (maximum {values['MaxWindSpeed']:g} m/s), occupants "
                     f"{values['occupants'][position]:g}, HVAC system "
                     f"{'off' if values['hvac_off'][position] else 'on'} in the previous timestep")
            mismatches.append({
                'timestep': outputs.timestamps[position],
                'zone_or_window': window,
                'check': 'Check2_OpeningFactor',
                'description': (f'The opening factor of {window} is {found[position]:.6f} instead of '
                                f'{expected[position]:.6f}, that of its EMS programs ({state})'),
                'value_found': round(float(found[position]), 6),
                'value_expected': round(float(expected[position]), 6),
            })
        lines.append(f"  '{window}' Check2_OpeningFactor ({description}): {len(bad)} mismatch(es) in "
                     f"{int(checked.sum())} timesteps; open in {int((found > 0).sum())}")
    if site_outputs:
        lines.insert(1, "  Note: the outputs lack the outdoor air temperature and the wind speed of the zones of the "
                        "windows, which their programs read ('Zone Outdoor Air Drybulb Temperature' and 'Zone Outdoor "
                        "Air Wind Speed', which output_type='detailed' adds): those of the site are taken instead, so "
                        "a mismatch may be the difference between them.")
    return mismatches, lines


class AccimSimulationVerifier:
    """
    Checks 1 and 2 of :func:`verify_accim_simulation` as an object: the timesteps in which the HVAC system of a zone
    is on and does not hold its setpoint, and the operation of the windows in mixed mode.

    Since accim 1.2.0 this class runs the code of the function (before, it had its own checks 1 and 2, with other
    criteria and identifiers, and it raised a ``ValueError`` with the zones whose names have ':').
    :func:`verify_accim_simulation` also has checks 3 to 6, of the values that the EMS calculates.

    Parameters
    ----------
    eso_file_path : str
        The ESO file of the simulation. If the CSV file of ``ReadVarsESO`` is next to it (the same name, with
        ``.csv``), it is read instead, without running ``ReadVarsESO``.
    idf_path : str
        The IDF that was simulated.
    eplus_install_dir : Optional[str], default None
        The folder of EnergyPlus, for ``ReadVarsESO`` (when the ESO file is read).
    tolerance : float, default 0.1
        The difference between the operative temperature of a zone and its setpoint that check 1 allows (°C).
    calculation_tolerance : float, default 0.001
        The largest difference between the opening factor of a window and that of its EMS programs (check 2).

    Attributes
    ----------
    summary : str
        The lines of the summary of both checks.
    violations : Dict[str, pd.DataFrame]
        ``'setpoint'``: the timesteps of check 1 (``Check1_Cooling`` and ``Check1_Heating``): the system of a zone is
        on and the zone is beyond its setpoint by more than ``tolerance``. They are not mismatches of the EMS: they
        tell of the capacity or the response of the HVAC system. ``'window'``: the mismatches of check 2
        (``Check2_OpeningFactor``): the opening factor of a window is not that of its EMS programs. Their columns are
        ``['timestep', 'zone_or_window', 'check', 'description', 'value_found', 'value_expected']``.
    summary_table_setpoint : pd.DataFrame
        The number of rows of ``violations['setpoint']`` of each zone and check, with the columns
        ``['zone_or_window', 'check', 'count']``.
    summary_table_window : pd.DataFrame
        The number of rows of ``violations['window']`` of each window and check.

    Notes
    -----
    Check 2 needs the outputs at timestep frequency (the EMS opens and closes each window with the operative
    temperature and the HVAC system of the previous timestep), and the outdoor air temperature and the wind speed of
    the zones to be exact (``output_type='detailed'`` adds them): see :func:`verify_accim_simulation`.
    """
    def __init__(
            self,
            eso_file_path: str,
            idf_path: str,
            eplus_install_dir: Optional[str] = None,
            tolerance: float = 0.1,
            calculation_tolerance: float = 1e-3,
    ):
        self.eso_file_path = eso_file_path
        self.idf_path = idf_path
        self.eplus_install_dir = eplus_install_dir
        self.tolerance = tolerance
        self.calculation_tolerance = calculation_tolerance

        self.summary: str = ""
        self.violations: Dict[str, pd.DataFrame] = {
            "setpoint": pd.DataFrame(columns=_MISMATCH_COLUMNS),
            "window": pd.DataFrame(columns=_MISMATCH_COLUMNS),
        }
        self.summary_table_setpoint: pd.DataFrame = pd.DataFrame(columns=['zone_or_window', 'check', 'count'])
        self.summary_table_window: pd.DataFrame = pd.DataFrame(columns=['zone_or_window', 'check', 'count'])

        self._evaluate()

    def _evaluate(self):
        from accim.sim.accis import load_idf

        # The CSV file of ReadVarsESO next to the ESO file, if any: the same outputs, without running ReadVarsESO
        csv_path = os.path.splitext(self.eso_file_path)[0] + '.csv'
        if os.path.exists(csv_path):
            print(f"Reading CSV file directly: {csv_path}")
            data = read_csv_outputs(csv_path, only_run_period=True)['data']
        else:
            print(f"Reading ESO file: {self.eso_file_path}")
            data = read_eso_using_readvarseso(
                eso_file_path=self.eso_file_path,
                eplus_install_dir=self.eplus_install_dir,
                only_run_period=True,
                cleanup=False,
            )['data']
        if all(frame.empty for frame in data.values()):
            warnings.warn("No simulation output data found in the ESO file.")
            self.summary = "Verification failed: No simulation output data found."
            return

        print(f"Reading IDF: {self.idf_path}")
        building = load_idf(self.idf_path)
        not_met, setpoint_lines = _setpoints_not_met(building, data, self.tolerance)
        mismatches, window_lines = _window_mismatches(building, data, self.calculation_tolerance)

        self.violations["setpoint"] = pd.DataFrame(not_met, columns=_MISMATCH_COLUMNS)
        self.violations["window"] = pd.DataFrame(mismatches, columns=_MISMATCH_COLUMNS)
        for name in ('setpoint', 'window'):
            rows = self.violations[name]
            if len(rows):
                table = rows.groupby(['zone_or_window', 'check']).size().rename('count').reset_index()
                setattr(self, f'summary_table_{name}', table)

        lines: List[str] = []
        if setpoint_lines:
            lines += ['[Check 1: The setpoints of the zones while their HVAC systems are on]', *setpoint_lines,
                      f'{len(not_met)} timestep(s) with the HVAC system of a zone on and the zone beyond its setpoint '
                      f'(they are not mismatches of the EMS).']
        if window_lines:
            lines += ['[Check 2: The operation of the windows]', *window_lines,
                      f'{len(mismatches)} mismatch(es) of the operation of the windows.']
        self.summary = '\n'.join(lines)
        print(self.summary)
