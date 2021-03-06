# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 17:03:48 2021

@author: Daniel
"""

from eppy import modeleditor
from eppy.modeleditor import IDF

import pytest
from accim.sim import accim_Main

from accim.sim import accim_Base_EMS

def test_addEMSProgramsBase():
    
    from eppy import modeleditor
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
    
test_addEMSProgramsBase()
