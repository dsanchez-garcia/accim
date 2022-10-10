from eppy import modeleditor
from eppy.modeleditor import IDF
iddfile = r"C:\EnergyPlusV22-2-0\Energy+.idd"
fname1 = r'C:\Python\accim\OSM_02.idf'

IDF.setiddname(iddfile)
idf1 = IDF(fname1)

[i for i in idf1.idfobjects['zone']][0]

zonelist = []
for i in idf1.idfobjects['zonelist']:
    for j in idf1.idfobjects['people']:
        if j.Zone_or_ZoneList_or_Space_or_SpaceList_Name in i.Name:
            zonelist.append(i)

len(zonelist[0])
print([i for i in zonelist[0]])

for i in zonelist[0]:
    for i in range(len(idf1.idfobjects['zone'])):
        try:
            zonelist[0].Zone_


#try fitering by number of people > 0, or People per Floor Area {person/m2} > 0, or Floor Area per Person {m2/person} > 0