# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2025 Daniel Sánchez-García

# accim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# accim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from eppy import modeleditor
from eppy.modeleditor import IDF
import os

iddfile = r"C:\EnergyPlusV9-4-0\Energy+.idd"
# fname1 = r"D:\OneDrive - UNIVERSIDAD DE SEVILLA\Papers OneDrive\VPO_cadiz_parametrico\BA_V01.idf"

path = r'C:\Users\daniel.sanchez\Documents\Personal\VPO_parametrico\input_IDFs'
outputpath = r'C:\Users\daniel.sanchez\Documents\Personal\VPO_parametrico\output_IDFs'

filelist = [file.split('.idf')[0] for file in os.listdir(path) if file.endswith('.idf')]
print(filelist)

IDF.setiddname(iddfile)

# idf1.printidf()



facade_cond_list = [
    0.01292,
    0.02673,
    0.04152,
    0.05741,
    0.07453,
    0.09302,
    0.11305,
    0.13482,
    0.15858,
    0.18460,
    0.21323,
    0.24487,
    0.28003,
    0.31934,
    0.36357,
    0.41371,
    0.47103,
    0.53718,
    0.61438,
    0.70565,
]

facade_cond_list_full = [
    0.01292,
    0.02673,
    0.04152,
    0.05741,
    0.07453,
    0.09302,
    0.11305,
    0.13482,
    0.15858,
    0.18460,
    0.21323,
    0.24487,
    0.28003,
    0.31934,
    0.36357,
    0.41371,
    0.47103,
    0.53718,
    0.61438,
    0.70565,
    0.81522,
    0.94921,
    1.11681,
    1.33249,
    1.62037,
    2.02402,
    2.63085,
    3.64583,
    5.68946,
    11.93182
]

roof_cond_list = [
    0.03059,
    0.06240,
    0.09552,
    0.13001,
    0.16598,
    0.20350,
    0.24270,
    0.28369,
    0.32658,
    0.37152,
    0.41865,
    0.46814,
    0.52017,
    0.57495,
    0.63269,
    0.69364,
    0.75808,
    0.82632,
    0.89870,
    0.97561,
]

roof_cond_list_full = [
    0.03059,
    0.06240,
    0.09552,
    0.13001,
    0.16598,
    0.20350,
    0.24270,
    0.28369,
    0.32658,
    0.37152,
    0.41865,
    0.46814,
    0.52017,
    0.57495,
    0.63269,
    0.69364,
    0.75808,
    0.82632,
    0.89870,
    0.97561,
    1.05749,
    1.14484,
    1.23822,
    1.33829,
    1.44578,
    1.56156,
    1.68662,
    1.82213,
    1.96944,
    2.13018
]

floor_cond_list_full = [
    0.01679,
    0.03531,
    0.05586,
    0.07879,
    0.10452,
    0.13362,
    0.16678,
    0.20493,
    0.24927,
    0.30145,
    0.36375,
    0.43943,
    0.53333,
    0.65291,
    0.81038,
    1.02714,
    1.34445,
    1.85339,
    2.80267,
    5.19941,
    22.97796,
    -10.89783,
    -4.64513,
    -3.04410,
    -2.31123,
    -1.89099,
    -1.61850,
    -1.42750,
    -1.28618,
    -1.17739
]

floor_cond_list = [
    0.01679,
    0.03531,
    0.05586,
    0.07879,
    0.10452,
    0.13362,
    0.16678,
    0.20493,
    0.24927,
    0.30145,
    0.36375,
    0.43943,
    0.53333,
    0.65291,
    0.81038,
    1.02714,
    1.34445,
    1.85339,
    2.80267,
    5.19941,
]

for file in filelist:
    filename = file
    print(file)
    fname1 = path+'/'+filename + '.idf'
    idf1 = IDF(fname1)

    C01 = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'O CO1_.3'][0]
    C01.Name = 'O CO1_.2'
    C01.Thickness = 0.2

    slab = [mat for mat in idf1.idfobjects['MATERIAL'] if mat.Name == 'OOO Hormigon celular_.1'][0]
    slab.Name = 'Cast Concrete_.3'
    slab.Thickness = 0.3
    slab.Conductivity = 1.13
    slab.Density = 2000
    slab.Thermal_Absorptance = 0.9
    slab.Solar_Absorptance = 0.6
    slab.Visible_Absorptance = 0.6

    buildup = [cons for cons in idf1.idfobjects['CONSTRUCTION'] if cons.Name == 'OO CO1'][0]
    buildup.Layer_2 = 'O CO1_.2'
    buildup.Layer_3 = 'Cast Concrete_.3'

    buildup_rev = [cons for cons in idf1.idfobjects['CONSTRUCTION'] if cons.Name == 'OO CO1_Rev'][0]
    buildup_rev.Outside_Layer = 'Cast Concrete_.3'
    buildup_rev.Layer_2 = 'O CO1_.2'

    facade_mat = [mat
                  for mat
                  in idf1.idfobjects['MATERIAL']
                  if mat.Name == 'O FO1_.125'][0]
    # print(facade_mat)
    roof_mat = [mat
                for mat
                in idf1.idfobjects['MATERIAL']
                if mat.Name == 'O CO1_.2'][0]
    # print(roof_mat)
    try:
        floor_mat = [mat
                     for mat
                     in idf1.idfobjects['MATERIAL']
                     if mat.Name == 'O SO1_.16'][0]
        # print(floor_mat)
        therearefloors = True
    except IndexError:
        therearefloors = False
        # print(therearefloors)
    facade_cond = facade_mat.Conductivity
    # print(facade_cond)
    roof_cond = roof_mat.Conductivity
    # print(roof_cond)
    if therearefloors:
        floor_cond = floor_mat.Conductivity
        # print(floor_cond)
    # else:
    #     print('there are no floors')
    for i in range(len(facade_cond_list)):
        facade_mat.Conductivity = facade_cond_list[i]
        for j in range(len(roof_cond_list)):
            roof_mat.Conductivity = roof_cond_list[j]
            if therearefloors:
                floor_mat.Conductivity = floor_cond_list[j]
                if i+1 < 10:
                    if j+1 < 10:
                        outputname = (
                            filename
                            + '[F0'+repr(i+1)
                            + '[C0'+repr(j+1)
                            + '[S0'+repr(j+1)
                            + '.idf'
                        )
                    else:
                        outputname = (
                            filename
                            + '[F0'+repr(i+1)
                            + '[C'+repr(j+1)
                            + '[S'+repr(j+1)
                            + '.idf'
                        )
                else:
                    if j+1 < 10:
                        outputname = (
                            filename
                            + '[F'+repr(i+1)
                            + '[C0'+repr(j+1)
                            + '[S0'+repr(j+1)
                            + '.idf'
                        )
                    else:
                        outputname = (
                            filename
                            + '[F'+repr(i+1)
                            + '[C'+repr(j+1)
                            + '[S'+repr(j+1)
                            + '.idf'
                        )
            else:
                if i+1 < 10:
                    if j+1 < 10:
                        outputname = (
                            filename
                            + '[F0'+repr(i+1)
                            + '[C0'+repr(j+1)
                            + '[SXX'
                            + '.idf'
                        )
                    else:
                        outputname = (
                            filename
                            + '[F0'+repr(i+1)
                            + '[C'+repr(j+1)
                            + '[SXX'
                            + '.idf'
                        )
                else:
                    if j+1 < 10:
                        outputname = (
                            filename
                            + '[F'+repr(i+1)
                            + '[C0'+repr(j+1)
                            + '[SXX'
                            + '.idf'
                        )
                    else:
                        outputname = (
                            filename
                            + '[F'+repr(i+1)
                            + '[C'+repr(j+1)
                            + '[SXX'
                            + '.idf'
                        )
            idf1.savecopy(outputpath+'/'+outputname)
