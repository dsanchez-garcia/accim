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
"""

from typing import Tuple

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
    'SET_MY_VOF',
    'SET_WINDOW_OPERATION',
    'APPLY_AST_AIR_CONDITIONED',
    'format_lines',
]


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.strip('\n').split('\n'))


def format_lines(lines: Tuple[str, ...], zone: str = None, window: str = None) -> list:
    """The lines of a program of a zone or window, with its name."""
    result = list(lines)
    if zone is not None:
        result = [line.replace('{zone}', zone) for line in result]
    if window is not None:
        result = [line.replace('{window}', window) for line in result]
    return result


#: Comfort (neutral) temperature of each comfort standard.
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
set ComfTemp = PMOT*0.39+18.42
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

#: Comfortable and discomfortable hours of a zone, within the applicability limits: in each timestep, one of the five
#: counters is the length of the timestep and the others are 0. The operative temperature is compared with the
#: setpoints without tolerance of the timestep (RunACCIS_<zone> runs it after SetASTnoTol).
COUNT_HOURS = _lines("""
if (ComfStand == 1) || (ComfStand == 10)
if (RMOT >= AHSTall) && (RMOT <= ACSTaul)
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
elseif (RMOT > ACSTaul)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 1*ZoneTimeStep
set DiscomfNonAppColdHours_{zone} = 0
elseif (RMOT < AHSTall)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 0
set DiscomfNonAppColdHours_{zone} = 1*ZoneTimeStep
endif
else
if (PMOT >= AHSTall) && (PMOT <= ACSTaul)
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
elseif (PMOT > ACSTaul)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 1*ZoneTimeStep
set DiscomfNonAppColdHours_{zone} = 0
elseif (PMOT < AHSTall)
set ComfHours_{zone} = 0
set DiscomfAppHotHours_{zone} = 0
set DiscomfAppColdHours_{zone} = 0
set DiscomfNonAppHotHours_{zone} = 0
set DiscomfNonAppColdHours_{zone} = 1*ZoneTimeStep
endif
endif
""")

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
elseif ComfStand == 1 || ComfStand == 10
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

#: Setpoints and ventilation of a zone in mixed mode.
APPLY_AST_MIXED_MODE = _lines("""
if {zone}_CoolCoil==0
if {zone}_HeatCoil==0
set NoH_NoC_reqs = 1
else
set NoH_NoC_reqs = 0
endif
else
set NoH_NoC_reqs = 0
endif
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
""")

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

#: Opening of a window or door in mixed mode.
SET_WINDOW_OPERATION = _lines("""
if {window}_CoolCoil==0
if {window}_HeatCoil==0
set NoH_NoC_reqs = 1
else
set NoH_NoC_reqs = 0
endif
else
set NoH_NoC_reqs = 0
endif
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
""")

#: Setpoints of a zone with full air-conditioning.
APPLY_AST_AIR_CONDITIONED = _lines("""
set ACST_Act_{zone} = ACST
set AHST_Act_{zone} = AHST
""")
