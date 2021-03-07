# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 17:03:48 2021

@author: Daniel
"""

from eppy import modeleditor
from eppy.modeleditor import IDF

import pytest

from accim.sim import accim_Base_EMS


def lookfor(self, name, objectType):
    """
    Look for name in objectType list.
    """
    listToSearchIn = ([x.Name for x in self.idf1.idfobjects[objectType]])

    if name in listToSearchIn:
        return True
    else:
        return False


def test_addEMSProgramsBase(self):
    pass
    
