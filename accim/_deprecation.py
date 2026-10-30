# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Support for the names that accim 1.0.0 renamed to follow PEP 8.

The old names of functions, classes and arguments keep working, with a ``DeprecationWarning``
that gives the new name.
"""

import functools
import warnings
from typing import Callable, Dict, Mapping, Optional

__all__ = ['accepts_legacy_kwargs', 'deprecated_alias', 'rename_legacy_kwargs', 'warn_deprecated']


def warn_deprecated(old: str, new: str, stacklevel: int = 3) -> None:
    """Warn that ``old`` is deprecated in favour of ``new``."""
    warnings.warn(
        f'{old} is deprecated since accim 1.0.0 and will be removed in a future version; use {new} instead.',
        DeprecationWarning,
        stacklevel=stacklevel,
    )


def rename_legacy_kwargs(
    kwargs: Mapping,
    mapping: Mapping[str, str],
    function_name: str,
    stacklevel: int = 3,
) -> Dict:
    """Return the keyword arguments with the legacy names replaced by the new ones.

    :param kwargs: The keyword arguments received.
    :param mapping: The new name of each legacy argument.
    :param function_name: The name of the function, for the messages.
    :param stacklevel: The stack level of the warning (the caller of the public function).
    :raises TypeError: If an argument is given with both its legacy and its new name.
    """
    renamed = {}
    legacy = []
    for key, value in kwargs.items():
        new = mapping.get(key)
        if new is None:
            renamed[key] = value
            continue
        if new in kwargs:
            raise TypeError(f'{function_name}() got the argument {new!r} twice (as {key!r} and as {new!r}).')
        renamed[new] = value
        legacy.append(f'{key} -> {new}')
    if legacy:
        warnings.warn(
            f'The argument names {", ".join(k.split(" ")[0] for k in legacy)} of {function_name}() are deprecated '
            f'since accim 1.0.0; use the new names ({"; ".join(legacy)}).',
            DeprecationWarning,
            stacklevel=stacklevel,
        )
    return renamed


def deprecated_alias(
    new_callable: Callable,
    old_name: str,
    new_name: str,
    legacy_kwargs: Optional[Mapping[str, str]] = None,
) -> Callable:
    """Make a deprecated alias of a function or class.

    :param new_callable: The function or class that replaces the old one.
    :param old_name: The old name (shown in the warning).
    :param new_name: The new name (shown in the warning).
    :param legacy_kwargs: The new name of each legacy keyword argument of the old function.
    """
    @functools.wraps(new_callable)
    def alias(*args, **kwargs):
        warn_deprecated(old_name, new_name)
        if legacy_kwargs:
            kwargs = rename_legacy_kwargs(kwargs, legacy_kwargs, old_name.split('.')[-1])
        return new_callable(*args, **kwargs)

    alias.__name__ = old_name.split('.')[-1].rstrip('()')
    alias.__qualname__ = alias.__name__
    alias.__doc__ = f'Deprecated alias of :func:`{new_name}` (accim 1.0.0).'
    return alias


def accepts_legacy_kwargs(mapping: Mapping[str, str]) -> Callable:
    """Decorator: the function also accepts the old names of its keyword arguments, with a DeprecationWarning.

    :param mapping: The new name of each old keyword argument.
    """
    def decorator(function: Callable) -> Callable:
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            if any(key in mapping for key in kwargs):
                kwargs = rename_legacy_kwargs(kwargs, mapping, function.__name__)
            return function(*args, **kwargs)
        return wrapper
    return decorator
