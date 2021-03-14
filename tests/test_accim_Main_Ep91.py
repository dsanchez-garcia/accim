from accim.sim import accim_Main

def test_accimobj_SingleZone_Ep91():
    from accim.sim import accim_Main
    import os
    originalname = 'TestModel_SingleZone'
    newidfname = originalname + '_pymod'

    z = accim_Main.accimobj_SingleZone_Ep91(
        filename_temp=originalname,
        verboseMode=False
        )

    assert (newidfname + '.idf') in [i for i in os.listdir() if '_pymod' in i]
    os.remove(newidfname+'.idf')


def test_accimobj_MultipleZone_Ep91():
    from accim.sim import accim_Main
    import os
    originalname = 'TestModel_MultipleZone'
    newidfname = originalname + '_pymod'

    z = accim_Main.accimobj_MultipleZone_Ep91(
        filename_temp=originalname,
        verboseMode=False
        )

    assert (newidfname + '.idf') in [i for i in os.listdir() if '_pymod' in i]
    os.remove(newidfname+'.idf')


def test_accimInstance():
    from accim.sim import accim_Main
    import os
    from eppy.modeleditor import IDF

    iddfile = 'C:/EnergyPlusV9-1-0/Energy+.idd'
    IDF.setiddname(iddfile)

    originalname = 'TestModel_SingleZone'
    newidfname = originalname + '_pymod'
    idf0 = IDF(originalname + '.idf')

    zonenames_orig = ([zone.Name for zone in idf0.idfobjects['ZONE']])
    z = accim_Main.accimInstance(
        filename_temp=originalname,
        ScriptType='sz',
        EnergyPlus_version='ep91',
        verboseMode=False
    )
    assert (newidfname + '.idf') in [i for i in os.listdir() if '_pymod' in i]
    assert zonenames_orig == z.zonenames_orig
    os.remove(newidfname + '.idf')

    originalname = 'TestModel_MultipleZone'
    newidfname = originalname + '_pymod'
    idf0 = IDF(originalname + '.idf')

    zonenames_orig = ([zone.Name for zone in idf0.idfobjects['ZONE']])
    windownamelist_orig = (
        [window.Name for window in idf0.idfobjects['AirflowNetwork:MultiZone:Component:DetailedOpening'] if
         window.Name.endswith('_Win')])
    z = accim_Main.accimInstance(
        filename_temp=originalname,
        ScriptType='mz',
        EnergyPlus_version='ep91',
        verboseMode=False
    )

    assert (newidfname + '.idf') in [i for i in os.listdir() if '_pymod' in i]
    assert zonenames_orig == z.zonenames_orig
    assert windownamelist_orig == z.windownamelist_orig
    os.remove(newidfname + '.idf')
