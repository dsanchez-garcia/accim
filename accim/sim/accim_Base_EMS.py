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

"""Add EMS objects in common to both ExistingHVAC and VRFsystem."""
import warnings


def addEMSProgramsBase(self, ScriptType: str = None, verboseMode: bool = True):
    """
    Add EMS programs for Base accim.
    Checks if some programs objects are already
    in the model, and otherwise adds them.

    :param ScriptType: Inherited from class `accim.sim.accis.addAccis`
    :param verboseMode: Inherited from class `accim.sim.accis.addAccis`
    """


    programlist = ([program.Name
                    for program
                    in self.idf1.idfobjects['EnergyManagementSystem:Program']])

    if 'SetComfTemp' in programlist:
        if verboseMode:
            print('Not added - SetComfTemp Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='SetComfTemp',
            Program_Line_1='if ComfStand == 99',
            Program_Line_2='set ComfTemp = PMOT*m+n',
            Program_Line_3='elseif ComfStand == 1',
            Program_Line_4='set ComfTemp = RMOT*0.33+18.8',
            Program_Line_5='elseif ComfStand == 2',
            Program_Line_6='set ComfTemp = PMOT*0.31+17.8',
            Program_Line_7='elseif ComfStand == 3',
            Program_Line_8='set ComfTemp = PMOT*0.48+14.4',
            Program_Line_9='elseif ComfStand == 4',
            Program_Line_10='set ComfTemp = 0',
            Program_Line_11='elseif ComfStand == 5',
            Program_Line_12='set ComfTemp = 0',
            Program_Line_13='elseif ComfStand == 6',
            Program_Line_14='set ComfTemp = 0',
            Program_Line_15='elseif ComfStand == 7',
            Program_Line_16='set ComfTemp = PMOT*0.54+12.83',
            Program_Line_17='elseif ComfStand == 8',
            Program_Line_18='set ComfTemp = PMOT*0.28+17.87',
            Program_Line_19='elseif ComfStand == 9',
            Program_Line_20='set ComfTemp = PMOT*0.39+18.42',
            Program_Line_21='elseif ComfStand == 10',
            Program_Line_22='set ComfTemp = PMOT*0.42+17.6',
            Program_Line_23='elseif ComfStand == 11',
            Program_Line_24='set ComfTemp = PMOT*0.75+5.37',
            Program_Line_25='elseif ComfStand == 12',
            Program_Line_26='set ComfTemp = PMOT*0.25+19.7',
            Program_Line_27='elseif ComfStand == 13',
            Program_Line_28='set ComfTemp = PMOT*0.26+15.9',
            Program_Line_29='elseif ComfStand == 14',
            Program_Line_30='set ComfTemp = PMOT*0.26+16.75',
            Program_Line_31='elseif ComfStand == 15',
            Program_Line_32='set ComfTemp = PMOT*0.56+12.74',
            Program_Line_33='elseif ComfStand == 16',
            Program_Line_34='set ComfTemp = PMOT*0.09+22.32',
            Program_Line_35='elseif ComfStand == 17',
            Program_Line_36='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_37='set ComfTemp = PMOT*0.48+13.9',
            Program_Line_38='else',
            Program_Line_39='set ComfTemp = PMOT*0.59+9.6',
            Program_Line_40='endif',
            Program_Line_41='elseif ComfStand == 18',
            Program_Line_42='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_43='set ComfTemp = PMOT*0.84+5.3',
            Program_Line_44='else',
            Program_Line_45='set ComfTemp = PMOT*0.96-3.6',
            Program_Line_46='endif',
            Program_Line_47='elseif ComfStand == 19',
            Program_Line_48='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_49='set ComfTemp = PMOT*0.27+17.9',
            Program_Line_50='else',
            Program_Line_51='set ComfTemp = PMOT*0.53+10.3',
            Program_Line_52='endif',
            Program_Line_53='elseif ComfStand == 20',
            Program_Line_54='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_55='set ComfTemp = PMOT*0.38+15.7',
            Program_Line_56='else',
            Program_Line_57='set ComfTemp = PMOT*0.47+9.07',
            Program_Line_58='endif',
            Program_Line_59='elseif ComfStand == 21',
            Program_Line_60='set ComfTemp = PMOT*0.678+13.51',
            Program_Line_61='endif',
        )
        if verboseMode:
            print('Added - SetComfTemp Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetComfTemp'])

    for zonename in self.ems_objs_name:
        if 'CountHours_'+zonename in programlist:
            if verboseMode:
                print('Not added - CountHours_'+zonename+' Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='CountHours_'+zonename,
                Program_Line_1='if (ComfStand == 1) || (ComfStand == 10)',
                Program_Line_2='if (RMOT >= AHSTall) && (RMOT <= ACSTaul)',
                Program_Line_3='if (' + zonename + '_OpT <= ACSTnoTol)',
                Program_Line_4='if (' + zonename + '_OpT >= AHSTnoTol)',
                Program_Line_5='set ComfHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_6='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_7='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_8='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_9='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_10='endif',
                Program_Line_11='elseif (' + zonename + '_OpT > ACSTnoTol)',
                Program_Line_12='set ComfHours_' + zonename + ' = 0',
                Program_Line_13='set DiscomfAppHotHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_14='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_15='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_16='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_17='elseif (' + zonename + '_OpT < AHSTnoTol)',
                Program_Line_18='set ComfHours_' + zonename + ' = 0',
                Program_Line_19='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_20='set DiscomfAppColdHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_21='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_22='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_23='endif',
                Program_Line_24='elseif (RMOT > ACSTaul)',
                Program_Line_25='set ComfHours_' + zonename + ' = 0',
                Program_Line_26='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_27='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_28='set DiscomfNonAppHotHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_29='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_30='elseif (RMOT < AHSTall)',
                Program_Line_31='set ComfHours_' + zonename + ' = 0',
                Program_Line_32='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_33='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_34='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_35='set DiscomfNonAppColdHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_36='endif',
                Program_Line_37='else',
                Program_Line_38='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
                Program_Line_39='if (' + zonename + '_OpT <= ACSTnoTol)',
                Program_Line_40='if (' + zonename + '_OpT >= AHSTnoTol)',
                Program_Line_41='set ComfHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_42='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_43='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_44='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_45='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_46='endif',
                Program_Line_47='elseif (' + zonename + '_OpT > ACSTnoTol)',
                Program_Line_48='set ComfHours_' + zonename + ' = 0',
                Program_Line_49='set DiscomfAppHotHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_50='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_51='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_52='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_53='elseif (' + zonename + '_OpT < AHSTnoTol)',
                Program_Line_54='set ComfHours_' + zonename + ' = 0',
                Program_Line_55='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_56='set DiscomfAppColdHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_57='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_58='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_59='endif',
                Program_Line_60='elseif (PMOT > ACSTaul)',
                Program_Line_61='set ComfHours_' + zonename + ' = 0',
                Program_Line_62='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_63='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_64='set DiscomfNonAppHotHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_65='set DiscomfNonAppColdHours_' + zonename + ' = 0',
                Program_Line_66='elseif (PMOT < AHSTall)',
                Program_Line_67='set ComfHours_' + zonename + ' = 0',
                Program_Line_68='set DiscomfAppHotHours_' + zonename + ' = 0',
                Program_Line_69='set DiscomfAppColdHours_' + zonename + ' = 0',
                Program_Line_70='set DiscomfNonAppHotHours_' + zonename + ' = 0',
                Program_Line_71='set DiscomfNonAppColdHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_72='endif',
                Program_Line_73='endif',
            )
            if verboseMode:
                print('Added - CountHours_'+zonename+' Program')
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'CountHours_'+zonename])

    if 'SetAppLimits' in programlist:
        if verboseMode:
            print('Not added - SetAppLimits Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='SetAppLimits',
            Program_Line_1='if ComfStand == 99',
            Program_Line_2='set ACSTaul = 33.5',
            Program_Line_3='set ACSTall = 10',
            Program_Line_4='set AHSTaul = 33.5',
            Program_Line_5='set AHSTall = 10',
            Program_Line_6='elseif ComfStand == 1',
            Program_Line_7='set ACSTaul = 30',
            Program_Line_8='set ACSTall = 10',
            Program_Line_9='set AHSTaul = 30',
            Program_Line_10='set AHSTall = 10',
            Program_Line_11='elseif ComfStand == 2 || ComfStand == 12',
            Program_Line_12='set ACSTaul = 33.5',
            Program_Line_13='set ACSTall = 10',
            Program_Line_14='set AHSTaul = 33.5',
            Program_Line_15='set AHSTall = 10',
            Program_Line_16='elseif ComfStand == 3',
            Program_Line_17='set ACSTaul = 30',
            Program_Line_18='set ACSTall = 5',
            Program_Line_19='set AHSTaul = 30',
            Program_Line_20='set AHSTall = 5',
            Program_Line_21='elseif (ComfStand == 4) || (ComfStand == 5)',
            Program_Line_22='if CAT == 1',
            Program_Line_23='set ACSTaul = 28',
            Program_Line_24='set ACSTall = 18',
            Program_Line_25='set AHSTaul = 28',
            Program_Line_26='set AHSTall = 18',
            Program_Line_27='elseif CAT == 2',
            Program_Line_28='set ACSTaul = 30',
            Program_Line_29='set ACSTall = 18',
            Program_Line_30='set AHSTaul = 28',
            Program_Line_31='set AHSTall = 16',
            Program_Line_32='else',
            Program_Line_33='set ACSTaul = 50',
            Program_Line_34='set ACSTall = 50',
            Program_Line_35='set AHSTaul = 50',
            Program_Line_36='set AHSTall = 50',
            Program_Line_37='endif',
            Program_Line_38='elseif ComfStand == 6',
            Program_Line_39='set ACSTaul = 30',
            Program_Line_40='set ACSTall = -7',
            Program_Line_41='set AHSTaul = 30',
            Program_Line_42='set AHSTall = -7',
            Program_Line_43='elseif ComfStand == 7',
            Program_Line_44='set ACSTaul = 31',
            Program_Line_45='set ACSTall = 12.5',
            Program_Line_46='set AHSTaul = 31',
            Program_Line_47='set AHSTall = 12.5',
            Program_Line_48='elseif ComfStand == 8',
            Program_Line_49='set ACSTaul = 38.5',
            Program_Line_50='set ACSTall = 13',
            Program_Line_51='set AHSTaul = 38.5',
            Program_Line_52='set AHSTall = 13',
            Program_Line_53='elseif ComfStand == 9 || ComfStand == 10 || ComfStand == 11',
            Program_Line_54='set ACSTaul = 33',
            Program_Line_55='set ACSTall = 5.5',
            Program_Line_56='set AHSTaul = 33',
            Program_Line_57='set AHSTall = 5.5',
            Program_Line_58='elseif ComfStand == 13',
            Program_Line_59='set ACSTaul = 25',
            Program_Line_60='set ACSTall = 10',
            Program_Line_61='set AHSTaul = 25',
            Program_Line_62='set AHSTall = 10',
            Program_Line_63='elseif ComfStand == 14',
            Program_Line_64='set ACSTaul = 27',
            Program_Line_65='set ACSTall = 8',
            Program_Line_66='set AHSTaul = 27',
            Program_Line_67='set AHSTall = 8',
            Program_Line_68='elseif ComfStand == 15',
            Program_Line_69='set ACSTaul = 24.8',
            Program_Line_70='set ACSTall = 16.9',
            Program_Line_71='set AHSTaul = 24.8',
            Program_Line_72='set AHSTall = 16.9',
            Program_Line_73='elseif ComfStand == 16',
            Program_Line_74='set ACSTaul = 25.7',
            Program_Line_75='set ACSTall = 16.4',
            Program_Line_76='set AHSTaul = 25.7',
            Program_Line_77='set AHSTall = 16.4',
            Program_Line_78='elseif ComfStand == 17',
            Program_Line_79='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_80='set ACSTaul = 25.25',
            Program_Line_81='set ACSTall = 11.25',
            Program_Line_82='set AHSTaul = 25.25',
            Program_Line_83='set AHSTall = 11.25',
            Program_Line_84='else',
            Program_Line_85='set ACSTaul = 45',
            Program_Line_86='set ACSTall = 23',
            Program_Line_87='set AHSTaul = 45',
            Program_Line_88='set AHSTall = 23',
            Program_Line_89='endif',
            Program_Line_90='elseif ComfStand == 18',
            Program_Line_91='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_92='set ACSTaul = 27.5',
            Program_Line_93='set ACSTall = 15.5',
            Program_Line_94='set AHSTaul = 27.5',
            Program_Line_95='set AHSTall = 15.5',
            Program_Line_96='else',
            Program_Line_97='set ACSTaul = 34',
            Program_Line_98='set ACSTall = 23',
            Program_Line_99='set AHSTaul = 34',
            Program_Line_100='set AHSTall = 23',
            Program_Line_101='endif',
            Program_Line_102='elseif ComfStand == 19',
            Program_Line_103='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_104='set ACSTaul = 25.25',
            Program_Line_105='set ACSTall = 5',
            Program_Line_106='set AHSTaul = 25.25',
            Program_Line_107='set AHSTall = 5',
            Program_Line_108='else',
            Program_Line_109='set ACSTaul = 25.25',
            Program_Line_110='set ACSTall = 11.75',
            Program_Line_111='set AHSTaul = 25.25',
            Program_Line_112='set AHSTall = 11.75',
            Program_Line_113='endif',
            Program_Line_114='elseif ComfStand == 20',
            Program_Line_115='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_116='set ACSTaul = 29.75',
            Program_Line_117='set ACSTall = 13',
            Program_Line_118='set AHSTaul = 29.75',
            Program_Line_119='set AHSTall = 13',
            Program_Line_120='else',
            Program_Line_121='set ACSTaul = 45',
            Program_Line_122='set ACSTall = 23',
            Program_Line_123='set AHSTaul = 45',
            Program_Line_124='set AHSTall = 23',
            Program_Line_125='endif',
            Program_Line_126='elseif ComfStand == 21',
            Program_Line_127='set ACSTaul = 20',
            Program_Line_128='set ACSTall = 6.5',
            Program_Line_129='set AHSTaul = 20',
            Program_Line_130='set AHSTall = 6.5',
            Program_Line_131='else',
            Program_Line_132='set ACSTaul = 50',
            Program_Line_133='set ACSTall = 50',
            Program_Line_134='set AHSTaul = 50',
            Program_Line_135='set AHSTall = 50',
            Program_Line_136='endif',
        )
        if verboseMode:
            print('Added - SetAppLimits Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetAppLimits'])

    if 'ApplyCAT' in programlist:
        if verboseMode:
            print('Not added - ApplyCAT Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='ApplyCAT',
            Program_Line_1='set CATcoolOffset = 0',
            Program_Line_2='set CATheatOffset = 0',
            Program_Line_3='if ComfStand == 99',
            Program_Line_4='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_5='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_6='elseif (ComfStand == 1 )',
            Program_Line_7='if (CAT == 1)',
            Program_Line_8='set ACSToffset = 2+CATcoolOffset',
            Program_Line_9='set AHSToffset = -3+CATheatOffset',
            Program_Line_10='elseif (CAT == 2)',
            Program_Line_11='set ACSToffset = 3+CATcoolOffset',
            Program_Line_12='set AHSToffset = -4+CATheatOffset',
            Program_Line_13='elseif (CAT == 3)',
            Program_Line_14='set ACSToffset = 4+CATcoolOffset',
            Program_Line_15='set AHSToffset = -5+CATheatOffset',
            Program_Line_16='endif',
            Program_Line_17='elseif ComfStand == 2 || ComfStand == 3 || ComfStand == 11',
            Program_Line_18='if (CAT == 90)',
            Program_Line_19='set ACSToffset = 2.5+CATcoolOffset',
            Program_Line_20='set AHSToffset = -2.5+CATheatOffset',
            Program_Line_21='elseif (CAT == 80)',
            Program_Line_22='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_23='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_24='endif',
            Program_Line_25='elseif (ComfStand == 4 ) || (ComfStand == 5) || (ComfStand == 6)',
            Program_Line_26='set ACSToffset = 0+CATcoolOffset',
            Program_Line_27='set AHSToffset = 0+CATheatOffset',
            Program_Line_28='elseif (ComfStand == 7)',
            Program_Line_29='if (CAT == 90)',
            Program_Line_30='set ACSToffset = 2.4+CATcoolOffset',
            Program_Line_31='set AHSToffset = -2.4+CATheatOffset',
            Program_Line_32='elseif (CAT == 85)',
            Program_Line_33='set ACSToffset = 3.3+CATcoolOffset',
            Program_Line_34='set AHSToffset = -3.3+CATheatOffset',
            Program_Line_35='elseif (CAT == 80)',
            Program_Line_36='set ACSToffset = 4.1+CATcoolOffset',
            Program_Line_37='set AHSToffset = -4.1+CATheatOffset',
            Program_Line_38='endif',
            Program_Line_39='elseif (ComfStand == 8)',
            Program_Line_40='if (CAT == 90)',
            Program_Line_41='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_42='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_43='elseif (CAT == 85)',
            Program_Line_44='set ACSToffset = 4.8+CATcoolOffset',
            Program_Line_45='set AHSToffset = -4.8+CATheatOffset',
            Program_Line_46='elseif (CAT == 80)',
            Program_Line_47='set ACSToffset = 5.9+CATcoolOffset',
            Program_Line_48='set AHSToffset = -5.9+CATheatOffset',
            Program_Line_49='endif',
            Program_Line_50='elseif ComfStand == 9 || ComfStand == 10',
            Program_Line_51='if (CAT == 90)',
            Program_Line_52='set ACSToffset = 2.15+CATcoolOffset',
            Program_Line_53='set AHSToffset = -2.15+CATheatOffset',
            Program_Line_54='elseif (CAT == 80)',
            Program_Line_55='set ACSToffset = 3.6+CATcoolOffset',
            Program_Line_56='set AHSToffset = -3.6+CATheatOffset',
            Program_Line_57='endif',
            Program_Line_58='elseif ComfStand == 12',
            Program_Line_59='if (CAT == 90)',
            Program_Line_60='set ACSToffset = 1.7+CATcoolOffset',
            Program_Line_61='set AHSToffset = -1.7+CATheatOffset',
            Program_Line_62='elseif (CAT == 80)',
            Program_Line_63='set ACSToffset = 2.89+CATcoolOffset',
            Program_Line_64='set AHSToffset = -2.89+CATheatOffset',
            Program_Line_65='endif',
            Program_Line_66='elseif ComfStand == 13',
            Program_Line_67='if (CAT == 90)',
            Program_Line_68='set ACSToffset = 3.45+CATcoolOffset',
            Program_Line_69='set AHSToffset = -3.45+CATheatOffset',
            Program_Line_70='elseif (CAT == 80)',
            Program_Line_71='set ACSToffset = 4.55+CATcoolOffset',
            Program_Line_72='set AHSToffset = -4.55+CATheatOffset',
            Program_Line_73='endif',
            Program_Line_74='elseif ComfStand == 14',
            Program_Line_75='if (CAT == 90)',
            Program_Line_76='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_77='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_78='elseif (CAT == 80)',
            Program_Line_79='set ACSToffset = 4.5+CATcoolOffset',
            Program_Line_80='set AHSToffset = -4.5+CATheatOffset',
            Program_Line_81='endif',
            Program_Line_82='elseif ComfStand == 15',
            Program_Line_83='if (CAT == 90)',
            Program_Line_84='set ACSToffset = 2.8+CATcoolOffset',
            Program_Line_85='set AHSToffset = -2.8+CATheatOffset',
            Program_Line_86='elseif (CAT == 80)',
            Program_Line_87='set ACSToffset = 3.8+CATcoolOffset',
            Program_Line_88='set AHSToffset = -3.8+CATheatOffset',
            Program_Line_89='endif',
            Program_Line_90='elseif ComfStand == 16',
            Program_Line_91='if (CAT == 90)',
            Program_Line_92='set ACSToffset = 1.1+CATcoolOffset',
            Program_Line_93='set AHSToffset = -1.1+CATheatOffset',
            Program_Line_94='elseif (CAT == 80)',
            Program_Line_95='set ACSToffset = 2.1+CATcoolOffset',
            Program_Line_96='set AHSToffset = -2.1+CATheatOffset',
            Program_Line_97='endif',
            Program_Line_98='elseif (ComfStand == 17) || (ComfStand == 18)',
            Program_Line_99='if CAT == 90',
            Program_Line_100='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_101='set ACSToffset = 2+CATcoolOffset',
            Program_Line_102='set AHSToffset = -2+CATheatOffset',
            Program_Line_103='else',
            Program_Line_104='set ACSToffset = 2+CATcoolOffset',
            Program_Line_105='set AHSToffset = -2+CATheatOffset',
            Program_Line_106='endif',
            Program_Line_107='elseif CAT == 80',
            Program_Line_108='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_109='set ACSToffset = 3+CATcoolOffset',
            Program_Line_110='set AHSToffset = -3+CATheatOffset',
            Program_Line_111='else',
            Program_Line_112='set ACSToffset = 3+CATcoolOffset',
            Program_Line_113='set AHSToffset = -3+CATheatOffset',
            Program_Line_114='endif',
            Program_Line_115='endif',
            Program_Line_116='elseif ComfStand == 19',
            Program_Line_117='if CAT == 90',
            Program_Line_118='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_119='set ACSToffset = 2+CATcoolOffset',
            Program_Line_120='set AHSToffset = -2+CATheatOffset',
            Program_Line_121='else',
            Program_Line_122='set ACSToffset = 1+CATcoolOffset',
            Program_Line_123='set AHSToffset = -1+CATheatOffset',
            Program_Line_124='endif',
            Program_Line_125='elseif CAT == 80',
            Program_Line_126='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_127='set ACSToffset = 3+CATcoolOffset',
            Program_Line_128='set AHSToffset = -3+CATheatOffset',
            Program_Line_129='else',
            Program_Line_130='set ACSToffset = 2+CATcoolOffset',
            Program_Line_131='set AHSToffset = -2+CATheatOffset',
            Program_Line_132='endif',
            Program_Line_133='endif',
            Program_Line_134='elseif ComfStand == 20',
            Program_Line_135='if CAT == 90',
            Program_Line_136='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_137='set ACSToffset = 2+CATcoolOffset',
            Program_Line_138='set AHSToffset = -2+CATheatOffset',
            Program_Line_139='else',
            Program_Line_140='set ACSToffset = 5+CATcoolOffset',
            Program_Line_141='set AHSToffset = -5+CATheatOffset',
            Program_Line_142='endif',
            Program_Line_143='elseif CAT == 80',
            Program_Line_144='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_145='set ACSToffset = 3+CATcoolOffset',
            Program_Line_146='set AHSToffset = -3+CATheatOffset',
            Program_Line_147='else',
            Program_Line_148='set ACSToffset = 6+CATcoolOffset',
            Program_Line_149='set AHSToffset = -6+CATheatOffset',
            Program_Line_150='endif',
            Program_Line_151='endif',
            Program_Line_152='elseif ComfStand == 21',
            Program_Line_153='if (CAT == 90)',
            Program_Line_154='set ACSToffset = 2.5+CATcoolOffset',
            Program_Line_155='set AHSToffset = -2.5+CATheatOffset',
            Program_Line_156='elseif (CAT == 80)',
            Program_Line_157='set ACSToffset = 4+CATcoolOffset',
            Program_Line_158='set AHSToffset = -4+CATheatOffset',
            Program_Line_159='endif',
            Program_Line_160='endif',
        )
        if verboseMode:
            print('Added - ApplyCAT Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyCAT'])
    
    # ========== MODULAR SetAST ARCHITECTURE ==========
    # Replace the monolithic SetAST with a master program + 23 per-ComfStand subprograms.
    # Each subprogram (SetAST_CS{N}) handles all ComfMod logic internally via if/elseif,
    # so the total EMS program count is kept small (23 subprograms + 1 master).

    if 'SetAST_Master' in programlist:
        if verboseMode:
            print('Not added - SetAST_Master Program (already exists)')
    else:
        # Import modular SetAST functions
        from accim.sim.setAST_models import get_SetAST_Master_program, get_all_SetAST_modular_programs

        try:
            # Create the SetAST_Master program (routes to per-ComfStand subprograms)
            master_lines = get_SetAST_Master_program()
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='SetAST_Master',
            )
            master_program = [p for p in self.idf1.idfobjects['EnergyManagementSystem:Program']
                              if p.Name == 'SetAST_Master'][0]

            # Add master program lines
            for i, line in enumerate(master_lines, 1):
                field_name = f'Program_Line_{i}'
                if field_name not in master_program.objls:
                    master_program.objls.append(field_name)
                    master_program.obj.append('')
                setattr(master_program, field_name, line)

            if verboseMode:
                print(f'Added - SetAST_Master Program with {len(master_lines)} lines')

            # Get all per-ComfStand SetAST subprograms.
            # 'modular' is now keyed by ComfStand integer (e.g. {0: {...}, 1: {...}, ...})
            all_programs = get_all_SetAST_modular_programs()
            modular_programs = all_programs['modular']

            # Add each per-ComfStand subprogram chunk
            programs_added = 0
            for (cs, chunk_idx), program_dict in modular_programs.items():
                program_name = program_dict['name']  # e.g. 'SetAST_CS1_0'

                # Check if program already exists
                existing_program = [p for p in self.idf1.idfobjects['EnergyManagementSystem:Program']
                                    if p.Name == program_name]

                if not existing_program:
                    # Create the subprogram
                    self.idf1.newidfobject(
                        'EnergyManagementSystem:Program',
                        Name=program_name,
                    )
                    modular_program = [p for p in self.idf1.idfobjects['EnergyManagementSystem:Program']
                                       if p.Name == program_name][0]

                    # Add program lines
                    for i, line in enumerate(program_dict['lines'], 1):
                        field_name = f'Program_Line_{i}'
                        if field_name not in modular_program.objls:
                            modular_program.objls.append(field_name)
                            modular_program.obj.append('')
                        setattr(modular_program, field_name, line)

                    programs_added += 1

            if verboseMode:
                print(f'Added - {programs_added} per-ComfStand SetAST subprograms')
            
            # Create base SetAST program for backward compatibility
            # This program just calls SetAST_Master and initializes variables
            legacy_setast = [p for p in self.idf1.idfobjects['EnergyManagementSystem:Program'] 
                            if p.Name == 'SetAST']
            if not legacy_setast:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Program',
                    Name='SetAST',
                    # Initialize variables needed for modular programs
                    Program_Line_1='set SetpointAcc = 10000',
                    Program_Line_2='set m = 0.31',
                    Program_Line_3='set n = 17.8',
                    # Call the SetAST_Master program
                    Program_Line_4='run SetAST_Master',
                )
                if verboseMode:
                    print('Added - SetAST Program (base program that calls SetAST_Master)')
        
        except Exception as e:
            if verboseMode:
                print(f'ERROR in modular SetAST initialization: {e}')
            raise
    
    if 'SetASTnoTol' in programlist:
        if verboseMode:
            print('Not added - SetASTnoTol Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='SetASTnoTol',
            Program_Line_1='set ACSTnoTol = ACST-ACSTtol',
            Program_Line_2='set AHSTnoTol = AHST-AHSTtol'
            )
        if verboseMode:
            print('Added - SetASTnoTol Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetASTnoTol'])

    for zonename in self.ems_objs_name:
        if 'CountHoursNoApp_'+zonename in programlist:
            if verboseMode:
                print('Not added - CountHoursNoApp_'+zonename+' Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='CountHoursNoApp_'+zonename,
                Program_Line_1='if (' + zonename + '_OpT <= ACSTnoTol)',
                Program_Line_2='if (' + zonename + '_OpT >= AHSTnoTol)',
                Program_Line_3='set ComfHoursNoApp_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_4='if Occ_count_' + zonename + '',
                Program_Line_5='set OccComfHoursNoApp_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_6='else',
                Program_Line_7='set OccComfHoursNoApp_' + zonename + ' = 0',
                Program_Line_8='endif',
                Program_Line_9='else',
                Program_Line_10='set ComfHoursNoApp_' + zonename + ' = 0',
                Program_Line_11='endif',
                Program_Line_12='else',
                Program_Line_13='set ComfHoursNoApp_' + zonename + ' = 0',
                Program_Line_14='endif',
                Program_Line_15='if ' + zonename + '_OpT > ACSTnoTol || ' + zonename + '_OpT < AHSTnoTol',
                Program_Line_16='if Occ_count_' + zonename + '',
                Program_Line_17='set OccDiscomfHoursNoApp_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_18='else',
                Program_Line_19='set OccDiscomfHoursNoApp_' + zonename + ' = 0',
                Program_Line_20='endif',
                Program_Line_21='else',
                Program_Line_22='set OccDiscomfHoursNoApp_' + zonename + ' = 0',
                Program_Line_23='endif',
                Program_Line_24='if Occ_count_' + zonename + ' > 0',
                Program_Line_25='set OccHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_26='else',
                Program_Line_27='set OccHours_' + zonename + ' = 0',
                Program_Line_28='endif',
            )
            if verboseMode:
                print('Added - CountHoursNoApp_'+zonename+' Program')
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'CountHoursNoApp_'+zonename])

        if 'SetGeoVar'+zonename in programlist:
            if verboseMode:
                print('Not added - SetGeoVar'+zonename+' Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='SetGeoVar'+zonename,
                Program_Line_1='set ZoneFloorArea_' + zonename + ' = ZFA_' + zonename + '/2',
                Program_Line_2='set ZoneAirVolume_' + zonename + ' = ZAV_' + zonename + '/2'
            )
            if verboseMode:
                print('Added - SetGeoVar'+zonename+' Program')
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetGeoVar'+zonename])

    if 'SetInputData' in programlist:
        if verboseMode:
            print('Not added - SetInputData Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='SetInputData',
            Program_Line_1='set ComfStand = 1',
            Program_Line_2='set CAT = 1',
            Program_Line_3='set ComfMod = 2',
            Program_Line_4='set HVACmode = 2',
            Program_Line_5='set VentCtrl = 0',
            Program_Line_6='set VSToffset = 0',
            Program_Line_7='set MinOToffset = 7',
            Program_Line_8='set MaxWindSpeed = 6',
            Program_Line_9='set ACSTtol = -0.25',
            Program_Line_10='set AHSTtol = 0.25',
            Program_Line_11='set CoolSeasonStart = 121',
            Program_Line_12='set CoolSeasonEnd = 274',
            # Program_Line_13='set CATcoolOffset = 0',
            # Program_Line_14='set CATheatOffset = 0',

            # Program_Line_11='set SetpointAcc = 10000',

        )
        if verboseMode:
            print('Added - SetInputData Program')
    
    if (ScriptType.lower() == 'vrf_mm' or
        ScriptType.lower() == 'ex_mm'):

        if 'SetVOFinputData' in programlist:
            if verboseMode:
                print('Not added - SetVOFinputData Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='SetVOFinputData',
                Program_Line_1='set MaxTempDiffVOF = 6',
                Program_Line_2='set MinTempDiffVOF = 1',
                Program_Line_3='set MultiplierVOF = 0.25',
            )
            if verboseMode:
                print('Added - SetVOFinputData Program')

        if 'SetVST' in programlist:
            if verboseMode:
                print('Not added - SetVST Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='SetVST',
                Program_Line_1='set MinOutTemp = roundedAHST - MinOToffset',
                Program_Line_2='if (VentCtrl == 0) || (VentCtrl==2)',
                Program_Line_3='if ComfStand == 0',
                Program_Line_4='if (CurrentTime < 7)',
                Program_Line_5='set VST = (roundedACST+roundedAHST)/2+VSToffset',
                Program_Line_6='elseif (CurrentTime < 15)',
                Program_Line_7='set VST = 22.5+VSToffset',
                Program_Line_8='elseif (CurrentTime < 23)',
                Program_Line_9='set VST = (roundedACST+roundedAHST)/2+VSToffset',
                Program_Line_10='elseif (CurrentTime < 24)',
                Program_Line_11='set VST = (roundedACST+roundedAHST)/2+VSToffset',
                Program_Line_12='endif',
                Program_Line_13='elseif ComfStand == 1 || ComfStand == 10',
                Program_Line_14='if (RMOT >= AHSTall) && (RMOT <= ACSTaul)',
                Program_Line_15='set VST = ComfTemp+VSToffset',
                Program_Line_16='else',
                Program_Line_17='set VST = (roundedACST+roundedAHST)/2+VSToffset',
                Program_Line_18='endif',
                Program_Line_19='elseif ComfStand == 4 || ComfStand == 5 || ComfStand == 6',
                Program_Line_20='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
                Program_Line_21='set VST = (roundedACST+roundedAHST)/2+VSToffset',
                Program_Line_22='else',
                Program_Line_23='set VST = 0',
                Program_Line_24='endif',
                Program_Line_25='else',
                Program_Line_26='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
                Program_Line_27='set VST = ComfTemp+VSToffset',
                Program_Line_28='else',
                Program_Line_29='set VST = (roundedACST+roundedAHST)/2+VSToffset',
                Program_Line_30='endif',
                Program_Line_31='endif',
                Program_Line_32='elseif (VentCtrl == 1) || (VentCtrl==3)',
                Program_Line_33='set VST = roundedAHST+VSToffset',
                Program_Line_34='endif',
            )
            if verboseMode:
                print('Added - SetVST Program')
        #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetVST'])

        for zonename in self.ems_objs_name:
            if 'ApplyAST_'+zonename in programlist:
                if verboseMode:
                    print('Not added - ApplyAST_'+zonename+' Program')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Program',
                    Name='ApplyAST_'+zonename,
                    # todo if there is no cooling coil, then zonename_COOLCOIL sensor won't be added
                    #  and therefore it should be omitted in all ExistingHVAC EMS programs; same for _HEATCOIL

                    Program_Line_1='if ' + zonename + '_CoolCoil==0',
                    Program_Line_2='if ' + zonename + '_HeatCoil==0',
                    Program_Line_3='set NoH_NoC_reqs = 1',
                    Program_Line_4='else',
                    Program_Line_5='set NoH_NoC_reqs = 0',
                    Program_Line_6='endif',
                    Program_Line_7='else',
                    Program_Line_8='set NoH_NoC_reqs = 0',
                    Program_Line_9='endif',
                    Program_Line_10='if ' + zonename + '_OpT<roundedACST',
                    Program_Line_11='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_12='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_13='if ' + zonename + '_OutT < ' + zonename + '_OpT',
                    Program_Line_14='set meets_base_reqs = 1',
                    Program_Line_15='else',
                    Program_Line_16='set meets_base_reqs = 0',
                    Program_Line_17='endif',
                    Program_Line_18='else',
                    Program_Line_19='set meets_base_reqs = 0',
                    Program_Line_20='endif',
                    Program_Line_21='else',
                    Program_Line_22='set meets_base_reqs = 0',
                    Program_Line_23='endif',
                    Program_Line_24='else',
                    Program_Line_25='set meets_base_reqs = 0',
                    Program_Line_26='endif',
                    Program_Line_27='if (NoH_NoC_reqs == 1) && (meets_base_reqs == 1)',
                    Program_Line_28='if ' + zonename + '_OpT>VST',
                    Program_Line_29='set Ventilates_HVACmode2_' + zonename + ' = 1',
                    Program_Line_30='else',
                    Program_Line_31='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_32='endif',
                    Program_Line_33='else',
                    Program_Line_34='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_35='endif',
                    Program_Line_36='if VentCtrl == 0',
                    Program_Line_37='if ' + zonename + '_OutT < ' + zonename + '_OpT',
                    Program_Line_38='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_39='if ' + zonename + '_OpT > VST',
                    Program_Line_40='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_41='set Ventilates_HVACmode1_' + zonename + ' = 1',
                    Program_Line_42='else',
                    Program_Line_43='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_44='endif',
                    Program_Line_45='else',
                    Program_Line_46='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_47='endif',
                    Program_Line_48='else',
                    Program_Line_49='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_50='endif',
                    Program_Line_51='else',
                    Program_Line_52='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_53='endif',
                    Program_Line_54='elseif VentCtrl == 1',
                    Program_Line_55='if ' + zonename + '_OutT<' + zonename + '_OpT',
                    Program_Line_56='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_57='if ' + zonename + '_OpT > ACSTnoTol',
                    Program_Line_58='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_59='set Ventilates_HVACmode1_' + zonename + ' = 1',
                    Program_Line_60='else',
                    Program_Line_61='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_62='endif',
                    Program_Line_63='else',
                    Program_Line_64='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_65='endif',
                    Program_Line_66='else',
                    Program_Line_67='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_68='endif',
                    Program_Line_69='else',
                    Program_Line_70='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_71='endif',
                    Program_Line_72='endif',
                    Program_Line_73='if HVACmode == 0',
                    Program_Line_74='if Occ_count_' + zonename + ' == 0',
                    Program_Line_75='Set ACST_Act_' + zonename + ' = 100',
                    Program_Line_76='Set AHST_Act_' + zonename + ' = -100',
                    Program_Line_77='else',
                    Program_Line_78='set ACST_Act_' + zonename + ' = roundedACST',
                    Program_Line_79='set AHST_Act_' + zonename + ' = roundedAHST',
                    Program_Line_80='endif',
                    Program_Line_81='elseif HVACmode == 1',
                    Program_Line_82='Set ACST_Act_' + zonename + ' = 100',
                    Program_Line_83='Set AHST_Act_' + zonename + ' = -100',
                    Program_Line_84='if Ventilates_HVACmode1_' + zonename + ' == 1 && Occ_count_' + zonename + ' > 0',
                    Program_Line_85='set VentHours_' + zonename + ' = 1*ZoneTimeStep',
                    Program_Line_86='else',
                    Program_Line_87='set VentHours_' + zonename + ' = 0',
                    Program_Line_88='endif',
                    Program_Line_89='elseif HVACmode == 2',
                    Program_Line_90='if Occ_count_' + zonename + ' == 0',
                    Program_Line_91='Set ACST_Act_' + zonename + ' = 100',
                    Program_Line_92='Set AHST_Act_' + zonename + ' = -100',
                    Program_Line_93='set VentHours_' + zonename + ' = 0',
                    Program_Line_94='else',
                    Program_Line_95='if Ventilates_HVACmode2_' + zonename + ' == 1',
                    Program_Line_96='set VentHours_' + zonename + ' = 1*ZoneTimeStep',
                    Program_Line_97='elseif Ventilates_HVACmode2_' + zonename + ' == 0',
                    Program_Line_98='set VentHours_' + zonename + ' = 0',
                    Program_Line_99='set ACST_Act_' + zonename + ' = roundedACST',
                    Program_Line_100='set AHST_Act_' + zonename + ' = roundedAHST',
                    Program_Line_101='endif',
                    Program_Line_102='endif',
                    Program_Line_103='endif',
                )
                if verboseMode:
                    print('Added - ApplyAST_'+zonename+' Program')
            #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyAST_'+windowname])

        for windowname in self.windownamelist:
            if 'SetMyVOF_'+windowname in programlist:
                if verboseMode:
                    print('Not added - SetMyVOF_'+windowname+' Program')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Program',
                    Name='SetMyVOF_'+windowname,
                    Program_Line_1='set slope = (1 - MultiplierVOF) / (MinTempDiffVOF - MaxTempDiffVOF)',
                    Program_Line_2='if ' + windowname + '_OutT > 0',
                    Program_Line_3='set ' + windowname + '_TempDiffVOF = ' + windowname + '_OpT - ' + windowname + '_OutT',
                    Program_Line_4='else',
                    Program_Line_5='set ' + windowname + '_TempDiffVOF = ' + windowname + '_OpT + ' + windowname + '_OutT',
                    Program_Line_6='endif',
                    Program_Line_7='if ' + windowname + '_OutT > ' + windowname + '_OpT',
                    Program_Line_8='set ' + windowname + '_MyVOF = 0',
                    Program_Line_9='else',
                    Program_Line_10='if ' + windowname + '_TempDiffVOF > MaxTempDiffVOF',
                    Program_Line_11='set ' + windowname + '_MyVOF = MultiplierVOF',
                    Program_Line_12='elseif ' + windowname + '_TempDiffVOF < MinTempDiffVOF',
                    Program_Line_13='set ' + windowname + '_MyVOF = 1.0',
                    Program_Line_14='else',
                    Program_Line_15='set ' + windowname + '_MyVOF = slope*' + windowname + '_TempDiffVOF - slope*MinTempDiffVOF + 1',
                    Program_Line_16='endif',
                    Program_Line_17='endif',
                )
                if verboseMode:
                    print('Added - SetMyVOF_'+windowname+' Program')
            #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetMyVOF_'+windowname])

            if 'SetWindowOperation_'+windowname in programlist:
                if verboseMode:
                    print('Not added - SetWindowOperation_'+windowname+' Program')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Program',
                    Name='SetWindowOperation_'+windowname,
                    # todo if there is no cooling coil, then zonename_COOLCOIL sensor won't be added
                    #  and therefore it should be omitted in all ExistingHVAC EMS programs; same for _HEATCOIL

                    Program_Line_1='if ' + windowname + '_CoolCoil==0',
                    Program_Line_2='if ' + windowname + '_HeatCoil==0',
                    Program_Line_3='set NoH_NoC_reqs = 1',
                    Program_Line_4='else',
                    Program_Line_5='set NoH_NoC_reqs = 0',
                    Program_Line_6='endif',
                    Program_Line_7='else',
                    Program_Line_8='set NoH_NoC_reqs = 0',
                    Program_Line_9='endif',
                    Program_Line_10='if ' + windowname + '_OpT<roundedACST',
                    Program_Line_11='if ' + windowname + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_12='if ' + windowname + '_OutT>MinOutTemp',
                    Program_Line_13='if ' + windowname + '_OutT < ' + windowname + '_OpT',
                    Program_Line_14='if ' + windowname + '_Occ_count > 0',
                    Program_Line_15='set meets_base_reqs = 1',
                    Program_Line_16='else',
                    Program_Line_17='set meets_base_reqs = 0',
                    Program_Line_18='endif',
                    Program_Line_19='else',
                    Program_Line_20='set meets_base_reqs = 0',
                    Program_Line_21='endif',
                    Program_Line_22='else',
                    Program_Line_23='set meets_base_reqs = 0',
                    Program_Line_24='endif',
                    Program_Line_25='else',
                    Program_Line_26='set meets_base_reqs = 0',
                    Program_Line_27='endif',
                    Program_Line_28='else',
                    Program_Line_29='set meets_base_reqs = 0',
                    Program_Line_30='endif',
                    Program_Line_31='if (NoH_NoC_reqs == 1) && (meets_base_reqs == 1)',
                    Program_Line_32='if ' + windowname + '_OpT>VST',
                    Program_Line_33='set Ventilates_HVACmode2_' + windowname + ' = 1',
                    Program_Line_34='else',
                    Program_Line_35='set Ventilates_HVACmode2_' + windowname + ' = 0',
                    Program_Line_36='endif',
                    Program_Line_37='else',
                    Program_Line_38='set Ventilates_HVACmode2_' + windowname + ' = 0',
                    Program_Line_39='endif',
                    Program_Line_40='if VentCtrl == 0',
                    Program_Line_41='if ' + windowname + '_OutT < ' + windowname + '_OpT',
                    Program_Line_42='if ' + windowname + '_OutT>MinOutTemp',
                    Program_Line_43='if ' + windowname + '_OpT > VST',
                    Program_Line_44='if ' + windowname + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_45='set Ventilates_HVACmode1_' + windowname + ' = 1',
                    Program_Line_46='else',
                    Program_Line_47='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_48='endif',
                    Program_Line_49='else',
                    Program_Line_50='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_51='endif',
                    Program_Line_52='else',
                    Program_Line_53='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_54='endif',
                    Program_Line_55='else',
                    Program_Line_56='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_57='endif',
                    Program_Line_58='elseif VentCtrl == 1',
                    Program_Line_59='if ' + windowname + '_OutT<' + windowname + '_OpT',
                    Program_Line_60='if ' + windowname + '_OutT>MinOutTemp',
                    Program_Line_61='if ' + windowname + '_OpT > ACSTnoTol',
                    Program_Line_62='if ' + windowname + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_63='set Ventilates_HVACmode1_' + windowname + ' = 1',
                    Program_Line_64='else',
                    Program_Line_65='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_66='endif',
                    Program_Line_67='else',
                    Program_Line_68='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_69='endif',
                    Program_Line_70='else',
                    Program_Line_71='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_72='endif',
                    Program_Line_73='else',
                    Program_Line_74='set Ventilates_HVACmode1_' + windowname + ' = 0',
                    Program_Line_75='endif',
                    Program_Line_76='endif',
                    Program_Line_77='if HVACmode == 0',
                    Program_Line_78='set ' + windowname + '_VentOpenFact = 0',
                    Program_Line_79='elseif HVACmode == 1',
                    Program_Line_80='if Ventilates_HVACmode1_' + windowname + ' == 1',
                    Program_Line_81='set ' + windowname + '_VentOpenFact = ' + windowname + '_MyVOF',
                    Program_Line_82='else',
                    Program_Line_83='set ' + windowname + '_VentOpenFact = 0',
                    Program_Line_84='endif',
                    Program_Line_85='elseif HVACmode == 2',
                    Program_Line_86='if Ventilates_HVACmode2_' + windowname + ' == 1',
                    Program_Line_87='if (VentCtrl==0) || (VentCtrl==1)',
                    Program_Line_88='set ' + windowname + '_VentOpenFact = 1',
                    Program_Line_89='elseif (VentCtrl==2) || (VentCtrl==3)',
                    Program_Line_90='set ' + windowname + '_VentOpenFact = ' + windowname + '_MyVOF',
                    Program_Line_91='endif',
                    Program_Line_92='else',
                    Program_Line_93='set ' + windowname + '_VentOpenFact = 0',
                    Program_Line_94='endif',
                    Program_Line_95='endif',
                )
                if verboseMode:
                    print('Added - SetWindowOperation_'+windowname+' Program')
            #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetWindowOperation_'+windowname])
    elif ScriptType.lower() == 'ex_ac' or ScriptType.lower() == 'vrf_ac':
        for zonename in self.ems_objs_name:
            if 'ApplyAST_'+zonename in programlist:
                if verboseMode:
                    print('Not added - ApplyAST_'+zonename+' Program')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Program',
                    Name='ApplyAST_'+zonename,
                    Program_Line_1='set ACST_Act_' + zonename + ' = ACST',
                    Program_Line_2='set AHST_Act_' + zonename + ' = AHST'
                    )

    del programlist


def addEMSPCMBase(self, verboseMode: bool = True):
    """
    Add EMS program calling managers for Base accim.
    Checks if some EMS program calling manager objects are already
    in the model, and otherwise adds them.

    :param self: Used as a method for class ``accim.sim.accim_Main.accimJob``
    :param verboseMode: Inherited from class ``accim.sim.accis.addAccis``
    """
    programlist = ([program.Name
                    for program
                    in self.idf1.idfobjects['EnergyManagementSystem:Program']])
    pcmlist = ([pcm.Name
                for pcm
                in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager']])

    # Programs that are called via EMS 'run' statements and therefore must NOT
    # have their own ProgramCallingManager (EnergyPlus would run them twice).
    # SetAST_CS* subprograms are invoked by SetAST_Master via 'run SetAST_CS{N}'.
    # SetAST_Master is invoked by SetAST via 'run SetAST_Master'.
    subroutine_programs = {p for p in programlist if p.startswith('SetAST_CS') or p == 'SetAST_Master'}

    priority_programs = ['SetInputData', 'SetVOFinputData', 'SetAppLimits', 'ApplyCAT']
    top_level_programs = [p for p in programlist if p not in subroutine_programs]
    top_level_programs = sorted(
        top_level_programs,
        key=lambda x: priority_programs.index(x) if x in priority_programs else len(priority_programs)
    )

    for i in top_level_programs:
        if i in pcmlist:
            if verboseMode:
                print('Not added - '+i+' Program Calling Manager')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:ProgramCallingManager',
                Name=i,
                EnergyPlus_Model_Calling_Point="BeginTimestepBeforePredictor",
                Program_Name_1=i
                )
            if verboseMode:
                print('Added - '+i+' Program Calling Manager')
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager'] if program.Name == i])

    del programlist, pcmlist, subroutine_programs, top_level_programs

# todo add argument for mm outputvariables
def addEMSOutputVariableBase(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS output variables for Base accim.
    Checks if some EMS output variables objects are already
    in the model, and otherwise adds them.

    :param self: Used as a method for class ``accim.sim.accim_Main.accimJob``
    :param ScriptType: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    EMSOutputVariableAvg_dict = {
        'Comfort Temperature': ['ComfTemp', 'C'],
        'Adaptive Cooling Setpoint Temperature': ['roundedACST', 'C'],
        'Adaptive Heating Setpoint Temperature': ['roundedAHST', 'C'],
        'Adaptive Cooling Setpoint Temperature_No Tolerance': ['ACSTnoTol', 'C'],
        'Adaptive Heating Setpoint Temperature_No Tolerance': ['AHSTnoTol', 'C'],
        'z_test_ComfStand': ['ComfStand', 'NA'],
        'z_test_ACSTaul': ['ACSTaul', 'C'],
        'z_test_ACSTall': ['ACSTall', 'C'],
        'z_test_AHSTaul': ['AHSTaul', 'C'],
        'z_test_AHSTall': ['AHSTall', 'C'],
        'z_test_CAT': ['CAT', 'C'],
        'z_test_ACSToffset': ['ACSToffset', 'C'],
        'z_test_AHSToffset': ['AHSToffset', 'C'],
        'z_test_ComfMod': ['ComfMod', 'NA'],
        'z_test_ACSTtol': ['ACSTtol', 'C'],
        'z_test_SetpointAcc': ['SetpointAcc', 'NA'],
        'z_test_CustAST_m': ['m', 'NA'],
        'z_test_CustAST_n': ['n', 'NA'],
        'z_test_AHSTtol': ['AHSTtol', 'C'],
        'z_test_AHSTtol': ['AHSTtol', 'C'],
    }
    EMSOutputVariableAvgMM_dict = {
        'Ventilation Setpoint Temperature': ['VST', 'C'],
        'Minimum Outdoor Temperature for ventilation': ['MinOutTemp', 'C'],
        'Minimum Outdoor Temperature Difference for ventilation': ['MinTempDiffVOF', 'C'],
        'Maximum Outdoor Temperature Difference for ventilation': ['MaxTempDiffVOF', 'C'],
        'Multiplier for Ventilation Opening Factor': ['MultiplierVOF', ''],
    }
    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        EMSOutputVariableAvg_dict.update(EMSOutputVariableAvgMM_dict)

    outputvariablelist = ([outvar.Name
                           for outvar
                           in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']])

    for i in EMSOutputVariableAvg_dict:
        if i in outputvariablelist:
            if verboseMode:
                print('Not added - '+i+' Output Variable')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:OutputVariable',
                Name=i,
                EMS_Variable_Name=EMSOutputVariableAvg_dict[i][0],
                Type_of_Data_in_Variable='Averaged',
                Update_Frequency='ZoneTimestep',
                EMS_Program_or_Subroutine_Name='',
                Units=EMSOutputVariableAvg_dict[i][1]
                )
            if verboseMode:
                print('Added - '+i+' Output Variable')
            # print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == i])

    # EMSOutputVariableZone_dict = {
    #     'Comfortable Hours_No Applicability': ['ComfHoursNoApp', 'H', 'Summed'],
    #     'Comfortable Hours_Applicability': ['ComfHours', 'H', 'Summed'],
    #     'Occupied Comfortable Hours_No Applicability': ['OccComfHoursNoApp', 'H', 'Summed'],
    #     'Occupied Hours': ['OccHours', 'H', 'Summed'],
    #     'Discomfortable Applicable Hot Hours': ['DiscomfAppHotHours', 'H', 'Summed'],
    #     'Discomfortable Applicable Cold Hours': ['DiscomfAppColdHours', 'H', 'Summed'],
    #     'Discomfortable Non Applicable Hot Hours': ['DiscomfNonAppHotHours', 'H', 'Summed'],
    #     'Discomfortable Non Applicable Cold Hours': ['DiscomfNonAppColdHours', 'H', 'Summed'],
    #     'Zone Floor Area': ['ZoneFloorArea', 'm2', 'Averaged'],
    #     'Zone Air Volume': ['ZoneAirVolume', 'm3', 'Averaged'],
    #     'People Occupant Count': ['Occ_count', '', 'Summed'],
    # }
    from accim.sim.dicts import EMSOutputVariableZone_dict
    for i in EMSOutputVariableZone_dict:
        for zonename in self.ems_objs_name:
            if i+'_'+zonename in outputvariablelist:
                if verboseMode:
                    print('Not added - '+i+'_'
                          + zonename + ' Output Variable')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:OutputVariable',
                    Name=i + '_' + zonename,
                    EMS_Variable_Name=EMSOutputVariableZone_dict[i][0]+'_' + zonename,
                    Type_of_Data_in_Variable=EMSOutputVariableZone_dict[i][2],
                    Update_Frequency='ZoneTimestep',
                    EMS_Program_or_Subroutine_Name='',
                    Units=EMSOutputVariableZone_dict[i][1]
                    )
                if verboseMode:
                    print('Added - '+i+'_'
                          + zonename + ' Output Variable')
            # print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == i+'_'+zonename'])

    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        EMSOutputVariableIDFzones_dict = {
            'Ventilation Hours': 'VentHours'
            }

        for i in EMSOutputVariableIDFzones_dict:
            for zonename in self.ems_objs_name:
                if i+'_'+zonename in outputvariablelist:
                    if verboseMode:
                        print('Not added - '+i+'_'
                              + zonename + ' Output Variable')
                else:
                    self.idf1.newidfobject(
                        'EnergyManagementSystem:OutputVariable',
                        Name=i + '_' + zonename,
                        EMS_Variable_Name=EMSOutputVariableIDFzones_dict[i]+'_'
                        + zonename,
                        Type_of_Data_in_Variable='Summed',
                        Update_Frequency='ZoneTimestep',
                        EMS_Program_or_Subroutine_Name='',
                        Units='H'
                        )
                    if verboseMode:
                        print('Added - '+i+'_'
                              + zonename + ' Output Variable')
                    # print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == i+'_'+zonename'])

    del outputvariablelist


def addGlobVarList(self, ScriptType: str = None, verboseMode: bool = True):
    """Remove existing Global Variable objects and add correct Global Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param ScriptType: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    globalvariablelist = ([program for program in self.idf1.idfobjects['ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE']])

    for i in range(len(globalvariablelist)):
        firstglobalvariablelist = self.idf1.idfobjects['ENERGYMANAGEMENTSYSTEM:GLOBALVARIABLE'][-1]
        self.idf1.removeidfobject(firstglobalvariablelist)

    del globalvariablelist

    self.idf1.newidfobject(
        'EnergyManagementSystem:GlobalVariable',
        Erl_Variable_1_Name='ACST',
        Erl_Variable_2_Name='AHST',
        Erl_Variable_3_Name='ACSTnoTol',
        Erl_Variable_4_Name='AHSTnoTol',
        Erl_Variable_5_Name='ComfStand',
        Erl_Variable_6_Name='ACSTaul',
        Erl_Variable_7_Name='ACSTall',
        Erl_Variable_8_Name='AHSTaul',
        Erl_Variable_9_Name='AHSTall',
        Erl_Variable_10_Name='CAT',
        Erl_Variable_11_Name='ACSToffset',
        Erl_Variable_12_Name='AHSToffset',
        Erl_Variable_13_Name='ComfMod',
        Erl_Variable_14_Name='ComfTemp',
        Erl_Variable_15_Name='ACSTtol',
        Erl_Variable_16_Name='AHSTtol',
        Erl_Variable_17_Name='SetpointAcc',
        Erl_Variable_18_Name='roundedACST',
        Erl_Variable_19_Name='roundedAHST',
        Erl_Variable_20_Name='CoolSeasonStart',
        Erl_Variable_21_Name='CoolSeasonEnd',
        Erl_Variable_22_Name='m',
        Erl_Variable_23_Name='n',
    )

    for zonename in self.ems_objs_name:
        self.idf1.newidfobject(
            'EnergyManagementSystem:GlobalVariable',
            Erl_Variable_1_Name='ComfHours_'+zonename,
            Erl_Variable_2_Name='DiscomfAppHotHours_'+zonename,
            Erl_Variable_3_Name='DiscomfAppColdHours_'+zonename,
            Erl_Variable_4_Name='DiscomfNonAppHotHours_'+zonename,
            Erl_Variable_5_Name='DiscomfNonAppColdHours_'+zonename,
            Erl_Variable_6_Name='ComfHoursNoApp_'+zonename,
            Erl_Variable_7_Name='ZoneFloorArea_' + zonename,
            Erl_Variable_8_Name='ZoneAirVolume_' + zonename,
            Erl_Variable_9_Name='OccHours_' + zonename,
            Erl_Variable_10_Name='OccComfHoursNoApp_' + zonename,
            Erl_Variable_11_Name='OccDiscomfHoursNoApp_' + zonename,
            # Erl_Variable_11_Name='VentHours_' + zonename
        )

    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        self.idf1.newidfobject(
            'EnergyManagementSystem:GlobalVariable',
            Erl_Variable_1_Name='VST',
            Erl_Variable_2_Name='VSToffset',
            Erl_Variable_3_Name='MaxWindSpeed',
            Erl_Variable_4_Name='VentCtrl',
            Erl_Variable_5_Name='HVACmode',
            Erl_Variable_6_Name='MinOutTemp',
            Erl_Variable_7_Name='MinOToffset',
            Erl_Variable_8_Name='MaxTempDiffVOF',
            Erl_Variable_9_Name='MinTempDiffVOF',
            Erl_Variable_10_Name='MultiplierVOF',
            )

        for zonename in self.ems_objs_name:
            self.idf1.newidfobject(
                'EnergyManagementSystem:GlobalVariable',
                Erl_Variable_1_Name='VentHours_' + zonename
            )
        for windowname in self.windownamelist:
            self.idf1.newidfobject(
                'EnergyManagementSystem:GlobalVariable',
                Erl_Variable_1_Name=windowname + '_MyVOF'
            )


    if verboseMode:
        print("Global variables objects have been added")

def addIntVarList(self, verboseMode: bool = True):
    """Add Internal variables objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    internalvariablelist = ([program for program in self.idf1.idfobjects['ENERGYMANAGEMENTSYSTEM:INTERNALVARIABLE']])

    for i in range(len(internalvariablelist)):
        firstinternalvariablelist = self.idf1.idfobjects['ENERGYMANAGEMENTSYSTEM:INTERNALVARIABLE'][-1]
        self.idf1.removeidfobject(firstinternalvariablelist)

    del internalvariablelist

    intvardict = {
        'ZFA_': 'Zone Floor Area',
        'ZAV_': 'Zone Air Volume'
    }

    for i in range(len(self.ems_objs_name)):
        for j in intvardict:
            self.idf1.newidfobject(
                'EnergyManagementSystem:InternalVariable',
                Name=j+self.ems_objs_name[i],
                Internal_Data_Index_Key_Name=self.ems_zonenames[i],
                Internal_Data_Type=intvardict[j]
            )
    if verboseMode:
        print("Internal variables objects have been added")

def removeExistingOutputVariables(self):
    """Remove existing Output:Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    """
    EnvironmentalImpactFactorslist = ([output for output in self.idf1.idfobjects['Output:EnvironmentalImpactFactors']])
    outputmeterlist = ([output for output in self.idf1.idfobjects['Output:Meter']])
    alloutputs = ([output for output in self.idf1.idfobjects['Output:Variable']])

    for i in range(len(EnvironmentalImpactFactorslist)):
        firstEnvironmentalImpactFactor = self.idf1.idfobjects['Output:EnvironmentalImpactFactors'][-1]
        self.idf1.removeidfobject(firstEnvironmentalImpactFactor)
    for i in range(len(outputmeterlist)):
        firstoutputmeter = self.idf1.idfobjects['Output:Meter'][-1]
        self.idf1.removeidfobject(firstoutputmeter)
    for i in range(len(alloutputs)):
        firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
        self.idf1.removeidfobject(firstoutput)

    del EnvironmentalImpactFactorslist, outputmeterlist, alloutputs, \
        # firstEnvironmentalImpactFactor, firstoutputmeter, firstoutput

def removeDuplicatedOutputVariables(self):
    """Remove duplicated Output:Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    """
    for freq in ['Timestep', 'Hourly', 'Daily', 'Monthly', 'Runperiod']:
        alloutputs = [
            output
            for output
            in self.idf1.idfobjects['Output:Variable']
            if freq == output.Reporting_Frequency
        ]
        unique_list = []
        duplicated_list = []
        for i in alloutputs:
            if i.Variable_Name not in unique_list:
                unique_list.append(i)
            else:
                duplicated_list.append(i)
        for j in range(len(duplicated_list)):
            firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
            self.idf1.removeidfobject(firstoutput)

    ## Alternative method (probably better)
    # alloutputs = [
    #     output
    #     for output
    #     in self.idf1.idfobjects['Output:Variable']
    # ]
    # unique_list = []
    # duplicated_list = []
    # for i in alloutputs:
    #     if i not in unique_list:
    #         unique_list.append(i)
    #     else:
    #         duplicated_list.append(i)
    # for j in range(len(duplicated_list)):
    #     firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
    #     self.idf1.removeidfobject(firstoutput)

    # del alloutputs, firstoutput, unique_list, duplicated_list

def outputsSpecified(
        self,
        remove_or_keep: str = None,
):
    """Remove duplicated Output:Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param remove_or_keep: Inherited from :class:``accim.sim.accis.addAccis``
    """
    all_outputs_to_delete = []
    for freq in ['Timestep', 'Hourly', 'Daily', 'Monthly', 'Runperiod']:
        alloutputs = [
                output
                for output
                in self.idf1.idfobjects['Output:Variable']
                if freq == output.Reporting_Frequency
        ]
        if len(alloutputs) == 0:
            continue
        else:
            alloutputsnames = [
                output.Variable_Name
                for output
                in self.idf1.idfobjects['Output:Variable']
                if freq == output.Reporting_Frequency
            ]
            alloutputsnames = list(dict.fromkeys(alloutputsnames))
            print(f'\nThe current existing outputs for {freq} Frequency are:')
            print(*alloutputsnames, sep='\n')
            if remove_or_keep is None:
                remove_or_keep = input('Do you want to remove some input or keep it and remove all others? Please enter remove or keep:')
                custom_outputs = list(str(output) for output in input('Please enter these outputs (which must be contained in the list above) separated by semicolon (;): ').split(';'))
                if remove_or_keep.lower() == 'remove':
                    outputs_to_delete = [i for i in alloutputs if any([i.Variable_Name == j for j in custom_outputs])]
                elif remove_or_keep.lower() == 'keep':
                    outputs_to_delete = [i for i in alloutputs if all([i.Variable_Name != j for j in custom_outputs])]
                remove_or_keep = None
                outputs_to_keep = [i for i in alloutputs if i not in outputs_to_delete]

            # outputs_to_delete = []
            # for i in outputs_to_delete:
            #     for j in alloutputs:
            #         if remove_or_keep.lower() == 'remove':
            #             if i in j.Variable_Name:
            #                 outputs_to_delete.append(j)
            #         if remove_or_keep.lower() == 'keep':
            #             if i in j.Variable_Name:
            #                 outputs_to_delete.append(j)

            all_outputs_to_delete.extend(outputs_to_delete)


        # unique_list = []
        # duplicated_list = []
        # for i in alloutputs:
        #     if i.Variable_Name not in unique_list:
        #         unique_list.append(i)
        #     else:
        #         duplicated_list.append(i)
    # for j in range(len(all_outputs_to_delete)):
    #     firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
    #     self.idf1.removeidfobject(firstoutput)

    for j in all_outputs_to_delete:
        # firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
        self.idf1.removeidfobject(j)


    # del alloutputs, firstoutput, unique_list, duplicated_list


def genOutputDataframe(
        self,
        idf_filename: str = None,
):
    """
    Used to generate a pandas DataFrame instance containing all Output:Variable objects in the model.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param idf_filename: Inherited from :class:``accim.sim.accis.addAccis``
    """
    import pandas as pd
    alloutputs = [
        output
        for output
        in self.idf1.idfobjects['Output:Variable']
    ]
    self.df_outputs_temp = pd.DataFrame(columns=['file', 'key_value', 'variable_name', 'reporting_frequency', 'schedule_name'])
    for i in range(len(alloutputs)):
        self.df_outputs_temp.loc[i, 'file'] = idf_filename
        self.df_outputs_temp.loc[i, 'key_value'] = alloutputs[i].Key_Value
        self.df_outputs_temp.loc[i, 'variable_name'] = alloutputs[i].Variable_Name
        self.df_outputs_temp.loc[i, 'reporting_frequency'] = alloutputs[i].Reporting_Frequency
        self.df_outputs_temp.loc[i, 'schedule_name'] = alloutputs[i].Schedule_Name

def takeOutputDataFrame(
        self,
        idf_filename,
        df_outputs_in,
        verboseMode,
        singleidf=False,
):
    """
    Used to read a pandas DataFrame containing the Output:Variable objects to be kept.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param idf_filename: Inherited from :class:``accim.sim.accis.addAccis``
    :param df_outputs_in: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    import pandas as pd

    if df_outputs_in is not None:
        if 'reporting_frequency' not in df_outputs_in.columns and 'frequency' in df_outputs_in.columns:
            df_outputs_in = df_outputs_in.rename(columns={'frequency': 'reporting_frequency'})

    if not singleidf:
        df_outputs_in = df_outputs_in[
            df_outputs_in['file'].str.contains(idf_filename)
        ]
        df_outputs_in = df_outputs_in.set_index([pd.RangeIndex(len(df_outputs_in))])

    alloutputs = [
        output
        for output
        in self.idf1.idfobjects['Output:Variable']
    ]
    for i in alloutputs:
        self.idf1.removeidfobject(i)

    for i in df_outputs_in.index:
        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value=df_outputs_in.loc[i, 'key_value'],
            Variable_Name=df_outputs_in.loc[i, 'variable_name'],
            Reporting_Frequency=df_outputs_in.loc[i, 'reporting_frequency'].capitalize(),
            Schedule_Name=df_outputs_in.loc[i, 'schedule_name']
            )
        if verboseMode:
            print('Added - '+df_outputs_in.loc[i, 'key_value']+ ' '+df_outputs_in.loc[i, 'variable_name']+' Output:Variable data')

def addOutputVariablesSimplified(
        self,
        Outputs_freq: any = None,
        TempCtrl: str = None,
        verboseMode: bool = True
):
    """
    Add simplified Output:Variable objects for accim.
    Remove all outputs and add only VFR outdoor unit consumption
    and operative temperature.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param Outputs_freq: Inherited from :class:``accim.sim.accis.addAccis``
    :param TempCtrl: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``

    """

    additionaloutputs = [
        # 'Zone Thermostat Operative Temperature',
        'Zone Operative Temperature',
        'Cooling Coil Total Cooling Rate',
        'Heating Coil Heating Rate',
    ]

    if TempCtrl.lower() == 'pmv':
        additionaloutputs.extend([
            'Zone Thermal Comfort Fanger Model PMV',
            'Zone Thermal Comfort Fanger Model PPD'
        ])

    for freq in Outputs_freq:
        for addittionaloutput in additionaloutputs:
            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value='*',
                Variable_Name=addittionaloutput,
                Reporting_Frequency=freq.capitalize(),
                Schedule_Name=''
                )
            if verboseMode:
                print('Added - '+addittionaloutput+' Output:Variable data')

    del additionaloutputs


def addOutputVariablesStandard(
        self,
        Outputs_freq: any = None,
        ScriptType: str = None,
        TempCtrl: str = None,
        verboseMode: bool = True
):
    """Add Output:Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param Outputs_freq: Inherited from :class:``accim.sim.accis.addAccis``
    :param ScriptType: Inherited from :class:``accim.sim.accis.addAccis``
    :param TempCtrl: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """

    EMSoutputvariablenamelist = ([outputvariable.Name
                           for outputvariable
                           in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']])
    addittionaloutputs = [
        'Zone Thermostat Operative Temperature',
        'Zone Thermostat Air Temperature',
        'Zone Operative Temperature',
        'Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature',
        'Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature',
        'Cooling Coil Total Cooling Rate',
        'Heating Coil Heating Rate',
        'Facility Total HVAC Electric Demand Power',
        'Facility Total HVAC Electricity Demand Rate',
        # todo maybe create a new output type to include this variable, to be used in case of tests
        'AFN Surface Venting Window or Door Opening Factor',
        'AFN Zone Infiltration Air Change Rate',
        'AFN Zone Infiltration Volume',
        'AFN Zone Ventilation Air Change Rate',
        'AFN Zone Ventilation Volume',
        'Zone Ventilation Standard Density Air Change Rate',
    ]
    if TempCtrl.lower() == 'pmv':
        addittionaloutputs.extend([
            'Zone Thermal Comfort Fanger Model PMV',
            'Zone Thermal Comfort Fanger Model PPD'
        ])

    for freq in Outputs_freq:
        outputnamelist = (
            [
                output.Variable_Name
                for output
                in self.idf1.idfobjects['Output:Variable']
                if output.Reporting_Frequency == freq.capitalize()
            ]
        )
        for outputvariable in EMSoutputvariablenamelist:
            if outputvariable in outputnamelist:
                if verboseMode:
                    print('Not added - '+outputvariable+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')
            elif outputvariable.startswith("WIP"):
                if verboseMode:
                    print('Not added - '+outputvariable+' Output:Variable data because its WIP')
            elif outputvariable.startswith('Adaptive Thermal Comfort Cost Index'):
                if verboseMode:
                    print('Not added - '+outputvariable+' Output:Variable data because its ATCCI')
            else:
                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value='*',
                    Variable_Name=outputvariable,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                    )
                if verboseMode:
                    print('Added - '+outputvariable+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')
        #        print([output for output in self.idf1.idfobjects['Output:Variable'] if output.Variable_Name == outputvariable])

        for addittionaloutput in addittionaloutputs:
            if addittionaloutput in outputnamelist:
                if verboseMode:
                    print('Not added - '+addittionaloutput+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')
            else:
                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value='*',
                    Variable_Name=addittionaloutput,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                    )
                if verboseMode:
                    print('Added - '+addittionaloutput+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')

        outputlist = (
            [
                output
                for output
                in self.idf1.idfobjects['Output:Variable']
                if output.Reporting_Frequency == freq.capitalize()
            ]
        )
        for i in outputlist:
            for addittionaloutput in addittionaloutputs:
                if addittionaloutput in i.Variable_Name:
                    i.Schedule_Name = ''

        siteAddOutputs = [
            'Site Outdoor Air Drybulb Temperature',
            'Site Wind Speed',
            'Site Outdoor Air Relative Humidity'
        ]

        # other_site_outputs = [
        #     'Site Outdoor Air Drybulb Temperature [C]',
        #     'Site Outdoor Air Dewpoint Temperature [C]',
        #     'Site Outdoor Air Wetbulb Temperature [C]',
        #     'Site Outdoor Air Humidity Ratio [kgWater/kgAir]',
        #     'Site Outdoor Air Relative Humidity [%]',
        #     'Site Outdoor Air Barometric Pressure [Pa]',
        #     'Site Wind Speed [m/s]',
        #     'Site Wind Direction [deg]',
        #     'Site Sky Temperature [C]',
        #     'Site Horizontal Infrared Radiation Rate per Area [W/m2]',
        #     'Site Difuse Solar Radiation Rate per Area [W/m2]',
        #     'Site Direct Solar Radiation Rate per Area [W/m2]',
        #     'Site Total Sky Cover []',
        #     'Site Opaque Sky Cover []',
        #     'Site Precipitation Depth [m]',
        #     'Site Ground Refected Solar Radiation Rate per Area [W/m2]',
        #     'Site Ground Temperature [C]',
        #     'Site Surface Ground Temperature [C]',
        #     'Site Deep Ground Temperature [C]',
        #     'Site Simple Factor Model Ground Temperature [C]',
        #     'Site Outdoor Air Enthalpy [J/kg]',
        #     'Site Outdoor Air Density [kg/m3]',
        #     'Site Solar Azimuth Angle [deg]',
        #     'Site Solar Altitude Angle [deg]',
        #     'Site Solar Hour Angle [deg]',
        #     'Site Rain Status []',
        #     'Site Snow on Ground Status []',
        #     'Site Exterior Horizontal Sky Illuminance [lux]',
        #     'Site Exterior Horizontal Beam Illuminance [lux]',
        #     'Site Exterior Beam Normal Illuminance [lux]',
        #     'Site Sky Difuse Solar Radiation Luminous Eﬀcacy [lum/W]',
        #     'Site Beam Solar Radiation Luminous Eﬀcacy [lum/W]',
        #     'Site Daylighting Model Sky Clearness []',
        #     'Sky Brightness for Daylighting Calculation []',
        #     'Site Daylight Saving Time Status []',
        #     'Site Day Type Index []',
        #     'Site Mains Water Temperature [C]',
        # ]

        for addittionaloutput in siteAddOutputs:
            if addittionaloutput in outputnamelist:
                if verboseMode:
                    print('Not added - '+addittionaloutput+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')
            else:
                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value='Environment',
                    Variable_Name=addittionaloutput,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                    )
                if verboseMode:
                    print('Added - '+addittionaloutput+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')

        for zonename in self.ems_objs_name:
            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value='AHST_Sch_'+zonename,
                Variable_Name='Schedule Value',
                Reporting_Frequency=freq.capitalize(),
                Schedule_Name=''
                )
            if verboseMode:
                print('Added - AHST_Sch_'+zonename+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')

            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value='ACST_Sch_'+zonename,
                Variable_Name='Schedule Value',
                Reporting_Frequency=freq.capitalize(),
                Schedule_Name=''
                )
            if verboseMode:
                print('Added - ACST_Sch_'+zonename+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')

        if hasattr(self, 'natural_ventilation_type') and self.natural_ventilation_type == 'Scheduled':
            for sch_name in self.scheduled_ventilation_dict.values():
                output_exist = any(
                    out.Variable_Name == 'Schedule Value' and out.Key_Value == sch_name 
                    for out in self.idf1.idfobjects['Output:Variable']
                    if out.Reporting_Frequency == freq.capitalize()
                )
                if not output_exist:
                    self.idf1.newidfobject(
                        'Output:Variable',
                        Key_Value=sch_name,
                        Variable_Name='Schedule Value',
                        Reporting_Frequency=freq.capitalize(),
                        Schedule_Name=''
                    )
                    if verboseMode:
                        print('Added - Schedule Value for ' + sch_name + ' Reporting Frequency' + freq.capitalize() + ' Output:Variable data')

        # for zonename in self.zonenames_orig:
        #     self.idf1.newidfobject(
        #         'Output:Variable',
        #         Key_Value=zonename,
        #         Variable_Name='Zone Operative Temperature',
        #         Reporting_Frequency=freq.capitalize(),
        #         Schedule_Name=''
        #         )
        #     if verboseMode:
        #         print('Added - '+zonename+' Reporting Frequency'+freq.capitalize()+' Zone Operative Temperature Output:Variable data')

        if 'vrf' in ScriptType.lower():
            VRFoutputs = [
                'VRF Heat Pump Cooling Electricity Energy',
                'VRF Heat Pump Heating Electricity Energy',
            ]

            for addittionaloutput in VRFoutputs:
                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value='*',
                    Variable_Name=addittionaloutput,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print('Added - ' + addittionaloutput +' Reporting Frequency'+freq.capitalize() + ' Output:Variable data')

            for zonename in self.zonenames:
                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value=zonename + ' VRF Indoor Unit DX Cooling Coil',
                    Variable_Name='Cooling Coil Total Cooling Rate',
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print('Added - ' + zonename + ' VRF Indoor Unit DX Cooling Coil'+' Reporting Frequency'+freq.capitalize() + ' Output:Variable data')

                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value=zonename + ' VRF Indoor Unit DX Heating Coil',
                    Variable_Name='Heating Coil Heating Rate',
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                )
                if verboseMode:
                    print('Added - ' + zonename + ' VRF Indoor Unit DX Heating Coil'+' Reporting Frequency '+freq.capitalize()+' Output:Variable data')

    meter_objects = [
        'EnergyTransfer:HVAC',
        'Electricity:HVAC',
        'DistrictHeating:Facility',
        'DistrictCooling:Facility',
        'Heating:EnergyTransfer',
        'Cooling:EnergyTransfer',
        'Heating:Electricity',
        'Cooling:Electricity',
    ]

    for freq in Outputs_freq:
        # Get existing meters for this frequency to avoid duplicates
        # Note: Key_Name is the field for the meter name
        current_meters = [
            m.Key_Name for m in self.idf1.idfobjects['Output:Meter']
            if m.Reporting_Frequency.upper() == freq.upper()
        ]

        for meter in meter_objects:
            if meter not in current_meters:
                self.idf1.newidfobject(
                    'Output:Meter',
                    Key_Name=meter,
                    Reporting_Frequency=freq.capitalize()
                )
                if verboseMode:
                    print(f"Added Output:Meter for {meter} ({freq})")
            else:
                warnings.warn(f"Output:Meter '{meter}' ({freq}) already exists. Skipping.")

    del EMSoutputvariablenamelist, outputnamelist, addittionaloutputs,


def addOutputVariablesDetailed(
        self,
        Outputs_freq: any = None,
        verboseMode: bool = True
):
    """Add Output:Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param Outputs_freq: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """

    addittionaloutputs = [
        'AFN Surface Venting Window or Door Opening Factor',
        'Zone Ventilation Standard Density Air Change Rate',
    ]

    for freq in Outputs_freq:
        outputnamelist = (
            [
                output.Variable_Name
                for output
                in self.idf1.idfobjects['Output:Variable']
                if output.Reporting_Frequency == freq.capitalize()
            ]
        )

        for addittionaloutput in addittionaloutputs:
            if addittionaloutput in outputnamelist:
                if verboseMode:
                    print('Not added - '+addittionaloutput+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')
            else:
                self.idf1.newidfobject(
                    'Output:Variable',
                    Key_Value='*',
                    Variable_Name=addittionaloutput,
                    Reporting_Frequency=freq.capitalize(),
                    Schedule_Name=''
                    )
                if verboseMode:
                    print('Added - '+addittionaloutput+' Reporting Frequency'+freq.capitalize()+' Output:Variable data')

        # Add outputs for scheduled ventilation opening fractions
        if hasattr(self, 'natural_ventilation_type') and self.natural_ventilation_type == 'Scheduled':
            for sch_name in self.scheduled_ventilation_dict.values():
                output_exist = any(
                    out.Variable_Name == 'Schedule Value' and out.Key_Value == sch_name 
                    for out in self.idf1.idfobjects['Output:Variable']
                    if out.Reporting_Frequency == freq.capitalize()
                )
                if not output_exist:
                    self.idf1.newidfobject(
                        'Output:Variable',
                        Key_Value=sch_name,
                        Variable_Name='Schedule Value',
                        Reporting_Frequency=freq.capitalize(),
                        Schedule_Name=''
                    )
                    if verboseMode:
                        print('Added - Schedule Value for ' + sch_name + ' Reporting Frequency' + freq.capitalize() + ' Output:Variable data')

def addEMSSensorsBase(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS sensors for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param ScriptType: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    sensorlist = ([sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']])

    ppl_key_name = self.ems_objs_key[0]

    # spacelist = [i for i in self.idf1.idfobjects['spacelist']]

    if 'RMOT' in sensorlist:
        if verboseMode:
            print('Not added - RMOT Sensor')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Sensor',
            Name='RMOT',
            #todo if there is spacelist, the key name must be f'{space.Name} {people.Name}', for instance 'PERIMETER_ZN_1 OFFICE WHOLEBUILDING - SM OFFICE PEOPLE'
            OutputVariable_or_OutputMeter_Index_Key_Name=ppl_key_name,
            OutputVariable_or_OutputMeter_Name='Zone Thermal Comfort CEN 15251 Adaptive Model Running Average Outdoor Air Temperature'
            )
        if verboseMode:
            print('Added - RMOT Sensor')
    #    print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name=='RMOT'])

    if 'PMOT' in sensorlist:
        if verboseMode:
            print('Not added - PMOT Sensor')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Sensor',
            Name='PMOT',
            OutputVariable_or_OutputMeter_Index_Key_Name=ppl_key_name,
            OutputVariable_or_OutputMeter_Name='Zone Thermal Comfort ASHRAE 55 Adaptive Model Running Average Outdoor Air Temperature'
            )
        if verboseMode:
            print('Added - PMOT Sensor')
    #    print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name=='PMOT'])


    # if self.spacelist_use:
    #     for i in range(len(self.spacenames_for_ems_uniquekey)):
    #         if f'Occ_count_{self.spacenames_for_ems_name[i]}' in sensorlist:
    #             if verboseMode:
    #                 print(f'Not added - Occ_count_{self.spacenames_for_ems_name[i]} Sensor')
    #         else:
    #             self.idf1.newidfobject(
    #                 'EnergyManagementSystem:Sensor',
    #                 Name=f'Occ_count_{self.spacenames_for_ems_name[i]}',
    #                 OutputVariable_or_OutputMeter_Index_Key_Name=self.spacenames_for_ems_uniquekey[i],
    #                 OutputVariable_or_OutputMeter_Name='People Occupant Count'
    #             )
    #             if verboseMode:
    #                 print(f'Added - Occ_count_{self.spacenames_for_ems_name[i]} Sensor')
    # else:

    occ_count_keys = self.ems_objs_key

    for i in range(len(self.ems_objs_name)):
        if f'Occ_count_{self.ems_objs_name[i]}' in sensorlist:
            if verboseMode:
                print(f'Not added - Occ_count_{self.ems_objs_name[i]} Sensor')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=f'Occ_count_{self.ems_objs_name[i]}',
                OutputVariable_or_OutputMeter_Index_Key_Name=occ_count_keys[i],
                OutputVariable_or_OutputMeter_Name='People Occupant Count'
            )
            if verboseMode:
                print(f'Added - Occ_count_{self.ems_objs_name[i]} Sensor')


    for i in range(len(self.ems_objs_name)):
        if self.ems_objs_name[i]+'_OpT' in sensorlist:
            if verboseMode:
                print('Not added - '+self.ems_objs_name[i]+'_OpT Sensor')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=self.ems_objs_name[i]+'_OpT',
                OutputVariable_or_OutputMeter_Index_Key_Name=self.ems_zonenames[i],
                OutputVariable_or_OutputMeter_Name='Zone Operative Temperature'
                )
            if verboseMode:
                print('Added - '+self.ems_objs_name[i]+'_OpT Sensor')
    #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_OpT'])


        
        if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
            if self.ems_objs_name[i]+'_WindSpeed' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.ems_objs_name[i]+'_WindSpeed Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.ems_objs_name[i]+'_WindSpeed',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.ems_zonenames[i],
                    OutputVariable_or_OutputMeter_Name='Zone Outdoor Air Wind Speed'
                    )
                if verboseMode:
                    print('Added - '+self.ems_objs_name[i]+'_WindSpeed Sensor')
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_WindSpeed'])
            if self.ems_objs_name[i]+'_OutT' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.ems_objs_name[i]+'_OutT Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.ems_objs_name[i]+'_OutT',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.ems_zonenames[i],
                    OutputVariable_or_OutputMeter_Name='Zone Outdoor Air Drybulb Temperature'
                    )
                if verboseMode:
                    print('Added - '+self.ems_objs_name[i]+'_OutT Sensor')
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_OutT']

    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        for i in range(len(self.windownamelist)):
            if self.windownamelist[i]+'_OpT' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_OpT Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_OpT',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[i][0],
                    OutputVariable_or_OutputMeter_Name='Zone Operative Temperature'
                )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_OpT Sensor')

            if self.windownamelist[i]+'_WindSpeed' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_WindSpeed Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_WindSpeed',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[i][0],
                    OutputVariable_or_OutputMeter_Name='Zone Outdoor Air Wind Speed'
                    )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_WindSpeed Sensor')

            if self.windownamelist[i]+'_OutT' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_WindSpeed Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_OutT',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.windownamelist_orig_split[i][0],
                    OutputVariable_or_OutputMeter_Name='Zone Outdoor Air Drybulb Temperature'
                    )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_OutT Sensor')

            if self.windownamelist[i]+'_Occ_count' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_Occ_count Sensor')
            else:
                correct_key = 'People '+self.windownamelist_orig_split[i][0]
                # Try to find the exact key from ems_objs_key
                for idx, z_name in enumerate(self.ems_zonenames):
                    if z_name.lower() == self.windownamelist_orig_split[i][0].lower():
                        correct_key = self.ems_objs_key[idx]
                        break
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_Occ_count',
                    OutputVariable_or_OutputMeter_Index_Key_Name=correct_key,
                    OutputVariable_or_OutputMeter_Name='People Occupant Count'
                    )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_Occ_count Sensor')

    if 'OutT' in sensorlist:
        if verboseMode:
            print('Not added - OutT Sensor')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Sensor',
            Name='OutT',
            OutputVariable_or_OutputMeter_Index_Key_Name='Environment',
            OutputVariable_or_OutputMeter_Name='Site Outdoor Air Drybulb Temperature'
            )
        if verboseMode:
            print('Added - OutT Sensor')

    # if 'HVACConsump' in sensorlist:
    #     print('Not added - HVACConsump Sensor')
    # else:
    #     self.idf1.newidfobject(
    #         'EnergyManagementSystem:Sensor',
    #         Name='HVACConsump',
    #         OutputVariable_or_OutputMeter_Index_Key_Name='Whole Building',
    #         OutputVariable_or_OutputMeter_Name='Facility Total HVAC Electric Demand Power'
    #         )
    #     print('Added - HVACConsump Sensor')
    #     print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name=='HVACConsump'])


    del sensorlist


def addEMSActuatorsBase(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS actuators for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param ScriptType: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    actuatorlist = ([actuator.Name for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator']])

    for i in range(len(self.ems_objs_name)):
        if 'AHST_Act_'+self.ems_objs_name[i] in actuatorlist:
            if verboseMode:
                print('Not added - AHST_Act_'+self.ems_objs_name[i]+' Actuator')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Actuator',
                Name='AHST_Act_'+self.ems_objs_name[i],
                Actuated_Component_Unique_Name='AHST_Sch_'+self.ems_objs_name[i],
                Actuated_Component_Type='Schedule:Compact',
                Actuated_Component_Control_Type='Schedule Value'
                )
            if verboseMode:
                print('Added - AHST_Act_'+self.ems_objs_name[i]+' Actuator')
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='AHST_Act_'+zonename])

        if 'ACST_Act_'+self.ems_objs_name[i] in actuatorlist:
            if verboseMode:
                print('Not added - ACST_Act_'+self.ems_objs_name[i]+' Actuator')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Actuator',
                Name='ACST_Act_'+self.ems_objs_name[i],
                Actuated_Component_Unique_Name='ACST_Sch_'+self.ems_objs_name[i],
                Actuated_Component_Type='Schedule:Compact',
                Actuated_Component_Control_Type='Schedule Value'
                )
            if verboseMode:
                print('Added - ACST_Act_'+self.ems_zonenames[i]+' Actuator')
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='ACST_Act_'+zonename])

    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        for i in range(len(self.windownamelist)):
            if self.windownamelist[i]+'_VentOpenFact' in actuatorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_OpT Actuator')
            else:
                if hasattr(self, 'natural_ventilation_type') and self.natural_ventilation_type == 'Scheduled':
                    self.idf1.newidfobject(
                        'EnergyManagementSystem:Actuator',
                        Name=self.windownamelist[i]+'_VentOpenFact',
                        Actuated_Component_Unique_Name=self.scheduled_ventilation_dict[self.windownamelist_orig[i]],
                        Actuated_Component_Type='Schedule:Constant',
                        Actuated_Component_Control_Type='Schedule Value'
                    )
                else:
                    self.idf1.newidfobject(
                        'EnergyManagementSystem:Actuator',
                        Name=self.windownamelist[i]+'_VentOpenFact',
                        Actuated_Component_Unique_Name=self.windownamelist_orig[i],
                        Actuated_Component_Type='AirFlow Network Window/Door Opening',
                        Actuated_Component_Control_Type='Venting Opening Factor'
                        )
                if verboseMode:
                    print('Added - '+self.windownamelist[i]+'_VentOpenFact Actuator')
    del actuatorlist


def makeAverages(self, verboseMode):
    """
    Makes averages for some variables.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    #Make average for hours variables
    gvs = [i.obj for i in self.idf1.idfobjects['EnergyManagementSystem:GlobalVariable']]

    vars_to_avg = {
        'ComfHours': {'gvs': []},
        'DiscomfAppHotHours': {'gvs': []},
        'DiscomfAppColdHours': {'gvs': []},
        'DiscomfNonAppHotHours': {'gvs': []},
        'DiscomfNonAppColdHours': {'gvs': []},
        'ComfHoursNoApp': {'gvs': []},
        'OccHours': {'gvs': []},
        'OccComfHoursNoApp': {'gvs': []},
        'OccDiscomfHoursNoApp': {'gvs': []},
        'VentHours': {'gvs': []},
    }

    for i in gvs:
        for j in i:
            if 'energymanagementsystem' not in j.lower():
                for k, key in enumerate(vars_to_avg.keys()):
                    if key.lower() == j.split('_')[0].lower():
                        vars_to_avg[key]['gvs'].append(j)
                        # gvs_all.append(j)

    for k, key in enumerate(vars_to_avg.keys()):
        vars_to_avg[key].update({'summed_gvs': '+'.join(vars_to_avg[key]['gvs'])})

    from accim.sim.dicts import EMSOutputVariableZone_dict

    gvs_all = []
    for i in gvs:
        for j in i:
            if 'energymanagementsystem' not in j.lower():
                gvs_all.append(j)

    for i, key in enumerate(vars_to_avg.keys()):

        if f'{key}BuildAvg' in gvs_all:
            if verboseMode:
                print(f'Not added - Make{key}BuildAvg GlobalVariable')
        else:
            self.idf1.newidfobject(
                key='EnergyManagementSystem:GlobalVariable',
                Erl_Variable_1_Name=f'{key}BuildAvg'
            )
            if verboseMode:
                print(f'Added - {key}BuildAvg GlobalVariable')

        if f'Make{key}BuildAvg' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager']]:
            if verboseMode:
                print(f'Not added - Make{key}BuildAvg ProgramCallingManager')
        else:
            self.idf1.newidfobject(
                key='EnergyManagementSystem:ProgramCallingManager',
                Name=f'Make{key}BuildAvg',
                EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
                Program_Name_1=f'Make{key}BuildAvg',
            )
            if verboseMode:
                print(f'Added - Make{key}BuildAvg ProgramCallingManager')

        if f'Make{key}BuildAvg' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:Program']]:
            if verboseMode:
                print(f'Not added - Make{key}BuildAvg Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name=f'Make{key}BuildAvg',
                Program_Line_1=f'set {key}BuildAvgNum = ' + vars_to_avg[key]['summed_gvs'],
                Program_Line_2=f'set {key}BuildAvgDen = ' + str(len(vars_to_avg[key]['gvs'])),
                Program_Line_3=f'set {key}BuildAvg = {key}BuildAvgNum/{key}BuildAvgDen'
            )
            if verboseMode:
                print(f'Added - Make{key}BuildAvg Program')

        for j, output in enumerate(EMSOutputVariableZone_dict.keys()):
            if EMSOutputVariableZone_dict[output][0].lower() == key.lower():

                if f'{output}_Building_Average' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']]:
                    if verboseMode:
                        print(f'Not added - {output}_Building_Average EMS OutputVariable')
                else:
                    self.idf1.newidfobject(
                        key='EnergyManagementSystem:OutputVariable',
                        Name=f'{output}_Building_Average',
                        EMS_Variable_Name=f'{key}BuildAvg',
                        Type_of_Data_in_Variable='Summed',
                        Update_Frequency='ZoneTimestep',
                        Units='H'
                    )
                    if verboseMode:
                        print(f'Added - {output}_Building_Average EMS OutputVariable')

                # self.idf1.newidfobject(
                #     key='Output:Variable',
                #     Key_Value='*',
                #     Variable_Name=f'{output}_Building_Average',
                #     Reporting_Frequency='Hourly'
                # )

    #Make average for output:variable (sensors) objects

    output_vars = {
        'Zone Operative Temperature': {
            'sensor_name': 'OpT',
            'short_name': 'OpTemp',
            'units': 'C',
            'agg': 'Averaged'
        },
        'AFN Zone Ventilation Air Change Rate': {
            'sensor_name': 'VentACR',
            'short_name': 'VentACR',
            'units': 'ach',
            'agg': 'Averaged'
        },
        'AFN Zone Infiltration Air Change Rate': {
            'sensor_name': 'InfACR',
            'short_name': 'InfACR',
            'units': 'ach',
            'agg': 'Averaged'
        }

    }

    for k, v in output_vars.items():

        sensorlist = [
            i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if
            i.OutputVariable_or_OutputMeter_Name == k
        ]
        for i, zone in enumerate(self.zonenames_orig):
            sensorname = self.zonenames[i]+'_'+output_vars[k]['sensor_name']
            if sensorname in sensorlist:
                if verboseMode:
                    print('Not added - '+sensorname+' Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=sensorname,
                    OutputVariable_or_OutputMeter_Index_Key_Name=zone,
                    OutputVariable_or_OutputMeter_Name=k
                )
                if verboseMode:
                    print('Added - '+sensorname+' Sensor')

        sensorlist = [
            i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if
            i.OutputVariable_or_OutputMeter_Name == k
        ]
        output_var_sum = '+'.join(sensorlist)


        key = output_vars[k]['short_name']
        if f'{key}BuildAvg' in gvs_all:
            if verboseMode:
                print(f'Not added - Make{key}BuildAvg GlobalVariable')
        else:
            self.idf1.newidfobject(
                key='EnergyManagementSystem:GlobalVariable',
                Erl_Variable_1_Name=f'{key}BuildAvg'
            )
            if verboseMode:
                print(f'Added - {key}BuildAvg GlobalVariable')

        if f'Make{key}BuildAvg' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager']]:
            if verboseMode:
                print(f'Not added - Make{key}BuildAvg ProgramCallingManager')
        else:
            self.idf1.newidfobject(
                key='EnergyManagementSystem:ProgramCallingManager',
                Name=f'Make{key}BuildAvg',
                EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
                Program_Name_1=f'Make{key}BuildAvg',
            )
            if verboseMode:
                print(f'Added - Make{key}BuildAvg ProgramCallingManager')

        if f'Make{key}BuildAvg' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:Program']]:
            if verboseMode:
                print(f'Not added - Make{key}BuildAvg Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name=f'Make{key}BuildAvg',
                Program_Line_1=f'set {key}BuildAvgNum = ' + output_var_sum,
                Program_Line_2=f'set {key}BuildAvgDen = ' + str(len(sensorlist)),
                Program_Line_3=f'set {key}BuildAvg = {key}BuildAvgNum/{key}BuildAvgDen'
            )
            if verboseMode:
                print(f'Added - Make{key}BuildAvg Program')


        if f'{k}_Building_Average' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']]:
            if verboseMode:
                print(f'Not added - {k}_Building_Average EMS OutputVariable')
        else:
            self.idf1.newidfobject(
                key='EnergyManagementSystem:OutputVariable',
                Name=f'{k}_Building_Average',
                EMS_Variable_Name=f'{key}BuildAvg',
                Type_of_Data_in_Variable=output_vars[k]['agg'],
                Update_Frequency='ZoneTimestep',
                Units=output_vars[k]['units']
            )
            if verboseMode:
                print(f'Added - {k}_Building_Average EMS OutputVariable')

