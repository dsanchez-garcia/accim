"""Tests for accim.data.morphing.morph_epws, with the Java tool (FutureWeatherGenerator) mocked.

morph_epws moves each EPW to a folder of its own, morphs it there and moves back the original EPW and the
scenario EPWs, renamed after the original. The folder that it moves them to was only defined when a scenario EPW
was found, so an EPW for which the tool produced none stopped it with a NameError ('parent_folder_path') and was
left in its folder. Ported from the tests of the branches refactor/sim-v1 and review/refactor-sim-v1-20261024.
"""
import subprocess

import pytest

from accim.data.morphing import morph_epws


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
