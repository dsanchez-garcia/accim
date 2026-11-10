# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The Schedule:File objects of hourly values that accim writes from a weather file (task H2 of the review of accim
1.2.0: the mean of the maximum and minimum of each day, T0 of the outdoor metric 'te_ref_nl' of the custom model;
task H6: the clothing insulation as a function of the outdoor temperature).

EnergyPlus reads the values of a Schedule:File object from a text file with one value per hour of the year, from the
hour 1 of 1 January: 8760 hours, or 8784 with 29 February (Input Output Reference 25.2, 1.8.13; the fields Rows to Skip
at Top and Number of Hours of Data). accim writes a CSV file with a header row and one column, in the folder of the
model (that of its file, or the current folder for a model in memory, such as those of
:class:`accim.sim.accis.AddAccis`, which writes its output IDFs there), and the Schedule:File object gets the absolute
path of the file, as the Input Output Reference recommends ("The field should include a full path with file name, for
best results"; it also says that the field must have 100 characters or fewer, but EnergyPlus 25.1 read a path of 139
characters in the tests of accim), so the model can be saved in another folder while the CSV file stays where it is.
The schedules have no interpolation (Interpolate to Timestep No, 60 minutes per item), the schedule type limits
:data:`SCHEDULE_TYPE_LIMITS` (without it, EnergyPlus warns that the schedule is not validated) and, in the IDDs that
have the field (not those of EnergyPlus 9.4 and 9.6), Adjust Schedule for Daylight Savings No, so that their values
are those of the hours of the weather file (in standard time).
"""

import os
from pathlib import Path
from typing import Any, Optional, Sequence, Union

__all__ = ['SCHEDULE_TYPE_LIMITS', 'model_folder', 'remove_schedule_file', 'schedule_file_path', 'write_schedule_file']

#: The schedule type limits of the Schedule:File objects of accim: a ScheduleTypeLimits object with only a name, which
#: does not limit the values (the models of DesignBuilder have it; accim adds it to the others)
SCHEDULE_TYPE_LIMITS = 'Any Number'
#: The numbers of hours of a Schedule:File object (Energy+.idd: "should be either 8760 or 8784")
_HOURS = (8760, 8784)


def model_folder(idf: Any) -> Path:
    """The folder of the file of a model (eppy), or the current folder if the model is in memory."""
    name = getattr(idf, 'idfname', None)
    if isinstance(name, (str, os.PathLike)) and str(name):
        return Path(os.path.abspath(os.fspath(name))).parent
    return Path(os.getcwd())


def write_schedule_file(idf: Any, name: str, values: Sequence[float], file_name: str,
                        folder: Union[str, os.PathLike, None] = None) -> Path:
    """Write the hourly values of a schedule in a CSV file and give the model a Schedule:File object with that name
    that reads them (or update the one it has).

    :param idf: The model (eppy), changed in place.
    :param name: The name of the Schedule:File object.
    :param values: The value of each hour of the year, from the hour 1 of 1 January: 8760 values, or 8784 with 29
        February.
    :param file_name: The name of the CSV file.
    :param folder: The folder of the CSV file (made if it does not exist); None for that of the model
        (:func:`model_folder`).
    :return: The absolute path of the CSV file (unchanged if it already had these values).
    :raises ValueError: If the number of values is not 8760 or 8784.
    """
    values = [float(value) for value in values]
    if len(values) not in _HOURS:
        raise ValueError(f'A Schedule:File object needs 8760 or 8784 hourly values (Number of Hours of Data), not '
                         f'{len(values)}.')
    path = Path(os.path.abspath(folder if folder is not None else model_folder(idf))) / file_name
    # The values as repr writes them, so that EnergyPlus reads the same floats
    text = f'{name}\n' + '\n'.join(repr(value) for value in values) + '\n'
    if not path.is_file() or path.read_text(encoding='utf-8') != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    if idf.getobject('ScheduleTypeLimits', SCHEDULE_TYPE_LIMITS) is None:
        idf.newidfobject('ScheduleTypeLimits', Name=SCHEDULE_TYPE_LIMITS)
    schedule = idf.getobject('Schedule:File', name)
    if schedule is None:
        schedule = idf.newidfobject('Schedule:File', Name=name)
    fields = dict(Schedule_Type_Limits_Name=SCHEDULE_TYPE_LIMITS, File_Name=str(path), Column_Number=1,
                  Rows_to_Skip_at_Top=1, Number_of_Hours_of_Data=len(values), Column_Separator='Comma',
                  Interpolate_to_Timestep='No', Minutes_per_Item=60)
    if 'Adjust_Schedule_for_Daylight_Savings' in schedule.fieldnames:
        fields['Adjust_Schedule_for_Daylight_Savings'] = 'No'
    for field, value in fields.items():
        setattr(schedule, field, value)
    return path


def schedule_file_path(idf: Any, name: str) -> Optional[str]:
    """The path of the file of a Schedule:File object of a model, or None if the model has not the object."""
    schedule = idf.getobject('Schedule:File', name)
    return None if schedule is None else str(schedule.File_Name)


def remove_schedule_file(idf: Any, name: str) -> None:
    """Remove a Schedule:File object from a model (the CSV file stays: other models can read it)."""
    schedule = idf.getobject('Schedule:File', name)
    if schedule is not None:
        idf.removeidfobject(schedule)
