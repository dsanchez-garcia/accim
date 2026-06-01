# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García
#
# Interactive (terminal) prompts for accim.sim.
#
# This module isolates every ``input()`` interaction so the rest of accim.sim is
# free of interactive I/O and can be used purely programmatically (scripts,
# Jupyter, pipelines). The entry points (e.g. ``AddAccis``) call these helpers
# only when the corresponding arguments were not provided, preserving the
# historical interactive behaviour.

from accim import lists as _lists

# Validation vocabularies (shared with the entry points).
fullScriptTypeList = [
    'vrf_ac',
    'vrf_mm',
    'ex_mm',
    'ex_ac',
]

SupplyAirTempInputMethodList = [
    'supply air temperature',
    'temperature difference',
]

fullOutputsTypeList = [
    'Standard', 'standard',
    'Simplified', 'simplified',
    'Detailed', 'detailed',
    'Custom', 'custom',
]

fullOutputsFreqList = [
    'Timestep', 'timestep',
    'Hourly', 'hourly',
    'Daily', 'daily',
    'Monthly', 'monthly',
    'Runperiod', 'runperiod',
]

fullTempCtrllist = [
    'temperature',
    'temp',
    'pmv',
]


def collect_basic_inputs():
    """Prompt the user (terminal) for the basic ACCIS inputs.

    Returns a dict with the keys: ``script_type``, ``supply_air_temp_method``,
    ``output_keep_existing``, ``output_type``, ``output_freqs``,
    ``output_gen_dataframe``, ``energyplus_version``, ``temp_control``.

    ``supply_air_temp_method`` is only asked for VRF script types (None otherwise).
    """
    print(
        '\nNow, you are going to be asked to enter some information for different arguments '
        'to generate the output IDFs with adaptive setpoint temperatures. '
        '\nIf you are not sure about how to use these parameters, please take a look at the documentation in the following link: '
        '\nhttps://accim.readthedocs.io/en/master/4_detailed%20use.html'
        '\n\nPlease, enter the following information:'
    )
    script_type = input("\nEnter the ScriptType (\n"
                        "for VRFsystem with full air-conditioning mode: vrf_ac;\n"
                        "for VRFsystem with mixed-mode: vrf_mm;\n"
                        "for ExistingHVAC with mixed mode: ex_mm;\n"
                        "for ExistingHVAC with full air-conditioning mode: ex_ac\n"
                        "): ")
    while script_type not in fullScriptTypeList:
        script_type = input("    ScriptType was not correct. "
                            "    Enter the ScriptType (\n"
                            "    for VRFsystem with full air-conditioning mode: vrf_ac;\n"
                            "    for VRFsystem with mixed-mode: vrf_mm;\n"
                            "    for ExistingHVAC with mixed mode: ex_mm;\n"
                            "    for ExistingHVAC with full air-conditioning mode: ex_ac\n"
                            "    ): ")
    supply_air_temp_method = None
    if 'vrf' in script_type.lower():
        supply_air_temp_method = input("\nEnter the SupplyAirTempInputMethod (\n"
                            "for Supply Air Temperature: supply air temperature;\n"
                            "for Temperature Difference: temperature difference;\n"
                            "): ")
        while supply_air_temp_method not in SupplyAirTempInputMethodList:
            supply_air_temp_method = input(
                "    SupplyAirTempInputMethod was not correct. "
                "    Enter the SupplyAirTempInputMethod (\n"
                            "for Supply Air Temperature: supply air temperature;\n"
                            "for Temperature Difference: temperature difference;\n"
                            "): ")
    output_keep_existing = input('\nDo you want to keep the existing outputs (true or false)?: ')
    while output_keep_existing.lower() not in ['true', 'false']:
        output_keep_existing = input('The answer you entered is not valid. '
                                     'Do you want to keep the existing outputs (true or false)?: ')
    output_type = input("\nEnter the Output type (standard, simplified, detailed or custom): ")
    while output_type not in fullOutputsTypeList:
        output_type = input("   Output type was not correct. "
                            "Please, enter the Output type (standard, simplified, detailed or custom): ")
    output_freqs = list(freq for freq in input(
        "\nEnter the Output frequencies separated by space (timestep, hourly, daily, monthly, runperiod): ").split())
    while (not (all(elem in fullOutputsFreqList for elem in output_freqs))):
        output_freqs = list(freq for freq in input(
            "Some of the Output frequencies are not correct. "
            "Please, enter the Output frequencies again separated by space "
            "(timestep, hourly, daily, monthly, runperiod): ").split())
    output_gen_dataframe = input('\nDo you want to generate a dataframe to see all outputs? (true or false): ')
    while output_gen_dataframe.lower() not in ['true', 'false']:
        output_gen_dataframe = input('The answer you entered is not valid. '
                                     'Do you want to generate a dataframe to see all outputs? (true or false):')
    if output_gen_dataframe.lower() == 'true':
        output_gen_dataframe = True
    elif output_gen_dataframe.lower() == 'false':
        output_gen_dataframe = False
    energyplus_version = input("\nEnter the EnergyPlus version (9.1 to 25.1, or auto): ")
    while energyplus_version not in _lists.fullEPversionsList:
        energyplus_version = input("    EnergyPlus version was not correct. "
                                   "Please, enter the EnergyPlus version (9.1 to 25.1, or auto): ")
    temp_control = input('\nEnter the Temperature Control method (temperature or pmv): ')
    while temp_control not in fullTempCtrllist:
        temp_control = input("  Temperature Control method was not correct. "
                             "Please, enter the Temperature Control method (temperature or pmv): ")

    return {
        'script_type': script_type,
        'supply_air_temp_method': supply_air_temp_method,
        'output_keep_existing': output_keep_existing,
        'output_type': output_type,
        'output_freqs': output_freqs,
        'output_gen_dataframe': output_gen_dataframe,
        'energyplus_version': energyplus_version,
        'temp_control': temp_control,
    }


def collect_comfort_inputs(self, script_type: str = None):
    """Input data for IDF generation.

    :param self: Used as a method for class ``accim.sim.engine.AccimJob``
    :param script_type: Inherited from class ``accim.sim.AddAccis``
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


def confirm_generation_prompt():
    """Ask the user whether to proceed with the output IDF generation.

    Returns ``True`` if the user answers 'y', ``False`` otherwise.
    """
    answer = input('Do you still want to run ACCIS? [y/n]: ')
    return answer == 'y'


def prompt_custom_outputs():
    """Interactively ask which outputs to keep/remove for the 'custom' output type.

    Returns a tuple ``(remove_or_keep, custom_outputs)`` where ``remove_or_keep``
    is the string 'remove'/'keep' and ``custom_outputs`` is the list of output
    variable names entered (separated by ';').
    """
    remove_or_keep = input('Do you want to remove some input or keep it and remove all others? Please enter remove or keep:')
    custom_outputs = list(str(output) for output in input(
        'Please enter these outputs (which must be contained in the list above) separated by semicolon (;): ').split(';'))
    return remove_or_keep, custom_outputs
