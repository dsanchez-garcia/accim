"""run_sensitivity_analysis_by_epw with synthetic results, without EnergyPlus.

The results of the Sobol analysis of SALib do not have the names of the parameters (those of Morris do), so
the Sobol analysis by EPW stopped with KeyError: 'names'.
"""
import numpy as np
import pandas as pd
import pytest

pytest.importorskip('SALib')

from besos.parameters import RangeParameter  # noqa: E402
from SALib.sample import morris as morris_sampler  # noqa: E402
from SALib.sample import saltelli  # noqa: E402

from accim.parametric_and_optimisation.main import ParametricSimulation  # noqa: E402

BOUNDS = {'x1': (0.0, 1.0), 'x2': (0.0, 1.0)}


class _Input:
    def __init__(self, name, low, high):
        self.name = name
        self.value_descriptors = [RangeParameter(low, high)]


class _Problem:
    def __init__(self):
        self.inputs = [_Input(name, *bounds) for (name, bounds) in BOUNDS.items()]

    def names(self, kind):
        return [i.name for i in self.inputs] if kind == 'inputs' else ['obj']


def _simulation(samples, epws):
    sim = ParametricSimulation(buildings=None, epws=list(epws), parameters_type=None, bypass_add_accis=True)
    sim.problem = _Problem()
    sim.last_run_type = 'parametric'
    frames = []
    for epw in epws:
        df = pd.DataFrame(samples, columns=list(BOUNDS))
        # x2 matters four times as much as x1
        df['obj'] = df['x1'] + 4 * df['x2']
        df['epw'] = epw
        frames.append(df)
    sim.outputs_param_simulation = pd.concat(frames, ignore_index=True)
    return sim


def _salib_problem():
    return {'num_vars': len(BOUNDS), 'names': list(BOUNDS), 'bounds': [list(b) for b in BOUNDS.values()]}


@pytest.mark.parametrize('method', ['sobol', 'morris'])
def test_sensitivity_analysis_by_epw(tmp_path, method):
    if method == 'sobol':
        samples = saltelli.sample(_salib_problem(), 64)
    else:
        samples = morris_sampler.sample(_salib_problem(), N=20, num_levels=4, seed=1)
    sim = _simulation(samples, epws=['Seville', 'Madrid'])

    results = sim.run_sensitivity_analysis_by_epw(method=method, out_dir=str(tmp_path), seed=1)

    assert set(results) == {'Seville', 'Madrid'}
    for epw in ('Seville', 'Madrid'):
        table = pd.read_csv(tmp_path / f'results_sa_{method}_{epw}.csv')
        assert list(table['parameter']) == ['x1', 'x2']
        importance = table.set_index('parameter')['ST' if method == 'sobol' else 'mu_star']
        assert importance['x2'] > importance['x1']
        assert (tmp_path / f'plot_sa_{method}_{epw}.png').exists()
    assert np.isfinite(results['Seville']['obj']['ST' if method == 'sobol' else 'mu_star']).all()
