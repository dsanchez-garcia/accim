"""Tests for the files that resume a session (accim.utils.session): Table.save and Table.load, which save and read one
table of accim.data.postprocessing.main.Table, and save_session and load_session, which save and read several objects,
each in a pickle file (to resume the session) and a JSON file (to read it).

The tables are those of the sample CSV files of the repository, with a fake IDF (see test_table_methods).
"""
import copy
import datetime
import inspect
import json
import os
import pickle
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import accim
from accim.data.postprocessing.main import Table
from accim.utils import session

from .test_table_methods import SAMPLE_CSVS, _sample_table

pytestmark = [pytest.mark.filterwarnings('ignore::pandas.errors.PerformanceWarning'),
              pytest.mark.skipif(len(SAMPLE_CSVS) != 4, reason='needs the sample CSV files of the repository')]

COOLING = 'Building_Total_Cooling Energy Demand (kWh/m2) (summed)'


@pytest.fixture(scope='module')
def sample_folder(tmp_path_factory):
    folder = tmp_path_factory.mktemp('sample_csvs')
    for csv in SAMPLE_CSVS:
        shutil.copy(csv, folder)
    return folder


@pytest.fixture(scope='module')
def runperiod(sample_folder):
    return _sample_table(sample_folder)


@pytest.fixture
def table(runperiod):
    """A copy of the run period table, formatted and reshaped, which the test can change."""
    table = copy.deepcopy(runperiod)
    table.format_table(type_of_table='energy demand')
    table.wrangled_table(reshaping='unstack', vars_to_gather=['ComfMod'], baseline='CM_0',
                         comparison_mode=['baseline compared to others'], comparison_cols=['relative', 'absolute'])
    return table


def _strict_json(path):
    """The content of a JSON file, which must be valid JSON (without NaN or Infinity)."""
    def refuse(constant):
        raise ValueError(f'{constant} is not valid JSON')

    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=refuse)


# Table.save and Table.load -------------------------------------------------------------------------------------------

def test_a_saved_table_is_loaded_with_all_its_attributes(table, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    paths = table.save('case_study')

    assert paths == (str(tmp_path / 'case_study.pkl'), str(tmp_path / 'case_study.json'))
    assert sorted(os.listdir(tmp_path)) == ['case_study.json', 'case_study.pkl']
    assert 'Table.load resumes it' in capsys.readouterr().out
    loaded = Table.load('case_study.pkl')
    assert isinstance(loaded, Table) and sorted(vars(loaded)) == sorted(vars(table))
    for name in ('df', 'df_backup', 'wrangled_df_unstacked'):
        pd.testing.assert_frame_equal(getattr(loaded, name), getattr(table, name))
    for name in ('arguments', 'frequency', 'occupied_zone_list', 'block_list', 'cols_for_multiindex',
                 'suggested_vars_dict', 'type_of_table', 'custom_cols', 'indexcols', 'val_cols'):
        assert getattr(loaded, name) == getattr(table, name), name
    # Its methods work as before saving it
    loaded.format_table(type_of_table='custom', custom_cols=[COOLING])
    assert list(loaded.df.columns) == loaded.indexcols + [COOLING]
    assert loaded.df[COOLING].tolist() == table.df_backup[COOLING].tolist()


def test_the_json_file_of_a_table_can_be_read(table, tmp_path):
    content = _strict_json(table.save(tmp_path / 'case_study')[1])

    assert list(content)[:4] == ['description', 'accim_version', 'saved', 'folder']
    assert 'case_study.pkl' in content['description'] and content['accim_version'] == accim.__version__
    assert list(content)[4:] == ['arguments', 'frequency', 'occupied_zone_list', 'hvac_zone_list', 'block_list',
                                 'cols_for_multiindex', 'suggested_vars_dict', 'type_of_table', 'custom_cols',
                                 'indexcols', 'val_cols', 'df', 'wrangled_df_unstacked']
    assert content['arguments']['datasets'] == [csv.name for csv in SAMPLE_CSVS]
    assert content['arguments']['frequency'] == content['frequency'] == 'runperiod'
    assert content['suggested_vars_dict'] == {'ComfMod': ['CM_0', 'CM_3'],
                                              'EPW_City_or_subcountry': ['Aberdeen', 'London']}
    assert content['type_of_table'] == 'energy demand'
    # The table as format_table left it: its number of rows and the values of its rows, as {column: [values]}
    assert (content['df']['number_of_rows'], content['df']['rows_shown']) == (4, 4)
    rows = content['df']['data']
    assert list(rows) == list(table.df.columns)
    assert rows[COOLING] == pytest.approx(table.df[COOLING].tolist())
    assert rows['ComfMod'] == ['CM_0', 'CM_0', 'CM_3', 'CM_3']
    # The reshaped table: its index first, and the names of its columns of several levels joined with '['
    unstacked = content['wrangled_df_unstacked']['data']
    assert unstacked['EPW_City_or_subcountry'] == ['Aberdeen', 'London']
    assert f'{COOLING}[CM_0' in unstacked and len(unstacked) == 1 + table.wrangled_df_unstacked.shape[1]
    assert 'the values of the first 1000 of them' in content['description']


def test_the_files_of_a_table_take_the_name_without_its_extension(table, tmp_path):
    for name in ('table.pkl', 'table.json', 'table.PKL'):
        assert table.save(tmp_path / name) == (str(tmp_path / 'table.pkl'), str(tmp_path / 'table.json'))
    assert sorted(os.listdir(tmp_path)) == ['table.json', 'table.pkl']
    # The extension can be left out when the table is loaded
    assert Table.load(tmp_path / 'table').frequency == 'runperiod'


def test_load_explains_the_files_that_are_not_tables(table, tmp_path):
    table.save(tmp_path / 'table')
    session.save_session(tmp_path / 'session', table=table)
    pd.to_pickle(pd.DataFrame({'a': [1]}), tmp_path / 'frame.pkl')

    with pytest.raises(ValueError, match=r'only for reading: open the pickle file, .*table\.pkl'):
        Table.load(tmp_path / 'table.json')
    with pytest.raises(ValueError, match='It is a session saved with save_session: open it with '
                                         'accim.utils.load_session'):
        Table.load(tmp_path / 'session.pkl')
    with pytest.raises(ValueError, match='does not have a table saved with Table.save'):
        Table.load(tmp_path / 'frame.pkl')
    with pytest.raises(FileNotFoundError, match='There is no file .*missing nor .*missing.pkl'):
        Table.load(tmp_path / 'missing')


def test_a_table_that_only_wrote_the_concatenated_csv_file_cannot_be_saved(tmp_path):
    for csv in SAMPLE_CSVS:
        shutil.copy(csv, tmp_path)
    written = _sample_table(tmp_path, concatenated_csv_name='concatenated')

    with pytest.raises(ValueError, match='only writes the concatenated CSV file'):
        written.save(tmp_path / 'table')
    assert not list(tmp_path.glob('table.*'))


def test_the_table_keeps_its_arguments_and_the_columns_of_format_table(runperiod):
    table = copy.deepcopy(runperiod)

    assert list(table.arguments) == list(inspect.signature(Table).parameters)
    assert table.arguments['level_agg_func'] == ['sum', 'mean'] and table.arguments['idf_path'] == 'TestModel.idf'
    assert not hasattr(table, 'type_of_table')
    # A generator of columns is read once
    table.format_table(type_of_table='custom', custom_cols=(c for c in ['Building_Total_Cooling Energy Demand']))
    assert (table.type_of_table, table.custom_cols) == ('custom', ['Building_Total_Cooling Energy Demand'])
    assert table.val_cols == [COOLING, 'Building_Total_Cooling Energy Demand (kWh/m2) (mean)']
    table.format_table()
    assert (table.type_of_table, table.custom_cols) == ('all', [])
    # A call that fails leaves the whole table, as its columns say
    table.format_table(type_of_table='energy demand')
    with pytest.raises(ValueError, match='You have not selected any column'):
        table.format_table(type_of_table='custom', custom_cols=['__no_such_column__'])
    assert (table.type_of_table, table.custom_cols) == ('all', []) and table.df is table.df_backup


# save_session and load_session ---------------------------------------------------------------------------------------

class _Thing:
    def __repr__(self):
        return '<a thing>'


def test_a_session_is_saved_and_loaded_with_its_objects(table, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    frame = pd.DataFrame([[1.0, np.nan], [np.inf, -np.inf]], index=pd.Index(['r1', 'r2'], name='row'),
                         columns=pd.MultiIndex.from_tuples([('a', 'x'), ('a', 'y')]))
    objects = dict(
        dataset_runperiod=table,
        csvs=[csv.name for csv in SAMPLE_CSVS],
        settings={'processes': np.int64(4), 'ratio': np.float64(0.5), 'missing': float('nan'), 1: 'one'},
        frame=frame,
        series=pd.Series([1.5, 2.5], index=['x', 'y']),
        array=np.array([[1, 2], [3, 4]]),
        when=datetime.date(2026, 11, 3),
        path=Path('a') / 'b.csv',
        tags={'b', 'a'},
        thing=_Thing(),
    )

    paths = session.save_session('case_study', **objects)

    assert paths == (str(tmp_path / 'case_study.pkl'), str(tmp_path / 'case_study.json'))
    assert 'load_session resumes it' in capsys.readouterr().out
    loaded = session.load_session('case_study')
    assert list(loaded) == list(objects)
    assert 'dataset_runperiod (Table), csvs (list)' in capsys.readouterr().out
    pd.testing.assert_frame_equal(loaded['dataset_runperiod'].df, table.df)
    pd.testing.assert_frame_equal(loaded['frame'], frame)
    assert loaded['csvs'] == objects['csvs'] and loaded['when'] == objects['when'] and loaded['tags'] == {'a', 'b'}
    assert isinstance(loaded['thing'], _Thing)

    content = _strict_json(paths[1])
    assert list(content) == ['description', 'accim_version', 'saved', 'folder', 'objects']
    assert content['folder'] == str(tmp_path) and 'case_study.pkl' in content['description']
    readable = content['objects']
    assert {name: value['type'] for name, value in readable.items()} == {
        'dataset_runperiod': 'Table', 'csvs': 'list', 'settings': 'dict', 'frame': 'DataFrame', 'series': 'Series',
        'array': 'ndarray', 'when': 'date', 'path': type(objects['path']).__name__, 'tags': 'set', 'thing': '_Thing'}
    assert readable['dataset_runperiod']['value']['suggested_vars_dict']['ComfMod'] == ['CM_0', 'CM_3']
    assert readable['settings']['value'] == {'processes': 4, 'ratio': 0.5, 'missing': None, '1': 'one'}
    assert readable['frame']['value'] == {'number_of_rows': 2, 'rows_shown': 2, 'data': {
        'row': ['r1', 'r2'], 'a[x': [1.0, 'Infinity'], 'a[y': [None, '-Infinity']}}
    assert readable['series']['value'] == {'number_of_rows': 2, 'rows_shown': 2, 'data': {'x': 1.5, 'y': 2.5}}
    assert readable['array']['value'] == [[1, 2], [3, 4]]
    assert readable['when']['value'] == '2026-11-03'
    assert readable['path']['value'] == os.path.join('a', 'b.csv')
    assert readable['tags']['value'] == ['a', 'b'] and readable['thing']['value'] == '<a thing>'


def test_the_json_files_keep_the_labels_of_the_rows(tmp_path):
    # As the tables of wrangled_table with transpose=True, whose index has no names
    transposed = pd.DataFrame({'Aberdeen': [1.0, 2.0], 'London': [3.0, 4.0]},
                              index=pd.MultiIndex.from_tuples([('Cooling', 'Stat'), ('Cooling', 'Adap')]))
    numbers = pd.DataFrame({'a': [1, 2, 3]})

    paths = session.save_session(tmp_path / 'frames', transposed=transposed, numbers=numbers,
                                 labelled=pd.DataFrame({'value': [1.0]}, index=['x']), filtered=numbers.iloc[[0, 2]])

    readable = {name: value['value']['data'] for name, value in _strict_json(paths[1])['objects'].items()}
    assert readable['transposed'] == {'level_0': ['Cooling', 'Cooling'], 'level_1': ['Stat', 'Adap'],
                                      'Aberdeen': [1.0, 2.0], 'London': [3.0, 4.0]}
    assert readable['labelled'] == {'index': ['x'], 'value': [1.0]}
    # The row numbers of the default index are left out, but not those of a selection of rows
    assert readable['numbers'] == {'a': [1, 2, 3]}
    assert readable['filtered'] == {'index': [0, 2], 'a': [1, 3]}


def test_the_json_files_show_the_first_rows_of_the_tables(table, tmp_path):
    frame = pd.DataFrame({'a': range(2500), 'b': [0.5] * 2500})

    paths = session.save_session(tmp_path / 'default', frame=frame, column=frame['a'], csvs=['a.csv'] * 1200)

    readable = _strict_json(paths[1])
    assert 'the values of the first 1000 of them (the pickle file has all of them)' in readable['description']
    shown = readable['objects']['frame']['value']
    assert (shown['number_of_rows'], shown['rows_shown'], shown['data']['a'][-1]) == (2500, 1000, 999)
    assert readable['objects']['column']['value']['rows_shown'] == 1000
    # Only the tables are shortened
    assert len(readable['objects']['csvs']['value']) == 1200
    pd.testing.assert_frame_equal(session.load_session(paths[0])['frame'], frame)
    few = _strict_json(session.save_session(tmp_path / 'few', json_max_rows=10, frame=frame)[1])
    assert few['objects']['frame']['value']['rows_shown'] == len(few['objects']['frame']['value']['data']['a']) == 10
    every = _strict_json(session.save_session(tmp_path / 'all', json_max_rows=None, frame=frame)[1])
    assert every['objects']['frame']['value']['rows_shown'] == 2500 and 'shows all its rows' in every['description']
    content = _strict_json(table.save(tmp_path / 'table', json_max_rows=2)[1])
    assert (content['df']['number_of_rows'], content['df']['rows_shown'], len(content['df']['data']['ComfMod'])) == \
        (4, 2, 2)
    for wrong in (-1, 1.5, True, '10'):
        with pytest.raises(ValueError, match='json_max_rows'):
            session.save_session(tmp_path / 'wrong', json_max_rows=wrong, frame=frame)
        with pytest.raises(ValueError, match='json_max_rows'):
            table.save(tmp_path / 'wrong', json_max_rows=wrong)
    assert not list(tmp_path.glob('wrong*'))


def test_the_pickle_file_is_saved_even_if_the_json_file_cannot_be(table, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise MemoryError('no memory left')

    monkeypatch.setattr(session, '_json_value', fail)

    with pytest.raises(RuntimeError, match=r'The pickle file .*session\.pkl has been saved, but not the JSON file'):
        session.save_session(tmp_path / 'session', table=table)
    with pytest.raises(RuntimeError, match=r'The pickle file .*table\.pkl has been saved, but not the JSON file'):
        table.save(tmp_path / 'table')

    assert sorted(os.listdir(tmp_path)) == ['session.pkl', 'table.pkl']
    pd.testing.assert_frame_equal(session.load_session(tmp_path / 'session.pkl')['table'].df, table.df)
    pd.testing.assert_frame_equal(Table.load(tmp_path / 'table.pkl').df, table.df)


def test_save_session_names_the_objects_that_pickle_cannot_save(tmp_path):
    with pytest.raises(ValueError, match='Give the objects to save as keyword arguments'):
        session.save_session(tmp_path / 'session')
    with pytest.raises(TypeError, match=r"The object 'reader' \(function\) cannot be saved in a pickle file"):
        session.save_session(tmp_path / 'session', csvs=['a.csv'], reader=lambda path: path)
    assert not list(tmp_path.iterdir())


def test_a_failed_save_keeps_the_files_saved_before(tmp_path):
    session.save_session(tmp_path / 'session', csvs=['a.csv'])

    with pytest.raises(TypeError):
        session.save_session(tmp_path / 'session', csvs=['b.csv'], reader=lambda path: path)

    assert sorted(os.listdir(tmp_path)) == ['session.json', 'session.pkl']
    assert session.load_session(tmp_path / 'session.pkl') == {'csvs': ['a.csv']}
    assert _strict_json(tmp_path / 'session.json')['objects'] == {'csvs': {'type': 'list', 'value': ['a.csv']}}


def test_load_session_explains_the_files_that_are_not_sessions(table, tmp_path):
    table.save(tmp_path / 'table')
    with open(tmp_path / 'other.pkl', 'wb') as handle:
        pickle.dump({'objects': {}}, handle)

    with pytest.raises(ValueError, match='It is a table saved with Table.save: open it with Table.load'):
        session.load_session(tmp_path / 'table.pkl')
    with pytest.raises(ValueError, match='is not a session saved with save_session'):
        session.load_session(tmp_path / 'other.pkl')
    with pytest.raises(ValueError, match='only for reading'):
        session.load_session(tmp_path / 'table.json')
    with pytest.raises(FileNotFoundError, match=r'There is no file .*missing\.pkl\.$'):
        session.load_session(tmp_path / 'missing.pkl')


def test_the_functions_of_the_sessions_are_in_accim_utils():
    from accim.utils import load_session, save_session

    assert (save_session, load_session) == (session.save_session, session.load_session)
    assert {'save_session', 'load_session'} <= set(accim.utils.__all__)
