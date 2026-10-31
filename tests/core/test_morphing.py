"""Tests for accim.data.morphing.morph_epws, with the Java tool (FutureWeatherGenerator) mocked.

morph_epws moves each EPW to a folder of its own, morphs it there and moves back the original EPW and the
scenario EPWs, renamed after the original. The folder that it moves them to was only defined when a scenario EPW
was found, so an EPW for which the tool produced none stopped it with a NameError ('parent_folder_path') and was
left in its folder. Ported from the tests of the branches refactor/sim-v1 and review/refactor-sim-v1-20261024.
"""
import os
import subprocess

import pytest

from accim.data.morphing import morph_epws

SCENARIOS = ['ssp126_2050', 'ssp126_2080', 'ssp245_2050', 'ssp245_2080', 'ssp370_2050', 'ssp370_2080',
             'ssp585_2050', 'ssp585_2080']


@pytest.mark.parametrize('delete_morphing_files', [False, True])
@pytest.mark.parametrize('emit_scenario', [False, True])
def test_morph_epws_moves_back_every_original_epw(tmp_path, monkeypatch, delete_morphing_files, emit_scenario):
    monkeypatch.chdir(tmp_path)
    originals = {'Seville.epw': b'seville-original\r\n', 'Granada.epw': b'granada-original\r\n'}
    for name, content in originals.items():
        (tmp_path / name).write_bytes(content)
    commands = []

    def fake_java(command, **kwargs):
        commands.append(command)
        # Only one EPW produces a scenario; the other must also be moved back
        if emit_scenario and 'Seville.epw' in command:
            (tmp_path / 'Seville' / 'generated_ssp245_2050.epw').write_bytes(b'future-weather')
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'run', fake_java)
    morph_epws(fwg_path='FutureWeatherGenerator.jar', epw_filepaths=list(originals),
               delete_morphing_files=delete_morphing_files)

    assert len(commands) == 2
    for name, content in originals.items():
        assert (tmp_path / name).read_bytes() == content
        assert (tmp_path / name[:-len('.epw')]).exists() is (not delete_morphing_files)
    future = tmp_path / 'Seville_ssp245_2050.epw'
    assert future.exists() is emit_scenario
    if emit_scenario:
        assert future.read_bytes() == b'future-weather'


def test_morph_epws_only_morphs_the_listed_epws(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ('Seville.epw', 'Other.epw'):
        (tmp_path / name).write_text('EPW', encoding='utf-8')
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: subprocess.CompletedProcess(command, 0))

    morph_epws(fwg_path='FutureWeatherGenerator.jar', epw_filepaths=['Seville.epw'], delete_morphing_files=True)

    assert (tmp_path / 'Seville.epw').exists()
    assert (tmp_path / 'Other.epw').exists()
    assert not (tmp_path / 'Seville').exists()


def test_morph_epws_morphs_every_epw_of_the_working_folder_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ('Seville.epw', 'Granada.epw', 'notes.txt'):
        (tmp_path / name).write_text(name, encoding='utf-8')
    commands = []

    def fake_java(command, **kwargs):
        commands.append(command)
        folder = tmp_path / ('Seville' if 'Seville.epw' in command else 'Granada')
        # The tool writes an EPW for each scenario, and other files
        for scenario in SCENARIOS:
            (folder / f'{folder.name}_Ensemble_{scenario}.epw').write_text(scenario, encoding='utf-8')
        (folder / f'{folder.name}_Ensemble_statistics.csv').write_text('', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'run', fake_java)
    morph_epws(fwg_path='FutureWeatherGenerator.jar')

    assert len(commands) == 2
    for command in commands:
        assert ' 1 72 "' in command and command.endswith('/" True 0 True')
    expected = ['Granada.epw', 'Seville.epw', 'notes.txt'] + [
        f'{city}_{scenario}.epw' for city in ('Granada', 'Seville') for scenario in SCENARIOS]
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(expected)
    assert (tmp_path / 'Seville_ssp585_2080.epw').read_text(encoding='utf-8') == 'ssp585_2080'
    assert (tmp_path / 'Seville.epw').read_text(encoding='utf-8') == 'Seville.epw'


def test_morph_epws_gives_its_options_to_futureweathergenerator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('EPW', encoding='utf-8')
    commands = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: commands.append(command))

    morph_epws(fwg_path='C:/FWG/FutureWeatherGenerator.jar', fwg_options_gcms='CanESM5,MIROC6',
               fwg_options_ensemble=0, fwg_options_month_transition_hours=24,
               fwg_options_do_multithread_computation=False, fwg_options_interpolation_method_id=2,
               fwg_options_do_limit_variables=False)

    folder = os.path.join(os.getcwd(), 'Seville')
    assert commands == [
        f'java -cp "C:/FWG/FutureWeatherGenerator.jar" futureweathergenerator.Morph '
        f'"{os.path.join(folder, "Seville.epw")}" CanESM5,MIROC6 0 24 "{folder}/" False 2 False'
    ]
