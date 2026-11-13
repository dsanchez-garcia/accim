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
from typing import Dict, Optional, Tuple

import numpy as np
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


def read_csv_outputs(csv_path: str, only_run_period: bool = True) -> Dict[str, Dict[str, pd.DataFrame]]:
    """The outputs of a CSV file of ReadVarsESO (as that which EnergyPlus leaves next to its ESO file), as
    :func:`read_eso_using_readvarseso` returns them, which reads its CSV file with this function.

    The columns of the DataFrame of each frequency are (key, variable, units): the key is the text before the last
    ':' of each name, so the keys with ':' are whole (the zones ``Block1:Zone1``); its index is the date and time of
    each row.

    :param csv_path: The CSV file.
    :type csv_path: str
    :param only_run_period: True to keep the rows of the last environment only (the run period, without the
        sizing periods before it).
    :type only_run_period: bool
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
        def parse_date_value(date_str):
            try:
                s = str(date_str).strip()
                match = re.search(r'(\d{1,2})/(\d{1,2})', s)
                if match:
                    m, d = int(match.group(1)), int(match.group(2))
                    return m * 100 + d
                return 0
            except:
                return 0

        time_values = df_all[date_col].apply(parse_date_value).values
        diffs = np.diff(time_values)
        reset_indices = np.where(diffs < -100)[0]

        if len(reset_indices) > 0:
            start_idx = reset_indices[-1] + 1
            df_all = df_all.iloc[start_idx:].reset_index(drop=True)
        elif len(df_all) > 8800:
            df_all = df_all.tail(8760).reset_index(drop=True)

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

    result = read_csv_outputs(csv_output_path, only_run_period=only_run_period)

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
