from accim.parametric_and_optimisation.funcs_for_besos import param_accis, param_apmv

accim_predef_model_params = {
    # accim predefined models parameters
    'ComfStand': param_accis.modify_ComfStand,
    'CAT': param_accis.modify_CAT,
    'CATcoolOffset': param_accis.modify_CATcoolOffset,
    'CATheatOffset': param_accis.modify_CATheatOffset,
    'ComfMod': param_accis.modify_ComfMod,
    'SetpointAcc': param_accis.modify_SetpointAcc,
    'CoolSeasonStart': param_accis.modify_CoolSeasonStart,
    'CoolSeasonEnd': param_accis.modify_CoolSeasonEnd,
    'HVACmode': param_accis.modify_HVACmode,
    'VentCtrl': param_accis.modify_VentCtrl,
    'MaxTempDiffVOF': param_accis.modify_MaxTempDiffVOF,
    'MinTempDiffVOF': param_accis.modify_MinTempDiffVOF,
    'MultiplierVOF': param_accis.modify_MultiplierVOF,
    'VSToffset': param_accis.modify_VSToffset,
    'MinOToffset': param_accis.modify_MinOToffset,
    'MaxWindSpeed': param_accis.modify_MaxWindSpeed,
    'ASTtol': param_accis.modify_ASTtol,
}
accim_custom_model_params = {
    # accim custom models parameters
    'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul,
    'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall,
    'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul,
    'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall,
    'CustAST_ASTaul': param_accis.modify_CustAST_ASTaul,
    'CustAST_ASTall': param_accis.modify_CustAST_ASTall,
    'CustAST_m': param_accis.modify_CustAST_m,
    'CustAST_n': param_accis.modify_CustAST_n,
    'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset,
    'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset,
    'CustAST_ASToffset': param_accis.modify_CustAST_ASToffset,
}
apmv_setpoints_params = {
    # apmv setpoints parameters
    'Adaptive coefficient': param_apmv.change_adaptive_coeff_all_zones,
    'Adaptive cooling coefficient': param_apmv.change_adaptive_coeff_cooling_all_zones,
    'Adaptive heating coefficient': param_apmv.change_adaptive_coeff_heating_all_zones,
    'PMV setpoint': param_apmv.change_pmv_setpoint_all_zones,
    'PMV cooling setpoint': param_apmv.change_pmv_cooling_setpoint_all_zones,
    'PMV heating setpoint': param_apmv.change_pmv_heating_setpoint_all_zones,
}

all_params = {}
all_params.update(accim_predef_model_params)
all_params.update(accim_custom_model_params)
all_params.update(apmv_setpoints_params)