# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""The EnergyPlus versions of the models: the IDD files and the transition of IDF files to newer versions."""

import os
import re
import shutil
import subprocess
import tempfile
from typing import Optional

from accim._deprecation import accepts_legacy_kwargs
from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS

__all__ = [
    'get_idd_path_from_ep_version',
    'update_idf_version',
]


@accepts_legacy_kwargs({'EnergyPlus_version': 'energyplus_version'})
def get_idd_path_from_ep_version(energyplus_version: str) -> str:
    """The path of the IDD file of an EnergyPlus version in its default folder in Windows.

    :param energyplus_version: The EnergyPlus version, such as '25.1'. (Its name was EnergyPlus_version before
        accim 1.0.0.)
    :return: The path, for instance 'C:/EnergyPlusV25-1-0/Energy+.idd', or 'not-supported' if accim does not support
        the version. :func:`accim.energyplus.idd_path` also finds the installations in other folders.
    """
    version = str(energyplus_version).lower()
    if version not in SUPPORTED_ENERGYPLUS_VERSIONS:
        return 'not-supported'
    major, minor = version.split('.')
    return f'C:/EnergyPlusV{major}-{minor}-0/Energy+.idd'


def update_idf_version(
        input_idf_path: str,
        ep_version_target: str,
        output_idf_name: Optional[str] = None,
        intermediate_idf_pattern: Optional[str] = None
) -> None:
    """
    Updates an EnergyPlus IDF file to a target version by sequentially running
    the native EnergyPlus Transition tools.

    This function operates inside an isolated temporary directory. This guarantees
    that all required EnergyPlus .idd files are present during execution, prevents
    legacy Fortran path/space bugs, and ensures your project directory isn't
    littered with junk files (.idfold, .VCpErr, etc.).

    Args:
        input_idf_path (str): Absolute or relative path to the source .idf file.
        ep_version_target (str): The desired target EnergyPlus version (e.g., "25.1" or "25.1.0").
        output_idf_name (str, optional): The filename for the final updated IDF.
            Can optionally include the '{version}' placeholder (e.g., "model_v{version}.idf").
            If not provided, the script will overwrite the original input file.
        intermediate_idf_pattern (str, optional): The naming pattern for saving
            intermediate versions. MUST include the '{version}' placeholder
            (e.g., "backup_step_{version}.idf"). If None, no intermediate files are saved.

    Raises:
        ValueError: If intermediate_idf_pattern lacks the '{version}' placeholder,
                    or if the initial IDF version cannot be read.
        FileNotFoundError: If the target EnergyPlus transition directory cannot be found.
        RuntimeError: If there is a missing transition tool to complete the chain.
        subprocess.CalledProcessError: If the native EnergyPlus executable fails.
    """

    # =========================================================================
    # 0. ARGUMENT VALIDATION
    # =========================================================================
    if intermediate_idf_pattern and "{version}" not in intermediate_idf_pattern:
        raise ValueError(
            "The 'intermediate_idf_pattern' argument must contain the '{version}' "
            "placeholder to prevent intermediate files from overwriting each other. "
            "Example: 'my_model_{version}.idf'"
        )

    # =========================================================================
    # 1. PARSE AND NORMALIZE TARGET VERSION
    # =========================================================================
    target_parts = re.findall(r'\d+', ep_version_target)
    while len(target_parts) < 3:
        target_parts.append('0')
    target_str = "-".join(target_parts)

    ep_dir = rf"C:\EnergyPlusV{target_str}"
    updater_dir = os.path.join(ep_dir, "PreProcess", "IDFVersionUpdater")

    if not os.path.exists(updater_dir):
        raise FileNotFoundError(
            f"Could not find the updater directory: {updater_dir}\n"
            f"Please ensure EnergyPlus {ep_version_target} is installed on the C: drive."
        )

    # =========================================================================
    # 2. DETECT INITIAL VERSION OF THE IDF FILE
    # =========================================================================
    with open(input_idf_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    match_version = re.search(r'Version,\s*(\d+(?:\.\d+)+)\s*;', content, re.IGNORECASE)
    if not match_version:
        raise ValueError("Could not detect the initial version inside the IDF file.")

    current_parts = re.findall(r'\d+', match_version.group(1))
    while len(current_parts) < 3:
        current_parts.append('0')
    current_v_str = "-".join(current_parts)

    # =========================================================================
    # 3. MAP AVAILABLE TRANSITION TOOLS
    # =========================================================================
    transitions = {}
    for file_name in os.listdir(updater_dir):
        if file_name.startswith("Transition-") and file_name.endswith(".exe"):
            match_exe = re.match(r'Transition-V(.*)-to-V(.*)\.exe', file_name, re.IGNORECASE)
            if match_exe:
                transitions[match_exe.group(1)] = {
                    "v_to": match_exe.group(2),
                    "exe_path": os.path.join(updater_dir, file_name)
                }

    # =========================================================================
    # 4. BUILD THE TRANSITION CHAIN
    # =========================================================================
    paths_to_execute = []
    versions_route = []

    temp_v = current_v_str
    while temp_v != target_str:
        if temp_v not in transitions:
            raise RuntimeError(
                f"Broken transition chain: No tool found to upgrade from version {temp_v}."
            )
        next_step = transitions[temp_v]
        paths_to_execute.append(next_step["exe_path"])
        versions_route.append(temp_v)
        temp_v = next_step["v_to"]

    if not paths_to_execute:
        print(f"The IDF file is already at the target version ({ep_version_target}).")
        return

    # =========================================================================
    # 5. EXECUTION IN ISOLATED TEMPORARY WORKSPACE
    # =========================================================================
    base_dir = os.path.dirname(os.path.abspath(input_idf_path))
    original_idf_filename = os.path.basename(input_idf_path)
    original_cwd = os.getcwd()

    # Use a temporary directory. It automatically cleans up all junk files when done.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_idf_path = os.path.join(temp_dir, original_idf_filename)
        shutil.copy2(input_idf_path, temp_idf_path)

        # FIX: Copy ALL .idd files into the temp directory so the Fortran tools find them
        for item in os.listdir(updater_dir):
            if item.lower().endswith('.idd'):
                shutil.copy2(os.path.join(updater_dir, item), temp_dir)

        try:
            # Change working directory to the temporary environment
            os.chdir(temp_dir)

            for i, exe_path in enumerate(paths_to_execute):
                current_loop_v = versions_route[i]
                next_loop_v = transitions[current_loop_v]["v_to"]
                clean_current_v = current_loop_v.replace('-', '.')

                # Copy intermediate backup to the user's project folder BEFORE transition
                if intermediate_idf_pattern:
                    intermediate_name = intermediate_idf_pattern.format(version=clean_current_v)
                    shutil.copy2(original_idf_filename, os.path.join(base_dir, intermediate_name))

                print(f"Transitioning: {clean_current_v} -> {next_loop_v.replace('-', '.')} ...")

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                # Run transition on the local file. The tool automatically overwrites it.
                subprocess.run([exe_path, original_idf_filename],
                               check=True,
                               capture_output=True,
                               text=True,
                               startupinfo=startupinfo
                               )

            # =================================================================
            # 6. HANDLE FINAL OUTPUT NAME AND EXPORT
            # =================================================================
            clean_target_v = target_str.replace('-', '.')

            if output_idf_name:
                final_filename = output_idf_name.format(version=clean_target_v)
            else:
                final_filename = original_idf_filename

            final_output_path = os.path.join(base_dir, final_filename)

            # Move the final updated file from the temp space back to the user's folder
            shutil.copy2(original_idf_filename, final_output_path)
            print(f"Success! Final IDF saved as: {final_output_path}")

        except subprocess.CalledProcessError as e:
            print("\n[ERROR] Transition failed.")
            print("Standard Output:", e.stdout)
            print("Standard Error:", e.stderr)
            raise

        finally:
            # Revert to the original working directory so the rest of your app works normally
            os.chdir(original_cwd)
