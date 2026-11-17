# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The outputs of the simulations: the outputs available in a model, and the ESO files and their CSV files."""

import os
import platform
import re
import shutil
import subprocess
import tempfile
import warnings
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from accim._besos_compat import patch_besos_read_eso
from accim.utils.editing import reduce_runtime
from accim.utils.people import get_idf_hierarchy_with_people

__all__ = [
    'identify_variable_key_pattern',
    'print_available_outputs_mod',
    'read_csv_outputs',
    'read_eso_using_readvarseso',
]


class print_available_outputs_mod:
    def __init__(
            self,
            building,
            version=None,
            name=None,
            frequency=None,
            out_dir: str = 'available_outputs',
            keep_out_dir: bool = False,
    ):
        """
        A modified version of besos' print_available_outputs function.

        :param building: The besos or eppy idf class instance.
        :param version: Deprecated.
        :param name:
        :param frequency:
        """
        # backwards compatibility
        if version:
            warnings.warn(
                "the version argument is deprecated for print_available_outputs,"
                " and will be removed in the future",
                FutureWarning,
            )
            from besos.eplus_funcs import get_idf_version
            assert version == get_idf_version(building), "Incorrect version"

        if name is not None:
            name = name.lower()
        if frequency is not None:
            frequency = frequency.lower()
        from besos.eplus_funcs import run_building
        patch_besos_read_eso()
        results = run_building(building, stdout_mode="Verbose", out_dir=out_dir)
        outputlist = []
        for key in results.keys():
            if name is not None:
                if name not in key[0].lower():
                    continue
                if frequency is not None and key[1].lower() != frequency:
                    continue
            elif frequency is not None:
                if key[1].lower() != frequency:
                    continue
            # print(list(key))
            outputlist.append(list(key))

        self.variablereaderlist = []
        self.meterreaderlist = []
        for i in range(len(outputlist)):
            if ',' in outputlist[i][0]:
                outputlist[i] = [
                    outputlist[i][0].split(',')[0],
                    outputlist[i][0].split(',')[1],
                    outputlist[i][1]
                ]
                self.variablereaderlist.append(outputlist[i])
            else:
                self.meterreaderlist.append(outputlist[i])

        # Cleanup by default to avoid leaving transient discovery folders.
        if not keep_out_dir:
            try:
                shutil.rmtree(out_dir, ignore_errors=True)
            except Exception:
                pass


#: The date and time of a row of the CSV files of ReadVarsESO, ' 07/15  00:10:00': the end of each timestep or hour
#: (the outputs of the days, months and run periods are in the row of the last timestep of the period)
_CSV_STAMP = re.compile(r'^\s*(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2}):\d{2}\s*$')
#: The first day of each month (0 for 1 January) in a leap year, so that 29 February has a day of its own
_LEAP_MONTH_STARTS = (0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335)
_FEBRUARY_28, _MARCH_1 = 58, 60
_MINUTES_PER_DAY = 24 * 60


def _follows(previous: Tuple[int, int], current: Tuple[int, int]) -> bool:
    """Whether a row of the outputs (its day of the year, in a leap year, and its minutes since midnight) follows the
    row before it in the same environment: a later time of the same day (or the same one, as in the CSV files with
    several frequencies), or the first hour of the next day after the end of its day (24:00); 28 February is
    followed by 29 February or 1 March, and 31 December by 1 January."""
    (day, minutes), (next_day, next_minutes) = previous, current
    if next_day == day:
        return next_minutes >= minutes
    following = (next_day - day) % 366 == 1 or (day == _FEBRUARY_28 and next_day == _MARCH_1)
    return following and minutes == _MINUTES_PER_DAY and next_minutes <= 60


def _csv_environment_starts(stamps: Iterable[Any]) -> List[int]:
    """The positions of the rows of the outputs of EnergyPlus that begin an environment (a sizing period, or a run
    period) from their dates and times (' 07/15  00:10:00', as in the CSV files of ReadVarsESO): those whose date and
    time do not follow those of the row with a date and time before it, as the timesteps or hours of a period follow
    each other (see :func:`_follows`); the first row with a date and time is one. The rows without them are skipped.

    A sizing period whose last day is the day before the first day of the next environment is not told apart from
    it by the dates: :func:`read_eso_using_readvarseso` takes the first date and time of the run period from the ESO
    file.

    :param stamps: The dates and times of the rows, in their order.
    :return: The positions of the first rows of the environments, in their order.
    """
    starts: List[int] = []
    previous: Optional[Tuple[int, int]] = None
    for position, stamp in enumerate(stamps):
        match = _CSV_STAMP.match(str(stamp))
        if not match or not 1 <= int(match.group(1)) <= 12:
            continue
        month, day, hour, minute = (int(match.group(number)) for number in (1, 2, 3, 4))
        current = (_LEAP_MONTH_STARTS[month - 1] + day - 1, hour * 60 + minute)
        if previous is None or not _follows(previous, current):
            starts.append(position)
        previous = current
    return starts


def _run_period_start(stamps: Sequence[Any], first_stamp: Optional[str] = None) -> int:
    """The position of the first row of the run period (the last environment) of the rows of the outputs: the
    first row of the last environment of :func:`_csv_environment_starts`, or, with ``first_stamp`` (the date and time of
    the first row of the run period, from the ESO file), the first row from it on with that date and time (if it is
    another one, the environment before the run period ends the day before it begins)."""
    starts = _csv_environment_starts(stamps)
    start = starts[-1] if starts else 0
    if first_stamp is not None:
        wanted = first_stamp.strip()
        for position in range(start, len(stamps)):
            if str(stamps[position]).strip() == wanted:
                return position
    return start


def _eso_run_period_start(eso_path: str) -> Optional[str]:
    """The date and time of the first timestep (or hour) of the last environment of an ESO file (the run period, after
    the sizing periods), as ReadVarsESO writes it in its CSV file (' 01/01  00:10:00'), or None without it: from the
    first time record (2) after its last environment record (1), ``2,<day of simulation>,<month>,<day of month>,<DST
    indicator>,<hour>,<start minute>,<end minute>,<day type>`` (the hour that ends at the end minute, so the end
    minute 60 is the hour itself)."""
    found, waiting, in_data = None, False, False
    with open(eso_path, 'r', encoding='latin-1') as eso:
        for line in eso:
            if not in_data:
                in_data = line.startswith('End of Data Dictionary')
            elif line.startswith('1,'):
                waiting = True
            elif waiting and line.startswith('2,'):
                fields = line.split(',')
                try:
                    month, day, hour = int(fields[2]), int(fields[3]), int(fields[5])
                    end = int(round(float(fields[7])))
                except (IndexError, ValueError):
                    return None
                hour, end = (hour, 0) if end == 60 else (hour - 1, end)
                found, waiting = f' {month:02d}/{day:02d}  {hour:02d}:{end:02d}:00', False
    return found


def read_csv_outputs(csv_path: str, only_run_period: bool = True,
                     run_period_start: Optional[str] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
    """The outputs of a CSV file of ReadVarsESO (as that which EnergyPlus leaves next to its ESO file), as
    :func:`read_eso_using_readvarseso` returns them, which reads its CSV file with this function.

    The columns of the DataFrame of each frequency are (key, variable, units): the key is the text before the last
    ':' of each name, so the keys with ':' are whole (the zones ``Block1:Zone1``); its index is the date and time of
    each row.

    The run period is the last environment of the file, whose rows begin where their dates and times stop following
    each other (:func:`_csv_environment_starts`): the sizing periods are before it, when the model simulates them
    (``Run Simulation for Sizing Periods`` of its ``SimulationControl``). Until accim 1.2.0, a jump back of the
    month told them apart, so the rows of a sizing period of the same month as the first day of the run period were
    taken as part of it, and, without such a jump, the rows of an output file of more than 8800 rows were cut to the
    last 8760 (those of an hourly year), so the outputs at timestep frequency of a run period of more than about 61
    days lost their first days.

    :param csv_path: The CSV file.
    :type csv_path: str
    :param only_run_period: True to keep the rows of the last environment only (the run period, without the
        sizing periods before it).
    :type only_run_period: bool
    :param run_period_start: The date and time of the first row of the run period, as the CSV file writes it
        (``' 01/01  00:10:00'``), if it is known (:func:`read_eso_using_readvarseso` takes it from the ESO file): the
        first row of the run period is then the first one with it from the last environment of the dates on, which
        tells apart a sizing period whose last day is the day before the run period begins.
    :type run_period_start: str, optional
    :return: ``{'data': {frequency: DataFrame}, 'metadata': {frequency: DataFrame}}``, with the frequencies of the
        file ('Timestep', 'Hourly', 'Daily', 'Monthly', 'Runperiod'...).
    :rtype: dict
    """
    try:
        # utf-8-sig para evitar problemas con BOM
        df_all = pd.read_csv(csv_path, encoding='utf-8-sig')
        df_all.columns = df_all.columns.str.strip()  # Limpiar espacios en headers
    except Exception as e:
        raise RuntimeError(f"Fallo al leer el CSV generado: {e}")

    # --- 5. FILTRAR DÍAS DE DISEÑO ---
    date_col = 'Date/Time'
    if only_run_period and date_col in df_all.columns:
        start_idx = _run_period_start(df_all[date_col].tolist(), run_period_start)
        if start_idx:
            df_all = df_all.iloc[start_idx:].reset_index(drop=True)

    # --- 6. SEPARAR POR FRECUENCIA Y CREAR METADATA ---
    data_dict = {}
    metadata_dict = {}

    freq_pattern = re.compile(r'\((Hourly|Daily|Monthly|RunPeriod|Annual|TimeStep)\)$', re.IGNORECASE)
    cols_by_freq = {}

    for col in df_all.columns:
        if col == date_col: continue
        match = freq_pattern.search(col)
        if match:
            raw_freq = match.group(1).capitalize()
            if raw_freq == "Timestep": raw_freq = "Timestep"
            if raw_freq not in cols_by_freq: cols_by_freq[raw_freq] = []
            cols_by_freq[raw_freq].append(col)
        else:
            if 'Other' not in cols_by_freq: cols_by_freq['Other'] = []
            cols_by_freq['Other'].append(col)

    # --- FUNCIÓN DE PARSEO CORREGIDA ---
    def parse_column_metadata(raw_col_name: str) -> Tuple[str, str, str]:
        """
        Parsea 'Object:Variable [Units](Freq)' usando rsplit para manejar
        nombres de objetos que contienen dos puntos.
        """
        # 1. Quitar sufijo de frecuencia
        clean_col = re.sub(r'\([a-zA-Z]+\)$', '', raw_col_name).strip()

        # 2. Extraer Unidades
        units = "-"
        unit_match = re.search(r'\[(.*?)\]', clean_col)
        if unit_match:
            units = unit_match.group(1)
            clean_col = re.sub(r'\s*\[.*?\]', '', clean_col).strip()

        # 3. Extraer Area y Variable
        # CORRECCIÓN AQUÍ: Usar rsplit en lugar de split
        if ':' in clean_col:
            # Divide por el ÚLTIMO dos puntos encontrado
            parts = clean_col.rsplit(':', 1)
            area = parts[0].strip()
            variable = parts[1].strip()
        else:
            area = "Environment"  # O EMS, dependiendo del caso, pero Environment es el default seguro
            variable = clean_col.strip()

        return area, variable, units

    # Procesar dataframes
    for freq, cols in cols_by_freq.items():
        extract_cols = [date_col] + cols if date_col in df_all.columns else cols
        df_subset = df_all[extract_cols].copy()
        df_subset.dropna(how='all', subset=cols, inplace=True)

        if date_col in df_subset.columns:
            df_subset.set_index(date_col, inplace=True)

        new_columns = []
        for col in cols:
            area, variable, units = parse_column_metadata(col)
            new_columns.append((area, variable, units))

        if not df_subset.empty:
            df_subset.columns = pd.MultiIndex.from_tuples(
                new_columns,
                names=['Area', 'Variable', 'Units']
            )

        data_dict[freq] = df_subset

        meta_df = pd.DataFrame(new_columns, columns=['Area', 'Report Type', 'Units'])
        meta_df = meta_df[['Report Type', 'Area', 'Units']]
        meta_df.sort_values(by=['Report Type', 'Area'], inplace=True)
        metadata_dict[freq] = meta_df.reset_index(drop=True)

    return {'data': data_dict, 'metadata': metadata_dict}


def read_eso_using_readvarseso(
        eso_file_path: str = 'eplusout.eso',
        eplus_install_dir: Optional[str] = None,
        only_run_period: bool = True,
        cleanup: bool = True
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Lee el archivo .eso usando ReadVarsESO y parsea correctamente los nombres de objetos
    que contienen dos puntos (ej: Nombres de Zonas o Equipos VRF).

    With ``only_run_period`` (the default), the outputs are those of the run period, the last environment of the
    ESO file, without the sizing periods before it: see :func:`read_csv_outputs`, which takes the first date and
    time of the run period from the ESO file.
    """

    # --- 1. ENCONTRAR EJECUTABLE READVARSESO ---
    exe_name = 'ReadVarsESO'
    if platform.system() == 'Windows':
        exe_name += '.exe'

    readvars_path = None

    # A. Verificar si el usuario dio una ruta específica
    if eplus_install_dir:
        paths_to_check = [
            eplus_install_dir,
            os.path.join(eplus_install_dir, exe_name),
            os.path.join(eplus_install_dir, 'PostProcess', exe_name)
        ]
        for p in paths_to_check:
            if os.path.isfile(p) and p.endswith(exe_name):
                readvars_path = p
                break

    # B. Búsqueda automática en rutas por defecto
    if not readvars_path:
        common_paths = [
            r'C:\EnergyPlusV26-2-0', r'C:\EnergyPlusV26-1-0',
            r'C:\EnergyPlusV25-2-0', r'C:\EnergyPlusV25-1-0', r'C:\EnergyPlusV24-2-0', r'C:\EnergyPlusV24-1-0',
            r'C:\EnergyPlusV23-2-0', r'C:\EnergyPlusV23-1-0',
            r'C:\EnergyPlusV22-2-0', r'C:\EnergyPlusV22-1-0',
            r'C:\EnergyPlusV9-6-0', r'C:\EnergyPlusV9-5-0', r'C:\EnergyPlusV9-4-0',
            '/usr/local/bin', '/Applications/EnergyPlus-23-1-0'
        ]

        for base_path in common_paths:
            potential_paths = [
                os.path.join(base_path, 'PostProcess', exe_name),
                os.path.join(base_path, exe_name)
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    readvars_path = p
                    break
            if readvars_path: break

    if not readvars_path:
        raise FileNotFoundError(
            f"No se pudo encontrar '{exe_name}'. Por favor, especifica 'eplus_install_dir'."
        )

    # --- 2. PREPARAR ARCHIVOS ---
    abs_eso_path = os.path.abspath(eso_file_path)
    if not os.path.exists(abs_eso_path):
        raise FileNotFoundError(f"No se encuentra el archivo .eso: {abs_eso_path}")

    work_dir = os.path.dirname(abs_eso_path)
    eso_filename = os.path.basename(abs_eso_path)

    csv_filename = os.path.splitext(eso_filename)[0] + '.csv'
    csv_output_path = os.path.join(work_dir, csv_filename)
    rvi_filename = 'temp_readvars.rvi'
    rvi_path = os.path.join(work_dir, rvi_filename)

    with open(rvi_path, 'w') as f:
        f.write(f"{eso_filename}\n")
        f.write(f"{csv_filename}\n")

    # --- 3. EJECUTAR READVARSESO ---
    cmd = [readvars_path, rvi_filename]
    try:
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if e.stderr else "Sin mensaje de error."
        raise RuntimeError(f"ReadVarsESO falló.\nError: {err_msg}")

    # --- 4. LEER CSV ---
    if not os.path.exists(csv_output_path):
        raise FileNotFoundError("No se generó el archivo CSV.")

    # The first date and time of the run period, from the ESO file (see read_csv_outputs)
    run_period_start = _eso_run_period_start(abs_eso_path) if only_run_period else None
    result = read_csv_outputs(csv_output_path, only_run_period=only_run_period, run_period_start=run_period_start)

    # --- 7. LIMPIEZA ---
    if cleanup:
        try:
            if os.path.exists(csv_output_path): os.remove(csv_output_path)
            if os.path.exists(rvi_path): os.remove(rvi_path)
            audit_file = os.path.join(work_dir, 'readvars.audit')
            if os.path.exists(audit_file): os.remove(audit_file)
        except OSError:
            pass

    return result


def identify_variable_key_pattern(
        idf_path: str,
        variable_name: str,
        epw_path: str,
        eplus_install_dir: Optional[str] = None
) -> str:
    """
    Identifies the naming pattern (Key Index) used by EnergyPlus for a specific Report Variable.

    This function performs a quick simulation to generate the .eso output file, extracts the
    actual 'Key Value' (Area) generated by EnergyPlus, and compares it against the IDF objects
    to determine the naming convention.

    It uses a two-level search strategy:
    1. **Direct Object Match:** Checks the first field of every object in the IDF (obj.obj[1])
       to see if it matches the ESO Key. This handles systems like VRF, Boilers, Chillers, etc.
    2. **Hierarchy Match:** If no direct object is found, it analyzes the Zone/Space/People
       hierarchy to detect composite patterns (e.g., '[Space Name] [People Name]').

    :param idf_path: Path to the input .idf file.
    :param variable_name: The name of the Output:Variable to analyze (e.g., 'VRF Heat Pump Cooling Electricity Energy').
    :param epw_path: Path to the weather file (.epw) required for simulation.
    :param eplus_install_dir: (Optional) Path to the EnergyPlus installation directory.
    :return: A string representing the pattern with placeholders (e.g., '[AirConditioner:VariableRefrigerantFlow Name]').
    """

    # --- 1. SETUP AND PREPARATION ---
    # Load the building model using BESOS/Eppy
    from besos.eplus_funcs import run_building
    from besos.eppy_funcs import get_building
    patch_besos_read_eso()
    building = get_building(idf_path)

    # Check if the requested Output:Variable exists in the IDF.
    # We check for Key_Value='*' to ensure we capture all instances.
    exists = any(
        v.Variable_Name.lower() == variable_name.lower() and v.Key_Value == '*'
        for v in building.idfobjects['Output:Variable']
    )

    # If it doesn't exist, add it to the model to ensure it appears in the output.
    if not exists:
        building.newidfobject(
            'Output:Variable',
            Key_Value='*',
            Variable_Name=variable_name,
            Reporting_Frequency='Hourly'
        )

    # Apply settings to drastically reduce simulation runtime.
    # We only need 1 day of simulation to generate the headers in the ESO file.
    reduce_runtime(
        idf_object=building,
        minimal_shadowing=True,
        shading_calculation_update_frequency=20,
        timesteps=2,
        runperiod_begin_month=1,
        runperiod_begin_day_of_month=1,
        runperiod_end_month=1,
        runperiod_end_day_of_month=1
    )

    # Create a temporary directory for simulation outputs to avoid cluttering the workspace.
    temp_dir = tempfile.mkdtemp()
    out_dir = os.path.join(temp_dir, 'output')

    try:
        print(f"Running quick simulation to trace variable: '{variable_name}'...")

        # --- RUN SIMULATION (Robust Mode) ---
        # BESOS run_building tries to parse the ESO file automatically and fails on some lines.
        # We wrap it in try/except to ignore BESOS parsing errors, as we use our own parser later.
        try:
            run_building(building, out_dir=out_dir, epw=epw_path, stdout_mode='Verbose')
        except ValueError as e:
            # If BESOS complains about "could not match", it means E+ finished but BESOS parser failed.
            # We can safely ignore this if the .eso file exists.
            if "could not match" in str(e):
                print("Warning: BESOS internal parser failed (ignored). Proceeding with custom parser.")
            else:
                # If it's another ValueError, re-raise it just in case.
                raise e
        except Exception as e:
            print(f"Warning: Simulation execution raised an exception: {e}")

        # Check if the ESO file was actually generated
        eso_path = os.path.join(out_dir, 'eplusout.eso')
        if not os.path.exists(eso_path):
            return "Error: eplusout.eso was not generated. Simulation failed."

        # --- 2. READ ESO AND EXTRACT TARGET KEY ---
        # Parse the ESO file to get metadata using the modified read_eso_using_readvarseso
        eso_data = read_eso_using_readvarseso(
            eso_file_path=eso_path,
            eplus_install_dir=eplus_install_dir,
            cleanup=False
        )

        # Try to get metadata from 'Hourly' frequency, or fallback to the first available one.
        metadata = None
        for freq in eso_data['metadata']:
            metadata = eso_data['metadata'][freq]
            break

        if metadata is None:
            return "Error: No metadata found in ESO file."

        # Filter rows matching the requested variable name.
        target_rows = metadata[metadata['Report Type'].str.lower() == variable_name.lower()]

        if target_rows.empty:
            return f"Error: Variable '{variable_name}' was not found in the simulation output."

        # Extract the 'Area' (Key Index) generated by EnergyPlus.
        # This is the string we need to match against the IDF (e.g., "VRF SYSTEM 1").
        eso_key_raw = str(target_rows.iloc[0]['Area'])

        # Crucial cleaning: remove leading/trailing spaces and convert to uppercase for comparison.
        eso_key_clean = eso_key_raw.strip().upper()

        # Handle global variables (Environment)
        if eso_key_clean == 'ENVIRONMENT':
            return "[Environment]"

        print(f"Target Key Index found in ESO: '{eso_key_raw}'")

        # --- 3. LEVEL 1 SEARCH: DIRECT OBJECT MATCH (obj.obj[1]) ---
        # This step checks if the Key Index corresponds exactly to the name of an object in the IDF.

        # List of object types to exclude to optimize performance (irrelevant for output keys).
        exclude_objs = [
            'VERSION', 'SIMULATIONCONTROL', 'BUILDING', 'GLOBALGEOMETRYRULES',
            'SITE:LOCATION', 'DESIGNDAY', 'RUNPERIOD', 'OUTPUT:VARIABLE',
            'SCHEDULE:COMPACT', 'SCHEDULE:YEAR', 'MATERIAL', 'CONSTRUCTION',
            'OUTPUT:TABLE:SUMMARYREPORTS', 'OUTPUTCONTROL:TABLE:STYLE'
        ]

        found_obj_key = None

        # Iterate over all object types present in the IDF
        for obj_type in building.idfobjects:
            if obj_type in exclude_objs:
                continue

            # Iterate over each instance of the object type
            for obj in building.idfobjects[obj_type]:
                try:
                    # In Eppy, obj.obj is the raw list of fields from the IDF line.
                    # obj.obj[0] is the Object Type (Key).
                    # obj.obj[1] is the First Field (usually Name, Heat_Pump_Name, Zone_Name, etc.).

                    # Skip if the object doesn't have at least one field after the key
                    if len(obj.obj) < 2:
                        continue

                        # Access the raw value of the first field directly.
                    # We do not rely on .Name because the field name varies in the IDD.
                    obj_name_val = str(obj.obj[1])

                    # Clean and compare
                    if obj_name_val.strip().upper() == eso_key_clean:
                        found_obj_key = obj.key  # This holds the object type (e.g., AirConditioner:VariableRefrigerantFlow)
                        break

                except Exception:
                    continue

            if found_obj_key: break

        if found_obj_key:
            # Return the formatted placeholder string using the Object Type found.
            # Example: [AirConditioner:VariableRefrigerantFlow Name]
            return f"[{found_obj_key} Name]"

        # --- 4. LEVEL 2 SEARCH: COMPOSITE HIERARCHY ---
        # If no direct object match is found, the Key Index might be a composite name
        # generated by EnergyPlus (e.g., Space Name + People Name).

        print("Direct object match not found. Analyzing Zone/Space/People hierarchy...")

        # Get the hierarchy structure (Zones -> Spaces -> People)
        hierarchy = get_idf_hierarchy_with_people(building)

        for zone_name, zone_data in hierarchy['zones'].items():

            # Check Zone Name (Fallback, though usually caught in Level 1)
            if str(zone_name).strip().upper() == eso_key_clean:
                return "[Zone Name]"

            for space in zone_data['spaces']:
                s_name = str(space['name']).strip()
                p_name = space['people']

                # 1. Check Space Name
                if s_name.upper() == eso_key_clean:
                    return "[Space Name]"

                if p_name:
                    p_name_clean = str(p_name).strip()

                    # 2. Check People Name
                    if p_name_clean.upper() == eso_key_clean:
                        return "[People Name]"

                    # 3. Check Composite: Zone Name + People Name (before the space: the default
                    # space of a zone without Space objects is named like the zone)
                    if f"{str(zone_name).strip()} {p_name_clean}".upper() == eso_key_clean:
                        return "[Zone Name] [People Name]"

                    # 4. Check Composite: Space Name + People Name
                    if f"{s_name} {p_name_clean}".upper() == eso_key_clean:
                        return "[Space Name] [People Name]"

        return f"Pattern not identified automatically for key: '{eso_key_raw}'"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"

    finally:
        # Cleanup temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
