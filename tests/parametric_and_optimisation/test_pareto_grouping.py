import pandas as pd

from accim.parametric_and_optimisation.analysis import AnalysisMixin
from accim.parametric_and_optimisation.main import SimulationBase
from accim.parametric_and_optimisation.plotting import PlottingMixin


class _DummyProblem:
	def __init__(self, output_names, minimize_outputs=None):
		self._output_names = list(output_names)
		self.minimize_outputs = minimize_outputs

	def names(self, group):
		if group == 'outputs':
			return list(self._output_names)
		return []


class _DummyPlotOptimisation(AnalysisMixin, PlottingMixin):
	pass


def test_annotate_pareto_status_supports_idf_and_epw_grouping():
	sim = SimulationBase.__new__(SimulationBase)
	sim.problem = _DummyProblem(output_names=['Heating:Electricity'], minimize_outputs=[True])

	df = pd.DataFrame(
		{
			'Heating:Electricity': [10.0, 12.0],
			'epw': ['Seville', 'Seville'],
			'idf': ['A', 'B'],
		}
	)

	by_epw = sim._annotate_pareto_status(df.copy(), df.copy(), group_by=['epw'])
	assert bool(by_epw.loc[by_epw['idf'] == 'A', 'pareto-optimal'].iloc[0]) is True
	assert bool(by_epw.loc[by_epw['idf'] == 'B', 'pareto-optimal'].iloc[0]) is False

	by_epw_idf = sim._annotate_pareto_status(df.copy(), df.copy(), group_by=['epw', 'idf'])
	assert by_epw_idf['pareto-optimal'].tolist() == [True, True]


def test_plot_best_compromise_solutions_respects_group_options(tmp_path):
	sim = _DummyPlotOptimisation()
	sim.last_run_type = 'optimisation'
	sim.outputs_normalized = False
	sim.problem = _DummyProblem(
		output_names=['Heating:Electricity', 'Cooling:Electricity'],
		minimize_outputs=[True, True],
	)
	sim.outputs_optimisation = pd.DataFrame(
		{
			'Heating:Electricity': [10.0, 11.0, 12.0, 13.0],
			'Cooling:Electricity': [5.0, 4.0, 6.0, 3.0],
			'pareto-optimal': [True, True, True, True],
			'epw': ['Seville', 'Seville', 'Sydney', 'Sydney'],
			'idf': ['A', 'B', 'A', 'B'],
		}
	)

	grouped_all = sim.plot_best_compromise_solutions(
		out_dir=str(tmp_path),
		mcdm_configs=[{'method': 'topsis'}],
		separate_by_epw=False,
		separate_by_idf=False,
	)
	assert len(grouped_all) == 1
	assert grouped_all['mcdm_group'].tolist() == ['all']

	grouped_idf_epw = sim.plot_best_compromise_solutions(
		out_dir=str(tmp_path),
		mcdm_configs=[{'method': 'topsis'}],
		separate_by_epw=True,
		separate_by_idf=True,
	)
	assert len(grouped_idf_epw) == 4
	assert grouped_idf_epw['mcdm_group'].nunique() == 4

