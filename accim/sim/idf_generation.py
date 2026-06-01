# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Generate IDFs."""
from accim.sim.ems.setast_models import get_SetAST_lines


def generate_idfs(self,
    script_type: str = None,
    temp_control: str = None,
    comfort_standard: list = None,
    category: list = None,
    category_cool_offset: float = 0,
    category_heat_offset: float = 0,
    comfort_mode: list = None,
    setpoint_accuracy: float = 10000,
    custom_ast_acst_aul: float = 0,
    custom_ast_acst_all: float = 0,
    custom_ast_ahst_aul: float = 0,
    custom_ast_ahst_all: float = 0,
    custom_ast_m: float = 0,
    custom_ast_n: float = 0,
    custom_ast_acst_offset: float = 0,
    custom_ast_ahst_offset: float = 0,
    cooling_season_start=121,
    cooling_season_end=274,
    hvac_mode: list = None,
    vent_control: list = None,
    vof_max_temp_diff: float = 6,
    vof_min_temp_diff: float = 1,
    vof_multiplier: float = 0.25,
    vent_setpoint_offset: list = [0],
    min_outdoor_temp_offset: list = [50],
    max_wind_speed: list = [50],
    ast_tol_start: float = 0.1,
    ast_tol_end: float = 0.1,
    ast_tol_steps: float = 0.1,
    name_suffix: str = '',
    verbose: bool = True,
    confirm_generation: bool = None,
    filelist_pymod: list = None
):
    """Generate IDFs.

    :param self: Used as a method for class ``accim.sim.engine.AccimJob``
    :param script_type: Inherited from class ``accim.sim.AddAccis``
    :param temp_control: Inherited from class ``accim.sim.AddAccis``
    :param comfort_standard: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_m: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_n: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_acst_offset: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_ahst_offset: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_acst_all: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_acst_aul: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_ahst_all: Inherited from class ``accim.sim.AddAccis``
    :param custom_ast_ahst_aul: Inherited from class ``accim.sim.AddAccis``
    :param category: Inherited from class ``accim.sim.AddAccis``
    :param category_cool_offset: Inherited from class ``accim.sim.AddAccis``
    :param category_heat_offset: Inherited from class ``accim.sim.AddAccis``
    :param comfort_mode: Inherited from :class:``accim.sim.AddAccis``
    :param setpoint_accuracy: Inherited from :class:``accim.sim.AddAccis``
    :param cooling_season_start: Inherited from :class:``accim.sim.AddAccis``
    :param cooling_season_end: Inherited from :class:``accim.sim.AddAccis``
    :param hvac_mode: Inherited from :class:``accim.sim.AddAccis``
    :param vent_control: Inherited from :class:``accim.sim.AddAccis``
    :param vof_max_temp_diff: Inherited from :class:``accim.sim.AddAccis``
    :param vof_min_temp_diff: Inherited from :class:``accim.sim.AddAccis``
    :param vof_multiplier: Inherited from :class:``accim.sim.AddAccis``
    :param vent_setpoint_offset: Inherited from :class:``accim.sim.AddAccis``
    :param min_outdoor_temp_offset: Inherited from :class:``accim.sim.AddAccis``
    :param max_wind_speed: Inherited from :class:``accim.sim.AddAccis``
    :param ast_tol_start: Inherited from :class:``accim.sim.AddAccis``
    :param ast_tol_end: Inherited from :class:``accim.sim.AddAccis``
    :param ast_tol_steps: Inherited from :class:``accim.sim.AddAccis``
    :param name_suffix: Inherited from :class:``accim.sim.AddAccis``
    :param verbose: Inherited from :class:``accim.sim.AddAccis``
    :param confirm_generation: Inherited from :class:``accim.sim.AddAccis``
    """
    import os
    from os import listdir
    import numpy
    from eppy import modeleditor
    from eppy.modeleditor import IDF
    from besos.eppy_funcs import get_building
    # import time
    # from tqdm import tqdm

    arguments = (comfort_standard is None,
                 category is None,
                 category_cool_offset == 0,
                 category_heat_offset == 0,
                 comfort_mode is None,
                 setpoint_accuracy == 10000,
                 custom_ast_acst_aul == 0,
                 custom_ast_acst_all == 0,
                 custom_ast_ahst_aul == 0,
                 custom_ast_ahst_all == 0,
                 custom_ast_m == 0,
                 custom_ast_n == 0,
                 custom_ast_acst_offset == 0,
                 custom_ast_ahst_offset == 0,
                 cooling_season_start == 121,
                 cooling_season_end == 274,
                 hvac_mode is None,
                 vent_control is None,
                 vof_max_temp_diff == 6,
                 vof_min_temp_diff == 1,
                 vof_multiplier == 0.25,
                 vent_setpoint_offset == [0],
                 min_outdoor_temp_offset == [50],
                 max_wind_speed == [50],
                 ast_tol_start == 0.1,
                 ast_tol_end == 0.1,
                 ast_tol_steps == 0.1)
    if all(arguments):
        self.ASTtol_value_to = self.ASTtol_value_to_input + self.ASTtol_value_steps
    else:
        ASTtol_end = ast_tol_end + ast_tol_steps

    if all(arguments):
        self.ASTtol_value_from = round(self.ASTtol_value_from, 2)
        self.ASTtol_value_to = round(self.ASTtol_value_to, 2)
        self.ASTtol_value_steps = round(self.ASTtol_value_steps, 2)
    else:
        self.ComfStand_List = comfort_standard
        self.CAT_List = category
        self.ComfMod_List = comfort_mode
        self.setpoint_accuracy = setpoint_accuracy
        self.category_cool_offset = category_cool_offset
        self.category_heat_offset = category_heat_offset
        self.custom_ast_acst_aul = custom_ast_acst_aul
        self.custom_ast_acst_all = custom_ast_acst_all
        self.custom_ast_ahst_aul = custom_ast_ahst_aul
        self.custom_ast_ahst_all = custom_ast_ahst_all
        self.custom_ast_m = custom_ast_m
        self.custom_ast_n = custom_ast_n
        self.custom_ast_acst_offset = custom_ast_acst_offset
        self.custom_ast_ahst_offset = custom_ast_ahst_offset

        
        if type(cooling_season_start) is str:
            cooling_season_start = list(int(num) for num in cooling_season_start.split('/'))
            from datetime import date
            day_of_year = date(2007, cooling_season_start[1], cooling_season_start[0]).timetuple().tm_yday
        elif type(cooling_season_start) is int:
            day_of_year = cooling_season_start
        self.cooling_season_start = day_of_year
        
        # CoolSeasonEnd = list(int(num) for num in CoolSeasonEnd.split('/'))
        # if len(CoolSeasonEnd) == 1:
        #     day_of_year = CoolSeasonEnd[0]
        # elif len(CoolSeasonEnd) == 2:
        #     from datetime import date
        #     day_of_year = date(2007, CoolSeasonEnd[1], CoolSeasonEnd[0]).timetuple().tm_yday
        # self.CoolSeasonEnd = day_of_year
        if type(cooling_season_end) is str:
            cooling_season_end = list(int(num) for num in cooling_season_end.split('/'))
            from datetime import date
            day_of_year = date(2007, cooling_season_end[1], cooling_season_end[0]).timetuple().tm_yday
        elif type(cooling_season_end) is int:
            day_of_year = cooling_season_end
        self.cooling_season_end = day_of_year

        
        self.HVACmode_List = hvac_mode
        self.VentCtrl_List = vent_control
        self.vof_max_temp_diff = vof_max_temp_diff,
        self.vof_min_temp_diff = vof_min_temp_diff,
        self.vof_multiplier = vof_multiplier,
        self.VSToffset_List = vent_setpoint_offset
        self.MinOToffset_List = min_outdoor_temp_offset
        self.MaxWindSpeed_List = max_wind_speed
        self.ASTtol_value_from = round(ast_tol_start, 2)
        self.ASTtol_value_to = round(ASTtol_end, 2)
        self.ASTtol_value_steps = round(ast_tol_steps, 2)

    if 'ac' in script_type.lower():
        self.HVACmode_List = [0]
        self.VentCtrl_List = [0]
        self.vof_max_temp_diff = 1,
        self.vof_min_temp_diff = 0,
        self.vof_multiplier = 0,
        self.VSToffset_List = [0]
        self.MinOToffset_List = [0]
        self.MaxWindSpeed_List = [0]

    if any([i in self.VentCtrl_List for i in [2, 3]]):
        if type(self.vof_max_temp_diff) is tuple:
            self.vof_max_temp_diff = self.vof_max_temp_diff[0]
        if type(self.vof_min_temp_diff) is tuple:
            self.vof_min_temp_diff = self.vof_min_temp_diff[0]
        if type(self.vof_multiplier) is tuple:
            self.vof_multiplier = self.vof_multiplier[0]

    self.VSToffset_List = [float(i) for i in self.VSToffset_List]
    self.MinOToffset_List = [float(i) for i in self.MinOToffset_List]
    self.MaxWindSpeed_List = [float(i) for i in self.MaxWindSpeed_List]

    if name_suffix == '':
        suffix = '[NS_X'
    else:
        suffix = '[NS_' + name_suffix

    if filelist_pymod is None:
        filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
        filelist_pymod = ([file.split('.idf')[0] for file in filelist_pymod])
    else:
        filelist_pymod = ([file.split('.idf')[0] for file in filelist_pymod if file.endswith('_pymod.idf')])
    # print(filelist_pymod)

    # Characters not admitted: & ^ , = % " / \ : * ? " < > |
    ComfStand_dict = {
        0: '[CS_ESP CTE',
        1: '[CS_INT EN16798',
        2: '[CS_INT ASHRAE55',
        3: '[CS_JPN Rijal',
        4: '[CS_CHN GBT50785 Cold',
        5: '[CS_CHN GBT50785 HotMild',
        6: '[CS_CHN Yang',
        7: '[CS_IND IMAC C NV',
        8: '[CS_IND IMAC C MM',
        9: '[CS_IND IMAC R 7DRM',
        10: '[CS_IND IMAC R 30DRM',
        11: '[CS_IND Dhaka',
        12: '[CS_ROU Udrea',
        13: '[CS_AUS Williamson',
        14: '[CS_AUS DeDear',
        15: '[CS_BRA Rupp NV',
        16: '[CS_BRA Rupp AC',
        17: '[CS_MEX Oropeza Arid',
        18: '[CS_MEX Oropeza DryTropic',
        19: '[CS_MEX Oropeza Temperate',
        20: '[CS_MEX Oropeza HumTropic',
        21: '[CS_CHL Perez-Fargallo',
        22: '[CS_INT ISO7730',
        99: '[CS_CUSTOM',
    }

    outputlist = []
    for file in filelist_pymod:
        filename = file.replace('_pymod', '')
        if temp_control.lower() == 'temp' or temp_control.lower() == 'temperature':
            for ComfStand_value in self.ComfStand_List:
                if ComfStand_value == 0:
                    for HVACmode_value in self.HVACmode_List:
                        if HVACmode_value == 0:
                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                             self.ASTtol_value_steps):
                                outputname = (
                                        filename
                                        + ComfStand_dict[ComfStand_value]
                                        + '[CA_X'
                                        + '[CM_X'
                                        + '[HM_' + str(HVACmode_value)
                                        + '[VC_X'
                                        + '[VO_X'
                                        + '[MT_X'
                                        + '[MW_X'
                                        + '[AT_' + str(round(ASTtol_value, 2))
                                        + suffix
                                        + '.idf'
                                )
                                outputlist.append(outputname)
                        else:
                            for VentCtrl_value in self.VentCtrl_List:
                                if HVACmode_value == 1 and VentCtrl_value == 2:
                                    continue
                                elif HVACmode_value == 1 and VentCtrl_value == 3:
                                    continue
                                else:
                                    for VSToffset_value in self.VSToffset_List:
                                        for MinOToffset_value in self.MinOToffset_List:
                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    outputname = (
                                                            filename
                                                            + ComfStand_dict[ComfStand_value]
                                                            + '[CA_X'
                                                            + '[CM_X'
                                                            + '[HM_' + str(HVACmode_value)
                                                            + '[VC_' + str(VentCtrl_value)
                                                            + '[VO_' + str(VSToffset_value)
                                                            + '[MT_' + str(MinOToffset_value)
                                                            + '[MW_' + str(MaxWindSpeed_value)
                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                            + suffix
                                                            + '.idf'
                                                    )
                                                    outputlist.append(outputname)
                elif ComfStand_value in [1, 4, 5, 22]:
                    for CAT_value in self.CAT_List:
                        if ComfStand_value in [1, 22] and CAT_value not in range(0, 4):
                            continue
                        elif ComfStand_value in [4, 5] and CAT_value not in [1, 2]:
                            continue
                        else:
                            for ComfMod_value in self.ComfMod_List:
                                if ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                    continue
                                elif ComfStand_value == 22 and ComfMod_value != 0:
                                    continue
                                else:
                                    for HVACmode_value in self.HVACmode_List:
                                        if HVACmode_value == 0:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                                             self.ASTtol_value_steps):
                                                outputname = (
                                                        filename
                                                        + ComfStand_dict[ComfStand_value]
                                                        + '[CA_' + str(CAT_value)
                                                        + '[CM_' + str(ComfMod_value)
                                                        + '[HM_' + str(HVACmode_value)
                                                        + '[VC_X'
                                                        + '[VO_X'
                                                        + '[MT_X'
                                                        + '[MW_X'
                                                        + '[AT_' + str(round(ASTtol_value, 2))
                                                        + suffix
                                                        + '.idf'
                                                )
                                                outputlist.append(outputname)
                                        else:
                                            for VentCtrl_value in self.VentCtrl_List:
                                                if HVACmode_value == 1 and VentCtrl_value == 2:
                                                    continue
                                                elif HVACmode_value == 1 and VentCtrl_value == 3:
                                                    continue
                                                else:
                                                    for VSToffset_value in self.VSToffset_List:
                                                        for MinOToffset_value in self.MinOToffset_List:
                                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                                 self.ASTtol_value_to,
                                                                                                 self.ASTtol_value_steps):
                                                                    outputname = (
                                                                            filename
                                                                            + ComfStand_dict[ComfStand_value]
                                                                            + '[CA_' + str(CAT_value)
                                                                            + '[CM_' + str(ComfMod_value)
                                                                            + '[HM_' + str(HVACmode_value)
                                                                            + '[VC_' + str(VentCtrl_value)
                                                                            + '[VO_' + str(VSToffset_value)
                                                                            + '[MT_' + str(MinOToffset_value)
                                                                            + '[MW_' + str(MaxWindSpeed_value)
                                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                                            + suffix
                                                                            + '.idf'
                                                                    )
                                                                    outputlist.append(outputname)
                elif ComfStand_value in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 99]:
                    for CAT_value in self.CAT_List:
                        if ComfStand_value in [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                               20, 21] and CAT_value not in range(80, 91, 10):
                            continue
                        elif ComfStand_value in [7, 8] and CAT_value not in range(80, 91, 5):
                            continue
                        else:
                            for ComfMod_value in self.ComfMod_List:
                                if ComfStand_value in [13, 14] and ComfMod_value in [0, 1]:
                                    continue
                                elif ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                    continue
                                elif ComfStand_value == 21 and ComfMod_value not in [2, 3]:
                                    continue
                                else:
                                    for HVACmode_value in self.HVACmode_List:
                                        if HVACmode_value == 0:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                                             self.ASTtol_value_steps):
                                                outputname = (
                                                        filename
                                                        + ComfStand_dict[ComfStand_value]
                                                        + '[CA_' + str(CAT_value)
                                                        + '[CM_' + str(ComfMod_value)
                                                        + '[HM_' + str(HVACmode_value)
                                                        + '[VC_X'
                                                        + '[VO_X'
                                                        + '[MT_X'
                                                        + '[MW_X'
                                                        + '[AT_' + str(round(ASTtol_value, 2))
                                                        + suffix
                                                        + '.idf'
                                                )
                                                outputlist.append(outputname)
                                        else:
                                            for VentCtrl_value in self.VentCtrl_List:
                                                if HVACmode_value == 1 and VentCtrl_value == 2:
                                                    continue
                                                elif HVACmode_value == 1 and VentCtrl_value == 3:
                                                    continue
                                                else:
                                                    for VSToffset_value in self.VSToffset_List:
                                                        for MinOToffset_value in self.MinOToffset_List:
                                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                                 self.ASTtol_value_to,
                                                                                                 self.ASTtol_value_steps):
                                                                    outputname = (
                                                                            filename
                                                                            + ComfStand_dict[ComfStand_value]
                                                                            + '[CA_' + str(CAT_value)
                                                                            + '[CM_' + str(ComfMod_value)
                                                                            + '[HM_' + str(HVACmode_value)
                                                                            + '[VC_' + str(VentCtrl_value)
                                                                            + '[VO_' + str(VSToffset_value)
                                                                            + '[MT_' + str(MinOToffset_value)
                                                                            + '[MW_' + str(MaxWindSpeed_value)
                                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                                            + suffix
                                                                            + '.idf'
                                                                    )
                                                                    outputlist.append(outputname)
        elif temp_control.lower() == 'pmv':
            outputname = (
                    filename
                    + '[CS_PMV'
                    + '[CA_X'
                    + '[CM_X'
                    + '[HM_X'
                    + '[VC_X'
                    + '[VO_X'
                    + '[MT_X'
                    + '[MW_X'
                    + '[AT_X'
                    + suffix
                    + '.idf'
            )
            outputlist.append(outputname)

    if verbose:
        print('The list of output IDFs is going to be:')
        print(*outputlist, sep="\n")
        print(f'And the total number of output IDFs is going to be {len(outputlist)}')

    if confirm_generation is None:
        from accim.sim.prompts import confirm_generation_prompt
        confirm_generation = confirm_generation_prompt()

    if confirm_generation == True:
        if verbose:
            print('Generating the following output IDF files:')
        # pbar = tqdm(total=len(outputlist))
        # self.output_idf_dict = {}
        for file in filelist_pymod:
            filename = file

            fname1 = filename + '.idf'

            filename = file.replace('_pymod', '')
            # if verboseMode:
            #     print(f'Taking "{fname1}" as input IDF file:')

            # idf1 = IDF(fname1)
            idf1 = get_building(fname1)

            # print(filename)
            SetInputData = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetInputData'])
            ApplyCAT = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'ApplyCAT'])
            SetVOFinputData = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetVOFinputData'])
            SetAST = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetAST'])
            SetComfTemp= ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                       program.Name == 'SetComfTemp'])
            SetAppLimits= ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                       program.Name == 'SetAppLimits'])
            if temp_control.lower() == 'temp' or temp_control.lower() == 'temperature':
                for ComfStand_value in self.ComfStand_List:
                    SetInputData[0].Program_Line_1 = 'set ComfStand = ' + str(ComfStand_value)
                    if ComfStand_value == 0:
                        SetInputData[0].Program_Line_2 = 'set CAT = 1'
                        SetInputData[0].Program_Line_3 = 'set ComfMod = 0'
                        for HVACmode_value in self.HVACmode_List:
                            SetInputData[0].Program_Line_4 = 'set HVACmode = ' + str(HVACmode_value)
                            if HVACmode_value == 0:
                                for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                                 self.ASTtol_value_steps):
                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + str(-ASTtol_value)
                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + str(ASTtol_value)
                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + str(self.cooling_season_start)
                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + str(self.cooling_season_end)
                                    ApplyCAT[0].Program_Line_1 = 'set CATcoolOffset = ' + str(self.category_cool_offset)
                                    ApplyCAT[0].Program_Line_2 = 'set CATheatOffset = ' + str(self.category_heat_offset)
                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + str(self.setpoint_accuracy)
                                    outputname = (
                                            filename
                                            + ComfStand_dict[ComfStand_value]
                                            + '[CA_X'
                                            + '[CM_X'
                                            + '[HM_' + str(HVACmode_value)
                                            + '[VC_X'
                                            + '[VO_X'
                                            + '[MT_X'
                                            + '[MW_X'
                                            + '[AT_' + str(round(ASTtol_value, 2))
                                            + suffix
                                            + '.idf'
                                    )
                                    if verbose:
                                        print(outputname)
                                        # time.sleep(0.1)
                                        # pbar.update(1)
                                    while len(SetAST[0].obj) > 18:
                                        SetAST[0].obj.pop()
                                    dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                                    for dline in dynamic_lines:
                                        SetAST[0].obj.append(dline)
                                    idf1.savecopy(outputname)
                                    self.output_idf_dict.update({outputname: idf1})
                            else:
                                for VentCtrl_value in self.VentCtrl_List:
                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + str(VentCtrl_value)
                                    if HVACmode_value == 2:
                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                            SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + str(self.vof_max_temp_diff)
                                            SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + str(self.vof_min_temp_diff)
                                            SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + str(self.vof_multiplier)
                                    for VSToffset_value in self.VSToffset_List:
                                        SetInputData[0].Program_Line_6 = 'set VSToffset = ' + str(VSToffset_value)
                                        for MinOToffset_value in self.MinOToffset_List:
                                            SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + str(
                                                MinOToffset_value)
                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = ' + str(
                                                    MaxWindSpeed_value)
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + str(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + str(ASTtol_value)
                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + str(self.cooling_season_start)
                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + str(self.cooling_season_end)
                                                    ApplyCAT[0].Program_Line_1 = 'set CATcoolOffset = ' + str(self.category_cool_offset)
                                                    ApplyCAT[0].Program_Line_2 = 'set CATheatOffset = ' + str(self.category_heat_offset)
                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + str(self.setpoint_accuracy)
                                                    outputname = (
                                                            filename
                                                            + ComfStand_dict[ComfStand_value]
                                                            + '[CA_X'
                                                            + '[CM_X'
                                                            + '[HM_' + str(HVACmode_value)
                                                            + '[VC_' + str(VentCtrl_value)
                                                            + '[VO_' + str(VSToffset_value)
                                                            + '[MT_' + str(MinOToffset_value)
                                                            + '[MW_' + str(MaxWindSpeed_value)
                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                            + suffix
                                                            + '.idf'
                                                    )
                                                    if verbose:
                                                        print(outputname)
                                                        # time.sleep(0.1)
                                                        # pbar.update(1)
                                                    while len(SetAST[0].obj) > 18:
                                                        SetAST[0].obj.pop()
                                                    dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                                                    for dline in dynamic_lines:
                                                        SetAST[0].obj.append(dline)
                                                    idf1.savecopy(outputname)
                                                    self.output_idf_dict.update({outputname: idf1})
                    elif ComfStand_value in [1, 4, 5, 22]:
                        for CAT_value in self.CAT_List:
                            if ComfStand_value in [1, 22] and CAT_value not in range(0, 4):
                                continue
                            elif ComfStand_value in [4, 5] and CAT_value not in [1, 2]:
                                continue
                            else:
                                SetInputData[0].Program_Line_2 = 'set CAT = ' + str(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    if ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                        continue
                                    elif ComfStand_value == 22 and ComfMod_value != 0:
                                        continue
                                    else:
                                        SetInputData[0].Program_Line_3 = 'set ComfMod = ' + str(ComfMod_value)
                                        for HVACmode_value in self.HVACmode_List:
                                            SetInputData[0].Program_Line_4 = 'set HVACmode = ' + str(HVACmode_value)
                                            if HVACmode_value == 0:
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + str(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + str(ASTtol_value)
                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + str(self.cooling_season_start)
                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + str(self.cooling_season_end)
                                                    ApplyCAT[0].Program_Line_1 = 'set CATcoolOffset = ' + str(self.category_cool_offset)
                                                    ApplyCAT[0].Program_Line_2 = 'set CATheatOffset = ' + str(self.category_heat_offset)
                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + str(self.setpoint_accuracy)
                                                    outputname = (
                                                            filename
                                                            + ComfStand_dict[ComfStand_value]
                                                            + '[CA_' + str(CAT_value)
                                                            + '[CM_' + str(ComfMod_value)
                                                            + '[HM_' + str(HVACmode_value)
                                                            + '[VC_X'
                                                            + '[VO_X'
                                                            + '[MT_X'
                                                            + '[MW_X'
                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                            + suffix
                                                            + '.idf'
                                                    )
                                                    if verbose:
                                                        print(outputname)
                                                        # time.sleep(0.1)
                                                        # pbar.update(1)
                                                    while len(SetAST[0].obj) > 18:
                                                        SetAST[0].obj.pop()
                                                    dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                                                    for dline in dynamic_lines:
                                                        SetAST[0].obj.append(dline)
                                                    idf1.savecopy(outputname)
                                                    self.output_idf_dict.update({outputname: idf1})
                                            else:
                                                for VentCtrl_value in self.VentCtrl_List:
                                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + str(VentCtrl_value)
                                                    if HVACmode_value == 2:
                                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                                            SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + str(self.vof_max_temp_diff)
                                                            SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + str(self.vof_min_temp_diff)
                                                            SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + str(self.vof_multiplier)
                                                    for VSToffset_value in self.VSToffset_List:
                                                        SetInputData[0].Program_Line_6 = 'set VSToffset = ' + str(
                                                            VSToffset_value)
                                                        for MinOToffset_value in self.MinOToffset_List:
                                                            SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + str(
                                                                MinOToffset_value)
                                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                                SetInputData[
                                                                    0].Program_Line_8 = 'set MaxWindSpeed = ' + str(
                                                                    MaxWindSpeed_value)
                                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                                 self.ASTtol_value_to,
                                                                                                 self.ASTtol_value_steps):
                                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + str(-ASTtol_value)
                                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + str(ASTtol_value)
                                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + str(self.cooling_season_start)
                                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + str(self.cooling_season_end)
                                                                    ApplyCAT[0].Program_Line_1 = 'set CATcoolOffset = ' + str(self.category_cool_offset)
                                                                    ApplyCAT[0].Program_Line_2 = 'set CATheatOffset = ' + str(self.category_heat_offset)

                                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + str(self.setpoint_accuracy)
                                                                    outputname = (
                                                                            filename
                                                                            + ComfStand_dict[ComfStand_value]
                                                                            + '[CA_' + str(CAT_value)
                                                                            + '[CM_' + str(ComfMod_value)
                                                                            + '[HM_' + str(HVACmode_value)
                                                                            + '[VC_' + str(VentCtrl_value)
                                                                            + '[VO_' + str(VSToffset_value)
                                                                            + '[MT_' + str(MinOToffset_value)
                                                                            + '[MW_' + str(MaxWindSpeed_value)
                                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                                            + suffix
                                                                            + '.idf'
                                                                    )
                                                                    if verbose:
                                                                        print(outputname)
                                                                        # time.sleep(0.1)
                                                                        # pbar.update(1)
                                                                    while len(SetAST[0].obj) > 18:
                                                                        SetAST[0].obj.pop()
                                                                    dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                                                                    for idx, dline in enumerate(dynamic_lines, start=17):
                                                                        SetAST[0].__setattr__(f'Program_Line_{idx}', dline)
                                                                    idf1.savecopy(outputname)
                                                                    self.output_idf_dict.update({outputname: idf1})
                    elif ComfStand_value in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 99]:
                        for CAT_value in self.CAT_List:
                            if ComfStand_value in [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                                   20, 21] and CAT_value not in range(80, 91, 10):
                                continue
                            elif ComfStand_value in [7, 8] and CAT_value not in range(80, 91, 5):
                                continue
                            else:
                                SetInputData[0].Program_Line_2 = 'set CAT = ' + str(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    if ComfStand_value in [13, 14] and ComfMod_value in [0, 1]:
                                        continue
                                    elif ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                        continue
                                    elif ComfStand_value == 21 and ComfMod_value not in [2, 3]:
                                        continue
                                    else:
                                        SetInputData[0].Program_Line_3 = 'set ComfMod = ' + str(ComfMod_value)
                                        for HVACmode_value in self.HVACmode_List:
                                            SetInputData[0].Program_Line_4 = 'set HVACmode = ' + str(HVACmode_value)
                                            if HVACmode_value == 0:
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + str(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + str(ASTtol_value)
                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + str(self.cooling_season_start)
                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + str(self.cooling_season_end)
                                                    # SetComfTemp[0].Program_Line_2 = f'set ComfTemp = PMOT*{str(self.CustAST_m)}+{str(self.CustAST_n)}'
                                                    SetAppLimits[0].Program_Line_2 = f'set ACSTaul = {str(self.custom_ast_acst_aul)}'
                                                    SetAppLimits[0].Program_Line_3 = f'set ACSTall = {str(self.custom_ast_acst_all)}'
                                                    SetAppLimits[0].Program_Line_4 = f'set AHSTaul = {str(self.custom_ast_ahst_aul)}'
                                                    SetAppLimits[0].Program_Line_5 = f'set AHSTall = {str(self.custom_ast_ahst_all)}'
                                                    ApplyCAT[0].Program_Line_1 = 'set CATcoolOffset = ' + str(self.category_cool_offset)
                                                    ApplyCAT[0].Program_Line_2 = 'set CATheatOffset = ' + str(self.category_heat_offset)
                                                    ApplyCAT[0].Program_Line_4 = f'set ACSToffset = {str(self.custom_ast_acst_offset)} + {str(self.category_cool_offset)}'
                                                    ApplyCAT[0].Program_Line_5 = f'set AHSToffset = {str(self.custom_ast_ahst_offset)} + {str(self.category_heat_offset)}'
                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + str(self.setpoint_accuracy)
                                                    SetAST[0].Program_Line_2 = 'set m = ' + str(self.custom_ast_m)
                                                    SetAST[0].Program_Line_3 = 'set n = ' + str(self.custom_ast_n)
                                                    outputname = (
                                                            filename
                                                            + ComfStand_dict[ComfStand_value]
                                                            + '[CA_' + str(CAT_value)
                                                            + '[CM_' + str(ComfMod_value)
                                                            + '[HM_' + str(HVACmode_value)
                                                            + '[VC_X'
                                                            + '[VO_X'
                                                            + '[MT_X'
                                                            + '[MW_X'
                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                            + suffix
                                                            + '.idf'
                                                    )
                                                    if verbose:
                                                        print(outputname)
                                                        # time.sleep(0.1)
                                                        # pbar.update(1)
                                                    while len(SetAST[0].obj) > 18:
                                                        SetAST[0].obj.pop()
                                                    dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                                                    for dline in dynamic_lines:
                                                        SetAST[0].obj.append(dline)
                                                    idf1.savecopy(outputname)
                                                    self.output_idf_dict.update({outputname: idf1})
                                            else:
                                                for VentCtrl_value in self.VentCtrl_List:
                                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + str(VentCtrl_value)
                                                    if HVACmode_value == 2:
                                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                                            SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + str(self.vof_max_temp_diff)
                                                            SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + str(self.vof_min_temp_diff)
                                                            SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + str(self.vof_multiplier)
                                                    for VSToffset_value in self.VSToffset_List:
                                                        SetInputData[0].Program_Line_6 = 'set VSToffset = ' + str(
                                                            VSToffset_value)
                                                        for MinOToffset_value in self.MinOToffset_List:
                                                            SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + str(
                                                                MinOToffset_value)
                                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                                SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = ' + str(MaxWindSpeed_value)
                                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                                 self.ASTtol_value_to,
                                                                                                 self.ASTtol_value_steps):
                                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + str(-ASTtol_value)
                                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + str(ASTtol_value)
                                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + str(self.cooling_season_start)
                                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + str(self.cooling_season_end)
                                                                    # SetComfTemp[0].Program_Line_2 = f'set ComfTemp = PMOT*{str(self.CustAST_m)}+{str(self.CustAST_n)}'
                                                                    SetAppLimits[0].Program_Line_2 = f'set ACSTaul = {str(self.custom_ast_acst_aul)}'
                                                                    SetAppLimits[0].Program_Line_3 = f'set ACSTall = {str(self.custom_ast_acst_all)}'
                                                                    SetAppLimits[0].Program_Line_4 = f'set AHSTaul = {str(self.custom_ast_ahst_aul)}'
                                                                    SetAppLimits[0].Program_Line_5 = f'set AHSTall = {str(self.custom_ast_ahst_all)}'

                                                                    ApplyCAT[0].Program_Line_1 = 'set CATcoolOffset = ' + str(self.category_cool_offset)
                                                                    ApplyCAT[0].Program_Line_2 = 'set CATheatOffset = ' + str(self.category_heat_offset)
                                                                    ApplyCAT[0].Program_Line_4 = f'set ACSToffset = {str(self.custom_ast_acst_offset)} + {str(self.category_cool_offset)}'
                                                                    ApplyCAT[0].Program_Line_5 = f'set AHSToffset = {str(self.custom_ast_ahst_offset)} + {str(self.category_heat_offset)}'
                                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + str(self.setpoint_accuracy)
                                                                    SetAST[0].Program_Line_2 = 'set m = ' + str(self.custom_ast_m)
                                                                    SetAST[0].Program_Line_3 = 'set n = ' + str(self.custom_ast_n)

                                                                    outputname = (
                                                                            filename
                                                                            + ComfStand_dict[ComfStand_value]
                                                                            + '[CA_' + str(CAT_value)
                                                                            + '[CM_' + str(ComfMod_value)
                                                                            + '[HM_' + str(HVACmode_value)
                                                                            + '[VC_' + str(VentCtrl_value)
                                                                            + '[VO_' + str(VSToffset_value)
                                                                            + '[MT_' + str(MinOToffset_value)
                                                                            + '[MW_' + str(MaxWindSpeed_value)
                                                                            + '[AT_' + str(round(ASTtol_value, 2))
                                                                            + suffix
                                                                            + '.idf'
                                                                    )
                                                                    if verbose:
                                                                        print(outputname)
                                                                        # time.sleep(0.1)
                                                                        # pbar.update(1)
                                                                    while len(SetAST[0].obj) > 18:
                                                                        SetAST[0].obj.pop()
                                                                    dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                                                                    for idx, dline in enumerate(dynamic_lines, start=17):
                                                                        SetAST[0].__setattr__(f'Program_Line_{idx}', dline)
                                                                    idf1.savecopy(outputname)
                                                                    self.output_idf_dict.update({outputname: idf1})
            elif temp_control.lower() == 'pmv':
                SetInputData[0].Program_Line_4 = 'set HVACmode = 0'
                outputname = (
                        filename
                        + '[CS_PMV'
                        + '[CA_X'
                        + '[CM_X'
                        + '[HM_0'
                        + '[VC_X'
                        + '[VO_X'
                        + '[MT_X'
                        + '[MW_X'
                        + '[AT_X'
                        + suffix
                        + '.idf'
                )
                if verbose:
                    print(outputname)
                    # time.sleep(0.1)
                    # pbar.update(1)
                while len(SetAST[0].obj) > 18:
                    SetAST[0].obj.pop()
                dynamic_lines = get_SetAST_lines(ComfStand_value, ComfMod_value)
                for idx, dline in enumerate(dynamic_lines, start=17):
                    SetAST[0].__setattr__(f'Program_Line_{idx}', dline)
                idf1.savecopy(outputname)
                self.output_idf_dict.update({outputname: idf1})
        # pbar.close()
    elif confirm_generation == False:
        if verbose:
            print('IDF generation has been shut down')

    filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
    for file in filelist_pymod:
        os.remove(file)

    # del SetInputData
