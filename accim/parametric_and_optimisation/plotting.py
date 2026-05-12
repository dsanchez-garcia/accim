import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import seaborn as sns

class PlottingMixin:

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