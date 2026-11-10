"""Tests for accim.data.morphing.morph_epws, with the Java tool (FutureWeatherGenerator) mocked.

morph_epws moves each EPW to a folder of its own, morphs it there and moves back the original EPW and the
scenario EPWs, renamed after the original. The folder that it moves them to was only defined when a scenario EPW
was found, so an EPW for which the tool produced none stopped it with a NameError ('parent_folder_path') and was
left in its folder. Ported from the tests of the branches refactor/sim-v1 and review/refactor-sim-v1-20261024.

Found on 2026-11-02 (review of 2026-10-24): the command of Java was a string without ``shell=True``, which only
works on Windows, and its exit code was not checked, so a failure of the tool (or no Java) went unnoticed. Now the
command is a list of arguments, and morph_epws raises an error after moving the original EPWs back.
"""
import os
import subprocess
import warnings

import pytest

from accim.data.morphing import DEFAULT_GCMS, morph_epws

SCENARIOS = ['ssp126_2050', 'ssp126_2080', 'ssp245_2050', 'ssp245_2080', 'ssp370_2050', 'ssp370_2080',
             'ssp585_2050', 'ssp585_2080']


def _epw(command):
    """The name of the EPW that a command of Java morphs."""
    return os.path.basename(command[4])


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
        if emit_scenario and _epw(command) == 'Seville.epw':
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
        folder = tmp_path / _epw(command)[:-len('.epw')]
        # The tool writes an EPW for each scenario, and other files
        for scenario in SCENARIOS:
            (folder / f'{folder.name}_Ensemble_{scenario}.epw').write_text(scenario, encoding='utf-8')
        (folder / f'{folder.name}_Ensemble_statistics.csv').write_text('', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'run', fake_java)
    morph_epws(fwg_path='FutureWeatherGenerator.jar')

    assert len(commands) == 2
    for command in commands:
        assert command[6:8] == ['1', '72'] and command[8].endswith('/') and command[9:] == ['True', '0', 'True']
    expected = ['Granada.epw', 'Seville.epw', 'notes.txt'] + [
        f'{city}_{scenario}.epw' for city in ('Granada', 'Seville') for scenario in SCENARIOS]
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(expected)
    assert (tmp_path / 'Seville_ssp585_2080.epw').read_text(encoding='utf-8') == 'ssp585_2080'
    assert (tmp_path / 'Seville.epw').read_text(encoding='utf-8') == 'Seville.epw'


def test_morph_epws_gives_its_options_to_futureweathergenerator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('EPW', encoding='utf-8')
    commands = []
    monkeypatch.setattr(subprocess, 'run',
                        lambda command, **kwargs: commands.append(command) or subprocess.CompletedProcess(command, 0))

    # Without the ensemble, also with Java (finding E4-2 of the review of 1.2.0)
    with pytest.warns(UserWarning, match='With fwg_options_ensemble=0'):
        morph_epws(fwg_path='C:/FWG folder/FutureWeatherGenerator.jar', fwg_options_gcms='CanESM5,MIROC6',
                   fwg_options_ensemble=0, fwg_options_month_transition_hours=24,
                   fwg_options_do_multithread_computation=False, fwg_options_interpolation_method_id=2,
                   fwg_options_do_limit_variables=False)

    # A list of arguments: the paths with blanks need no quotes, on any operating system
    folder = os.path.join(os.getcwd(), 'Seville')
    assert commands == [[
        'java', '-cp', 'C:/FWG folder/FutureWeatherGenerator.jar', 'futureweathergenerator.Morph',
        os.path.join(folder, 'Seville.epw'), 'CanESM5,MIROC6', '0', '24', folder + '/', 'False', '2', 'False']]


@pytest.mark.parametrize('failure, message', [
    (subprocess.CompletedProcess([], 1), r'Seville\.epw \(exit code 1\)'),
    (FileNotFoundError(2, 'The system cannot find the file specified'), r'Seville\.epw \(Java could not be run'),
])
def test_a_failure_of_the_tool_is_reported_after_moving_the_epws_back(tmp_path, monkeypatch, failure, message):
    monkeypatch.chdir(tmp_path)
    for name in ('Seville.epw', 'Granada.epw'):
        (tmp_path / name).write_text(name, encoding='utf-8')

    def fake_java(command, **kwargs):
        if _epw(command) == 'Granada.epw':
            return subprocess.CompletedProcess(command, 0)
        if isinstance(failure, Exception):
            raise failure
        return failure

    monkeypatch.setattr(subprocess, 'run', fake_java)
    with pytest.raises(RuntimeError, match=message) as error:
        morph_epws(fwg_path='FutureWeatherGenerator.jar', delete_morphing_files=True)

    assert 'Granada' not in str(error.value)
    assert sorted(p.name for p in tmp_path.iterdir()) == ['Granada.epw', 'Seville.epw']


# engine='pyfwg' (proposal E4 of accim 1.2.0) ------------------------------------------------------------------------

def _fake_pyfwg(monkeypatch, distribution='global', scenarios=SCENARIOS, error=None):
    """A module pyfwg whose morph_epw_global writes the files of the scenarios with the default names of the tool
    (as the Java tool of the tests above) in output_dir, and returns their paths."""
    import sys
    import types

    calls = []
    module = types.ModuleType('pyfwg')
    module.detect_fwg_tool = lambda jar_path: distribution

    def morph_epw_global(*, epw_paths, fwg_jar_path, output_dir='./morphed_epws', delete_temp_files=True,
                         temp_base_dir='./morphing_temp_results', fwg_show_tool_output=False, fwg_gcms=None,
                         fwg_create_ensemble=None, fwg_month_transition_hours=None, fwg_use_multithreading=None,
                         fwg_interpolation_method_id=None, fwg_limit_variables=None, fwg_add_uhi=None,
                         fwg_version=None):
        calls.append(dict(epw_paths=epw_paths, fwg_jar_path=fwg_jar_path, output_dir=output_dir,
                          delete_temp_files=delete_temp_files, temp_base_dir=temp_base_dir,
                          fwg_show_tool_output=fwg_show_tool_output, fwg_gcms=fwg_gcms,
                          fwg_create_ensemble=fwg_create_ensemble,
                          fwg_month_transition_hours=fwg_month_transition_hours,
                          fwg_use_multithreading=fwg_use_multithreading,
                          fwg_interpolation_method_id=fwg_interpolation_method_id,
                          fwg_limit_variables=fwg_limit_variables, fwg_add_uhi=fwg_add_uhi, fwg_version=fwg_version))
        if error is not None:
            raise error
        created = []
        for epw_path in epw_paths:
            stem = os.path.splitext(os.path.basename(epw_path))[0]
            for scenario in scenarios:
                for extension in ('.epw', '.stat'):
                    path = os.path.join(output_dir, f'{stem}_Ensemble_{scenario}{extension}')
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(f'{stem} {scenario}')
                    created.append(path)
        return created

    module.morph_epw_global = morph_epw_global
    monkeypatch.setitem(sys.modules, 'pyfwg', module)
    return calls


@pytest.mark.parametrize('delete_morphing_files', [True, False])
def test_morph_epws_with_pyfwg(tmp_path, monkeypatch, delete_morphing_files):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('seville', encoding='utf-8')
    other = tmp_path / 'tmy' / 'Granada TMY.epw'
    other.parent.mkdir()
    other.write_text('granada', encoding='utf-8')
    calls = _fake_pyfwg(monkeypatch)

    morph_epws(fwg_path='C:/FWG folder/FutureWeatherGenerator_v4.jar', epw_filepaths=['Seville.epw', str(other)],
               delete_morphing_files=delete_morphing_files, engine='pyfwg')

    # One call for each EPW, with its folder next to it, and the options of morph_epws as those of pyfwg
    assert [call['epw_paths'] for call in calls] == [[str(tmp_path / 'Seville.epw')], [str(other)]]
    assert calls[0]['output_dir'] == str(tmp_path / 'Seville')
    assert calls[1]['output_dir'] == str(other.parent / 'Granada TMY')
    assert calls[0]['temp_base_dir'] == str(tmp_path / 'Seville' / 'pyfwg_temp')
    for call in calls:
        assert call['fwg_jar_path'] == 'C:/FWG folder/FutureWeatherGenerator_v4.jar'
        assert call['fwg_gcms'] == list(DEFAULT_GCMS)
        assert (call['fwg_create_ensemble'], call['fwg_month_transition_hours'], call['fwg_use_multithreading'],
                call['fwg_interpolation_method_id'], call['fwg_limit_variables']) == (True, 72, True, 0, True)
        assert call['fwg_show_tool_output'] is True and call['delete_temp_files'] is delete_morphing_files
        # Without the urban heat island, as the command line of Java (finding E4-1 of the review of 1.2.0)
        assert call['fwg_add_uhi'] is False
    # The future EPWs next to the originals, named as with Java; the originals do not move
    expected = ['Seville.epw', 'tmy'] + [f'Seville_{scenario}.epw' for scenario in SCENARIOS]
    if not delete_morphing_files:
        expected.append('Seville')
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(expected)
    assert (tmp_path / 'Seville_ssp585_2080.epw').read_text(encoding='utf-8') == 'Seville ssp585_2080'
    assert (tmp_path / 'Seville.epw').read_text(encoding='utf-8') == 'seville'
    assert sorted(p.name for p in other.parent.iterdir()) == sorted(
        ['Granada TMY.epw'] + [f'Granada TMY_{scenario}.epw' for scenario in SCENARIOS]
        + ([] if delete_morphing_files else ['Granada TMY']))
    if not delete_morphing_files:
        # The other files of the tool stay in the folder
        assert len(list((tmp_path / 'Seville').glob('*.stat'))) == len(SCENARIOS)


def test_morph_epws_gives_its_options_and_pyfwg_arguments_to_pyfwg(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('EPW', encoding='utf-8')
    calls = _fake_pyfwg(monkeypatch)

    # Without the ensemble, the EPW of each scenario that is kept is that of one of the models (finding E4-2)
    with pytest.warns(UserWarning, match=r'With fwg_options_ensemble=0, the Future Weather Generator writes an EPW for '
                                         r'each climate model and scenario'):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', fwg_options_gcms='CanESM5,MIROC6', fwg_options_ensemble=0,
                   fwg_options_month_transition_hours=24, fwg_options_do_multithread_computation=False,
                   fwg_options_interpolation_method_id=2, fwg_options_do_limit_variables=False, engine='pyfwg',
                   pyfwg_arguments={'fwg_add_uhi': True, 'fwg_version': 4, 'fwg_show_tool_output': False})

    [call] = calls
    assert call['fwg_gcms'] == ['CanESM5', 'MIROC6']
    assert (call['fwg_create_ensemble'], call['fwg_month_transition_hours'], call['fwg_use_multithreading'],
            call['fwg_interpolation_method_id'], call['fwg_limit_variables']) == (False, 24, False, 2, False)
    # pyfwg_arguments gives the urban heat island
    assert (call['fwg_add_uhi'], call['fwg_version'], call['fwg_show_tool_output']) == (True, 4, False)
    # With the ensemble (also as text), no warning
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        morph_epws(fwg_path='FutureWeatherGenerator.jar', epw_filepaths=['Seville.epw'], fwg_options_ensemble='1',
                   engine='pyfwg')


@pytest.mark.parametrize('delete_morphing_files', [True, False])
def test_a_value_error_of_pyfwg_removes_the_folders(tmp_path, monkeypatch, delete_morphing_files):
    # Finding E4-3 of the review of 1.2.0: as after the other errors, the folders that morph_epws made are removed
    monkeypatch.chdir(tmp_path)
    for name in ('Granada.epw', 'Seville.epw'):
        (tmp_path / name).write_text(name, encoding='utf-8')
    good = _fake_pyfwg(monkeypatch)
    import sys

    module = sys.modules['pyfwg']
    morph_good = module.morph_epw_global

    def morph(**kwargs):
        if os.path.basename(kwargs['epw_paths'][0]) == 'Granada.epw':
            return morph_good(**kwargs)
        os.makedirs(kwargs['temp_base_dir'], exist_ok=True)
        raise ValueError('The parameters of the tool are not valid.')

    module.morph_epw_global = morph
    with pytest.raises(ValueError, match='The parameters of the tool are not valid'):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', epw_filepaths=['Granada.epw', 'Seville.epw'],
                   delete_morphing_files=delete_morphing_files, engine='pyfwg')
    assert len(good) == 1
    names = {p.name for p in tmp_path.iterdir()}
    assert {'Granada.epw', 'Seville.epw'} | {f'Granada_{scenario}.epw' for scenario in SCENARIOS} <= names
    assert ({'Granada', 'Seville'} & names) == (set() if delete_morphing_files else {'Granada', 'Seville'})


def test_the_arguments_of_the_engines_are_checked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('EPW', encoding='utf-8')
    calls = _fake_pyfwg(monkeypatch)
    with pytest.raises(ValueError, match=r"engine must be one of \['java', 'pyfwg'\], not 'jar'"):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', engine='jar')
    with pytest.raises(ValueError, match="pyfwg_arguments needs engine='pyfwg'"):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', pyfwg_arguments={'fwg_add_uhi': False})
    with pytest.raises(ValueError, match=r"pyfwg_arguments cannot give \['output_dir'\]"):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', engine='pyfwg', pyfwg_arguments={'output_dir': 'x'})
    with pytest.raises(ValueError, match=r"pyfwg.morph_epw_global does not take: \['fwg_rcm_pairs'\]"):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', engine='pyfwg', pyfwg_arguments={'fwg_rcm_pairs': []})
    assert not calls and sorted(p.name for p in tmp_path.iterdir()) == ['Seville.epw']


def test_pyfwg_runs_the_global_tool_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('EPW', encoding='utf-8')
    calls = _fake_pyfwg(monkeypatch, distribution='europe')
    with pytest.raises(ValueError, match='fwg_path is the europe Future Weather Generator'):
        morph_epws(fwg_path='FutureWeatherGenerator_Europe_v2.0.2.jar', engine='pyfwg')
    assert not calls
    # A tool that pyfwg does not identify is left to pyfwg
    _fake_pyfwg(monkeypatch, distribution=None)
    morph_epws(fwg_path='tool.jar', engine='pyfwg')
    assert (tmp_path / 'Seville_ssp126_2050.epw').exists()


@pytest.mark.parametrize('error, message', [
    (None, r'Seville\.epw \(no future EPW was written\)'),
    (FileNotFoundError(2, 'The system cannot find the file specified'), r'Seville\.epw \(Java could not be run'),
])
def test_a_failure_of_pyfwg_is_reported(tmp_path, monkeypatch, error, message):
    monkeypatch.chdir(tmp_path)
    for name in ('Seville.epw', 'Granada.epw'):
        (tmp_path / name).write_text(name, encoding='utf-8')
    calls = []
    good = _fake_pyfwg(monkeypatch)
    import sys

    module = sys.modules['pyfwg']
    morph_good = module.morph_epw_global

    def morph(**kwargs):
        calls.append(kwargs)
        if os.path.basename(kwargs['epw_paths'][0]) == 'Granada.epw':
            return morph_good(**kwargs)
        if error is not None:
            raise error
        # pyfwg logs the errors of the tool and returns the files that it wrote
        return []

    module.morph_epw_global = morph
    with pytest.raises(RuntimeError, match=message) as raised:
        morph_epws(fwg_path='FutureWeatherGenerator.jar', delete_morphing_files=True, engine='pyfwg')
    assert 'Granada' not in str(raised.value) and 'pyfwg.enable_console_logging()' in str(raised.value)
    # Both EPWs were given to pyfwg, and only Granada was morphed
    assert len(calls) == 2 and [call['epw_paths'] for call in good] == [[str(tmp_path / 'Granada.epw')]]
    # The original EPWs stay, and the other EPW is morphed
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == sorted(['Granada.epw', 'Seville.epw'] + [f'Granada_{scenario}.epw' for scenario in SCENARIOS])


def test_without_pyfwg_the_engine_pyfwg_says_how_to_install_it(tmp_path, monkeypatch):
    import sys

    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('EPW', encoding='utf-8')
    monkeypatch.setitem(sys.modules, 'pyfwg', None)
    with pytest.raises(ImportError, match=r'pip install accim\[weather\]'):
        morph_epws(fwg_path='FutureWeatherGenerator.jar', engine='pyfwg')
    assert sorted(p.name for p in tmp_path.iterdir()) == ['Seville.epw']


def test_the_arguments_and_constants_are_those_of_pyfwg():
    import inspect

    pyfwg = pytest.importorskip('pyfwg')
    # The scenarios, timeframes and climate models of the global tool in pyfwg
    assert list(SCENARIOS) == [f'{scenario}_{year}' for scenario in pyfwg.GLOBAL_SCENARIOS
                               for year in pyfwg.ALL_POSSIBLE_YEARS]
    assert set(DEFAULT_GCMS) <= set(pyfwg.DEFAULT_GLOBAL_GCMS)
    # morph_epw_global takes the arguments that morph_epws gives
    inspect.signature(pyfwg.morph_epw_global).bind(
        epw_paths=['Seville.epw'], fwg_jar_path='FutureWeatherGenerator.jar', output_dir='Seville',
        temp_base_dir='Seville/pyfwg_temp', delete_temp_files=True, fwg_show_tool_output=True,
        fwg_gcms=list(DEFAULT_GCMS), fwg_create_ensemble=True, fwg_month_transition_hours=72,
        fwg_use_multithreading=True, fwg_interpolation_method_id=0, fwg_limit_variables=True, fwg_add_uhi=False)
    assert pyfwg.detect_fwg_tool('FutureWeatherGenerator_Europe_v2.0.2.jar') == 'europe'


FWG_JAR = os.environ.get('ACCIM_FWG_JAR', '')


@pytest.mark.skipif(not os.path.isfile(FWG_JAR),
                    reason='needs the jar of the global Future Weather Generator (its path in the environment variable '
                           'ACCIM_FWG_JAR), Java and pyfwg')
def test_morph_epws_with_pyfwg_and_the_tool(tmp_path, monkeypatch):
    import shutil
    from pathlib import Path

    pytest.importorskip('pyfwg')
    monkeypatch.chdir(tmp_path)
    shutil.copy(Path(__file__).resolve().parents[2] / 'Seville_Present.epw', tmp_path / 'Seville.epw')
    morph_epws(fwg_path=FWG_JAR, epw_filepaths=['Seville.epw'], engine='pyfwg')
    for scenario in SCENARIOS:
        lines = (tmp_path / f'Seville_{scenario}.epw').read_text(errors='replace').splitlines()
        assert lines[0].startswith('LOCATION') and len(lines) >= 8 + 8760