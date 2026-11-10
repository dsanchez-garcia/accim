"""Tests for JPN Aqilah 2025, the comfort standard 23 (proposal B4 of accim 1.2.0, decisions D1 and D2 of the brief).

JPN Aqilah 2025 is the adaptive comfort model of the Japanese dwellings in free-running mode of Aqilah, Rijal, Yoshida &
Nicol (2025): ``Tc = 0.38·Trm + 16.9`` (equation 8), with the running mean outdoor temperature of α = 0.8 (RMOT of
EnergyPlus, as INT EN16798), applicable from 5 to 30 °C, with the comfort bands of ±2.0 K (80 %) and ±1.5 K (90 %), and
the static setpoints of 20 and 28 °C of comfort modes 0 and 1, which the paper does not give (D2). It is built in and
defined by its data (``accim.sim.standards.built_in_definitions``): its EMS code is added at the end of the chains of
the other comfort standards, whose output IDFs do not change (golden master). The last tests simulate output IDFs of
AddAccis with EnergyPlus 25.1 (verify_accim_simulation, and both backends).
"""
import filecmp
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from accim.energyplus import default_energyplus_folder, find_energyplus
from accim.sim import standards as st
from accim.sim.ems import program_lines as pl
from accim.sim.ems import standard_lines as sdl
from accim.sim.ems.setast import MODULAR_COMFORT_MODES
from accim.sim.ems.setpoint_lines import SETPOINT_LINES
from accim.sim.preview import compute_setpoints
from accim.utils import get_setpoint_ems_code, get_setpoint_ems_programs

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
LEGACY_IDF = next((REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'runEp').glob('TestModel_V2510*.idf'), None)
EPW = REPO / 'Seville_Present.epw'
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                               reason='needs EnergyPlus 25.1 and the sample IDF of the repository')
ZONES = ['Block1_Zone1', 'Block1_Zone2']
STEPS = 6
CITATION = ('Aqilah, Rijal, Yoshida & Nicol (2025) Energy & Buildings 335, 115469, '
            'doi:10.1016/j.enbuild.2025.115469')


def test_the_comfort_standard_23():
    standard = st.get_comfort_standard(23)
    assert (standard.number, standard.label, standard.title) == (23, 'JPN Aqilah2025', '23 = JPN Aqilah2025')
    assert standard.categories == {80: '80% acceptability', 90: '90% acceptability'}
    assert list(standard.comfort_modes) == [0, 1, 2, 3] == MODULAR_COMFORT_MODES[23]
    assert 'a choice of the user' in standard.comfort_modes[0]
    # Built in, after INT ISO7730 and before the custom model; not one of the registry
    assert list(st.COMFORT_STANDARDS)[-3:] == [22, 23, 99]
    assert st.comfort_standard_definition(23) is None and 23 not in st.registered_comfort_standards()
    definition = st.definition_of(23)
    assert definition is st.built_in_definitions()[23] and definition.standard is standard
    [regime] = definition.regimes
    assert (definition.outdoor_metric, regime.slope, regime.intercept) == ('rmot', 0.38, 16.9)
    assert (regime.cooling_lower_limit, regime.cooling_upper_limit, regime.heating_lower_limit,
            regime.heating_upper_limit) == (5.0, 30.0, 5.0, 30.0)
    assert definition.category_offsets == {80: (2.0, -2.0), 90: (1.5, -1.5)}
    # Decision D2: the static setpoints of 20 and 28 °C, a choice of the user
    assert definition.static_setpoints == (20.0, 28.0)
    assert definition.citation == CITATION
    assert definition.evidence['N'] == 11566 and definition.evidence['R2'] == 0.67
    # The same data as the YAML file of the sample files (101), but its outdoor metric (the EMS calculates the running
    # mean of the YAML file)
    [sample] = st.load_comfort_standards(REPO / 'accim' / 'sample_files' / 'comfort_standards'
                                         / 'jpn_aqilah2025_fr.yaml', register=False)
    assert sample.regimes == definition.regimes and sample.static_setpoints == definition.static_setpoints
    assert dict(sample.category_offsets) == dict(definition.category_offsets)
    assert sample.evidence == definition.evidence and sample.citation == definition.citation
    assert (sample.outdoor_metric, sample.alpha) == ('rmot_alpha', 0.8)
    # A comfort standard of the registry cannot have its label
    data = {'number': 102, 'label': 'jpn aqilah2025', 'title': '102 = Copy', 'citation': 'x', 'outdoor_metric': 'rmot',
            'comfort_temperature': {'slope': 0.38, 'intercept': 16.9},
            'applicability': {'metric_min': 5, 'metric_max': 30},
            'categories': {80: {'cooling_offset': 2, 'heating_offset': -2}}, 'comfort_modes': [3],
            'evidence': {'N': 1}}
    with pytest.raises(ValueError, match="The label 'jpn aqilah2025' is that of the comfort standard 23"):
        st.register_comfort_standard(st.definition_from_mapping(data))


def test_its_ems_code_is_that_of_its_data():
    definition = st.definition_of(23)
    # The literal lines are those that accim.sim.ems.standard_lines writes from the definition
    assert pl.BUILT_IN_BRANCHES[23] == sdl.standard_branches(definition)
    assert {mode: SETPOINT_LINES[(23, mode)] for mode in range(4)} == sdl.setpoint_lines(definition)
    assert pl.BUILT_IN_BRANCHES[23]['SetComfTemp'] == ('elseif ComfStand == 23', 'set ComfTemp = RMOT*0.38+16.9')
    assert SETPOINT_LINES[(23, 0)] == ('set ACST = 28+ACSTtol', 'set AHST = 20+AHSTtol')
    # Comfort modes 2 and 3 are written as those of JPN Rijal (3), with RMOT and the coefficients of equation 8
    for mode in (2, 3):
        rijal = [line.replace('PMOT', 'RMOT').replace('*0.48+14.4', '*0.38+16.9') for line in SETPOINT_LINES[(3, mode)]]
        assert list(SETPOINT_LINES[(23, mode)]) == rijal, mode
    # The hour counters and the ventilation setpoint compare RMOT with its limits, as INT EN16798
    assert pl.BUILT_IN_BRANCHES[23]['CountHours'][1:] == tuple(pl._count_hours_body('RMOT').split('\n'))
    assert pl.BUILT_IN_BRANCHES[23]['SetVST'][1] == 'if (RMOT >= AHSTall) && (RMOT <= ACSTaul)'


def test_the_ems_code_of_jpn_aqilah_2025():
    code = get_setpoint_ems_code(23, 80, 1)
    for line in ('! Comfort standard (ComfStand): 23 = JPN Aqilah2025', '! Category (CAT): 80 = 80% acceptability',
                 f'! Comfort standard built in, defined by its data (accim.sim.standards): {CITATION}',
                 '! Outdoor metric: rmot, in the EMS RMOT', '! Static setpoints: 20.0 for heating and 28.0 for cooling',
                 '!     N: 11566', '!     within_band: {90: 0.66, 80: 0.79}'):
        assert line in code.split('\n'), line
    programs = get_setpoint_ems_programs(23, 90, 2)
    assert programs['SetComfTemp'] == ['if ComfStand == 23', 'set ComfTemp = RMOT*0.38+16.9', 'endif']
    assert programs['SetAppLimits'] == ['if ComfStand == 23', 'set ACSTaul = 30', 'set ACSTall = 5',
                                        'set AHSTaul = 30', 'set AHSTall = 5', 'endif']
    assert programs['ApplyCAT'] == ['if ComfStand == 23', 'if (CAT == 80)', 'set ACSToffset = 2+CATcoolOffset',
                                    'set AHSToffset = -2+CATheatOffset', 'elseif (CAT == 90)',
                                    'set ACSToffset = 1.5+CATcoolOffset', 'set AHSToffset = -1.5+CATheatOffset',
                                    'endif', 'endif']
    # Its running mean is that of EnergyPlus: no programs of the outdoor metric
    assert 'SetOutdoorMetric' not in programs
    # The categories and comfort modes of the other comfort standards are rejected
    with pytest.raises(ValueError, match=r'category 1 is not a category of comfort_standard 23'):
        get_setpoint_ems_code(23, 1, 3)


@pytest.mark.parametrize('comfort_mode', [0, 1, 2, 3])
def test_compute_setpoints_of_jpn_aqilah_2025(comfort_mode):
    result = compute_setpoints(EPW, 23, 90, comfort_mode, frequency='timestep', start_date='01/04')
    assert result.attrs['metric'] == 'RMOT' and (result['Tout_metric'] == result['RMOT']).all()
    # The RMOT that the EMS reads: that of the previous day at the first timestep of each day (0 at the first
    # timestep of the run period, out of the applicability limits)
    rmot = result['RMOT'].to_numpy()
    first = np.arange(len(result)) % (24 * STEPS) == 0
    read = np.where(first, np.r_[0.0, rmot[:-1]], rmot)
    np.testing.assert_allclose(result['ComfTemp'], 0.38 * read + 16.9, rtol=0, atol=1e-9)
    within = (read >= 5) & (read <= 30)
    assert not within[0] and within[1:].all()
    np.testing.assert_array_equal(result['applicable'], within.astype(int))
    # Within the limits, the comfort temperature ±1.5 K (category 90); at the first timestep, below them
    below = {0: (28, 20), 1: (28, 20), 2: (24, 20), 3: (0.38 * 5 + 16.9 + 1.5, 0.38 * 5 + 16.9 - 1.5)}[comfort_mode]
    for column, offset, value in (('ACSTnoTol', 1.5, below[0]), ('AHSTnoTol', -1.5, below[1])):
        expected = np.where(within, 0.38 * read + 16.9 + offset, value)
        if comfort_mode == 0:
            expected = np.full(len(read), value, dtype=float)
        np.testing.assert_allclose(result[column], expected, rtol=0, atol=1e-9)


def test_the_valid_combinations_of_the_parametric_module():
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis

    assert param_accis.get_valid_param_combinations()[23] == [[80, 90], [0, 1, 2, 3]]
    plan = pd.DataFrame({'comfort_standard': [23, 23, 23], 'category': [80, 1, 90], 'comfort_mode': [1, 1, 0.1]})
    assert param_accis.drop_invalid_param_combinations(plan).values.tolist() == [[23, 80, 1]]


# AddAccis and modify_accis --------------------------------------------------------------------------------------------

def _add_accis(folder, monkeypatch, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                  output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                  setpoint_type='temperature', comfort_standard=[1], category=[1], comfort_mode=[1, 3],
                  hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    return {path.name: path for path in folder.glob('TestModel[[]*.idf')}


def _programs(idf):
    return {p.Name: [str(line).strip() for line in p.fieldvalues[2:]]
            for p in idf.idfobjects['EnergyManagementSystem:Program']}


@needs_idd
def test_add_accis_with_jpn_aqilah_2025(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.outdoor_metric import has_outdoor_metric_code

    reference = _add_accis(tmp_path / 'reference', monkeypatch)
    written = _add_accis(tmp_path / 'aqilah', monkeypatch, comfort_standard=[1, 23], category=[1, 80])
    # The output IDFs of the other comfort standards do not change
    assert len(reference) == 2 and set(reference) < set(written)
    for name, path in reference.items():
        assert filecmp.cmp(path, written[name], shallow=False), name
    names = sorted(name for name in written if name not in reference)
    assert [name.split('[')[1:4] for name in names] == [['CS_JPN Aqilah2025', 'CA_80', 'CM_1'],
                                                        ['CS_JPN Aqilah2025', 'CA_80', 'CM_3']]
    idf = load_idf(written[names[0]])
    programs = _programs(idf)
    assert programs['SetComfTemp'] == ['if ComfStand == 23', 'set ComfTemp = RMOT*0.38+16.9', 'endif']
    assert sorted(name for name in programs if name.startswith('SetAST_CS')) == ['SetAST_CS23_0', 'SetAST_CS23_1']
    assert programs['SetVST'].count('elseif ComfStand == 23') == 1
    for zone in ZONES:
        assert programs[f'CountHours_{zone}'][:2] == ['if ComfStand == 23',
                                                     'if (RMOT >= AHSTall) && (RMOT <= ACSTaul)']
    for program in input_programs(idf).values():
        inputs = read_inputs(program)
        assert (inputs['ComfStand'], inputs['CAT'], inputs['ComfMod']) == (23, 80, 1)
        # Its running mean is that of EnergyPlus: the zones have no inputs of the outdoor metric
        assert 'CustAST_metric' not in inputs
    assert not has_outdoor_metric_code(idf)


@needs_idd
def test_modify_accis_with_jpn_aqilah_2025(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf, modify_accis
    from accim.sim.ems.inputs import input_programs, read_inputs

    # An output IDF of AddAccis with the EMS code of INT EN16798 only gets that of JPN Aqilah 2025
    written = _add_accis(tmp_path / 'model', monkeypatch, comfort_mode=[3])
    [path] = written.values()
    idf = load_idf(path)
    modify_accis(idf, comfort_standard=23, category=90, comfort_mode=2)
    programs = _programs(idf)
    assert programs['SetComfTemp'] == ['if ComfStand == 1', 'set ComfTemp = RMOT*0.33+18.8', 'elseif ComfStand == 23',
                                       'set ComfTemp = RMOT*0.38+16.9', 'endif']
    assert {'SetAST_CS1_0', 'SetAST_CS1_1', 'SetAST_CS23_0', 'SetAST_CS23_1'} <= set(programs)
    assert all((read_inputs(p)['ComfStand'], read_inputs(p)['CAT'], read_inputs(p)['ComfMod']) == (23, 90, 2)
               for p in input_programs(idf).values())


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_do_not_have_it(tmp_path):
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis
    from accim.sim.accis import load_idf, modify_accis

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    with pytest.raises(ValueError, match='which does not have the EMS code of the comfort standard 23'):
        modify_accis(building, comfort_standard=23, category=80, comfort_mode=3)
    with pytest.raises(ValueError, match='which does not have the EMS code of the comfort standard 23'):
        param_accis.modify_ComfStand(building, 23)


# EnergyPlus ---------------------------------------------------------------------------------------------------------

def _energyplus_with_api():
    folder = find_energyplus('25.1', required=False)
    ready = folder is not None and (folder / 'pyenergyplus').is_dir() and SAMPLE_IDF.exists() and EPW.exists()
    return folder if ready else None


needs_energyplus = pytest.mark.skipif(
    _energyplus_with_api() is None,
    reason='needs EnergyPlus 25.1 (with its Python API) and the sample files of the repository')


def _output_idf(folder, monkeypatch, begin, end, frequency, script_type='vrf_mm', **arguments):
    """The output IDF of AddAccis of the sample model with JPN Aqilah 2025 (category 80, comfort mode 1), whose input
    IDF has the run period given."""
    from accim.sim.accis import AddAccis, load_idf

    folder.mkdir(parents=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    model = load_idf(folder / 'TestModel.idf')
    run_period = model.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = begin
    run_period.End_Month, run_period.End_Day_of_Month = end
    model.save()
    monkeypatch.chdir(folder)
    values = dict(script_type=script_type, supply_air_temp_input_method='temperature difference',
                  output_type='standard', output_frequencies=[frequency], keep_existing_outputs=False,
                  energyplus_version='auto', setpoint_type='temperature', comfort_standard=[23], category=[80],
                  comfort_mode=[1], hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        AddAccis(**values)
    [path] = folder.glob('TestModel[[]*.idf')
    shutil.copy(path, folder / 'model.idf')
    return folder / 'model.idf'


def _run_energyplus(model, folder):
    energyplus = _energyplus_with_api() / 'energyplus.exe'
    result = subprocess.run([str(energyplus), '-d', str(folder), '-p', 'run', '-s', 'C', '-r', '-x', '-w', str(EPW),
                             str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-3000:]
    return pd.read_csv(folder / 'run.csv')


@needs_energyplus
def test_jpn_aqilah_2025_in_energyplus(tmp_path, monkeypatch, capsys):
    from accim.utils.verification import verify_accim_simulation

    model = _output_idf(tmp_path / 'january', monkeypatch, (1, 1), (1, 7), 'timestep')
    results = _run_energyplus(model, tmp_path / 'january' / 'out')
    assert len(results) == 7 * 24 * STEPS
    # The setpoints are those of compute_setpoints (check 4), also at the first timestep, out of the limits
    mismatches = verify_accim_simulation(str(tmp_path / 'january' / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any()
    for zone in ZONES:
        for check in ('Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 1008 timesteps", output), (zone, check)
    found = results['EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_Block1_Zone1 [C](TimeStep)']
    # The static setpoint of comfort mode 1 at the first timestep (RMOT is 0 for the EMS), then 0.38·RMOT + 16.9 + 2
    assert found.iloc[0] == pytest.approx(28) and found.iloc[1:].between(16, 30).all()


@needs_energyplus
def test_the_ems_and_api_backends_give_the_same_results(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    model = _output_idf(tmp_path / 'model', monkeypatch, (6, 1), (6, 10), 'hourly', category=[90], comfort_mode=[3])
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
