"""Utilities to normalize and apply simulation output cleanup policies.

This module centralizes extension-policy validation used by parametric and
optimisation workflows to prune temporary simulation files safely.

Usage
-----
Use ``normalize_sim_file_cleanup_options`` when validating user arguments and
``prune_simulation_output_files`` to apply the cleanup at the end of a run.

Examples
--------
extensions, policy = normalize_sim_file_cleanup_options(['csv', '.err'], 'keep')
stats = prune_simulation_output_files('path/to/sim', extensions, policy)
"""

import os
from typing import Literal, Optional, Sequence, Union

SimFilePolicy = Literal['keep', 'delete']


def _normalise_extension_token(token: str, argument_name: str) -> str:
    """Normalize one extension token to a lowercase ``.ext`` format.

    Parameters
    ----------
    token : str
        Raw extension token provided by the caller (for example ``csv`` or
        ``*.err``).
    argument_name : str
        Argument name used to build precise validation error messages.

    Returns
    -------
    str
        Normalized extension in lowercase dot-prefixed format.

    Usage
    -----
    Called by higher-level validators before comparing extension sets.

    Examples
    --------
    ext = _normalise_extension_token('*.ERR', argument_name='sim_files_extensions')
    """
    value = str(token).strip().lower()
    if len(value) == 0:
        raise ValueError(f"Argument '{argument_name}' contains an empty extension value.")

    if value.startswith('*.'):
        value = value[1:]

    if value.startswith('*') and len(value) > 1:
        value = value[1:]

    if not value.startswith('.'):
        value = f'.{value}'

    if value == '.':
        raise ValueError(f"Argument '{argument_name}' contains an invalid extension value: {token!r}")

    return value


def _normalise_extensions_list(
    sim_files_extensions: Union[str, Sequence[str]],
    argument_name: str,
) -> tuple[str, ...]:
    """Normalize and deduplicate extension collections.

    Parameters
    ----------
    sim_files_extensions : Union[str, Sequence[str]]
        One extension token or a sequence of extension tokens.
    argument_name : str
        Argument name used for error reporting.

    Returns
    -------
    tuple[str, ...]
        Sorted tuple of unique normalized extensions.

    Usage
    -----
    Used by cleanup-option parsing before policy logic is evaluated.

    Examples
    --------
    exts = _normalise_extensions_list(['csv', '.err', '*.csv'], 'sim_files_extensions')
    """
    if isinstance(sim_files_extensions, str):
        raw_values = [sim_files_extensions]
    elif isinstance(sim_files_extensions, Sequence):
        raw_values = list(sim_files_extensions)
    else:
        raise TypeError(
            f"Argument '{argument_name}' must be a string or a sequence of strings. "
            f"Got: {type(sim_files_extensions).__name__}."
        )

    if len(raw_values) == 0:
        raise ValueError(f"Argument '{argument_name}' cannot be an empty sequence.")

    normalised = []
    seen = set()
    for value in raw_values:
        if not isinstance(value, str):
            raise TypeError(
                f"Argument '{argument_name}' must contain only strings. "
                f"Found: {type(value).__name__}."
            )
        extension = _normalise_extension_token(value, argument_name=argument_name)
        if extension not in seen:
            seen.add(extension)
            normalised.append(extension)

    if len(normalised) == 0:
        raise ValueError(f"Argument '{argument_name}' does not contain valid extension values.")

    return tuple(sorted(normalised))


def _normalise_policy(sim_files_policy: str, argument_name: str = 'sim_files_policy') -> SimFilePolicy:
    """Validate and normalize the file cleanup policy token.

    Parameters
    ----------
    sim_files_policy : str
        Requested cleanup policy. Valid values are ``'keep'`` and ``'delete'``.
    argument_name : str
        Argument name used in validation errors.

    Returns
    -------
    SimFilePolicy
        Normalized cleanup policy.

    Usage
    -----
    Called before cleanup evaluation to guarantee policy consistency.

    Examples
    --------
    policy = _normalise_policy('KEEP')
    """
    policy = str(sim_files_policy).strip().lower()
    if policy not in {'keep', 'delete'}:
        raise ValueError(
            f"Invalid {argument_name}={sim_files_policy!r}. Valid values are: ['delete', 'keep']."
        )
    return policy  # type: ignore[return-value]


def normalize_sim_file_cleanup_options(
    sim_files_extensions: Optional[Union[str, Sequence[str]]] = None,
    sim_files_policy: str = 'keep',
) -> tuple[Optional[tuple[str, ...]], SimFilePolicy]:
    """Validate and normalize simulation file cleanup options.

    Parameters
    ----------
    sim_files_extensions : Optional[Union[str, Sequence[str]]]
        Extensions used by cleanup logic. If ``None``, cleanup is disabled.
    sim_files_policy : str
        Cleanup policy. ``'keep'`` means keep listed extensions and delete the
        rest; ``'delete'`` means delete only listed extensions.

    Returns
    -------
    tuple[Optional[tuple[str, ...]], SimFilePolicy]
        Pair ``(extensions, policy)`` where ``extensions`` is ``None`` when no
        cleanup should be applied.

    Usage
    -----
    Call this function once after reading user options and pass the normalized
    output to cleanup utilities.

    Examples
    --------
    extensions, policy = normalize_sim_file_cleanup_options(['csv', '.err'], 'delete')
    """
    policy = _normalise_policy(sim_files_policy)
    if sim_files_extensions is None:
        return None, policy

    extensions = _normalise_extensions_list(
        sim_files_extensions=sim_files_extensions,
        argument_name='sim_files_extensions',
    )
    return extensions, policy


def sim_file_policy_will_remove_extension(
    sim_files_extensions: Optional[Union[str, Sequence[str]]],
    sim_files_policy: str,
    extension: str,
) -> bool:
    """Check whether a cleanup configuration removes a specific extension.

    Parameters
    ----------
    sim_files_extensions : Optional[Union[str, Sequence[str]]]
        Extension configuration passed by the caller.
    sim_files_policy : str
        Cleanup policy token (``'keep'`` or ``'delete'``).
    extension : str
        Extension to test against the configured policy.

    Returns
    -------
    bool
        ``True`` when files with ``extension`` would be removed.

    Usage
    -----
    Use this helper to decide whether specific file products are expected to be
    deleted before running cleanup.

    Examples
    --------
    remove_err = sim_file_policy_will_remove_extension(['csv'], 'keep', '.err')
    """
    extensions, policy = normalize_sim_file_cleanup_options(
        sim_files_extensions=sim_files_extensions,
        sim_files_policy=sim_files_policy,
    )
    if extensions is None:
        return False

    normalised_extension = _normalise_extension_token(extension, argument_name='extension')
    if policy == 'keep':
        return normalised_extension not in set(extensions)
    return normalised_extension in set(extensions)


def prune_simulation_output_files(
    sim_dir: Union[str, os.PathLike],
    sim_files_extensions: Optional[Union[str, Sequence[str]]],
    sim_files_policy: str = 'keep',
) -> dict:
    """Remove files in ``sim_dir`` according to an extension policy.

    Parameters
    ----------
    sim_dir : Union[str, os.PathLike]
        Root simulation directory to scan recursively.
    sim_files_extensions : Optional[Union[str, Sequence[str]]]
        Extension list used by policy logic. If ``None``, no cleanup is applied.
    sim_files_policy : str
        Cleanup policy. ``'keep'`` keeps listed extensions and removes others;
        ``'delete'`` removes only listed extensions.

    Returns
    -------
    dict
        Cleanup statistics with keys ``processed``, ``scanned_files``,
        ``removed_files``, ``remove_errors``, and ``removed_empty_dirs``.

    Usage
    -----
    Call this function after simulations finish to remove transient files and
    then persist the returned stats for logging.

    Examples
    --------
    stats = prune_simulation_output_files('sim/run_01', ['csv', '.err'], 'delete')
    """
    result = {
        'processed': False,
        'scanned_files': 0,
        'removed_files': 0,
        'remove_errors': 0,
        'removed_empty_dirs': 0,
    }

    extensions, policy = normalize_sim_file_cleanup_options(
        sim_files_extensions=sim_files_extensions,
        sim_files_policy=sim_files_policy,
    )
    if extensions is None:
        return result

    dir_path = os.path.abspath(os.fspath(sim_dir))
    if not os.path.isdir(dir_path):
        return result

    extensions_set = set(extensions)
    result['processed'] = True

    for root, _, files in os.walk(dir_path):
        for filename in files:
            result['scanned_files'] += 1
            file_extension = os.path.splitext(filename)[1].lower()
            should_remove = (
                file_extension not in extensions_set if policy == 'keep'
                else file_extension in extensions_set
            )
            if not should_remove:
                continue

            file_path = os.path.join(root, filename)
            try:
                os.remove(file_path)
                result['removed_files'] += 1
            except OSError:
                result['remove_errors'] += 1

    for root, dirs, _ in os.walk(dir_path, topdown=False):
        for dirname in dirs:
            subdir_path = os.path.join(root, dirname)
            try:
                if len(os.listdir(subdir_path)) == 0:
                    os.rmdir(subdir_path)
                    result['removed_empty_dirs'] += 1
            except OSError:
                continue

    return result

