from eppy import modeleditor
from eppy.modeleditor import IDF
import os

iddfile = r"C:\EnergyPlusV9-4-0\Energy+.idd"
# fname1 = r"D:\OneDrive - UNIVERSIDAD DE SEVILLA\Papers OneDrive\VPO_cadiz_parametrico\BA_V01.idf"

path = r'C:\Users\daniel.sanchez\Documents\Personal\VPO_parametrico\input_IDFs'
outputpath = r'C:\Users\daniel.sanchez\Documents\Personal\VPO_parametrico\output_IDFs'

IDF.setiddname(iddfile)

file = path+'/BA_V01_corregido.idf'

idf1 = IDF(file)

# idf1.printidf()

C01 = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name== 'O CO1_.3'][0]
print(C01)

C01.Name = 'O CO1_.2'
C01.Thickness = 0.2

print(C01)

slab = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name== 'OOO Hormigon celular_.1'][0]

print(slab)

slab.Name = 'Cast Concrete_.3'
slab.Thickness = 0.3
slab.Conductivity = 1.13
slab.Density = 2000
slab.Thermal_Absorptance = 0.9
slab.Solar_Absorptance = 0.6
slab.Visible_Absorptance = 0.6

print(slab)

buildup = [cons for cons in idf1.idfobjects['CONSTRUCTION'] if cons.Name == 'OO CO1'][0]

print(buildup)

buildup.Layer_2 = 'O CO1_.2'
buildup.Layer_3 = 'Cast Concrete_.3'

print(buildup)

buildup_rev = [cons for cons in idf1.idfobjects['CONSTRUCTION'] if cons.Name == 'OO CO1_Rev'][0]

print(buildup_rev)

buildup_rev.Outside_Layer = 'Cast Concrete_.3'
buildup_rev.Layer_2 = 'O CO1_.2'

print(buildup_rev)

idf1.savecopy(file.split('.idf')[0]+'_amended.idf')