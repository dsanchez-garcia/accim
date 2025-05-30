# Scanning occupied zones
self.occupiedZones_orig = []

# Check if model comes from OpenStudio

# Check if ZoneList or SpaceList are used
occupiedZones_orig_osm = []

self.spacelist_use = False
try:
    if len(self.idf1.idfobjects['SPACELIST']) > 0:
        self.spacelist_use = True
        self.spacenames_for_ems_uniquekey = []
        self.spacenames_for_ems_name = []
        self.spacenames_for_ems_uniquekey_people = []
        self.zonenames_for_ems_with_sl = []
        for people in self.idf1.idfobjects['PEOPLE']:
            for spacelist in [i for i in self.idf1.idfobjects['SPACELIST'] if
                              i.Name == people.Zone_or_ZoneList_or_Space_or_SpaceList_Name]:
                for space in [i for i in self.idf1.idfobjects['SPACE'] if i.Space_Type == spacelist.Name]:
                    self.spacenames_for_ems_uniquekey.append(f'{space.Name} {spacelist.Name}')
                    self.spacenames_for_ems_name.append(space.Name)
                    self.spacenames_for_ems_uniquekey_people.append(f'{space.Name} {people.Name}')
                    occupiedZones_orig_osm.append(space.Zone_Name)
                    for zone in [i for i in self.idf1.idfobjects['ZONE'] if space.Zone_Name == i.Name]:
                        self.zonenames_for_ems_with_sl.append(zone.Name)
except KeyError:
    idd = '-'.join([str(i) for i in self.idf1.idd_version])
    print('Searching Spacelist objects returned KeyError. '
          f'That means these are not supported in the EnergyPlus version {idd}')

# occupiedZones_orig_osm = []
# if len([h for h in self.idf1.idfobjects['zonelist']]) > 0:
#     if len(self.idf1.idfobjects['zone']) == 1:
#         no_of_zones = range(1, 2)
#     else:
#         no_of_zones = range(1, len(self.idf1.idfobjects['zone']))
#
#     for i in no_of_zones:
#         for j in self.idf1.idfobjects['zonelist']:
#             for k in self.idf1.idfobjects['zone']:
#                 if k.Name in j[f'Zone_{i}_Name']:
#                     occupiedZones_orig_osm.append(k.Name)
#
#     # for i in self.idf1.idfobjects['zone']:
#     #     if all(i.Name not in [j for j in occupiedZones_orig_osm]):
#     #         occupiedZones_orig_osm.append(i.Name)

occupiedZones_orig_dsb = []
for i in self.idf1.idfobjects['ZONE']:
    for k in self.idf1.idfobjects['PEOPLE']:
        try:
            if i.Name == k.Zone_or_ZoneList_or_Space_or_SpaceList_Name:
                occupiedZones_orig_dsb.append(i.Name.upper())
        except eppy.bunch_subclass.BadEPFieldError:
            if i.Name == k.Zone_or_ZoneList_Name:
                occupiedZones_orig_dsb.append(i.Name.upper())

if self.spacelist_use:
    self.occupiedZones_orig = occupiedZones_orig_osm
    self.occupiedZones = [i.replace(' ', '_') for i in self.occupiedZones_orig]
    self.origin_dsb = False
    self.ems_objs_name = self.spacenames_for_ems_name
    self.ems_objs_key = self.spacenames_for_ems_uniquekey
    self.ems_zonenames = self.zonenames_for_ems_with_sl
    self.ems_zonenames_underscore = [i.replace(' ', '_') for i in self.ems_zonenames]
else:
    self.occupiedZones_orig = occupiedZones_orig_dsb
    self.occupiedZones = [i.replace(':', '_') for i in self.occupiedZones_orig]
    self.origin_dsb = True
    self.ems_objs_name = self.occupiedZones
    self.ems_objs_key = self.occupiedZones_orig
    self.ems_zonenames = self.occupiedZones_orig
    self.ems_zonenames_underscore = self.occupiedZones_orig
