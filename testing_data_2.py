import pandas as pd
x = pd.read_csv(
    'z_other_CSVs/TestModel[CS_INT EN16798[CA_1[CM_1[HM_2[VC_0[VO_0[MT_50[MW_50[AT_0.1[NS_daily[United-Kingdom_Aberdeen_Present.csv')

x['Month'] = x['Date/Time']