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
            Program_Line_1='if AdapStand == 1',
            Program_Line_2='set ComfTemp = RMOT*0.33+18.8',
            Program_Line_3='elseif AdapStand == 2',
            Program_Line_4='set ComfTemp = PMOT*0.31+17.8',
            Program_Line_5='elseif AdapStand == 3',
            Program_Line_6='set ComfTemp = PMOT*0.48+14.4',
            Program_Line_7='endif'
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
                Program_Line_1='if (AdapStand == 1 )',
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
                Program_Line_37='elseif (AdapStand == 2 )|| (AdapStand == 3)',
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
                Program_Line_73='endif'
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
            Program_Line_1='If AdapStand == 1',
            Program_Line_2='set ACSTaul = 30',
            Program_Line_3='set ACSTall = 10',
            Program_Line_4='set AHSTaul = 30',
            Program_Line_5='set AHSTall = 10',
            Program_Line_6='elseif AdapStand == 2',
            Program_Line_7='set ACSTaul = 33.5',
            Program_Line_8='set ACSTall = 10',
            Program_Line_9='set AHSTaul = 33.5',
            Program_Line_10='set AHSTall = 10',
            Program_Line_11='elseif AdapStand == 3',
            Program_Line_12='set ACSTaul = 30',
            Program_Line_13='set ACSTall = 5',
            Program_Line_14='set AHSTaul = 30',
            Program_Line_15='set AHSTall = 5',
            Program_Line_16='else',
            Program_Line_17='set ACSTaul = 50',
            Program_Line_18='set ACSTall = 50',
            Program_Line_19='set AHSTaul = 50',
            Program_Line_20='set AHSTall = 50',
            Program_Line_21='endif'
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
            Program_Line_1='if (AdapStand == 1 )',
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
            Program_Line_12='elseif (AdapStand == 2 ) || (AdapStand == 3)',
            Program_Line_13='if (CAT == 90)',
            Program_Line_14='set ACSToffset = 2.5',
            Program_Line_15='set AHSToffset = -2.5',
            Program_Line_16='elseif (CAT == 80)',
            Program_Line_17='set ACSToffset = 3.5',
            Program_Line_18='set AHSToffset = -3.5',
            Program_Line_19='endif',
            Program_Line_20='endif',
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
            Program_Line_1='if (AdapStand == 0) && (CurrentTime < 7)',
            Program_Line_2='set ACST = 27+ACSTtol',
            Program_Line_3='set AHST = 17+AHSTtol',
            Program_Line_4='elseif (AdapStand == 0) && (CurrentTime < 15)',
            Program_Line_5='set ACST = 25',
            Program_Line_6='set AHST = 20+AHSTtol',
            Program_Line_7='elseif (AdapStand == 0) && (CurrentTime < 23)',
            Program_Line_8='set ACST = 25+ACSTtol',
            Program_Line_9='set AHST = 20+AHSTtol',
            Program_Line_10='elseif (AdapStand == 0) && (CurrentTime < 24)',
            Program_Line_11='set ACST = 27+ACSTtol',
            Program_Line_12='set AHST = 17+AHSTtol',
            Program_Line_13='endif',
            Program_Line_14='if (AdapStand == 1) && (ComfMod == 0)',
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
            Program_Line_33='if (AdapStand == 1) && (ComfMod == 0)',
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
            Program_Line_52='if (AdapStand == 1) && (ComfMod == 1) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_53='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_54='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 7)',
            Program_Line_55='set ACST = 27+ACSTtol',
            Program_Line_56='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 15)',
            Program_Line_57='set ACST = 50',
            Program_Line_58='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 23)',
            Program_Line_59='set ACST = 25+ACSTtol',
            Program_Line_60='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 24)',
            Program_Line_61='set ACST = 27+ACSTtol',
            Program_Line_62='endif',
            Program_Line_63='if (AdapStand == 1) && (ComfMod == 1) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_64='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_65='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 7)',
            Program_Line_66='set AHST = 17+AHSTtol',
            Program_Line_67='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 23)',
            Program_Line_68='set AHST = 20+AHSTtol',
            Program_Line_69='elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 24)',
            Program_Line_70='set AHST = 17+AHSTtol',
            Program_Line_71='endif',
            Program_Line_72='if (AdapStand == 1) && (ComfMod == 2) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_73='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_74='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==1)',
            Program_Line_75='set ACST = 25+ACSTtol',
            Program_Line_76='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==1)',
            Program_Line_77='set ACST = 25.5+ACSTtol',
            Program_Line_78='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==2)',
            Program_Line_79='set ACST = 25+ACSTtol',
            Program_Line_80='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==2)',
            Program_Line_81='set ACST = 26+ACSTtol',
            Program_Line_82='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==3)',
            Program_Line_83='set ACST = 25+ACSTtol',
            Program_Line_84='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==3)',
            Program_Line_85='set ACST = 27+ACSTtol',
            Program_Line_86='endif',
            Program_Line_87='if (AdapStand == 1) && (ComfMod == 2) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_88='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_89='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==1)',
            Program_Line_90='set AHST = 21+AHSTtol',
            Program_Line_91='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==1)',
            Program_Line_92='set AHST = 23.5+AHSTtol',
            Program_Line_93='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==2)',
            Program_Line_94='set AHST = 20+AHSTtol',
            Program_Line_95='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==2)',
            Program_Line_96='set AHST = 23+AHSTtol',
            Program_Line_97='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==3)',
            Program_Line_98='set AHST = 18+AHSTtol',
            Program_Line_99='elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==3)',
            Program_Line_100='set AHST = 22+AHSTtol',
            Program_Line_101='endif',
            Program_Line_102='if (AdapStand == 1) && (ComfMod == 3) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)',
            Program_Line_103='set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_104='elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT < ACSTall)',
            Program_Line_105='set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_106='elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT > ACSTaul)',
            Program_Line_107='set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol',
            Program_Line_108='endif',
            Program_Line_109='if (AdapStand == 1) && (ComfMod == 3) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)',
            Program_Line_110='set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_111='elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT < AHSTall)',
            Program_Line_112='set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_113='elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT > AHSTaul)',
            Program_Line_114='set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol',
            Program_Line_115='endif',
            Program_Line_116='if (AdapStand == 2) && (ComfMod == 0)',
            Program_Line_117='if (DayOfYear >= 121) && (DayOfYear < 274)',
            Program_Line_118='if (CAT==80)',
            Program_Line_119='set ACST = 28.35+ACSTtol',
            Program_Line_120='elseif (CAT==90)',
            Program_Line_121='set ACST = 27.42+ACSTtol',
            Program_Line_122='endif',
            Program_Line_123='else',
            Program_Line_124='if (CAT==80)',
            Program_Line_125='set ACST = 26.35+ACSTtol',
            Program_Line_126='elseif (CAT==90)',
            Program_Line_127='set ACST = 25.09+ACSTtol',
            Program_Line_128='endif',
            Program_Line_129='endif',
            Program_Line_130='endif',
            Program_Line_131='if (AdapStand == 2) && (ComfMod == 0)',
            Program_Line_132='if (DayOfYear >= 121) && (DayOfYear < 274)',
            Program_Line_133='if (CAT==80)',
            Program_Line_134='set AHST = 23.78+AHSTtol',
            Program_Line_135='elseif (CAT==90)',
            Program_Line_136='set AHST = 24.74+AHSTtol',
            Program_Line_137='endif',
            Program_Line_138='else',
            Program_Line_139='if (CAT==80)',
            Program_Line_140='set AHST = 20.1+AHSTtol',
            Program_Line_141='elseif (CAT==90)',
            Program_Line_142='set AHST = 21.44+AHSTtol',
            Program_Line_143='endif',
            Program_Line_144='endif',
            Program_Line_145='endif',
            Program_Line_146='if (AdapStand == 2) && (ComfMod == 1) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_147='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_148='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 7)',
            Program_Line_149='set ACST = 27+ACSTtol',
            Program_Line_150='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 15)',
            Program_Line_151='set ACST = 50',
            Program_Line_152='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 23)',
            Program_Line_153='set ACST = 25+ACSTtol',
            Program_Line_154='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 24)',
            Program_Line_155='set ACST = 27+ACSTtol',
            Program_Line_156='endif',
            Program_Line_157='if (AdapStand == 2) && (ComfMod == 1) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_158='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_159='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 7)',
            Program_Line_160='set AHST = 17+AHSTtol',
            Program_Line_161='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 23)',
            Program_Line_162='set AHST = 20+AHSTtol',
            Program_Line_163='elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 24)',
            Program_Line_164='set AHST = 17+AHSTtol',
            Program_Line_165='endif',
            Program_Line_166='if (AdapStand == 2) && (ComfMod == 2)',
            Program_Line_167='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_168='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_169='elseif CAT==80',
            Program_Line_170='if PMOT < ACSTall',
            Program_Line_171='set ACST = 26.35+ACSTtol',
            Program_Line_172='elseif PMOT > ACSTaul',
            Program_Line_173='set ACST = 28.35+ACSTtol',
            Program_Line_174='endif',
            Program_Line_175='elseif CAT==90',
            Program_Line_176='if PMOT < ACSTall',
            Program_Line_177='set ACST = 25.09+ACSTtol',
            Program_Line_178='elseif PMOT > ACSTaul',
            Program_Line_179='set ACST = 27.42+ACSTtol',
            Program_Line_180='endif',
            Program_Line_181='endif',
            Program_Line_182='endif',
            Program_Line_183='if (AdapStand == 2) && (ComfMod == 2)',
            Program_Line_184='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_185='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_186='elseif CAT==80',
            Program_Line_187='if PMOT < AHSTall',
            Program_Line_188='set AHST = 20.1+AHSTtol',
            Program_Line_189='elseif PMOT > AHSTaul',
            Program_Line_190='set AHST = 23.78+AHSTtol',
            Program_Line_191='endif',
            Program_Line_192='elseif CAT==90',
            Program_Line_193='if PMOT < AHSTall',
            Program_Line_194='set AHST = 21.44+AHSTtol',
            Program_Line_195='elseif PMOT > AHSTaul',
            Program_Line_196='set AHST = 24.74+AHSTtol',
            Program_Line_197='endif',
            Program_Line_198='endif',
            Program_Line_199='endif',
            Program_Line_200='if (AdapStand == 2) && (ComfMod == 3) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_201='set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_202='elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT < ACSTall)',
            Program_Line_203='set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_204='elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT > ACSTaul)',
            Program_Line_205='set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol',
            Program_Line_206='endif',
            Program_Line_207='if (AdapStand == 2) && (ComfMod == 3) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_208='set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_209='elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT < AHSTall)',
            Program_Line_210='set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_211='elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT > AHSTaul)',
            Program_Line_212='set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol',
            Program_Line_213='endif',
            Program_Line_214='if (AdapStand == 3) && (ComfMod == 0)',
            Program_Line_215='if (CAT==80)',
            Program_Line_216='set ACST = 28+ACSTtol',
            Program_Line_217='elseif (CAT==90)',
            Program_Line_218='set ACST = 27+ACSTtol',
            Program_Line_219='endif',
            Program_Line_220='endif',
            Program_Line_221='if (AdapStand == 3) && (ComfMod == 0)',
            Program_Line_222='if (CAT==80)',
            Program_Line_223='set AHST = 18+AHSTtol',
            Program_Line_224='elseif (CAT==90)',
            Program_Line_225='set AHST = 19+AHSTtol',
            Program_Line_226='endif',
            Program_Line_227='endif',
            Program_Line_228='if (AdapStand == 3) && (ComfMod == 1)',
            Program_Line_229='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_230='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_231='elseif CAT==80',
            Program_Line_232='if PMOT < ACSTall',
            Program_Line_233='set ACST = 28+ACSTtol',
            Program_Line_234='elseif PMOT > ACSTaul',
            Program_Line_235='set ACST = 28+ACSTtol',
            Program_Line_236='endif',
            Program_Line_237='elseif CAT==90',
            Program_Line_238='if PMOT < ACSTall',
            Program_Line_239='set ACST = 27+ACSTtol',
            Program_Line_240='elseif PMOT > ACSTaul',
            Program_Line_241='set ACST = 27+ACSTtol',
            Program_Line_242='endif',
            Program_Line_243='endif',
            Program_Line_244='endif',
            Program_Line_245='if (AdapStand == 3) && (ComfMod == 1)',
            Program_Line_246='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_247='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_248='elseif CAT==80',
            Program_Line_249='if PMOT < AHSTall',
            Program_Line_250='set AHST = 18+AHSTtol',
            Program_Line_251='elseif PMOT > AHSTaul',
            Program_Line_252='set AHST = 18+AHSTtol',
            Program_Line_253='endif',
            Program_Line_254='elseif CAT==90',
            Program_Line_255='if PMOT < AHSTall',
            Program_Line_256='set AHST = 19+AHSTtol',
            Program_Line_257='elseif PMOT > AHSTaul',
            Program_Line_258='set AHST = 19+AHSTtol',
            Program_Line_259='endif',
            Program_Line_260='endif',
            Program_Line_261='endif',
            Program_Line_262='if (AdapStand == 3) && (ComfMod == 2)',
            Program_Line_263='if (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_264='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_265='elseif CAT==80',
            Program_Line_266='if PMOT < ACSTall',
            Program_Line_267='set ACST = 26.35+ACSTtol',
            Program_Line_268='elseif PMOT > ACSTaul',
            Program_Line_269='set ACST = 28.35+ACSTtol',
            Program_Line_270='endif',
            Program_Line_271='elseif CAT==90',
            Program_Line_272='if PMOT < ACSTall',
            Program_Line_273='set ACST = 25.09+ACSTtol',
            Program_Line_274='elseif PMOT > ACSTaul',
            Program_Line_275='set ACST = 27.42+ACSTtol',
            Program_Line_276='endif',
            Program_Line_277='endif',
            Program_Line_278='endif',
            Program_Line_279='if (AdapStand == 3) && (ComfMod == 2)',
            Program_Line_280='if (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_281='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_282='elseif CAT==80',
            Program_Line_283='if PMOT < AHSTall',
            Program_Line_284='set AHST = 20.1+AHSTtol',
            Program_Line_285='elseif PMOT > AHSTaul',
            Program_Line_286='set AHST = 23.78+AHSTtol',
            Program_Line_287='endif',
            Program_Line_288='elseif CAT==90',
            Program_Line_289='if PMOT < AHSTall',
            Program_Line_290='set AHST = 21.44+AHSTtol',
            Program_Line_291='elseif PMOT > AHSTaul',
            Program_Line_292='set AHST = 24.74+AHSTtol',
            Program_Line_293='endif',
            Program_Line_294='endif',
            Program_Line_295='endif',
            Program_Line_296='if (AdapStand == 3) && (ComfMod == 3) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)',
            Program_Line_297='set ACST = PMOT*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_298='elseif (AdapStand == 3) && (ComfMod == 3) && (PMOT < ACSTall)',
            Program_Line_299='set ACST = ACSTall*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_300='elseif (AdapStand == 3) && (ComfMod == 3) && (PMOT > ACSTaul)',
            Program_Line_301='set ACST = ACSTaul*0.48+14.4+ACSToffset+ACSTtol',
            Program_Line_302='endif',
            Program_Line_303='if (AdapStand == 3) && (ComfMod == 3) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)',
            Program_Line_304='set AHST = PMOT*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_305='elseif (AdapStand == 3) && (ComfMod == 3) && (PMOT < AHSTall)',
            Program_Line_306='set AHST = AHSTall*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_307='elseif (AdapStand == 3) && (ComfMod == 3) && (PMOT > AHSTaul)',
            Program_Line_308='set AHST = AHSTaul*0.48+14.4+AHSToffset+AHSTtol',
            Program_Line_309='endif',
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
            Program_Line_1='set AdapStand = 1',
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
                Program_Line_2='if AdapStand == 0',
                Program_Line_3='if (CurrentTime < 7)',
                Program_Line_4='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_5='elseif (CurrentTime < 15)',
                Program_Line_6='set VST = 22.5+VSToffset',
                Program_Line_7='elseif (CurrentTime < 23)',
                Program_Line_8='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_9='elseif (CurrentTime < 24)',
                Program_Line_10='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_11='endif',
                Program_Line_12='elseif AdapStand == 1',
                Program_Line_13='if (RMOT >= AHSTall) && (RMOT <= ACSTaul)',
                Program_Line_14='set VST = ComfTemp+VSToffset',
                Program_Line_15='else',
                Program_Line_16='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_17='endif',
                Program_Line_18='elseif AdapStand == 2 || AdapStand == 3',
                Program_Line_19='if (PMOT >= AHSTall) && (PMOT <= ACSTaul)',
                Program_Line_20='set VST = ComfTemp+VSToffset',
                Program_Line_21='else',
                Program_Line_22='set VST = (ACST+AHST)/2+VSToffset',
                Program_Line_23='endif',
                Program_Line_24='endif'
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
                    Program_Line_7='set VentHours_' + zonename + ' = 1*ZoneTimeStep',
                    Program_Line_8='else',
                    Program_Line_9='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_10='set VentHours_' + zonename + ' = 0',
                    Program_Line_11='endif',
                    Program_Line_12='else',
                    Program_Line_13='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_14='set VentHours_' + zonename + ' = 0',
                    Program_Line_15='endif',
                    Program_Line_16='else',
                    Program_Line_17='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_18='set VentHours_' + zonename + ' = 0',
                    Program_Line_19='endif',
                    Program_Line_20='else',
                    Program_Line_21='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_22='set VentHours_' + zonename + ' = 0',
                    Program_Line_23='endif',
                    Program_Line_24='else',
                    Program_Line_25='set Ventilates_HVACmode2_' + zonename + ' = 0',
                    Program_Line_26='set VentHours_' + zonename + ' = 0',
                    Program_Line_27='endif',
                    Program_Line_28='if VentCtrl == 0',
                    Program_Line_29='if ' + zonename + '_OutT < ' + zonename + '_OpT',
                    Program_Line_30='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_31='if ' + zonename + '_OpT > VST',
                    Program_Line_32='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_33='set Ventilates_HVACmode1_' + zonename + ' = 1',
                    Program_Line_34='set VentHours_' + zonename + ' = 1*ZoneTimeStep',
                    Program_Line_35='else',
                    Program_Line_36='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_37='set VentHours_' + zonename + ' = 0',
                    Program_Line_38='endif',
                    Program_Line_39='else',
                    Program_Line_40='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_41='set VentHours_' + zonename + ' = 0',
                    Program_Line_42='endif',
                    Program_Line_43='else',
                    Program_Line_44='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_45='set VentHours_' + zonename + ' = 0',
                    Program_Line_46='endif',
                    Program_Line_47='else',
                    Program_Line_48='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_49='set VentHours_' + zonename + ' = 0',
                    Program_Line_50='endif',
                    Program_Line_51='elseif VentCtrl == 1',
                    Program_Line_52='if ' + zonename + '_OutT<' + zonename + '_OpT',
                    Program_Line_53='if ' + zonename + '_OutT>MinOutTemp',
                    Program_Line_54='if ' + zonename + '_OpT > ACSTnoTol',
                    Program_Line_55='if ' + zonename + '_WindSpeed <= MaxWindSpeed',
                    Program_Line_56='set Ventilates_HVACmode1_' + zonename + ' = 1',
                    Program_Line_57='set VentHours_' + zonename + ' = 1*ZoneTimeStep',
                    Program_Line_58='else',
                    Program_Line_59='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_60='set VentHours_' + zonename + ' = 0',
                    Program_Line_61='endif',
                    Program_Line_62='else',
                    Program_Line_63='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_64='set VentHours_' + zonename + ' = 0',
                    Program_Line_65='endif',
                    Program_Line_66='else',
                    Program_Line_67='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_68='set VentHours_' + zonename + ' = 0',
                    Program_Line_69='endif',
                    Program_Line_70='else',
                    Program_Line_71='set Ventilates_HVACmode1_' + zonename + ' = 0',
                    Program_Line_72='set VentHours_' + zonename + ' = 0',
                    Program_Line_73='endif',
                    Program_Line_74='endif',
                    Program_Line_75='if HVACmode == 0',
                    Program_Line_76='set FORSCRIPT_ACST_Sch_' + zonename + ' = ACST',
                    Program_Line_77='set FORSCRIPT_AHST_Sch_' + zonename + ' = AHST',
                    Program_Line_78='elseif HVACmode == 1',
                    Program_Line_79='Set FORSCRIPT_ACST_Sch_' + zonename + ' = 100',
                    Program_Line_80='Set FORSCRIPT_AHST_Sch_' + zonename + ' = -100',
                    Program_Line_81='elseif HVACmode == 2',
                    Program_Line_82='if Ventilates_HVACmode2_' + zonename + ' == 0',
                    Program_Line_83='set FORSCRIPT_ACST_Sch_' + zonename + ' = ACST',
                    Program_Line_84='set FORSCRIPT_AHST_Sch_' + zonename + ' = AHST',
                    Program_Line_85='endif',
                    Program_Line_86='endif'
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
                    Program_Line_1='set FORSCRIPT_ACST_Sch_' + zonename + ' = ACST',
                    Program_Line_2='set FORSCRIPT_AHST_Sch_' + zonename + ' = AHST'
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
        Erl_Variable_5_Name='AdapStand',
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

    outputvariablelist = ([outputvariable.Name
                           for outputvariable
                           in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable']])
    outputlist = ([output.Variable_Name for output in self.idf1.idfobjects['Output:Variable']])
    addittionaloutputs = [
        'Zone Thermostat Operative Temperature',
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


    for outputvariable in outputvariablelist:
        if outputvariable in outputlist:
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
        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value='*',
            Variable_Name=addittionaloutput,
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - '+addittionaloutput+' Output:Variable data')

    del outputvariablelist, outputlist, addittionaloutputs,

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
            Key_Value='FORSCRIPT_AHST_'+zonename,
            Variable_Name='Schedule Value',
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - FORSCRIPT_AHST_'+zonename+' Output:Variable data')

        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value='FORSCRIPT_ACST_'+zonename,
            Variable_Name='Schedule Value',
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - FORSCRIPT_ACST_'+zonename+' Output:Variable data')

    for zonename in self.zonenames_orig:
        self.idf1.newidfobject(
            'Output:Variable',
            Key_Value=zonename,
            Variable_Name='Zone Operative Temperature',
            Reporting_Frequency='Hourly',
            Schedule_Name=''
            )
        if verboseMode:
            print('Added - '+zonename+' Zone Operative Temperature Output:Variable data')

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
        'Zone Thermostat Operative Temperature',
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
        if 'FORSCRIPT_AHST_Schedule_'+zonename in actuatorlist:
            if verboseMode:
                print('Not added - FORSCRIPT_AHST_Sch_'+zonename+' Actuator')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Actuator',
                Name='FORSCRIPT_AHST_Sch_'+zonename,
                Actuated_Component_Unique_Name='FORSCRIPT_AHST_'+zonename,
                Actuated_Component_Type='Schedule:Compact',
                Actuated_Component_Control_Type='Schedule Value'
                )
            if verboseMode:
                print('Added - FORSCRIPT_AHST_Sch_'+zonename+' Actuator')
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='FORSCRIPT_AHST_Schedule_'+zonename])

        if 'FORSCRIPT_ACST_Schedule_'+zonename in actuatorlist:
            if verboseMode:
                print('Not added - FORSCRIPT_ACST_Sch_'+zonename+' Actuator')
        else:
            self.idf1.newidfobject(
                'EnergyManagementSystem:Actuator',
                Name='FORSCRIPT_ACST_Sch_'+zonename,
                Actuated_Component_Unique_Name='FORSCRIPT_ACST_'+zonename,
                Actuated_Component_Type='Schedule:Compact',
                Actuated_Component_Control_Type='Schedule Value'
                )
            if verboseMode:
                print('Added - FORSCRIPT_ACST_Sch_'+zonename+' Actuator')
        #    print([actuator for actuator in self.idf1.idfobjects['EnergyManagementSystem:Actuator'] if actuator.Name=='FORSCRIPT_ACST_Schedule_'+zonename])

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


