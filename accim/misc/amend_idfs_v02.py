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

if 'Cast Concrete_.1' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_cast_concrete = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'Cast Concrete_.1'][0]
    mat_cast_concrete.Roughness = 'Rough'
    mat_cast_concrete.Thickness = 0.1
    mat_cast_concrete.Conductivity = 1.13
    mat_cast_concrete.Density = 2000
    mat_cast_concrete.Specific_Heat = 1000
    mat_cast_concrete.Thermal_Absorptance = 0.9
    mat_cast_concrete.Solar_Absorptance = 0.6
    mat_cast_concrete.Visible_Absorptance = 0.6
else:
    idf1.newidfobject('MATERIAL',
        Name='Cast Concrete_.1',
        Roughness='Rough',
        Thickness=0.1,
        Conductivity=1.13,
        Density=2000,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.6,
        Visible_Absorptance=0.6
        )

if 'O SO1_.16' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_S01 = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'O SO1_.16'][0]
    mat_S01.Roughness = 'Rough'
    mat_S01.Thickness = 0.16
    mat_S01.Conductivity = 0.01679
    mat_S01.Density = 1700
    mat_S01.Specific_Heat = 1000
    mat_S01.Thermal_Absorptance = 0.9
    mat_S01.Solar_Absorptance = 0.7
    mat_S01.Visible_Absorptance = 0.7
else:
    idf1.newidfobject('MATERIAL',
        Name='O SO1_.16',
        Roughness='Rough',
        Thickness=0.16,
        Conductivity=0.01679,
        Density=1700,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7
        )

if 'Floor/Roof Screed_.O7' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_screed = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'Floor/Roof Screed_.O7'][0]
    mat_screed.Roughness = 'Rough'
    mat_screed.Thickness = 0.07
    mat_screed.Conductivity = 0.41
    mat_screed.Density = 1200
    mat_screed.Specific_Heat = 840
    mat_screed.Thermal_Absorptance = 0.9
    mat_screed.Solar_Absorptance = 0.73
    mat_screed.Visible_Absorptance = 0.73
else:
    idf1.newidfobject('MATERIAL',
        Name='Floor/Roof Screed_.O7',
        Roughness='Rough',
        Thickness=0.07,
        Conductivity=0.41,
        Density=1200,
        Specific_Heat=840,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.73,
        Visible_Absorptance=0.73
        )


if 'OO SO1' in [i.Name for i in idf1.idfobjects['CONSTRUCTION']]:
    cons_S01 = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO SO1'][0]
    cons_S01.Name = 'OO SO1'
    cons_S01.Outside_Layer = 'Cast Concrete_.1'
    cons_S01.Layer_2 = 'O SO1_.16'
    cons_S01.Layer_3 = 'Floor/Roof Screed_.O7'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO SO1',
        Outside_Layer='Cast Concrete_.1',
        Layer_2='O SO1_.16',
        Layer_3='Floor/Roof Screed_.O7'
        )

if 'OO SO1_Rev' in [i.Name for i in idf1.idfobjects['CONSTRUCTION']]:
    cons_S01 = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO SO1_Rev'][0]
    cons_S01.Name = 'OO SO1_Rev'
    cons_S01.Outside_Layer = 'Floor/Roof Screed_.O7'
    cons_S01.Layer_2 = 'O SO1_.16'
    cons_S01.Layer_3 = 'Cast Concrete_.1'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO SO1_Rev',
        Outside_Layer='Floor/Roof Screed_.O7',
        Layer_2='O SO1_.16',
        Layer_3='Cast Concrete_.1'
        )

















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