"""Tests for the parameters of the floor and ceiling of the setpoints of the parametric module (proposal B5 of accim
1.2.0, accim.sim.ems.setpoint_limits): ``heating_setpoint_floor`` and ``cooling_setpoint_ceiling``, with the accim
predefined models and the accim custom models. tests/core/test_setpoint_limits.py checks what their modifiers do to a
model."""
from accim.parametric_and_optimisation import parameters, params_dicts
from accim.parametric_and_optimisation.funcs_for_besos import param_accis
from accim.parametric_and_optimisation.main import ParametricSimulation

NAMES = {'heating_setpoint_floor': param_accis.modify_AHSTfloor,
         'cooling_setpoint_ceiling': param_accis.modify_ACSTceil}


def _simulation(parameters_type):
    return ParametricSimulation(buildings=None, epws=['Test.epw'], parameters_type=parameters_type,
                                bypass_add_accis=True)


def test_the_parameters_of_the_floor_and_ceiling_of_the_setpoints():
    for name, modifier in NAMES.items():
        assert params_dicts.accim_predef_model_params[name] is modifier
        assert params_dicts.accim_custom_model_params[name] is modifier
        assert params_dicts.all_params[name] is modifier
        assert name in parameters.get_available_params_accim_predef_models()
        assert name in parameters.get_available_params_accim_custom_models()
    for parameters_type in ('accim predefined model', 'accim custom model'):
        assert set(NAMES) <= set(_simulation(parameters_type).get_available_parameters())
    # Not with the PMV-based setpoints, which have neither floor nor ceiling (decision D5 of accim 1.2.0)
    for parameters_type in ('apmv setpoints', 'epmv setpoints'):
        assert not set(NAMES) & set(_simulation(parameters_type).get_available_parameters())
    # They have no names of accim 0.x
    assert params_dicts.resolve_parameter_name('Heating_Setpoint_Floor') == 'heating_setpoint_floor'
    assert not set(NAMES) & set(params_dicts.LEGACY_PARAMETER_NAMES.values())


def test_the_wrappers_and_the_descriptors_of_the_floor_and_ceiling():
    assert parameters.HeatingSetpointFloor().name == 'heating_setpoint_floor'
    assert parameters.CoolingSetpointCeiling().name == 'cooling_setpoint_ceiling'
    # A range with a tuple, options with a list
    descriptor = parameters.accis_parameter('heating_setpoint_floor', (18, 21)).value_descriptors[0]
    assert (descriptor.name, descriptor.min, descriptor.max) == ('heating_setpoint_floor', 18, 21)
    descriptor = parameters.accis_parameter('cooling_setpoint_ceiling', [25.5, 26.0, 27.0]).value_descriptors[0]
    assert descriptor.name == 'cooling_setpoint_ceiling' and list(descriptor.options) == [25.5, 26.0, 27.0]
