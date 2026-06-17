import pandas as pd
import pytest

from accim.parametric_and_optimisation.analysis import AnalysisMixin


class _DummyProblem:
    def __init__(self, output_names, minimize_outputs=None):
        self._output_names = list(output_names)
        self.minimize_outputs = minimize_outputs

    def names(self, group):
        if group == 'outputs':
            return list(self._output_names)
        return []


class _DummyOptimisation(AnalysisMixin):
    pass


def _build_dummy_sim(df, output_names, minimize_outputs=None):
    sim = _DummyOptimisation()
    sim.last_run_type = 'optimisation'
    sim.problem = _DummyProblem(output_names=output_names, minimize_outputs=minimize_outputs)
    sim.outputs_optimisation = df
    return sim


def test_get_best_compromise_solution_resolves_normalized_outputs():
    df = pd.DataFrame(
        {
            'Heating:Electricity_kWh/m2': [4.0, 6.0],
            'Cooling:Electricity_kWh/m2': [3.0, 1.5],
            'pareto-optimal': [True, True],
            'epw': ['Seville', 'Seville'],
        }
    )
    sim = _build_dummy_sim(
        df=df,
        output_names=['Heating:Electricity', 'Cooling:Electricity'],
        minimize_outputs=[True, True],
    )

    best = sim.get_best_compromise_solution(method='topsis')

    assert len(best) == 1
    assert 'topsis_score' in best.columns
    assert 'Heating:Electricity_kWh/m2' in best.columns
    assert 'Cooling:Electricity_kWh/m2' in best.columns


def test_get_best_compromise_solution_raises_when_output_not_found():
    df = pd.DataFrame(
        {
            'Heating:Electricity_kWh/m2': [4.0, 6.0],
            'pareto-optimal': [True, True],
            'epw': ['Seville', 'Seville'],
        }
    )
    sim = _build_dummy_sim(
        df=df,
        output_names=['Heating:Electricity', 'Cooling:Electricity'],
        minimize_outputs=[True, True],
    )

    with pytest.raises(KeyError, match='Could not resolve output column'):
        sim.get_best_compromise_solution(method='knee_point')

