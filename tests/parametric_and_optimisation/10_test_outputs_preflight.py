"""
10_test_outputs_preflight.py

Tests del flujo de outputs preflight:
- discover_available_outputs: obtiene outputs reales disponibles (test-sim)
- select_outputs: valida wishlist, detecta missing, sugiere alternativas
- apply_outputs_preflight: limpia outputs (mode='all') y deja el IDF con lo seleccionado
"""

import pytest
import pandas as pd
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

    available_outputs = sim.discover_available_outputs(reduce_sim_time=True, prefer='testsimeplus')
    df_meters_av = available_outputs['meters']
    df_vars_av = available_outputs['variables']
    meta = available_outputs['meta']
    assert meta.get('source') in {'testsimeplus', 'rdd_mdd'}
    assert 'key_name' in df_meters_av.columns
    assert 'variable_name' in df_vars_av.columns
    assert len(df_vars_av) > 0

    real_var_name = str(df_vars_av.iloc[0]['variable_name'])

    with pytest.warns(UserWarning):
        selection = sim.select_outputs(
            meters=['Heating:Electricity', 'Heatng:Electricity'],  # typo on purpose
            variables=[real_var_name, 'Definitely Not A Real Variable Name'],
            on_missing='warn',
            suggest=True,
            reduce_sim_time=True,
        )
        df_meters_sel = selection['meters']
        df_vars_sel = selection['variables']
        report = selection['report']

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
    available_outputs = sim.discover_available_outputs(reduce_sim_time=True, prefer='testsimeplus')
    df_vars_av = available_outputs['variables']
    var_name = str(df_vars_av.iloc[0]['variable_name'])

    selection = sim.select_outputs(
        meters=['Heating:Electricity'],
        variables=[var_name],
        on_missing='raise',
        suggest=False,
        reduce_sim_time=True,
    )
    df_meters_sel = selection['meters']
    df_vars_sel = selection['variables']

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


def test_keep_only_outputs_in_idfs_filters_all_buildings():
    ts.print_section("TEST: Outputs preflight - keep only selected outputs in all IDFs")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:1],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    sim.clear_outputs(mode='meters_vars', idf_scope='all')
    for building in buildings:
        building.newidfobject(
            'OUTPUT:VARIABLE',
            Key_Value='*',
            Variable_Name='Zone Air Temperature',
            Reporting_Frequency='Hourly',
            Schedule_Name='',
        )
        building.newidfobject(
            'OUTPUT:VARIABLE',
            Key_Value='*',
            Variable_Name='Site Outdoor Air Drybulb Temperature',
            Reporting_Frequency='Hourly',
            Schedule_Name='',
        )
        building.newidfobject('OUTPUT:METER', Key_Name='Heating:Electricity', Reporting_Frequency='Hourly')
        building.newidfobject('OUTPUT:METER', Key_Name='Cooling:Electricity', Reporting_Frequency='Hourly')

    report = sim.keep_only_outputs_in_idfs(
        output_meters=['Heating:Electricity'],
        output_variables=[('*', 'Zone Air Temperature')],
        idf_scope='all',
    )

    assert len(report['buildings']) == 2
    for building in buildings:
        meters = [obj.Key_Name for obj in building.idfobjects['Output:Meter']]
        variables = [obj.Variable_Name for obj in building.idfobjects['Output:Variable']]
        assert meters == ['Heating:Electricity']
        assert variables == ['Zone Air Temperature']


def test_set_output_meters_to_idf_mode_replace_replaces_existing_meters():
    ts.print_section("TEST: set_output_meters_to_idf mode='replace'")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:1],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    sim.clear_outputs(mode='meters_vars', idf_scope='all')
    for building in buildings:
        building.newidfobject('OUTPUT:METER', Key_Name='Heating:Electricity', Reporting_Frequency='Hourly')
        building.newidfobject('OUTPUT:METER', Key_Name='Cooling:Electricity', Reporting_Frequency='Hourly')

    df_output_meter = pd.DataFrame([
        {'key_name': 'DistrictHeating:Facility', 'frequency': 'Hourly'},
        {'key_name': 'DistrictCooling:Facility', 'frequency': 'Hourly'},
    ])

    sim.set_output_meters_to_idf(
        df_output_meter=df_output_meter,
        validate=False,
        idf_scope='all',
        mode='replace',
    )

    expected_names = ['DISTRICTCOOLING:FACILITY', 'DISTRICTHEATING:FACILITY']
    for building in buildings:
        meters = list(building.idfobjects['Output:Meter'])
        assert sorted([obj.Key_Name.upper() for obj in meters]) == expected_names
        assert all(str(obj.Reporting_Frequency).lower() == 'hourly' for obj in meters)


def test_output_scope_first_modifies_only_first_idf():
    ts.print_section("TEST: Outputs preflight - idf_scope='first'")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:1],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    sim.clear_outputs(mode='meters_vars', idf_scope='all')
    for building in buildings:
        building.newidfobject('OUTPUT:METER', Key_Name='Heating:Electricity', Reporting_Frequency='Hourly')

    sim.clear_outputs(mode='meters_vars', idf_scope='first')

    assert len(buildings[0].idfobjects['Output:Meter']) == 0
    assert len(buildings[1].idfobjects['Output:Meter']) == 1

