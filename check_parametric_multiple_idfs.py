import os
import shutil
import tempfile
import pandas as pd

from besos import eppy_funcs as ef
from besos.IO_Objects import Objective

from accim.parametric_and_optimisation.main import OptimParamSimulation
from accim.utils import remove_accents_in_idf, reduce_runtime


class ResultCountObjective(Objective):
    def __init__(self, name='num_result_series'):
        self.name = name

    def setup(self, building):
        return None

    def __call__(self, results):
        return float(len(results))


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    ep_path = r'C:\EnergyPlusV9-6-0'

    idf_paths = [
        os.path.join(base_dir, 'SF_Detached_B_min_North.idf'),
        os.path.join(base_dir, 'SF_Detached_D_min_North.idf'),
    ]
    epw_paths = [
        os.path.join(base_dir, 'seville_2024.epw'),
        os.path.join(base_dir, 'seville_2025.epw'),
        os.path.join(base_dir, 'madrid_2024.epw'),
        os.path.join(base_dir, 'madrid_2025.epw'),
    ]

    temp_dir = tempfile.mkdtemp(prefix='accim_parametric_check_', dir=base_dir)
    temp_idf_paths = []
    try:
        for path in idf_paths:
            temp_path = os.path.join(temp_dir, os.path.basename(path))
            shutil.copy2(path, temp_path)
            remove_accents_in_idf(temp_path)
            temp_idf_paths.append(temp_path)

        buildings = [ef.get_building(path, ep_path=ep_path) for path in temp_idf_paths]
        for building in buildings:
            try:
                reduce_runtime(idf_object=building)
            except IndexError:
                print(f"Skipping reduce_runtime for {building.idfname}: missing required IDF objects.")

        parametric = OptimParamSimulation(
            building=buildings,
            parameters_type=None,
            output_freqs=['hourly'],
            bypass_addAccis=True,
        )

        parametric.set_parameters()
        parametric.sim_outputs = [ResultCountObjective()]
        parametric.set_problem()

        simulation_plan = pd.DataFrame(
            {
                'idf': [
                    'SF_Detached_B_min_North',
                    'SF_Detached_B_min_North',
                    'SF_Detached_D_min_North',
                    'SF_Detached_D_min_North',
                ],
                'epw': [
                    os.path.join(base_dir, 'seville_2024.epw'),
                    os.path.join(base_dir, 'seville_2025.epw'),
                    os.path.join(base_dir, 'madrid_2024.epw'),
                    os.path.join(base_dir, 'madrid_2025.epw'),
                ],
            }
        )

        parametric.run_parametric_simulation(
            epws=epw_paths,
            out_dir=os.path.join(base_dir, 'check_parametric_multiple_idfs_results'),
            df=simulation_plan,
            processes=1,
            keep_dirs=False,
        )
        results = parametric.outputs_param_simulation

        expected_pairs = {
            ('SF_Detached_B_min_North', 'seville_2024'),
            ('SF_Detached_B_min_North', 'seville_2025'),
            ('SF_Detached_D_min_North', 'madrid_2024'),
            ('SF_Detached_D_min_North', 'madrid_2025'),
        }
        obtained_pairs = set(zip(results['idf'], results['epw']))

        if len(results) != 4:
            raise AssertionError(f'Expected 4 simulations, but got {len(results)}.')
        if obtained_pairs != expected_pairs:
            raise AssertionError(f'Unexpected idf/epw combinations: {obtained_pairs}')
        if 'idf' not in results.columns:
            raise AssertionError("Column 'idf' not found in outputs_param_simulation.")
        if 'idf' not in results.attrs.get('parameters_names', []):
            raise AssertionError("Value 'idf' not found in outputs_param_simulation.attrs['parameters_names'].")
        if (results['num_result_series'] <= 0).any():
            raise AssertionError('At least one simulation returned an empty BESOS results payload.')

        print(results[['idf', 'epw', 'num_result_series']])
        print("\nValidation completed successfully.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
