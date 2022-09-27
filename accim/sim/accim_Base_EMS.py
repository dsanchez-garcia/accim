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
            Program_Line_226='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
            Program_Line_227='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_228='elseif PMOT < ACSTall',
            Program_Line_229='set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_230='elseif PMOT > ACSTaul',
            Program_Line_231='set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol',
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
            Program_Line_338='set AHST = PMOT*0.87+2.76+AHSTtol',
            Program_Line_339='elseif CAT == 2',
            Program_Line_340='set ACST = PMOT*0.73+15.28+ACSTtol',
            Program_Line_341='set AHST = PMOT*0.91-0.48+AHSTtol',
            Program_Line_342='else',
            Program_Line_343='set ACST = 100',
            Program_Line_344='set AHST = -100',
            Program_Line_345='endif',
            Program_Line_346='endif',
            Program_Line_347='endif',
            Program_Line_348='if (ComfStand == 5)',
            Program_Line_349='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_350='if CAT == 1',
            Program_Line_351='set ACST = PMOT*0.77+9.34+ACSTtol',
            Program_Line_352='set AHST = PMOT*0.87-0.31+AHSTtol',
            Program_Line_353='elseif CAT == 2',
            Program_Line_354='set ACST = PMOT*0.73+12.72+ACSTtol',
            Program_Line_355='set AHST = PMOT*0.91-3.69+AHSTtol',
            Program_Line_356='else',
            Program_Line_357='set ACST = 100',
            Program_Line_358='set AHST = -100',
            Program_Line_359='endif',
            Program_Line_360='endif',
            Program_Line_361='endif',
            Program_Line_362='!NUEVO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',
            Program_Line_363='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_364='if CAT==80',
            Program_Line_365='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_366='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_367='elseif PMOT < ACSTall',
            Program_Line_368='set ACST = 26.35+ACSTtol',
            Program_Line_369='elseif PMOT > ACSTaul',
            Program_Line_370='set ACST = 28.35+ACSTtol',
            Program_Line_371='endif',
            Program_Line_372='elseif CAT==90',
            Program_Line_373='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_374='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_375='elseif PMOT < ACSTall',
            Program_Line_376='set ACST = 25.09+ACSTtol',
            Program_Line_377='elseif PMOT > ACSTaul',
            Program_Line_378='set ACST = 27.42+ACSTtol',
            Program_Line_379='endif',
            Program_Line_380='endif',
            Program_Line_381='endif',
            Program_Line_382='if (ComfStand == 6) && (ComfMod == 2)',
            Program_Line_383='if CAT==80',
            Program_Line_384='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_385='set AHST = PMOT*0.30+25.9+AHSTtol',
            Program_Line_386='elseif PMOT < AHSTall',
            Program_Line_387='set AHST = 20.1+AHSTtol',
            Program_Line_388='elseif PMOT > AHSTaul',
            Program_Line_389='set AHST = 23.78+AHSTtol',
            Program_Line_390='endif',
            Program_Line_391='elseif CAT==90',
            Program_Line_392='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_393='set AHST = PMOT*0.30+23.6+AHSTtol',
            Program_Line_394='elseif PMOT < AHSTall',
            Program_Line_395='set AHST = 21.44+AHSTtol',
            Program_Line_396='elseif PMOT > AHSTaul',
            Program_Line_397='set AHST = 24.74+AHSTtol',
            Program_Line_398='endif',
            Program_Line_399='endif',
            Program_Line_400='endif',
            Program_Line_401='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_402='if CAT == 80',
            Program_Line_403='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_404='set ACST = PMOT*0.30+25.9+ACSTtol',
            Program_Line_405='elseif (PMOT < ACSTall)',
            Program_Line_406='set ACST = ACSTall*0.30+25.9+ACSTtol',
            Program_Line_407='elseif (PMOT > ACSTaul)',
            Program_Line_408='set ACST = ACSTaul*0.30+25.9+ACSTtol',
            Program_Line_409='endif',
            Program_Line_410='elseif CAT == 90',
            Program_Line_411='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_412='set ACST = PMOT*0.30+23.6+ACSTtol',
            Program_Line_413='elseif (PMOT < ACSTall)',
            Program_Line_414='set ACST = ACSTall*0.30+23.6+ACSTtol',
            Program_Line_415='elseif (PMOT > ACSTaul)',
            Program_Line_416='set ACST = ACSTaul*0.30+23.6+ACSTtol',
            Program_Line_417='endif',
            Program_Line_418='endif',
            Program_Line_419='endif',
            Program_Line_420='if (ComfStand == 6) && (ComfMod == 3)',
            Program_Line_421='if CAT == 80',
            Program_Line_422='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_423='set AHST = PMOT*0.32+14.88+AHSTtol',
            Program_Line_424='elseif (PMOT < AHSTall)',
            Program_Line_425='set AHST = AHSTall*0.32+14.88+AHSTtol',
            Program_Line_426='elseif (PMOT > AHSTaul)',
            Program_Line_427='set AHST = AHSTaul*0.32+14.88+AHSTtol',
            Program_Line_428='endif',
            Program_Line_429='elseif CAT == 90',
            Program_Line_430='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_431='set AHST = PMOT*0.31+17.14+AHSTtol',
            Program_Line_432='elseif (PMOT < AHSTall)',
            Program_Line_433='set AHST = AHSTall*0.31+17.14+AHSTtol',
            Program_Line_434='elseif (PMOT > AHSTaul)',
            Program_Line_435='set AHST = AHSTaul*0.31+17.14+AHSTtol',
            Program_Line_436='endif',
            Program_Line_437='endif',
            Program_Line_438='endif',
            Program_Line_439='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_440='if (ComfMod == 0)',
            Program_Line_441='if CAT==80',
            Program_Line_442='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_443='elseif CAT==85',
            Program_Line_444='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_445='elseif CAT==90',
            Program_Line_446='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_447='endif',
            Program_Line_448='endif',
            Program_Line_449='endif',
            Program_Line_450='if ComfStand == 7 || ComfStand == 8 || ComfStand == 9 || ComfStand == 10',
            Program_Line_451='if (ComfMod == 0)',
            Program_Line_452='if CAT==80',
            Program_Line_453='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_454='elseif CAT==85',
            Program_Line_455='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_456='elseif CAT==90',
            Program_Line_457='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_458='endif',
            Program_Line_459='endif',
            Program_Line_460='endif',
            Program_Line_461='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_462='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_463='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_464='else',
            Program_Line_465='if CAT==80',
            Program_Line_466='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_467='elseif CAT==85',
            Program_Line_468='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_469='elseif CAT==90',
            Program_Line_470='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_471='endif',
            Program_Line_472='endif',
            Program_Line_473='endif',
            Program_Line_474='if (ComfStand == 7) && (ComfMod == 1)',
            Program_Line_475='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_476='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_477='else',
            Program_Line_478='if CAT==80',
            Program_Line_479='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_480='elseif CAT==85',
            Program_Line_481='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_482='elseif CAT==90',
            Program_Line_483='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_484='endif',
            Program_Line_485='endif',
            Program_Line_486='endif',
            Program_Line_487='!NUEVO HASTA AQUI!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',
            Program_Line_488='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_489='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_490='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_491='elseif CAT==80',
            Program_Line_492='if PMOT < ACSTall',
            Program_Line_493='set ACST = 26.35+ACSTtol',
            Program_Line_494='elseif PMOT > ACSTaul',
            Program_Line_495='set ACST = 28.35+ACSTtol',
            Program_Line_496='endif',
            Program_Line_497='elseif CAT==85',
            Program_Line_498='if PMOT < ACSTall',
            Program_Line_499='set ACST = 25.72+ACSTtol',
            Program_Line_500='elseif PMOT > ACSTaul',
            Program_Line_501='set ACST = 27.89+ACSTtol',
            Program_Line_502='endif',
            Program_Line_503='elseif CAT==90',
            Program_Line_504='if PMOT < ACSTall',
            Program_Line_505='set ACST = 25.09+ACSTtol',
            Program_Line_506='elseif PMOT > ACSTaul',
            Program_Line_507='set ACST = 27.42+ACSTtol',
            Program_Line_508='endif',
            Program_Line_509='endif',
            Program_Line_510='endif',
            Program_Line_511='if (ComfStand == 7) && (ComfMod == 2)',
            Program_Line_512='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_513='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_514='elseif CAT==80',
            Program_Line_515='if PMOT < AHSTall',
            Program_Line_516='set AHST = 20.1+AHSTtol',
            Program_Line_517='elseif PMOT > AHSTaul',
            Program_Line_518='set AHST = 23.78+AHSTtol',
            Program_Line_519='endif',
            Program_Line_520='elseif CAT==85',
            Program_Line_521='if PMOT < AHSTall',
            Program_Line_522='set AHST = 20.77+AHSTtol',
            Program_Line_523='elseif PMOT > AHSTaul',
            Program_Line_524='set AHST = 24.26+AHSTtol',
            Program_Line_525='endif',
            Program_Line_526='elseif CAT==90',
            Program_Line_527='if PMOT < AHSTall',
            Program_Line_528='set AHST = 21.44+AHSTtol',
            Program_Line_529='elseif PMOT > AHSTaul',
            Program_Line_530='set AHST = 24.74+AHSTtol',
            Program_Line_531='endif',
            Program_Line_532='endif',
            Program_Line_533='endif',
            Program_Line_534='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_535='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_536='set ACST = PMOT*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_537='elseif PMOT < ACSTall',
            Program_Line_538='set ACST = ACSTall*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_539='elseif PMOT > ACSTaul',
            Program_Line_540='set ACST = ACSTaul*0.54+12.83+ACSToffset+ACSTtol',
            Program_Line_541='endif',
            Program_Line_542='endif',
            Program_Line_543='if (ComfStand == 7) && (ComfMod == 3)',
            Program_Line_544='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_545='set AHST = PMOT*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_546='elseif PMOT < AHSTall',
            Program_Line_547='set AHST = AHSTall*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_548='elseif PMOT > AHSTaul',
            Program_Line_549='set AHST = AHSTaul*0.54+12.83+AHSToffset+AHSTtol',
            Program_Line_550='endif',
            Program_Line_551='endif',
            Program_Line_552='!Nuevo_______________________',
            Program_Line_553='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_554='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_555='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_556='else',
            Program_Line_557='if CAT==80',
            Program_Line_558='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_559='elseif CAT==85',
            Program_Line_560='set ACST = PMOT*0.078+23.25+2.11+ACSTtol',
            Program_Line_561='elseif CAT==90',
            Program_Line_562='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_563='endif',
            Program_Line_564='endif',
            Program_Line_565='endif',
            Program_Line_566='if (ComfStand == 8) && (ComfMod == 1)',
            Program_Line_567='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_568='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_569='else',
            Program_Line_570='if CAT==80',
            Program_Line_571='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_572='elseif CAT==85',
            Program_Line_573='set AHST = PMOT*0.078+23.25-2.11+AHSTtol',
            Program_Line_574='elseif CAT==90',
            Program_Line_575='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_576='endif',
            Program_Line_577='endif',
            Program_Line_578='endif',
            Program_Line_579='!Nuevo hasta aqui__________',
            Program_Line_580='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_581='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_582='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_583='elseif CAT==80',
            Program_Line_584='if PMOT < ACSTall',
            Program_Line_585='set ACST = 26.35+ACSTtol',
            Program_Line_586='elseif PMOT > ACSTaul',
            Program_Line_587='set ACST = 28.35+ACSTtol',
            Program_Line_588='endif',
            Program_Line_589='elseif CAT==85',
            Program_Line_590='if PMOT < ACSTall',
            Program_Line_591='set ACST = 25.72+ACSTtol',
            Program_Line_592='elseif PMOT > ACSTaul',
            Program_Line_593='set ACST = 27.89+ACSTtol',
            Program_Line_594='endif',
            Program_Line_595='elseif CAT==90',
            Program_Line_596='if PMOT < ACSTall',
            Program_Line_597='set ACST = 25.09+ACSTtol',
            Program_Line_598='elseif PMOT > ACSTaul',
            Program_Line_599='set ACST = 27.42+ACSTtol',
            Program_Line_600='endif',
            Program_Line_601='endif',
            Program_Line_602='endif',
            Program_Line_603='if (ComfStand == 8) && (ComfMod == 2)',
            Program_Line_604='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_605='set AHST = PMOT*0.28+17.87+AHSToffset+AHSTtol',
            Program_Line_606='elseif CAT==80',
            Program_Line_607='if PMOT < AHSTall',
            Program_Line_608='set AHST = 20.1+AHSTtol',
            Program_Line_609='elseif PMOT > AHSTaul',
            Program_Line_610='set AHST = 23.78+AHSTtol',
            Program_Line_611='endif',
            Program_Line_612='elseif CAT==85',
            Program_Line_613='if PMOT < AHSTall',
            Program_Line_614='set AHST = 20.77+AHSTtol',
            Program_Line_615='elseif PMOT > AHSTaul',
            Program_Line_616='set AHST = 24.26+AHSTtol',
            Program_Line_617='endif',
            Program_Line_618='elseif CAT==90',
            Program_Line_619='if PMOT < AHSTall',
            Program_Line_620='set AHST = 21.44+AHSTtol',
            Program_Line_621='elseif PMOT > AHSTaul',
            Program_Line_622='set AHST = 24.74+AHSTtol',
            Program_Line_623='endif',
            Program_Line_624='endif',
            Program_Line_625='endif',
            Program_Line_626='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_627='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_628='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_629='elseif PMOT < ACSTall',
            Program_Line_630='set ACST = ACSTall*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_631='elseif PMOT > ACSTaul',
            Program_Line_632='set ACST = ACSTaul*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_633='endif',
            Program_Line_634='endif',
            Program_Line_635='if (ComfStand == 8) && (ComfMod == 3)',
            Program_Line_636='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
            Program_Line_637='set ACST = PMOT*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_638='elseif PMOT < ACSTall',
            Program_Line_639='set ACST = ACSTall*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_640='elseif PMOT > ACSTaul',
            Program_Line_641='set ACST = ACSTaul*0.28+17.87+ACSToffset+ACSTtol',
            Program_Line_642='endif',
            Program_Line_643='endif',
            Program_Line_644='!Nuevo_______________________',
            Program_Line_645='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_646='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_647='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_648='else',
            Program_Line_649='if CAT==80',
            Program_Line_650='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_651='elseif CAT==90',
            Program_Line_652='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_653='endif',
            Program_Line_654='endif',
            Program_Line_655='endif',
            Program_Line_656='if (ComfStand == 9) && (ComfMod == 1)',
            Program_Line_657='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_658='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_659='else',
            Program_Line_660='if CAT==80',
            Program_Line_661='set AHST = PMOT*0.078+23.25+2.72+AHSTtol',
            Program_Line_662='elseif CAT==90',
            Program_Line_663='set AHST = PMOT*0.078+23.25+1.5+AHSTtol',
            Program_Line_664='endif',
            Program_Line_665='endif',
            Program_Line_666='endif',
            Program_Line_667='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_668='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_669='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_670='elseif CAT==80',
            Program_Line_671='if PMOT < ACSTall',
            Program_Line_672='set ACST = 26.35+ACSTtol',
            Program_Line_673='elseif PMOT > ACSTaul',
            Program_Line_674='set ACST = 28.35+ACSTtol',
            Program_Line_675='endif',
            Program_Line_676='elseif CAT==90',
            Program_Line_677='if PMOT < ACSTall',
            Program_Line_678='set ACST = 25.09+ACSTtol',
            Program_Line_679='elseif PMOT > ACSTaul',
            Program_Line_680='set ACST = 27.42+ACSTtol',
            Program_Line_681='endif',
            Program_Line_682='endif',
            Program_Line_683='endif',
            Program_Line_684='if (ComfStand == 9) && (ComfMod == 2)',
            Program_Line_685='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_686='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_687='elseif CAT==80',
            Program_Line_688='if PMOT < AHSTall',
            Program_Line_689='set AHST = 20.1+AHSTtol',
            Program_Line_690='elseif PMOT > AHSTaul',
            Program_Line_691='set AHST = 23.78+AHSTtol',
            Program_Line_692='endif',
            Program_Line_693='elseif CAT==90',
            Program_Line_694='if PMOT < AHSTall',
            Program_Line_695='set AHST = 21.44+AHSTtol',
            Program_Line_696='elseif PMOT > AHSTaul',
            Program_Line_697='set AHST = 24.74+AHSTtol',
            Program_Line_698='endif',
            Program_Line_699='endif',
            Program_Line_700='endif',
            Program_Line_701='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_702='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_703='set ACST = PMOT*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_704='elseif PMOT < ACSTall',
            Program_Line_705='set ACST = ACSTall*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_706='elseif PMOT > ACSTaul',
            Program_Line_707='set ACST = ACSTaul*0.39+18.42+ACSToffset+ACSTtol',
            Program_Line_708='endif',
            Program_Line_709='endif',
            Program_Line_710='if (ComfStand == 9) && (ComfMod == 3)',
            Program_Line_711='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_712='set AHST = PMOT*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_713='elseif PMOT < AHSTall',
            Program_Line_714='set AHST = AHSTall*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_715='elseif PMOT > AHSTaul',
            Program_Line_716='set AHST = AHSTaul*0.39+18.42+AHSToffset+AHSTtol',
            Program_Line_717='endif',
            Program_Line_718='endif',
            Program_Line_719='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_720='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_721='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_722='else',
            Program_Line_723='if CAT==80',
            Program_Line_724='set ACST = RMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_725='elseif CAT==90',
            Program_Line_726='set ACST = RMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_727='endif',
            Program_Line_728='endif',
            Program_Line_729='endif',
            Program_Line_730='if (ComfStand == 10) && (ComfMod == 1)',
            Program_Line_731='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_732='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_733='else',
            Program_Line_734='if CAT==80',
            Program_Line_735='set AHST = RMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_736='elseif CAT==90',
            Program_Line_737='set AHST = RMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_738='endif',
            Program_Line_739='endif',
            Program_Line_740='endif',
            Program_Line_741='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_742='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_743='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_744='elseif CAT==80',
            Program_Line_745='if RMOT < ACSTall',
            Program_Line_746='set ACST = 26.35+ACSTtol',
            Program_Line_747='elseif RMOT > ACSTaul',
            Program_Line_748='set ACST = 28.35+ACSTtol',
            Program_Line_749='endif',
            Program_Line_750='elseif CAT==90',
            Program_Line_751='if RMOT < ACSTall',
            Program_Line_752='set ACST = 25.09+ACSTtol',
            Program_Line_753='elseif RMOT > ACSTaul',
            Program_Line_754='set ACST = 27.42+ACSTtol',
            Program_Line_755='endif',
            Program_Line_756='endif',
            Program_Line_757='endif',
            Program_Line_758='if (ComfStand == 10) && (ComfMod == 2)',
            Program_Line_759='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_760='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_761='elseif CAT==80',
            Program_Line_762='if RMOT < AHSTall',
            Program_Line_763='set AHST = 20.1+AHSTtol',
            Program_Line_764='elseif RMOT > AHSTaul',
            Program_Line_765='set AHST = 23.78+AHSTtol',
            Program_Line_766='endif',
            Program_Line_767='elseif CAT==90',
            Program_Line_768='if RMOT < AHSTall',
            Program_Line_769='set AHST = 21.44+AHSTtol',
            Program_Line_770='elseif RMOT > AHSTaul',
            Program_Line_771='set AHST = 24.74+AHSTtol',
            Program_Line_772='endif',
            Program_Line_773='endif',
            Program_Line_774='endif',
            Program_Line_775='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_776='if (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_777='set ACST = RMOT*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_778='elseif RMOT < ACSTall',
            Program_Line_779='set ACST = ACSTall*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_780='elseif RMOT > ACSTaul',
            Program_Line_781='set ACST = ACSTaul*0.42+17.6+ACSToffset+ACSTtol',
            Program_Line_782='endif',
            Program_Line_783='endif',
            Program_Line_784='if (ComfStand == 10) && (ComfMod == 3)',
            Program_Line_785='if (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_786='set AHST = RMOT*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_787='elseif RMOT < AHSTall',
            Program_Line_788='set AHST = AHSTall*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_789='elseif RMOT > AHSTaul',
            Program_Line_790='set AHST = AHSTaul*0.42+17.6+AHSToffset+AHSTtol',
            Program_Line_791='endif',
            Program_Line_792='endif',
            Program_Line_793='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_794='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_795='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_796='else',
            Program_Line_797='if CAT==80',
            Program_Line_798='set ACST = PMOT*0.078+23.25+2.72+ACSTtol',
            Program_Line_799='elseif CAT==90',
            Program_Line_800='set ACST = PMOT*0.078+23.25+1.5+ACSTtol',
            Program_Line_801='endif',
            Program_Line_802='endif',
            Program_Line_803='endif',
            Program_Line_804='if (ComfStand == 11) && (ComfMod == 1)',
            Program_Line_805='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_806='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_807='else',
            Program_Line_808='if CAT==80',
            Program_Line_809='set AHST = PMOT*0.078+23.25-2.72+AHSTtol',
            Program_Line_810='elseif CAT==90',
            Program_Line_811='set AHST = PMOT*0.078+23.25-1.5+AHSTtol',
            Program_Line_812='endif',
            Program_Line_813='endif',
            Program_Line_814='endif',
            Program_Line_815='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_816='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_817='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_818='elseif CAT==80',
            Program_Line_819='if PMOT < ACSTall',
            Program_Line_820='set ACST = 26.35+ACSTtol',
            Program_Line_821='elseif PMOT > ACSTaul',
            Program_Line_822='set ACST = 28.35+ACSTtol',
            Program_Line_823='endif',
            Program_Line_824='elseif CAT==90',
            Program_Line_825='if PMOT < ACSTall',
            Program_Line_826='set ACST = 25.09+ACSTtol',
            Program_Line_827='elseif PMOT > ACSTaul',
            Program_Line_828='set ACST = 27.42+ACSTtol',
            Program_Line_829='endif',
            Program_Line_830='endif',
            Program_Line_831='endif',
            Program_Line_832='if (ComfStand == 11) && (ComfMod == 2)',
            Program_Line_833='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_834='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_835='elseif CAT==80',
            Program_Line_836='if PMOT < AHSTall',
            Program_Line_837='set AHST = 20.1+AHSTtol',
            Program_Line_838='elseif PMOT > AHSTaul',
            Program_Line_839='set AHST = 23.78+AHSTtol',
            Program_Line_840='endif',
            Program_Line_841='elseif CAT==90',
            Program_Line_842='if PMOT < AHSTall',
            Program_Line_843='set AHST = 21.44+AHSTtol',
            Program_Line_844='elseif PMOT > AHSTaul',
            Program_Line_845='set AHST = 24.74+AHSTtol',
            Program_Line_846='endif',
            Program_Line_847='endif',
            Program_Line_848='endif',
            Program_Line_849='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_850='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_851='set ACST = PMOT*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_852='elseif PMOT < ACSTall',
            Program_Line_853='set ACST = ACSTall*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_854='elseif PMOT > ACSTaul',
            Program_Line_855='set ACST = ACSTaul*0.75+5.37+ACSToffset+ACSTtol',
            Program_Line_856='endif',
            Program_Line_857='endif',
            Program_Line_858='if (ComfStand == 11) && (ComfMod == 3)',
            Program_Line_859='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_860='set AHST = PMOT*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_861='elseif PMOT < AHSTall',
            Program_Line_862='set AHST = AHSTall*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_863='elseif PMOT > AHSTaul',
            Program_Line_864='set AHST = AHSTaul*0.75+5.37+AHSToffset+AHSTtol',
            Program_Line_865='endif',
            Program_Line_866='endif',
            Program_Line_867='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_868='if (CAT==80)',
            Program_Line_869='set ACST = 27+ACSTtol',
            Program_Line_870='elseif (CAT==90)',
            Program_Line_871='set ACST = 25.5+ACSTtol',
            Program_Line_872='endif',
            Program_Line_873='endif',
            Program_Line_874='if (ComfStand == 12) && (ComfMod == 0)',
            Program_Line_875='if (CAT==80)',
            Program_Line_876='set AHST = 20+AHSTtol',
            Program_Line_877='elseif (CAT==90)',
            Program_Line_878='set AHST = 21.5+AHSTtol',
            Program_Line_879='endif',
            Program_Line_880='endif',
            Program_Line_881='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_882='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_883='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_884='elseif CAT==80',
            Program_Line_885='if PMOT < ACSTall',
            Program_Line_886='set ACST = 27+ACSTtol',
            Program_Line_887='elseif PMOT > ACSTaul',
            Program_Line_888='set ACST = 27+ACSTtol',
            Program_Line_889='endif',
            Program_Line_890='elseif CAT==90',
            Program_Line_891='if PMOT < ACSTall',
            Program_Line_892='set ACST = 25.5+ACSTtol',
            Program_Line_893='elseif PMOT > ACSTaul',
            Program_Line_894='set ACST = 25.5+ACSTtol',
            Program_Line_895='endif',
            Program_Line_896='endif',
            Program_Line_897='endif',
            Program_Line_898='if (ComfStand == 12) && (ComfMod == 1)',
            Program_Line_899='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_900='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_901='elseif CAT==80',
            Program_Line_902='if PMOT < AHSTall',
            Program_Line_903='set AHST = 20+AHSTtol',
            Program_Line_904='elseif PMOT > AHSTaul',
            Program_Line_905='set AHST = 20+AHSTtol',
            Program_Line_906='endif',
            Program_Line_907='elseif CAT==90',
            Program_Line_908='if PMOT < AHSTall',
            Program_Line_909='set AHST = 21.5+AHSTtol',
            Program_Line_910='elseif PMOT > AHSTaul',
            Program_Line_911='set AHST = 21.5+AHSTtol',
            Program_Line_912='endif',
            Program_Line_913='endif',
            Program_Line_914='endif',
            Program_Line_915='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_916='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_917='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_918='elseif CAT==80',
            Program_Line_919='if PMOT < ACSTall',
            Program_Line_920='set ACST = 26.35+ACSTtol',
            Program_Line_921='elseif PMOT > ACSTaul',
            Program_Line_922='set ACST = 28.35+ACSTtol',
            Program_Line_923='endif',
            Program_Line_924='elseif CAT==90',
            Program_Line_925='if PMOT < ACSTall',
            Program_Line_926='set ACST = 25.09+ACSTtol',
            Program_Line_927='elseif PMOT > ACSTaul',
            Program_Line_928='set ACST = 27.42+ACSTtol',
            Program_Line_929='endif',
            Program_Line_930='endif',
            Program_Line_931='endif',
            Program_Line_932='if (ComfStand == 12) && (ComfMod == 2)',
            Program_Line_933='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_934='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_935='elseif CAT==80',
            Program_Line_936='if PMOT < AHSTall',
            Program_Line_937='set AHST = 20.1+AHSTtol',
            Program_Line_938='elseif PMOT > AHSTaul',
            Program_Line_939='set AHST = 23.78+AHSTtol',
            Program_Line_940='endif',
            Program_Line_941='elseif CAT==90',
            Program_Line_942='if PMOT < AHSTall',
            Program_Line_943='set AHST = 21.44+AHSTtol',
            Program_Line_944='elseif PMOT > AHSTaul',
            Program_Line_945='set AHST = 24.74+AHSTtol',
            Program_Line_946='endif',
            Program_Line_947='endif',
            Program_Line_948='endif',
            Program_Line_949='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_950='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_951='set ACST = PMOT*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_952='elseif PMOT < ACSTall',
            Program_Line_953='set ACST = ACSTall*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_954='elseif PMOT > ACSTaul',
            Program_Line_955='set ACST = ACSTaul*0.25+19.7+ACSToffset+ACSTtol',
            Program_Line_956='endif',
            Program_Line_957='endif',
            Program_Line_958='if (ComfStand == 12) && (ComfMod == 3)',
            Program_Line_959='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_960='set AHST = PMOT*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_961='elseif PMOT < AHSTall',
            Program_Line_962='set AHST = AHSTall*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_963='elseif PMOT > AHSTaul',
            Program_Line_964='set AHST = AHSTaul*0.25+19.7+AHSToffset+AHSTtol',
            Program_Line_965='endif',
            Program_Line_966='endif',
            Program_Line_967='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_968='if (ComfMod == 0)',
            Program_Line_969='if (CAT==80)',
            Program_Line_970='set ACST = 28+ACSTtol',
            Program_Line_971='elseif (CAT==90)',
            Program_Line_972='set ACST = 26+ACSTtol',
            Program_Line_973='endif',
            Program_Line_974='endif',
            Program_Line_975='endif',
            Program_Line_976='if (ComfStand == 13) || (ComfStand == 14)',
            Program_Line_977='if (ComfMod == 0)',
            Program_Line_978='if (CAT==80)',
            Program_Line_979='set AHST = 20+AHSTtol',
            Program_Line_980='elseif (CAT==90)',
            Program_Line_981='set AHST = 21+AHSTtol',
            Program_Line_982='endif',
            Program_Line_983='endif',
            Program_Line_984='endif',
            Program_Line_985='if (ComfStand == 13) && (ComfMod == 1)',
            Program_Line_986='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_987='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_988='elseif CAT==80',
            Program_Line_989='if PMOT < ACSTall',
            Program_Line_990='set ACST = 28+ACSTtol',
            Program_Line_991='elseif PMOT > ACSTaul',
            Program_Line_992='set ACST = 28+ACSTtol',
            Program_Line_993='endif',
            Program_Line_994='elseif CAT==90',
            Program_Line_995='if PMOT < ACSTall',
            Program_Line_996='set ACST = 26+ACSTtol',
            Program_Line_997='elseif PMOT > ACSTaul',
            Program_Line_998='set ACST = 26+ACSTtol',
            Program_Line_999='endif',
            Program_Line_1000='endif',
            Program_Line_1001='endif',
            Program_Line_1002='if (ComfStand == 13) && (ComfMod == 1)',
            Program_Line_1003='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1004='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1005='elseif CAT==80',
            Program_Line_1006='if PMOT < AHSTall',
            Program_Line_1007='set AHST = 20+AHSTtol',
            Program_Line_1008='elseif PMOT > AHSTaul',
            Program_Line_1009='set AHST = 20+AHSTtol',
            Program_Line_1010='endif',
            Program_Line_1011='elseif CAT==90',
            Program_Line_1012='if PMOT < AHSTall',
            Program_Line_1013='set AHST = 21+AHSTtol',
            Program_Line_1014='elseif PMOT > AHSTaul',
            Program_Line_1015='set AHST = 21+AHSTtol',
            Program_Line_1016='endif',
            Program_Line_1017='endif',
            Program_Line_1018='endif',
            Program_Line_1019='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1020='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1021='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1022='elseif CAT==80',
            Program_Line_1023='if PMOT < ACSTall',
            Program_Line_1024='set ACST = 26.35+ACSTtol',
            Program_Line_1025='elseif PMOT > ACSTaul',
            Program_Line_1026='set ACST = 28.35+ACSTtol',
            Program_Line_1027='endif',
            Program_Line_1028='elseif CAT==90',
            Program_Line_1029='if PMOT < ACSTall',
            Program_Line_1030='set ACST = 25.09+ACSTtol',
            Program_Line_1031='elseif PMOT > ACSTaul',
            Program_Line_1032='set ACST = 27.42+ACSTtol',
            Program_Line_1033='endif',
            Program_Line_1034='endif',
            Program_Line_1035='endif',
            Program_Line_1036='if (ComfStand == 13) && (ComfMod == 2)',
            Program_Line_1037='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1038='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1039='elseif CAT==80',
            Program_Line_1040='if PMOT < AHSTall',
            Program_Line_1041='set AHST = 20.1+AHSTtol',
            Program_Line_1042='elseif PMOT > AHSTaul',
            Program_Line_1043='set AHST = 23.78+AHSTtol',
            Program_Line_1044='endif',
            Program_Line_1045='elseif CAT==90',
            Program_Line_1046='if PMOT < AHSTall',
            Program_Line_1047='set AHST = 21.44+AHSTtol',
            Program_Line_1048='elseif PMOT > AHSTaul',
            Program_Line_1049='set AHST = 24.74+AHSTtol',
            Program_Line_1050='endif',
            Program_Line_1051='endif',
            Program_Line_1052='endif',
            Program_Line_1053='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1054='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1055='set ACST = PMOT*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1056='elseif PMOT < ACSTall',
            Program_Line_1057='set ACST = ACSTall*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1058='elseif PMOT > ACSTaul',
            Program_Line_1059='set ACST = ACSTaul*0.26+15.9+ACSToffset+ACSTtol',
            Program_Line_1060='endif',
            Program_Line_1061='endif',
            Program_Line_1062='if (ComfStand == 13) && (ComfMod == 3)',
            Program_Line_1063='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1064='set AHST = PMOT*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1065='elseif PMOT < AHSTall',
            Program_Line_1066='set AHST = AHSTall*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1067='elseif PMOT > AHSTaul',
            Program_Line_1068='set AHST = AHSTaul*0.26+15.9+AHSToffset+AHSTtol',
            Program_Line_1069='endif',
            Program_Line_1070='endif',
            Program_Line_1071='if (ComfStand == 14) && (ComfMod == 1)',
            Program_Line_1072='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1073='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1074='elseif CAT==80',
            Program_Line_1075='if PMOT < ACSTall',
            Program_Line_1076='set ACST = 28+ACSTtol',
            Program_Line_1077='elseif PMOT > ACSTaul',
            Program_Line_1078='set ACST = 28+ACSTtol',
            Program_Line_1079='endif',
            Program_Line_1080='elseif CAT==90',
            Program_Line_1081='if PMOT < ACSTall',
            Program_Line_1082='set ACST = 26+ACSTtol',
            Program_Line_1083='elseif PMOT > ACSTaul',
            Program_Line_1084='set ACST = 26+ACSTtol',
            Program_Line_1085='endif',
            Program_Line_1086='endif',
            Program_Line_1087='endif',
            Program_Line_1088='if (ComfStand == 14) && (ComfMod == 1)',
            Program_Line_1089='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1090='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1091='elseif CAT==80',
            Program_Line_1092='if PMOT < AHSTall',
            Program_Line_1093='set AHST = 20+AHSTtol',
            Program_Line_1094='elseif PMOT > AHSTaul',
            Program_Line_1095='set AHST = 20+AHSTtol',
            Program_Line_1096='endif',
            Program_Line_1097='elseif CAT==90',
            Program_Line_1098='if PMOT < AHSTall',
            Program_Line_1099='set AHST = 21+AHSTtol',
            Program_Line_1100='elseif PMOT > AHSTaul',
            Program_Line_1101='set AHST = 21+AHSTtol',
            Program_Line_1102='endif',
            Program_Line_1103='endif',
            Program_Line_1104='endif',
            Program_Line_1105='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1106='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1107='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1108='elseif CAT==80',
            Program_Line_1109='if PMOT < ACSTall',
            Program_Line_1110='set ACST = 26.35+ACSTtol',
            Program_Line_1111='elseif PMOT > ACSTaul',
            Program_Line_1112='set ACST = 28.35+ACSTtol',
            Program_Line_1113='endif',
            Program_Line_1114='elseif CAT==90',
            Program_Line_1115='if PMOT < ACSTall',
            Program_Line_1116='set ACST = 25.09+ACSTtol',
            Program_Line_1117='elseif PMOT > ACSTaul',
            Program_Line_1118='set ACST = 27.42+ACSTtol',
            Program_Line_1119='endif',
            Program_Line_1120='endif',
            Program_Line_1121='endif',
            Program_Line_1122='if (ComfStand == 14) && (ComfMod == 2)',
            Program_Line_1123='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1124='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1125='elseif CAT==80',
            Program_Line_1126='if PMOT < AHSTall',
            Program_Line_1127='set AHST = 20.1+AHSTtol',
            Program_Line_1128='elseif PMOT > AHSTaul',
            Program_Line_1129='set AHST = 23.78+AHSTtol',
            Program_Line_1130='endif',
            Program_Line_1131='elseif CAT==90',
            Program_Line_1132='if PMOT < AHSTall',
            Program_Line_1133='set AHST = 21.44+AHSTtol',
            Program_Line_1134='elseif PMOT > AHSTaul',
            Program_Line_1135='set AHST = 24.74+AHSTtol',
            Program_Line_1136='endif',
            Program_Line_1137='endif',
            Program_Line_1138='endif',
            Program_Line_1139='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1140='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1141='set ACST = PMOT*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1142='elseif PMOT < ACSTall',
            Program_Line_1143='set ACST = ACSTall*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1144='elseif PMOT > ACSTaul',
            Program_Line_1145='set ACST = ACSTaul*0.26+16.75+ACSToffset+ACSTtol',
            Program_Line_1146='endif',
            Program_Line_1147='endif',
            Program_Line_1148='if (ComfStand == 14) && (ComfMod == 3)',
            Program_Line_1149='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1150='set AHST = PMOT*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1151='elseif PMOT < AHSTall',
            Program_Line_1152='set AHST = AHSTall*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1153='elseif PMOT > AHSTaul',
            Program_Line_1154='set AHST = AHSTaul*0.26+16.75+AHSToffset+AHSTtol',
            Program_Line_1155='endif',
            Program_Line_1156='endif',
            Program_Line_1157='if (ComfStand == 15) || (ComfStand == 16)',
            Program_Line_1158='if (ComfMod == 0)',
            Program_Line_1159='if (CAT==80)',
            Program_Line_1160='set ACST = 26+ACSTtol',
            Program_Line_1161='elseif (CAT==90)',
            Program_Line_1162='set ACST = 25+ACSTtol',
            Program_Line_1163='endif',
            Program_Line_1164='endif',
            Program_Line_1165='endif',
            Program_Line_1166='if (ComfStand == 15) || (ComfStand == 16)',
            Program_Line_1167='if (ComfMod == 0)',
            Program_Line_1168='if (CAT==80)',
            Program_Line_1169='set AHST = 22+AHSTtol',
            Program_Line_1170='elseif (CAT==90)',
            Program_Line_1171='set AHST = 23+AHSTtol',
            Program_Line_1172='endif',
            Program_Line_1173='endif',
            Program_Line_1174='endif',
            Program_Line_1175='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1176='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1177='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1178='elseif CAT==80',
            Program_Line_1179='if PMOT < ACSTall',
            Program_Line_1180='set ACST = 26+ACSTtol',
            Program_Line_1181='elseif PMOT > ACSTaul',
            Program_Line_1182='set ACST = 26+ACSTtol',
            Program_Line_1183='endif',
            Program_Line_1184='elseif CAT==90',
            Program_Line_1185='if PMOT < ACSTall',
            Program_Line_1186='set ACST = 25+ACSTtol',
            Program_Line_1187='elseif PMOT > ACSTaul',
            Program_Line_1188='set ACST = 25+ACSTtol',
            Program_Line_1189='endif',
            Program_Line_1190='endif',
            Program_Line_1191='endif',
            Program_Line_1192='if (ComfStand == 15) && (ComfMod == 1)',
            Program_Line_1193='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1194='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1195='elseif CAT==80',
            Program_Line_1196='if PMOT < AHSTall',
            Program_Line_1197='set AHST = 22+AHSTtol',
            Program_Line_1198='elseif PMOT > AHSTaul',
            Program_Line_1199='set AHST = 22+AHSTtol',
            Program_Line_1200='endif',
            Program_Line_1201='elseif CAT==90',
            Program_Line_1202='if PMOT < AHSTall',
            Program_Line_1203='set AHST = 23+AHSTtol',
            Program_Line_1204='elseif PMOT > AHSTaul',
            Program_Line_1205='set AHST = 23+AHSTtol',
            Program_Line_1206='endif',
            Program_Line_1207='endif',
            Program_Line_1208='endif',
            Program_Line_1209='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1210='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1211='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1212='elseif CAT==80',
            Program_Line_1213='if PMOT < ACSTall',
            Program_Line_1214='set ACST = 26.35+ACSTtol',
            Program_Line_1215='elseif PMOT > ACSTaul',
            Program_Line_1216='set ACST = 28.35+ACSTtol',
            Program_Line_1217='endif',
            Program_Line_1218='elseif CAT==90',
            Program_Line_1219='if PMOT < ACSTall',
            Program_Line_1220='set ACST = 25.09+ACSTtol',
            Program_Line_1221='elseif PMOT > ACSTaul',
            Program_Line_1222='set ACST = 27.42+ACSTtol',
            Program_Line_1223='endif',
            Program_Line_1224='endif',
            Program_Line_1225='endif',
            Program_Line_1226='if (ComfStand == 15) && (ComfMod == 2)',
            Program_Line_1227='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1228='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1229='elseif CAT==80',
            Program_Line_1230='if PMOT < AHSTall',
            Program_Line_1231='set AHST = 20.1+AHSTtol',
            Program_Line_1232='elseif PMOT > AHSTaul',
            Program_Line_1233='set AHST = 23.78+AHSTtol',
            Program_Line_1234='endif',
            Program_Line_1235='elseif CAT==90',
            Program_Line_1236='if PMOT < AHSTall',
            Program_Line_1237='set AHST = 21.44+AHSTtol',
            Program_Line_1238='elseif PMOT > AHSTaul',
            Program_Line_1239='set AHST = 24.74+AHSTtol',
            Program_Line_1240='endif',
            Program_Line_1241='endif',
            Program_Line_1242='endif',
            Program_Line_1243='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1244='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1245='set ACST = PMOT*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1246='elseif PMOT < ACSTall',
            Program_Line_1247='set ACST = ACSTall*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1248='elseif PMOT > ACSTaul',
            Program_Line_1249='set ACST = ACSTaul*0.56+12.74+ACSToffset+ACSTtol',
            Program_Line_1250='endif',
            Program_Line_1251='endif',
            Program_Line_1252='if (ComfStand == 15) && (ComfMod == 3)',
            Program_Line_1253='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1254='set AHST = PMOT*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1255='elseif PMOT < AHSTall',
            Program_Line_1256='set AHST = AHSTall*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1257='elseif PMOT > AHSTaul',
            Program_Line_1258='set AHST = AHSTaul*0.56+12.74+AHSToffset+AHSTtol',
            Program_Line_1259='endif',
            Program_Line_1260='endif',
            Program_Line_1261='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1262='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1263='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1264='elseif CAT==80',
            Program_Line_1265='if PMOT < ACSTall',
            Program_Line_1266='set ACST = 26+ACSTtol',
            Program_Line_1267='elseif PMOT > ACSTaul',
            Program_Line_1268='set ACST = 26+ACSTtol',
            Program_Line_1269='endif',
            Program_Line_1270='elseif CAT==90',
            Program_Line_1271='if PMOT < ACSTall',
            Program_Line_1272='set ACST = 25+ACSTtol',
            Program_Line_1273='elseif PMOT > ACSTaul',
            Program_Line_1274='set ACST = 25+ACSTtol',
            Program_Line_1275='endif',
            Program_Line_1276='endif',
            Program_Line_1277='endif',
            Program_Line_1278='if (ComfStand == 16) && (ComfMod == 1)',
            Program_Line_1279='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1280='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1281='elseif CAT==80',
            Program_Line_1282='if PMOT < AHSTall',
            Program_Line_1283='set AHST = 22+AHSTtol',
            Program_Line_1284='elseif PMOT > AHSTaul',
            Program_Line_1285='set AHST = 22+AHSTtol',
            Program_Line_1286='endif',
            Program_Line_1287='elseif CAT==90',
            Program_Line_1288='if PMOT < AHSTall',
            Program_Line_1289='set AHST = 23+AHSTtol',
            Program_Line_1290='elseif PMOT > AHSTaul',
            Program_Line_1291='set AHST = 23+AHSTtol',
            Program_Line_1292='endif',
            Program_Line_1293='endif',
            Program_Line_1294='endif',
            Program_Line_1295='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1296='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1297='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1298='elseif CAT==80',
            Program_Line_1299='if PMOT < ACSTall',
            Program_Line_1300='set ACST = 26.35+ACSTtol',
            Program_Line_1301='elseif PMOT > ACSTaul',
            Program_Line_1302='set ACST = 28.35+ACSTtol',
            Program_Line_1303='endif',
            Program_Line_1304='elseif CAT==90',
            Program_Line_1305='if PMOT < ACSTall',
            Program_Line_1306='set ACST = 25.09+ACSTtol',
            Program_Line_1307='elseif PMOT > ACSTaul',
            Program_Line_1308='set ACST = 27.42+ACSTtol',
            Program_Line_1309='endif',
            Program_Line_1310='endif',
            Program_Line_1311='endif',
            Program_Line_1312='if (ComfStand == 16) && (ComfMod == 2)',
            Program_Line_1313='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1314='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1315='elseif CAT==80',
            Program_Line_1316='if PMOT < AHSTall',
            Program_Line_1317='set AHST = 20.1+AHSTtol',
            Program_Line_1318='elseif PMOT > AHSTaul',
            Program_Line_1319='set AHST = 23.78+AHSTtol',
            Program_Line_1320='endif',
            Program_Line_1321='elseif CAT==90',
            Program_Line_1322='if PMOT < AHSTall',
            Program_Line_1323='set AHST = 21.44+AHSTtol',
            Program_Line_1324='elseif PMOT > AHSTaul',
            Program_Line_1325='set AHST = 24.74+AHSTtol',
            Program_Line_1326='endif',
            Program_Line_1327='endif',
            Program_Line_1328='endif',
            Program_Line_1329='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1330='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_1331='set ACST = PMOT*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1332='elseif PMOT < ACSTall',
            Program_Line_1333='set ACST = ACSTall*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1334='elseif PMOT > ACSTaul',
            Program_Line_1335='set ACST = ACSTaul*0.09+22.32+ACSToffset+ACSTtol',
            Program_Line_1336='endif',
            Program_Line_1337='endif',
            Program_Line_1338='if (ComfStand == 16) && (ComfMod == 3)',
            Program_Line_1339='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_1340='set AHST = PMOT*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1341='elseif PMOT < AHSTall',
            Program_Line_1342='set AHST = AHSTall*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1343='elseif PMOT > AHSTaul',
            Program_Line_1344='set AHST = AHSTaul*0.09+22.32+AHSToffset+AHSTtol',
            Program_Line_1345='endif',
            Program_Line_1346='endif',
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


