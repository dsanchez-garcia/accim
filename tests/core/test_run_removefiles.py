"""Tests for accim.run.remove_files (removefiles in accim 0.x).

Before, removefiles deleted every file of the working folder except the '.py', '.idf', '.epw',
'.csv' and '.eso' files (Jupyter notebooks, spreadsheets, notes...), deleted any CSV ending with
'Table.csv', 'Meter.csv' or 'Zsz.csv', and failed if the folder had subfolders. Now it only
deletes the simulation files of run_ep, which are named 'IDF name[EPW name'.
"""
import os

import pytest

from accim.run import run

SIMULATION = 'model[CS_INT EN16798[CA_1[CM_3[HM_2[NS_X[Spain_Seville_Present'

KEPT = [
    'analysis.ipynb',
    'notes.txt',
    'results.xlsx',
    'MyTable.csv',
    'script.py',
    'model.idf',
    'model[CS_INT EN16798[CA_1[CM_3[HM_2[NS_X.idf',
    'Spain_Seville_Present.epw',
    f'{SIMULATION}.csv',
    f'{SIMULATION}.eso',
]

DELETED = [
    f'{SIMULATION}.audit',
    f'{SIMULATION}.eio',
    f'{SIMULATION}.end',
    f'{SIMULATION}.err',
    f'{SIMULATION}.mtr',
    f'{SIMULATION}.rvaudit',
    f'{SIMULATION}.shd',
    f'{SIMULATION}Table.htm',
    f'{SIMULATION}Table.csv',
    f'{SIMULATION}Meter.csv',
    f'{SIMULATION}Zsz.csv',
]


def _simulation_folder(tmp_path, monkeypatch):
    for name in KEPT + DELETED:
        (tmp_path / name).write_text('')
    for folder in ['multi_runs', 'old[results']:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / 'in.idf').write_text('')
    monkeypatch.chdir(tmp_path)


def _assert_only_the_simulation_files_were_deleted(tmp_path):
    assert sorted(os.listdir(tmp_path)) == sorted(KEPT + ['multi_runs', 'old[results'])
    assert (tmp_path / 'multi_runs' / 'in.idf').exists()


def test_remove_files_deletes_only_the_simulation_files(tmp_path, monkeypatch):
    _simulation_folder(tmp_path, monkeypatch)

    run.remove_files()

    _assert_only_the_simulation_files_were_deleted(tmp_path)


def test_removefiles_is_a_deprecated_alias_of_remove_files(tmp_path, monkeypatch):
    _simulation_folder(tmp_path, monkeypatch)

    with pytest.warns(DeprecationWarning, match='use accim.run.remove_files instead'):
        run.removefiles()

    _assert_only_the_simulation_files_were_deleted(tmp_path)
