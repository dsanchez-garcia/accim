"""
10_test_outputs_preflight.py

Tests del flujo de outputs preflight:
- discover_available_outputs: obtiene outputs reales disponibles (test-sim)
- select_outputs: valida wishlist, detecta missing, sugiere alternativas
- apply_outputs_preflight: limpia outputs (mode='all') y deja el IDF con lo seleccionado
"""

import inspect
import os

import pytest
import pandas as pd
from accim.parametric_and_optimisation import main as main_module
from .. import test_setup as ts


def _idfobjects_get_case(building, key):
    objects = list(getattr(building, 'idfobjects', {}).get(key, []))
    if len(objects) == 0:
        objects = list(getattr(building, 'idfobjects', {}).get(str(key).upper(), []))
    if len(objects) == 0:
        objects = list(getattr(building, 'idfobjects', {}).get(str(key).title(), []))
    if len(objects) == 0:
        objects = list(getattr(building, 'idfobjects', {}).get(str(key).lower(), []))
    return objects


def _remove_idfobjects_case(building, key):
    for obj in list(_idfobjects_get_case(building, key)):
        building.removeidfobject(obj)


def _write_minimal_rdd_mdd(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'eplusout.rdd'), 'w', encoding='utf-8') as rdd_file:
        rdd_file.write('Program Version,EnergyPlus\n')
        rdd_file.write('Var Type (reported time step),Var Report Type\n')
        rdd_file.write('Output:Variable,*,Zone Mean Air Temperature,hourly,[C]\n')
        rdd_file.write('Output:Variable,*,Site Outdoor Air Drybulb Temperature,hourly,[C]\n')

    with open(os.path.join(out_dir, 'eplusout.mdd'), 'w', encoding='utf-8') as mdd_file:
        mdd_file.write('Program Version,EnergyPlus\n')
        mdd_file.write('Var Type (reported time step),Meter Report Type\n')
        mdd_file.write('Output:Meter,Heating:Electricity,hourly,[J]\n')


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


def test_simulationbase_init_forwards_explicit_addaccis_kwargs(monkeypatch):
    ts.print_section('TEST: addAccis passthrough explícito (eer/cop)')

    captured_calls = []

    def fake_addaccis(**kwargs):
        captured_calls.append(kwargs)

    monkeypatch.setattr(main_module.accis, 'addAccis', fake_addaccis)

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim custom model',
        bypass_addAccis=False,
        verbosemode=False,
        eer=4.42,
        cop=4.95,
    )

    assert len(captured_calls) == 1
    assert captured_calls[0]['eer'] == pytest.approx(4.42)
    assert captured_calls[0]['cop'] == pytest.approx(4.95)


def test_simulationbase_init_forwards_addaccis_defaults(monkeypatch):
    ts.print_section('TEST: addAccis passthrough defaults')

    captured_calls = []
    addaccis_sig = inspect.signature(main_module.accis.addAccis)

    def fake_addaccis(**kwargs):
        captured_calls.append(kwargs)

    monkeypatch.setattr(main_module.accis, 'addAccis', fake_addaccis)

    replicated = [
        'Output_take_dataframe',
        'EnergyPlus_version',
        'VRFschedule',
        'eer',
        'cop',
        'hvac_zone_map',
    ]

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type='accim custom model',
        bypass_addAccis=False,
        verbosemode=False,
    )

    assert len(captured_calls) == 1
    for param_name in replicated:
        assert captured_calls[0][param_name] == addaccis_sig.parameters[param_name].default


def test_simulationbase_addaccis_default_sync_contract():
    ts.print_section('TEST: sincronización de defaults SimulationBase vs addAccis')

    replicated = [
        'Output_take_dataframe',
        'EnergyPlus_version',
        'VRFschedule',
        'eer',
        'cop',
        'hvac_zone_map',
    ]
    base_sig = inspect.signature(main_module.SimulationBase.__init__)
    addaccis_sig = inspect.signature(main_module.accis.addAccis)

    mismatches = []
    for param_name in replicated:
        if base_sig.parameters[param_name].default != addaccis_sig.parameters[param_name].default:
            mismatches.append(
                f"{param_name}: SimulationBase={base_sig.parameters[param_name].default!r}, "
                f"addAccis={addaccis_sig.parameters[param_name].default!r}"
            )

    assert not mismatches, (
        'Los defaults replicados en SimulationBase.__init__ no están sincronizados con addAccis:\n'
        + '\n'.join(mismatches)
    )


def test_discover_available_outputs_rdd_mdd_uses_existing_files_without_simulation(monkeypatch, tmp_path):
    ts.print_section("TEST: discover_available_outputs rdd_mdd usa RDD/MDD existentes")

    monkeypatch.chdir(tmp_path)
    _write_minimal_rdd_mdd(tmp_path / 'available_outputs')

    run_calls = []

    def fake_run_building(*args, **kwargs):
        run_calls.append((args, kwargs))

    monkeypatch.setattr('besos.eplus_funcs.run_building', fake_run_building)

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        verbosemode=False,
    )

    discovered = sim.discover_available_outputs(prefer='rdd_mdd', refresh=False)

    assert len(run_calls) == 0
    assert list(discovered['meters'].columns) == ['key_name', 'frequency']
    assert list(discovered['variables'].columns) == ['key_value', 'variable_name', 'frequency']
    assert discovered['meta']['source'] == 'rdd_mdd'


def test_discover_available_outputs_rdd_mdd_generates_and_caches_without_testsimeplus(monkeypatch, tmp_path):
    ts.print_section("TEST: discover_available_outputs rdd_mdd genera RDD/MDD sin ESO/testsimeplus")

    monkeypatch.chdir(tmp_path)

    call_counter = {
        'runner': 0,
        'print_available_outputs_mod': 0,
        'read_eso_using_readvarseso': 0,
    }

    def fake_run_building(*args, **kwargs):
        call_counter['runner'] += 1
        _write_minimal_rdd_mdd(kwargs['out_dir'])
        return {}

    def fail_print_available_outputs(*args, **kwargs):
        call_counter['print_available_outputs_mod'] += 1
        raise AssertionError('print_available_outputs_mod no debe llamarse con prefer=\'rdd_mdd\'.')

    def fail_read_eso(*args, **kwargs):
        call_counter['read_eso_using_readvarseso'] += 1
        raise AssertionError('No se debe parsear eplusout.eso con prefer=\'rdd_mdd\'.')

    monkeypatch.setattr('besos.eplus_funcs.run_building', fake_run_building)
    monkeypatch.setattr(main_module, 'print_available_outputs_mod', fail_print_available_outputs)
    monkeypatch.setattr(main_module, 'read_eso_using_readvarseso', fail_read_eso)

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        verbosemode=False,
    )

    discovered = sim.discover_available_outputs(
        prefer='rdd_mdd',
        refresh=True,
        keep_available_outputs=False,
    )

    assert call_counter['runner'] == 1
    assert call_counter['print_available_outputs_mod'] == 0
    assert call_counter['read_eso_using_readvarseso'] == 0
    assert discovered['meta']['source'] == 'rdd_mdd_testsim'
    assert not os.path.exists('available_outputs')

    sim.set_output_meters_to_idf(
        output_meters=['Heating:Electricity'],
        validate=True,
        on_missing='raise',
        auto_filter=True,
        reduce_sim_time=True,
    )

    assert call_counter['runner'] == 1
    assert call_counter['print_available_outputs_mod'] == 0


def test_discover_available_outputs_default_prefer_still_uses_testsimeplus(monkeypatch):
    ts.print_section("TEST: discover_available_outputs mantiene testsimeplus por defecto")

    calls = []

    def fake_get_outputs_df_from_testsim(self, reduce_sim_time=True, idf_scope='all', keep_available_outputs=False):
        calls.append(
            {
                'reduce_sim_time': reduce_sim_time,
                'idf_scope': idf_scope,
                'keep_available_outputs': keep_available_outputs,
            }
        )
        return {
            'meters': pd.DataFrame(columns=['key_name', 'frequency']),
            'variables': pd.DataFrame(columns=['key_value', 'variable_name', 'frequency']),
        }

    monkeypatch.setattr(main_module.SimulationBase, 'get_outputs_df_from_testsim', fake_get_outputs_df_from_testsim)

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        verbosemode=False,
    )

    discovered = sim.discover_available_outputs()

    assert len(calls) == 1
    assert discovered['meta']['requested_prefer'] == 'testsimeplus'
    assert discovered['meta']['source'] == 'testsimeplus'


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


def test_set_output_variables_to_idf_signature_exposes_validation_arguments():
    ts.print_section("TEST: firma set_output_variables_to_idf expone argumentos de validacion")

    signature = inspect.signature(main_module.SimulationBase.set_output_variables_to_idf)
    for expected in [
        'validate',
        'on_missing',
        'auto_filter',
        'reduce_sim_time',
        'validation_idf_scope',
        'keep_available_outputs',
    ]:
        assert expected in signature.parameters


def test_set_output_variables_to_idf_validate_autofilter_skips_missing(monkeypatch):
    ts.print_section("TEST: set_output_variables_to_idf validate + auto_filter")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:1],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    sim.clear_outputs(mode='meters_vars', idf_scope='all')

    discover_calls = []
    available_rows = []
    for idx, building in enumerate(buildings):
        available_rows.append(
            {
                'idf': sim._get_idf_identifier(building, idx),
                'key_value': '*',
                'variable_name': 'Zone Mean Air Temperature',
                'frequency': 'Hourly',
            }
        )

    def fake_discover(self, reduce_sim_time=True, prefer='testsimeplus', refresh=False, idf_scope='all', keep_available_outputs=False):
        discover_calls.append(
            {
                'reduce_sim_time': reduce_sim_time,
                'prefer': prefer,
                'refresh': refresh,
                'idf_scope': idf_scope,
                'keep_available_outputs': keep_available_outputs,
            }
        )
        return {
            'meters': pd.DataFrame(columns=['key_name', 'frequency']),
            'variables': pd.DataFrame(available_rows),
            'meta': {'source': 'testsimeplus'},
        }

    monkeypatch.setattr(main_module.SimulationBase, 'discover_available_outputs', fake_discover)

    with pytest.warns(UserWarning, match='Output:Variable'):
        sim.set_output_variables_to_idf(
            output_variables=[
                {'key_value': '*', 'variable_name': 'Zone Mean Air Temperature', 'frequency': 'Hourly'},
                {'key_value': '*', 'variable_name': 'Definitely Missing Variable', 'frequency': 'Hourly'},
            ],
            validate=True,
            on_missing='warn',
            auto_filter=True,
            reduce_sim_time=False,
            idf_scope='all',
            validation_idf_scope='all',
            mode='replace',
        )

    assert len(discover_calls) == 1
    assert discover_calls[0]['prefer'] == 'testsimeplus'
    assert discover_calls[0]['idf_scope'] == 'all'

    for building in buildings:
        variables = _idfobjects_get_case(building, 'Output:Variable')
        assert len(variables) == 1
        assert str(variables[0].Variable_Name) == 'Zone Mean Air Temperature'
        assert str(variables[0].Reporting_Frequency).lower() == 'hourly'


@pytest.mark.parametrize('sim_cls', [ts.ParametricSimulation, ts.OptimisationSimulation])
@pytest.mark.parametrize('precreate_outputcontrol', [False, True])
def test_simulation_init_ensures_outputcontrol_files(sim_cls, precreate_outputcontrol):
    ts.print_section("TEST: constructor ensures OutputControl:Files")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    building = buildings[0]
    _remove_idfobjects_case(building, 'OutputControl:Files')

    if precreate_outputcontrol:
        building.newidfobject(
            key='OUTPUTCONTROL:FILES',
            Output_CSV='No',
            Output_MTR='No',
            Output_ESO='No',
        )

    sim_cls(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    output_control_files = _idfobjects_get_case(building, 'OutputControl:Files')
    assert len(output_control_files) >= 1
    target = output_control_files[0]
    assert str(getattr(target, 'Output_CSV', '')).upper() == 'YES'
    assert str(getattr(target, 'Output_MTR', '')).upper() == 'YES'
    assert str(getattr(target, 'Output_ESO', '')).upper() == 'YES'


@pytest.mark.parametrize('sim_cls', [ts.ParametricSimulation, ts.OptimisationSimulation])
def test_simulation_init_removes_tabular_outputs_by_default(sim_cls):
    ts.print_section("TEST: constructor removes monthly/annual output tables by default")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    building = buildings[0]
    _remove_idfobjects_case(building, 'Output:Table:Monthly')
    _remove_idfobjects_case(building, 'Output:Table:Annual')

    building.newidfobject(key='OUTPUT:TABLE:MONTHLY')
    building.newidfobject(key='OUTPUT:TABLE:ANNUAL')

    sim_cls(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    assert len(_idfobjects_get_case(building, 'Output:Table:Monthly')) == 0
    assert len(_idfobjects_get_case(building, 'Output:Table:Annual')) == 0


@pytest.mark.parametrize('sim_cls', [ts.ParametricSimulation, ts.OptimisationSimulation])
def test_simulation_init_keeps_tabular_outputs_when_disabled(sim_cls):
    ts.print_section("TEST: constructor keeps monthly/annual output tables when disabled")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    building = buildings[0]
    _remove_idfobjects_case(building, 'Output:Table:Monthly')
    _remove_idfobjects_case(building, 'Output:Table:Annual')

    building.newidfobject(key='OUTPUT:TABLE:MONTHLY')
    building.newidfobject(key='OUTPUT:TABLE:ANNUAL')

    sim_cls(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
        remove_output_tables=False,
    )

    assert len(_idfobjects_get_case(building, 'Output:Table:Monthly')) == 1
    assert len(_idfobjects_get_case(building, 'Output:Table:Annual')) == 1


def test_get_hourly_df_split_by_category_handles_variable_output_columns():
    ts.print_section("TEST: get_hourly_df split_by con columnas variables")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:2],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    sim.set_category_mapping(
        idf_mapping_rules={
            'climate_zone': {
                'B': '_B_',
                'D': '_D_',
            }
        }
    )

    idf_0 = sim._get_idf_identifier(buildings[0], 0)
    idf_1 = sim._get_idf_identifier(buildings[1], 1)
    epw_0 = ts.TEST_CATEGORIES['medium']['epws'][0]
    epw_1 = ts.TEST_CATEGORIES['medium']['epws'][1]

    sim.outputs_param_simulation = pd.DataFrame([
        {
            'idf': idf_0,
            'epw': epw_0,
            'Zone Mean Air Temperature [Zone_1]': [20.0, 21.0],
            'Zone Mean Air Temperature [Zone_2]': [],
        },
        {
            'idf': idf_1,
            'epw': epw_1,
            'Zone Mean Air Temperature [Zone_1]': [],
            'Zone Mean Air Temperature [Zone_2]': [19.0, 20.0],
        },
    ])

    hourly_by_category = sim.get_hourly_df(
        start_date='2024-01-01 01',
        split_by='climate_zone',
    )

    assert isinstance(hourly_by_category, dict)
    assert set(hourly_by_category.keys()) == {'B', 'D'}
    assert len(hourly_by_category['B']) == 2
    assert len(hourly_by_category['D']) == 2
    assert 'climate_zone' in sim.outputs_param_simulation_hourly.columns

    # Each category dataframe should keep only non-empty output columns for that group.
    assert 'Zone Mean Air Temperature [Zone_2]' not in hourly_by_category['B'].columns
    assert 'Zone Mean Air Temperature [Zone_1]' not in hourly_by_category['D'].columns


def test_get_monthly_df_supports_daily_monthly_and_runperiod_frequency():
    ts.print_section("TEST: agregación diaria/mensual/runperiod")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:2],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    sim.set_category_mapping(
        idf_mapping_rules={
            'climate_zone': {
                'B': '_B_',
                'D': '_D_',
            }
        }
    )

    idf_0 = sim._get_idf_identifier(buildings[0], 0)
    idf_1 = sim._get_idf_identifier(buildings[1], 1)
    epw_0 = ts.TEST_CATEGORIES['medium']['epws'][0]
    epw_1 = ts.TEST_CATEGORIES['medium']['epws'][1]

    sim.outputs_param_simulation = pd.DataFrame([
        {
            'idf': idf_0,
            'epw': epw_0,
            'Zone Mean Air Temperature [Zone_1]': [20.0, 22.0],
            'Zone Mean Air Temperature [Zone_2]': [],
        },
        {
            'idf': idf_1,
            'epw': epw_1,
            'Zone Mean Air Temperature [Zone_1]': [],
            'Zone Mean Air Temperature [Zone_2]': [19.0, 21.0],
        },
    ])

    sim.get_hourly_df(start_date='2024-01-01 01')

    daily_by_category = sim.get_output_df(
        frequency='daily',
        split_by='climate_zone',
    )
    assert isinstance(daily_by_category, dict)
    assert set(daily_by_category.keys()) == {'B', 'D'}
    assert sim.outputs_param_simulation_daily is not None
    assert 'day' in sim.outputs_param_simulation_daily.columns

    monthly_df = sim.get_monthly_df()
    assert monthly_df is not None and not monthly_df.empty
    assert 'month' in monthly_df.columns

    runperiod_df = sim.get_output_df(frequency='runperiod')
    assert runperiod_df is not None and not runperiod_df.empty
    assert 'day' not in runperiod_df.columns
    assert 'month' not in runperiod_df.columns
    assert len(runperiod_df) == 2


def test_get_monthly_df_optimisation_supports_daily_and_runperiod_frequency():
    ts.print_section("TEST: agregación daily/runperiod en optimización")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['medium']['idfs'])
    sim = ts.OptimisationSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['medium']['epws'][:2],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )
    sim.last_run_type = 'optimisation'

    idf_0 = sim._get_idf_identifier(buildings[0], 0)
    idf_1 = sim._get_idf_identifier(buildings[1], 1)
    epw_0 = ts.TEST_CATEGORIES['medium']['epws'][0]
    epw_1 = ts.TEST_CATEGORIES['medium']['epws'][1]

    sim.outputs_optimisation_hourly = pd.DataFrame([
        {
            'idf': idf_0,
            'epw': epw_0,
            'pareto-optimal': True,
            'hour': 1,
            'datetime': pd.Timestamp('2024-01-01 01:00'),
            'Zone Mean Air Temperature [Zone_1]': 20.0,
        },
        {
            'idf': idf_0,
            'epw': epw_0,
            'pareto-optimal': True,
            'hour': 2,
            'datetime': pd.Timestamp('2024-01-01 02:00'),
            'Zone Mean Air Temperature [Zone_1]': 22.0,
        },
        {
            'idf': idf_1,
            'epw': epw_1,
            'pareto-optimal': False,
            'hour': 1,
            'datetime': pd.Timestamp('2024-01-01 01:00'),
            'Zone Mean Air Temperature [Zone_2]': 19.0,
        },
        {
            'idf': idf_1,
            'epw': epw_1,
            'pareto-optimal': False,
            'hour': 2,
            'datetime': pd.Timestamp('2024-01-01 02:00'),
            'Zone Mean Air Temperature [Zone_2]': 21.0,
        },
    ])

    sim.set_category_mapping(
        idf_mapping_rules={
            'climate_zone': {
                'B': '_B_',
                'D': '_D_',
            }
        }
    )

    daily_by_category = sim.get_output_df(
        frequency='daily',
        split_by='climate_zone',
    )
    assert isinstance(daily_by_category, dict)
    assert set(daily_by_category.keys()) == {'B', 'D'}
    assert sim.outputs_optimisation_daily is not None
    assert 'day' in sim.outputs_optimisation_daily.columns

    runperiod_df = sim.get_output_df(frequency='runperiod')
    assert runperiod_df is not None and not runperiod_df.empty
    assert 'day' not in runperiod_df.columns
    assert 'month' not in runperiod_df.columns
    assert len(runperiod_df) == 2


def test_output_keep_existing_default_is_consistent_across_classes():
    ts.print_section("TEST: output_keep_existing default consistency")

    from accim.parametric_and_optimisation.main import SimulationBase

    base_default = inspect.signature(SimulationBase.__init__).parameters['output_keep_existing'].default
    param_default = inspect.signature(ts.ParametricSimulation.__init__).parameters['output_keep_existing'].default
    optim_default = inspect.signature(ts.OptimisationSimulation.__init__).parameters['output_keep_existing'].default
    predef_default = inspect.signature(ts.AccimPredefModelsParamSim.__init__).parameters['output_keep_existing'].default

    assert base_default is True
    assert param_default is True
    assert optim_default is True
    assert predef_default is True


def test_addaccis_passthrough_params_are_exposed_in_all_constructors():
    ts.print_section('TEST: parámetros addAccis expuestos en constructores')

    expected = [
        'Output_take_dataframe',
        'EnergyPlus_version',
        'VRFschedule',
        'eer',
        'cop',
        'hvac_zone_map',
    ]
    classes_to_check = [
        main_module.SimulationBase,
        ts.ParametricSimulation,
        ts.OptimisationSimulation,
        ts.AccimPredefModelsParamSim,
    ]

    for cls in classes_to_check:
        sig = inspect.signature(cls.__init__)
        for param_name in expected:
            assert param_name in sig.parameters, f"{cls.__name__}.__init__ no expone '{param_name}'."


def test_parametric_output_wrappers_expose_explicit_advanced_arguments():
    ts.print_section("TEST: firmas explícitas en wrappers paramétricos de outputs")

    hourly_sig = inspect.signature(ts.ParametricSimulation.get_hourly_df)
    output_sig = inspect.signature(ts.ParametricSimulation.get_output_df)

    for expected in [
        'epw_filter',
        'simulation_indices',
        'output_columns',
        'include_summary_columns',
        'file_source',
        'eplus_install_dir',
        'only_run_period',
        'skip_confirmation',
    ]:
        assert expected in hourly_sig.parameters
        assert expected in output_sig.parameters

    assert all(p.kind != inspect.Parameter.VAR_KEYWORD for p in hourly_sig.parameters.values())
    assert all(p.kind != inspect.Parameter.VAR_KEYWORD for p in output_sig.parameters.values())


def test_normalize_outputs_tracks_df_types_without_global_blocking():
    ts.print_section("TEST: normalize_outputs tracking por tipo de dataframe")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    idf_0 = sim._get_idf_identifier(buildings[0], 0)
    sim.building_floor_area = {idf_0: 100.0}

    sim.outputs_param_simulation_hourly = pd.DataFrame([
        {
            'idf': idf_0,
            'epw': ts.TEST_CATEGORIES['fast']['epws'][0],
            'hour': 1,
            'datetime': pd.Timestamp('2024-01-01 01:00'),
            'DistrictHeating:Facility [J]': 3_600_000.0,
        }
    ])
    sim.outputs_param_simulation_monthly = pd.DataFrame([
        {
            'idf': idf_0,
            'epw': ts.TEST_CATEGORIES['fast']['epws'][0],
            'month': pd.Period('2024-01', freq='M'),
            'DistrictHeating:Facility [J]': 7_200_000.0,
        }
    ])

    sim.normalize_outputs(df_types=['parametric_hourly'])
    assert 'DistrictHeating:Facility [kWh/m2]' in sim.outputs_param_simulation_hourly.columns
    assert 'DistrictHeating:Facility [J]' in sim.outputs_param_simulation_monthly.columns
    assert sim._is_df_type_normalized('parametric_hourly')
    assert not sim._is_df_type_normalized('parametric_monthly')
    assert sim.outputs_normalized is False

    sim.normalize_outputs(df_types=['parametric_monthly'])
    assert 'DistrictHeating:Facility [kWh/m2]' in sim.outputs_param_simulation_monthly.columns
    assert sim._is_df_type_normalized('parametric_monthly')
    assert sim.outputs_normalized is True


def test_get_output_df_warns_for_unclassified_numeric_columns_defaulting_to_sum():
    ts.print_section("TEST: warning de agregación por defecto en columnas no clasificadas")

    buildings = ts.prepare_buildings(ts.TEST_CATEGORIES['fast']['idfs'])
    sim = ts.ParametricSimulation(
        buildings=buildings,
        epws=ts.TEST_CATEGORIES['fast']['epws'],
        parameters_type=None,
        output_freqs=['hourly'],
        verbosemode=False,
    )

    idf_0 = sim._get_idf_identifier(buildings[0], 0)
    sim.outputs_param_simulation = pd.DataFrame([
        {
            'idf': idf_0,
            'epw': ts.TEST_CATEGORIES['fast']['epws'][0],
            'Custom KPI [arb]': [1.0, 2.0],
        }
    ])

    with pytest.warns(UserWarning, match="unclassified numeric columns"):
        daily_df = sim.get_output_df(frequency='daily', start_date='2024-01-01 01')

    assert daily_df is not None and not daily_df.empty
    assert daily_df['Custom KPI [arb]'].iloc[0] == pytest.approx(3.0)


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

