import os
import glob
import pandas as pd
from besos import eplus_funcs
from accim.parametric_and_optimisation.main import OptimParamSimulation

def main():
    # 1. Recopilar archivos
    # Ignora cualquier archivo que no sea .epw o .idf
    all_epws = glob.glob('*.epw')
    all_idfs = glob.glob('*.idf')

    # 2. Operación con eppy/besos antes de instanciar (opcional)

    # 3. Definir reglas de mapeo
    epw_mapping_rules = {
        'type': {
            'tmy': 'tmy',
            'met': 'met',
            'long-term': [str(year) for year in range(2005, 2026)] # Busca cualquier año entre 2005 y 2025
        },
        'city': {
            'granada': 'granada',
            'seville': 'seville',
            'malaga': 'malaga',
            'madrid': 'madrid',
            'leon': 'leon'
        }
    }

    idf_mapping_rules = {
        'climate_zone': {
            'A': '_A_',
            'B': '_B_',
            'C': '_C_',
            'D': '_D_',
            'E': '_E_'
        },
        'performance': {
            'max': 'max',
            'min': 'min'
        }
    }

    # 4. Plan de simulación customizado (mapeo IDF-EPW)
    custom_plan = []
    for epw in all_epws:
        epw_lower = epw.lower()
        for idf in all_idfs:
            idf_lower = idf.lower()
            
            # Asignaciones específicas pedidas
            if 'leon' in epw_lower and '_e_' in idf_lower:
                custom_plan.append({'idf': idf.replace('.idf', ''), 'epw': epw})
            elif 'seville' in epw_lower and '_b_' in idf_lower:
                custom_plan.append({'idf': idf.replace('.idf', ''), 'epw': epw})
            elif 'madrid' in epw_lower and '_d_' in idf_lower:
                custom_plan.append({'idf': idf.replace('.idf', ''), 'epw': epw})
            elif 'malaga' in epw_lower and '_a_' in idf_lower:
                custom_plan.append({'idf': idf.replace('.idf', ''), 'epw': epw})
            elif 'granada' in epw_lower and '_c_' in idf_lower:
                custom_plan.append({'idf': idf.replace('.idf', ''), 'epw': epw})

    custom_plan_df = pd.DataFrame(custom_plan)

    from accim.utils import get_building
    buildings = [get_building(idf) for idf in all_idfs]

    # 6. Instanciar OptimParamSimulation
    # bypass_addAccis=True evita ejecutar addAccis ni apply_apmv_setpoints
    # parameters_type=None porque no usamos parámetros custom predefinidos
    sim = OptimParamSimulation(
        buildings=buildings,
        epws=all_epws,
        parameters_type=None,
        bypass_addAccis=True
    )

    # 7. Aplicar reglas de mapeo de categoría y previsualizar
    sim.set_category_mapping(
        epw_mapping_rules=epw_mapping_rules,
        idf_mapping_rules=idf_mapping_rules
    )
    preview = sim.preview_category_mapping()
    print("\nEPW Preview:")
    print(preview['epw'].head(10).to_string(index=False))
    print("\nIDF Preview:")
    print(preview['idf'].head(10).to_string(index=False))

    # 8. Configurar outputs (solo DistrictHeating:Facility y DistrictCooling:Facility)
    df_output_meter = pd.DataFrame([
        {'key_name': 'DistrictHeating:Facility', 'frequency': 'hourly'},
        {'key_name': 'DistrictCooling:Facility', 'frequency': 'hourly'}
    ])
    sim.set_outputs_for_simulation(
        df_output_meter=df_output_meter,
        df_output_variable=None
    )

    # Sin variables de parametrización adicionales
    sim.set_parameters()
    sim.set_problem()

    # 9. Asignar el plan de muestreo manual (sampling_custom)
    sim.sampling_custom(custom_plan_df)

    # 10. Lanzar simulaciones (keep_dirs=True para guardar todos los resultados)
    sim.run_parametric_simulation(
        epws=all_epws,
        out_dir='results_parametric',
        df=sim.parameters_values_df,
        processes=4, # Ajusta según los cores que desees utilizar
        keep_dirs=True,
        keep_input=True
    )
    
    # 11. Configurar y aplicar mapeo de categorías
    epw_mapping_rules = {
        'city': {
            'seville': ['seville'],
            'sydney': ['sydney'],
            'madrid': ['madrid']
        },
        'weather_type': {
            'tmy': ['seville.epw', 'sydney.epw'],
            'met': ['2024', '2025']
        }
    }
    idf_mapping_rules = {
        'performance': {
            'type_a': ['a_max'],
            'type_b': ['b_min'],
            'type_d': ['d_min'],
            'test': ['test']
        }
    }
    sim.set_category_mapping(epw_mapping_rules=epw_mapping_rules, idf_mapping_rules=idf_mapping_rules)
    sim.apply_category_mapping()
    
    # 12. Generar boxplots categóricos con overlay de tmy y met
    print("\nGenerando boxplots de energía...")
    sim.plot_categorical_boxplots(
        df_source='parametric', 
        col='city', 
        row='performance', 
        highlight_dict={'weather_type': ['tmy', 'met']},
        out_dir='results_parametric'
    )
    sim.plot_categorical_boxplots(
        df_source='parametric', 
        col='city', 
        hue='performance', 
        highlight_dict={'weather_type': ['tmy', 'met']},
        out_dir='results_parametric'
    )
    
    print("\nSimulaciones y análisis completados. Resultados guardados en 'results_parametric'.")

if __name__ == '__main__':
    main()
