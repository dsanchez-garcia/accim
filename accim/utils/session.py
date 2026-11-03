# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Sessions of accim saved in files, to resume them later: the tables of
:class:`accim.data.postprocessing.main.Table`, the lists of files, the arguments or any other objects of a script or a
notebook.

:func:`save_session` writes two files:

- a pickle file (``.pkl``) with the objects, which :func:`load_session` reads in a new session (for instance, after
  restarting the kernel of a notebook), so that the tables do not have to be made again from the CSV files of the
  simulations;
- a JSON file (``.json``), a copy that people and other programs can read: the version of accim, the date, the
  working folder and each object with its type (the tables of ``Table`` with their arguments, zones, variables and
  rows, the DataFrames with their number of rows and their first rows...). It is not read back.

:meth:`Table.save <accim.data.postprocessing.main.Table.save>` and
:meth:`Table.load <accim.data.postprocessing.main.Table.load>` do the same with one table, and the graphical user
interface (:mod:`accim.gui`) saves its sessions with :func:`save_session`.

Pickle files can run code when they are read: open only the files that you or someone you trust saved. They also need
a version of pandas that can read the objects of the version that saved them; the JSON files do not.
"""

import datetime
import json
import math
import os
import pickle
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, Union

import numpy as np
import pandas as pd

__all__ = [
    'load_session',
    'save_session',
]

PathType = Union[str, os.PathLike]

#: The version of the format of the pickle files of save_session (the key 'accim_session' of their content)
_SESSION_FORMAT = 1
#: The extensions of the two files of a session
_EXTENSIONS = ('.pkl', '.json')


def _file_paths(filename: PathType) -> Tuple[str, str]:
    """The absolute paths of the pickle and JSON files of a name, given with or without one of their extensions."""
    base = os.fspath(filename)
    root, extension = os.path.splitext(base)
    if extension.lower() in _EXTENSIONS:
        base = root
    if not os.path.basename(base).strip():
        raise ValueError(f'filename: {os.fspath(filename)!r} has no name for the files.')
    return os.path.abspath(base + '.pkl'), os.path.abspath(base + '.json')


def _pickle_file(pickle_path: PathType) -> str:
    """The pickle file to read: the path, or the path with ``.pkl`` if it has no extension."""
    path = os.fspath(pickle_path)
    if path.lower().endswith('.json'):
        raise ValueError(f'{path} is the JSON file, which is only for reading: open the pickle file, '
                         f'{path[:-len(".json")]}.pkl.')
    if not os.path.isfile(path) and os.path.isfile(path + '.pkl'):
        path += '.pkl'
    if not os.path.isfile(path):
        also = '' if path.lower().endswith('.pkl') else f' nor {path}.pkl'
        raise FileNotFoundError(f'There is no file {path}{also}.')
    return path


def _read_pickle(pickle_path: PathType) -> Tuple[Any, str]:
    """The object of a pickle file of this module, and the path of the file."""
    path = _pickle_file(pickle_path)
    return pd.read_pickle(path), path


def _metadata() -> Dict[str, Any]:
    """The version of accim, the date and the working folder of a file saved now."""
    from accim import __version__

    return {'accim_version': __version__,
            'saved': datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
            'folder': os.getcwd()}


def _write_through_temporary_file(path: str, write: Callable[[str], None]) -> None:
    """Write a file through a temporary one, so that a failure does not leave half a file (nor replace a former one)."""
    temporary = f'{path}.tmp'
    try:
        write(temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def _check_picklable(objects: Mapping[str, Any], error: Exception) -> None:
    """Raise an error that names the object that pickle cannot save (``error`` is that of the whole content)."""
    for name, value in objects.items():
        try:
            pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as object_error:  # noqa: BLE001 (pickle raises several types)
            raise TypeError(f'The object {name!r} ({type(value).__name__}) cannot be saved in a pickle file: '
                            f'{object_error}') from object_error
    raise error


def _check_json_max_rows(json_max_rows: Optional[int]) -> None:
    if json_max_rows is not None and (isinstance(json_max_rows, bool) or not isinstance(json_max_rows, int)
                                      or json_max_rows < 0):
        raise ValueError(f'json_max_rows: {json_max_rows!r} is not a number of rows (a whole number, 0 or more) or '
                         f'None (all the rows).')


def _rows_note(json_max_rows: Optional[int]) -> str:
    """What the JSON file shows of each table, for its description."""
    if json_max_rows is None:
        return 'Each table (DataFrame) shows all its rows.'
    return (f'Each table (DataFrame) shows its number of rows and the values of the first {json_max_rows} of them '
            f'(the pickle file has all of them).')


def _save_files(content: Any, readable: Union[Mapping[str, Any], Callable[[], Mapping[str, Any]]],
                filename: PathType, objects: Mapping[str, Any]) -> Tuple[str, str]:
    """Save ``content`` in the pickle file, and then ``readable`` (with the types of JSON, or a function that gives it)
    in the JSON file, so that the pickle file, which resumes the session, is saved even if the JSON file fails.

    :param objects: The objects of the content by name, to tell which one pickle cannot save.
    :return: The paths of the two files.
    """
    pickle_path, json_path = _file_paths(filename)

    def write_pickle(path: str) -> None:
        try:
            pd.to_pickle(content, path, compression=None, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as error:  # noqa: BLE001 (pickle raises several types)
            _check_picklable(objects, error)

    _write_through_temporary_file(pickle_path, write_pickle)
    try:
        # allow_nan=False: _json_value replaces the values that are not valid in JSON (NaN, infinity)
        text = json.dumps(readable() if callable(readable) else readable, indent=2, ensure_ascii=False,
                          allow_nan=False)

        def write_json(path: str) -> None:
            with open(path, 'w', encoding='utf-8', newline='\n') as handle:
                handle.write(text + '\n')

        _write_through_temporary_file(json_path, write_json)
    except Exception as error:  # noqa: BLE001 (the pickle file is saved: say so)
        raise RuntimeError(f'The pickle file {pickle_path} has been saved, but not the JSON file {json_path}: '
                           f'{error}') from error
    return pickle_path, json_path


# Values in JSON ------------------------------------------------------------------------------------------------------

def _json_float(value: float) -> Union[float, str, None]:
    """A float in JSON, which has no NaN or infinity: NaN gives null, and infinity the text 'Infinity'."""
    if math.isfinite(value):
        return float(value)
    if math.isnan(value):
        return None
    return 'Infinity' if value > 0 else '-Infinity'


def _json_key(key: Any) -> str:
    """A key of a JSON object (a text); the keys of several levels, such as columns, are joined with '['."""
    if isinstance(key, str):
        return key
    if isinstance(key, tuple):
        return '['.join(str(part) for part in key if str(part) != '')
    value = _json_value(key)
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _json_values(values: Union[pd.Series, pd.Index]) -> List[Any]:
    """The values of a column or an index, with the types of JSON."""
    dtype = values.dtype
    if pd.api.types.is_datetime64_any_dtype(dtype) or pd.api.types.is_timedelta64_dtype(dtype) \
            or isinstance(dtype, pd.PeriodDtype):
        return [None if pd.isna(value) else str(value) for value in values]
    # The numbers of numpy (the nullable types of pandas can have pd.NA, which the general case below takes)
    if isinstance(dtype, np.dtype) and dtype.kind == 'f':
        return [value if math.isfinite(value) else _json_float(value) for value in values.tolist()]
    if isinstance(dtype, np.dtype) and dtype.kind in 'biu':
        return values.tolist()
    return [_json_value(value) for value in values.tolist()]


def _add_column(data: Dict[str, List[Any]], name: str, values: List[Any]) -> None:
    """Add a column to the columns of a DataFrame in JSON, with a number after its name if another has it."""
    unique, number = name, 1
    while unique in data:
        number += 1
        unique = f'{name} ({number})'
    data[unique] = values


def _default_index(index: pd.Index) -> bool:
    """Whether an index is the default one of pandas: the row numbers 0, 1, 2..., without a name."""
    return isinstance(index, pd.RangeIndex) and index.name is None and index.start == 0 and index.step == 1


def _frame_json(df: pd.DataFrame, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """A DataFrame in JSON: its number of rows, the number of rows shown (the first ``max_rows``, or all of them if
    None) and their data, as their columns with their values (``{column: [values]}``, as the results of the parametric
    module): first the levels of its index, unless it is the default one (the row numbers), named as ``reset_index``
    names them, and the names of the columns of several levels joined with '['."""
    shown = df if max_rows is None else df.head(max_rows)
    data: Dict[str, List[Any]] = {}
    index = shown.index
    if not _default_index(index):
        for level, name in enumerate(index.names):
            default = 'index' if index.nlevels == 1 else f'level_{level}'
            _add_column(data, _json_key(name if name is not None else default),
                        _json_values(index.get_level_values(level)))
    for position, column in enumerate(shown.columns):
        _add_column(data, _json_key(column), _json_values(shown.iloc[:, position]))
    return {'number_of_rows': len(df), 'rows_shown': len(shown), 'data': data}


def _series_json(series: pd.Series, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """A Series in JSON, as a DataFrame (:func:`_frame_json`): its values, by index if it is unique and not the
    default one."""
    shown = series if max_rows is None else series.head(max_rows)
    if _default_index(series.index) or not series.index.is_unique:
        data: Any = _json_values(shown)
    else:
        data = dict(zip([_json_key(key) for key in shown.index], _json_values(shown)))
    return {'number_of_rows': len(series), 'rows_shown': len(shown), 'data': data}


def _json_value(value: Any, max_rows: Optional[int] = None) -> Any:
    """A value with the types of JSON only, to read it: the tables of Table give the attributes that their JSON file
    shows, the DataFrames and the Series their number of rows and the values of the first ``max_rows`` rows (all if
    None), the numbers of numpy are numbers, the dates are texts, and the other objects their representation
    (``repr``)."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return _json_float(value)
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (np.datetime64, np.timedelta64)):
        return None if np.isnat(value) else str(value)
    if isinstance(value, np.generic):
        return _json_value(value.item())
    json_content = getattr(type(value), '_json_content', None)
    if callable(json_content):
        return _json_value(value._json_content(), max_rows)
    if isinstance(value, pd.DataFrame):
        return _frame_json(value, max_rows)
    if isinstance(value, pd.Series):
        return _series_json(value, max_rows)
    if isinstance(value, pd.Index):
        return _json_values(value)
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist(), max_rows)
    if isinstance(value, Mapping):
        return {_json_key(key): _json_value(item, max_rows) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [_json_value(item, max_rows) for item in sorted(value, key=repr)]
    if isinstance(value, (list, tuple)):
        return [_json_value(item, max_rows) for item in value]
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    return repr(value)


# Sessions ------------------------------------------------------------------------------------------------------------

def save_session(filename: PathType, /, *, json_max_rows: Optional[int] = 1000, **objects: Any) -> Tuple[str, str]:
    """Save objects of a session in a pickle file, to resume the session with :func:`load_session`, and in a JSON file,
    to read them. For instance, in a notebook, once the tables of the results are made::

        from accim.utils import save_session
        save_session('case_study', dataset_runperiod=dataset_runperiod, dataset_hourly=dataset_hourly, csvs=csvs)

    writes ``case_study.pkl`` and ``case_study.json`` in the working folder. The JSON file has the version of accim,
    the date, the working folder and each object with its type: the tables of ``Table`` with their arguments, zones,
    variables and rows (see :meth:`Table.save <accim.data.postprocessing.main.Table.save>`), the DataFrames with their
    number of rows and the values of their first rows (``{'number_of_rows': ..., 'rows_shown': ..., 'data': {column:
    [values]}}``), and the lists, dictionaries, texts and numbers as they are.

    :param filename: The name of the two files, without extension (``.pkl`` or ``.json`` are left out), in the working
        folder or with a path. Existing files with these names are replaced.
    :param json_max_rows: The number of rows of each table (DataFrame or Series, also those of the tables of ``Table``)
        that the JSON file shows: hourly tables of many simulations have hundreds of thousands, which would make the
        JSON file large and slow to write. None shows all of them. The pickle file always has all of them.
    :param objects: The objects to save, as keyword arguments: :func:`load_session` gives them back with these names
        (any name but ``json_max_rows``). Anything that pickle can save: tables of ``Table``, DataFrames, lists,
        dictionaries, texts, numbers... (not, for instance, functions defined in the session or open files).
    :return: The paths of the pickle file and of the JSON file.
    :raises ValueError: If no object is given, or ``json_max_rows`` is not a number of rows.
    :raises TypeError: If pickle cannot save an object (the message gives its name); then no file is written.
    :raises RuntimeError: If the JSON file cannot be written (the pickle file is saved first).
    """
    if not objects:
        raise ValueError("Give the objects to save as keyword arguments, with their names: for instance, "
                         "save_session('my_session', table=table, csvs=csvs).")
    _check_json_max_rows(json_max_rows)
    metadata = _metadata()
    content = {'accim_session': _SESSION_FORMAT, **metadata, 'objects': dict(objects)}
    pickle_name = os.path.basename(_file_paths(filename)[0])

    def readable() -> Dict[str, Any]:
        return {
            'description': f'Session of accim: a readable copy of the objects of the pickle file {pickle_name}, which '
                           f'accim.utils.load_session reads to resume the session (this file is not read back). '
                           f'{_rows_note(json_max_rows)}',
            **metadata,
            'objects': {name: {'type': type(value).__name__, 'value': _json_value(value, json_max_rows)}
                        for name, value in objects.items()},
        }

    pickle_path, json_path = _save_files(content, readable, filename, objects)
    print(f'The session has been saved in {pickle_path} (load_session resumes it) and in {json_path} (to read it).')
    return pickle_path, json_path


def _describe(objects: Mapping[str, Any]) -> str:
    return ', '.join(f'{name} ({type(value).__name__})' for name, value in objects.items())


def load_session(pickle_path: PathType) -> Dict[str, Any]:
    """The objects of a session saved with :func:`save_session`, to resume it::

        from accim.utils import load_session
        session = load_session('case_study.pkl')
        dataset_runperiod = session['dataset_runperiod']

    (``globals().update(session)`` gives them all back as variables of the script or the notebook). It prints when,
    with which version of accim and in which folder the session was saved, and its objects.

    Open only the files that you or someone you trust saved: pickle files can run code when they are read.

    :param pickle_path: The path of the pickle file (the extension ``.pkl`` can be left out).
    :return: The objects, by name (a dictionary).
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If it is the JSON file, or a file that :func:`save_session` did not save (for instance, a table
        saved with ``Table.save``, which ``Table.load`` reads).
    """
    content, path = _read_pickle(pickle_path)
    if not (isinstance(content, dict) and 'accim_session' in content and isinstance(content.get('objects'), dict)):
        hint = (' It is a table saved with Table.save: open it with Table.load (in the graphical user interface, with '
                '"Open a table..." in the tab "6. Table and figures").' if type(content).__name__ == 'Table' else '')
        raise ValueError(f'{path} is not a session saved with save_session.{hint}')
    objects = dict(content['objects'])
    print(f'The session saved on {content.get("saved")} with accim {content.get("accim_version")} in '
          f'{content.get("folder")} has been loaded from {path}: {_describe(objects)}.')
    return objects
