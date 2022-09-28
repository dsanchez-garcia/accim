"""Add EMS objects in common to both ExistingHVAC and VRFsystem."""


def addEMSProgramsBase(self, ScriptType: str = None, verboseMode: bool = True):
    """
    Add EMS programs for Base accim.

    Checks if some programs objects are already
    in the model, and otherwise adds them.
    :param verboseMode:
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
            Program_Line_33='endif',
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
            Program_Line_1='if ComfStand == 1',
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
            Program_Line_73='else',
            Program_Line_74='set ACSTaul = 50',
            Program_Line_75='set ACSTall = 50',
            Program_Line_76='set AHSTaul = 50',
            Program_Line_77='set AHSTall = 50',
            Program_Line_78='endif',
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
            Program_Line_1='if (ComfStand == 1 )',
            Program_Line_2='if (CAT == 1)',
            Program_Line_3='set ACSToffset = 2',
            Program_Line_4='set AHSToffset = -3',
            Program_Line_5='elseif (CAT == 2)',
            Program_Line_6='set ACSToffset = 3',
            Program_Line_7='set AHSToffset = -4',
            Program_Line_8='elseif (CAT == 3)',
            Program_Line_9='set ACSToffset = 4',
            Program_Line_10='set AHSToffset = -5',
            Program_Line_11='endif',
            Program_Line_12='elseif ComfStand == 2 || ComfStand == 3 || ComfStand == 11',
            Program_Line_13='if (CAT == 90)',
            Program_Line_14='set ACSToffset = 2.5',
            Program_Line_15='set AHSToffset = -2.5',
            Program_Line_16='elseif (CAT == 80)',
            Program_Line_17='set ACSToffset = 3.5',
            Program_Line_18='set AHSToffset = -3.5',
            Program_Line_19='endif',
            Program_Line_20='elseif (ComfStand == 4 ) || (ComfStand == 5) || (ComfStand == 6)',
            Program_Line_21='set ACSToffset = 0',
            Program_Line_22='set AHSToffset = 0',
            Program_Line_23='elseif (ComfStand == 7)',
            Program_Line_24='if (CAT == 90)',
            Program_Line_25='set ACSToffset = 2.4',
            Program_Line_26='set AHSToffset = -2.4',
            Program_Line_27='elseif (CAT == 85)',
            Program_Line_28='set ACSToffset = 3.3',
            Program_Line_29='set AHSToffset = -3.3',
            Program_Line_30='elseif (CAT == 80)',
            Program_Line_31='set ACSToffset = 4.1',
            Program_Line_32='set AHSToffset = -4.1',
            Program_Line_33='endif',
            Program_Line_34='elseif (ComfStand == 8)',
            Program_Line_35='if (CAT == 90)',
            Program_Line_36='set ACSToffset = 3.5',
            Program_Line_37='set AHSToffset = -3.5',
            Program_Line_38='elseif (CAT == 85)',
            Program_Line_39='set ACSToffset = 4.8',
            Program_Line_40='set AHSToffset = -4.8',
            Program_Line_41='elseif (CAT == 80)',
            Program_Line_42='set ACSToffset = 5.9',
            Program_Line_43='set AHSToffset = -5.9',
            Program_Line_44='endif',
            Program_Line_45='elseif ComfStand == 9 || ComfStand == 10',
            Program_Line_46='if (CAT == 90)',
            Program_Line_47='set ACSToffset = 2.15',
            Program_Line_48='set AHSToffset = -2.15',
            Program_Line_49='elseif (CAT == 80)',
            Program_Line_50='set ACSToffset = 3.6',
            Program_Line_51='set AHSToffset = -3.6',
            Program_Line_52='endif',
            Program_Line_53='elseif ComfStand == 12',
            Program_Line_54='if (CAT == 90)',
            Program_Line_55='set ACSToffset = 1.7',
            Program_Line_56='set AHSToffset = -1.7',
            Program_Line_57='elseif (CAT == 80)',
            Program_Line_58='set ACSToffset = 2.89',
            Program_Line_59='set AHSToffset = -2.89',
            Program_Line_60='endif',
            Program_Line_61='elseif ComfStand == 13',
            Program_Line_62='if (CAT == 90)',
            Program_Line_63='set ACSToffset = 3.45',
            Program_Line_64='set AHSToffset = -3.45',
            Program_Line_65='elseif (CAT == 80)',
            Program_Line_66='set ACSToffset = 4.55',
            Program_Line_67='set AHSToffset = -4.55',
            Program_Line_68='endif',
            Program_Line_69='elseif ComfStand == 14',
            Program_Line_70='if (CAT == 90)',
            Program_Line_71='set ACSToffset = 3.5',
            Program_Line_72='set AHSToffset = -3.5',
            Program_Line_73='elseif (CAT == 80)',
            Program_Line_74='set ACSToffset = 4.5',
            Program_Line_75='set AHSToffset = -4.5',
            Program_Line_76='endif',
            Program_Line_77='elseif ComfStand == 15',
            Program_Line_78='if (CAT == 90)',
            Program_Line_79='set ACSToffset = 2.8',
            Program_Line_80='set AHSToffset = -2.8',
            Program_Line_81='elseif (CAT == 80)',
            Program_Line_82='set ACSToffset = 3.8',
            Program_Line_83='set AHSToffset = -3.8',
            Program_Line_84='endif',
            Program_Line_85='elseif ComfStand == 16',
            Program_Line_86='if (CAT == 90)',
            Program_Line_87='set ACSToffset = 1.1',
            Program_Line_88='set AHSToffset = -1.1',
            Program_Line_89='elseif (CAT == 80)',
            Program_Line_90='set ACSToffset = 2.1',
            Program_Line_91='set AHSToffset = -2.1',
            Program_Line_92='endif',
            Program_Line_93='endif',
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
            Program_Line_1='if (ComfStand == 0) && (CurrentTime < 8)',
            Program_Line_2='set ACST = 27+ACSTtol',
            Program_Line_3='set AHST = 17+AHSTtol',
            Program_Line_4='elseif (ComfStand == 0) && (CurrentTime < 16)',
            Program_Line_5='set ACST = 25+ACSTtol',
            Program_Line_6='set AHST = 20+AHSTtol',
            Program_Line_7='elseif (ComfStand == 0) && (CurrentTime < 23)',
            Program_Line_8='set ACST = 25+ACSTtol',
            Program_Line_9='set AHST = 20+AHSTtol',
            Program_Line_10='elseif (ComfStand == 0) && (CurrentTime < 24)',
            Program_Line_11='set ACST = 27+ACSTtol',
            Program_Line_12='set AHST = 17+AHSTtol',
            Program_Line_13='endif',
            Program_Line_14='if (ComfStand == 1) && (ComfMod == 0)',
            Program_Line_15='if (DayOfYear >= 121) && (DayOfYear < 274)',
            Program_Line_16='if (CAT==1)',
            Program_Line_17='set ACST = 25.5+ACSTtol',
            Program_Line_18='elseif (CAT==2)',
            Program_Line_19='set ACST = 26+ACSTtol',
            Program_Line_20='elseif (CAT==3)',
            Program_Line_21='set ACST = 27+ACSTtol',
            Program_Line_22='endif',
            Program_Line_23='else',
            Program_Line_24='if (CAT==1)',
            Program_Line_25='set ACST = 25+ACSTtol',
            Program_Line_26='elseif (CAT==2)',
            Program_Line_27='set ACST = 25+ACSTtol',
            Program_Line_28='elseif (CAT==3)',
            Program_Line_29='set ACST = 25+ACSTtol',
            Program_Line_30='endif',
            Program_Line_31='endif',
            Program_Line_32='endif',
            Program_Line_33='if (ComfStand == 1) && (ComfMod == 0)',
            Program_Line_34='if (DayOfYear >= 121) && (DayOfYear < 274)',
            Program_Line_35='if (CAT==1)',
            Program_Line_36='set AHST = 23.5+AHSTtol',
            Program_Line_37='elseif (CAT==2)',
            Program_Line_38='set AHST = 23+AHSTtol',
            Program_Line_39='elseif (CAT==3)',
            Program_Line_40='set AHST = 22+AHSTtol',
            Program_Line_41='endif',
            Program_Line_42='else',
            Program_Line_43='if (CAT==1)',
            Program_Line_44='set AHST = 21+AHSTtol',
            Program_Line_45='elseif (CAT==2)',
            Program_Line_46='set AHST = 20+AHSTtol',
            Program_Line_47='elseif (CAT==3)',
            Program_Line_48='set AHST = 18+AHSTtol',
            Program_Line_49='endif',
            Program_Line_50='endif',
            Program_Line_51='endif',
            Program_Line_52='if (ComfStand == 1) && (ComfMod == 1)',
            Program_Line_53='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_54='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_55='elseif CurrentTime < 7',
            Program_Line_56='set ACST = 27+ACSTtol',
            Program_Line_57='elseif CurrentTime < 15',
            Program_Line_58='set ACST = 50',
            Program_Line_59='elseif CurrentTime < 23',
            Program_Line_60='set ACST = 25+ACSTtol',
            Program_Line_61='elseif CurrentTime < 24',
            Program_Line_62='set ACST = 27+ACSTtol',
            Program_Line_63='endif',
            Program_Line_64='endif',
            Program_Line_65='if (ComfStand == 1) && (ComfMod == 1)',
            Program_Line_66='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_67='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_68='elseif CurrentTime < 7',
            Program_Line_69='set AHST = 17+AHSTtol',
            Program_Line_70='elseif CurrentTime < 23',
            Program_Line_71='set AHST = 20+AHSTtol',
            Program_Line_72='elseif CurrentTime < 24',
            Program_Line_73='set AHST = 17+AHSTtol',
            Program_Line_74='endif',
            Program_Line_75='endif',
            Program_Line_76='if (ComfStand == 1) && (ComfMod == 2)',
            Program_Line_77='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_78='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_79='elseif (RMOT < ACSTall) && (CAT==1)',
            Program_Line_80='set ACST = 25+ACSTtol',
            Program_Line_81='elseif (RMOT > ACSTaul) && (CAT==1)',
            Program_Line_82='set ACST = 25.5+ACSTtol',
            Program_Line_83='elseif (RMOT < ACSTall) && (CAT==2)',
            Program_Line_84='set ACST = 25+ACSTtol',
            Program_Line_85='elseif (RMOT > ACSTaul) && (CAT==2)',
            Program_Line_86='set ACST = 26+ACSTtol',
            Program_Line_87='elseif (RMOT < ACSTall) && (CAT==3)',
            Program_Line_88='set ACST = 25+ACSTtol',
            Program_Line_89='elseif (RMOT > ACSTaul) && (CAT==3)',
            Program_Line_90='set ACST = 27+ACSTtol',
            Program_Line_91='endif',
            Program_Line_92='endif',
            Program_Line_93='if (ComfStand == 1) && (ComfMod == 2)',
            Program_Line_94='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_95='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_96='elseif (RMOT < AHSTall) && (CAT==1)',
            Program_Line_97='set AHST = 21+AHSTtol',
            Program_Line_98='elseif (RMOT > AHSTaul) && (CAT==1)',
            Program_Line_99='set AHST = 23.5+AHSTtol',
            Program_Line_100='elseif (RMOT < AHSTall) && (CAT==2)',
            Program_Line_101='set AHST = 20+AHSTtol',
            Program_Line_102='elseif (RMOT > AHSTaul) && (CAT==2)',
            Program_Line_103='set AHST = 23+AHSTtol',
            Program_Line_104='elseif (RMOT < AHSTall) && (CAT==3)',
            Program_Line_105='set AHST = 18+AHSTtol',
            Program_Line_106='elseif (RMOT > AHSTaul) && (CAT==3)',
            Program_Line_107='set AHST = 22+AHSTtol',
            Program_Line_108='endif',
            Program_Line_109='endif',
            Program_Line_110='if (ComfStand == 1) && (ComfMod == 3)',
            Program_Line_111='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_112='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_113='elseif RMOT < ACSTall',
            Program_Line_114='set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_115='elseif RMOT > ACSTaul',
            Program_Line_116='set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_117='endif',
            Program_Line_118='endif',
            Program_Line_119='if (ComfStand == 1) && (ComfMod == 3)',
            Program_Line_120='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_121='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_122='elseif RMOT < AHSTall',
            Program_Line_123='set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_124='elseif RMOT > AHSTaul',
            Program_Line_125='set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_126='endif',
            Program_Line_127='endif',
            Program_Line_128='if (ComfStand == 2) && (ComfMod == 0)',
            Program_Line_129='if (DayOfYear >= 121) && (DayOfYear < 274)',
            Program_Line_130='if (CAT==80)',
            Program_Line_131='set ACST = 28.35+ACSTtol',
            Program_Line_132='elseif (CAT==90)',
            Program_Line_133='set ACST = 27.42+ACSTtol',
            Program_Line_134='endif',
            Program_Line_135='else',
            Program_Line_136='if (CAT==80)',
            Program_Line_137='set ACST = 26.35+ACSTtol',
            Program_Line_138='elseif (CAT==90)',
            Program_Line_139='set ACST = 25.09+ACSTtol',
            Program_Line_140='endif',
            Program_Line_141='endif',
            Program_Line_142='endif',
            Program_Line_143='if (ComfStand == 2) && (ComfMod == 0)',
            Program_Line_144='if (DayOfYear >= 121) && (DayOfYear < 274)',
            Program_Line_145='if (CAT==80)',
            Program_Line_146='set AHST = 23.78+AHSTtol',
            Program_Line_147='elseif (CAT==90)',
            Program_Line_148='set AHST = 24.74+AHSTtol',
            Program_Line_149='endif',
            Program_Line_150='else',
            Program_Line_151='if (CAT==80)',
            Program_Line_152='set AHST = 20.1+AHSTtol',
            Program_Line_153='elseif (CAT==90)',
            Program_Line_154='set AHST = 21.44+AHSTtol',
            Program_Line_155='endif',
            Program_Line_156='endif',
            Program_Line_157='endif',
            Program_Line_158='if (ComfStand == 2) && (ComfMod == 1)',
            Program_Line_159='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_160='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_161='elseif CurrentTime < 7',
            Program_Line_162='set ACST = 27+ACSTtol',
            Program_Line_163='elseif CurrentTime < 15',
            Program_Line_164='set ACST = 50',
            Program_Line_165='elseif CurrentTime < 23',
            Program_Line_166='set ACST = 25+ACSTtol',
            Program_Line_167='elseif CurrentTime < 24',
            Program_Line_168='set ACST = 27+ACSTtol',
            Program_Line_169='endif',
            Program_Line_170='endif',
            Program_Line_171='if (ComfStand == 2) && (ComfMod == 1)',
            Program_Line_172='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_173='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_174='elseif CurrentTime < 7',
            Program_Line_175='set AHST = 17+AHSTtol',
            Program_Line_176='elseif CurrentTime < 23',
            Program_Line_177='set AHST = 20+AHSTtol',
            Program_Line_178='elseif CurrentTime < 24',
            Program_Line_179='set AHST = 17+AHSTtol',
            Program_Line_180='endif',
            Program_Line_181='endif',
            Program_Line_182='if (ComfStand == 2) && (ComfMod == 2)',
            Program_Line_183='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_184='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_185='elseif CAT==80',
            Program_Line_186='if PMOT < ACSTall',
            Program_Line_187='set ACST = 26.35+ACSTtol',
            Program_Line_188='elseif PMOT > ACSTaul',
            Program_Line_189='set ACST = 28.35+ACSTtol',
            Program_Line_190='endif',
            Program_Line_191='elseif CAT==90',
            Program_Line_192='if PMOT < ACSTall',
            Program_Line_193='set ACST = 25.09+ACSTtol',
            Program_Line_194='elseif PMOT > ACSTaul',
            Program_Line_195='set ACST = 27.42+ACSTtol',
            Program_Line_196='endif',
            Program_Line_197='endif',
            Program_Line_198='endif',
            Program_Line_199='if (ComfStand == 2) && (ComfMod == 2)',
            Program_Line_200='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_201='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_202='elseif CAT==80',
            Program_Line_203='if PMOT < AHSTall',
            Program_Line_204='set AHST = 20.1+AHSTtol',
            Program_Line_205='elseif PMOT > AHSTaul',
            Program_Line_206='set AHST = 23.78+AHSTtol',
            Program_Line_207='endif',
            Program_Line_208='elseif CAT==90',
            Program_Line_209='if PMOT < AHSTall',
            Program_Line_210='set AHST = 21.44+AHSTtol',
            Program_Line_211='elseif PMOT > AHSTaul',
            Program_Line_212='set AHST = 24.74+AHSTtol',
            Program_Line_213='endif',
            Program_Line_214='endif',
            Program_Line_215='endif',
            Program_Line_216='if (ComfStand == 2) && (ComfMod == 3)',
            Program_Line_217='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_218='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_219='elseif PMOT < ACSTall',
            Program_Line_220='set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_221='elseif PMOT > ACSTaul',
            Program_Line_222='set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_223='endif',
            Program_Line_224='endif',
            Program_Line_225='if (ComfStand == 2) && (ComfMod == 3)',
            Program_Line_226='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_227='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_228='elseif PMOT < AHSTall',
            Program_Line_229='set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_230='elseif PMOT > AHSTaul',
            Program_Line_231='set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_232='endif',
            Program_Line_233='endif',
            Program_Line_234='if (ComfStand == 3) && (ComfMod == 0)',
            Program_Line_235='if (CAT==80)',
            Program_Line_236='set ACST = 28+ACSTtol',
            Program_Line_237='elseif (CAT==90)',
            Program_Line_238='set ACST = 27+ACSTtol',
            Program_Line_239='endif',
            Program_Line_240='endif',
            Program_Line_241='if (ComfStand == 3) && (ComfMod == 0)',
            Program_Line_242='if (CAT==80)',
            Program_Line_243='set AHST = 18+AHSTtol',
            Program_Line_244='elseif (CAT==90)',
            Program_Line_245='set AHST = 19+AHSTtol',
            Program_Line_246='endif',
            Program_Line_247='endif',
            Program_Line_248='if (ComfStand == 3) && (ComfMod == 1)',
            Program_Line_249='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_250='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_251='elseif CAT==80',
            Program_Line_252='if PMOT < ACSTall',
            Program_Line_253='set ACST = 28+ACSTtol',
            Program_Line_254='elseif PMOT > ACSTaul',
            Program_Line_255='set ACST = 28+ACSTtol',
            Program_Line_256='endif',
            Program_Line_257='elseif CAT==90',
            Program_Line_258='if PMOT < ACSTall',
            Program_Line_259='set ACST = 27+ACSTtol',
            Program_Line_260='elseif PMOT > ACSTaul',
            Program_Line_261='set ACST = 27+ACSTtol',
            Program_Line_262='endif',
            Program_Line_263='endif',
            Program_Line_264='endif',
            Program_Line_265='if (ComfStand == 3) && (ComfMod == 1)',
            Program_Line_266='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_267='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_268='elseif CAT==80',
            Program_Line_269='if PMOT < AHSTall',
            Program_Line_270='set AHST = 18+AHSTtol',
            Program_Line_271='elseif PMOT > AHSTaul',
            Program_Line_272='set AHST = 18+AHSTtol',
            Program_Line_273='endif',
            Program_Line_274='elseif CAT==90',
            Program_Line_275='if PMOT < AHSTall',
            Program_Line_276='set AHST = 19+AHSTtol',
            Program_Line_277='elseif PMOT > AHSTaul',
            Program_Line_278='set AHST = 19+AHSTtol',
            Program_Line_279='endif',
            Program_Line_280='endif',
            Program_Line_281='endif',
            Program_Line_282='if (ComfStand == 3) && (ComfMod == 2)',
            Program_Line_283='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_284='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_285='elseif CAT==80',
            Program_Line_286='if PMOT < ACSTall',
            Program_Line_287='set ACST = 26.35+ACSTtol',
            Program_Line_288='elseif PMOT > ACSTaul',
            Program_Line_289='set ACST = 28.35+ACSTtol',
            Program_Line_290='endif',
            Program_Line_291='elseif CAT==90',
            Program_Line_292='if PMOT < ACSTall',
            Program_Line_293='set ACST = 25.09+ACSTtol',
            Program_Line_294='elseif PMOT > ACSTaul',
            Program_Line_295='set ACST = 27.42+ACSTtol',
            Program_Line_296='endif',
            Program_Line_297='endif',
            Program_Line_298='endif',
            Program_Line_299='if (ComfStand == 3) && (ComfMod == 2)',
            Program_Line_300='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_301='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_302='elseif CAT==80',
            Program_Line_303='if PMOT < AHSTall',
            Program_Line_304='set AHST = 20.1+AHSTtol',
            Program_Line_305='elseif PMOT > AHSTaul',
            Program_Line_306='set AHST = 23.78+AHSTtol',
            Program_Line_307='endif',
            Program_Line_308='elseif CAT==90',
            Program_Line_309='if PMOT < AHSTall',
            Program_Line_310='set AHST = 21.44+AHSTtol',
            Program_Line_311='elseif PMOT > AHSTaul',
            Program_Line_312='set AHST = 24.74+AHSTtol',
            Program_Line_313='endif',
            Program_Line_314='endif',
            Program_Line_315='endif',
            Program_Line_316='if (ComfStand == 3) && (ComfMod == 3)',
            Program_Line_317='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_318='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_319='elseif PMOT < ACSTall',
            Program_Line_320='set ACST = ACSTall*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_321='elseif PMOT > ACSTaul',
            Program_Line_322='set ACST = ACSTaul*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_323='endif',
            Program_Line_324='endif',
            Program_Line_325='if (ComfStand == 3) && (ComfMod == 3)',
            Program_Line_326='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_327='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_328='elseif PMOT < AHSTall',
            Program_Line_329='set AHST = AHSTall*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_330='elseif PMOT > AHSTaul',
            Program_Line_331='set AHST = AHSTaul*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_332='endif',
            Program_Line_333='endif',
            Program_Line_334='if (ComfStand == 4)',
            Program_Line_335='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_336='if CAT == 1',
            Program_Line_337='set ACST = PMOT*0.77+12.04+ACSTtol',
            Program_Line_338='elseif CAT == 2',
            Program_Line_339='set ACST = PMOT*0.73+15.28+ACSTtol',
            Program_Line_340='endif',
            Program_Line_341='else',
            Program_Line_342='set ACST = 100',
            Program_Line_343='endif',
            Program_Line_344='endif',
            Program_Line_345='if (ComfStand == 4)',
            Program_Line_346='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_347='if CAT == 1',
            Program_Line_348='set AHST = PMOT*0.87+2.76+AHSTtol',
            Program_Line_349='elseif CAT == 2',
            Program_Line_350='set AHST = PMOT*0.91-0.48+AHSTtol',
            Program_Line_351='endif',
            Program_Line_352='else',
            Program_Line_353='set AHST = -100',
            Program_Line_354='endif',
            Program_Line_355='endif',
            Program_Line_356='if (ComfStand == 5)',
            Program_Line_357='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_358='if CAT == 1',
            Program_Line_359='set ACST = PMOT*0.77+9.34+ACSTtol',
            Program_Line_360='elseif CAT == 2',
            Program_Line_361='set ACST = PMOT*0.73+12.72+ACSTtol',
            Program_Line_362='endif',
            Program_Line_363='else',
            Program_Line_364='set ACST = 100',
            Program_Line_365='endif',
            Program_Line_366='endif',
            Program_Line_367='if (ComfStand == 5)',
            Program_Line_368='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_369='if CAT == 1',
            Program_Line_370='set AHST = PMOT*0.87-0.31+AHSTtol',
            Program_Line_371='elseif CAT == 2',
            Program_Line_372='set AHST = PMOT*0.91-3.69+AHSTtol',
            Program_Line_373='endif',
            Program_Line_374='else',
            Program_Line_375='set AHST = -100',
            Program_Line_376='endif',
            Program_Line_377='endif',
            Program_Line_378='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_379='if CAT==80',
            Program_Line_380='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_381='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_382='elseif PMOT < ACSTall',
            Program_Line_383='set ACST = 26.35+ACSTtol',
            Program_Line_384='elseif PMOT > ACSTaul',
            Program_Line_385='set ACST = 28.35+ACSTtol',
            Program_Line_386='endif',
            Program_Line_387='elseif CAT==90',
            Program_Line_388='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_389='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_390='elseif PMOT < ACSTall',
            Program_Line_391='set ACST = 25.09+ACSTtol',
            Program_Line_392='elseif PMOT > ACSTaul',
            Program_Line_393='set ACST = 27.42+ACSTtol',
            Program_Line_394='endif',
            Program_Line_395='endif',
            Program_Line_396='endif',
            Program_Line_397='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_398='if CAT==80',
            Program_Line_399='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_400='set AHST = PMOT*0.30+25.9+AHSTtol',
            Program_Line_401='elseif PMOT < AHSTall',
            Program_Line_402='set AHST = 20.1+AHSTtol',
            Program_Line_403='elseif PMOT > AHSTaul',
            Program_Line_404='set AHST = 23.78+AHSTtol',
            Program_Line_405='endif',
            Program_Line_406='elseif CAT==90',
            Program_Line_407='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_408='set AHST = PMOT*0.30+23.6+AHSTtol',
            Program_Line_409='elseif PMOT < AHSTall',
            Program_Line_410='set AHST = 21.44+AHSTtol',
            Program_Line_411='elseif PMOT > AHSTaul',
            Program_Line_412='set AHST = 24.74+AHSTtol',
            Program_Line_413='endif',
            Program_Line_414='endif',
            Program_Line_415='endif',
            Program_Line_416='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_417='if CAT == 80',
            Program_Line_418='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_419='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_420='elseif (PMOT < ACSTall)',
            Program_Line_421='set ACST = ACSTall*0.30+25.9+ACSTtol',
            Program_Line_422='elseif (PMOT > ACSTaul)',
            Program_Line_423='set ACST = ACSTaul*0.30+25.9+ACSTtol',
            Program_Line_424='endif',
            Program_Line_425='elseif CAT == 90',
            Program_Line_426='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_427='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_428='elseif (PMOT < ACSTall)',
            Program_Line_429='set ACST = ACSTall*0.30+23.6+ACSTtol',
            Program_Line_430='elseif (PMOT > ACSTaul)',
            Program_Line_431='set ACST = ACSTaul*0.30+23.6+ACSTtol',
            Program_Line_432='endif',
            Program_Line_433='endif',
            Program_Line_434='endif',
            Program_Line_435='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_436='if CAT == 80',
            Program_Line_437='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_438='set AHST = PMOT*0.32+14.88+AHSTtol',
            Program_Line_439='elseif (PMOT < AHSTall)',
            Program_Line_440='set AHST = AHSTall*0.32+14.88+AHSTtol',
            Program_Line_441='elseif (PMOT > AHSTaul)',
            Program_Line_442='set AHST = AHSTaul*0.32+14.88+AHSTtol',
            Program_Line_443='endif',
            Program_Line_444='elseif CAT == 90',
            Program_Line_445='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_446='set AHST = PMOT*0.31+17.14+AHSTtol',
            Program_Line_447='elseif (PMOT < AHSTall)',
            Program_Line_448='set AHST = AHSTall*0.31+17.14+AHSTtol',
            Program_Line_449='elseif (PMOT > AHSTaul)',
            Program_Line_450='set AHST = AHSTaul*0.31+17.14+AHSTtol',
            Program_Line_451='endif',
            Program_Line_452='endif',
            Program_Line_453='endif',
            Program_Line_454='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_455='if (ComfMod == 0)',
            Program_Line_456='if CAT==80',
            Program_Line_457='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_458='elseif CAT==85',
            Program_Line_459='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_460='elseif CAT==90',
            Program_Line_461='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_462='endif',
            Program_Line_463='endif',
            Program_Line_464='endif',
            Program_Line_465='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_466='if (ComfMod == 0)',
            Program_Line_467='if CAT==80',
            Program_Line_468='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_469='elseif CAT==85',
            Program_Line_470='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_471='elseif CAT==90',
            Program_Line_472='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_473='endif',
            Program_Line_474='endif',
            Program_Line_475='endif',
            Program_Line_476='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_477='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_478='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_479='else',
            Program_Line_480='if CAT==80',
            Program_Line_481='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_482='elseif CAT==85',
            Program_Line_483='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_484='elseif CAT==90',
            Program_Line_485='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_486='endif',
            Program_Line_487='endif',
            Program_Line_488='endif',
            Program_Line_489='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_490='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_491='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_492='else',
            Program_Line_493='if CAT==80',
            Program_Line_494='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_495='elseif CAT==85',
            Program_Line_496='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_497='elseif CAT==90',
            Program_Line_498='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_499='endif',
            Program_Line_500='endif',
            Program_Line_501='endif',
            Program_Line_502='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_503='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_504='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_505='elseif CAT==80',
            Program_Line_506='if PMOT < ACSTall',
            Program_Line_507='set ACST = 26.35+ACSTtol',
            Program_Line_508='elseif PMOT > ACSTaul',
            Program_Line_509='set ACST = 28.35+ACSTtol',
            Program_Line_510='endif',
            Program_Line_511='elseif CAT==85',
            Program_Line_512='if PMOT < ACSTall',
            Program_Line_513='set ACST = 25.72+ACSTtol',
            Program_Line_514='elseif PMOT > ACSTaul',
            Program_Line_515='set ACST = 27.89+ACSTtol',
            Program_Line_516='endif',
            Program_Line_517='elseif CAT==90',
            Program_Line_518='if PMOT < ACSTall',
            Program_Line_519='set ACST = 25.09+ACSTtol',
            Program_Line_520='elseif PMOT > ACSTaul',
            Program_Line_521='set ACST = 27.42+ACSTtol',
            Program_Line_522='endif',
            Program_Line_523='endif',
            Program_Line_524='endif',
            Program_Line_525='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_526='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_527='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_528='elseif CAT==80',
            Program_Line_529='if PMOT < AHSTall',
            Program_Line_530='set AHST = 20.1+AHSTtol',
            Program_Line_531='elseif PMOT > AHSTaul',
            Program_Line_532='set AHST = 23.78+AHSTtol',
            Program_Line_533='endif',
            Program_Line_534='elseif CAT==85',
            Program_Line_535='if PMOT < AHSTall',
            Program_Line_536='set AHST = 20.77+AHSTtol',
            Program_Line_537='elseif PMOT > AHSTaul',
            Program_Line_538='set AHST = 24.26+AHSTtol',
            Program_Line_539='endif',
            Program_Line_540='elseif CAT==90',
            Program_Line_541='if PMOT < AHSTall',
            Program_Line_542='set AHST = 21.44+AHSTtol',
            Program_Line_543='elseif PMOT > AHSTaul',
            Program_Line_544='set AHST = 24.74+AHSTtol',
            Program_Line_545='endif',
            Program_Line_546='endif',
            Program_Line_547='endif',
            Program_Line_548='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_549='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_550='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_551='elseif PMOT < ACSTall',
            Program_Line_552='set ACST = ACSTall*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_553='elseif PMOT > ACSTaul',
            Program_Line_554='set ACST = ACSTaul*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_555='endif',
            Program_Line_556='endif',
            Program_Line_557='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_558='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_559='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_560='elseif PMOT < AHSTall',
            Program_Line_561='set AHST = AHSTall*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_562='elseif PMOT > AHSTaul',
            Program_Line_563='set AHST = AHSTaul*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_564='endif',
            Program_Line_565='endif',
            Program_Line_566='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_567='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_568='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_569='else',
            Program_Line_570='if CAT==80',
            Program_Line_571='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_572='elseif CAT==85',
            Program_Line_573='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_574='elseif CAT==90',
            Program_Line_575='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_576='endif',
            Program_Line_577='endif',
            Program_Line_578='endif',
            Program_Line_579='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_580='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_581='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_582='else',
            Program_Line_583='if CAT==80',
            Program_Line_584='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_585='elseif CAT==85',
            Program_Line_586='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_587='elseif CAT==90',
            Program_Line_588='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_589='endif',
            Program_Line_590='endif',
            Program_Line_591='endif',
            Program_Line_592='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_593='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_594='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_595='elseif CAT==80',
            Program_Line_596='if PMOT < ACSTall',
            Program_Line_597='set ACST = 26.35+ACSTtol',
            Program_Line_598='elseif PMOT > ACSTaul',
            Program_Line_599='set ACST = 28.35+ACSTtol',
            Program_Line_600='endif',
            Program_Line_601='elseif CAT==85',
            Program_Line_602='if PMOT < ACSTall',
            Program_Line_603='set ACST = 25.72+ACSTtol',
            Program_Line_604='elseif PMOT > ACSTaul',
            Program_Line_605='set ACST = 27.89+ACSTtol',
            Program_Line_606='endif',
            Program_Line_607='elseif CAT==90',
            Program_Line_608='if PMOT < ACSTall',
            Program_Line_609='set ACST = 25.09+ACSTtol',
            Program_Line_610='elseif PMOT > ACSTaul',
            Program_Line_611='set ACST = 27.42+ACSTtol',
            Program_Line_612='endif',
            Program_Line_613='endif',
            Program_Line_614='endif',
            Program_Line_615='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_616='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_617='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_618='elseif CAT==80',
            Program_Line_619='if PMOT < AHSTall',
            Program_Line_620='set AHST = 20.1+AHSTtol',
            Program_Line_621='elseif PMOT > AHSTaul',
            Program_Line_622='set AHST = 23.78+AHSTtol',
            Program_Line_623='endif',
            Program_Line_624='elseif CAT==85',
            Program_Line_625='if PMOT < AHSTall',
            Program_Line_626='set AHST = 20.77+AHSTtol',
            Program_Line_627='elseif PMOT > AHSTaul',
            Program_Line_628='set AHST = 24.26+AHSTtol',
            Program_Line_629='endif',
            Program_Line_630='elseif CAT==90',
            Program_Line_631='if PMOT < AHSTall',
            Program_Line_632='set AHST = 21.44+AHSTtol',
            Program_Line_633='elseif PMOT > AHSTaul',
            Program_Line_634='set AHST = 24.74+AHSTtol',
            Program_Line_635='endif',
            Program_Line_636='endif',
            Program_Line_637='endif',
            Program_Line_638='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_639='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_640='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_641='elseif PMOT < ACSTall',
            Program_Line_642='set ACST = ACSTall*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_643='elseif PMOT > ACSTaul',
            Program_Line_644='set ACST = ACSTaul*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_645='endif',
            Program_Line_646='endif',
            Program_Line_647='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_648='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_649='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_650='elseif PMOT < AHSTall',
            Program_Line_651='set AHST = AHSTall*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_652='elseif PMOT > AHSTaul',
            Program_Line_653='set AHST = AHSTaul*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_654='endif',
            Program_Line_655='endif',
            Program_Line_656='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_657='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_658='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_659='else',
            Program_Line_660='if CAT==80',
            Program_Line_661='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_662='elseif CAT==90',
            Program_Line_663='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_664='endif',
            Program_Line_665='endif',
            Program_Line_666='endif',
            Program_Line_667='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_668='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_669='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_670='else',
            Program_Line_671='if CAT==80',
            Program_Line_672='set AHST = PMOT*0.078+23.25+2.72+AHSTtol',
            Program_Line_673='elseif CAT==90',
            Program_Line_674='set AHST = PMOT*0.078+23.25+1.5+AHSTtol',
            Program_Line_675='endif',
            Program_Line_676='endif',
            Program_Line_677='endif',
            Program_Line_678='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_679='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_680='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_681='elseif CAT==80',
            Program_Line_682='if PMOT < ACSTall',
            Program_Line_683='set ACST = 26.35+ACSTtol',
            Program_Line_684='elseif PMOT > ACSTaul',
            Program_Line_685='set ACST = 28.35+ACSTtol',
            Program_Line_686='endif',
            Program_Line_687='elseif CAT==90',
            Program_Line_688='if PMOT < ACSTall',
            Program_Line_689='set ACST = 25.09+ACSTtol',
            Program_Line_690='elseif PMOT > ACSTaul',
            Program_Line_691='set ACST = 27.42+ACSTtol',
            Program_Line_692='endif',
            Program_Line_693='endif',
            Program_Line_694='endif',
            Program_Line_695='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_696='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_697='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_698='elseif CAT==80',
            Program_Line_699='if PMOT < AHSTall',
            Program_Line_700='set AHST = 20.1+AHSTtol',
            Program_Line_701='elseif PMOT > AHSTaul',
            Program_Line_702='set AHST = 23.78+AHSTtol',
            Program_Line_703='endif',
            Program_Line_704='elseif CAT==90',
            Program_Line_705='if PMOT < AHSTall',
            Program_Line_706='set AHST = 21.44+AHSTtol',
            Program_Line_707='elseif PMOT > AHSTaul',
            Program_Line_708='set AHST = 24.74+AHSTtol',
            Program_Line_709='endif',
            Program_Line_710='endif',
            Program_Line_711='endif',
            Program_Line_712='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_713='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_714='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_715='elseif PMOT < ACSTall',
            Program_Line_716='set ACST = ACSTall*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_717='elseif PMOT > ACSTaul',
            Program_Line_718='set ACST = ACSTaul*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_719='endif',
            Program_Line_720='endif',
            Program_Line_721='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_722='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_723='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_724='elseif PMOT < AHSTall',
            Program_Line_725='set AHST = AHSTall*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_726='elseif PMOT > AHSTaul',
            Program_Line_727='set AHST = AHSTaul*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_728='endif',
            Program_Line_729='endif',
            Program_Line_730='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_731='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_732='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_733='else',
            Program_Line_734='if CAT==80',
            Program_Line_735='set ACST = RMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_736='elseif CAT==90',
            Program_Line_737='set ACST = RMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_738='endif',
            Program_Line_739='endif',
            Program_Line_740='endif',
            Program_Line_741='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_742='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_743='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_744='else',
            Program_Line_745='if CAT==80',
            Program_Line_746='set AHST = RMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_747='elseif CAT==90',
            Program_Line_748='set AHST = RMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_749='endif',
            Program_Line_750='endif',
            Program_Line_751='endif',
            Program_Line_752='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_753='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_754='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_755='elseif CAT==80',
            Program_Line_756='if RMOT < ACSTall',
            Program_Line_757='set ACST = 26.35+ACSTtol',
            Program_Line_758='elseif RMOT > ACSTaul',
            Program_Line_759='set ACST = 28.35+ACSTtol',
            Program_Line_760='endif',
            Program_Line_761='elseif CAT==90',
            Program_Line_762='if RMOT < ACSTall',
            Program_Line_763='set ACST = 25.09+ACSTtol',
            Program_Line_764='elseif RMOT > ACSTaul',
            Program_Line_765='set ACST = 27.42+ACSTtol',
            Program_Line_766='endif',
            Program_Line_767='endif',
            Program_Line_768='endif',
            Program_Line_769='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_770='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_771='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_772='elseif CAT==80',
            Program_Line_773='if RMOT < AHSTall',
            Program_Line_774='set AHST = 20.1+AHSTtol',
            Program_Line_775='elseif RMOT > AHSTaul',
            Program_Line_776='set AHST = 23.78+AHSTtol',
            Program_Line_777='endif',
            Program_Line_778='elseif CAT==90',
            Program_Line_779='if RMOT < AHSTall',
            Program_Line_780='set AHST = 21.44+AHSTtol',
            Program_Line_781='elseif RMOT > AHSTaul',
            Program_Line_782='set AHST = 24.74+AHSTtol',
            Program_Line_783='endif',
            Program_Line_784='endif',
            Program_Line_785='endif',
            Program_Line_786='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_787='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_788='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_789='elseif RMOT < ACSTall',
            Program_Line_790='set ACST = ACSTall*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_791='elseif RMOT > ACSTaul',
            Program_Line_792='set ACST = ACSTaul*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_793='endif',
            Program_Line_794='endif',
            Program_Line_795='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_796='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_797='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_798='elseif RMOT < AHSTall',
            Program_Line_799='set AHST = AHSTall*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_800='elseif RMOT > AHSTaul',
            Program_Line_801='set AHST = AHSTaul*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_802='endif',
            Program_Line_803='endif',
            Program_Line_804='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_805='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_806='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_807='else',
            Program_Line_808='if CAT==80',
            Program_Line_809='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_810='elseif CAT==90',
            Program_Line_811='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_812='endif',
            Program_Line_813='endif',
            Program_Line_814='endif',
            Program_Line_815='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_816='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_817='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_818='else',
            Program_Line_819='if CAT==80',
            Program_Line_820='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_821='elseif CAT==90',
            Program_Line_822='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_823='endif',
            Program_Line_824='endif',
            Program_Line_825='endif',
            Program_Line_826='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_827='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_828='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_829='elseif CAT==80',
            Program_Line_830='if PMOT < ACSTall',
            Program_Line_831='set ACST = 26.35+ACSTtol',
            Program_Line_832='elseif PMOT > ACSTaul',
            Program_Line_833='set ACST = 28.35+ACSTtol',
            Program_Line_834='endif',
            Program_Line_835='elseif CAT==90',
            Program_Line_836='if PMOT < ACSTall',
            Program_Line_837='set ACST = 25.09+ACSTtol',
            Program_Line_838='elseif PMOT > ACSTaul',
            Program_Line_839='set ACST = 27.42+ACSTtol',
            Program_Line_840='endif',
            Program_Line_841='endif',
            Program_Line_842='endif',
            Program_Line_843='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_844='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_845='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_846='elseif CAT==80',
            Program_Line_847='if PMOT < AHSTall',
            Program_Line_848='set AHST = 20.1+AHSTtol',
            Program_Line_849='elseif PMOT > AHSTaul',
            Program_Line_850='set AHST = 23.78+AHSTtol',
            Program_Line_851='endif',
            Program_Line_852='elseif CAT==90',
            Program_Line_853='if PMOT < AHSTall',
            Program_Line_854='set AHST = 21.44+AHSTtol',
            Program_Line_855='elseif PMOT > AHSTaul',
            Program_Line_856='set AHST = 24.74+AHSTtol',
            Program_Line_857='endif',
            Program_Line_858='endif',
            Program_Line_859='endif',
            Program_Line_860='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_861='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_862='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_863='elseif PMOT < ACSTall',
            Program_Line_864='set ACST = ACSTall*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_865='elseif PMOT > ACSTaul',
            Program_Line_866='set ACST = ACSTaul*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_867='endif',
            Program_Line_868='endif',
            Program_Line_869='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_870='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_871='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_872='elseif PMOT < AHSTall',
            Program_Line_873='set AHST = AHSTall*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_874='elseif PMOT > AHSTaul',
            Program_Line_875='set AHST = AHSTaul*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_876='endif',
            Program_Line_877='endif',
            Program_Line_878='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_879='if (CAT==80)',
            Program_Line_880='set ACST = 27+ACSTtol',
            Program_Line_881='elseif (CAT==90)',
            Program_Line_882='set ACST = 25.5+ACSTtol',
            Program_Line_883='endif',
            Program_Line_884='endif',
            Program_Line_885='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_886='if (CAT==80)',
            Program_Line_887='set AHST = 20+AHSTtol',
            Program_Line_888='elseif (CAT==90)',
            Program_Line_889='set AHST = 21.5+AHSTtol',
            Program_Line_890='endif',
            Program_Line_891='endif',
            Program_Line_892='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_893='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_894='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_895='elseif CAT==80',
            Program_Line_896='if PMOT < ACSTall',
            Program_Line_897='set ACST = 27+ACSTtol',
            Program_Line_898='elseif PMOT > ACSTaul',
            Program_Line_899='set ACST = 27+ACSTtol',
            Program_Line_900='endif',
            Program_Line_901='elseif CAT==90',
            Program_Line_902='if PMOT < ACSTall',
            Program_Line_903='set ACST = 25.5+ACSTtol',
            Program_Line_904='elseif PMOT > ACSTaul',
            Program_Line_905='set ACST = 25.5+ACSTtol',
            Program_Line_906='endif',
            Program_Line_907='endif',
            Program_Line_908='endif',
            Program_Line_909='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_910='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_911='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_912='elseif CAT==80',
            Program_Line_913='if PMOT < AHSTall',
            Program_Line_914='set AHST = 20+AHSTtol',
            Program_Line_915='elseif PMOT > AHSTaul',
            Program_Line_916='set AHST = 20+AHSTtol',
            Program_Line_917='endif',
            Program_Line_918='elseif CAT==90',
            Program_Line_919='if PMOT < AHSTall',
            Program_Line_920='set AHST = 21.5+AHSTtol',
            Program_Line_921='elseif PMOT > AHSTaul',
            Program_Line_922='set AHST = 21.5+AHSTtol',
            Program_Line_923='endif',
            Program_Line_924='endif',
            Program_Line_925='endif',
            Program_Line_926='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_927='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_928='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_929='elseif CAT==80',
            Program_Line_930='if PMOT < ACSTall',
            Program_Line_931='set ACST = 26.35+ACSTtol',
            Program_Line_932='elseif PMOT > ACSTaul',
            Program_Line_933='set ACST = 28.35+ACSTtol',
            Program_Line_934='endif',
            Program_Line_935='elseif CAT==90',
            Program_Line_936='if PMOT < ACSTall',
            Program_Line_937='set ACST = 25.09+ACSTtol',
            Program_Line_938='elseif PMOT > ACSTaul',
            Program_Line_939='set ACST = 27.42+ACSTtol',
            Program_Line_940='endif',
            Program_Line_941='endif',
            Program_Line_942='endif',
            Program_Line_943='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_944='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_945='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_946='elseif CAT==80',
            Program_Line_947='if PMOT < AHSTall',
            Program_Line_948='set AHST = 20.1+AHSTtol',
            Program_Line_949='elseif PMOT > AHSTaul',
            Program_Line_950='set AHST = 23.78+AHSTtol',
            Program_Line_951='endif',
            Program_Line_952='elseif CAT==90',
            Program_Line_953='if PMOT < AHSTall',
            Program_Line_954='set AHST = 21.44+AHSTtol',
            Program_Line_955='elseif PMOT > AHSTaul',
            Program_Line_956='set AHST = 24.74+AHSTtol',
            Program_Line_957='endif',
            Program_Line_958='endif',
            Program_Line_959='endif',
            Program_Line_960='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_961='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_962='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_963='elseif PMOT < ACSTall',
            Program_Line_964='set ACST = ACSTall*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_965='elseif PMOT > ACSTaul',
            Program_Line_966='set ACST = ACSTaul*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_967='endif',
            Program_Line_968='endif',
            Program_Line_969='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_970='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_971='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_972='elseif PMOT < AHSTall',
            Program_Line_973='set AHST = AHSTall*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_974='elseif PMOT > AHSTaul',
            Program_Line_975='set AHST = AHSTaul*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_976='endif',
            Program_Line_977='endif',
            Program_Line_978='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_979='if (ComfMod == 0)',
            Program_Line_980='if (CAT==80)',
            Program_Line_981='set ACST = 28+ACSTtol',
            Program_Line_982='elseif (CAT==90)',
            Program_Line_983='set ACST = 26+ACSTtol',
            Program_Line_984='endif',
            Program_Line_985='endif',
            Program_Line_986='endif',
            Program_Line_987='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_988='if (ComfMod == 0)',
            Program_Line_989='if (CAT==80)',
            Program_Line_990='set AHST = 20+AHSTtol',
            Program_Line_991='elseif (CAT==90)',
            Program_Line_992='set AHST = 21+AHSTtol',
            Program_Line_993='endif',
            Program_Line_994='endif',
            Program_Line_995='endif',
            Program_Line_996='if (ComfStand == 13) && (ComfMod == 1)',
            Program_Line_997='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_998='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_999='elseif CAT==80',
            Program_Line_1000='if PMOT < ACSTall',
            Program_Line_1001='set ACST = 28+ACSTtol',
            Program_Line_1002='elseif PMOT > ACSTaul',
            Program_Line_1003='set ACST = 28+ACSTtol',
            Program_Line_1004='endif',
            Program_Line_1005='elseif CAT==90',
            Program_Line_1006='if PMOT < ACSTall',
            Program_Line_1007='set ACST = 26+ACSTtol',
            Program_Line_1008='elseif PMOT > ACSTaul',
            Program_Line_1009='set ACST = 26+ACSTtol',
            Program_Line_1010='endif',
            Program_Line_1011='endif',
            Program_Line_1012='endif',
            Program_Line_1013='if (ComfStand == 13) && (ComfMod == 1)',
            Program_Line_1014='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1015='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1016='elseif CAT==80',
            Program_Line_1017='if PMOT < AHSTall',
            Program_Line_1018='set AHST = 20+AHSTtol',
            Program_Line_1019='elseif PMOT > AHSTaul',
            Program_Line_1020='set AHST = 20+AHSTtol',
            Program_Line_1021='endif',
            Program_Line_1022='elseif CAT==90',
            Program_Line_1023='if PMOT < AHSTall',
            Program_Line_1024='set AHST = 21+AHSTtol',
            Program_Line_1025='elseif PMOT > AHSTaul',
            Program_Line_1026='set AHST = 21+AHSTtol',
            Program_Line_1027='endif',
            Program_Line_1028='endif',
            Program_Line_1029='endif',
            Program_Line_1030='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1031='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1032='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1033='elseif CAT==80',
            Program_Line_1034='if PMOT < ACSTall',
            Program_Line_1035='set ACST = 26.35+ACSTtol',
            Program_Line_1036='elseif PMOT > ACSTaul',
            Program_Line_1037='set ACST = 28.35+ACSTtol',
            Program_Line_1038='endif',
            Program_Line_1039='elseif CAT==90',
            Program_Line_1040='if PMOT < ACSTall',
            Program_Line_1041='set ACST = 25.09+ACSTtol',
            Program_Line_1042='elseif PMOT > ACSTaul',
            Program_Line_1043='set ACST = 27.42+ACSTtol',
            Program_Line_1044='endif',
            Program_Line_1045='endif',
            Program_Line_1046='endif',
            Program_Line_1047='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1048='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1049='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1050='elseif CAT==80',
            Program_Line_1051='if PMOT < AHSTall',
            Program_Line_1052='set AHST = 20.1+AHSTtol',
            Program_Line_1053='elseif PMOT > AHSTaul',
            Program_Line_1054='set AHST = 23.78+AHSTtol',
            Program_Line_1055='endif',
            Program_Line_1056='elseif CAT==90',
            Program_Line_1057='if PMOT < AHSTall',
            Program_Line_1058='set AHST = 21.44+AHSTtol',
            Program_Line_1059='elseif PMOT > AHSTaul',
            Program_Line_1060='set AHST = 24.74+AHSTtol',
            Program_Line_1061='endif',
            Program_Line_1062='endif',
            Program_Line_1063='endif',
            Program_Line_1064='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1065='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1066='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1067='elseif PMOT < ACSTall',
            Program_Line_1068='set ACST = ACSTall*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1069='elseif PMOT > ACSTaul',
            Program_Line_1070='set ACST = ACSTaul*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1071='endif',
            Program_Line_1072='endif',
            Program_Line_1073='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1074='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1075='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1076='elseif PMOT < AHSTall',
            Program_Line_1077='set AHST = AHSTall*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1078='elseif PMOT > AHSTaul',
            Program_Line_1079='set AHST = AHSTaul*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1080='endif',
            Program_Line_1081='endif',
            Program_Line_1082='if (ComfStand == 14) && (ComfMod == 1)',
            Program_Line_1083='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1084='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1085='elseif CAT==80',
            Program_Line_1086='if PMOT < ACSTall',
            Program_Line_1087='set ACST = 28+ACSTtol',
            Program_Line_1088='elseif PMOT > ACSTaul',
            Program_Line_1089='set ACST = 28+ACSTtol',
            Program_Line_1090='endif',
            Program_Line_1091='elseif CAT==90',
            Program_Line_1092='if PMOT < ACSTall',
            Program_Line_1093='set ACST = 26+ACSTtol',
            Program_Line_1094='elseif PMOT > ACSTaul',
            Program_Line_1095='set ACST = 26+ACSTtol',
            Program_Line_1096='endif',
            Program_Line_1097='endif',
            Program_Line_1098='endif',
            Program_Line_1099='if (ComfStand == 14) && (ComfMod == 1)',
            Program_Line_1100='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1101='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1102='elseif CAT==80',
            Program_Line_1103='if PMOT < AHSTall',
            Program_Line_1104='set AHST = 20+AHSTtol',
            Program_Line_1105='elseif PMOT > AHSTaul',
            Program_Line_1106='set AHST = 20+AHSTtol',
            Program_Line_1107='endif',
            Program_Line_1108='elseif CAT==90',
            Program_Line_1109='if PMOT < AHSTall',
            Program_Line_1110='set AHST = 21+AHSTtol',
            Program_Line_1111='elseif PMOT > AHSTaul',
            Program_Line_1112='set AHST = 21+AHSTtol',
            Program_Line_1113='endif',
            Program_Line_1114='endif',
            Program_Line_1115='endif',
            Program_Line_1116='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1117='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1118='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1119='elseif CAT==80',
            Program_Line_1120='if PMOT < ACSTall',
            Program_Line_1121='set ACST = 26.35+ACSTtol',
            Program_Line_1122='elseif PMOT > ACSTaul',
            Program_Line_1123='set ACST = 28.35+ACSTtol',
            Program_Line_1124='endif',
            Program_Line_1125='elseif CAT==90',
            Program_Line_1126='if PMOT < ACSTall',
            Program_Line_1127='set ACST = 25.09+ACSTtol',
            Program_Line_1128='elseif PMOT > ACSTaul',
            Program_Line_1129='set ACST = 27.42+ACSTtol',
            Program_Line_1130='endif',
            Program_Line_1131='endif',
            Program_Line_1132='endif',
            Program_Line_1133='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1134='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1135='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1136='elseif CAT==80',
            Program_Line_1137='if PMOT < AHSTall',
            Program_Line_1138='set AHST = 20.1+AHSTtol',
            Program_Line_1139='elseif PMOT > AHSTaul',
            Program_Line_1140='set AHST = 23.78+AHSTtol',
            Program_Line_1141='endif',
            Program_Line_1142='elseif CAT==90',
            Program_Line_1143='if PMOT < AHSTall',
            Program_Line_1144='set AHST = 21.44+AHSTtol',
            Program_Line_1145='elseif PMOT > AHSTaul',
            Program_Line_1146='set AHST = 24.74+AHSTtol',
            Program_Line_1147='endif',
            Program_Line_1148='endif',
            Program_Line_1149='endif',
            Program_Line_1150='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1151='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1152='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1153='elseif PMOT < ACSTall',
            Program_Line_1154='set ACST = ACSTall*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1155='elseif PMOT > ACSTaul',
            Program_Line_1156='set ACST = ACSTaul*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1157='endif',
            Program_Line_1158='endif',
            Program_Line_1159='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1160='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1161='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1162='elseif PMOT < AHSTall',
            Program_Line_1163='set AHST = AHSTall*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1164='elseif PMOT > AHSTaul',
            Program_Line_1165='set AHST = AHSTaul*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1166='endif',
            Program_Line_1167='endif',
            Program_Line_1168='if (ComfStand == 15) || (ComfStand == 16)',
            Program_Line_1169='if (ComfMod == 0)',
            Program_Line_1170='if (CAT==80)',
            Program_Line_1171='set ACST = 26+ACSTtol',
            Program_Line_1172='elseif (CAT==90)',
            Program_Line_1173='set ACST = 25+ACSTtol',
            Program_Line_1174='endif',
            Program_Line_1175='endif',
            Program_Line_1176='endif',
            Program_Line_1177='if (ComfStand == 15) || (ComfStand == 16)',
            Program_Line_1178='if (ComfMod == 0)',
            Program_Line_1179='if (CAT==80)',
            Program_Line_1180='set AHST = 22+AHSTtol',
            Program_Line_1181='elseif (CAT==90)',
            Program_Line_1182='set AHST = 23+AHSTtol',
            Program_Line_1183='endif',
            Program_Line_1184='endif',
            Program_Line_1185='endif',
            Program_Line_1186='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1187='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1188='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1189='elseif CAT==80',
            Program_Line_1190='if PMOT < ACSTall',
            Program_Line_1191='set ACST = 26+ACSTtol',
            Program_Line_1192='elseif PMOT > ACSTaul',
            Program_Line_1193='set ACST = 26+ACSTtol',
            Program_Line_1194='endif',
            Program_Line_1195='elseif CAT==90',
            Program_Line_1196='if PMOT < ACSTall',
            Program_Line_1197='set ACST = 25+ACSTtol',
            Program_Line_1198='elseif PMOT > ACSTaul',
            Program_Line_1199='set ACST = 25+ACSTtol',
            Program_Line_1200='endif',
            Program_Line_1201='endif',
            Program_Line_1202='endif',
            Program_Line_1203='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1204='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1205='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1206='elseif CAT==80',
            Program_Line_1207='if PMOT < AHSTall',
            Program_Line_1208='set AHST = 22+AHSTtol',
            Program_Line_1209='elseif PMOT > AHSTaul',
            Program_Line_1210='set AHST = 22+AHSTtol',
            Program_Line_1211='endif',
            Program_Line_1212='elseif CAT==90',
            Program_Line_1213='if PMOT < AHSTall',
            Program_Line_1214='set AHST = 23+AHSTtol',
            Program_Line_1215='elseif PMOT > AHSTaul',
            Program_Line_1216='set AHST = 23+AHSTtol',
            Program_Line_1217='endif',
            Program_Line_1218='endif',
            Program_Line_1219='endif',
            Program_Line_1220='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1221='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1222='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1223='elseif CAT==80',
            Program_Line_1224='if PMOT < ACSTall',
            Program_Line_1225='set ACST = 26.35+ACSTtol',
            Program_Line_1226='elseif PMOT > ACSTaul',
            Program_Line_1227='set ACST = 28.35+ACSTtol',
            Program_Line_1228='endif',
            Program_Line_1229='elseif CAT==90',
            Program_Line_1230='if PMOT < ACSTall',
            Program_Line_1231='set ACST = 25.09+ACSTtol',
            Program_Line_1232='elseif PMOT > ACSTaul',
            Program_Line_1233='set ACST = 27.42+ACSTtol',
            Program_Line_1234='endif',
            Program_Line_1235='endif',
            Program_Line_1236='endif',
            Program_Line_1237='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1238='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1239='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1240='elseif CAT==80',
            Program_Line_1241='if PMOT < AHSTall',
            Program_Line_1242='set AHST = 20.1+AHSTtol',
            Program_Line_1243='elseif PMOT > AHSTaul',
            Program_Line_1244='set AHST = 23.78+AHSTtol',
            Program_Line_1245='endif',
            Program_Line_1246='elseif CAT==90',
            Program_Line_1247='if PMOT < AHSTall',
            Program_Line_1248='set AHST = 21.44+AHSTtol',
            Program_Line_1249='elseif PMOT > AHSTaul',
            Program_Line_1250='set AHST = 24.74+AHSTtol',
            Program_Line_1251='endif',
            Program_Line_1252='endif',
            Program_Line_1253='endif',
            Program_Line_1254='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1255='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1256='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1257='elseif PMOT < ACSTall',
            Program_Line_1258='set ACST = ACSTall*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1259='elseif PMOT > ACSTaul',
            Program_Line_1260='set ACST = ACSTaul*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1261='endif',
            Program_Line_1262='endif',
            Program_Line_1263='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1264='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1265='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1266='elseif PMOT < AHSTall',
            Program_Line_1267='set AHST = AHSTall*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1268='elseif PMOT > AHSTaul',
            Program_Line_1269='set AHST = AHSTaul*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1270='endif',
            Program_Line_1271='endif',
            Program_Line_1272='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1273='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1274='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1275='elseif CAT==80',
            Program_Line_1276='if PMOT < ACSTall',
            Program_Line_1277='set ACST = 26+ACSTtol',
            Program_Line_1278='elseif PMOT > ACSTaul',
            Program_Line_1279='set ACST = 26+ACSTtol',
            Program_Line_1280='endif',
            Program_Line_1281='elseif CAT==90',
            Program_Line_1282='if PMOT < ACSTall',
            Program_Line_1283='set ACST = 25+ACSTtol',
            Program_Line_1284='elseif PMOT > ACSTaul',
            Program_Line_1285='set ACST = 25+ACSTtol',
            Program_Line_1286='endif',
            Program_Line_1287='endif',
            Program_Line_1288='endif',
            Program_Line_1289='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1290='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1291='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1292='elseif CAT==80',
            Program_Line_1293='if PMOT < AHSTall',
            Program_Line_1294='set AHST = 22+AHSTtol',
            Program_Line_1295='elseif PMOT > AHSTaul',
            Program_Line_1296='set AHST = 22+AHSTtol',
            Program_Line_1297='endif',
            Program_Line_1298='elseif CAT==90',
            Program_Line_1299='if PMOT < AHSTall',
            Program_Line_1300='set AHST = 23+AHSTtol',
            Program_Line_1301='elseif PMOT > AHSTaul',
            Program_Line_1302='set AHST = 23+AHSTtol',
            Program_Line_1303='endif',
            Program_Line_1304='endif',
            Program_Line_1305='endif',
            Program_Line_1306='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1307='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1308='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1309='elseif CAT==80',
            Program_Line_1310='if PMOT < ACSTall',
            Program_Line_1311='set ACST = 26.35+ACSTtol',
            Program_Line_1312='elseif PMOT > ACSTaul',
            Program_Line_1313='set ACST = 28.35+ACSTtol',
            Program_Line_1314='endif',
            Program_Line_1315='elseif CAT==90',
            Program_Line_1316='if PMOT < ACSTall',
            Program_Line_1317='set ACST = 25.09+ACSTtol',
            Program_Line_1318='elseif PMOT > ACSTaul',
            Program_Line_1319='set ACST = 27.42+ACSTtol',
            Program_Line_1320='endif',
            Program_Line_1321='endif',
            Program_Line_1322='endif',
            Program_Line_1323='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1324='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1325='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1326='elseif CAT==80',
            Program_Line_1327='if PMOT < AHSTall',
            Program_Line_1328='set AHST = 20.1+AHSTtol',
            Program_Line_1329='elseif PMOT > AHSTaul',
            Program_Line_1330='set AHST = 23.78+AHSTtol',
            Program_Line_1331='endif',
            Program_Line_1332='elseif CAT==90',
            Program_Line_1333='if PMOT < AHSTall',
            Program_Line_1334='set AHST = 21.44+AHSTtol',
            Program_Line_1335='elseif PMOT > AHSTaul',
            Program_Line_1336='set AHST = 24.74+AHSTtol',
            Program_Line_1337='endif',
            Program_Line_1338='endif',
            Program_Line_1339='endif',
            Program_Line_1340='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1341='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1342='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1343='elseif PMOT < ACSTall',
            Program_Line_1344='set ACST = ACSTall*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1345='elseif PMOT > ACSTaul',
            Program_Line_1346='set ACST = ACSTaul*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1347='endif',
            Program_Line_1348='endif',
            Program_Line_1349='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1350='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1351='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1352='elseif PMOT < AHSTall',
            Program_Line_1353='set AHST = AHSTall*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1354='elseif PMOT > AHSTaul',
            Program_Line_1355='set AHST = AHSTaul*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1356='endif',
            Program_Line_1357='endif',
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
                Program_Line_1='if ('+zonename+'_OpT <= ACSTnoTol)',
                Program_Line_2='if ('+zonename+'_OpT >= AHSTnoTol)',
                Program_Line_3='set ComfHoursNoApp_'+zonename+'  = 1*ZoneTimeStep',
                Program_Line_4='else',
                Program_Line_5='set ComfHoursNoApp_'+zonename+' = 0',
                Program_Line_6='endif',
                Program_Line_7='else',
                Program_Line_8='set ComfHoursNoApp_'+zonename+' = 0',
                Program_Line_9='endif'
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
            Program_Line_10='set AHSTtol = 0.25'
            )
        if verboseMode:
            print('Added - SetInputData Program')

    if (ScriptType.lower() == 'vrf' or
        ScriptType.lower() == 'ex_mm'):
        if 'SetVST' in programlist:
            if verboseMode:
                print('Not added - SetVST Program')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Program',
                Name='SetVST',
                Program_Line_1='set MinOutTemp = AHST - MinOToffset',
                Program_Line_2='if ComfStand == 0',
                Program_Line_3='if (CurrentTime < 7)',
                Program_Line_4='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_5='elseif (CurrentTime < 15)',
                Program_Line_6='set VST = 22.5+VSToffset',
                Program_Line_7='elseif (CurrentTime < 23)',
                Program_Line_8='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_9='elseif (CurrentTime < 24)',
                Program_Line_10='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_11='endif',
                Program_Line_12='elseif ComfStand == 1 || ComfStand == 10',
                Program_Line_13='if (RMOT >= AHSTall) && (RMOT <= ACSTaul)',
                Program_Line_14='set VST = ComfTemp+VSToffset',
                Program_Line_15='else',
                Program_Line_16='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_17='endif',
                Program_Line_18='elseif ComfStand == 4 || ComfStand == 5 || ComfStand == 6',
                Program_Line_19='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
                Program_Line_20='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_21='else',
                Program_Line_22='set VST = 0',
                Program_Line_23='endif',
                Program_Line_24='else',
                Program_Line_25='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
                Program_Line_26='set VST = ComfTemp+VSToffset',
                Program_Line_27='else',
                Program_Line_28='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_29='endif',
                Program_Line_30='endif',
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
                    Program_Line_1='if (' + zonename + '_OpT>VST)&&(' + zonename + '_OutT<VST)',
                    # todo if there is no cooling coil, then zonename_COOLCOIL sensor won't be added
                    #  and therefore it should be omitted in all ExistingHVAC EMS programs; same for _HEATCOIL
                    Program_Line_2='if ' + zonename + '_CoolCoil==0',
                    Program_Line_3='if ' + zonename + '_HeatCoil==0',
                    Program_Line_4='if (' + zonename + '_OpT<ACST)&&(' + zonename + '_OutT>MinOutTemp)',
                    Program_Line_5='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_6='set Ventilates_HVACmode2_' + zonename + ' = 1',
                    Program_Line_7='else',
                    Program_Line_8='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_9='endif',
                    Program_Line_10='else',
                    Program_Line_11='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_12='endif',
                    Program_Line_13='else',
                    Program_Line_14='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_15='endif',
                    Program_Line_16='else',
                    Program_Line_17='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_18='endif',
                    Program_Line_19='else',
                    Program_Line_20='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_21='endif',
                    Program_Line_22='if VentCtrl == 0',
                    Program_Line_23='if ' + zonename + '_OutT < ' + zonename + '_OpT',
                    Program_Line_24='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_25='if ' + zonename + '_OpT > VST',
                    Program_Line_26='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_27='set Ventilates_HVACmode1_' + zonename + ' = 1',
                    Program_Line_28='else',
                    Program_Line_29='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_30='endif',
                    Program_Line_31='else',
                    Program_Line_32='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_33='endif',
                    Program_Line_34='else',
                    Program_Line_35='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_36='endif',
                    Program_Line_37='else',
                    Program_Line_38='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_39='endif',
                    Program_Line_40='elseif VentCtrl == 1',
                    Program_Line_41='if ' + zonename + '_OutT<' + zonename + '_OpT',
                    Program_Line_42='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_43='if ' + zonename + '_OpT > ACSTnoTol',
                    Program_Line_44='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_45='set Ventilates_HVACmode1_' + zonename + ' = 1',
                    Program_Line_46='else',
                    Program_Line_47='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_48='endif',
                    Program_Line_49='else',
                    Program_Line_50='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_51='endif',
                    Program_Line_52='else',
                    Program_Line_53='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_54='endif',
                    Program_Line_55='else',
                    Program_Line_56='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_57='endif',
                    Program_Line_58='endif',
                    Program_Line_59='if HVACmode == 0',
                    Program_Line_60='set ACST_Act_' + zonename + ' = ACST',
                    Program_Line_61='set AHST_Act_' + zonename + ' = AHST',
                    Program_Line_62='elseif HVACmode == 1',
                    Program_Line_63='Set ACST_Act_' + zonename + ' = 100',
                    Program_Line_64='Set AHST_Act_' + zonename + ' = -100',
                    Program_Line_65='if Ventilates_HVACmode1_' + zonename + ' == 1',
                    Program_Line_66='set VentHours_' + zonename + ' = 1',
                    Program_Line_67='else',
                    Program_Line_68='set VentHours_' + zonename + ' = 0',
                    Program_Line_69='endif',
                    Program_Line_70='elseif HVACmode == 2',
                    Program_Line_71='if Ventilates_HVACmode2_' + zonename + ' == 1',
                    Program_Line_72='set VentHours_' + zonename + ' = 1',
                    Program_Line_73='elseif Ventilates_HVACmode2_' + zonename + ' == 0',
                    Program_Line_74='set VentHours_' + zonename + ' = 0',
                    Program_Line_75='set ACST_Act_' + zonename + ' = ACST',
                    Program_Line_76='set AHST_Act_' + zonename + ' = AHST',
                    Program_Line_77='endif',
                    Program_Line_78='endif'
                )
                if verboseMode:
                    print('Added - ApplyAST_'+zonename+' Program')
            #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyAST_'+windowname])

        for windowname in self.windownamelist:
            if 'SetWindowOperation_'+windowname in programlist:
                if verboseMode:
                    print('Not added - SetWindowOperation_'+windowname+' Program')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:Program',
                    Name='SetWindowOperation_'+windowname,
                    Program_Line_1='if ('+windowname+'_OpT>VST)&&('+windowname+'_OutT < VST)',
                    # todo if there is no cooling coil, then zonename_COOLCOIL sensor won't be added
                    #  and therefore it should be omitted in all ExistingHVAC EMS programs; same for _HEATCOIL
                    Program_Line_2='if '+windowname+'_CoolCoil==0',
                    Program_Line_3='if '+windowname+'_HeatCoil==0',
                    Program_Line_4='if ('+windowname+'_OpT<ACST)&&('+windowname+'_OutT>MinOutTemp)',
                    Program_Line_5='if '+windowname+'_WindSpeed <= MaxWindSpeed',
                    Program_Line_6='set Ventilates_HVACmode2_'+windowname+' = 1',
                    Program_Line_7='else',
                    Program_Line_8='set Ventilates_HVACmode2_'+windowname+' = 0',
                    Program_Line_9='endif',
                    Program_Line_10='else',
                    Program_Line_11='set Ventilates_HVACmode2_'+windowname+' = 0',
                    Program_Line_12='endif',
                    Program_Line_13='else',
                    Program_Line_14='set Ventilates_HVACmode2_'+windowname+' = 0',
                    Program_Line_15='endif',
                    Program_Line_16='else',
                    Program_Line_17='set Ventilates_HVACmode2_'+windowname+' = 0',
                    Program_Line_18='endif',
                    Program_Line_19='else',
                    Program_Line_20='set Ventilates_HVACmode2_'+windowname+' = 0',
                    Program_Line_21='endif',
                    Program_Line_22='if VentCtrl == 0',
                    Program_Line_23='if '+windowname+'_OutT < '+windowname+'_OpT',
                    Program_Line_24='if '+windowname+'_OutT>MinOutTemp',
                    Program_Line_25='if '+windowname+'_OpT > VST',
                    Program_Line_26='if '+windowname+'_WindSpeed <= MaxWindSpeed',
                    Program_Line_27='set Ventilates_HVACmode1_'+windowname+' = 1',
                    Program_Line_28='else',
                    Program_Line_29='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_30='endif',
                    Program_Line_31='else',
                    Program_Line_32='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_33='endif',
                    Program_Line_34='else',
                    Program_Line_35='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_36='endif',
                    Program_Line_37='else',
                    Program_Line_38='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_39='endif',
                    Program_Line_40='elseif VentCtrl == 1',
                    Program_Line_41='if '+windowname+'_OutT<'+windowname+'_OpT',
                    Program_Line_42='if '+windowname+'_OutT>MinOutTemp',
                    Program_Line_43='if '+windowname+'_OpT > ACSTnoTol',
                    Program_Line_44='if '+windowname+'_WindSpeed <= MaxWindSpeed',
                    Program_Line_45='set Ventilates_HVACmode1_'+windowname+' = 1',
                    Program_Line_46='else',
                    Program_Line_47='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_48='endif',
                    Program_Line_49='else',
                    Program_Line_50='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_51='endif',
                    Program_Line_52='else',
                    Program_Line_53='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_54='endif',
                    Program_Line_55='else',
                    Program_Line_56='set Ventilates_HVACmode1_'+windowname+' = 0',
                    Program_Line_57='endif',
                    Program_Line_58='endif',
                    Program_Line_59='if HVACmode == 0',
                    Program_Line_60='set '+windowname+'_VentOpenFact = 0',
                    Program_Line_61='elseif HVACmode == 1',
                    Program_Line_62='if Ventilates_HVACmode1_'+windowname+' == 1',
                    Program_Line_63='set '+windowname+'_VentOpenFact = 1',
                    Program_Line_64='else',
                    Program_Line_65='set '+windowname+'_VentOpenFact = 0',
                    Program_Line_66='endif',
                    Program_Line_67='elseif HVACmode == 2',
                    Program_Line_68='if Ventilates_HVACmode2_'+windowname+' == 1',
                    Program_Line_69='set '+windowname+'_VentOpenFact = 1',
                    Program_Line_70='else',
                    Program_Line_71='set '+windowname+'_VentOpenFact = 0',
                    Program_Line_72='endif',
                    Program_Line_73='endif'
                    )
                if verboseMode:
                    print('Added - SetWindowOperation_'+windowname+' Program')
            #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetWindowOperation_'+windowname])
    elif ScriptType.lower() == 'ex_ac':
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


def addEMSOutputVariableBase(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS output variables for Base accim.

    Checks if some EMS output variables objects are already
    in the model, and otherwise adds them.
    """
    EMSOutputVariableAvg_dict = {
        'Comfort Temperature': ['ComfTemp', 'C'],
        'Adaptive Cooling Setpoint Temperature': ['ACST', 'C'],
        'Adaptive Heating Setpoint Temperature': ['AHST', 'C'],
        'Adaptive Cooling Setpoint Temperature_No Tolerance': ['ACSTnoTol', 'C'],
        'Adaptive Heating Setpoint Temperature_No Tolerance': ['AHSTnoTol', 'C'],
    }
    EMSOutputVariableAvgMM_dict = {
        'Ventilation Setpoint Temperature': ['VST', 'C'],
        'Minimum Outdoor Temperature for ventilation': ['MinOutTemp', 'C']
        }
    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
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

    EMSOutputVariableSum_dict = {
        'Comfortable Hours_No Applicability': ['ComfHoursNoApp', 'H'],
        'Comfortable Hours_Applicability': ['ComfHours', 'H'],
        'Discomfortable Applicable Hot Hours': ['DiscomfAppHotHours', 'H'],
        'Discomfortable Applicable Cold Hours': ['DiscomfAppColdHours', 'H'],
        'Discomfortable Non Applicable Hot Hours': ['DiscomfNonAppHotHours', 'H'],
        'Discomfortable Non Applicable Cold Hours': ['DiscomfNonAppColdHours', 'H'],
        'Zone Floor Area': ['ZoneFloorArea', 'm2'],
        'Zone Air Volume': ['ZoneAirVolume', 'm3'],
    }

    for i in EMSOutputVariableSum_dict:
        for zonename in self.occupiedZones:
            if i+'_'+zonename in outputvariablelist:
                if verboseMode:
                    print('Not added - '+i+'_'
                          + zonename + ' Output Variable')
            else:
                self.idf1.newidfobject(
                    'EnergyManagementSystem:OutputVariable',
                    Name=i + '_' + zonename,
                    EMS_Variable_Name=EMSOutputVariableSum_dict[i][0]+'_'
                    + zonename,
                    Type_of_Data_in_Variable='Summed',
                    Update_Frequency='ZoneTimestep',
                    EMS_Program_or_Subroutine_Name='',
                    Units=EMSOutputVariableSum_dict[i][1]
                    )
                if verboseMode:
                    print('Added - '+i+'_'
                          + zonename + ' Output Variable')
                # print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == i+'_'+zonename'])

    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
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
    """Remove existing Global Variable objects and add correct Global Variable objects for accim."""
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
        Erl_Variable_16_Name='AHSTtol'
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
            Erl_Variable_8_Name='ZoneAirVolume_' + zonename

        )

    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
        self.idf1.newidfobject(
            'EnergyManagementSystem:GlobalVariable',
            Erl_Variable_1_Name='VST',
            Erl_Variable_2_Name='VSToffset',
            Erl_Variable_3_Name='MaxWindSpeed',
            Erl_Variable_4_Name='VentCtrl',
            Erl_Variable_5_Name='HVACmode',
            Erl_Variable_6_Name='MinOutTemp',
            Erl_Variable_7_Name='MinOToffset'
            )
        for zonename in self.zonenames:
            self.idf1.newidfobject(
                'EnergyManagementSystem:GlobalVariable',
                Erl_Variable_1_Name='VentHours_' + zonename
            )

    if verboseMode:
        print("Global variables objects have been added")

def addIntVarList(self, verboseMode: bool = True):
    """Add Internal variables objects for accim."""
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

# todo add argument for mm outputvariables
def addOutputVariablesBase(
        self,
        ScriptType: str = None,
        TempCtrl: str = None,
        verboseMode: bool = True):
    """Add Output:Variable objects for accim."""
    EnvironmentalImpactFactorslist = ([output for output in self.idf1.idfobjects['Output:EnvironmentalImpactFactors']])
    outputmeterlist = ([output for output in self.idf1.idfobjects['Output:Meter']])
    alloutputs = ([output for output in self.idf1.idfobjects['Output:Variable']])

    if ScriptType.lower() == 'vrf':
        for i in range(len(EnvironmentalImpactFactorslist)):
            firstEnvironmentalImpactFactor = self.idf1.idfobjects['Output:EnvironmentalImpactFactors'][-1]
            self.idf1.removeidfobject(firstEnvironmentalImpactFactor)
        for i in range(len(outputmeterlist)):
            firstoutputmeter = self.idf1.idfobjects['Output:Meter'][-1]
            self.idf1.removeidfobject(firstoutputmeter)
        for i in range(len(alloutputs)):
            firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
            self.idf1.removeidfobject(firstoutput)

    # del EnvironmentalImpactFactorslist,firstEnvironmentalImpactFactor, outputmeterlist, firstoutputmeter, alloutputs, firstoutput

    EMSoutputvariablenamelist = ([outputvariable.Name
                           for outputvariable
                           in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']])
    outputnamelist = ([output.Variable_Name for output in self.idf1.idfobjects['Output:Variable']])
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
        # 'AFN Surface Venting Window or Door Opening Factor',
        'AFN Zone Infiltration Air Change Rate',
        'AFN Zone Infiltration Volume'
    ]
    if TempCtrl.lower() == 'pmv':
        addittionaloutputs.extend([
            'Zone Thermal Comfort Fanger Model PMV',
            'Zone Thermal Comfort Fanger Model PPD'
        ])


    for outputvariable in EMSoutputvariablenamelist:
        if outputvariable in outputnamelist:
            if verboseMode:
                print('Not added - '+outputvariable+' Output:Variable data')
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
                Reporting_Frequency='Hourly',
                Schedule_Name=''
                )
            if verboseMode:
                print('Added - '+outputvariable+' Output:Variable data')
    #        print([output for output in self.idf1.idfobjects['Output:Variable'] if output.Variable_Name == outputvariable])

    for addittionaloutput in addittionaloutputs:
        if addittionaloutput in outputnamelist:
            if verboseMode:
                print('Not added - '+addittionaloutput+' Output:Variable data')
        else:
            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value='*',
                Variable_Name=addittionaloutput,
                Reporting_Frequency='Hourly',
                Schedule_Name=''
                )
            if verboseMode:
                print('Added - '+addittionaloutput+' Output:Variable data')

    outputlist = ([output for output in self.idf1.idfobjects['Output:Variable']])
    for i in outputlist:
        for addittionaloutput in addittionaloutputs:
            if addittionaloutput in i.Variable_Name:
                i.Schedule_Name = ''

    siteAddOutputs = [
        'Site Outdoor Air Drybulb Temperature',
        'Site Wind Speed',
        'Site Outdoor Air Relative Humidity'
    ]

    other_site_outputs = [
        'Site Outdoor Air Drybulb Temperature [C]',
        'Site Outdoor Air Dewpoint Temperature [C]',
        'Site Outdoor Air Wetbulb Temperature [C]',
        'Site Outdoor Air Humidity Ratio [kgWater/kgAir]',
        'Site Outdoor Air Relative Humidity [%]',
        'Site Outdoor Air Barometric Pressure [Pa]',
        'Site Wind Speed [m/s]',
        'Site Wind Direction [deg]',
        'Site Sky Temperature [C]',
        'Site Horizontal Infrared Radiation Rate per Area [W/m2]',
        'Site Difuse Solar Radiation Rate per Area [W/m2]',
        'Site Direct Solar Radiation Rate per Area [W/m2]',
        'Site Total Sky Cover []',
        'Site Opaque Sky Cover []',
        'Site Precipitation Depth [m]',
        'Site Ground Refected Solar Radiation Rate per Area [W/m2]',
        'Site Ground Temperature [C]',
        'Site Surface Ground Temperature [C]',
        'Site Deep Ground Temperature [C]',
        'Site Simple Factor Model Ground Temperature [C]',
        'Site Outdoor Air Enthalpy [J/kg]',
        'Site Outdoor Air Density [kg/m3]',
        'Site Solar Azimuth Angle [deg]',
        'Site Solar Altitude Angle [deg]',
        'Site Solar Hour Angle [deg]',
        'Site Rain Status []',
        'Site Snow on Ground Status []',
        'Site Exterior Horizontal Sky Illuminance [lux]',
        'Site Exterior Horizontal Beam Illuminance [lux]',
        'Site Exterior Beam Normal Illuminance [lux]',
        'Site Sky Difuse Solar Radiation Luminous Eﬀcacy [lum/W]',
        'Site Beam Solar Radiation Luminous Eﬀcacy [lum/W]',
        'Site Daylighting Model Sky Clearness []',
        'Sky Brightness for Daylighting Calculation []',
        'Site Daylight Saving Time Status []',
        'Site Day Type Index []',
        'Site Mains Water Temperature [C]',
    ]

    for addittionaloutput in siteAddOutputs:
        if addittionaloutput in outputnamelist:
            if verboseMode:
                print('Not added - '+addittionaloutput+' Output:Variable data')
        else:
            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value='Environment',
                Variable_Name=addittionaloutput,
                Reporting_Frequency='Hourly',
                Schedule_Name=''
                )
            if verboseMode:
                print('Added - '+addittionaloutput+' Output:Variable data')

    for zonename in self.zonenames:
        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value='AHST_Sch_'+zonename,
            Variable_Name='Schedule Value',
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - AHST_Sch_'+zonename+' Output:Variable data')

        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value='ACST_Sch_'+zonename,
            Variable_Name='Schedule Value',
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - ACST_Sch_'+zonename+' Output:Variable data')

    # for zonename in self.zonenames_orig:
    #     self.idf1.newidfobject(
    #         'Output:Variable',
    #         Key_Value=zonename,
    #         Variable_Name='Zone Operative Temperature',
    #         Reporting_Frequency='Hourly',
    #         Schedule_Name=''
    #         )
    #     if verboseMode:
    #         print('Added - '+zonename+' Zone Operative Temperature Output:Variable data')

    if ScriptType.lower() == 'vrf':
        VRFoutputs = [
            'VRF Heat Pump Cooling Electricity Energy',
            'VRF Heat Pump Heating Electricity Energy',
        ]

        for addittionaloutput in VRFoutputs:
            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value='*',
                Variable_Name=addittionaloutput,
                Reporting_Frequency='Hourly',
                Schedule_Name=''
            )
            if verboseMode:
                print('Added - ' + addittionaloutput + ' Output:Variable data')

        for zonename in self.zonenames:
            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value=zonename + ' VRF Indoor Unit DX Cooling Coil',
                Variable_Name='Cooling Coil Total Cooling Rate',
                Reporting_Frequency='Hourly',
                Schedule_Name=''
            )
            if verboseMode:
                print('Added - ' + zonename + ' VRF Indoor Unit DX Cooling Coil Output:Variable data')

            self.idf1.newidfobject(
                'Output:Variable',
                Key_Value=zonename + ' VRF Indoor Unit DX Heating Coil',
                Variable_Name='Heating Coil Heating Rate',
                Reporting_Frequency='Hourly',
                Schedule_Name=''
            )
            if verboseMode:
                print('Added - ' + zonename + ' VRF Indoor Unit DX Heating Coil Output:Variable data')

    del EMSoutputvariablenamelist, outputnamelist, addittionaloutputs,


def addOutputVariablesTimestep(self, verboseMode: bool = True):
    """
    Add Output:Variable objects in timestep frequency.

    No need for further description.
    """
    fulloutputlist = ([output
                       for output
                       in self.idf1.idfobjects['Output:Variable']])
    # print(fulloutputlist)

    outputlist = ([output.Variable_Name
                   for output
                   in self.idf1.idfobjects['Output:Variable']])
    # print(outputlist)

    for i in range(len(outputlist)):
        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value=fulloutputlist[i].Key_Value,
            Variable_Name=fulloutputlist[i].Variable_Name,
            Reporting_Frequency='Timestep',
            Schedule_Name=fulloutputlist[i].Schedule_Name
            )
        if verboseMode:
            print('Added - '+
                  fulloutputlist[i].Variable_Name+
                  ' Output:Variable Timestep data')

    # print([output for output in self.idf1.idfobjects['Output:Variable'] if output.Reporting_Frequency == 'Timestep'])

    del fulloutputlist, outputlist


def addSimplifiedOutputVariables(
        self,
        TempCtrl: str = None,
        verboseMode: bool = True):
    """
    Add simplified Output:Variable objects for accim.

    Remove all outputs and add only VFR outdoor unit consumption
    and operative temperature.
    """
    EnvList = ([output
                for output
                in self.idf1.idfobjects['Output:EnvironmentalImpactFactors']])
    for i in range(len(EnvList)):
        firstEnv = self.idf1.idfobjects['Output:EnvironmentalImpactFactors'][-1]
        self.idf1.removeidfobject(firstEnv)

    outputmeterlist = ([output
                        for output
                        in self.idf1.idfobjects['Output:Meter']])
    for i in range(len(outputmeterlist)):
        firstoutputmeter = self.idf1.idfobjects['Output:Meter'][-1]
        self.idf1.removeidfobject(firstoutputmeter)

    alloutputs = ([output
                   for output
                   in self.idf1.idfobjects['Output:Variable']])
    for i in range(len(alloutputs)):
        firstoutput = self.idf1.idfobjects['Output:Variable'][-1]
        self.idf1.removeidfobject(firstoutput)

    # del EnvironmentalImpactFactorslist,firstEnvironmentalImpactFactor, outputmeterlist, firstoutputmeter, alloutputs, firstoutput

    addittionaloutputs = [
        # 'Zone Thermostat Operative Temperature',
        'Zone Operative Temperature',
        'Cooling Coil Total Cooling Rate',
        'Heating Coil Heating Rate',
    ]

    if TempCtrl.lower() == 'pmv':
        addittionaloutputs.extend([
            'Zone Thermal Comfort Fanger Model PMV',
            'Zone Thermal Comfort Fanger Model PPD'
        ])

    for addittionaloutput in addittionaloutputs:
        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value='*',
            Variable_Name=addittionaloutput,
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - '+addittionaloutput+' Output:Variable data')

    del addittionaloutputs


def addEMSSensorsBase(self, ScriptType: str = None, verboseMode: bool = True):
    """Add EMS sensors for accim."""
    sensorlist = ([sensor.Name for sensor in self.idf1.idfobjects['EnergyManagementSystem:Sensor']])

    if 'RMOT' in sensorlist:
        if verboseMode:
            print('Not added - RMOT Sensor')
    else:
        self.idf1.newidfobject(
            'EnergyManagementSystem:Sensor',
            Name='RMOT',
            OutputVariable_or_OutputMeter_Index_Key_Name='People '+self.zonenames_orig[0],
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
            OutputVariable_or_OutputMeter_Index_Key_Name='People '+self.zonenames_orig[0],
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
        if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
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

    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
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
    """Add EMS actuators for accim."""
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

    if ScriptType.lower() == 'vrf' or ScriptType.lower() == 'ex_mm':
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


