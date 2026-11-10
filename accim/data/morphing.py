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
the tool with Java from the command line (``engine='java'``, the default, as before accim 1.2.0), with the arguments
of the command line of the versions of the tool that accim has used, or through pyfwg (``engine='pyfwg'``, since
accim 1.2.0, proposal E4), the Python package that runs the tool and checks its parameters
(``pyfwg.morph_epw_global``, which supports the versions 3, 4 and 5 of the global tool). pyfwg is optional: install
it with ``pip install accim[weather]``, which also installs pyweatherfiles, a package that generates typical
meteorological years (``pyweatherfiles.TMYGenerator``) and writes EPW files from hourly weather data
(``pyweatherfiles.hourly_epw_converter.HourlyEPWConverter``); with ``engine='pyfwg'``, ``epw_filepaths`` takes the paths
of EPW files of any folder, such as those, and the future EPW files are written next to each one.
"""
import os
import shutil
import subprocess
import warnings
from typing import Any, Dict, Iterable, List, Optional

__all__ = ['DEFAULT_GCMS', 'ENGINES', 'SCENARIOS', 'morph_epws']

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
        :data:`DEFAULT_GCMS`.
    :param fwg_options_ensemble: Option to create an ensemble from the selected models: 0 is no, 1 is yes. With 0,
        the EPW of each scenario that is kept is that of one of the models (a warning).
    :param fwg_options_month_transition_hours: the number of hours to smooth the transition between months: 0 to 336 hours.
    :param fwg_options_do_multithread_computation: True to do the computations in multithread.
    :param fwg_options_interpolation_method_id: Selects the grid method: 0 – bilinear interpolation, 1 – an average of the four nearest points; 2 – nearest point.
    :param fwg_options_do_limit_variables: True to bound each generated variable to its physical limits
    :param engine: 'java' (the default) to run the tool with Java from the command line, or 'pyfwg' to run it through
        pyfwg (:data:`ENGINES`).
    :param pyfwg_arguments: With ``engine='pyfwg'``, other keyword arguments of ``pyfwg.morph_epw_global`` (such as
        ``fwg_version`` or ``fwg_add_uhi``, False unless given here), which replace those that this function gives;
        not those of the files (``epw_paths``, ``fwg_jar_path``, ``output_dir``, ``temp_base_dir`` and
        ``delete_temp_files``), which it sets.
    :raises RuntimeError: If Java cannot be run or the tool fails with an EPW (after moving all the original EPWs
        back to the working folder); with ``engine='pyfwg'``, if the tool writes no future EPW for an EPW (pyfwg
        reports the errors of the tool in its log: ``pyfwg.enable_console_logging()`` shows it).
    :raises ValueError: If ``engine`` is not one of :data:`ENGINES`; with ``engine='pyfwg'``, if the tool is not the
        global Future Weather Generator, ``pyfwg_arguments`` has arguments that ``pyfwg.morph_epw_global`` does not take
        or that this function sets, or pyfwg finds the parameters not valid (the folders that it made for the
        morphing are then removed with ``delete_morphing_files``, as after the other errors: finding E4-3 of the
        review of accim 1.2.0).
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
        command = ['java', '-cp', str(fwg_path), 'futureweathergenerator.Morph', epw_path, fwg_options_gcms,
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
        _move_scenario_epws(folder_name, folder_path, parent_folder_path, verbose)

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
        raise RuntimeError('FutureWeatherGenerator could not morph ' + '; '.join(failed) + '. The original EPW '
                           'files are back in the working folder. Check that Java is installed and that fwg_path is '
                           'the path of the jar file of FutureWeatherGenerator (with delete_morphing_files=False, '
                           'the files that the tool wrote are kept).')


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

