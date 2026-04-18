# from accim.utils import update_idf_version
# from os import listdir
# idfs = [i for i in listdir() if i.endswith('.idf')]
# for idf in idfs:
#     update_idf_version(
#         input_idf_path=idf,
#         ep_version_target='25.1.0',
#         # output_idf_name ='OSM_SmallOffice_noHVAC_always-occ_V{version}.idf'
#     )

from accim.utils import update_idf_version

# Works
# base_idf = 'TestModel_ExistingHVAC_PTAC.idf'
# base_idf = 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf'

# Do not work
# base_idf = 'OSM_SmallOffice_exHVAC_always-occ.idf'

# Testing:
base_idf = 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf'




# update_idf_version(input_idf_path=base_idf, ep_version_target='25.2.0')




from accim.sim import accis
accis.addAccis(
    idfs=[base_idf],
    ScriptType='vrf_mm',
    SupplyAirTempInputMethod='temperature difference',
    Output_keep_existing=False,
    Output_type='detailed',
    Output_freqs=['timestep'],
    # EnergyPlus_version='auto',
    TempCtrl='temp',
    ComfStand=[14],
    CAT=[80],
    ComfMod=[3],
    HVACmode=[2],
    VentCtrl=[0],
    VSToffset=[0],
    MinOToffset=[50],
    MaxWindSpeed=[50],
    ASTtol_steps=0.1,
    ASTtol_start=0.1,
    ASTtol_end_input=0.1,
    confirmGen=True
)

#

from besos.eplus_funcs import run_building, run_energyplus
import os

base_idf = 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf'

output_idf = base_idf.replace('.idf', '') + '[CS_AUS DeDear[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
output_dir = 'temp_output_dir_vrf_mm_02'

run_energyplus(
    # building_path='TestResidentialUnit_v01_onlygeometry_SchNatVent[CS_AUS DeDear[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf',
    # building_path='OSM_SmallOffice_exHVAC_always-occ.idf',
    # building_path='TestModel_ExistingHVAC_PTAC.idf',
    building_path=output_idf,
    epw='Sydney.epw',
    out_dir=output_dir
)

##

# ─── EMS Verification ──────────────────────────────────────────────────────
# Verifies that the ACCIS EMS scripts (setpoints and window operation) are
# working correctly by inspecting the simulation output.

from accim.utils import verify_accim_simulation
import os

base_idf = 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf'
output_idf = base_idf.replace('.idf', '') + '[CS_AUS DeDear[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
output_dir = 'temp_output_dir_vrf_mm_02'


eso_path = os.path.join(output_dir, 'eplusout.eso')

df_violations = verify_accim_simulation_simple(
    eso_file_path=eso_path,
    idf_path=output_idf,
    # eplus_install_dir=None,  # set to your EnergyPlus dir if auto-detection fails
)

# Show a summary of violations (empty DataFrame means all checks passed)
print('\n=== Verification Summary ===')
if df_violations.empty:
    print('✓ All EMS checks passed.')
else:
    print(f'✗ {len(df_violations)} violation(s) found:')
    print(df_violations.groupby(['zone_or_window', 'check']).size()
          .rename('count').reset_index().to_string(index=False))
    print('\nFull details stored in df_violations.')
