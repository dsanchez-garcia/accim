"""Tests for the parameters of the occupants and of the new indices and models of the parametric module (proposal C1
of accim 1.2.0): ``clothing_insulation``, ``activity_level`` and ``air_velocity`` (the inputs of the PMV, with the
setpoints based on the PMV), ``custom_outdoor_metric``, ``custom_alpha`` and ``custom_days`` (the outdoor metric of the
custom model, B1), their wrapper classes (``Clo``, ``Met``, ``AirVelocity``, ``ExpectancyFactor``,
``AdaptiveCoefficientCooling``, ``AdaptiveCoefficientHeating``, ``CustAST_metric``, ``CustAST_alpha``,
``CustAST_days``), and the plans that drop a minimum heating setpoint that is not lower than the maximum of the
cooling setpoint (B5). The ranges of the warnings are those of ISO 7730:2025 (section 4) and ASHRAE 55-2020.
"""
import shutil
import warnings
from pathlib import Path

import pandas as pd
import pytest

from accim.constants import ASHRAE55_MAX_CLOTHING_INSULATION, PMV_BODY_SURFACE_AREA, PMV_INPUT_RANGES
from accim.energyplus import default_energyplus_folder
from accim.parametric_and_optimisation import parameters, params_dicts
from accim.parametric_and_optimisation.funcs_for_besos import param_accis, param_apmv
from accim.parametric_and_optimisation.main import ParametricSimulation

REPO = Path(__file__).resolve().parents[2]
SAMPLE_IDF = (REPO / 'accim' / 'sample_files' / 'sample IDFs' / 'input_IDFs'
              / 'TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf')
EPW = REPO / 'Seville_Present.epw'
# An output IDF of accim 0.x (before SetAST_Master), with one program SetInputData for all the zones
LEGACY_IDF = next((REPO / 'accim' / 'sample_files' / 'jupyter_notebooks' / 'runEp').glob('TestModel_V2510*.idf'), None)
IDD_25_1 = default_energyplus_folder('25.1') / 'Energy+.idd'
needs_idd = pytest.mark.skipif(not (IDD_25_1.exists() and SAMPLE_IDF.exists() and EPW.exists()),
                               reason='needs EnergyPlus 25.1 and the sample files of the repository')
PMV_INPUTS = {'clothing_insulation': param_apmv.change_clothing_insulation_all_zones,
              'activity_level': param_apmv.change_activity_level_all_zones,
              'air_velocity': param_apmv.change_air_velocity_all_zones}
METRIC_INPUTS = {'custom_outdoor_metric': param_accis.modify_CustAST_metric,
                 'custom_alpha': param_accis.modify_CustAST_alpha,
                 'custom_days': param_accis.modify_CustAST_days}
WRAPPERS = {'Clo': 'clothing_insulation', 'Met': 'activity_level', 'AirVelocity': 'air_velocity',
            'ExpectancyFactor': 'expectancy_factor', 'AdaptiveCoefficientCooling': 'adaptive_coefficient_cooling',
            'AdaptiveCoefficientHeating': 'adaptive_coefficient_heating', 'CustAST_metric': 'custom_outdoor_metric',
            'CustAST_alpha': 'custom_alpha', 'CustAST_days': 'custom_days',
            'HeatingSetpointMinimum': 'heating_setpoint_minimum', 'CoolingSetpointMaximum': 'cooling_setpoint_maximum'}


def _simulation(parameters_type):
    return ParametricSimulation(buildings=None, epws=['Test.epw'], parameters_type=parameters_type,
                                bypass_add_accis=True)


def test_the_parameters_are_registered():
    for name, modifier in PMV_INPUTS.items():
        assert params_dicts.apmv_setpoints_params[name] is modifier
        assert params_dicts.epmv_setpoints_params[name] is modifier
        assert name in parameters.get_available_params_apmv_setpoints()
        assert name in parameters.get_available_params_epmv_setpoints()
        assert name not in params_dicts.accim_custom_model_params
    for name, modifier in METRIC_INPUTS.items():
        assert params_dicts.accim_custom_model_params[name] is modifier
        assert name in parameters.get_available_params_accim_custom_models()
        assert name not in params_dicts.accim_predef_model_params
    assert set(PMV_INPUTS) <= set(_simulation('apmv setpoints').get_available_parameters())
    assert set(PMV_INPUTS) <= set(_simulation('epmv setpoints').get_available_parameters())
    assert set(METRIC_INPUTS) <= set(_simulation('accim custom model').get_available_parameters())
    for name in (*PMV_INPUTS, *METRIC_INPUTS):
        assert params_dicts.all_params[name] in (PMV_INPUTS.get(name), METRIC_INPUTS.get(name))
    for wrapper, name in WRAPPERS.items():
        assert getattr(parameters, wrapper)().name == name
        assert name in params_dicts.all_params


def test_the_ranges_of_the_inputs_of_the_pmv():
    # ISO 7730:2025, section 4: 46 to 232 W/m2 (0.8 to 4 met) with A_Du = 1.8 m2 (also that of EnergyPlus,
    # Engineering Reference 19.1); 0 to 2 clo; 0 to 1 m/s
    assert PMV_BODY_SURFACE_AREA == 1.8
    assert PMV_INPUT_RANGES['activity_level'] == pytest.approx((82.8, 417.6))
    assert PMV_INPUT_RANGES['clothing_insulation'] == (0.0, 2.0)
    assert PMV_INPUT_RANGES['air_velocity'] == (0.0, 1.0)
    assert ASHRAE55_MAX_CLOTHING_INSULATION == 1.5
    check = param_apmv._check_pmv_input
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert check('clothing_insulation', 1.5) == 1.5
        assert check('activity_level', 82.8) == 82.8 and check('activity_level', 417.6) == 417.6
        assert check('air_velocity', 0) == 0
    with pytest.warns(UserWarning, match=r'clothing_insulation 1\.8 clo is above 1\.5 clo, with which ASHRAE 55-2020'):
        check('clothing_insulation', 1.8)
    with pytest.warns(UserWarning, match=r'clothing_insulation 2\.5 clo is outside 0\.0 to 2\.0 clo, the range in '
                                         r'which ISO 7730:2025 \(section 4\) uses the PMV'):
        check('clothing_insulation', 2.5)
    with pytest.warns(UserWarning, match=r'activity_level 70 W/person is outside 82\.8 to 417\.6 W/person'):
        check('activity_level', 70)
    with pytest.warns(UserWarning, match=r'air_velocity 1\.5 m/s is outside 0\.0 to 1\.0 m/s'):
        check('air_velocity', 1.5)
    for value in (-0.1, '0.5', True):
        with pytest.raises(ValueError, match='must be a number of at least 0'):
            check('air_velocity', value)


def test_the_plans_drop_a_floor_that_is_not_below_the_ceiling():
    plan = pd.DataFrame({'heating_setpoint_minimum': [18, 21, 22, 26], 'cooling_setpoint_maximum': [26, 25, 22, 25]})
    kept = param_accis.drop_invalid_param_combinations(plan)
    assert kept.values.tolist() == [[18, 26], [21, 25]]
    # The full sets of the accim custom models too (those of the predefined models already were)
    simulation = _simulation('accim custom model')
    simulation.epws = []
    simulation.parameters_list = [parameters.accis_parameter('heating_setpoint_minimum', [20, 26]),
                                  parameters.accis_parameter('cooling_setpoint_maximum', [25.5, 26])]
    simulation.descriptors_has_options = True
    simulation.sampling_full_set()
    limits = simulation.parameters_values_df[['heating_setpoint_minimum', 'cooling_setpoint_maximum']]
    assert limits.values.tolist() == [[20, 25.5], [20, 26]]


def _apmv_model(tmp_path):
    from accim.sim.accis import load_idf
    from accim.sim.apmv import apply_apmv_setpoints

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        apply_apmv_setpoints(building=building, output_frequencies=['hourly'], verbose=False)
    return building


def _schedule_values(building, prefix):
    """The values of the schedules of the People objects, by the name of the schedule (the last field of each
    Schedule:Compact with one value: 'Until: 24:00,0.5' as accim writes it, or '0.5' once eppy has read it again)."""
    return {s.Name: float(str(s.fieldvalues[-1]).split(',')[-1]) for s in building.idfobjects['Schedule:Compact']
            if s.Name.startswith(prefix)}


@needs_idd
def test_the_modifiers_of_the_inputs_of_the_pmv(tmp_path):
    building = _apmv_model(tmp_path)
    param_apmv.change_clothing_insulation_all_zones(building, 0.7)
    parameters.Met().modify(building, 126)
    parameters.AirVelocity().modify(building, 0.2)
    clothing = _schedule_values(building, 'Sch_Clo_')
    assert clothing and set(clothing.values()) == {0.7}
    assert set(_schedule_values(building, 'Sch_Act_').values()) == {126}
    assert set(_schedule_values(building, 'Sch_Vel_').values()) == {0.2}
    assert all(p.Clothing_Insulation_Schedule_Name in clothing for p in building.idfobjects['People'])


@needs_idd
def test_a_two_point_design_of_the_clothing_insulation(tmp_path, monkeypatch):
    from besos.evaluator import EvaluatorEP

    from accim.sim.accis import load_idf

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    monkeypatch.chdir(tmp_path)
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        simulation = ParametricSimulation(buildings=[building], epws=[str(EPW)], parameters_type='apmv setpoints',
                                          output_frequencies=['hourly'], verbose=False)
    simulation.set_parameters({'clothing_insulation': [0.5, 1.0]})
    simulation.set_problem()
    simulation.sampling_full_set()
    plan = simulation.parameters_values_df
    assert plan['clothing_insulation'].tolist() == [0.5, 1.0]
    # The IDFs of the design, as the simulations of the parametric module get them (without running EnergyPlus)
    evaluator = EvaluatorEP(problem=simulation.problem, building=simulation.building, epw=str(EPW))
    for row, value in enumerate(plan['clothing_insulation']):
        evaluator.generate_building(plan, row, str(tmp_path / f'design_{row}'))
        generated = load_idf(tmp_path / f'design_{row}.idf')
        clothing = _schedule_values(generated, 'Sch_Clo_')
        assert len(clothing) == 2 and set(clothing.values()) == {value}
        assert sorted(p.Clothing_Insulation_Schedule_Name for p in generated.idfobjects['People']) == sorted(clothing)


def _custom_model(tmp_path):
    from accim.sim.accis import add_accis_to_idf, load_idf, modify_accis

    shutil.copy(SAMPLE_IDF, tmp_path / 'model.idf')
    building = load_idf(tmp_path / 'model.idf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        add_accis_to_idf(building, script_type='vrf_ac', supply_air_temp_input_method='temperature difference',
                         output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                         setpoint_type='temperature', verbose=False)
    modify_accis(building, comfort_standard=99, category=80, comfort_mode=3)
    return building


def _inputs(building):
    from accim.sim.ems.inputs import input_programs, read_inputs

    return {zone: {name: values.get(name) for name in ('CustAST_metric', 'CustAST_alpha', 'CustAST_days')}
            for zone, values in ((z, read_inputs(p)) for z, p in input_programs(building).items())}


@needs_idd
def test_the_modifiers_of_the_outdoor_metric_of_the_custom_model(tmp_path):
    from accim.sim.ems import outdoor_metric as om

    building = _custom_model(tmp_path)
    assert not om.has_outdoor_metric_code(building)
    # The parameters of a sample are applied one after the other: alpha before the metric is kept
    parameters.CustAST_alpha().modify(building, 0.7)
    assert not om.has_outdoor_metric_code(building)
    with pytest.warns(UserWarning, match='begins with the running mean of ASHRAE 55'):
        parameters.CustAST_metric().modify(building, 2.0)
    assert om.has_outdoor_metric_code(building) and not om.begins_with_weather_file(building)
    assert all(values == {'CustAST_metric': 2, 'CustAST_alpha': 0.7, 'CustAST_days': 30}
               for values in _inputs(building).values())
    # The days of a range are rounded; more than 30 days keeps more daily means
    parameters.CustAST_days().modify(building, 44.6)
    assert {values['CustAST_days'] for values in _inputs(building).values()} == {45}
    assert 'set Tday_45 = Tday_44' in [str(line).strip() for line in building.getobject(
        'EnergyManagementSystem:Program', om.PROGRAM).fieldvalues[2:]]
    with pytest.warns(UserWarning, match=r'custom_alpha 0\.95 .* is outside 0\.6 to 0\.9'):
        param_accis.modify_CustAST_alpha(building, 0.95)
    # 'monthly_mean' needs the monthly means of a weather file (modify_accis with epw)
    with pytest.raises(ValueError, match="'monthly_mean' needs the weather file"):
        param_accis.modify_CustAST_metric(building, 'monthly_mean')
    with pytest.raises(ValueError, match='custom_outdoor_metric must be one of'):
        param_accis.modify_CustAST_metric(building, 2.5)
    # Back to 'pmot': the model has no EMS code of the outdoor metric
    param_accis.modify_CustAST_metric(building, 0)
    assert not om.has_outdoor_metric_code(building)


@needs_idd
def test_the_metric_keeps_the_weather_file_of_modify_accis(tmp_path):
    from accim.sim.accis import modify_accis
    from accim.sim.ems import outdoor_metric as om

    building = _custom_model(tmp_path)
    modify_accis(building, comfort_standard=99, category=80, comfort_mode=3, custom_outdoor_metric='rmot_alpha',
                 epw=str(EPW))
    assert om.begins_with_weather_file(building)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        parameters.CustAST_metric().modify(building, 'monthly_mean')
        parameters.CustAST_alpha().modify(building, 0.75)
    assert om.begins_with_weather_file(building)
    assert {values['CustAST_metric'] for values in _inputs(building).values()} == {6}


@needs_idd
@pytest.mark.skipif(LEGACY_IDF is None, reason='needs the output IDF of accim 0.x of the repository')
def test_the_models_of_earlier_versions_have_no_outdoor_metric(tmp_path):
    from accim.sim.accis import load_idf

    shutil.copy(LEGACY_IDF, tmp_path / 'legacy.idf')
    building = load_idf(tmp_path / 'legacy.idf')
    for modifier, value in ((param_accis.modify_CustAST_metric, 2), (param_accis.modify_CustAST_alpha, 0.7),
                            (param_accis.modify_CustAST_days, 7)):
        with pytest.raises(ValueError, match="only has the outdoor metric 'pmot'"):
            modifier(building, value)
