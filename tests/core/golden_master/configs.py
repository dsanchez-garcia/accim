"""Configurations of the golden master: what to generate with accim, and from which input models.

Each batch configuration copies some input models into an empty folder and runs ``AddAccis`` there; each single
configuration reads one input model and calls the in-memory functions on it (``add_accis_to_idf``, ``modify_accis``,
``gen_outputs_df`` and the aPMV setpoints). The arguments have the names of accim 1.0.0; ``LEGACY_NAMES`` gives
their names in accim 0.x, to run the same configurations with it (``runner.py write --legacy``).

These are the 29 configurations with which accim 1.0.0 was checked against accim 0.8.2 (see the migration guide,
section 9.3); with accim 0.8.2, b10 gives no output IDF (its existing HVAC system has two kinds of heating coils,
which 'ex_mm' rejected until it read the loads of the thermostats instead of the coils). b21 and b22 were added later
with the arguments of the existing HVAC systems (``existing_hvac_*``), which accim 0.x does not have (``runner.py
write --legacy`` leaves them out: b21 is then b11).
"""

ALL_CS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 99]
ALL_CAT = [1, 2, 3, 80, 85, 90]
ALL_CM = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]

# Input models (inputs/<name>.idf.xz): sample IDFs of accim/sample_files/sample IDFs/input_IDFs, updated to the
# version of EnergyPlus given here with accim.utils.update_idf_version when it was another one.
INPUT_MODELS = {
    'vrf2zones': ('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf', '25.1'),
    'exptac': ('TestModel_ExistingHVAC_PTAC_V950.idf', '25.1'),
    'exrad': ('TestModel_ExistingHVAC_ElectricRadiators_V950.idf', '25.1'),
    'exbeams': ('TestModel_ExistingHVAC_CooledBeams_V950.idf', '25.1'),
    'osmofficeex': ('OSM_SmallOffice_exHVAC_V2320.idf', '25.1'),
    'osmofficenohvac': ('OSM_SmallOffice_noHVAC_V2320.idf', '25.1'),
    'osmresschvent': ('OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent.idf', '25.1'),
    'osmres': ('OSM_TestResidentialUnit_v01_onlygeometry.idf', '25.1'),
    'vrf2zones262': ('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf', '26.2'),
    # vrf2zones262 with a People:Definition and a People:Instance object instead of each People object
    'vrf2zones262inst': ('TestModel_onlyGeometryForVRFsystem_2zones_CalcVent_V2510.idf', '26.2'),
}

BASE = dict(
    supply_air_temp_input_method='temperature difference',
    output_type='standard',
    output_frequencies=['hourly'],
    keep_existing_outputs=False,
    energyplus_version='auto',
    setpoint_type='temperature',
    confirm=True,
    verbose=False,
)

# AddAccis on the files of the working folder
BATCH = {
    # every valid comfort model with full air-conditioning
    'b01_vrf_ac_all': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_ac', comfort_standard=ALL_CS, category=ALL_CAT, comfort_mode=ALL_CM, hvac_mode=[0])),
    # mixed mode: HVAC modes, ventilation controls, offsets, tolerances and other arguments
    'b02_vrf_mm_grid': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_mm', comfort_standard=[1, 13], category=[3, 80], comfort_mode=[0.1, 2, 3], hvac_mode=[0, 1, 2],
        ventilation_control=[0, 1, 2, 3], ventilation_setpoint_offset=[0, -1.5], min_outdoor_temp_offset=[50], max_wind_speed=[50],
        setpoint_tolerance_start=0.1, setpoint_tolerance_end=0.2, setpoint_tolerance_step=0.1, name_suffix='grid', setpoint_accuracy=2,
        category_cooling_offset=0.5, category_heating_offset=-0.5, cooling_season_start='15/05', cooling_season_end=300,
        output_type='detailed', output_frequencies=['hourly', 'daily'], keep_existing_outputs=True,
        add_building_averages=True, debug_ems=True, make_outputs_dataframe=True,
        opening_factor_max_temp_diff=5, opening_factor_min_temp_diff=2, min_opening_factor=0.5)),
    'b03_vrf_mm_all_cs': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_mm', comfort_standard=ALL_CS, category=[1, 80], comfort_mode=[0, 1.2, 3], hvac_mode=[2],
        ventilation_control=[1], ventilation_setpoint_offset=[1], min_outdoor_temp_offset=[4], max_wind_speed=[6], output_frequencies=['timestep', 'monthly'])),
    'b04_vrf_pmv': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_ac', setpoint_type='pmv', comfort_standard=[1], category=[3], comfort_mode=[3], hvac_mode=[0])),
    'b05_vrf_mm_pmv_simplified': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_mm', setpoint_type='pmv', supply_air_temp_input_method='supply air temperature',
        output_type='simplified', comfort_standard=[2], category=[80], comfort_mode=[3], hvac_mode=[2], ventilation_control=[0])),
    'b06_ex_ac_ptac': dict(models=['exptac'], kwargs=dict(
        BASE, script_type='ex_ac', comfort_standard=[1, 2], category=[2, 90], comfort_mode=[2, 3], hvac_mode=[0],
        output_type='simplified', output_frequencies=['timestep'])),
    'b07_ex_mm_ptac': dict(models=['exptac'], kwargs=dict(
        BASE, script_type='ex_mm', comfort_standard=[2], category=[80], comfort_mode=[3], hvac_mode=[1, 2], ventilation_control=[0, 2],
        opening_factor_max_temp_diff=5, opening_factor_min_temp_diff=2, min_opening_factor=0.5, add_building_averages=True)),
    'b08_ex_mm_radiators': dict(models=['exrad'], kwargs=dict(
        BASE, script_type='ex_mm', comfort_standard=[1], category=[2], comfort_mode=[3], hvac_mode=[2], ventilation_control=[1])),
    'b09_ex_mm_beams': dict(models=['exbeams'], kwargs=dict(
        BASE, script_type='ex_mm', comfort_standard=[14], category=[90], comfort_mode=[1.3, 2], hvac_mode=[2], ventilation_control=[3])),
    # an existing HVAC system with two kinds of heating coils (accim 0.8.2 rejected the model)
    'b10_ex_mm_osm_office': dict(models=['osmofficeex'], kwargs=dict(
        BASE, script_type='ex_mm', comfort_standard=[2], category=[90], comfort_mode=[3], hvac_mode=[0, 2], ventilation_control=[0],
        output_type='detailed')),
    'b11_ex_ac_osm_office': dict(models=['osmofficeex'], kwargs=dict(
        BASE, script_type='ex_ac', comfort_standard=[1], category=[1], comfort_mode=[0, 3], hvac_mode=[0],
        keep_existing_outputs=True)),
    'b12_vrf_mm_osm_office_nohvac': dict(models=['osmofficenohvac'], kwargs=dict(
        BASE, script_type='vrf_mm', comfort_standard=[7], category=[85], comfort_mode=[1, 3], hvac_mode=[2], ventilation_control=[0])),
    'b13_vrf_mm_scheduled_vent': dict(models=['osmresschvent'], kwargs=dict(
        BASE, script_type='vrf_mm', comfort_standard=[1, 99], category=[3, 80], comfort_mode=[3], hvac_mode=[1, 2],
        ventilation_control=[0, 1], output_type='detailed', custom_slope=0.4, custom_intercept=15, custom_cooling_offset=3,
        custom_heating_offset=-3, custom_cooling_upper_limit=32, custom_cooling_lower_limit=12, custom_heating_upper_limit=31,
        custom_heating_lower_limit=11)),
    'b14_vrf_ac_osm_res': dict(models=['osmres'], kwargs=dict(
        BASE, script_type='vrf_ac', comfort_standard=[22, 0], category=[2], comfort_mode=[0], hvac_mode=[0], add_building_averages=True)),
    'b15_two_models_explicit_version': dict(models=['vrf2zones', 'osmresschvent'], kwargs=dict(
        BASE, script_type='vrf_mm', energyplus_version='25.1', comfort_standard=[3], category=[90], comfort_mode=[3],
        hvac_mode=[2], ventilation_control=[0], vrf_eer=3.5, vrf_cop=3.2, vrf_availability_schedule='On', make_outputs_dataframe=True)),
    'b16_vrf_mm_262': dict(models=['vrf2zones262'], kwargs=dict(
        BASE, script_type='vrf_mm', comfort_standard=[1, 99], category=[3, 80], comfort_mode=[3], hvac_mode=[2], ventilation_control=[0])),
    'b17_vrf_mm_262_instances': dict(models=['vrf2zones262inst'], kwargs=dict(
        BASE, script_type='vrf_mm', comfort_standard=[1], category=[3], comfort_mode=[3], hvac_mode=[2], ventilation_control=[0],
        add_building_averages=True)),
    'b18_vrf_ac_262_pmv_instances': dict(models=['vrf2zones262inst'], kwargs=dict(
        BASE, script_type='vrf_ac', setpoint_type='pmv', comfort_standard=[1], category=[3], comfort_mode=[3], hvac_mode=[0])),
    # outputs_dataframe: the temperature outputs of a first run with make_outputs_dataframe
    'b19_take_dataframe': dict(models=['vrf2zones'], take_dataframe=True, kwargs=dict(
        BASE, script_type='vrf_ac', comfort_standard=[2], category=[80], comfort_mode=[3], hvac_mode=[0])),
    'b20_tolerance_range': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_ac', comfort_standard=[0, 2], category=[80], comfort_mode=[3], hvac_mode=[0],
        setpoint_tolerance_start=0, setpoint_tolerance_end=1, setpoint_tolerance_step=0.25)),
    # b11 with the thermostats of the model, which control the air temperature (as accim 0.x and as b11 before the
    # operative temperature control of the existing HVAC systems)
    'b21_ex_ac_osm_office_air_temperature': dict(models=['osmofficeex'], kwargs=dict(
        BASE, script_type='ex_ac', comfort_standard=[1], category=[1], comfort_mode=[0, 3], hvac_mode=[0],
        keep_existing_outputs=True, existing_hvac_operative_temperature_control=False)),
    # b10 with the existing HVAC systems always available, with the outdoor temperature limits of the VRF systems and
    # with backup ideal loads air systems
    'b22_ex_mm_osm_office_existing_hvac_options': dict(models=['osmofficeex'], kwargs=dict(
        BASE, script_type='ex_mm', comfort_standard=[2], category=[90], comfort_mode=[3], hvac_mode=[2],
        ventilation_control=[0], output_type='detailed', existing_hvac_availability_schedule='On 24/7',
        existing_hvac_widen_outdoor_temperature_limits=True, existing_hvac_ideal_loads_backup=True)),
}

_ADD = dict(supply_air_temp_input_method='temperature difference', output_type='standard', output_frequencies=['hourly'],
            keep_existing_outputs=False, setpoint_type='temperature', verbose=False)

# In-memory functions on one model: a list of (call, arguments), in order. 'class_add' is the class of
# accim 0.x (accis_single_idf.addAccis); with accim 1.0.0 it is add_accis_to_idf, as 'add'.
SINGLE = {
    's01_add_vrf_mm': dict(model='vrf2zones', calls=[
        ('add', dict(_ADD, script_type='vrf_mm')),
    ]),
    's02_add_modify': dict(model='vrf2zones', calls=[
        ('add', dict(_ADD, script_type='vrf_mm', supply_air_temp_input_method='supply air temperature',
                     output_type='detailed', keep_existing_outputs=True, add_building_averages=True)),
        ('modify', dict(comfort_standard=2, category=80, comfort_mode=3, hvac_mode=2, ventilation_control=0, ventilation_setpoint_offset=1, min_outdoor_temp_offset=3,
                        max_wind_speed=8, setpoint_tolerance=0.25, cooling_season_start='01/06', cooling_season_end=250)),
        ('modify', dict(comfort_standard=99, category=80, comfort_mode=3, hvac_mode=2, ventilation_control=2, custom_slope=0.3, custom_intercept=17,
                        custom_cooling_offset=2.5, custom_heating_offset=-2.5, custom_cooling_upper_limit=30,
                        custom_cooling_lower_limit=10, custom_heating_upper_limit=30, custom_heating_lower_limit=10, opening_factor_max_temp_diff=7,
                        opening_factor_min_temp_diff=1.5, min_opening_factor=0.3)),
    ]),
    's03_add_ex_ac': dict(model='exptac', calls=[
        ('add', dict(script_type='ex_ac', output_type='simplified', output_frequencies=['timestep'],
                     keep_existing_outputs=False, setpoint_type='temperature', verbose=False)),
    ]),
    's04_add_ex_mm_osm': dict(model='osmofficeex', calls=[
        ('add', dict(script_type='ex_mm', output_type='standard', output_frequencies=['hourly'], keep_existing_outputs=False,
                     setpoint_type='temperature', verbose=False, debug_ems=True)),
    ]),
    's05_gen_outputs_df': dict(model='vrf2zones', calls=[
        ('gen_outputs_df', dict(script_type='vrf_ac', output_type='standard', output_frequencies=['hourly', 'daily'],
                                keep_existing_outputs=False, setpoint_type='temperature')),
    ]),
    's06_class_add_vrf_mm_pmv': dict(model='vrf2zones', calls=[
        ('class_add', dict(_ADD, script_type='vrf_mm', setpoint_type='pmv')),
    ]),
    's07_apmv_default': dict(model='vrf2zones', calls=[
        ('apmv_vrf', dict()),
        ('apmv', dict(output_frequencies=['hourly'], verbose=False)),
    ]),
    # '*first*': the first target of the model (get_available_target_names)
    's08_apmv_dicts': dict(model='osmresschvent', calls=[
        ('apmv_vrf', dict()),
        ('apmv', dict(output_frequencies=['hourly', 'timestep'], other_pmv_related_outputs=False,
                      adaptive_coefficient_cooling={'*first*': 0.3}, pmv_cooling_setpoint=0.4, cooling_season_start='01/06',
                      cooling_season_end='15/09', verbose=False)),
    ]),
    's09_add_vrf_mm_262_instances': dict(model='vrf2zones262inst', calls=[
        ('add', dict(_ADD, script_type='vrf_mm')),
        ('modify', dict(comfort_standard=1, category=3, comfort_mode=3, hvac_mode=2, ventilation_control=0)),
    ]),
}

NAMES = list(BATCH) + list(SINGLE)

# The arguments that accim 0.x does not have, which runner.py write --legacy leaves out (their values in the
# configurations b21 and b22; accim 0.x controlled the air temperature, as b21)
NEW_ARGUMENTS = ('existing_hvac_operative_temperature_control', 'existing_hvac_availability_schedule',
                 'existing_hvac_widen_outdoor_temperature_limits', 'existing_hvac_ideal_loads_backup')

# The names of the arguments in accim 0.x (accim.sim.arguments.LEGACY_ARGUMENT_NAMES, reversed)
LEGACY_NAMES = {
    'script_type': 'ScriptType', 'supply_air_temp_input_method': 'SupplyAirTempInputMethod',
    'output_type': 'Output_type', 'output_frequencies': 'Output_freqs', 'keep_existing_outputs': 'Output_keep_existing',
    'make_outputs_dataframe': 'Output_gen_dataframe', 'outputs_dataframe': 'Output_take_dataframe',
    'energyplus_version': 'EnergyPlus_version', 'setpoint_type': 'TempCtrl',
    'vrf_availability_schedule': 'VRFschedule', 'vrf_eer': 'eer', 'vrf_cop': 'cop',
    'add_building_averages': 'make_averages', 'debug_ems': 'debugging', 'comfort_standard': 'ComfStand',
    'category': 'CAT', 'category_cooling_offset': 'CATcoolOffset', 'category_heating_offset': 'CATheatOffset',
    'comfort_mode': 'ComfMod', 'setpoint_accuracy': 'SetpointAcc', 'custom_cooling_upper_limit': 'CustAST_ACSTaul',
    'custom_cooling_lower_limit': 'CustAST_ACSTall', 'custom_heating_upper_limit': 'CustAST_AHSTaul',
    'custom_heating_lower_limit': 'CustAST_AHSTall', 'custom_slope': 'CustAST_m', 'custom_intercept': 'CustAST_n',
    'custom_cooling_offset': 'CustAST_ACSToffset', 'custom_heating_offset': 'CustAST_AHSToffset',
    'cooling_season_start': 'CoolSeasonStart', 'cooling_season_end': 'CoolSeasonEnd', 'hvac_mode': 'HVACmode',
    'ventilation_control': 'VentCtrl', 'opening_factor_max_temp_diff': 'MaxTempDiffVOF',
    'opening_factor_min_temp_diff': 'MinTempDiffVOF', 'min_opening_factor': 'MultiplierVOF',
    'ventilation_setpoint_offset': 'VSToffset', 'min_outdoor_temp_offset': 'MinOToffset',
    'max_wind_speed': 'MaxWindSpeed', 'setpoint_tolerance_start': 'ASTtol_start',
    'setpoint_tolerance_end': 'ASTtol_end_input', 'setpoint_tolerance_step': 'ASTtol_steps',
    'setpoint_tolerance': 'ASTtol', 'name_suffix': 'NameSuffix', 'verbose': 'verboseMode', 'confirm': 'confirmGen',
}
# The names of the arguments of apply_apmv_setpoints and add_vrf_system in accim 0.x (accim.sim.apmv._LEGACY_ARGUMENTS,
# reversed)
LEGACY_APMV_NAMES = {
    'output_frequencies': 'outputs_freq', 'other_pmv_related_outputs': 'other_PMV_related_outputs',
    'adaptive_coefficient_cooling': 'adap_coeff_cooling', 'adaptive_coefficient_heating': 'adap_coeff_heating',
    'pmv_cooling_setpoint': 'pmv_cooling_sp', 'pmv_heating_setpoint': 'pmv_heating_sp', 'verbose': 'verbose_mode',
}

def models(name):
    """The input models of a configuration."""
    return BATCH[name]['models'] if name in BATCH else [SINGLE[name]['model']]


def energyplus_versions(name):
    """The EnergyPlus versions whose IDD a configuration needs."""
    return sorted({INPUT_MODELS[model][1] for model in models(name)})
