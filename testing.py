from eppy import modeleditor
from eppy.modeleditor import IDF
iddfile = r"C:\EnergyPlusV22-2-0\Energy+.idd"
fname1_home = r'C:\Python\accim\OSM_02.idf'
# fname1_uni = r'C:\Users\user\PycharmProjects\accim\accim\OSM_03.idf'
fname1_uni = r'C:\Users\user\PycharmProjects\accim\accim\OSM_Example_00.idf'


IDF.setiddname(iddfile)
idf1 = IDF(fname1_uni)

##
zonelist = []

if len(idf1.idfobjects['zone']) == 1:
    no_of_zones = range(1, 2)
else:
    no_of_zones = range(1, len(idf1.idfobjects['zone']))

for i in no_of_zones:
    for j in idf1.idfobjects['zonelist']:
        for k in idf1.idfobjects['zone']:
            if k.Name in j[f'Zone_{i}_Name']:
                zonelist.append(k.Name)

##
zonelist = []
for i in idf1.idfobjects['zonelist']:
    for j in range(1, len(idf1.idfobjects['zone'])):
        if i[f'Zone_{j}_Name'] != '':
            zonelist.append(i.Name)

##
people_objs = []
for i in idf1.idfobjects['people']:
    no_of_ppl = False
    ppl_per_floor = False
    person_per_floor = False
    try:
        if i.Number_of_People > 0:
             no_of_ppl = True
    except TypeError:
        pass

    try:
        if i.People_per_Floor_Area > 0:
            ppl_per_floor = True
    except TypeError:
        pass

    try:
        if i.Floor_Area_per_Person > 0:
            person_per_floor = True
    except TypeError:
        pass

    if any([no_of_ppl, ppl_per_floor, person_per_floor]):
        people_objs.append(i)

##

