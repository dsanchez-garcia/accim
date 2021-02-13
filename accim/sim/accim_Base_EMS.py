"""Add EMS objects in common to both SingleZone and MultipleZone."""


def addEMSProgramsBase(self):
    """
    Add EMS programs for Base accim.

    Checks if some programs objects are already
    in the model, and otherwise adds them.
    """
    programlist = [
        program.Name
        for program in self.idf1.idfobjects["EnergyManagementSystem:Program"]
    ]

    if "SetComfTemp" in programlist:
        print("Not added - SetComfTemp Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="SetComfTemp",
            Program_Line_1="if AdapStand == 1",
            Program_Line_2="set ComfTemp = RMOT*0.33+18.8",
            Program_Line_3="elseif AdapStand == 2",
            Program_Line_4="set ComfTemp = PMOT*0.31+17.8",
            Program_Line_5="endif",
        )
        print("Added - SetComfTemp Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetComfTemp'])

    for zonename in self.zonenames:
        if "CountHours_" + zonename in programlist:
            print("Not added - CountHours_" + zonename + " Program")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Program",
                Name="CountHours_" + zonename,
                Program_Line_1="if (AdapStand == 1 )",
                Program_Line_2="if (RMOT >= AHSTall) && (RMOT <= ACSTaul)",
                Program_Line_3="if (" + zonename + "_OpT <= ACSTnoTol)",
                Program_Line_4="if (" + zonename + "_OpT >= AHSTnoTol)",
                Program_Line_5="set ComfHours_" + zonename + " = 1*ZoneTimeStep",
                Program_Line_6="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_7="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_8="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_9="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_10="endif",
                Program_Line_11="elseif (" + zonename + "_OpT > ACSTnoTol)",
                Program_Line_12="set ComfHours_" + zonename + " = 0",
                Program_Line_13="set DiscomfAppHotHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_14="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_15="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_16="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_17="elseif (" + zonename + "_OpT < AHSTnoTol)",
                Program_Line_18="set ComfHours_" + zonename + " = 0",
                Program_Line_19="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_20="set DiscomfAppColdHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_21="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_22="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_23="endif",
                Program_Line_24="elseif (RMOT > ACSTaul)",
                Program_Line_25="set ComfHours_" + zonename + " = 0",
                Program_Line_26="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_27="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_28="set DiscomfNonAppHotHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_29="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_30="elseif (RMOT < AHSTall)",
                Program_Line_31="set ComfHours_" + zonename + " = 0",
                Program_Line_32="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_33="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_34="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_35="set DiscomfNonAppColdHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_36="endif",
                Program_Line_37="elseif (AdapStand == 2 )",
                Program_Line_38="if (PMOT >= AHSTall) && (PMOT <= ACSTaul)",
                Program_Line_39="if (" + zonename + "_OpT <= ACSTnoTol)",
                Program_Line_40="if (" + zonename + "_OpT >= AHSTnoTol)",
                Program_Line_41="set ComfHours_" + zonename + " = 1*ZoneTimeStep",
                Program_Line_42="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_43="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_44="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_45="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_46="endif",
                Program_Line_47="elseif (" + zonename + "_OpT > ACSTnoTol)",
                Program_Line_48="set ComfHours_" + zonename + " = 0",
                Program_Line_49="set DiscomfAppHotHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_50="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_51="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_52="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_53="elseif (" + zonename + "_OpT < AHSTnoTol)",
                Program_Line_54="set ComfHours_" + zonename + " = 0",
                Program_Line_55="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_56="set DiscomfAppColdHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_57="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_58="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_59="endif",
                Program_Line_60="elseif (PMOT > ACSTaul)",
                Program_Line_61="set ComfHours_" + zonename + " = 0",
                Program_Line_62="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_63="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_64="set DiscomfNonAppHotHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_65="set DiscomfNonAppColdHours_" + zonename + " = 0",
                Program_Line_66="elseif (PMOT < AHSTall)",
                Program_Line_67="set ComfHours_" + zonename + " = 0",
                Program_Line_68="set DiscomfAppHotHours_" + zonename + " = 0",
                Program_Line_69="set DiscomfAppColdHours_" + zonename + " = 0",
                Program_Line_70="set DiscomfNonAppHotHours_" + zonename + " = 0",
                Program_Line_71="set DiscomfNonAppColdHours_"
                + zonename
                + " = 1*ZoneTimeStep",
                Program_Line_72="endif",
                Program_Line_73="endif",
            )
            print("Added - CountHours_" + zonename + " Program")
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'CountHours_'+zonename])

    if "SetAppLimits" in programlist:
        print("Not added - SetAppLimits Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="SetAppLimits",
            Program_Line_1="If AdapStand == 1",
            Program_Line_2="set ACSTaul = 30",
            Program_Line_3="set ACSTall = 10",
            Program_Line_4="set AHSTaul = 30",
            Program_Line_5="set AHSTall = 10",
            Program_Line_6="elseif AdapStand == 2",
            Program_Line_7="set ACSTaul = 33.5",
            Program_Line_8="set ACSTall = 10",
            Program_Line_9="set AHSTaul = 33.5",
            Program_Line_10="set AHSTall = 10",
            Program_Line_11="else",
            Program_Line_12="set ACSTaul = 50",
            Program_Line_13="set ACSTall = 50",
            Program_Line_14="set AHSTaul = 50",
            Program_Line_15="set AHSTall = 50",
            Program_Line_16="endif",
        )
        print("Added - SetAppLimits Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetAppLimits'])

    if "ApplyCAT" in programlist:
        print("Not added - ApplyCAT Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="ApplyCAT",
            Program_Line_1="if (AdapStand == 1 )",
            Program_Line_2="if (CAT == 1)",
            Program_Line_3="set ACSToffset = 2",
            Program_Line_4="set AHSToffset = -3",
            Program_Line_5="elseif (CAT == 2)",
            Program_Line_6="set ACSToffset = 3",
            Program_Line_7="set AHSToffset = -4",
            Program_Line_8="elseif (CAT == 3)",
            Program_Line_9="set ACSToffset = 4",
            Program_Line_10="set AHSToffset = -5",
            Program_Line_11="endif",
            Program_Line_12="elseif (AdapStand == 2 )",
            Program_Line_13="if (CAT == 90)",
            Program_Line_14="set ACSToffset = 2.5",
            Program_Line_15="set AHSToffset = -2.5",
            Program_Line_16="elseif (CAT == 80)",
            Program_Line_17="set ACSToffset = 3.5",
            Program_Line_18="set AHSToffset = -3.5",
            Program_Line_19="endif",
            Program_Line_20="endif",
        )
        print("Added - ApplyCAT Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'ApplyCAT'])

    if "SetAST" in programlist:
        print("Not added - SetAST Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="SetAST",
            Program_Line_1="if (AdapStand == 0) && (CurrentTime < 7)",
            Program_Line_2="set ACST = 27+ACSTtol",
            Program_Line_3="set AHST = 17+AHSTtol",
            Program_Line_4="elseif (AdapStand == 0) && (CurrentTime < 15)",
            Program_Line_5="set ACST = 25",
            Program_Line_6="set AHST = 20+AHSTtol",
            Program_Line_7="elseif (AdapStand == 0) && (CurrentTime < 23)",
            Program_Line_8="set ACST = 25+ACSTtol",
            Program_Line_9="set AHST = 20+AHSTtol",
            Program_Line_10="elseif (AdapStand == 0) && (CurrentTime < 24)",
            Program_Line_11="set ACST = 27+ACSTtol",
            Program_Line_12="set AHST = 17+AHSTtol",
            Program_Line_13="endif",
            Program_Line_14="if (AdapStand == 1) && (ComfMod == 0)",
            Program_Line_15="if (DayOfYear >= 121) && (DayOfYear < 274)",
            Program_Line_16="if (CAT==1)",
            Program_Line_17="set ACST = 25.5+ACSTtol",
            Program_Line_18="elseif (CAT==2)",
            Program_Line_19="set ACST = 26+ACSTtol",
            Program_Line_20="elseif (CAT==3)",
            Program_Line_21="set ACST = 27+ACSTtol",
            Program_Line_22="endif",
            Program_Line_23="else",
            Program_Line_24="if (CAT==1)",
            Program_Line_25="set ACST = 25+ACSTtol",
            Program_Line_26="elseif (CAT==2)",
            Program_Line_27="set ACST = 25+ACSTtol",
            Program_Line_28="elseif (CAT==3)",
            Program_Line_29="set ACST = 25+ACSTtol",
            Program_Line_30="endif",
            Program_Line_31="endif",
            Program_Line_32="endif",
            Program_Line_33="if (AdapStand == 1) && (ComfMod == 0)",
            Program_Line_34="if (DayOfYear >= 121) && (DayOfYear < 274)",
            Program_Line_35="if (CAT==1)",
            Program_Line_36="set AHST = 23.5+AHSTtol",
            Program_Line_37="elseif (CAT==2)",
            Program_Line_38="set AHST = 23+AHSTtol",
            Program_Line_39="elseif (CAT==3)",
            Program_Line_40="set AHST = 22+AHSTtol",
            Program_Line_41="endif",
            Program_Line_42="else",
            Program_Line_43="if (CAT==1)",
            Program_Line_44="set AHST = 21+AHSTtol",
            Program_Line_45="elseif (CAT==2)",
            Program_Line_46="set AHST = 20+AHSTtol",
            Program_Line_47="elseif (CAT==3)",
            Program_Line_48="set AHST = 18+AHSTtol",
            Program_Line_49="endif",
            Program_Line_50="endif",
            Program_Line_51="endif",
            Program_Line_52="if (AdapStand == 1) && (ComfMod == 1) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)",
            Program_Line_53="set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol",
            Program_Line_54="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 7)",
            Program_Line_55="set ACST = 27+ACSTtol",
            Program_Line_56="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 15)",
            Program_Line_57="set ACST = 50",
            Program_Line_58="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 23)",
            Program_Line_59="set ACST = 25+ACSTtol",
            Program_Line_60="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 24)",
            Program_Line_61="set ACST = 27+ACSTtol",
            Program_Line_62="endif",
            Program_Line_63="if (AdapStand == 1) && (ComfMod == 1) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)",
            Program_Line_64="set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol",
            Program_Line_65="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 7)",
            Program_Line_66="set AHST = 17+AHSTtol",
            Program_Line_67="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 23)",
            Program_Line_68="set AHST = 20+AHSTtol",
            Program_Line_69="elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 24)",
            Program_Line_70="set AHST = 17+AHSTtol",
            Program_Line_71="endif",
            Program_Line_72="if (AdapStand == 1) && (ComfMod == 2) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)",
            Program_Line_73="set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol",
            Program_Line_74="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==1)",
            Program_Line_75="set ACST = 25+ACSTtol",
            Program_Line_76="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==1)",
            Program_Line_77="set ACST = 25.5+ACSTtol",
            Program_Line_78="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==2)",
            Program_Line_79="set ACST = 25+ACSTtol",
            Program_Line_80="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==2)",
            Program_Line_81="set ACST = 26+ACSTtol",
            Program_Line_82="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==3)",
            Program_Line_83="set ACST = 25+ACSTtol",
            Program_Line_84="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==3)",
            Program_Line_85="set ACST = 27+ACSTtol",
            Program_Line_86="endif",
            Program_Line_87="if (AdapStand == 1) && (ComfMod == 2) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)",
            Program_Line_88="set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol",
            Program_Line_89="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==1)",
            Program_Line_90="set AHST = 21+AHSTtol",
            Program_Line_91="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==1)",
            Program_Line_92="set AHST = 23.5+AHSTtol",
            Program_Line_93="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==2)",
            Program_Line_94="set AHST = 20+AHSTtol",
            Program_Line_95="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==2)",
            Program_Line_96="set AHST = 23+AHSTtol",
            Program_Line_97="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==3)",
            Program_Line_98="set AHST = 18+AHSTtol",
            Program_Line_99="elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==3)",
            Program_Line_100="set AHST = 22+AHSTtol",
            Program_Line_101="endif",
            Program_Line_102="if (AdapStand == 1) && (ComfMod == 3) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)",
            Program_Line_103="set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol",
            Program_Line_104="elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT < ACSTall)",
            Program_Line_105="set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol",
            Program_Line_106="elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT > ACSTaul)",
            Program_Line_107="set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol",
            Program_Line_108="endif",
            Program_Line_109="if (AdapStand == 1) && (ComfMod == 3) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)",
            Program_Line_110="set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol",
            Program_Line_111="elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT < AHSTall)",
            Program_Line_112="set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol",
            Program_Line_113="elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT > AHSTaul)",
            Program_Line_114="set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol",
            Program_Line_115="endif",
            Program_Line_116="if (AdapStand == 2) && (ComfMod == 0)",
            Program_Line_117="if (DayOfYear >= 121) && (DayOfYear < 274)",
            Program_Line_118="if (CAT==80)",
            Program_Line_119="set ACST = 26.8+ACSTtol",
            Program_Line_120="elseif (CAT==90)",
            Program_Line_121="set ACST = 25.8+ACSTtol",
            Program_Line_122="endif",
            Program_Line_123="else",
            Program_Line_124="if (CAT==80)",
            Program_Line_125="set ACST = 22.9+ACSTtol",
            Program_Line_126="elseif (CAT==90)",
            Program_Line_127="set ACST = 23.9+ACSTtol",
            Program_Line_128="endif",
            Program_Line_129="endif",
            Program_Line_130="endif",
            Program_Line_131="if (AdapStand == 2) && (ComfMod == 0)",
            Program_Line_132="if (DayOfYear >= 121) && (DayOfYear < 274)",
            Program_Line_133="if (CAT==80)",
            Program_Line_134="set AHST = 24.6+AHSTtol",
            Program_Line_135="elseif (CAT==90)",
            Program_Line_136="set AHST = 23.6+AHSTtol",
            Program_Line_137="endif",
            Program_Line_138="else",
            Program_Line_139="if (CAT==80)",
            Program_Line_140="set AHST = 18.6+AHSTtol",
            Program_Line_141="elseif (CAT==90)",
            Program_Line_142="set AHST = 19.6+AHSTtol",
            Program_Line_143="endif",
            Program_Line_144="endif",
            Program_Line_145="endif",
            Program_Line_146="if (AdapStand == 2) && (ComfMod == 1) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)",
            Program_Line_147="set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol",
            Program_Line_148="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 7)",
            Program_Line_149="set ACST = 27+ACSTtol",
            Program_Line_150="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 15)",
            Program_Line_151="set ACST = 50",
            Program_Line_152="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 23)",
            Program_Line_153="set ACST = 25+ACSTtol",
            Program_Line_154="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 24)",
            Program_Line_155="set ACST = 27+ACSTtol",
            Program_Line_156="endif",
            Program_Line_157="if (AdapStand == 2) && (ComfMod == 1) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)",
            Program_Line_158="set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol",
            Program_Line_159="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 7)",
            Program_Line_160="set AHST = 17+AHSTtol",
            Program_Line_161="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 23)",
            Program_Line_162="set AHST = 20+AHSTtol",
            Program_Line_163="elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 24)",
            Program_Line_164="set AHST = 17+AHSTtol",
            Program_Line_165="endif",
            Program_Line_166="if (AdapStand == 2) && (ComfMod == 2) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)",
            Program_Line_167="set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol",
            Program_Line_168="elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT < ACSTall)",
            Program_Line_169="set ACST = 23.9+ACSTtol",
            Program_Line_170="elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT > ACSTaul)",
            Program_Line_171="set ACST = 26.8+ACSTtol",
            Program_Line_172="endif",
            Program_Line_173="if (AdapStand == 2) && (ComfMod == 2) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)",
            Program_Line_174="set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol",
            Program_Line_175="elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT < AHSTall)",
            Program_Line_176="set AHST = 19.6+AHSTtol",
            Program_Line_177="elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT > AHSTaul)",
            Program_Line_178="set AHST = 23.6+AHSTtol",
            Program_Line_179="endif",
            Program_Line_180="if (AdapStand == 2) && (ComfMod == 3) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)",
            Program_Line_181="set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol",
            Program_Line_182="elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT < ACSTall)",
            Program_Line_183="set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol",
            Program_Line_184="elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT > ACSTaul)",
            Program_Line_185="set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol",
            Program_Line_186="endif",
            Program_Line_187="if (AdapStand == 2) && (ComfMod == 3) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)",
            Program_Line_188="set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol",
            Program_Line_189="elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT < AHSTall)",
            Program_Line_190="set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol",
            Program_Line_191="elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT > AHSTaul)",
            Program_Line_192="set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol",
            Program_Line_193="endif",
        )
        print("Added - SetAST Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetAST'])

    if "SetASTnoTol" in programlist:
        print("Not added - SetASTnoTol Program")
    else:
        self.idf1.newidfobject(
            "EnergyManagementSystem:Program",
            Name="SetASTnoTol",
            Program_Line_1="set ACSTnoTol = ACST-ACSTtol",
            Program_Line_2="set AHSTnoTol = AHST-AHSTtol",
        )
        print("Added - SetASTnoTol Program")
    #    print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'SetASTnoTol'])

    for zonename in self.zonenames:
        if "CountHoursNoApp_" + zonename in programlist:
            print("Not added - CountHoursNoApp_" + zonename + " Program")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:Program",
                Name="CountHoursNoApp_" + zonename,
                Program_Line_1="if (" + zonename + "_OpT <= ACSTnoTol)",
                Program_Line_2="if (" + zonename + "_OpT >= AHSTnoTol)",
                Program_Line_3="set ComfHoursNoApp_" + zonename + "  = 1*ZoneTimeStep",
                Program_Line_4="else",
                Program_Line_5="set ComfHoursNoApp_" + zonename + " = 0",
                Program_Line_6="endif",
                Program_Line_7="else",
                Program_Line_8="set ComfHoursNoApp_" + zonename + " = 0",
                Program_Line_9="endif",
            )
            print("Added - CountHoursNoApp_" + zonename + " Program")
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:Program'] if program.Name == 'CountHoursNoApp_'+zonename])

    del programlist


def addEMSPCMBase(self):
    """
    Add EMS program calling managers for Base accim.

    Checks if some EMS program calling manager objects are already
    in the model, and otherwise adds them.
    """
    programlist = [
        program.Name
        for program in self.idf1.idfobjects["EnergyManagementSystem:Program"]
    ]
    pcmlist = [
        pcm.Name
        for pcm in self.idf1.idfobjects["EnergyManagementSystem:ProgramCallingManager"]
    ]

    for i in programlist:
        if i in pcmlist:
            print("Not added - " + i + " Program Calling Manager")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:ProgramCallingManager",
                Name=i,
                EnergyPlus_Model_Calling_Point="BeginTimestepBeforePredictor",
                Program_Name_1=i,
            )
            print("Added - " + i + " Program Calling Manager")
    #        print([program for program in self.idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager'] if program.Name == i])

    del programlist, pcmlist


def addEMSOutputVariableBase(self):
    """Add EMS output variables for Base accim.

    Checks if some EMS output variables objects are already
    in the model, and otherwise adds them.
    """
    EMSOutputVariableComfTemp_dict = {
        "Comfort Temperature": "ComfTemp",
        "Adaptive Cooling Setpoint Temperature": "ACST",
        "Adaptive Heating Setpoint Temperature": "AHST",
        "Adaptive Cooling Setpoint Temperature_No Tolerance": "ACSTnoTol",
        "Adaptive Heating Setpoint Temperature_No Tolerance": "AHSTnoTol",
    }

    outputvariablelist = [
        program.Name
        for program in self.idf1.idfobjects["EnergyManagementSystem:OutputVariable"]
    ]

    for i in EMSOutputVariableComfTemp_dict:
        if i in outputvariablelist:
            print("Not added - " + i + " Output Variable")
        else:
            self.idf1.newidfobject(
                "EnergyManagementSystem:OutputVariable",
                Name=i,
                EMS_Variable_Name=EMSOutputVariableComfTemp_dict[i],
                Type_of_Data_in_Variable="Averaged",
                Update_Frequency="ZoneTimestep",
                EMS_Program_or_Subroutine_Name="",
                Units="C",
            )
            print("Added - " + i + " Output Variable")
            # print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == i])

    EMSOutputVariableComfHours_dict = {
        "Comfortable Hours_No Applicability": "ComfHoursNoApp",
        "Comfortable Hours": "ComfHours",
        "Discomfortable Applicable Hot Hours": "DiscomfAppHotHours",
        "Discomfortable Applicable Cold Hours": "DiscomfAppColdHours",
        "Discomfortable Non Applicable Hot Hours": "DiscomfNonAppHotHours",
        "Discomfortable Non Applicable Cold Hours": "DiscomfNonAppColdHours",
    }

    for i in EMSOutputVariableComfHours_dict:
        for zonename in self.zonenames:
            if i + "_" + zonename + " (summed)" in outputvariablelist:
                print("Not added - " + i + "_" + zonename + " (summed) Output Variable")
            else:
                self.idf1.newidfobject(
                    "EnergyManagementSystem:OutputVariable",
                    Name=i + "_" + zonename + " (summed)",
                    EMS_Variable_Name=EMSOutputVariableComfHours_dict[i]
                    + "_"
                    + zonename,
                    Type_of_Data_in_Variable="Summed",
                    Update_Frequency="ZoneTimestep",
                    EMS_Program_or_Subroutine_Name="",
                    Units="H",
                )
                print("Added - " + i + "_" + zonename + " (summed) Output Variable")
                # print([outputvariable for outputvariable in self.idf1.idfobjects['EnergyManagementSystem:OutputVariable'] if outputvariable.Name == i+'_'+zonename+' (summed)'])

    del outputvariablelist


def addOutputVariablesTimestep(self):
    """
    Add Output:Variable objects in timestep frequency.

    No need for further description.
    """
    fulloutputlist = [output for output in self.idf1.idfobjects["Output:Variable"]]
    # print(fulloutputlist)

    outputlist = [
        output.Variable_Name for output in self.idf1.idfobjects["Output:Variable"]
    ]
    # print(outputlist)

    for i in range(len(outputlist)):
        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value=fulloutputlist[i].Key_Value,
            Variable_Name=fulloutputlist[i].Variable_Name,
            Reporting_Frequency="Timestep",
            Schedule_Name=fulloutputlist[i].Schedule_Name,
        )
        print(
            "Added - "
            + fulloutputlist[i].Variable_Name
            + " Output:Variable Timestep data"
        )

    # print([output for output in self.idf1.idfobjects['Output:Variable'] if output.Reporting_Frequency == 'Timestep'])

    del fulloutputlist, outputlist


def addSimplifiedOutputVariables(self):
    """
    Add simplified Output:Variable objects for accim.

    Remove all outputs and add only VFR outdoor unit consumption
    and operative temperature.
    """
    EnvironmentalImpactFactorslist = [
        output for output in self.idf1.idfobjects["Output:EnvironmentalImpactFactors"]
    ]
    for i in range(len(EnvironmentalImpactFactorslist)):
        firstEnvironmentalImpactFactor = self.idf1.idfobjects[
            "Output:EnvironmentalImpactFactors"
        ][-1]
        self.idf1.removeidfobject(firstEnvironmentalImpactFactor)

    outputmeterlist = [output for output in self.idf1.idfobjects["Output:Meter"]]
    for i in range(len(outputmeterlist)):
        firstoutputmeter = self.idf1.idfobjects["Output:Meter"][-1]
        self.idf1.removeidfobject(firstoutputmeter)

    alloutputs = [output for output in self.idf1.idfobjects["Output:Variable"]]
    for i in range(len(alloutputs)):
        firstoutput = self.idf1.idfobjects["Output:Variable"][-1]
        self.idf1.removeidfobject(firstoutput)

    # del EnvironmentalImpactFactorslist,firstEnvironmentalImpactFactor, outputmeterlist, firstoutputmeter, alloutputs, firstoutput

    addittionaloutputs = [
        "Zone Thermostat Operative Temperature",
        "VRF Heat Pump Cooling Electricity Energy",
        "VRF Heat Pump Heating Electricity Energy",
    ]

    for addittionaloutput in addittionaloutputs:
        self.idf1.newidfobject(
            "Output:Variable",
            Key_Value="*",
            Variable_Name=addittionaloutput,
            Reporting_Frequency="Hourly",
            Schedule_Name="",
        )
        print("Added - " + addittionaloutput + " Output:Variable data")

    del addittionaloutputs
