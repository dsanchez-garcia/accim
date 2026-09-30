"""Hermetic reporting-contract tests: no IDD, EPW, model runs or discovery.

Prepared for later test execution; static review is not numerical EMS validation.
"""

from collections import defaultdict
from copy import deepcopy

import pytest

from accim.sim.comfort_metrics import add_comfort_metrics, REPORTING_POINT


class FakeObject:
    def __init__(self, key, **fields):
        self.key = key.upper()
        self.fieldnames = ['key', *fields]
        self.__dict__.update(fields)

    def __getitem__(self, field):
        return getattr(self, field)


class FakeIDF:
    def __init__(self):
        self.idfname = 'test.idf'
        self.idfobjects = defaultdict(list)

    def newidfobject(self, kind, **fields):
        obj = FakeObject(kind, **fields)
        self.idfobjects[kind.upper()].append(obj)
        return obj

    def removeidfobject(self, obj):
        self.idfobjects[obj.key].remove(obj)


def model(reference='Zone A'):
    building = FakeIDF()
    building.newidfobject('Zone', Name='Zone A')
    building.newidfobject('People', Name='Office People', Zone_or_ZoneList_Name=reference,
                          Thermal_Comfort_Model_1_Type='AdaptiveCEN15251',
                          Thermal_Comfort_Model_2_Type='Fanger')
    building.newidfobject('Schedule:Constant', Name='Original occupancy', Hourly_Value=1)
    building.newidfobject('ZoneControl:Thermostat', Name='Original thermostat', Zone_or_ZoneList_Name='Zone A')
    return building


def snapshot(building):
    return {key: [deepcopy(vars(obj)) for obj in values]
            for key, values in building.idfobjects.items() if values}


def program_text(building, suffix):
    matches = [obj for obj in building.idfobjects['ENERGYMANAGEMENTSYSTEM:PROGRAM']
               if obj.Name.endswith(suffix)]
    assert len(matches) == 1
    return '\n'.join(getattr(matches[0], field) for field in matches[0].fieldnames
                     if field.startswith('Program_Line_'))


def test_fixed_en_is_independent_and_reports_timestep_increments():
    building = model()
    before = snapshot(building)
    report = add_comfort_metrics(building)
    variables = {row['metric']: row for row in report['outputs']}
    assert set(variables) == {'occupied', 'fixed_en'}
    assert variables['fixed_en']['units'] == 'C-hr'
    assert variables['fixed_en']['key_value'] == 'EMS'
    text = program_text(building, '_EN')
    assert text.startswith('SET ACCIM_CM_Zone_A_DH = 0\n')
    for line in ('WarmupFlag == 0', '_N > 0', '@Min ACCIM_CM_Zone_A_RMOT 30',
                 '@Max ACCIM_CM_Zone_A_R 10', '0.33 *', '+ 18.8',
                 '_Neutral - 4', '_Neutral + 3', '* ZoneTimeStep'):
        assert line in text
    for forbidden in ('CustAST', 'ACST', 'AHST', 'PMOT'):
        assert forbidden not in text
    sensors = building.idfobjects['ENERGYMANAGEMENTSYSTEM:SENSOR']
    assert {s.OutputVariable_or_OutputMeter_Index_Key_Name for s in sensors
            if s.Name.endswith('_To')} == {'Zone A'}
    assert {s.OutputVariable_or_OutputMeter_Index_Key_Name for s in sensors
            if not s.Name.endswith('_To')} == {'Office People'}
    assert all(obj.EnergyPlus_Model_Calling_Point == REPORTING_POINT
               for obj in building.idfobjects['ENERGYMANAGEMENTSYSTEM:PROGRAMCALLINGMANAGER'])
    assert all(obj.Type_of_Data_in_Variable == 'Summed' and obj.Update_Frequency == 'ZoneTimestep'
               for obj in building.idfobjects['ENERGYMANAGEMENTSYSTEM:OUTPUTVARIABLE'])
    after = snapshot(building)
    for kind, values in before.items():
        assert after[kind] == values
    assert not building.idfobjects['ENERGYMANAGEMENTSYSTEM:ACTUATOR']
    assert not building.idfobjects['OUTPUT:VARIABLE']  # Low-level builder does not select reporting requests.


def test_identical_calls_and_incremental_metric_families_are_idempotent():
    building = model()
    first = add_comfort_metrics(building)
    original = snapshot(building)
    second = add_comfort_metrics(building)
    assert second['added'] == 0 and second['reused'] == first['added']
    assert snapshot(building) == original
    combined = add_comfort_metrics(building, metrics=('fixed_en', 'fixed_pmv'))
    assert {row['metric'] for row in combined['outputs']} == {'occupied', 'fixed_en', 'pmv_integral', 'fixed_pmv_hours'}
    assert len([s for s in building.idfobjects['ENERGYMANAGEMENTSYSTEM:SENSOR'] if s.Name.endswith('_N')]) == 1
    text = program_text(building, '_PMV')
    assert '@Abs ACCIM_CM_Zone_A_PMV' in text and '_AbsValue > 0.5' in text
    assert 'ZoneTimeStep' in text and 'WarmupFlag == 0' in text
    assert add_comfort_metrics(building, metrics=('fixed_en', 'fixed_pmv'))['added'] == 0


@pytest.mark.parametrize('container', ['zone-list', 'space', 'space-list', 'zone-with-spaces'])
def test_resolved_people_and_space_keys(container):
    building = model()
    person = building.idfobjects['PEOPLE'][0]
    if container == 'zone-list':
        building.newidfobject('ZoneList', Name='Offices', Zone_1_Name='Zone A')
        person.Zone_or_ZoneList_Name = 'Offices'
        expected = {'Zone A Office People'}
    else:
        building.newidfobject('Space', Name='Space 1', Zone_Name='Zone A')
        if container == 'space-list':
            building.newidfobject('Space', Name='Space 2', Zone_Name='Zone A')
            building.newidfobject('SpaceList', Name='Workspaces', Space_1_Name='Space 1', Space_2_Name='Space 2')
            person.Zone_or_ZoneList_Name = 'Workspaces'
            expected = {'Space 1 Office People', 'Space 2 Office People'}
        elif container == 'space':
            person.Zone_or_ZoneList_Name = 'Space 1'
            expected = {'Space 1 Office People'}
        else:
            expected = {'Space 1 Office People'}
    report = add_comfort_metrics(building)
    assert {target['sensor_key'] for target in report['targets']} == expected
    assert len(report['outputs']) == 2 * len(expected)


def test_unresolved_or_duplicate_targets_fail_before_mutation():
    building = model('Does not exist')
    before = snapshot(building)
    with pytest.raises(ValueError, match='Unresolved'):
        add_comfort_metrics(building)
    assert snapshot(building) == before
    building = model()
    building.newidfobject('People', Name='Other People', Zone_or_ZoneList_Name='Zone A',
                          Thermal_Comfort_Model_1_Type='AdaptiveCEN15251')
    before = snapshot(building)
    with pytest.raises(ValueError, match='duplicate'):
        add_comfort_metrics(building)
    assert snapshot(building) == before


def test_models_required_without_adding_fanger_or_changing_people():
    building = model()
    building.idfobjects['PEOPLE'][0].Thermal_Comfort_Model_2_Type = ''
    before = snapshot(building)
    with pytest.raises(ValueError, match='Fanger'):
        add_comfort_metrics(building, metrics=('fixed_pmv',))
    assert snapshot(building) == before


@pytest.mark.parametrize('name', ['ACCIM_CM_Zone_A_DH', 'ACCIM_CM_Zone_A_R', 'ACCIM_CM_Zone_A_N'])
def test_globals_and_scratch_names_cannot_capture_unrelated_control_state(name):
    building = model()
    building.newidfobject('EnergyManagementSystem:GlobalVariable', Erl_Variable_1_Name='Unrelated', Erl_Variable_2_Name=name)
    before = snapshot(building)
    with pytest.raises(ValueError, match='collision|not owned'):
        add_comfort_metrics(building)
    assert snapshot(building) == before


def test_conflicting_definition_and_extra_calling_manager_are_rejected():
    building = model()
    add_comfort_metrics(building)
    program = next(obj for obj in building.idfobjects['ENERGYMANAGEMENTSYSTEM:PROGRAM'] if obj.Name.endswith('_EN'))
    original_line = program.Program_Line_1
    program.Program_Line_1 = 'SET ACCIM_CM_Zone_A_DH = 100'
    with pytest.raises(ValueError, match='different definition'):
        add_comfort_metrics(building)
    program.Program_Line_1 = original_line
    building.newidfobject('EnergyManagementSystem:ProgramCallingManager', Name='Unwanted',
                          EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor', Program_Name_1=program.Name)
    with pytest.raises(ValueError, match='unexpected calling manager'):
        add_comfort_metrics(building)


def test_dry_run_and_failed_creation_preserve_original_objects(monkeypatch):
    building = model()
    before = snapshot(building)
    preview = add_comfort_metrics(building, dry_run=True)
    assert preview['added'] == 0 and preview['would_add'] > 0
    assert snapshot(building) == before
    create = building.newidfobject

    def fail_program(kind, **fields):
        if kind == 'EnergyManagementSystem:Program':
            raise RuntimeError('Synthetic IDD failure')
        return create(kind, **fields)

    monkeypatch.setattr(building, 'newidfobject', fail_program)
    with pytest.raises(RuntimeError, match='Synthetic'):
        add_comfort_metrics(building)
    assert snapshot(building) == before


def test_session_wrapper_scopes_appends_invalidates_and_never_discovers(monkeypatch):
    from accim.parametric_and_optimisation.main import SimulationBase

    session = SimulationBase.__new__(SimulationBase)
    session.buildings = [model(), model()]
    session.buildings[1].idfname = 'second.idf'
    session.output_freqs = ['hourly']
    session.available_outputs_ = {'old': 'inventory'}
    unchanged_readers = object()
    session.sim_outputs = unchanged_readers
    requests = []

    def append(**kwargs):
        requests.append(kwargs)
        return {'added': len(kwargs['df_output_variable'])}

    def forbidden(*args, **kwargs):
        raise AssertionError('No discovery/simulation is allowed')

    monkeypatch.setattr(session, 'set_output_variables_to_idf', append)
    monkeypatch.setattr(session, 'discover_available_outputs', forbidden)
    report = session.add_comfort_metrics(idf_scope=1)
    assert session.available_outputs_ is None and session._output_definitions_changed
    assert session.sim_outputs is unchanged_readers
    assert not session.buildings[0].idfobjects['ENERGYMANAGEMENTSYSTEM:PROGRAM']
    assert set(report['outputs']['idf']) == {'second'}
    assert len(requests) == 1 and requests[0]['validate'] is False
    assert requests[0]['mode'] == 'append' and requests[0]['idf_scope'] == 1


def test_next_explicit_discovery_does_not_reuse_stale_disk_dictionaries(monkeypatch, tmp_path):
    from accim.parametric_and_optimisation.main import SimulationBase

    session = SimulationBase.__new__(SimulationBase)
    session.buildings, session.epws = [model()], ['never-run.epw']
    session._output_definitions_changed = True
    directory = tmp_path / 'available_outputs'
    directory.mkdir()
    for name in ('eplusout.rdd', 'eplusout.mdd'):
        (directory / name).write_text('stale inventory; must not be read', encoding='utf-8')
    monkeypatch.chdir(tmp_path)

    def stop_before_preparation(**kwargs):
        raise RuntimeError('Fresh discovery required; STOP before any simulation')

    monkeypatch.setattr(session, '_prepare_reduced_testsim_building', stop_before_preparation)
    with pytest.raises(RuntimeError, match='Fresh discovery required'):
        session.discover_available_outputs(prefer='rdd_mdd', refresh=False)
    assert session._output_definitions_changed

