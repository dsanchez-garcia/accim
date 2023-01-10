"""Generate IDFs."""


def inputData(self, ScriptType: str = None):
    """Input data for IDF generation."""
    CS_CA_CM_list_dict = {
        '0 = ESP CTE': [['n/a'], ['n/a']],
        '1 = INT EN16798-1': [[1, 2, 3], [0, 1, 2, 3]],
        '2 = INT ASHRAE55': [[80, 90], [0, 1, 2, 3]],
        '3 = JPN Rijal': [[80, 90], [0, 1, 2, 3]],
        '4 = CHN GBT50785 Cold': [[1, 2], [3]],
        '5 = CHN GBT50785 HotMild': [[1, 2], [3]],
        '6 = CHN Yang': [[80, 90], [0, 1, 2, 3]],
        '7 = IND IMAC C NV': [[80, 85, 90], [0, 1, 2, 3]],
        '8 = IND IMAC C MM': [[80, 85, 90], [0, 1, 2, 3]],
        '9 = IND IMAC R 7DRM': [[80, 90], [0, 1, 2, 3]],
        '10 = IND IMAC R 30DRM': [[80, 90], [0, 1, 2, 3]],
        '11 = IND Dhaka': [[80, 90], [0, 1, 2, 3]],
        '12 = ROM Udrea': [[80, 90], [0, 1, 2, 3]],
        '13 = AUS Williamson': [[80, 90], [0, 1, 2, 3]],
        '14 = AUS DeDear': [[80, 90], [0, 1, 2, 3]],
        '15 = BRA Rupp NV': [[80, 90], [0, 1, 2, 3]],
        '16 = BRA Rupp AC': [[80, 90], [0, 1, 2, 3]],
        '17 = MEX Oropeza Arid': [[80, 90], [0, 1, 2, 3]],
        '18 = MEX Oropeza DryTropic': [[80, 90], [0, 1, 2, 3]],
        '19 = MEX Oropeza Temperate': [[80, 90], [0, 1, 2, 3]],
        '20 = MEX Oropeza HumTropic': [[80, 90], [0, 1, 2, 3]],
        '21 = CHL Perez-Fargallo': [[80, 90], [2, 3]],

    }


    CS_CA_CM_data_dict = {
        0: {
            'name': '0 = ESP CTE',
            'CAT':{
                'n/a': 'n/a'
            },
            'ComfMod': {
                'n/a': 'n/a'
            }
        },
        1: {
            'name': '1 = INT EN16798',
            'CAT': {
                1: 'EN16798 Category I',
                2: 'EN16798 Category II',
                3: 'EN16798 Category III',
            },
            'ComfMod': {
                0: 'EN16798 Static setpoints',
                1: 'EN16798 Adaptive setpoints when applicable, otherwise CTE',
                2: 'EN16798 Adaptive setpoints when applicable, otherwise EN16798 Static setpoints',
                3: 'EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive setpoints horizontally extended',
            }
        },
        2: {
            'name': '2 = INT ASHRAE55',
            'CAT': {
                80: 'ASHRAE 55 80% acceptability',
                90: 'ASHRAE 55 90% acceptability',
            },
            'ComfMod': {
                0: 'ASHRAE 55 Static setpoints (calculated with Clima Tool)',
                1: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise CTE',
                2: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints horizontally extended',
            }
        },
        3: {
            'name': '3 = JPN Rijal',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'COOLBIZ Static setpoints',
                1: 'Rijal Model Adaptive setpoints when applicable, otherwise COOLBIZ Static setpoints',
                2: 'Rijal Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Rijal Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        4: {
            'name': '4 = CHN GBT50785 Cold',
            'CAT': {
                1: '90% acceptability',
                2: '75-90% acceptability',
            },
            'ComfMod': {
                # 0: 'X Static setpoints',
                # 1: 'GBT50785 Cold Model Adaptive setpoints when applicable, otherwise X Static setpoints',
                # 2: 'GBT50785 Cold Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'GBT50785 Cold Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        5: {
            'name': '5 = CHN GBT50785 HotMild',
            'CAT': {
                1: '90% acceptability',
                2: '75-90% acceptability',
            },
            'ComfMod': {
                # 0: 'X Static setpoints',
                # 1: 'GBT50785 HotMild Model Adaptive setpoints when applicable, otherwise X Static setpoints',
                # 2: 'GBT50785 HotMild Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'GBT50785 HotMild Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        6: {
            'name': '6 = CHN Yang',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                # 0: 'X Static setpoints',
                # 1: 'Yang Model Adaptive setpoints when applicable, otherwise X Static setpoints',
                2: 'Yang Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Yang Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        7: {
            'name': '7 = IND IMAC C NV',
            'CAT': {
                80: '80% acceptability',
                85: '85% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Indian Building Code Static setpoints',
                1: 'IMAC C NV Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints',
                2: 'IMAC C NV Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'IMAC C NV Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        8: {
            'name': '8 = IND IMAC C MM',
            'CAT': {
                80: '80% acceptability',
                85: '85% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Indian Building Code Static setpoints',
                1: 'IMAC C MM Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints',
                2: 'IMAC C MM Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'IMAC C MM Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        9: {
            'name': '9 = IND IMAC R 7DRM',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Indian Building Code Static setpoints',
                1: 'IMAC R 7DRM Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints',
                2: 'IMAC R 7DRM Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'IMAC R 7DRM Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        10: {
            'name': '10 = IND IMAC R 30DRM',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Indian Building Code Static setpoints',
                1: 'IMAC R 30DRM Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints',
                2: 'IMAC R 30DRM Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'IMAC R 30DRM Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        11: {
            'name': '11 = IND Dhaka',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Indian Building Code Static setpoints',
                1: 'Dhaka Model Adaptive setpoints when applicable, otherwise Indian Building Code Static setpoints',
                2: 'Dhaka Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Dhaka Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        12: {
            'name': '12 = ROM Udrea',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Romanian Building Code Static setpoints',
                1: 'Udrea Model Adaptive setpoints when applicable, otherwise Romanian Building Code Static setpoints',
                2: 'Udrea Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Udrea Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        13: {
            'name': '13 = AUS Williamson',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Australian Building Code Static setpoints',
                1: 'Williamson Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints',
                2: 'Williamson Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Williamson Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        14: {
            'name': '14 = AUS DeDear',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Australian Building Code Static setpoints',
                1: 'DeDear Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints',
                2: 'DeDear Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'DeDear Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        15: {
            'name': '15 = BRA Rupp NV',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Brazilian Building Code Static setpoints (ABNT NBR 16401-2 Standard (2008))',
                1: 'Rupp NV Model Adaptive setpoints when applicable, otherwise Brazilian Building Code Static setpoints',
                2: 'Rupp NV Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Rupp NV Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        16: {
            'name': '16 = BRA Rupp AC',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Brazilian Building Code Static setpoints (ABNT NBR 16401-2 Standard (2008))',
                1: 'Rupp AC Model Adaptive setpoints when applicable, otherwise Brazilian Building Code Static setpoints',
                2: 'Rupp AC Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Rupp AC Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        17: {
            'name': '17 = MEX Oropeza Arid',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Relevant Static setpoints for Mexico: 20 for heating and 25 for cooling',
                1: 'Oropeza Arid Model Adaptive setpoints when applicable, otherwise Relevant Static setpoints for Mexico',
                2: 'Oropeza Arid Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Oropeza Arid Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        18: {
            'name': '18 = MEX Oropeza DryTropic',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Relevant Static setpoints for Mexico: 20 for heating and 25 for cooling',
                1: 'Oropeza DryTropic Model Adaptive setpoints when applicable, otherwise Relevant Static setpoints for Mexico',
                2: 'Oropeza DryTropic Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Oropeza DryTropic Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        19: {
            'name': '19 = MEX Oropeza Temperate',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Relevant Static setpoints for Mexico: 20 for heating and 25 for cooling',
                1: 'Oropeza Temperate Model Adaptive setpoints when applicable, otherwise Relevant Static setpoints for Mexico',
                2: 'Oropeza Temperate Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Oropeza Temperate Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        20: {
            'name': '20 = MEX Oropeza HumTropic',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                0: 'Relevant Static setpoints for Mexico: 20 for heating and 25 for cooling',
                1: 'Oropeza HumTropic Model Adaptive setpoints when applicable, otherwise Relevant Static setpoints for Mexico',
                2: 'Oropeza HumTropic Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Oropeza HumTropic Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },
        21: {
            'name': '21 = CHL Perez-Fargallo',
            'CAT': {
                80: '80% acceptability',
                90: '90% acceptability',
            },
            'ComfMod': {
                2: 'Perez-Fargallo Model Adaptive setpoints when applicable, otherwise ISO 7730 Static setpoints',
                3: 'Perez-Fargallo Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },

    }

    print('The information you will be required to enter below will be used to generate the customised output IDFs:')
    fullComfStandList = list(range(len(CS_CA_CM_list_dict)))
    self.ComfStand_List = list(int(num) for num in input(
        'Enter the Comfort Standard numbers separated by space (\n'
        '0 = ESP CTE;\n'
        '1 = INT EN16798-1;\n'
        '2 = INT ASHRAE55;\n'
        '3 = JPN Rijal;\n'
        '4 = CHN GBT50785 Cold;\n'
        '5 = CHN GBT50785 HotMild;\n'
        '6 = CHN Yang;\n'
        '7 = IND IMAC C NV;\n'
        '8 = IND IMAC C MM;\n'
        '9 = IND IMAC R 7DRM;\n'
        '10 = IND IMAC R 30DRM;\n'
        '11 = IND Dhaka;\n'
        '12 = ROM Udrea;\n'
        '13 = AUS Williamson;\n'
        '14 = AUS DeDear;\n'
        '15 = BRA Rupp NV;\n'
        '16 = BRA Rupp AC;\n'
        '17 = MEX Oropeza Arid;\n'
        '18 = MEX Oropeza DryTropic;\n'
        '19 = MEX Oropeza Temperate;\n'
        '20 = MEX Oropeza HumTropic;\n'
        '21 = CHL Perez-Fargallo;\n'
        '): '
    ).split())
    while len(self.ComfStand_List) == 0 or not all(elem in fullComfStandList for elem in self.ComfStand_List):
        print('          Comfort Standard numbers are not correct. Please enter the numbers again.')
        self.ComfStand_List = list(
            int(num) for num in input("     Enter the Comfort Standard numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.ComfStand_List = list(
            int(num) for num in input("     Enter the Comfort Standard numbers separated by space: ").split())
        while len(self.ComfStand_List) == 0 or not all(elem in fullComfStandList for elem in self.ComfStand_List):
            print('          Comfort Standard numbers are not correct. Please enter the numbers again.')
            self.ComfStand_List = list(
                int(num) for num in input("     Enter the Comfort Standard numbers separated by space: ").split())

    for i in self.ComfStand_List:
        print('For the comfort standard ' + CS_CA_CM_data_dict[i]['name'] + ', the available categories you can choose are: ')
        for j in CS_CA_CM_data_dict[i]['CAT']:
            print(str(j) + ' = ' + CS_CA_CM_data_dict[i]['CAT'][j])

    fullCATlist = [1, 2, 3, 80, 85, 90]
    self.CAT_List = list(int(num) for num in input(
        "Enter the Category numbers separated by space (\n"
        "1 = CAT I;\n"
        "2 = CAT II;\n"
        "3 = CAT III;\n"
        "80 = 80% ACCEPT;\n"
        "85 = 85% ACCEPT;\n"
        "90 = 90% ACCEPT;\n"
        "Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png\n"
        "): ").split())
    while len(self.CAT_List) == 0 or not all(elem in fullCATlist for elem in self.CAT_List):
        print('          Category numbers are not correct. Please enter the numbers again.')
        self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.CAT_List = list(int(num) for num in input("     Enter the Category numbers separated by space: ").split())
        while len(self.CAT_List) == 0 or not all(elem in fullCATlist for elem in self.CAT_List):
            print('          Category numbers are not correct. Please enter the numbers again.')
            self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space: ").split())

    for i in self.ComfStand_List:
        print('For the comfort standard ' + CS_CA_CM_data_dict[i]['name'] + ', the available ComfMods you can choose are: ')
        for j in CS_CA_CM_data_dict[i]['ComfMod']:
            print(str(j) + ' = ' + CS_CA_CM_data_dict[i]['ComfMod'][j])

    fullComfModList = [0, 1, 2, 3]
    self.ComfMod_List = list(int(num) for num in input(
        "Enter the Comfort Mode numbers separated by space (\n"
        "0 = Static;\n"
        "1, 2, 3 = Adaptive;\n"
        "Please refer to the full list of setpoint temperatures at https://github.com/dsanchez-garcia/accim/blob/master/docs/images/full_table.png\n"
        "): ").split())
    while len(self.ComfMod_List) == 0 or not all(elem in fullComfModList for elem in self.ComfMod_List):
        print('          Comfort Mode numbers are not correct. Please enter the numbers again.')
        self.ComfMod_List = list(
            int(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.ComfMod_List = list(
            int(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())
        while len(self.ComfMod_List) == 0 or not all(elem in fullComfModList for elem in self.ComfMod_List):
            print('          Comfort Mode numbers are not correct. Please enter the numbers again.')
            self.ComfMod_List = list(
                int(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())

    if 'mm' in ScriptType.lower():
        fullHVACmodeList = [0, 1, 2]
        self.HVACmode_List = list(int(num) for num in input(
            "Enter the HVAC Mode numbers separated by space (\n"
            "0 = Fully Air-conditioned;\n"
            "1 = Naturally ventilated;\n"
            "2 = Mixed Mode;\n"
            "): ").split())
        while len(self.HVACmode_List) == 0 or not all(elem in fullHVACmodeList for elem in self.HVACmode_List):
            print('          HVACmode numbers are not correct. Please enter the numbers again.')
            self.HVACmode_List = list(
                int(num) for num in input("     Enter the HVACmode numbers separated by space: ").split())
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.HVACmode_List = list(
                int(num) for num in input("     Enter the HVACmode numbers separated by space: ").split())
            while len(self.HVACmode_List) == 0 or not all(elem in fullHVACmodeList for elem in self.HVACmode_List):
                print('          HVACmode numbers are not correct. Please enter the numbers again.')
                self.HVACmode_List = list(
                    int(num) for num in input("     Enter the HVACmode numbers separated by space: ").split())

        fullVentCtrlList = [0, 1, 2, 3]
        self.VentCtrl_List = list(int(num) for num in input(
            "Enter the Ventilation Control numbers separated by space (\n"
            "If HVACmode = 1:"
            "   0 = Ventilates above neutral temperature;\n"
            "   1 = Ventilates above upper comfort limit;\n"
            "If HVACmode = 2:\n"
            "   0 = Ventilates above neutral temperature and fully opens doors and windows;\n"
            "   1 = Ventilates above lower comfort limit and fully opens doors and windows;\n"
            "   2 = Ventilates above neutral temperature and opens doors and windows based on the customised venting opening factor;\n"
            "   3 = Ventilates above lower comfort limit and opens doors and windows based on the customised venting opening factor;\n"
            "): ").split())
        while len(self.VentCtrl_List) == 0 or not all(elem in fullVentCtrlList for elem in self.VentCtrl_List):
            print('          Ventilation Control numbers are not correct. Please enter the numbers again.')
            self.VentCtrl_List = list(
                int(num) for num in input("     Enter the Ventilation Control numbers separated by space: ").split())
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.VentCtrl_List = list(
                int(num) for num in input("     Enter the Ventilation Control numbers separated by space: ").split())
            while len(self.VentCtrl_List) == 0 or not all(elem in fullVentCtrlList for elem in self.VentCtrl_List):
                print('          Ventilation Control numbers are not correct. Please enter the numbers again.')
                self.VentCtrl_List = list(int(num) for num in input(
                    "     Enter the Ventilation Control numbers separated by space: ").split())

        if any([i in self.VentCtrl_List for i in [2, 3]]):
            self.MaxTempDiffVOF = float(input('Enter the maximum temperature difference number for Ventilation Opening Factor: '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.MaxTempDiffVOF = float(input('      Enter the maximum temperature difference number for Ventilation Opening Factor: '))
            self.MinTempDiffVOF = float(input('Enter the minimum temperature difference number for Ventilation Opening Factor: '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.MinTempDiffVOF = float(input('      Enter the minimum temperature difference number for Ventilation Opening Factor: '))
            self.MultiplierVOF = float(input('Enter the multiplier number for Ventilation Opening Factor: '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.MultiplierVOF = float(input('      Enter the multiplier number for Ventilation Opening Factor: '))

        self.VSToffset_List = list(float(num) for num in input(
            "Enter the VSToffset numbers separated by space (if omitted, will be 0): ").split())
        if len(self.VSToffset_List) == 0:
            self.VSToffset_List = [float(0)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.VSToffset_List = list(float(num) for num in input(
                "     Enter the VSToffset numbers separated by space (if omitted, will be 0): ").split())
            if len(self.VSToffset_List) == 0:
                self.VSToffset_List = [float(0)]

        self.MinOToffset_List = list(float(num) for num in input(
            "Enter the MinOToffset numbers separated by space (if omitted, will be 50): ").split())
        if len(self.MinOToffset_List) == 0:
            self.MinOToffset_List = [float(50)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.MinOToffset_List = list(float(num) for num in input(
                "     Enter the MinOToffset numbers separated by space (if omitted, will be 50): ").split())
            if len(self.MinOToffset_List) == 0:
                self.MinOToffset_List = [float(50)]

        self.MaxWindSpeed_List = list(float(num) for num in input(
            "Enter the MaxWindSpeed numbers separated by space (if omitted, will be 50): ").split())
        if len(self.MaxWindSpeed_List) == 0:
            self.MaxWindSpeed_List = [float(50)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.MaxWindSpeed_List = list(float(num) for num in input(
                "     Enter the MaxWindSpeed numbers separated by space (if omitted, will be 50): ").split())
            if len(self.MaxWindSpeed_List) == 0:
                self.MaxWindSpeed_List = [float(50)]
    elif 'ac' in ScriptType.lower():
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
           MaxTempDiffVOF=7.5,
           MinTempDiffVOF=0,
           MultiplierVOF=0,
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
                 MaxTempDiffVOF == 7.5,
                 MinTempDiffVOF == 0,
                 MultiplierVOF == 0,
                 VSToffset == [0],
                 MinOToffset == [50],
                 MaxWindSpeed == [50],
                 ASTtol_start == 0.1,
                 ASTtol_end_input == 0.1,
                 ASTtol_steps == 0.1)
    if all(arguments):
        self.ASTtol_value_to = self.ASTtol_value_to_input + self.ASTtol_value_steps
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
        self.MaxTempDiffVOF = MaxTempDiffVOF,
        self.MinTempDiffVOF = MinTempDiffVOF,
        self.MultiplierVOF = MultiplierVOF,
        self.VSToffset_List = VSToffset
        self.MinOToffset_List = MinOToffset
        self.MaxWindSpeed_List = MaxWindSpeed
        self.ASTtol_value_from = round(ASTtol_start, 2)
        self.ASTtol_value_to = round(ASTtol_end, 2)
        self.ASTtol_value_steps = round(ASTtol_steps, 2)

    if 'ac' in ScriptType.lower():
        self.HVACmode_List = [0]
        self.VentCtrl_List = [0]
        self.MaxTempDiffVOF = 1,
        self.MinTempDiffVOF = 0,
        self.MultiplierVOF = 0,
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
    }

    outputlist = []
    for file in filelist_pymod:
        filename = file.replace('_pymod', '')
        if TempCtrl.lower() == 'temp' or TempCtrl.lower() == 'temperature':
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
                                if HVACmode_value == 1:
                                    if VentCtrl_value == 2 or VentCtrl_value == 3:
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
                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                                         self.ASTtol_value_steps):
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
                                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                         self.ASTtol_value_to,
                                                                                         self.ASTtol_value_steps):
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
                elif ComfStand_value in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]:
                    for CAT_value in self.CAT_List:
                        if ComfStand_value in [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                               20, 21] and CAT_value not in range(80, 91, 10):
                            continue
                        elif ComfStand_value in [7, 8] and CAT_value not in range(80, 91, 5):
                            continue
                        else:
                            for ComfMod_value in self.ComfMod_List:
                                for HVACmode_value in self.HVACmode_List:
                                    if HVACmode_value == 0:
                                        for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                                         self.ASTtol_value_steps):
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
                                            if HVACmode_value == 1:
                                                if VentCtrl_value == 2 or VentCtrl_value == 3:
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

            fname1 = filename + '.idf'

            filename = file.replace('_pymod', '')
            # if verboseMode:
            #     print(f'Taking "{fname1}" as input IDF file:')
            idf1 = IDF(fname1)

            # print(filename)
            SetInputData = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetInputData'])
            SetVOFinputData = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetVOFinputData'])
            if TempCtrl.lower() == 'temp' or TempCtrl.lower() == 'temperature':
                for ComfStand_value in self.ComfStand_List:
                    SetInputData[0].Program_Line_1 = 'set ComfStand = ' + repr(ComfStand_value)
                    if ComfStand_value == 0:
                        SetInputData[0].Program_Line_2 = 'set CAT = 1'
                        SetInputData[0].Program_Line_3 = 'set ComfMod = 0'
                        for HVACmode_value in self.HVACmode_List:
                            SetInputData[0].Program_Line_4 = 'set HVACmode = ' + repr(HVACmode_value)
                            if HVACmode_value == 0:
                                for ASTtol_value in numpy.arange(self.ASTtol_value_from, self.ASTtol_value_to,
                                                                 self.ASTtol_value_steps):
                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
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
                                    if HVACmode_value == 1:
                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                            continue
                                    else:
                                        SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl_value)
                                        SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(self.MaxTempDiffVOF[0])
                                        SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + repr(self.MinTempDiffVOF[0])
                                        SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + repr(self.MultiplierVOF[0])
                                    for VSToffset_value in self.VSToffset_List:
                                        SetInputData[0].Program_Line_6 = 'set VSToffset = ' + repr(VSToffset_value)
                                        for MinOToffset_value in self.MinOToffset_List:
                                            SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + repr(
                                                MinOToffset_value)
                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = ' + repr(
                                                    MaxWindSpeed_value)
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(
                                                        -ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(
                                                        ASTtol_value)
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
                                SetInputData[0].Program_Line_2 = 'set CAT = ' + repr(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    SetInputData[0].Program_Line_3 = 'set ComfMod = ' + repr(ComfMod_value)
                                    for HVACmode_value in self.HVACmode_List:
                                        SetInputData[0].Program_Line_4 = 'set HVACmode = ' + repr(HVACmode_value)
                                        if HVACmode_value == 0:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                             self.ASTtol_value_to,
                                                                             self.ASTtol_value_steps):
                                                SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
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
                                                if HVACmode_value == 1:
                                                    if VentCtrl_value == 2 or VentCtrl_value == 3:
                                                        continue
                                                else:
                                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl_value)
                                                    SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(self.MaxTempDiffVOF[0])
                                                    SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + repr(self.MinTempDiffVOF[0])
                                                    SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + repr(self.MultiplierVOF[0])
                                                for VSToffset_value in self.VSToffset_List:
                                                    SetInputData[0].Program_Line_6 = 'set VSToffset = ' + repr(
                                                        VSToffset_value)
                                                    for MinOToffset_value in self.MinOToffset_List:
                                                        SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + repr(
                                                            MinOToffset_value)
                                                        for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                            SetInputData[
                                                                0].Program_Line_8 = 'set MaxWindSpeed = ' + repr(
                                                                MaxWindSpeed_value)
                                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                             self.ASTtol_value_to,
                                                                                             self.ASTtol_value_steps):
                                                                SetInputData[
                                                                    0].Program_Line_9 = 'set ACSTtol = ' + repr(
                                                                    -ASTtol_value)
                                                                SetInputData[
                                                                    0].Program_Line_10 = 'set AHSTtol = ' + repr(
                                                                    ASTtol_value)
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
                    elif ComfStand_value in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]:
                        for CAT_value in self.CAT_List:
                            if ComfStand_value in [2, 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                                   20, 21] and CAT_value not in range(80, 91, 10):
                                continue
                            elif ComfStand_value in [7, 8] and CAT_value not in range(80, 91, 5):
                                continue
                            else:
                                SetInputData[0].Program_Line_2 = 'set CAT = ' + repr(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    SetInputData[0].Program_Line_3 = 'set ComfMod = ' + repr(ComfMod_value)
                                    for HVACmode_value in self.HVACmode_List:
                                        SetInputData[0].Program_Line_4 = 'set HVACmode = ' + repr(HVACmode_value)
                                        if HVACmode_value == 0:
                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                             self.ASTtol_value_to,
                                                                             self.ASTtol_value_steps):
                                                SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
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
                                                if HVACmode_value == 1:
                                                    if VentCtrl_value == 2 or VentCtrl_value == 3:
                                                        continue
                                                else:
                                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl_value)
                                                    SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(self.MaxTempDiffVOF[0])
                                                    SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + repr(self.MinTempDiffVOF[0])
                                                    SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + repr(self.MultiplierVOF[0])
                                                for VSToffset_value in self.VSToffset_List:
                                                    SetInputData[0].Program_Line_6 = 'set VSToffset = ' + repr(
                                                        VSToffset_value)
                                                    for MinOToffset_value in self.MinOToffset_List:
                                                        SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + repr(
                                                            MinOToffset_value)
                                                        for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                            SetInputData[
                                                                0].Program_Line_8 = 'set MaxWindSpeed = ' + repr(
                                                                MaxWindSpeed_value)
                                                            for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                             self.ASTtol_value_to,
                                                                                             self.ASTtol_value_steps):
                                                                SetInputData[
                                                                    0].Program_Line_9 = 'set ACSTtol = ' + repr(
                                                                    -ASTtol_value)
                                                                SetInputData[
                                                                    0].Program_Line_10 = 'set AHSTtol = ' + repr(
                                                                    ASTtol_value)
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
