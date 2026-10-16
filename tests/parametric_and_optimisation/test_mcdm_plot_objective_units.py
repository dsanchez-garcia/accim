"""Tests for the units of the objectives in plot_best_compromise_solutions.

Only energy objectives are converted to kWh (or kWh/m2) and labelled with that unit. Before, the
second objective was labelled kWh/m2, or divided by 3.6e6 and labelled kWh, even when it was a
temperature.
"""
import re

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use('Agg')

from accim.parametric_and_optimisation.main import OptimisationSimulation

TEMPERATURE = 'Annual mean operative temperature LIVING'


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._inputs = list(inputs)
        self._outputs = list(outputs)
        self.minimize_outputs = [True] * len(self._outputs)

    def names(self, typ):
        if typ == 'inputs':
            return list(self._inputs)
        if typ == 'outputs':
            return list(self._outputs)
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _optimisation_with_energy_and_temperature_objectives():
    sim = OptimisationSimulation(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.last_run_type = 'optimisation'
    sim.building_floor_area = 100.0
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Electricity:HVAC', TEMPERATURE])
    sim.outputs_optimisation = pd.DataFrame({
        'x': [0.1, 0.5, 0.9],
        'Electricity:HVAC': [3.6e9, 7.2e9, 10.8e9],
        TEMPERATURE: [26.5, 25.0, 24.0],
        'pareto-optimal': [True, True, True],
        'epw': ['Seville'] * 3,
    })
    return sim


def _capture_subplots(monkeypatch):
    figures = []
    original_subplots = plt.subplots

    def _subplots(*args, **kwargs):
        (fig, axes) = original_subplots(*args, **kwargs)
        figures.append(fig)
        return (fig, axes)

    monkeypatch.setattr(plt, 'subplots', _subplots)
    return figures


def _printed_temperature(out):
    line = next(line for line in out.splitlines() if line.strip().startswith('topsis'))
    return re.search(re.escape(TEMPERATURE) + r'=(.*)$', line.rstrip()).group(1)


def test_mcdm_plot_keeps_the_values_and_label_of_a_temperature_objective(monkeypatch, tmp_path, capsys):
    sim = _optimisation_with_energy_and_temperature_objectives()
    figures = _capture_subplots(monkeypatch)

    sim.plot_best_compromise_solutions(out_dir=str(tmp_path), mcdm_configs=[{'method': 'topsis'}])

    ax = figures[0].axes[0]
    pareto_points = ax.collections[1].get_offsets()
    assert sorted(pareto_points[:, 0].tolist()) == [1000.0, 2000.0, 3000.0]
    assert sorted(pareto_points[:, 1].tolist()) == [24.0, 25.0, 26.5]
    assert ax.get_xlabel() == 'Electricity:HVAC (kWh)'
    assert ax.get_ylabel() == TEMPERATURE
    assert _printed_temperature(capsys.readouterr().out) in {'24.0', '25.0', '26.5'}


def test_mcdm_plot_per_m2_only_converts_the_energy_objective(monkeypatch, tmp_path, capsys):
    sim = _optimisation_with_energy_and_temperature_objectives()
    figures = _capture_subplots(monkeypatch)

    sim.plot_best_compromise_solutions(
        out_dir=str(tmp_path), mcdm_configs=[{'method': 'topsis'}], normalize_per_m2=True,
    )

    ax = figures[0].axes[0]
    pareto_points = ax.collections[1].get_offsets()
    assert sorted(pareto_points[:, 0].tolist()) == [10.0, 20.0, 30.0]
    assert sorted(pareto_points[:, 1].tolist()) == [24.0, 25.0, 26.5]
    assert ax.get_xlabel() == 'Electricity:HVAC (kWh/m2)'
    assert ax.get_ylabel() == TEMPERATURE
    assert _printed_temperature(capsys.readouterr().out) in {'24.0', '25.0', '26.5'}


def test_mcdm_plot_of_normalised_results_keeps_the_temperature_label(monkeypatch, tmp_path):
    sim = _optimisation_with_energy_and_temperature_objectives()
    sim.normalize_outputs(df_types=['optimisation'])
    figures = _capture_subplots(monkeypatch)

    sim.plot_best_compromise_solutions(out_dir=str(tmp_path), mcdm_configs=[{'method': 'topsis'}])

    ax = figures[0].axes[0]
    pareto_points = ax.collections[1].get_offsets()
    assert sorted(pareto_points[:, 0].tolist()) == [10.0, 20.0, 30.0]
    assert sorted(pareto_points[:, 1].tolist()) == [24.0, 25.0, 26.5]
    assert ax.get_xlabel() == 'Electricity:HVAC_kWh/m2 (kWh/m2)'
    assert ax.get_ylabel() == TEMPERATURE
