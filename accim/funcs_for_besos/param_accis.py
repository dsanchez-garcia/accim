
def modify_VSToffset(building, value):
    import accim.sim.accis_single_idf_funcs as accis
    accis.modifyAccis(
        idf=building,
        ComfStand=1,
        CAT=3,
        ComfMod=3,
        # SetpointAcc=1000,
        HVACmode=2,
        VentCtrl=0,
        CoolSeasonStart='01/02',
        CoolSeasonEnd='01/03',
        VSToffset=value,
        # MinOToffset=50,
        # MaxWindSpeed=50
    )
    return


def get_valid_param_combinations():

    # CS_CA_CM_list_dict = {
    #     0:{
    #         'name': '0 = ESP CTE',
    #         'CAT': ['n/a'],
    #         'ComfMod': ['n/a'],
    #     },
    #     0: {
    #         'name': ,
    #         'CAT': ,
    #         'ComfMod': ,
    #     },
    #
    # }
    #     '0 = ESP CTE': [, ],
    #     '1 = INT EN16798-1': [[1, 2, 3], [0, 1, 2, 3]],
    #     '2 = INT ASHRAE55': [[80, 90], [0, 1, 2, 3]],
    #     '3 = JPN Rijal': [[80, 90], [0, 1, 2, 3]],
    #     '4 = CHN GBT50785 Cold': [[1, 2], [3]],
    #     '5 = CHN GBT50785 HotMild': [[1, 2], [3]],
    #     '6 = CHN Yang': [[80, 90], [0, 1, 2, 3]],
    #     '7 = IND IMAC C NV': [[80, 85, 90], [0, 1, 2, 3]],
    #     '8 = IND IMAC C MM': [[80, 85, 90], [0, 1, 2, 3]],
    #     '9 = IND IMAC R 7DRM': [[80, 90], [0, 1, 2, 3]],
    #     '10 = IND IMAC R 30DRM': [[80, 90], [0, 1, 2, 3]],
    #     '11 = IND Dhaka': [[80, 90], [0, 1, 2, 3]],
    #     '12 = ROM Udrea': [[80, 90], [0, 1, 2, 3]],
    #     '13 = AUS Williamson': [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
    #     '14 = AUS DeDear': [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
    #     '15 = BRA Rupp NV': [[80, 90], [0, 1, 2, 3]],
    #     '16 = BRA Rupp AC': [[80, 90], [0, 1, 2, 3]],
    #     '17 = MEX Oropeza Arid': [[80, 90], [0, 1, 2, 3]],
    #     '18 = MEX Oropeza DryTropic': [[80, 90], [0, 1, 2, 3]],
    #     '19 = MEX Oropeza Temperate': [[80, 90], [0, 1, 2, 3]],
    #     '20 = MEX Oropeza HumTropic': [[80, 90], [0, 1, 2, 3]],
    #     '21 = CHL Perez-Fargallo': [[80, 90], [2, 3]],
    #     '22 = INT ISO7730': [[1, 2, 3], [0]],
    # }

    CS_CA_CM_list_dict = {
        0: [['n/a'], ['n/a']],
        1: [[1, 2, 3], [0, 1, 2, 3]],
        2: [[80, 90], [0, 1, 2, 3]],
        3: [[80, 90], [0, 1, 2, 3]],
        4: [[1, 2], [3]],
        5: [[1, 2], [3]],
        6: [[80, 90], [0, 1, 2, 3]],
        7: [[80, 85, 90], [0, 1, 2, 3]],
        8: [[80, 85, 90], [0, 1, 2, 3]],
        9: [[80, 90], [0, 1, 2, 3]],
        10: [[80, 90], [0, 1, 2, 3]],
        11: [[80, 90], [0, 1, 2, 3]],
        12: [[80, 90], [0, 1, 2, 3]],
        13: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        14: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        15: [[80, 90], [0, 1, 2, 3]],
        16: [[80, 90], [0, 1, 2, 3]],
        17: [[80, 90], [0, 1, 2, 3]],
        18: [[80, 90], [0, 1, 2, 3]],
        19: [[80, 90], [0, 1, 2, 3]],
        20: [[80, 90], [0, 1, 2, 3]],
        21: [[80, 90], [2, 3]],
        22: [[1, 2, 3], [0]],
    }

    return CS_CA_CM_list_dict

def drop_invalid_param_combinations(samples_df):
    samples_df = samples_df.dropna()

    valid_params = {
        0: [['n/a'], ['n/a']],
        1: [[1, 2, 3], [0, 1, 2, 3]],
        2: [[80, 90], [0, 1, 2, 3]],
        3: [[80, 90], [0, 1, 2, 3]],
        4: [[1, 2], [3]],
        5: [[1, 2], [3]],
        6: [[80, 90], [0, 1, 2, 3]],
        7: [[80, 85, 90], [0, 1, 2, 3]],
        8: [[80, 85, 90], [0, 1, 2, 3]],
        9: [[80, 90], [0, 1, 2, 3]],
        10: [[80, 90], [0, 1, 2, 3]],
        11: [[80, 90], [0, 1, 2, 3]],
        12: [[80, 90], [0, 1, 2, 3]],
        13: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        14: [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        15: [[80, 90], [0, 1, 2, 3]],
        16: [[80, 90], [0, 1, 2, 3]],
        17: [[80, 90], [0, 1, 2, 3]],
        18: [[80, 90], [0, 1, 2, 3]],
        19: [[80, 90], [0, 1, 2, 3]],
        20: [[80, 90], [0, 1, 2, 3]],
        21: [[80, 90], [2, 3]],
        22: [[1, 2, 3], [0]],
    }

    samples_df['valid'] = True
    for i in samples_df.index:
        try:
            if samples_df.loc[i, 'CAT'] not in valid_params[samples_df.loc[i, 'ComfStand']][0]:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'ComfMod'] not in valid_params[samples_df.loc[i, 'ComfStand']][1]:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'VentCtrl'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'VSToffset'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'MinOToffset'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'MaxWindSpeed'] != 0 and samples_df.loc[i, 'HVACmode'] == 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'SetpointAcc'] < 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue
        try:
            if samples_df.loc[i, 'MaxTempDiffVOF'] <= 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'MinTempDiffVOF'] <= 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue
        try:
            if samples_df.loc[i, 'MinTempDiffVOF'] >= samples_df.loc[i, 'MaxTempDiffVOF'] <= 0:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue

        try:
            if samples_df.loc[i, 'MultiplierVOF'] < 0 or samples_df.loc[i, 'MultiplierVOF'] > 1:
                samples_df.loc[i, 'valid'] = False
        except KeyError:
            continue


    samples_cleaned = samples_df[samples_df['valid'] == True].drop(columns=['valid'])

    return samples_cleaned


def modify_ComfStand(idf, value: int):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_1 = f'set ComfStand = {value}'

    return

def modify_CustAST_ACSTaul(idf, value):
    SetAppLimits = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                          program.Name == 'SetAppLimits'][0])
    SetAppLimits.Program_Line_2 = f'set ACSTaul = {repr(value)}'

    return

def modify_CustAST_ACSTall(idf, value):
    SetAppLimits = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                          program.Name == 'SetAppLimits'][0])
    SetAppLimits.Program_Line_3 = f'set ACSTall = {value}'

    return

def modify_CustAST_AHSTaul(idf, value):
    SetAppLimits = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                          program.Name == 'SetAppLimits'][0])
    SetAppLimits.Program_Line_4 = f'set AHSTaul = {value}'

    return

def modify_CustAST_AHSTall(idf, value):
    SetAppLimits = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                          program.Name == 'SetAppLimits'][0])
    SetAppLimits.Program_Line_5 = f'set AHSTall = {value}'

    return

def modify_CustAST_m(idf, value):
    SetAST = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
               program.Name == 'SetAST'][0])
    SetAST.Program_Line_2 = f'set m = {value}'

    return


def modify_CustAST_n(idf, value):
    SetAST = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
               program.Name == 'SetAST'][0])
    SetAST.Program_Line_3 = f'set n = {value}'

    return

def modify_CustAST_ACSToffset(idf, value):
    ApplyCAT = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                 program.Name == 'ApplyCAT'][0])
    ApplyCAT.Program_Line_4 = f'set ACSToffset = {repr(value)}'

    return


def modify_CustAST_AHSToffset(idf, value):
    ApplyCAT = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                 program.Name == 'ApplyCAT'][0])
    ApplyCAT.Program_Line_5 = f'set AHSToffset = {repr(value)}'

    return


def modify_CAT(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_2 = f'set CAT = {value}'

    return

def modify_CATcoolOffset(idf, value):
    ApplyCAT = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                 program.Name == 'ApplyCAT'][0])
    ApplyCAT.Program_Line_1 = f'set CATcoolOffset = {value}'

    return

def modify_CATheatOffset(idf, value):
    ApplyCAT = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                 program.Name == 'ApplyCAT'][0])
    ApplyCAT.Program_Line_2 = f'set CATheatOffset = {value}'

    return

def modify_ComfMod(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_3 = f'set ComfMod = {value}'

    return

def modify_HVACmode(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_4 = f'set HVACmode = {value}'
    return

def modify_VentCtrl(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_5 = f'set VentCtrl = {value}'
    return

def modify_VSToffset(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_6 = f'set VSToffset = {value}'
    return

def modify_MinOToffset(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_7 = f'set MinOToffset = {value}'
    return

def modify_MaxWindSpeed(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_8 = f'set MaxWindSpeed = {value}'
    return

def modify_ASTtol(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    SetInputData.Program_Line_9 = f'set ACSTtol = {value}'
    SetInputData.Program_Line_10 = f'set AHSTtol = {value}'
    return

def modify_CoolSeasonStart(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    if type(value) is str:
        from accim.utils import transform_ddmm_to_int
        value = transform_ddmm_to_int(value)

    SetInputData.Program_Line_11 = f'set CoolSeasonStart = {value}'
    return

def modify_CoolSeasonEnd(idf, value):
    SetInputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                     program.Name == 'SetInputData'][0])
    if type(value) is str:
        from accim.utils import transform_ddmm_to_int
        value = transform_ddmm_to_int(value)

    SetInputData.Program_Line_12 = f'set CoolSeasonEnd = {value}'
    return

def modify_SetpointAcc(idf, value):
    SetAST = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
               program.Name == 'SetAST'][0])
    SetAST.Program_Line_1 = f'set SetpointAcc = {value}'
    return

def modify_MaxTempDiffVOF(idf, value):
    SetVOFinputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                        program.Name == 'SetVOFinputData'][0])
    SetVOFinputData.Program_Line_1 = f'set MaxTempDiffVOF = {value}'
    return

def modify_MinTempDiffVOF(idf, value):
    SetVOFinputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                        program.Name == 'SetVOFinputData'][0])
    SetVOFinputData.Program_Line_2 = f'set MinTempDiffVOF = {value}'
    return

def modify_MultiplierVOF(idf, value):
    SetVOFinputData = ([program for program in idf.idfobjects['EnergyManagementSystem:Program'] if
                        program.Name == 'SetVOFinputData'][0])
    SetVOFinputData.Program_Line_3 = f'set MultiplierVOF = {value}'
    return
