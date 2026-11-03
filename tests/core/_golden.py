"""Golden files: compare an output with a stored copy, or write the copy again.

The golden files are compressed by their suffix: ``.gz`` (gzip, written without a time stamp) or ``.xz``
(lzma, much smaller for texts that repeat themselves, such as the output IDFs of the golden master). Writing
the same content again does not change them. A missing golden file is a failure, not a new golden file.

After an intended change, write them again and review the change before committing them::

    python -m pytest tests/core -q -p no:cacheprovider --update-golden
    git status --short tests/core

(or set the environment variable ``ACCIM_UPDATE_GOLDEN=1``).
"""
import difflib
import gzip
import itertools
import lzma
import re
from pathlib import Path

import pytest

UPDATE_HINT = 'run the tests with --update-golden (or ACCIM_UPDATE_GOLDEN=1) to write it'


def decompress(path, data):
    """Uncompress the bytes ``data`` of the golden file ``path`` (by its suffix)."""
    return lzma.decompress(data) if Path(path).suffix == '.xz' else gzip.decompress(data)


def compress(path, data):
    """Compress ``data`` for the golden file ``path`` (by its suffix)."""
    if Path(path).suffix == '.xz':
        return lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)
    return gzip.compress(data, mtime=0)


def read_golden(path):
    """Return the uncompressed bytes of the golden file ``path``."""
    return decompress(path, Path(path).read_bytes())


def write_golden(path, data):
    """Write ``data`` (bytes) to the golden file ``path``, unless it already holds that content."""
    path = Path(path)
    if path.exists() and read_golden(path) == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compress(path, data))
    return True


def _shift_hunk(line, offset):
    """A hunk header of a unified diff ('@@ -a,b +c,d @@') with its line numbers moved by ``offset``."""
    match = re.match(r'^@@ -(\d+)(,\d+)? \+(\d+)(,\d+)? @@$', line)
    if match is None or offset == 0:
        return line
    old, old_count, new, new_count = match.groups()
    return f'@@ -{int(old) + offset}{old_count or ""} +{int(new) + offset}{new_count or ""} @@'


def text_diff(expected, actual, max_lines=80, from_label='golden', to_label='actual', window=4000):
    """Unified diff of two byte strings, from their first different line, cut after ``max_lines`` lines.

    Only ``window`` lines of each text are compared, from just before their first different line: the complete
    diff of two long texts with changes all along them (the outputs of a configuration of the golden master with
    many output IDFs) takes difflib a very long time, and only its first lines are shown.
    """
    a = expected.decode('utf-8', 'replace').splitlines()
    b = actual.decode('utf-8', 'replace').splitlines()
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    start = max(first - 2, 0)
    lines = difflib.unified_diff(a[start:start + window], b[start:start + window], from_label, to_label, lineterm='',
                                 n=2)
    diff = [_shift_hunk(line, start) for line in itertools.islice(lines, max_lines + 1)]
    if len(diff) > max_lines:
        diff = diff[:max_lines] + ['... (more lines)']
    return '\n'.join(diff)


def check_golden(path, actual, update, what=None, dump=None):
    """Fail unless ``actual`` (bytes) equals the golden file ``path``; with ``update``, write it instead.

    With ``dump`` (a path), a different ``actual`` is also written there, uncompressed, to compare it whole.
    """
    path = Path(path)
    if update:
        write_golden(path, actual)
        return
    what = what or path.name
    if not path.exists():
        pytest.fail(f'The golden file of {what} is missing ({path}): {UPDATE_HINT}.', pytrace=False)
    expected = read_golden(path)
    if actual != expected:
        where = ''
        if dump is not None:
            Path(dump).write_bytes(actual)
            where = f' (the whole output is in {dump})'
        pytest.fail(f'{what} differs from its golden file {path.name}{where}; if the change is intended, '
                    f'{UPDATE_HINT} again.\n{text_diff(expected, actual)}', pytrace=False)
