"""Tests for the parameters of the minimum and maximum of the setpoints of the parametric module (proposal B5 of accim
1.2.0, accim.sim.ems.setpoint_limits): ``heating_setpoint_minimum`` and ``cooling_setpoint_maximum``, with the accim
predefined models and the accim custom models. tests/core/test_setpoint_limits.py checks what their modifiers do to a
model."""
import pytest

from accim.parametric_and_optimisation import parameters, params_dicts
from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.parametric_and_optimisation.main import ParametricSimulation

NAMES = {'heating_setpoint_minimum': param_accis.modify_AHSTmin,
         'cooling_setpoint_maximum': param_accis.modify_ACSTmax}


def _simulation(parameters_type):
    return ParametricSimulation(buildings=None, epws=['Test.epw'], parameters_type=parameters_type,
                                bypass_add_accis=True)


def test_the_parameters_of_the_minimum_and_maximum_of_the_setpoints():
    for name, modifier in NAMES.items():
        assert params_dicts.accim_predef_model_params[name] is modifier
        assert params_dicts.accim_custom_model_params[name] is modifier
        assert params_dicts.all_params[name] is modifier
        assert name in parameters.get_available_params_accim_predef_models()
        assert name in parameters.get_available_params_accim_custom_models()
    for parameters_type in ('accim predefined model', 'accim custom model'):
        assert set(NAMES) <= set(_simulation(parameters_type).get_available_parameters())
    # Not with the PMV-based setpoints, which have neither minimum nor maximum (decision D5 of accim 1.2.0)
    for parameters_type in ('apmv setpoints', 'epmv setpoints'):
        assert not set(NAMES) & set(_simulation(parameters_type).get_available_parameters())
    # Their names are case-insensitive, and they have no names of accim 0.x, only those of the development of 1.2.0
    assert params_dicts.resolve_parameter_name('Heating_Setpoint_Minimum') == 'heating_setpoint_minimum'
    assert {old for old, new in params_dicts.LEGACY_PARAMETER_NAMES.items() if new in NAMES} == {
        'heating_setpoint_floor', 'cooling_setpoint_ceiling'}


def test_the_wrappers_and_the_descriptors_of_the_minimum_and_maximum():
    assert parameters.HeatingSetpointMinimum().name == 'heating_setpoint_minimum'
    assert parameters.CoolingSetpointMaximum().name == 'cooling_setpoint_maximum'
    # A range with a tuple, options with a list
    descriptor = parameters.accis_parameter('heating_setpoint_minimum', (18, 21)).value_descriptors[0]
    assert (descriptor.name, descriptor.min, descriptor.max) == ('heating_setpoint_minimum', 18, 21)
    descriptor = parameters.accis_parameter('cooling_setpoint_maximum', [25.5, 26.0, 27.0]).value_descriptors[0]
    assert descriptor.name == 'cooling_setpoint_maximum' and list(descriptor.options) == [25.5, 26.0, 27.0]


def test_the_names_of_the_development_of_accim_1_2_0():
    # Task H1 of the review of 1.2.0: the modifiers of heating_setpoint_floor and cooling_setpoint_ceiling are
    # deprecated aliases of the new ones
    for old, new in ((param_accis.modify_AHSTfloor, param_accis.modify_AHSTmin),
                     (param_accis.modify_ACSTceil, param_accis.modify_ACSTmax)):
        assert old.__wrapped__ is new
    calls = []
    original = param_accis._set_setpoint_limit
    try:
        param_accis._set_setpoint_limit = lambda idf, variable, value: calls.append((variable, value))
        with pytest.warns(DeprecationWarning, match='param_accis.modify_AHSTfloor is deprecated since accim 1.2.0'):
            param_accis.modify_AHSTfloor(None, 20)
        with pytest.warns(DeprecationWarning, match='param_accis.modify_ACSTceil is deprecated since accim 1.2.0'):
            param_accis.modify_ACSTceil(None, 26)
    finally:
        param_accis._set_setpoint_limit = original
    assert calls == [('AHSTmin', 20), ('ACSTmax', 26)]
    # The old names of the parameters give the new ones
    with pytest.warns(DeprecationWarning, match="'heating_setpoint_floor' is deprecated since accim 1.2.0"):
        descriptor = parameters.accis_parameter('heating_setpoint_floor', (18, 21)).value_descriptors[0]
    assert descriptor.name == 'heating_setpoint_minimum'
