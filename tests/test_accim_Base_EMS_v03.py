# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 17:03:48 2021

@author: Daniel
"""


import pytest
from accim.sim import accim_Main

def test_addEMSProgramsBase():
    
    from eppy.modeleditor import IDF
    
    iddfile = 'C:/EnergyPlusV9-4-0/Energy+.idd'
    IDF.setiddname(iddfile)
    
    idf0 = IDF('TestModel_SingleZone.idf')
    
    programlist = ([program.Name for program in idf0.idfobjects['EnergyManagementSystem:Program']])
    assert ('SetComfTemp' in programlist) == False
    
    z = accim_Main.accimobj_SingleZone_Ep94('TestModel_SingleZone')
    z.addEMSProgramsBase()
    z.saveaccim()
    
    idf1 = IDF('TestModel_SingleZone_pymod.idf')
    
    programlist = ([program.Name for program in idf1.idfobjects['EnergyManagementSystem:Program']])
    assert ('SetComfTemp' in programlist) == True

    SetComfTemp = ([program
                    for program
                    in idf1.idfobjects['EnergyManagementSystem:Program']
                    if program.Name == 'SetComfTemp'])

    assert SetComfTemp[0].Program_Line_1 == 'if AdapStand == 1'
    assert SetComfTemp[0].Program_Line_2 == 'set ComfTemp = RMOT*0.33+18.8'
    assert SetComfTemp[0].Program_Line_3 == 'elseif AdapStand == 2'
    assert SetComfTemp[0].Program_Line_4 == 'set ComfTemp = PMOT*0.31+17.8'
    assert SetComfTemp[0].Program_Line_5 == 'endif'

    print(SetComfTemp[0].Name)
    print(SetComfTemp[0].Program_Line_1)
    
# test_addEMSProgramsBase()
