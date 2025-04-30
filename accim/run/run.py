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

"""
Multiprocessing runs.

using generators instead of a list
when you are running 100 files you have to use generators
original script: https://eppy.readthedocs.io/en/latest/runningeplus.html
slightly modified so that takes multiple sample_EPWs located in the local folder
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
        'output_prefix': os.path.basename(fname).split('.idf')[0]+'['+epw,
        'output_suffix': 'C',
        'output_directory': os.path.dirname(fname),
        'readvars': True,
        'expandobjects': True
        }
    return options


def runEp(
        runOnlyAccim: bool=None,
        confirmRun: bool=None,
        num_CPUs: int = 2,
        EnergyPlus_version: str = None
):
    """
    Run simulations in the latest EnergyPlus version installed in the computer.

    :param runOnlyAccim: Default is None.
        Enter True to run only ACCIM output IDFs, or False to run all IDFs.
    :type runOnlyAccim: bool
    :param confirmRun: Default is None.
        Enter True to run all simulations regardless the no. of them,
        or False to shut down all runs.
    :type confirmRun: bool
    :param num_CPUs: An integer. The number of CPUs to be used.
    :type num_CPUs: int
    :param EnergyPlus_version: A string.
        It should be the EnergyPlus version of the IDFs, from '9.0' to '23.2'.
    :type EnergyPlus_version: str
    """

    # fullEPversionsList = [
    #     '9.1',
    #     '9.2',
    #     '9.3',
    #     '9.4',
    #     '9.5',
    #     '9.6',
    #     '22.1',
    #     '22.2',
    #     '23.1',
    #     '23.2',
    # ]

    if EnergyPlus_version is None:
        print('You must enter an EnergyPlus version from the following list:')
        print(fullEPversionsList)
        EnergyPlus_version = input('Please enter the desired EnergyPlus version: ')

    iddfile = get_idd_path_from_ep_version(EnergyPlus_version=EnergyPlus_version)

    # if EnergyPlus_version.lower() == '9.1':
    #     iddfile = 'C:/EnergyPlusV9-1-0/Energy+.idd'
    # elif EnergyPlus_version.lower() == '9.2':
    #     iddfile = 'C:/EnergyPlusV9-2-0/Energy+.idd'
    # elif EnergyPlus_version.lower() == '9.3':
    #     iddfile = 'C:/EnergyPlusV9-3-0/Energy+.idd'
    # elif EnergyPlus_version.lower() == '9.4':
    #     iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    # elif EnergyPlus_version.lower() == '9.5':
    #     iddfile = 'C:/EnergyPlusV9-5-0/Energy+.idd'
    # elif EnergyPlus_version.lower() == '9.6':
    #     iddfile = 'C:/EnergyPlusV9-6-0/Energy+.idd'
    # elif EnergyPlus_version.lower() == '22.1':
    #     iddfile = 'C:\EnergyPlusV22-1-0\Energy+.idd'
    # elif EnergyPlus_version.lower() == '22.2':
    #     iddfile = 'C:\EnergyPlusV22-2-0\Energy+.idd'
    # elif EnergyPlus_version.lower() == '23.1':
    #     iddfile = 'C:\EnergyPlusV23-1-0\Energy+.idd'
    # elif EnergyPlus_version.lower() == '23.2':
    #     iddfile = 'C:\EnergyPlusV23-2-0\Energy+.idd'
    # else:
    if iddfile == 'not-supported':
        while EnergyPlus_version.lower() not in fullEPversionsList:
            print(f'{EnergyPlus_version} is not available. You must enter one of the following list:')
            print(fullEPversionsList)
            EnergyPlus_version = input('Please enter the desired EnergyPlus version: ')

    try:
        IDF.setiddname(iddfile)
    except IDDAlreadySetError:
        print('IDD was already set.')

    if runOnlyAccim is None:
        runOnlyAccim = input('Do you want to run only ACCIM output IDFs? [y or n]: ')
        if runOnlyAccim.lower() == 'y' or runOnlyAccim.lower() == '':
            idfnames = [x for x in os.listdir() if x.endswith('.idf') and '[' in x]
        else:
            idfnames = [x for x in os.listdir() if x.endswith('.idf')]
    elif runOnlyAccim:
        idfnames = [x for x in os.listdir() if x.endswith('.idf') and '[' in x]
    else:
        idfnames = [x for x in os.listdir() if x.endswith('.idf')]

    epwnames = [x for x in os.listdir() if x.endswith('.epw')]
    epwnames_run = [x.replace('.epw', '') for x in os.listdir() if x.endswith('.epw')]

    # if IDFfilesPath is None:
    # else:
    #     if runOnlyAccim.lower() == 'y' or runOnlyAccim.lower() == '':
    #         idfnames = [x for x in os.listdir(IDFfilesPath) if x.endswith('.idf') and '_pymod' in x]
    #     else:
    #         idfnames = [x for x in os.listdir(IDFfilesPath) if x.endswith('.idf')]
    #
    # if EPWfilesPath is None:
    #     epwnames = [x for x in os.listdir() if x.endswith('.epw')]
    #     epwnames_run = [x.split('.epw')[0] for x in os.listdir() if x.endswith('.epw')]
    # else:
    #     epwnames = [x for x in os.listdir(EPWfilesPath) if x.endswith('.epw')]
    #     epwnames_run = [x.split('.epw')[0] for x in os.listdir(EPWfilesPath) if x.endswith('.epw')]

    print(f'The IDFs we are going to run are:')
    print(*idfnames, sep="\n")
    print(f' and the No. of IDFs is going to be {len(idfnames)}')
    print(f'The sample_EPWs we are going to run are:')
    print(*epwnames, sep="\n")
    print(f' and the No. of sample_EPWs is going to be {len(epwnames)}')

    print('Therefore, the simulations are going to be:')
    idfs = []
    for i in idfnames:
        for j in epwnames:
            tempidf = IDF(i, j)
            print(i.split('.idf')[0] + '[' + j.split('.epw')[0])
            idfs.append(tempidf)
    print(f' and the No. of simulations is going to be {len(idfs)}')
    # print(idfs)

    runs = []
    for i in idfs:
        for j in epwnames_run:
            temprun = (i, make_eplaunch_options(i, j))
            if i.epw == j+'.epw':
                # print(temprun)
                runs.append(temprun)
            else:
                continue

    if confirmRun is None:
        confirmRun = input(
            f'The number of simulations is going to be {len(runs)}. Do you still want to proceed? [y or n]: ')
        if confirmRun == 'y':
            runIDFs(runs, num_CPUs)
        else:
            print('Run has been shut down')
    elif confirmRun:
        runIDFs(runs, num_CPUs)
    else:
        print('Run has been shut down')


def removefiles():
    """
    Delete all files except '.py', '.idf', '.epw', '.csv' and '.eso'.

    'Table.csv', 'Meter.csv', 'Zsz.csv' files are deleted as well.
    """
    extensions = ('.py', '.idf', '.epw', '.csv', '.eso')
    csvextensions = ('Table.csv', 'Meter.csv', 'Zsz.csv')
    deletelist = ([file for file in os.listdir() if not file.endswith(extensions)])
    for file in deletelist:
        os.remove(file)
    csvlist = ([file for file in os.listdir() if file.endswith(csvextensions)])
    for file in csvlist:
        os.remove(file)
