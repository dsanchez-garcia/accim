"""Regression tests for the per-IDF floor-area mapping used by normalize_outputs().

With several IDFs, set_building_floor_area() stores a dictionary {IDF name: floor area in m2}
and normalize_outputs() divides each energy value by 3.6e6 J/kWh times the area of the IDF
named in the 'idf' column of its row. These tests pin that:

- each row is divided by the area of its own IDF, in every results table (parametric and
  optimisation, summary, hourly, daily, monthly and runperiod), whatever the order of the rows
  and of the dictionary;
- the keys built by set_building_floor_area() are the identifiers written in the 'idf' column
  of the results: with the IDFs loaded in the session (also with an upper-case '.IDF'
  extension), with the IDFs reloaded from the accim backups in a new session, and with a
  custom_area dictionary keyed by file or backup names;
- a custom_area dictionary must name exactly the loaded IDFs, and a rejected dictionary keeps
  the previous areas;
- an IDF without floor area, or several different areas for a table without 'idf' column,
  raise a ValueError that says how to fix it instead of using 1 m2 or the first area (before,
  these rows were divided silently by a wrong area); the robustness analysis uses the area of
  the IDF it simulates.
"""
import os
from types import SimpleNamespace

import matplotlib
import pandas as pd
import pytest

import accim.parametric_and_optimisation.main as main_module
from accim.parametric_and_optimisation.main import OptimisationSimulation, ParametricSimulation

from .test_analysis_floor_area import make_idf

matplotlib.use('Agg')

AREAS = {'office_a': 25.0, 'office_b': 50.0, 'office_c': 200.0}


class _DummyProblem:
    def __init__(self, inputs, outputs):
        self._inputs = list(inputs)
        self._outputs = list(outputs)

    def names(self, typ):
        if typ == 'inputs':
            return list(self._inputs)
        if typ == 'outputs':
            return list(self._outputs)
        if typ == 'constraints':
            return []
        raise KeyError(typ)


def _new_parametric():
    return ParametricSimulation(
        buildings=None,
        epws=['Seville.epw', 'Oslo.epw'],
        parameters_type=None,
        bypass_addAccis=True,
    )


def _idf_stem(label):
    label = os.path.basename(str(label))
    return os.path.splitext(label)[0] if label.lower().endswith('.idf') else label


def _fake_building(file_name):
    area = AREAS[_idf_stem(file_name)]
    # Two floors, to check that the area of an IDF is the sum of its floors.
    building = make_idf(file_name, zones=['Z1', 'Z2'], floors={'Z1': 0.6 * area, 'Z2': 0.4 * area})

    def _savecopy(path):
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write('Version,9.6;\n')

    building.savecopy = _savecopy
    return building


def _fake_worker(idf_path, epw, epwname, idf_basename, out_dir, problem_names_inputs,
                 problem_names_outputs, output_specs, add_output_specs, add_output_names,
                 row_dict, keep_dirs, keep_input, sim_files_extensions=None,
                 sim_files_policy='keep', additional_params=None):
    # 3.6e8 J per unit of x in every IDF: 100 * x kWh before dividing by the floor area.
    result = {problem_names_outputs[0]: float(row_dict['x']) * 3.6e8, 'epw': epwname, 'idf': idf_basename}
    if keep_input:
        result.update(row_dict)
    return result


def _run_fake_parametric(monkeypatch, out_dir, idf_files):
    monkeypatch.setattr(main_module, '_run_single_evaluation_worker', _fake_worker)
    monkeypatch.setattr(pd.DataFrame, 'to_excel', lambda self, *args, **kwargs: None, raising=False)
    sim = _new_parametric()
    sim.buildings = [_fake_building(file_name) for file_name in idf_files]
    sim.building = sim.buildings[0]
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity'])
    sim.run_parametric_simulation(
        df=pd.DataFrame({'x': [1, 2]}),
        out_dir=str(out_dir),
        processes=1,
        keep_dirs=False,
        keep_input=True,
    )
    return sim


def _expected_kwh_per_m2(results):
    return [100.0 * x / AREAS[_idf_stem(idf)] for (x, idf) in zip(results['x'], results['idf'])]


# ----------------------------------------------------------------------------- divisor of each row

def test_each_row_is_divided_by_the_floor_area_of_its_own_idf():
    sim = _new_parametric()
    # The order of the dictionary differs from the order of the rows on purpose.
    sim.building_floor_area = {'office_c': 200.0, 'office_a': 25.0, 'office_b': 50.0}
    idfs = ['office_a', 'office_b', 'office_c', 'office_b', 'office_a', 'office_c']
    sim.outputs_param_simulation = pd.DataFrame({
        'x': [1, 1, 1, 2, 2, 2],
        'epw': ['Seville', 'Seville', 'Oslo', 'Oslo', 'Oslo', 'Seville'],
        'idf': idfs,
        'Heating:Electricity [J]': [3.6e8] * 6,
        'Cooling:Electricity [J]': [7.2e8] * 6,
    })

    sim.normalize_outputs(df_types=['parametric'])

    results = sim.outputs_param_simulation
    # 3.6e8 J is 100 kWh: 4 kWh/m2 over 25 m2, 2 over 50 m2 and 0.5 over 200 m2.
    assert results['Heating:Electricity [kWh/m2]'].tolist() == pytest.approx([4.0, 2.0, 0.5, 2.0, 4.0, 0.5])
    assert results['Cooling:Electricity [kWh/m2]'].tolist() == pytest.approx([8.0, 4.0, 1.0, 4.0, 8.0, 1.0])
    assert results['idf'].tolist() == idfs
    assert results['x'].tolist() == [1, 1, 1, 2, 2, 2]


TABLES = [
    (ParametricSimulation, 'parametric', 'outputs_param_simulation'),
    (ParametricSimulation, 'parametric_hourly', 'outputs_param_simulation_hourly'),
    (ParametricSimulation, 'parametric_daily', 'outputs_param_simulation_daily'),
    (ParametricSimulation, 'parametric_monthly', 'outputs_param_simulation_monthly'),
    (ParametricSimulation, 'parametric_runperiod', 'outputs_param_simulation_runperiod'),
    (OptimisationSimulation, 'optimisation', 'outputs_optimisation'),
    (OptimisationSimulation, 'optimisation_hourly', 'outputs_optimisation_hourly'),
    (OptimisationSimulation, 'optimisation_daily', 'outputs_optimisation_daily'),
    (OptimisationSimulation, 'optimisation_monthly', 'outputs_optimisation_monthly'),
    (OptimisationSimulation, 'optimisation_runperiod', 'outputs_optimisation_runperiod'),
]


@pytest.mark.parametrize(('sim_class', 'df_type', 'attribute'), TABLES, ids=[t[1] for t in TABLES])
def test_every_results_table_uses_the_floor_area_of_the_idf_of_each_row(sim_class, df_type, attribute):
    sim = sim_class(buildings=None, epws=['Seville.epw'], parameters_type=None, bypass_addAccis=True)
    sim.building_floor_area = dict(AREAS)
    setattr(sim, attribute, pd.DataFrame({
        'epw': ['Seville'] * 3,
        'idf': ['office_c', 'office_a', 'office_b'],
        'Electricity:Facility [J]': [7.2e8, 7.2e8, 7.2e8],
        'BLOCK1:ZONE1:Zone Operative Temperature [C]': [21.0, 22.0, 23.0],
    }))

    sim.normalize_outputs(df_types=[df_type])

    table = getattr(sim, attribute)
    assert table['Electricity:Facility [kWh/m2]'].tolist() == pytest.approx([1.0, 8.0, 4.0])
    assert table['BLOCK1:ZONE1:Zone Operative Temperature [C]'].tolist() == [21.0, 22.0, 23.0]
    assert sim._is_df_type_normalized(df_type)


@pytest.mark.parametrize('floor_area', [50.0, {'office_b': 50.0}], ids=['float', 'single_idf_dictionary'])
def test_the_area_of_a_single_idf_applies_to_tables_without_idf_column(floor_area):
    sim = _new_parametric()
    sim.building_floor_area = floor_area
    sim.outputs_param_simulation_hourly = pd.DataFrame({
        'epw': ['Seville', 'Seville'],
        'hour': [1, 2],
        'Heating:Electricity [J](Hourly)': [3.6e8, 7.2e8],
    })

    sim.normalize_outputs(df_types=['parametric_hourly'])

    hourly = sim.outputs_param_simulation_hourly
    assert hourly['Heating:Electricity [kWh/m2](Hourly)'].tolist() == pytest.approx([2.0, 4.0])


# ----------------------------------------------------------------------------- keys of the area dictionary

def test_areas_of_the_loaded_idfs_match_the_idf_column_of_a_parametric_run(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    sim = _run_fake_parametric(monkeypatch, tmp_path / 'param', ['office_a.idf', 'office_b.idf', 'office_c.idf'])

    areas = sim.set_building_floor_area(mode='all')

    assert areas == pytest.approx(AREAS)
    assert set(sim.outputs_param_simulation['idf']) == set(AREAS)
    assert len(sim.outputs_param_simulation) == 12  # 3 IDFs x 2 EPWs x 2 rows of the plan

    sim.normalize_outputs(df_types=['parametric'])

    results = sim.outputs_param_simulation
    assert results['Heating:Electricity_kWh/m2'].tolist() == pytest.approx(_expected_kwh_per_m2(results))


def test_areas_reloaded_from_idf_backups_in_a_new_session_match_the_loaded_results(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    first = _run_fake_parametric(monkeypatch, tmp_path / 'param', ['office_a.idf', 'office_b.idf', 'office_c.idf'])
    json_path = os.path.splitext(first.outputs_param_simulation_filepath)[0] + '.json'
    backup_names = sorted(os.path.basename(path) for path in first.idf_backup_path)
    loaded = []

    def fake_get_building(path):
        # Like eppy, the IDF read from a backup is named after the backup file.
        file_name = os.path.basename(path)
        loaded.append(file_name)
        stem = next(name for name in AREAS if file_name.startswith(f'accim_idf_backup_{name}_pre_parametric_'))
        return make_idf(path, zones=['Z1'], floors={'Z1': AREAS[stem]})

    monkeypatch.setattr('accim.utils.get_building', fake_get_building)

    second = _new_parametric()
    second.load_outputs_parametric(json_path=json_path)
    areas = second.set_building_floor_area(mode='all')

    assert sorted(loaded) == backup_names
    assert areas == pytest.approx(AREAS)

    second.normalize_outputs(df_types=['parametric'])

    results = second.outputs_param_simulation
    assert results['Heating:Electricity_kWh/m2'].tolist() == pytest.approx(_expected_kwh_per_m2(results))


def test_custom_area_dictionary_keyed_by_file_or_backup_names_reaches_the_rows_of_each_idf():
    sim = _new_parametric()
    sim.buildings = [_fake_building(name) for name in ['office_a.idf', 'office_b.idf', 'office_c.idf']]
    sim.building = sim.buildings[0]

    areas = sim.set_building_floor_area(
        mode='custom',
        custom_area={
            'office_a.idf': '25',
            'C:/models/office_b.idf': 50,
            'accim_idf_backup_office_c_pre_parametric_20260101_101010.idf': 200.0,
        },
    )

    assert areas == pytest.approx(AREAS)
    idf_labels = [sim._get_idf_identifier(building, idx) for (idx, building) in enumerate(sim.buildings)]
    sim.outputs_param_simulation = pd.DataFrame({
        'x': [1, 1, 1],
        'epw': ['Seville'] * 3,
        'idf': idf_labels,
        'Heating:Electricity': [3.6e8] * 3,
    })

    sim.normalize_outputs(df_types=['parametric'])

    assert sim.outputs_param_simulation['Heating:Electricity_kWh/m2'].tolist() == pytest.approx([4.0, 2.0, 0.5])


def test_custom_area_dictionary_must_name_exactly_the_loaded_idfs_and_keeps_previous_areas_if_not():
    sim = _new_parametric()
    sim.buildings = [_fake_building(name) for name in ['office_a.idf', 'office_b.idf', 'office_c.idf']]
    sim.building = sim.buildings[0]
    sim.building_floor_area = dict(AREAS)

    with pytest.raises(ValueError, match=r"missing IDF keys: \['office_c'\]"):
        sim.set_building_floor_area(mode='custom', custom_area={'office_a': 25.0, 'office_b': 50.0})
    with pytest.raises(ValueError, match=r"unknown IDF keys: \['office_d'\]"):
        sim.set_building_floor_area(mode='custom', custom_area={**AREAS, 'office_d.idf': 10.0})
    with pytest.raises(ValueError, match=r"Duplicate IDF key for custom_area: 'office_a.idf'"):
        sim.set_building_floor_area(mode='custom', custom_area={**AREAS, 'office_a.idf': 10.0})

    assert sim.building_floor_area == AREAS


# ----------------------------------------------------------------------------- wrong or missing mapping

def test_rows_of_an_idf_without_floor_area_are_rejected_without_normalising_the_table():
    sim = _new_parametric()
    sim.building_floor_area = {'office_a': 25.0, 'office_b': 50.0}
    sim.outputs_param_simulation = pd.DataFrame({
        'x': [1, 1, 1],
        'epw': ['Seville'] * 3,
        'idf': ['office_a', 'office_b', 'office_c'],
        'Heating:Electricity [J]': [3.6e8] * 3,
    })

    with pytest.raises(ValueError) as exc_info:
        sim.normalize_outputs(df_types=['parametric'])

    message = str(exc_info.value)
    assert "no floor area for the IDF(s) ['office_c'] of outputs_param_simulation" in message
    assert "IDFs with a floor area: ['office_a', 'office_b']" in message
    assert 'set_building_floor_area(' in message
    # The table is left in J and can be normalised once the areas are fixed.
    assert sim.outputs_param_simulation['Heating:Electricity [J]'].tolist() == [3.6e8] * 3
    assert not sim._is_df_type_normalized('parametric')
    assert sim.outputs_normalized is False

    sim.building_floor_area = dict(AREAS)
    sim.normalize_outputs(df_types=['parametric'])
    assert sim.outputs_param_simulation['Heating:Electricity [kWh/m2]'].tolist() == pytest.approx([4.0, 2.0, 0.5])


def test_several_floor_areas_and_a_table_without_idf_column_are_rejected():
    sim = _new_parametric()
    sim.building_floor_area = {'office_a': 25.0, 'office_b': 50.0}
    sim.outputs_param_simulation_hourly = pd.DataFrame({
        'epw': ['Seville'] * 4,
        'hour': [1, 2, 1, 2],
        'Heating:Electricity [J](Hourly)': [3.6e8] * 4,
    })

    with pytest.raises(ValueError) as exc_info:
        sim.normalize_outputs(df_types=['parametric_hourly'])

    message = str(exc_info.value)
    assert "outputs_param_simulation_hourly has no 'idf' column" in message
    assert "['office_a', 'office_b']" in message
    assert 'include_summary_columns=True' in message
    assert "set_building_floor_area(mode='custom'" in message
    assert 'Heating:Electricity [J](Hourly)' in sim.outputs_param_simulation_hourly.columns


def test_equal_floor_areas_apply_to_a_table_without_idf_column():
    sim = _new_parametric()
    sim.building_floor_area = {'office_a': 50.0, 'office_b': 50.0}
    sim.outputs_param_simulation_hourly = pd.DataFrame({
        'epw': ['Seville'] * 2,
        'hour': [1, 2],
        'Heating:Electricity [J](Hourly)': [3.6e8, 7.2e8],
    })

    sim.normalize_outputs(df_types=['parametric_hourly'])

    hourly = sim.outputs_param_simulation_hourly
    assert hourly['Heating:Electricity [kWh/m2](Hourly)'].tolist() == pytest.approx([2.0, 4.0])


def test_idf_labels_and_area_keys_are_matched_without_extension_folder_or_backup_affixes():
    sim = _new_parametric()
    sim.building_floor_area = {'office_a.idf': 25.0, 'accim_idf_backup_office_b_post_setup_20260101_101010.idf': 50.0}
    sim.outputs_param_simulation = pd.DataFrame({
        'x': [1, 1],
        'epw': ['Seville'] * 2,
        'idf': ['C:/models/office_b.IDF', 'office_a'],
        'Heating:Electricity [J]': [3.6e8] * 2,
    })

    sim.normalize_outputs(df_types=['parametric'])

    assert sim.outputs_param_simulation['Heating:Electricity [kWh/m2]'].tolist() == pytest.approx([2.0, 4.0])


@pytest.mark.parametrize('file_name', ['office_a.idf', 'office_a.IDF', 'C:/models/office_a.Idf'])
def test_idf_identifiers_ignore_the_case_of_the_idf_extension(file_name):
    sim = _new_parametric()

    assert sim._get_idf_identifier(SimpleNamespace(idfname=file_name), 0) == 'office_a'
    assert sim._normalize_plan_idf_value(file_name) == 'office_a'
    assert sim._get_floor_area_idf_name(SimpleNamespace(idfname=file_name), 0) == 'office_a'


def test_idf_files_with_upper_case_extension_are_normalised_with_their_own_area(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    sim = _run_fake_parametric(monkeypatch, tmp_path / 'param', ['office_a.IDF', 'office_b.idf'])
    sim.set_building_floor_area(mode='all')

    sim.normalize_outputs(df_types=['parametric'])

    results = sim.outputs_param_simulation
    assert set(results['idf']) == {'office_a', 'office_b'}
    assert sorted(os.path.basename(path).split('_pre_parametric_')[0] for path in sim.idf_backup_path) == [
        'accim_idf_backup_office_a',
        'accim_idf_backup_office_b',
    ]
    assert results['Heating:Electricity_kWh/m2'].tolist() == pytest.approx(_expected_kwh_per_m2(results))


# ----------------------------------------------------------------------------- robustness analysis

class _FakeRobustnessEvaluator:
    def df_apply(self, df, keep_input=True, keep_dirs=False):
        outputs = df.reset_index(drop=True).copy()
        # 3.6e8 J per unit of x for each objective: 200 * x kWh in total.
        outputs['Heating:Electricity'] = 3.6e8 * outputs['x']
        outputs['Cooling:Electricity'] = 3.6e8 * outputs['x']
        return outputs


def _robustness_session(monkeypatch, floor_areas):
    monkeypatch.setattr(
        ParametricSimulation,
        'set_evaluator',
        lambda self, epw, out_dir, building=None: _FakeRobustnessEvaluator(),
    )
    sim = _new_parametric()
    sim.buildings = [_fake_building('office_a.idf'), _fake_building('office_b.idf')]
    sim.building = sim.buildings[0]
    sim.problem = _DummyProblem(inputs=['x'], outputs=['Heating:Electricity', 'Cooling:Electricity'])
    sim.last_run_type = 'parametric'
    sim.building_floor_area = floor_areas
    return sim


def test_robustness_analysis_uses_the_floor_area_of_the_simulated_idf(monkeypatch, tmp_path):
    # The area of the simulated IDF (self.building, office_a) is not the first one of the dictionary.
    sim = _robustness_session(monkeypatch, {'office_b': 50.0, 'office_a': 25.0})

    robustness = sim.run_robustness_analysis(
        optimal_solutions_df=pd.DataFrame({'x': [1.0, 2.0]}),
        epws_robustness=['Oslo.epw'],
        out_dir=str(tmp_path),
        normalize_per_m2=True,
    )

    assert robustness['Total_Energy_kWh_m2'].tolist() == pytest.approx([8.0, 16.0])


def test_robustness_analysis_rejects_a_simulated_idf_without_floor_area(monkeypatch, tmp_path):
    sim = _robustness_session(monkeypatch, {'office_b': 50.0, 'office_c': 200.0})

    with pytest.raises(ValueError, match=r"no floor area for the IDF\(s\) \['office_a'\] of the robustness results"):
        sim.run_robustness_analysis(
            optimal_solutions_df=pd.DataFrame({'x': [1.0, 2.0]}),
            epws_robustness=['Oslo.epw'],
            out_dir=str(tmp_path),
            normalize_per_m2=True,
        )
