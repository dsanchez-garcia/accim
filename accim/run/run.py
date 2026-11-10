# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Run the simulations of the IDFs and EPWs of the working folder.

Each IDF is run with each EPW, in parallel, and the output files are named 'IDF name[EPW name'
(for instance 'model[CS_INT EN16798[...[NS_X[Seville.csv'), as EP-Launch names them.

Two backends run the EMS programs of the output IDFs of accim:

- 'ems' (default): EnergyPlus runs them with its Energy Management System, through eppy.
- 'api': EnergyPlus runs through its Python API, and the programs run in Python
  (:mod:`accim.sim.energyplus_api`), with the same results.
"""

import os
import re
from typing import Callable, List, Optional, Sequence

from eppy.modeleditor import IDDAlreadySetError, IDF
from eppy.runner.run_functions import runIDFs

from accim._deprecation import deprecated_alias
from accim.constants import SUPPORTED_ENERGYPLUS_VERSIONS
from accim.energyplus import idd_path

__all__ = ['BACKENDS', 'get_iddfile_from_idfs', 'make_eplaunch_options', 'remove_files', 'removefiles', 'runEp',
           'run_ep', 'simulation_name']

#: 'ems' runs the EMS programs with the EMS of EnergyPlus; 'api', in Python through the API of EnergyPlus
BACKENDS = ('ems', 'api')
_VERSIONS = list(SUPPORTED_ENERGYPLUS_VERSIONS) + ['auto']


def get_iddfile_from_idfs(idfnames: Sequence[str]) -> str:
    """The path of the IDD file of the EnergyPlus version of the IDFs.

    eppy uses a single IDD file in each Python session, therefore all IDFs must be of the same
    EnergyPlus version.

    :param idfnames: The IDF file names.
    :return: The path of the IDD file, for instance 'C:/EnergyPlusV26-2-0/Energy+.idd' (see
        :func:`accim.energyplus.idd_path`).
    :raises ValueError: If the IDFs are of different or unsupported versions, or have no Version object.
    """
    versions = set()
    for idfname in idfnames:
        with open(idfname, 'r', encoding='utf-8', errors='ignore') as f:
            match = re.search(r'^\s*Version\s*,\s*(\d+)\.(\d+)', f.read(), re.IGNORECASE | re.MULTILINE)
        if match is None:
            raise ValueError(f'The EnergyPlus version of {idfname} could not be read.')
        versions.add(f'{int(match.group(1))}.{int(match.group(2))}')
    versions = sorted(versions)
    if len(versions) > 1:
        raise ValueError(
            f'The IDFs are of different EnergyPlus versions ({", ".join(versions)}). '
            f'Please run the IDFs of each version separately, or update them to the same version.'
        )
    if versions[0] not in SUPPORTED_ENERGYPLUS_VERSIONS:
        raise ValueError(
            f'The IDFs are of EnergyPlus {versions[0]}, which is not supported. '
            f'The supported versions are: {list(SUPPORTED_ENERGYPLUS_VERSIONS)}'
        )
    return idd_path(versions[0])


def _stem(name: str, extension: str) -> str:
    base = os.path.basename(name)
    return base[:-len(extension)] if base.lower().endswith(extension) else base


def simulation_name(idf: str, epw: str) -> str:
    """The name of the output files of the simulation of an IDF with an EPW: 'IDF name[EPW name'.

    :param idf: The name or path of the IDF file (with or without '.idf').
    :param epw: The name or path of the EPW file (with or without '.epw').
    """
    return f'{_stem(idf, ".idf")}[{_stem(epw, ".epw")}'


def make_eplaunch_options(idf, epw: str) -> dict:
    """The options of eppy's runIDFs to run an IDF like EP-Launch on Windows.

    :param idf: The eppy IDF object.
    :param epw: The name of the EPW file (with or without '.epw').
    """
    # The major, minor and patch numbers ('9.4.0.002' of DesignBuilder is '9-4-0', '23.1' is '23-1-0')
    idfversion = [item.strip() for item in idf.idfobjects['version'][0].Version_Identifier.split('.')][:3]
    idfversion.extend([0] * (3 - len(idfversion)))
    idfversionstr = '-'.join([str(item) for item in idfversion])
    return {
        'ep_version': idfversionstr,  # runIDFs needs the version number
        'output_prefix': simulation_name(idf.idfname, epw),
        'output_suffix': 'C',
        'output_directory': os.path.dirname(idf.idfname),
        'readvars': True,
        'expandobjects': True,
    }


def _ask_version(energyplus_version: Optional[str]) -> str:
    if energyplus_version is None:
        print('You must enter an EnergyPlus version from the following list:')
        print(_VERSIONS)
        energyplus_version = input('Please enter the desired EnergyPlus version: ')
    while energyplus_version.lower() not in _VERSIONS:
        print(f'{energyplus_version} is not available. You must enter one of the following list:')
        print(_VERSIONS)
        energyplus_version = input('Please enter the desired EnergyPlus version: ')
    return energyplus_version


def _idf_names(only_accim_idfs: Optional[bool]) -> List[str]:
    if only_accim_idfs is None:
        answer = input('Do you want to run only ACCIM output IDFs? [y or n]: ')
        only_accim_idfs = answer.lower() in ('y', '')
    return sorted(x for x in os.listdir() if x.endswith('.idf') and ('[' in x or not only_accim_idfs))


def _confirm(confirm: Optional[bool], number: int) -> bool:
    if confirm is None:
        answer = input(f'The number of simulations is going to be {number}. Do you still want to proceed? [y or n]: ')
        confirm = answer == 'y'
    if not confirm:
        print('Run has been shut down')
    return bool(confirm)


def run_ep(
    only_accim_idfs: Optional[bool] = None,
    confirm: Optional[bool] = None,
    processes: int = 2,
    energyplus_version: Optional[str] = None,
    backend: str = 'ems',
    hooks: Optional[Sequence[Callable]] = None,
):
    """Run the simulations of the IDFs and EPWs in the working folder, with the EnergyPlus version of each IDF.

    :param only_accim_idfs: True to run only the output IDFs of accim (those with '[' in the name), False to
        run all IDFs; None to ask.
    :param confirm: True to run the simulations without asking, False to cancel them; None to ask.
    :param processes: The number of simulations that run at the same time.
    :param energyplus_version: The EnergyPlus version of the IDFs, from '9.1' to '26.2', or 'auto' to read it
        from the IDFs; None to ask. With ``backend='api'``, the version of each IDF is used.
    :param backend: 'ems' to run the EMS programs with the EMS of EnergyPlus (through eppy), or 'api' to run
        them in Python through the API of EnergyPlus (EnergyPlus 24.2 or later), with the same results.
    :param hooks: With ``backend='api'`` (since accim 1.2.0), functions called after the EMS programs at each calling
        point of each simulation, as ``hook(controller, calling_point)`` (the ``after_programs`` of
        :func:`accim.sim.energyplus_api.run_simulation`), such as the hooks of the setpoints of the ATHB and of the SET
        (:func:`accim.sim.comfort_hooks.apply_athb_setpoints` and :func:`accim.sim.comfort_hooks.apply_set_setpoints`);
        the same hooks run in every simulation of the folder; they run in the processes of the simulations, so they
        must be objects that can be pickled (functions or instances of classes defined at the top level of a module).
    :return: With ``backend='api'``, the results of the simulations
        (:class:`accim.sim.energyplus_api.SimulationResult`); otherwise, None.
    :raises NotImplementedError: If ``hooks`` are given with ``backend='ems'``, whose EMS runs the programs in
        EnergyPlus.

    :func:`accim.run.estimate_results_size` estimates the size of the results before running them.
    """
    if backend not in BACKENDS:
        raise ValueError(f'{backend!r} is not a valid backend. Valid values: {list(BACKENDS)}.')
    if hooks and backend != 'api':
        raise NotImplementedError("hooks need run_ep(backend='api'): the EMS of EnergyPlus cannot run Python code (the "
                                  "setpoints of the ATHB, for instance).")
    if backend == 'api':
        energyplus_version = energyplus_version or 'auto'
    energyplus_version = _ask_version(energyplus_version)
    idfnames = _idf_names(only_accim_idfs)
    epwnames = sorted(x for x in os.listdir() if x.endswith('.epw'))

    print('The IDFs we are going to run are:')
    print(*idfnames, sep='\n')
    print(f' and the No. of IDFs is going to be {len(idfnames)}')
    print('The EPWs we are going to run are:')
    print(*epwnames, sep='\n')
    print(f' and the No. of EPWs is going to be {len(epwnames)}')
    print('Therefore, the simulations are going to be:')
    pairs = [(idf, epw) for idf in idfnames for epw in epwnames]
    for idf, epw in pairs:
        print(simulation_name(idf, epw))
    print(f' and the No. of simulations is going to be {len(pairs)}')

    if backend == 'api':
        if not _confirm(confirm, len(pairs)):
            return []
        from accim.sim.energyplus_api import run_simulations
        jobs = [(idf, epw, {'output_directory': os.getcwd(), 'output_prefix': simulation_name(idf, epw)})
                for idf, epw in pairs]
        if hooks:
            return run_simulations(jobs, processes=processes, after_programs=list(hooks))
        return run_simulations(jobs, processes=processes)

    if energyplus_version.lower() == 'auto':
        iddfile = get_iddfile_from_idfs(idfnames) if idfnames else None
    else:
        iddfile = idd_path(energyplus_version)
    if iddfile is not None:
        try:
            IDF.setiddname(iddfile)
        except IDDAlreadySetError:
            print('IDD was already set.')
    if not _confirm(confirm, len(pairs)):
        return None
    runs = []
    for idf, epw in pairs:
        model = IDF(idf, epw)
        runs.append((model, make_eplaunch_options(model, epw)))
    runIDFs(runs, processes)
    return None


def remove_files() -> None:
    """Delete the simulation files written by :func:`run_ep` in the working folder, except '.py', '.idf',
    '.epw', '.csv' and '.eso'.

    'Table.csv', 'Meter.csv' and 'Zsz.csv' files are deleted as well. run_ep names the simulation files
    'IDF name[EPW name', so only the files whose name contains '[' are deleted: other files and subfolders
    are kept.
    """
    extensions = ('.py', '.idf', '.epw', '.csv', '.eso')
    csv_extensions = ('Table.csv', 'Meter.csv', 'Zsz.csv')
    simulation_files = [file for file in os.listdir() if '[' in file and os.path.isfile(file)]
    for file in simulation_files:
        if not file.endswith(extensions) or file.endswith(csv_extensions):
            os.remove(file)


runEp = deprecated_alias(
    run_ep, 'accim.run.run.runEp', 'accim.run.run_ep',
    legacy_kwargs={'runOnlyAccim': 'only_accim_idfs', 'confirmRun': 'confirm', 'num_CPUs': 'processes',
                   'EnergyPlus_version': 'energyplus_version'})
removefiles = deprecated_alias(remove_files, 'accim.run.run.removefiles', 'accim.run.remove_files')
