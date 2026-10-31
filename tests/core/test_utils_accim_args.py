"""Tests for accim.utils.get_accim_args and get_accim_args_flattened, which read the arguments of the ACCIS (or
of the aPMV setpoints) back from the EMS programs of a model.

Ported from the round trip of the branch refactor/sim-v1 (tests/utils/test_utils_idf.py), with the names of
the arguments of accim 1.0.0: the EMS programs keep the names of accim 0.x (ComfStand, CAT...), which are the
keys of accim.sim.arguments.LEGACY_ARGUMENT_NAMES.

The models without natural ventilation ('vrf_ac' and 'ex_ac') have no program SetVOFinputData, and
get_accim_args stopped when it did not find it: it returned SetInputData only, without SetAST (SetpointAcc) and
the arguments of the custom comfort model (CustAST). Now SetVOFinputData is read only when the model has it.
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
                      output_freqs=['hourly'], output_keep_existing=False, temp_ctrl='temperature',
                      verbose_mode=False)
#: Arguments of modify_accis whose EMS variable is named after the argument of accim 0.x
ARGUMENTS = dict(comf_stand=2, cat=80, comf_mod=3, hvac_mode=2, vent_ctrl=1, vst_offset=1, min_ot_offset=5,
                 max_wind_speed=8, cool_season_start=152, cool_season_end=273, setpoint_acc=1000)
VOF_DEFAULTS = dict(max_temp_diff_vof=6, min_temp_diff_vof=1, multiplier_vof=0.25)

pytestmark = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists()),
                                reason='needs EnergyPlus 25.1 and the sample IDF of the repository')


@pytest.fixture
def building(tmp_path):
    from besos.eppy_funcs import get_building

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    return get_building(str(tmp_path / 'model.idf'))


@pytest.mark.parametrize('script_type', ['vrf_mm', 'vrf_ac'])
def test_get_accim_args_reads_back_the_arguments_of_modify_accis(building, script_type):
    from accim.sim.accis import add_accis_to_idf, modify_accis

    add_accis_to_idf(building, script_type=script_type, **ADD_ACCIS_ARGS)
    modify_accis(building, ast_tol=0.25, cust_ast_m=0.31, cust_ast_n=17.8, cust_ast_acst_offset=2.5,
                 cat_cool_offset=1, cust_ast_acst_aul=33.5, cust_ast_acst_all=10, cust_ast_ahst_aul=32.5,
                 cust_ast_ahst_all=11, **ARGUMENTS)

    args = get_accim_args(building)
    flattened = get_accim_args_flattened(building)

    expected = dict(ARGUMENTS, **(VOF_DEFAULTS if script_type == 'vrf_mm' else {}))
    assert {LEGACY_ARGUMENT_NAMES[k]: v for k, v in flattened.items() if k in LEGACY_ARGUMENT_NAMES} == expected
    assert (args['SetInputData']['ACSTtol'], args['SetInputData']['AHSTtol']) == (-0.25, 0.25)
    assert ('SetVOFinputData' in args) is (script_type == 'vrf_mm')
    assert args['SetAST'] == {'SetpointAcc': 1000}
    # modify_accis writes the offsets of the comfort model as sums with the offsets of the category
    assert args['CustAST'] == {'ACSToffset': 3.5, 'AHSToffset': 0, 'm': 0.31, 'n': 17.8, 'ACSTaul': 33.5,
                               'ACSTall': 10, 'AHSTaul': 32.5, 'AHSTall': 11}
    assert flattened == {k: v for program in args.values() for k, v in program.items()}


def test_get_accim_args_of_the_apmv_setpoints(building):
    from accim.sim.apmv import apply_apmv_setpoints

    assert get_accim_args(building) == {}

    apply_apmv_setpoints(building, adap_coeff_cooling=0.3, adap_coeff_heating=-0.2, pmv_cooling_sp=0.4,
                         pmv_heating_sp=-0.6, verbose_mode=False)

    args = get_accim_args(building)
    assert sorted(args) == ['set_zone_input_data_Block1_Zone1', 'set_zone_input_data_Block1_Zone2']
    zone1 = args['set_zone_input_data_Block1_Zone1']
    assert zone1['adap_coeff_cooling_Block1_Zone1'] == 0.3
    assert zone1['adap_coeff_heating_Block1_Zone1'] == -0.2
    assert zone1['pmv_cooling_sp_Block1_Zone1'] == 0.4
    assert zone1['pmv_heating_sp_Block1_Zone1'] == -0.6
