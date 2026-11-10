"""Tests for the parameters of the limiter of the drift of the setpoints of the parametric module (task F2 of block F of
accim 1.2.0, :mod:`accim.sim.ems.drift_limiter`): ``drift_mode`` (the codes 0, none; 1, 'rate'; 2, 'window'),
``max_drift_rate``, ``alpha_indoor``, ``delta_cool``, ``delta_heat`` and ``initial_T_rm_in``, with the accim predefined
models and the accim custom models. tests/core/test_drift_limiter.py checks the limiter."""
import shutil
import warnings
from pathlib import Path

import pytest

from accim.parametric_and_optimisation import parameters, params_dicts
from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.parametric_and_optimisation.main import ParametricSimulation
from accim.sim.ems import drift_limiter as dl

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
NAMES = {'drift_mode': param_accis.modify_DriftMode, 'max_drift_rate': param_accis.modify_MaxDriftRate,
         'alpha_indoor': param_accis.modify_AlphaIndoor, 'delta_cool': param_accis.modify_DeltaCool,
         'delta_heat': param_accis.modify_DeltaHeat, 'initial_T_rm_in': param_accis.modify_InitTrmIn}
CLASSES = {'drift_mode': parameters.DriftMode, 'max_drift_rate': parameters.MaxDriftRate,
           'alpha_indoor': parameters.AlphaIndoor, 'delta_cool': parameters.DeltaCool,
           'delta_heat': parameters.DeltaHeat, 'initial_T_rm_in': parameters.InitialTRmIn}


def _simulation(parameters_type):
    return ParametricSimulation(buildings=None, epws=['Test.epw'], parameters_type=parameters_type,
                                bypass_add_accis=True)


def test_the_parameters_of_the_limiter_of_the_drift():
    for name, modifier in NAMES.items():
        assert params_dicts.accim_predef_model_params[name] is modifier
        assert params_dicts.accim_custom_model_params[name] is modifier
        assert params_dicts.all_params[name] is modifier
        assert CLASSES[name]().name == name
        assert name in parameters.get_available_params_accim_predef_models()
        assert name in parameters.get_available_params_accim_custom_models()
    for parameters_type in ('accim predefined model', 'accim custom model'):
        assert set(NAMES) <= set(_simulation(parameters_type).get_available_parameters())
    # Not with the PMV-based setpoints, whose setpoints are not temperatures
    for parameters_type in ('apmv setpoints', 'epmv setpoints'):
        assert not set(NAMES) & set(_simulation(parameters_type).get_available_parameters())
    assert params_dicts.resolve_parameter_name('Drift_Mode') == 'drift_mode'
    descriptor = parameters.accis_parameter('drift_mode', [0, 1, 2]).value_descriptors[0]
    assert descriptor.name == 'drift_mode' and list(descriptor.options) == [0, 1, 2]


def _model(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    idf = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(idf, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    return idf


def _inputs(idf):
    from accim.sim.ems.inputs import input_programs, read_inputs

    return {zone: {name: value for name, value in read_inputs(program).items() if name in dl.INPUTS}
            for zone, program in input_programs(idf).items()}


@pytest.mark.skipif(not SAMPLE_IDF.exists(), reason='needs the sample IDF of the repository')
def test_the_modifiers_of_the_limiter_of_the_drift(tmp_path):
    idf = _model(tmp_path)
    # The arguments before drift_mode wait in the inputs; drift_mode 0 without the limiter does nothing
    param_accis.modify_MaxDriftRate(idf, 0.25)
    param_accis.modify_DriftMode(idf, 0)
    assert set(map(frozenset, (values.items() for values in _inputs(idf).values()))) == {
        frozenset({('MaxDriftRate', 0.25)})}
    assert not dl.has_drift_limiter(idf)
    # drift_mode 2: the limiter, with the rate given before and the defaults of the others
    param_accis.modify_DriftMode(idf, 2)
    for values in _inputs(idf).values():
        assert values == {'DriftMode': 2, 'MaxDriftRate': 0.25, 'AlphaIndoor': 0.8, 'DeltaCool': 1.0,
                          'DeltaHeat': 1.0}
    assert dl.has_drift_limiter(idf)
    param_accis.modify_InitTrmIn(idf, 24)
    param_accis.modify_DeltaCool(idf, 1.5)
    zone = next(iter(_inputs(idf)))
    program = idf.getobject('EnergyManagementSystem:Program', f'{dl.PROGRAM_PREFIX}{zone}')
    assert [str(value).strip() for value in program.fieldvalues[2:]] == dl.program_lines(zone, initial=True)
    assert _inputs(idf)[zone]['DeltaCool'] == 1.5 and _inputs(idf)[zone]['InitTrmIn'] == 24
    # The names of the modes, and 0 or 'none' turns it off (the programs stay)
    param_accis.modify_DriftMode(idf, 'rate')
    assert {values['DriftMode'] for values in _inputs(idf).values()} == {1}
    param_accis.modify_DriftMode(idf, 'none')
    assert {values['DriftMode'] for values in _inputs(idf).values()} == {0}
    assert dl.has_drift_limiter(idf)
    for modifier, value, message in ((param_accis.modify_DriftMode, 3, 'drift_mode must be 0'),
                                     (param_accis.modify_MaxDriftRate, 0, 'max_drift_rate must be in'),
                                     (param_accis.modify_AlphaIndoor, 1.0, 'alpha_indoor must be in'),
                                     (param_accis.modify_DeltaHeat, -1, 'delta_heat must be in')):
        with pytest.raises(ValueError, match=message):
            modifier(idf, value)
