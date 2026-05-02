
# ─── EMS Verification ──────────────────────────────────────────────────────
# Verifies that the ACCIS EMS scripts (setpoints and window operation) are
# working correctly by inspecting the simulation output.

from accim.utils import AccimSimulationVerifier
import os

base_idf = 'OSM_TestResidentialUnit_v01_onlygeometry_SchNatVent_v2520.idf'
output_idf = base_idf.replace('.idf', '') + '[CS_AUS DeDear[CA_80[CM_3[HM_2[VC_0[VO_0.0[MT_50.0[MW_50.0[AT_0.1[NS_X.idf'
output_dir = 'temp_output_dir_vrf_mm_03'


eso_path = os.path.join(output_dir, 'eplusout.csv')

verifier = AccimSimulationVerifier(
    eso_file_path=eso_path,
    idf_path=output_idf,
    # eplus_install_dir=None,  # set to your EnergyPlus dir if auto-detection fails
)

# Show a summary of violations
print('\n=== Verification Summary ===')
print(verifier.summary)

print("\n--- Setpoint Violations Table ---")
df_s = verifier.violations['setpoint']
if not df_s.empty:
    print(df_s.groupby(['zone_or_window', 'check']).size()
          .rename('count').reset_index().to_string(index=False))

print("\n--- Window Violations Table ---")
df_w = verifier.violations['window']
if not df_w.empty:
    print(df_w.groupby(['zone_or_window', 'check']).size()
          .rename('count').reset_index().to_string(index=False))
