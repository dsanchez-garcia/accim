from accim.data.data_postprocessing import Table

block_zone = {
    'BLOQUE1':[
        'LIVINGXROOM',
        'BEDROOM1',
        'BEDROOM2',
        'MASTERBEDROOM',
        'BATHROOM1',
        'BATHROOM2',
        'KITCHEN',
    ]
}

data_analysis = Table(
    source_concatenated_csv_filepath='ACCIM_Chile[srcfreq-monthly[freq-monthly[frequency_agg_func-sum[standard_outputs-True[CSVconcatenated.csv',
    source_frequency='monthly',
    frequency='monthly',
    frequency_agg_func='sum',
    standard_outputs=True,
    level=['building'],
    level_agg_func=['sum'],
    split_epw_names=True,
    block_zone_hierarchy=block_zone
)