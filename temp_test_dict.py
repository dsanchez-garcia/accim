d = {
    1: {
        'name': 'EN16798',
        'CAT':{
            1: 'EN16798 Category I',
            2: 'EN16798 Category II',
            3: 'EN16798 Category III',
        },
        'ComfMod': {
            0: 'EN16798 Static setpoints',
            1: 'EN16798 Adaptive setpoints when applicable, otherwise CTE',
            2: 'EN16798 Adaptive setpoints when applicable, otherwise EN16798 Static setpoints',
            3: 'EN16798 Adaptive setpoints when applicable, otherwise EN16798 Adaptive setpoints horizontally extended',
        }
    },
    2: {
        'name': 'ASHRAE55',
        'CAT': {
            80: 'ASHRAE 55 80% acceptability',
            90: 'ASHRAE 55 90% acceptability',
        },
        'ComfMod': {
            0: 'ASHRAE 55 Static setpoints (calculated with Clima Tool)',
            1: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise CTE',
            2: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Static setpoints',
            3: 'ASHRAE 55 Adaptive setpoints when applicable, otherwise ASHRAE 55 Adaptive setpoints horizontally extended',
        }
    }
}

d[1]['name']
d[1]['CAT'][1]

CSlist = [1, 2]

for i in CSlist:
    print('For the comfort standard ' + d[i]['name'] + ', the available categories you can choose are: ')
    for j in d[i]['CAT']:
        print(str(j) + ' = '+ d[i]['CAT'][j])
    # print(d[i]['CAT'], sep='\n')