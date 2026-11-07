# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EnergyPlus installations: their folders, IDD files and versions of IDF files."""

import os
import platform
import re
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import List, Optional, Union

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS

__all__ = [
    'ENERGYPLUS_DIR_VARIABLE',
    'default_energyplus_folder',
    'expand_objects',
    'find_energyplus',
    'idd_path',
    'read_idf_version',
    'unsupported_version_message',
]

#: Environment variable with the folder of an EnergyPlus installation, which takes precedence over the
#: default folders when its version is the one needed.
ENERGYPLUS_DIR_VARIABLE = 'ACCIM_ENERGYPLUS_DIR'
_VERSION_OBJECT = re.compile(r'^\s*version\s*,\s*([0-9][0-9.\-]*)\s*[;,]', re.IGNORECASE | re.MULTILINE)


def unsupported_version_message(version: str) -> str:
    """The message of the error for an EnergyPlus version that accim does not support."""
    first, last = SUPPORTED_ENERGYPLUS_VERSIONS[0], SUPPORTED_ENERGYPLUS_VERSIONS[-1]
    return (f'EnergyPlus {version} is not supported. accim only works with the versions between EnergyPlus '
            f'{first} (enter {first}) and EnergyPlus {last} (enter {last}).')


def _major_minor(version: str) -> tuple:
    parts = str(version).replace('-', '.').split('.')
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(f'{version!r} is not an EnergyPlus version (for instance, 25.1).')
    return parts[0], parts[1]


def default_energyplus_folder(version: str) -> Path:
    """The folder where the EnergyPlus installer puts a version (for instance C:/EnergyPlusV25-1-0)."""
    major, minor = _major_minor(version)
    system = platform.system()
    if system == 'Windows':
        return Path(f'C:/EnergyPlusV{major}-{minor}-0')
    if system == 'Darwin':
        return Path(f'/Applications/EnergyPlus-{major}-{minor}-0')
    return Path(f'/usr/local/EnergyPlus-{major}-{minor}-0')


def _folder_version(folder: Path) -> Optional[str]:
    idd = folder / 'Energy+.idd'
    if not idd.is_file():
        return None
    with open(idd, encoding='latin-1') as file:
        first_line = file.readline()
    match = re.search(r'IDD_Version\s+(\d+)\.(\d+)', first_line)
    return f'{match.group(1)}.{match.group(2)}' if match else None


def find_energyplus(version: str, required: bool = True) -> Optional[Path]:
    """The folder of the installation of an EnergyPlus version.

    The folder in the environment variable ``ACCIM_ENERGYPLUS_DIR`` is used if it has that version;
    otherwise, the default folder of the installer.

    :param version: The EnergyPlus version, such as '25.1' (later numbers, such as '25.1.0', are ignored).
    :param required: If True, raise an error when the version is not installed; otherwise, return None.
    :raises FileNotFoundError: If the version is not installed and ``required`` is True.
    """
    major, minor = _major_minor(version)
    wanted = f'{major}.{minor}'
    candidates: List[Path] = []
    if os.environ.get(ENERGYPLUS_DIR_VARIABLE):
        candidates.append(Path(os.environ[ENERGYPLUS_DIR_VARIABLE]))
    candidates.append(default_energyplus_folder(wanted))
    for folder in candidates:
        if _folder_version(folder) == wanted:
            return folder
    if required:
        raise FileNotFoundError(
            f'EnergyPlus {wanted} was not found in {default_energyplus_folder(wanted)}. Install it there, or set the '
            f'environment variable {ENERGYPLUS_DIR_VARIABLE} to the folder where it is installed.'
        )
    return None


def idd_path(version: str) -> str:
    """The path of the IDD file of an EnergyPlus version (that of the default folder if it is not installed).

    :raises ValueError: If accim does not support the version.
    """
    major, minor = _major_minor(version)
    if f'{major}.{minor}' not in SUPPORTED_ENERGYPLUS_VERSIONS:
        raise ValueError(unsupported_version_message(f'{major}.{minor}'))
    folder = find_energyplus(f'{major}.{minor}', required=False) or default_energyplus_folder(f'{major}.{minor}')
    return (folder / 'Energy+.idd').as_posix()


def read_idf_version(path: Union[str, os.PathLike]) -> str:
    """The EnergyPlus version of an IDF file, as 'major.minor' (for instance '25.1').

    :raises ValueError: If the file has no Version object.
    """
    with open(path, 'rb') as file:
        text = file.read().decode('latin-1')
    text = re.sub(r'!.*', '', text)
    match = _VERSION_OBJECT.search(text)
    if match is None:
        raise ValueError(f'The EnergyPlus version of {path} could not be read (the file has no Version object).')
    major, minor = _major_minor(match.group(1))
    return f'{major}.{minor}'


def expand_objects(
    path: Union[str, os.PathLike],
    output: Optional[Union[str, os.PathLike]] = None,
    version: Optional[str] = None,
) -> Path:
    """Expand the HVACTemplate objects of an IDF file into the HVAC objects they stand for (thermostats, zone
    equipment, air and plant loops...), with the program ExpandObjects of EnergyPlus, as EnergyPlus does when it runs
    with ``--expandobjects`` (and :func:`accim.run.run_ep`).

    accim needs the expanded models to change the thermostats and the HVAC objects of the existing HVAC systems:
    :class:`accim.sim.accis.AddAccis` expands its input IDFs if they have HVACTemplate objects.

    :param path: The IDF file.
    :param output: The expanded IDF file; by default, '<name>_expanded.idf' in the folder of the IDF file.
    :param version: The EnergyPlus version whose ExpandObjects expands the file; by default, that of the file.
    :return: The path of the expanded IDF file.
    :raises FileNotFoundError: If that EnergyPlus version is not installed.
    :raises RuntimeError: If ExpandObjects writes no expanded file.
    """
    path = Path(path)
    version = version or read_idf_version(path)
    folder = find_energyplus(version)
    program = folder / ('ExpandObjects.exe' if platform.system() == 'Windows' else 'ExpandObjects')
    output = Path(output) if output is not None else path.with_name(f'{path.stem}_expanded.idf')
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        shutil.copyfile(path, work / 'in.idf')
        # ExpandObjects checks the fields with the IDD of its working folder
        shutil.copyfile(folder / 'Energy+.idd', work / 'Energy+.idd')
        result = subprocess.run([str(program)], cwd=work, capture_output=True, text=True, errors='replace')
        errors_file = work / 'expandedidf.err'
        errors = errors_file.read_text(errors='replace').strip() if errors_file.is_file() else ''
        expanded = work / 'expanded.idf'
        if not expanded.is_file():
            raise RuntimeError(f'ExpandObjects of EnergyPlus {version} could not expand {path}: '
                               f'{errors or result.stdout.strip()}')
        if errors:
            warnings.warn(f'ExpandObjects of EnergyPlus {version} reported these errors when it expanded {path}:\n'
                          f'{errors}', stacklevel=2)
        shutil.copyfile(expanded, output)
    return output
