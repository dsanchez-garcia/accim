"""Ownership of batch IDF working copies, without directory-wide cleanup."""

from contextvars import ContextVar
from functools import wraps
import os
import shutil
import logging
from typing import Optional

_batch_files: ContextVar[Optional[set[str]]] = ContextVar('accim_batch_working_files', default=None)


def cleanup_files(paths):
    for path in list(paths):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            logging.getLogger(__name__).warning('Could not remove owned ACCIM working file %s: %s', path, exc)
            continue
        # A later invocation may reserve this name as soon as unlink succeeds.
        # Neither the job nor its enclosing batch may delete that new file.
        if hasattr(paths, 'discard'):
            paths.discard(path)
        batch = _batch_files.get()
        if batch is not None:
            batch.discard(path)


def batch_workspace(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        paths = set()
        token = _batch_files.set(paths)
        try:
            return function(*args, **kwargs)
        finally:
            _batch_files.reset(token)
            cleanup_files(paths)
    return wrapped


def copy_job_input(job, source, destination):
    """Reserve the traditional name exclusively; never overwrite a prior run."""
    destination = os.path.abspath(destination)
    with open(source, 'rb') as original:
        with open(destination, 'xb') as working:
            job._owned_pymod_files = {destination}
            batch = _batch_files.get()
            if batch is not None:
                batch.add(destination)
            shutil.copyfileobj(original, working)
    return destination


def cleanup_failed_job(function):
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        self._owned_pymod_files = set()
        try:
            return function(self, *args, **kwargs)
        except BaseException:
            cleanup_files(self._owned_pymod_files)
            raise
    return wrapped


def cleanup_after_generation(function):
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        finally:
            cleanup_files(getattr(self, '_owned_pymod_files', ()))
    return wrapped



