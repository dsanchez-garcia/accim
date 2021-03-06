"""
Multiprocessing runs.

using generators instead of a list
when you are running a 100 files you have to use generators
original script: https://eppy.readthedocs.io/en/latest/runningeplus.html
slightly modified so that takes multiple EPWs located in the local folder
"""

import os
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs


def make_eplaunch_options(idf, epw):
    """Make options for run, so that it runs like EPLaunch on Windows."""
    idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
    idfversion.extend([0] * (3 - len(idfversion)))
    idfversionstr = '-'.join([str(item) for item in idfversion])
    epw = epw.split('.')[0]
    fname = idf.idfname + '_' + epw
    options = {
        'ep_version': idfversionstr,  # runIDFs needs the version number
        'output_prefix': os.path.basename(fname).split('.')[0]+'['+epw,
        'output_suffix': 'C',
        'output_directory': os.path.dirname(fname),
        'readvars': True,
        'expandobjects': True
        }
    return options


def runEp94(runOnlyAccim=None, confirmRun=None):
    """
    Run simulations in Energy Plus 9.4.0.

    :param runOnlyAccim: Default is None. Enter True to run only ACCIM output IDFs, or False to run all IDFs.
    :param confirmRun: Default is None. Enter True to run all simulations regardless the no. of them,
    or False to shut down all runs.
    :return:
    """
    iddfile = "C:/EnergyPlusV9-4-0/Energy+.idd"
    IDF.setiddname(iddfile)

    if runOnlyAccim is None:
        runOnlyAccim = input('Do you want to run only ACCIM output IDFs? [y or n]: ')
        if runOnlyAccim.lower() == 'y' or runOnlyAccim.lower() == '':
            idfnames = [x for x in os.listdir() if x.endswith('.idf') and '_pymod' in x]
        else:
            idfnames = [x for x in os.listdir() if x.endswith('.idf')]
    elif runOnlyAccim:
        idfnames = [x for x in os.listdir() if x.endswith('.idf') and '_pymod' in x]
    else:
        idfnames = [x for x in os.listdir() if x.endswith('.idf')]

    epwnames = [x for x in os.listdir() if x.endswith('.epw')]
    epwnames_run = [x.split('.epw')[0] for x in os.listdir() if x.endswith('.epw')]

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

    print(f'The IDFs we are going to run are: {idfnames}')
    print(f' and the No. of IDFs is going to be {len(idfnames)}')
    print(f'The EPWs we are going to run are: {epwnames}')
    print(f' and the No. of EPWs is going to be {len(epwnames)}')

    print('Therefore, the simulations are going to be:')
    idfs = []
    for i in idfnames:
        for j in epwnames:
            tempidf = IDF(i, j)
            print(i + '[' + j)
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

    num_CPUs = 2

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
    Delete all files except '.py', '.idf', '.epw' and '.csv'.

    'Table.csv', 'Zsz.csv' files are deleted as well.
    """
    extensions = ('.py', '.idf', '.epw', '.csv')
    csvextensions = ('Table.csv', 'Zsz.csv')
    deletelist = ([file for file in os.listdir() if not file.endswith(extensions)])
    for file in deletelist:
        os.remove(file)
    csvlist = ([file for file in os.listdir() if file.endswith(csvextensions)])
    for file in csvlist:
        os.remove(file)
