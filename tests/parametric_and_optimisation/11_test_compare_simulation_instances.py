import os
from pathlib import Path

import pandas as pd

from accim.parametric_and_optimisation.main import (
    SimulationComparisonSession,
    compare_simulation_instances,
    compare_latest_pickles_in_folders,
    compare_multiple_pickles_with_reference,
)


class DummySimulation:
    """Minimal instance-like object for comparison utility tests."""

    def __init__(self, df: pd.DataFrame, run_type: str = 'parametric'):
        self.outputs_param_simulation = df if run_type == 'parametric' else None
        self.outputs_optimisation = df if run_type == 'optimisation' else None
        self.outputs_param_simulation_filepath = None
        self.outputs_optimisation_filepath = None
        self.last_run_type = run_type


def _make_parametric_df() -> pd.DataFrame:
    df = pd.DataFrame(
        {
            'ComfStand': [0, 1, 2],
            'epw': ['Seville.epw', 'Seville.epw', 'Seville.epw'],
            'HVAC energy': [10.0, 12.5, 15.0],
        }
    )
    df.attrs['parameters_names'] = ['ComfStand', 'epw']
    df.attrs['outputs_names'] = ['HVAC energy']
    return df


def test_compare_simulation_instances_equal_from_pickle(tmp_path):
    left = _make_parametric_df()
    right = left.sample(frac=1, random_state=42).reset_index(drop=True)

    left_path = tmp_path / 'left.pkl'
    right_path = tmp_path / 'right.pkl'
    left.to_pickle(left_path)
    right.to_pickle(right_path)

    report = compare_simulation_instances(left_path, right_path)

    assert report['equal'] is True
    assert report['inputs']['same_input_set'] is True
    assert report['outputs']['same_for_common_inputs'] is True
    assert report['outputs']['mismatched_rows_count'] == 0


def test_compare_simulation_instances_detects_output_changes(tmp_path):
    left = _make_parametric_df()
    right = _make_parametric_df()
    right.loc[right['ComfStand'] == 1, 'HVAC energy'] = 25.0

    left_path = tmp_path / 'left_out_diff.pkl'
    right_path = tmp_path / 'right_out_diff.pkl'
    left.to_pickle(left_path)
    right.to_pickle(right_path)

    report = compare_simulation_instances(left_path, right_path)

    assert report['equal'] is False
    assert report['outputs']['mismatched_rows_count'] == 1
    assert report['outputs']['column_mismatch_counts']['HVAC energy'] == 1


def test_compare_simulation_instances_detects_input_set_changes(tmp_path):
    left = _make_parametric_df()
    right = _make_parametric_df()
    right.loc[right['ComfStand'] == 2, 'ComfStand'] = 3

    left_path = tmp_path / 'left_input_diff.pkl'
    right_path = tmp_path / 'right_input_diff.pkl'
    left.to_pickle(left_path)
    right.to_pickle(right_path)

    report = compare_simulation_instances(left_path, right_path)

    assert report['equal'] is False
    assert report['inputs']['same_input_set'] is False
    assert report['inputs']['missing_in_right_count'] == 1
    assert report['inputs']['missing_in_left_count'] == 1


def test_compare_simulation_instances_accepts_instance_like_objects():
    left = DummySimulation(_make_parametric_df(), run_type='parametric')
    right = DummySimulation(_make_parametric_df(), run_type='parametric')

    report = compare_simulation_instances(left, right, compare_attrs=False)

    assert report['equal'] is True
    assert report['left']['source_type'] == 'instance_memory'
    assert report['right']['source_type'] == 'instance_memory'


def test_compare_latest_pickles_in_folders_uses_newest_pickle(tmp_path):
    left_dir = tmp_path / 'left'
    right_dir = tmp_path / 'right'
    left_dir.mkdir()
    right_dir.mkdir()

    df_base = _make_parametric_df()
    df_old = _make_parametric_df()
    df_old.loc[df_old['ComfStand'] == 1, 'HVAC energy'] = 999.0

    left_old = left_dir / 'old_left.pkl'
    left_new = left_dir / 'new_left.pkl'
    right_old = right_dir / 'old_right.pkl'
    right_new = right_dir / 'new_right.pkl'

    df_old.to_pickle(left_old)
    df_base.to_pickle(left_new)
    df_old.to_pickle(right_old)
    df_base.to_pickle(right_new)

    os.utime(left_old, (1000, 1000))
    os.utime(right_old, (1000, 1000))
    os.utime(left_new, (2000, 2000))
    os.utime(right_new, (2000, 2000))

    report = compare_latest_pickles_in_folders(left_dir=left_dir, right_dir=right_dir)

    assert report['equal'] is True
    assert report['left_latest_pickle'] == str(left_new.resolve())
    assert report['right_latest_pickle'] == str(right_new.resolve())
    assert report['comparison']['equal'] is True


def test_compare_multiple_pickles_with_reference_by_path(tmp_path):
    df_ref = _make_parametric_df()
    df_equal = _make_parametric_df()
    df_diff = _make_parametric_df()
    df_diff.loc[df_diff['ComfStand'] == 2, 'HVAC energy'] = -1.0

    ref_path = tmp_path / 'ref.pkl'
    equal_path = tmp_path / 'equal.pkl'
    diff_path = tmp_path / 'diff.pkl'

    df_ref.to_pickle(ref_path)
    df_equal.to_pickle(equal_path)
    df_diff.to_pickle(diff_path)

    report = compare_multiple_pickles_with_reference(
        pickle_paths=[diff_path, ref_path, equal_path],
        reference=ref_path,
    )

    assert report['total_pickles'] == 3
    assert report['compared_pickles_count'] == 2
    assert report['equal_count'] == 1
    assert report['different_count'] == 1
    assert report['equal_all'] is False

    by_name = {Path(item['pickle']).name: item['equal'] for item in report['comparisons']}
    assert by_name['equal.pkl'] is True
    assert by_name['diff.pkl'] is False


def test_compare_multiple_pickles_with_reference_by_index_from_directory(tmp_path):
    df_ref = _make_parametric_df()
    df_equal = _make_parametric_df()
    df_diff = _make_parametric_df()
    df_diff.loc[df_diff['ComfStand'] == 0, 'HVAC energy'] = 123.0

    ref_path = tmp_path / 'a_ref.pkl'
    equal_path = tmp_path / 'b_equal.pkl'
    diff_path = tmp_path / 'c_diff.pkl'

    df_ref.to_pickle(ref_path)
    df_equal.to_pickle(equal_path)
    df_diff.to_pickle(diff_path)

    report = compare_multiple_pickles_with_reference(
        directory=tmp_path,
        glob_pattern='*.pkl',
        order_by='name',
        descending=False,
        reference=0,
    )

    assert Path(report['reference_pickle']).name == 'a_ref.pkl'
    assert report['total_pickles'] == 3
    assert report['equal_count'] == 1
    assert report['different_count'] == 1


def test_compare_multiple_pickles_with_reference_from_mixed_sources(tmp_path):
    source_a = tmp_path / 'source_a'
    source_b = tmp_path / 'source_b'
    source_a.mkdir()
    source_b.mkdir()

    df_ref = _make_parametric_df()
    df_equal = _make_parametric_df()
    df_diff = _make_parametric_df()
    df_diff.loc[df_diff['ComfStand'] == 1, 'HVAC energy'] = 777.0

    ref_path = source_a / 'ref.pkl'
    equal_path = source_b / 'equal.pkl'
    diff_path = source_b / 'diff.pkl'

    df_ref.to_pickle(ref_path)
    df_equal.to_pickle(equal_path)
    df_diff.to_pickle(diff_path)

    report = compare_multiple_pickles_with_reference(
        pickle_sources=[source_a, str(source_b / '*.pkl')],
        reference='ref.pkl',
        order_by='name',
        descending=False,
    )

    assert report['total_pickles'] == 3
    assert report['equal_count'] == 1
    assert report['different_count'] == 1


def test_compare_multiple_pickles_with_reference_accepts_pickle_list_alias(tmp_path):
    df_ref = _make_parametric_df()
    df_equal = _make_parametric_df()

    ref_path = tmp_path / 'ref_alias.pkl'
    equal_path = tmp_path / 'equal_alias.pkl'
    df_ref.to_pickle(ref_path)
    df_equal.to_pickle(equal_path)

    report = compare_multiple_pickles_with_reference(
        pickle_list=[ref_path, equal_path],
        reference='ref_alias.pkl',
    )

    assert report['total_pickles'] == 2
    assert report['compared_pickles_count'] == 1
    assert report['equal_count'] == 1
    assert report['equal_all'] is True


def test_compare_simulation_instances_relaxed_mode_with_reference_matching():
    left = _make_parametric_df().copy()
    right = _make_parametric_df().copy()

    left['ComfStand'] = [0, 1, 2]
    right['ComfStand'] = [10, 11, 12]
    # Keep outputs equivalent so relaxed/reference mode can match behaviour.
    left['HVAC energy'] = [100.0, 200.0, 300.0]
    right['HVAC energy'] = [100.0, 200.0, 300.0]

    report_strict = compare_simulation_instances(
        left,
        right,
        compare_attrs=False,
        equal_mode='strict',
        inputs_mismatch_strategy='auto',
        reference_columns=['ComfStand'],
    )
    report_relaxed = compare_simulation_instances(
        left,
        right,
        compare_attrs=False,
        equal_mode='relaxed',
        inputs_mismatch_strategy='auto',
        reference_columns=['ComfStand'],
    )

    assert report_strict['equal'] is False
    assert report_relaxed['equal'] is True
    assert report_relaxed['reference']['enabled'] is True
    assert report_relaxed['reference']['pairs_compared'] == 3
    assert report_relaxed['reference']['all_pairs_equal'] is True


def test_compare_multiple_pickles_with_reference_relaxed_mode(tmp_path):
    df_ref = _make_parametric_df().copy()
    df_shifted = _make_parametric_df().copy()
    df_shifted['ComfStand'] = [10, 11, 12]

    ref_path = tmp_path / 'ref_relaxed.pkl'
    shifted_path = tmp_path / 'shifted_relaxed.pkl'
    df_ref.to_pickle(ref_path)
    df_shifted.to_pickle(shifted_path)

    strict_report = compare_multiple_pickles_with_reference(
        pickle_paths=[ref_path, shifted_path],
        reference='ref_relaxed.pkl',
        equal_mode='strict',
        compare_attrs=False,
    )
    relaxed_report = compare_multiple_pickles_with_reference(
        pickle_paths=[ref_path, shifted_path],
        reference='ref_relaxed.pkl',
        equal_mode='relaxed',
        inputs_mismatch_strategy='auto',
        reference_columns=['ComfStand'],
        compare_attrs=False,
    )

    assert strict_report['different_count'] == 1
    assert strict_report['equal_all'] is False
    assert relaxed_report['equal_count'] == 1
    assert relaxed_report['equal_all'] is True


def test_comparison_session_stores_attributes_and_history(tmp_path):
    session = SimulationComparisonSession(
        compare_attrs=False,
        inputs_mismatch_strategy='auto',
        equal_mode='relaxed',
    )

    left = _make_parametric_df().copy()
    right = _make_parametric_df().copy()
    right['ComfStand'] = [10, 11, 12]

    report = session.compare(left=left, right=right, reference_columns=['ComfStand'])

    assert isinstance(report, dict)
    assert session.last_operation == 'compare'
    assert session.last_report is not None
    assert session.last_comparison is not None
    assert session.last_inputs is not None
    assert session.last_outputs is not None
    assert session.last_reference is not None
    assert len(session.history) == 1

    summary = session.get_last_summary()
    assert summary['operation'] == 'compare'
    assert 'equal' in summary

    report_path = tmp_path / 'session_last_report.json'
    saved_path = session.save_last_report_json(report_path)
    assert Path(saved_path).is_file()


def test_comparison_session_compare_latest_sources_in_folders(tmp_path):
    left_dir = tmp_path / 'left_csv'
    right_dir = tmp_path / 'right_csv'
    left_dir.mkdir()
    right_dir.mkdir()

    left_df = _make_parametric_df()
    right_df = _make_parametric_df()

    left_file = left_dir / 'outputs_param_simulation_left.csv'
    right_file = right_dir / 'outputs_param_simulation_right.csv'
    left_df.to_csv(left_file, index=False)
    right_df.to_csv(right_file, index=False)

    session = SimulationComparisonSession(compare_attrs=False)
    report = session.compare_latest_sources_in_folders(
        left_dir=left_dir,
        right_dir=right_dir,
        glob_pattern='*.csv',
        preferred_name_tokens=['outputs_param_simulation'],
    )

    assert isinstance(report, dict)
    assert report['left_source'].endswith('outputs_param_simulation_left.csv')
    assert report['right_source'].endswith('outputs_param_simulation_right.csv')
    assert session.last_operation == 'compare_latest_sources_in_folders'
    assert session.last_comparison is not None


def test_comparison_session_compare_selected_outputs_from_last_compare():
    left_df = pd.DataFrame(
        {
            'idf': ['A', 'B'],
            'epw': ['Seville.epw', 'Sydney.epw'],
            'DistrictHeating:Facility': [10.0, 20.0],
            'DistrictCooling:Facility': [5.0, 6.0],
        }
    )
    right_df = pd.DataFrame(
        {
            'idf': ['A', 'B'],
            'epw': ['Seville.epw', 'Sydney.epw'],
            'DistrictHeating:Facility': [11.0, 20.0],
            'DistrictCooling:Facility': [4.0, 8.0],
        }
    )

    left_df.attrs['parameters_names'] = ['idf', 'epw']
    left_df.attrs['outputs_names'] = ['DistrictHeating:Facility', 'DistrictCooling:Facility']
    right_df.attrs['parameters_names'] = ['idf', 'epw']
    right_df.attrs['outputs_names'] = ['DistrictHeating:Facility', 'DistrictCooling:Facility']

    session = SimulationComparisonSession(compare_attrs=False)
    session.compare(
        left=left_df,
        right=right_df,
        input_columns=['idf', 'epw'],
    )

    output_report = session.compare_selected_outputs(
        outputs=['DistrictHeating:Facility', 'DistrictCooling:Facility'],
    )

    assert output_report['rows_compared'] == 2
    assert output_report['left_unmatched_rows'] == 0
    assert output_report['right_unmatched_rows'] == 0

    changes_by_case = output_report['changes_by_case']
    assert 'DistrictHeating:Facility_delta' in changes_by_case.columns
    assert 'DistrictCooling:Facility_delta' in changes_by_case.columns
    assert float(changes_by_case['DistrictHeating:Facility_delta'].sum()) == 1.0
    assert float(changes_by_case['DistrictCooling:Facility_delta'].sum()) == 1.0

    changes_by_categories = output_report['changes_by_categories']
    assert 'DistrictHeating:Facility_delta_sum' in changes_by_categories.columns
    assert 'DistrictCooling:Facility_delta_sum' in changes_by_categories.columns

    assert session.last_output_changes is not None
    assert session.last_output_changes_by_case is not None
    assert session.last_output_changes_by_categories is not None


