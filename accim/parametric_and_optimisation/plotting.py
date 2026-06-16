import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import seaborn as sns

class PlottingMixin:

    @staticmethod
    def _safe_plot_token(value: str) -> str:
        token = re.sub(r'[^A-Za-z0-9_.-]+', '_', str(value).strip())
        return token.strip('_') or 'unknown'

    @staticmethod
    def _is_energy_like_column(column_name: str) -> bool:
        keywords = ('heating', 'cooling', 'energy', 'electricity', 'gas', 'facility')
        lowered = str(column_name).lower()
        return any(k in lowered for k in keywords)

    def _get_plot_source_df(self, df_source: str = 'parametric') -> pd.DataFrame:
        source_map = {
            'parametric': 'outputs_param_simulation',
            'optimisation': 'outputs_optimisation',
        }
        if df_source not in source_map:
            raise ValueError("df_source must be 'parametric' or 'optimisation'")
        df = getattr(self, source_map[df_source], None)
        if df is None or df.empty:
            raise ValueError(f'No results found for {df_source}. Please run the simulation first.')
        return df.copy()

    def _normalise_plot_columns(self, df: pd.DataFrame, columns: list, normalize_per_m2: bool = False) -> tuple[pd.DataFrame, dict]:
        outputs_normalized = getattr(self, 'outputs_normalized', False)
        area_attr = getattr(self, 'building_floor_area', None)

        if outputs_normalized:
            if normalize_per_m2:
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect.')
            normalize_per_m2 = False
            base_divisor = 1.0
            energy_unit = 'kWh/m2'
        else:
            base_divisor = 3600000.0
            energy_unit = 'kWh/m2' if normalize_per_m2 else 'kWh'
            if normalize_per_m2 and not area_attr:
                print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                normalize_per_m2 = False
                energy_unit = 'kWh'

        unit_map = {}
        for column in list(dict.fromkeys(columns)):
            if column not in df.columns:
                continue
            if not pd.api.types.is_numeric_dtype(df[column]):
                unit_map[column] = None
                continue
            if not self._is_energy_like_column(column):
                unit_map[column] = None
                continue

            if outputs_normalized:
                unit_map[column] = energy_unit
                continue

            if normalize_per_m2:
                if isinstance(area_attr, dict) and 'idf' in df.columns:
                    divisors = df['idf'].map(area_attr).fillna(1.0) * base_divisor
                else:
                    area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    divisors = base_divisor * area_val
            else:
                divisors = base_divisor

            df[column] = df[column] / divisors
            unit_map[column] = energy_unit

        return (df, unit_map)

    def plot_best_compromise_solutions(self, out_dir: str='.', mcdm_configs: list=None, normalize_per_m2: bool=False) -> pd.DataFrame:
        """
        Identifies the best compromise solution(s) from the Pareto front for
        each EPW found in ``outputs_optimisation``, saves the results to a
        CSV and a scatter-plot PNG, and returns the combined DataFrame.

        :param out_dir: directory where output files will be saved.
        :param mcdm_configs: list of dicts, each specifying one MCDM run.
            Each dict must have a ``'method'`` key (``'knee_point'`` or
            ``'topsis'``) and may optionally have:

            - ``'weights'``: list of per-objective weights (TOPSIS only).
            - ``'label'``: string label used in the legend and CSV column
              (auto-generated if omitted).

            Default (when ``None``)::

                [
                    {'method': 'knee_point'},
                    {'method': 'topsis'},
                    {'method': 'topsis', 'weights': [0.7, 0.3], 'label': 'topsis_w70_30'},
                ]

        :return: pandas DataFrame with all best solutions (one row per
            EPW × MCDM method), also saved to CSV.
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('MCDM best compromise solutions can only be evaluated after an optimisation simulation. Please ensure you run run_optimisation() first.')
        import matplotlib.pyplot as plt
        if getattr(self, 'outputs_normalized', False):
            if normalize_per_m2:
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect.')
            normalize_per_m2 = False
            unit_str = 'kWh/m2'
            base_divisor = 1.0
        else:
            unit_str = 'kWh/m2' if normalize_per_m2 else 'kWh'
            base_divisor = 3600000.0
            if normalize_per_m2:
                area_attr = getattr(self, 'building_floor_area', None)
                if not area_attr:
                    print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                    unit_str = 'kWh'
                    normalize_per_m2 = False
        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError('No optimisation results found. Run run_optimisation (or load via load_outputs_optimisation) first.')
        os.makedirs(out_dir, exist_ok=True)
        if mcdm_configs is None:
            output_names = self.problem.names('outputs')
            n_obj = len(output_names)
            mcdm_configs = [{'method': 'knee_point'}, {'method': 'topsis'}, {'method': 'topsis', 'weights': [0.7] + [0.3 / max(n_obj - 1, 1)] * (n_obj - 1), 'label': 'topsis_w70_30'}]
        label_counts: dict = {}
        for cfg in mcdm_configs:
            if 'label' not in cfg:
                base = cfg['method']
                label_counts[base] = label_counts.get(base, 0) + 1
                suffix = '' if label_counts[base] == 1 else f'_{label_counts[base]}'
                cfg['label'] = f'{base}{suffix}'
        _marker_cycle = ['*', 'D', 's', '^', 'P', 'X', 'v', 'o']
        _colour_cycle = ['#e63946', '#f4a261', '#2a9d8f', '#e9c46a', '#264653', '#a8dadc', '#457b9d', '#6d6875']
        _size_cycle = [220, 120, 120, 120, 120, 120, 120, 120]
        epw_labels = self.outputs_optimisation['epw'].unique()
        output_names = self.problem.names('outputs')
        heating_col = next((c for c in output_names if 'Heating' in c), output_names[0])
        _fallback_cool = output_names[-1] if len(output_names) > 1 else output_names[0]
        cooling_col = next((c for c in output_names if 'Cooling' in c), _fallback_cool)
        all_mcdm_rows = []
        original_optim = self.outputs_optimisation
        for epw_label in epw_labels:
            epw_tag = str(epw_label).replace(' ', '_')
            self.outputs_optimisation = original_optim[original_optim['epw'] == epw_label].copy()
            print(f'\n  [{epw_tag}] Best compromise solutions:')
            for cfg in mcdm_configs:
                method = cfg['method']
                weights = cfg.get('weights', None)
                label = cfg['label']
                row_df = self.get_best_compromise_solution(method=method, weights=weights)
                row_df = row_df.copy()
                row_df['mcdm_method'] = label
                row_df['epw'] = epw_tag
                all_mcdm_rows.append(row_df)
                if normalize_per_m2:
                    if isinstance(area_attr, dict) and 'idf' in row_df.columns:
                        area_val = area_attr.get(row_df['idf'].iloc[0], 1.0)
                    else:
                        area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    div = base_divisor * area_val
                else:
                    div = base_divisor
                    
                h_kwh = row_df[heating_col].iloc[0] / div
                c_kwh = row_df[cooling_col].iloc[0] / div
                print(f'    {label:25s} | {heating_col}={h_kwh:.1f} {unit_str} | {cooling_col}={c_kwh:.1f} {unit_str}')
            self.outputs_optimisation = original_optim
        mcdm_df = pd.concat(all_mcdm_rows, ignore_index=True)
        fname_csv = os.path.join(out_dir, 'results_mcdm_best_solutions.csv')
        mcdm_df.to_csv(fname_csv, index=False)
        print(f'\n  MCDM summary saved: {fname_csv}')
        (fig, axes) = plt.subplots(1, len(epw_labels), figsize=(8 * len(epw_labels), 6), squeeze=False)
        for (ax_idx, epw_label) in enumerate(epw_labels):
            epw_tag = str(epw_label).replace(' ', '_')
            ax_m = axes[0][ax_idx]
            df_epw = original_optim[original_optim['epw'] == epw_label].copy()
            if normalize_per_m2:
                if isinstance(area_attr, dict) and 'idf' in df_epw.columns:
                    areas = df_epw['idf'].map(area_attr).fillna(1.0)
                    divs = base_divisor * areas
                else:
                    area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    divs = base_divisor * area_val
            else:
                divs = base_divisor
                
            df_epw['_h'] = df_epw[heating_col] / divs
            df_epw['_c'] = df_epw[cooling_col] / divs
            dom = df_epw[~df_epw['pareto-optimal']]
            par = df_epw[df_epw['pareto-optimal']]
            ax_m.scatter(dom['_h'], dom['_c'], c='#cccccc', alpha=0.3, s=15, zorder=1)
            ax_m.scatter(par['_h'], par['_c'], c='#457b9d', alpha=0.6, s=40, edgecolors='k', linewidths=0.4, zorder=2, label='Pareto-optimal')
            for (i, cfg) in enumerate(mcdm_configs):
                label = cfg['label']
                row = mcdm_df[(mcdm_df['epw'] == epw_tag) & (mcdm_df['mcdm_method'] == label)]
                if row.empty:
                    continue
                if normalize_per_m2:
                    if isinstance(area_attr, dict) and 'idf' in row.columns:
                        area_val = area_attr.get(row['idf'].iloc[0], 1.0)
                    else:
                        area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    div = base_divisor * area_val
                else:
                    div = base_divisor
                    
                h = row[heating_col].iloc[0] / div
                c = row[cooling_col].iloc[0] / div
                ax_m.scatter(h, c, marker=_marker_cycle[i % len(_marker_cycle)], c=_colour_cycle[i % len(_colour_cycle)], s=_size_cycle[i % len(_size_cycle)], zorder=5, edgecolors='k', linewidths=0.6, label=label)
            ax_m.set_xlabel(f'{heating_col} ({unit_str})', fontsize=11)
            ax_m.set_ylabel(f'{cooling_col} ({unit_str})', fontsize=11)
            ax_m.set_title(f'Pareto Front + MCDM best solutions\n[{epw_tag}]', fontsize=11)
            ax_m.legend(fontsize=9)
        plt.tight_layout()
        fname_plot = os.path.join(out_dir, 'plot_mcdm_best_solutions.png')
        plt.savefig(fname_plot, dpi=300, bbox_inches='tight')
        plt.close()
        print(f'  MCDM plot saved: {fname_plot}')
        return mcdm_df

    def plot_pareto_front(self, color_by: str=None, size_by: str=None, out_dir: str='.', normalize_per_m2: bool=False):
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('This method can only be run after an optimisation simulation. Ensure you run run_optimisation() first.')

        Plots the Pareto front scatter for each EPW.
        If color_by is provided a colorbar is added. If size_by is provided,
        representative size handles appear in the legend.
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('Pareto front scatter plot can only be generated after an optimisation simulation. Please ensure you run run_optimisation() first.')
        import os
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        from matplotlib.colors import Normalize
        from matplotlib.lines import Line2D
        import pandas as pd
        if getattr(self, 'outputs_normalized', False):
            if normalize_per_m2:
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect.')
            normalize_per_m2 = False
            unit_str = 'kWh/m2'
            base_divisor = 1.0
        else:
            unit_str = 'kWh/m2' if normalize_per_m2 else 'kWh'
            base_divisor = 3600000.0
            if normalize_per_m2:
                area_attr = getattr(self, 'building_floor_area', None)
                if not area_attr:
                    print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                    unit_str = 'kWh'
                    normalize_per_m2 = False
        os.makedirs(out_dir, exist_ok=True)
        df = self.outputs_optimisation.copy()
        epw_labels = df['epw'].unique()
        heating_col = next((c for c in df.columns if 'Heating:Electricity' in c), None)
        cooling_col = next((c for c in df.columns if 'Cooling:Electricity' in c), None)
        if not heating_col or not cooling_col:
            print('[!] Heating or Cooling electricity columns not found.')
            return
        for epw_label in epw_labels:
            epw_tag = epw_label.replace('\\', '/').split('/')[-1].replace('.epw', '').replace(' ', '_')
            df_epw = df[df['epw'] == epw_label].copy()
            pareto_epw = df_epw[df_epw['pareto-optimal']].copy()
            dominated_epw = df_epw[~df_epw['pareto-optimal']].copy()
            if normalize_per_m2:
                if isinstance(area_attr, dict) and 'idf' in df_epw.columns:
                    areas = df_epw['idf'].map(area_attr).fillna(1.0)
                    divs = base_divisor * areas
                    
                    dom_divs = dominated_epw['idf'].map(area_attr).fillna(1.0) * base_divisor
                    par_divs = pareto_epw['idf'].map(area_attr).fillna(1.0) * base_divisor
                else:
                    area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    divs = base_divisor * area_val
                    dom_divs = divs
                    par_divs = divs
            else:
                divs = base_divisor
                dom_divs = base_divisor
                par_divs = base_divisor
                
            (fig, ax) = plt.subplots(figsize=(8, 6))
            ax.scatter(dominated_epw[heating_col] / dom_divs, dominated_epw[cooling_col] / dom_divs, c='#cccccc', alpha=0.3, s=15, zorder=1)
            if size_by and size_by in pareto_epw.columns:
                sizes = pareto_epw[size_by] * 300
            else:
                sizes = 80
            use_colormap = color_by and color_by in pareto_epw.columns and pd.api.types.is_numeric_dtype(pareto_epw[color_by])
            if use_colormap:
                vmin = df_epw[color_by].min()
                vmax = df_epw[color_by].max()
                norm = Normalize(vmin=vmin, vmax=vmax)
                sc = ax.scatter(pareto_epw[heating_col] / par_divs, pareto_epw[cooling_col] / par_divs, c=pareto_epw[color_by], cmap='RdYlGn', norm=norm, s=sizes, alpha=0.85, edgecolors='k', linewidths=0.4, zorder=3)
                cbar = fig.colorbar(sc, ax=ax, pad=0.02, shrink=0.85)
                cbar.set_label(color_by, fontsize=10)
            else:
                sc = ax.scatter(pareto_epw[heating_col] / par_divs, pareto_epw[cooling_col] / par_divs, c='#e63946', s=sizes, alpha=0.85, edgecolors='k', linewidths=0.4, zorder=3)
            pf_epw = pareto_epw.sort_values(heating_col)
            
            if normalize_per_m2 and isinstance(area_attr, dict) and 'idf' in pf_epw.columns:
                pf_divs = pf_epw['idf'].map(area_attr).fillna(1.0) * base_divisor
            else:
                pf_divs = divs
                
            ax.plot(pf_epw[heating_col] / pf_divs, pf_epw[cooling_col] / pf_divs, '--', color='grey', lw=0.8, zorder=2)
            legend_handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor='#cccccc', markersize=7, alpha=0.6, label='Dominated')]
            if use_colormap:
                if size_by and size_by in pareto_epw.columns:
                    size_col = pareto_epw[size_by]
                    for sv in [size_col.min(), size_col.median(), size_col.max()]:
                        ms = max(4, min(18, (sv * 300) ** 0.5 / 1.5))
                        legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='#888888', markeredgecolor='k', markersize=ms, label=f'{size_by} = {sv:.2f}'))
                legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='#888888', markeredgecolor='k', markersize=9, label='Pareto-optimal'))
            else:
                legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='#e63946', markeredgecolor='k', markersize=9, label='Pareto-optimal'))
            ax.legend(handles=legend_handles, fontsize=8, loc='upper right')
            ax.set_xlabel(f'Annual Heating Electricity ({unit_str})', fontsize=12)
            ax.set_ylabel(f'Annual Cooling Electricity ({unit_str})', fontsize=12)
            title_base = 'Pareto Front'
            if getattr(self, 'parameters_type', None):
                title_base += ' - ' + self.parameters_type.title()
            title_lines = [title_base + ' [' + epw_tag + ']']
            subtitle_parts = []
            if size_by:
                subtitle_parts.append('Dot size proportional to ' + size_by)
            if color_by:
                subtitle_parts.append('Colour = ' + color_by)
            if subtitle_parts:
                title_lines.append('  |  '.join(subtitle_parts))
            ax.set_title('\n'.join(title_lines), fontsize=10)
            plt.tight_layout()
            fname_suffix = epw_tag
            if color_by:
                fname_suffix += '_c_' + color_by
            if size_by:
                fname_suffix += '_s_' + size_by
            fname_pareto = os.path.join(out_dir, 'plot_pareto_front_' + fname_suffix + '.png')
            plt.savefig(fname_pareto, dpi=300, bbox_inches='tight')
            plt.close()
            print('  Pareto front plot saved: ' + fname_pareto)

    def plot_parallel_coordinates(self, out_dir: str='.'):
        """
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('This method requires either a parametric or optimisation simulation to be run first.')

        Plots a multivariate parallel coordinates visualization of the parameter space.
        """
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('Parallel coordinates plot requires either a parametric or optimisation simulation to be run first.')
        import os
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        os.makedirs(out_dir, exist_ok=True)
        df = self.outputs_optimisation.copy()
        epw_labels = df['epw'].unique()
        param_cols = self.problem.names('inputs')
        df['pareto_str'] = df['pareto-optimal'].map({True: 'Pareto-optimal', False: 'Dominated'})
        for epw_label in epw_labels:
            epw_tag = epw_label.replace('\\', '/').split('/')[-1].replace('.epw', '').replace(' ', '_')
            df_epw = df[df['epw'] == epw_label].copy()
            df_pc_norm = df_epw[param_cols + ['pareto_str']].copy()
            for c in param_cols:
                (lo, hi) = (df_pc_norm[c].min(), df_pc_norm[c].max())
                if hi > lo:
                    df_pc_norm[c] = (df_pc_norm[c] - lo) / (hi - lo)
                else:
                    df_pc_norm[c] = 0.5
            (fig, ax) = plt.subplots(figsize=(12, 5))
            colour_map = {'Pareto-optimal': '#e63946', 'Dominated': '#adb5bd'}
            for (_, row) in df_pc_norm.iterrows():
                colour = colour_map[row['pareto_str']]
                alpha = 0.7 if row['pareto_str'] == 'Pareto-optimal' else 0.12
                lw = 1.2 if row['pareto_str'] == 'Pareto-optimal' else 0.5
                ax.plot(range(len(param_cols)), row[param_cols].values, color=colour, alpha=alpha, lw=lw)
            ax.set_xticks(range(len(param_cols)))
            ax.set_xticklabels([c.replace('_', '\n') for c in param_cols], fontsize=9)
            ax.set_ylabel('Normalised parameter value', fontsize=10)
            ax.set_title(f'Parallel Coordinates [{epw_tag}]\n(Red = Pareto-optimal | Grey = Dominated)', fontsize=11)
            legend_elements = [Line2D([0], [0], color='#e63946', lw=1.5, label='Pareto-optimal'), Line2D([0], [0], color='#adb5bd', lw=1.0, label='Dominated')]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
            plt.tight_layout()
            fname_parallel = os.path.join(out_dir, f'plot_parallel_coordinates_{epw_tag}.png')
            plt.savefig(fname_parallel, dpi=300, bbox_inches='tight')
            plt.close()
            print(f'  Parallel coordinates plot saved: {fname_parallel}')

    def plot_pairwise_scatter_matrix(self, out_dir: str='.', normalize_per_m2: bool=False):
        """
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('This method requires either a parametric or optimisation simulation to be run first.')

        Plots a pairwise scatter matrix using seaborn.PairGrid for Pareto-optimal solutions.
        """
        if getattr(self, 'last_run_type', None) not in ['parametric', 'optimisation']:
            raise ValueError('Pairwise scatter matrix requires either a parametric or optimisation simulation to be run first.')
        import os
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        from matplotlib.colors import Normalize
        if getattr(self, 'outputs_normalized', False):
            if normalize_per_m2:
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect.')
            normalize_per_m2 = False
            unit_str = 'kWh/m2'
            base_divisor = 1.0
        else:
            unit_str = 'kWh/m2' if normalize_per_m2 else 'kWh'
            base_divisor = 3600000.0
            if normalize_per_m2:
                area_attr = getattr(self, 'building_floor_area', None)
                if not area_attr:
                    print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                    unit_str = 'kWh'
                    normalize_per_m2 = False
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for PairGrid. Please pip install seaborn.')
            return
        os.makedirs(out_dir, exist_ok=True)
        df = self.outputs_optimisation.copy()
        heating_col = next((c for c in df.columns if 'Heating:Electricity' in c), None)
        cooling_col = next((c for c in df.columns if 'Cooling:Electricity' in c), None)
        if heating_col and cooling_col:
            if normalize_per_m2:
                if isinstance(area_attr, dict) and 'idf' in df.columns:
                    divs = df['idf'].map(area_attr).fillna(1.0) * base_divisor
                else:
                    area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    divs = base_divisor * area_val
            else:
                divs = base_divisor
            df['Total_Energy'] = (df[heating_col] + df[cooling_col]) / divs
        else:
            df['Total_Energy'] = 0
        epw_labels = df['epw'].unique()
        param_cols = self.problem.names('inputs')
        for epw_label in epw_labels:
            epw_tag = epw_label.replace('\\', '/').split('/')[-1].replace('.epw', '').replace(' ', '_')
            pareto_epw = df[(df['epw'] == epw_label) & df['pareto-optimal']].copy()
            if len(pareto_epw) < 2:
                print(f'  [!] Skipping PairGrid for {epw_tag}: fewer than 2 Pareto-optimal points.')
                continue
            norm_e = Normalize(pareto_epw['Total_Energy'].min(), pareto_epw['Total_Energy'].max())
            try:
                cmap_e = plt.colormaps['coolwarm']
            except AttributeError:
                cmap_e = cm.get_cmap('coolwarm')

            def _pairplot_scatter(x, y, **kwargs):
                ax_pg = plt.gca()
                colours = cmap_e(norm_e(pareto_epw.loc[x.index, 'Total_Energy'].values))
                ax_pg.scatter(x.values, y.values, c=colours, s=30, alpha=0.8, edgecolors='k', linewidths=0.2)

            def _pairplot_hist(x, **kwargs):
                plt.gca().hist(x, bins=10, color='#457b9d', alpha=0.7, edgecolor='white')
            g = sns.PairGrid(pareto_epw[param_cols + ['Total_Energy']], vars=param_cols)
            g.map_diag(_pairplot_hist)
            g.map_offdiag(_pairplot_scatter)
            sm = cm.ScalarMappable(cmap='coolwarm', norm=norm_e)
            sm.set_array([])
            cbar = g.figure.colorbar(sm, ax=g.axes, shrink=0.6, pad=0.02)
            cbar.set_label(f'Total HVAC Energy ({unit_str})', fontsize=9)
            g.figure.suptitle(f'Pairwise Parameter Space – Pareto-Optimal Solutions [{epw_tag}]', y=1.01, fontsize=11)
            fname_pair = os.path.join(out_dir, f'plot_pairwise_scatter_matrix_{epw_tag}.png')
            g.figure.savefig(fname_pair, dpi=300, bbox_inches='tight')
            plt.close('all')
            print(f'  Pairwise scatter matrix saved: {fname_pair}')

    def plot_categorical_boxplots(self, df_source: str='parametric', y_vars: list=None, col: str=None, row: str=None, hue: str=None, highlight_dict: dict=None, out_dir: str='.', normalize_per_m2: bool=False, sharey: bool=True, show_points: bool=True, height: float=4, aspect: float=1.2, figsize: tuple=None):
        """
        Generates categorical boxplots from simulation results, automatically melting
        specified energy columns (or detecting Heating/Cooling by default) so they share
        the Y-axis and appear side-by-side on the X-axis for each FacetGrid subplot.

        :param df_source: 'parametric' (uses outputs_param_simulation) or 'optimisation'
            (uses outputs_optimisation).
        :param y_vars: List of column names to plot on the Y-axis. If None, it attempts
            to find 'Heating' and 'Cooling' electricity columns.
        :param col: Category mapping variable to use for grid columns.
        :param row: Category mapping variable to use for grid rows.
        :param hue: Category mapping variable to use for color coding.
        :param highlight_dict: Dictionary of category columns and values to highlight 
            as overlaid points (e.g., {'weather_type': ['tmy', 'met']}).
        :param out_dir: Output directory for saving the plot.
        :param normalize_per_m2: If True, values will be divided by building floor area.
        :param sharey: If True, all subplots will share the same Y-axis scale.
        :param show_points: If True, overlays all underlying simulation data points on the boxplots.
        :param height: Height (in inches) of each individual facet subplot. Default 4.
        :param aspect: Width/height ratio of each facet. The subplot width is
            height * aspect. Default 1.2.
        :param figsize: Optional (width, height) tuple (in inches) to override the
            figure size calculated from height and aspect. Applied after the
            FacetGrid is built, so it always takes precedence.
            Example: figsize=(20, 8).
        """
        import os
        import pandas as pd
        import matplotlib.pyplot as plt
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_categorical_boxplots. Please pip install seaborn.')
            return

        if df_source == 'parametric':
            df = getattr(self, 'outputs_param_simulation', None)
        elif df_source == 'optimisation':
            df = getattr(self, 'outputs_optimisation', None)
        else:
            raise ValueError("df_source must be 'parametric' or 'optimisation'")

        if df is None or df.empty:
            raise ValueError(f"No results found for {df_source}. Please run the simulation first.")

        df = df.copy()
        
        if getattr(self, 'outputs_normalized', False):
            if normalize_per_m2:
                print('[!] Warning: outputs_normalized is already True. The argument normalize_per_m2=True will have no effect.')
            normalize_per_m2 = False
            unit_str = 'kWh/m2'
            base_divisor = 1.0
        else:
            unit_str = 'kWh/m2' if normalize_per_m2 else 'kWh'
            base_divisor = 3600000.0
            if normalize_per_m2:
                area_attr = getattr(self, 'building_floor_area', None)
                if not area_attr:
                    print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                    unit_str = 'kWh'
                    normalize_per_m2 = False

        if y_vars is None:
            heating_col = next((c for c in df.columns if 'Heating' in c), None)
            cooling_col = next((c for c in df.columns if 'Cooling' in c), None)
            y_vars = []
            if heating_col: y_vars.append(heating_col)
            if cooling_col: y_vars.append(cooling_col)
            if not y_vars:
                print('[!] Heating or Cooling columns not found and y_vars not provided.')
                return

        # Apply Normalization
        for y_var in y_vars:
            if normalize_per_m2:
                if isinstance(area_attr, dict) and 'idf' in df.columns:
                    divs = df['idf'].map(area_attr).fillna(1.0) * base_divisor
                else:
                    area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    divs = base_divisor * area_val
                df[y_var] = df[y_var] / divs
            else:
                df[y_var] = df[y_var] / base_divisor

        id_vars = [v for v in [col, row, hue, 'idf', 'epw'] if v and v in df.columns]
        if highlight_dict:
            for k in highlight_dict.keys():
                if k in df.columns and k not in id_vars:
                    id_vars.append(k)
                    
        df_melt = df.melt(
            id_vars=id_vars,
            value_vars=y_vars,
            var_name='Energy_Type',
            value_name='Energy_Value'
        )

        # Clean variable names for the legend
        df_melt['Energy_Type'] = df_melt['Energy_Type'].apply(lambda x: 'Heating' if 'Heating' in x else ('Cooling' if 'Cooling' in x else x))

        os.makedirs(out_dir, exist_ok=True)

        order = df_melt['Energy_Type'].unique().tolist()
        hue_order = sorted(df_melt[hue].dropna().unique()) if hue else None

        g = sns.catplot(
            data=df_melt,
            x='Energy_Type',
            y='Energy_Value',
            col=col,
            row=row,
            hue=hue,
            kind='box',
            order=order,
            hue_order=hue_order,
            sharex=True,
            sharey=sharey,
            palette='Set2',
            height=height,
            aspect=aspect
        )

        # Apply explicit figsize override if requested
        if figsize is not None:
            g.fig.set_size_inches(figsize)
        
        # Overlay all points if requested
        if show_points:
            def plot_all_points(data, **kwargs):
                if data.empty:
                    return
                sns.stripplot(
                    data=data,
                    x='Energy_Type',
                    y='Energy_Value',
                    hue=hue,
                    order=order,
                    hue_order=hue_order,
                    dodge=True if hue else False,
                    palette=['#555555']*len(hue_order) if hue else None,
                    color='#555555' if not hue else None,
                    alpha=0.6,
                    jitter=True,
                    size=4,
                    ax=plt.gca(),
                    legend=False
                )
            g.map_dataframe(plot_all_points)
        
        # Overlay highlights if requested
        if highlight_dict:
            axes_dict = g.axes_dict
            markers = ['*', 'X', 'D', '^', 'v', 'p']
            legend_handles = []
            
            for k, v in highlight_dict.items():
                if k not in df_melt.columns:
                    print(f"[!] Highlight column '{k}' not found in dataframe.")
                    continue
                v_list = v if isinstance(v, list) else [v]
                
                for i, val in enumerate(v_list):
                    marker = markers[i % len(markers)]
                    df_val = df_melt[df_melt[k] == val]
                    if df_val.empty:
                        continue
                        
                    # Add to legend handles
                    from matplotlib.lines import Line2D
                    legend_handles.append(Line2D([0], [0], marker=marker, color='w', markerfacecolor='black', markersize=9, label=f"{k}: {val}"))
                    
                    for facet_key, ax in axes_dict.items():
                        mask = pd.Series(True, index=df_val.index)
                        if row and col:
                            # Seaborn uses a tuple (row_val, col_val) for row and col
                            mask &= (df_val[row] == facet_key[0]) & (df_val[col] == facet_key[1])
                        elif row:
                            mask &= (df_val[row] == facet_key)
                        elif col:
                            mask &= (df_val[col] == facet_key)
                            
                        df_facet = df_val[mask]
                        if not df_facet.empty:
                            sns.stripplot(
                                data=df_facet,
                                x='Energy_Type',
                                y='Energy_Value',
                                hue=hue,
                                order=order,
                                hue_order=hue_order,
                                dodge=True if hue else False,
                                marker=marker,
                                palette=['black']*len(hue_order) if hue else None,
                                color='black' if not hue else None,
                                size=8,
                                linewidth=0.5,
                                edgecolor='white',
                                ax=ax,
                                jitter=False,
                                legend=False
                            )
            
            # Merge highlight handles into the FacetGrid's figure-level legend
            if legend_handles and g.axes.size > 0:
                from matplotlib.patches import Patch
                existing_handles, existing_labels, legend_title = [], [], (hue or '')
                _fg_legend = getattr(g, '_legend', None)
                if _fg_legend is not None:
                    existing_handles = list(_fg_legend.legend_handles)
                    existing_labels = [t.get_text() for t in _fg_legend.get_texts()]
                    legend_title = _fg_legend.get_title().get_text()
                    # Remove the seaborn-placed legend before rebuilding it
                    _fg_legend.remove()
                    g._legend = None
                # Blank patch used as a visual section separator
                blank = Patch(visible=False, label='')
                divider = Patch(visible=False, label='― Highlights ―')
                combined_handles = existing_handles + [blank, divider] + legend_handles
                combined_labels = (
                    existing_labels
                    + ['', '― Highlights ―']
                    + [h.get_label() for h in legend_handles]
                )
                new_legend = g.fig.legend(
                    handles=combined_handles,
                    labels=combined_labels,
                    title=legend_title,
                    loc='center right',
                    bbox_to_anchor=(1.0, 0.5),
                    frameon=True,
                    fontsize='small',
                    title_fontsize='small',
                )
                # Bold the section-divider text
                for text in new_legend.get_texts():
                    if text.get_text().startswith('―'):
                        text.set_fontweight('bold')
                g._legend = new_legend

        g.set_axis_labels('Energy Type', f'Energy ({unit_str})')
        g.fig.subplots_adjust(top=0.9)
        g.fig.suptitle(f"Categorical Energy Boxplots ({df_source.capitalize()})", fontsize=14)

        fname_suffix = f"col_{col}" if col else ""
        fname_suffix += f"_row_{row}" if row else ""
        fname_suffix += f"_hue_{hue}" if hue else ""
        
        fname_plot = os.path.join(out_dir, f'plot_categorical_boxplots_{df_source}_{fname_suffix}.png')
        g.savefig(fname_plot, dpi=300, bbox_inches='tight')
        plt.close(g.fig)
        print(f'  Categorical boxplot saved: {fname_plot}')
        return g

    def plot_parametric_scatter(
            self,
            x: str,
            y: str,
            df_source: str='parametric',
            hue: str=None,
            style: str=None,
            size: str=None,
            col: str=None,
            row: str=None,
            add_trend: str=None,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            alpha: float=0.75,
            height: float=4,
            aspect: float=1.2,
            figsize: tuple=None,
    ):
        """
        Generates a scatter plot (optionally faceted) for parametric/optimisation outputs.

        :param x: Column name for the X axis.
        :param y: Column name for the Y axis.
        :param df_source: 'parametric' or 'optimisation'.
        :param hue: Optional grouping column for point colour.
        :param style: Optional grouping column for point marker.
        :param size: Optional grouping column for point size.
        :param col: Optional faceting column.
        :param row: Optional faceting row.
        :param add_trend: Optional trend line ('linear' or 'lowess').
        :param out_dir: Output directory for saving the figure.
        :param normalize_per_m2: Normalize energy-like axes to kWh/m2 (if possible).
        :param alpha: Point transparency.
        :param height: Height (inches) of each facet.
        :param aspect: Width/height ratio of each facet.
        :param figsize: Optional full-figure size override (width, height).
        :return: seaborn FacetGrid.
        """
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_parametric_scatter. Please pip install seaborn.')
            return

        allowed_trends = {None, 'linear', 'lowess'}
        if add_trend not in allowed_trends:
            raise ValueError("add_trend must be one of: None, 'linear', 'lowess'")

        df = self._get_plot_source_df(df_source=df_source)
        required_cols = [x, y]
        optional_cols = [hue, style, size, col, row]

        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(f'Missing required columns for scatter plot: {missing}')

        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for scatter plot: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x, y], normalize_per_m2=normalize_per_m2)

        os.makedirs(out_dir, exist_ok=True)
        g = sns.relplot(
            data=df,
            x=x,
            y=y,
            hue=hue,
            style=style,
            size=size,
            col=col,
            row=row,
            kind='scatter',
            alpha=alpha,
            height=height,
            aspect=aspect,
        )

        if figsize is not None:
            g.fig.set_size_inches(figsize)

        if add_trend is not None and pd.api.types.is_numeric_dtype(df[x]) and pd.api.types.is_numeric_dtype(df[y]):
            if g.axes_dict:
                for facet_key, ax in g.axes_dict.items():
                    mask = pd.Series(True, index=df.index)
                    if row and col:
                        mask &= (df[row] == facet_key[0]) & (df[col] == facet_key[1])
                    elif row:
                        mask &= (df[row] == facet_key)
                    elif col:
                        mask &= (df[col] == facet_key)
                    df_facet = df[mask]
                    if len(df_facet) < 2:
                        continue
                    sns.regplot(
                        data=df_facet,
                        x=x,
                        y=y,
                        scatter=False,
                        lowess=(add_trend == 'lowess'),
                        ax=ax,
                        line_kws={'color': '#111111', 'lw': 1.2, 'alpha': 0.9},
                    )
            else:
                sns.regplot(
                    data=df,
                    x=x,
                    y=y,
                    scatter=False,
                    lowess=(add_trend == 'lowess'),
                    ax=g.ax,
                    line_kws={'color': '#111111', 'lw': 1.2, 'alpha': 0.9},
                )

        x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
        y_label = f"{y} ({unit_map[y]})" if unit_map.get(y) else y
        g.set_axis_labels(x_label, y_label)

        title = f"Scatter Plot ({df_source.capitalize()})"
        if add_trend:
            title += f" | Trend: {add_trend}"
        g.fig.subplots_adjust(top=0.9)
        g.fig.suptitle(title, fontsize=13)

        fname = os.path.join(
            out_dir,
            f"plot_parametric_scatter_{df_source}_{self._safe_plot_token(x)}_vs_{self._safe_plot_token(y)}.png",
        )
        g.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close(g.fig)
        print(f'  Parametric scatter plot saved: {fname}')
        return g

    def plot_parametric_lines(
            self,
            x: str,
            y_vars: list=None,
            df_source: str='parametric',
            hue: str='epw',
            style: str=None,
            units: str=None,
            col: str='idf',
            row: str=None,
            estimator: str='mean',
            errorbar=('ci', 95),
            markers: bool=True,
            dashes: bool=False,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            height: float=4,
            aspect: float=1.2,
            figsize: tuple=None,
            sort_x: bool=True,
    ) -> dict:
        """
        Generates one or more line plots to inspect trends against a swept parameter.

        :param x: Column name for the X axis.
        :param y_vars: List of output columns to plot. If None, Heating/Cooling are auto-detected.
        :param df_source: 'parametric' or 'optimisation'.
        :param hue: Optional grouping column for colour.
        :param style: Optional grouping column for line style.
        :param units: Optional column used as line units (useful when estimator=None).
        :param col: Optional faceting column.
        :param row: Optional faceting row.
        :param estimator: Aggregation estimator (e.g., 'mean', 'median') or None for raw traces.
        :param errorbar: Seaborn errorbar specification. Falls back to legacy ci= when needed.
        :param markers: Show markers at sampled X locations.
        :param dashes: Use dashed lines for style groups.
        :param out_dir: Output directory for saving figures.
        :param normalize_per_m2: Normalize energy-like Y columns to kWh/m2 (if possible).
        :param height: Height (inches) of each facet.
        :param aspect: Width/height ratio of each facet.
        :param figsize: Optional full-figure size override (width, height).
        :param sort_x: Sort X values before plotting lines.
        :return: dict mapping each y_var to its saved PNG file path.
        """
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_parametric_lines. Please pip install seaborn.')
            return {}

        df = self._get_plot_source_df(df_source=df_source)
        if x not in df.columns:
            raise KeyError(f"Column '{x}' not found in dataframe.")

        if y_vars is None:
            heating_col = next((c for c in df.columns if 'Heating' in c), None)
            cooling_col = next((c for c in df.columns if 'Cooling' in c), None)
            y_vars = [c for c in [heating_col, cooling_col] if c is not None]
            if not y_vars:
                raise ValueError('Heating/Cooling columns not found and y_vars was not provided.')

        missing_y = [y_var for y_var in y_vars if y_var not in df.columns]
        if missing_y:
            raise KeyError(f'Missing y_vars columns: {missing_y}')

        optional_cols = [hue, style, units, col, row]
        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for line plot: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x] + list(y_vars), normalize_per_m2=normalize_per_m2)
        os.makedirs(out_dir, exist_ok=True)

        saved = {}
        for y_var in y_vars:
            relplot_kwargs = {
                'data': df,
                'x': x,
                'y': y_var,
                'hue': hue,
                'style': style,
                'units': units,
                'col': col,
                'row': row,
                'kind': 'line',
                'estimator': estimator,
                'markers': markers,
                'dashes': dashes,
                'sort': sort_x,
                'height': height,
                'aspect': aspect,
            }

            if errorbar is not None:
                relplot_kwargs['errorbar'] = errorbar

            try:
                g = sns.relplot(**relplot_kwargs)
            except TypeError as err:
                # Compatibility fallback for seaborn<0.12 where errorbar= is unavailable.
                if 'errorbar' not in str(err):
                    raise
                relplot_kwargs.pop('errorbar', None)
                if errorbar is not None:
                    if isinstance(errorbar, tuple) and len(errorbar) == 2 and str(errorbar[0]).lower() == 'ci':
                        relplot_kwargs['ci'] = errorbar[1]
                    elif isinstance(errorbar, (int, float)):
                        relplot_kwargs['ci'] = errorbar
                g = sns.relplot(**relplot_kwargs)

            if figsize is not None:
                g.fig.set_size_inches(figsize)

            x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
            y_label = f"{y_var} ({unit_map[y_var]})" if unit_map.get(y_var) else y_var
            g.set_axis_labels(x_label, y_label)
            g.fig.subplots_adjust(top=0.9)
            g.fig.suptitle(f"Parametric Line Plot ({df_source.capitalize()}) - {y_var}", fontsize=13)

            fname = os.path.join(
                out_dir,
                f"plot_parametric_lines_{df_source}_{self._safe_plot_token(y_var)}_by_{self._safe_plot_token(x)}.png",
            )
            g.savefig(fname, dpi=300, bbox_inches='tight')
            plt.close(g.fig)
            print(f'  Parametric line plot saved: {fname}')
            saved[y_var] = fname

        return saved

    def plot_parametric_heatmap(
            self,
            x: str,
            y: str,
            z: str,
            df_source: str='parametric',
            aggfunc: str='mean',
            col: str=None,
            row: str=None,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            cmap: str='viridis',
            annot: bool=False,
            fmt: str='.2f',
            figsize: tuple=None,
            vmin: float=None,
            vmax: float=None,
    ) -> str:
        """
        Creates one or more heatmaps from (x, y) parameter combinations and z values.
        """
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_parametric_heatmap. Please pip install seaborn.')
            return ''

        df = self._get_plot_source_df(df_source=df_source)
        required_cols = [x, y, z]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(f'Missing required columns for heatmap: {missing}')

        optional_cols = [col, row]
        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for heatmap: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x, y, z], normalize_per_m2=normalize_per_m2)
        os.makedirs(out_dir, exist_ok=True)

        row_values = list(pd.unique(df[row].dropna())) if row else [None]
        col_values = list(pd.unique(df[col].dropna())) if col else [None]
        if len(row_values) == 0:
            row_values = [None]
        if len(col_values) == 0:
            col_values = [None]

        n_rows = len(row_values)
        n_cols = len(col_values)
        if figsize is None:
            figsize = (4.8 * n_cols, 4.2 * n_rows)

        (fig, axes) = plt.subplots(n_rows, n_cols, figsize=figsize, squeeze=False)
        for (i, row_val) in enumerate(row_values):
            for (j, col_val) in enumerate(col_values):
                ax = axes[i][j]
                mask = pd.Series(True, index=df.index)
                if row:
                    mask &= df[row] == row_val
                if col:
                    mask &= df[col] == col_val

                df_facet = df.loc[mask, [x, y, z]].dropna()
                if df_facet.empty:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_axis_off()
                    continue

                pivot_df = pd.pivot_table(df_facet, index=y, columns=x, values=z, aggfunc=aggfunc)
                if pivot_df.empty:
                    ax.text(0.5, 0.5, 'No pivot data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_axis_off()
                    continue

                pivot_df = pivot_df.sort_index(axis=0).sort_index(axis=1)
                sns.heatmap(
                    pivot_df,
                    ax=ax,
                    cmap=cmap,
                    annot=annot,
                    fmt=fmt,
                    vmin=vmin,
                    vmax=vmax,
                    cbar=True,
                )

                x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
                y_label = f"{y} ({unit_map[y]})" if unit_map.get(y) else y
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)

                title_parts = []
                if row:
                    title_parts.append(f'{row}={row_val}')
                if col:
                    title_parts.append(f'{col}={col_val}')
                if title_parts:
                    ax.set_title(' | '.join(title_parts), fontsize=10)

        z_label = f"{z} ({unit_map[z]})" if unit_map.get(z) else z
        fig.suptitle(f'Parametric Heatmap ({df_source.capitalize()}) - {z_label}', fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.96))

        fname = os.path.join(
            out_dir,
            f'plot_parametric_heatmap_{df_source}_{self._safe_plot_token(z)}_by_{self._safe_plot_token(x)}_{self._safe_plot_token(y)}.png',
        )
        fig.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f'  Parametric heatmap saved: {fname}')
        return fname

    def plot_parametric_contour(
            self,
            x: str,
            y: str,
            z: str,
            df_source: str='parametric',
            col: str=None,
            row: str=None,
            levels: int=12,
            filled: bool=True,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            cmap: str='viridis',
            scatter_overlay: bool=True,
            figsize: tuple=None,
    ) -> str:
        """
        Creates contour (or filled contour) plots from numeric x, y, z columns.
        """
        df = self._get_plot_source_df(df_source=df_source)
        required_cols = [x, y, z]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(f'Missing required columns for contour plot: {missing}')

        for c in required_cols:
            if not pd.api.types.is_numeric_dtype(df[c]):
                raise TypeError(f"Column '{c}' must be numeric for contour plotting.")

        optional_cols = [col, row]
        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for contour plot: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x, y, z], normalize_per_m2=normalize_per_m2)
        os.makedirs(out_dir, exist_ok=True)

        row_values = list(pd.unique(df[row].dropna())) if row else [None]
        col_values = list(pd.unique(df[col].dropna())) if col else [None]
        if len(row_values) == 0:
            row_values = [None]
        if len(col_values) == 0:
            col_values = [None]

        n_rows = len(row_values)
        n_cols = len(col_values)
        if figsize is None:
            figsize = (5.2 * n_cols, 4.6 * n_rows)

        (fig, axes) = plt.subplots(n_rows, n_cols, figsize=figsize, squeeze=False)
        for (i, row_val) in enumerate(row_values):
            for (j, col_val) in enumerate(col_values):
                ax = axes[i][j]
                mask = pd.Series(True, index=df.index)
                if row:
                    mask &= df[row] == row_val
                if col:
                    mask &= df[col] == col_val
                df_facet = df.loc[mask, [x, y, z]].dropna()

                if df_facet.empty:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_axis_off()
                    continue

                if len(df_facet) < 3 or df_facet[x].nunique() < 2 or df_facet[y].nunique() < 2:
                    sc = ax.scatter(df_facet[x], df_facet[y], c=df_facet[z], cmap=cmap, s=35, alpha=0.85)
                    fig.colorbar(sc, ax=ax, pad=0.02, shrink=0.85)
                    ax.set_title('Fallback scatter (insufficient points)', fontsize=9)
                else:
                    try:
                        if filled:
                            contour = ax.tricontourf(df_facet[x], df_facet[y], df_facet[z], levels=levels, cmap=cmap)
                        else:
                            contour = ax.tricontour(df_facet[x], df_facet[y], df_facet[z], levels=levels, cmap=cmap)
                        fig.colorbar(contour, ax=ax, pad=0.02, shrink=0.85)
                        if scatter_overlay:
                            ax.scatter(df_facet[x], df_facet[y], c='#111111', s=14, alpha=0.5)
                    except Exception:
                        sc = ax.scatter(df_facet[x], df_facet[y], c=df_facet[z], cmap=cmap, s=35, alpha=0.85)
                        fig.colorbar(sc, ax=ax, pad=0.02, shrink=0.85)
                        ax.set_title('Fallback scatter', fontsize=9)

                x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
                y_label = f"{y} ({unit_map[y]})" if unit_map.get(y) else y
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)

                facet_title_parts = []
                if row:
                    facet_title_parts.append(f'{row}={row_val}')
                if col:
                    facet_title_parts.append(f'{col}={col_val}')
                if facet_title_parts:
                    base_title = ax.get_title()
                    prefix = ' | '.join(facet_title_parts)
                    ax.set_title(f'{prefix}\n{base_title}' if base_title else prefix, fontsize=9)

        z_label = f"{z} ({unit_map[z]})" if unit_map.get(z) else z
        fig.suptitle(f'Parametric Contour ({df_source.capitalize()}) - {z_label}', fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.96))

        fname = os.path.join(
            out_dir,
            f'plot_parametric_contour_{df_source}_{self._safe_plot_token(z)}_by_{self._safe_plot_token(x)}_{self._safe_plot_token(y)}.png',
        )
        fig.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f'  Parametric contour plot saved: {fname}')
        return fname

    def plot_parametric_distributions(
            self,
            x: str,
            y_vars: list=None,
            kind: str='violin',
            df_source: str='parametric',
            hue: str=None,
            col: str=None,
            row: str=None,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            inner: str='box',
            cut: float=0,
            sharey: bool=True,
            show_points: bool=False,
            height: float=4,
            aspect: float=1.2,
            figsize: tuple=None,
    ) -> dict:
        """
        Creates categorical distribution plots (violin, boxen, or box) for one or more outputs.
        """
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_parametric_distributions. Please pip install seaborn.')
            return {}

        allowed_kinds = {'violin', 'boxen', 'box'}
        if kind not in allowed_kinds:
            raise ValueError(f"kind must be one of {sorted(allowed_kinds)}")

        df = self._get_plot_source_df(df_source=df_source)
        if x not in df.columns:
            raise KeyError(f"Column '{x}' not found in dataframe.")

        if y_vars is None:
            heating_col = next((c for c in df.columns if 'Heating' in c), None)
            cooling_col = next((c for c in df.columns if 'Cooling' in c), None)
            y_vars = [c for c in [heating_col, cooling_col] if c is not None]
            if not y_vars:
                raise ValueError('Heating/Cooling columns not found and y_vars was not provided.')

        missing_y = [y_var for y_var in y_vars if y_var not in df.columns]
        if missing_y:
            raise KeyError(f'Missing y_vars columns: {missing_y}')

        optional_cols = [hue, col, row]
        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for distribution plot: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x] + list(y_vars), normalize_per_m2=normalize_per_m2)
        os.makedirs(out_dir, exist_ok=True)

        saved = {}
        for y_var in y_vars:
            catplot_kwargs = {
                'data': df,
                'x': x,
                'y': y_var,
                'hue': hue,
                'col': col,
                'row': row,
                'kind': kind,
                'sharey': sharey,
                'height': height,
                'aspect': aspect,
            }
            if kind == 'violin':
                catplot_kwargs['inner'] = inner
                catplot_kwargs['cut'] = cut

            g = sns.catplot(**catplot_kwargs)
            if figsize is not None:
                g.fig.set_size_inches(figsize)

            if show_points:
                g.map_dataframe(
                    sns.stripplot,
                    x=x,
                    y=y_var,
                    hue=hue,
                    dodge=True if hue else False,
                    alpha=0.45,
                    jitter=True,
                    size=3,
                    color='#4d4d4d' if hue is None else None,
                )

            x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
            y_label = f"{y_var} ({unit_map[y_var]})" if unit_map.get(y_var) else y_var
            g.set_axis_labels(x_label, y_label)
            g.fig.subplots_adjust(top=0.9)
            g.fig.suptitle(f'Parametric {kind.title()} Plot ({df_source.capitalize()}) - {y_var}', fontsize=13)

            fname = os.path.join(
                out_dir,
                f'plot_parametric_{kind}_{df_source}_{self._safe_plot_token(y_var)}_by_{self._safe_plot_token(x)}.png',
            )
            g.savefig(fname, dpi=300, bbox_inches='tight')
            plt.close(g.fig)
            print(f'  Parametric {kind} plot saved: {fname}')
            saved[y_var] = fname

        return saved

    def plot_parametric_ecdf(
            self,
            x: str,
            df_source: str='parametric',
            hue: str=None,
            col: str=None,
            row: str=None,
            complementary: bool=False,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            height: float=4,
            aspect: float=1.2,
            figsize: tuple=None,
    ) -> str:
        """
        Creates an ECDF plot to compare cumulative distributions across scenarios.
        """
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_parametric_ecdf. Please pip install seaborn.')
            return ''

        df = self._get_plot_source_df(df_source=df_source)
        if x not in df.columns:
            raise KeyError(f"Column '{x}' not found in dataframe.")
        if not pd.api.types.is_numeric_dtype(df[x]):
            raise TypeError(f"Column '{x}' must be numeric for ECDF plotting.")

        optional_cols = [hue, col, row]
        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for ECDF plot: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x], normalize_per_m2=normalize_per_m2)
        os.makedirs(out_dir, exist_ok=True)

        displot_kwargs = {
            'data': df,
            'x': x,
            'hue': hue,
            'col': col,
            'row': row,
            'kind': 'ecdf',
            'height': height,
            'aspect': aspect,
        }

        if complementary:
            displot_kwargs['complementary'] = True

        try:
            g = sns.displot(**displot_kwargs)
        except TypeError:
            # Compatibility fallback for older seaborn versions.
            displot_kwargs.pop('complementary', None)
            g = sns.displot(**displot_kwargs)

        if figsize is not None:
            g.fig.set_size_inches(figsize)

        x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
        y_label = '1 - F(x)' if complementary else 'F(x)'
        g.set_axis_labels(x_label, y_label)
        g.fig.subplots_adjust(top=0.9)
        g.fig.suptitle(f'Parametric ECDF ({df_source.capitalize()}) - {x_label}', fontsize=13)

        fname = os.path.join(
            out_dir,
            f'plot_parametric_ecdf_{df_source}_{self._safe_plot_token(x)}.png',
        )
        g.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close(g.fig)
        print(f'  Parametric ECDF plot saved: {fname}')
        return fname

    def plot_parametric_density_2d(
            self,
            x: str,
            y: str,
            kind: str='hexbin',
            df_source: str='parametric',
            hue: str=None,
            col: str=None,
            row: str=None,
            out_dir: str='.',
            normalize_per_m2: bool=False,
            cmap: str='viridis',
            gridsize: int=28,
            mincnt: int=1,
            levels: int=12,
            fill: bool=True,
            alpha: float=0.85,
            scatter_overlay: bool=False,
            figsize: tuple=None,
    ) -> str:
        """
        Creates 2D density visualizations using either hexbin or KDE.
        """
        try:
            import seaborn as sns
        except ImportError:
            print('[!] Seaborn is required for plot_parametric_density_2d. Please pip install seaborn.')
            return ''

        allowed_kinds = {'hexbin', 'kde'}
        if kind not in allowed_kinds:
            raise ValueError(f"kind must be one of {sorted(allowed_kinds)}")

        df = self._get_plot_source_df(df_source=df_source)
        required_cols = [x, y]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(f'Missing required columns for 2D density plot: {missing}')

        for c in required_cols:
            if not pd.api.types.is_numeric_dtype(df[c]):
                raise TypeError(f"Column '{c}' must be numeric for 2D density plotting.")

        optional_cols = [hue, col, row]
        missing_optional = [c for c in optional_cols if c and c not in df.columns]
        if missing_optional:
            raise KeyError(f'Missing optional columns for 2D density plot: {missing_optional}')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=[x, y], normalize_per_m2=normalize_per_m2)
        os.makedirs(out_dir, exist_ok=True)

        row_values = list(pd.unique(df[row].dropna())) if row else [None]
        col_values = list(pd.unique(df[col].dropna())) if col else [None]
        if len(row_values) == 0:
            row_values = [None]
        if len(col_values) == 0:
            col_values = [None]

        n_rows = len(row_values)
        n_cols = len(col_values)
        if figsize is None:
            figsize = (5.0 * n_cols, 4.5 * n_rows)

        (fig, axes) = plt.subplots(n_rows, n_cols, figsize=figsize, squeeze=False)
        for (i, row_val) in enumerate(row_values):
            for (j, col_val) in enumerate(col_values):
                ax = axes[i][j]
                mask = pd.Series(True, index=df.index)
                if row:
                    mask &= df[row] == row_val
                if col:
                    mask &= df[col] == col_val
                df_facet = df.loc[mask].copy()

                if df_facet.empty:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_axis_off()
                    continue

                if kind == 'hexbin':
                    hb = ax.hexbin(
                        df_facet[x],
                        df_facet[y],
                        gridsize=gridsize,
                        mincnt=mincnt,
                        cmap=cmap,
                        alpha=alpha,
                    )
                    fig.colorbar(hb, ax=ax, pad=0.02, shrink=0.85, label='Count')
                    if hue:
                        ax.text(0.01, 0.98, 'hue ignored for hexbin', transform=ax.transAxes, va='top', fontsize=8)
                else:
                    kde_kwargs = {
                        'data': df_facet,
                        'x': x,
                        'y': y,
                        'fill': fill,
                        'levels': levels,
                        'ax': ax,
                    }
                    if hue:
                        kde_kwargs['hue'] = hue
                        kde_kwargs['common_norm'] = False
                        kde_kwargs['alpha'] = alpha
                    else:
                        kde_kwargs['cmap'] = cmap
                    try:
                        sns.kdeplot(**kde_kwargs)
                    except Exception:
                        sc = ax.scatter(df_facet[x], df_facet[y], c='#1f77b4', s=22, alpha=0.75)
                        ax.set_title('Fallback scatter', fontsize=9)

                if scatter_overlay:
                    ax.scatter(df_facet[x], df_facet[y], c='#111111', s=10, alpha=0.35)

                x_label = f"{x} ({unit_map[x]})" if unit_map.get(x) else x
                y_label = f"{y} ({unit_map[y]})" if unit_map.get(y) else y
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)

                title_parts = []
                if row:
                    title_parts.append(f'{row}={row_val}')
                if col:
                    title_parts.append(f'{col}={col_val}')
                if title_parts:
                    ax.set_title(' | '.join(title_parts), fontsize=10)

        fig.suptitle(f'Parametric 2D Density ({kind}) - {df_source.capitalize()}', fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.96))

        fname = os.path.join(
            out_dir,
            f'plot_parametric_density2d_{kind}_{df_source}_{self._safe_plot_token(x)}_vs_{self._safe_plot_token(y)}.png',
        )
        fig.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f'  Parametric 2D density plot saved: {fname}')
        return fname

    def plot_parametric_radar(
            self,
            metrics: list=None,
            group_by: str='epw',
            df_source: str='parametric',
            aggfunc: str='mean',
            out_dir: str='.',
            normalize_per_m2: bool=False,
            figsize: tuple=(8, 8),
            fill_alpha: float=0.12,
    ) -> pd.DataFrame:
        """
        Creates a radar chart from aggregated groups and returns the aggregated values.
        """
        df = self._get_plot_source_df(df_source=df_source)
        if group_by not in df.columns:
            raise KeyError(f"Column '{group_by}' not found in dataframe.")

        if metrics is None:
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            energy_cols = [c for c in numeric_cols if self._is_energy_like_column(c)]
            if len(energy_cols) >= 3:
                metrics = energy_cols[:6]
            else:
                metrics = numeric_cols[:6]

        if not metrics:
            raise ValueError('No numeric metrics found for radar plotting.')

        missing_metrics = [m for m in metrics if m not in df.columns]
        if missing_metrics:
            raise KeyError(f'Missing metric columns for radar plot: {missing_metrics}')

        non_numeric = [m for m in metrics if not pd.api.types.is_numeric_dtype(df[m])]
        if non_numeric:
            raise TypeError(f'All metrics must be numeric for radar plotting: {non_numeric}')

        if len(metrics) < 3:
            raise ValueError('Radar plot requires at least 3 metrics.')

        (df, unit_map) = self._normalise_plot_columns(df=df, columns=list(metrics), normalize_per_m2=normalize_per_m2)
        agg_df = df.groupby(group_by, dropna=False)[metrics].agg(aggfunc).reset_index()
        if agg_df.empty:
            raise ValueError('No aggregated rows available for radar plotting.')

        normalised_df = agg_df.copy()
        for metric in metrics:
            col_min = normalised_df[metric].min()
            col_max = normalised_df[metric].max()
            if pd.isna(col_min) or pd.isna(col_max):
                normalised_df[metric] = 0.0
            elif col_max > col_min:
                normalised_df[metric] = (normalised_df[metric] - col_min) / (col_max - col_min)
            else:
                normalised_df[metric] = 0.5

        os.makedirs(out_dir, exist_ok=True)
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]

        (fig, ax) = plt.subplots(figsize=figsize, subplot_kw={'polar': True})
        for idx in range(len(normalised_df)):
            values = normalised_df.loc[idx, metrics].tolist()
            values += values[:1]
            label = str(agg_df[group_by].iloc[idx])
            ax.plot(angles, values, linewidth=1.8, label=label)
            ax.fill(angles, values, alpha=fill_alpha)

        metric_labels = [f"{m}\n({unit_map[m]})" if unit_map.get(m) else m for m in metrics]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['0.00', '0.25', '0.50', '0.75', '1.00'], fontsize=8)
        ax.set_title(
            f'Parametric Radar ({df_source.capitalize()})\nGroup: {group_by} | Agg: {aggfunc} | Normalized [0, 1]',
            fontsize=11,
            va='bottom',
        )
        ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.10), fontsize=8)

        fname = os.path.join(
            out_dir,
            f'plot_parametric_radar_{df_source}_group_{self._safe_plot_token(group_by)}.png',
        )
        fig.tight_layout()
        fig.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f'  Parametric radar plot saved: {fname}')
        return agg_df

