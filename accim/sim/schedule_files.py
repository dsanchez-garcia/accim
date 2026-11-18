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
To move a model with its files, to another folder or computer, :func:`relative_schedule_files` gives the objects the
paths of their files relative to the folder of the model (since accim 1.2.0): EnergyPlus looks for the file of a
relative path in the current folder and then in the folder of the IDF file (measured with EnergyPlus 25.1 on
2026-11-18: a model moved with its file found it from another current folder, and a file with the same path in the
current folder was read instead of the one next to the IDF file). The runners of accim simulate copies of the models
in other folders (``run_ep``, with both backends, and the parametric module), where EnergyPlus does not find those
files, so they give the copies the absolute paths of the files (:func:`absolute_schedule_files`).
The schedules have no interpolation (Interpolate to Timestep No, 60 minutes per item), the schedule type limits
:data:`SCHEDULE_TYPE_LIMITS` (without it, EnergyPlus warns that the schedule is not validated) and, in the IDDs that
have the field (not those of EnergyPlus 9.4 and 9.6), Adjust Schedule for Daylight Savings No, so that their values
are those of the hours of the weather file (in standard time). With the IDDs of EnergyPlus 9.4 and 9.6, which have
not that field, EnergyPlus shifts the values of a Schedule:File object by one hour while the daylight saving time is
active (RunPeriodControl:DaylightSavingTime, or that of the weather file: ScheduleManager.cc of EnergyPlus 9.6.0 adds
the indicator of the daylight saving time to the hour), so in the models of those versions with daylight saving time
each hour of that period takes the value of the next hour of the weather file (T0 of 'te_ref_nl' in the last hour of
each day is that of the next day, and the clothing insulation of a function that of the next hour; findings A22 and
A26 of the self-audit of 2026-11-11; measured on 2026-11-18 with EnergyPlus 9.6 and its sample model in July, and
not in January nor with EnergyPlus 25.1). :func:`write_schedule_file` warns of it (:func:`daylight_saving_period`).
"""

import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

__all__ = ['SCHEDULE_TYPE_LIMITS', 'absolute_schedule_files', 'daylight_saving_period', 'model_folder',
           'relative_schedule_files', 'remove_schedule_file', 'schedule_file_path', 'write_schedule_file']

#: The schedule type limits of the Schedule:File objects of accim: a ScheduleTypeLimits object with only a name, which
#: does not limit the values (the models of DesignBuilder have it; accim adds it to the others)
SCHEDULE_TYPE_LIMITS = 'Any Number'
#: The numbers of hours of a Schedule:File object (Energy+.idd: "should be either 8760 or 8784")
_HOURS = (8760, 8784)
#: The field of the Schedule:File objects with which EnergyPlus does not shift their values with the daylight saving
#: time (not in the IDDs of EnergyPlus 9.4 and 9.6)
_DAYLIGHT_SAVINGS_FIELD = 'Adjust_Schedule_for_Daylight_Savings'
#: The line of the header of a weather file with its daylight saving period (its third and fourth fields, the start and
#: end dates; 0 without one)
_HOLIDAYS_LINE = 'HOLIDAYS/DAYLIGHT SAVINGS'


def model_folder(idf: Any) -> Path:
    """The folder of the file of a model (eppy), or the current folder if the model is in memory."""
    name = getattr(idf, 'idfname', None)
    if isinstance(name, (str, os.PathLike)) and str(name):
        return Path(os.path.abspath(os.fspath(name))).parent
    return Path(os.getcwd())


def _objects(idf: Any, object_type: str) -> List[Any]:
    """The objects of a type of a model (none if it has not the type)."""
    try:
        return list(idf.idfobjects[object_type])
    except (AttributeError, KeyError, TypeError):
        return []


def daylight_saving_period(idf: Any, epw: Union[str, os.PathLike, None] = None) -> Optional[str]:
    """The daylight saving time of a model, if it has one: that of its RunPeriodControl:DaylightSavingTime object, or,
    if a RunPeriod uses the daylight saving period of the weather file (its field Use Weather File Daylight Saving
    Period, Yes by default), that of the header of the weather file ``epw`` (the start and end dates of its line
    'HOLIDAYS/DAYLIGHT SAVINGS', 0 without one).

    :param idf: The model (eppy).
    :param epw: The weather file of the simulations, or None.
    :return: A description of the period, such as 'RunPeriodControl:DaylightSavingTime, from Last Sunday in March to
        Last Sunday in October', or None without one.
    """
    for control in _objects(idf, 'RunPeriodControl:DaylightSavingTime'):
        return (f'RunPeriodControl:DaylightSavingTime, from {str(getattr(control, "Start_Date", "")).strip()} to '
                f'{str(getattr(control, "End_Date", "")).strip()}')
    uses_weather_file = any(str(getattr(run_period, 'Use_Weather_File_Daylight_Saving_Period', '') or 'Yes').strip()
                            .upper() != 'NO' for run_period in _objects(idf, 'RunPeriod'))
    if epw is None or not uses_weather_file:
        return None
    try:
        with open(epw, 'r', encoding='latin-1') as file:
            header = [next(file, '') for _ in range(8)]
        name = Path(os.fspath(epw)).name
    except (OSError, TypeError, ValueError):
        return None
    for line in header:
        if line.upper().startswith(_HOLIDAYS_LINE):
            fields = [field.strip() for field in line.split(',')]
            start, end = (fields + ['', '', '', ''])[2:4]
            if start not in ('', '0') and end not in ('', '0'):
                return f'that of the weather file {name}, from {start} to {end}'
    return None


def write_schedule_file(idf: Any, name: str, values: Sequence[float], file_name: str,
                        folder: Union[str, os.PathLike, None] = None,
                        epw: Union[str, os.PathLike, None] = None) -> Path:
    """Write the hourly values of a schedule in a CSV file and give the model a Schedule:File object with that name
    that reads them (or update the one it has).

    Without the field Adjust Schedule for Daylight Savings in the IDD of the model (EnergyPlus 9.4 and 9.6), it warns
    if the model has daylight saving time (:func:`daylight_saving_period`): EnergyPlus then shifts the values of the
    Schedule:File object by one hour while it is active, so each hour takes the value of the next hour of the file
    (measured on 2026-11-18 with EnergyPlus 9.6 and the sample model of 9.6 in July; not in January, nor with EnergyPlus
    25.1, whose Schedule:File objects accim writes with that field No).

    :param idf: The model (eppy), changed in place.
    :param name: The name of the Schedule:File object.
    :param values: The value of each hour of the year, from the hour 1 of 1 January: 8760 values, or 8784 with 29
        February.
    :param file_name: The name of the CSV file.
    :param folder: The folder of the CSV file (made if it does not exist); None for that of the model
        (:func:`model_folder`).
    :param epw: The weather file of the simulations, whose daylight saving period the model may use, for the warning;
        None to look only at the model.
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
    if _DAYLIGHT_SAVINGS_FIELD in schedule.fieldnames:
        fields[_DAYLIGHT_SAVINGS_FIELD] = 'No'
    else:
        period = daylight_saving_period(idf, epw)
        if period is not None:
            warnings.warn(f'The Schedule:File object {name} reads its values from {path.name}, and the IDD of the '
                          f'model has not the field Adjust Schedule for Daylight Savings (EnergyPlus 9.4 and 9.6): '
                          f'while the daylight saving time of the model is active ({period}), EnergyPlus shifts '
                          f'the values of the object by one hour, so each hour takes the value of the next hour of '
                          f'the file. Remove the daylight saving time from the model, or simulate it with a version of '
                          f'EnergyPlus whose Schedule:File objects have that field (such as 25.1), which accim writes '
                          f'as No.', UserWarning, stacklevel=2)
    for field, value in fields.items():
        setattr(schedule, field, value)
    return path


def schedule_file_path(idf: Any, name: str) -> Optional[str]:
    """The path of the file of a Schedule:File object of a model, as the object has it (relative to the folder of the
    model after :func:`relative_schedule_files`), or None if the model has not the object."""
    schedule = idf.getobject('Schedule:File', name)
    return None if schedule is None else str(schedule.File_Name)


def remove_schedule_file(idf: Any, name: str) -> None:
    """Remove a Schedule:File object from a model (the CSV file stays: other models can read it)."""
    schedule = idf.getobject('Schedule:File', name)
    if schedule is not None:
        idf.removeidfobject(schedule)


def _model(idf: Any) -> Tuple[Any, bool]:
    """The model (eppy) of ``idf``, and whether it was read from a file: a path is that of an IDF file, read with the
    IDD of its EnergyPlus version (:func:`accim.sim.accis.load_idf`), with the text of its numbers
    (:func:`accim.sim.accis.numbers_as_text`), so that the file saved again changes only in the paths."""
    if isinstance(idf, (str, os.PathLike)):
        from accim.sim.accis import load_idf, numbers_as_text

        with numbers_as_text():
            return load_idf(idf), True
    return idf, False


def _relative_path(path: str, folder: Path) -> Optional[str]:
    """The path of a file relative to a folder, with '/' between its folders, or None if the file is not in that
    folder or in its subfolders."""
    try:
        relative = os.path.relpath(os.path.abspath(path), folder)
    except ValueError:  # On another drive (Windows)
        return None
    if relative in (os.curdir, os.pardir) or relative.startswith(os.pardir + os.sep):
        return None
    return Path(relative).as_posix()


def relative_schedule_files(idf: Any, folder: Union[str, os.PathLike, None] = None) -> Dict[str, str]:
    """Give the Schedule:File objects of a model the paths of their files relative to the folder of the model, so
    that the model can be moved with its files, to another folder or computer (since accim 1.2.0): those whose files
    are in that folder or in its subfolders, with '/' between the folders (the separator of Linux and macOS, which
    EnergyPlus 25.1 also read on Windows in the tests of accim). The objects whose files are elsewhere keep their
    absolute paths, with a warning; those with relative paths keep them. accim writes the absolute paths
    (:func:`write_schedule_file`), so this is done once the model is complete: the output IDFs of
    :class:`accim.sim.accis.AddAccis`, whose files of T0 of the outdoor metric 'te_ref_nl' are in their folder, or a
    model with a function of the clothing insulation (:func:`accim.sim.apmv.set_pmv_input_parameters`), whose files are
    in the folder of the model (``modify_accis`` with ``epw`` writes the absolute path of the file of T0 again).

    EnergyPlus looks for the file of a relative path in the current folder and then in the folder of the IDF file
    (measured with EnergyPlus 25.1 on 2026-11-18), so it finds the files of the model from any current folder that has
    no file with the same path. The runners of accim (``run_ep``, with both backends, and the parametric module)
    simulate copies of the models in other folders, so they give the copies the absolute paths of the files
    (:func:`absolute_schedule_files`); other tools that do so, such as the evaluators of besos and its function
    ``run_building``, need the absolute paths first.

    :param idf: The model (eppy), changed in place (to be saved afterwards), or the path of an IDF file, which is read
        (:func:`accim.sim.accis.load_idf`) and saved again with eppy if a path changes.
    :param folder: The folder of the IDF file of the model: None for that of the model (:func:`model_folder`).
    :return: The new paths, by the name of the Schedule:File object.
    """
    model, from_file = _model(idf)
    base = Path(os.path.abspath(folder if folder is not None else model_folder(model)))
    changed: Dict[str, str] = {}
    elsewhere = []
    for schedule in _objects(model, 'Schedule:File'):
        path = str(schedule.File_Name).strip()
        if not path or not os.path.isabs(path):
            continue
        relative = _relative_path(path, base)
        if relative is None:
            elsewhere.append(f'{schedule.Name} ({path})')
            continue
        schedule.File_Name = relative
        changed[str(schedule.Name)] = relative
    if elsewhere:
        warnings.warn(f'The files of the Schedule:File objects {", ".join(elsewhere)} are not in the folder of the '
                      f'model ({base}) or in its subfolders: the objects keep their absolute paths, so the model finds '
                      f'those files only where they are now.', UserWarning, stacklevel=2)
    if changed and from_file:
        model.save()
    return changed


def absolute_schedule_files(idf: Any, folders: Optional[Sequence[Union[str, os.PathLike]]] = None) -> Dict[str, str]:
    """Give the Schedule:File objects of a model whose files have relative paths the absolute paths of those files,
    looked for in the folders given, in their order: by default, the current folder and the folder of the model, where
    EnergyPlus looks for them (measured with EnergyPlus 25.1 on 2026-11-18). The paths of files that are not found
    there do not change.

    The runners of accim do it in the copies of the models that they simulate in other folders (``run_ep``, with both
    backends, and the parametric module, with the models that it gets), where EnergyPlus would not find the files:
    until accim 1.2.0, it stopped there before the simulation with the severe error ``Schedule:File="...", File Name:
    "..." not found`` with any model whose Schedule:File objects had relative paths.

    :param idf: The model (eppy), changed in place, or the path of an IDF file, which is read
        (:func:`accim.sim.accis.load_idf`) and saved again with eppy if a path changes.
    :param folders: The folders where the files are looked for: None for the current folder and that of the model
        (:func:`model_folder`).
    :return: The new paths, by the name of the Schedule:File object.
    """
    model, from_file = _model(idf)
    if folders is None:
        folders = (os.getcwd(), model_folder(model))
    changed: Dict[str, str] = {}
    for schedule in _objects(model, 'Schedule:File'):
        path = str(schedule.File_Name).strip()
        if not path or os.path.isabs(path):
            continue
        for folder in folders:
            # A path written on Windows may have '\' between its folders, which is no separator on Linux and macOS
            candidate = Path(os.path.abspath(os.path.join(os.fspath(folder), path.replace('\\', '/'))))
            if candidate.is_file():
                schedule.File_Name = str(candidate)
                changed[str(schedule.Name)] = str(candidate)
                break
    if changed and from_file:
        model.save()
    return changed
