# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 17:03:48 2021

@author: Daniel
"""

import pytest
from accim.sim import accim_Main

@pytest.fixture()
def IDFobject():
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    IDF.setiddname(iddfile)

    z = accim_Main.accimJob(
        filename_temp='TestModel_SingleZone',
        ScriptType='sz',
        EnergyPlus_version='ep94',
        verboseMode=False)
    return z

def test_addEMSProgramsBase(IDFobject):

    from eppy.modeleditor import IDF

    IDFobject.addEMSProgramsBase(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)

    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    programlist = ([program.Name for program in idf1.idfobjects['EnergyManagementSystem:Program']])
    assert ('SetComfTemp' in programlist)

    SetComfTemp = ([program
                    for program
                    in idf1.idfobjects['EnergyManagementSystem:Program']
                    if program.Name == 'SetComfTemp'])
    assert SetComfTemp[0].Program_Line_1 == 'if AdapStand == 1'
    assert SetComfTemp[0].Program_Line_2 == 'set ComfTemp = RMOT*0.33+18.8'
    assert SetComfTemp[0].Program_Line_3 == 'elseif AdapStand == 2'
    assert SetComfTemp[0].Program_Line_4 == 'set ComfTemp = PMOT*0.31+17.8'
    assert SetComfTemp[0].Program_Line_5 == 'endif'

    zonenames = ([sub.replace(':', '_') for sub in ([zone.Name for zone in idf1.idfobjects['ZONE']])])

    for zonename in zonenames:
        CountHours = ([program
                        for program
                        in idf1.idfobjects['EnergyManagementSystem:Program']
                        if program.Name == 'CountHours_' + zonename])
        assert CountHours[0].Name == 'CountHours_' + zonename
        assert CountHours[0].Program_Line_1 == 'if (AdapStand == 1 )'
        assert CountHours[0].Program_Line_2 == 'if (RMOT >= AHSTall) && (RMOT <= ACSTaul)'
        assert CountHours[0].Program_Line_3 == 'if (' + zonename + '_OpT <= ACSTnoTol)'
        assert CountHours[0].Program_Line_4 == 'if (' + zonename + '_OpT >= AHSTnoTol)'
        assert CountHours[0].Program_Line_5 == 'set ComfHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_6 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_7 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_8 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_9 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_10 == 'endif'
        assert CountHours[0].Program_Line_11 == 'elseif (' + zonename + '_OpT > ACSTnoTol)'
        assert CountHours[0].Program_Line_12 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_13 == 'set DiscomfAppHotHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_14 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_15 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_16 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_17 == 'elseif (' + zonename + '_OpT < AHSTnoTol)'
        assert CountHours[0].Program_Line_18 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_19 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_20 == 'set DiscomfAppColdHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_21 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_22 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_23 == 'endif'
        assert CountHours[0].Program_Line_24 == 'elseif (RMOT > ACSTaul)'
        assert CountHours[0].Program_Line_25 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_26 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_27 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_28 == 'set DiscomfNonAppHotHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_29 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_30 == 'elseif (RMOT < AHSTall)'
        assert CountHours[0].Program_Line_31 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_32 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_33 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_34 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_35 == 'set DiscomfNonAppColdHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_36 == 'endif'
        assert CountHours[0].Program_Line_37 == 'elseif (AdapStand == 2 )'
        assert CountHours[0].Program_Line_38 == 'if (PMOT >= AHSTall) && (PMOT <= ACSTaul)'
        assert CountHours[0].Program_Line_39 == 'if (' + zonename + '_OpT <= ACSTnoTol)'
        assert CountHours[0].Program_Line_40 == 'if (' + zonename + '_OpT >= AHSTnoTol)'
        assert CountHours[0].Program_Line_41 == 'set ComfHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_42 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_43 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_44 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_45 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_46 == 'endif'
        assert CountHours[0].Program_Line_47 == 'elseif (' + zonename + '_OpT > ACSTnoTol)'
        assert CountHours[0].Program_Line_48 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_49 == 'set DiscomfAppHotHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_50 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_51 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_52 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_53 == 'elseif (' + zonename + '_OpT < AHSTnoTol)'
        assert CountHours[0].Program_Line_54 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_55 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_56 == 'set DiscomfAppColdHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_57 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_58 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_59 == 'endif'
        assert CountHours[0].Program_Line_60 == 'elseif (PMOT > ACSTaul)'
        assert CountHours[0].Program_Line_61 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_62 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_63 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_64 == 'set DiscomfNonAppHotHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_65 == 'set DiscomfNonAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_66 == 'elseif (PMOT < AHSTall)'
        assert CountHours[0].Program_Line_67 == 'set ComfHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_68 == 'set DiscomfAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_69 == 'set DiscomfAppColdHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_70 == 'set DiscomfNonAppHotHours_' + zonename + ' = 0'
        assert CountHours[0].Program_Line_71 == 'set DiscomfNonAppColdHours_' + zonename + ' = 1*ZoneTimeStep'
        assert CountHours[0].Program_Line_72 == 'endif'
        assert CountHours[0].Program_Line_73 == 'endif'

    SetAppLimits = ([program
                    for program
                    in idf1.idfobjects['EnergyManagementSystem:Program']
                    if program.Name == 'SetAppLimits'])
    assert SetAppLimits[0].Name == 'SetAppLimits'
    assert SetAppLimits[0].Program_Line_1 == 'If AdapStand == 1'
    assert SetAppLimits[0].Program_Line_2 == 'set ACSTaul = 30'
    assert SetAppLimits[0].Program_Line_3 == 'set ACSTall = 10'
    assert SetAppLimits[0].Program_Line_4 == 'set AHSTaul = 30'
    assert SetAppLimits[0].Program_Line_5 == 'set AHSTall = 10'
    assert SetAppLimits[0].Program_Line_6 == 'elseif AdapStand == 2'
    assert SetAppLimits[0].Program_Line_7 == 'set ACSTaul = 33.5'
    assert SetAppLimits[0].Program_Line_8 == 'set ACSTall = 10'
    assert SetAppLimits[0].Program_Line_9 == 'set AHSTaul = 33.5'
    assert SetAppLimits[0].Program_Line_10 == 'set AHSTall = 10'
    assert SetAppLimits[0].Program_Line_11 == 'else'
    assert SetAppLimits[0].Program_Line_12 == 'set ACSTaul = 50'
    assert SetAppLimits[0].Program_Line_13 == 'set ACSTall = 50'
    assert SetAppLimits[0].Program_Line_14 == 'set AHSTaul = 50'
    assert SetAppLimits[0].Program_Line_15 == 'set AHSTall = 50'
    assert SetAppLimits[0].Program_Line_16 == 'endif'

    
    ApplyCAT = ([program
                 for program
                 in idf1.idfobjects['EnergyManagementSystem:Program']
                 if program.Name == 'ApplyCAT'])
    assert ApplyCAT[0].Name == 'ApplyCAT'
    assert ApplyCAT[0].Program_Line_1 == 'if (AdapStand == 1 )'
    assert ApplyCAT[0].Program_Line_2 == 'if (CAT == 1)'
    assert ApplyCAT[0].Program_Line_3 == 'set ACSToffset = 2'
    assert ApplyCAT[0].Program_Line_4 == 'set AHSToffset = -3'
    assert ApplyCAT[0].Program_Line_5 == 'elseif (CAT == 2)'
    assert ApplyCAT[0].Program_Line_6 == 'set ACSToffset = 3'
    assert ApplyCAT[0].Program_Line_7 == 'set AHSToffset = -4'
    assert ApplyCAT[0].Program_Line_8 == 'elseif (CAT == 3)'
    assert ApplyCAT[0].Program_Line_9 == 'set ACSToffset = 4'
    assert ApplyCAT[0].Program_Line_10 == 'set AHSToffset = -5'
    assert ApplyCAT[0].Program_Line_11 == 'endif'
    assert ApplyCAT[0].Program_Line_12 == 'elseif (AdapStand == 2 )'
    assert ApplyCAT[0].Program_Line_13 == 'if (CAT == 90)'
    assert ApplyCAT[0].Program_Line_14 == 'set ACSToffset = 2.5'
    assert ApplyCAT[0].Program_Line_15 == 'set AHSToffset = -2.5'
    assert ApplyCAT[0].Program_Line_16 == 'elseif (CAT == 80)'
    assert ApplyCAT[0].Program_Line_17 == 'set ACSToffset = 3.5'
    assert ApplyCAT[0].Program_Line_18 == 'set AHSToffset = -3.5'
    assert ApplyCAT[0].Program_Line_19 == 'endif'
    assert ApplyCAT[0].Program_Line_20 == 'endif'
    
    SetAST = ([program
               for program
               in idf1.idfobjects['EnergyManagementSystem:Program']
               if program.Name == 'SetAST'])
    assert SetAST[0].Name == 'SetAST'
    assert SetAST[0].Program_Line_1 == 'if (AdapStand == 0) && (CurrentTime < 7)'
    assert SetAST[0].Program_Line_2 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_3 == 'set AHST = 17+AHSTtol'
    assert SetAST[0].Program_Line_4 == 'elseif (AdapStand == 0) && (CurrentTime < 15)'
    assert SetAST[0].Program_Line_5 == 'set ACST = 25'
    assert SetAST[0].Program_Line_6 == 'set AHST = 20+AHSTtol'
    assert SetAST[0].Program_Line_7 == 'elseif (AdapStand == 0) && (CurrentTime < 23)'
    assert SetAST[0].Program_Line_8 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_9 == 'set AHST = 20+AHSTtol'
    assert SetAST[0].Program_Line_10 == 'elseif (AdapStand == 0) && (CurrentTime < 24)'
    assert SetAST[0].Program_Line_11 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_12 == 'set AHST = 17+AHSTtol'
    assert SetAST[0].Program_Line_13 == 'endif'
    assert SetAST[0].Program_Line_14 == 'if (AdapStand == 1) && (ComfMod == 0)'
    assert SetAST[0].Program_Line_15 == 'if (DayOfYear >= 121) && (DayOfYear < 274)'
    assert SetAST[0].Program_Line_16 == 'if (CAT==1)'
    assert SetAST[0].Program_Line_17 == 'set ACST = 25.5+ACSTtol'
    assert SetAST[0].Program_Line_18 == 'elseif (CAT==2)'
    assert SetAST[0].Program_Line_19 == 'set ACST = 26+ACSTtol'
    assert SetAST[0].Program_Line_20 == 'elseif (CAT==3)'
    assert SetAST[0].Program_Line_21 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_22 == 'endif'
    assert SetAST[0].Program_Line_23 == 'else'
    assert SetAST[0].Program_Line_24 == 'if (CAT==1)'
    assert SetAST[0].Program_Line_25 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_26 == 'elseif (CAT==2)'
    assert SetAST[0].Program_Line_27 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_28 == 'elseif (CAT==3)'
    assert SetAST[0].Program_Line_29 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_30 == 'endif'
    assert SetAST[0].Program_Line_31 == 'endif'
    assert SetAST[0].Program_Line_32 == 'endif'
    assert SetAST[0].Program_Line_33 == 'if (AdapStand == 1) && (ComfMod == 0)'
    assert SetAST[0].Program_Line_34 == 'if (DayOfYear >= 121) && (DayOfYear < 274)'
    assert SetAST[0].Program_Line_35 == 'if (CAT==1)'
    assert SetAST[0].Program_Line_36 == 'set AHST = 23.5+AHSTtol'
    assert SetAST[0].Program_Line_37 == 'elseif (CAT==2)'
    assert SetAST[0].Program_Line_38 == 'set AHST = 23+AHSTtol'
    assert SetAST[0].Program_Line_39 == 'elseif (CAT==3)'
    assert SetAST[0].Program_Line_40 == 'set AHST = 22+AHSTtol'
    assert SetAST[0].Program_Line_41 == 'endif'
    assert SetAST[0].Program_Line_42 == 'else'
    assert SetAST[0].Program_Line_43 == 'if (CAT==1)'
    assert SetAST[0].Program_Line_44 == 'set AHST = 21+AHSTtol'
    assert SetAST[0].Program_Line_45 == 'elseif (CAT==2)'
    assert SetAST[0].Program_Line_46 == 'set AHST = 20+AHSTtol'
    assert SetAST[0].Program_Line_47 == 'elseif (CAT==3)'
    assert SetAST[0].Program_Line_48 == 'set AHST = 18+AHSTtol'
    assert SetAST[0].Program_Line_49 == 'endif'
    assert SetAST[0].Program_Line_50 == 'endif'
    assert SetAST[0].Program_Line_51 == 'endif'
    assert SetAST[0].Program_Line_52 == 'if (AdapStand == 1) && (ComfMod == 1) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)'
    assert SetAST[0].Program_Line_53 == 'set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_54 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 7)'
    assert SetAST[0].Program_Line_55 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_56 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 15)'
    assert SetAST[0].Program_Line_57 == 'set ACST = 50'
    assert SetAST[0].Program_Line_58 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 23)'
    assert SetAST[0].Program_Line_59 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_60 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 24)'
    assert SetAST[0].Program_Line_61 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_62 == 'endif'
    assert SetAST[0].Program_Line_63 == 'if (AdapStand == 1) && (ComfMod == 1) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)'
    assert SetAST[0].Program_Line_64 == 'set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_65 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 7)'
    assert SetAST[0].Program_Line_66 == 'set AHST = 17+AHSTtol'
    assert SetAST[0].Program_Line_67 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 23)'
    assert SetAST[0].Program_Line_68 == 'set AHST = 20+AHSTtol'
    assert SetAST[0].Program_Line_69 == 'elseif (AdapStand == 1) && (ComfMod == 1) && (CurrentTime < 24)'
    assert SetAST[0].Program_Line_70 == 'set AHST = 17+AHSTtol'
    assert SetAST[0].Program_Line_71 == 'endif'
    assert SetAST[0].Program_Line_72 == 'if (AdapStand == 1) && (ComfMod == 2) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)'
    assert SetAST[0].Program_Line_73 == 'set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_74 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==1)'
    assert SetAST[0].Program_Line_75 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_76 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==1)'
    assert SetAST[0].Program_Line_77 == 'set ACST = 25.5+ACSTtol'
    assert SetAST[0].Program_Line_78 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==2)'
    assert SetAST[0].Program_Line_79 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_80 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==2)'
    assert SetAST[0].Program_Line_81 == 'set ACST = 26+ACSTtol'
    assert SetAST[0].Program_Line_82 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < ACSTall) && (CAT==3)'
    assert SetAST[0].Program_Line_83 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_84 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > ACSTaul) && (CAT==3)'
    assert SetAST[0].Program_Line_85 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_86 == 'endif'
    assert SetAST[0].Program_Line_87 == 'if (AdapStand == 1) && (ComfMod == 2) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)'
    assert SetAST[0].Program_Line_88 == 'set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_89 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==1)'
    assert SetAST[0].Program_Line_90 == 'set AHST = 21+AHSTtol'
    assert SetAST[0].Program_Line_91 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==1)'
    assert SetAST[0].Program_Line_92 == 'set AHST = 23.5+AHSTtol'
    assert SetAST[0].Program_Line_93 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==2)'
    assert SetAST[0].Program_Line_94 == 'set AHST = 20+AHSTtol'
    assert SetAST[0].Program_Line_95 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==2)'
    assert SetAST[0].Program_Line_96 == 'set AHST = 23+AHSTtol'
    assert SetAST[0].Program_Line_97 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT < AHSTall) && (CAT==3)'
    assert SetAST[0].Program_Line_98 == 'set AHST = 18+AHSTtol'
    assert SetAST[0].Program_Line_99 == 'elseif (AdapStand == 1) && (ComfMod == 2) && (RMOT > AHSTaul) && (CAT==3)'
    assert SetAST[0].Program_Line_100 == 'set AHST = 22+AHSTtol'
    assert SetAST[0].Program_Line_101 == 'endif'
    assert SetAST[0].Program_Line_102 == 'if (AdapStand == 1) && (ComfMod == 3) && (RMOT >= ACSTall) && (RMOT <= ACSTaul)'
    assert SetAST[0].Program_Line_103 == 'set ACST = RMOT*0.33+18.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_104 == 'elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT < ACSTall)'
    assert SetAST[0].Program_Line_105 == 'set ACST = ACSTall*0.33+18.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_106 == 'elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT > ACSTaul)'
    assert SetAST[0].Program_Line_107 == 'set ACST = ACSTaul*0.33+18.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_108 == 'endif'
    assert SetAST[0].Program_Line_109 == 'if (AdapStand == 1) && (ComfMod == 3) && (RMOT >= AHSTall) && (RMOT <= AHSTaul)'
    assert SetAST[0].Program_Line_110 == 'set AHST = RMOT*0.33+18.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_111 == 'elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT < AHSTall)'
    assert SetAST[0].Program_Line_112 == 'set AHST = AHSTall*0.33+18.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_113 == 'elseif (AdapStand == 1) && (ComfMod == 3) && (RMOT > AHSTaul)'
    assert SetAST[0].Program_Line_114 == 'set AHST = AHSTaul*0.33+18.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_115 == 'endif'
    assert SetAST[0].Program_Line_116 == 'if (AdapStand == 2) && (ComfMod == 0)'
    assert SetAST[0].Program_Line_117 == 'if (DayOfYear >= 121) && (DayOfYear < 274)'
    assert SetAST[0].Program_Line_118 == 'if (CAT==80)'
    assert SetAST[0].Program_Line_119 == 'set ACST = 26.8+ACSTtol'
    assert SetAST[0].Program_Line_120 == 'elseif (CAT==90)'
    assert SetAST[0].Program_Line_121 == 'set ACST = 25.8+ACSTtol'
    assert SetAST[0].Program_Line_122 == 'endif'
    assert SetAST[0].Program_Line_123 == 'else'
    assert SetAST[0].Program_Line_124 == 'if (CAT==80)'
    assert SetAST[0].Program_Line_125 == 'set ACST = 22.9+ACSTtol'
    assert SetAST[0].Program_Line_126 == 'elseif (CAT==90)'
    assert SetAST[0].Program_Line_127 == 'set ACST = 23.9+ACSTtol'
    assert SetAST[0].Program_Line_128 == 'endif'
    assert SetAST[0].Program_Line_129 == 'endif'
    assert SetAST[0].Program_Line_130 == 'endif'
    assert SetAST[0].Program_Line_131 == 'if (AdapStand == 2) && (ComfMod == 0)'
    assert SetAST[0].Program_Line_132 == 'if (DayOfYear >= 121) && (DayOfYear < 274)'
    assert SetAST[0].Program_Line_133 == 'if (CAT==80)'
    assert SetAST[0].Program_Line_134 == 'set AHST = 24.6+AHSTtol'
    assert SetAST[0].Program_Line_135 == 'elseif (CAT==90)'
    assert SetAST[0].Program_Line_136 == 'set AHST = 23.6+AHSTtol'
    assert SetAST[0].Program_Line_137 == 'endif'
    assert SetAST[0].Program_Line_138 == 'else'
    assert SetAST[0].Program_Line_139 == 'if (CAT==80)'
    assert SetAST[0].Program_Line_140 == 'set AHST = 18.6+AHSTtol'
    assert SetAST[0].Program_Line_141 == 'elseif (CAT==90)'
    assert SetAST[0].Program_Line_142 == 'set AHST = 19.6+AHSTtol'
    assert SetAST[0].Program_Line_143 == 'endif'
    assert SetAST[0].Program_Line_144 == 'endif'
    assert SetAST[0].Program_Line_145 == 'endif'
    assert SetAST[0].Program_Line_146 == 'if (AdapStand == 2) && (ComfMod == 1) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)'
    assert SetAST[0].Program_Line_147 == 'set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_148 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 7)'
    assert SetAST[0].Program_Line_149 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_150 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 15)'
    assert SetAST[0].Program_Line_151 == 'set ACST = 50'
    assert SetAST[0].Program_Line_152 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 23)'
    assert SetAST[0].Program_Line_153 == 'set ACST = 25+ACSTtol'
    assert SetAST[0].Program_Line_154 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 24)'
    assert SetAST[0].Program_Line_155 == 'set ACST = 27+ACSTtol'
    assert SetAST[0].Program_Line_156 == 'endif'
    assert SetAST[0].Program_Line_157 == 'if (AdapStand == 2) && (ComfMod == 1) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)'
    assert SetAST[0].Program_Line_158 == 'set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_159 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 7)'
    assert SetAST[0].Program_Line_160 == 'set AHST = 17+AHSTtol'
    assert SetAST[0].Program_Line_161 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 23)'
    assert SetAST[0].Program_Line_162 == 'set AHST = 20+AHSTtol'
    assert SetAST[0].Program_Line_163 == 'elseif (AdapStand == 2) && (ComfMod == 1) && (CurrentTime < 24)'
    assert SetAST[0].Program_Line_164 == 'set AHST = 17+AHSTtol'
    assert SetAST[0].Program_Line_165 == 'endif'
    assert SetAST[0].Program_Line_166 == 'if (AdapStand == 2) && (ComfMod == 2) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)'
    assert SetAST[0].Program_Line_167 == 'set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_168 == 'elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT < ACSTall)'
    assert SetAST[0].Program_Line_169 == 'set ACST = 23.9+ACSTtol'
    assert SetAST[0].Program_Line_170 == 'elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT > ACSTaul)'
    assert SetAST[0].Program_Line_171 == 'set ACST = 26.8+ACSTtol'
    assert SetAST[0].Program_Line_172 == 'endif'
    assert SetAST[0].Program_Line_173 == 'if (AdapStand == 2) && (ComfMod == 2) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)'
    assert SetAST[0].Program_Line_174 == 'set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_175 == 'elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT < AHSTall)'
    assert SetAST[0].Program_Line_176 == 'set AHST = 19.6+AHSTtol'
    assert SetAST[0].Program_Line_177 == 'elseif (AdapStand == 2) && (ComfMod == 2) && (PMOT > AHSTaul)'
    assert SetAST[0].Program_Line_178 == 'set AHST = 23.6+AHSTtol'
    assert SetAST[0].Program_Line_179 == 'endif'
    assert SetAST[0].Program_Line_180 == 'if (AdapStand == 2) && (ComfMod == 3) && (PMOT >= ACSTall) && (PMOT <= ACSTaul)'
    assert SetAST[0].Program_Line_181 == 'set ACST = PMOT*0.31+17.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_182 == 'elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT < ACSTall)'
    assert SetAST[0].Program_Line_183 == 'set ACST = ACSTall*0.31+17.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_184 == 'elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT > ACSTaul)'
    assert SetAST[0].Program_Line_185 == 'set ACST = ACSTaul*0.31+17.8+ACSToffset+ACSTtol'
    assert SetAST[0].Program_Line_186 == 'endif'
    assert SetAST[0].Program_Line_187 == 'if (AdapStand == 2) && (ComfMod == 3) && (PMOT >= AHSTall) && (PMOT <= AHSTaul)'
    assert SetAST[0].Program_Line_188 == 'set AHST = PMOT*0.31+17.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_189 == 'elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT < AHSTall)'
    assert SetAST[0].Program_Line_190 == 'set AHST = AHSTall*0.31+17.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_191 == 'elseif (AdapStand == 2) && (ComfMod == 3) && (PMOT > AHSTaul)'
    assert SetAST[0].Program_Line_192 == 'set AHST = AHSTaul*0.31+17.8+AHSToffset+AHSTtol'
    assert SetAST[0].Program_Line_193 == 'endif'
    
    SetASTnoTol = ([program
               for program
               in idf1.idfobjects['EnergyManagementSystem:Program']
               if program.Name == 'SetASTnoTol'])
    assert SetASTnoTol[0].Name == 'SetASTnoTol'
    assert SetASTnoTol[0].Program_Line_1 == 'set ACSTnoTol = ACST-ACSTtol'
    assert SetASTnoTol[0].Program_Line_2 == 'set AHSTnoTol = AHST-AHSTtol'

    for zonename in zonenames:
        CountHoursNoApp = ([program
                        for program
                        in idf1.idfobjects['EnergyManagementSystem:Program']
                        if program.Name == 'CountHoursNoApp_' + zonename])
        assert CountHoursNoApp[0].Name == 'CountHoursNoApp_' + zonename
        assert CountHoursNoApp[0].Program_Line_1 == 'if (' + zonename + '_OpT <= ACSTnoTol)'
        assert CountHoursNoApp[0].Program_Line_2 == 'if (' + zonename + '_OpT >= AHSTnoTol)'
        assert CountHoursNoApp[0].Program_Line_3 == 'set ComfHoursNoApp_' + zonename + '  = 1*ZoneTimeStep'
        assert CountHoursNoApp[0].Program_Line_4 == 'else'
        assert CountHoursNoApp[0].Program_Line_5 == 'set ComfHoursNoApp_' + zonename + ' = 0'
        assert CountHoursNoApp[0].Program_Line_6 == 'endif'
        assert CountHoursNoApp[0].Program_Line_7 == 'else'
        assert CountHoursNoApp[0].Program_Line_8 == 'set ComfHoursNoApp_' + zonename + ' = 0'
        assert CountHoursNoApp[0].Program_Line_9 == 'endif'


def test_addEMSPCMBase(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addEMSProgramsBase(verboseMode=False)
    IDFobject.addEMSPCMBase(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    programlist = ([program.Name for program in idf1.idfobjects['EnergyManagementSystem:Program']])

    for i in programlist:
        pcm = ([pcm for pcm in idf1.idfobjects['EnergyManagementSystem:ProgramCallingManager'] if pcm.Name == i])
        assert pcm[0].Name == i
        assert pcm[0].EnergyPlus_Model_Calling_Point == "BeginTimestepBeforePredictor"
        assert pcm[0].Program_Name_1 == i

def test_addEMSOutputVariableBase(IDFobject):
    from eppy.modeleditor import IDF
    
    IDFobject.addEMSOutputVariableBase(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')
    
    EMSOutputVariableComfTemp_dict = {
        'Comfort Temperature': 'ComfTemp',
        'Adaptive Cooling Setpoint Temperature': 'ACST',
        'Adaptive Heating Setpoint Temperature': 'AHST',
        'Adaptive Cooling Setpoint Temperature_No Tolerance': 'ACSTnoTol',
        'Adaptive Heating Setpoint Temperature_No Tolerance': 'AHSTnoTol',
        }
    
    for i in EMSOutputVariableComfTemp_dict:
        outputvariable = ([x
                           for x
                           in idf1.idfobjects['EnergyManagementSystem:OutputVariable']
                           if x.Name == i])
        assert outputvariable[0].Name == i
        assert outputvariable[0].EMS_Variable_Name == EMSOutputVariableComfTemp_dict[i]
        assert outputvariable[0].Type_of_Data_in_Variable == 'Averaged'
        assert outputvariable[0].Update_Frequency == 'ZoneTimestep'
        assert outputvariable[0].EMS_Program_or_Subroutine_Name == ''
        assert outputvariable[0].Units == 'C'

    EMSOutputVariableComfHours_dict = {
        'Comfortable Hours_No Applicability': 'ComfHoursNoApp',
        'Comfortable Hours': 'ComfHours',
        'Discomfortable Applicable Hot Hours': 'DiscomfAppHotHours',
        'Discomfortable Applicable Cold Hours': 'DiscomfAppColdHours',
        'Discomfortable Non Applicable Hot Hours': 'DiscomfNonAppHotHours',
        'Discomfortable Non Applicable Cold Hours': 'DiscomfNonAppColdHours',
        }

    zonenames = ([sub.replace(':', '_') for sub in ([zone.Name for zone in idf1.idfobjects['ZONE']])])
    for i in EMSOutputVariableComfHours_dict:
        for zonename in zonenames:
            outputvariable = ([x
                               for x
                               in idf1.idfobjects['EnergyManagementSystem:OutputVariable']
                               if x.Name == i + '_' + zonename + ' (summed)'])
            assert outputvariable[0].Name == i + '_' + zonename + ' (summed)'
            assert outputvariable[0].EMS_Variable_Name == EMSOutputVariableComfHours_dict[i]+'_' + zonename
            assert outputvariable[0].Type_of_Data_in_Variable == 'Summed'
            assert outputvariable[0].Update_Frequency == 'ZoneTimestep'
            assert outputvariable[0].EMS_Program_or_Subroutine_Name == ''
            assert outputvariable[0].Units == 'H'


def test_addOutputVariablesTimestep(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addOutputVariablesSingleZone(verboseMode=False)
    IDFobject.addOutputVariablesTimestep(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    fulloutputlist = ([output for output in idf1.idfobjects['Output:Variable']])
    outputlist = ([output.Variable_Name for output in idf1.idfobjects['Output:Variable']])

    for i in range(len(outputlist)):
        outputvariable = ([x
                           for x
                           in idf1.idfobjects['Output:Variable']
                           if x.Key_Value == fulloutputlist[i].Key_Value
                           and x.Variable_Name == fulloutputlist[i].Variable_Name
                           and x.Reporting_Frequency == 'Timestep'])
        assert outputvariable[0].Key_Value == fulloutputlist[i].Key_Value
        assert outputvariable[0].Variable_Name == fulloutputlist[i].Variable_Name
        assert outputvariable[0].Reporting_Frequency == 'Timestep'
        assert outputvariable[0].Schedule_Name == fulloutputlist[i].Schedule_Name


def test_addSimplifiedOutputVariables(IDFobject):
    from eppy.modeleditor import IDF

    IDFobject.addSimplifiedOutputVariables(verboseMode=False)
    IDFobject.saveaccim(verboseMode=False)
    idf1 = IDF('TestModel_SingleZone_pymod.idf')

    EnvironmentalImpactFactorslist = ([output for output in idf1.idfobjects['Output:EnvironmentalImpactFactors']])
    outputmeterlist = ([output for output in idf1.idfobjects['Output:Meter']])
    alloutputs = ([output for output in idf1.idfobjects['Output:Variable']])

    assert len(EnvironmentalImpactFactorslist) == 0
    assert len(outputmeterlist) == 0

    addittionaloutputs = ['Zone Thermostat Operative Temperature',
                          'VRF Heat Pump Cooling Electricity Energy',
                          'VRF Heat Pump Heating Electricity Energy',
                          'Facility Total HVAC Electric Demand Power',
                          'Facility Total HVAC Electricity Demand Rate'
                          ]
    for addittionaloutput in addittionaloutputs:
        outputvariable = ([x
                           for x
                           in idf1.idfobjects['Output:Variable']
                           if x.Variable_Name == addittionaloutput])
        assert outputvariable[0].Key_Value == '*'
        assert outputvariable[0].Variable_Name == addittionaloutput
        assert outputvariable[0].Reporting_Frequency == 'Hourly'
        assert outputvariable[0].Schedule_Name == ''
