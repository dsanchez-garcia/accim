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

    if 'SetAST' in programlist:
        if verboseMode:
            print('Not added - SetAST Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name='SetAST',
            #todo for some reason, SetpointAcc variable is not defined if set out of this program; ideally, it should be located in SetInputData program
            Program_Line_1='set SetpointAcc = 10000',
            Program_Line_2='set m = 0.31',
            Program_Line_3='set n = 17.8',
            Program_Line_4='if CoolSeasonEnd > CoolSeasonStart',
            Program_Line_5='if (DayOfYear >= CoolSeasonStart) && (DayOfYear < CoolSeasonEnd)',
            Program_Line_6='set CoolingSeason = 1',
            Program_Line_7='else',
            Program_Line_8='set CoolingSeason = 0',
            Program_Line_9='endif',
            Program_Line_10='elseif CoolSeasonStart > CoolSeasonEnd',
            Program_Line_11='if (DayOfYear >= CoolSeasonStart) || (DayOfYear < CoolSeasonEnd)',
            Program_Line_12='set CoolingSeason = 1',
            Program_Line_13='else',
            Program_Line_14='set CoolingSeason = 0',
            Program_Line_15='endif',
            Program_Line_16='endif',
            Program_Line_17='if (ComfStand == 99) && (ComfMod == 3)',
            Program_Line_18='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_19='set ACST = PMOT*m+n+ACSToffset+ACSTtol',
            Program_Line_20='elseif PMOT < ACSTall',
            Program_Line_21='set ACST = ACSTall*m+n+ACSToffset+ACSTtol',
            Program_Line_22='elseif PMOT > ACSTaul',
            Program_Line_23='set ACST = ACSTaul*m+n+ACSToffset+ACSTtol',
            Program_Line_24='endif',
            Program_Line_25='endif',
            Program_Line_26='if (ComfStand == 99) && (ComfMod == 3)',
            Program_Line_27='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_28='set AHST = PMOT*m+n+AHSToffset+AHSTtol',
            Program_Line_29='elseif PMOT < AHSTall',
            Program_Line_30='set AHST = AHSTall*m+n+AHSToffset+AHSTtol',
            Program_Line_31='elseif PMOT > AHSTaul',
            Program_Line_32='set AHST = AHSTaul*m+n+AHSToffset+AHSTtol',
            Program_Line_33='endif',
            Program_Line_34='endif',
            Program_Line_35='if (ComfStand == 0) && (CurrentTime < 8)',
            Program_Line_36='set ACST = 27+ACSTtol',
            Program_Line_37='set AHST = 17+AHSTtol',
            Program_Line_38='elseif (ComfStand == 0) && (CurrentTime < 16)',
            Program_Line_39='set ACST = 25+ACSTtol',
            Program_Line_40='set AHST = 20+AHSTtol',
            Program_Line_41='elseif (ComfStand == 0) && (CurrentTime < 23)',
            Program_Line_42='set ACST = 25+ACSTtol',
            Program_Line_43='set AHST = 20+AHSTtol',
            Program_Line_44='elseif (ComfStand == 0) && (CurrentTime < 24)',
            Program_Line_45='set ACST = 27+ACSTtol',
            Program_Line_46='set AHST = 17+AHSTtol',
            Program_Line_47='endif',
            Program_Line_48='if (ComfStand == 1) && (ComfMod == 0)',
            Program_Line_49='if CoolingSeason == 1',
            Program_Line_50='if (CAT==1)',
            Program_Line_51='set ACST = 25.5+ACSTtol',
            Program_Line_52='elseif (CAT==2)',
            Program_Line_53='set ACST = 26+ACSTtol',
            Program_Line_54='elseif (CAT==3)',
            Program_Line_55='set ACST = 27+ACSTtol',
            Program_Line_56='endif',
            Program_Line_57='else',
            Program_Line_58='if (CAT==1)',
            Program_Line_59='set ACST = 25+ACSTtol',
            Program_Line_60='elseif (CAT==2)',
            Program_Line_61='set ACST = 25+ACSTtol',
            Program_Line_62='elseif (CAT==3)',
            Program_Line_63='set ACST = 25+ACSTtol',
            Program_Line_64='endif',
            Program_Line_65='endif',
            Program_Line_66='endif',
            Program_Line_67='if (ComfStand == 1) && (ComfMod == 0)',
            Program_Line_68='if CoolingSeason == 1',
            Program_Line_69='if (CAT==1)',
            Program_Line_70='set AHST = 23.5+AHSTtol',
            Program_Line_71='elseif (CAT==2)',
            Program_Line_72='set AHST = 23+AHSTtol',
            Program_Line_73='elseif (CAT==3)',
            Program_Line_74='set AHST = 22+AHSTtol',
            Program_Line_75='endif',
            Program_Line_76='else',
            Program_Line_77='if (CAT==1)',
            Program_Line_78='set AHST = 21+AHSTtol',
            Program_Line_79='elseif (CAT==2)',
            Program_Line_80='set AHST = 20+AHSTtol',
            Program_Line_81='elseif (CAT==3)',
            Program_Line_82='set AHST = 18+AHSTtol',
            Program_Line_83='endif',
            Program_Line_84='endif',
            Program_Line_85='endif',
            Program_Line_86='if (ComfStand == 1) && (ComfMod == 1)',
            Program_Line_87='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_88='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_89='elseif CurrentTime < 7',
            Program_Line_90='set ACST = 27+ACSTtol',
            Program_Line_91='elseif CurrentTime < 15',
            Program_Line_92='set ACST = 50',
            Program_Line_93='elseif CurrentTime < 23',
            Program_Line_94='set ACST = 25+ACSTtol',
            Program_Line_95='elseif CurrentTime < 24',
            Program_Line_96='set ACST = 27+ACSTtol',
            Program_Line_97='endif',
            Program_Line_98='endif',
            Program_Line_99='if (ComfStand == 1) && (ComfMod == 1)',
            Program_Line_100='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_101='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_102='elseif CurrentTime < 7',
            Program_Line_103='set AHST = 17+AHSTtol',
            Program_Line_104='elseif CurrentTime < 23',
            Program_Line_105='set AHST = 20+AHSTtol',
            Program_Line_106='elseif CurrentTime < 24',
            Program_Line_107='set AHST = 17+AHSTtol',
            Program_Line_108='endif',
            Program_Line_109='endif',
            Program_Line_110='if (ComfStand == 1) && (ComfMod == 2)',
            Program_Line_111='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_112='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_113='elseif (RMOT < ACSTall) && (CAT==1)',
            Program_Line_114='set ACST = 25+ACSTtol',
            Program_Line_115='elseif (RMOT > ACSTaul) && (CAT==1)',
            Program_Line_116='set ACST = 25.5+ACSTtol',
            Program_Line_117='elseif (RMOT < ACSTall) && (CAT==2)',
            Program_Line_118='set ACST = 25+ACSTtol',
            Program_Line_119='elseif (RMOT > ACSTaul) && (CAT==2)',
            Program_Line_120='set ACST = 26+ACSTtol',
            Program_Line_121='elseif (RMOT < ACSTall) && (CAT==3)',
            Program_Line_122='set ACST = 25+ACSTtol',
            Program_Line_123='elseif (RMOT > ACSTaul) && (CAT==3)',
            Program_Line_124='set ACST = 27+ACSTtol',
            Program_Line_125='endif',
            Program_Line_126='endif',
            Program_Line_127='if (ComfStand == 1) && (ComfMod == 2)',
            Program_Line_128='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_129='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_130='elseif (RMOT < AHSTall) && (CAT==1)',
            Program_Line_131='set AHST = 21+AHSTtol',
            Program_Line_132='elseif (RMOT > AHSTaul) && (CAT==1)',
            Program_Line_133='set AHST = 23.5+AHSTtol',
            Program_Line_134='elseif (RMOT < AHSTall) && (CAT==2)',
            Program_Line_135='set AHST = 20+AHSTtol',
            Program_Line_136='elseif (RMOT > AHSTaul) && (CAT==2)',
            Program_Line_137='set AHST = 23+AHSTtol',
            Program_Line_138='elseif (RMOT < AHSTall) && (CAT==3)',
            Program_Line_139='set AHST = 18+AHSTtol',
            Program_Line_140='elseif (RMOT > AHSTaul) && (CAT==3)',
            Program_Line_141='set AHST = 22+AHSTtol',
            Program_Line_142='endif',
            Program_Line_143='endif',
            Program_Line_144='if (ComfStand == 1) && (ComfMod == 3)',
            Program_Line_145='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_146='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_147='elseif RMOT < ACSTall',
            Program_Line_148='set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_149='elseif RMOT > ACSTaul',
            Program_Line_150='set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_151='endif',
            Program_Line_152='endif',
            Program_Line_153='if (ComfStand == 1) && (ComfMod == 3)',
            Program_Line_154='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_155='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_156='elseif RMOT < AHSTall',
            Program_Line_157='set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_158='elseif RMOT > AHSTaul',
            Program_Line_159='set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_160='endif',
            Program_Line_161='endif',
            Program_Line_162='if (ComfStand == 2) && (ComfMod == 0)',
            Program_Line_163='if CoolingSeason == 1',
            Program_Line_164='if (CAT==80)',
            Program_Line_165='set ACST = 27+ACSTtol',
            Program_Line_166='elseif (CAT==90)',
            Program_Line_167='set ACST = 26+ACSTtol',
            Program_Line_168='endif',
            Program_Line_169='else',
            Program_Line_170='if (CAT==80)',
            Program_Line_171='set ACST = 25+ACSTtol',
            Program_Line_172='elseif (CAT==90)',
            Program_Line_173='set ACST = 24+ACSTtol',
            Program_Line_174='endif',
            Program_Line_175='endif',
            Program_Line_176='endif',
            Program_Line_177='if (ComfStand == 2) && (ComfMod == 0)',
            Program_Line_178='if CoolingSeason == 1',
            Program_Line_179='if (CAT==80)',
            Program_Line_180='set AHST = 22+AHSTtol',
            Program_Line_181='elseif (CAT==90)',
            Program_Line_182='set AHST = 23+AHSTtol',
            Program_Line_183='endif',
            Program_Line_184='else',
            Program_Line_185='if (CAT==80)',
            Program_Line_186='set AHST = 19+AHSTtol',
            Program_Line_187='elseif (CAT==90)',
            Program_Line_188='set AHST = 20+AHSTtol',
            Program_Line_189='endif',
            Program_Line_190='endif',
            Program_Line_191='endif',
            Program_Line_192='if (ComfStand == 2) && (ComfMod == 1)',
            Program_Line_193='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_194='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_195='elseif CurrentTime < 7',
            Program_Line_196='set ACST = 27+ACSTtol',
            Program_Line_197='elseif CurrentTime < 15',
            Program_Line_198='set ACST = 50',
            Program_Line_199='elseif CurrentTime < 23',
            Program_Line_200='set ACST = 25+ACSTtol',
            Program_Line_201='elseif CurrentTime < 24',
            Program_Line_202='set ACST = 27+ACSTtol',
            Program_Line_203='endif',
            Program_Line_204='endif',
            Program_Line_205='if (ComfStand == 2) && (ComfMod == 1)',
            Program_Line_206='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_207='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_208='elseif CurrentTime < 7',
            Program_Line_209='set AHST = 17+AHSTtol',
            Program_Line_210='elseif CurrentTime < 23',
            Program_Line_211='set AHST = 20+AHSTtol',
            Program_Line_212='elseif CurrentTime < 24',
            Program_Line_213='set AHST = 17+AHSTtol',
            Program_Line_214='endif',
            Program_Line_215='endif',
            Program_Line_216='if (ComfStand == 2) && (ComfMod == 2)',
            Program_Line_217='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_218='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_219='elseif CAT==80',
            Program_Line_220='if PMOT < ACSTall',
            Program_Line_221='set ACST = 25+ACSTtol',
            Program_Line_222='elseif PMOT > ACSTaul',
            Program_Line_223='set ACST = 27+ACSTtol',
            Program_Line_224='endif',
            Program_Line_225='elseif CAT==90',
            Program_Line_226='if PMOT < ACSTall',
            Program_Line_227='set ACST = 24+ACSTtol',
            Program_Line_228='elseif PMOT > ACSTaul',
            Program_Line_229='set ACST = 26+ACSTtol',
            Program_Line_230='endif',
            Program_Line_231='endif',
            Program_Line_232='endif',
            Program_Line_233='if (ComfStand == 2) && (ComfMod == 2)',
            Program_Line_234='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_235='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_236='elseif CAT==80',
            Program_Line_237='if PMOT < AHSTall',
            Program_Line_238='set AHST = 19+AHSTtol',
            Program_Line_239='elseif PMOT > AHSTaul',
            Program_Line_240='set AHST = 22+AHSTtol',
            Program_Line_241='endif',
            Program_Line_242='elseif CAT==90',
            Program_Line_243='if PMOT < AHSTall',
            Program_Line_244='set AHST = 20+AHSTtol',
            Program_Line_245='elseif PMOT > AHSTaul',
            Program_Line_246='set AHST = 23+AHSTtol',
            Program_Line_247='endif',
            Program_Line_248='endif',
            Program_Line_249='endif',
            Program_Line_250='if (ComfStand == 2) && (ComfMod == 3)',
            Program_Line_251='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_252='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_253='elseif PMOT < ACSTall',
            Program_Line_254='set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_255='elseif PMOT > ACSTaul',
            Program_Line_256='set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_257='endif',
            Program_Line_258='endif',
            Program_Line_259='if (ComfStand == 2) && (ComfMod == 3)',
            Program_Line_260='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_261='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_262='elseif PMOT < AHSTall',
            Program_Line_263='set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_264='elseif PMOT > AHSTaul',
            Program_Line_265='set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_266='endif',
            Program_Line_267='endif',
            Program_Line_268='if (ComfStand == 3) && (ComfMod == 0)',
            Program_Line_269='if (CAT==80)',
            Program_Line_270='set ACST = 28+ACSTtol',
            Program_Line_271='elseif (CAT==90)',
            Program_Line_272='set ACST = 27+ACSTtol',
            Program_Line_273='endif',
            Program_Line_274='endif',
            Program_Line_275='if (ComfStand == 3) && (ComfMod == 0)',
            Program_Line_276='if (CAT==80)',
            Program_Line_277='set AHST = 18+AHSTtol',
            Program_Line_278='elseif (CAT==90)',
            Program_Line_279='set AHST = 19+AHSTtol',
            Program_Line_280='endif',
            Program_Line_281='endif',
            Program_Line_282='if (ComfStand == 3) && (ComfMod == 1)',
            Program_Line_283='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_284='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_285='elseif CAT==80',
            Program_Line_286='if PMOT < ACSTall',
            Program_Line_287='set ACST = 28+ACSTtol',
            Program_Line_288='elseif PMOT > ACSTaul',
            Program_Line_289='set ACST = 28+ACSTtol',
            Program_Line_290='endif',
            Program_Line_291='elseif CAT==90',
            Program_Line_292='if PMOT < ACSTall',
            Program_Line_293='set ACST = 27+ACSTtol',
            Program_Line_294='elseif PMOT > ACSTaul',
            Program_Line_295='set ACST = 27+ACSTtol',
            Program_Line_296='endif',
            Program_Line_297='endif',
            Program_Line_298='endif',
            Program_Line_299='if (ComfStand == 3) && (ComfMod == 1)',
            Program_Line_300='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_301='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_302='elseif CAT==80',
            Program_Line_303='if PMOT < AHSTall',
            Program_Line_304='set AHST = 18+AHSTtol',
            Program_Line_305='elseif PMOT > AHSTaul',
            Program_Line_306='set AHST = 18+AHSTtol',
            Program_Line_307='endif',
            Program_Line_308='elseif CAT==90',
            Program_Line_309='if PMOT < AHSTall',
            Program_Line_310='set AHST = 19+AHSTtol',
            Program_Line_311='elseif PMOT > AHSTaul',
            Program_Line_312='set AHST = 19+AHSTtol',
            Program_Line_313='endif',
            Program_Line_314='endif',
            Program_Line_315='endif',
            Program_Line_316='if (ComfStand == 3) && (ComfMod == 2)',
            Program_Line_317='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_318='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_319='elseif CAT==80',
            Program_Line_320='if PMOT < ACSTall',
            Program_Line_321='set ACST = 25+ACSTtol',
            Program_Line_322='elseif PMOT > ACSTaul',
            Program_Line_323='set ACST = 27+ACSTtol',
            Program_Line_324='endif',
            Program_Line_325='elseif CAT==90',
            Program_Line_326='if PMOT < ACSTall',
            Program_Line_327='set ACST = 24+ACSTtol',
            Program_Line_328='elseif PMOT > ACSTaul',
            Program_Line_329='set ACST = 26+ACSTtol',
            Program_Line_330='endif',
            Program_Line_331='endif',
            Program_Line_332='endif',
            Program_Line_333='if (ComfStand == 3) && (ComfMod == 2)',
            Program_Line_334='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_335='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_336='elseif CAT==80',
            Program_Line_337='if PMOT < AHSTall',
            Program_Line_338='set AHST = 19+AHSTtol',
            Program_Line_339='elseif PMOT > AHSTaul',
            Program_Line_340='set AHST = 22+AHSTtol',
            Program_Line_341='endif',
            Program_Line_342='elseif CAT==90',
            Program_Line_343='if PMOT < AHSTall',
            Program_Line_344='set AHST = 20+AHSTtol',
            Program_Line_345='elseif PMOT > AHSTaul',
            Program_Line_346='set AHST = 23+AHSTtol',
            Program_Line_347='endif',
            Program_Line_348='endif',
            Program_Line_349='endif',
            Program_Line_350='if (ComfStand == 3) && (ComfMod == 3)',
            Program_Line_351='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_352='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_353='elseif PMOT < ACSTall',
            Program_Line_354='set ACST = ACSTall*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_355='elseif PMOT > ACSTaul',
            Program_Line_356='set ACST = ACSTaul*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_357='endif',
            Program_Line_358='endif',
            Program_Line_359='if (ComfStand == 3) && (ComfMod == 3)',
            Program_Line_360='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_361='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_362='elseif PMOT < AHSTall',
            Program_Line_363='set AHST = AHSTall*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_364='elseif PMOT > AHSTaul',
            Program_Line_365='set AHST = AHSTaul*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_366='endif',
            Program_Line_367='endif',
            Program_Line_368='if (ComfStand == 4) && (ComfMod == 3)',
            Program_Line_369='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_370='if CAT == 1',
            Program_Line_371='set ACST = PMOT*0.77+12.04+ACSTtol',
            Program_Line_372='elseif CAT == 2',
            Program_Line_373='set ACST = PMOT*0.73+15.28+ACSTtol',
            Program_Line_374='endif',
            Program_Line_375='elseif PMOT < ACSTall',
            Program_Line_376='if CAT == 1',
            Program_Line_377='set ACST = ACSTall*0.77+12.04+ACSTtol',
            Program_Line_378='elseif CAT == 2',
            Program_Line_379='set ACST = ACSTall*0.73+15.28+ACSTtol',
            Program_Line_380='endif',
            Program_Line_381='elseif PMOT > ACSTaul',
            Program_Line_382='if CAT == 1',
            Program_Line_383='set ACST = ACSTaul*0.77+12.04+ACSTtol',
            Program_Line_384='elseif CAT == 2',
            Program_Line_385='set ACST = ACSTaul*0.73+15.28+ACSTtol',
            Program_Line_386='endif',
            Program_Line_387='endif',
            Program_Line_388='endif',
            Program_Line_389='if (ComfStand == 4) && (ComfMod == 3)',
            Program_Line_390='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_391='if CAT == 1',
            Program_Line_392='set AHST = PMOT*0.87+2.76+AHSTtol',
            Program_Line_393='elseif CAT == 2',
            Program_Line_394='set AHST = PMOT*0.91-0.48+AHSTtol',
            Program_Line_395='endif',
            Program_Line_396='elseif PMOT < AHSTall',
            Program_Line_397='if CAT == 1',
            Program_Line_398='set AHST = AHSTall*0.87+2.76+AHSTtol',
            Program_Line_399='elseif CAT == 2',
            Program_Line_400='set AHST = AHSTall*0.91-0.48+AHSTtol',
            Program_Line_401='endif',
            Program_Line_402='elseif PMOT > AHSTaul',
            Program_Line_403='if CAT == 1',
            Program_Line_404='set AHST = AHSTaul*0.87+2.76+AHSTtol',
            Program_Line_405='elseif CAT == 2',
            Program_Line_406='set AHST = AHSTaul*0.91-0.48+AHSTtol',
            Program_Line_407='endif',
            Program_Line_408='endif',
            Program_Line_409='endif',
            Program_Line_410='if (ComfStand == 5) && (ComfMod == 3)',
            Program_Line_411='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_412='if CAT == 1',
            Program_Line_413='set ACST = PMOT*0.77+9.34+ACSTtol',
            Program_Line_414='elseif CAT == 2',
            Program_Line_415='set ACST = PMOT*0.73+12.72+ACSTtol',
            Program_Line_416='endif',
            Program_Line_417='elseif PMOT < ACSTall',
            Program_Line_418='if CAT == 1',
            Program_Line_419='set ACST = ACSTall*0.77+9.34+ACSTtol',
            Program_Line_420='elseif CAT == 2',
            Program_Line_421='set ACST = ACSTall*0.73+12.72+ACSTtol',
            Program_Line_422='endif',
            Program_Line_423='elseif PMOT > ACSTaul',
            Program_Line_424='if CAT == 1',
            Program_Line_425='set ACST = ACSTaul*0.77+9.34+ACSTtol',
            Program_Line_426='elseif CAT == 2',
            Program_Line_427='set ACST = ACSTaul*0.73+12.72+ACSTtol',
            Program_Line_428='endif',
            Program_Line_429='endif',
            Program_Line_430='endif',
            Program_Line_431='if (ComfStand == 5) && (ComfMod == 3)',
            Program_Line_432='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_433='if CAT == 1',
            Program_Line_434='set AHST = PMOT*0.87-0.31+AHSTtol',
            Program_Line_435='elseif CAT == 2',
            Program_Line_436='set AHST = PMOT*0.91-3.69+AHSTtol',
            Program_Line_437='endif',
            Program_Line_438='elseif PMOT < AHSTall',
            Program_Line_439='if CAT == 1',
            Program_Line_440='set AHST = AHSTall*0.87-0.31+AHSTtol',
            Program_Line_441='elseif CAT == 2',
            Program_Line_442='set AHST = AHSTall*0.91-3.69+AHSTtol',
            Program_Line_443='endif',
            Program_Line_444='elseif PMOT > AHSTaul',
            Program_Line_445='if CAT == 1',
            Program_Line_446='set AHST = AHSTaul*0.87-0.31+AHSTtol',
            Program_Line_447='elseif CAT == 2',
            Program_Line_448='set AHST = AHSTaul*0.91-3.69+AHSTtol',
            Program_Line_449='endif',
            Program_Line_450='endif',
            Program_Line_451='endif',
            Program_Line_452='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_453='if CAT==80',
            Program_Line_454='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_455='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_456='elseif PMOT < ACSTall',
            Program_Line_457='set ACST = 25+ACSTtol',
            Program_Line_458='elseif PMOT > ACSTaul',
            Program_Line_459='set ACST = 27+ACSTtol',
            Program_Line_460='endif',
            Program_Line_461='elseif CAT==90',
            Program_Line_462='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_463='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_464='elseif PMOT < ACSTall',
            Program_Line_465='set ACST = 24+ACSTtol',
            Program_Line_466='elseif PMOT > ACSTaul',
            Program_Line_467='set ACST = 26+ACSTtol',
            Program_Line_468='endif',
            Program_Line_469='endif',
            Program_Line_470='endif',
            Program_Line_471='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_472='if CAT==80',
            Program_Line_473='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_474='set AHST = PMOT*0.30+25.9+AHSTtol',
            Program_Line_475='elseif PMOT < AHSTall',
            Program_Line_476='set AHST = 19+AHSTtol',
            Program_Line_477='elseif PMOT > AHSTaul',
            Program_Line_478='set AHST = 22+AHSTtol',
            Program_Line_479='endif',
            Program_Line_480='elseif CAT==90',
            Program_Line_481='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_482='set AHST = PMOT*0.30+23.6+AHSTtol',
            Program_Line_483='elseif PMOT < AHSTall',
            Program_Line_484='set AHST = 20+AHSTtol',
            Program_Line_485='elseif PMOT > AHSTaul',
            Program_Line_486='set AHST = 23+AHSTtol',
            Program_Line_487='endif',
            Program_Line_488='endif',
            Program_Line_489='endif',
            Program_Line_490='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_491='if CAT == 80',
            Program_Line_492='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_493='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_494='elseif (PMOT < ACSTall)',
            Program_Line_495='set ACST = ACSTall*0.30+25.9+ACSTtol',
            Program_Line_496='elseif (PMOT > ACSTaul)',
            Program_Line_497='set ACST = ACSTaul*0.30+25.9+ACSTtol',
            Program_Line_498='endif',
            Program_Line_499='elseif CAT == 90',
            Program_Line_500='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_501='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_502='elseif (PMOT < ACSTall)',
            Program_Line_503='set ACST = ACSTall*0.30+23.6+ACSTtol',
            Program_Line_504='elseif (PMOT > ACSTaul)',
            Program_Line_505='set ACST = ACSTaul*0.30+23.6+ACSTtol',
            Program_Line_506='endif',
            Program_Line_507='endif',
            Program_Line_508='endif',
            Program_Line_509='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_510='if CAT == 80',
            Program_Line_511='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_512='set AHST = PMOT*0.32+14.88+AHSTtol',
            Program_Line_513='elseif (PMOT < AHSTall)',
            Program_Line_514='set AHST = AHSTall*0.32+14.88+AHSTtol',
            Program_Line_515='elseif (PMOT > AHSTaul)',
            Program_Line_516='set AHST = AHSTaul*0.32+14.88+AHSTtol',
            Program_Line_517='endif',
            Program_Line_518='elseif CAT == 90',
            Program_Line_519='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_520='set AHST = PMOT*0.31+17.14+AHSTtol',
            Program_Line_521='elseif (PMOT < AHSTall)',
            Program_Line_522='set AHST = AHSTall*0.31+17.14+AHSTtol',
            Program_Line_523='elseif (PMOT > AHSTaul)',
            Program_Line_524='set AHST = AHSTaul*0.31+17.14+AHSTtol',
            Program_Line_525='endif',
            Program_Line_526='endif',
            Program_Line_527='endif',
            Program_Line_528='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_529='if (ComfMod == 0)',
            Program_Line_530='if CAT==80',
            Program_Line_531='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_532='elseif CAT==85',
            Program_Line_533='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_534='elseif CAT==90',
            Program_Line_535='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_536='endif',
            Program_Line_537='endif',
            Program_Line_538='endif',
            Program_Line_539='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_540='if (ComfMod == 0)',
            Program_Line_541='if CAT==80',
            Program_Line_542='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_543='elseif CAT==85',
            Program_Line_544='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_545='elseif CAT==90',
            Program_Line_546='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_547='endif',
            Program_Line_548='endif',
            Program_Line_549='endif',
            Program_Line_550='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_551='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_552='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_553='else',
            Program_Line_554='if CAT==80',
            Program_Line_555='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_556='elseif CAT==85',
            Program_Line_557='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_558='elseif CAT==90',
            Program_Line_559='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_560='endif',
            Program_Line_561='endif',
            Program_Line_562='endif',
            Program_Line_563='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_564='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_565='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_566='else',
            Program_Line_567='if CAT==80',
            Program_Line_568='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_569='elseif CAT==85',
            Program_Line_570='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_571='elseif CAT==90',
            Program_Line_572='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_573='endif',
            Program_Line_574='endif',
            Program_Line_575='endif',
            Program_Line_576='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_577='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_578='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_579='elseif CAT==80',
            Program_Line_580='if PMOT < ACSTall',
            Program_Line_581='set ACST = 25+ACSTtol',
            Program_Line_582='elseif PMOT > ACSTaul',
            Program_Line_583='set ACST = 27+ACSTtol',
            Program_Line_584='endif',
            Program_Line_585='elseif CAT==85',
            Program_Line_586='if PMOT < ACSTall',
            Program_Line_587='set ACST = 25.72+ACSTtol',
            Program_Line_588='elseif PMOT > ACSTaul',
            Program_Line_589='set ACST = 27.89+ACSTtol',
            Program_Line_590='endif',
            Program_Line_591='elseif CAT==90',
            Program_Line_592='if PMOT < ACSTall',
            Program_Line_593='set ACST = 24+ACSTtol',
            Program_Line_594='elseif PMOT > ACSTaul',
            Program_Line_595='set ACST = 26+ACSTtol',
            Program_Line_596='endif',
            Program_Line_597='endif',
            Program_Line_598='endif',
            Program_Line_599='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_600='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_601='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_602='elseif CAT==80',
            Program_Line_603='if PMOT < AHSTall',
            Program_Line_604='set AHST = 19+AHSTtol',
            Program_Line_605='elseif PMOT > AHSTaul',
            Program_Line_606='set AHST = 22+AHSTtol',
            Program_Line_607='endif',
            Program_Line_608='elseif CAT==85',
            Program_Line_609='if PMOT < AHSTall',
            Program_Line_610='set AHST = 20.77+AHSTtol',
            Program_Line_611='elseif PMOT > AHSTaul',
            Program_Line_612='set AHST = 24.26+AHSTtol',
            Program_Line_613='endif',
            Program_Line_614='elseif CAT==90',
            Program_Line_615='if PMOT < AHSTall',
            Program_Line_616='set AHST = 20+AHSTtol',
            Program_Line_617='elseif PMOT > AHSTaul',
            Program_Line_618='set AHST = 23+AHSTtol',
            Program_Line_619='endif',
            Program_Line_620='endif',
            Program_Line_621='endif',
            Program_Line_622='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_623='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_624='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_625='elseif PMOT < ACSTall',
            Program_Line_626='set ACST = ACSTall*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_627='elseif PMOT > ACSTaul',
            Program_Line_628='set ACST = ACSTaul*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_629='endif',
            Program_Line_630='endif',
            Program_Line_631='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_632='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_633='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_634='elseif PMOT < AHSTall',
            Program_Line_635='set AHST = AHSTall*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_636='elseif PMOT > AHSTaul',
            Program_Line_637='set AHST = AHSTaul*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_638='endif',
            Program_Line_639='endif',
            Program_Line_640='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_641='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_642='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_643='else',
            Program_Line_644='if CAT==80',
            Program_Line_645='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_646='elseif CAT==85',
            Program_Line_647='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_648='elseif CAT==90',
            Program_Line_649='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_650='endif',
            Program_Line_651='endif',
            Program_Line_652='endif',
            Program_Line_653='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_654='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_655='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_656='else',
            Program_Line_657='if CAT==80',
            Program_Line_658='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_659='elseif CAT==85',
            Program_Line_660='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_661='elseif CAT==90',
            Program_Line_662='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_663='endif',
            Program_Line_664='endif',
            Program_Line_665='endif',
            Program_Line_666='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_667='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_668='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_669='elseif CAT==80',
            Program_Line_670='if PMOT < ACSTall',
            Program_Line_671='set ACST = 25+ACSTtol',
            Program_Line_672='elseif PMOT > ACSTaul',
            Program_Line_673='set ACST = 27+ACSTtol',
            Program_Line_674='endif',
            Program_Line_675='elseif CAT==85',
            Program_Line_676='if PMOT < ACSTall',
            Program_Line_677='set ACST = 25.72+ACSTtol',
            Program_Line_678='elseif PMOT > ACSTaul',
            Program_Line_679='set ACST = 27.89+ACSTtol',
            Program_Line_680='endif',
            Program_Line_681='elseif CAT==90',
            Program_Line_682='if PMOT < ACSTall',
            Program_Line_683='set ACST = 24+ACSTtol',
            Program_Line_684='elseif PMOT > ACSTaul',
            Program_Line_685='set ACST = 26+ACSTtol',
            Program_Line_686='endif',
            Program_Line_687='endif',
            Program_Line_688='endif',
            Program_Line_689='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_690='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_691='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_692='elseif CAT==80',
            Program_Line_693='if PMOT < AHSTall',
            Program_Line_694='set AHST = 19+AHSTtol',
            Program_Line_695='elseif PMOT > AHSTaul',
            Program_Line_696='set AHST = 22+AHSTtol',
            Program_Line_697='endif',
            Program_Line_698='elseif CAT==85',
            Program_Line_699='if PMOT < AHSTall',
            Program_Line_700='set AHST = 20.77+AHSTtol',
            Program_Line_701='elseif PMOT > AHSTaul',
            Program_Line_702='set AHST = 24.26+AHSTtol',
            Program_Line_703='endif',
            Program_Line_704='elseif CAT==90',
            Program_Line_705='if PMOT < AHSTall',
            Program_Line_706='set AHST = 20+AHSTtol',
            Program_Line_707='elseif PMOT > AHSTaul',
            Program_Line_708='set AHST = 23+AHSTtol',
            Program_Line_709='endif',
            Program_Line_710='endif',
            Program_Line_711='endif',
            Program_Line_712='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_713='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_714='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_715='elseif PMOT < ACSTall',
            Program_Line_716='set ACST = ACSTall*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_717='elseif PMOT > ACSTaul',
            Program_Line_718='set ACST = ACSTaul*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_719='endif',
            Program_Line_720='endif',
            Program_Line_721='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_722='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_723='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_724='elseif PMOT < AHSTall',
            Program_Line_725='set AHST = AHSTall*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_726='elseif PMOT > AHSTaul',
            Program_Line_727='set AHST = AHSTaul*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_728='endif',
            Program_Line_729='endif',
            Program_Line_730='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_731='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_732='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_733='else',
            Program_Line_734='if CAT==80',
            Program_Line_735='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_736='elseif CAT==90',
            Program_Line_737='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_738='endif',
            Program_Line_739='endif',
            Program_Line_740='endif',
            Program_Line_741='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_742='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_743='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_744='else',
            Program_Line_745='if CAT==80',
            Program_Line_746='set AHST = PMOT*0.078+23.25+2.72+AHSTtol',
            Program_Line_747='elseif CAT==90',
            Program_Line_748='set AHST = PMOT*0.078+23.25+1.5+AHSTtol',
            Program_Line_749='endif',
            Program_Line_750='endif',
            Program_Line_751='endif',
            Program_Line_752='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_753='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_754='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_755='elseif CAT==80',
            Program_Line_756='if PMOT < ACSTall',
            Program_Line_757='set ACST = 25+ACSTtol',
            Program_Line_758='elseif PMOT > ACSTaul',
            Program_Line_759='set ACST = 27+ACSTtol',
            Program_Line_760='endif',
            Program_Line_761='elseif CAT==90',
            Program_Line_762='if PMOT < ACSTall',
            Program_Line_763='set ACST = 24+ACSTtol',
            Program_Line_764='elseif PMOT > ACSTaul',
            Program_Line_765='set ACST = 26+ACSTtol',
            Program_Line_766='endif',
            Program_Line_767='endif',
            Program_Line_768='endif',
            Program_Line_769='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_770='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_771='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_772='elseif CAT==80',
            Program_Line_773='if PMOT < AHSTall',
            Program_Line_774='set AHST = 19+AHSTtol',
            Program_Line_775='elseif PMOT > AHSTaul',
            Program_Line_776='set AHST = 22+AHSTtol',
            Program_Line_777='endif',
            Program_Line_778='elseif CAT==90',
            Program_Line_779='if PMOT < AHSTall',
            Program_Line_780='set AHST = 20+AHSTtol',
            Program_Line_781='elseif PMOT > AHSTaul',
            Program_Line_782='set AHST = 23+AHSTtol',
            Program_Line_783='endif',
            Program_Line_784='endif',
            Program_Line_785='endif',
            Program_Line_786='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_787='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_788='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_789='elseif PMOT < ACSTall',
            Program_Line_790='set ACST = ACSTall*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_791='elseif PMOT > ACSTaul',
            Program_Line_792='set ACST = ACSTaul*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_793='endif',
            Program_Line_794='endif',
            Program_Line_795='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_796='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_797='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_798='elseif PMOT < AHSTall',
            Program_Line_799='set AHST = AHSTall*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_800='elseif PMOT > AHSTaul',
            Program_Line_801='set AHST = AHSTaul*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_802='endif',
            Program_Line_803='endif',
            Program_Line_804='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_805='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_806='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_807='else',
            Program_Line_808='if CAT==80',
            Program_Line_809='set ACST = RMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_810='elseif CAT==90',
            Program_Line_811='set ACST = RMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_812='endif',
            Program_Line_813='endif',
            Program_Line_814='endif',
            Program_Line_815='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_816='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_817='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_818='else',
            Program_Line_819='if CAT==80',
            Program_Line_820='set AHST = RMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_821='elseif CAT==90',
            Program_Line_822='set AHST = RMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_823='endif',
            Program_Line_824='endif',
            Program_Line_825='endif',
            Program_Line_826='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_827='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_828='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_829='elseif CAT==80',
            Program_Line_830='if RMOT < ACSTall',
            Program_Line_831='set ACST = 25+ACSTtol',
            Program_Line_832='elseif RMOT > ACSTaul',
            Program_Line_833='set ACST = 27+ACSTtol',
            Program_Line_834='endif',
            Program_Line_835='elseif CAT==90',
            Program_Line_836='if RMOT < ACSTall',
            Program_Line_837='set ACST = 24+ACSTtol',
            Program_Line_838='elseif RMOT > ACSTaul',
            Program_Line_839='set ACST = 26+ACSTtol',
            Program_Line_840='endif',
            Program_Line_841='endif',
            Program_Line_842='endif',
            Program_Line_843='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_844='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_845='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_846='elseif CAT==80',
            Program_Line_847='if RMOT < AHSTall',
            Program_Line_848='set AHST = 19+AHSTtol',
            Program_Line_849='elseif RMOT > AHSTaul',
            Program_Line_850='set AHST = 22+AHSTtol',
            Program_Line_851='endif',
            Program_Line_852='elseif CAT==90',
            Program_Line_853='if RMOT < AHSTall',
            Program_Line_854='set AHST = 20+AHSTtol',
            Program_Line_855='elseif RMOT > AHSTaul',
            Program_Line_856='set AHST = 23+AHSTtol',
            Program_Line_857='endif',
            Program_Line_858='endif',
            Program_Line_859='endif',
            Program_Line_860='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_861='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_862='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_863='elseif RMOT < ACSTall',
            Program_Line_864='set ACST = ACSTall*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_865='elseif RMOT > ACSTaul',
            Program_Line_866='set ACST = ACSTaul*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_867='endif',
            Program_Line_868='endif',
            Program_Line_869='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_870='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_871='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_872='elseif RMOT < AHSTall',
            Program_Line_873='set AHST = AHSTall*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_874='elseif RMOT > AHSTaul',
            Program_Line_875='set AHST = AHSTaul*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_876='endif',
            Program_Line_877='endif',
            Program_Line_878='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_879='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_880='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_881='else',
            Program_Line_882='if CAT==80',
            Program_Line_883='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_884='elseif CAT==90',
            Program_Line_885='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_886='endif',
            Program_Line_887='endif',
            Program_Line_888='endif',
            Program_Line_889='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_890='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_891='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_892='else',
            Program_Line_893='if CAT==80',
            Program_Line_894='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_895='elseif CAT==90',
            Program_Line_896='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_897='endif',
            Program_Line_898='endif',
            Program_Line_899='endif',
            Program_Line_900='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_901='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_902='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_903='elseif CAT==80',
            Program_Line_904='if PMOT < ACSTall',
            Program_Line_905='set ACST = 25+ACSTtol',
            Program_Line_906='elseif PMOT > ACSTaul',
            Program_Line_907='set ACST = 27+ACSTtol',
            Program_Line_908='endif',
            Program_Line_909='elseif CAT==90',
            Program_Line_910='if PMOT < ACSTall',
            Program_Line_911='set ACST = 24+ACSTtol',
            Program_Line_912='elseif PMOT > ACSTaul',
            Program_Line_913='set ACST = 26+ACSTtol',
            Program_Line_914='endif',
            Program_Line_915='endif',
            Program_Line_916='endif',
            Program_Line_917='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_918='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_919='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_920='elseif CAT==80',
            Program_Line_921='if PMOT < AHSTall',
            Program_Line_922='set AHST = 19+AHSTtol',
            Program_Line_923='elseif PMOT > AHSTaul',
            Program_Line_924='set AHST = 22+AHSTtol',
            Program_Line_925='endif',
            Program_Line_926='elseif CAT==90',
            Program_Line_927='if PMOT < AHSTall',
            Program_Line_928='set AHST = 20+AHSTtol',
            Program_Line_929='elseif PMOT > AHSTaul',
            Program_Line_930='set AHST = 23+AHSTtol',
            Program_Line_931='endif',
            Program_Line_932='endif',
            Program_Line_933='endif',
            Program_Line_934='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_935='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_936='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_937='elseif PMOT < ACSTall',
            Program_Line_938='set ACST = ACSTall*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_939='elseif PMOT > ACSTaul',
            Program_Line_940='set ACST = ACSTaul*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_941='endif',
            Program_Line_942='endif',
            Program_Line_943='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_944='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_945='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_946='elseif PMOT < AHSTall',
            Program_Line_947='set AHST = AHSTall*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_948='elseif PMOT > AHSTaul',
            Program_Line_949='set AHST = AHSTaul*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_950='endif',
            Program_Line_951='endif',
            Program_Line_952='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_953='if (CAT==80)',
            Program_Line_954='set ACST = 27+ACSTtol',
            Program_Line_955='elseif (CAT==90)',
            Program_Line_956='set ACST = 25.5+ACSTtol',
            Program_Line_957='endif',
            Program_Line_958='endif',
            Program_Line_959='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_960='if (CAT==80)',
            Program_Line_961='set AHST = 20+AHSTtol',
            Program_Line_962='elseif (CAT==90)',
            Program_Line_963='set AHST = 21.5+AHSTtol',
            Program_Line_964='endif',
            Program_Line_965='endif',
            Program_Line_966='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_967='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_968='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_969='elseif CAT==80',
            Program_Line_970='if PMOT < ACSTall',
            Program_Line_971='set ACST = 27+ACSTtol',
            Program_Line_972='elseif PMOT > ACSTaul',
            Program_Line_973='set ACST = 27+ACSTtol',
            Program_Line_974='endif',
            Program_Line_975='elseif CAT==90',
            Program_Line_976='if PMOT < ACSTall',
            Program_Line_977='set ACST = 25.5+ACSTtol',
            Program_Line_978='elseif PMOT > ACSTaul',
            Program_Line_979='set ACST = 25.5+ACSTtol',
            Program_Line_980='endif',
            Program_Line_981='endif',
            Program_Line_982='endif',
            Program_Line_983='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_984='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_985='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_986='elseif CAT==80',
            Program_Line_987='if PMOT < AHSTall',
            Program_Line_988='set AHST = 20+AHSTtol',
            Program_Line_989='elseif PMOT > AHSTaul',
            Program_Line_990='set AHST = 20+AHSTtol',
            Program_Line_991='endif',
            Program_Line_992='elseif CAT==90',
            Program_Line_993='if PMOT < AHSTall',
            Program_Line_994='set AHST = 21.5+AHSTtol',
            Program_Line_995='elseif PMOT > AHSTaul',
            Program_Line_996='set AHST = 21.5+AHSTtol',
            Program_Line_997='endif',
            Program_Line_998='endif',
            Program_Line_999='endif',
            Program_Line_1000='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_1001='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1002='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1003='elseif CAT==80',
            Program_Line_1004='if PMOT < ACSTall',
            Program_Line_1005='set ACST = 25+ACSTtol',
            Program_Line_1006='elseif PMOT > ACSTaul',
            Program_Line_1007='set ACST = 27+ACSTtol',
            Program_Line_1008='endif',
            Program_Line_1009='elseif CAT==90',
            Program_Line_1010='if PMOT < ACSTall',
            Program_Line_1011='set ACST = 24+ACSTtol',
            Program_Line_1012='elseif PMOT > ACSTaul',
            Program_Line_1013='set ACST = 26+ACSTtol',
            Program_Line_1014='endif',
            Program_Line_1015='endif',
            Program_Line_1016='endif',
            Program_Line_1017='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_1018='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1019='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1020='elseif CAT==80',
            Program_Line_1021='if PMOT < AHSTall',
            Program_Line_1022='set AHST = 19+AHSTtol',
            Program_Line_1023='elseif PMOT > AHSTaul',
            Program_Line_1024='set AHST = 22+AHSTtol',
            Program_Line_1025='endif',
            Program_Line_1026='elseif CAT==90',
            Program_Line_1027='if PMOT < AHSTall',
            Program_Line_1028='set AHST = 20+AHSTtol',
            Program_Line_1029='elseif PMOT > AHSTaul',
            Program_Line_1030='set AHST = 23+AHSTtol',
            Program_Line_1031='endif',
            Program_Line_1032='endif',
            Program_Line_1033='endif',
            Program_Line_1034='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_1035='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1036='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1037='elseif PMOT < ACSTall',
            Program_Line_1038='set ACST = ACSTall*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1039='elseif PMOT > ACSTaul',
            Program_Line_1040='set ACST = ACSTaul*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_1041='endif',
            Program_Line_1042='endif',
            Program_Line_1043='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_1044='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1045='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1046='elseif PMOT < AHSTall',
            Program_Line_1047='set AHST = AHSTall*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1048='elseif PMOT > AHSTaul',
            Program_Line_1049='set AHST = AHSTaul*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_1050='endif',
            Program_Line_1051='endif',
            Program_Line_1052='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_1053='if (CAT==80)',
            Program_Line_1054='if (CurrentTime > 6) && (CurrentTime < 23)',
            Program_Line_1055='if (ComfMod == 0.1)',
            Program_Line_1056='set ACST = 27+ACSTtol',
            Program_Line_1057='elseif (ComfMod == 0.2)',
            Program_Line_1058='set ACST = 26+ACSTtol',
            Program_Line_1059='elseif (ComfMod == 0.3)',
            Program_Line_1060='set ACST = 25+ACSTtol',
            Program_Line_1061='elseif (ComfMod == 0.4)',
            Program_Line_1062='set ACST = 24+ACSTtol',
            Program_Line_1063='elseif (ComfMod == 0.5)',
            Program_Line_1064='set ACST = 23+ACSTtol',
            Program_Line_1065='endif',
            Program_Line_1066='else',
            Program_Line_1067='set ACST = 24+ACSTtol',
            Program_Line_1068='endif',
            Program_Line_1069='elseif (CAT==90)',
            Program_Line_1070='if (CurrentTime > 6) && (CurrentTime < 23)',
            Program_Line_1071='if (ComfMod == 0.1)',
            Program_Line_1072='set ACST = 26+ACSTtol',
            Program_Line_1073='elseif (ComfMod == 0.2)',
            Program_Line_1074='set ACST = 25+ACSTtol',
            Program_Line_1075='elseif (ComfMod == 0.3)',
            Program_Line_1076='set ACST = 24+ACSTtol',
            Program_Line_1077='elseif (ComfMod == 0.4)',
            Program_Line_1078='set ACST = 23+ACSTtol',
            Program_Line_1079='elseif (ComfMod == 0.5)',
            Program_Line_1080='set ACST = 22+ACSTtol',
            Program_Line_1081='endif',
            Program_Line_1082='else',
            Program_Line_1083='set ACST = 23+ACSTtol',
            Program_Line_1084='endif',
            Program_Line_1085='endif',
            Program_Line_1086='endif',
            Program_Line_1087='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_1088='if (ComfMod == 0.1) || (ComfMod == 0.2) || (ComfMod == 0.3) || (ComfMod == 0.4) || (ComfMod == 0.5)',
            Program_Line_1089='if (CAT==80)',
            Program_Line_1090='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1091='set AHST = 20+AHSTtol',
            Program_Line_1092='else',
            Program_Line_1093='set AHST = 18+AHSTtol',
            Program_Line_1094='endif',
            Program_Line_1095='elseif (CAT==90)',
            Program_Line_1096='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1097='set AHST = 21+AHSTtol',
            Program_Line_1098='else',
            Program_Line_1099='set AHST = 19+AHSTtol',
            Program_Line_1100='endif',
            Program_Line_1101='endif',
            Program_Line_1102='endif',
            Program_Line_1103='endif',
            Program_Line_1104='if (ComfStand == 13)',
            Program_Line_1105='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1106='if CAT == 80',
            Program_Line_1107='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1108='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1109='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1110='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1111='set ACST = 27+ACSTtol',
            Program_Line_1112='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1113='set ACST = 26+ACSTtol',
            Program_Line_1114='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1115='set ACST = 25+ACSTtol',
            Program_Line_1116='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1117='set ACST = 24+ACSTtol',
            Program_Line_1118='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1119='set ACST = 23+ACSTtol',
            Program_Line_1120='else',
            Program_Line_1121='set ACST = 24+ACSTtol',
            Program_Line_1122='endif',
            Program_Line_1123='endif',
            Program_Line_1124='elseif CAT==90',
            Program_Line_1125='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1126='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1127='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1128='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1129='set ACST = 26+ACSTtol',
            Program_Line_1130='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1131='set ACST = 25+ACSTtol',
            Program_Line_1132='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1133='set ACST = 24+ACSTtol',
            Program_Line_1134='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1135='set ACST = 23+ACSTtol',
            Program_Line_1136='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1137='set ACST = 22+ACSTtol',
            Program_Line_1138='else',
            Program_Line_1139='set ACST = 23+ACSTtol',
            Program_Line_1140='endif',
            Program_Line_1141='endif',
            Program_Line_1142='endif',
            Program_Line_1143='endif',
            Program_Line_1144='endif',
            Program_Line_1145='if (ComfStand == 13)',
            Program_Line_1146='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1147='if CAT == 80',
            Program_Line_1148='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1149='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1150='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1151='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1152='set AHST = 20+AHSTtol',
            Program_Line_1153='else',
            Program_Line_1154='set AHST = 18+AHSTtol',
            Program_Line_1155='endif',
            Program_Line_1156='endif',
            Program_Line_1157='elseif CAT==90',
            Program_Line_1158='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1159='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1160='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1161='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1162='set AHST = 21+AHSTtol',
            Program_Line_1163='else',
            Program_Line_1164='set AHST = 19+AHSTtol',
            Program_Line_1165='endif',
            Program_Line_1166='endif',
            Program_Line_1167='endif',
            Program_Line_1168='endif',
            Program_Line_1169='endif',
            Program_Line_1170='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1171='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1172='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1173='elseif CAT==80',
            Program_Line_1174='if PMOT < ACSTall',
            Program_Line_1175='set ACST = 25+ACSTtol',
            Program_Line_1176='elseif PMOT > ACSTaul',
            Program_Line_1177='set ACST = 27+ACSTtol',
            Program_Line_1178='endif',
            Program_Line_1179='elseif CAT==90',
            Program_Line_1180='if PMOT < ACSTall',
            Program_Line_1181='set ACST = 24+ACSTtol',
            Program_Line_1182='elseif PMOT > ACSTaul',
            Program_Line_1183='set ACST = 26+ACSTtol',
            Program_Line_1184='endif',
            Program_Line_1185='endif',
            Program_Line_1186='endif',
            Program_Line_1187='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1188='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1189='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1190='elseif CAT==80',
            Program_Line_1191='if PMOT < AHSTall',
            Program_Line_1192='set AHST = 19+AHSTtol',
            Program_Line_1193='elseif PMOT > AHSTaul',
            Program_Line_1194='set AHST = 22+AHSTtol',
            Program_Line_1195='endif',
            Program_Line_1196='elseif CAT==90',
            Program_Line_1197='if PMOT < AHSTall',
            Program_Line_1198='set AHST = 20+AHSTtol',
            Program_Line_1199='elseif PMOT > AHSTaul',
            Program_Line_1200='set AHST = 23+AHSTtol',
            Program_Line_1201='endif',
            Program_Line_1202='endif',
            Program_Line_1203='endif',
            Program_Line_1204='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1205='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1206='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1207='elseif PMOT < ACSTall',
            Program_Line_1208='set ACST = ACSTall*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1209='elseif PMOT > ACSTaul',
            Program_Line_1210='set ACST = ACSTaul*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1211='endif',
            Program_Line_1212='endif',
            Program_Line_1213='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1214='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1215='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1216='elseif PMOT < AHSTall',
            Program_Line_1217='set AHST = AHSTall*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1218='elseif PMOT > AHSTaul',
            Program_Line_1219='set AHST = AHSTaul*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1220='endif',
            Program_Line_1221='endif',
            Program_Line_1222='if (ComfStand == 14)',
            Program_Line_1223='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1224='if CAT == 80',
            Program_Line_1225='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1226='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1227='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1228='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1229='set ACST = 27+ACSTtol',
            Program_Line_1230='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1231='set ACST = 26+ACSTtol',
            Program_Line_1232='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1233='set ACST = 25+ACSTtol',
            Program_Line_1234='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1235='set ACST = 24+ACSTtol',
            Program_Line_1236='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1237='set ACST = 23+ACSTtol',
            Program_Line_1238='else',
            Program_Line_1239='set ACST = 24+ACSTtol',
            Program_Line_1240='endif',
            Program_Line_1241='endif',
            Program_Line_1242='elseif CAT==90',
            Program_Line_1243='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1244='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1245='elseif (PMOT < ACSTall) || (PMOT > ACSTaul)',
            Program_Line_1246='if (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.1)',
            Program_Line_1247='set ACST = 26+ACSTtol',
            Program_Line_1248='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.2)',
            Program_Line_1249='set ACST = 25+ACSTtol',
            Program_Line_1250='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.3)',
            Program_Line_1251='set ACST = 24+ACSTtol',
            Program_Line_1252='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.4)',
            Program_Line_1253='set ACST = 23+ACSTtol',
            Program_Line_1254='elseif (CurrentTime > 6) && (CurrentTime < 23) && (ComfMod == 1.5)',
            Program_Line_1255='set ACST = 22+ACSTtol',
            Program_Line_1256='else',
            Program_Line_1257='set ACST = 23+ACSTtol',
            Program_Line_1258='endif',
            Program_Line_1259='endif',
            Program_Line_1260='endif',
            Program_Line_1261='endif',
            Program_Line_1262='endif',
            Program_Line_1263='if (ComfStand == 14)',
            Program_Line_1264='if (ComfMod == 1.1) || (ComfMod == 1.2) || (ComfMod == 1.3) || (ComfMod == 1.4) || (ComfMod == 1.5)',
            Program_Line_1265='if CAT == 80',
            Program_Line_1266='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1267='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1268='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1269='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1270='set AHST = 20+AHSTtol',
            Program_Line_1271='else',
            Program_Line_1272='set AHST = 18+AHSTtol',
            Program_Line_1273='endif',
            Program_Line_1274='endif',
            Program_Line_1275='elseif CAT==90',
            Program_Line_1276='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1277='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1278='elseif (PMOT < AHSTall) || (PMOT > AHSTaul)',
            Program_Line_1279='if (CurrentTime >6) && (CurrentTime < 12)',
            Program_Line_1280='set AHST = 21+AHSTtol',
            Program_Line_1281='else',
            Program_Line_1282='set AHST = 19+AHSTtol',
            Program_Line_1283='endif',
            Program_Line_1284='endif',
            Program_Line_1285='endif',
            Program_Line_1286='endif',
            Program_Line_1287='endif',
            Program_Line_1288='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1289='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1290='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1291='elseif CAT==80',
            Program_Line_1292='if PMOT < ACSTall',
            Program_Line_1293='set ACST = 25+ACSTtol',
            Program_Line_1294='elseif PMOT > ACSTaul',
            Program_Line_1295='set ACST = 27+ACSTtol',
            Program_Line_1296='endif',
            Program_Line_1297='elseif CAT==90',
            Program_Line_1298='if PMOT < ACSTall',
            Program_Line_1299='set ACST = 24+ACSTtol',
            Program_Line_1300='elseif PMOT > ACSTaul',
            Program_Line_1301='set ACST = 26+ACSTtol',
            Program_Line_1302='endif',
            Program_Line_1303='endif',
            Program_Line_1304='endif',
            Program_Line_1305='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1306='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1307='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1308='elseif CAT==80',
            Program_Line_1309='if PMOT < AHSTall',
            Program_Line_1310='set AHST = 19+AHSTtol',
            Program_Line_1311='elseif PMOT > AHSTaul',
            Program_Line_1312='set AHST = 22+AHSTtol',
            Program_Line_1313='endif',
            Program_Line_1314='elseif CAT==90',
            Program_Line_1315='if PMOT < AHSTall',
            Program_Line_1316='set AHST = 20+AHSTtol',
            Program_Line_1317='elseif PMOT > AHSTaul',
            Program_Line_1318='set AHST = 23+AHSTtol',
            Program_Line_1319='endif',
            Program_Line_1320='endif',
            Program_Line_1321='endif',
            Program_Line_1322='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1323='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1324='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1325='elseif PMOT < ACSTall',
            Program_Line_1326='set ACST = ACSTall*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1327='elseif PMOT > ACSTaul',
            Program_Line_1328='set ACST = ACSTaul*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1329='endif',
            Program_Line_1330='endif',
            Program_Line_1331='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1332='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1333='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1334='elseif PMOT < AHSTall',
            Program_Line_1335='set AHST = AHSTall*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1336='elseif PMOT > AHSTaul',
            Program_Line_1337='set AHST = AHSTaul*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1338='endif',
            Program_Line_1339='endif',
            Program_Line_1340='if (ComfStand == 15) || (ComfStand == 16)',
            Program_Line_1341='if (ComfMod == 0)',
            Program_Line_1342='if (CAT==80)',
            Program_Line_1343='if PMOT < 20',
            Program_Line_1344='set ACST = 23.5+ACSTtol',
            Program_Line_1345='set AHST = 21+ACSTtol',
            Program_Line_1346='else',
            Program_Line_1347='set ACST = 25.5+ACSTtol',
            Program_Line_1348='set AHST = 22.5+ACSTtol',
            Program_Line_1349='endif',
            Program_Line_1350='elseif (CAT==90)',
            Program_Line_1351='if PMOT < 20',
            Program_Line_1352='set ACST = 23+ACSTtol',
            Program_Line_1353='set AHST = 21.5+ACSTtol',
            Program_Line_1354='else',
            Program_Line_1355='set ACST = 25+ACSTtol',
            Program_Line_1356='set AHST = 23+ACSTtol',
            Program_Line_1357='endif',
            Program_Line_1358='endif',
            Program_Line_1359='endif',
            Program_Line_1360='endif',
            Program_Line_1361='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1362='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1363='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1364='elseif CAT==80',
            Program_Line_1365='if PMOT < ACSTall',
            Program_Line_1366='set ACST = 23.5+ACSTtol',
            Program_Line_1367='elseif PMOT > ACSTaul',
            Program_Line_1368='set ACST = 25.5+ACSTtol',
            Program_Line_1369='endif',
            Program_Line_1370='elseif CAT==90',
            Program_Line_1371='if PMOT < ACSTall',
            Program_Line_1372='set ACST = 23+ACSTtol',
            Program_Line_1373='elseif PMOT > ACSTaul',
            Program_Line_1374='set ACST = 25+ACSTtol',
            Program_Line_1375='endif',
            Program_Line_1376='endif',
            Program_Line_1377='endif',
            Program_Line_1378='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1379='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1380='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1381='elseif CAT==80',
            Program_Line_1382='if PMOT < AHSTall',
            Program_Line_1383='set AHST = 21+AHSTtol',
            Program_Line_1384='elseif PMOT > AHSTaul',
            Program_Line_1385='set AHST = 22.5+AHSTtol',
            Program_Line_1386='endif',
            Program_Line_1387='elseif CAT==90',
            Program_Line_1388='if PMOT < AHSTall',
            Program_Line_1389='set AHST = 23+AHSTtol',
            Program_Line_1390='elseif PMOT > AHSTaul',
            Program_Line_1391='set AHST = 23+AHSTtol',
            Program_Line_1392='endif',
            Program_Line_1393='endif',
            Program_Line_1394='endif',
            Program_Line_1395='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1396='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1397='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1398='elseif CAT==80',
            Program_Line_1399='if PMOT < ACSTall',
            Program_Line_1400='set ACST = 25+ACSTtol',
            Program_Line_1401='elseif PMOT > ACSTaul',
            Program_Line_1402='set ACST = 27+ACSTtol',
            Program_Line_1403='endif',
            Program_Line_1404='elseif CAT==90',
            Program_Line_1405='if PMOT < ACSTall',
            Program_Line_1406='set ACST = 24+ACSTtol',
            Program_Line_1407='elseif PMOT > ACSTaul',
            Program_Line_1408='set ACST = 26+ACSTtol',
            Program_Line_1409='endif',
            Program_Line_1410='endif',
            Program_Line_1411='endif',
            Program_Line_1412='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1413='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1414='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1415='elseif CAT==80',
            Program_Line_1416='if PMOT < AHSTall',
            Program_Line_1417='set AHST = 19+AHSTtol',
            Program_Line_1418='elseif PMOT > AHSTaul',
            Program_Line_1419='set AHST = 22+AHSTtol',
            Program_Line_1420='endif',
            Program_Line_1421='elseif CAT==90',
            Program_Line_1422='if PMOT < AHSTall',
            Program_Line_1423='set AHST = 20+AHSTtol',
            Program_Line_1424='elseif PMOT > AHSTaul',
            Program_Line_1425='set AHST = 23+AHSTtol',
            Program_Line_1426='endif',
            Program_Line_1427='endif',
            Program_Line_1428='endif',
            Program_Line_1429='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1430='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1431='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1432='elseif PMOT < ACSTall',
            Program_Line_1433='set ACST = ACSTall*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1434='elseif PMOT > ACSTaul',
            Program_Line_1435='set ACST = ACSTaul*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1436='endif',
            Program_Line_1437='endif',
            Program_Line_1438='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1439='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1440='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1441='elseif PMOT < AHSTall',
            Program_Line_1442='set AHST = AHSTall*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1443='elseif PMOT > AHSTaul',
            Program_Line_1444='set AHST = AHSTaul*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1445='endif',
            Program_Line_1446='endif',
            Program_Line_1447='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1448='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1449='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1450='elseif CAT==80',
            Program_Line_1451='if PMOT < ACSTall',
            Program_Line_1452='set ACST = 23.5+ACSTtol',
            Program_Line_1453='elseif PMOT > ACSTaul',
            Program_Line_1454='set ACST = 25.5+ACSTtol',
            Program_Line_1455='endif',
            Program_Line_1456='elseif CAT==90',
            Program_Line_1457='if PMOT < ACSTall',
            Program_Line_1458='set ACST = 23+ACSTtol',
            Program_Line_1459='elseif PMOT > ACSTaul',
            Program_Line_1460='set ACST = 25+ACSTtol',
            Program_Line_1461='endif',
            Program_Line_1462='endif',
            Program_Line_1463='endif',
            Program_Line_1464='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1465='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1466='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1467='elseif CAT==80',
            Program_Line_1468='if PMOT < AHSTall',
            Program_Line_1469='set AHST = 21+AHSTtol',
            Program_Line_1470='elseif PMOT > AHSTaul',
            Program_Line_1471='set AHST = 22.5+AHSTtol',
            Program_Line_1472='endif',
            Program_Line_1473='elseif CAT==90',
            Program_Line_1474='if PMOT < AHSTall',
            Program_Line_1475='set AHST = 23+AHSTtol',
            Program_Line_1476='elseif PMOT > AHSTaul',
            Program_Line_1477='set AHST = 23+AHSTtol',
            Program_Line_1478='endif',
            Program_Line_1479='endif',
            Program_Line_1480='endif',
            Program_Line_1481='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1482='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1483='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1484='elseif CAT==80',
            Program_Line_1485='if PMOT < ACSTall',
            Program_Line_1486='set ACST = 25+ACSTtol',
            Program_Line_1487='elseif PMOT > ACSTaul',
            Program_Line_1488='set ACST = 27+ACSTtol',
            Program_Line_1489='endif',
            Program_Line_1490='elseif CAT==90',
            Program_Line_1491='if PMOT < ACSTall',
            Program_Line_1492='set ACST = 24+ACSTtol',
            Program_Line_1493='elseif PMOT > ACSTaul',
            Program_Line_1494='set ACST = 26+ACSTtol',
            Program_Line_1495='endif',
            Program_Line_1496='endif',
            Program_Line_1497='endif',
            Program_Line_1498='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1499='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1500='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1501='elseif CAT==80',
            Program_Line_1502='if PMOT < AHSTall',
            Program_Line_1503='set AHST = 19+AHSTtol',
            Program_Line_1504='elseif PMOT > AHSTaul',
            Program_Line_1505='set AHST = 22+AHSTtol',
            Program_Line_1506='endif',
            Program_Line_1507='elseif CAT==90',
            Program_Line_1508='if PMOT < AHSTall',
            Program_Line_1509='set AHST = 20+AHSTtol',
            Program_Line_1510='elseif PMOT > AHSTaul',
            Program_Line_1511='set AHST = 23+AHSTtol',
            Program_Line_1512='endif',
            Program_Line_1513='endif',
            Program_Line_1514='endif',
            Program_Line_1515='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1516='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1517='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1518='elseif PMOT < ACSTall',
            Program_Line_1519='set ACST = ACSTall*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1520='elseif PMOT > ACSTaul',
            Program_Line_1521='set ACST = ACSTaul*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1522='endif',
            Program_Line_1523='endif',
            Program_Line_1524='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1525='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1526='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1527='elseif PMOT < AHSTall',
            Program_Line_1528='set AHST = AHSTall*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1529='elseif PMOT > AHSTaul',
            Program_Line_1530='set AHST = AHSTaul*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1531='endif',
            Program_Line_1532='endif',
            Program_Line_1533='if (ComfStand == 17) || (ComfStand == 18) || (ComfStand == 19) || (ComfStand == 20)',
            Program_Line_1534='if ComfMod == 0',
            Program_Line_1535='set ACST = 25+ACSTtol',
            Program_Line_1536='set AHST = 20+AHSTtol',
            Program_Line_1537='endif',
            Program_Line_1538='endif',
            Program_Line_1539='if (ComfStand == 17) && (ComfMod == 1)',
            Program_Line_1540='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1541='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1542='set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1543='else',
            Program_Line_1544='set ACST = 25+ACSTtol',
            Program_Line_1545='endif',
            Program_Line_1546='else',
            Program_Line_1547='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1548='set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1549='else',
            Program_Line_1550='set ACST = 25+ACSTtol',
            Program_Line_1551='endif',
            Program_Line_1552='endif',
            Program_Line_1553='endif',
            Program_Line_1554='if (ComfStand == 17) && (ComfMod == 1)',
            Program_Line_1555='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1556='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1557='set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1558='else',
            Program_Line_1559='set AHST = 20+AHSTtol',
            Program_Line_1560='endif',
            Program_Line_1561='else',
            Program_Line_1562='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1563='set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1564='else',
            Program_Line_1565='set AHST = 20+AHSTtol',
            Program_Line_1566='endif',
            Program_Line_1567='endif',
            Program_Line_1568='endif',
            Program_Line_1569='if (ComfStand == 17) && (ComfMod == 2)',
            Program_Line_1570='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1571='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1572='set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1573='elseif PMOT < ACSTall',
            Program_Line_1574='if CAT == 90',
            Program_Line_1575='set ACST = 24+ACSTtol',
            Program_Line_1576='elseif CAT == 80',
            Program_Line_1577='set ACST = 25+ACSTtol',
            Program_Line_1578='endif',
            Program_Line_1579='elseif PMOT > ACSTaul',
            Program_Line_1580='if CAT == 90',
            Program_Line_1581='set ACST = 26+ACSTtol',
            Program_Line_1582='elseif CAT == 80',
            Program_Line_1583='set ACST = 27+ACSTtol',
            Program_Line_1584='endif',
            Program_Line_1585='endif',
            Program_Line_1586='else',
            Program_Line_1587='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1588='set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1589='elseif PMOT < ACSTall',
            Program_Line_1590='if CAT == 90',
            Program_Line_1591='set ACST = 24+ACSTtol',
            Program_Line_1592='elseif CAT == 80',
            Program_Line_1593='set ACST = 25+ACSTtol',
            Program_Line_1594='endif',
            Program_Line_1595='elseif PMOT > ACSTaul',
            Program_Line_1596='if CAT == 90',
            Program_Line_1597='set ACST = 26+ACSTtol',
            Program_Line_1598='elseif CAT == 80',
            Program_Line_1599='set ACST = 27+ACSTtol',
            Program_Line_1600='endif',
            Program_Line_1601='endif',
            Program_Line_1602='endif',
            Program_Line_1603='endif',
            Program_Line_1604='if (ComfStand == 17) && (ComfMod == 2)',
            Program_Line_1605='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1606='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1607='set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1608='elseif PMOT < AHSTall',
            Program_Line_1609='if CAT == 90',
            Program_Line_1610='set AHST = 20+AHSTtol',
            Program_Line_1611='elseif CAT == 80',
            Program_Line_1612='set AHST = 19+AHSTtol',
            Program_Line_1613='endif',
            Program_Line_1614='elseif PMOT > AHSTaul',
            Program_Line_1615='if CAT == 90',
            Program_Line_1616='set AHST = 23+AHSTtol',
            Program_Line_1617='elseif CAT == 80',
            Program_Line_1618='set AHST = 22+AHSTtol',
            Program_Line_1619='endif',
            Program_Line_1620='endif',
            Program_Line_1621='else',
            Program_Line_1622='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1623='set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1624='elseif PMOT < AHSTall',
            Program_Line_1625='if CAT == 90',
            Program_Line_1626='set AHST = 20+AHSTtol',
            Program_Line_1627='elseif CAT == 80',
            Program_Line_1628='set AHST = 19+AHSTtol',
            Program_Line_1629='endif',
            Program_Line_1630='elseif PMOT > AHSTaul',
            Program_Line_1631='if CAT == 90',
            Program_Line_1632='set AHST = 23+AHSTtol',
            Program_Line_1633='elseif CAT == 80',
            Program_Line_1634='set AHST = 22+AHSTtol',
            Program_Line_1635='endif',
            Program_Line_1636='endif',
            Program_Line_1637='endif',
            Program_Line_1638='endif',
            Program_Line_1639='if (ComfStand == 17) && (ComfMod == 3)',
            Program_Line_1640='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1641='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1642='set ACST = PMOT*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1643='elseif PMOT < ACSTall',
            Program_Line_1644='set ACST = ACSTall*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1645='elseif PMOT > ACSTaul',
            Program_Line_1646='set ACST = ACSTaul*0.48+13.9+ACSToffset+ACSTtol',
            Program_Line_1647='endif',
            Program_Line_1648='else',
            Program_Line_1649='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1650='set ACST = PMOT*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1651='elseif PMOT < ACSTall',
            Program_Line_1652='set ACST = ACSTall*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1653='elseif PMOT > ACSTaul',
            Program_Line_1654='set ACST = ACSTaul*0.59+9.6+ACSToffset+ACSTtol',
            Program_Line_1655='endif',
            Program_Line_1656='endif',
            Program_Line_1657='endif',
            Program_Line_1658='if (ComfStand == 17) && (ComfMod == 3)',
            Program_Line_1659='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1660='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1661='set AHST = PMOT*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1662='elseif PMOT < AHSTall',
            Program_Line_1663='set AHST = AHSTall*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1664='elseif PMOT > AHSTaul',
            Program_Line_1665='set AHST = AHSTaul*0.48+13.9+AHSToffset+AHSTtol',
            Program_Line_1666='endif',
            Program_Line_1667='else',
            Program_Line_1668='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1669='set AHST = PMOT*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1670='elseif PMOT < AHSTall',
            Program_Line_1671='set AHST = AHSTall*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1672='elseif PMOT > AHSTaul',
            Program_Line_1673='set AHST = AHSTaul*0.59+9.6+AHSToffset+AHSTtol',
            Program_Line_1674='endif',
            Program_Line_1675='endif',
            Program_Line_1676='endif',
            Program_Line_1677='if (ComfStand == 18) && (ComfMod == 1)',
            Program_Line_1678='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1679='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1680='set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1681='else',
            Program_Line_1682='set ACST = 25+ACSTtol',
            Program_Line_1683='endif',
            Program_Line_1684='else',
            Program_Line_1685='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1686='set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1687='else',
            Program_Line_1688='set ACST = 25+ACSTtol',
            Program_Line_1689='endif',
            Program_Line_1690='endif',
            Program_Line_1691='endif',
            Program_Line_1692='if (ComfStand == 18) && (ComfMod == 1)',
            Program_Line_1693='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1694='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1695='set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1696='else',
            Program_Line_1697='set AHST = 20+AHSTtol',
            Program_Line_1698='endif',
            Program_Line_1699='else',
            Program_Line_1700='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1701='set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1702='else',
            Program_Line_1703='set AHST = 20+AHSTtol',
            Program_Line_1704='endif',
            Program_Line_1705='endif',
            Program_Line_1706='endif',
            Program_Line_1707='if (ComfStand == 18) && (ComfMod == 2)',
            Program_Line_1708='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1709='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1710='set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1711='elseif PMOT < ACSTall',
            Program_Line_1712='if CAT == 90',
            Program_Line_1713='set ACST = 24+ACSTtol',
            Program_Line_1714='elseif CAT == 80',
            Program_Line_1715='set ACST = 25+ACSTtol',
            Program_Line_1716='endif',
            Program_Line_1717='elseif PMOT > ACSTaul',
            Program_Line_1718='if CAT == 90',
            Program_Line_1719='set ACST = 26+ACSTtol',
            Program_Line_1720='elseif CAT == 80',
            Program_Line_1721='set ACST = 27+ACSTtol',
            Program_Line_1722='endif',
            Program_Line_1723='endif',
            Program_Line_1724='else',
            Program_Line_1725='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1726='set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1727='elseif PMOT < ACSTall',
            Program_Line_1728='if CAT == 90',
            Program_Line_1729='set ACST = 24+ACSTtol',
            Program_Line_1730='elseif CAT == 80',
            Program_Line_1731='set ACST = 25+ACSTtol',
            Program_Line_1732='endif',
            Program_Line_1733='elseif PMOT > ACSTaul',
            Program_Line_1734='if CAT == 90',
            Program_Line_1735='set ACST = 26+ACSTtol',
            Program_Line_1736='elseif CAT == 80',
            Program_Line_1737='set ACST = 27+ACSTtol',
            Program_Line_1738='endif',
            Program_Line_1739='endif',
            Program_Line_1740='endif',
            Program_Line_1741='endif',
            Program_Line_1742='if (ComfStand == 18) && (ComfMod == 2)',
            Program_Line_1743='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1744='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1745='set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1746='elseif PMOT < AHSTall',
            Program_Line_1747='if CAT == 90',
            Program_Line_1748='set AHST = 20+AHSTtol',
            Program_Line_1749='elseif CAT == 80',
            Program_Line_1750='set AHST = 19+AHSTtol',
            Program_Line_1751='endif',
            Program_Line_1752='elseif PMOT > AHSTaul',
            Program_Line_1753='if CAT == 90',
            Program_Line_1754='set AHST = 23+AHSTtol',
            Program_Line_1755='elseif CAT == 80',
            Program_Line_1756='set AHST = 22+AHSTtol',
            Program_Line_1757='endif',
            Program_Line_1758='endif',
            Program_Line_1759='else',
            Program_Line_1760='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1761='set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1762='elseif PMOT < AHSTall',
            Program_Line_1763='if CAT == 90',
            Program_Line_1764='set AHST = 20+AHSTtol',
            Program_Line_1765='elseif CAT == 80',
            Program_Line_1766='set AHST = 19+AHSTtol',
            Program_Line_1767='endif',
            Program_Line_1768='elseif PMOT > AHSTaul',
            Program_Line_1769='if CAT == 90',
            Program_Line_1770='set AHST = 23+AHSTtol',
            Program_Line_1771='elseif CAT == 80',
            Program_Line_1772='set AHST = 22+AHSTtol',
            Program_Line_1773='endif',
            Program_Line_1774='endif',
            Program_Line_1775='endif',
            Program_Line_1776='endif',
            Program_Line_1777='if (ComfStand == 18) && (ComfMod == 3)',
            Program_Line_1778='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1779='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1780='set ACST = PMOT*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1781='elseif PMOT < ACSTall',
            Program_Line_1782='set ACST = ACSTall*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1783='elseif PMOT > ACSTaul',
            Program_Line_1784='set ACST = ACSTaul*0.84+5.3+ACSToffset+ACSTtol',
            Program_Line_1785='endif',
            Program_Line_1786='else',
            Program_Line_1787='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1788='set ACST = PMOT*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1789='elseif PMOT < ACSTall',
            Program_Line_1790='set ACST = ACSTall*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1791='elseif PMOT > ACSTaul',
            Program_Line_1792='set ACST = ACSTaul*0.96-3.6+ACSToffset+ACSTtol',
            Program_Line_1793='endif',
            Program_Line_1794='endif',
            Program_Line_1795='endif',
            Program_Line_1796='if (ComfStand == 18) && (ComfMod == 3)',
            Program_Line_1797='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1798='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1799='set AHST = PMOT*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1800='elseif PMOT < AHSTall',
            Program_Line_1801='set AHST = AHSTall*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1802='elseif PMOT > AHSTaul',
            Program_Line_1803='set AHST = AHSTaul*0.84+5.3+AHSToffset+AHSTtol',
            Program_Line_1804='endif',
            Program_Line_1805='else',
            Program_Line_1806='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1807='set AHST = PMOT*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1808='elseif PMOT < AHSTall',
            Program_Line_1809='set AHST = AHSTall*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1810='elseif PMOT > AHSTaul',
            Program_Line_1811='set AHST = AHSTaul*0.96-3.6+AHSToffset+AHSTtol',
            Program_Line_1812='endif',
            Program_Line_1813='endif',
            Program_Line_1814='endif',
            Program_Line_1815='if (ComfStand == 19) && (ComfMod == 1)',
            Program_Line_1816='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1817='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1818='set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1819='else',
            Program_Line_1820='set ACST = 25+ACSTtol',
            Program_Line_1821='endif',
            Program_Line_1822='else',
            Program_Line_1823='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1824='set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1825='else',
            Program_Line_1826='set ACST = 25+ACSTtol',
            Program_Line_1827='endif',
            Program_Line_1828='endif',
            Program_Line_1829='endif',
            Program_Line_1830='if (ComfStand == 19) && (ComfMod == 1)',
            Program_Line_1831='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1832='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1833='set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1834='else',
            Program_Line_1835='set AHST = 20+AHSTtol',
            Program_Line_1836='endif',
            Program_Line_1837='else',
            Program_Line_1838='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1839='set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1840='else',
            Program_Line_1841='set AHST = 20+AHSTtol',
            Program_Line_1842='endif',
            Program_Line_1843='endif',
            Program_Line_1844='endif',
            Program_Line_1845='if (ComfStand == 19) && (ComfMod == 2)',
            Program_Line_1846='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1847='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1848='set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1849='elseif PMOT < ACSTall',
            Program_Line_1850='if CAT == 90',
            Program_Line_1851='set ACST = 24+ACSTtol',
            Program_Line_1852='elseif CAT == 80',
            Program_Line_1853='set ACST = 25+ACSTtol',
            Program_Line_1854='endif',
            Program_Line_1855='elseif PMOT > ACSTaul',
            Program_Line_1856='if CAT == 90',
            Program_Line_1857='set ACST = 26+ACSTtol',
            Program_Line_1858='elseif CAT == 80',
            Program_Line_1859='set ACST = 27+ACSTtol',
            Program_Line_1860='endif',
            Program_Line_1861='endif',
            Program_Line_1862='else',
            Program_Line_1863='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1864='set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1865='elseif PMOT < ACSTall',
            Program_Line_1866='if CAT == 90',
            Program_Line_1867='set ACST = 24+ACSTtol',
            Program_Line_1868='elseif CAT == 80',
            Program_Line_1869='set ACST = 25+ACSTtol',
            Program_Line_1870='endif',
            Program_Line_1871='elseif PMOT > ACSTaul',
            Program_Line_1872='if CAT == 90',
            Program_Line_1873='set ACST = 26+ACSTtol',
            Program_Line_1874='elseif CAT == 80',
            Program_Line_1875='set ACST = 27+ACSTtol',
            Program_Line_1876='endif',
            Program_Line_1877='endif',
            Program_Line_1878='endif',
            Program_Line_1879='endif',
            Program_Line_1880='if (ComfStand == 19) && (ComfMod == 2)',
            Program_Line_1881='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1882='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1883='set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1884='elseif PMOT < AHSTall',
            Program_Line_1885='if CAT == 90',
            Program_Line_1886='set AHST = 20+AHSTtol',
            Program_Line_1887='elseif CAT == 80',
            Program_Line_1888='set AHST = 19+AHSTtol',
            Program_Line_1889='endif',
            Program_Line_1890='elseif PMOT > AHSTaul',
            Program_Line_1891='if CAT == 90',
            Program_Line_1892='set AHST = 23+AHSTtol',
            Program_Line_1893='elseif CAT == 80',
            Program_Line_1894='set AHST = 22+AHSTtol',
            Program_Line_1895='endif',
            Program_Line_1896='endif',
            Program_Line_1897='else',
            Program_Line_1898='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1899='set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1900='elseif PMOT < AHSTall',
            Program_Line_1901='if CAT == 90',
            Program_Line_1902='set AHST = 20+AHSTtol',
            Program_Line_1903='elseif CAT == 80',
            Program_Line_1904='set AHST = 19+AHSTtol',
            Program_Line_1905='endif',
            Program_Line_1906='elseif PMOT > AHSTaul',
            Program_Line_1907='if CAT == 90',
            Program_Line_1908='set AHST = 23+AHSTtol',
            Program_Line_1909='elseif CAT == 80',
            Program_Line_1910='set AHST = 22+AHSTtol',
            Program_Line_1911='endif',
            Program_Line_1912='endif',
            Program_Line_1913='endif',
            Program_Line_1914='endif',
            Program_Line_1915='if (ComfStand == 19) && (ComfMod == 3)',
            Program_Line_1916='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1917='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1918='set ACST = PMOT*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1919='elseif PMOT < ACSTall',
            Program_Line_1920='set ACST = ACSTall*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1921='elseif PMOT > ACSTaul',
            Program_Line_1922='set ACST = ACSTaul*0.27+17.9+ACSToffset+ACSTtol',
            Program_Line_1923='endif',
            Program_Line_1924='else',
            Program_Line_1925='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1926='set ACST = PMOT*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1927='elseif PMOT < ACSTall',
            Program_Line_1928='set ACST = ACSTall*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1929='elseif PMOT > ACSTaul',
            Program_Line_1930='set ACST = ACSTaul*0.53+10.3+ACSToffset+ACSTtol',
            Program_Line_1931='endif',
            Program_Line_1932='endif',
            Program_Line_1933='endif',
            Program_Line_1934='if (ComfStand == 19) && (ComfMod == 3)',
            Program_Line_1935='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1936='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1937='set AHST = PMOT*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1938='elseif PMOT < AHSTall',
            Program_Line_1939='set AHST = AHSTall*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1940='elseif PMOT > AHSTaul',
            Program_Line_1941='set AHST = AHSTaul*0.27+17.9+AHSToffset+AHSTtol',
            Program_Line_1942='endif',
            Program_Line_1943='else',
            Program_Line_1944='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1945='set AHST = PMOT*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1946='elseif PMOT < AHSTall',
            Program_Line_1947='set AHST = AHSTall*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1948='elseif PMOT > AHSTaul',
            Program_Line_1949='set AHST = AHSTaul*0.53+10.3+AHSToffset+AHSTtol',
            Program_Line_1950='endif',
            Program_Line_1951='endif',
            Program_Line_1952='endif',
            Program_Line_1953='if (ComfStand == 20) && (ComfMod == 1)',
            Program_Line_1954='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1955='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1956='set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_1957='else',
            Program_Line_1958='set ACST = 25+ACSTtol',
            Program_Line_1959='endif',
            Program_Line_1960='else',
            Program_Line_1961='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1962='set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_1963='else',
            Program_Line_1964='set ACST = 25+ACSTtol',
            Program_Line_1965='endif',
            Program_Line_1966='endif',
            Program_Line_1967='endif',
            Program_Line_1968='if (ComfStand == 20) && (ComfMod == 1)',
            Program_Line_1969='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1970='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1971='set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_1972='else',
            Program_Line_1973='set AHST = 20+AHSTtol',
            Program_Line_1974='endif',
            Program_Line_1975='else',
            Program_Line_1976='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1977='set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_1978='else',
            Program_Line_1979='set AHST = 20+AHSTtol',
            Program_Line_1980='endif',
            Program_Line_1981='endif',
            Program_Line_1982='endif',
            Program_Line_1983='if (ComfStand == 20) && (ComfMod == 2)',
            Program_Line_1984='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_1985='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1986='set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_1987='elseif PMOT < ACSTall',
            Program_Line_1988='if CAT == 90',
            Program_Line_1989='set ACST = 24+ACSTtol',
            Program_Line_1990='elseif CAT == 80',
            Program_Line_1991='set ACST = 25+ACSTtol',
            Program_Line_1992='endif',
            Program_Line_1993='elseif PMOT > ACSTaul',
            Program_Line_1994='if CAT == 90',
            Program_Line_1995='set ACST = 26+ACSTtol',
            Program_Line_1996='elseif CAT == 80',
            Program_Line_1997='set ACST = 27+ACSTtol',
            Program_Line_1998='endif',
            Program_Line_1999='endif',
            Program_Line_2000='else',
            Program_Line_2001='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2002='set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2003='elseif PMOT < ACSTall',
            Program_Line_2004='if CAT == 90',
            Program_Line_2005='set ACST = 24+ACSTtol',
            Program_Line_2006='elseif CAT == 80',
            Program_Line_2007='set ACST = 25+ACSTtol',
            Program_Line_2008='endif',
            Program_Line_2009='elseif PMOT > ACSTaul',
            Program_Line_2010='if CAT == 90',
            Program_Line_2011='set ACST = 26+ACSTtol',
            Program_Line_2012='elseif CAT == 80',
            Program_Line_2013='set ACST = 27+ACSTtol',
            Program_Line_2014='endif',
            Program_Line_2015='endif',
            Program_Line_2016='endif',
            Program_Line_2017='endif',
            Program_Line_2018='if (ComfStand == 20) && (ComfMod == 2)',
            Program_Line_2019='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_2020='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2021='set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2022='elseif PMOT < AHSTall',
            Program_Line_2023='if CAT == 90',
            Program_Line_2024='set AHST = 20+AHSTtol',
            Program_Line_2025='elseif CAT == 80',
            Program_Line_2026='set AHST = 19+AHSTtol',
            Program_Line_2027='endif',
            Program_Line_2028='elseif PMOT > AHSTaul',
            Program_Line_2029='if CAT == 90',
            Program_Line_2030='set AHST = 23+AHSTtol',
            Program_Line_2031='elseif CAT == 80',
            Program_Line_2032='set AHST = 22+AHSTtol',
            Program_Line_2033='endif',
            Program_Line_2034='endif',
            Program_Line_2035='else',
            Program_Line_2036='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2037='set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2038='elseif PMOT < AHSTall',
            Program_Line_2039='if CAT == 90',
            Program_Line_2040='set AHST = 20+AHSTtol',
            Program_Line_2041='elseif CAT == 80',
            Program_Line_2042='set AHST = 19+AHSTtol',
            Program_Line_2043='endif',
            Program_Line_2044='elseif PMOT > AHSTaul',
            Program_Line_2045='if CAT == 90',
            Program_Line_2046='set AHST = 23+AHSTtol',
            Program_Line_2047='elseif CAT == 80',
            Program_Line_2048='set AHST = 22+AHSTtol',
            Program_Line_2049='endif',
            Program_Line_2050='endif',
            Program_Line_2051='endif',
            Program_Line_2052='endif',
            Program_Line_2053='if (ComfStand == 20) && (ComfMod == 3)',
            Program_Line_2054='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_2055='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2056='set ACST = PMOT*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_2057='elseif PMOT < ACSTall',
            Program_Line_2058='set ACST = ACSTall*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_2059='elseif PMOT > ACSTaul',
            Program_Line_2060='set ACST = ACSTaul*0.38+15.7+ACSToffset+ACSTtol',
            Program_Line_2061='endif',
            Program_Line_2062='else',
            Program_Line_2063='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2064='set ACST = PMOT*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2065='elseif PMOT < ACSTall',
            Program_Line_2066='set ACST = ACSTall*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2067='elseif PMOT > ACSTaul',
            Program_Line_2068='set ACST = ACSTaul*0.47+9.07+ACSToffset+ACSTtol',
            Program_Line_2069='endif',
            Program_Line_2070='endif',
            Program_Line_2071='endif',
            Program_Line_2072='if (ComfStand == 20) && (ComfMod == 3)',
            Program_Line_2073='if (DayOfYear <= 121) || (DayOfYear > 295)',
            Program_Line_2074='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2075='set AHST = PMOT*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2076='elseif PMOT < AHSTall',
            Program_Line_2077='set AHST = AHSTall*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2078='elseif PMOT > AHSTaul',
            Program_Line_2079='set AHST = AHSTaul*0.38+15.7+AHSToffset+AHSTtol',
            Program_Line_2080='endif',
            Program_Line_2081='else',
            Program_Line_2082='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2083='set AHST = PMOT*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2084='elseif PMOT < AHSTall',
            Program_Line_2085='set AHST = AHSTall*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2086='elseif PMOT > AHSTaul',
            Program_Line_2087='set AHST = AHSTaul*0.47+9.07+AHSToffset+AHSTtol',
            Program_Line_2088='endif',
            Program_Line_2089='endif',
            Program_Line_2090='endif',
            Program_Line_2091='if (ComfStand == 21) && (ComfMod == 2)',
            Program_Line_2092='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2093='set ACST = PMOT*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2094='elseif CAT==80',
            Program_Line_2095='if PMOT < ACSTall',
            Program_Line_2096='set ACST = 25+ACSTtol',
            Program_Line_2097='elseif PMOT > ACSTaul',
            Program_Line_2098='set ACST = 27+ACSTtol',
            Program_Line_2099='endif',
            Program_Line_2100='elseif CAT==90',
            Program_Line_2101='if PMOT < ACSTall',
            Program_Line_2102='set ACST = 24+ACSTtol',
            Program_Line_2103='elseif PMOT > ACSTaul',
            Program_Line_2104='set ACST = 26+ACSTtol',
            Program_Line_2105='endif',
            Program_Line_2106='endif',
            Program_Line_2107='endif',
            Program_Line_2108='if (ComfStand == 21) && (ComfMod == 2)',
            Program_Line_2109='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2110='set AHST = PMOT*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2111='elseif CAT==80',
            Program_Line_2112='if PMOT < AHSTall',
            Program_Line_2113='set AHST = 19+AHSTtol',
            Program_Line_2114='elseif PMOT > AHSTaul',
            Program_Line_2115='set AHST = 22+AHSTtol',
            Program_Line_2116='endif',
            Program_Line_2117='elseif CAT==90',
            Program_Line_2118='if PMOT < AHSTall',
            Program_Line_2119='set AHST = 20+AHSTtol',
            Program_Line_2120='elseif PMOT > AHSTaul',
            Program_Line_2121='set AHST = 23+AHSTtol',
            Program_Line_2122='endif',
            Program_Line_2123='endif',
            Program_Line_2124='endif',
            Program_Line_2125='if (ComfStand == 21) && (ComfMod == 3)',
            Program_Line_2126='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_2127='set ACST = PMOT*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2128='elseif PMOT < ACSTall',
            Program_Line_2129='set ACST = ACSTall*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2130='elseif PMOT > ACSTaul',
            Program_Line_2131='set ACST = ACSTaul*0.678+13.51+ACSToffset+ACSTtol',
            Program_Line_2132='endif',
            Program_Line_2133='endif',
            Program_Line_2134='if (ComfStand == 21) && (ComfMod == 3)',
            Program_Line_2135='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_2136='set AHST = PMOT*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2137='elseif PMOT < AHSTall',
            Program_Line_2138='set AHST = AHSTall*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2139='elseif PMOT > AHSTaul',
            Program_Line_2140='set AHST = AHSTaul*0.678+13.51+AHSToffset+AHSTtol',
            Program_Line_2141='endif',
            Program_Line_2142='endif',
            Program_Line_2143='if (ComfStand == 22)',
            Program_Line_2144='if CoolingSeason == 1',
            Program_Line_2145='if (CAT==3)',
            Program_Line_2146='set ACST = 24.5+2.5+ACSTtol',
            Program_Line_2147='elseif (CAT==2)',
            Program_Line_2148='set ACST = 24.5+1.5+ACSTtol',
            Program_Line_2149='elseif (CAT==1)',
            Program_Line_2150='set ACST = 24.5+1+ACSTtol',
            Program_Line_2151='endif',
            Program_Line_2152='else',
            Program_Line_2153='if (CAT==3)',
            Program_Line_2154='set ACST = 22+3+ACSTtol',
            Program_Line_2155='elseif (CAT==2)',
            Program_Line_2156='set ACST = 22+2+ACSTtol',
            Program_Line_2157='elseif (CAT==1)',
            Program_Line_2158='set ACST = 22+1+ACSTtol',
            Program_Line_2159='endif',
            Program_Line_2160='endif',
            Program_Line_2161='endif',
            Program_Line_2162='if (ComfStand == 22)',
            Program_Line_2163='if CoolingSeason == 1',
            Program_Line_2164='if (CAT==3)',
            Program_Line_2165='set AHST = 24.5-2.5+AHSTtol',
            Program_Line_2166='elseif (CAT==2)',
            Program_Line_2167='set AHST = 24.5-1.5+AHSTtol',
            Program_Line_2168='elseif (CAT==1)',
            Program_Line_2169='set AHST = 24.5-1+AHSTtol',
            Program_Line_2170='endif',
            Program_Line_2171='else',
            Program_Line_2172='if (CAT==3)',
            Program_Line_2173='set AHST = 22-3+AHSTtol',
            Program_Line_2174='elseif (CAT==2)',
            Program_Line_2175='set AHST = 22-2+AHSTtol',
            Program_Line_2176='elseif (CAT==1)',
            Program_Line_2177='set AHST = 22-1+AHSTtol',
            Program_Line_2178='endif',
            Program_Line_2179='endif',
            Program_Line_2180='endif',
            Program_Line_2181='set ACSTx2 = ACST*SetpointAcc',
            Program_Line_2182='set AHSTx2 = AHST*SetpointAcc',
            Program_Line_2183='set roundedACSTx2 = @Round ACSTx2',
            Program_Line_2184='set roundedAHSTx2 = @Round AHSTx2',
            Program_Line_2185='if roundedACSTx2 - ACSTx2 < 0',
            Program_Line_2186='set ACSTroundedUp = 0',
            Program_Line_2187='else',
            Program_Line_2188='set ACSTroundedUp = 1',
            Program_Line_2189='endif',
            Program_Line_2190='if roundedAHSTx2 - AHSTx2 < 0',
            Program_Line_2191='set AHSTroundedUp = 0',
            Program_Line_2192='else',
            Program_Line_2193='set AHSTroundedUp = 1',
            Program_Line_2194='endif',
            Program_Line_2195='if ACSTroundedUp == 0',
            Program_Line_2196='set roundedACST = roundedACSTx2 / SetpointAcc',
            Program_Line_2197='else',
            Program_Line_2198='set roundedACST = (roundedACSTx2 - 1) / SetpointAcc',
            Program_Line_2199='endif',
            Program_Line_2200='if AHSTroundedUp == 0',
            Program_Line_2201='set roundedAHST = (roundedAHSTx2 + 1) / SetpointAcc',
            Program_Line_2202='else',
            Program_Line_2203='set roundedAHST = roundedAHSTx2 / SetpointAcc',
            Program_Line_2204='endif',
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
        verboseMode: bool = True
):
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
    elif self.spacelist_use:
        # space_list = []
        # for people in self.idf1.idfobjects['PEOPLE']:
        #     for spacelist in [i for i in self.idf1.idfobjects['SPACELIST'] if i.Name == people.Zone_or_ZoneList_or_Space_or_SpaceList_Name]:
        #         for space in [i for i in self.idf1.idfobjects['SPACE'] if i.Space_Type == spacelist.Name]:
        #             space_list.append(f'{space.Name} {people.Name}')
        # ppl_key_name = space_list[0]
        ppl_key_name = self.spacenames_for_ems_uniquekey_people[0]
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

    if self.spacelist_use:
        # occ_count_keys = [f'{i} People' for i in self.ems_objs_key]
        occ_count_keys = [i for i in self.spacenames_for_ems_uniquekey_people]
    else:
        occ_count_keys = [f'People {i}' for i in self.ems_objs_key]

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

    # Make average for operative temperature
    op_temp_sensors = [
        i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:Sensor'] if
        'OpT' in i.Name and
        i.OutputVariable_or_OutputMeter_Index_Key_Name in self.zonenames_orig
    ]
    op_temp_sum = '+'.join(op_temp_sensors)

    if f'OpTempBuildAvg' in gvs_all:
        if verboseMode:
            print(f'Not added - MakeOpTempBuildAvg GlobalVariable')
    else:
        self.idf1.newidfobject(
            key='EnergyManagementSystem:GlobalVariable',
            Erl_Variable_1_Name=f'OpTempBuildAvg'
        )
        if verboseMode:
            print(f'Added - OpTempBuildAvg GlobalVariable')

    if f'MakeOpTempBuildAvg' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager']]:
        if verboseMode:
            print(f'Not added - MakeOpTempBuildAvg ProgramCallingManager')
    else:
        self.idf1.newidfobject(
            key='EnergyManagementSystem:ProgramCallingManager',
            Name=f'MakeOpTempBuildAvg',
            EnergyPlus_Model_Calling_Point='BeginTimestepBeforePredictor',
            Program_Name_1=f'MakeOpTempBuildAvg',
        )
        if verboseMode:
            print(f'Added - MakeOpTempBuildAvg ProgramCallingManager')

    if f'MakeOpTempBuildAvg' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:Program']]:
        if verboseMode:
            print(f'Not added - MakeOpTempBuildAvg Program')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Program',
            Name=f'MakeOpTempBuildAvg',
            Program_Line_1=f'set OpTempBuildAvgNum = ' + op_temp_sum,
            Program_Line_2=f'set OpTempBuildAvgDen = ' + str(len(op_temp_sensors)),
            Program_Line_3=f'set OpTempBuildAvg = OpTempBuildAvgNum/OpTempBuildAvgDen'
        )
        if verboseMode:
            print(f'Added - MakeOpTempBuildAvg Program')

    if f'OpTemp_Building_Average' in [i.Name for i in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']]:
        if verboseMode:
            print(f'Not added - OpTemp_Building_Average EMS OutputVariable')
    else:
        self.idf1.newidfobject(
            key='EnergyManagementSystem:OutputVariable',
            Name=f'Zone Operative Temperature_Building_Average',
            EMS_Variable_Name=f'OpTempBuildAvg',
            Type_of_Data_in_Variable='Averaged',
            Update_Frequency='ZoneTimestep',
            Units='C'
        )
        if verboseMode:
            print(f'Added - Zone Operative Temperature_Building_Average EMS OutputVariable')
