"""Tests for JPN Aqilah 2025, the comfort standard 23 (proposal B4 of accim 1.2.0, decisions D1 and D2 of the brief, and
findings B4-1 and B4-2 of the review of 1.2.0, task G4 of ``notes/PROPUESTAS_MEJORAS_post_1.1.0_v04.md``).

JPN Aqilah 2025 is the adaptive comfort model of the Japanese dwellings in free-running mode of Aqilah, Rijal, Yoshida &
Nicol (2025): ``Tc = 0.38·Trm + 16.9`` (equation 8), with the running mean outdoor temperature of α = 0.8 (RMOT of
EnergyPlus, as INT EN16798; with the weather file of the simulation, the running mean of EN 16798-1 with α = 0.8 that
the EMS calculates from it, as the comfort standard 101 of its YAML file), applicable from 5 to 30 °C, with the comfort
bands of ±2.0 K (80 %) and ±1.5 K (90 %), and the static setpoints of comfort modes 0 and 1, which the paper does not
give: the inputs StaticAHST and StaticACST of the zones (20 and 28 °C by default, D2). It is built in and defined by its
data (``accim.sim.standards.built_in_definitions``): its EMS code is added at the end of the chains of the other comfort
standards, whose output IDFs do not change (golden master). The last tests simulate output IDFs of AddAccis with
EnergyPlus 25.1 (verify_accim_simulation, and both backends).
"""
import dataclasses
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
    # Built in, after INT ISO7730 and before the custom model (and INT Sun2026 SET, 24, task F1); not one of the
    # registry
    assert list(st.COMFORT_STANDARDS)[-4:] == [22, 23, 24, 99]
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
    # Its static setpoints are the inputs StaticAHST and StaticACST of the zone (finding B4-2 of the review of 1.2.0)
    assert SETPOINT_LINES[(23, 0)] == ('set ACST = StaticACST+ACSTtol', 'set AHST = StaticAHST+AHSTtol')
    assert [line for line in SETPOINT_LINES[(23, 1)] if 'Static' in line] == [
        'set ACST = StaticACST+ACSTtol', 'set ACST = StaticACST+ACSTtol', 'set AHST = StaticAHST+AHSTtol',
        'set AHST = StaticAHST+AHSTtol']
    # Those of a comfort standard of the registry with the same data are its numbers
    copy = dataclasses.replace(definition, standard=dataclasses.replace(definition.standard, number=102,
                                                                        label='Copy'))
    assert sdl.setpoint_lines(copy)[0] == ('set ACST = 28+ACSTtol', 'set AHST = 20+AHSTtol')
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
                 '! Outdoor metric: rmot, in the EMS RMOT',
                 '! Static setpoints: 20.0 for heating and 28.0 for cooling (the inputs StaticAHST and StaticACST of '
                 'the zone: static_heating_setpoint and static_cooling_setpoint)',
                 '!     N: 11566', '!     within_band: {90: 0.66, 80: 0.79}', 'set StaticAHST = 20',
                 'set StaticACST = 28'):
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
    # Without the weather file (outdoor_metric_start 'pmot', as the output IDFs of AddAccis without epw): RMOT
    result = compute_setpoints(EPW, 23, 90, comfort_mode, frequency='timestep', start_date='01/04',
                               outdoor_metric_start='pmot')
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


@pytest.fixture
def yaml_twin():
    """The comfort standard 101 of the YAML file of the sample files (the data of JPN Aqilah 2025 with the running mean
    'rmot_alpha' that the EMS calculates), registered for the test."""
    [definition] = st.load_comfort_standards(REPO / 'accim' / 'sample_files' / 'comfort_standards'
                                             / 'jpn_aqilah2025_fr.yaml', register=True)
    yield definition
    st.unregister_comfort_standard(definition.number)


def test_the_ems_code_with_the_weather_file():
    code = get_setpoint_ems_code(23, 80, 3, epw=EPW, start_date='08/01').split('\n')
    assert ('! Outdoor metric: rmot_alpha (alpha 0.8), in the EMS Tout_metric, which begins with the values of the '
            'weather file (without it, rmot, in the EMS RMOT)') in code
    programs = get_setpoint_ems_programs(23, 80, 3, epw=EPW, start_date='08/01')
    assert {'InitOutdoorMetric', 'SetOutdoorMetric', 'SetOutdoorMetric_<zone>'} <= set(programs)
    assert programs['SetComfTemp'] == ['if ComfStand == 23', 'set ComfTemp = Tout_metric*0.38+16.9', 'endif']
    assert not any('RMOT' in line for name in ('SetAST_CS23_0', 'SetAST_CS23_1') for line in programs[name])
    assert sum('Tout_metric' in line for line in programs['SetAST_CS23_1']) > 0
    # The inputs of the zone: the running mean of EN 16798-1 with alpha 0.8, whatever the arguments of the custom model
    inputs = get_setpoint_ems_programs(23, 80, 3, epw=EPW, custom_outdoor_metric='ndrm', custom_alpha=0.6,
                                       custom_days=10)['SetInputData_<zone>']
    assert {'set CustAST_metric = 2', 'set CustAST_alpha = 0.8', 'set CustAST_days = 30'} <= set(inputs)
    # The lines of comfort mode 0, which do not use the running mean, as without the weather file
    subprogram = get_setpoint_ems_programs(23, 80, 0, epw=EPW)['SetAST_CS23_0']
    start = subprogram.index('if (ComfMod == 0)') + 1
    assert subprogram[start:start + 2] == list(SETPOINT_LINES[(23, 0)])


@pytest.mark.parametrize('start_date', ['01/01', '08/01', '01/07'])
def test_with_the_weather_file_it_is_its_yaml_twin(yaml_twin, start_date):
    # With the weather file (outdoor_metric_start 'epw', the default, as the output IDFs of AddAccis with epw), the
    # running mean of JPN Aqilah 2025 is that of the comfort standard 101 of its YAML file from the first day: the same
    # setpoints in every timestep (finding B4-1 of the review of 1.2.0)
    for category in (80, 90):
        for comfort_mode in (0, 1, 2, 3):
            built_in = compute_setpoints(EPW, 23, category, comfort_mode, frequency='timestep', start_date=start_date)
            twin = compute_setpoints(EPW, 101, category, comfort_mode, frequency='timestep', start_date=start_date)
            assert built_in.attrs['metric'] == twin.attrs['metric'] == 'rmot_alpha'
            pd.testing.assert_frame_equal(built_in, twin, check_exact=False, rtol=0, atol=1e-9)


@pytest.mark.parametrize('start_date, day_1', [('01/04', 1.4662), ('01/07', 1.9262)])
def test_without_the_weather_file_its_running_mean_begins_lower(yaml_twin, start_date, day_1):
    # Without the weather file, JPN Aqilah 2025 reads the RMOT of EnergyPlus, whose first value in a run period is the
    # sum of equation 19.82 of the Engineering Reference, not divided by 1 - 0.8**7: its comfort temperature is lower
    # than that of the comfort standard 101 of its YAML file, by more than 1 K on the first day and less than 0.1 K
    # from day 21 (review of 1.2.0, B4-1). In the first timestep of each day, the EMS of JPN Aqilah 2025 still reads
    # the RMOT of the previous day, while that of 101 has already updated its running mean, so the hours that contain
    # it (the first hour of each day) differ by the change of the running mean of a day in a timestep (up to 0.10 K
    # in the hourly means of the year from 1 January, on 2 May): they are left out of the comparison of the transient.
    # From 1 January the transient of the first day is 0.92 K (measured, hours 2 to 24), so the starts of 1 April and
    # 1 July of the review are those of the test
    rmot = compute_setpoints(EPW, 23, 90, 3, start_date=start_date, outdoor_metric_start='pmot')
    twin = compute_setpoints(EPW, 101, 90, 3, start_date=start_date)
    difference = (twin['ComfTemp'] - rmot['ComfTemp']).to_numpy()
    day = np.arange(len(difference)) // 24 + 1
    not_first_hour = np.arange(len(difference)) % 24 != 0
    assert (difference[(day == 1) & not_first_hour] > 1).all()
    assert difference[(day == 1) & not_first_hour].min() == pytest.approx(day_1, abs=1e-4)
    assert np.abs(difference[(day >= 21) & not_first_hour]).max() < 0.1
    # The whole days 21 to 30, with their first hours, too
    assert np.abs(difference[(day >= 21) & (day <= 30)]).max() < 0.1
    # The running mean itself, more than 1/0.38 K higher on the first day
    assert (twin['Tout_metric'] - rmot['Tout_metric'])[(day == 1) & not_first_hour].min() > 1 / 0.38


@pytest.mark.parametrize('comfort_mode', [0, 1])
def test_its_static_setpoints_are_arguments(comfort_mode):
    default = compute_setpoints(EPW, 23, 80, comfort_mode, frequency='timestep', start_date='01/01',
                                outdoor_metric_start='pmot')
    result = compute_setpoints(EPW, 23, 80, comfort_mode, frequency='timestep', start_date='01/01',
                               outdoor_metric_start='pmot', static_heating_setpoint=19, static_cooling_setpoint=26.5)
    # Where the defaults apply (comfort mode 0, or out of the limits in comfort mode 1), the arguments apply
    static = (default['ACSTnoTol'] == 28) & (default['AHSTnoTol'] == 20)
    assert static.all() if comfort_mode == 0 else 0 < static.sum() < len(static)
    np.testing.assert_allclose(result.loc[static, 'ACSTnoTol'], 26.5, rtol=0, atol=1e-9)
    np.testing.assert_allclose(result.loc[static, 'AHSTnoTol'], 19, rtol=0, atol=1e-9)
    pd.testing.assert_frame_equal(result.loc[~static], default.loc[~static])
    # The heating setpoint must be lower than the cooling setpoint
    with pytest.raises(ValueError, match=r'static_heating_setpoint \(28\) must be lower than static_cooling_setpoint'):
        get_setpoint_ems_code(23, 80, comfort_mode, static_heating_setpoint=28)
    with pytest.raises(ValueError, match='static_cooling_setpoint must be a number'):
        get_setpoint_ems_code(23, 80, comfort_mode, static_cooling_setpoint='28')
    # The other comfort standards ignore them
    assert get_setpoint_ems_code(1, 2, 0, static_heating_setpoint=28) == get_setpoint_ems_code(1, 2, 0)


def test_the_valid_combinations_of_the_parametric_module():
    pytest.importorskip('besos')
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis

    assert param_accis.get_valid_param_combinations()[23] == [[80, 90], [0, 1, 2, 3]]
    plan = pd.DataFrame({'comfort_standard': [23, 23, 23], 'category': [80, 1, 90], 'comfort_mode': [1, 1, 0.1]})
    assert param_accis.drop_invalid_param_combinations(plan).values.tolist() == [[23, 80, 1]]


# AddAccis and modify_accis --------------------------------------------------------------------------------------------

def _add_accis(folder, monkeypatch, record_warnings=False, **arguments):
    from accim.sim.accis import AddAccis

    folder.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_IDF, folder / 'TestModel.idf')
    monkeypatch.chdir(folder)
    values = dict(script_type='vrf_mm', supply_air_temp_input_method='temperature difference', output_type='standard',
                  output_frequencies=['hourly'], keep_existing_outputs=False, energyplus_version='auto',
                  setpoint_type='temperature', comfort_standard=[1], category=[1], comfort_mode=[1, 3],
                  hvac_mode=[2], ventilation_control=[0], confirm=True, verbose=False)
    values.update(arguments)
    if record_warnings:
        # The warnings go to the caller, which records them
        AddAccis(**values)
    else:
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


def _static_variables(idf):
    return [[str(value).strip() for value in obj.fieldvalues[1:] if str(value).strip()]
            for obj in idf.idfobjects['EnergyManagementSystem:GlobalVariable']
            if 'StaticAHST' in [str(value).strip() for value in obj.fieldvalues[1:]]]


def _rmot_warnings(caught):
    return [w for w in caught if 'reads the running mean outdoor temperature of CEN 15251' in str(w.message)]


@needs_idd
def test_add_accis_with_the_weather_file(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.outdoor_metric import begins_with_weather_file, has_outdoor_metric_code

    reference = _add_accis(tmp_path / 'reference', monkeypatch)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        written = _add_accis(tmp_path / 'aqilah', monkeypatch, comfort_standard=[1, 23], category=[1, 80],
                             epw=str(EPW), static_heating_setpoint=19, static_cooling_setpoint=27,
                             record_warnings=True)
    assert not _rmot_warnings(caught)
    # The output IDFs of the other comfort standards do not change: they ignore the weather file and the static
    # setpoints
    for name, path in reference.items():
        assert filecmp.cmp(path, written[name], shallow=False), name
    names = sorted(name for name in written if name not in reference)
    idf = load_idf(written[names[0]])
    programs = _programs(idf)
    # With the weather file, its code reads the running mean of EN 16798-1 with alpha 0.8, which begins with its values
    assert has_outdoor_metric_code(idf) and begins_with_weather_file(idf)
    assert programs['SetComfTemp'] == ['if ComfStand == 23', 'set ComfTemp = Tout_metric*0.38+16.9', 'endif']
    for zone in ZONES:
        assert programs[f'CountHours_{zone}'][:2] == ['if ComfStand == 23',
                                                     'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)']
    vst = programs['SetVST']
    assert vst[vst.index('elseif ComfStand == 23') + 1] == 'if (Tout_metric >= AHSTall) && (Tout_metric <= ACSTaul)'
    for name in ('SetAST_CS23_0', 'SetAST_CS23_1'):
        assert not any(re.search(r'\bRMOT\b', line) for line in programs[name])
    for program in input_programs(idf).values():
        inputs = read_inputs(program)
        assert {name: inputs[name] for name in ('CustAST_metric', 'CustAST_alpha', 'CustAST_days', 'StaticAHST',
                                                'StaticACST')} == {'CustAST_metric': 2, 'CustAST_alpha': 0.8,
                                                                   'CustAST_days': 30, 'StaticAHST': 19,
                                                                   'StaticACST': 27}
    assert _static_variables(idf) == [['StaticAHST', 'StaticACST']]
    # The output IDFs of the other comfort standards do not declare them
    assert _static_variables(load_idf(written[sorted(reference)[0]])) == []


@needs_idd
def test_add_accis_without_the_weather_file_warns(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf
    from accim.sim.ems.inputs import input_programs, read_inputs

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        written = _add_accis(tmp_path / 'aqilah', monkeypatch, comfort_standard=[23], category=[90],
                             comfort_mode=[0], record_warnings=True)
    [warning] = _rmot_warnings(caught)
    assert 'not divided by 1 - 0.8**7' in str(warning.message) and 'argument epw' in str(warning.message)
    [path] = written.values()
    idf = load_idf(path)
    assert _programs(idf)['SetComfTemp'] == ['if ComfStand == 23', 'set ComfTemp = RMOT*0.38+16.9', 'endif']
    assert all((read_inputs(p)['StaticAHST'], read_inputs(p)['StaticACST']) == (20.0, 28.0)
               for p in input_programs(idf).values())
    assert _static_variables(idf) == [['StaticAHST', 'StaticACST']]
    # The static setpoints are checked before writing anything
    with pytest.raises(ValueError, match=r'static_heating_setpoint \(28\) must be lower than static_cooling_setpoint'):
        _add_accis(tmp_path / 'wrong', monkeypatch, comfort_standard=[23], category=[90], static_heating_setpoint=28)
    with pytest.raises(ValueError, match=r"must be lower than static_cooling_setpoint \(18\) \(zone 'Block1:Zone1'\)"):
        _add_accis(tmp_path / 'wrong_zone', monkeypatch, comfort_standard=[23], category=[90],
                   zone_arguments={'Block1:Zone1': {'static_cooling_setpoint': 18}})


@needs_idd
def test_modify_accis_gives_it_the_weather_file_and_the_static_setpoints(tmp_path, monkeypatch):
    from accim.sim.accis import load_idf, modify_accis
    from accim.sim.ems.inputs import input_programs, read_inputs
    from accim.sim.ems.outdoor_metric import begins_with_weather_file, has_outdoor_metric_code

    written = _add_accis(tmp_path / 'model', monkeypatch, comfort_mode=[3])
    [path] = written.values()
    idf = load_idf(path)
    assert _static_variables(idf) == []
    # Without the weather file: RMOT, with a warning, and the default static setpoints
    with pytest.warns(UserWarning, match='reads the running mean outdoor temperature of CEN 15251'):
        modify_accis(idf, comfort_standard=23, category=80, comfort_mode=1)
    assert not has_outdoor_metric_code(idf)
    assert _static_variables(idf) == [['StaticAHST', 'StaticACST']]
    assert all((read_inputs(p)['StaticAHST'], read_inputs(p)['StaticACST']) == (20.0, 28.0)
               for p in input_programs(idf).values())
    # With it: the running mean of EN 16798-1 with alpha 0.8, from the values of the weather file
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        modify_accis(idf, epw=str(EPW), static_heating_setpoint=18)
    assert not _rmot_warnings(caught)
    assert has_outdoor_metric_code(idf) and begins_with_weather_file(idf)
    programs = _programs(idf)
    assert 'set ComfTemp = Tout_metric*0.38+16.9' in programs['SetComfTemp']
    assert 'set ComfTemp = RMOT*0.33+18.8' in programs['SetComfTemp']
    for program in input_programs(idf).values():
        inputs = read_inputs(program)
        assert (inputs['CustAST_metric'], inputs['CustAST_alpha'], inputs['StaticAHST'], inputs['StaticACST']) == (
            2, 0.8, 18, 28.0)
    # The model keeps them: the zones of JPN Aqilah 2025 keep the values of the weather file
    modify_accis(idf, static_cooling_setpoint=26, zone_arguments={'Block1:Zone2': {'static_heating_setpoint': 17}})
    assert begins_with_weather_file(idf)
    assert {zone: (read_inputs(p)['StaticAHST'], read_inputs(p)['StaticACST'])
            for zone, p in input_programs(idf).items()} == {'Block1_Zone1': (18, 26), 'Block1_Zone2': (17, 26)}
    with pytest.raises(ValueError, match=r"static_heating_setpoint \(27\) must be lower than static_cooling_setpoint "
                                         r"\(26\) \(zone 'Block1_Zone[12]'\)"):
        modify_accis(idf, static_heating_setpoint=27)
    # The zones that leave it and come back keep the values of the weather file of the model
    modify_accis(idf, comfort_standard=1, category=2, comfort_mode=3)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        modify_accis(idf, comfort_standard=23, category=90, comfort_mode=3)
    assert not _rmot_warnings(caught)
    assert begins_with_weather_file(idf)
    assert 'set ComfTemp = Tout_metric*0.38+16.9' in _programs(idf)['SetComfTemp']
    assert all(read_inputs(p)['CustAST_metric'] == 2 for p in input_programs(idf).values())


@needs_idd
def test_the_models_of_add_accis_to_idf_declare_its_static_setpoints(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis
    from accim.sim.ems.inputs import input_programs, read_inputs

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                     output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     setpoint_type='temperature', verbose=False)
    # The code of all the comfort standards: the static setpoints are declared, and every zone has them, with the
    # defaults, whatever its comfort standard is (finding A24 of the self-audit of 2026-11-11, decided on 2026-11-12:
    # before, only the zones of JPN Aqilah 2025 had them, so a zone switched to it by editing its program stopped
    # EnergyPlus), at the end of the inputs of the zones with full air-conditioning
    assert _static_variables(idf) == [['StaticAHST', 'StaticACST']]
    for program in input_programs(idf).values():
        assert read_inputs(program)['ComfStand'] == 1
        assert [str(line).strip() for line in program.fieldvalues[-2:]] == ['set StaticAHST = 20.0',
                                                                            'set StaticACST = 28.0']
    with pytest.warns(UserWarning, match='reads the running mean outdoor temperature of CEN 15251'):
        modify_accis(idf, comfort_standard=23, category=80, comfort_mode=0,
                     zone_arguments={'Block1:Zone2': {'comfort_standard': 1, 'category': 2}})
    inputs = {zone: read_inputs(p) for zone, p in input_programs(idf).items()}
    assert (inputs['Block1_Zone1']['StaticAHST'], inputs['Block1_Zone1']['StaticACST']) == (20.0, 28.0)
    # The zone of INT EN16798 keeps them, and ignores them
    assert (inputs['Block1_Zone2']['StaticAHST'], inputs['Block1_Zone2']['StaticACST']) == (20.0, 28.0)
    # A model that loses the code of JPN Aqilah 2025 loses them in the zones of the other comfort standards
    from accim.sim.ems.programs import set_comfort_standard_code

    modify_accis(idf, comfort_standard=1, category=2, comfort_mode=3)
    set_comfort_standard_code(idf, [1])
    assert _static_variables(idf) == []
    assert not any('StaticAHST' in read_inputs(p) or 'StaticACST' in read_inputs(p)
                   for p in input_programs(idf).values())


@needs_idd
def test_every_zone_of_a_model_with_its_code_has_its_static_setpoints(tmp_path, monkeypatch):
    # Finding A24 of the self-audit of 2026-11-11: an output IDF of AddAccis with a zone of JPN Aqilah 2025 has its
    # code, so its other zones have the inputs of its static setpoints too, with the defaults (they ignore them)
    from accim.sim.accis import load_idf
    from accim.sim.ems.inputs import input_programs, read_inputs

    written = _add_accis(tmp_path / 'model', monkeypatch, comfort_standard=[1], category=[1], comfort_mode=[3],
                         static_heating_setpoint=19, static_cooling_setpoint=27,
                         zone_arguments={'Block1:Zone2': {'comfort_standard': 23, 'category': 80, 'comfort_mode': 1}})
    [path] = written.values()
    idf = load_idf(path)
    inputs = {zone: read_inputs(program) for zone, program in input_programs(idf).items()}
    assert (inputs['Block1_Zone2']['ComfStand'], inputs['Block1_Zone1']['ComfStand']) == (23, 1)
    assert (inputs['Block1_Zone2']['StaticAHST'], inputs['Block1_Zone2']['StaticACST']) == (19, 27)
    assert (inputs['Block1_Zone1']['StaticAHST'], inputs['Block1_Zone1']['StaticACST']) == (20.0, 28.0)
    # In the same place in both programs: before the inputs of the venting opening factor (mixed mode)
    for program in input_programs(idf).values():
        lines = [str(line).strip() for line in program.fieldvalues[2:]]
        position = next(n for n, line in enumerate(lines) if line.startswith('set StaticAHST'))
        assert lines[position + 1].startswith('set StaticACST') and lines[position + 2] == 'set MaxTempDiffVOF = 6'
    assert _static_variables(idf) == [['StaticAHST', 'StaticACST']]
    # The output IDFs without its code have neither the variables nor the inputs
    reference = _add_accis(tmp_path / 'reference', monkeypatch, comfort_mode=[3], static_heating_setpoint=19)
    [path] = reference.values()
    other = load_idf(path)
    assert _static_variables(other) == []
    assert not any('StaticAHST' in read_inputs(p) for p in input_programs(other).values())


@needs_idd
def test_the_parameters_of_its_static_setpoints(tmp_path, monkeypatch):
    pytest.importorskip('besos')
    from accim.parametric_and_optimisation import parameters, params_dicts
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis
    from accim.sim.accis import load_idf
    from accim.sim.ems.inputs import input_programs, read_inputs

    assert params_dicts.accim_predef_model_params['static_heating_setpoint'] is param_accis.modify_StaticAHST
    assert params_dicts.accim_predef_model_params['static_cooling_setpoint'] is param_accis.modify_StaticACST
    assert parameters.StaticHeatingSetpoint().name == 'static_heating_setpoint'
    assert parameters.StaticCoolingSetpoint().name == 'static_cooling_setpoint'
    written = _add_accis(tmp_path / 'model', monkeypatch, comfort_mode=[3])
    [path] = written.values()
    idf = load_idf(path)
    # A static setpoint given before the comfort standard is kept; the other one gets its default
    parameters.StaticHeatingSetpoint().modify(idf, 19)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        param_accis.modify_ComfStand(idf, 23)
    assert all((read_inputs(p)['StaticAHST'], read_inputs(p)['StaticACST']) == (19, 28.0)
               for p in input_programs(idf).values())
    assert _static_variables(idf) == [['StaticAHST', 'StaticACST']]
    parameters.StaticCoolingSetpoint().modify(idf, 25)
    assert all(read_inputs(p)['StaticACST'] == 25 for p in input_programs(idf).values())
    with pytest.raises(ValueError, match=r'static_heating_setpoint \(25\) must be lower than static_cooling_setpoint'):
        param_accis.modify_StaticAHST(idf, 25)
    plan = pd.DataFrame({'comfort_standard': [23, 23], 'category': [80, 80], 'comfort_mode': [1, 1],
                         'static_heating_setpoint': [19, 26], 'static_cooling_setpoint': [27, 26]})
    assert param_accis.drop_invalid_param_combinations(plan)['static_heating_setpoint'].tolist() == [19]


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_do_not_have_it(tmp_path):
    from accim.sim.accis import load_idf, modify_accis

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    with pytest.raises(ValueError, match='which does not have the EMS code of the comfort standard 23'):
        modify_accis(building, comfort_standard=23, category=80, comfort_mode=3)
    # The parametric module (it needs besos)
    pytest.importorskip('besos')
    from accim.parametric_and_optimisation.funcs_for_besos import param_accis

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
def test_a_zone_switched_to_jpn_aqilah_2025_by_hand_runs_in_energyplus(tmp_path, monkeypatch):
    # Finding A24 of the self-audit of 2026-11-11 (decided on 2026-11-12): in a model with the EMS code of all the
    # comfort standards (add_accis_to_idf), a zone whose program SetInputData_<zone> was edited to comfort standard 23
    # stopped EnergyPlus in the warm-up ("Variable = 'STATICACST' used in expression has not been initialized"), since
    # only the zones of 23 had the inputs of its static setpoints. Now every zone has them
    from accim.sim.accis import add_accis_to_idf, load_idf
    from accim.sim.ems.inputs import input_programs, set_inputs

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    run_period = idf.idfobjects['RunPeriod'][0]
    run_period.Begin_Month, run_period.Begin_Day_of_Month = 7, 1
    run_period.End_Month, run_period.End_Day_of_Month = 7, 2
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['timestep'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    # By hand: only the comfort standard, the category and the comfort mode of one zone (static setpoints)
    assert set_inputs(input_programs(idf)['Block1_Zone1'], {'ComfStand': 23, 'CAT': 80, 'ComfMod': 0}) == []
    idf.saveas(str(tmp_path / 'edited.idf'))
    monkeypatch.chdir(tmp_path)
    results = _run_energyplus(tmp_path / 'edited.idf', tmp_path / 'out')
    assert len(results) == 2 * 24 * STEPS
    # Its static setpoints are the defaults, 20 and 28 °C
    zone = 'Block1_Zone1 [C](TimeStep)'
    assert (results[f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone}'] == 28).all()
    assert (results[f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone}'] == 20).all()
    # The other zone keeps the adaptive setpoints of INT EN16798, the default of add_accis_to_idf
    other = results['EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_Block1_Zone2 [C](TimeStep)']
    assert other.iloc[1:].between(22, 33).all() and other.iloc[1:].nunique() > 1


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


@needs_energyplus
def test_jpn_aqilah_2025_with_the_weather_file_in_energyplus(tmp_path, monkeypatch, capsys):
    from accim.utils.verification import verify_accim_simulation

    # From 8 January (a run period that begins between the 2nd and the 30th of January), with the weather file, the
    # static setpoints 19 and 27 °C, and comfort mode 0 in the second zone
    folder = tmp_path / 'weather'
    model = _output_idf(folder, monkeypatch, (1, 8), (1, 21), 'timestep', epw=str(EPW), static_heating_setpoint=19,
                        static_cooling_setpoint=27, zone_arguments={'Block1:Zone2': {'comfort_mode': 0}})
    results = _run_energyplus(model, folder / 'out')
    assert len(results) == 14 * 24 * STEPS
    mismatches = verify_accim_simulation(str(folder / 'out' / 'run.eso'), str(model), epw=str(EPW))
    output = capsys.readouterr().out
    assert len(mismatches) == 0 or not mismatches['check'].str.match('Check4').any()
    for zone in ZONES:
        for check in ('Check4_ACST', 'Check4_AHST', 'Check4_ComfTemp', 'Check4_Tout_metric'):
            assert re.search(rf"'{zone}' {check} \(.*\): 0 mismatch\(es\) in 2016 timesteps", output), (zone, check)
    # The running mean of EN 16798-1 with alpha 0.8 of the weather file from the first timestep (not 0, as RMOT)
    metric = results['EMS:Tout_metric_Block1_Zone1 [C](TimeStep)']
    expected = compute_setpoints(EPW, 23, 80, 1, frequency='timestep', start_date='08/01')
    np.testing.assert_allclose(metric.to_numpy(), expected['Tout_metric'].to_numpy()[:len(metric)], rtol=0, atol=1e-6)
    assert metric.iloc[0] > 5
    # The static setpoints of comfort mode 0
    zone2 = 'Block1_Zone2 [C](TimeStep)'
    assert (results[f'EMS:Adaptive Cooling Setpoint Temperature_No Tolerance_{zone2}'] == 27).all()
    assert (results[f'EMS:Adaptive Heating Setpoint Temperature_No Tolerance_{zone2}'] == 19).all()


@needs_energyplus
def test_the_backends_give_the_same_results_with_the_weather_file(tmp_path, monkeypatch):
    from accim.sim.energyplus_api import run_simulations

    model = _output_idf(tmp_path / 'model', monkeypatch, (6, 1), (6, 10), 'hourly', category=[90], comfort_mode=[1],
                        epw=str(EPW), static_heating_setpoint=21, static_cooling_setpoint=26)
    ems_results = _run_energyplus(model, tmp_path / 'ems')
    results = run_simulations([(model, EPW, {'output_directory': tmp_path / 'api', 'output_prefix': 'run'})],
                              processes=1)
    assert results[0].success, results[0].error
    api_results = pd.read_csv(tmp_path / 'api' / 'run.csv')
    assert len(ems_results) == 10 * 24
    assert 'EMS:Tout_metric_Block1_Zone1 [C](Hourly)' in ems_results
    pd.testing.assert_frame_equal(api_results, ems_results, check_exact=True)
