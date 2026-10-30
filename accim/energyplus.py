# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EnergyPlus installations: their folders, IDD files and versions of IDF files."""

import os
import platform
import re
from pathlib import Path
from typing import List, Optional, Union

from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS

__all__ = [
    'ENERGYPLUS_DIR_VARIABLE',
    'default_energyplus_folder',
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
