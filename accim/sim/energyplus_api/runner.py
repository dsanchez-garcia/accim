# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Run simulations with the Python API of EnergyPlus, which runs the EMS programs of the models in Python."""

import multiprocessing
import os
import shutil
import tempfile
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from accim.energyplus import read_idf_version
from accim.sim.energyplus_api.controller import ErlController, Hook
from accim.sim.energyplus_api.idf import prepare_for_api
from accim.sim.energyplus_api.runtime import load_energyplus_api

__all__ = ['SimulationResult', 'run_simulation', 'run_simulations']

PathLike = Union[str, os.PathLike]


@dataclass
class SimulationResult:
    """The result of a simulation.

    :ivar idf: The path of the IDF.
    :ivar epw: The path of the EPW (None for design days only).
    :ivar output_directory: The folder of the output files.
    :ivar output_prefix: The prefix of the output files.
    :ivar exit_code: The exit code of EnergyPlus (0 if the simulation ended without fatal errors).
    :ivar environments: The number of environments (sizing periods and run periods) simulated.
    :ivar error: The error that stopped the simulation, as text, if any.
    """

    idf: str
    epw: Optional[str]
    output_directory: str
    output_prefix: str
    exit_code: int
    environments: int = 0
    error: Optional[str] = None
    output_suffix: str = 'C'

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and self.error is None

    @property
    def err_file(self) -> str:
        """The path of the .err file of EnergyPlus."""
        name = {'L': f'{self.output_prefix}out.err', 'D': f'{self.output_prefix}-out.err'}.get(
            self.output_suffix.upper(), f'{self.output_prefix}.err')
        return os.path.join(self.output_directory, name)


def run_simulation(
    idf: PathLike,
    epw: Optional[PathLike] = None,
    output_directory: Optional[PathLike] = None,
    output_prefix: Optional[str] = None,
    output_suffix: str = 'C',
    readvars: bool = True,
    expand_objects: bool = True,
    annual: bool = False,
    design_day: bool = False,
    before_programs: Sequence[Hook] = (),
    after_programs: Sequence[Hook] = (),
    verbose: bool = False,
    raise_errors: bool = True,
) -> SimulationResult:
    """Run a simulation with the Python API of EnergyPlus, which runs the EMS programs of the model in Python.

    The model is run without its EMS programs, program calling managers and actuators: the programs run
    in the callbacks of the API, with the rules of the EMS of EnergyPlus, so the results are those of the
    EMS. The other objects of the model (and the IDF file) do not change. The EnergyPlus version is that
    of the model, which must be 24.2 or later (:data:`~accim.sim.energyplus_api.runtime.MINIMUM_API_VERSION`).
    eppy reads the model with the IDD of its version (see :func:`accim.sim.accis.load_idf`), so in a Python session
    this function can only run the models of one EnergyPlus version (:func:`run_simulations` runs each simulation in
    its own process).

    :param idf: The path of the IDF.
    :param epw: The path of the EPW (None to simulate the design days only).
    :param output_directory: The folder of the output files (by default, that of the IDF).
    :param output_prefix: The prefix of the output files (by default, the name of the IDF).
    :param output_suffix: The style of the names of the output files: 'C' (prefix.csv, prefixMeter.csv...),
        'L' (prefixout.csv...) or 'D' (prefix-out.csv...).
    :param readvars: True to write the CSV files of the outputs.
    :param expand_objects: True to expand the HVACTemplate objects (ExpandObjects).
    :param annual: True to simulate the whole weather file.
    :param design_day: True to simulate the design days only.
    :param before_programs: Functions called at each calling point before the EMS programs, as
        ``hook(controller, calling_point)``; :class:`~accim.sim.energyplus_api.controller.ErlController`
        gives access to the variables of the programs.
    :param after_programs: Functions called at each calling point after the EMS programs, before the
        actuators are set.
    :param verbose: True to print the messages of EnergyPlus.
    :param raise_errors: True to raise an error if the EMS programs fail or EnergyPlus ends with a fatal
        error; False to return it in the result.
    :raises RuntimeError: If the simulation fails and ``raise_errors`` is True.
    """
    from accim.sim.accis import load_idf

    idf = Path(idf).resolve()
    version = read_idf_version(idf)
    api = load_energyplus_api(version)
    model = load_idf(idf, version)
    ems = prepare_for_api(model)
    controller = ErlController(ems, before_programs=before_programs, after_programs=after_programs)
    output_directory = Path(output_directory).resolve() if output_directory is not None else idf.parent
    output_directory.mkdir(parents=True, exist_ok=True)
    output_prefix = output_prefix if output_prefix is not None else idf.stem

    with tempfile.TemporaryDirectory(prefix='accim_api_') as folder:
        # Each simulation runs in its own folder (ExpandObjects and ReadVarsESO write files with fixed names
        # there), and then its output files are moved to the output directory
        model_file = Path(folder) / 'model' / 'in.idf'
        model_file.parent.mkdir()
        model.saveas(str(model_file))
        run_folder = Path(folder) / 'output'
        run_folder.mkdir()
        args = ['-d', str(run_folder), '-p', output_prefix, '-s', output_suffix]
        if readvars:
            args.append('-r')
        if expand_objects:
            args.append('-x')
        if annual:
            args.append('-a')
        if design_day:
            args.append('-D')
        if epw is not None:
            args += ['-w', str(Path(epw).resolve())]
        args.append(str(model_file))
        state = api.state_manager.new_state()
        working_directory = os.getcwd()
        try:
            if not verbose and hasattr(api.runtime, 'set_console_output_status'):
                api.runtime.set_console_output_status(state, False)
            controller.register(api, state)
            # Some programs of EnergyPlus also write files with fixed names in the working directory
            os.chdir(run_folder)
            exit_code = api.runtime.run_energyplus(state, args)
        finally:
            os.chdir(working_directory)
            api.state_manager.delete_state(state)
        for file in run_folder.iterdir():
            if file.is_file():
                shutil.move(str(file), str(output_directory / file.name))

    result = SimulationResult(str(idf), None if epw is None else str(Path(epw).resolve()), str(output_directory),
                              output_prefix, exit_code, controller.environments, output_suffix=output_suffix)
    if controller.error is not None:
        result.error = f'{type(controller.error).__name__}: {controller.error}'
        if raise_errors:
            raise RuntimeError(f'The EMS programs of {idf.name} failed in the Python API backend: '
                               f'{result.error}') from controller.error
    elif exit_code != 0:
        result.error = f'EnergyPlus ended with exit code {exit_code}; see {result.err_file}'
        if raise_errors:
            raise RuntimeError(f'The simulation of {idf.name} failed: {result.error}')
    return result


def _run_job(job: Tuple[str, Optional[str], Mapping]) -> SimulationResult:
    idf, epw, kwargs = job
    try:
        return run_simulation(idf, epw, raise_errors=False, **kwargs)
    except Exception as error:  # noqa: BLE001 (the error is returned with the result)
        return SimulationResult(str(idf), epw, str(kwargs.get('output_directory') or Path(idf).parent),
                                str(kwargs.get('output_prefix') or Path(idf).stem), -1,
                                error=f'{type(error).__name__}: {error}')


def run_simulations(
    jobs: Iterable[Union[Tuple[PathLike, Optional[PathLike]], Tuple[PathLike, Optional[PathLike], Mapping]]],
    processes: int = 2,
    **kwargs,
) -> List[SimulationResult]:
    """Run simulations with the Python API of EnergyPlus, each one in its own process.

    :param jobs: (IDF, EPW) or (IDF, EPW, arguments of :func:`run_simulation`) of each simulation.
    :param processes: The number of simulations that run at the same time.
    :param kwargs: Arguments of :func:`run_simulation` for all the simulations (the hooks must be functions
        defined at the top level of a module, so that they can be sent to the processes).
    :return: The results, in the order of the jobs. The simulations that fail have an ``error``.
    """
    prepared = []
    for job in jobs:
        idf, epw = str(job[0]), (None if job[1] is None else str(job[1]))
        arguments = dict(kwargs)
        if len(job) > 2:
            arguments.update(job[2])
        prepared.append((idf, epw, arguments))
    if not prepared:
        return []
    context = multiprocessing.get_context('spawn')
    try:
        # A new process for each simulation, since a process can only load the API of one EnergyPlus version
        executor = ProcessPoolExecutor(max_workers=processes, mp_context=context, max_tasks_per_child=1)
    except TypeError:  # Python 3.10 and earlier
        executor = ProcessPoolExecutor(max_workers=processes, mp_context=context)
    with executor:
        results = list(executor.map(_run_job, prepared))
    failed = [r for r in results if not r.success]
    if failed:
        warnings.warn(f'{len(failed)} of {len(results)} simulations failed: '
                      + '; '.join(f'{Path(r.idf).name}: {r.error}' for r in failed[:5]), RuntimeWarning, stacklevel=2)
    return results
