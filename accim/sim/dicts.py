# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Dictionaries to be used in multiple files"""



EMSOutputVariableZone_dict = {
    'Comfortable Hours_No Applicability': ['ComfHoursNoApp', 'H', 'Summed'],
    'Comfortable Hours_Applicability': ['ComfHours', 'H', 'Summed'],
    'Occupied Comfortable Hours_No Applicability': ['OccComfHoursNoApp', 'H', 'Summed'],
    'Occupied Discomfortable Hours_No Applicability': ['OccDiscomfHoursNoApp', 'H', 'Summed'],
    'Occupied Hours': ['OccHours', 'H', 'Summed'],
    'Discomfortable Applicable Hot Hours': ['DiscomfAppHotHours', 'H', 'Summed'],
    'Discomfortable Applicable Cold Hours': ['DiscomfAppColdHours', 'H', 'Summed'],
    'Discomfortable Non Applicable Hot Hours': ['DiscomfNonAppHotHours', 'H', 'Summed'],
    'Discomfortable Non Applicable Cold Hours': ['DiscomfNonAppColdHours', 'H', 'Summed'],
    'Zone Floor Area': ['ZoneFloorArea', 'm2', 'Averaged'],
    'Zone Air Volume': ['ZoneAirVolume', 'm3', 'Averaged'],
    'People Occupant Count': ['Occ_count', '', 'Summed'],
}

