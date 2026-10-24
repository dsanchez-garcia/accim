"""Validated, versioned checkpoints. Pickle files must come from trusted sources.

Compatibility fingerprints describe known execution inputs; custom functions
using external files/services/state must declare those dependencies through
``checkpoint_context``. This is integrity checking, not pickle sandboxing.
"""

import functools
import hashlib
import importlib.metadata
import inspect
import json
import marshal
import math
import os
import pickle
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
import pandas as pd

SIGNATURE = '_accim_task_signature'
PARAMETRIC_FORMAT = 'parametric_state_v3'
OPTIMISATION_FORMAT = 'optimisation_state_v2'


class CheckpointError(ValueError):
    """An incomplete or incompatible checkpoint cannot be safely reused."""


def file_digest(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_pickle(payload, path):
    """Publish only a complete pickle; leave the previous checkpoint on failure."""
    path = os.path.abspath(os.fspath(path))
    fd, temporary = tempfile.mkstemp(prefix='.accim-', suffix='.tmp', dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'wb') as stream:
            pickle.dump(payload, stream, protocol=pickle.HIGHEST_PROTOCOL)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_pickle(path):
    try:
        return pd.read_pickle(path)
    except Exception as exc:
        raise CheckpointError(f'Cannot read checkpoint/batch file: {path}. Original data was not overwritten.') from exc


def validate_frame(frame, *, required=(), context='checkpoint', signatures=False, nonempty=False):
    if not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique:
        raise CheckpointError(f'Invalid {context}: expected a DataFrame with unique columns.')
    if nonempty and frame.empty:
        raise CheckpointError(f'Invalid {context}: empty history/result batch.')
    required = list(required) + ([SIGNATURE] if signatures else [])
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise CheckpointError(f'Invalid {context}: missing result columns {missing}.')
    if signatures:
        values = frame[SIGNATURE]
        if not all(isinstance(v, str) and v for v in values) or values.duplicated().any():
            raise CheckpointError(f'Invalid {context}: missing or duplicate task signatures.')
    return frame


def batch_receipt(path, frame=None):
    frame = read_pickle(path) if frame is None else frame
    validate_frame(frame, signatures=True, nonempty=True, context=f'batch {path}')
    return {'sha256': file_digest(path), 'rows': len(frame), 'columns': list(frame.columns)}


def read_batches(paths, receipts=None, required=()):
    frames = []
    for path in paths:
        if not isinstance(path, (str, os.PathLike)):
            raise CheckpointError('Invalid batch path in checkpoint.')
        path = os.path.abspath(os.fspath(path))
        if not os.path.isfile(path):
            raise CheckpointError(f'Checkpoint batch is missing: {path}. Restore it or start a new run.')
        if receipts is not None:
            receipt = receipts.get(path)
            if not isinstance(receipt, dict) or receipt.get('sha256') != file_digest(path):
                raise CheckpointError(f'Checkpoint batch fingerprint mismatch: {path}.')
        frame = validate_frame(read_pickle(path), required=required, signatures=True,
                               nonempty=True, context=f'checkpoint batch {path}')
        if receipts is not None and (receipt.get('rows') != len(frame) or receipt.get('columns') != list(frame.columns)):
            raise CheckpointError(f'Checkpoint batch schema/count mismatch: {path}.')
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=[SIGNATURE, *required])
    return pd.concat(frames, ignore_index=True).drop_duplicates(SIGNATURE, keep='last').reset_index(drop=True)


def _require_format(payload, expected):
    if not isinstance(payload, dict) or payload.get('checkpoint_format') != expected:
        raise CheckpointError(
            f'Unsupported or legacy checkpoint format; expected {expected}. '
            'Legacy checkpoints cannot prove evaluation identity. Keep the old files and '
            'run with resume_from_checkpoint=False in a new output directory.'
        )
    if not isinstance(payload.get('evaluation_identity'), dict):
        raise CheckpointError('Checkpoint has no validated evaluation identity.')


def load_parametric(path):
    payload = read_pickle(path)
    _require_format(payload, PARAMETRIC_FORMAT)
    signatures = payload.get('completed_signatures')
    paths = payload.get('batch_pickles')
    receipts = payload.get('batch_metadata')
    if not isinstance(signatures, list) or not all(isinstance(s, str) and s for s in signatures):
        raise CheckpointError('Invalid completed task signatures in checkpoint.')
    if len(signatures) != len(set(signatures)) or payload.get('completed_tasks') != len(signatures):
        raise CheckpointError('Checkpoint completed task count/signature mismatch.')
    if not isinstance(payload.get('total_tasks'), int) or payload['total_tasks'] < len(signatures):
        raise CheckpointError('Invalid checkpoint total task count.')
    if not isinstance(paths, list) or not isinstance(receipts, dict):
        raise CheckpointError('Invalid checkpoint batch manifest.')
    if not isinstance(payload.get('input_plan'), pd.DataFrame):
        raise CheckpointError('Checkpoint is missing its input plan.')
    if payload.get('input_plan_sha256') != frame_digest(payload['input_plan']):
        raise CheckpointError('Checkpoint input plan fingerprint mismatch.')
    frame = read_batches(paths, receipts)
    if not set(signatures).issubset(set(frame[SIGNATURE])):
        raise CheckpointError('Incomplete checkpoint: completed signatures have no backing result rows.')
    return dict(payload, completed_signatures=set(signatures), legacy_results_df=None)


def save_parametric(path, *, signatures, paths, total_tasks, input_plan, identity, receipts=None):
    if not isinstance(identity, dict):
        raise CheckpointError('A validated evaluation identity is required to save a checkpoint.')
    receipts = {} if receipts is None else receipts
    paths = list(dict.fromkeys(os.path.abspath(os.fspath(p)) for p in paths))
    for path_entry in paths:
        if path_entry not in receipts:
            receipts[path_entry] = batch_receipt(path_entry)
    payload = {
        'checkpoint_format': PARAMETRIC_FORMAT,
        'evaluation_identity': identity,
        'completed_signatures': sorted(signatures),
        'batch_pickles': paths,
        'batch_metadata': {p: receipts[p] for p in paths},
        'completed_tasks': len(signatures), 'total_tasks': int(total_tasks),
        'input_plan': input_plan.copy(),
        'input_plan_sha256': frame_digest(input_plan),
    }
    atomic_pickle(payload, path)
    return len(signatures)


def validate_optimisation_cases(cases, required=()):
    if not isinstance(cases, dict):
        raise CheckpointError('Invalid optimisation checkpoint cases.')
    for case_id, case in cases.items():
        if not isinstance(case_id, str) or not isinstance(case, dict):
            raise CheckpointError('Invalid optimisation checkpoint case.')
        for name, nonempty in [('outputs_full', True), ('outputs_non_dominated', False)]:
            frame = validate_frame(case.get(name), required=required,
                                   nonempty=nonempty, context=f'checkpoint case {case_id} {name}')
            if case.get(name + '_rows') != len(frame) or case.get(name + '_columns') != list(frame.columns):
                raise CheckpointError(f'Checkpoint case history schema/count mismatch: {case_id}.')
            if case.get(name + '_sha256') != frame_digest(frame):
                raise CheckpointError(f'Checkpoint case history fingerprint mismatch: {case_id}.')
        for column in ('idf', 'epw'):
            for name in ('outputs_full', 'outputs_non_dominated'):
                frame = case[name]
                if column not in frame.columns or not frame[column].eq(case.get(column)).all():
                    raise CheckpointError(f'Checkpoint case {case_id} has inconsistent {column} labels.')


def load_optimisation(path):
    payload = read_pickle(path)
    _require_format(payload, OPTIMISATION_FORMAT)
    cases = payload.get('cases')
    validate_optimisation_cases(cases)
    if payload.get('completed_cases') != len(cases) or payload.get('case_count') != len(cases):
        raise CheckpointError('Optimisation checkpoint case count mismatch.')
    if not isinstance(payload.get('total_cases'), int) or payload['total_cases'] < len(cases):
        raise CheckpointError('Invalid optimisation checkpoint total case count.')
    return payload


def save_optimisation(path, *, cases, total_cases, resume_signature, identity):
    if not isinstance(identity, dict):
        raise CheckpointError('A validated evaluation identity is required to save a checkpoint.')
    stored = {}
    for case_id, original in cases.items():
        case = dict(original)
        for name in ('outputs_full', 'outputs_non_dominated'):
            frame = validate_frame(case.get(name), nonempty=name == 'outputs_full', context=f'checkpoint case {case_id}')
            case[name + '_rows'] = len(frame)
            case[name + '_columns'] = list(frame.columns)
            case[name + '_sha256'] = frame_digest(frame)
        stored[case_id] = case
    validate_optimisation_cases(stored)
    payload = {
        'checkpoint_format': OPTIMISATION_FORMAT, 'evaluation_identity': identity,
        'total_cases': int(total_cases), 'completed_cases': len(stored), 'case_count': len(stored),
        'resume_signature': resume_signature, 'cases': stored,
    }
    atomic_pickle(payload, path)
    return len(stored)


def require_same_identity(stored, current):
    if stored != current:
        raise CheckpointError(
            'Incompatible checkpoint evaluation identity/fingerprint: model, weather, problem, '
            'engine, code, declared dependencies or output policy changed. '
            'Keep the checkpoint and start a fresh run in another directory.'
        )


def _code_digest(code):
    """Ignore source locations/debug line tables, not executable constants."""
    constants = tuple(_normalise_code(item) if isinstance(item, types.CodeType) else item for item in code.co_consts)
    return hashlib.sha256(marshal.dumps(_normalise_code(code, constants))).hexdigest()


def _normalise_code(code, constants=None):
    if constants is None:
        constants = tuple(_normalise_code(item) if isinstance(item, types.CodeType) else item for item in code.co_consts)
    changes = {'co_filename': '', 'co_firstlineno': 1, 'co_consts': constants}
    changes['co_linetable' if hasattr(code, 'co_linetable') else 'co_lnotab'] = b''
    return code.replace(**changes)


class Fingerprint:
    """Canonical descriptions, without repr/address-based fallback for objects."""

    def __init__(self):
        self.files = {}
        self.active = set()

    def file(self, path):
        path = os.path.abspath(os.fspath(path))
        if path not in self.files:
            if not os.path.isfile(path):
                raise CheckpointError(f'Cannot fingerprint required input file: {path}')
            self.files[path] = {'sha256': file_digest(path), 'size': os.path.getsize(path)}
        return self.files[path]

    def reference(self, value):
        result = {'name': f'{value.__module__}.{value.__qualname__}'}
        module = sys.modules.get(value.__module__)
        path = getattr(module, '__file__', None)
        if path and os.path.isfile(path):
            result['module_file'] = self.file(path)
        return result

    def value(self, value):
        if value is pd.NA or value is pd.NaT:
            return {'missing': type(value).__name__}
        if isinstance(value, pd.Timestamp):
            return {'timestamp': value.isoformat()}
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, np.generic):
            return self.value(value.item())
        if isinstance(value, float):
            return value if math.isfinite(value) else {'float': str(value)}
        if isinstance(value, bytes):
            return {'bytes': hashlib.sha256(value).hexdigest()}
        if isinstance(value, os.PathLike):
            return {'file': self.file(value)}
        if inspect.isclass(value):
            return {'class': self.reference(value)}
        if isinstance(value, types.ModuleType):
            path = getattr(value, '__file__', None)
            result = {'module': value.__name__, 'version': getattr(value, '__version__', None)}
            if path and os.path.isfile(path):
                result['file'] = self.file(path)
            return result
        if id(value) in self.active:
            if inspect.isfunction(value):
                return {'recursive_function': self.reference(value), 'code': _code_digest(value.__code__)}
            raise CheckpointError('Cannot fingerprint cyclic/external callable state; use a simpler explicit evaluation specification.')
        self.active.add(id(value))
        try:
            if isinstance(value, dict):
                return {'mapping': sorted([[self.value(k), self.value(v)] for k, v in value.items()], key=lambda pair: json.dumps(pair[0], sort_keys=True))}
            if isinstance(value, (tuple, list)):
                return {type(value).__name__: [self.value(item) for item in value]}
            if isinstance(value, (set, frozenset)):
                return {'set': sorted([self.value(item) for item in value], key=lambda item: json.dumps(item, sort_keys=True))}
            if isinstance(value, np.ndarray):
                return {'array': self.value(value.tolist()), 'dtype': str(value.dtype)}
            if isinstance(value, functools.partial):
                return {'partial': self.value(value.func), 'args': self.value(value.args), 'kwargs': self.value(value.keywords)}
            if inspect.ismethod(value):
                return {'method': self.value(value.__func__), 'instance': self.value(value.__self__)}
            if inspect.isfunction(value):
                closure = inspect.getclosurevars(value)
                globals_used = {name: self.value(item) for name, item in closure.globals.items()}
                return {'function': self.reference(value),
                        'code': _code_digest(value.__code__),
                        'defaults': self.value(value.__defaults__), 'kwdefaults': self.value(value.__kwdefaults__),
                        'closure': self.value(closure.nonlocals), 'globals': globals_used}
            if inspect.isbuiltin(value):
                return {'builtin': self.reference(value)}
            if hasattr(value, '__dict__'):
                state = {key: item for key, item in vars(value).items() if key != '_to_repr'}
                for base in type(value).__mro__:
                    slots = getattr(base, '__slots__', ())
                    slots = (slots,) if isinstance(slots, str) else slots
                    for slot in slots:
                        if slot not in {'__dict__', '__weakref__'} and hasattr(value, slot):
                            state[slot] = getattr(value, slot)
                description = {'object': self.reference(type(value)), 'state': self.value(state)}
                if callable(value):
                    call = getattr(type(value), '__call__', None)
                    if not inspect.isfunction(call):
                        raise CheckpointError('Unsupported callable checkpoint identity; use a Python function or supported reader.')
                    description['call'] = self.value(call)
                return description
        finally:
            self.active.remove(id(value))
        raise CheckpointError(f'Unsupported checkpoint identity value: {type(value).__name__}. Use a supported reader/selector or disable checkpointing.')


def frame_digest(frame):
    data = {'columns': list(frame.columns), 'dtypes': [str(t) for t in frame.dtypes],
            'rows': frame.to_numpy().tolist()}
    canonical = Fingerprint().value(data)
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode('utf-8')).hexdigest()


def evaluation_identity(simulation, *, models, epws, options, context=None):
    """Hash the prepared snapshots and effective BESOS problem once per run."""
    from besos import config
    from besos.eplus_funcs import get_ep_path, get_idf_version_pth

    identity = Fingerprint()
    if not models:
        raise CheckpointError('Checkpointing requires prepared IDF snapshots; no model identity is available.')
    model_inputs = {}
    engines = {}
    for name, path in sorted(models.items()):
        model_inputs[name] = identity.file(path)
        version = get_idf_version_pth(path)
        if version not in engines:
            try:
                executable, home = get_ep_path(version)
            except Exception as exc:
                raise CheckpointError(f'Cannot resolve checkpoint EnergyPlus identity for version {version}.') from exc
            engine_files = [executable, os.path.join(home, 'Energy+.idd')]
            for library in ('EnergyPlusAPI.dll', 'libenergyplusapi.so', 'libenergyplusapi.dylib', 'ExpandObjects.exe', 'ExpandObjects'):
                if os.path.isfile(os.path.join(home, library)):
                    engine_files.append(os.path.join(home, library))
            engines[version] = {os.path.basename(p): identity.file(p) for p in engine_files}
    problem = simulation.problem
    parameters = getattr(problem, 'parameters', getattr(simulation, 'parameters_list', []))
    specification = {
        'parameters': parameters, 'outputs': getattr(problem, 'outputs', None),
        'worker_outputs': simulation._serialize_problem_outputs(),
        'additional_outputs': getattr(problem, 'add_outputs', []),
        'directions': getattr(problem, 'minimize_outputs', None),
        'constraints': getattr(problem, 'constraints', []),
        'bounds': getattr(problem, 'constraint_bounds', []),
        'converters': getattr(problem, 'converters', None),
        'input_names': problem.names('inputs'), 'output_names': problem.names('outputs'),
        'constraint_names': problem.names('constraints'),
        'default_output_frequency': getattr(config, 'frequency', None),
    }
    library_root = Path(__file__).resolve().parents[1]
    code = {str(path.relative_to(library_root)): identity.file(path)
            for path in sorted(library_root.rglob('*.py'))
            if not {'sample_files', 'misc', '__pycache__'}.intersection(path.relative_to(library_root).parts)}
    packages = {}
    for package in ('besos', 'eppy', 'numpy', 'pandas', 'platypus-opt'):
        packages[package] = importlib.metadata.version(package)
    external_files = {}
    for building in getattr(simulation, 'buildings', []):
        for object_type, objects in getattr(building, 'idfobjects', {}).items():
            if objects and str(object_type).upper().startswith('PYTHONPLUGIN:') and not context:
                raise CheckpointError('PythonPlugin checkpointing requires checkpoint_context declaring its code/data dependencies.')
            for obj in objects:
                for field in getattr(obj, 'fieldnames', []):
                    if field in {'File_Name', 'External_File_Name', 'FMU_File_Name'}:
                        value = getattr(obj, field, '')
                        if value:
                            external_files[os.path.abspath(str(value))] = identity.file(str(value))
    definition = {'models': model_inputs, 'weather': {os.path.abspath(os.fspath(epw)): identity.file(epw) for epw in sorted(set(epws))},
                  'engines': engines, 'problem': identity.value(specification),
                  'options': identity.value(options), 'context': identity.value(context),
                  'external_files': external_files,
                  'implementation': code, 'packages': packages, 'python': list(sys.version_info[:3])}
    digest = hashlib.sha256(json.dumps(definition, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
    return {'schema': 1, 'sha256': digest, 'definition': definition}





