"""Tests for the parameters type 'epmv setpoints' of the parametric module (the ePMV setpoints of accim 1.2.0, see
accim.sim.apmv.apply_epmv_setpoints)."""
import pytest

from accim.parametric_and_optimisation import parameters, params_dicts
from accim.parametric_and_optimisation.main import ParametricSimulation


def _simulation(parameters_type):
    return ParametricSimulation(buildings=None, epws=['Test.epw'], parameters_type=parameters_type,
                                bypass_add_accis=True)


def test_the_parameters_of_the_epmv_setpoints():
    simulation = _simulation('epmv setpoints')

    assert simulation.is_epmv_setpoints and not simulation.is_apmv_setpoints
    assert simulation.get_available_parameters() == ['expectancy_factor', 'pmv_setpoint', 'pmv_cooling_setpoint',
                                                     'pmv_heating_setpoint']
    assert parameters.get_available_params_epmv_setpoints() == simulation.get_available_parameters()
    # The setpoints are changed by the modifiers of the aPMV setpoints, which find the lines by their variables
    for name in ('pmv_setpoint', 'pmv_cooling_setpoint', 'pmv_heating_setpoint'):
        assert params_dicts.epmv_setpoints_params[name] is params_dicts.apmv_setpoints_params[name]
    assert params_dicts.all_params['expectancy_factor'] is params_dicts.epmv_setpoints_params['expectancy_factor']
    assert not _simulation('apmv setpoints').is_epmv_setpoints


def test_the_parameters_types():
    with pytest.raises(KeyError, match='"apmv setpoints" or "epmv setpoints"'):
        _simulation('xpmv setpoints')
