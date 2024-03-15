"""Add EMS objects in common to both ExistingHVAC and VRFsystem."""


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
            Program_Line_1='if ComfStand == 1',
            Program_Line_2='set ComfTemp = RMOT*0.33+18.8',
            Program_Line_3='elseif ComfStand == 2',
            Program_Line_4='set ComfTemp = PMOT*0.31+17.8',
            Program_Line_5='elseif ComfStand == 3',
            Program_Line_6='set ComfTemp = PMOT*0.48+14.4',
            Program_Line_7='elseif ComfStand == 4',
            Program_Line_8='set ComfTemp = 0',
            Program_Line_9='elseif ComfStand == 5',
            Program_Line_10='set ComfTemp = 0',
            Program_Line_11='elseif ComfStand == 6',
            Program_Line_12='set ComfTemp = 0',
            Program_Line_13='elseif ComfStand == 7',
            Program_Line_14='set ComfTemp = PMOT*0.54+12.83',
            Program_Line_15='elseif ComfStand == 8',
            Program_Line_16='set ComfTemp = PMOT*0.28+17.87',
            Program_Line_17='elseif ComfStand == 9',
            Program_Line_18='set ComfTemp = PMOT*0.39+18.42',
            Program_Line_19='elseif ComfStand == 10',
            Program_Line_20='set ComfTemp = PMOT*0.42+17.6',
            Program_Line_21='elseif ComfStand == 11',
            Program_Line_22='set ComfTemp = PMOT*0.75+5.37',
            Program_Line_23='elseif ComfStand == 12',
            Program_Line_24='set ComfTemp = PMOT*0.25+19.7',
            Program_Line_25='elseif ComfStand == 13',
            Program_Line_26='set ComfTemp = PMOT*0.26+15.9',
            Program_Line_27='elseif ComfStand == 14',
            Program_Line_28='set ComfTemp = PMOT*0.26+16.75',
            Program_Line_29='elseif ComfStand == 15',
            Program_Line_30='set ComfTemp = PMOT*0.56+12.74',
            Program_Line_31='elseif ComfStand == 16',
            Program_Line_32='set ComfTemp = PMOT*0.09+22.32',
            Program_Line_33='elseif ComfStand == 17',
            Program_Line_34='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_35='set ComfTemp = PMOT*0.48+13.9',
            Program_Line_36='else',
            Program_Line_37='set ComfTemp = PMOT*0.59+9.6',
            Program_Line_38='endif',
            Program_Line_39='elseif ComfStand == 18',
            Program_Line_40='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_41='set ComfTemp = PMOT*0.84+5.3',
            Program_Line_42='else',
            Program_Line_43='set ComfTemp = PMOT*0.96-3.6',
            Program_Line_44='endif',
            Program_Line_45='elseif ComfStand == 19',
            Program_Line_46='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_47='set ComfTemp = PMOT*0.27+17.9',
            Program_Line_48='else',
            Program_Line_49='set ComfTemp = PMOT*0.53+10.3',
            Program_Line_50='endif',
            Program_Line_51='elseif ComfStand == 20',
            Program_Line_52='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_53='set ComfTemp = PMOT*0.38+15.7',
            Program_Line_54='else',
            Program_Line_55='set ComfTemp = PMOT*0.47+9.07',
            Program_Line_56='endif',
            Program_Line_57='elseif ComfStand == 21',
            Program_Line_58='set ComfTemp = PMOT*0.678+13.51',
            Program_Line_59='endif',
        )
        if verboseMode:
            print('Added - SetComfTemp Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetComfTemp'])

    for zonename in self.occupiedZones:
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
            Program_Line_1='If ComfStand == 1',
            Program_Line_2='set ACSTaul = 30',
            Program_Line_3='set ACSTall = 10',
            Program_Line_4='set AHSTaul = 30',
            Program_Line_5='set AHSTall = 10',
            Program_Line_6='elseif ComfStand == 2 || ComfStand == 12',
            Program_Line_7='set ACSTaul = 33.5',
            Program_Line_8='set ACSTall = 10',
            Program_Line_9='set AHSTaul = 33.5',
            Program_Line_10='set AHSTall = 10',
            Program_Line_11='elseif ComfStand == 3',
            Program_Line_12='set ACSTaul = 30',
            Program_Line_13='set ACSTall = 5',
            Program_Line_14='set AHSTaul = 30',
            Program_Line_15='set AHSTall = 5',
            Program_Line_16='elseif (ComfStand == 4) || (ComfStand == 5)',
            Program_Line_17='if CAT == 1',
            Program_Line_18='set ACSTaul = 28',
            Program_Line_19='set ACSTall = 18',
            Program_Line_20='set AHSTaul = 28',
            Program_Line_21='set AHSTall = 18',
            Program_Line_22='elseif CAT == 2',
            Program_Line_23='set ACSTaul = 30',
            Program_Line_24='set ACSTall = 18',
            Program_Line_25='set AHSTaul = 28',
            Program_Line_26='set AHSTall = 16',
            Program_Line_27='else',
            Program_Line_28='set ACSTaul = 50',
            Program_Line_29='set ACSTall = 50',
            Program_Line_30='set AHSTaul = 50',
            Program_Line_31='set AHSTall = 50',
            Program_Line_32='endif',
            Program_Line_33='elseif ComfStand == 6',
            Program_Line_34='set ACSTaul = 30',
            Program_Line_35='set ACSTall = -7',
            Program_Line_36='set AHSTaul = 30',
            Program_Line_37='set AHSTall = -7',
            Program_Line_38='elseif ComfStand == 7',
            Program_Line_39='set ACSTaul = 31',
            Program_Line_40='set ACSTall = 12.5',
            Program_Line_41='set AHSTaul = 31',
            Program_Line_42='set AHSTall = 12.5',
            Program_Line_43='elseif ComfStand == 8',
            Program_Line_44='set ACSTaul = 38.5',
            Program_Line_45='set ACSTall = 13',
            Program_Line_46='set AHSTaul = 38.5',
            Program_Line_47='set AHSTall = 13',
            Program_Line_48='elseif ComfStand == 9 || ComfStand == 10 || ComfStand == 11',
            Program_Line_49='set ACSTaul = 33',
            Program_Line_50='set ACSTall = 5.5',
            Program_Line_51='set AHSTaul = 33',
            Program_Line_52='set AHSTall = 5.5',
            Program_Line_53='elseif ComfStand == 13',
            Program_Line_54='set ACSTaul = 25',
            Program_Line_55='set ACSTall = 10',
            Program_Line_56='set AHSTaul = 25',
            Program_Line_57='set AHSTall = 10',
            Program_Line_58='elseif ComfStand == 14',
            Program_Line_59='set ACSTaul = 27',
            Program_Line_60='set ACSTall = 8',
            Program_Line_61='set AHSTaul = 27',
            Program_Line_62='set AHSTall = 8',
            Program_Line_63='elseif ComfStand == 15',
            Program_Line_64='set ACSTaul = 24.8',
            Program_Line_65='set ACSTall = 16.9',
            Program_Line_66='set AHSTaul = 24.8',
            Program_Line_67='set AHSTall = 16.9',
            Program_Line_68='elseif ComfStand == 16',
            Program_Line_69='set ACSTaul = 25.7',
            Program_Line_70='set ACSTall = 16.4',
            Program_Line_71='set AHSTaul = 25.7',
            Program_Line_72='set AHSTall = 16.4',
            Program_Line_73='elseif ComfStand == 17',
            Program_Line_74='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_75='set ACSTaul = 25.25',
            Program_Line_76='set ACSTall = 11.25',
            Program_Line_77='set AHSTaul = 25.25',
            Program_Line_78='set AHSTall = 11.25',
            Program_Line_79='else',
            Program_Line_80='set ACSTaul = 45',
            Program_Line_81='set ACSTall = 23',
            Program_Line_82='set AHSTaul = 45',
            Program_Line_83='set AHSTall = 23',
            Program_Line_84='endif',
            Program_Line_85='elseif ComfStand == 18',
            Program_Line_86='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_87='set ACSTaul = 27.5',
            Program_Line_88='set ACSTall = 15.5',
            Program_Line_89='set AHSTaul = 27.5',
            Program_Line_90='set AHSTall = 15.5',
            Program_Line_91='else',
            Program_Line_92='set ACSTaul = 34',
            Program_Line_93='set ACSTall = 23',
            Program_Line_94='set AHSTaul = 34',
            Program_Line_95='set AHSTall = 23',
            Program_Line_96='endif',
            Program_Line_97='elseif ComfStand == 19',
            Program_Line_98='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_99='set ACSTaul = 25.25',
            Program_Line_100='set ACSTall = 5',
            Program_Line_101='set AHSTaul = 25.25',
            Program_Line_102='set AHSTall = 5',
            Program_Line_103='else',
            Program_Line_104='set ACSTaul = 25.25',
            Program_Line_105='set ACSTall = 11.75',
            Program_Line_106='set AHSTaul = 25.25',
            Program_Line_107='set AHSTall = 11.75',
            Program_Line_108='endif',
            Program_Line_109='elseif ComfStand == 20',
            Program_Line_110='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_111='set ACSTaul = 29.75',
            Program_Line_112='set ACSTall = 13',
            Program_Line_113='set AHSTaul = 29.75',
            Program_Line_114='set AHSTall = 13',
            Program_Line_115='else',
            Program_Line_116='set ACSTaul = 45',
            Program_Line_117='set ACSTall = 23',
            Program_Line_118='set AHSTaul = 45',
            Program_Line_119='set AHSTall = 23',
            Program_Line_120='endif',
            Program_Line_121='elseif ComfStand == 21',
            Program_Line_122='set ACSTaul = 20',
            Program_Line_123='set ACSTall = 6.5',
            Program_Line_124='set AHSTaul = 20',
            Program_Line_125='set AHSTall = 6.5',
            Program_Line_126='else',
            Program_Line_127='set ACSTaul = 50',
            Program_Line_128='set ACSTall = 50',
            Program_Line_129='set AHSTaul = 50',
            Program_Line_130='set AHSTall = 50',
            Program_Line_131='endif',
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
            Program_Line_1='set CATcoolOffset = 2',
            Program_Line_2='set CATheatOffset = 2',
            Program_Line_3='if (ComfStand == 1 )',
            Program_Line_4='if (CAT == 1)',
            Program_Line_5='set ACSToffset = 2+CATcoolOffset',
            Program_Line_6='set AHSToffset = -3+CATheatOffset',
            Program_Line_7='elseif (CAT == 2)',
            Program_Line_8='set ACSToffset = 3+CATcoolOffset',
            Program_Line_9='set AHSToffset = -4+CATheatOffset',
            Program_Line_10='elseif (CAT == 3)',
            Program_Line_11='set ACSToffset = 4+CATcoolOffset',
            Program_Line_12='set AHSToffset = -5+CATheatOffset',
            Program_Line_13='endif',
            Program_Line_14='elseif ComfStand == 2 || ComfStand == 3 || ComfStand == 11',
            Program_Line_15='if (CAT == 90)',
            Program_Line_16='set ACSToffset = 2.5+CATcoolOffset',
            Program_Line_17='set AHSToffset = -2.5+CATheatOffset',
            Program_Line_18='elseif (CAT == 80)',
            Program_Line_19='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_20='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_21='endif',
            Program_Line_22='elseif (ComfStand == 4 ) || (ComfStand == 5) || (ComfStand == 6)',
            Program_Line_23='set ACSToffset = 0+CATcoolOffset',
            Program_Line_24='set AHSToffset = 0+CATheatOffset',
            Program_Line_25='elseif (ComfStand == 7)',
            Program_Line_26='if (CAT == 90)',
            Program_Line_27='set ACSToffset = 2.4+CATcoolOffset',
            Program_Line_28='set AHSToffset = -2.4+CATheatOffset',
            Program_Line_29='elseif (CAT == 85)',
            Program_Line_30='set ACSToffset = 3.3+CATcoolOffset',
            Program_Line_31='set AHSToffset = -3.3+CATheatOffset',
            Program_Line_32='elseif (CAT == 80)',
            Program_Line_33='set ACSToffset = 4.1+CATcoolOffset',
            Program_Line_34='set AHSToffset = -4.1+CATheatOffset',
            Program_Line_35='endif',
            Program_Line_36='elseif (ComfStand == 8)',
            Program_Line_37='if (CAT == 90)',
            Program_Line_38='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_39='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_40='elseif (CAT == 85)',
            Program_Line_41='set ACSToffset = 4.8+CATcoolOffset',
            Program_Line_42='set AHSToffset = -4.8+CATheatOffset',
            Program_Line_43='elseif (CAT == 80)',
            Program_Line_44='set ACSToffset = 5.9+CATcoolOffset',
            Program_Line_45='set AHSToffset = -5.9+CATheatOffset',
            Program_Line_46='endif',
            Program_Line_47='elseif ComfStand == 9 || ComfStand == 10',
            Program_Line_48='if (CAT == 90)',
            Program_Line_49='set ACSToffset = 2.15+CATcoolOffset',
            Program_Line_50='set AHSToffset = -2.15+CATheatOffset',
            Program_Line_51='elseif (CAT == 80)',
            Program_Line_52='set ACSToffset = 3.6+CATcoolOffset',
            Program_Line_53='set AHSToffset = -3.6+CATheatOffset',
            Program_Line_54='endif',
            Program_Line_55='elseif ComfStand == 12',
            Program_Line_56='if (CAT == 90)',
            Program_Line_57='set ACSToffset = 1.7+CATcoolOffset',
            Program_Line_58='set AHSToffset = -1.7+CATheatOffset',
            Program_Line_59='elseif (CAT == 80)',
            Program_Line_60='set ACSToffset = 2.89+CATcoolOffset',
            Program_Line_61='set AHSToffset = -2.89+CATheatOffset',
            Program_Line_62='endif',
            Program_Line_63='elseif ComfStand == 13',
            Program_Line_64='if (CAT == 90)',
            Program_Line_65='set ACSToffset = 3.45+CATcoolOffset',
            Program_Line_66='set AHSToffset = -3.45+CATheatOffset',
            Program_Line_67='elseif (CAT == 80)',
            Program_Line_68='set ACSToffset = 4.55+CATcoolOffset',
            Program_Line_69='set AHSToffset = -4.55+CATheatOffset',
            Program_Line_70='endif',
            Program_Line_71='elseif ComfStand == 14',
            Program_Line_72='if (CAT == 90)',
            Program_Line_73='set ACSToffset = 3.5+CATcoolOffset',
            Program_Line_74='set AHSToffset = -3.5+CATheatOffset',
            Program_Line_75='elseif (CAT == 80)',
            Program_Line_76='set ACSToffset = 4.5+CATcoolOffset',
            Program_Line_77='set AHSToffset = -4.5+CATheatOffset',
            Program_Line_78='endif',
            Program_Line_79='elseif ComfStand == 15',
            Program_Line_80='if (CAT == 90)',
            Program_Line_81='set ACSToffset = 2.8+CATcoolOffset',
            Program_Line_82='set AHSToffset = -2.8+CATheatOffset',
            Program_Line_83='elseif (CAT == 80)',
            Program_Line_84='set ACSToffset = 3.8+CATcoolOffset',
            Program_Line_85='set AHSToffset = -3.8+CATheatOffset',
            Program_Line_86='endif',
            Program_Line_87='elseif ComfStand == 16',
            Program_Line_88='if (CAT == 90)',
            Program_Line_89='set ACSToffset = 1.1+CATcoolOffset',
            Program_Line_90='set AHSToffset = -1.1+CATheatOffset',
            Program_Line_91='elseif (CAT == 80)',
            Program_Line_92='set ACSToffset = 2.1+CATcoolOffset',
            Program_Line_93='set AHSToffset = -2.1+CATheatOffset',
            Program_Line_94='endif',
            Program_Line_95='elseif (ComfStand == 17) || (ComfStand == 18)',
            Program_Line_96='if CAT == 90',
            Program_Line_97='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_98='set ACSToffset = 2+CATcoolOffset',
            Program_Line_99='set AHSToffset = -2+CATheatOffset',
            Program_Line_100='else',
            Program_Line_101='set ACSToffset = 2+CATcoolOffset',
            Program_Line_102='set AHSToffset = -2+CATheatOffset',
            Program_Line_103='endif',
            Program_Line_104='elseif CAT == 80',
            Program_Line_105='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_106='set ACSToffset = 3+CATcoolOffset',
            Program_Line_107='set AHSToffset = -3+CATheatOffset',
            Program_Line_108='else',
            Program_Line_109='set ACSToffset = 3+CATcoolOffset',
            Program_Line_110='set AHSToffset = -3+CATheatOffset',
            Program_Line_111='endif',
            Program_Line_112='endif',
            Program_Line_113='elseif ComfStand == 19',
            Program_Line_114='if CAT == 90',
            Program_Line_115='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_116='set ACSToffset = 2+CATcoolOffset',
            Program_Line_117='set AHSToffset = -2+CATheatOffset',
            Program_Line_118='else',
            Program_Line_119='set ACSToffset = 1+CATcoolOffset',
            Program_Line_120='set AHSToffset = -1+CATheatOffset',
            Program_Line_121='endif',
            Program_Line_122='elseif CAT == 80',
            Program_Line_123='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_124='set ACSToffset = 3+CATcoolOffset',
            Program_Line_125='set AHSToffset = -3+CATheatOffset',
            Program_Line_126='else',
            Program_Line_127='set ACSToffset = 2+CATcoolOffset',
            Program_Line_128='set AHSToffset = -2+CATheatOffset',
            Program_Line_129='endif',
            Program_Line_130='endif',
            Program_Line_131='elseif ComfStand == 20',
            Program_Line_132='if CAT == 90',
            Program_Line_133='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_134='set ACSToffset = 2+CATcoolOffset',
            Program_Line_135='set AHSToffset = -2+CATheatOffset',
            Program_Line_136='else',
            Program_Line_137='set ACSToffset = 5+CATcoolOffset',
            Program_Line_138='set AHSToffset = -5+CATheatOffset',
            Program_Line_139='endif',
            Program_Line_140='elseif CAT == 80',
            Program_Line_141='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_142='set ACSToffset = 3+CATcoolOffset',
            Program_Line_143='set AHSToffset = -3+CATheatOffset',
            Program_Line_144='else',
            Program_Line_145='set ACSToffset = 6+CATcoolOffset',
            Program_Line_146='set AHSToffset = -6+CATheatOffset',
            Program_Line_147='endif',
            Program_Line_148='endif',
            Program_Line_149='elseif ComfStand == 21',
            Program_Line_150='if (CAT == 90)',
            Program_Line_151='set ACSToffset = 2.5+CATcoolOffset',
            Program_Line_152='set AHSToffset = -2.5+CATheatOffset',
            Program_Line_153='elseif (CAT == 80)',
            Program_Line_154='set ACSToffset = 4+CATcoolOffset',
            Program_Line_155='set AHSToffset = -4+CATheatOffset',
            Program_Line_156='endif',
            Program_Line_157='endif',
        )
        if verboseMode:
            print('Added - ApplyCAT Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyCAT'])

    if 'SetAST' in programlist:
        if verboseMode:
            print('Not added - SetAST Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='SetAST',
            #todo for some reason, SetpointAcc variable is not defined if set out of this program; ideally, it should be located in SetInputData program
            Program_Line_1='set SetpointAcc = 10000',
            Program_Line_2='if CoolSeasonEnd > CoolSeasonStart',
            Program_Line_3='if (DayOfYear >= CoolSeasonStart) && (DayOfYear < CoolSeasonEnd)',
            Program_Line_4='set CoolingSeason = 1',
            Program_Line_5='else',
            Program_Line_6='set CoolingSeason = 0',
            Program_Line_7='endif',
            Program_Line_8='elseif CoolSeasonStart > CoolSeasonEnd',
            Program_Line_9='if (DayOfYear >= CoolSeasonStart) || (DayOfYear < CoolSeasonEnd)',
            Program_Line_10='set CoolingSeason = 1',
            Program_Line_11='else',
            Program_Line_12='set CoolingSeason = 0',
            Program_Line_13='endif',
            Program_Line_14='endif',
            Program_Line_15='if (ComfStand == 0) && (CurrentTime < 8)',
            Program_Line_16='set ACST = 27+ACSTtol',
            Program_Line_17='set AHST = 17+AHSTtol',
            Program_Line_18='elseif (ComfStand == 0) && (CurrentTime < 16)',
            Program_Line_19='set ACST = 25+ACSTtol',
            Program_Line_20='set AHST = 20+AHSTtol',
            Program_Line_21='elseif (ComfStand == 0) && (CurrentTime < 23)',
            Program_Line_22='set ACST = 25+ACSTtol',
            Program_Line_23='set AHST = 20+AHSTtol',
            Program_Line_24='elseif (ComfStand == 0) && (CurrentTime < 24)',
            Program_Line_25='set ACST = 27+ACSTtol',
            Program_Line_26='set AHST = 17+AHSTtol',
            Program_Line_27='endif',
            Program_Line_28='if (ComfStand == 1) && (ComfMod == 0)',
            Program_Line_29='if CoolingSeason == 1',
            Program_Line_30='if (CAT==1)',
            Program_Line_31='set ACST = 25.5+ACSTtol',
            Program_Line_32='elseif (CAT==2)',
            Program_Line_33='set ACST = 26+ACSTtol',
            Program_Line_34='elseif (CAT==3)',
            Program_Line_35='set ACST = 27+ACSTtol',
            Program_Line_36='endif',
            Program_Line_37='else',
            Program_Line_38='if (CAT==1)',
            Program_Line_39='set ACST = 25+ACSTtol',
            Program_Line_40='elseif (CAT==2)',
            Program_Line_41='set ACST = 25+ACSTtol',
            Program_Line_42='elseif (CAT==3)',
            Program_Line_43='set ACST = 25+ACSTtol',
            Program_Line_44='endif',
            Program_Line_45='endif',
            Program_Line_46='endif',
            Program_Line_47='if (ComfStand == 1) && (ComfMod == 0)',
            Program_Line_48='if CoolingSeason == 1',
            Program_Line_49='if (CAT==1)',
            Program_Line_50='set AHST = 23.5+AHSTtol',
            Program_Line_51='elseif (CAT==2)',
            Program_Line_52='set AHST = 23+AHSTtol',
            Program_Line_53='elseif (CAT==3)',
            Program_Line_54='set AHST = 22+AHSTtol',
            Program_Line_55='endif',
            Program_Line_56='else',
            Program_Line_57='if (CAT==1)',
            Program_Line_58='set AHST = 21+AHSTtol',
            Program_Line_59='elseif (CAT==2)',
            Program_Line_60='set AHST = 20+AHSTtol',
            Program_Line_61='elseif (CAT==3)',
            Program_Line_62='set AHST = 18+AHSTtol',
            Program_Line_63='endif',
            Program_Line_64='endif',
            Program_Line_65='endif',
            Program_Line_66='if (ComfStand == 1) && (ComfMod == 1)',
            Program_Line_67='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_68='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_69='elseif CurrentTime < 7',
            Program_Line_70='set ACST = 27+ACSTtol',
            Program_Line_71='elseif CurrentTime < 15',
            Program_Line_72='set ACST = 50',
            Program_Line_73='elseif CurrentTime < 23',
            Program_Line_74='set ACST = 25+ACSTtol',
            Program_Line_75='elseif CurrentTime < 24',
            Program_Line_76='set ACST = 27+ACSTtol',
            Program_Line_77='endif',
            Program_Line_78='endif',
            Program_Line_79='if (ComfStand == 1) && (ComfMod == 1)',
            Program_Line_80='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_81='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_82='elseif CurrentTime < 7',
            Program_Line_83='set AHST = 17+AHSTtol',
            Program_Line_84='elseif CurrentTime < 23',
            Program_Line_85='set AHST = 20+AHSTtol',
            Program_Line_86='elseif CurrentTime < 24',
            Program_Line_87='set AHST = 17+AHSTtol',
            Program_Line_88='endif',
            Program_Line_89='endif',
            Program_Line_90='if (ComfStand == 1) && (ComfMod == 2)',
            Program_Line_91='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_92='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_93='elseif (RMOT < ACSTall) && (CAT==1)',
            Program_Line_94='set ACST = 25+ACSTtol',
            Program_Line_95='elseif (RMOT > ACSTaul) && (CAT==1)',
            Program_Line_96='set ACST = 25.5+ACSTtol',
            Program_Line_97='elseif (RMOT < ACSTall) && (CAT==2)',
            Program_Line_98='set ACST = 25+ACSTtol',
            Program_Line_99='elseif (RMOT > ACSTaul) && (CAT==2)',
            Program_Line_100='set ACST = 26+ACSTtol',
            Program_Line_101='elseif (RMOT < ACSTall) && (CAT==3)',
            Program_Line_102='set ACST = 25+ACSTtol',
            Program_Line_103='elseif (RMOT > ACSTaul) && (CAT==3)',
            Program_Line_104='set ACST = 27+ACSTtol',
            Program_Line_105='endif',
            Program_Line_106='endif',
            Program_Line_107='if (ComfStand == 1) && (ComfMod == 2)',
            Program_Line_108='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_109='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_110='elseif (RMOT < AHSTall) && (CAT==1)',
            Program_Line_111='set AHST = 21+AHSTtol',
            Program_Line_112='elseif (RMOT > AHSTaul) && (CAT==1)',
            Program_Line_113='set AHST = 23.5+AHSTtol',
            Program_Line_114='elseif (RMOT < AHSTall) && (CAT==2)',
            Program_Line_115='set AHST = 20+AHSTtol',
            Program_Line_116='elseif (RMOT > AHSTaul) && (CAT==2)',
            Program_Line_117='set AHST = 23+AHSTtol',
            Program_Line_118='elseif (RMOT < AHSTall) && (CAT==3)',
            Program_Line_119='set AHST = 18+AHSTtol',
            Program_Line_120='elseif (RMOT > AHSTaul) && (CAT==3)',
            Program_Line_121='set AHST = 22+AHSTtol',
            Program_Line_122='endif',
            Program_Line_123='endif',
            Program_Line_124='if (ComfStand == 1) && (ComfMod == 3)',
            Program_Line_125='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_126='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_127='elseif RMOT < ACSTall',
            Program_Line_128='set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_129='elseif RMOT > ACSTaul',
            Program_Line_130='set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_131='endif',
            Program_Line_132='endif',
            Program_Line_133='if (ComfStand == 1) && (ComfMod == 3)',
            Program_Line_134='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_135='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_136='elseif RMOT < AHSTall',
            Program_Line_137='set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_138='elseif RMOT > AHSTaul',
            Program_Line_139='set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_140='endif',
            Program_Line_141='endif',
            Program_Line_142='if (ComfStand == 2) && (ComfMod == 0)',
            Program_Line_143='if CoolingSeason == 1',
            Program_Line_144='if (CAT==80)',
            Program_Line_145='set ACST = 27+ACSTtol',
            Program_Line_146='elseif (CAT==90)',
            Program_Line_147='set ACST = 26+ACSTtol',
            Program_Line_148='endif',
            Program_Line_149='else',
            Program_Line_150='if (CAT==80)',
            Program_Line_151='set ACST = 25+ACSTtol',
            Program_Line_152='elseif (CAT==90)',
            Program_Line_153='set ACST = 24+ACSTtol',
            Program_Line_154='endif',
            Program_Line_155='endif',
            Program_Line_156='endif',
            Program_Line_157='if (ComfStand == 2) && (ComfMod == 0)',
            Program_Line_158='if CoolingSeason == 1',
            Program_Line_159='if (CAT==80)',
            Program_Line_160='set AHST = 22+AHSTtol',
            Program_Line_161='elseif (CAT==90)',
            Program_Line_162='set AHST = 23+AHSTtol',
            Program_Line_163='endif',
            Program_Line_164='else',
            Program_Line_165='if (CAT==80)',
            Program_Line_166='set AHST = 19+AHSTtol',
            Program_Line_167='elseif (CAT==90)',
            Program_Line_168='set AHST = 20+AHSTtol',
            Program_Line_169='endif',
            Program_Line_170='endif',
            Program_Line_171='endif',
            Program_Line_172='if (ComfStand == 2) && (ComfMod == 1)',
            Program_Line_173='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_174='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_175='elseif CurrentTime < 7',
            Program_Line_176='set ACST = 27+ACSTtol',
            Program_Line_177='elseif CurrentTime < 15',
            Program_Line_178='set ACST = 50',
            Program_Line_179='elseif CurrentTime < 23',
            Program_Line_180='set ACST = 25+ACSTtol',
            Program_Line_181='elseif CurrentTime < 24',
            Program_Line_182='set ACST = 27+ACSTtol',
            Program_Line_183='endif',
            Program_Line_184='endif',
            Program_Line_185='if (ComfStand == 2) && (ComfMod == 1)',
            Program_Line_186='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_187='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_188='elseif CurrentTime < 7',
            Program_Line_189='set AHST = 17+AHSTtol',
            Program_Line_190='elseif CurrentTime < 23',
            Program_Line_191='set AHST = 20+AHSTtol',
            Program_Line_192='elseif CurrentTime < 24',
            Program_Line_193='set AHST = 17+AHSTtol',
            Program_Line_194='endif',
            Program_Line_195='endif',
            Program_Line_196='if (ComfStand == 2) && (ComfMod == 2)',
            Program_Line_197='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_198='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_199='elseif CAT==80',
            Program_Line_200='if PMOT < ACSTall',
            Program_Line_201='set ACST = 25+ACSTtol',
            Program_Line_202='elseif PMOT > ACSTaul',
            Program_Line_203='set ACST = 27+ACSTtol',
            Program_Line_204='endif',
            Program_Line_205='elseif CAT==90',
            Program_Line_206='if PMOT < ACSTall',
            Program_Line_207='set ACST = 24+ACSTtol',
            Program_Line_208='elseif PMOT > ACSTaul',
            Program_Line_209='set ACST = 26+ACSTtol',
            Program_Line_210='endif',
            Program_Line_211='endif',
            Program_Line_212='endif',
            Program_Line_213='if (ComfStand == 2) && (ComfMod == 2)',
            Program_Line_214='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_215='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_216='elseif CAT==80',
            Program_Line_217='if PMOT < AHSTall',
            Program_Line_218='set AHST = 19+AHSTtol',
            Program_Line_219='elseif PMOT > AHSTaul',
            Program_Line_220='set AHST = 22+AHSTtol',
            Program_Line_221='endif',
            Program_Line_222='elseif CAT==90',
            Program_Line_223='if PMOT < AHSTall',
            Program_Line_224='set AHST = 20+AHSTtol',
            Program_Line_225='elseif PMOT > AHSTaul',
            Program_Line_226='set AHST = 23+AHSTtol',
            Program_Line_227='endif',
            Program_Line_228='endif',
            Program_Line_229='endif',
            Program_Line_230='if (ComfStand == 2) && (ComfMod == 3)',
            Program_Line_231='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_232='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_233='elseif PMOT < ACSTall',
            Program_Line_234='set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_235='elseif PMOT > ACSTaul',
            Program_Line_236='set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_237='endif',
            Program_Line_238='endif',
            Program_Line_239='if (ComfStand == 2) && (ComfMod == 3)',
            Program_Line_240='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_241='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_242='elseif PMOT < AHSTall',
            Program_Line_243='set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_244='elseif PMOT > AHSTaul',
            Program_Line_245='set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_246='endif',
            Program_Line_247='endif',
            Program_Line_248='if (ComfStand == 3) && (ComfMod == 0)',
            Program_Line_249='if (CAT==80)',
            Program_Line_250='set ACST = 28+ACSTtol',
            Program_Line_251='elseif (CAT==90)',
            Program_Line_252='set ACST = 27+ACSTtol',
            Program_Line_253='endif',
            Program_Line_254='endif',
            Program_Line_255='if (ComfStand == 3) && (ComfMod == 0)',
            Program_Line_256='if (CAT==80)',
            Program_Line_257='set AHST = 18+AHSTtol',
            Program_Line_258='elseif (CAT==90)',
            Program_Line_259='set AHST = 19+AHSTtol',
            Program_Line_260='endif',
            Program_Line_261='endif',
            Program_Line_262='if (ComfStand == 3) && (ComfMod == 1)',
            Program_Line_263='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_264='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_265='elseif CAT==80',
            Program_Line_266='if PMOT < ACSTall',
            Program_Line_267='set ACST = 28+ACSTtol',
            Program_Line_268='elseif PMOT > ACSTaul',
            Program_Line_269='set ACST = 28+ACSTtol',
            Program_Line_270='endif',
            Program_Line_271='elseif CAT==90',
            Program_Line_272='if PMOT < ACSTall',
            Program_Line_273='set ACST = 27+ACSTtol',
            Program_Line_274='elseif PMOT > ACSTaul',
            Program_Line_275='set ACST = 27+ACSTtol',
            Program_Line_276='endif',
            Program_Line_277='endif',
            Program_Line_278='endif',
            Program_Line_279='if (ComfStand == 3) && (ComfMod == 1)',
            Program_Line_280='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_281='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_282='elseif CAT==80',
            Program_Line_283='if PMOT < AHSTall',
            Program_Line_284='set AHST = 18+AHSTtol',
            Program_Line_285='elseif PMOT > AHSTaul',
            Program_Line_286='set AHST = 18+AHSTtol',
            Program_Line_287='endif',
            Program_Line_288='elseif CAT==90',
            Program_Line_289='if PMOT < AHSTall',
            Program_Line_290='set AHST = 19+AHSTtol',
            Program_Line_291='elseif PMOT > AHSTaul',
            Program_Line_292='set AHST = 19+AHSTtol',
            Program_Line_293='endif',
            Program_Line_294='endif',
            Program_Line_295='endif',
            Program_Line_296='if (ComfStand == 3) && (ComfMod == 2)',
            Program_Line_297='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_298='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_299='elseif CAT==80',
            Program_Line_300='if PMOT < ACSTall',
            Program_Line_301='set ACST = 25+ACSTtol',
            Program_Line_302='elseif PMOT > ACSTaul',
            Program_Line_303='set ACST = 27+ACSTtol',
            Program_Line_304='endif',
            Program_Line_305='elseif CAT==90',
            Program_Line_306='if PMOT < ACSTall',
            Program_Line_307='set ACST = 24+ACSTtol',
            Program_Line_308='elseif PMOT > ACSTaul',
            Program_Line_309='set ACST = 26+ACSTtol',
            Program_Line_310='endif',
            Program_Line_311='endif',
            Program_Line_312='endif',
            Program_Line_313='if (ComfStand == 3) && (ComfMod == 2)',
            Program_Line_314='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_315='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_316='elseif CAT==80',
            Program_Line_317='if PMOT < AHSTall',
            Program_Line_318='set AHST = 19+AHSTtol',
            Program_Line_319='elseif PMOT > AHSTaul',
            Program_Line_320='set AHST = 22+AHSTtol',
            Program_Line_321='endif',
            Program_Line_322='elseif CAT==90',
            Program_Line_323='if PMOT < AHSTall',
            Program_Line_324='set AHST = 20+AHSTtol',
            Program_Line_325='elseif PMOT > AHSTaul',
            Program_Line_326='set AHST = 23+AHSTtol',
            Program_Line_327='endif',
            Program_Line_328='endif',
            Program_Line_329='endif',
            Program_Line_330='if (ComfStand == 3) && (ComfMod == 3)',
            Program_Line_331='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_332='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_333='elseif PMOT < ACSTall',
            Program_Line_334='set ACST = ACSTall*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_335='elseif PMOT > ACSTaul',
            Program_Line_336='set ACST = ACSTaul*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_337='endif',
            Program_Line_338='endif',
            Program_Line_339='if (ComfStand == 3) && (ComfMod == 3)',
            Program_Line_340='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_341='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_342='elseif PMOT < AHSTall',
            Program_Line_343='set AHST = AHSTall*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_344='elseif PMOT > AHSTaul',
            Program_Line_345='set AHST = AHSTaul*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_346='endif',
            Program_Line_347='endif',
            Program_Line_348='if (ComfStand == 4) && (ComfMod == 3)',
            Program_Line_349='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_350='if CAT == 1',
            Program_Line_351='set ACST = PMOT*0.77+12.04+ACSTtol',
            Program_Line_352='elseif CAT == 2',
            Program_Line_353='set ACST = PMOT*0.73+15.28+ACSTtol',
            Program_Line_354='endif',
            Program_Line_355='elseif PMOT < ACSTall',
            Program_Line_356='if CAT == 1',
            Program_Line_357='set ACST = ACSTall*0.77+12.04+ACSTtol',
            Program_Line_358='elseif CAT == 2',
            Program_Line_359='set ACST = ACSTall*0.73+15.28+ACSTtol',
            Program_Line_360='endif',
            Program_Line_361='elseif PMOT > ACSTaul',
            Program_Line_362='if CAT == 1',
            Program_Line_363='set ACST = ACSTaul*0.77+12.04+ACSTtol',
            Program_Line_364='elseif CAT == 2',
            Program_Line_365='set ACST = ACSTaul*0.73+15.28+ACSTtol',
            Program_Line_366='endif',
            Program_Line_367='endif',
            Program_Line_368='endif',
            Program_Line_369='if (ComfStand == 4) && (ComfMod == 3)',
            Program_Line_370='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_371='if CAT == 1',
            Program_Line_372='set AHST = PMOT*0.87+2.76+AHSTtol',
            Program_Line_373='elseif CAT == 2',
            Program_Line_374='set AHST = PMOT*0.91-0.48+AHSTtol',
            Program_Line_375='endif',
            Program_Line_376='elseif PMOT < AHSTall',
            Program_Line_377='if CAT == 1',
            Program_Line_378='set AHST = AHSTall*0.87+2.76+AHSTtol',
            Program_Line_379='elseif CAT == 2',
            Program_Line_380='set AHST = AHSTall*0.91-0.48+AHSTtol',
            Program_Line_381='endif',
            Program_Line_382='elseif PMOT > AHSTaul',
            Program_Line_383='if CAT == 1',
            Program_Line_384='set AHST = AHSTaul*0.87+2.76+AHSTtol',
            Program_Line_385='elseif CAT == 2',
            Program_Line_386='set AHST = AHSTaul*0.91-0.48+AHSTtol',
            Program_Line_387='endif',
            Program_Line_388='endif',
            Program_Line_389='endif',
            Program_Line_390='if (ComfStand == 5) && (ComfMod == 3)',
            Program_Line_391='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_392='if CAT == 1',
            Program_Line_393='set ACST = PMOT*0.77+9.34+ACSTtol',
            Program_Line_394='elseif CAT == 2',
            Program_Line_395='set ACST = PMOT*0.73+12.72+ACSTtol',
            Program_Line_396='endif',
            Program_Line_397='elseif PMOT < ACSTall',
            Program_Line_398='if CAT == 1',
            Program_Line_399='set ACST = ACSTall*0.77+9.34+ACSTtol',
            Program_Line_400='elseif CAT == 2',
            Program_Line_401='set ACST = ACSTall*0.73+12.72+ACSTtol',
            Program_Line_402='endif',
            Program_Line_403='elseif PMOT > ACSTaul',
            Program_Line_404='if CAT == 1',
            Program_Line_405='set ACST = ACSTaul*0.77+9.34+ACSTtol',
            Program_Line_406='elseif CAT == 2',
            Program_Line_407='set ACST = ACSTaul*0.73+12.72+ACSTtol',
            Program_Line_408='endif',
            Program_Line_409='endif',
            Program_Line_410='endif',
            Program_Line_411='if (ComfStand == 5) && (ComfMod == 3)',
            Program_Line_412='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_413='if CAT == 1',
            Program_Line_414='set AHST = PMOT*0.87-0.31+AHSTtol',
            Program_Line_415='elseif CAT == 2',
            Program_Line_416='set AHST = PMOT*0.91-3.69+AHSTtol',
            Program_Line_417='endif',
            Program_Line_418='elseif PMOT < AHSTall',
            Program_Line_419='if CAT == 1',
            Program_Line_420='set AHST = AHSTall*0.87-0.31+AHSTtol',
            Program_Line_421='elseif CAT == 2',
            Program_Line_422='set AHST = AHSTall*0.91-3.69+AHSTtol',
            Program_Line_423='endif',
            Program_Line_424='elseif PMOT > AHSTaul',
            Program_Line_425='if CAT == 1',
            Program_Line_426='set AHST = AHSTaul*0.87-0.31+AHSTtol',
            Program_Line_427='elseif CAT == 2',
            Program_Line_428='set AHST = AHSTaul*0.91-3.69+AHSTtol',
            Program_Line_429='endif',
            Program_Line_430='endif',
            Program_Line_431='endif',
            Program_Line_432='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_433='if CAT==80',
            Program_Line_434='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_435='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_436='elseif PMOT < ACSTall',
            Program_Line_437='set ACST = 25+ACSTtol',
            Program_Line_438='elseif PMOT > ACSTaul',
            Program_Line_439='set ACST = 27+ACSTtol',
            Program_Line_440='endif',
            Program_Line_441='elseif CAT==90',
            Program_Line_442='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_443='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_444='elseif PMOT < ACSTall',
            Program_Line_445='set ACST = 24+ACSTtol',
            Program_Line_446='elseif PMOT > ACSTaul',
            Program_Line_447='set ACST = 26+ACSTtol',
            Program_Line_448='endif',
            Program_Line_449='endif',
            Program_Line_450='endif',
            Program_Line_451='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_452='if CAT==80',
            Program_Line_453='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_454='set AHST = PMOT*0.30+25.9+AHSTtol',
            Program_Line_455='elseif PMOT < AHSTall',
            Program_Line_456='set AHST = 19+AHSTtol',
            Program_Line_457='elseif PMOT > AHSTaul',
            Program_Line_458='set AHST = 22+AHSTtol',
            Program_Line_459='endif',
            Program_Line_460='elseif CAT==90',
            Program_Line_461='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_462='set AHST = PMOT*0.30+23.6+AHSTtol',
            Program_Line_463='elseif PMOT < AHSTall',
            Program_Line_464='set AHST = 20+AHSTtol',
            Program_Line_465='elseif PMOT > AHSTaul',
            Program_Line_466='set AHST = 23+AHSTtol',
            Program_Line_467='endif',
            Program_Line_468='endif',
            Program_Line_469='endif',
            Program_Line_470='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_471='if CAT == 80',
            Program_Line_472='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_473='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_474='elseif (PMOT < ACSTall)',
            Program_Line_475='set ACST = ACSTall*0.30+25.9+ACSTtol',
            Program_Line_476='elseif (PMOT > ACSTaul)',
            Program_Line_477='set ACST = ACSTaul*0.30+25.9+ACSTtol',
            Program_Line_478='endif',
            Program_Line_479='elseif CAT == 90',
            Program_Line_480='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_481='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_482='elseif (PMOT < ACSTall)',
            Program_Line_483='set ACST = ACSTall*0.30+23.6+ACSTtol',
            Program_Line_484='elseif (PMOT > ACSTaul)',
            Program_Line_485='set ACST = ACSTaul*0.30+23.6+ACSTtol',
            Program_Line_486='endif',
            Program_Line_487='endif',
            Program_Line_488='endif',
            Program_Line_489='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_490='if CAT == 80',
            Program_Line_491='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_492='set AHST = PMOT*0.32+14.88+AHSTtol',
            Program_Line_493='elseif (PMOT < AHSTall)',
            Program_Line_494='set AHST = AHSTall*0.32+14.88+AHSTtol',
            Program_Line_495='elseif (PMOT > AHSTaul)',
            Program_Line_496='set AHST = AHSTaul*0.32+14.88+AHSTtol',
            Program_Line_497='endif',
            Program_Line_498='elseif CAT == 90',
            Program_Line_499='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_500='set AHST = PMOT*0.31+17.14+AHSTtol',
            Program_Line_501='elseif (PMOT < AHSTall)',
            Program_Line_502='set AHST = AHSTall*0.31+17.14+AHSTtol',
            Program_Line_503='elseif (PMOT > AHSTaul)',
            Program_Line_504='set AHST = AHSTaul*0.31+17.14+AHSTtol',
            Program_Line_505='endif',
            Program_Line_506='endif',
            Program_Line_507='endif',
            Program_Line_508='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_509='if (ComfMod == 0)',
            Program_Line_510='if CAT==80',
            Program_Line_511='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_512='elseif CAT==85',
            Program_Line_513='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_514='elseif CAT==90',
            Program_Line_515='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_516='endif',
            Program_Line_517='endif',
            Program_Line_518='endif',
            Program_Line_519='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_520='if (ComfMod == 0)',
            Program_Line_521='if CAT==80',
            Program_Line_522='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_523='elseif CAT==85',
            Program_Line_524='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_525='elseif CAT==90',
            Program_Line_526='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_527='endif',
            Program_Line_528='endif',
            Program_Line_529='endif',
            Program_Line_530='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_531='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_532='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_533='else',
            Program_Line_534='if CAT==80',
            Program_Line_535='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_536='elseif CAT==85',
            Program_Line_537='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_538='elseif CAT==90',
            Program_Line_539='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_540='endif',
            Program_Line_541='endif',
            Program_Line_542='endif',
            Program_Line_543='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_544='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_545='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_546='else',
            Program_Line_547='if CAT==80',
            Program_Line_548='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_549='elseif CAT==85',
            Program_Line_550='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_551='elseif CAT==90',
            Program_Line_552='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_553='endif',
            Program_Line_554='endif',
            Program_Line_555='endif',
            Program_Line_556='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_557='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_558='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_559='elseif CAT==80',
            Program_Line_560='if PMOT < ACSTall',
            Program_Line_561='set ACST = 25+ACSTtol',
            Program_Line_562='elseif PMOT > ACSTaul',
            Program_Line_563='set ACST = 27+ACSTtol',
            Program_Line_564='endif',
            Program_Line_565='elseif CAT==85',
            Program_Line_566='if PMOT < ACSTall',
            Program_Line_567='set ACST = 25.72+ACSTtol',
            Program_Line_568='elseif PMOT > ACSTaul',
            Program_Line_569='set ACST = 27.89+ACSTtol',
            Program_Line_570='endif',
            Program_Line_571='elseif CAT==90',
            Program_Line_572='if PMOT < ACSTall',
            Program_Line_573='set ACST = 24+ACSTtol',
            Program_Line_574='elseif PMOT > ACSTaul',
            Program_Line_575='set ACST = 26+ACSTtol',
            Program_Line_576='endif',
            Program_Line_577='endif',
            Program_Line_578='endif',
            Program_Line_579='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_580='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_581='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_582='elseif CAT==80',
            Program_Line_583='if PMOT < AHSTall',
            Program_Line_584='set AHST = 19+AHSTtol',
            Program_Line_585='elseif PMOT > AHSTaul',
            Program_Line_586='set AHST = 22+AHSTtol',
            Program_Line_587='endif',
            Program_Line_588='elseif CAT==85',
            Program_Line_589='if PMOT < AHSTall',
            Program_Line_590='set AHST = 20.77+AHSTtol',
            Program_Line_591='elseif PMOT > AHSTaul',
            Program_Line_592='set AHST = 24.26+AHSTtol',
            Program_Line_593='endif',
            Program_Line_594='elseif CAT==90',
            Program_Line_595='if PMOT < AHSTall',
            Program_Line_596='set AHST = 20+AHSTtol',
            Program_Line_597='elseif PMOT > AHSTaul',
            Program_Line_598='set AHST = 23+AHSTtol',
            Program_Line_599='endif',
            Program_Line_600='endif',
            Program_Line_601='endif',
            Program_Line_602='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_603='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_604='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_605='elseif PMOT < ACSTall',
            Program_Line_606='set ACST = ACSTall*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_607='elseif PMOT > ACSTaul',
            Program_Line_608='set ACST = ACSTaul*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_609='endif',
            Program_Line_610='endif',
            Program_Line_611='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_612='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_613='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_614='elseif PMOT < AHSTall',
            Program_Line_615='set AHST = AHSTall*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_616='elseif PMOT > AHSTaul',
            Program_Line_617='set AHST = AHSTaul*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_618='endif',
            Program_Line_619='endif',
            Program_Line_620='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_621='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_622='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_623='else',
            Program_Line_624='if CAT==80',
            Program_Line_625='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_626='elseif CAT==85',
            Program_Line_627='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_628='elseif CAT==90',
            Program_Line_629='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_630='endif',
            Program_Line_631='endif',
            Program_Line_632='endif',
            Program_Line_633='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_634='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_635='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_636='else',
            Program_Line_637='if CAT==80',
            Program_Line_638='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_639='elseif CAT==85',
            Program_Line_640='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_641='elseif CAT==90',
            Program_Line_642='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_643='endif',
            Program_Line_644='endif',
            Program_Line_645='endif',
            Program_Line_646='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_647='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_648='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_649='elseif CAT==80',
            Program_Line_650='if PMOT < ACSTall',
            Program_Line_651='set ACST = 25+ACSTtol',
            Program_Line_652='elseif PMOT > ACSTaul',
            Program_Line_653='set ACST = 27+ACSTtol',
            Program_Line_654='endif',
            Program_Line_655='elseif CAT==85',
            Program_Line_656='if PMOT < ACSTall',
            Program_Line_657='set ACST = 25.72+ACSTtol',
            Program_Line_658='elseif PMOT > ACSTaul',
            Program_Line_659='set ACST = 27.89+ACSTtol',
            Program_Line_660='endif',
            Program_Line_661='elseif CAT==90',
            Program_Line_662='if PMOT < ACSTall',
            Program_Line_663='set ACST = 24+ACSTtol',
            Program_Line_664='elseif PMOT > ACSTaul',
            Program_Line_665='set ACST = 26+ACSTtol',
            Program_Line_666='endif',
            Program_Line_667='endif',
            Program_Line_668='endif',
            Program_Line_669='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_670='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_671='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_672='elseif CAT==80',
            Program_Line_673='if PMOT < AHSTall',
            Program_Line_674='set AHST = 19+AHSTtol',
            Program_Line_675='elseif PMOT > AHSTaul',
            Program_Line_676='set AHST = 22+AHSTtol',
            Program_Line_677='endif',
            Program_Line_678='elseif CAT==85',
            Program_Line_679='if PMOT < AHSTall',
            Program_Line_680='set AHST = 20.77+AHSTtol',
            Program_Line_681='elseif PMOT > AHSTaul',
            Program_Line_682='set AHST = 24.26+AHSTtol',
            Program_Line_683='endif',
            Program_Line_684='elseif CAT==90',
            Program_Line_685='if PMOT < AHSTall',
            Program_Line_686='set AHST = 20+AHSTtol',
            Program_Line_687='elseif PMOT > AHSTaul',
            Program_Line_688='set AHST = 23+AHSTtol',
            Program_Line_689='endif',
            Program_Line_690='endif',
            Program_Line_691='endif',
            Program_Line_692='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_693='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_694='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_695='elseif PMOT < ACSTall',
            Program_Line_696='set ACST = ACSTall*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_697='elseif PMOT > ACSTaul',
            Program_Line_698='set ACST = ACSTaul*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_699='endif',
            Program_Line_700='endif',
            Program_Line_701='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_702='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_703='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_704='elseif PMOT < AHSTall',
            Program_Line_705='set AHST = AHSTall*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_706='elseif PMOT > AHSTaul',
            Program_Line_707='set AHST = AHSTaul*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_708='endif',
            Program_Line_709='endif',
            Program_Line_710='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_711='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_712='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_713='else',
            Program_Line_714='if CAT==80',
            Program_Line_715='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_716='elseif CAT==90',
            Program_Line_717='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_718='endif',
            Program_Line_719='endif',
            Program_Line_720='endif',
            Program_Line_721='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_722='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_723='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_724='else',
            Program_Line_725='if CAT==80',
            Program_Line_726='set AHST = PMOT*0.078+23.25+2.72+AHSTtol',
            Program_Line_727='elseif CAT==90',
            Program_Line_728='set AHST = PMOT*0.078+23.25+1.5+AHSTtol',
            Program_Line_729='endif',
            Program_Line_730='endif',
            Program_Line_731='endif',
            Program_Line_732='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_733='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_734='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_735='elseif CAT==80',
            Program_Line_736='if PMOT < ACSTall',
            Program_Line_737='set ACST = 25+ACSTtol',
            Program_Line_738='elseif PMOT > ACSTaul',
            Program_Line_739='set ACST = 27+ACSTtol',
            Program_Line_740='endif',
            Program_Line_741='elseif CAT==90',
            Program_Line_742='if PMOT < ACSTall',
            Program_Line_743='set ACST = 24+ACSTtol',
            Program_Line_744='elseif PMOT > ACSTaul',
            Program_Line_745='set ACST = 26+ACSTtol',
            Program_Line_746='endif',
            Program_Line_747='endif',
            Program_Line_748='endif',
            Program_Line_749='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_750='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_751='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_752='elseif CAT==80',
            Program_Line_753='if PMOT < AHSTall',
            Program_Line_754='set AHST = 19+AHSTtol',
            Program_Line_755='elseif PMOT > AHSTaul',
            Program_Line_756='set AHST = 22+AHSTtol',
            Program_Line_757='endif',
            Program_Line_758='elseif CAT==90',
            Program_Line_759='if PMOT < AHSTall',
            Program_Line_760='set AHST = 20+AHSTtol',
            Program_Line_761='elseif PMOT > AHSTaul',
            Program_Line_762='set AHST = 23+AHSTtol',
            Program_Line_763='endif',
            Program_Line_764='endif',
            Program_Line_765='endif',
            Program_Line_766='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_767='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_768='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_769='elseif PMOT < ACSTall',
            Program_Line_770='set ACST = ACSTall*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_771='elseif PMOT > ACSTaul',
            Program_Line_772='set ACST = ACSTaul*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_773='endif',
            Program_Line_774='endif',
            Program_Line_775='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_776='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_777='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_778='elseif PMOT < AHSTall',
            Program_Line_779='set AHST = AHSTall*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_780='elseif PMOT > AHSTaul',
            Program_Line_781='set AHST = AHSTaul*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_782='endif',
            Program_Line_783='endif',
            Program_Line_784='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_785='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_786='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_787='else',
            Program_Line_788='if CAT==80',
            Program_Line_789='set ACST = RMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_790='elseif CAT==90',
            Program_Line_791='set ACST = RMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_792='endif',
            Program_Line_793='endif',
            Program_Line_794='endif',
            Program_Line_795='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_796='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_797='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_798='else',
            Program_Line_799='if CAT==80',
            Program_Line_800='set AHST = RMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_801='elseif CAT==90',
            Program_Line_802='set AHST = RMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_803='endif',
            Program_Line_804='endif',
            Program_Line_805='endif',
            Program_Line_806='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_807='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_808='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_809='elseif CAT==80',
            Program_Line_810='if RMOT < ACSTall',
            Program_Line_811='set ACST = 25+ACSTtol',
            Program_Line_812='elseif RMOT > ACSTaul',
            Program_Line_813='set ACST = 27+ACSTtol',
            Program_Line_814='endif',
            Program_Line_815='elseif CAT==90',
            Program_Line_816='if RMOT < ACSTall',
            Program_Line_817='set ACST = 24+ACSTtol',
            Program_Line_818='elseif RMOT > ACSTaul',
            Program_Line_819='set ACST = 26+ACSTtol',
            Program_Line_820='endif',
            Program_Line_821='endif',
            Program_Line_822='endif',
            Program_Line_823='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_824='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_825='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_826='elseif CAT==80',
            Program_Line_827='if RMOT < AHSTall',
            Program_Line_828='set AHST = 19+AHSTtol',
            Program_Line_829='elseif RMOT > AHSTaul',
            Program_Line_830='set AHST = 22+AHSTtol',
            Program_Line_831='endif',
            Program_Line_832='elseif CAT==90',
            Program_Line_833='if RMOT < AHSTall',
            Program_Line_834='set AHST = 20+AHSTtol',
            Program_Line_835='elseif RMOT > AHSTaul',
            Program_Line_836='set AHST = 23+AHSTtol',
            Program_Line_837='endif',
            Program_Line_838='endif',
            Program_Line_839='endif',
            Program_Line_840='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_841='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_842='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_843='elseif RMOT < ACSTall',
            Program_Line_844='set ACST = ACSTall*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_845='elseif RMOT > ACSTaul',
            Program_Line_846='set ACST = ACSTaul*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_847='endif',
            Program_Line_848='endif',
            Program_Line_849='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_850='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_851='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_852='elseif RMOT < AHSTall',
            Program_Line_853='set AHST = AHSTall*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_854='elseif RMOT > AHSTaul',
            Program_Line_855='set AHST = AHSTaul*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_856='endif',
            Program_Line_857='endif',
            Program_Line_858='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_859='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_860='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_861='else',
            Program_Line_862='if CAT==80',
            Program_Line_863='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_864='elseif CAT==90',
            Program_Line_865='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_866='endif',
            Program_Line_867='endif',
            Program_Line_868='endif',
            Program_Line_869='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_870='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_871='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_872='else',
            Program_Line_873='if CAT==80',
            Program_Line_874='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_875='elseif CAT==90',
            Program_Line_876='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_877='endif',
            Program_Line_878='endif',
            Program_Line_879='endif',
            Program_Line_880='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_881='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_882='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_883='elseif CAT==80',
            Program_Line_884='if PMOT < ACSTall',
            Program_Line_885='set ACST = 25+ACSTtol',
            Program_Line_886='elseif PMOT > ACSTaul',
            Program_Line_887='set ACST = 27+ACSTtol',
            Program_Line_888='endif',
            Program_Line_889='elseif CAT==90',
            Program_Line_890='if PMOT < ACSTall',
            Program_Line_891='set ACST = 24+ACSTtol',
            Program_Line_892='elseif PMOT > ACSTaul',
            Program_Line_893='set ACST = 26+ACSTtol',
            Program_Line_894='endif',
            Program_Line_895='endif',
            Program_Line_896='endif',
            Program_Line_897='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_898='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_899='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_900='elseif CAT==80',
            Program_Line_901='if PMOT < AHSTall',
            Program_Line_902='set AHST = 19+AHSTtol',
            Program_Line_903='elseif PMOT > AHSTaul',
            Program_Line_904='set AHST = 22+AHSTtol',
            Program_Line_905='endif',
            Program_Line_906='elseif CAT==90',
            Program_Line_907='if PMOT < AHSTall',
            Program_Line_908='set AHST = 20+AHSTtol',
            Program_Line_909='elseif PMOT > AHSTaul',
            Program_Line_910='set AHST = 23+AHSTtol',
            Program_Line_911='endif',
            Program_Line_912='endif',
            Program_Line_913='endif',
            Program_Line_914='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_915='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_916='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_917='elseif PMOT < ACSTall',
            Program_Line_918='set ACST = ACSTall*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_919='elseif PMOT > ACSTaul',
            Program_Line_920='set ACST = ACSTaul*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_921='endif',
            Program_Line_922='endif',
            Program_Line_923='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_924='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_925='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_926='elseif PMOT < AHSTall',
            Program_Line_927='set AHST = AHSTall*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_928='elseif PMOT > AHSTaul',
            Program_Line_929='set AHST = AHSTaul*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_930='endif',
            Program_Line_931='endif',
            Program_Line_932='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_933='if (CAT==80)',
            Program_Line_934='set ACST = 27+ACSTtol',
            Program_Line_935='elseif (CAT==90)',
            Program_Line_936='set ACST = 25.5+ACSTtol',
            Program_Line_937='endif',
            Program_Line_938='endif',
            Program_Line_939='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_940='if (CAT==80)',
            Program_Line_941='set AHST = 20+AHSTtol',
            Program_Line_942='elseif (CAT==90)',
            Program_Line_943='set AHST = 21.5+AHSTtol',
            Program_Line_944='endif',
            Program_Line_945='endif',
            Program_Line_946='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_947='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_948='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_949='elseif CAT==80',
            Program_Line_950='if PMOT < ACSTall',
            Program_Line_951='set ACST = 27+ACSTtol',
            Program_Line_952='elseif PMOT > ACSTaul',
            Program_Line_953='set ACST = 27+ACSTtol',
            Program_Line_954='endif',
            Program_Line_955='elseif CAT==90',
            Program_Line_956='if PMOT < ACSTall',
            Program_Line_957='set ACST = 25.5+ACSTtol',
            Program_Line_958='elseif PMOT > ACSTaul',
            Program_Line_959='set ACST = 25.5+ACSTtol',
            Program_Line_960='endif',
            Program_Line_961='endif',
            Program_Line_962='endif',
            Program_Line_963='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_964='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_965='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_966='elseif CAT==80',
            Program_Line_967='if PMOT < AHSTall',
            Program_Line_968='set AHST = 20+AHSTtol',
            Program_Line_969='elseif PMOT > AHSTaul',
            Program_Line_970='set AHST = 20+AHSTtol',
            Program_Line_971='endif',
            Program_Line_972='elseif CAT==90',
            Program_Line_973='if PMOT < AHSTall',
            Program_Line_974='set AHST = 21.5+AHSTtol',
            Program_Line_975='elseif PMOT > AHSTaul',
            Program_Line_976='set AHST = 21.5+AHSTtol',
            Program_Line_977='endif',
            Program_Line_978='endif',
            Program_Line_979='endif',
            Program_Line_980='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_981='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_982='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_983='elseif CAT==80',
            Program_Line_984='if PMOT < ACSTall',
            Program_Line_985='set ACST = 25+ACSTtol',
            Program_Line_986='elseif PMOT > ACSTaul',
            Program_Line_987='set ACST = 27+ACSTtol',
            Program_Line_988='endif',
            Program_Line_989='elseif CAT==90',
            Program_Line_990='if PMOT < ACSTall',
            Program_Line_991='set ACST = 24+ACSTtol',
            Program_Line_992='elseif PMOT > ACSTaul',
            Program_Line_993='set ACST = 26+ACSTtol',
            Program_Line_994='endif',
            Program_Line_995='endif',
            Program_Line_996='endif',
            Program_Line_997='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_998='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_999='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1000='elseif CAT==80',
            Program_Line_1001='if PMOT < AHSTall',
            Program_Line_1002='set AHST = 19+AHSTtol',
            Program_Line_1003='elseif PMOT > AHSTaul',
            Program_Line_1004='set AHST = 22+AHSTtol',
            Program_Line_1005='endif',
            Program_Line_1006='elseif CAT==90',
            Program_Line_1007='if PMOT < AHSTall',
            Program_Line_1008='set AHST = 20+AHSTtol',
            Program_Line_1009='elseif PMOT > AHSTaul',
            Program_Line_1010='set AHST = 23+AHSTtol',
            Program_Line_1011='endif',
            Program_Line_1012='endif',
            Program_Line_1013='endif',
            Program_Line_1014='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_1015='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1016='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1017='elseif PMOT < ACSTall',
            Program_Line_1018='set ACST = ACSTall*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1019='elseif PMOT > ACSTaul',
            Program_Line_1020='set ACST = ACSTaul*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1021='endif',
            Program_Line_1022='endif',
            Program_Line_1023='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_1024='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1025='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1026='elseif PMOT < AHSTall',
            Program_Line_1027='set AHST = AHSTall*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1028='elseif PMOT > AHSTaul',
            Program_Line_1029='set AHST = AHSTaul*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1030='endif',
            Program_Line_1031='endif',
            Program_Line_1032='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_1033='if (CAT==80)',
            Program_Line_1034='if (CurrentTime > 6) && (CurrentTime < 23)',
            Program_Line_1035='if (ComfMod == 0.1)',
            Program_Line_1036='set ACST = 27+ACSTtol',
            Program_Line_1037='elseif (ComfMod == 0.2)',
            Program_Line_1038='set ACST = 26+ACSTtol',
            Program_Line_1039='elseif (ComfMod == 0.3)',
            Program_Line_1040='set ACST = 25+ACSTtol',
            Program_Line_1041='elseif (ComfMod == 0.4)',
            Program_Line_1042='set ACST = 24+ACSTtol',
            Program_Line_1043='elseif (ComfMod == 0.5)',
            Program_Line_1044='set ACST = 23+ACSTtol',
            Program_Line_1045='endif',
            Program_Line_1046='else',
            Program_Line_1047='set ACST = 24+ACSTtol',
            Program_Line_1048='endif',
            Program_Line_1049='elseif (CAT==90)',
            Program_Line_1050='if (CurrentTime > 6) && (CurrentTime < 23)',
            Program_Line_1051='if (ComfMod == 0.1)',
            Program_Line_1052='set ACST = 26+ACSTtol',
            Program_Line_1053='elseif (ComfMod == 0.2)',
            Program_Line_1054='set ACST = 25+ACSTtol',
            Program_Line_1055='elseif (ComfMod == 0.3)',
            Program_Line_1056='set ACST = 24+ACSTtol',
            Program_Line_1057='elseif (ComfMod == 0.4)',
            Program_Line_1058='set ACST = 23+ACSTtol',
            Program_Line_1059='elseif (ComfMod == 0.5)',
            Program_Line_1060='set ACST = 22+ACSTtol',
            Program_Line_1061='endif',
            Program_Line_1062='else',
            Program_Line_1063='set ACST = 23+ACSTtol',
            Program_Line_1064='endif',
            Program_Line_1065='endif',
            Program_Line_1066='endif',
            Program_Line_1067='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_1068='if (ComfMod == 0.1) || (ComfMod == 0.2) || (ComfMod == 0.3) || (ComfMod == 0.4) || (ComfMod == 0.5)',
            Program_Line_1069='if (CAT==80)',
            Program_Line_1070='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1071='set AHST = 20+AHSTtol',
            Program_Line_1072='else',
            Program_Line_1073='set AHST = 18+AHSTtol',
            Program_Line_1074='endif',
            Program_Line_1075='elseif (CAT==90)',
            Program_Line_1076='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1077='set AHST = 21+AHSTtol',
            Program_Line_1078='else',
            Program_Line_1079='set AHST = 19+AHSTtol',
            Program_Line_1080='endif',
            Program_Line_1081='endif',
            Program_Line_1082='endif',
            Program_Line_1083='endif',
            Program_Line_1084='if (ComfStand == 13)',
            Program_Line_1085='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1086='if CAT == 80',
            Program_Line_1087='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1088='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1089='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1090='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1091='set ACST = 27+ACSTtol',
            Program_Line_1092='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1093='set ACST = 26+ACSTtol',
            Program_Line_1094='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1095='set ACST = 25+ACSTtol',
            Program_Line_1096='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1097='set ACST = 24+ACSTtol',
            Program_Line_1098='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1099='set ACST = 23+ACSTtol',
            Program_Line_1100='else',
            Program_Line_1101='set ACST = 24+ACSTtol',
            Program_Line_1102='endif',
            Program_Line_1103='endif',
            Program_Line_1104='elseif CAT==90',
            Program_Line_1105='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1106='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1107='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1108='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1109='set ACST = 26+ACSTtol',
            Program_Line_1110='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1111='set ACST = 25+ACSTtol',
            Program_Line_1112='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1113='set ACST = 24+ACSTtol',
            Program_Line_1114='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1115='set ACST = 23+ACSTtol',
            Program_Line_1116='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1117='set ACST = 22+ACSTtol',
            Program_Line_1118='else',
            Program_Line_1119='set ACST = 23+ACSTtol',
            Program_Line_1120='endif',
            Program_Line_1121='endif',
            Program_Line_1122='endif',
            Program_Line_1123='endif',
            Program_Line_1124='endif',
            Program_Line_1125='if (ComfStand == 13)',
            Program_Line_1126='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1127='if CAT == 80',
            Program_Line_1128='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1129='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1130='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1131='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1132='set AHST = 20+AHSTtol',
            Program_Line_1133='else',
            Program_Line_1134='set AHST = 18+AHSTtol',
            Program_Line_1135='endif',
            Program_Line_1136='endif',
            Program_Line_1137='elseif CAT==90',
            Program_Line_1138='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1139='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1140='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1141='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1142='set AHST = 21+AHSTtol',
            Program_Line_1143='else',
            Program_Line_1144='set AHST = 19+AHSTtol',
            Program_Line_1145='endif',
            Program_Line_1146='endif',
            Program_Line_1147='endif',
            Program_Line_1148='endif',
            Program_Line_1149='endif',
            Program_Line_1150='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1151='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1152='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1153='elseif CAT==80',
            Program_Line_1154='if PMOT < ACSTall',
            Program_Line_1155='set ACST = 25+ACSTtol',
            Program_Line_1156='elseif PMOT > ACSTaul',
            Program_Line_1157='set ACST = 27+ACSTtol',
            Program_Line_1158='endif',
            Program_Line_1159='elseif CAT==90',
            Program_Line_1160='if PMOT < ACSTall',
            Program_Line_1161='set ACST = 24+ACSTtol',
            Program_Line_1162='elseif PMOT > ACSTaul',
            Program_Line_1163='set ACST = 26+ACSTtol',
            Program_Line_1164='endif',
            Program_Line_1165='endif',
            Program_Line_1166='endif',
            Program_Line_1167='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1168='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1169='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1170='elseif CAT==80',
            Program_Line_1171='if PMOT < AHSTall',
            Program_Line_1172='set AHST = 19+AHSTtol',
            Program_Line_1173='elseif PMOT > AHSTaul',
            Program_Line_1174='set AHST = 22+AHSTtol',
            Program_Line_1175='endif',
            Program_Line_1176='elseif CAT==90',
            Program_Line_1177='if PMOT < AHSTall',
            Program_Line_1178='set AHST = 20+AHSTtol',
            Program_Line_1179='elseif PMOT > AHSTaul',
            Program_Line_1180='set AHST = 23+AHSTtol',
            Program_Line_1181='endif',
            Program_Line_1182='endif',
            Program_Line_1183='endif',
            Program_Line_1184='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1185='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1186='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1187='elseif PMOT < ACSTall',
            Program_Line_1188='set ACST = ACSTall*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1189='elseif PMOT > ACSTaul',
            Program_Line_1190='set ACST = ACSTaul*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1191='endif',
            Program_Line_1192='endif',
            Program_Line_1193='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1194='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1195='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1196='elseif PMOT < AHSTall',
            Program_Line_1197='set AHST = AHSTall*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1198='elseif PMOT > AHSTaul',
            Program_Line_1199='set AHST = AHSTaul*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1200='endif',
            Program_Line_1201='endif',
            Program_Line_1202='if (ComfStand == 14)',
            Program_Line_1203='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1204='if CAT == 80',
            Program_Line_1205='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1206='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1207='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1208='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1209='set ACST = 27+ACSTtol',
            Program_Line_1210='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1211='set ACST = 26+ACSTtol',
            Program_Line_1212='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1213='set ACST = 25+ACSTtol',
            Program_Line_1214='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1215='set ACST = 24+ACSTtol',
            Program_Line_1216='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1217='set ACST = 23+ACSTtol',
            Program_Line_1218='else',
            Program_Line_1219='set ACST = 24+ACSTtol',
            Program_Line_1220='endif',
            Program_Line_1221='endif',
            Program_Line_1222='elseif CAT==90',
            Program_Line_1223='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1224='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1225='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1226='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1227='set ACST = 26+ACSTtol',
            Program_Line_1228='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1229='set ACST = 25+ACSTtol',
            Program_Line_1230='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1231='set ACST = 24+ACSTtol',
            Program_Line_1232='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1233='set ACST = 23+ACSTtol',
            Program_Line_1234='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1235='set ACST = 22+ACSTtol',
            Program_Line_1236='else',
            Program_Line_1237='set ACST = 23+ACSTtol',
            Program_Line_1238='endif',
            Program_Line_1239='endif',
            Program_Line_1240='endif',
            Program_Line_1241='endif',
            Program_Line_1242='endif',
            Program_Line_1243='if (ComfStand == 14)',
            Program_Line_1244='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1245='if CAT == 80',
            Program_Line_1246='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1247='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1248='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1249='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1250='set AHST = 20+AHSTtol',
            Program_Line_1251='else',
            Program_Line_1252='set AHST = 18+AHSTtol',
            Program_Line_1253='endif',
            Program_Line_1254='endif',
            Program_Line_1255='elseif CAT==90',
            Program_Line_1256='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1257='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1258='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1259='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1260='set AHST = 21+AHSTtol',
            Program_Line_1261='else',
            Program_Line_1262='set AHST = 19+AHSTtol',
            Program_Line_1263='endif',
            Program_Line_1264='endif',
            Program_Line_1265='endif',
            Program_Line_1266='endif',
            Program_Line_1267='endif',
            Program_Line_1268='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1269='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1270='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1271='elseif CAT==80',
            Program_Line_1272='if PMOT < ACSTall',
            Program_Line_1273='set ACST = 25+ACSTtol',
            Program_Line_1274='elseif PMOT > ACSTaul',
            Program_Line_1275='set ACST = 27+ACSTtol',
            Program_Line_1276='endif',
            Program_Line_1277='elseif CAT==90',
            Program_Line_1278='if PMOT < ACSTall',
            Program_Line_1279='set ACST = 24+ACSTtol',
            Program_Line_1280='elseif PMOT > ACSTaul',
            Program_Line_1281='set ACST = 26+ACSTtol',
            Program_Line_1282='endif',
            Program_Line_1283='endif',
            Program_Line_1284='endif',
            Program_Line_1285='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1286='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1287='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1288='elseif CAT==80',
            Program_Line_1289='if PMOT < AHSTall',
            Program_Line_1290='set AHST = 19+AHSTtol',
            Program_Line_1291='elseif PMOT > AHSTaul',
            Program_Line_1292='set AHST = 22+AHSTtol',
            Program_Line_1293='endif',
            Program_Line_1294='elseif CAT==90',
            Program_Line_1295='if PMOT < AHSTall',
            Program_Line_1296='set AHST = 20+AHSTtol',
            Program_Line_1297='elseif PMOT > AHSTaul',
            Program_Line_1298='set AHST = 23+AHSTtol',
            Program_Line_1299='endif',
            Program_Line_1300='endif',
            Program_Line_1301='endif',
            Program_Line_1302='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1303='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1304='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1305='elseif PMOT < ACSTall',
            Program_Line_1306='set ACST = ACSTall*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1307='elseif PMOT > ACSTaul',
            Program_Line_1308='set ACST = ACSTaul*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1309='endif',
            Program_Line_1310='endif',
            Program_Line_1311='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1312='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1313='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1314='elseif PMOT < AHSTall',
            Program_Line_1315='set AHST = AHSTall*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1316='elseif PMOT > AHSTaul',
            Program_Line_1317='set AHST = AHSTaul*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1318='endif',
            Program_Line_1319='endif',
            Program_Line_1320='if (ComfStand == 15) || (ComfStand == 16)',
            Program_Line_1321='if (ComfMod == 0)',
            Program_Line_1322='if (CAT==80)',
            Program_Line_1323='if PMOT < 20',
            Program_Line_1324='set ACST = 23.5+ACSTtol',
            Program_Line_1325='set AHST = 21+ACSTtol',
            Program_Line_1326='else',
            Program_Line_1327='set ACST = 25.5+ACSTtol',
            Program_Line_1328='set AHST = 22.5+ACSTtol',
            Program_Line_1329='endif',
            Program_Line_1330='elseif (CAT==90)',
            Program_Line_1331='if PMOT < 20',
            Program_Line_1332='set ACST = 23+ACSTtol',
            Program_Line_1333='set AHST = 21.5+ACSTtol',
            Program_Line_1334='else',
            Program_Line_1335='set ACST = 25+ACSTtol',
            Program_Line_1336='set AHST = 23+ACSTtol',
            Program_Line_1337='endif',
            Program_Line_1338='endif',
            Program_Line_1339='endif',
            Program_Line_1340='endif',
            Program_Line_1341='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1342='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1343='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1344='elseif CAT==80',
            Program_Line_1345='if PMOT < ACSTall',
            Program_Line_1346='set ACST = 23.5+ACSTtol',
            Program_Line_1347='elseif PMOT > ACSTaul',
            Program_Line_1348='set ACST = 25.5+ACSTtol',
            Program_Line_1349='endif',
            Program_Line_1350='elseif CAT==90',
            Program_Line_1351='if PMOT < ACSTall',
            Program_Line_1352='set ACST = 23+ACSTtol',
            Program_Line_1353='elseif PMOT > ACSTaul',
            Program_Line_1354='set ACST = 25+ACSTtol',
            Program_Line_1355='endif',
            Program_Line_1356='endif',
            Program_Line_1357='endif',
            Program_Line_1358='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1359='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1360='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1361='elseif CAT==80',
            Program_Line_1362='if PMOT < AHSTall',
            Program_Line_1363='set AHST = 21+AHSTtol',
            Program_Line_1364='elseif PMOT > AHSTaul',
            Program_Line_1365='set AHST = 22.5+AHSTtol',
            Program_Line_1366='endif',
            Program_Line_1367='elseif CAT==90',
            Program_Line_1368='if PMOT < AHSTall',
            Program_Line_1369='set AHST = 23+AHSTtol',
            Program_Line_1370='elseif PMOT > AHSTaul',
            Program_Line_1371='set AHST = 23+AHSTtol',
            Program_Line_1372='endif',
            Program_Line_1373='endif',
            Program_Line_1374='endif',
            Program_Line_1375='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1376='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1377='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1378='elseif CAT==80',
            Program_Line_1379='if PMOT < ACSTall',
            Program_Line_1380='set ACST = 25+ACSTtol',
            Program_Line_1381='elseif PMOT > ACSTaul',
            Program_Line_1382='set ACST = 27+ACSTtol',
            Program_Line_1383='endif',
            Program_Line_1384='elseif CAT==90',
            Program_Line_1385='if PMOT < ACSTall',
            Program_Line_1386='set ACST = 24+ACSTtol',
            Program_Line_1387='elseif PMOT > ACSTaul',
            Program_Line_1388='set ACST = 26+ACSTtol',
            Program_Line_1389='endif',
            Program_Line_1390='endif',
            Program_Line_1391='endif',
            Program_Line_1392='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1393='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1394='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1395='elseif CAT==80',
            Program_Line_1396='if PMOT < AHSTall',
            Program_Line_1397='set AHST = 19+AHSTtol',
            Program_Line_1398='elseif PMOT > AHSTaul',
            Program_Line_1399='set AHST = 22+AHSTtol',
            Program_Line_1400='endif',
            Program_Line_1401='elseif CAT==90',
            Program_Line_1402='if PMOT < AHSTall',
            Program_Line_1403='set AHST = 20+AHSTtol',
            Program_Line_1404='elseif PMOT > AHSTaul',
            Program_Line_1405='set AHST = 23+AHSTtol',
            Program_Line_1406='endif',
            Program_Line_1407='endif',
            Program_Line_1408='endif',
            Program_Line_1409='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1410='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1411='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1412='elseif PMOT < ACSTall',
            Program_Line_1413='set ACST = ACSTall*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1414='elseif PMOT > ACSTaul',
            Program_Line_1415='set ACST = ACSTaul*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1416='endif',
            Program_Line_1417='endif',
            Program_Line_1418='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1419='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1420='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1421='elseif PMOT < AHSTall',
            Program_Line_1422='set AHST = AHSTall*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1423='elseif PMOT > AHSTaul',
            Program_Line_1424='set AHST = AHSTaul*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1425='endif',
            Program_Line_1426='endif',
            Program_Line_1427='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1428='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1429='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1430='elseif CAT==80',
            Program_Line_1431='if PMOT < ACSTall',
            Program_Line_1432='set ACST = 23.5+ACSTtol',
            Program_Line_1433='elseif PMOT > ACSTaul',
            Program_Line_1434='set ACST = 25.5+ACSTtol',
            Program_Line_1435='endif',
            Program_Line_1436='elseif CAT==90',
            Program_Line_1437='if PMOT < ACSTall',
            Program_Line_1438='set ACST = 23+ACSTtol',
            Program_Line_1439='elseif PMOT > ACSTaul',
            Program_Line_1440='set ACST = 25+ACSTtol',
            Program_Line_1441='endif',
            Program_Line_1442='endif',
            Program_Line_1443='endif',
            Program_Line_1444='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1445='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1446='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1447='elseif CAT==80',
            Program_Line_1448='if PMOT < AHSTall',
            Program_Line_1449='set AHST = 21+AHSTtol',
            Program_Line_1450='elseif PMOT > AHSTaul',
            Program_Line_1451='set AHST = 22.5+AHSTtol',
            Program_Line_1452='endif',
            Program_Line_1453='elseif CAT==90',
            Program_Line_1454='if PMOT < AHSTall',
            Program_Line_1455='set AHST = 23+AHSTtol',
            Program_Line_1456='elseif PMOT > AHSTaul',
            Program_Line_1457='set AHST = 23+AHSTtol',
            Program_Line_1458='endif',
            Program_Line_1459='endif',
            Program_Line_1460='endif',
            Program_Line_1461='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1462='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1463='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1464='elseif CAT==80',
            Program_Line_1465='if PMOT < ACSTall',
            Program_Line_1466='set ACST = 25+ACSTtol',
            Program_Line_1467='elseif PMOT > ACSTaul',
            Program_Line_1468='set ACST = 27+ACSTtol',
            Program_Line_1469='endif',
            Program_Line_1470='elseif CAT==90',
            Program_Line_1471='if PMOT < ACSTall',
            Program_Line_1472='set ACST = 24+ACSTtol',
            Program_Line_1473='elseif PMOT > ACSTaul',
            Program_Line_1474='set ACST = 26+ACSTtol',
            Program_Line_1475='endif',
            Program_Line_1476='endif',
            Program_Line_1477='endif',
            Program_Line_1478='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1479='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1480='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1481='elseif CAT==80',
            Program_Line_1482='if PMOT < AHSTall',
            Program_Line_1483='set AHST = 19+AHSTtol',
            Program_Line_1484='elseif PMOT > AHSTaul',
            Program_Line_1485='set AHST = 22+AHSTtol',
            Program_Line_1486='endif',
            Program_Line_1487='elseif CAT==90',
            Program_Line_1488='if PMOT < AHSTall',
            Program_Line_1489='set AHST = 20+AHSTtol',
            Program_Line_1490='elseif PMOT > AHSTaul',
            Program_Line_1491='set AHST = 23+AHSTtol',
            Program_Line_1492='endif',
            Program_Line_1493='endif',
            Program_Line_1494='endif',
            Program_Line_1495='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1496='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1497='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1498='elseif PMOT < ACSTall',
            Program_Line_1499='set ACST = ACSTall*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1500='elseif PMOT > ACSTaul',
            Program_Line_1501='set ACST = ACSTaul*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1502='endif',
            Program_Line_1503='endif',
            Program_Line_1504='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1505='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1506='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1507='elseif PMOT < AHSTall',
            Program_Line_1508='set AHST = AHSTall*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1509='elseif PMOT > AHSTaul',
            Program_Line_1510='set AHST = AHSTaul*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1511='endif',
            Program_Line_1512='endif',
            Program_Line_1513='if (ComfStand == 17) || (ComfStand == 18) || (ComfStand == 19) || (ComfStand == 20)',
            Program_Line_1514='if ComfMod == 0',
            Program_Line_1515='set ACST = 25+ACSTtol',
            Program_Line_1516='set AHST = 20+AHSTtol',
            Program_Line_1517='endif',
            Program_Line_1518='endif',
            Program_Line_1519='if (ComfStand == 17) && (ComfMod == 1)',
            Program_Line_1520='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1521='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1522='set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1523='else',
            Program_Line_1524='set ACST = 25+ACSTtol',
            Program_Line_1525='endif',
            Program_Line_1526='else',
            Program_Line_1527='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1528='set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1529='else',
            Program_Line_1530='set ACST = 25+ACSTtol',
            Program_Line_1531='endif',
            Program_Line_1532='endif',
            Program_Line_1533='endif',
            Program_Line_1534='if (ComfStand == 17) && (ComfMod == 1)',
            Program_Line_1535='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1536='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1537='set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1538='else',
            Program_Line_1539='set AHST = 20+AHSTtol',
            Program_Line_1540='endif',
            Program_Line_1541='else',
            Program_Line_1542='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1543='set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1544='else',
            Program_Line_1545='set AHST = 20+AHSTtol',
            Program_Line_1546='endif',
            Program_Line_1547='endif',
            Program_Line_1548='endif',
            Program_Line_1549='if (ComfStand == 17) && (ComfMod == 2)',
            Program_Line_1550='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1551='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1552='set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1553='elseif PMOT < ACSTall',
            Program_Line_1554='if CAT == 90',
            Program_Line_1555='set ACST = 24+ACSTtol',
            Program_Line_1556='elseif CAT == 80',
            Program_Line_1557='set ACST = 25+ACSTtol',
            Program_Line_1558='endif',
            Program_Line_1559='elseif PMOT > ACSTaul',
            Program_Line_1560='if CAT == 90',
            Program_Line_1561='set ACST = 26+ACSTtol',
            Program_Line_1562='elseif CAT == 80',
            Program_Line_1563='set ACST = 27+ACSTtol',
            Program_Line_1564='endif',
            Program_Line_1565='endif',
            Program_Line_1566='else',
            Program_Line_1567='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1568='set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1569='elseif PMOT < ACSTall',
            Program_Line_1570='if CAT == 90',
            Program_Line_1571='set ACST = 24+ACSTtol',
            Program_Line_1572='elseif CAT == 80',
            Program_Line_1573='set ACST = 25+ACSTtol',
            Program_Line_1574='endif',
            Program_Line_1575='elseif PMOT > ACSTaul',
            Program_Line_1576='if CAT == 90',
            Program_Line_1577='set ACST = 26+ACSTtol',
            Program_Line_1578='elseif CAT == 80',
            Program_Line_1579='set ACST = 27+ACSTtol',
            Program_Line_1580='endif',
            Program_Line_1581='endif',
            Program_Line_1582='endif',
            Program_Line_1583='endif',
            Program_Line_1584='if (ComfStand == 17) && (ComfMod == 2)',
            Program_Line_1585='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1586='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1587='set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1588='elseif PMOT < AHSTall',
            Program_Line_1589='if CAT == 90',
            Program_Line_1590='set AHST = 20+AHSTtol',
            Program_Line_1591='elseif CAT == 80',
            Program_Line_1592='set AHST = 19+AHSTtol',
            Program_Line_1593='endif',
            Program_Line_1594='elseif PMOT > AHSTaul',
            Program_Line_1595='if CAT == 90',
            Program_Line_1596='set AHST = 23+AHSTtol',
            Program_Line_1597='elseif CAT == 80',
            Program_Line_1598='set AHST = 22+AHSTtol',
            Program_Line_1599='endif',
            Program_Line_1600='endif',
            Program_Line_1601='else',
            Program_Line_1602='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1603='set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1604='elseif PMOT < AHSTall',
            Program_Line_1605='if CAT == 90',
            Program_Line_1606='set AHST = 20+AHSTtol',
            Program_Line_1607='elseif CAT == 80',
            Program_Line_1608='set AHST = 19+AHSTtol',
            Program_Line_1609='endif',
            Program_Line_1610='elseif PMOT > AHSTaul',
            Program_Line_1611='if CAT == 90',
            Program_Line_1612='set AHST = 23+AHSTtol',
            Program_Line_1613='elseif CAT == 80',
            Program_Line_1614='set AHST = 22+AHSTtol',
            Program_Line_1615='endif',
            Program_Line_1616='endif',
            Program_Line_1617='endif',
            Program_Line_1618='endif',
            Program_Line_1619='if (ComfStand == 17) && (ComfMod == 3)',
            Program_Line_1620='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1621='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1622='set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1623='elseif PMOT < ACSTall',
            Program_Line_1624='set ACST = ACSTall*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1625='elseif PMOT > ACSTaul',
            Program_Line_1626='set ACST = ACSTaul*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1627='endif',
            Program_Line_1628='else',
            Program_Line_1629='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1630='set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1631='elseif PMOT < ACSTall',
            Program_Line_1632='set ACST = ACSTall*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1633='elseif PMOT > ACSTaul',
            Program_Line_1634='set ACST = ACSTaul*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1635='endif',
            Program_Line_1636='endif',
            Program_Line_1637='endif',
            Program_Line_1638='if (ComfStand == 17) && (ComfMod == 3)',
            Program_Line_1639='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1640='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1641='set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1642='elseif PMOT < AHSTall',
            Program_Line_1643='set AHST = AHSTall*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1644='elseif PMOT > AHSTaul',
            Program_Line_1645='set AHST = AHSTaul*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1646='endif',
            Program_Line_1647='else',
            Program_Line_1648='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1649='set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1650='elseif PMOT < AHSTall',
            Program_Line_1651='set AHST = AHSTall*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1652='elseif PMOT > AHSTaul',
            Program_Line_1653='set AHST = AHSTaul*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1654='endif',
            Program_Line_1655='endif',
            Program_Line_1656='endif',
            Program_Line_1657='if (ComfStand == 18) && (ComfMod == 1)',
            Program_Line_1658='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1659='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1660='set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1661='else',
            Program_Line_1662='set ACST = 25+ACSTtol',
            Program_Line_1663='endif',
            Program_Line_1664='else',
            Program_Line_1665='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1666='set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1667='else',
            Program_Line_1668='set ACST = 25+ACSTtol',
            Program_Line_1669='endif',
            Program_Line_1670='endif',
            Program_Line_1671='endif',
            Program_Line_1672='if (ComfStand == 18) && (ComfMod == 1)',
            Program_Line_1673='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1674='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1675='set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1676='else',
            Program_Line_1677='set AHST = 20+AHSTtol',
            Program_Line_1678='endif',
            Program_Line_1679='else',
            Program_Line_1680='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1681='set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1682='else',
            Program_Line_1683='set AHST = 20+AHSTtol',
            Program_Line_1684='endif',
            Program_Line_1685='endif',
            Program_Line_1686='endif',
            Program_Line_1687='if (ComfStand == 18) && (ComfMod == 2)',
            Program_Line_1688='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1689='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1690='set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1691='elseif PMOT < ACSTall',
            Program_Line_1692='if CAT == 90',
            Program_Line_1693='set ACST = 24+ACSTtol',
            Program_Line_1694='elseif CAT == 80',
            Program_Line_1695='set ACST = 25+ACSTtol',
            Program_Line_1696='endif',
            Program_Line_1697='elseif PMOT > ACSTaul',
            Program_Line_1698='if CAT == 90',
            Program_Line_1699='set ACST = 26+ACSTtol',
            Program_Line_1700='elseif CAT == 80',
            Program_Line_1701='set ACST = 27+ACSTtol',
            Program_Line_1702='endif',
            Program_Line_1703='endif',
            Program_Line_1704='else',
            Program_Line_1705='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1706='set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1707='elseif PMOT < ACSTall',
            Program_Line_1708='if CAT == 90',
            Program_Line_1709='set ACST = 24+ACSTtol',
            Program_Line_1710='elseif CAT == 80',
            Program_Line_1711='set ACST = 25+ACSTtol',
            Program_Line_1712='endif',
            Program_Line_1713='elseif PMOT > ACSTaul',
            Program_Line_1714='if CAT == 90',
            Program_Line_1715='set ACST = 26+ACSTtol',
            Program_Line_1716='elseif CAT == 80',
            Program_Line_1717='set ACST = 27+ACSTtol',
            Program_Line_1718='endif',
            Program_Line_1719='endif',
            Program_Line_1720='endif',
            Program_Line_1721='endif',
            Program_Line_1722='if (ComfStand == 18) && (ComfMod == 2)',
            Program_Line_1723='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1724='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1725='set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1726='elseif PMOT < AHSTall',
            Program_Line_1727='if CAT == 90',
            Program_Line_1728='set AHST = 20+AHSTtol',
            Program_Line_1729='elseif CAT == 80',
            Program_Line_1730='set AHST = 19+AHSTtol',
            Program_Line_1731='endif',
            Program_Line_1732='elseif PMOT > AHSTaul',
            Program_Line_1733='if CAT == 90',
            Program_Line_1734='set AHST = 23+AHSTtol',
            Program_Line_1735='elseif CAT == 80',
            Program_Line_1736='set AHST = 22+AHSTtol',
            Program_Line_1737='endif',
            Program_Line_1738='endif',
            Program_Line_1739='else',
            Program_Line_1740='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1741='set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1742='elseif PMOT < AHSTall',
            Program_Line_1743='if CAT == 90',
            Program_Line_1744='set AHST = 20+AHSTtol',
            Program_Line_1745='elseif CAT == 80',
            Program_Line_1746='set AHST = 19+AHSTtol',
            Program_Line_1747='endif',
            Program_Line_1748='elseif PMOT > AHSTaul',
            Program_Line_1749='if CAT == 90',
            Program_Line_1750='set AHST = 23+AHSTtol',
            Program_Line_1751='elseif CAT == 80',
            Program_Line_1752='set AHST = 22+AHSTtol',
            Program_Line_1753='endif',
            Program_Line_1754='endif',
            Program_Line_1755='endif',
            Program_Line_1756='endif',
            Program_Line_1757='if (ComfStand == 18) && (ComfMod == 3)',
            Program_Line_1758='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1759='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1760='set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1761='elseif PMOT < ACSTall',
            Program_Line_1762='set ACST = ACSTall*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1763='elseif PMOT > ACSTaul',
            Program_Line_1764='set ACST = ACSTaul*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1765='endif',
            Program_Line_1766='else',
            Program_Line_1767='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1768='set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1769='elseif PMOT < ACSTall',
            Program_Line_1770='set ACST = ACSTall*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1771='elseif PMOT > ACSTaul',
            Program_Line_1772='set ACST = ACSTaul*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1773='endif',
            Program_Line_1774='endif',
            Program_Line_1775='endif',
            Program_Line_1776='if (ComfStand == 18) && (ComfMod == 3)',
            Program_Line_1777='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1778='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1779='set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1780='elseif PMOT < AHSTall',
            Program_Line_1781='set AHST = AHSTall*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1782='elseif PMOT > AHSTaul',
            Program_Line_1783='set AHST = AHSTaul*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1784='endif',
            Program_Line_1785='else',
            Program_Line_1786='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1787='set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1788='elseif PMOT < AHSTall',
            Program_Line_1789='set AHST = AHSTall*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1790='elseif PMOT > AHSTaul',
            Program_Line_1791='set AHST = AHSTaul*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1792='endif',
            Program_Line_1793='endif',
            Program_Line_1794='endif',
            Program_Line_1795='if (ComfStand == 19) && (ComfMod == 1)',
            Program_Line_1796='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1797='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1798='set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1799='else',
            Program_Line_1800='set ACST = 25+ACSTtol',
            Program_Line_1801='endif',
            Program_Line_1802='else',
            Program_Line_1803='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1804='set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1805='else',
            Program_Line_1806='set ACST = 25+ACSTtol',
            Program_Line_1807='endif',
            Program_Line_1808='endif',
            Program_Line_1809='endif',
            Program_Line_1810='if (ComfStand == 19) && (ComfMod == 1)',
            Program_Line_1811='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1812='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1813='set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1814='else',
            Program_Line_1815='set AHST = 20+AHSTtol',
            Program_Line_1816='endif',
            Program_Line_1817='else',
            Program_Line_1818='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1819='set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1820='else',
            Program_Line_1821='set AHST = 20+AHSTtol',
            Program_Line_1822='endif',
            Program_Line_1823='endif',
            Program_Line_1824='endif',
            Program_Line_1825='if (ComfStand == 19) && (ComfMod == 2)',
            Program_Line_1826='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1827='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1828='set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1829='elseif PMOT < ACSTall',
            Program_Line_1830='if CAT == 90',
            Program_Line_1831='set ACST = 24+ACSTtol',
            Program_Line_1832='elseif CAT == 80',
            Program_Line_1833='set ACST = 25+ACSTtol',
            Program_Line_1834='endif',
            Program_Line_1835='elseif PMOT > ACSTaul',
            Program_Line_1836='if CAT == 90',
            Program_Line_1837='set ACST = 26+ACSTtol',
            Program_Line_1838='elseif CAT == 80',
            Program_Line_1839='set ACST = 27+ACSTtol',
            Program_Line_1840='endif',
            Program_Line_1841='endif',
            Program_Line_1842='else',
            Program_Line_1843='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1844='set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1845='elseif PMOT < ACSTall',
            Program_Line_1846='if CAT == 90',
            Program_Line_1847='set ACST = 24+ACSTtol',
            Program_Line_1848='elseif CAT == 80',
            Program_Line_1849='set ACST = 25+ACSTtol',
            Program_Line_1850='endif',
            Program_Line_1851='elseif PMOT > ACSTaul',
            Program_Line_1852='if CAT == 90',
            Program_Line_1853='set ACST = 26+ACSTtol',
            Program_Line_1854='elseif CAT == 80',
            Program_Line_1855='set ACST = 27+ACSTtol',
            Program_Line_1856='endif',
            Program_Line_1857='endif',
            Program_Line_1858='endif',
            Program_Line_1859='endif',
            Program_Line_1860='if (ComfStand == 19) && (ComfMod == 2)',
            Program_Line_1861='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1862='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1863='set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1864='elseif PMOT < AHSTall',
            Program_Line_1865='if CAT == 90',
            Program_Line_1866='set AHST = 20+AHSTtol',
            Program_Line_1867='elseif CAT == 80',
            Program_Line_1868='set AHST = 19+AHSTtol',
            Program_Line_1869='endif',
            Program_Line_1870='elseif PMOT > AHSTaul',
            Program_Line_1871='if CAT == 90',
            Program_Line_1872='set AHST = 23+AHSTtol',
            Program_Line_1873='elseif CAT == 80',
            Program_Line_1874='set AHST = 22+AHSTtol',
            Program_Line_1875='endif',
            Program_Line_1876='endif',
            Program_Line_1877='else',
            Program_Line_1878='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1879='set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1880='elseif PMOT < AHSTall',
            Program_Line_1881='if CAT == 90',
            Program_Line_1882='set AHST = 20+AHSTtol',
            Program_Line_1883='elseif CAT == 80',
            Program_Line_1884='set AHST = 19+AHSTtol',
            Program_Line_1885='endif',
            Program_Line_1886='elseif PMOT > AHSTaul',
            Program_Line_1887='if CAT == 90',
            Program_Line_1888='set AHST = 23+AHSTtol',
            Program_Line_1889='elseif CAT == 80',
            Program_Line_1890='set AHST = 22+AHSTtol',
            Program_Line_1891='endif',
            Program_Line_1892='endif',
            Program_Line_1893='endif',
            Program_Line_1894='endif',
            Program_Line_1895='if (ComfStand == 19) && (ComfMod == 3)',
            Program_Line_1896='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1897='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1898='set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1899='elseif PMOT < ACSTall',
            Program_Line_1900='set ACST = ACSTall*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1901='elseif PMOT > ACSTaul',
            Program_Line_1902='set ACST = ACSTaul*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1903='endif',
            Program_Line_1904='else',
            Program_Line_1905='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1906='set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1907='elseif PMOT < ACSTall',
            Program_Line_1908='set ACST = ACSTall*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1909='elseif PMOT > ACSTaul',
            Program_Line_1910='set ACST = ACSTaul*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1911='endif',
            Program_Line_1912='endif',
            Program_Line_1913='endif',
            Program_Line_1914='if (ComfStand == 19) && (ComfMod == 3)',
            Program_Line_1915='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1916='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1917='set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1918='elseif PMOT < AHSTall',
            Program_Line_1919='set AHST = AHSTall*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1920='elseif PMOT > AHSTaul',
            Program_Line_1921='set AHST = AHSTaul*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1922='endif',
            Program_Line_1923='else',
            Program_Line_1924='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1925='set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1926='elseif PMOT < AHSTall',
            Program_Line_1927='set AHST = AHSTall*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1928='elseif PMOT > AHSTaul',
            Program_Line_1929='set AHST = AHSTaul*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1930='endif',
            Program_Line_1931='endif',
            Program_Line_1932='endif',
            Program_Line_1933='if (ComfStand == 20) && (ComfMod == 1)',
            Program_Line_1934='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1935='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1936='set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_1937='else',
            Program_Line_1938='set ACST = 25+ACSTtol',
            Program_Line_1939='endif',
            Program_Line_1940='else',
            Program_Line_1941='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1942='set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_1943='else',
            Program_Line_1944='set ACST = 25+ACSTtol',
            Program_Line_1945='endif',
            Program_Line_1946='endif',
            Program_Line_1947='endif',
            Program_Line_1948='if (ComfStand == 20) && (ComfMod == 1)',
            Program_Line_1949='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1950='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1951='set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_1952='else',
            Program_Line_1953='set AHST = 20+AHSTtol',
            Program_Line_1954='endif',
            Program_Line_1955='else',
            Program_Line_1956='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1957='set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_1958='else',
            Program_Line_1959='set AHST = 20+AHSTtol',
            Program_Line_1960='endif',
            Program_Line_1961='endif',
            Program_Line_1962='endif',
            Program_Line_1963='if (ComfStand == 20) && (ComfMod == 2)',
            Program_Line_1964='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1965='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1966='set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_1967='elseif PMOT < ACSTall',
            Program_Line_1968='if CAT == 90',
            Program_Line_1969='set ACST = 24+ACSTtol',
            Program_Line_1970='elseif CAT == 80',
            Program_Line_1971='set ACST = 25+ACSTtol',
            Program_Line_1972='endif',
            Program_Line_1973='elseif PMOT > ACSTaul',
            Program_Line_1974='if CAT == 90',
            Program_Line_1975='set ACST = 26+ACSTtol',
            Program_Line_1976='elseif CAT == 80',
            Program_Line_1977='set ACST = 27+ACSTtol',
            Program_Line_1978='endif',
            Program_Line_1979='endif',
            Program_Line_1980='else',
            Program_Line_1981='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1982='set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_1983='elseif PMOT < ACSTall',
            Program_Line_1984='if CAT == 90',
            Program_Line_1985='set ACST = 24+ACSTtol',
            Program_Line_1986='elseif CAT == 80',
            Program_Line_1987='set ACST = 25+ACSTtol',
            Program_Line_1988='endif',
            Program_Line_1989='elseif PMOT > ACSTaul',
            Program_Line_1990='if CAT == 90',
            Program_Line_1991='set ACST = 26+ACSTtol',
            Program_Line_1992='elseif CAT == 80',
            Program_Line_1993='set ACST = 27+ACSTtol',
            Program_Line_1994='endif',
            Program_Line_1995='endif',
            Program_Line_1996='endif',
            Program_Line_1997='endif',
            Program_Line_1998='if (ComfStand == 20) && (ComfMod == 2)',
            Program_Line_1999='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_2000='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2001='set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2002='elseif PMOT < AHSTall',
            Program_Line_2003='if CAT == 90',
            Program_Line_2004='set AHST = 20+AHSTtol',
            Program_Line_2005='elseif CAT == 80',
            Program_Line_2006='set AHST = 19+AHSTtol',
            Program_Line_2007='endif',
            Program_Line_2008='elseif PMOT > AHSTaul',
            Program_Line_2009='if CAT == 90',
            Program_Line_2010='set AHST = 23+AHSTtol',
            Program_Line_2011='elseif CAT == 80',
            Program_Line_2012='set AHST = 22+AHSTtol',
            Program_Line_2013='endif',
            Program_Line_2014='endif',
            Program_Line_2015='else',
            Program_Line_2016='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2017='set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2018='elseif PMOT < AHSTall',
            Program_Line_2019='if CAT == 90',
            Program_Line_2020='set AHST = 20+AHSTtol',
            Program_Line_2021='elseif CAT == 80',
            Program_Line_2022='set AHST = 19+AHSTtol',
            Program_Line_2023='endif',
            Program_Line_2024='elseif PMOT > AHSTaul',
            Program_Line_2025='if CAT == 90',
            Program_Line_2026='set AHST = 23+AHSTtol',
            Program_Line_2027='elseif CAT == 80',
            Program_Line_2028='set AHST = 22+AHSTtol',
            Program_Line_2029='endif',
            Program_Line_2030='endif',
            Program_Line_2031='endif',
            Program_Line_2032='endif',
            Program_Line_2033='if (ComfStand == 20) && (ComfMod == 3)',
            Program_Line_2034='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_2035='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2036='set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_2037='elseif PMOT < ACSTall',
            Program_Line_2038='set ACST = ACSTall*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_2039='elseif PMOT > ACSTaul',
            Program_Line_2040='set ACST = ACSTaul*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_2041='endif',
            Program_Line_2042='else',
            Program_Line_2043='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2044='set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2045='elseif PMOT < ACSTall',
            Program_Line_2046='set ACST = ACSTall*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2047='elseif PMOT > ACSTaul',
            Program_Line_2048='set ACST = ACSTaul*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2049='endif',
            Program_Line_2050='endif',
            Program_Line_2051='endif',
            Program_Line_2052='if (ComfStand == 20) && (ComfMod == 3)',
            Program_Line_2053='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_2054='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2055='set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2056='elseif PMOT < AHSTall',
            Program_Line_2057='set AHST = AHSTall*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2058='elseif PMOT > AHSTaul',
            Program_Line_2059='set AHST = AHSTaul*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2060='endif',
            Program_Line_2061='else',
            Program_Line_2062='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2063='set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2064='elseif PMOT < AHSTall',
            Program_Line_2065='set AHST = AHSTall*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2066='elseif PMOT > AHSTaul',
            Program_Line_2067='set AHST = AHSTaul*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2068='endif',
            Program_Line_2069='endif',
            Program_Line_2070='endif',
            Program_Line_2071='if (ComfStand == 21) && (ComfMod == 2)',
            Program_Line_2072='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2073='set ACST = PMOT*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2074='elseif CAT==80',
            Program_Line_2075='if PMOT < ACSTall',
            Program_Line_2076='set ACST = 25+ACSTtol',
            Program_Line_2077='elseif PMOT > ACSTaul',
            Program_Line_2078='set ACST = 27+ACSTtol',
            Program_Line_2079='endif',
            Program_Line_2080='elseif CAT==90',
            Program_Line_2081='if PMOT < ACSTall',
            Program_Line_2082='set ACST = 24+ACSTtol',
            Program_Line_2083='elseif PMOT > ACSTaul',
            Program_Line_2084='set ACST = 26+ACSTtol',
            Program_Line_2085='endif',
            Program_Line_2086='endif',
            Program_Line_2087='endif',
            Program_Line_2088='if (ComfStand == 21) && (ComfMod == 2)',
            Program_Line_2089='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2090='set AHST = PMOT*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2091='elseif CAT==80',
            Program_Line_2092='if PMOT < AHSTall',
            Program_Line_2093='set AHST = 19+AHSTtol',
            Program_Line_2094='elseif PMOT > AHSTaul',
            Program_Line_2095='set AHST = 22+AHSTtol',
            Program_Line_2096='endif',
            Program_Line_2097='elseif CAT==90',
            Program_Line_2098='if PMOT < AHSTall',
            Program_Line_2099='set AHST = 20+AHSTtol',
            Program_Line_2100='elseif PMOT > AHSTaul',
            Program_Line_2101='set AHST = 23+AHSTtol',
            Program_Line_2102='endif',
            Program_Line_2103='endif',
            Program_Line_2104='endif',
            Program_Line_2105='if (ComfStand == 21) && (ComfMod == 3)',
            Program_Line_2106='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2107='set ACST = PMOT*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2108='elseif PMOT < ACSTall',
            Program_Line_2109='set ACST = ACSTall*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2110='elseif PMOT > ACSTaul',
            Program_Line_2111='set ACST = ACSTaul*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2112='endif',
            Program_Line_2113='endif',
            Program_Line_2114='if (ComfStand == 21) && (ComfMod == 3)',
            Program_Line_2115='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2116='set AHST = PMOT*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2117='elseif PMOT < AHSTall',
            Program_Line_2118='set AHST = AHSTall*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2119='elseif PMOT > AHSTaul',
            Program_Line_2120='set AHST = AHSTaul*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2121='endif',
            Program_Line_2122='endif',
            Program_Line_2123='if (ComfStand == 22)',
            Program_Line_2124='if CoolingSeason == 1',
            Program_Line_2125='if (CAT==3)',
            Program_Line_2126='set ACST = 24.5+2.5+ACSTtol',
            Program_Line_2127='elseif (CAT==2)',
            Program_Line_2128='set ACST = 24.5+1.5+ACSTtol',
            Program_Line_2129='elseif (CAT==1)',
            Program_Line_2130='set ACST = 24.5+1+ACSTtol',
            Program_Line_2131='endif',
            Program_Line_2132='else',
            Program_Line_2133='if (CAT==3)',
            Program_Line_2134='set ACST = 22+3+ACSTtol',
            Program_Line_2135='elseif (CAT==2)',
            Program_Line_2136='set ACST = 22+2+ACSTtol',
            Program_Line_2137='elseif (CAT==1)',
            Program_Line_2138='set ACST = 22+1+ACSTtol',
            Program_Line_2139='endif',
            Program_Line_2140='endif',
            Program_Line_2141='endif',
            Program_Line_2142='if (ComfStand == 22)',
            Program_Line_2143='if CoolingSeason == 1',
            Program_Line_2144='if (CAT==3)',
            Program_Line_2145='set AHST = 24.5-2.5+AHSTtol',
            Program_Line_2146='elseif (CAT==2)',
            Program_Line_2147='set AHST = 24.5-1.5+AHSTtol',
            Program_Line_2148='elseif (CAT==1)',
            Program_Line_2149='set AHST = 24.5-1+AHSTtol',
            Program_Line_2150='endif',
            Program_Line_2151='else',
            Program_Line_2152='if (CAT==3)',
            Program_Line_2153='set AHST = 22-3+AHSTtol',
            Program_Line_2154='elseif (CAT==2)',
            Program_Line_2155='set AHST = 22-2+AHSTtol',
            Program_Line_2156='elseif (CAT==1)',
            Program_Line_2157='set AHST = 22-1+AHSTtol',
            Program_Line_2158='endif',
            Program_Line_2159='endif',
            Program_Line_2160='endif',
            Program_Line_2161='set ACSTx2 = ACST*SetpointAcc',
            Program_Line_2162='set AHSTx2 = AHST*SetpointAcc',
            Program_Line_2163='set roundedACSTx2 = @Round ACSTx2',
            Program_Line_2164='set roundedAHSTx2 = @Round AHSTx2',
            Program_Line_2165='if roundedACSTx2 - ACSTx2 < 0',
            Program_Line_2166='set ACSTroundedUp = 0',
            Program_Line_2167='else',
            Program_Line_2168='set ACSTroundedUp = 1',
            Program_Line_2169='endif',
            Program_Line_2170='if roundedAHSTx2 - AHSTx2 < 0',
            Program_Line_2171='set AHSTroundedUp = 0',
            Program_Line_2172='else',
            Program_Line_2173='set AHSTroundedUp = 1',
            Program_Line_2174='endif',
            Program_Line_2175='if ACSTroundedUp == 0',
            Program_Line_2176='set roundedACST = roundedACSTx2 / SetpointAcc',
            Program_Line_2177='else',
            Program_Line_2178='set roundedACST = (roundedACSTx2 - 1) / SetpointAcc',
            Program_Line_2179='endif',
            Program_Line_2180='if AHSTroundedUp == 0',
            Program_Line_2181='set roundedAHST = (roundedAHSTx2 + 1) / SetpointAcc',
            Program_Line_2182='else',
            Program_Line_2183='set roundedAHST = roundedAHSTx2 / SetpointAcc',
            Program_Line_2184='endif',
        )
        if verboseMode:
            print('Added - SetAST Program')
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetAST'])

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

    for zonename in self.occupiedZones:
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
                Program_Line_15='if Occ_count_' + zonename + ' > 0',
                Program_Line_16='set OccHours_' + zonename + ' = 1*ZoneTimeStep',
                Program_Line_17='else',
                Program_Line_18='set OccHours_' + zonename + ' = 0',
                Program_Line_19='endif',
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
                Program_Line_1='set MaxTempDiffVOF = 7.5',
                Program_Line_2='set MinTempDiffVOF = 0',
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

        for zonename in self.zonenames:
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
        for zonename in self.zonenames:
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

    for i in programlist:
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

    del programlist, pcmlist

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

    EMSOutputVariableZone_dict = {
        'Comfortable Hours_No Applicability': ['ComfHoursNoApp', 'H', 'Summed'],
        'Comfortable Hours_Applicability': ['ComfHours', 'H', 'Summed'],
        'Occupied Comfortable Hours_No Applicability': ['OccComfHoursNoApp', 'H', 'Summed'],
        'Occupied Hours': ['OccHours', 'H', 'Summed'],
        'Discomfortable Applicable Hot Hours': ['DiscomfAppHotHours', 'H', 'Summed'],
        'Discomfortable Applicable Cold Hours': ['DiscomfAppColdHours', 'H', 'Summed'],
        'Discomfortable Non Applicable Hot Hours': ['DiscomfNonAppHotHours', 'H', 'Summed'],
        'Discomfortable Non Applicable Cold Hours': ['DiscomfNonAppColdHours', 'H', 'Summed'],
        'Zone Floor Area': ['ZoneFloorArea', 'm2', 'Averaged'],
        'Zone Air Volume': ['ZoneAirVolume', 'm3', 'Averaged'],
        'People Occupant Count': ['Occ_count', '', 'Summed'],
    }

    for i in EMSOutputVariableZone_dict:
        for zonename in self.occupiedZones:
            if i+'_'+zonename in outputvariablelist:
                if verboseMode:
                    print('Not added - '+i+'_'
                          + zonename + ' Output Variable')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:OutputVariable',
                    Name=i + '_' + zonename,
                    EMS_Variable_Name=EMSOutputVariableZone_dict[i][0]+'_'
                    + zonename,
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
            for zonename in self.zonenames:
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
    )
    for zonename in self.occupiedZones:
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
        for zonename in self.zonenames:
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

    for i in range(len(self.zonenames)):
        for j in intvardict:
            self.idf1.newidfobject(
                'EnergyManagementSystem:InternalVariable',
                Name=j+self.zonenames[i],
                Internal_Data_Index_Key_Name=self.zonenames_orig[i],
                Internal_Data_Type=intvardict[j]
            )
    if verboseMode:
        print("Internal variables objects have been added")

def removeExistingOutputVariables(
        self,
):
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

def removeDuplicatedOutputVariables(
        self,
):
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
):
    """
    Used to read a pandas DataFrame containing the Output:Variable objects to be kept.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param idf_filename: Inherited from :class:``accim.sim.accis.addAccis``
    :param df_outputs_in: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    import pandas as pd
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

    for i in range(len(df_outputs_in)):
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
        verboseMode: bool = True):
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
        # 'Zone Thermostat Operative Temperature',
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

        for zonename in self.zonenames:
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

    del EMSoutputvariablenamelist, outputnamelist, addittionaloutputs,


def addOutputVariablesDetailed(
        self,
        Outputs_freq: any = None,
        verboseMode: bool = True):
    """Add Output:Variable objects for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param Outputs_freq: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """

    addittionaloutputs = [
        'AFN Surface Venting Window or Door Opening Factor',
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

def addEMSSensorsBase(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS sensors for accim.

    :param self: Used as a method for :class:``accim.sim.accim_Main.accimJob``
    :param ScriptType: Inherited from :class:``accim.sim.accis.addAccis``
    :param verboseMode: Inherited from :class:``accim.sim.accis.addAccis``
    """
    sensorlist = ([sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']])

    if len([i.Name for i in self.idf1.idfobjects['zonelist']]) > 0:
        ppl_key_name = self.occupiedZones_orig[0] + ' People'
    else:
        ppl_key_name = [i for i in self.idf1.idfobjects['PEOPLE']][0].Name

    # spacelist = [i for i in self.idf1.idfobjects['spacelist']]

    if 'RMOT' in sensorlist:
        if verboseMode:
            print('Not added - RMOT Sensor')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Sensor',
            Name='RMOT',
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

    for i in range(len(self.zonenames)):
        if self.zonenames[i]+'_OpT' in sensorlist:
            if verboseMode:
                print('Not added - '+self.zonenames[i]+'_OpT Sensor')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=self.zonenames[i]+'_OpT',
                OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i],
                OutputVariable_or_OutputMeter_Name='Zone Operative Temperature'
                )
            if verboseMode:
                print('Added - '+self.zonenames[i]+'_OpT Sensor')
    #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_OpT'])
        
        if f'Occ_count_{self.zonenames[i]}' in sensorlist:
            if verboseMode:
                print(f'Not added - Occ_count_{self.zonenames[i]} Sensor')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Sensor',
                Name=f'Occ_count_{self.zonenames[i]}',
                OutputVariable_or_OutputMeter_Index_Key_Name='People '+self.zonenames_orig[i],
                OutputVariable_or_OutputMeter_Name='People Occupant Count'
            )
            if verboseMode:
                print(f'Added - Occ_count_{self.zonenames[i]} Sensor')

        
        if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
            if self.zonenames[i]+'_WindSpeed' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.zonenames[i]+'_WindSpeed Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.zonenames[i]+'_WindSpeed',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i],
                    OutputVariable_or_OutputMeter_Name='Zone Outdoor Air Wind Speed'
                    )
                if verboseMode:
                    print('Added - '+self.zonenames[i]+'_WindSpeed Sensor')
        #        print([sensor for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if sensor.Name==self.zonenames[i]+'_WindSpeed'])
            if self.zonenames[i]+'_OutT' in sensorlist:
                if verboseMode:
                    print('Not added - '+self.zonenames[i]+'_OutT Sensor')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.zonenames[i]+'_OutT',
                    OutputVariable_or_OutputMeter_Index_Key_Name=self.zonenames_orig[i],
                    OutputVariable_or_OutputMeter_Name='Zone Outdoor Air Drybulb Temperature'
                    )
                if verboseMode:
                    print('Added - '+self.zonenames[i]+'_OutT Sensor')
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
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Sensor',
                    Name=self.windownamelist[i]+'_Occ_count',
                    OutputVariable_or_OutputMeter_Index_Key_Name='People '+self.windownamelist_orig_split[i][0],
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

    for zonename in self.zonenames:
        if 'AHST_Act_'+zonename in actuatorlist:
            if verboseMode:
                print('Not added - AHST_Act_'+zonename+' Actuator')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Actuator',
                Name='AHST_Act_'+zonename,
                Actuated_Component_Unique_Name='AHST_Sch_'+zonename,
                Actuated_Component_Type='Schedule:Compact',
                Actuated_Component_Control_Type='Schedule Value'
                )
            if verboseMode:
                print('Added - AHST_Act_'+zonename+' Actuator')
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='AHST_Act_'+zonename])

        if 'ACST_Act_'+zonename in actuatorlist:
            if verboseMode:
                print('Not added - ACST_Act_'+zonename+' Actuator')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Actuator',
                Name='ACST_Act_'+zonename,
                Actuated_Component_Unique_Name='ACST_Sch_'+zonename,
                Actuated_Component_Type='Schedule:Compact',
                Actuated_Component_Control_Type='Schedule Value'
                )
            if verboseMode:
                print('Added - ACST_Act_'+zonename+' Actuator')
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='ACST_Act_'+zonename])

    if ScriptType.lower() == 'vrf_mm' or ScriptType.lower() == 'ex_mm':
        for i in range(len(self.windownamelist)):
            if self.windownamelist[i]+'_VentOpenFact' in actuatorlist:
                if verboseMode:
                    print('Not added - '+self.windownamelist[i]+'_OpT Actuator')
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


