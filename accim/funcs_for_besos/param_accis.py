
def modify_VSToffset(building, value):
    import accim.sim.accis_single_idf_funcs as accis
    accis.modifyAccis(
        idf=building,
        ComfStand=1,
        CAT=3,
        ComfMod=3,
        # SetpointAcc=1000,
        HVACmode=2,
        VentCtrl=0,
        CoolSeasonStart='01/02',
        CoolSeasonEnd='01/03',
        VSToffset=value,
        # MinOToffset=50,
        # MaxWindSpeed=50
    )
    return
