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
import struct
import subprocess
import warnings
import zipfile

import pytest

from accim.data.morphing import DEFAULT_GCMS, ENGINE_INTERPOLATION_METHODS, _java_version, fwg_jar_info, morph_epws

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


# The jar of the tool: the FWG Engine (the global tool since its version 5), and the Java that it needs ---------------

#: The name of the jar of the version 5.3.0 of the global tool
ENGINE_JAR = 'FutureWeatherGenerator-CMIP6-Global-v5.3.0.jar'


def _jar(path, engine=True, java=17):
    """A jar file with what morph_epws reads of that of the tool: the manifest and the header of its main class, of
    the FWG Engine (as the jar of the version 5.3.0, whose classes are of Java 17) or of an earlier version."""
    header = b'\xca\xfe\xba\xbe' + struct.pack('>HH', 0, java + 44)
    with zipfile.ZipFile(path, 'w') as jar:
        if engine:
            jar.writestr('META-INF/MANIFEST.MF', '\r\n\r\n'.join([
                'Manifest-Version: 1.0', 'Created-By: 26.0.1+8 (Eclipse Adoptium)',
                'Main-Class: futureweathergenerator.Main', 'Specification-Version: 5.3.0', 'FWG-Engine-Version: 1.2.0',
                'FWG-Distribution-Id: fwg-cmip6-global', 'FWG-Distribution-Version: 5.3.0']) + '\r\n')
            jar.writestr('futureweathergenerator/Main.class', header + b'the rest of the class')
        else:
            jar.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\r\nCreated-By: a test\r\n')
        jar.writestr('futureweathergenerator/Morph.class', header + b'the rest of the class')
    return str(path)


def _fake_java(commands, version='17.0.4', tool=None):
    """A subprocess.run that answers ``java -version`` with a version of Java and keeps the other commands (those of
    the tool), after which ``tool(command)`` writes the files of the tool and gives its exit code (0 without it)."""
    def run(command, **kwargs):
        if list(command[1:]) == ['-version']:
            return subprocess.CompletedProcess(command, 0, stdout='',
                                               stderr=f'openjdk version "{version}" 2022-07-19\n')
        commands.append(command)
        return subprocess.CompletedProcess(command, (tool(command) or 0) if tool is not None else 0)
    return run


def _engine_files(folder, scenarios=SCENARIOS):
    """The files that the FWG Engine writes for an EPW of Seville in its output folder, with the layout ORGANIZED:
    the weather files of the scenarios, named after the location of the EPW, and the baseline that the tool
    checks, in the folder weather; and its reports, in other folders."""
    (folder / 'weather').mkdir(exist_ok=True)
    for scenario in scenarios:
        (folder / 'weather' / f'ESP_-_SEVILLA_Ensemble_{scenario}.epw').write_text(scenario, encoding='utf-8')
        (folder / 'weather' / f'ESP_-_SEVILLA_Ensemble_{scenario}.stat').write_text('', encoding='utf-8')
    (folder / 'weather' / f'{folder.name}_FutureWeatherGenerator-SolarQC_multimodel_constrained_ensemble_perez_1990'
                          f'.epw').write_text('baseline', encoding='utf-8')
    (folder / 'reports').mkdir(exist_ok=True)
    (folder / 'reports' / 'ESP_-_SEVILLA_Ensemble_ssp585_2080.epw.moisture-audit.txt').write_text('', encoding='utf-8')


def test_the_information_of_the_jar_of_the_tool(tmp_path):
    # The version of the tool and of its engine, from the manifest, and the Java of its main class (61 - 44)
    assert fwg_jar_info(_jar(tmp_path / ENGINE_JAR)) == {'version': '5.3.0', 'engine': '1.2.0', 'java': 17}
    # The jars before the FWG Engine do not say their version: the Java of the class that their command line runs
    assert fwg_jar_info(_jar(tmp_path / 'FutureWeatherGenerator_v1.2.1.jar', engine=False, java=8)) == {
        'version': None, 'engine': None, 'java': 8}
    # Not a jar, a jar without the classes of the tool, or no file
    (tmp_path / 'text.jar').write_text('not a jar', encoding='utf-8')
    with zipfile.ZipFile(tmp_path / 'other.jar', 'w') as jar:
        jar.writestr('other/Main.class', b'\xca\xfe\xba\xbe\x00\x00\x00\x3d')
    for path in (tmp_path / 'text.jar', tmp_path / 'other.jar', tmp_path / 'missing.jar', 'FutureWeatherGenerator.jar'):
        assert fwg_jar_info(path) == {'version': None, 'engine': None, 'java': None}


@pytest.mark.parametrize('output, expected', [
    ('java version "1.8.0_481"\nJava(TM) SE Runtime Environment (build 1.8.0_481-b10)', (8, '1.8.0_481')),
    ('openjdk version "17.0.4" 2022-07-19', (17, '17.0.4')),
    ('openjdk version "25.0.4.1" 2026-08-18', (25, '25.0.4.1')),
    ('openjdk version "9"', (9, '9')),
    ('no version here', None),
])
def test_the_version_of_the_java_of_the_path(monkeypatch, output, expected):
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: subprocess.CompletedProcess(
        command, 0, stdout='', stderr=output))
    assert _java_version() == expected

    def no_java(command, **kwargs):
        raise FileNotFoundError(2, 'The system cannot find the file specified')

    monkeypatch.setattr(subprocess, 'run', no_java)
    assert _java_version() is None


def test_the_java_engine_runs_the_command_line_of_the_fwg_engine(tmp_path, monkeypatch):
    # Found with the jar of the version 5.3.0 (2026-11-17): the FWG Engine, the global tool since its version 5, does
    # not take the 8 positional arguments of engine='java' ("Unknown or malformed option... Baseline EPW is required
    # (-epw=<path>)"), and writes the weather files in the folder weather of its output folder, named after the
    # location of the EPW
    monkeypatch.chdir(tmp_path)
    jar = _jar(tmp_path / ENGINE_JAR)
    (tmp_path / 'Seville.epw').write_text('original', encoding='utf-8')
    commands = []
    monkeypatch.setattr(subprocess, 'run', _fake_java(
        commands, tool=lambda command: _engine_files(tmp_path / 'Seville')))

    morph_epws(fwg_path=jar)

    # The command line that pyfwg builds for the FWG Engine with these options
    folder = os.path.join(os.getcwd(), 'Seville')
    assert commands == [[
        'java', '-jar', jar, '-g', f"-epw={os.path.join(folder, 'Seville.epw')}", f'-output_folder={folder}{os.sep}',
        '-output_layout=ORGANIZED', f"-models={','.join(DEFAULT_GCMS)}", '-ensemble=true', '-temp_shift_winter=0.0',
        '-temp_shift_summer=0.0', '-smooth_hours=72', '-multithread=true', '-grid_interpolation_method=IDW',
        '-epw_dictionary_limits=true', '-output_type=EPW']]
    # The EPW of each scenario, renamed after the original one; not the baseline of the tool, nor its other files
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        [ENGINE_JAR, 'Seville.epw'] + [f'Seville_{scenario}.epw' for scenario in SCENARIOS])
    assert (tmp_path / 'Seville_ssp585_2080.epw').read_text(encoding='utf-8') == 'ssp585_2080'
    assert (tmp_path / 'Seville.epw').read_text(encoding='utf-8') == 'original'

    # Its options
    commands.clear()
    with pytest.warns(UserWarning, match='With fwg_options_ensemble=0'):
        morph_epws(fwg_path=jar, epw_filepaths=['Seville.epw'], fwg_options_gcms='CanESM5,MIROC6',
                   fwg_options_ensemble=0, fwg_options_month_transition_hours=24,
                   fwg_options_do_multithread_computation=False, fwg_options_interpolation_method_id=3,
                   fwg_options_do_limit_variables=False, delete_morphing_files=False)
    assert commands[0][7:] == [
        '-models=CanESM5,MIROC6', '-ensemble=false', '-temp_shift_winter=0.0', '-temp_shift_summer=0.0',
        '-smooth_hours=24', '-multithread=false', '-grid_interpolation_method=NP', '-epw_dictionary_limits=false',
        '-output_type=EPW']
    # With delete_morphing_files=False, the other files of the tool are kept in the folder of the EPW
    assert sorted(p.name for p in (tmp_path / 'Seville' / 'weather').iterdir())[-1].startswith(
        'Seville_FutureWeatherGenerator-SolarQC') and (tmp_path / 'Seville' / 'reports').is_dir()
    # The interpolation methods of the engine, by their identifiers (those of pyfwg) or by their names
    assert ENGINE_INTERPOLATION_METHODS == {0: 'IDW', 1: 'BI', 2: 'AVG4P', 3: 'NP', 4: 'SCI', 5: 'SGBI', 6: 'STBI'}
    for method, name in ((1, 'BI'), ('2', 'AVG4P'), ('stbi', 'STBI')):
        commands.clear()
        morph_epws(fwg_path=jar, epw_filepaths=['Seville.epw'], fwg_options_interpolation_method_id=method)
        assert f'-grid_interpolation_method={name}' in commands[0]
    commands.clear()
    with pytest.raises(ValueError, match='fwg_options_interpolation_method_id must be one of .* not 7'):
        morph_epws(fwg_path=jar, epw_filepaths=['Seville.epw'], fwg_options_interpolation_method_id=7)
    assert commands == [] and (tmp_path / 'Seville.epw').exists() and not (tmp_path / 'Seville').exists()


def test_a_failure_of_the_fwg_engine_is_reported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'Seville.epw').write_text('original', encoding='utf-8')
    # The tool stops before it writes its folder of the weather files
    monkeypatch.setattr(subprocess, 'run', _fake_java([], tool=lambda command: 1))
    with pytest.raises(RuntimeError, match=r'Seville\.epw \(exit code 1\)') as error:
        morph_epws(fwg_path=_jar(tmp_path / ENGINE_JAR), epw_filepaths=['Seville.epw'])
    assert "engine='pyfwg'" not in str(error.value)
    assert sorted(p.name for p in tmp_path.iterdir()) == [ENGINE_JAR, 'Seville.epw']
    # With the jar of an earlier version, whose command line is that of the versions that accim used before, the
    # error says that pyfwg runs the versions 3 and 4
    old = _jar(tmp_path / 'FutureWeatherGenerator_v3.0.1.jar', engine=False, java=8)
    commands = []
    monkeypatch.setattr(subprocess, 'run', _fake_java(commands, tool=lambda command: 1))
    with pytest.raises(RuntimeError, match=r"With the versions 3 and 4 of the tool.*use engine='pyfwg'\."):
        morph_epws(fwg_path=old, epw_filepaths=['Seville.epw'])
    assert commands[0][:4] == ['java', '-cp', old, 'futureweathergenerator.Morph'] and len(commands[0]) == 12


@pytest.mark.parametrize('engine', ['java', 'pyfwg'])
def test_the_java_of_the_path_is_checked_against_the_jar(tmp_path, monkeypatch, engine):
    # Found on 2026-11-17: the classes of the version 5.3.0 of the tool are of Java 17 (class file version 61), and
    # with the Java 8 of the PATH the tool stopped with an UnsupportedClassVersionError for each EPW
    monkeypatch.chdir(tmp_path)
    jar = _jar(tmp_path / ENGINE_JAR)
    (tmp_path / 'Seville.epw').write_text('original', encoding='utf-8')
    calls = _fake_pyfwg(monkeypatch)
    commands = []
    monkeypatch.setattr(subprocess, 'run', _fake_java(commands, version='1.8.0_481'))
    with pytest.raises(RuntimeError, match=r'The Future Weather Generator 5\.3\.0 of fwg_path needs Java 17 or later '
                                           r'\(the class file version of its classes is 61\), and the Java of the '
                                           r'PATH is 1\.8\.0_481\..*No EPW file was moved\.'):
        morph_epws(fwg_path=jar, epw_filepaths=['Seville.epw'], engine=engine)
    assert commands == [] and calls == []
    assert sorted(p.name for p in tmp_path.iterdir()) == [ENGINE_JAR, 'Seville.epw']
    # With that Java or a later one, the tool is run
    for version in ('17.0.4', '25.0.4.1'):
        monkeypatch.setattr(subprocess, 'run', _fake_java(commands, version=version))
        morph_epws(fwg_path=jar, epw_filepaths=['Seville.epw'], engine=engine)
    assert (len(commands), len(calls)) == ((2, 0) if engine == 'java' else (0, 2))
    # And when Java does not say its version: the tool tells
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: commands.append(command)
                        or subprocess.CompletedProcess(command, 0, stdout='', stderr=''))
    morph_epws(fwg_path=jar, epw_filepaths=['Seville.epw'], engine=engine)
    assert commands[-1][1:] == (['-jar', jar] + commands[-1][3:] if engine == 'java' else ['-version'])


# The tool itself ----------------------------------------------------------------------------------------------------

FWG_JAR = os.environ.get('ACCIM_FWG_JAR', '')


def _tool_can_run():
    """Whether the jar of ACCIM_FWG_JAR is there and the Java of the PATH is the one that its classes need."""
    if not os.path.isfile(FWG_JAR):
        return False
    needed, installed = fwg_jar_info(FWG_JAR)['java'], _java_version()
    return installed is not None and (needed is None or installed[0] >= needed)


needs_the_tool = pytest.mark.skipif(
    not _tool_can_run(), reason='needs the jar of the global Future Weather Generator (its path in the environment '
                                'variable ACCIM_FWG_JAR), the Java that it needs in the PATH (17 or later for the '
                                'version 5.3.0) and pyfwg')


def _seville(tmp_path):
    import shutil
    from pathlib import Path

    shutil.copy(Path(__file__).resolve().parents[2] / 'Seville_Present.epw', tmp_path / 'Seville.epw')


@needs_the_tool
def test_morph_epws_with_pyfwg_and_the_tool(tmp_path, monkeypatch):
    pytest.importorskip('pyfwg')
    monkeypatch.chdir(tmp_path)
    _seville(tmp_path)
    morph_epws(fwg_path=FWG_JAR, epw_filepaths=['Seville.epw'], engine='pyfwg')
    for scenario in SCENARIOS:
        lines = (tmp_path / f'Seville_{scenario}.epw').read_text(errors='replace').splitlines()
        assert lines[0].startswith('LOCATION') and len(lines) >= 8 + 8760


@needs_the_tool
def test_both_engines_give_the_same_future_epws_with_the_tool(tmp_path, monkeypatch):
    # With the jar of the version 5.3.0 (2026-11-17), engine='java' could not morph an EPW (the 8 positional arguments
    # are not those of the FWG Engine); with its command line, both engines give the same files, byte by byte
    import filecmp

    pytest.importorskip('pyfwg')
    for engine in ('java', 'pyfwg'):
        (tmp_path / engine).mkdir()
        monkeypatch.chdir(tmp_path / engine)
        _seville(tmp_path / engine)
        # Two climate models: about 40 s for each engine
        morph_epws(fwg_path=FWG_JAR, epw_filepaths=['Seville.epw'], engine=engine, fwg_options_gcms='CanESM5,MIROC6')
        assert sorted(p.name for p in (tmp_path / engine).iterdir()) == sorted(
            ['Seville.epw'] + [f'Seville_{scenario}.epw' for scenario in SCENARIOS])
    for scenario in SCENARIOS:
        java, pyfwg = (tmp_path / engine / f'Seville_{scenario}.epw' for engine in ('java', 'pyfwg'))
        lines = java.read_text(errors='replace').splitlines()
        assert lines[0].startswith('LOCATION') and len(lines) == 8 + 8760
        # The year of the scenario, and the climate models of the ensemble
        assert lines[8].startswith(f'{scenario[-4:]},1,1,1,') and 'Ensemble (CanESM5, MIROC6)' in lines[5]
        assert filecmp.cmp(java, pyfwg, shallow=False), scenario


@needs_the_tool
def test_the_command_line_of_the_java_engine_is_that_of_pyfwg_with_the_tool(tmp_path, monkeypatch):
    # The command line of pyfwg is the reference of that of engine='java' (decided by the author on 2026-11-10):
    # both, with the jar of the tool (which pyfwg reads) and without running it
    pytest.importorskip('pyfwg')
    monkeypatch.chdir(tmp_path)
    _seville(tmp_path)
    commands = []

    def no_weather_files(command):
        # The folder of the weather files of the output folder, empty
        [output] = [argument for argument in command if argument.startswith('-output_folder=')]
        os.makedirs(os.path.join(output[len('-output_folder='):], 'weather'), exist_ok=True)

    monkeypatch.setattr(subprocess, 'run', _fake_java(commands, version='99', tool=no_weather_files))
    options = dict(fwg_options_gcms='CanESM5,MIROC6', fwg_options_month_transition_hours=48,
                   fwg_options_do_multithread_computation=False, fwg_options_interpolation_method_id=1,
                   fwg_options_do_limit_variables=False)
    morph_epws(fwg_path=FWG_JAR, epw_filepaths=['Seville.epw'], engine='java', **options)
    with pytest.raises(RuntimeError, match='no future EPW was written'):
        morph_epws(fwg_path=FWG_JAR, epw_filepaths=['Seville.epw'], engine='pyfwg', **options)
    java, pyfwg = ([argument for argument in command if not argument.startswith(('-epw=', '-output_folder='))]
                   for command in commands if '-g' in command)
    assert java == pyfwg and '-grid_interpolation_method=BI' in java and len(java) == 14
    assert fwg_jar_info(FWG_JAR)['engine'] is not None