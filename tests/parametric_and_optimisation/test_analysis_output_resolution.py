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


def _two_climate_fronts():
    # The Sydney front is 100 times larger: chosen together, both choices would fall in Seville.
    return pd.DataFrame(
        {
            'Heating:Electricity': [1.0, 4.0, 10.0, 100.0, 400.0, 1000.0],
            'Cooling:Electricity': [10.0, 4.0, 1.0, 1000.0, 400.0, 100.0],
            'pareto-optimal': [True] * 6,
            'epw': ['Seville'] * 3 + ['Sydney'] * 3,
        }
    )


@pytest.mark.parametrize('method', ['knee_point', 'topsis'])
def test_best_compromise_solution_is_chosen_in_the_front_of_each_epw(method):
    sim = _build_dummy_sim(
        df=_two_climate_fronts(),
        output_names=['Heating:Electricity', 'Cooling:Electricity'],
        minimize_outputs=[True, True],
    )

    best = sim.get_best_compromise_solution(method=method)

    assert best['epw'].tolist() == ['Seville', 'Sydney']
    assert best['Heating:Electricity'].tolist() == [4.0, 400.0]
    assert best.index.tolist() == [1, 4]


def test_best_compromise_solution_over_one_front_when_epws_are_not_separated():
    df = _two_climate_fronts()
    sim = _build_dummy_sim(
        df=df,
        output_names=['Heating:Electricity', 'Cooling:Electricity'],
        minimize_outputs=[True, True],
    )

    assert len(sim.get_best_compromise_solution(method='knee_point', separate_by_epw=False)) == 1

    df.attrs['pareto_separate_by_epw'] = False
    assert len(sim.get_best_compromise_solution(method='knee_point')) == 1


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

