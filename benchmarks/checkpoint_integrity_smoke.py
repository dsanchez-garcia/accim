"""Opt-in real-engine integration check using an already prepared ACCIM IDF.

Requires a model with SetAST/CustAST_m, zone BLOCK1:ZONE1 and an installed
matching EnergyPlus. Example input: the 26.2 one-day custom-model fixture in
 tests/core/test_energyplus_versions.py. A NEW output directory is mandatory.
"""

import argparse
import hashlib
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
from besos.eppy_funcs import get_building
from besos.objectives import MeterReader, VariableReader
from besos.problem import EPProblem

from accim.parametric_and_optimisation import ParametricSimulation, OptimisationSimulation
from accim.parametric_and_optimisation.parameters import accis_parameter


def session(cls, idf, weather, constrained=False):
    simulation = cls(buildings=get_building(str(idf)), epws=[str(p) for p in weather],
                     parameters_type=None, bypass_addAccis=True)
    simulation.parameters_list = [accis_parameter('CustAST_m', (0.2, 0.4))]
    simulation.sim_outputs = [MeterReader(key_name='Electricity:Facility', frequency='Hourly', name='energy')]
    simulation.problem = EPProblem(
        inputs=simulation.parameters_list, outputs=simulation.sim_outputs,
        constraints=[MeterReader(key_name='Electricity:Facility', frequency='Hourly', name='energy_bound')] if constrained else None,
        constraint_bounds=['<=1000000000000'] if constrained else None,
        add_outputs=[VariableReader(key_value='BLOCK1:ZONE1', variable_name='Zone Operative Temperature',
                                    frequency='Hourly', name='temperature_sum')],
    )
    return simulation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--idf', type=Path, required=True)
    parser.add_argument('--epw', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    idf, epw, root = args.idf.absolute(), args.epw.absolute(), args.output_dir.absolute()
    original_hashes = [hashlib.sha256(p.read_bytes()).digest() for p in (idf, epw)]
    root.mkdir(parents=True, exist_ok=False)
    weather = [root / 'A.epw', root / 'B.epw']
    for target in weather:
        shutil.copyfile(epw, target)
    reference = None
    for processes in [1, 2]:
        sim = session(ParametricSimulation, idf, weather[:1])
        out = root / f'param-{processes}'
        options = dict(out_dir=str(out), df=pd.DataFrame({'CustAST_m': [0.25, 0.35, 0.25]}),
                       processes=processes, batch_size=2, checkpoint_every_batch=True, keep_dirs=True)
        first = sim.run_parametric_simulation(**options)
        assert len(first) == 3
        numerical = first[['CustAST_m', 'energy', 'temperature_sum']].to_numpy(dtype=float)
        assert np.isfinite(numerical).all()
        if reference is None:
            reference = numerical
        else:
            np.testing.assert_allclose(numerical, reference, rtol=1e-10)
        csv_paths = sorted(out.rglob('eplusout.csv'))
        assert len(csv_paths) == 2
        resumed = session(ParametricSimulation, idf, weather[:1]).run_parametric_simulation(
            **options, resume_from_checkpoint=True)
        np.testing.assert_array_equal(resumed[['CustAST_m', 'energy', 'temperature_sum']].to_numpy(dtype=float), numerical)
        assert sorted(out.rglob('eplusout.csv')) == csv_paths
        assert len(list(out.glob('accim_run_*'))) == 1
        print(f'PASS parametric processes={processes}, duplicates/add_outputs/resume', flush=True)

    sim = session(OptimisationSimulation, idf, weather, constrained=True)
    out = root / 'optim'
    options = dict(out_dir=str(out), processes=2, evaluations=2, population_size=2,
                   checkpoint_every_case=True, keep_sim_files='all', show_progress=False)
    first = sim.run_optimisation(**options)
    assert len(first) == 4
    columns = ['CustAST_m', 'energy', 'energy_bound', 'temperature_sum']
    assert np.isfinite(first[columns].to_numpy(dtype=float)).all()
    csv_paths = sorted(out.rglob('eplusout.csv'))
    assert len(csv_paths) == 4
    resumed = session(OptimisationSimulation, idf, weather, constrained=True).run_optimisation(
        **options, resume_from_checkpoint=True)
    np.testing.assert_array_equal(resumed[columns].to_numpy(dtype=float), first[columns].to_numpy(dtype=float))
    assert resumed['pareto-optimal'].tolist() == first['pareto-optimal'].tolist()
    assert sorted(out.rglob('eplusout.csv')) == csv_paths
    assert len(list(out.glob('accim_run_*'))) == 1
    assert [hashlib.sha256(p.read_bytes()).digest() for p in (idf, epw)] == original_hashes
    print('PASS optimisation two workers/two EPWs, constraints/add_outputs/resume; inputs unchanged', flush=True)


if __name__ == '__main__':
    main()

