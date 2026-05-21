import os
import glob
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any, Dict, Literal, Optional, Union

class AnalysisMixin:

    @staticmethod
    def _normalise_floor_area_idf_name(name: str) -> str:
        import re

        normalised = os.path.basename(str(name)) if name is not None else ''
        if normalised.lower().endswith('.idf'):
            normalised = os.path.splitext(normalised)[0]
        normalised = re.sub(r'^accim_idf_backup_', '', normalised)
        normalised = re.sub(
            r'_(?:pre|post)_(?:setup|parametric|optimisation)_\d{8}_\d{6}$',
            '',
            normalised,
        )
        return normalised

    def _get_floor_area_idf_name(self, idf: Any, idx: int) -> str:
        if hasattr(self, '_get_idf_identifier'):
            raw_name = self._get_idf_identifier(idf, idx)
        else:
            raw_name = getattr(idf, 'idfname', f'unknown_idf_{idx}')
        idf_name = self._normalise_floor_area_idf_name(raw_name)
        return idf_name if idf_name else f'unknown_idf_{idx}'

    @staticmethod
    def _idf_objects(idf: Any, object_key: str) -> list:
        idfobjects = getattr(idf, 'idfobjects', {})
        for key in (object_key, object_key.upper(), object_key.lower()):
            try:
                return idfobjects[key]
            except (KeyError, TypeError):
                pass
        try:
            for key in idfobjects.keys():
                if str(key).upper() == object_key.upper():
                    return idfobjects[key]
        except AttributeError:
            pass
        return []

    @staticmethod
    def _idf_object_items(idf: Any):
        idfobjects = getattr(idf, 'idfobjects', {})
        try:
            keys = list(idfobjects.keys())
        except AttributeError:
            return
        for key in keys:
            try:
                yield str(key), idfobjects[key]
            except KeyError:
                continue

    @staticmethod
    def _first_existing_attr(obj: Any, attrs: list):
        for attr in attrs:
            value = getattr(obj, attr, None)
            if value not in (None, ''):
                return value
        return None

    @staticmethod
    def _iter_list_object_values(obj: Any, prefix: str):
        seen = set()
        fieldnames = getattr(obj, 'fieldnames', [])
        for field in fieldnames:
            if field == 'Name':
                continue
            if prefix.lower() in field.lower() and field.lower().endswith('name'):
                value = getattr(obj, field, None)
                if value not in (None, '') and value not in seen:
                    seen.add(value)
                    yield value
        for i in range(1, 500):
            for attr in (f'{prefix}_{i}_Name', f'{prefix}_Name_{i}'):
                value = getattr(obj, attr, None)
                if value not in (None, '') and value not in seen:
                    seen.add(value)
                    yield value

    def _get_zone_lookup(self, idf: Any) -> Dict[str, str]:
        return {
            z.Name.upper(): z.Name
            for z in self._idf_objects(idf, 'ZONE')
            if getattr(z, 'Name', None)
        }

    def _get_space_to_zone_lookup(self, idf: Any) -> Dict[str, str]:
        lookup = {}
        for space in self._idf_objects(idf, 'SPACE'):
            space_name = getattr(space, 'Name', None)
            zone_name = self._first_existing_attr(space, ['Zone_Name', 'Zone_or_ZoneList_Name'])
            if space_name and zone_name:
                lookup[space_name.upper()] = zone_name.upper()
        return lookup

    def _get_zonelist_lookup(self, idf: Any) -> Dict[str, set]:
        lookup = {}
        for zonelist in self._idf_objects(idf, 'ZONELIST'):
            name = getattr(zonelist, 'Name', None)
            if name:
                lookup[name.upper()] = {z.upper() for z in self._iter_list_object_values(zonelist, 'Zone')}
        return lookup

    def _get_spacelist_lookup(self, idf: Any) -> Dict[str, set]:
        space_to_zone = self._get_space_to_zone_lookup(idf)
        lookup = {}
        for spacelist in self._idf_objects(idf, 'SPACELIST'):
            name = getattr(spacelist, 'Name', None)
            if not name:
                continue
            zones = set()
            for space_name in self._iter_list_object_values(spacelist, 'Space'):
                zone_name = space_to_zone.get(space_name.upper())
                if zone_name:
                    zones.add(zone_name)
            lookup[name.upper()] = zones
        return lookup

    def _resolve_zone_like_names(self, idf: Any, names: list) -> set:
        zone_lookup = self._get_zone_lookup(idf)
        space_to_zone = self._get_space_to_zone_lookup(idf)
        zonelist_lookup = self._get_zonelist_lookup(idf)
        spacelist_lookup = self._get_spacelist_lookup(idf)
        resolved = set()

        for name in names:
            if name in (None, ''):
                continue
            upper_name = str(name).upper()
            if upper_name in zone_lookup:
                resolved.add(upper_name)
            if upper_name in space_to_zone:
                resolved.add(space_to_zone[upper_name])
            if upper_name in zonelist_lookup:
                resolved.update(zonelist_lookup[upper_name])
            if upper_name in spacelist_lookup:
                resolved.update(spacelist_lookup[upper_name])

        return resolved

    def _resolve_occupied_zone_names(self, idf: Any) -> set:
        targets = []
        people_target_fields = [
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name',
            'Zone_or_ZoneList_Name',
            'Zone_Name',
        ]
        for people in self._idf_objects(idf, 'PEOPLE'):
            target = self._first_existing_attr(people, people_target_fields)
            if target:
                targets.append(target)
        return self._resolve_zone_like_names(idf, targets)

    @staticmethod
    def _is_air_conditioning_object_class(class_name: str) -> bool:
        upper_class = class_name.upper()
        return (
            upper_class == 'ZONEHVAC:EQUIPMENTCONNECTIONS'
            or upper_class.startswith('ZONECONTROL:')
            or upper_class.startswith('ZONEHVAC:')
            or upper_class.startswith('HVACTEMPLATE:ZONE:')
            or upper_class.startswith('AIRTERMINAL:')
        )

    @staticmethod
    def _is_conditioned_zone_field(field_name: str) -> bool:
        field = field_name.lower()
        exact_zone_fields = {
            'zone_name',
            'zone_or_zonelist_name',
            'zone_or_zonelist_or_space_or_spacelist_name',
            'control_zone_name',
            'controlled_zone_name',
            'controlling_zone_name',
            'controlling_zone_or_thermostat_location',
        }
        if field in exact_zone_fields:
            return True
        if field.endswith('_zone_name'):
            skipped_terms = ('node', 'equipment', 'supply', 'return', 'inlet', 'outlet', 'exhaust')
            return not any(term in field for term in skipped_terms)
        return False

    def _iter_conditioned_zone_targets(self, obj: Any):
        explicit_fields = [
            'Zone_Name',
            'Zone_or_ZoneList_Name',
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name',
            'Control_Zone_Name',
            'Controlled_Zone_Name',
            'Controlling_Zone_Name',
            'Controlling_Zone_or_Thermostat_Location',
        ]
        seen = set()
        for field in explicit_fields:
            value = getattr(obj, field, None)
            if value not in (None, '') and value not in seen:
                seen.add(value)
                yield value
        for field in getattr(obj, 'fieldnames', []):
            if self._is_conditioned_zone_field(field):
                value = getattr(obj, field, None)
                if value not in (None, '') and value not in seen:
                    seen.add(value)
                    yield value

    def _resolve_air_conditioned_zone_names(self, idf: Any) -> set:
        targets = []
        for object_class, objects in self._idf_object_items(idf):
            if not self._is_air_conditioning_object_class(object_class):
                continue
            for obj in objects:
                targets.extend(self._iter_conditioned_zone_targets(obj))
        return self._resolve_zone_like_names(idf, targets)

    def _sum_floor_area(self, idf: Any, floors: list, zone_names: set = None) -> float:
        if zone_names is None:
            return sum((getattr(f, 'area', 0.0) for f in floors))

        space_to_zone = self._get_space_to_zone_lookup(idf)
        total_area = 0.0
        for floor in floors:
            floor_zone_name = getattr(floor, 'Zone_Name', '')
            floor_space_name = getattr(floor, 'Space_Name', '')
            floor_zone_upper = str(floor_zone_name).upper() if floor_zone_name else ''
            floor_space_upper = str(floor_space_name).upper() if floor_space_name else ''
            floor_space_zone = space_to_zone.get(floor_space_upper, '')
            if floor_zone_upper in zone_names or floor_space_zone in zone_names:
                total_area += getattr(floor, 'area', 0.0)
        return total_area

    def _resolve_floor_area_config(self, config: Any, idf_name: str, idf_names: list, argument_name: str):
        if not isinstance(config, dict):
            return config

        normalised_config = {}
        for key, value in config.items():
            normalised_key = self._normalise_floor_area_idf_name(key)
            if normalised_key in normalised_config:
                raise ValueError(f"Duplicate IDF key for {argument_name}: {key!r}")
            normalised_config[normalised_key] = value

        expected = set(idf_names)
        provided = set(normalised_config)
        missing = sorted(expected - provided)
        unknown = sorted(provided - expected)
        if missing or unknown:
            msg = []
            if missing:
                msg.append(f'missing IDF keys: {missing}')
            if unknown:
                msg.append(f'unknown IDF keys: {unknown}')
            raise ValueError(f"Invalid {argument_name} dictionary ({'; '.join(msg)}).")

        return normalised_config[idf_name]

    @staticmethod
    def _coerce_custom_floor_area(value: Union[str, float, int]) -> float:
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
        return float(value)

    def _coerce_zones_list(self, idf: Any, zones_list: Any, idf_name: str) -> set:
        if zones_list in (None, ''):
            raise ValueError("zones_list must be provided when mode='list'")
        if isinstance(zones_list, str):
            zone_values = [zones_list]
        else:
            zone_values = list(zones_list)
        if not zone_values:
            raise ValueError("zones_list must be provided when mode='list'")

        resolved = self._resolve_zone_like_names(idf, zone_values)
        unknown = [z for z in zone_values if not self._resolve_zone_like_names(idf, [z])]
        if unknown:
            raise ValueError(f"zones_list includes unknown zones/lists for IDF '{idf_name}': {unknown}")
        return resolved

    def _get_floor_area_buildings(self) -> list:
        buildings = getattr(self, 'buildings', [])
        if buildings:
            return buildings

        idf = getattr(self, 'building', None)
        if idf is not None:
            return [idf]

        backup_path = getattr(self, 'idf_backup_path', None)
        backup_list = backup_path if isinstance(backup_path, list) else ([backup_path] if backup_path else [])
        valid_backups = [p for p in backup_list if p and os.path.isfile(p)]
        if not valid_backups:
            raise AttributeError(
                "self.building is None and no valid idf_backup_path is available. "
                "Either provide mode='custom' with a custom_area value, or load the "
                "session with an IDF object (building= argument)."
            )
        from accim.utils import get_building
        loaded = [get_building(p) for p in valid_backups]
        self.buildings = loaded
        print(f'  [info] {len(loaded)} IDF(s) auto-loaded from backup paths.')
        return loaded

    def _set_and_return_building_floor_area(self, areas: Dict[str, float]):
        if len(areas) == 1:
            self.building_floor_area = list(areas.values())[0]
            print(f'  [info] Building floor area: {self.building_floor_area:.2f} m² (single IDF)')
            return self.building_floor_area

        self.building_floor_area = areas
        for idf_name, area in areas.items():
            print(f'  [info] Building floor area [{idf_name}]: {area:.2f} m²')
        return areas

    def set_building_floor_area(
            self,
            mode: Literal['all', 'occupied', 'air-conditioned', 'air-condicioned', 'custom', 'list']='all',
            zones_list: Union[list, Dict[str, list]]=None,
            custom_area: Union[str, float, Dict[str, Union[str, float]]]=None
    ) -> Union[float, Dict[str, float]]:
        """
        Calculates or sets the floor area to be used for normalizing energy results (kWh/m2).

        :param mode: 'all' to use all Floor surfaces in the IDF.
                     'occupied' to use Floor surfaces in zones that have a People object.
                     'air-conditioned' to use Floor surfaces in zones served or controlled by HVAC objects.
                     'custom' to use the value provided in `custom_area`.
                     'list' to use Floor surfaces only in the zones specified in `zones_list`.
        :param zones_list: List of zone names for mode 'list', or a dict mapping each IDF to its list.
        :param custom_area: Float/string value for mode 'custom', or a dict mapping each IDF to its value.
        :return: the calculated or assigned floor area.
        """
        normalised_mode = str(mode).lower().replace('_', '-').strip()
        if normalised_mode == 'air-condicioned':
            normalised_mode = 'air-conditioned'

        if normalised_mode == 'custom':
            if custom_area is None:
                raise ValueError("custom_area must be provided when mode='custom'")
            if not isinstance(custom_area, dict):
                self.building_floor_area = self._coerce_custom_floor_area(custom_area)
                return self.building_floor_area

        buildings = self._get_floor_area_buildings()
        idf_names = [self._get_floor_area_idf_name(idf, idx) for idx, idf in enumerate(buildings)]

        areas = {}
        for idx, idf in enumerate(buildings):
            idf_name = idf_names[idx]
            surfaces = self._idf_objects(idf, 'BuildingSurface:Detailed')
            floors = [s for s in surfaces if getattr(s, 'Surface_Type', '').lower() == 'floor']

            if normalised_mode == 'custom':
                custom_value = self._resolve_floor_area_config(custom_area, idf_name, idf_names, 'custom_area')
                total_area = self._coerce_custom_floor_area(custom_value)
            elif normalised_mode == 'all':
                total_area = self._sum_floor_area(idf, floors)
            elif normalised_mode == 'occupied':
                zone_names = self._resolve_occupied_zone_names(idf)
                total_area = self._sum_floor_area(idf, floors, zone_names)
            elif normalised_mode == 'air-conditioned':
                zone_names = self._resolve_air_conditioned_zone_names(idf)
                total_area = self._sum_floor_area(idf, floors, zone_names)
            elif normalised_mode == 'list':
                idf_zones_list = self._resolve_floor_area_config(zones_list, idf_name, idf_names, 'zones_list')
                zone_names = self._coerce_zones_list(idf, idf_zones_list, idf_name)
                total_area = self._sum_floor_area(idf, floors, zone_names)
            else:
                raise ValueError(f'Unknown mode: {mode}')

            areas[idf_name] = total_area

        return self._set_and_return_building_floor_area(areas)

    def normalize_outputs(self, df_types: list=None):
        """
        Normalizes energy-related columns in the specified dataframes by dividing them
        by the building floor area (and converting from Joules to kWh). 
        The results are saved in-place, and `self.outputs_normalized` is set to True.
        
        :param df_types: A list of strings specifying which dataframes to normalize.
            Options include: 'parametric', 'parametric_hourly', 'parametric_monthly',
            'optimisation', 'optimisation_hourly', 'optimisation_monthly'.
            If None, all available dataframes will be normalized.
        """
        import pandas as pd
        area_attr = getattr(self, 'building_floor_area', None)
        if not area_attr:
            raise ValueError('building_floor_area is not set. Please call set_building_floor_area() first.')
            
        if getattr(self, 'outputs_normalized', False):
            print('Outputs are already normalized. Skipping.')
            return

        if df_types is None:
            df_types = [
                'parametric', 'parametric_hourly', 'parametric_monthly',
                'optimisation', 'optimisation_hourly', 'optimisation_monthly'
            ]
            
        df_mapping = {
            'parametric': 'outputs_param_simulation',
            'parametric_hourly': 'outputs_param_simulation_hourly',
            'parametric_monthly': 'outputs_param_simulation_monthly',
            'optimisation': 'outputs_optimisation',
            'optimisation_hourly': 'outputs_optimisation_hourly',
            'optimisation_monthly': 'outputs_optimisation_monthly'
        }
        
        energy_keywords = ['Heating', 'Cooling', 'Energy', 'Electricity', 'Gas', 'Facility']
        
        for df_key in df_types:
            df_attr = df_mapping.get(df_key)
            if not df_attr:
                continue
                
            df = getattr(self, df_attr, None)
            if df is None or df.empty:
                continue
                
            # Find energy columns
            energy_cols = []
            for col in df.columns:
                if any(kw in col for kw in energy_keywords) and pd.api.types.is_numeric_dtype(df[col]):
                    energy_cols.append(col)
                    
            if not energy_cols:
                continue
                
            # Calculate divisors per row
            if isinstance(area_attr, dict) and 'idf' in df.columns:
                areas = df['idf'].map(area_attr)
                # Fill missing areas with 1 to avoid NaN if idf not found (though it shouldn't happen)
                areas = areas.fillna(1.0)
                divisors = 3600000.0 * areas
            else:
                area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                divisors = 3600000.0 * area_val
                
            # Apply normalisation
            # divisors is either a pd.Series (per-row, when area is a dict) or a float (uniform)
            if isinstance(divisors, float):
                for col in energy_cols:
                    df[col] = df[col] / divisors
            else:
                for col in energy_cols:
                    def safe_divide(val, div):
                        if isinstance(val, list):
                            return [v / div for v in val]
                        return val / div
                    df[col] = [safe_divide(val, div) for val, div in zip(df[col], divisors)]
                
            # Rename columns
            new_columns = {}
            for col in energy_cols:
                new_col = col
                if '[J]' in new_col:
                    new_col = new_col.replace('[J]', '[kWh/m2]')
                elif ' [J]' in new_col:
                    new_col = new_col.replace(' [J]', ' [kWh/m2]')
                else:
                    new_col = new_col + '_kWh/m2'
                new_columns[col] = new_col
                
            df.rename(columns=new_columns, inplace=True)
            print(f'  [info] Normalized {len(energy_cols)} energy columns in {df_attr}.')
            
        self.outputs_normalized = True

    def run_sensitivity_analysis(
            self,
            method: Literal['sobol', 'morris'] = 'sobol',
            calc_second_order: bool = True,
            num_resamples: int = 100,
            conf_level: float = 0.95,
            print_to_console: bool = False,
            parallel: bool = False,
            n_processors: Optional[int] = None,
            keep_resamples: bool = False,
            seed: Optional[int] = None,
            scaled: bool = False,
            num_levels: int = 4,
    ) -> dict:
        """
        Runs Sensitivity Analysis on the results of a parametric simulation using SALib.
        
        :param method: 'sobol' or 'morris'. Must match the sampling method used.
        :param calc_second_order: Sobol only. Calculate second-order sensitivities.
        :param num_resamples: number of resamples used for confidence intervals.
        :param conf_level: confidence interval level.
        :param print_to_console: print SALib results directly to console.
        :param parallel: Sobol only. Perform analysis in parallel.
        :param n_processors: Sobol only. Number of parallel processes when parallel=True.
        :param keep_resamples: Sobol only. Store intermediate resampling results.
        :param seed: random seed used by SALib.
        :param scaled: Morris only. Scale elementary effects by X/Y standard deviation.
        :param num_levels: Morris only. Number of grid levels used by sampling_morris.
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
                    res = sobol.analyze(
                        problem,
                        Y,
                        calc_second_order=calc_second_order,
                        num_resamples=num_resamples,
                        conf_level=conf_level,
                        print_to_console=print_to_console,
                        parallel=parallel,
                        n_processors=n_processors,
                        keep_resamples=keep_resamples,
                        seed=seed,
                    )
                except ValueError as e:
                    raise ValueError(f'Error analyzing with Sobol. Make sure you generated samples with sampling_sobol(). Details: {e}')
            elif method == 'morris':
                try:
                    res = morris.analyze(
                        problem,
                        df[problem['names']].values.astype(float),
                        Y,
                        num_resamples=num_resamples,
                        conf_level=conf_level,
                        scaled=scaled,
                        print_to_console=print_to_console,
                        num_levels=num_levels,
                        seed=seed,
                    )
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

    def run_sensitivity_analysis_by_epw(
            self,
            method: Literal['sobol', 'morris'] = 'morris',
            out_dir: str = '.',
            calc_second_order: bool = True,
            num_resamples: int = 100,
            conf_level: float = 0.95,
            print_to_console: bool = False,
            parallel: bool = False,
            n_processors: Optional[int] = None,
            keep_resamples: bool = False,
            seed: Optional[int] = None,
            scaled: bool = False,
            num_levels: int = 4,
    ) -> dict:
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
        :param calc_second_order: Sobol only. Forwarded to ``run_sensitivity_analysis``.
        :param num_resamples: forwarded to ``run_sensitivity_analysis``.
        :param conf_level: forwarded to ``run_sensitivity_analysis``.
        :param print_to_console: forwarded to ``run_sensitivity_analysis``.
        :param parallel: Sobol only. Forwarded to ``run_sensitivity_analysis``.
        :param n_processors: Sobol only. Forwarded to ``run_sensitivity_analysis``.
        :param keep_resamples: Sobol only. Forwarded to ``run_sensitivity_analysis``.
        :param seed: forwarded to ``run_sensitivity_analysis``.
        :param scaled: Morris only. Forwarded to ``run_sensitivity_analysis``.
        :param num_levels: Morris only. Forwarded to ``run_sensitivity_analysis``.
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
            sa_results = self.run_sensitivity_analysis(
                method=method,
                calc_second_order=calc_second_order,
                num_resamples=num_resamples,
                conf_level=conf_level,
                print_to_console=print_to_console,
                parallel=parallel,
                n_processors=n_processors,
                keep_resamples=keep_resamples,
                seed=seed,
                scaled=scaled,
                num_levels=num_levels,
            )
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
        if normalize_per_m2:
            area_attr = getattr(self, 'building_floor_area', None)
            if not area_attr:
                print('[!] normalize_per_m2 is True but building_floor_area is not set. Call set_building_floor_area() first. Falling back to kWh.')
                unit_str = 'kWh'
                normalize_per_m2 = False
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
            if normalize_per_m2:
                if isinstance(area_attr, dict) and 'idf' in robustness_df.columns:
                    areas = robustness_df['idf'].map(area_attr).fillna(1.0)
                    divisors = 3600000.0 * areas
                else:
                    area_val = area_attr if not isinstance(area_attr, dict) else list(area_attr.values())[0]
                    divisors = 3600000.0 * area_val
            else:
                divisors = 3600000.0
                
            robustness_df[f'Total_Energy_{unit_str.replace("/", "_")}'] = (robustness_df[heating_col] + robustness_df[cooling_col]) / divisors
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
