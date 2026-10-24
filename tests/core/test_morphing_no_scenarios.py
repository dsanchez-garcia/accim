"""Restore original weather files even when the external tool emits no scenario."""

import subprocess

import pytest

from accim.data.morphing import morph_epws


@pytest.mark.parametrize('delete_intermediates', [False, True])
@pytest.mark.parametrize('emit_scenario', [False, True])
def test_morphing_restores_each_original(tmp_path, monkeypatch, delete_intermediates, emit_scenario):
    monkeypatch.chdir(tmp_path)
    originals = {'Seville.epw': b'seville-original\r\n', 'Granada.epw': b'granada-original\r\n'}
    for name, content in originals.items():
        (tmp_path / name).write_bytes(content)
    commands = []

    def fake_java(command, **kwargs):
        commands.append(command)
        # Only one input produces a scenario; the other must still be restored.
        if emit_scenario and 'Seville.epw' in command:
            (tmp_path / 'Seville' / 'generated_ssp245_2050.epw').write_bytes(b'future-weather')
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'run', fake_java)
    morph_epws(
        fwg_path='FutureWeatherGenerator.jar', epw_filepaths=list(originals),
        delete_morphing_files=delete_intermediates,
    )

    assert len(commands) == 2
    for name, content in originals.items():
        assert (tmp_path / name).read_bytes() == content
        assert (tmp_path / name.removesuffix('.epw')).exists() is (not delete_intermediates)
    future = tmp_path / 'Seville_ssp245_2050.epw'
    assert future.exists() is emit_scenario
    if emit_scenario:
        assert future.read_bytes() == b'future-weather'

