"""Generate IDFs."""





def inputData(self, ScriptType: str = None):
    """Input data for IDF generation."""
    print('The information you will be required to enter below will be used to generate the customised output IDFs:')
    fullComfStandList = list(range(16+1))
    self.ComfStand_List = list(int(num) for num in input(
        'Enter the Comfort Standard numbers separated by space (\n'
        '0 = CTE;\n'
        '1 = EN16798-1;\n'
        '2 = ASHRAE 55;\n'
        '3 = JPN·Rijal;\n'
        '4 = GBT50785·Cold;\n'
        '5 = GBT50785·HotMild;\n'
        '6 = CHN·Yang;\n'
        '7 = IMAC·C·NV;\n'
        '8 = IMAC·C·MM;\n'
        '9 = IMAC·R·7DRM;\n'
        '10 = IMAC·R·30DRM;\n'
        '11 = IND·Dhaka;\n'
        '12 = ROM·Udrea;\n'
        '13 = AUS·Williamson;\n'
        '14 = AUS·DeDear;\n'
        '15 = BRA·Rupp·NV;\n'
        '16 = BRA·Rupp·AC;\n'
        '): '
    ).split())
    while len(self.ComfStand_List) == 0 or not all(elem in fullComfStandList for elem in self.ComfStand_List):
        print('          Comfort Standard numbers are not correct. Please enter the numbers again.')
        self.ComfStand_List = list(int(num) for num in input("     Enter the Comfort Standard numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.ComfStand_List = list(int(num) for num in input("     Enter the Comfort Standard numbers separated by space: ").split())
        while len(self.ComfStand_List) == 0 or not all(elem in fullComfStandList for elem in self.ComfStand_List):
            print('          Comfort Standard numbers are not correct. Please enter the numbers again.')
            self.ComfStand_List = list(int(num) for num in input("     Enter the Comfort Standard numbers separated by space: ").split())

    fullCATlist = [1, 2, 3, 80, 85, 90]
    self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space (1 = CAT I; 2 = CAT II; 3 = CAT III; 80 = 80% ACCEPT; 85 = 85% ACCEPT; 90 = 90% ACCEPT; Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png): ").split())
    while len(self.CAT_List) == 0 or not all(elem in fullCATlist for elem in self.CAT_List):
        print('          Category numbers are not correct. Please enter the numbers again.')
        self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.CAT_List = list(int(num) for num in input("     Enter the Category numbers separated by space: ").split())
        while len(self.CAT_List) == 0 or not all(elem in fullCATlist for elem in self.CAT_List):
            print('          Category numbers are not correct. Please enter the numbers again.')
            self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space: ").split())

    fullComfModList = [0, 1, 2, 3]
    self.ComfMod_List = list(int(num) for num in input("Enter the Comfort Mode numbers separated by space (0 = Static; 1, 2, 3 = Adaptive; Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png): ").split())
    while len(self.ComfMod_List) == 0 or not all(elem in fullComfModList for elem in self.ComfMod_List):
        print('          Comfort Mode numbers are not correct. Please enter the numbers again.')
        self.ComfMod_List = list(int(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.ComfMod_List = list(int(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())
        while len(self.ComfMod_List) == 0 or not all(elem in fullComfModList for elem in self.ComfMod_List):
            print('          Comfort Mode numbers are not correct. Please enter the numbers again.')
            self.ComfMod_List = list(int(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())

    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
        fullHVACmodeList = [0, 1, 2]
        self.HVACmode_List = list(int(num) for num in input("Enter the HVAC Mode numbers separated by space (0 = Fully Air-conditioned; 1 = Naturally ventilated; 2 = Mixed Mode): ").split())
        while len(self.HVACmode_List) == 0 or not all(elem in fullHVACmodeList for elem in self.HVACmode_List):
            print('          HVACmode numbers are not correct. Please enter the numbers again.')
            self.HVACmode_List = list(int(num) for num in input("     Enter the HVACmode numbers separated by space: ").split())
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.HVACmode_List = list(int(num) for num in input("     Enter the HVACmode numbers separated by space: ").split())
            while len(self.HVACmode_List) == 0 or not all(elem in fullHVACmodeList for elem in self.HVACmode_List):
                print('          HVACmode numbers are not correct. Please enter the numbers again.')
                self.HVACmode_List = list(int(num) for num in input("     Enter the HVACmode numbers separated by space: ").split())

        fullVentCtrlList = [0, 1]
        self.VentCtrl_List = list(int(num) for num in input("Enter the Ventilation Control numbers separated by space (0 = Ventilates above neutral temperature; 1 = Ventilates above upper comfort limit): ").split())
        while len(self.VentCtrl_List) == 0 or not all(elem in fullVentCtrlList for elem in self.VentCtrl_List):
            print('          Ventilation Control numbers are not correct. Please enter the numbers again.')
            self.VentCtrl_List = list(int(num) for num in input("     Enter the Ventilation Control numbers separated by space: ").split())
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.VentCtrl_List = list(int(num) for num in input("     Enter the Ventilation Control numbers separated by space: ").split())
            while len(self.VentCtrl_List) == 0 or not all(elem in fullVentCtrlList for elem in self.VentCtrl_List):
                print('          Ventilation Control numbers are not correct. Please enter the numbers again.')
                self.VentCtrl_List = list(int(num) for num in input("     Enter the Ventilation Control numbers separated by space: ").split())

        self.VSToffset_List = list(float(num) for num in input("Enter the VSToffset numbers separated by space (if omitted, will be 0): ").split())
        if len(self.VSToffset_List) == 0:
            self.VSToffset_List = [float(0)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.VSToffset_List = list(float(num) for num in input("     Enter the VSToffset numbers separated by space (if omitted, will be 0): ").split())
            if len(self.VSToffset_List) == 0:
                self.VSToffset_List = [float(0)]

        self.MinOToffset_List = list(float(num) for num in input("Enter the MinOToffset numbers separated by space (if omitted, will be 50): ").split())
        if len(self.MinOToffset_List) == 0:
            self.MinOToffset_List = [float(50)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.MinOToffset_List = list(float(num) for num in input("     Enter the MinOToffset numbers separated by space (if omitted, will be 50): ").split())
            if len(self.MinOToffset_List) == 0:
                self.MinOToffset_List = [float(50)]

        self.MaxWindSpeed_List = list(float(num) for num in input("Enter the MaxWindSpeed numbers separated by space (if omitted, will be 50): ").split())
        if len(self.MaxWindSpeed_List) == 0:
            self.MaxWindSpeed_List = [float(50)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.MaxWindSpeed_List = list(float(num) for num in input("     Enter the MaxWindSpeed numbers separated by space (if omitted, will be 50): ").split())
            if len(self.MaxWindSpeed_List) == 0:
                self.MaxWindSpeed_List = [float(50)]
    elif ScriptType.lower() == 'ex_ac':
        self.HVACmode_List = [0]
        self.VentCtrl_List = [0]
        self.VSToffset_List = [0]
        self.MinOToffset_List = [0]
        self.MaxWindSpeed_List = [0]

    try:
        self.ASTtol_value_from = float(input('Enter the ASTtol value from (if omitted, will be 0.1): '))
    except ValueError:
        self.ASTtol_value_from = float(0.1)
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        try:
            self.ASTtol_value_from = float(input('     Enter the ASTtol value from (if omitted, will be 0.1): '))
        except ValueError:
            self.ASTtol_value_from = float(0.1)

    try:
        self.ASTtol_value_to_input = float(input('Enter the ASTtol value to (if omitted, will be 0.1): '))
    except ValueError:
        self.ASTtol_value_to_input = float(0.1)
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        try:
            self.ASTtol_value_to_input = float(input('     Enter the ASTtol value to (if omitted, will be 0.1): '))
        except ValueError:
            self.ASTtol_value_to_input = float(0.1)

    try:
        self.ASTtol_value_steps = float(input('Enter the ASTtol value steps (if omitted, will be 0.1): '))
    except ValueError:
        self.ASTtol_value_steps = float(0.1)
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        try:
            self.ASTtol_value_steps = float(input('     Enter the ASTtol value steps (if omitted, will be 0.1): '))
        except ValueError:
            self.ASTtol_value_steps = float(0.1)


def genIDF(self,
           ScriptType: str = None,
           TempCtrl: str = None,
           ComfStand=None,
           CAT=None,
           ComfMod=None,
           HVACmode=None,
           VentCtrl=None,
           VSToffset=[0],
           MinOToffset=[50],
           MaxWindSpeed=[50],
           ASTtol_start=0.1,
           ASTtol_end_input=0.1,
           ASTtol_steps=0.1,
           NameSuffix='',
           verboseMode: bool = True,
           confirmGen: bool = None
           ):
    """Generate IDFs."""
    import os
    from os import listdir
    import numpy
    from eppy import modeleditor
    from eppy.modeleditor import IDF
    # import time
    # from tqdm import tqdm

    arguments = (ComfStand is None,
                 CAT is None,
                 ComfMod is None,
                 HVACmode is None,
                 VentCtrl is None,
                 VSToffset == [0],
                 MinOToffset == [50],
                 MaxWindSpeed == [50],
                 ASTtol_start == 0.1,
                 ASTtol_end_input == 0.1,
                 ASTtol_steps == 0.1)
    if all(arguments):
        self.ASTtol_value_to = self.ASTtol_value_to_input+self.ASTtol_value_steps
    else:
        ASTtol_end = ASTtol_end_input + ASTtol_steps

    if all(arguments):
        self.ASTtol_value_from = round(self.ASTtol_value_from, 2)
        self.ASTtol_value_to = round(self.ASTtol_value_to, 2)
        self.ASTtol_value_steps = round(self.ASTtol_value_steps, 2)
    else:
        self.ComfStand_List = ComfStand
        self.CAT_List = CAT
        self.ComfMod_List = ComfMod
        self.HVACmode_List = HVACmode
        self.VentCtrl_List = VentCtrl
        self.VSToffset_List = VSToffset
        self.MinOToffset_List = MinOToffset
        self.MaxWindSpeed_List = MaxWindSpeed
        self.ASTtol_value_from = round(ASTtol_start, 2)
        self.ASTtol_value_to = round(ASTtol_end, 2)
        self.ASTtol_value_steps = round(ASTtol_steps, 2)

    if ScriptType.lower == 'ex_ac':
        self.HVACmode_List = [0]
        self.VentCtrl_List = [0]
        self.VSToffset_List = [0]
        self.MinOToffset_List = [0]
        self.MaxWindSpeed_List = [0]

    if NameSuffix == '':
        suffix = '[NS_X'
    else:
        suffix = '[NS_' + NameSuffix

    filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
    filelist_pymod = ([file.split('.idf')[0] for file in filelist_pymod])
    # print(filelist_pymod)

    # Characters not admitted: & ^ , = % " / \ : * ? " < > |
    ComfStand_dict = {
        0: '[CS_CTE',
        1: '[CS_EN16798',
        2: '[CS_ASHRAE55',
        3: '[CS_JPN·Rijal',
        4: '[CS_GBT50785·Cold',
        5: '[CS_GBT50785·HotMild',
        6: '[CS_CHN·Yang',
        7: '[CS_IMAC·C·NV',
        8: '[CS_IMAC·C·MM',
        9: '[CS_IMAC·R·7DRM',
        10: '[CS_IMAC·R·30DRM',
        11: '[CS_IND·Dhaka',
        12: '[CS_ROM·Udrea',
        13: '[CS_AUS·Williamson',
        14: '[CS_AUS·DeDear',
        15: '[CS_BRA·Rupp·NV',
        16: '[CS_BRA·Rupp·AC',
    }

    outputlist = []
    for file in filelist_pymod:
        filename = file.replace('_pymod', '')
        if TempCtrl.lower() == 'temp' or TempCtrl.lower() == 'temperature':
            for ComfStand_value in self.ComfStand_List:
                if ComfStand_value == 0:
                    for HVACmode_value in self.HVACmode_List:
                        if HVACmode_value == 0:
                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                outputname = (
                                    filename
                                    + ComfStand_dict[ComfStand_value]
                                    + '[CA_X'
                                    + '[CM_X'
                                    + '[HM_' + repr(HVACmode_value)
                                    + '[VC_X'
                                    + '[VO_X'
                                    + '[MT_X'
                                    + '[MW_X'
                                    + '[AT_' + repr(ASTtol_value)
                                    + suffix
                                    + '.idf'
                                    )
                                outputlist.append(outputname)
                        else:
                            for VentCtrl_value in self.VentCtrl_List:
                                for VSToffset_value in self.VSToffset_List:
                                    for MinOToffset_value in self.MinOToffset_List:
                                        for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                outputname = (
                                                    filename
                                                    + ComfStand_dict[ComfStand_value]
                                                    + '[CA_X'
                                                    + '[CM_X'
                                                    + '[HM_' + repr(HVACmode_value)
                                                    + '[VC_' + repr(VentCtrl_value)
                                                    + '[VO_' + repr(VSToffset_value)
                                                    + '[MT_' + repr(MinOToffset_value)
                                                    + '[MW_' + repr(MaxWindSpeed_value)
                                                    + '[AT_' + repr(ASTtol_value)
                                                    + suffix
                                                    + '.idf'
                                                    )
                                                outputlist.append(outputname)
                elif ComfStand_value in [1, 4, 5]:
                    for CAT_value in self.CAT_List:
                        if ComfStand_value in [1] and CAT_value not in range(0, 4):
                            continue
                        elif ComfStand_value in [4, 5] and CAT_value not in [1, 2]:
                            continue
                        else:
                            for ComfMod_value in self.ComfMod_List:
                                for HVACmode_value in self.HVACmode_List:
                                    if HVACmode_value == 0:
                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                            outputname = (
                                                filename
                                                + ComfStand_dict[ComfStand_value]
                                                + '[CA_' + repr(CAT_value)
                                                + '[CM_' + repr(ComfMod_value)
                                                + '[HM_' + repr(HVACmode_value)
                                                + '[VC_X'
                                                + '[VO_X'
                                                + '[MT_X'
                                                + '[MW_X'
                                                + '[AT_' + repr(ASTtol_value)
                                                + suffix
                                                + '.idf'
                                                )
                                            outputlist.append(outputname)
                                    else:
                                        for VentCtrl_value in self.VentCtrl_List:
                                            for VSToffset_value in self.VSToffset_List:
                                                for MinOToffset_value in self.MinOToffset_List:
                                                    for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                            outputname = (
                                                                filename
                                                                + ComfStand_dict[ComfStand_value]
                                                                + '[CA_' + repr(CAT_value)
                                                                + '[CM_' + repr(ComfMod_value)
                                                                + '[HM_' + repr(HVACmode_value)
                                                                + '[VC_' + repr(VentCtrl_value)
                                                                + '[VO_' + repr(VSToffset_value)
                                                                + '[MT_' + repr(MinOToffset_value)
                                                                + '[MW_' + repr(MaxWindSpeed_value)
                                                                + '[AT_' + repr(ASTtol_value)
                                                                + suffix
                                                                + '.idf'
                                                                )
                                                            outputlist.append(outputname)
                elif ComfStand_value in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
                    for CAT_value in self.CAT_List:
                        if ComfStand_value in [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16] and CAT_value not in range(80, 91, 10):
                            continue
                        elif ComfStand_value in [7, 8] and CAT_value not in range(80, 91, 5):
                            continue
                        else:
                            for ComfMod_value in self.ComfMod_List:
                                for HVACmode_value in self.HVACmode_List:
                                    if HVACmode_value == 0:
                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                            outputname = (
                                                filename
                                                + ComfStand_dict[ComfStand_value]
                                                + '[CA_' + repr(CAT_value)
                                                + '[CM_' + repr(ComfMod_value)
                                                + '[HM_' + repr(HVACmode_value)
                                                + '[VC_X'
                                                + '[VO_X'
                                                + '[MT_X'
                                                + '[MW_X'
                                                + '[AT_' + repr(ASTtol_value)
                                                + suffix
                                                + '.idf'
                                                )
                                            outputlist.append(outputname)
                                    else:
                                        for VentCtrl_value in self.VentCtrl_List:
                                            for VSToffset_value in self.VSToffset_List:
                                                for MinOToffset_value in self.MinOToffset_List:
                                                    for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                            outputname = (
                                                                filename
                                                                + ComfStand_dict[ComfStand_value]
                                                                + '[CA_' + repr(CAT_value)
                                                                + '[CM_' + repr(ComfMod_value)
                                                                + '[HM_' + repr(HVACmode_value)
                                                                + '[VC_' + repr(VentCtrl_value)
                                                                + '[VO_' + repr(VSToffset_value)
                                                                + '[MT_' + repr(MinOToffset_value)
                                                                + '[MW_' + repr(MaxWindSpeed_value)
                                                                + '[AT_' + repr(ASTtol_value)
                                                                + suffix
                                                                + '.idf'
                                                                )
                                                            outputlist.append(outputname)
        elif TempCtrl.lower() == 'pmv':
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

    if verboseMode:
        print('The list of output IDFs is going to be:')
        print(*outputlist, sep="\n")
        print(f'And the total number of output IDFs is going to be {len(outputlist)}')

    if confirmGen is None:
        confirmGen = input('Do you still want to run ACCIS? [y/n]: ')
        if confirmGen == 'y':
            confirmGen = True
        else:
            confirmGen = False

    if confirmGen == True:
        if verboseMode:
            print('Generating the following output IDF files:')
        # pbar = tqdm(total=len(outputlist))
        for file in filelist_pymod:
            filename = file

            fname1 = filename+'.idf'

            filename = file.replace('_pymod', '')
            # if verboseMode:
            #     print(f'Taking "{fname1}" as input IDF file:')
            idf1 = IDF(fname1)

            # print(filename)
            SetInputData = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetInputData'])
            if TempCtrl.lower() == 'temp' or TempCtrl.lower() == 'temperature':
                for ComfStand_value in self.ComfStand_List:
                    SetInputData[0].Program_Line_1 = 'set ComfStand = '+repr(ComfStand_value)
                    if ComfStand_value == 0:
                        SetInputData[0].Program_Line_2 = 'set CAT = 1'
                        SetInputData[0].Program_Line_3 = 'set ComfMod = 0'
                        for HVACmode_value in self.HVACmode_List:
                            SetInputData[0].Program_Line_4 = 'set HVACmode = '+repr(HVACmode_value)
                            if HVACmode_value == 0:
                                for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = '+repr(-ASTtol_value)
                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = '+repr(ASTtol_value)
                                    outputname = (
                                        filename
                                        + ComfStand_dict[ComfStand_value]
                                        + '[CA_X'
                                        + '[CM_X'
                                        + '[HM_' + repr(HVACmode_value)
                                        + '[VC_X'
                                        + '[VO_X'
                                        + '[MT_X'
                                        + '[MW_X'
                                        + '[AT_' + repr(ASTtol_value)
                                        + suffix
                                        + '.idf'
                                        )
                                    if verboseMode:
                                        print(outputname)
                                        # time.sleep(0.1)
                                        # pbar.update(1)
                                    idf1.savecopy(outputname)
                            else:
                                for VentCtrl_value in self.VentCtrl_List:
                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = '+repr(VentCtrl_value)
                                    for VSToffset_value in self.VSToffset_List:
                                        SetInputData[0].Program_Line_6 = 'set VSToffset = '+repr(VSToffset_value)
                                        for MinOToffset_value in self.MinOToffset_List:
                                            SetInputData[0].Program_Line_7 = 'set MinOToffset = '+repr(MinOToffset_value)
                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = '+repr(MaxWindSpeed_value)
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = '+repr(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = '+repr(ASTtol_value)
                                                    outputname = (
                                                        filename
                                                        + ComfStand_dict[ComfStand_value]
                                                        + '[CA_X'
                                                        + '[CM_X'
                                                        + '[HM_' + repr(HVACmode_value)
                                                        + '[VC_' + repr(VentCtrl_value)
                                                        + '[VO_' + repr(VSToffset_value)
                                                        + '[MT_' + repr(MinOToffset_value)
                                                        + '[MW_' + repr(MaxWindSpeed_value)
                                                        + '[AT_' + repr(ASTtol_value)
                                                        + suffix
                                                        + '.idf'
                                                        )
                                                    if verboseMode:
                                                        print(outputname)
                                                        # time.sleep(0.1)
                                                        # pbar.update(1)
                                                    idf1.savecopy(outputname)
                    elif ComfStand_value in [1, 4, 5]:
                        for CAT_value in self.CAT_List:
                            if ComfStand_value in [1] and CAT_value not in range(0, 4):
                                continue
                            elif ComfStand_value in [4, 5] and CAT_value not in [1, 2]:
                                continue
                            else:
                                SetInputData[0].Program_Line_2 = 'set CAT = '+repr(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    SetInputData[0].Program_Line_3 = 'set ComfMod = '+repr(ComfMod_value)
                                    for HVACmode_value in self.HVACmode_List:
                                        SetInputData[0].Program_Line_4 = 'set HVACmode = '+repr(HVACmode_value)
                                        if HVACmode_value == 0:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                SetInputData[0].Program_Line_9 = 'set ACSTtol = '+repr(-ASTtol_value)
                                                SetInputData[0].Program_Line_10 = 'set AHSTtol = '+repr(ASTtol_value)
                                                outputname = (
                                                    filename
                                                    + ComfStand_dict[ComfStand_value]
                                                    + '[CA_' + repr(CAT_value)
                                                    + '[CM_' + repr(ComfMod_value)
                                                    + '[HM_' + repr(HVACmode_value)
                                                    + '[VC_X'
                                                    + '[VO_X'
                                                    + '[MT_X'
                                                    + '[MW_X'
                                                    + '[AT_' + repr(ASTtol_value)
                                                    + suffix
                                                    + '.idf'
                                                    )
                                                if verboseMode:
                                                    print(outputname)
                                                    # time.sleep(0.1)
                                                    # pbar.update(1)
                                                idf1.savecopy(outputname)
                                        else:
                                            for VentCtrl_value in self.VentCtrl_List:
                                                SetInputData[0].Program_Line_5 = 'set VentCtrl = '+repr(VentCtrl_value)
                                                for VSToffset_value in self.VSToffset_List:
                                                    SetInputData[0].Program_Line_6 = 'set VSToffset = '+repr(VSToffset_value)
                                                    for MinOToffset_value in self.MinOToffset_List:
                                                        SetInputData[0].Program_Line_7 = 'set MinOToffset = '+repr(MinOToffset_value)
                                                        for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                            SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = '+repr(MaxWindSpeed_value)
                                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                                SetInputData[0].Program_Line_9 = 'set ACSTtol = '+repr(-ASTtol_value)
                                                                SetInputData[0].Program_Line_10 = 'set AHSTtol = '+repr(ASTtol_value)
                                                                outputname = (
                                                                    filename
                                                                    + ComfStand_dict[ComfStand_value]
                                                                    + '[CA_' + repr(CAT_value)
                                                                    + '[CM_' + repr(ComfMod_value)
                                                                    + '[HM_' + repr(HVACmode_value)
                                                                    + '[VC_' + repr(VentCtrl_value)
                                                                    + '[VO_' + repr(VSToffset_value)
                                                                    + '[MT_' + repr(MinOToffset_value)
                                                                    + '[MW_' + repr(MaxWindSpeed_value)
                                                                    + '[AT_' + repr(ASTtol_value)
                                                                    + suffix
                                                                    + '.idf'
                                                                    )
                                                                if verboseMode:
                                                                    print(outputname)
                                                                    # time.sleep(0.1)
                                                                    # pbar.update(1)
                                                                idf1.savecopy(outputname)
                    elif ComfStand_value in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
                        for CAT_value in self.CAT_List:
                            if ComfStand_value in [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16] and CAT_value not in range(80, 91, 10):
                                continue
                            elif ComfStand_value in [7, 8] and CAT_value not in range(80, 91, 5):
                                continue
                            else:
                                SetInputData[0].Program_Line_2 = 'set CAT = '+repr(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    SetInputData[0].Program_Line_3 = 'set ComfMod = '+repr(ComfMod_value)
                                    for HVACmode_value in self.HVACmode_List:
                                        SetInputData[0].Program_Line_4 = 'set HVACmode = '+repr(HVACmode_value)
                                        if HVACmode_value == 0:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                SetInputData[0].Program_Line_9 = 'set ACSTtol = '+repr(-ASTtol_value)
                                                SetInputData[0].Program_Line_10 = 'set AHSTtol = '+repr(ASTtol_value)
                                                outputname = (
                                                    filename
                                                    + ComfStand_dict[ComfStand_value]
                                                    + '[CA_' + repr(CAT_value)
                                                    + '[CM_' + repr(ComfMod_value)
                                                    + '[HM_' + repr(HVACmode_value)
                                                    + '[VC_X'
                                                    + '[VO_X'
                                                    + '[MT_X'
                                                    + '[MW_X'
                                                    + '[AT_' + repr(ASTtol_value)
                                                    + suffix
                                                    + '.idf'
                                                    )
                                                if verboseMode:
                                                    print(outputname)
                                                    # time.sleep(0.1)
                                                    # pbar.update(1)
                                                idf1.savecopy(outputname)
                                        else:
                                            for VentCtrl_value in self.VentCtrl_List:
                                                SetInputData[0].Program_Line_5 = 'set VentCtrl = '+repr(VentCtrl_value)
                                                for VSToffset_value in self.VSToffset_List:
                                                    SetInputData[0].Program_Line_6 = 'set VSToffset = '+repr(VSToffset_value)
                                                    for MinOToffset_value in self.MinOToffset_List:
                                                        SetInputData[0].Program_Line_7 = 'set MinOToffset = '+repr(MinOToffset_value)
                                                        for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                            SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = '+repr(MaxWindSpeed_value)
                                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to, self.ASTtol_value_steps):
                                                                SetInputData[0].Program_Line_9 = 'set ACSTtol = '+repr(-ASTtol_value)
                                                                SetInputData[0].Program_Line_10 = 'set AHSTtol = '+repr(ASTtol_value)
                                                                outputname = (
                                                                    filename
                                                                    + ComfStand_dict[ComfStand_value]
                                                                    + '[CA_' + repr(CAT_value)
                                                                    + '[CM_' + repr(ComfMod_value)
                                                                    + '[HM_' + repr(HVACmode_value)
                                                                    + '[VC_' + repr(VentCtrl_value)
                                                                    + '[VO_' + repr(VSToffset_value)
                                                                    + '[MT_' + repr(MinOToffset_value)
                                                                    + '[MW_' + repr(MaxWindSpeed_value)
                                                                    + '[AT_' + repr(ASTtol_value)
                                                                    + suffix
                                                                    + '.idf'
                                                                    )
                                                                if verboseMode:
                                                                    print(outputname)
                                                                    # time.sleep(0.1)
                                                                    # pbar.update(1)
                                                                idf1.savecopy(outputname)
            elif TempCtrl.lower() == 'pmv':
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
                if verboseMode:
                    print(outputname)
                    # time.sleep(0.1)
                    # pbar.update(1)
                idf1.savecopy(outputname)

        # pbar.close()
    elif confirmGen == False:
        if verboseMode:
            print('IDF generation has been shut down')

    filelist_pymod = ([file for file in listdir() if file.endswith('_pymod.idf')])
    for file in filelist_pymod:
        os.remove(file)

    # del SetInputData
