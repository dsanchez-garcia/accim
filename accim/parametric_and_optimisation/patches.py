"""Runtime patches for BESOS evaluator and EnergyPlus execution.

This module injects helper behavior used by optimisation workflows, including
capturing per-run ``in.idf`` files, storing evaluation records, optional cleanup
of simulation outputs, and JSONL logging.

Usage
-----
Import these helpers when configuring BESOS evaluators that need ACCIM-specific
recording and cleanup behavior.

Examples
--------
_ensure_run_energyplus_copies_in_idf()
problem = _patched_to_platypus(evaluator)
"""

import os
import json
import functools
from accim.parametric_and_optimisation.file_cleanup import prune_simulation_output_files

class GlobalAllCapsDict(dict):
    """Dictionary wrapper that resolves keys case-insensitively in uppercase.

    Usage
    -----
    Use this helper when upstream code writes keys in mixed case but consumers
    always access keys as uppercase tokens.

    Examples
    --------
    data = GlobalAllCapsDict({'CSV': 1})
    value = data['csv']
    """

    def __getitem__(self, key):
        """Fetch item value using ``key.upper()`` lookup.

        Parameters
        ----------
        key : str
            Dictionary key requested by caller.

        Returns
        -------
        Any
            Value stored under the uppercase version of ``key``.

        Usage
        -----
        Called automatically by ``dict`` indexing operations.

        Examples
        --------
        data = GlobalAllCapsDict({'ABC': 10})
        value = data['abc']
        """
        return super().__getitem__(key.upper())


def _ensure_run_energyplus_copies_in_idf():
    """Patch BESOS so each simulation directory keeps the executed ``in.idf``.

    BESOS usually runs EnergyPlus with a temporary input file (often named
    ``in.idf`` under ``.besos_*``). This patch copies that exact file into the
    simulation output directory, so each result folder contains the final IDF
    used for that run.

    Parameters
    ----------
    None

    Returns
    -------
    None
        The patch is applied in-place to ``besos.eplus_funcs.run_energyplus``.

    Usage
    -----
    Call once during evaluator setup before launching optimisation workers.

    Examples
    --------
    _ensure_run_energyplus_copies_in_idf()
    """
    import shutil
    import besos.eplus_funcs as eplus_funcs

    if getattr(eplus_funcs, '_accim_copy_in_idf_patched', False):
        return

    original_run_energyplus = eplus_funcs.run_energyplus

    def _patched_run_energyplus(building_path, weather_path=None, out_dir=None, **kwargs):
        """Copy executed IDF into ``out_dir`` before delegating to BESOS.

        Parameters
        ----------
        building_path : Union[str, os.PathLike]
            Input IDF path BESOS passes to ``run_energyplus``.
        weather_path : Optional[Union[str, os.PathLike]]
            Optional EPW path.
        out_dir : Optional[Union[str, os.PathLike]]
            Output directory where ``in.idf`` should be copied.
        **kwargs : dict
            Additional keyword arguments forwarded to the original BESOS call.

        Returns
        -------
        Any
            Return value from the original ``run_energyplus`` implementation.

        Usage
        -----
        Created internally by ``_ensure_run_energyplus_copies_in_idf`` and used
        as a monkey-patched replacement.

        Examples
        --------
        result = _patched_run_energyplus('in.idf', weather_path='site.epw', out_dir='sim')
        """
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            src = os.fspath(building_path)
            dst = os.path.join(out_dir, 'in.idf')
            try:
                shutil.copy2(src, dst)
            except Exception:
                # Never fail the simulation because of a copy issue.
                pass

        if weather_path is not None:
            return original_run_energyplus(building_path, weather_path, out_dir=out_dir, **kwargs)
        return original_run_energyplus(building_path, out_dir=out_dir, **kwargs)

    eplus_funcs.run_energyplus = _patched_run_energyplus
    eplus_funcs._accim_copy_in_idf_patched = True

def _patched_eval_func(evaluator, all_outputs):
    """Evaluate one candidate while storing ACCIM optimisation metadata.

    Parameters
    ----------
    evaluator : Any
        BESOS evaluator instance patched by ACCIM.
    all_outputs : Sequence[Any]
        Candidate input vector to evaluate.

    Returns
    -------
    Any
        Packaged Platypus-compatible evaluation output.

    Usage
    -----
    Used as the function callback assigned in ``_patched_to_platypus``.

    Examples
    --------
    packed = _patched_eval_func(evaluator, all_outputs)
    """
    _ensure_run_energyplus_copies_in_idf()
    if getattr(evaluator, 'out_dir', None) is not None:
        if not hasattr(evaluator, '_out_dir_patched'):
            evaluator.out_dir = f'{evaluator.out_dir}_{os.getpid()}'
            evaluator._out_dir_patched = True
    keep_dirs = getattr(evaluator, '_keep_dirs', False)
    results = evaluator(all_outputs, keep_dirs=keep_dirs)
    if not hasattr(evaluator, '_optimisation_eval_records'):
        evaluator._optimisation_eval_records = []
    store_records_in_memory = bool(getattr(evaluator, '_store_optimisation_records_in_memory', True))
    eval_record = {'inputs': tuple(all_outputs)}
    if keep_dirs:
        eval_record['results'] = tuple(results[:-1])
        eval_record['sim_dir'] = results[-1]
    else:
        eval_record['results'] = tuple(results)
        eval_record['sim_dir'] = None

    # In multiprocessing, BESOS stores add_outputs in each worker-local problem.
    # Capture the latest computed add_outputs values into the evaluation record.
    def _normalize_add_output_value(value):
        """Convert add-output values to JSON/dataframe-friendly Python objects.

        Parameters
        ----------
        value : Any
            Raw add-output value produced by BESOS.

        Returns
        -------
        Any
            Plain list/scalar representation when conversion is possible.

        Usage
        -----
        Called while building ``eval_record['add_outputs_values']``.

        Examples
        --------
        normalized = _normalize_add_output_value(value)
        """
        # Prefer raw numeric sequences for dataframe/pickle/json portability.
        try:
            data = getattr(value, 'data', None)
            if data is not None:
                if hasattr(data, 'columns') and 'Value' in getattr(data, 'columns', []):
                    return data['Value'].tolist()
                if hasattr(data, 'squeeze'):
                    squeezed = data.squeeze()
                    if hasattr(squeezed, 'tolist'):
                        return squeezed.tolist()
                if hasattr(data, 'tolist'):
                    return data.tolist()
        except Exception:
            pass
        if hasattr(value, 'tolist'):
            try:
                return value.tolist()
            except Exception:
                pass
        return value

    add_outputs_values = []
    try:
        add_outputs_list = getattr(evaluator.problem, 'add_outputs_list', None)
        if add_outputs_list:
            last_record = add_outputs_list[-1]
            n_inputs = len(all_outputs)
            add_outputs_values = [_normalize_add_output_value(v) for v in list(last_record[n_inputs:])]
    except Exception:
        add_outputs_values = []
    eval_record['add_outputs_values'] = tuple(add_outputs_values)

    sim_files_extensions = getattr(evaluator, '_sim_files_extensions', None)
    sim_files_policy = getattr(evaluator, '_sim_files_policy', 'keep')
    if keep_dirs and eval_record.get('sim_dir') is not None and sim_files_extensions is not None:
        try:
            prune_simulation_output_files(
                sim_dir=eval_record['sim_dir'],
                sim_files_extensions=sim_files_extensions,
                sim_files_policy=sim_files_policy,
            )
        except Exception:
            # Never fail optimisation because post-run cleanup failed.
            pass

    if store_records_in_memory:
        evaluator._optimisation_eval_records.append(eval_record)
    log_base = getattr(evaluator, '_optimisation_log_base', None)
    if log_base is not None:

        def _json_safe(value):
            """Recursively convert values into JSON-serializable structures.

            Parameters
            ----------
            value : Any
                Value to serialize into JSON-safe primitives.

            Returns
            -------
            Any
                Converted value containing only JSON-serializable data.

            Usage
            -----
            Used when writing optimisation evaluation logs to JSONL files.

            Examples
            --------
            safe_value = _json_safe(value)
            """
            if isinstance(value, dict):
                return {k: _json_safe(v) for (k, v) in value.items()}
            if isinstance(value, (list, tuple)):
                return [_json_safe(v) for v in value]
            if isinstance(value, os.PathLike):
                return os.fspath(value)
            if hasattr(value, 'item'):
                try:
                    return value.item()
                except (ValueError, TypeError):
                    pass
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            return str(value)
        log_payload = {
            'inputs': _json_safe(list(eval_record['inputs'])),
            'results': _json_safe(list(eval_record['results'])),
            'sim_dir': _json_safe(eval_record['sim_dir']),
            'add_outputs_values': _json_safe(list(eval_record.get('add_outputs_values', ()))),
        }
        log_path = f'{log_base}_{os.getpid()}.jsonl'
        with open(log_path, 'a', encoding='utf-8') as logfile:
            logfile.write(json.dumps(log_payload) + '\n')
    if keep_dirs:
        results = results[:-1]
    keep_sim_files = getattr(evaluator, '_keep_sim_files', 'all')
    if keep_dirs and keep_sim_files == 'non-dominated' and store_records_in_memory:
        records = evaluator._optimisation_eval_records
        if len(records) > 0 and len(records) % getattr(evaluator, '_keep_sim_files_batch_size', 50) == 0:
            import shutil
            import numpy as np
            minimize_flags = getattr(evaluator.problem, 'minimize_outputs', None)
            output_names = evaluator.problem.names('outputs')
            n_outputs = len(output_names)
            if minimize_flags is None:
                minimize_flags = [True] * n_outputs
            else:
                minimize_flags = [m if m is not None else True for m in minimize_flags]
            costs = np.zeros((len(records), n_outputs))
            for (i, rec) in enumerate(records):
                costs[i, :] = rec['results'][:n_outputs]
            for (j, minimize) in enumerate(minimize_flags):
                if not minimize:
                    costs[:, j] = -costs[:, j]
            n = costs.shape[0]
            is_pareto = np.ones(n, dtype=bool)
            for i in range(n):
                if not is_pareto[i]:
                    continue
                others_mask = np.arange(n) != i
                dominated_i = np.all(costs[others_mask] <= costs[i], axis=1) & np.any(costs[others_mask] < costs[i], axis=1)
                if np.any(dominated_i):
                    is_pareto[i] = False
            for i in range(n):
                if not is_pareto[i]:
                    sim_dir = records[i].get('sim_dir')
                    if sim_dir is not None and os.path.exists(sim_dir):
                        try:
                            shutil.rmtree(sim_dir)
                        except Exception:
                            pass
                        records[i]['sim_dir'] = None
    return evaluator.package_for_platypus(results)


def _patched_to_platypus(self):
    """Build a Platypus problem with ACCIM patched evaluation callback.

    Parameters
    ----------
    self : Any
        BESOS evaluator instance exposing ``problem.to_platypus()``.

    Returns
    -------
    Any
        Platypus problem with ``problem.function`` patched to ACCIM evaluator.

    Usage
    -----
    Call this helper after evaluator setup to inject ``_patched_eval_func``.

    Examples
    --------
    problem = _patched_to_platypus(evaluator)
    """
    problem = self.problem.to_platypus()
    problem.function = functools.partial(_patched_eval_func, self)
    return problem