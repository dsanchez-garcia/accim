"""Analysis helpers for ACCIM parametric and optimisation post-processing.

This module centralises floor-area normalization, sensitivity analysis,
and decision-support routines used by the simulation workflows.

Usage
-----
Use `AnalysisMixin` in the main workflow class and call the public methods
after running parametric or optimisation simulations.

Examples
--------
sim.set_building_floor_area(mode='all')
sim.normalize_outputs()
"""

import os
import glob
import shutil
import re
import difflib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any, Dict, Literal, Optional, Union
from accim.parametric_and_optimisation.utils import apply_data_filter, resolve_subplot_orders

class AnalysisMixin:

    """Mixin with post-processing helpers for parametric and optimisation runs.

    The mixin groups internal utilities for floor-area handling, plus public
    methods for normalization, sensitivity analysis, clustering, and robustness.

    Usage
    -----
    Inherit this mixin in the simulation session class and call the public
    APIs once `outputs_param_simulation` or `outputs_optimisation` are available.

    Examples
    --------
    session.set_building_floor_area(mode='occupied')
    session.run_sensitivity_analysis(method='morris')
    """

    @staticmethod
    def _normalise_floor_area_idf_name(name: str) -> str:
        """Normalize an IDF identifier to a canonical name used for floor-area mapping.

        Parameters
        ----------
        name : Any
            Raw IDF/object name or text to normalize.

        Returns
        -------
        str
            Canonical IDF key without backup prefixes/suffixes.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        AnalysisMixin._normalise_floor_area_idf_name('accim_idf_backup_Model_A_post_setup_20260624_101010.idf')
        """

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
        """Resolve a stable, normalized IDF name for floor-area calculations.

        Parameters
        ----------
        idf : Any
            IDF model object.
        idx : Any
            Zero-based IDF index used for deterministic fallback names.

        Returns
        -------
        str
            Normalized IDF name, with a deterministic fallback when unavailable.

        Usage
        -----
        Used internally by `set_building_floor_area` during floor-area resolution.

        Examples
        --------
        self._get_floor_area_idf_name(idf=my_idf, idx=0)
        """

        if hasattr(self, '_get_idf_identifier'):
            raw_name = self._get_idf_identifier(idf, idx)
        else:
            raw_name = getattr(idf, 'idfname', f'unknown_idf_{idx}')
        idf_name = self._normalise_floor_area_idf_name(raw_name)
        return idf_name if idf_name else f'unknown_idf_{idx}'

    @staticmethod
    def _idf_objects(idf: Any, object_key: str) -> list:
        """Retrieve IDF objects for a class key using tolerant key matching.

        Parameters
        ----------
        idf : Any
            IDF model object.
        object_key : Any
            Requested EnergyPlus object class key.

        Returns
        -------
        list
            Matching list of IDF objects for the requested class key.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        self._idf_objects(idf=my_idf, object_key='ZONE')
        """

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
        """Iterate IDF object-class items safely even when mappings are non-standard.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        Iterator[tuple[str, Any]]
            Pairs of object class name and associated object collection.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._idf_object_items(idf=...)
        """

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
        """Find the first non-empty attribute value from a list of candidate names.

        Parameters
        ----------
        obj : Any
            IDF object to inspect.
        attrs : Any
            Ordered attribute names to evaluate.

        Returns
        -------
        Any
            First non-empty attribute value or None when no candidate exists.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._first_existing_attr(obj=..., attrs=...)
        """

        for attr in attrs:
            value = getattr(obj, attr, None)
            if value not in (None, ''):
                return value
        return None

    @staticmethod
    def _iter_list_object_values(obj: Any, prefix: str):
        """Yield unique referenced object names from list-like IDF fields.

        Parameters
        ----------
        obj : Any
            IDF object to inspect.
        prefix : Any
            Prefix used to identify list-like field names.

        Returns
        -------
        Iterator[Any]
            Unique referenced names extracted from list-style fields.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._iter_list_object_values(obj=..., prefix=...)
        """

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
        """Build a lookup from uppercase zone names to original zone names.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        dict
            Dictionary keyed by uppercase zone name.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._get_zone_lookup(idf=...)
        """

        return {
            z.Name.upper(): z.Name
            for z in self._idf_objects(idf, 'ZONE')
            if getattr(z, 'Name', None)
        }

    def _get_space_to_zone_lookup(self, idf: Any) -> Dict[str, str]:
        """Build a lookup from space names to their parent zone names.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        dict
            Dictionary keyed by uppercase space name with uppercase zone values.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._get_space_to_zone_lookup(idf=...)
        """

        lookup = {}
        for space in self._idf_objects(idf, 'SPACE'):
            space_name = getattr(space, 'Name', None)
            zone_name = self._first_existing_attr(space, ['Zone_Name', 'Zone_or_ZoneList_Name'])
            if space_name and zone_name:
                lookup[space_name.upper()] = zone_name.upper()
        return lookup

    def _get_zonelist_lookup(self, idf: Any) -> Dict[str, set]:
        """Build a lookup from zonelist names to the set of contained zones.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        dict
            Dictionary keyed by uppercase zonelist name with zone-name sets.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._get_zonelist_lookup(idf=...)
        """

        lookup = {}
        for zonelist in self._idf_objects(idf, 'ZONELIST'):
            name = getattr(zonelist, 'Name', None)
            if name:
                lookup[name.upper()] = {z.upper() for z in self._iter_list_object_values(zonelist, 'Zone')}
        return lookup

    def _get_spacelist_lookup(self, idf: Any) -> Dict[str, set]:
        """Build a lookup from spacelist names to resolved zone names.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        dict
            Dictionary keyed by uppercase spacelist name with zone-name sets.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._get_spacelist_lookup(idf=...)
        """

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
        """Resolve names that can reference zones, spaces, zonelists, or spacelists.

        Parameters
        ----------
        idf : Any
            IDF model object.
        names : Any
            Candidate names that may reference zones, spaces, or list objects.

        Returns
        -------
        set
            Set of uppercase resolved zone names.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._resolve_zone_like_names(idf=..., names=...)
        """

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
        """Resolve occupied zone names from PEOPLE object targets.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        set
            Set of uppercase occupied zone names.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._resolve_occupied_zone_names(idf=...)
        """

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
        """Check whether an object class can reference conditioned zones.

        Parameters
        ----------
        class_name : Any
            EnergyPlus object class name.

        Returns
        -------
        bool
            True when the object class is HVAC/zone-control related.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._is_air_conditioning_object_class(class_name=...)
        """

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
        """Check whether a field name is likely to represent a conditioned zone reference.

        Parameters
        ----------
        field_name : Any
            Field name to evaluate.

        Returns
        -------
        bool
            True when the field is considered a conditioned-zone reference field.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._is_conditioned_zone_field(field_name=...)
        """

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
        """Yield unique zone-like targets declared in HVAC-related IDF objects.

        Parameters
        ----------
        obj : Any
            IDF object to inspect.

        Returns
        -------
        Iterator[Any]
            Unique target names extracted from conditioned-zone fields.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        self._iter_conditioned_zone_targets(obj=...)
        """

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
        """Resolve conditioned zone names from HVAC/control objects.

        Parameters
        ----------
        idf : Any
            IDF model object.

        Returns
        -------
        set
            Set of uppercase air-conditioned zone names.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._resolve_air_conditioned_zone_names(idf=...)
        """

        targets = []
        for object_class, objects in self._idf_object_items(idf):
            if not self._is_air_conditioning_object_class(object_class):
                continue
            for obj in objects:
                targets.extend(self._iter_conditioned_zone_targets(obj))
        return self._resolve_zone_like_names(idf, targets)

    def _sum_floor_area(self, idf: Any, floors: list, zone_names: set = None) -> float:
        """Sum floor area for all floors or for floors linked to selected zones.

        Parameters
        ----------
        idf : Any
            IDF model object.
        floors : Any
            Collection of floor surfaces.
        zone_names : Any
            Optional set of uppercase zone names used to filter surfaces.

        Returns
        -------
        float
            Summed floor area in m2.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        self._sum_floor_area(idf=..., floors=..., zone_names=...)
        """

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
        """Resolve a scalar-or-dictionary floor-area configuration for one IDF.

        Parameters
        ----------
        config : Any
            Scalar value or dictionary keyed by IDF name.
        idf_name : Any
            Normalized IDF name currently being processed.
        idf_names : Any
            Expected normalized IDF names.
        argument_name : Any
            Argument label used in validation error messages.

        Returns
        -------
        Any
            Resolved scalar value for the current IDF.

        Usage
        -----
        Used internally by `set_building_floor_area` during floor-area resolution.

        Examples
        --------
        self._resolve_floor_area_config(config=..., idf_name=..., idf_names=..., argument_name=...)
        """

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
        """Coerce a custom floor-area value to float.

        Parameters
        ----------
        value : Any
            Input value to convert or normalize.

        Returns
        -------
        float
            Parsed numeric floor area.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        AnalysisMixin._coerce_custom_floor_area(value=...)
        """

        if isinstance(value, str):
            value = value.strip().replace(',', '.')
        return float(value)

    def _coerce_zones_list(self, idf: Any, zones_list: Any, idf_name: str) -> set:
        """Validate and resolve a user-provided zones list into canonical zone names.

        Parameters
        ----------
        idf : Any
            IDF model object.
        zones_list : Any
            Zone list value (list/string) or mapping by IDF.
        idf_name : Any
            Normalized IDF name currently being processed.

        Returns
        -------
        set
            Resolved set of uppercase zone names.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._coerce_zones_list(idf=..., zones_list=..., idf_name=...)
        """

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

    def _load_floor_area_buildings_from_backup_paths(self, requested_idf_names: Optional[list] = None) -> list:
        """Load IDF objects from backup paths, optionally filtered by requested names.

        Parameters
        ----------
        requested_idf_names : Any
            Optional list of IDF names that must be loaded.

        Returns
        -------
        list
            List of loaded IDF objects.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        self._load_floor_area_buildings_from_backup_paths(requested_idf_names=...)
        """

        backup_path = getattr(self, 'idf_backup_path', None)
        backup_list = backup_path if isinstance(backup_path, list) else ([backup_path] if backup_path else [])
        valid_backups = [p for p in backup_list if p and os.path.isfile(p)]
        if not valid_backups:
            raise AttributeError(
                "self.building is None and no valid idf_backup_path is available. "
                "Either provide mode='custom' with a custom_area value, or load the "
                "session with an IDF object (building= argument)."
            )

        selected_paths = valid_backups
        if requested_idf_names is not None:
            requested_names = []
            for name in requested_idf_names:
                normalised_name = self._normalise_floor_area_idf_name(name)
                if normalised_name and normalised_name not in requested_names:
                    requested_names.append(normalised_name)

            backup_by_name = {}
            duplicated_names = set()
            for path in valid_backups:
                normalised_name = self._normalise_floor_area_idf_name(path)
                if normalised_name in backup_by_name:
                    duplicated_names.add(normalised_name)
                    continue
                backup_by_name[normalised_name] = path

            if duplicated_names:
                duplicated = sorted(duplicated_names)
                raise ValueError(
                    f"Duplicate IDF names found in idf_backup_path for floor area calculation: {duplicated}. "
                    f"Use unique filenames or pre-load self.buildings with those IDFs."
                )

            missing = sorted(name for name in requested_names if name not in backup_by_name)
            if missing:
                available = sorted(backup_by_name.keys())
                raise ValueError(
                    f"Could not find IDF backup path(s) for: {missing}. "
                    f"Available IDFs from idf_backup_path: {available}"
                )

            selected_paths = [backup_by_name[name] for name in requested_names]

        from accim.utils import get_building
        return [get_building(path) for path in selected_paths]

    def _get_floor_area_buildings(self, requested_idf_names: Optional[list] = None) -> list:
        """Get IDF objects for floor-area calculations from loaded models or backup paths.

        Parameters
        ----------
        requested_idf_names : Any
            Optional list of IDF names that must be loaded.

        Returns
        -------
        list
            List of IDF objects matching the requested scope.

        Usage
        -----
        Used internally by `set_building_floor_area` during floor-area resolution.

        Examples
        --------
        self._get_floor_area_buildings(requested_idf_names=['Model_A', 'Model_B'])
        """

        requested_names = None
        if requested_idf_names is not None:
            requested_names = []
            for name in requested_idf_names:
                normalised_name = self._normalise_floor_area_idf_name(name)
                if normalised_name and normalised_name not in requested_names:
                    requested_names.append(normalised_name)

        buildings = getattr(self, 'buildings', [])
        if buildings:
            if requested_names is None:
                return buildings

            available = {
                self._get_floor_area_idf_name(idf, idx): idf
                for idx, idf in enumerate(buildings)
            }
            selected = []
            missing = []
            for name in requested_names:
                idf = available.get(name)
                if idf is None:
                    missing.append(name)
                else:
                    selected.append(idf)

            if not missing:
                return selected

            try:
                loaded_missing = self._load_floor_area_buildings_from_backup_paths(missing)
            except AttributeError:
                raise ValueError(
                    f"Could not find IDF object(s) for floor area calculation: {sorted(missing)}. "
                    f"Load those IDFs in self.buildings or provide matching idf_backup_path entries."
                )

            loaded_missing_map = {
                self._get_floor_area_idf_name(idf, idx): idf
                for idx, idf in enumerate(loaded_missing)
            }
            combined = dict(available)
            combined.update(loaded_missing_map)

            unresolved = sorted(name for name in requested_names if name not in combined)
            if unresolved:
                raise ValueError(
                    f"Could not find IDF object(s) for floor area calculation: {unresolved}."
                )

            return [combined[name] for name in requested_names]

        idf = getattr(self, 'building', None)
        if idf is not None:
            if requested_names is None:
                return [idf]

            idf_name = self._get_floor_area_idf_name(idf, 0)
            selected_names = [name for name in requested_names if name == idf_name]
            missing_names = [name for name in requested_names if name != idf_name]

            if not missing_names and selected_names:
                return [idf]

            try:
                loaded_missing = self._load_floor_area_buildings_from_backup_paths(missing_names) if missing_names else []
            except AttributeError:
                raise ValueError(
                    f"Could not find IDF object(s) for floor area calculation: {sorted(missing_names)}. "
                    f"Load those IDFs in self.buildings or provide matching idf_backup_path entries."
                )
            loaded_missing_map = {
                self._get_floor_area_idf_name(loaded_idf, idx): loaded_idf
                for idx, loaded_idf in enumerate(loaded_missing)
            }
            combined = {idf_name: idf}
            combined.update(loaded_missing_map)

            unresolved = sorted(name for name in requested_names if name not in combined)
            if unresolved:
                raise ValueError(
                    f"Could not find IDF object(s) for floor area calculation: {unresolved}."
                )

            return [combined[name] for name in requested_names]

        loaded = self._load_floor_area_buildings_from_backup_paths(requested_names)
        if requested_names is None:
            self.buildings = loaded
            print(f'  [info] {len(loaded)} IDF(s) auto-loaded from backup paths.')
        else:
            print(f'  [info] {len(loaded)} representative IDF(s) loaded from backup paths.')
        return loaded

    def _set_and_return_building_floor_area(self, areas: Dict[str, float]):
        """Store calculated floor area(s), print diagnostics, and return the stored value.

        Parameters
        ----------
        areas : Any
            Dictionary mapping IDF names to computed floor areas.

        Returns
        -------
        Any
            Stored floor area value (float or mapping).

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        self._set_and_return_building_floor_area(areas=...)
        """

        if len(areas) == 1:
            self.building_floor_area = list(areas.values())[0]
            print(f'  [info] Building floor area: {self.building_floor_area:.2f} m² (single IDF)')
            return self.building_floor_area

        self.building_floor_area = areas
        for idf_name, area in areas.items():
            print(f'  [info] Building floor area [{idf_name}]: {area:.2f} m²')
        return areas

    def _calculate_floor_area_for_idf(
            self,
            idf: Any,
            idf_name: str,
            idf_names: list,
            normalised_mode: str,
            zones_list: Union[list, Dict[str, list]],
            custom_area: Union[str, float, Dict[str, Union[str, float]]]
    ) -> float:
        """Compute floor area for one IDF according to the selected mode.

        Parameters
        ----------
        idf : Any
            IDF model object.
        idf_name : Any
            Normalized IDF name currently being processed.
        idf_names : Any
            Expected normalized IDF names.
        normalised_mode : Any
            Normalized floor-area mode.
        zones_list : Any
            Zone list value (list/string) or mapping by IDF.
        custom_area : Any
            Custom floor area value or mapping keyed by IDF.

        Returns
        -------
        float
            Calculated floor area for the target IDF in m2.

        Usage
        -----
        Used internally by `set_building_floor_area` during floor-area resolution.

        Examples
        --------
        self._calculate_floor_area_for_idf(idf=my_idf, idf_name='Model_A', idf_names=['Model_A'], normalised_mode='all', zones_list=None, custom_area=None)
        """

        surfaces = self._idf_objects(idf, 'BuildingSurface:Detailed')
        floors = [s for s in surfaces if getattr(s, 'Surface_Type', '').lower() == 'floor']

        if normalised_mode == 'custom':
            custom_value = self._resolve_floor_area_config(custom_area, idf_name, idf_names, 'custom_area')
            return self._coerce_custom_floor_area(custom_value)
        if normalised_mode == 'all':
            return self._sum_floor_area(idf, floors)
        if normalised_mode == 'occupied':
            zone_names = self._resolve_occupied_zone_names(idf)
            return self._sum_floor_area(idf, floors, zone_names)
        if normalised_mode == 'air-conditioned':
            zone_names = self._resolve_air_conditioned_zone_names(idf)
            return self._sum_floor_area(idf, floors, zone_names)
        if normalised_mode == 'list':
            idf_zones_list = self._resolve_floor_area_config(zones_list, idf_name, idf_names, 'zones_list')
            zone_names = self._coerce_zones_list(idf, idf_zones_list, idf_name)
            return self._sum_floor_area(idf, floors, zone_names)

        raise ValueError(f'Unknown mode: {normalised_mode}')

    @staticmethod
    def _normalise_representative_mode(mode: str) -> str:
        """Normalize representative mode labels to the internal canonical form.

        Parameters
        ----------
        mode : Any
            Value for `mode`.

        Returns
        -------
        str
            Normalized representative mode label.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        AnalysisMixin._normalise_representative_mode(mode=...)
        """

        return str(mode).strip().lower().replace('-', '_')

    @staticmethod
    def _normalise_representative_category_value(value: Any):
        """Normalize representative category values, mapping missing values to None.

        Parameters
        ----------
        value : Any
            Input value to convert or normalize.

        Returns
        -------
        Any
            Normalized category value, or None for missing values.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        AnalysisMixin._normalise_representative_category_value(value=...)
        """

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        return value

    @staticmethod
    def _representative_sort_key(value: Any) -> str:
        """Build a deterministic sort key for representative category values.

        Parameters
        ----------
        value : Any
            Input value to convert or normalize.

        Returns
        -------
        str
            String sort key used for deterministic ordering.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._representative_sort_key(value=...)
        """

        if value is None:
            return ''
        return str(value)

    @staticmethod
    def _format_representative_values(values: set) -> list:
        """Format representative category values in a sorted order for readable messages.

        Parameters
        ----------
        values : Any
            Value for `values`.

        Returns
        -------
        list
            Sorted category values ready for display.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        AnalysisMixin._format_representative_values(values=...)
        """

        return sorted(values, key=AnalysisMixin._representative_sort_key)

    def _available_idf_mapping_categories(self) -> list:
        """Get sorted IDF mapping categories available in the current session.

        Parameters
        ----------
        None
            This helper does not receive explicit arguments.

        Returns
        -------
        list
            Sorted category names from idf_mapping_rules.

        Usage
        -----
        Internal utility used by the analysis pipeline.

        Examples
        --------
        self._available_idf_mapping_categories()
        """

        idf_mapping_rules = getattr(self, 'idf_mapping_rules', {}) or {}
        return sorted(idf_mapping_rules.keys())

    def _get_floor_area_idf_category_groups(self, representative_category: str, available_categories: list):
        """Build IDF-to-category and category-to-IDFs mappings from simulation outputs.

        Parameters
        ----------
        representative_category : Any
            Grouping category name used for representative selection.
        available_categories : Any
            Valid category names available for grouping.

        Returns
        -------
        tuple
            Tuple with (idf_to_category, category_to_idfs).

        Usage
        -----
        Used internally by `set_building_floor_area` during floor-area resolution.

        Examples
        --------
        self._get_floor_area_idf_category_groups(representative_category=..., available_categories=...)
        """

        outputs = getattr(self, 'outputs_param_simulation', None)
        if outputs is None or outputs.empty:
            raise ValueError(
                "outputs_param_simulation must be available and non-empty when "
                "representative_mode is not 'all'."
            )
        if 'idf' not in outputs.columns:
            raise ValueError("Column 'idf' is required in outputs_param_simulation to use representative_mode.")
        if representative_category not in outputs.columns:
            raise ValueError(
                f"Category column '{representative_category}' is missing in outputs_param_simulation. "
                f"Available categories: {available_categories}"
            )

        idf_category_df = outputs[['idf', representative_category]].copy()
        idf_category_df['idf'] = idf_category_df['idf'].apply(self._normalise_floor_area_idf_name)
        idf_category_df[representative_category] = idf_category_df[representative_category].apply(
            self._normalise_representative_category_value
        )
        idf_category_df = idf_category_df[idf_category_df['idf'] != '']

        if idf_category_df.empty:
            raise ValueError('No valid IDF/category rows found in outputs_param_simulation for floor area mapping.')

        category_counts = idf_category_df.groupby('idf')[representative_category].nunique(dropna=False)
        conflicted_idfs = sorted(category_counts[category_counts > 1].index.tolist())
        if conflicted_idfs:
            raise ValueError(
                f"Category '{representative_category}' has multiple values for the same IDF in "
                f"outputs_param_simulation: {conflicted_idfs}"
            )

        unique_pairs = idf_category_df.drop_duplicates(subset=['idf'])
        idf_to_category = dict(zip(unique_pairs['idf'], unique_pairs[representative_category]))

        category_to_idfs = {}
        for idf_name, category_value in idf_to_category.items():
            category_to_idfs.setdefault(category_value, []).append(idf_name)
        for idf_list in category_to_idfs.values():
            idf_list.sort()

        return idf_to_category, category_to_idfs

    def _normalise_representative_map(self, representative_map: Optional[Dict[str, str]]) -> Dict[Any, str]:
        """Normalize and validate a custom representative map.

        Parameters
        ----------
        representative_map : Any
            Custom mapping from category values to representative IDF names.

        Returns
        -------
        dict
            Normalized category-to-representative-IDF mapping.

        Usage
        -----
        Internal utility used by analysis workflows to keep data handling deterministic.

        Examples
        --------
        self._normalise_representative_map(representative_map=...)
        """

        if not isinstance(representative_map, dict) or len(representative_map) == 0:
            raise ValueError("representative_map must be a non-empty dict when representative_mode='custom_map'.")

        normalised_map = {}
        for category_value, representative_idf in representative_map.items():
            normalised_category = self._normalise_representative_category_value(category_value)
            normalised_idf = self._normalise_floor_area_idf_name(representative_idf)
            if not normalised_idf:
                raise ValueError(
                    f"Invalid representative IDF for category {category_value!r}: {representative_idf!r}"
                )
            if normalised_category in normalised_map and normalised_map[normalised_category] != normalised_idf:
                raise ValueError(
                    f"Duplicate category key in representative_map after normalization: {category_value!r}"
                )
            normalised_map[normalised_category] = normalised_idf

        return normalised_map

    def _resolve_floor_area_representative_plan(
            self,
            representative_mode: str,
            representative_category: Optional[str],
            representative_map: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Resolve representative-IDF planning metadata for grouped floor-area calculation.

        Parameters
        ----------
        representative_mode : Any
            Representative loading strategy.
        representative_category : Any
            Grouping category name used for representative selection.
        representative_map : Any
            Custom mapping from category values to representative IDF names.

        Returns
        -------
        dict
            Representative plan with resolved category and IDF mappings.

        Usage
        -----
        Used internally by `set_building_floor_area` during floor-area resolution.

        Examples
        --------
        self._resolve_floor_area_representative_plan(representative_mode='by_idf_mapping_category', representative_category='building_type', representative_map=None)
        """

        available_categories = self._available_idf_mapping_categories()
        resolved_category = representative_category

        if representative_mode == 'by_idf_mapping_category':
            if not resolved_category:
                raise ValueError(
                    "representative_category must be provided when "
                    "representative_mode='by_idf_mapping_category'."
                )
        elif representative_mode == 'custom_map':
            if not resolved_category and len(available_categories) == 1:
                resolved_category = available_categories[0]
            if not resolved_category:
                raise ValueError(
                    "representative_category must be provided when representative_mode='custom_map'."
                )
        else:
            raise ValueError(f"Unknown representative_mode: {representative_mode}")

        if resolved_category not in available_categories:
            raise ValueError(
                f"Invalid representative_category={resolved_category!r}. "
                f"Available categories: {available_categories}"
            )

        idf_to_category, category_to_idfs = self._get_floor_area_idf_category_groups(
            representative_category=resolved_category,
            available_categories=available_categories,
        )

        if representative_mode == 'by_idf_mapping_category':
            category_to_representative = {
                category_value: idf_names[0]
                for category_value, idf_names in category_to_idfs.items()
            }
        else:
            normalised_map = self._normalise_representative_map(representative_map)
            expected_values = set(category_to_idfs.keys())
            provided_values = set(normalised_map.keys())
            missing_values = expected_values - provided_values
            unknown_values = provided_values - expected_values
            if missing_values or unknown_values:
                error_messages = []
                if missing_values:
                    error_messages.append(
                        f"missing category values: {self._format_representative_values(missing_values)}"
                    )
                if unknown_values:
                    error_messages.append(
                        f"unknown category values: {self._format_representative_values(unknown_values)}"
                    )
                raise ValueError(
                    f"Invalid representative_map ({'; '.join(error_messages)})."
                )

            available_idfs = sorted(idf_to_category.keys())
            category_to_representative = {}
            for category_value in category_to_idfs:
                representative_idf_name = normalised_map[category_value]
                if representative_idf_name not in idf_to_category:
                    raise ValueError(
                        f"Representative IDF '{representative_idf_name}' for category "
                        f"{category_value!r} was not found in outputs_param_simulation IDFs: {available_idfs}"
                    )
                if representative_idf_name not in category_to_idfs[category_value]:
                    expected_group = category_to_idfs[category_value]
                    raise ValueError(
                        f"Representative IDF '{representative_idf_name}' does not belong to category "
                        f"{category_value!r}. Expected one of: {expected_group}"
                    )
                category_to_representative[category_value] = representative_idf_name

        idf_to_representative = {
            idf_name: category_to_representative[category_value]
            for idf_name, category_value in idf_to_category.items()
        }
        all_idf_names = sorted(idf_to_representative.keys())
        representative_idf_names = sorted(set(idf_to_representative.values()))

        return {
            'representative_category': resolved_category,
            'all_idf_names': all_idf_names,
            'representative_idf_names': representative_idf_names,
            'idf_to_representative': idf_to_representative,
        }

    def set_building_floor_area(
            self,
            mode: Literal['all', 'occupied', 'air-conditioned', 'air-condicioned', 'custom', 'list']='all',
            zones_list: Union[list, Dict[str, list]]=None,
            custom_area: Union[str, float, Dict[str, Union[str, float]]]=None,
            representative_mode: Literal['all', 'by_idf_mapping_category', 'custom_map']='all',
            representative_category: Optional[str]=None,
            representative_map: Optional[Dict[str, str]]=None,
    ) -> Union[float, Dict[str, float]]:
        """Calculates or sets the floor area to be used for normalizing energy results (kWh/m2).
        
        :param mode: 'all' to use all Floor surfaces in the IDF.
                     'occupied' to use Floor surfaces in zones that have a People object.
                     'air-conditioned' to use Floor surfaces in zones served or controlled by HVAC objects.
                     'custom' to use the value provided in `custom_area`.
                     'list' to use Floor surfaces only in the zones specified in `zones_list`.
        :param zones_list: List of zone names for mode 'list', or a dict mapping each IDF to its list.
        :param custom_area: Float/string value for mode 'custom', or a dict mapping each IDF to its value.
        :param representative_mode: Strategy to reduce IDF loading when calculating areas.
            'all' keeps legacy behaviour.
            'by_idf_mapping_category' loads one deterministic representative IDF per
            category value in `representative_category`.
            'custom_map' uses `representative_map` (category_value -> representative_idf).
        :param representative_category: IDF category column name used to group IDFs.
            Must be one of the keys in `idf_mapping_rules` when representative_mode is
            not 'all'.
        :param representative_map: Explicit mapping for representative_mode='custom_map',
            with format {category_value: representative_idf}.
        
        Example::
        
            sim.set_building_floor_area(mode='air-conditioned')
            sim.set_building_floor_area(
                mode='air-conditioned',
                representative_mode='by_idf_mapping_category',
                representative_category='building_type',
            )
            sim.set_building_floor_area(
                mode='air-conditioned',
                representative_mode='custom_map',
                representative_category='building_type',
                representative_map={
                    'residential': 'Residential_A',
                    'office': 'Office_A',
                },
            )
        
        :return: the calculated or assigned floor area.
        
        Usage
        -----
        Use `AnalysisMixin.set_building_floor_area` within ACCIM parametric and optimisation workflows.
        """
        normalised_mode = str(mode).lower().replace('_', '-').strip()
        if normalised_mode == 'air-condicioned':
            normalised_mode = 'air-conditioned'

        normalised_representative_mode = self._normalise_representative_mode(representative_mode)
        valid_representative_modes = {'all', 'by_idf_mapping_category', 'custom_map'}
        if normalised_representative_mode not in valid_representative_modes:
            raise ValueError(
                f"Invalid representative_mode={representative_mode!r}. "
                f"Valid options are: {sorted(valid_representative_modes)}"
            )

        if normalised_mode == 'custom':
            if custom_area is None:
                raise ValueError("custom_area must be provided when mode='custom'")
            if not isinstance(custom_area, dict):
                self.building_floor_area = self._coerce_custom_floor_area(custom_area)
                return self.building_floor_area

        if normalised_representative_mode == 'all':
            buildings = self._get_floor_area_buildings()
            idf_names = [self._get_floor_area_idf_name(idf, idx) for idx, idf in enumerate(buildings)]

            print(
                f"  [info] Floor area calculation: total IDFs={len(idf_names)}, "
                f"representative IDFs loaded={len(idf_names)}."
            )

            areas = {}
            for idx, idf in enumerate(buildings):
                idf_name = idf_names[idx]
                areas[idf_name] = self._calculate_floor_area_for_idf(
                    idf=idf,
                    idf_name=idf_name,
                    idf_names=idf_names,
                    normalised_mode=normalised_mode,
                    zones_list=zones_list,
                    custom_area=custom_area,
                )

            print(f"  [info] Floor area mapping coverage: {len(areas)}/{len(idf_names)} IDFs.")
            return self._set_and_return_building_floor_area(areas)

        representative_plan = self._resolve_floor_area_representative_plan(
            representative_mode=normalised_representative_mode,
            representative_category=representative_category,
            representative_map=representative_map,
        )
        all_idf_names = representative_plan['all_idf_names']
        representative_idf_names = representative_plan['representative_idf_names']
        idf_to_representative = representative_plan['idf_to_representative']

        representative_buildings = self._get_floor_area_buildings(requested_idf_names=representative_idf_names)
        representative_buildings_by_name = {
            self._get_floor_area_idf_name(idf, idx): idf
            for idx, idf in enumerate(representative_buildings)
        }
        missing_representatives = [
            name for name in representative_idf_names
            if name not in representative_buildings_by_name
        ]
        if missing_representatives:
            raise ValueError(
                f"Could not load representative IDF object(s): {sorted(missing_representatives)}"
            )

        print(
            f"  [info] Floor area calculation: total IDFs={len(all_idf_names)}, "
            f"representative IDFs loaded={len(representative_idf_names)}."
        )

        representative_areas = {}
        for representative_idf_name in representative_idf_names:
            representative_areas[representative_idf_name] = self._calculate_floor_area_for_idf(
                idf=representative_buildings_by_name[representative_idf_name],
                idf_name=representative_idf_name,
                idf_names=all_idf_names,
                normalised_mode=normalised_mode,
                zones_list=zones_list,
                custom_area=custom_area,
            )

        areas = {}
        for idf_name in all_idf_names:
            representative_idf_name = idf_to_representative[idf_name]
            areas[idf_name] = representative_areas[representative_idf_name]

        print(f"  [info] Floor area mapping coverage: {len(areas)}/{len(all_idf_names)} IDFs.")
        return self._set_and_return_building_floor_area(areas)

    @staticmethod
    def _normalizable_output_df_mapping() -> dict:
        """Return the canonical mapping between df_type tokens and dataframe attributes."""
        return {
            'parametric': 'outputs_param_simulation',
            'parametric_hourly': 'outputs_param_simulation_hourly',
            'parametric_daily': 'outputs_param_simulation_daily',
            'parametric_monthly': 'outputs_param_simulation_monthly',
            'parametric_runperiod': 'outputs_param_simulation_runperiod',
            'optimisation': 'outputs_optimisation',
            'optimisation_hourly': 'outputs_optimisation_hourly',
            'optimisation_daily': 'outputs_optimisation_daily',
            'optimisation_monthly': 'outputs_optimisation_monthly',
            'optimisation_runperiod': 'outputs_optimisation_runperiod',
        }

    def _get_normalized_output_df_types(self) -> set:
        """Return/create the internal tracker of normalized dataframe types."""
        normalized_df_types = getattr(self, '_normalized_output_df_types', None)
        if not isinstance(normalized_df_types, set):
            normalized_df_types = set()
            self._normalized_output_df_types = normalized_df_types
        return normalized_df_types

    def _is_df_type_normalized(self, df_type: str) -> bool:
        """Check whether a specific output dataframe type has already been normalized."""
        return str(df_type) in self._get_normalized_output_df_types()

    def _invalidate_normalized_df_types(self, df_types: Optional[list] = None) -> None:
        """Invalidate normalization state for one or many dataframe types."""
        normalized_df_types = self._get_normalized_output_df_types()
        if df_types is None:
            normalized_df_types.clear()
        else:
            for df_type in df_types:
                normalized_df_types.discard(str(df_type))
        self._refresh_outputs_normalized_flag()

    def _refresh_outputs_normalized_flag(self) -> None:
        """Refresh the legacy global flag based on per-dataframe normalization state."""
        normalized_df_types = self._get_normalized_output_df_types()
        df_mapping = self._normalizable_output_df_mapping()
        loaded_df_types = []
        for (df_key, df_attr) in df_mapping.items():
            df = getattr(self, df_attr, None)
            if isinstance(df, pd.DataFrame) and (not df.empty):
                loaded_df_types.append(df_key)
        self.outputs_normalized = len(loaded_df_types) > 0 and all(
            (df_key in normalized_df_types) for df_key in loaded_df_types
        )

    def normalize_outputs(self, df_types: list=None):
        """
        Normalizes energy-related columns in the specified dataframes by dividing them
        by the building floor area (and converting from Joules to kWh).
        The results are saved in-place, and the legacy `self.outputs_normalized`
        flag is refreshed from per-dataframe normalization tracking.
        
        :param df_types: A list of strings specifying which dataframes to normalize.
            Options include: 'parametric', 'parametric_hourly', 'parametric_daily',
            'parametric_monthly', 'parametric_runperiod',
            'optimisation', 'optimisation_hourly', 'optimisation_daily',
            'optimisation_monthly', 'optimisation_runperiod'.
            If None, all available dataframes will be normalized.

        Usage::

            Call this method after `set_building_floor_area(...)` and after simulation
            outputs have been generated.

        Example::

            sim.set_building_floor_area(mode='all')
            sim.normalize_outputs(df_types=['parametric', 'optimisation'])
        """
        import pandas as pd
        area_attr = getattr(self, 'building_floor_area', None)
        if not area_attr:
            raise ValueError('building_floor_area is not set. Please call set_building_floor_area() first.')
            
        df_mapping = self._normalizable_output_df_mapping()
        normalized_df_types = self._get_normalized_output_df_types()

        if df_types is None:
            df_types = list(df_mapping.keys())
        else:
            df_types = [str(df_key) for df_key in df_types]
        
        energy_keywords = ['Heating', 'Cooling', 'Energy', 'Electricity', 'Gas', 'Facility']
        
        for df_key in df_types:
            df_attr = df_mapping.get(df_key)
            if not df_attr:
                continue

            if df_key in normalized_df_types:
                print(f'  [info] {df_attr} is already normalized. Skipping.')
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
            normalized_df_types.add(df_key)
            
        self._refresh_outputs_normalized_flag()

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

        Usage::

            Run this method after `run_parametric_simulation(...)` with a compatible
            SALib sampling workflow.

        Example::

            sim.sampling_morris(num_samples=50)
            sim.run_parametric_simulation(...)
            sa = sim.run_sensitivity_analysis(method='morris')
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

    @staticmethod
    def _canonical_output_name(name: Any) -> str:
        """Canonicalize an output column name for robust fuzzy matching.

        Parameters
        ----------
        name : Any
            Raw IDF/object name or text to normalize.

        Returns
        -------
        str
            Normalized token used for output-column matching.

        Usage
        -----
        Called by `_resolve_output_columns` to match output names with tolerant normalization.

        Examples
        --------
        AnalysisMixin._canonical_output_name(name=...)
        """

        text = str(name).strip().lower()
        text = re.sub(r'kwh/m(?:2|\u00b2)', '', text)
        text = re.sub(r'_kwh[/_]?m2$', '', text)
        text = re.sub(r'\[[^]]*]', '', text)
        text = re.sub(r'[^a-z0-9]+', '', text)
        return text

    def _resolve_output_columns(self, output_names: list, available_columns: list, strict: bool=True) -> list:
        """Resolve requested output names against available dataframe columns.

        :param output_names: Output names requested by the optimisation/sensitivity
            workflow.
        :param available_columns: Actual dataframe columns available for lookup.
        :param strict: If True, raises `KeyError` when one or more outputs cannot be
            resolved. If False, unresolved outputs are skipped.
        :return: Ordered list of resolved column names.

        Usage::

            Called internally before MCDM or sensitivity post-processing to align
            problem output names with dataframe columns.

        Example::

            resolved = self._resolve_output_columns(
                output_names=['Total HVAC Energy'],
                available_columns=list(df.columns),
                strict=False,
            )
        """
        available_cols = [str(col) for col in available_columns]
        lower_lookup = {}
        canonical_lookup = {}
        for col in available_cols:
            lower_lookup.setdefault(col.lower(), []).append(col)
            canonical_lookup.setdefault(self._canonical_output_name(col), []).append(col)

        resolved = []
        used_columns = set()

        def _pick_column(candidates: list) -> Optional[str]:
            if len(candidates) == 0:
                return None
            if len(candidates) == 1:
                return candidates[0]
            not_used = [c for c in candidates if c not in used_columns]
            if len(not_used) >= 1:
                return not_used[0]
            return candidates[0]

        for output_name in output_names:
            requested = str(output_name).strip()
            chosen = None

            if requested in available_cols:
                chosen = requested

            if chosen is None:
                chosen = _pick_column(lower_lookup.get(requested.lower(), []))

            if chosen is None:
                variants = [
                    f'{requested}_kWh/m2',
                    f'{requested} [kWh/m2]',
                    requested.replace('[J]', '[kWh/m2]'),
                    requested.replace(' [J]', ' [kWh/m2]'),
                ]
                for variant in variants:
                    if variant in available_cols:
                        chosen = variant
                        break
                    chosen = _pick_column(lower_lookup.get(variant.lower(), []))
                    if chosen is not None:
                        break

            if chosen is None:
                prefix_matches = [
                    col for col in available_cols
                    if col.lower().startswith(requested.lower())
                ]
                chosen = _pick_column(prefix_matches)

            if chosen is None:
                canonical = self._canonical_output_name(requested)
                chosen = _pick_column(canonical_lookup.get(canonical, []))

            if chosen is None:
                suggestions = difflib.get_close_matches(requested, available_cols, n=3, cutoff=0.45)
                if strict:
                    if suggestions:
                        raise KeyError(
                            f"Could not resolve output column '{requested}'. Suggestions: {suggestions}"
                        )
                    raise KeyError(
                        f"Could not resolve output column '{requested}'. Available columns: {available_cols}"
                    )
                continue

            resolved.append(chosen)
            used_columns.add(chosen)

        if strict and len(resolved) != len(output_names):
            raise KeyError('Could not resolve all output columns in optimisation results.')

        return resolved

    def get_best_compromise_solution(self, method: Literal['knee_point', 'topsis']='topsis', weights: list=None) -> pd.DataFrame:
        """
        Identifies the best compromise solution from the Pareto front.

        :param method: The MCDM method to use. 'knee_point' (closest distance to Utopia point) or 'topsis'.
        :param weights: A list of weights for each objective, used only in 'topsis'.
            If None, equal weights are applied. Must match the number of objectives.
        :return: A pandas DataFrame containing the best compromise solution(s).

        Usage::

            Call this method after `run_optimisation(...)` when `outputs_optimisation`
            contains Pareto-optimal rows.

        Example::

            best = sim.get_best_compromise_solution(method='topsis', weights=[0.5, 0.5])
        """
        if getattr(self, 'last_run_type', None) != 'optimisation':
            raise ValueError('MCDM best compromise solutions can only be evaluated after an optimisation simulation. Please ensure you run run_optimisation() first.')
        if getattr(self, 'outputs_optimisation', None) is None or self.outputs_optimisation.empty:
            raise ValueError('No optimization results found. Run optimization first.')
        pareto_df = self.outputs_optimisation[self.outputs_optimisation['pareto-optimal'] == True].copy()
        if pareto_df.empty:
            raise ValueError('No Pareto optimal solutions found in outputs_optimisation.')
        output_names = self.problem.names('outputs')
        resolved_output_names = self._resolve_output_columns(output_names, list(pareto_df.columns))
        minimize_outputs = getattr(self.problem, 'minimize_outputs', None)
        if minimize_outputs is None:
            minimize_flags = [True] * len(resolved_output_names)
        else:
            minimize_flags = [m if m is not None else True for m in minimize_outputs]
        obj_values = pareto_df[resolved_output_names].values.astype(float)
        mins = obj_values.min(axis=0)
        maxs = obj_values.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1.0
        norm_values = (obj_values - mins) / ranges
        if method == 'knee_point':
            utopia = np.zeros(len(resolved_output_names))
            for (i, minimize) in enumerate(minimize_flags):
                if not minimize:
                    utopia[i] = 1.0
            distances = np.sqrt(np.sum((norm_values - utopia) ** 2, axis=1))
            pareto_df['distance_to_utopia'] = distances
            best_idx = np.argmin(distances)
            return pareto_df.iloc[[best_idx]].copy()
        elif method == 'topsis':
            if weights is None:
                weights = np.ones(len(resolved_output_names)) / len(resolved_output_names)
            else:
                if len(weights) != len(resolved_output_names):
                    raise ValueError(f'Length of weights ({len(weights)}) must match number of outputs ({len(resolved_output_names)}).')
                weights = np.array(weights) / np.sum(weights)
            sq_sum = np.sqrt(np.sum(obj_values ** 2, axis=0))
            sq_sum[sq_sum == 0] = 1.0
            topsis_norm = obj_values / sq_sum
            weighted_norm = topsis_norm * weights
            ideal_best = np.zeros(len(resolved_output_names))
            ideal_worst = np.zeros(len(resolved_output_names))
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
            subplot_order_mode: Literal['auto', 'alphabetical', 'ascending', 'descending', 'custom'] = 'auto',
            subplot_order_custom: Optional[dict] = None,
            subplot_order_case_sensitive: bool = False,
            data_filter: Optional[dict] = None,
            data_filter_case_sensitive: bool = False,
            data_filter_strict: bool = True,
            data_filter_on_empty: Literal['error', 'warn', 'ignore'] = 'error',
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
        :param subplot_order_mode: Strategy used to order output subplots.
            Accepted values are ``'auto'``, ``'alphabetical'``, ``'ascending'``,
            ``'descending'``, and ``'custom'``.
        :param subplot_order_custom: Custom subplot order mapping passed when
            ``subplot_order_mode='custom'``.
        :param subplot_order_case_sensitive: Whether subplot ordering should respect
            case when comparing labels.
        :param data_filter: Optional filtering spec applied before per-EPW analysis.
        :param data_filter_case_sensitive: Whether text matching in ``data_filter``
            should be case-sensitive.
        :param data_filter_strict: If True, invalid filter keys/values raise errors.
        :param data_filter_on_empty: Behaviour when filtering produces no rows:
            ``'error'``, ``'warn'``, or ``'ignore'``.
        :return: nested dict ``{epw_label: {output_name: SALib_result}}``.

        Usage::

            Use this method after running a parametric simulation with multiple EPWs
            to obtain and export one sensitivity report per climate file.

        Example::

            sa_by_epw = sim.run_sensitivity_analysis_by_epw(
                method='morris',
                out_dir='results_sa',
                subplot_order_mode='alphabetical',
                data_filter={'building_type': ['residential']},
            )
        """
        if getattr(self, 'last_run_type', None) != 'parametric':
            raise ValueError('Sensitivity Analysis by EPW can only be run after a parametric simulation. Please ensure you run run_parametric_simulation() first.')
        import matplotlib
        import matplotlib.pyplot as plt
        if getattr(self, 'outputs_param_simulation', None) is None or self.outputs_param_simulation.empty:
            raise ValueError('No parametric simulation results found. Run run_parametric_simulation before calling this method.')

        (filtered_outputs, _) = apply_data_filter(
            df=self.outputs_param_simulation,
            data_filter=data_filter,
            case_sensitive=data_filter_case_sensitive,
            strict=data_filter_strict,
            on_empty=data_filter_on_empty,
            context='run_sensitivity_analysis_by_epw',
        )

        os.makedirs(out_dir, exist_ok=True)
        epw_labels = filtered_outputs['epw'].unique()
        results_by_epw = {}
        original_df = self.outputs_param_simulation
        for epw_label in epw_labels:
            raw_tag = str(epw_label).strip()
            if raw_tag.lower().endswith('.epw'):
                raw_tag = os.path.splitext(os.path.basename(raw_tag))[0]
            epw_tag = re.sub(r'[^A-Za-z0-9_.-]+', '_', raw_tag).strip('_') or 'unknown_epw'
            self.outputs_param_simulation = filtered_outputs[filtered_outputs['epw'] == epw_label].copy()
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
            subplot_orders = resolve_subplot_orders(
                dimension_values={'col': output_names_sa},
                mode=subplot_order_mode,
                custom=subplot_order_custom,
                case_sensitive=subplot_order_case_sensitive,
                context='run_sensitivity_analysis_by_epw',
            )
            if 'col' in subplot_orders:
                order_lookup = {label: idx for (idx, label) in enumerate(subplot_orders['col'])}
                output_names_sa = sorted(output_names_sa, key=lambda name: order_lookup[name])

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
        """Cluster simulation solutions into design families using KMeans.

        Parameters
        ----------
        n_clusters : Any
            Number of clusters for KMeans.
        cluster_by : Any
            Feature family used for clustering ('parameters' or 'objectives').
        pareto_only : Any
            Whether to use only Pareto-optimal rows when clustering.
        out_dir : Any
            Directory where result files are saved.

        Returns
        -------
        pd.DataFrame
            Results dataframe with cluster labels.

        Usage
        -----
        Call after a parametric/optimisation run to segment solutions by design similarity.

        Examples
        --------
        clusters = self.run_clustering(n_clusters=3, cluster_by='parameters', pareto_only=True, out_dir='results')
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
        """Evaluate selected solutions across alternative EPW files to assess robustness.

        Parameters
        ----------
        optimal_solutions_df : Any
            Dataframe with selected solutions to be re-evaluated.
        epws_robustness : Any
            List of EPW paths used in robustness checks.
        out_dir : Any
            Directory where result files are saved.
        normalize_per_m2 : Any
            Whether to normalize energy metrics by floor area.

        Returns
        -------
        pd.DataFrame
            Dataframe containing robustness results across EPWs.

        Usage
        -----
        Call after selecting candidate solutions to compare their stability under multiple climates.

        Examples
        --------
        robustness = self.run_robustness_analysis(optimal_solutions_df=best_df, epws_robustness=['Seville.epw', 'Sydney.epw'], out_dir='results')
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
