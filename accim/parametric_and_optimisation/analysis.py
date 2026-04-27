import os
import glob
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Literal

class AnalysisMixin:

    def set_building_floor_area(self, mode: Literal['all', 'occupied', 'custom', 'list']='all', zones_list: list=None, custom_area: float=None) -> float:
        """
        Calculates or sets the floor area to be used for normalizing energy results (kWh/m2).
        
        # TODO: Recordatorio para parametrización geométrica.
        # Si se utiliza parametrización de geometría en el futuro (áreas variables entre simulaciones
        # o distintos IDFs base), este cálculo estático aquí no servirá. Debería evaluarse
        # el área en cada variante iterativamente leyendo sus respectivos .bnd o archivos generados.
        
        :param mode: 'all' to use all Floor surfaces in the IDF.
                     'occupied' to use Floor surfaces in zones that have a People object.
                     'custom' to use the value provided in `custom_area`.
                     'list' to use Floor surfaces only in the zones specified in `zones_list`.
        :param zones_list: List of zone names for mode 'list'.
        :param custom_area: Float value for the area in mode 'custom'.
        :return: the calculated or assigned floor area.
        """
        if mode == 'custom':
            if custom_area is None:
                raise ValueError("custom_area must be provided when mode='custom'")
            self.building_floor_area = float(custom_area)
            return self.building_floor_area
        idf = self.building
        try:
            surfaces = idf.idfobjects['BuildingSurface:Detailed']
        except KeyError:
            surfaces = []
        floors = [s for s in surfaces if s.Surface_Type.lower() == 'floor']
        if mode == 'all':
            total_area = sum((f.area for f in floors))
        elif mode == 'occupied':
            occupied_names = set()
            try:
                people_objs = idf.idfobjects['PEOPLE']
            except KeyError:
                people_objs = []
            for p in people_objs:
                name = getattr(p, 'Zone_or_ZoneList_or_Space_or_SpaceList_Name', getattr(p, 'Zone_or_ZoneList_Name', None))
                if name:
                    occupied_names.add(name.upper())
            try:
                for zl in idf.idfobjects['ZONELIST']:
                    if zl.Name.upper() in occupied_names:
                        for i in range(1, 500):
                            z_name = getattr(zl, f'Zone_{i}_Name', getattr(zl, f'Zone_Name_{i}', None))
                            if z_name:
                                occupied_names.add(z_name.upper())
            except KeyError:
                pass
            try:
                for sl in idf.idfobjects['SPACELIST']:
                    if sl.Name.upper() in occupied_names:
                        for i in range(1, 500):
                            s_name = getattr(sl, f'Space_{i}_Name', getattr(sl, f'Space_Name_{i}', None))
                            if s_name:
                                occupied_names.add(s_name.upper())
            except KeyError:
                pass
            try:
                for s in idf.idfobjects['SPACE']:
                    if s.Name.upper() in occupied_names:
                        z_name = getattr(s, 'Zone_Name', getattr(s, 'Zone_or_ZoneList_Name', None))
                        if z_name:
                            occupied_names.add(z_name.upper())
            except KeyError:
                pass
            total_area = 0.0
            for f in floors:
                z_name = getattr(f, 'Zone_Name', '').upper()
                s_name = getattr(f, 'Space_Name', '').upper()
                if z_name in occupied_names or s_name in occupied_names:
                    total_area += f.area
        elif mode == 'list':
            if not zones_list:
                raise ValueError("zones_list must be provided when mode='list'")
            upper_zones = [z.upper() for z in zones_list]
            total_area = sum((f.area for f in floors if getattr(f, 'Zone_Name', '').upper() in upper_zones or getattr(f, 'Space_Name', '').upper() in upper_zones))
        else:
            raise ValueError(f'Unknown mode: {mode}')
        self.building_floor_area = total_area
        return total_area

    def run_sensitivity_analysis(self, method: Literal['sobol', 'morris']='sobol', **kwargs) -> dict:
        """
        Runs Sensitivity Analysis on the results of a parametric simulation using SALib.
        
        :param method: 'sobol' or 'morris'. Must match the sampling method used.
        :param kwargs: additional arguments to pass to SALib.analyze.sobol or SALib.analyze.morris.
        :return: a dictionary mapping each output name to its SALib analysis results.
        """
        if getattr(self, 'last_run_type', None) != 'parametric':
            raise ValueError('Sensitivity Analysis can only be run after a parametric simulation. Please ensure you run run_parametric_simulation() first.')
        if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
            raise ValueError('You must run run_parametric_simulation before running sensitivity analysis.')
        try:
            from SALib.analyze import sobol, morris
        except ImportError:
            raise ImportError('SALib is required for Sensitivity Analysis. Install it with: pip install SALib')
        problem = self._get_salib_problem()
        df = self.outputs_param_simulation
        output_names = self.problem.names('outputs')
        results = {}
        for output_name in output_names:
            if output_name not in df.columns:
                print(f'Warning: Output {output_name} not found in results DataFrame. Skipping.')
                continue
            Y = df[output_name].values.astype(float)
            if method == 'sobol':
                try:
                    res = sobol.analyze(problem, Y, **kwargs)
                except ValueError as e:
                    raise ValueError(f'Error analyzing with Sobol. Make sure you generated samples with sampling_sobol(). Details: {e}')
            elif method == 'morris':
                try:
                    res = morris.analyze(problem, df[problem['names']].values.astype(float), Y, **kwargs)
                except ValueError as e:
                    raise ValueError(f'Error analyzing with Morris. Make sure you generated samples with sampling_morris(). Details: {e}')
            else:
                raise ValueError(f'Unknown sensitivity analysis method: {method}')
            results[output_name] = res
        self.sensitivity_results = results
        return results

    def get_best_compromise_solution(self, method: Literal['knee_point', 'topsis']='topsis', weights: list=None) -> pd.DataFrame:
        """
        Identifies the best compromise solution from the Pareto front.

        :param method: The MCDM method to use. 'knee_point' (closest distance to Utopia point) or 'topsis'.
        :param weights: A list of weights for each objective, used only in 'topsis'. 
            If None, equal weights are applied. Must match the number of objectives.
        :return: A pandas DataFrame containing the best compromise solution(s).
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('MCDM best compromise solutions can only be evaluated after an optimisation simulation. Please ensure you run run_optimisation() first.')
        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError('No optimization results found. Run optimization first.')
        pareto_df = self.outputs_optimisation[self.outputs_optimisation['pareto-optimal'] == True].copy()
        if pareto_df.empty:
            raise ValueError('No Pareto optimal solutions found in outputs_optimisation.')
        output_names = self.problem.names('outputs')
        minimize_outputs = getattr(self.problem, 'minimize_outputs', None)
        if minimize_outputs is None:
            minimize_flags = [True] * len(output_names)
        else:
            minimize_flags = [m if m is not None else True for m in minimize_outputs]
        obj_values = pareto_df[output_names].values.astype(float)
        mins = obj_values.min(axis=0)
        maxs = obj_values.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1.0
        norm_values = (obj_values - mins) / ranges
        if method == 'knee_point':
            utopia = np.zeros(len(output_names))
            for (i, minimize) in enumerate(minimize_flags):
                if not minimize:
                    utopia[i] = 1.0
            distances = np.sqrt(np.sum((norm_values - utopia) ** 2, axis=1))
            pareto_df['distance_to_utopia'] = distances
            best_idx = np.argmin(distances)
            return pareto_df.iloc[[best_idx]].copy()
        elif method == 'topsis':
            if weights is None:
                weights = np.ones(len(output_names)) / len(output_names)
            else:
                if len(weights) != len(output_names):
                    raise ValueError(f'Length of weights ({len(weights)}) must match number of outputs ({len(output_names)}).')
                weights = np.array(weights) / np.sum(weights)
            sq_sum = np.sqrt(np.sum(obj_values ** 2, axis=0))
            sq_sum[sq_sum == 0] = 1.0
            topsis_norm = obj_values / sq_sum
            weighted_norm = topsis_norm * weights
            ideal_best = np.zeros(len(output_names))
            ideal_worst = np.zeros(len(output_names))
            for (i, minimize) in enumerate(minimize_flags):
                if minimize:
                    ideal_best[i] = np.min(weighted_norm[:, i])
                    ideal_worst[i] = np.max(weighted_norm[:, i])
                else:
                    ideal_best[i] = np.max(weighted_norm[:, i])
                    ideal_worst[i] = np.min(weighted_norm[:, i])
            d_best = np.sqrt(np.sum((weighted_norm - ideal_best) ** 2, axis=1))
            d_worst = np.sqrt(np.sum((weighted_norm - ideal_worst) ** 2, axis=1))
            denom = d_best + d_worst
            denom[denom == 0] = 1.0
            closeness = d_worst / denom
            pareto_df['topsis_score'] = closeness
            best_idx = np.argmax(closeness)
            return pareto_df.iloc[[best_idx]].copy()
        else:
            raise ValueError(f'Unknown MCDM method: {method}')

    def run_sensitivity_analysis_by_epw(self, method: Literal['sobol', 'morris']='morris', out_dir: str='.', **kwargs) -> dict:
        """
        Runs Sensitivity Analysis separately for each EPW found in
        ``outputs_param_simulation``, saves a CSV and a bar-chart PNG per EPW,
        and returns a nested dict ``{epw_label: SALib_results_dict}``.

        The results are also stored in ``self.sensitivity_results_by_epw``.

        Typical workflow::

            sim.sampling_morris(num_samples=50)
            sim.run_parametric_simulation(epws=['Seville.epw', 'Sydney.epw'], ...)
            sa = sim.run_sensitivity_analysis_by_epw(method='morris', out_dir='results')

        :param method: ``'sobol'`` or ``'morris'``. Must match the sampling
            method used before calling ``run_parametric_simulation``.
        :param out_dir: directory where CSV and PNG files will be saved.
        :param kwargs: additional keyword arguments forwarded to
            ``run_sensitivity_analysis``.
        :return: nested dict ``{epw_label: {output_name: SALib_result}}``.
        """
        if getattr(self, 'last_run_type', None) != 'parametric':
            raise ValueError('Sensitivity Analysis by EPW can only be run after a parametric simulation. Please ensure you run run_parametric_simulation() first.')
        import matplotlib
        import matplotlib.pyplot as plt
        if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
            raise ValueError('No parametric simulation results found. Run run_parametric_simulation before calling this method.')
        os.makedirs(out_dir, exist_ok=True)
        epw_labels = self.outputs_param_simulation['epw'].unique()
        results_by_epw = {}
        original_df = self.outputs_param_simulation
        for epw_label in epw_labels:
            epw_tag = str(epw_label).replace(' ', '_')
            self.outputs_param_simulation = original_df[original_df['epw'] == epw_label].copy()
            sa_results = self.run_sensitivity_analysis(method=method, **kwargs)
            results_by_epw[epw_label] = sa_results
            self.outputs_param_simulation = original_df
            rows = []
            if method == 'sobol':
                for (output_name, res) in sa_results.items():
                    for (param, s1, st) in zip(res['names'], res['S1'], res['ST']):
                        rows.append({'epw': epw_tag, 'output': output_name, 'parameter': param, 'S1': round(float(s1), 4), 'ST': round(float(st), 4)})
                x_labels = ('S1 (first-order)', 'ST (total-order)')
                bar_keys = ('S1', 'ST')
                y_label = 'Sobol Index'
                title_prefix = 'Sobol Sensitivity'
                bar_colours = ('#457b9d', '#e63946')
                ylim = (0, 1)
            else:
                for (output_name, res) in sa_results.items():
                    for (param, mu, mu_star, sigma) in zip(res['names'], res['mu'], res['mu_star'], res['sigma']):
                        rows.append({'epw': epw_tag, 'output': output_name, 'parameter': param, 'mu': round(float(mu), 4), 'mu_star': round(float(mu_star), 4), 'sigma': round(float(sigma), 4)})
                x_labels = ('mu* (importance)', 'sigma (interactions)')
                bar_keys = ('mu_star', 'sigma')
                y_label = 'Morris Index'
                title_prefix = 'Morris Sensitivity'
                bar_colours = ('#457b9d', '#e63946')
                ylim = None
            sa_df = pd.DataFrame(rows)
            fname_csv = os.path.join(out_dir, f'results_sa_{method}_{epw_tag}.csv')
            sa_df.to_csv(fname_csv, index=False)
            print(f'  SA ({method}) results saved: {fname_csv}')
            output_names_sa = list(sa_results.keys())
            n_outputs = len(output_names_sa)
            (fig, axes) = plt.subplots(1, n_outputs, figsize=(6 * n_outputs, 5), squeeze=False)
            width = 0.35
            for (ax_idx, output_name) in enumerate(output_names_sa):
                res = sa_results[output_name]
                ax_sa = axes[0][ax_idx]
                x = np.arange(len(res['names']))
                vals_a = np.abs(res[bar_keys[0]])
                vals_b = np.abs(res[bar_keys[1]])
                ax_sa.bar(x - width / 2, vals_a, width, label=x_labels[0], color=bar_colours[0], alpha=0.85)
                ax_sa.bar(x + width / 2, vals_b, width, label=x_labels[1], color=bar_colours[1], alpha=0.85)
                ax_sa.set_xticks(x)
                ax_sa.set_xticklabels(res['names'], rotation=30, ha='right', fontsize=9)
                ax_sa.set_ylabel(y_label, fontsize=10)
                ax_sa.set_title(f'{title_prefix} — {output_name}\n[{epw_tag}]', fontsize=10)
                ax_sa.legend(fontsize=8)
                if ylim:
                    ax_sa.set_ylim(*ylim)
                ax_sa.axhline(0, color='k', lw=0.5)
            plt.tight_layout()
            fname_plot = os.path.join(out_dir, f'plot_sa_{method}_{epw_tag}.png')
            plt.savefig(fname_plot, dpi=300, bbox_inches='tight')
            plt.close()
            print(f'  SA ({method}) plot saved: {fname_plot}')
        self.sensitivity_results_by_epw = results_by_epw
        return results_by_epw

    def run_clustering(self, n_clusters: int=3, cluster_by: str='parameters', pareto_only: bool=True, out_dir: str='.'):
        """
        if pareto_only and getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('Clustering with pareto_only=True requires an optimisation simulation. Run run_optimisation() first, or set pareto_only=False.')
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('This method requires either a parametric or optimisation simulation to be run first.')

        Groups solutions into K clusters using KMeans to identify design families.
        
        :param n_clusters: Number of clusters (K).
        :param cluster_by: 'parameters' or 'objectives'.
        :param pareto_only: If True, only clusters the Pareto optimal solutions.
        :param out_dir: Output directory for saving the CSV and plot.
        :return: DataFrame with the 'Cluster_ID' column added.
        """
        if pareto_only and getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('Clustering with pareto_only=True requires an optimisation simulation. Please ensure you run run_optimisation() first, or set pareto_only=False.')
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('Clustering requires either a parametric or optimisation simulation to be run first.')
        import os
        import pandas as pd
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        import matplotlib.pyplot as plt
        os.makedirs(out_dir, exist_ok=True)
        df = self.outputs_optimisation.copy()
        if pareto_only:
            df = df[df['pareto-optimal']].copy()
            if df.empty:
                raise ValueError('No Pareto-optimal solutions found to cluster.')
        if cluster_by == 'parameters':
            features = self.problem.names('inputs')
        elif cluster_by == 'objectives':
            features = self.problem.names('outputs')
        else:
            raise ValueError("cluster_by must be 'parameters' or 'objectives'.")
        missing_cols = [f for f in features if f not in df.columns]
        if missing_cols:
            raise KeyError(f'Missing features in DataFrame for clustering: {missing_cols}')
        epw_labels = df['epw'].unique()
        df['Cluster_ID'] = -1
        for epw_label in epw_labels:
            df_epw = df[df['epw'] == epw_label].copy()
            X = df_epw[features].values
            if len(X) < n_clusters:
                print(f'[!] Warning: Not enough points in {epw_label} to form {n_clusters} clusters.')
                df.loc[df['epw'] == epw_label, 'Cluster_ID'] = 0
                continue
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df_epw['Cluster_ID'] = kmeans.fit_predict(X_scaled)
            df.update(df_epw['Cluster_ID'])
        df['Cluster_ID'] = df['Cluster_ID'].astype(int)
        self.outputs_optimisation = df.copy()
        csv_path = os.path.join(out_dir, 'results_clustering.csv')
        df.to_csv(csv_path, index=False)
        print(f'  Clustering complete. Results saved: {csv_path}')
        return df

    def run_robustness_analysis(self, optimal_solutions_df: pd.DataFrame, epws_robustness: list, out_dir: str='.', normalize_per_m2: bool=False):
        """
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('This method requires either a parametric or optimisation simulation to be run first.')

        Evaluates the robustness of selected optimal solutions against variations in weather (multiple EPWs).
        
        TODO: Future expansion could include small mathematical parametric perturbations (e.g. ±5%) 
        within the same method or via an additional argument.
        
        :param optimal_solutions_df: A subset DataFrame of the optimal solutions (e.g., from MCDM).
        :param epws_robustness: A list of EPW strings to test against.
        :param out_dir: Output directory for saving the robustness results.
        """
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('Robustness analysis requires either a parametric or optimisation simulation to be run first.')
        import os
        import glob
        import shutil
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        unit_str = 'kWh/m2' if normalize_per_m2 else 'kWh'
        divisor = divisor
        if normalize_per_m2:
            area = getattr(self, 'building_floor_area', None)
            if not area:
                print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                unit_str = 'kWh'
            else:
                divisor *= area
        os.makedirs(out_dir, exist_ok=True)
        df_params = optimal_solutions_df[self.problem.names('inputs')].copy().drop_duplicates()
        print(f'Starting Robustness Analysis: {len(df_params)} solutions across {len(epws_robustness)} alternative EPWs.')
        results_list = []
        for epw in epws_robustness:
            epw_tag = epw.replace('\\', '/').split('/')[-1].replace('.epw', '')
            print(f'  Evaluating robustness against EPW: {epw_tag}...')
            evaluator = self.set_evaluator(epw=epw, out_dir=out_dir)
            outputs = evaluator.df_apply(df_params, keep_input=True, keep_dirs=False)
            outputs['Robustness_EPW'] = epw_tag
            outputs['Solution_ID'] = 'Sol_' + outputs.index.astype(str)
            results_list.append(outputs)
            worker_dirs = glob.glob(os.path.join(out_dir, 'BESOS_Output*'))
            for w_dir in worker_dirs:
                if os.path.isdir(w_dir):
                    try:
                        shutil.rmtree(w_dir)
                    except Exception:
                        pass
        robustness_df = pd.concat(results_list, ignore_index=True)
        heating_col = next((c for c in robustness_df.columns if 'Heating:Electricity' in c), None)
        cooling_col = next((c for c in robustness_df.columns if 'Cooling:Electricity' in c), None)
        if heating_col and cooling_col:
            robustness_df[f'Total_Energy_{unit_str.replace("/", "_")}'] = (robustness_df[heating_col] + robustness_df[cooling_col]) / divisor
            plt.figure(figsize=(10, 6))
            sns.boxplot(x='Solution_ID', y=f'Total_Energy_{unit_str.replace("/", "_")}', data=robustness_df, color='lightblue')
            sns.stripplot(x='Solution_ID', y=f'Total_Energy_{unit_str.replace("/", "_")}', data=robustness_df, hue='Robustness_EPW', jitter=True, marker='o', alpha=0.8)
            plt.title('Robustness Analysis: Optimal Solutions under Weather Variations')
            plt.ylabel(f'Total HVAC Energy ({unit_str})')
            plt.xlabel('Candidate Solutions')
            plt.legend(title='Climate Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            fname_plot = os.path.join(out_dir, 'plot_robustness_analysis.png')
            plt.savefig(fname_plot, dpi=300, bbox_inches='tight')
            plt.close()
            print(f'  Robustness plot saved: {fname_plot}')
        csv_path = os.path.join(out_dir, 'results_robustness.csv')
        robustness_df.to_csv(csv_path, index=False)
        print(f'  Robustness data saved: {csv_path}')
        return robustness_df