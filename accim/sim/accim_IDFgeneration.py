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
        '13 = AUS Williamson': [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        '14 = AUS DeDear': [[80, 90], [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]],
        '15 = BRA Rupp NV': [[80, 90], [0, 1, 2, 3]],
        '16 = BRA Rupp AC': [[80, 90], [0, 1, 2, 3]],
        '17 = MEX Oropeza Arid': [[80, 90], [0, 1, 2, 3]],
        '18 = MEX Oropeza DryTropic': [[80, 90], [0, 1, 2, 3]],
        '19 = MEX Oropeza Temperate': [[80, 90], [0, 1, 2, 3]],
        '20 = MEX Oropeza HumTropic': [[80, 90], [0, 1, 2, 3]],
        '21 = CHL Perez-Fargallo': [[80, 90], [2, 3]],
        '22 = INT ISO7730': [[1, 2, 3], [0]],

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
                0: 'ISO 7730 Static setpoints',
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
                0.1: 'Australian Building Code Static setpoints for climate zones 1, 2 and 3',
                0.2: 'Australian Building Code Static setpoints for climate zone 4',
                0.3: 'Australian Building Code Static setpoints for climate zone 5',
                0.4: 'Australian Building Code Static setpoints for climate zones 6 and 7',
                0.5: 'Australian Building Code Static setpoints for climate zone 8',
                1.1: 'Williamson Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zones 1, 2 and 3',
                1.2: 'Williamson Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zone 4',
                1.3: 'Williamson Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zone 5',
                1.4: 'Williamson Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zones 6 and 7',
                1.5: 'Williamson Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zone 8',
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
                0.1: 'Australian Building Code Static setpoints for climate zones 1, 2 and 3',
                0.2: 'Australian Building Code Static setpoints for climate zone 4',
                0.3: 'Australian Building Code Static setpoints for climate zone 5',
                0.4: 'Australian Building Code Static setpoints for climate zones 6 and 7',
                0.5: 'Australian Building Code Static setpoints for climate zone 8',
                1.1: 'DeDear Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zones 1, 2 and 3',
                1.2: 'DeDear Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zone 4',
                1.3: 'DeDear Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zone 5',
                1.4: 'DeDear Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zones 6 and 7',
                1.5: 'DeDear Model Adaptive setpoints when applicable, otherwise Australian Building Code Static setpoints for climate zone 8',
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
        22: {
            'name': '22 = INT ISO7730',
            'CAT': {
                1: 'Cat A: -0.2 < PMV < 0.2; PPD < 6%',
                2: 'Cat B: -0.5 < PMV < 0.5; PPD < 10%',
                3: 'Cat C: -0.7 < PMV < 0.7; PPD < 15%',
            },
            'ComfMod': {
                0: 'ISO 7730 Static setpoints',
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
        '22 = INT ISO7730;\n'
        'Please refer to the full list of setpoint temperatures at https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html\n'
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
    print('\n')
    for i in self.ComfStand_List:
        print('For the comfort standard ' + CS_CA_CM_data_dict[i]['name'] + ', the available categories you can choose are: ')
        for j in CS_CA_CM_data_dict[i]['CAT']:
            print(str(j) + ' = ' + CS_CA_CM_data_dict[i]['CAT'][j])

    fullCATlist = [1, 2, 3, 80, 85, 90]
    self.CAT_List = list(int(num) for num in input(
        "Enter the Category numbers separated by space (\n"
        "1 = CAT I / CAT A;\n"
        "2 = CAT II / CAT B;\n"
        "3 = CAT III / CAT C;\n"
        "80 = 80% ACCEPT;\n"
        "85 = 85% ACCEPT;\n"
        "90 = 90% ACCEPT;\n"
        "Please refer to the full list of setpoint temperatures at https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html\n"
        "): ").split())
    while len(self.CAT_List) == 0 or not all(elem in fullCATlist for elem in self.CAT_List):
        print('          Category numbers are not correct. Please enter the numbers again.')
        self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.CAT_List = list(int(num) for num in input("     Enter the Category numbers separated by space: ").split())
        while len(self.CAT_List) == 0 or not all(elem in fullCATlist for elem in self.CAT_List):
            print('          Category numbers are not correct. Please enter the numbers again.')
            self.CAT_List = list(int(num) for num in input("Enter the Category numbers separated by space: ").split())
    print('\n')
    for i in self.ComfStand_List:
        print('For the comfort standard ' + CS_CA_CM_data_dict[i]['name'] + ', the available ComfMods you can choose are: ')
        for j in CS_CA_CM_data_dict[i]['ComfMod']:
            print(str(j) + ' = ' + CS_CA_CM_data_dict[i]['ComfMod'][j])

    fullComfModList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 2, 3]
    self.ComfMod_List = list(float(num) for num in input(
        "Enter the Comfort Mode numbers separated by space (\n"
        # "0 = Static;\n"
        # "1, 2, 3 = Adaptive;\n"
        "Please refer to the full list of setpoint temperatures at https://raw.githack.com/dsanchez-garcia/accim/master/docs/full_setpoint_table.html\n"
        "): ").split())
    while len(self.ComfMod_List) == 0 or not all(elem in fullComfModList for elem in self.ComfMod_List):
        print('          Comfort Mode numbers are not correct. Please enter the numbers again.')
        self.ComfMod_List = list(
            float(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())
    while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
        self.ComfMod_List = list(
            float(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())
        while len(self.ComfMod_List) == 0 or not all(elem in fullComfModList for elem in self.ComfMod_List):
            print('          Comfort Mode numbers are not correct. Please enter the numbers again.')
            self.ComfMod_List = list(
                float(num) for num in input("     Enter the Comfort Mode numbers separated by space: ").split())

    self.SetpointAcc = float(input('Enter the setpoint accuracy number (any number greater than 0): '))
    while self.SetpointAcc < 0:
        print('          The setpoint accuracy number is not correct. It must be a number greater than 0. Please enter the number again.')
        self.SetpointAcc = float(input('         Enter the setpoint accuracy number (any number greater than 0): '))
    while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
        self.SetpointAcc = float(input('      Enter the setpoint accuracy number (any number greater than 0): '))
        while self.SetpointAcc < 0 or self.SetpointAcc > 1:
            print('          The setpoint accuracy number is not correct. It must be a number greater than 0. Please enter the number again.')
            self.SetpointAcc = float(input('         Enter the setpoint accuracy number (any number greater than 0): '))

    if (any(i in [1, 2] for i in self.ComfStand_List) and 0 in self.ComfMod_List) or 22 in self.ComfStand_List:
        self.CoolSeasonStart = list(
            int(num)
            for num
            in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
        )
        if len(self.CoolSeasonStart) == 1:
            day_of_year = self.CoolSeasonStart[0]
        elif len(self.CoolSeasonStart) == 2:
            from datetime import date
            day_of_year = date(2007, self.CoolSeasonStart[1], self.CoolSeasonStart[0]).timetuple().tm_yday
        while day_of_year < 1 or day_of_year > 365:
            print('          The start for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
            self.CoolSeasonStart = list(
                int(num)
                for num
                in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.CoolSeasonStart = list(
                int(num)
                for num
                in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
            if len(self.CoolSeasonStart) == 1:
                day_of_year = self.CoolSeasonStart[0]
            elif len(self.CoolSeasonStart) == 2:
                day_of_year = date(2007, self.CoolSeasonStart[1], self.CoolSeasonStart[0]).timetuple().tm_yday
            while day_of_year < 1 or day_of_year > 365:
                print('          The start for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
                self.CoolSeasonStart = list(
                    int(num)
                    for num
                    in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
                )
                if len(self.CoolSeasonStart) == 1:
                    day_of_year = self.CoolSeasonStart[0]
                elif len(self.CoolSeasonStart) == 2:
                    day_of_year = date(2007, self.CoolSeasonStart[1], self.CoolSeasonStart[0]).timetuple().tm_yday
        self.CoolSeasonStart = day_of_year

        self.CoolSeasonEnd = list(
            int(num)
            for num
            in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
        )
        if len(self.CoolSeasonEnd) == 1:
            day_of_year = self.CoolSeasonEnd[0]
        elif len(self.CoolSeasonEnd) == 2:
            from datetime import date
            day_of_year = date(2007, self.CoolSeasonEnd[1], self.CoolSeasonEnd[0]).timetuple().tm_yday
        while day_of_year < 1 or day_of_year > 365:
            print('          The end for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
            self.CoolSeasonEnd = list(
                int(num)
                for num
                in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.CoolSeasonEnd = list(
                int(num)
                for num
                in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
            if len(self.CoolSeasonEnd) == 1:
                day_of_year = self.CoolSeasonEnd[0]
            elif len(self.CoolSeasonEnd) == 2:
                day_of_year = date(2007, self.CoolSeasonEnd[1], self.CoolSeasonEnd[0]).timetuple().tm_yday
            while day_of_year < 1 or day_of_year > 365:
                print('          The end for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
                self.CoolSeasonEnd = list(
                    int(num)
                    for num
                    in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
                )
                if len(self.CoolSeasonEnd) == 1:
                    day_of_year = self.CoolSeasonEnd[0]
                elif len(self.CoolSeasonEnd) == 2:
                    day_of_year = date(2007, self.CoolSeasonEnd[1], self.CoolSeasonEnd[0]).timetuple().tm_yday
        self.CoolSeasonEnd = day_of_year
    else:
        self.CoolSeasonStart = 121
        self.CoolSeasonEnd = 274

    if 'mm' in ScriptType.lower():
        fullHVACmodeList = [0, 1, 2]
        self.HVACmode_List = list(int(num) for num in input(
            "\nEnter the HVAC Mode numbers separated by space (\n"
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
            "\nEnter the Ventilation Control numbers separated by space (\n"
            "If HVACmode = 1:\n"
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
            self.MaxTempDiffVOF = float(input('Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
            while self.MaxTempDiffVOF <= 0:
                print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                self.MaxTempDiffVOF = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.MaxTempDiffVOF = float(input('      Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                while self.MaxTempDiffVOF <= 0:
                    print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                    self.MaxTempDiffVOF = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))

            self.MinTempDiffVOF = float(input('Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
            while self.MinTempDiffVOF <= 0:
                print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                self.MinTempDiffVOF = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.MinTempDiffVOF = float(input('      Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                while self.MinTempDiffVOF <= 0:
                    print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                    self.MinTempDiffVOF = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))

            while self.MinTempDiffVOF >= self.MaxTempDiffVOF:
                print('The minimum temperature difference number you entered is larger than or equal to the maximum temperature difference number. Please enter both maximum and minimum temperature difference numbers again.')
                self.MaxTempDiffVOF = float(input('Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                while self.MaxTempDiffVOF <= 0:
                    print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                    self.MaxTempDiffVOF = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                    self.MaxTempDiffVOF = float(input('      Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                    while self.MaxTempDiffVOF <= 0:
                        print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                        self.MaxTempDiffVOF = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))

                self.MinTempDiffVOF = float(input('Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                while self.MinTempDiffVOF <= 0:
                    print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                    self.MinTempDiffVOF = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                    self.MinTempDiffVOF = float(input('      Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                    while self.MinTempDiffVOF <= 0:
                        print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                        self.MinTempDiffVOF = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))

            self.MultiplierVOF = float(input('Enter the multiplier number for Ventilation Opening Factor (any number between 0 and 1): '))
            while self.MultiplierVOF < 0 or self.MultiplierVOF > 1:
                print('          The multiplier number is not correct. It must be a number between 0 and 1. Please enter the number again.')
                self.MultiplierVOF = float(input('         Enter the multiplier number for modulating the Ventilation Opening Factor (any number between 0 and 1): '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.MultiplierVOF = float(input('      Enter the multiplier number for modulating the Ventilation Opening Factor (any number between 0 and 1): '))
                while self.MultiplierVOF < 0 or self.MultiplierVOF > 1:
                    print('          The multiplier number is not correct. It must be a number between 0 and 1. Please enter the number again.')
                    self.MultiplierVOF = float(input('         Enter the multiplier number for modulating the Ventilation Opening Factor (any number between 0 and 1): '))

        self.VSToffset_List = list(float(num) for num in input(
            "\nEnter the VSToffset numbers separated by space (if omitted, will be 0): ").split())
        if len(self.VSToffset_List) == 0:
            self.VSToffset_List = [float(0)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.VSToffset_List = list(float(num) for num in input(
                "     Enter the VSToffset numbers separated by space (if omitted, will be 0): ").split())
            if len(self.VSToffset_List) == 0:
                self.VSToffset_List = [float(0)]

        self.MinOToffset_List = list(float(num) for num in input(
            "\nEnter the MinOToffset numbers separated by space (if omitted, will be 50): ").split())
        if len(self.MinOToffset_List) == 0:
            self.MinOToffset_List = [float(50)]
        while input('          Are you sure the numbers are correct? [y or [] / n]: ') == 'n':
            self.MinOToffset_List = list(float(num) for num in input(
                "     Enter the MinOToffset numbers separated by space (if omitted, will be 50): ").split())
            if len(self.MinOToffset_List) == 0:
                self.MinOToffset_List = [float(50)]

        self.MaxWindSpeed_List = list(float(num) for num in input(
            "\nEnter the MaxWindSpeed numbers separated by space (if omitted, will be 50): ").split())
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
        self.MaxTempDiffVOF = 1
        self.MinTempDiffVOF = 0
        self.MultiplierVOF = 0
        self.VSToffset_List = [0]
        self.MinOToffset_List = [0]
        self.MaxWindSpeed_List = [0]

    try:
        self.ASTtol_value_from = float(input('\nEnter the ASTtol value from (if omitted, will be 0.1): '))
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
           SetpointAcc=10000,
           CoolSeasonStart=121,
           CoolSeasonEnd=274,
           HVACmode=None,
           VentCtrl=None,
           MaxTempDiffVOF=20,
           MinTempDiffVOF=0.5,
           MultiplierVOF=0.25,
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
                 SetpointAcc == 10000,
                 CoolSeasonStart == 121,
                 CoolSeasonEnd == 274,
                 HVACmode is None,
                 VentCtrl is None,
                 MaxTempDiffVOF == 20,
                 MinTempDiffVOF == 0.5,
                 MultiplierVOF == 0.25,
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
        self.SetpointAcc = SetpointAcc
        
        if type(CoolSeasonStart) is str:
            CoolSeasonStart = list(int(num) for num in CoolSeasonStart.split('/'))
            from datetime import date
            day_of_year = date(2007, CoolSeasonStart[1], CoolSeasonStart[0]).timetuple().tm_yday
        elif type(CoolSeasonStart) is int:
            day_of_year = CoolSeasonStart
        self.CoolSeasonStart = day_of_year
        
        # CoolSeasonEnd = list(int(num) for num in CoolSeasonEnd.split('/'))
        # if len(CoolSeasonEnd) == 1:
        #     day_of_year = CoolSeasonEnd[0]
        # elif len(CoolSeasonEnd) == 2:
        #     from datetime import date
        #     day_of_year = date(2007, CoolSeasonEnd[1], CoolSeasonEnd[0]).timetuple().tm_yday
        # self.CoolSeasonEnd = day_of_year
        if type(CoolSeasonEnd) is str:
            CoolSeasonEnd = list(int(num) for num in CoolSeasonEnd.split('/'))
            from datetime import date
            day_of_year = date(2007, CoolSeasonEnd[1], CoolSeasonEnd[0]).timetuple().tm_yday
        elif type(CoolSeasonEnd) is int:
            day_of_year = CoolSeasonEnd
        self.CoolSeasonEnd = day_of_year

        
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

    if any([i in self.VentCtrl_List for i in [2, 3]]):
        if type(self.MaxTempDiffVOF) is tuple:
            self.MaxTempDiffVOF = self.MaxTempDiffVOF[0]
        if type(self.MinTempDiffVOF) is tuple:
            self.MinTempDiffVOF = self.MinTempDiffVOF[0]
        if type(self.MultiplierVOF) is tuple:
            self.MultiplierVOF = self.MultiplierVOF[0]

    self.VSToffset_List = [float(i) for i in self.VSToffset_List]
    self.MinOToffset_List = [float(i) for i in self.MinOToffset_List]
    self.MaxWindSpeed_List = [float(i) for i in self.MaxWindSpeed_List]

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
        22: '[CS_INT ISO7730',
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
                                        + '[AT_' + repr(round(ASTtol_value, 2))
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
                                                            + '[HM_' + repr(HVACmode_value)
                                                            + '[VC_' + repr(VentCtrl_value)
                                                            + '[VO_' + repr(VSToffset_value)
                                                            + '[MT_' + repr(MinOToffset_value)
                                                            + '[MW_' + repr(MaxWindSpeed_value)
                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
                                else:
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
                                                        + '[AT_' + repr(round(ASTtol_value, 2))
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
                                                                            + '[CA_' + repr(CAT_value)
                                                                            + '[CM_' + repr(ComfMod_value)
                                                                            + '[HM_' + repr(HVACmode_value)
                                                                            + '[VC_' + repr(VentCtrl_value)
                                                                            + '[VO_' + repr(VSToffset_value)
                                                                            + '[MT_' + repr(MinOToffset_value)
                                                                            + '[MW_' + repr(MaxWindSpeed_value)
                                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
                                if ComfStand_value in [13, 14] and ComfMod_value in [0, 1]:
                                    continue
                                elif ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                    continue
                                else:
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
                                                        + '[AT_' + repr(round(ASTtol_value, 2))
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
                                                                            + '[CA_' + repr(CAT_value)
                                                                            + '[CM_' + repr(ComfMod_value)
                                                                            + '[HM_' + repr(HVACmode_value)
                                                                            + '[VC_' + repr(VentCtrl_value)
                                                                            + '[VO_' + repr(VSToffset_value)
                                                                            + '[MT_' + repr(MinOToffset_value)
                                                                            + '[MW_' + repr(MaxWindSpeed_value)
                                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
            SetAST = ([program for program in idf1.idfobjects['EnergyManagementSystem:Program'] if
                             program.Name == 'SetAST'])
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
                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + repr(self.CoolSeasonStart)
                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + repr(self.CoolSeasonEnd)
                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + repr(self.SetpointAcc)
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
                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl_value)
                                    if HVACmode_value == 2:
                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                            SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(self.MaxTempDiffVOF)
                                            SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + repr(self.MinTempDiffVOF)
                                            SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + repr(self.MultiplierVOF)
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
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + repr(self.CoolSeasonStart)
                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + repr(self.CoolSeasonEnd)
                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + repr(self.SetpointAcc)
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
                                                            + '[AT_' + repr(round(ASTtol_value, 2))
                                                            + suffix
                                                            + '.idf'
                                                    )
                                                    if verboseMode:
                                                        print(outputname)
                                                        # time.sleep(0.1)
                                                        # pbar.update(1)
                                                    idf1.savecopy(outputname)
                    elif ComfStand_value in [1, 4, 5, 22]:
                        for CAT_value in self.CAT_List:
                            if ComfStand_value in [1, 22] and CAT_value not in range(0, 4):
                                continue
                            elif ComfStand_value in [4, 5] and CAT_value not in [1, 2]:
                                continue
                            else:
                                SetInputData[0].Program_Line_2 = 'set CAT = ' + repr(CAT_value)
                                for ComfMod_value in self.ComfMod_List:
                                    if ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                        continue
                                    else:
                                        SetInputData[0].Program_Line_3 = 'set ComfMod = ' + repr(ComfMod_value)
                                        for HVACmode_value in self.HVACmode_List:
                                            SetInputData[0].Program_Line_4 = 'set HVACmode = ' + repr(HVACmode_value)
                                            if HVACmode_value == 0:
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + repr(self.CoolSeasonStart)
                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + repr(self.CoolSeasonEnd)
                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + repr(self.SetpointAcc)
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
                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
                                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl_value)
                                                    if HVACmode_value == 2:
                                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                                            SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(self.MaxTempDiffVOF)
                                                            SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + repr(self.MinTempDiffVOF)
                                                            SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + repr(self.MultiplierVOF)
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
                                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
                                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + repr(self.CoolSeasonStart)
                                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + repr(self.CoolSeasonEnd)
                                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + repr(self.SetpointAcc)
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
                                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
                                    if ComfStand_value in [13, 14] and ComfMod_value in [0, 1]:
                                        continue
                                    elif ComfStand_value not in [13, 14] and ComfMod_value in [0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 1.4, 1.5]:
                                        continue
                                    else:
                                        SetInputData[0].Program_Line_3 = 'set ComfMod = ' + repr(ComfMod_value)
                                        for HVACmode_value in self.HVACmode_List:
                                            SetInputData[0].Program_Line_4 = 'set HVACmode = ' + repr(HVACmode_value)
                                            if HVACmode_value == 0:
                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                 self.ASTtol_value_to,
                                                                                 self.ASTtol_value_steps):
                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + repr(self.CoolSeasonStart)
                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + repr(self.CoolSeasonEnd)
                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + repr(self.SetpointAcc)
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
                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
                                                    SetInputData[0].Program_Line_5 = 'set VentCtrl = ' + repr(VentCtrl_value)
                                                    if HVACmode_value == 2:
                                                        if VentCtrl_value == 2 or VentCtrl_value == 3:
                                                            SetVOFinputData[0].Program_Line_1 = 'set MaxTempDiffVOF = ' + repr(self.MaxTempDiffVOF)
                                                            SetVOFinputData[0].Program_Line_2 = 'set MinTempDiffVOF = ' + repr(self.MinTempDiffVOF)
                                                            SetVOFinputData[0].Program_Line_3 = 'set MultiplierVOF = ' + repr(self.MultiplierVOF)
                                                    for VSToffset_value in self.VSToffset_List:
                                                        SetInputData[0].Program_Line_6 = 'set VSToffset = ' + repr(
                                                            VSToffset_value)
                                                        for MinOToffset_value in self.MinOToffset_List:
                                                            SetInputData[0].Program_Line_7 = 'set MinOToffset = ' + repr(
                                                                MinOToffset_value)
                                                            for MaxWindSpeed_value in self.MaxWindSpeed_List:
                                                                SetInputData[0].Program_Line_8 = 'set MaxWindSpeed = ' + repr(MaxWindSpeed_value)
                                                                for ASTtol_value in numpy.arange(self.ASTtol_value_from,
                                                                                                 self.ASTtol_value_to,
                                                                                                 self.ASTtol_value_steps):
                                                                    SetInputData[0].Program_Line_9 = 'set ACSTtol = ' + repr(-ASTtol_value)
                                                                    SetInputData[0].Program_Line_10 = 'set AHSTtol = ' + repr(ASTtol_value)
                                                                    SetInputData[0].Program_Line_11 = 'set CoolSeasonStart = ' + repr(self.CoolSeasonStart)
                                                                    SetInputData[0].Program_Line_12 = 'set CoolSeasonEnd = ' + repr(self.CoolSeasonEnd)
                                                                    SetAST[0].Program_Line_1 = 'set SetpointAcc = ' + repr(self.SetpointAcc)
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
                                                                            + '[AT_' + repr(round(ASTtol_value, 2))
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
