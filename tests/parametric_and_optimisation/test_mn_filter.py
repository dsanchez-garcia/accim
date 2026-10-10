"""Tests for the m-n filter of custom adaptive models (set_mn_filter, MNFilter)."""

import os

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use('Agg')

from accim.parametric_and_optimisation.main import ParametricSimulation
from accim.parametric_and_optimisation.mn_filter import (
    _REVIEW_MODELS,
    MNFilter,
    MNFilterMapping,
    review_models,
)


def test_review_models_band():
    models = review_models()
    assert len(models) == 56
    band = MNFilter.from_data()
    assert band.slope == pytest.approx(-0.041317, abs=1e-6)
    assert band.intercept == pytest.approx(1.061322, abs=1e-6)
    # The bounds pass through the models farthest below (Li et al. [61]) and above (Ge et al. [62]).
    assert band.offset_lower == pytest.approx(0.1516, abs=1e-4)
    assert band.offset_upper == pytest.approx(0.1631, abs=1e-4)
    assert band.contains(models['m'], models['n']).all()


def test_symmetric_offset_on_grid():
    band = MNFilter.from_data(offset=0.17)
    grid = pd.DataFrame(
        [(m, n) for m in np.round(np.arange(0.0, 0.71, 0.1), 2) for n in np.arange(5.0, 22.6, 2.5)],
        columns=['m', 'n'],
    )
    inside = band.contains(grid['m'], grid['n'])
    assert inside.sum() == 26
    assert band.contains(m=0.7, n=5.0)
    assert not band.contains(m=0.7, n=22.5)
    assert not band.contains(m=0.0, n=5.0)


def test_offset_tuple_and_errors():
    band = MNFilter.from_data(offset=(0.1, 0.2))
    assert (band.offset_lower, band.offset_upper) == (0.1, 0.2)
    with pytest.raises(ValueError):
        MNFilter.from_data(offset='widest')
    with pytest.raises(ValueError):
        MNFilter.from_data(data=pd.DataFrame({'m': [0.3, 0.4]}))


def test_n_bounds_match_m_bounds():
    band = MNFilter.from_data()
    m = np.linspace(0.0, 0.7, 15)
    n_low, n_high = band.n_bounds(m)
    m_lower_at_n_low, _ = band.m_bounds(n_low)
    _, m_upper_at_n_high = band.m_bounds(n_high)
    assert np.allclose(m_lower_at_n_low, m)
    assert np.allclose(m_upper_at_n_high, m)


def test_mapping_keeps_every_candidate_inside():
    band = MNFilter.from_data()
    band.check_ranges(0.0, 0.7, 5.0, 22.5)
    mapping = MNFilterMapping(band.to_dict(), m_index=0, n_index=1, n_min=5.0, n_max=22.5)
    rng = np.random.default_rng(1)
    for m, n_raw in zip(rng.uniform(0.0, 0.7, 500), rng.uniform(5.0, 22.5, 500)):
        mapped = mapping.map_inputs([m, n_raw, 3.0])
        assert mapped[0] == m and mapped[2] == 3.0
        assert 5.0 - 1e-9 <= mapped[1] <= 22.5 + 1e-9
        assert band.contains(m, mapped[1])
    low, high = band.feasible_n_interval(0.35, 5.0, 22.5)
    assert band.map_n(0.35, 5.0, 5.0, 22.5) == pytest.approx(float(low))
    assert band.map_n(0.35, 22.5, 5.0, 22.5) == pytest.approx(float(high))
    assert band.map_n(0.35, 10.0, 5.0, 22.5) < band.map_n(0.35, 12.0, 5.0, 22.5)


def test_check_ranges_rejects_empty_band():
    band = MNFilter.from_data()
    with pytest.raises(ValueError):
        band.check_ranges(0.0, 0.7, 5.0, 8.0)


def test_sampling_plan_is_filtered():
    sim = ParametricSimulation.__new__(ParametricSimulation)
    sim.mn_filter = MNFilter.from_data()
    sim.parameters_values_df = pd.DataFrame({
        'CustAST_m': [0.31, 0.7, 0.0, 0.5],
        'CustAST_n': [17.8, 22.5, 5.0, 12.0],
        'CustAST_ASToffset': [2.0, 2.0, 2.0, 2.0],
    })
    sim._apply_mn_filter_to_samples('test')
    assert sim.parameters_values_df[['CustAST_m', 'CustAST_n']].values.tolist() == [[0.31, 17.8], [0.5, 12.0]]
    assert len(sim.mn_filter_excluded_df) == 2
    with pytest.raises(ValueError):
        sim._filter_plan_by_mn_filter(
            pd.DataFrame({'CustAST_m': [0.7], 'CustAST_n': [22.5]}), context='test',
        )


def test_review_models_ids_and_copies():
    models = review_models()
    assert models.index.name == 'id'
    assert list(models.index) == list(range(56))
    models.loc[0, 'm'] = 99.0  # Editing the copy leaves the review list unchanged.
    assert review_models().loc[0, 'm'] == pytest.approx(0.534)
    assert len(_REVIEW_MODELS) == 56
    band = MNFilter.from_data()
    assert set(band.data['origin']) == {'review'} and band.removed_data.empty


def test_drop_models_by_id_and_author():
    band = MNFilter.from_data(drop_models=[17, 'rijal et al. [78]'])
    assert sorted(band.removed_data.index) == [12, 13, 14, 17]
    assert 17 not in band.data.index and len(band.data) == 52
    # Li et al. [61] was the model farthest below the line, so the band narrows below.
    assert band.offset_lower < MNFilter.from_data().offset_lower
    expected = MNFilter.from_data(data=review_models().drop(index=[12, 13, 14, 17]))
    assert band.slope == pytest.approx(expected.slope)
    assert band.intercept == pytest.approx(expected.intercept)
    assert band.offset_lower == pytest.approx(expected.offset_lower)
    assert band.offset_upper == pytest.approx(expected.offset_upper)
    assert '4 removed' in band.source
    assert 'Models removed: 12: Rijal et al. [78]' in band.describe()
    assert MNFilter.from_data(drop_models=17).removed_data.index.tolist() == [17]
    with pytest.raises(ValueError):
        MNFilter.from_data(drop_models=[56])
    with pytest.raises(ValueError):
        MNFilter.from_data(drop_models=['Rijal et al.'])
    with pytest.raises(TypeError):
        MNFilter.from_data(drop_models=[True])


def test_add_models_formats():
    band = MNFilter.from_data(add_models=[
        {'author': 'Model A', 'year': 2024, 'mode': 'MM', 'm': 0.33, 'n': 18.8},
        (0.5, 13.0),
        ('Model C', 2025, 'NV', 0.6, 11.0),
    ])
    added = band.data[band.data['origin'] == 'added']
    assert list(added.index) == [56, 57, 58]
    assert list(added['author']) == ['Model A', 'Added model 2', 'Model C']
    assert len(band.data) == 59 and band.removed_data.empty
    m = np.r_[review_models()['m'].to_numpy(), [0.33, 0.5, 0.6]]
    n = np.r_[review_models()['n'].to_numpy(), [18.8, 13.0, 11.0]]
    slope, intercept = np.polyfit(n, m, 1)
    assert band.slope == pytest.approx(slope)
    assert band.intercept == pytest.approx(intercept)
    single = MNFilter.from_data(add_models={'m': 0.33, 'n': 18.8})
    frame = MNFilter.from_data(add_models=pd.DataFrame({'m': [0.33], 'n': [18.8]}))
    assert single.slope == pytest.approx(frame.slope)
    assert 'Models added: 56: Added model 1' in single.describe()
    assert MNFilter.from_data(add_models=[], drop_models=[]).describe() == MNFilter.from_data().describe()
    with pytest.raises(ValueError):
        MNFilter.from_data(add_models=[{'m': 0.3}])
    with pytest.raises(ValueError):
        MNFilter.from_data(add_models=[(0.3, 18.0, 2.0)])
    with pytest.raises(ValueError):
        MNFilter.from_data(add_models=[{'m': 'high', 'n': 18.0}])


def test_models_table_residuals():
    band = MNFilter.from_data(drop_models=['Ge et al. [62]'], add_models=[(0.33, 18.8)])
    table = band.models_table()
    assert len(table) == 57 and int((~table['used']).sum()) == 1
    used = table[table['used']]
    assert band.offset_lower == pytest.approx(-used['residual'].min())
    assert band.offset_upper == pytest.approx(used['residual'].max())
    # Ge et al. [62] set the upper bound; once removed, it lies above the new band.
    assert not band.contains(table.loc[23, 'm'], table.loc[23, 'n'])


def test_set_mn_filter_add_and_drop_models(tmp_path):
    sim = ParametricSimulation.__new__(ParametricSimulation)
    band = sim.set_mn_filter(drop_models=[55], add_models=[(0.33, 18.8)], verbose=False)
    assert band is sim.mn_filter
    assert band.removed_data.index.tolist() == [55]
    assert band.data.loc[56, 'origin'] == 'added'
    assert review_models().shape == (56, 5)
    path = sim.plot_mn_filter(out_dir=str(tmp_path))
    assert os.path.isfile(path)
    path_hidden = sim.plot_mn_filter(out_dir=str(tmp_path / 'hidden'), show_removed_models=False)
    assert os.path.isfile(path_hidden)
