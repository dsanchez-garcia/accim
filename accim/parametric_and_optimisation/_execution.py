"""Run-owned directories and crash-released interprocess checkpoint locks."""

import functools
import inspect
import os
import shutil
import stat
import tempfile
from contextlib import contextmanager, ExitStack


def is_link(path):
    """Include Windows junctions, which os.walk may otherwise traverse."""
    try:
        info = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    )


def owns_path(path, root):
    """Require lexical and physical containment, without nested reparse points."""
    if not root or not isinstance(path, (str, os.PathLike)):
        return False
    path = os.path.abspath(os.fspath(path))
    root = os.path.abspath(os.fspath(root))
    try:
        for normalise in (os.path.abspath, os.path.realpath):
            target, base = [os.path.normcase(normalise(p)) for p in (path, root)]
            if os.path.commonpath([target, base]) != base:
                return False
        current = path
        while True:
            if is_link(current):
                return False
            if os.path.normcase(current) == os.path.normcase(root):
                return True
            current = os.path.dirname(current)
    except (OSError, ValueError):
        return False


def remove_owned_directory(path, root):
    """Delete only a verified owned directory; report whether it disappeared."""
    if not owns_path(path, root):
        return False
    if not os.path.exists(path):
        return True
    try:
        shutil.rmtree(path)
    except OSError:
        return False
    return not os.path.exists(path)


@contextmanager
def file_lock(path):
    """Nonblocking advisory lock. The small lock file deliberately remains.

    Removing a lock file after unlocking creates an inode race with waiters.
    The OS releases this lock on process death; no stale-PID deletion is needed.
    """
    handle = open(path, 'a+b')
    locked = False
    try:
        if os.name == 'nt':
            import msvcrt
            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b'\0')
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise ValueError(f'Another execution is using this result directory or checkpoint: {path}') from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise ValueError(f'Another execution is using this result directory or checkpoint: {path}') from exc
        locked = True
        yield
    finally:
        if locked:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def isolated_run(function):
    """Give each public runner an owned workspace and serialize shared outputs."""
    signature = inspect.signature(function)

    @functools.wraps(function)
    def wrapped(self, *args, **kwargs):
        bound = signature.bind(self, *args, **kwargs)
        bound.apply_defaults()
        options = bound.arguments
        out_dir = os.path.abspath(self._resolve_results_out_dir(
            options['out_dir'], options.get('accim_results_root')
        ))
        os.makedirs(out_dir, exist_ok=True)
        kind = 'parametric' if 'parametric' in function.__name__ else 'optimisation'
        checkpoint = options.get('resume_from_checkpoint')
        if not isinstance(checkpoint, str):
            checkpoint = (self._default_parametric_checkpoint_path(out_dir) if kind == 'parametric'
                          else self._default_optimisation_checkpoint_path(out_dir))
        else:
            if not checkpoint.strip():
                raise ValueError("Argument 'resume_from_checkpoint' cannot be an empty string.")
            checkpoint = os.path.abspath(checkpoint.strip())
        lock_paths = {os.path.join(out_dir, '.accim-run.lock')}
        if os.path.isdir(os.path.dirname(checkpoint)):
            lock_paths.add(checkpoint + '.lock')
        with ExitStack() as stack:
            for lock_path in sorted(lock_paths):
                stack.enter_context(file_lock(lock_path))
            run_root = tempfile.mkdtemp(prefix='accim_run_', dir=out_dir)
            previous_root = getattr(self, '_active_run_root', None)
            self._active_run_root = run_root
            try:
                result = function(self, *args, **kwargs)
                if not options.get('keep_dirs', True) or options.get('keep_sim_files') == 'none':
                    remove_owned_directory(run_root, run_root)
                else:
                    try:
                        os.rmdir(run_root)
                    except OSError:
                        pass
                return result
            finally:
                # Keep this run's artifacts on failure for diagnosis/recovery.
                self._active_run_root = previous_root

    return wrapped


