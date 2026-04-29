import accim
from accim.parametric_and_optimisation.main import OptimParamSimulation

# 1. Instanciar en blanco (no ejecuta addAccis)
parametric = OptimParamSimulation()

# 2. Cargar Pickle (¡ya contiene los parámetros, outputs y la configuración!)
parametric.load_outputs_optimisation(pickle_path='testing_new_functionalities_optimisation/outputs_optimisation.pkl')



# 3. Analizar directamente
parametric.plot_parallel_coordinates()
parametric.plot_best_compromise_solutions()


##

from accim.parametric_and_optimisation.main import OptimParamSimulation
OUT_DIR = 'testing_new_functionalities_optimisation'

# 1. Instanciar en blanco (no ejecuta addAccis)
instance = OptimParamSimulation()
# instance.load_outputs_optimisation(pickle_path='testing_new_functionalities_optimisation/outputs_optimisation.pkl')
instance.load_outputs_optimisation(pickle_path='testing_new_functionalities_optimisation/outputs_optimisation_20260427_131743.pkl')
# instance.load_outputs_optimisation(json_path='testing_new_functionalities_optimisation/outputs_optimisation_25400.json')

area = instance.set_building_floor_area(mode='occupied')
# area = instance.set_building_floor_area(mode='list', zones_list=['Floor_1_Zone'])

# zones = [i.Name for i in instance.building.idfobjects['zone']]

instance.get_hourly_df_optimisation(skip_confirmation=True)

print("\n--- [12] Data Visualization ---")
instance.plot_pareto_front(
    out_dir=OUT_DIR,
    color_by='CustAST_ASToffset',
    size_by='CustAST_m',
    normalize_per_m2=True
)
instance.plot_parallel_coordinates(out_dir=OUT_DIR)
instance.plot_pairwise_scatter_matrix(out_dir=OUT_DIR)


