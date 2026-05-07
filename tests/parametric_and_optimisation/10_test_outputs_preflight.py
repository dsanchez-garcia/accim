"""
10_test_outputs_preflight.py

Tests del flujo de outputs preflight:
- discover_available_outputs: obtiene outputs reales disponibles (test-sim)
- select_outputs: valida wishlist, detecta missing, sugiere alternativas
- apply_outputs_preflight: limpia outputs (mode='all') y deja el IDF con lo seleccionado
"""

import pytest
from .. import test_setup as ts


def test_outputs_preflight_discover_and_select_with_suggestions():
    ts.print_section("TEST: Outputs preflight - discover + select (suggestions)")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['monthly'],
        verbosemode=False,
    )

    df_meters_av, df_vars_av, meta = sim.discover_available_outputs(reduce_sim_time=True, prefer='testsimeplus')
    assert meta.get('source') in {'testsimeplus', 'rdd_mdd'}
    assert 'key_name' in df_meters_av.columns
    assert 'variable_name' in df_vars_av.columns
    assert len(df_vars_av) > 0

    real_var_name = str(df_vars_av.iloc[0]['variable_name'])

    with pytest.warns(UserWarning):
        df_meters_sel, df_vars_sel, report = sim.select_outputs(
            meters=['Heating:Electricity', 'Heatng:Electricity'],  # typo on purpose
            variables=[real_var_name, 'Definitely Not A Real Variable Name'],
            on_missing='warn',
            suggest=True,
            reduce_sim_time=True,
        )

    assert isinstance(report, dict)
    assert 'missing' in report
    # Meter discovery may be empty depending on EnergyPlus/run_building behaviour;
    # only assert meter-missing detection when meters are available to validate against.
    if len(df_meters_av) > 0:
        assert any('HEATNG' in str(m).upper() for m in report['missing']['meters'])
    assert len(df_vars_sel) >= 1
    assert 'schedule_name' in df_vars_sel.columns  # normalized for apply step


def test_apply_outputs_preflight_cleans_all_and_applies_selection():
    ts.print_section("TEST: Outputs preflight - clean_mode='all' + apply")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['monthly'],
        verbosemode=False,
    )

    # Discover once to pick a known-valid variable name.
    _, df_vars_av, _ = sim.discover_available_outputs(reduce_sim_time=True, prefer='testsimeplus')
    var_name = str(df_vars_av.iloc[0]['variable_name'])

    df_meters_sel, df_vars_sel, _ = sim.select_outputs(
        meters=['Heating:Electricity'],
        variables=[var_name],
        on_missing='raise',
        suggest=False,
        reduce_sim_time=True,
    )

    # Add extra output objects to ensure cleaning is effective.
    b = sim.building
    b.newidfobject('OUTPUT:SQLITE', Option_Type='Simple')
    b.newidfobject('OUTPUTCONTROL:FILES', Output_CSV='Yes')
    assert len(b.idfobjects.get('OUTPUT:SQLITE', [])) == 1

    # Apply preflight with full clean
    report = sim.apply_outputs_preflight(
        df_vars_sel=df_vars_sel.head(1),
        df_meters_sel=df_meters_sel.head(1),
        clean_mode='all',
        validate_before_apply=False,   # keep this test fast (no extra test-sim here)
        validate_after_apply=True,
        on_missing='raise',
    )

    # Ensure extra output objects were removed by clean_mode='all',
    # except OUTPUTCONTROL:FILES which must always be preserved.
    assert len(b.idfobjects.get('OUTPUT:SQLITE', [])) == 0
    assert len(b.idfobjects.get('OUTPUTCONTROL:FILES', [])) >= 1

    # Ensure IDF outputs match the selection (best-effort verification in report)
    assert report['verification']['meters']['missing_in_idf'] == []
    assert report['verification']['vars']['missing_in_idf'] == []

