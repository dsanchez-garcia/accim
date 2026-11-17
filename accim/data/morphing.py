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

"""Future weather files: the EPW files of the climate change scenarios of the global Future Weather Generator
(https://future-weather-generator.adai.pt/, Rodrigues et al.), a Java tool, from present EPW files (:func:`morph_epws`).

:func:`morph_epws` runs the tool for each EPW file and keeps an EPW file for each scenario and timeframe
(:data:`SCENARIOS`), named after the original one: ``<EPW>_<scenario>.epw`` (``Granada_ssp126_2050.epw``...). It runs
the tool with Java from the command line (``engine='java'``, the default, as before accim 1.2.0), or through pyfwg
(``engine='pyfwg'``, since accim 1.2.0, proposal E4), the Python package that runs the tool and checks its parameters
(``pyfwg.morph_epw_global``, which supports the versions 3, 4 and 5 of the global tool). pyfwg is optional: install
it with ``pip install accim[weather]``, which also installs pyweatherfiles, a package that generates typical
meteorological years (``pyweatherfiles.TMYGenerator``) and writes EPW files from hourly weather data
(``pyweatherfiles.hourly_epw_converter.HourlyEPWConverter``); with ``engine='pyfwg'``, ``epw_filepaths`` takes the paths
of EPW files of any folder, such as those, and the future EPW files are written next to each one.

The command line of the tool has changed with its versions, and ``engine='java'`` has two of them (checked with the
jar of the version 5.3.0 on 2026-11-17, the only one at hand): that of the FWG Engine, the global tool since its
version 5 (``java -jar <jar> -g -epw=... -models=...``, as pyfwg builds it: the reference, decided by the author on
2026-11-10), for the jars whose manifest has the version of the engine (:func:`fwg_jar_info`); and, for the other jars,
the 8 positional arguments of the versions that accim used before (``java -cp <jar> futureweathergenerator.Morph``),
which the version 5.3.0 does not take. The versions 3 and 4 have other command lines (12 positional arguments, and
keys and values, in pyfwg), which ``engine='java'`` does not build and could not be checked: use ``engine='pyfwg'``
for them. The classes of the version 5.3.0 need Java 17 or later: :func:`morph_epws` checks the Java of the PATH
against the jar before it moves any file.
"""
import os
import re
import shutil
import struct
import subprocess
import warnings
import zipfile
from typing import Any, Dict, Iterable, List, Optional, Tuple

__all__ = ['DEFAULT_GCMS', 'ENGINES', 'ENGINE_INTERPOLATION_METHODS', 'SCENARIOS', 'fwg_jar_info', 'morph_epws']

#: The scenarios and timeframes of the future EPW files that :func:`morph_epws` keeps (those of the global Future
#: Weather Generator, also ``pyfwg.GLOBAL_SCENARIOS`` and ``pyfwg.ALL_POSSIBLE_YEARS``), named
#: ``<EPW>_<scenario>.epw``
SCENARIOS = ('ssp126_2050', 'ssp126_2080', 'ssp245_2050', 'ssp245_2080', 'ssp370_2050', 'ssp370_2080',
             'ssp585_2050', 'ssp585_2080')
#: The global climate models of :func:`morph_epws` by default (``fwg_options_gcms=None``)
DEFAULT_GCMS = ('BCC_CSM2_MR', 'CanESM5', 'CanESM5_1', 'CanESM5_CanOE', 'CAS_ESM2_0', 'CMCC_ESM2', 'CNRM_CM6_1_HR',
                'CNRM_ESM2_1', 'EC_Earth3', 'EC_Earth3_Veg', 'FGOALS_g3', 'GISS_E2_1_G', 'GISS_E2_1_H', 'GISS_E2_2_G',
                'IPSL_CM6A_LR', 'MIROC_ES2H', 'MIROC_ES2L', 'MIROC6', 'MRI_ESM2_0', 'UKESM1_0_LL')
#: The ways of :func:`morph_epws` to run the Future Weather Generator: 'java', the command line of Java; 'pyfwg', the
#: Python package pyfwg
ENGINES = ('java', 'pyfwg')
#: The arguments of ``pyfwg.morph_epw_global`` that :func:`morph_epws` sets itself, which ``pyfwg_arguments`` cannot
#: give
_PYFWG_MANAGED = ('epw_paths', 'fwg_jar_path', 'output_dir', 'temp_base_dir', 'delete_temp_files')
#: The interpolation methods of the FWG Engine (the global tool since its version 5) by the identifiers of
#: ``fwg_options_interpolation_method_id``, those of pyfwg (``pyfwg.constants.ENGINE_INTERPOLATION_METHODS``): the
#: geodesic inverse distance weighting of the four nearest points, the rectilinear bilinear interpolation, the mean of
#: the four nearest points, the nearest point, and three interpolations of structured grids
ENGINE_INTERPOLATION_METHODS = {0: 'IDW', 1: 'BI', 2: 'AVG4P', 3: 'NP', 4: 'SCI', 5: 'SGBI', 6: 'STBI'}
#: The key of the manifest of the jars of the FWG Engine with its version, and those of the version of the tool
_ENGINE_VERSION_KEY = 'FWG-Engine-Version'
_TOOL_VERSION_KEYS = ('FWG-Distribution-Version', 'Specification-Version')
#: The Java of a class file is its major version minus 44 (52, Java 8; 61, Java 17)
_CLASS_FILE_JAVA = 44
#: The class that the command line of the versions before the FWG Engine runs
_MORPH_CLASS = 'futureweathergenerator.Morph'
#: The folder of the output folder where the FWG Engine writes the weather files (its output layout ORGANIZED)
_ENGINE_WEATHER_FOLDER = 'weather'


def fwg_jar_info(fwg_path: Any) -> Dict[str, Any]:
    """What the jar file of the Future Weather Generator says about the tool, without running it (no Java needed).

    :param fwg_path: The path of the jar file.
    :return: ``{'version': ..., 'engine': ..., 'java': ...}``: the version of the tool (``'5.3.0'``) and that of its
        FWG Engine (``'1.2.0'``), from the manifest of the jar (None in the jars before the FWG Engine, those of
        the global tool before its version 5, which do not say them), and the Java that its classes need (17 for
        the version 5.3.0: the class file version of its main class, 61, minus 44). All None if the file is not a
        jar that can be read.
    """
    info: Dict[str, Any] = {'version': None, 'engine': None, 'java': None}
    try:
        with zipfile.ZipFile(str(fwg_path)) as jar:
            manifest: Dict[str, str] = {}
            try:
                text = jar.read('META-INF/MANIFEST.MF').decode('utf-8', 'replace')
            except KeyError:
                text = ''
            for line in text.splitlines():
                key, separator, value = line.partition(':')
                if separator and key.strip() and not line.startswith(' '):
                    manifest[key.strip()] = value.strip()
            info['engine'] = manifest.get(_ENGINE_VERSION_KEY) or None
            if info['engine']:
                info['version'] = next((manifest[key] for key in _TOOL_VERSION_KEYS if manifest.get(key)), None)
            names = set(jar.namelist())
            for main_class in (manifest.get('Main-Class'), _MORPH_CLASS):
                name = f"{main_class.replace('.', '/')}.class" if main_class else ''
                if name in names:
                    with jar.open(name) as class_file:
                        header = class_file.read(8)
                    if len(header) == 8 and header[:4] == b'\xca\xfe\xba\xbe':
                        info['java'] = struct.unpack('>H', header[6:8])[0] - _CLASS_FILE_JAVA
                    break
    except (OSError, zipfile.BadZipFile, ValueError):
        pass
    return info


def _java_version() -> Optional[Tuple[int, str]]:
    """The version of the Java of the PATH: its number (8 for 1.8.0_481, 17 for 17.0.4) and its text, or None if Java
    cannot be run or does not say it."""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
    except OSError:
        return None
    output = f"{getattr(result, 'stderr', '') or ''}\n{getattr(result, 'stdout', '') or ''}"
    match = re.search(r'version "([^"]+)"', output)
    if not match:
        return None
    numbers = re.findall(r'\d+', match.group(1))
    if not numbers:
        return None
    # 1.8.0_481 is Java 8; since Java 9, the first number is the version
    number = int(numbers[1]) if numbers[0] == '1' and len(numbers) > 1 else int(numbers[0])
    return number, match.group(1)


def _check_java(info: Dict[str, Any]) -> None:
    """Stop if the Java of the PATH is older than the one that the classes of the jar need: the tool would fail
    with an UnsupportedClassVersionError for each EPW file.

    :raises RuntimeError: If it is older.
    """
    needed = info.get('java')
    if needed is None:
        return
    installed = _java_version()
    if installed is None or installed[0] >= needed:
        return
    tool = f" {info['version']}" if info.get('version') else ''
    raise RuntimeError(f'The Future Weather Generator{tool} of fwg_path needs Java {needed} or later (the class file '
                       f'version of its classes is {needed + _CLASS_FILE_JAVA}), and the Java of the PATH is '
                       f'{installed[1]}. Install it, or put the folder of its java first in the PATH (in Python, '
                       f"os.environ['PATH'] = folder + os.pathsep + os.environ['PATH']). No EPW file was moved.")


def _engine_interpolation(method: Any) -> str:
    """The interpolation method of the FWG Engine of an identifier (0, '0') or of its name ('IDW').

    :raises ValueError: If it is neither.
    """
    name = str(method).strip().upper()
    if name in ENGINE_INTERPOLATION_METHODS.values():
        return name
    try:
        return ENGINE_INTERPOLATION_METHODS[int(name)]
    except (KeyError, ValueError):
        raise ValueError(f'fwg_options_interpolation_method_id must be one of {ENGINE_INTERPOLATION_METHODS} with '
                         f'the FWG Engine (the Future Weather Generator since its version 5), not '
                         f'{method!r}.') from None


def _engine_command(fwg_path: Any, epw_path: str, folder_path: str, gcms: str, ensemble: Any,
                    month_transition_hours: Any, multithread: Any, interpolation: str,
                    limit_variables: Any) -> List[str]:
    """The command line of the FWG Engine (the global Future Weather Generator since its version 5) with the options
    of :func:`morph_epws`: that which pyfwg 0.4.0 builds with them (``_build_command_engine`` of
    ``pyfwg/workflow.py``, the reference), with the weather files in the folder ``weather`` of the output folder
    and the shifts of the temperature of the tool at their defaults."""
    def flag(value: Any) -> str:
        return 'true' if value else 'false'

    return ['java', '-jar', str(fwg_path), '-g', f'-epw={epw_path}', f'-output_folder={folder_path}{os.sep}',
            '-output_layout=ORGANIZED', f'-models={gcms}', f'-ensemble={flag(int(ensemble))}',
            '-temp_shift_winter=0.0', '-temp_shift_summer=0.0',
            f'-smooth_hours={int(float(month_transition_hours))}', f'-multithread={flag(multithread)}',
            f'-grid_interpolation_method={interpolation}', f'-epw_dictionary_limits={flag(limit_variables)}',
            '-output_type=EPW']


def morph_epws(
        fwg_path: str,
        epw_filepaths: Any = 'all',
        delete_morphing_files: bool = True,
        verbose: bool = False,
        fwg_options_gcms: str = None,
        fwg_options_ensemble: int = 1,
        fwg_options_month_transition_hours: int = 72,
        fwg_options_do_multithread_computation: bool = True,
        fwg_options_interpolation_method_id: int = 0,
        fwg_options_do_limit_variables: bool = True,
        engine: str = 'java',
        pyfwg_arguments: Optional[Dict[str, Any]] = None,
):
    """
    This function is a wrapper for the use of the FutureWeatherGenerator tool (https://future-weather-generator.adai.pt/),
    developed by Eugènio Rodrigues et al., in command line.
    It will move the epws in the working directory to a folder with the same name,
    will morph them within their respective directories,
    then will rename them using the original epw filename with the suffix depending on the scenario
    (e.j. the future scenarios for Granada.epw will be Granada_ssp126_2050.epw, Granada_ssp126_2080.epw, etc.)
    and move them back to the parent directory.
    If requested, the files generated from the moprhing process will be deleted.

    With ``engine='java'`` (the default), the command line is that of the tool of the jar (see the module): that of
    the FWG Engine for the jars of the global tool since its version 5 (checked with the version 5.3.0, whose
    weather files the tool writes in the folder ``weather`` of the folder of each EPW), and the 8 positional
    arguments of the versions that accim used before for the other jars (not those of the versions 3 and 4: use
    ``engine='pyfwg'`` for them). Before moving any file, the Java of the PATH is checked against the one that
    the classes of the jar need (17 or later for the version 5.3.0; :func:`fwg_jar_info`).

    With ``engine='pyfwg'`` (since accim 1.2.0), the tool is run through pyfwg (``pyfwg.morph_epw_global``, installed
    with ``pip install accim[weather]``), which checks the parameters and supports the versions 3, 4 and 5 of the global
    tool: each EPW stays where it is, the tool writes its files in a folder with the name of the EPW next to it, and the
    future EPWs are renamed as with Java and moved next to the original EPW. The arguments ``fwg_options_*`` are given
    to pyfwg as ``fwg_gcms`` (a list), ``fwg_create_ensemble``, ``fwg_month_transition_hours``,
    ``fwg_use_multithreading``, ``fwg_interpolation_method_id`` and ``fwg_limit_variables``, and the output of the
    tool is shown, as with Java; the urban heat island is not added (``fwg_add_uhi=False``: pyfwg adds it by default
    with the versions 3 and 4 of the tool, from the local climate zone 14 to 1, and the command line of Java of
    accim does not, so both engines give the same future EPWs: finding E4-1 of the review of accim 1.2.0); the other
    parameters of the tool take the defaults of pyfwg, unless ``pyfwg_arguments`` gives them (also ``fwg_add_uhi``).

    With ``fwg_options_ensemble=0``, the tool writes an EPW for each climate model and scenario, which morph_epws
    renames to the same name, ``<EPW>_<scenario>.epw``, so only the last one is kept: a warning tells so (finding E4-2
    of the review of accim 1.2.0).

    :param fwg_path: The path to the FutureWeatherGenerator tool.
    :param epw_filepaths: A list of epw filenames to be morphed (those of the working directory with 'all'; with
        ``engine='pyfwg'``, also paths of EPW files of other folders).
    :param delete_morphing_files: True to delete all files resulting from the morphing process
        except .epw files.
    :param verbose: True to print on screen the performed actions.
    :param fwg_options_gcms: The GCMs separated by a comma (without white space); None for those of
        :data:`DEFAULT_GCMS`, the 20 models of the versions of the tool that accim used before (the version 5.3.0
        has 23: also ``CNRM_CM6_1``, ``EC_Earth3_Veg_LR`` and ``GFDL_ESM4``, which are not in the ensemble unless
        they are given here).
    :param fwg_options_ensemble: Option to create an ensemble from the selected models: 0 is no, 1 is yes. With 0,
        the EPW of each scenario that is kept is that of one of the models (a warning).
    :param fwg_options_month_transition_hours: the number of hours to smooth the transition between months: 0 to 336 hours.
    :param fwg_options_do_multithread_computation: True to do the computations in multithread.
    :param fwg_options_interpolation_method_id: Selects the grid method, by the identifier of the version of the
        tool. With the FWG Engine (the version 5 and later; :data:`ENGINE_INTERPOLATION_METHODS`, also by name) and,
        in pyfwg, with the versions 3 and 4: 0 – inverse distance weighting of the four nearest points (the default
        of the tool), 1 – bilinear interpolation, 2 – an average of the four nearest points, 3 – nearest point (and,
        with the FWG Engine, 4 to 6, interpolations of structured grids). With the versions that accim used
        before: 0 – bilinear interpolation, 1 – an average of the four nearest points; 2 – nearest point.
    :param fwg_options_do_limit_variables: True to bound each generated variable to its physical limits
    :param engine: 'java' (the default) to run the tool with Java from the command line, or 'pyfwg' to run it through
        pyfwg (:data:`ENGINES`).
    :param pyfwg_arguments: With ``engine='pyfwg'``, other keyword arguments of ``pyfwg.morph_epw_global`` (such as
        ``fwg_version`` or ``fwg_add_uhi``, False unless given here), which replace those that this function gives;
        not those of the files (``epw_paths``, ``fwg_jar_path``, ``output_dir``, ``temp_base_dir`` and
        ``delete_temp_files``), which it sets.
    :raises RuntimeError: If the Java of the PATH is older than the one that the jar needs (before moving any file);
        if Java cannot be run or the tool fails with an EPW (after moving all the original EPWs
        back to the working folder); with ``engine='pyfwg'``, if the tool writes no future EPW for an EPW (pyfwg
        reports the errors of the tool in its log: ``pyfwg.enable_console_logging()`` shows it).
    :raises ValueError: If ``engine`` is not one of :data:`ENGINES`; with ``engine='java'`` and the FWG Engine, if
        ``fwg_options_interpolation_method_id`` is not one of its methods; with ``engine='pyfwg'``, if the tool is
        not the global Future Weather Generator, ``pyfwg_arguments`` has arguments that
        ``pyfwg.morph_epw_global`` does not take or that this function sets, or pyfwg finds the parameters not valid
        (the folders that it made for the morphing are then removed with ``delete_morphing_files``, as after the
        other errors: finding E4-3 of the review of accim 1.2.0).
    :raises ImportError: With ``engine='pyfwg'``, if pyfwg is not installed.
    """
    if engine not in ENGINES:
        raise ValueError(f'engine must be one of {list(ENGINES)}, not {engine!r}.')
    if pyfwg_arguments and engine != 'pyfwg':
        raise ValueError("pyfwg_arguments needs engine='pyfwg'.")
    try:
        without_ensemble = int(fwg_options_ensemble) == 0
    except (TypeError, ValueError):
        without_ensemble = False
    if without_ensemble:
        warnings.warn('With fwg_options_ensemble=0, the Future Weather Generator writes an EPW for each climate model '
                      'and scenario, which morph_epws renames to the same <EPW>_<scenario>.epw, so only one of them '
                      'is kept for each scenario: use fwg_options_ensemble=1 (the ensemble of the models), or run '
                      'pyfwg directly to keep the EPW of each model.', stacklevel=2)

    # Get the absolute path of the current working directory
    cwd = os.getcwd()

    # Get a list of all .epw files in the current working directory
    if epw_filepaths == 'all':
        epw_files = [file for file in os.listdir() if file.endswith(".epw")]
    else:
        epw_files = epw_filepaths

    if fwg_options_gcms is None:
        fwg_options_gcms = ','.join(DEFAULT_GCMS)

    # What the jar says: the Java that its classes need, and whether it is the FWG Engine, whose command line is
    # another one
    tool = fwg_jar_info(fwg_path)
    _check_java(tool)
    engine_tool = tool['engine'] is not None
    interpolation = (_engine_interpolation(fwg_options_interpolation_method_id)
                     if engine_tool and engine == 'java' else None)

    if engine == 'pyfwg':
        _morph_with_pyfwg(fwg_path, epw_files, delete_morphing_files, verbose, pyfwg_arguments,
                          fwg_gcms=[gcm for gcm in fwg_options_gcms.split(',') if gcm],
                          fwg_create_ensemble=bool(int(fwg_options_ensemble)),
                          fwg_month_transition_hours=int(fwg_options_month_transition_hours),
                          fwg_use_multithreading=bool(fwg_options_do_multithread_computation),
                          fwg_interpolation_method_id=fwg_options_interpolation_method_id,
                          fwg_limit_variables=bool(fwg_options_do_limit_variables))
        return

    # List to store tuples of directories, EPW file names, absolute paths of folders, and absolute paths of EPW files
    directory_file_paths = []

    # Iterate through each .epw file
    for epw_file in epw_files:
        # Create a folder with the same name as the .epw file (without extension)
        folder_name = os.path.splitext(epw_file)[0]
        folder_path = os.path.join(cwd, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Move the .epw file into the created folder
        epw_file_path = os.path.join(folder_path, epw_file)
        shutil.move(epw_file, epw_file_path)

        # Save the directory name, EPW file name, folder absolute path, and EPW file absolute path in the list
        directory_file_paths.append((folder_name, epw_file, folder_path, epw_file_path))
        if verbose:
            print(f"Moved {epw_file} to folder {folder_name}")

    # The EPWs whose morphing failed, with the reason
    failed = []
    for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
        # A list of arguments, so that the paths with blanks need no quotes, in any operating system
        if engine_tool:
            command = _engine_command(fwg_path, epw_path, folder_path, fwg_options_gcms, fwg_options_ensemble,
                                      fwg_options_month_transition_hours, fwg_options_do_multithread_computation,
                                      interpolation, fwg_options_do_limit_variables)
        else:
            command = ['java', '-cp', str(fwg_path), _MORPH_CLASS, epw_path, fwg_options_gcms,
                       str(fwg_options_ensemble), str(fwg_options_month_transition_hours), folder_path + '/',
                       str(fwg_options_do_multithread_computation), str(fwg_options_interpolation_method_id),
                       str(fwg_options_do_limit_variables)]
        try:
            returncode = subprocess.run(command).returncode
        except OSError as error:
            # Java is not installed, or not in the PATH
            failed.append(f'{epw_name} (Java could not be run: {error})')
            continue
        if returncode != 0:
            failed.append(f'{epw_name} (exit code {returncode})')


    # Search for new EPW files in the folder paths and rename them according to the pattern
    for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
        # The working directory, where the EPW files are moved back (also when the morphing produced no EPW)
        parent_folder_path = os.path.dirname(folder_path)
        # The FWG Engine writes the weather files in a folder of the output folder
        weather_path = os.path.join(folder_path, _ENGINE_WEATHER_FOLDER) if engine_tool else folder_path
        if os.path.isdir(weather_path):
            _move_scenario_epws(folder_name, weather_path, parent_folder_path, verbose)

        # Move the original EPW file to the parent folder
        original_file_path = os.path.join(folder_path, folder_name + ".epw")
        shutil.move(original_file_path, parent_folder_path)
        if verbose:
            print(f"Moved {folder_name}.epw to {parent_folder_path}")

    if delete_morphing_files:
        # Delete the folders created during the process
        for folder_name, epw_name, folder_path, epw_path in [i for i in directory_file_paths]:
            shutil.rmtree(folder_path)
            if verbose:
                print(f"Deleted folder: {folder_path}")

    if failed:
        # The command line of the jars before the FWG Engine is that of the versions that accim used before
        versions = ('' if engine_tool else " With the versions 3 and 4 of the tool, whose command lines are others, "
                                           "use engine='pyfwg'.")
        raise RuntimeError('FutureWeatherGenerator could not morph ' + '; '.join(failed) + '. The original EPW '
                           'files are back in the working folder. Check that Java is installed and that fwg_path is '
                           'the path of the jar file of FutureWeatherGenerator (with delete_morphing_files=False, '
                           'the files that the tool wrote are kept).' + versions)


def _move_scenario_epws(folder_name: str, folder_path: str, parent_folder_path: str, verbose: bool) -> List[str]:
    """Rename the EPW files of the scenarios (:data:`SCENARIOS`) that the tool wrote in a folder after the original EPW
    (``<folder_name>_<scenario>.epw``) and move them to another folder.

    :return: The paths of the moved EPW files.
    """
    moved = []
    # List files in the folder path
    files_in_folder = [i for i in os.listdir(folder_path) if i.endswith('.epw')]

    for file_name in files_in_folder:
        # Check if the file name contains any of the scenario strings
        for scenario in SCENARIOS:
            if scenario in file_name:
                # Rename the file following the specified pattern
                new_file_name = f"{folder_name}_{scenario}.epw"
                old_file_path = os.path.join(folder_path, file_name)
                new_file_path = os.path.join(folder_path, new_file_name)
                os.rename(old_file_path, new_file_path)
                if verbose:
                    print(f"Renamed {file_name} to {new_file_name}")

                # Move the renamed file to the parent folder
                moved_file_path = os.path.join(parent_folder_path, new_file_name)
                shutil.move(new_file_path, moved_file_path)
                moved.append(moved_file_path)
                if verbose:
                    print(f"Moved {new_file_name} to {parent_folder_path}")
    return moved


def _pyfwg_arguments(function, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Check ``pyfwg_arguments``: keyword arguments of ``pyfwg.morph_epw_global`` that morph_epws does not set.

    :raises ValueError: If they are not valid.
    """
    import inspect

    arguments = dict(arguments or {})
    accepted = [name for name, parameter in inspect.signature(function).parameters.items()
                if parameter.kind in (parameter.KEYWORD_ONLY, parameter.POSITIONAL_OR_KEYWORD)]
    managed = [name for name in arguments if name in _PYFWG_MANAGED]
    if managed:
        raise ValueError(f'pyfwg_arguments cannot give {managed}: morph_epws sets them (the EPW files, fwg_path, the '
                         f'folders and delete_morphing_files).')
    unknown = [name for name in arguments if name not in accepted]
    if unknown:
        raise ValueError(f'pyfwg_arguments has arguments that pyfwg.morph_epw_global does not take: {unknown}. It '
                         f'takes {[name for name in accepted if name not in _PYFWG_MANAGED]}.')
    return arguments


def _morph_with_pyfwg(fwg_path: str, epw_files: Iterable[str], delete_morphing_files: bool, verbose: bool,
                      pyfwg_arguments: Optional[Dict[str, Any]], **options: Any) -> None:
    """Morph the EPW files with pyfwg (``pyfwg.morph_epw_global``): each one in a folder with its name next to it, whose
    future EPW files are renamed after it and moved next to it (see :func:`morph_epws`).

    :param options: The arguments ``fwg_*`` of ``pyfwg.morph_epw_global`` from those of morph_epws.
    """
    try:
        import pyfwg
    except ImportError as error:
        raise ImportError("engine='pyfwg' needs pyfwg: install it with pip install accim[weather] (or pip install "
                          "pyfwg).") from error

    distribution = pyfwg.detect_fwg_tool(str(fwg_path))
    if distribution not in (None, 'global'):
        raise ValueError(f"fwg_path is the {distribution} Future Weather Generator; morph_epws runs the global one "
                         f"(use pyfwg directly for the others).")
    # Without the urban heat island, as the command line of Java (finding E4-1 of the review of accim 1.2.0)
    arguments = dict(options, fwg_show_tool_output=True, fwg_add_uhi=False)
    arguments.update(_pyfwg_arguments(pyfwg.morph_epw_global, pyfwg_arguments))

    folders = []
    failed = []
    for epw_file in epw_files:
        epw_path = os.path.abspath(epw_file)
        folder_name = os.path.splitext(os.path.basename(epw_path))[0]
        parent_folder_path = os.path.dirname(epw_path)
        folder_path = os.path.join(parent_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        folders.append(folder_path)
        if verbose:
            print(f'Morphing {epw_path} with pyfwg in the folder {folder_name}')
        try:
            created = pyfwg.morph_epw_global(epw_paths=[epw_path], fwg_jar_path=str(fwg_path), output_dir=folder_path,
                                             temp_base_dir=os.path.join(folder_path, 'pyfwg_temp'),
                                             delete_temp_files=delete_morphing_files, **arguments)
        except OSError as error:
            # Java is not installed, or not in the PATH
            failed.append(f'{os.path.basename(epw_path)} (Java could not be run: {error})')
            continue
        except ValueError:
            # pyfwg finds the parameters not valid: the folders are removed as after the other errors (finding E4-3 of
            # the review of accim 1.2.0)
            if delete_morphing_files:
                for folder in folders:
                    shutil.rmtree(folder, ignore_errors=True)
            raise
        if not [path for path in created if str(path).lower().endswith('.epw')]:
            failed.append(f'{os.path.basename(epw_path)} (no future EPW was written)')
        _move_scenario_epws(folder_name, folder_path, parent_folder_path, verbose)

    if delete_morphing_files:
        for folder_path in folders:
            shutil.rmtree(folder_path)
            if verbose:
                print(f"Deleted folder: {folder_path}")

    if failed:
        raise RuntimeError('FutureWeatherGenerator could not morph ' + '; '.join(failed) + ' with pyfwg. Check that '
                           'Java is installed and that fwg_path is the path of the jar file of the global '
                           'FutureWeatherGenerator; pyfwg.enable_console_logging() shows the errors of the tool (with '
                           'delete_morphing_files=False, the files that the tool wrote are kept).')

