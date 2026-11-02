"""Tests for SimulationBase.select_outputs with several IDFs.

Found by the review of 2026-10-24: with several IDFs, the outputs found by the discovery have an 'idf' column, and
select_outputs dropped the repeated requests without it, so an output available in two IDFs was only kept for the
first one; then set_output_variables_to_idf, set_output_meters_to_idf and set_output_readers, which take the rows of
each IDF, did not request it in the second IDF.
"""
import pandas as pd

from accim.parametric_and_optimisation.main import SimulationBase

AVAILABLE = {
    'meters': pd.DataFrame([{'idf': idf, 'key_name': 'Heating:Electricity', 'frequency': 'Hourly'}
                            for idf in ('model_a', 'model_b')]),
    'variables': pd.DataFrame([{'idf': idf, 'key_value': '*', 'variable_name': 'Zone Mean Air Temperature',
                                'frequency': 'Hourly'} for idf in ('model_a', 'model_b')]),
    'meta': {'source': 'testsimeplus'},
}


def test_the_outputs_of_each_idf_are_kept(monkeypatch):
    monkeypatch.setattr(SimulationBase, 'discover_available_outputs', lambda self, **kwargs: AVAILABLE)
    sim = SimulationBase.__new__(SimulationBase)

    # Each output is requested twice, so it is selected twice for each IDF
    selection = sim.select_outputs(
        meters=['Heating:Electricity'], from_df_meters=pd.DataFrame({'key_name': ['HEATING:ELECTRICITY']}),
        variables=['Zone Mean Air Temperature'],
        from_df_vars=pd.DataFrame({'key_value': ['*'], 'variable_name': ['Zone Mean Air Temperature']}),
        on_missing='raise', suggest=False)

    assert selection['meters'][['idf', 'key_name']].values.tolist() == [['model_a', 'Heating:Electricity'],
                                                                        ['model_b', 'Heating:Electricity']]
    assert selection['variables']['idf'].tolist() == ['model_a', 'model_b']
    assert selection['report']['selected_counts'] == {'meters': 2, 'variables': 2}


def test_without_idf_column_the_repeated_outputs_are_dropped(monkeypatch):
    # One IDF: the discovery gives no 'idf' column
    available = {name: df.drop(columns='idf') if name != 'meta' else df for name, df in AVAILABLE.items()}
    monkeypatch.setattr(SimulationBase, 'discover_available_outputs', lambda self, **kwargs: available)
    sim = SimulationBase.__new__(SimulationBase)

    selection = sim.select_outputs(meters=['Heating:Electricity'], variables=['Zone Mean Air Temperature'],
                                   on_missing='raise', suggest=False)

    assert len(selection['meters']) == len(selection['variables']) == 1
