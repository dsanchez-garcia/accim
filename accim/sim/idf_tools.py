# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Helpers for the eppy IDF objects."""

from io import StringIO
from typing import Iterable, List

__all__ = ['add_program', 'copy_idf', 'idf_text', 'names', 'remove_objects', 'replace_program_lines',
           'set_program_lines', 'try_objects']


def try_objects(idf, object_type: str) -> list:
    """The objects of a type, or an empty list if the IDD of the model does not have that type."""
    try:
        return list(idf.idfobjects[object_type])
    except KeyError:
        return []


def idf_text(idf) -> str:
    """The text of a model, as eppy's ``IDF.idfstr()``."""
    return ''.join(obj.__repr__() for object_type in idf.model.dtls for obj in idf.idfobjects[object_type])


def copy_idf(idf):
    """A copy of a model: an IDF object of the same class read from its text (as eppy's files are re-read)."""
    return type(idf)(StringIO(idf_text(idf)))


def names(idf, object_type: str, field: str = 'Name') -> List[str]:
    """The values of a field (the names, by default) of the objects of a type."""
    return [getattr(obj, field) for obj in idf.idfobjects[object_type]]


def remove_objects(idf, object_type: str) -> None:
    """Remove all the objects of a type."""
    for obj in list(idf.idfobjects[object_type]):
        idf.removeidfobject(obj)


def set_program_lines(program, lines: Iterable[str], first: int = 1) -> None:
    """Set the lines of an EMS program from line number ``first``; eppy adds the fields it needs."""
    for number, line in enumerate(lines, start=first):
        setattr(program, f'Program_Line_{number}', line)


def replace_program_lines(program, lines: Iterable[str], keep: int = 0) -> None:
    """Keep the first ``keep`` lines of an EMS program and replace the others with ``lines``."""
    del program.obj[2 + keep:]
    set_program_lines(program, lines, first=keep + 1)


def add_program(idf, name: str, lines: Iterable[str]):
    """Add an EMS program with its lines."""
    program = idf.newidfobject('EnergyManagementSystem:Program', Name=name)
    set_program_lines(program, lines)
    return program
