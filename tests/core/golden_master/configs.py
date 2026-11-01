"""Configurations of the golden master: what to generate with accim, and from which input models.

Each batch configuration copies some input models into an empty folder and runs ``AddAccis`` there; each single
configuration reads one input model and calls the in-memory functions on it (``add_accis_to_idf``, ``modify_accis``,
``gen_outputs_df`` and the aPMV setpoints). The arguments have the names of accim 1.0.0; ``LEGACY_NAMES`` gives
their names in accim 0.x, to run the same configurations with it (``runner.py write --legacy``).

These are the 29 configurations with which accim 1.0.0 was checked against accim 0.8.2 (see the migration guide,
section 9.3); with accim 0.8.2, b10 gives no output IDF (its existing HVAC system has two kinds of heating coils,
which 'ex_mm' rejected until it read the loads of the thermostats instead of the coils).
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
    output_freqs=['hourly'],
    output_keep_existing=False,
    energyplus_version='auto',
    temp_ctrl='temperature',
    confirm_gen=True,
    verbose_mode=False,
)

# AddAccis on the files of the working folder
BATCH = {
    # every valid comfort model with full air-conditioning
    'b01_vrf_ac_all': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_ac', comf_stand=ALL_CS, cat=ALL_CAT, comf_mod=ALL_CM, hvac_mode=[0])),
    # mixed mode: HVAC modes, ventilation controls, offsets, tolerances and other arguments
    'b02_vrf_mm_grid': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_mm', comf_stand=[1, 13], cat=[3, 80], comf_mod=[0.1, 2, 3], hvac_mode=[0, 1, 2],
        vent_ctrl=[0, 1, 2, 3], vst_offset=[0, -1.5], min_ot_offset=[50], max_wind_speed=[50],
        ast_tol_start=0.1, ast_tol_end_input=0.2, ast_tol_steps=0.1, name_suffix='grid', setpoint_acc=2,
        cat_cool_offset=0.5, cat_heat_offset=-0.5, cool_season_start='15/05', cool_season_end=300,
        output_type='detailed', output_freqs=['hourly', 'daily'], output_keep_existing=True,
        make_averages=True, debugging=True, output_gen_dataframe=True,
        max_temp_diff_vof=5, min_temp_diff_vof=2, multiplier_vof=0.5)),
    'b03_vrf_mm_all_cs': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_mm', comf_stand=ALL_CS, cat=[1, 80], comf_mod=[0, 1.2, 3], hvac_mode=[2],
        vent_ctrl=[1], vst_offset=[1], min_ot_offset=[4], max_wind_speed=[6], output_freqs=['timestep', 'monthly'])),
    'b04_vrf_pmv': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_ac', temp_ctrl='pmv', comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[0])),
    'b05_vrf_mm_pmv_simplified': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_mm', temp_ctrl='pmv', supply_air_temp_input_method='supply air temperature',
        output_type='simplified', comf_stand=[2], cat=[80], comf_mod=[3], hvac_mode=[2], vent_ctrl=[0])),
    'b06_ex_ac_ptac': dict(models=['exptac'], kwargs=dict(
        BASE, script_type='ex_ac', comf_stand=[1, 2], cat=[2, 90], comf_mod=[2, 3], hvac_mode=[0],
        output_type='simplified', output_freqs=['timestep'])),
    'b07_ex_mm_ptac': dict(models=['exptac'], kwargs=dict(
        BASE, script_type='ex_mm', comf_stand=[2], cat=[80], comf_mod=[3], hvac_mode=[1, 2], vent_ctrl=[0, 2],
        max_temp_diff_vof=5, min_temp_diff_vof=2, multiplier_vof=0.5, make_averages=True)),
    'b08_ex_mm_radiators': dict(models=['exrad'], kwargs=dict(
        BASE, script_type='ex_mm', comf_stand=[1], cat=[2], comf_mod=[3], hvac_mode=[2], vent_ctrl=[1])),
    'b09_ex_mm_beams': dict(models=['exbeams'], kwargs=dict(
        BASE, script_type='ex_mm', comf_stand=[14], cat=[90], comf_mod=[1.3, 2], hvac_mode=[2], vent_ctrl=[3])),
    # an existing HVAC system with two kinds of heating coils (accim 0.8.2 rejected the model)
    'b10_ex_mm_osm_office': dict(models=['osmofficeex'], kwargs=dict(
        BASE, script_type='ex_mm', comf_stand=[2], cat=[90], comf_mod=[3], hvac_mode=[0, 2], vent_ctrl=[0],
        output_type='detailed')),
    'b11_ex_ac_osm_office': dict(models=['osmofficeex'], kwargs=dict(
        BASE, script_type='ex_ac', comf_stand=[1], cat=[1], comf_mod=[0, 3], hvac_mode=[0],
        output_keep_existing=True)),
    'b12_vrf_mm_osm_office_nohvac': dict(models=['osmofficenohvac'], kwargs=dict(
        BASE, script_type='vrf_mm', comf_stand=[7], cat=[85], comf_mod=[1, 3], hvac_mode=[2], vent_ctrl=[0])),
    'b13_vrf_mm_scheduled_vent': dict(models=['osmresschvent'], kwargs=dict(
        BASE, script_type='vrf_mm', comf_stand=[1, 99], cat=[3, 80], comf_mod=[3], hvac_mode=[1, 2],
        vent_ctrl=[0, 1], output_type='detailed', cust_ast_m=0.4, cust_ast_n=15, cust_ast_acst_offset=3,
        cust_ast_ahst_offset=-3, cust_ast_acst_aul=32, cust_ast_acst_all=12, cust_ast_ahst_aul=31,
        cust_ast_ahst_all=11)),
    'b14_vrf_ac_osm_res': dict(models=['osmres'], kwargs=dict(
        BASE, script_type='vrf_ac', comf_stand=[22, 0], cat=[2], comf_mod=[0], hvac_mode=[0], make_averages=True)),
    'b15_two_models_explicit_version': dict(models=['vrf2zones', 'osmresschvent'], kwargs=dict(
        BASE, script_type='vrf_mm', energyplus_version='25.1', comf_stand=[3], cat=[90], comf_mod=[3],
        hvac_mode=[2], vent_ctrl=[0], eer=3.5, cop=3.2, vrf_schedule='On', output_gen_dataframe=True)),
    'b16_vrf_mm_262': dict(models=['vrf2zones262'], kwargs=dict(
        BASE, script_type='vrf_mm', comf_stand=[1, 99], cat=[3, 80], comf_mod=[3], hvac_mode=[2], vent_ctrl=[0])),
    'b17_vrf_mm_262_instances': dict(models=['vrf2zones262inst'], kwargs=dict(
        BASE, script_type='vrf_mm', comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[2], vent_ctrl=[0],
        make_averages=True)),
    'b18_vrf_ac_262_pmv_instances': dict(models=['vrf2zones262inst'], kwargs=dict(
        BASE, script_type='vrf_ac', temp_ctrl='pmv', comf_stand=[1], cat=[3], comf_mod=[3], hvac_mode=[0])),
    # output_take_dataframe: the temperature outputs of a first run with output_gen_dataframe
    'b19_take_dataframe': dict(models=['vrf2zones'], take_dataframe=True, kwargs=dict(
        BASE, script_type='vrf_ac', comf_stand=[2], cat=[80], comf_mod=[3], hvac_mode=[0])),
    'b20_tolerance_range': dict(models=['vrf2zones'], kwargs=dict(
        BASE, script_type='vrf_ac', comf_stand=[0, 2], cat=[80], comf_mod=[3], hvac_mode=[0],
        ast_tol_start=0, ast_tol_end_input=1, ast_tol_steps=0.25)),
}

_ADD = dict(supply_air_temp_input_method='temperature difference', output_type='standard', output_freqs=['hourly'],
            output_keep_existing=False, temp_ctrl='temperature', verbose_mode=False)

# In-memory functions on one model: a list of (call, arguments), in order. 'class_add' is the class of
# accim 0.x (accis_single_idf.addAccis); with accim 1.0.0 it is add_accis_to_idf, as 'add'.
SINGLE = {
    's01_add_vrf_mm': dict(model='vrf2zones', calls=[
        ('add', dict(_ADD, script_type='vrf_mm')),
    ]),
    's02_add_modify': dict(model='vrf2zones', calls=[
        ('add', dict(_ADD, script_type='vrf_mm', supply_air_temp_input_method='supply air temperature',
                     output_type='detailed', output_keep_existing=True, make_averages=True)),
        ('modify', dict(comf_stand=2, cat=80, comf_mod=3, hvac_mode=2, vent_ctrl=0, vst_offset=1, min_ot_offset=3,
                        max_wind_speed=8, ast_tol=0.25, cool_season_start='01/06', cool_season_end=250)),
        ('modify', dict(comf_stand=99, cat=80, comf_mod=3, hvac_mode=2, vent_ctrl=2, cust_ast_m=0.3, cust_ast_n=17,
                        cust_ast_acst_offset=2.5, cust_ast_ahst_offset=-2.5, cust_ast_acst_aul=30,
                        cust_ast_acst_all=10, cust_ast_ahst_aul=30, cust_ast_ahst_all=10, max_temp_diff_vof=7,
                        min_temp_diff_vof=1.5, multiplier_vof=0.3)),
    ]),
    's03_add_ex_ac': dict(model='exptac', calls=[
        ('add', dict(script_type='ex_ac', output_type='simplified', output_freqs=['timestep'],
                     output_keep_existing=False, temp_ctrl='temperature', verbose_mode=False)),
    ]),
    's04_add_ex_mm_osm': dict(model='osmofficeex', calls=[
        ('add', dict(script_type='ex_mm', output_type='standard', output_freqs=['hourly'], output_keep_existing=False,
                     temp_ctrl='temperature', verbose_mode=False, debugging=True)),
    ]),
    's05_gen_outputs_df': dict(model='vrf2zones', calls=[
        ('gen_outputs_df', dict(script_type='vrf_ac', output_type='standard', output_freqs=['hourly', 'daily'],
                                output_keep_existing=False, temp_ctrl='temperature')),
    ]),
    's06_class_add_vrf_mm_pmv': dict(model='vrf2zones', calls=[
        ('class_add', dict(_ADD, script_type='vrf_mm', temp_ctrl='pmv')),
    ]),
    's07_apmv_default': dict(model='vrf2zones', calls=[
        ('apmv_vrf', dict()),
        ('apmv', dict(outputs_freq=['hourly'], verbose_mode=False)),
    ]),
    # '*first*': the first target of the model (get_available_target_names)
    's08_apmv_dicts': dict(model='osmresschvent', calls=[
        ('apmv_vrf', dict()),
        ('apmv', dict(outputs_freq=['hourly', 'timestep'], other_pmv_related_outputs=False,
                      adap_coeff_cooling={'*first*': 0.3}, pmv_cooling_sp=0.4, cooling_season_start='01/06',
                      cooling_season_end='15/09', verbose_mode=False)),
    ]),
    's09_add_vrf_mm_262_instances': dict(model='vrf2zones262inst', calls=[
        ('add', dict(_ADD, script_type='vrf_mm')),
        ('modify', dict(comf_stand=1, cat=3, comf_mod=3, hvac_mode=2, vent_ctrl=0)),
    ]),
}

NAMES = list(BATCH) + list(SINGLE)

# The names of the arguments in accim 0.x (accim.sim.arguments.LEGACY_ARGUMENT_NAMES, reversed)
LEGACY_NAMES = {
    'script_type': 'ScriptType', 'supply_air_temp_input_method': 'SupplyAirTempInputMethod',
    'output_type': 'Output_type', 'output_freqs': 'Output_freqs', 'output_keep_existing': 'Output_keep_existing',
    'output_gen_dataframe': 'Output_gen_dataframe', 'output_take_dataframe': 'Output_take_dataframe',
    'energyplus_version': 'EnergyPlus_version', 'temp_ctrl': 'TempCtrl', 'vrf_schedule': 'VRFschedule',
    'comf_stand': 'ComfStand', 'cat': 'CAT', 'cat_cool_offset': 'CATcoolOffset', 'cat_heat_offset': 'CATheatOffset',
    'comf_mod': 'ComfMod', 'setpoint_acc': 'SetpointAcc', 'cust_ast_acst_aul': 'CustAST_ACSTaul',
    'cust_ast_acst_all': 'CustAST_ACSTall', 'cust_ast_ahst_aul': 'CustAST_AHSTaul',
    'cust_ast_ahst_all': 'CustAST_AHSTall', 'cust_ast_m': 'CustAST_m', 'cust_ast_n': 'CustAST_n',
    'cust_ast_acst_offset': 'CustAST_ACSToffset', 'cust_ast_ahst_offset': 'CustAST_AHSToffset',
    'cool_season_start': 'CoolSeasonStart', 'cool_season_end': 'CoolSeasonEnd', 'hvac_mode': 'HVACmode',
    'vent_ctrl': 'VentCtrl', 'max_temp_diff_vof': 'MaxTempDiffVOF', 'min_temp_diff_vof': 'MinTempDiffVOF',
    'multiplier_vof': 'MultiplierVOF', 'vst_offset': 'VSToffset', 'min_ot_offset': 'MinOToffset',
    'max_wind_speed': 'MaxWindSpeed', 'ast_tol_start': 'ASTtol_start', 'ast_tol_end_input': 'ASTtol_end_input',
    'ast_tol_steps': 'ASTtol_steps', 'ast_tol': 'ASTtol', 'name_suffix': 'NameSuffix', 'verbose_mode': 'verboseMode',
    'confirm_gen': 'confirmGen',
}
# apply_apmv_setpoints of accim 0.x already used the other names of its arguments (verbose_mode, for instance)
LEGACY_APMV_NAMES = {'other_pmv_related_outputs': 'other_PMV_related_outputs'}


def models(name):
    """The input models of a configuration."""
    return BATCH[name]['models'] if name in BATCH else [SINGLE[name]['model']]


def energyplus_versions(name):
    """The EnergyPlus versions whose IDD a configuration needs."""
    return sorted({INPUT_MODELS[model][1] for model in models(name)})
