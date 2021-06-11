from eppy import modeleditor
from eppy.modeleditor import IDF
import os

iddfile = r"C:\EnergyPlusV9-4-0\Energy+.idd"
# fname1 = r"D:\OneDrive - UNIVERSIDAD DE SEVILLA\Papers OneDrive\VPO_cadiz_parametrico\BA_V01.idf"

path = r'D:\Paper_VPO_cadiz_parametrico\input_⁯IDFs'
outputpath = r'D:\Paper_VPO_cadiz_parametrico\output_IDFs'

IDF.setiddname(iddfile)

file = path+'/BB_V01.idf'

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
    cons_S01_rev = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO SO1_Rev'][0]
    cons_S01_rev.Name = 'OO SO1_Rev'
    cons_S01_rev.Outside_Layer = 'Floor/Roof Screed_.O7'
    cons_S01_rev.Layer_2 = 'O SO1_.16'
    cons_S01_rev.Layer_3 = 'Cast Concrete_.1'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO SO1_Rev',
        Outside_Layer='Floor/Roof Screed_.O7',
        Layer_2='O SO1_.16',
        Layer_3='Cast Concrete_.1'
        )









if 'OOO CTE Ladrillo perforado_.O5' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_perfbrick = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'OOO CTE Ladrillo perforado_.O5'][0]
    mat_perfbrick.Roughness = 'Rough'
    mat_perfbrick.Thickness = 0.05
    mat_perfbrick.Conductivity = 0.35
    mat_perfbrick.Density = 780
    mat_perfbrick.Specific_Heat = 1000
    mat_perfbrick.Thermal_Absorptance = 0.9
    mat_perfbrick.Solar_Absorptance = 0.7
    mat_perfbrick.Visible_Absorptance = 0.7
else:
    idf1.newidfobject(
        'MATERIAL',
        Name='OOO CTE Ladrillo perforado_.O5',
        Roughness='Rough',
        Thickness=0.05,
        Conductivity=0.35,
        Density=780,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7
    )

if 'O FO1_.125' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_F01 = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'O FO1_.125'][0]
    mat_F01.Roughness = 'Rough'
    mat_F01.Thickness = 0.125
    mat_F01.Conductivity = 0.01292
    mat_F01.Density = 1700
    mat_F01.Specific_Heat = 1000
    mat_F01.Thermal_Absorptance = 0.9
    mat_F01.Solar_Absorptance = 0.7
    mat_F01.Visible_Absorptance = 0.7
else:
    idf1.newidfobject(
        'MATERIAL',
        Name='O FO1_.125',
        Roughness='Rough',
        Thickness=0.125,
        Conductivity=0.01292,
        Density=1700,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7
    )

if 'OOO CTE Mortero_.O1' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_cementplaster = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'OOO CTE Mortero_.O1'][0]
    mat_cementplaster.Roughness = 'Rough'
    mat_cementplaster.Thickness = 0.01
    mat_cementplaster.Conductivity = 1
    mat_cementplaster.Density = 1700
    mat_cementplaster.Specific_Heat = 1000
    mat_cementplaster.Thermal_Absorptance = 0.9
    mat_cementplaster.Solar_Absorptance = 0.7
    mat_cementplaster.Visible_Absorptance = 0.7
else:
    idf1.newidfobject(
        'MATERIAL',
        Name='OOO CTE Mortero_.O1',
        Roughness='Rough',
        Thickness=0.01,
        Conductivity=1,
        Density=1700,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7
    )

if 'OO FO1' in [i.Name for i in idf1.idfobjects['CONSTRUCTION']]:
    cons_F01 = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO FO1'][0]
    cons_F01.Name = 'OO FO1'
    cons_F01.Outside_Layer = 'OOO CTE Ladrillo perforado_.O5'
    cons_F01.Layer_2 = 'O FO1_.125'
    cons_F01.Layer_3 = 'OOO CTE Mortero_.O1'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO FO1',
        Outside_Layer='OOO CTE Ladrillo perforado_.O5',
        Layer_2='O FO1_.125',
        Layer_3='OOO CTE Mortero_.O1'
        )

if 'OO FO1_Rev' in [i.Name for i in idf1.idfobjects['CONSTRUCTION']]:
    cons_F01_rev = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO FO1_Rev'][0]
    cons_F01_rev.Name = 'OO FO1_Rev'
    cons_F01_rev.Outside_Layer = 'OOO CTE Ladrillo perforado_.O5'
    cons_F01_rev.Layer_2 = 'O FO1_.125'
    cons_F01_rev.Layer_3 = 'OOO CTE Mortero_.O1'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO FO1_Rev',
        Outside_Layer='OOO CTE Mortero_.O1',
        Layer_2='O FO1_.125',
        Layer_3='OOO CTE Ladrillo perforado_.O5'
        )



if 'OOO CTE Arena_.O25' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_sand = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'OOO CTE Arena_.O25'][0]
    mat_sand.Roughness = 'Rough'
    mat_sand.Thickness = 0.025
    mat_sand.Conductivity = 2
    mat_sand.Density = 1700
    mat_sand.Specific_Heat = 910
    mat_sand.Thermal_Absorptance = 0.9
    mat_sand.Solar_Absorptance = 0.7
    mat_sand.Visible_Absorptance = 0.7
else:
    idf1.newidfobject(
        'MATERIAL',
        Name='OOO CTE Arena_.O25',
        Roughness='Rough',
        Thickness=0.025,
        Conductivity=2,
        Density=1700,
        Specific_Heat=910,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7
    )

if 'O CO1_.2' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_C01 = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'O CO1_.2'][0]
    mat_C01.Roughness = 'Rough'
    mat_C01.Thickness = 0.2
    mat_C01.Conductivity = 0.03059
    mat_C01.Density = 1700
    mat_C01.Specific_Heat = 1000
    mat_C01.Thermal_Absorptance = 0.9
    mat_C01.Solar_Absorptance = 0.7
    mat_C01.Visible_Absorptance = 0.7
else:
    idf1.newidfobject(
        'MATERIAL',
        Name='O CO1_.2',
        Roughness='Rough',
        Thickness=0.2,
        Conductivity=0.03059,
        Density=1700,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7
    )

if 'Cast Concrete_.3' in [mat.Name for mat in idf1.idfobjects['MATERIAL']]:
    mat_cast_concrete_thicker = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'Cast Concrete_.3'][0]
    mat_cast_concrete_thicker.Roughness = 'Rough'
    mat_cast_concrete_thicker.Thickness = 0.3
    mat_cast_concrete_thicker.Conductivity = 1.13
    mat_cast_concrete_thicker.Density = 2000
    mat_cast_concrete_thicker.Specific_Heat = 1000
    mat_cast_concrete_thicker.Thermal_Absorptance = 0.9
    mat_cast_concrete_thicker.Solar_Absorptance = 0.6
    mat_cast_concrete_thicker.Visible_Absorptance = 0.6
else:
    idf1.newidfobject(
        'MATERIAL',
        Name='Cast Concrete_.3',
        Roughness='Rough',
        Thickness=0.3,
        Conductivity=1.13,
        Density=2000,
        Specific_Heat=1000,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.6,
        Visible_Absorptance=0.6
    )

if 'OO CO1' in [i.Name for i in idf1.idfobjects['CONSTRUCTION']]:
    cons_C01 = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO CO1'][0]
    cons_C01.Name = 'OO CO1'
    cons_C01.Outside_Layer = 'OOO CTE Arena_.O25'
    cons_C01.Layer_2 = 'O CO1_.2'
    cons_C01.Layer_3 = 'Cast Concrete_.3'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO CO1',
        Outside_Layer='OOO CTE Arena_.O25',
        Layer_2='O CO1_.2',
        Layer_3='Cast Concrete_.3'
        )

if 'OO CO1_Rev' in [i.Name for i in idf1.idfobjects['CONSTRUCTION']]:
    cons_C01_rev = [i for i in idf1.idfobjects['CONSTRUCTION'] if i.Name == 'OO CO1_Rev'][0]
    cons_C01_rev.Name = 'OO CO1_Rev'
    cons_C01_rev.Outside_Layer = 'Cast Concrete_.3'
    cons_C01_rev.Layer_2 = 'O CO1_.2'
    cons_C01_rev.Layer_3 = 'OOO CTE Arena_.O25'
else:
    idf1.newidfobject(
        'CONSTRUCTION',
        Name='OO CO1_Rev',
        Outside_Layer='Cast Concrete_.3',
        Layer_2='O CO1_.2',
        Layer_3='OOO CTE Arena_.O25'
        )

floors = [i for i in idf1.idfobjects['BuildingSurface:Detailed']
         if i.Surface_Type=='Floor' and i.Outside_Boundary_Condition=='Ground']
# print(floors)
for i in floors:
    i.Construction_Name='OO SO1'

walls = [i for i in idf1.idfobjects['BuildingSurface:Detailed']
         if i.Surface_Type=='Wall' and i.Outside_Boundary_Condition=='Outdoors']
print(walls)
for i in walls:
    i.Construction_Name='OO FO1'

roofs = [i for i in idf1.idfobjects['BuildingSurface:Detailed']
         if i.Surface_Type=='Roof' and i.Outside_Boundary_Condition=='Outdoors']
# print(roofs)
for i in roofs:
    i.Construction_Name='OO CO1'


idf1.savecopy(file.split('.idf')[0]+'_amended.idf')