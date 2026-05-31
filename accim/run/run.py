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

"""Run EnergyPlus simulations for the IDF + EPW files in the working directory.

Multiprocessing runs based on the eppy example
(https://eppy.readthedocs.io/en/latest/runningeplus.html), adapted so that it
takes multiple EPWs located in the local folder.
"""

import os
from eppy.modeleditor import IDF, IDDAlreadySetError
from eppy.runner.run_functions import runIDFs
from accim.lists import fullEPversionsList
from accim.utils import get_idd_path_from_ep_version


def make_eplaunch_options(idf, epw):
    """Make options for run, so that it runs like EPLaunch on Windows."""
    idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
    idfversion.extend([0] * (3 - len(idfversion)))
    idfversionstr = '-'.join([str(item) for item in idfversion])
    epw = epw.split('.')[0]
    fname = idf.idfname + '_' + epw
    options = {
        'ep_version': idfversionstr,  # runIDFs needs the version number
        'output_prefix': os.path.basename(fname).split('.idf')[0] + '[' + epw,
        'output_suffix': 'C',
        'output_directory': os.path.dirname(fname),
        'readvars': True,
        'expandobjects': True,
    }
    return options


# --------------------------------------------------------------------------- #
# Interactive prompts (only used when the corresponding argument is not given)
# --------------------------------------------------------------------------- #
def _prompt_energyplus_version():
    print('You must enter an EnergyPlus version from the following list:')
    print(fullEPversionsList)
    return input('Please enter the desired EnergyPlus version: ')


def _prompt_run_only_accim():
    return input('Do you want to run only ACCIM output IDFs? [y or n]: ')


def _prompt_confirm_run(num_runs):
    return input(
        f'The number of simulations is going to be {num_runs}. '
        f'Do you still want to proceed? [y or n]: ')


def run_ep(
        run_only_accim: bool = None,
        confirm_run: bool = None,
        num_cpus: int = 2,
        energyplus_version: str = None,
):
    """Run the simulations for the IDF + EPW files in the current directory.

    :param run_only_accim: True to run only the ACCIM output IDFs (those whose
        name contains '['), False to run all IDFs. If None, the user is asked.
    :type run_only_accim: bool
    :param confirm_run: True to run all simulations regardless of their number,
        False to abort. If None, the user is asked.
    :type confirm_run: bool
    :param num_cpus: The number of CPUs to be used.
    :type num_cpus: int
    :param energyplus_version: The EnergyPlus version of the IDFs (e.g. '24.2').
        If None, the user is asked.
    :type energyplus_version: str
    """
    if energyplus_version is None:
        energyplus_version = _prompt_energyplus_version()

    iddfile = get_idd_path_from_ep_version(EnergyPlus_version=energyplus_version)
    # Re-prompt (and re-resolve the IDD) until a recognised version is entered.
    while iddfile == 'not-supported':
        print(f'{energyplus_version} is not available. You must enter one of the following list:')
        print(fullEPversionsList)
        energyplus_version = input('Please enter the desired EnergyPlus version: ')
        iddfile = get_idd_path_from_ep_version(EnergyPlus_version=energyplus_version)

    try:
        IDF.setiddname(iddfile)
    except IDDAlreadySetError:
        print('IDD was already set.')

    if run_only_accim is None:
        answer = _prompt_run_only_accim()
        run_only_accim = answer.lower() in ('y', '')
    if run_only_accim:
        idfnames = [x for x in os.listdir() if x.endswith('.idf') and '[' in x]
    else:
        idfnames = [x for x in os.listdir() if x.endswith('.idf')]

    epwnames = [x for x in os.listdir() if x.endswith('.epw')]
    epwnames_run = [x.replace('.epw', '') for x in epwnames]

    print('The IDFs we are going to run are:')
    print(*idfnames, sep="\n")
    print(f' and the No. of IDFs is going to be {len(idfnames)}')
    print('The EPWs we are going to run are:')
    print(*epwnames, sep="\n")
    print(f' and the No. of EPWs is going to be {len(epwnames)}')

    print('Therefore, the simulations are going to be:')
    idfs = []
    for i in idfnames:
        for j in epwnames:
            tempidf = IDF(i, j)
            print(i.split('.idf')[0] + '[' + j.split('.epw')[0])
            idfs.append(tempidf)
    print(f' and the No. of simulations is going to be {len(idfs)}')

    runs = []
    for i in idfs:
        for j in epwnames_run:
            if i.epw == j + '.epw':
                runs.append((i, make_eplaunch_options(i, j)))

    if confirm_run is None:
        confirm_run = _prompt_confirm_run(len(runs)).lower() == 'y'
    if confirm_run:
        runIDFs(runs, num_cpus)
    else:
        print('Run has been shut down')


def removefiles():
    """Delete all files except '.py', '.idf', '.epw', '.csv' and '.eso'.

    'Table.csv', 'Meter.csv', 'Zsz.csv' files are deleted as well.
    """
    extensions = ('.py', '.idf', '.epw', '.csv', '.eso')
    csvextensions = ('Table.csv', 'Meter.csv', 'Zsz.csv')
    deletelist = [file for file in os.listdir() if not file.endswith(extensions)]
    for file in deletelist:
        os.remove(file)
    csvlist = [file for file in os.listdir() if file.endswith(csvextensions)]
    for file in csvlist:
        os.remove(file)
