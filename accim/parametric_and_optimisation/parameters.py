from accim.parametric_and_optimisation.funcs_for_besos import param_accis, param_apmv
import accim.parametric_and_optimisation.params_dicts as params_dicts
from accim.parametric_and_optimisation.utils import descriptor_has_options

def accis_parameter(parameter_name, values):
    desc_has_options = descriptor_has_options(values)

    # all_params = {
    #     # accim predefined models parameters
    #     'ComfStand': param_accis.modify_ComfStand,
    #     'CAT': param_accis.modify_CAT,
    #     'CATcoolOffset': param_accis.modify_CATcoolOffset,
    #     'CATheatOffset': param_accis.modify_CATheatOffset,
    #     'ComfMod': param_accis.modify_ComfMod,
    #     'SetpointAcc': param_accis.modify_SetpointAcc,
    #     'CoolSeasonStart': param_accis.modify_CoolSeasonStart,
    #     'CoolSeasonEnd': param_accis.modify_CoolSeasonEnd,
    #     'HVACmode': param_accis.modify_HVACmode,
    #     'VentCtrl': param_accis.modify_VentCtrl,
    #     'MaxTempDiffVOF': param_accis.modify_MaxTempDiffVOF,
    #     'MinTempDiffVOF': param_accis.modify_MinTempDiffVOF,
    #     'MultiplierVOF': param_accis.modify_MultiplierVOF,
    #     'VSToffset': param_accis.modify_VSToffset,
    #     'MinOToffset': param_accis.modify_MinOToffset,
    #     'MaxWindSpeed': param_accis.modify_MaxWindSpeed,
    #     'ASTtol': param_accis.modify_ASTtol,
    #     # accim custom models parameters
    #     'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul,
    #     'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall,
    #     'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul,
    #     'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall,
    #     'CustAST_ASTaul': param_accis.modify_CustAST_ASTaul,
    #     'CustAST_ASTall': param_accis.modify_CustAST_ASTall,
    #     'CustAST_m': param_accis.modify_CustAST_m,
    #     'CustAST_n': param_accis.modify_CustAST_n,
    #     'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset,
    #     'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset,
    #     'CustAST_ASToffset': param_accis.modify_CustAST_ASToffset,
    #     #apmv setpoints parameters
    #     'Adaptive coefficient': param_apmv.change_adaptive_coeff_all_zones,
    #     'Adaptive cooling coefficient': param_apmv.change_adaptive_coeff_cooling_all_zones,
    #     'Adaptive heating coefficient': param_apmv.change_adaptive_coeff_heating_all_zones,
    #     'PMV setpoint': param_apmv.change_pmv_setpoint_all_zones,
    #     'PMV cooling setpoint': param_apmv.change_pmv_cooling_setpoint_all_zones,
    #     'PMV heating setpoint': param_apmv.change_pmv_heating_setpoint_all_zones,
    # }


    if parameter_name.lower() not in [k.lower() for k in params_dicts.all_params.keys()]:
        raise KeyError(f'Parameter do not exist.'
                       f'You need to chose one of the following list: {params_dicts.all_params.keys()}')

    name = [i for i in params_dicts.all_params.keys() if i.lower() == parameter_name.lower()][0]

    from besos.parameters import Parameter, GenericSelector, CategoryParameter, RangeParameter
    import accim.parametric_and_optimisation.funcs_for_besos.param_accis as bf
    import numpy as np

    if desc_has_options:
        parameter = Parameter(
            name=name,
            # selector=GenericSelector(set=change_adaptive_coeff),
            selector=GenericSelector(set=params_dicts.all_params[name]),
            # value_descriptors=RangeParameter(name='CustAST_m', min_val=0, max_val=0.7),
            value_descriptors=CategoryParameter(
                name=name,
                options=values
            ),
        ),
    else:
        parameter = Parameter(
            name=name,
            # selector=GenericSelector(set=change_adaptive_coeff),
            selector=GenericSelector(set=params_dicts.all_params[name]),
            # value_descriptors=RangeParameter(name='CustAST_m', min_val=0, max_val=0.7),
            value_descriptors=RangeParameter(
                name=name,
                min_val=values[0],
                max_val=values[1],
            ),
        ),

    return parameter[0]

def get_available_params_accim_predef_models():
    param_dict = [k for k in params_dicts.accim_predef_model_params.keys()]
    return param_dict
def get_available_params_accim_custom_models():
    param_dict = [k for k in params_dicts.accim_custom_model_params.keys()]
    return param_dict
def get_available_params_apmv_setpoints():
    param_dict = [k for k in params_dicts.apmv_setpoints_params.keys()]
    return param_dict

class Parameter:
    def __init__(self, parameter):
        parameters_accis = {
            'ComfStand': param_accis.modify_ComfStand,
            'CAT': param_accis.modify_CAT,
            'CATcoolOffset': param_accis.modify_CATcoolOffset,
            'CATheatOffset': param_accis.modify_CATheatOffset,
            'ComfMod': param_accis.modify_ComfMod,
            'SetpointAcc': param_accis.modify_SetpointAcc,
            'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul,
            'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall,
            'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul,
            'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall,
            'CustAST_m': param_accis.modify_CustAST_m,
            'CustAST_n': param_accis.modify_CustAST_n,
            'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset,
            'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset,
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

        if parameter.lower() not in [k.lower() for k in parameters_accis.keys()]:
            raise KeyError(f'Parameter do not exist.'
                           f'You need to chose one of the following list: {parameters_accis.keys()}')

        self.name = [i for i in parameters_accis.keys() if i.lower() == parameter.lower()][0]

    def modify(self, idf, value):
        parameters_accis = {
            'ComfStand': param_accis.modify_ComfStand(idf, value),
            'CAT': param_accis.modify_CAT(idf, value),
            'CATcoolOffset': param_accis.modify_CATcoolOffset(idf, value),
            'CATheatOffset': param_accis.modify_CATheatOffset(idf, value),
            'ComfMod': param_accis.modify_ComfMod(idf, value),
            'SetpointAcc': param_accis.modify_SetpointAcc(idf, value),
            'CustAST_ACSTaul': param_accis.modify_CustAST_ACSTaul(idf, value),
            'CustAST_ACSTall': param_accis.modify_CustAST_ACSTall(idf, value),
            'CustAST_AHSTaul': param_accis.modify_CustAST_AHSTaul(idf, value),
            'CustAST_AHSTall': param_accis.modify_CustAST_AHSTall(idf, value),
            'CustAST_m': param_accis.modify_CustAST_m(idf, value),
            'CustAST_n': param_accis.modify_CustAST_n(idf, value),
            'CustAST_ACSToffset': param_accis.modify_CustAST_ACSToffset(idf, value),
            'CustAST_AHSToffset': param_accis.modify_CustAST_AHSToffset(idf, value),
            'CoolSeasonStart': param_accis.modify_CoolSeasonStart(idf, value),
            'CoolSeasonEnd': param_accis.modify_CoolSeasonEnd(idf, value),
            'HVACmode': param_accis.modify_HVACmode(idf, value),
            'VentCtrl': param_accis.modify_VentCtrl(idf, value),
            'MaxTempDiffVOF': param_accis.modify_MaxTempDiffVOF(idf, value),
            'MinTempDiffVOF': param_accis.modify_MinTempDiffVOF(idf, value),
            'MultiplierVOF': param_accis.modify_MultiplierVOF(idf, value),
            'VSToffset': param_accis.modify_VSToffset(idf, value),
            'MinOToffset': param_accis.modify_MinOToffset(idf, value),
            'MaxWindSpeed': param_accis.modify_MaxWindSpeed(idf, value),
            'ASTtol': param_accis.modify_ASTtol(idf, value),
        }

        parameters_accis[self.name]


class ComfStand:
    def __init__(self):
        self.name = 'ComfStand'

    def modify(self, idf, value):
        param_accis.modify_ComfStand(idf, value)

class CustAST_ACSTaul:
    def __init__(self):
        self.name = 'CustAST_ACSTaul'

    def modify(self, idf, value):
        param_accis.modify_CustAST_ACSTaul(idf, value)

class CustAST_ACSTall:
    def __init__(self):
        self.name = 'CustAST_ACSTall'

    def modify(self, idf, value):
        param_accis.modify_CustAST_ACSTall(idf, value)

class CustAST_AHSTaul:
    def __init__(self):
        self.name = 'CustAST_AHSTaul'

    def modify(self, idf, value):
        param_accis.modify_CustAST_AHSTaul(idf, value)

class CustAST_AHSTall:
    def __init__(self):
        self.name = 'CustAST_AHSTall'

    def modify(self, idf, value):
        param_accis.modify_CustAST_AHSTall(idf, value)

class CustAST_ASTaul:
    def __init__(self):
        self.name = 'CustAST_ASTaul'

    def modify(self, idf, value):
        param_accis.modify_CustAST_ASTaul(idf, value)

class CustAST_ASTall:
    def __init__(self):
        self.name = 'CustAST_ASTall'

    def modify(self, idf, value):
        param_accis.modify_CustAST_ASTall(idf, value)

class CustAST_m:
    def __init__(self):
        self.name = 'CustAST_m'

    def modify(self, idf, value):
        param_accis.modify_CustAST_m(idf, value)

class CustAST_n:
    def __init__(self):
        self.name = 'CustAST_n'

    def modify(self, idf, value):
        param_accis.modify_CustAST_n(idf, value)

class CustAST_ACSToffset:
    def __init__(self):
        self.name = 'CustAST_ACSToffset'

    def modify(self, idf, value):
        param_accis.modify_CustAST_ACSToffset(idf, value)

class CustAST_AHSToffset:
    def __init__(self):
        self.name = 'CustAST_AHSToffset'

    def modify(self, idf, value):
        param_accis.modify_CustAST_AHSToffset(idf, value)

class CustAST_ASToffset:
    def __init__(self):
        self.name = 'CustAST_ASToffset'

    def modify(self, idf, value):
        param_accis.modify_CustAST_ASToffset(idf, value)

class CAT:
    def __init__(self):
        self.name = 'CAT'

    def modify(self, idf, value):
        param_accis.modify_CAT(idf, value)

class CATcoolOffset:
    def __init__(self):
        self.name = 'CATcoolOffset'

    def modify(self, idf, value):
        param_accis.modify_CATcoolOffset(idf, value)

class CATheatOffset:
    def __init__(self):
        self.name = 'CATheatOffset'

    def modify(self, idf, value):
        param_accis.modify_CATheatOffset(idf, value)

class ComfMod:
    def __init__(self):
        self.name = 'ComfMod'

    def modify(self, idf, value):
        param_accis.modify_ComfMod(idf, value)

class HVACmode:
    def __init__(self):
        self.name = 'HVACmode'

    def modify(self, idf, value):
        param_accis.modify_HVACmode(idf, value)

class VentCtrl:
    def __init__(self):
        self.name = 'VentCtrl'

    def modify(self, idf, value):
        param_accis.modify_VentCtrl(idf, value)

class VSToffset:
    def __init__(self):
        self.name = 'VSToffset'

    def modify(self, idf, value):
        param_accis.modify_VSToffset(idf, value)

class MinOToffset:
    def __init__(self):
        self.name = 'MinOToffset'

    def modify(self, idf, value):
        param_accis.modify_MinOToffset(idf, value)

class MaxWindSpeed:
    def __init__(self):
        self.name = 'MaxWindSpeed'

    def modify(self, idf, value):
        param_accis.modify_MaxWindSpeed(idf, value)

class ASTtol:
    def __init__(self):
        self.name = 'ASTtol'

    def modify(self, idf, value):
        param_accis.modify_ASTtol(idf, value)

class CoolSeasonStart:
    def __init__(self):
        self.name = 'CoolSeasonStart'

    def modify(self, idf, value):
        param_accis.modify_CoolSeasonStart(idf, value)

class CoolSeasonEnd:
    def __init__(self):
        self.name = 'CoolSeasonEnd'

    def modify(self, idf, value):
        param_accis.modify_CoolSeasonEnd(idf, value)

class SetpointAcc:
    def __init__(self):
        self.name = 'SetpointAcc'

    def modify(self, idf, value):
        param_accis.modify_SetpointAcc(idf, value)

class MaxTempDiffVOF:
    def __init__(self):
        self.name = 'MaxTempDiffVOF'

    def modify(self, idf, value):
        param_accis.modify_MaxTempDiffVOF(idf, value)

class MinTempDiffVOF:
    def __init__(self):
        self.name = 'MinTempDiffVOF'

    def modify(self, idf, value):
        param_accis.modify_MinTempDiffVOF(idf, value)

class MultiplierVOF:
    def __init__(self):
        self.name = 'MultiplierVOF'

    def modify(self, idf, value):
        param_accis.modify_MultiplierVOF(idf, value)

