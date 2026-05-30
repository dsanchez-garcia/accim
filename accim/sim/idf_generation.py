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


def input_data(self, script_type: str = None):
    """Input data for IDF generation.

    :param self: Used as a method for class ``accim.sim.accim_Main.AccimJob``
    :param ScriptType: Inherited from class ``accim.sim.accis.addAccis``
    """
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
        '99 = CUSTOM': [['n/a'], [3]],
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
        99: {
            'name': '99 = CUSTOM',
            'CAT': {
                'n/a': 'n/a'
            },
            'ComfMod': {
                3: 'Custom Model Adaptive setpoints when applicable, otherwise Adaptive setpoints horizontally extended',
            }
        },

    }

    print('The information you will be required to enter below will be used to generate the customised output IDFs:')
    fullComfStandList = list(range(len(CS_CA_CM_list_dict)-1))
    fullComfStandList.append(99)
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
        '99 = CUSTOM;\n'
        'Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html\n'
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
    if 99 in self.ComfStand_List:
        print('\nYou have requested the use of a custom comfort model. Please enter the following data necessary to build the custom comfort model:')

        self.custom_ast_m = float(input('\nEnter the m coefficient (slope) of comfort model linear regression (mx+n) (any number greater than 0): '))
        while self.custom_ast_m < 0:
            print(f'          The number you entered for CustAST_m is {self.custom_ast_m}, which is smaller than 0, and that is not allowed. ')
            self.custom_ast_m = float(input('          Enter the m coefficient (slope) of comfort model linear regression (mx+n) (any number greater than 0): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_m = float(input('          Enter the m coefficient (slope) of comfort model linear regression (mx+n) (any number greater than 0): '))

        self.custom_ast_n = float(input('\nEnter the n coefficient of comfort model linear regression (mx+n): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_n = float(input('          Enter the n coefficient of comfort model linear regression (mx+n): '))

        self.custom_ast_ahst_offset = float(input('\nEnter the offset from neutral temperature for the heating setpoint (value will be summed, therefore, it should be negative): '))
        while self.custom_ast_ahst_offset > 0:
            print(f'          The number you entered for CustAST_AHSToffset is {self.custom_ast_ahst_offset}, which is larger than 0, and that is not allowed. ')
            self.custom_ast_ahst_offset = float(input('          Enter the offset from neutral temperature for the heating setpoint (value will be summed, therefore, it should be negative): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_ahst_offset = float(input('          Enter the offset from neutral temperature for the heating setpoint (value will be summed, therefore, it should be negative): '))

        self.custom_ast_acst_offset = float(input('\nEnter the offset from neutral temperature for the cooling setpoint (value will be summed, therefore, it should be positive): '))
        while self.custom_ast_acst_offset < 0:
            print(f'          The number you entered for CustAST_ACSToffset is {self.custom_ast_acst_offset}, which is smaller than 0, and that is not allowed. ')
            self.custom_ast_acst_offset = float(input('          Enter the offset from neutral temperature for the cooling setpoint (value will be summed, therefore, it should be positive): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_acst_offset = float(input('          Enter the offset from neutral temperature for the cooling setpoint (value will be summed, therefore, it should be positive): '))

        self.custom_ast_acst_all = float(input('\nEnter the value for the cooling setpoint applicability lower limit (ACSTall): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_acst_all = float(input('          Enter the value for the cooling setpoint applicability lower limit (ACSTall): '))

        self.custom_ast_acst_aul = float(input('\nEnter the value for the cooling setpoint applicability upper limit (ACSTaul): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_acst_aul = float(input('          Enter the value for the cooling setpoint applicability upper limit (ACSTaul): '))

        self.custom_ast_ahst_all = float(
            input('\nEnter the value for the heating setpoint applicability lower limit (ACSTall): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_ahst_all = float(input('          Enter the value for the heating setpoint applicability lower limit (AHSTall): '))

        self.custom_ast_ahst_aul = float(
            input('\nEnter the value for the heating setpoint applicability upper limit (ACSTall): '))
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.custom_ast_ahst_aul = float(input('          Enter the value for the heating setpoint applicability upper limit (AHSTaul): '))
    else:
        self.custom_ast_m = 0
        self.custom_ast_n = 0
        self.custom_ast_ahst_offset = 0
        self.custom_ast_acst_offset = 0
        self.custom_ast_acst_all = 0
        self.custom_ast_acst_aul = 0
        self.custom_ast_ahst_all = 0
        self.custom_ast_ahst_aul = 0

    print('\n')
    for i in self.ComfStand_List:
        print('For the comfort standard ' + CS_CA_CM_data_dict[i]['name'] + ', the available categories you can choose are: ')
        for j in CS_CA_CM_data_dict[i]['CAT']:
            print(str(j) + ' = ' + CS_CA_CM_data_dict[i]['CAT'][j])

    fullCATlist = [1, 2, 3, 80, 85, 90]
    availableCATlist = []
    for i in self.ComfStand_List:
        availableCATlist.extend([j for j in CS_CA_CM_data_dict[i]['CAT'].keys() if j != 'n/a'])
    print("Enter the Category numbers separated by space (")
    if 1 in availableCATlist:
        print("1 = CAT I / CAT A;")
    if 2 in availableCATlist:
        print("2 = CAT II / CAT B;")
    if 3 in availableCATlist:
        print("3 = CAT III / CAT C;")
    if 80 in availableCATlist:
        print("80 = 80% ACCEPT;")
    if 85 in availableCATlist:
        print("85 = 85% ACCEPT;")
    if 90 in availableCATlist:
        print("90 = 90% ACCEPT;")
    print("Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html")
    self.CAT_List = list(int(num) for num in input('):').split())
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
        "0 or 0.X = Static;\n"
        "1, 1.X, 2, 3 = Adaptive;\n"
        "Please refer to the full list of setpoint temperatures at https://htmlpreview.github.io/?https://github.com/dsanchez-garcia/accim/blob/master/docs/source/html_files/full_setpoint_table.html\n"
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
    try:
        self.setpoint_accuracy = float(input('\nEnter the setpoint accuracy number (any number greater than 0, if omitted will be 100): '))
    except ValueError:
        self.setpoint_accuracy = 100
    while self.setpoint_accuracy < 0:
        print('          The setpoint accuracy number is not correct. It must be a number greater than 0. Please enter the number again.')
        self.setpoint_accuracy = float(input('         Enter the setpoint accuracy number (any number greater than 0, if omitted will be 100): '))
    while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
        try:
            self.setpoint_accuracy = float(input('      Enter the setpoint accuracy number (any number greater than 0, if omitted will be 100): '))
        except ValueError:
            self.setpoint_accuracy = 100
        while self.setpoint_accuracy < 0:
            print('          The setpoint accuracy number is not correct. It must be a number greater than 0. Please enter the number again.')
            try:
                self.setpoint_accuracy = float(input('      Enter the setpoint accuracy number (any number greater than 0, if omitted will be 100): '))
            except ValueError:
                self.setpoint_accuracy = 100
    try:
        self.category_cool_offset = float(input('\nEnter the number for the CAT cooling offset modifier (value will be summed to the ACST, if omitted will be 0): '))
    except ValueError:
        self.category_cool_offset = 0.0
    while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
        try:
            self.category_cool_offset = float(input('\n        Enter the number for the CAT cooling offset modifier (value will be summed to the ACST, if omitted will be 0): '))
        except ValueError:
            self.category_cool_offset = 0.0

    try:
        self.category_heat_offset = float(input('\nEnter the number for the CAT heating offset modifier (value will be summed to the AHST, if omitted will be 0): '))
    except ValueError:
        self.category_heat_offset = 0.0
    while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
        try:
            self.category_heat_offset = float(input('\n        Enter the number for the CAT heating offset modifier (value will be summed to the AHST, if omitted will be 0): '))
        except ValueError:
            self.category_heat_offset = 0.0
    while self.category_heat_offset > self.category_cool_offset:
        print(f'          You have entered a CATheatOffset ({self.category_heat_offset}) larger than the CATcoolOffset ({self.category_cool_offset}), '
              f'which will probably lead to an error in the EnergyPlus simulation.')
        try:
            self.category_heat_offset = float(input('\n        Enter the number for the CAT heating offset modifier (value will be summed to the AHST, if omitted will be 0): '))
        except ValueError:
            self.category_heat_offset = 0.0
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            try:
                self.category_heat_offset = float(input('\n        Enter the number for the CAT heating offset modifier (value will be summed to the AHST, if omitted will be 0): '))
            except ValueError:
                self.category_heat_offset = 0.0
        # self.CATheatOffset = float(input('\nEnter the number for the CAT heating offset modifier (value will be summed to the AHST): '))
        # while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
        #     self.CATheatOffset = float(input('      Enter the number for the CAT heating offset modifier (value will be summed to the AHST): '))

    if (any(i in [1, 2] for i in self.ComfStand_List) and 0 in self.ComfMod_List) or 22 in self.ComfStand_List:
        self.cooling_season_start = list(
            int(num)
            for num
            in input("\nEnter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
        )
        if len(self.cooling_season_start) == 1:
            day_of_year = self.cooling_season_start[0]
        elif len(self.cooling_season_start) == 2:
            from datetime import date
            day_of_year = date(2007, self.cooling_season_start[1], self.cooling_season_start[0]).timetuple().tm_yday
        while day_of_year < 1 or day_of_year > 365:
            print('          The start for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
            self.cooling_season_start = list(
                int(num)
                for num
                in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.cooling_season_start = list(
                int(num)
                for num
                in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
            if len(self.cooling_season_start) == 1:
                day_of_year = self.cooling_season_start[0]
            elif len(self.cooling_season_start) == 2:
                day_of_year = date(2007, self.cooling_season_start[1], self.cooling_season_start[0]).timetuple().tm_yday
            while day_of_year < 1 or day_of_year > 365:
                print('          The start for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
                self.cooling_season_start = list(
                    int(num)
                    for num
                    in input("Enter the start of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
                )
                if len(self.cooling_season_start) == 1:
                    day_of_year = self.cooling_season_start[0]
                elif len(self.cooling_season_start) == 2:
                    day_of_year = date(2007, self.cooling_season_start[1], self.cooling_season_start[0]).timetuple().tm_yday
        self.cooling_season_start = day_of_year

        self.cooling_season_end = list(
            int(num)
            for num
            in input("\nEnter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
        )
        if len(self.cooling_season_end) == 1:
            day_of_year = self.cooling_season_end[0]
        elif len(self.cooling_season_end) == 2:
            from datetime import date
            day_of_year = date(2007, self.cooling_season_end[1], self.cooling_season_end[0]).timetuple().tm_yday
        while day_of_year < 1 or day_of_year > 365:
            print('          The end for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
            self.cooling_season_end = list(
                int(num)
                for num
                in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
        while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
            self.cooling_season_end = list(
                int(num)
                for num
                in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
            )
            if len(self.cooling_season_end) == 1:
                day_of_year = self.cooling_season_end[0]
            elif len(self.cooling_season_end) == 2:
                day_of_year = date(2007, self.cooling_season_end[1], self.cooling_season_end[0]).timetuple().tm_yday
            while day_of_year < 1 or day_of_year > 365:
                print('          The end for cooling season is not correct. It must be a numeric date format dd/mm or the day of the year. Please enter the value again.')
                self.cooling_season_end = list(
                    int(num)
                    for num
                    in input("Enter the end of the cooling season in numeric date format dd/mm or the day of the year: ").split('/')
                )
                if len(self.cooling_season_end) == 1:
                    day_of_year = self.cooling_season_end[0]
                elif len(self.cooling_season_end) == 2:
                    day_of_year = date(2007, self.cooling_season_end[1], self.cooling_season_end[0]).timetuple().tm_yday
        self.cooling_season_end = day_of_year
    else:
        self.cooling_season_start = 121
        self.cooling_season_end = 274

    if 'mm' in script_type.lower():
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
            self.vof_max_temp_diff = float(input('Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
            while self.vof_max_temp_diff <= 0:
                print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                self.vof_max_temp_diff = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.vof_max_temp_diff = float(input('      Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                while self.vof_max_temp_diff <= 0:
                    print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                    self.vof_max_temp_diff = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))

            self.vof_min_temp_diff = float(input('Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
            while self.vof_min_temp_diff <= 0:
                print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                self.vof_min_temp_diff = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.vof_min_temp_diff = float(input('      Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                while self.vof_min_temp_diff <= 0:
                    print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                    self.vof_min_temp_diff = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))

            while self.vof_min_temp_diff >= self.vof_max_temp_diff:
                print('The minimum temperature difference number you entered is larger than or equal to the maximum temperature difference number. Please enter both maximum and minimum temperature difference numbers again.')
                self.vof_max_temp_diff = float(input('Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                while self.vof_max_temp_diff <= 0:
                    print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                    self.vof_max_temp_diff = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                    self.vof_max_temp_diff = float(input('      Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))
                    while self.vof_max_temp_diff <= 0:
                        print('          The maximum temperature difference number is not correct. It must be a number larger than 0. Please enter the number again.')
                        self.vof_max_temp_diff = float(input('         Enter the maximum temperature difference number for Ventilation Opening Factor (any number larger than 0): '))

                self.vof_min_temp_diff = float(input('Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                while self.vof_min_temp_diff <= 0:
                    print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                    self.vof_min_temp_diff = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                    self.vof_min_temp_diff = float(input('      Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))
                    while self.vof_min_temp_diff <= 0:
                        print('          The minimum temperature difference number is not correct. It must be a number larger than 0 and smaller than the maximum temperature difference number. Please enter the number again.')
                        self.vof_min_temp_diff = float(input('         Enter the minimum temperature difference number for Ventilation Opening Factor (any number larger than 0 and smaller than the maximum temperature difference number): '))

            self.vof_multiplier = float(input('Enter the multiplier number for Ventilation Opening Factor (any number between 0 and 1): '))
            while self.vof_multiplier < 0 or self.vof_multiplier > 1:
                print('          The multiplier number is not correct. It must be a number between 0 and 1. Please enter the number again.')
                self.vof_multiplier = float(input('         Enter the multiplier number for modulating the Ventilation Opening Factor (any number between 0 and 1): '))
            while input('          Are you sure the number is correct? [y or [] / n]: ') == 'n':
                self.vof_multiplier = float(input('      Enter the multiplier number for modulating the Ventilation Opening Factor (any number between 0 and 1): '))
                while self.vof_multiplier < 0 or self.vof_multiplier > 1:
                    print('          The multiplier number is not correct. It must be a number between 0 and 1. Please enter the number again.')
                    self.vof_multiplier = float(input('         Enter the multiplier number for modulating the Ventilation Opening Factor (any number between 0 and 1): '))
        else:
            self.vof_max_temp_diff = 6
            self.vof_min_temp_diff = 1
            self.vof_multiplier = 0.25

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
    elif 'ac' in script_type.lower():
        self.HVACmode_List = [0]
        self.VentCtrl_List = [0]
        self.vof_max_temp_diff = 1
        self.vof_min_temp_diff = 0
        self.vof_multiplier = 0
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

    self.user_input_arguments = {
        'ComfStand': self.ComfStand_List,
        'CAT': self.CAT_List,
        'CATcoolOffset': self.category_cool_offset,
        'CATheatOffset': self.category_heat_offset,
        'ComfMod': self.ComfMod_List,
        'SetpointAcc': self.setpoint_accuracy,
        'CustAST_ACSTaul': self.custom_ast_acst_aul,
        'CustAST_ACSTall': self.custom_ast_acst_all,
        'CustAST_AHSTaul': self.custom_ast_ahst_aul,
        'CustAST_AHSTall': self.custom_ast_ahst_all,
        'CustAST_m': self.custom_ast_m,
        'CustAST_n': self.custom_ast_n,
        'CustAST_ACSToffset': self.custom_ast_acst_offset,
        'CustAST_AHSToffset': self.custom_ast_ahst_offset,
        'CoolSeasonStart': self.cooling_season_start,
        'CoolSeasonEnd': self.cooling_season_end,
        'HVACmode': self.HVACmode_List,
        'VentCtrl': self.VentCtrl_List,
        'MaxTempDiffVOF': self.vof_max_temp_diff,
        'MinTempDiffVOF': self.vof_min_temp_diff,
        'MultiplierVOF': self.vof_multiplier,
        'VSToffset': self.VSToffset_List,
        'MinOToffset': self.MinOToffset_List,
        'MaxWindSpeed': self.MaxWindSpeed_List,
        'ASTtol_start': self.ASTtol_value_from,
        'ASTtol_end_input': self.ASTtol_value_to_input,
        'ASTtol_steps': self.ASTtol_value_steps,
    }


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

    :param self: Used as a method for class ``accim.sim.accim_Main.AccimJob``
    :param ScriptType: Inherited from class ``accim.sim.accis.addAccis``
    :param TempCtrl: Inherited from class ``accim.sim.accis.addAccis``
    :param ComfStand: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_m: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_n: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_ACSToffset: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_AHSToffset: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_ACSTall: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_ACSTaul: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_AHSTall: Inherited from class ``accim.sim.accis.addAccis``
    :param CustAST_AHSTaul: Inherited from class ``accim.sim.accis.addAccis``
    :param CAT: Inherited from class ``accim.sim.accis.addAccis``
    :param CATcoolOffset: Inherited from class ``accim.sim.accis.addAccis``
    :param CATheatOffset: Inherited from class ``accim.sim.accis.addAccis``
    :param ComfMod: Inherited from :class:``accim.sim.accis.addAccis``
    :param SetpointAcc: Inherited from :class:``accim.sim.accis.addAccis``
    :param CoolSeasonStart: Inherited from :class:``accim.sim.accis.addAccis``
    :param CoolSeasonEnd: Inherited from :class:``accim.sim.accis.addAccis``
    :param HVACmode: Inherited from :class:``accim.sim.accis.addAccis``
    :param VentCtrl: Inherited from :class:``accim.sim.accis.addAccis``
    :param MaxTempDiffVOF: Inherited from :class:``accim.sim.accis.addAccis``
    :param MinTempDiffVOF: Inherited from :class:``accim.sim.accis.addAccis``
    :param MultiplierVOF: Inherited from :class:``accim.sim.accis.addAccis``
    :param VSToffset: Inherited from :class:``accim.sim.accis.addAccis``
    :param MinOToffset: Inherited from :class:``accim.sim.accis.addAccis``
    :param MaxWindSpeed: Inherited from :class:``accim.sim.accis.addAccis``
    :param ASTtol_start: Inherited from :class:``accim.sim.accis.addAccis``
    :param ASTtol_end_input: Inherited from :class:``accim.sim.accis.addAccis``
    :param ASTtol_steps: Inherited from :class:``accim.sim.accis.addAccis``
    :param NameSuffix: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    :param confirmGen: Inherited from :class:``accim.sim.accis.addAccis``
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
        confirm_generation = input('Do you still want to run ACCIS? [y/n]: ')
        if confirm_generation == 'y':
            confirm_generation = True
        else:
            confirm_generation = False

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
