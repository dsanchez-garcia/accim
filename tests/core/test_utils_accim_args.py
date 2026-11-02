"""Tests for accim.utils.get_accim_args and get_accim_args_flattened, which read the arguments of the ACCIS (or
of the aPMV setpoints) back from the EMS programs of a model.

Ported from the round trip of the branch refactor/sim-v1 (tests/utils/test_utils_idf.py), with the names of
the arguments of accim 1.0.0: the EMS programs keep the names of accim 0.x (ComfStand, CAT...), which are the
keys of accim.sim.arguments.LEGACY_ARGUMENT_NAMES.

Since accim 1.0.0, each zone has all its arguments in a program SetInputData_<zone>, so get_accim_args returns one
dictionary for each of these programs (before, 'SetInputData', 'SetVOFinputData', 'SetAST' and 'CustAST', and
the models without natural ventilation, 'vrf_ac' and 'ex_ac', have no inputs of the venting opening factor).
"""
import shutil
from pathlib import Path

import pytest

from accim.energyplus import default_energyplus_folder
from accim.sim.arguments import LEGACY_ARGUMENT_NAMES
from accim.utils import get_accim_args, get_accim_args_flattened

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
ADD_ACCIS_ARGS = dict(supply_air_temp_input_method='temperature difference', output_type='simplified',
                      output_frequencies=['hourly'], keep_existing_outputs=False, setpoint_type='temperature',
                      verbose=False)
#: Arguments of modify_accis whose EMS variable is named after the argument of accim 0.x
ARGUMENTS = dict(comfort_standard=2, category=80, comfort_mode=3, hvac_mode=2, ventilation_control=1, ventilation_setpoint_offset=1, min_outdoor_temp_offset=5,
                 max_wind_speed=8, cooling_season_start=152, cooling_season_end=273, setpoint_accuracy=1000)
VOF_DEFAULTS = dict(opening_factor_max_temp_diff=6, opening_factor_min_temp_diff=1, min_opening_factor=0.25)

needs_energyplus_25_1 = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                                           reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    return get_building(str(tmp_path / 'model.idf'))


@needs_energyplus_25_1
@pytest.mark.parametrize('script_type', ['vrf_mm', 'vrf_ac'])
def test_get_accim_args_reads_back_the_arguments_of_modify_accis(building, script_type):
    from accim.sim.accis import add_accis_to_idf, modify_accis

    add_accis_to_idf(building, script_type=script_type, **ADD_ACCIS_ARGS)
    modify_accis(building, setpoint_tolerance=0.25, custom_slope=0.31, custom_intercept=17.8, custom_cooling_offset=2.5,
                 category_cooling_offset=1, custom_cooling_upper_limit=33.5, custom_cooling_lower_limit=10, custom_heating_upper_limit=32.5,
                 custom_heating_lower_limit=11, **ARGUMENTS)

    args = get_accim_args(building)
    flattened = get_accim_args_flattened(building)

    assert sorted(args) == ['SetInputData_Block1_Zone1', 'SetInputData_Block1_Zone2']
    expected = dict(ARGUMENTS, category_cooling_offset=1, category_heating_offset=0, custom_cooling_offset=2.5, custom_heating_offset=0,
                    custom_cooling_upper_limit=33.5, custom_cooling_lower_limit=10, custom_heating_upper_limit=32.5, custom_heating_lower_limit=11,
                    **(VOF_DEFAULTS if script_type == 'vrf_mm' else {}))
    for program in args.values():
        assert {LEGACY_ARGUMENT_NAMES[k]: v for k, v in program.items() if k in LEGACY_ARGUMENT_NAMES} == expected
        assert (program['ACSTtol'], program['AHSTtol'], program['m'], program['n']) == (-0.25, 0.25, 0.31, 17.8)
        assert ('MaxTempDiffVOF' in program) is (script_type == 'vrf_mm')
    # With several zones, the values of the last one
    assert flattened == args['SetInputData_Block1_Zone1']


@needs_energyplus_25_1
def test_get_accim_args_of_the_apmv_setpoints(building):
    from accim.sim.apmv import apply_apmv_setpoints

    assert get_accim_args(building) == {}

    apply_apmv_setpoints(building, adaptive_coefficient_cooling=0.3, adaptive_coefficient_heating=-0.2, pmv_cooling_setpoint=0.4,
                         pmv_heating_setpoint=-0.6, verbose=False)

    args = get_accim_args(building)
    assert sorted(args) == ['set_zone_input_data_Block1_Zone1', 'set_zone_input_data_Block1_Zone2']
    zone1 = args['set_zone_input_data_Block1_Zone1']
    assert zone1['adap_coeff_cooling_Block1_Zone1'] == 0.3
    assert zone1['adap_coeff_heating_Block1_Zone1'] == -0.2
    assert zone1['pmv_cooling_sp_Block1_Zone1'] == 0.4
    assert zone1['pmv_heating_sp_Block1_Zone1'] == -0.6


@pytest.mark.parametrize('text, value', [
    ('2', 2), ('-0.25', -0.25), ('3.5 + 1', 4.5), ('(33.5 - 1) * 2 / 4', 16.25), ('+1', 1),
    # Not numbers: they are kept as text
    ('CAT', 'CAT'), ('ACSToffset + 1', 'ACSToffset + 1'), ('1/0', '1/0'), ('2 ** 999999', '2 ** 999999'),
    ('', ''), ("__import__('os').getcwd()", "__import__('os').getcwd()"),
])
def test_the_values_of_the_program_lines_are_read_without_eval(text, value):
    # Found by the review of 2026-10-24: they were evaluated with eval, which runs any code of the program lines
    from accim.utils.accim_args import _value

    assert _value(text) == value and type(_value(text)) is type(value)
