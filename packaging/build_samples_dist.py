"""Build the 'accim-samples' distribution (the sample files of accim).

The core ``accim`` distribution does not include ``accim/sample_files``
(see ``MANIFEST.in`` and ``setup.py`` in the repository root). This script
packages that folder as the separate distribution ``accim-samples``, with the
same version as accim, so users can choose:

    pip install accim             # library only (lightweight)
    pip install "accim[samples]"  # library + sample files

Steps:

1. Read the version from ``accim/__init__.py`` (without importing accim).
2. Create a clean staging folder (``build/samples_stage``) with a copy of
   ``accim/sample_files`` (without ``__pycache__``, ``*.pyc`` or
   ``.ipynb_checkpoints``), the files in ``packaging/accim-samples``, the
   repository ``LICENSE`` and a ``VERSION`` file.
3. Run ``python -m build`` in the staging folder and write the result to
   ``dist/``.
4. Check that the wheel only contains ``accim/sample_files/**`` (never
   ``accim/__init__.py``) and warn if a file exceeds the PyPI size limit.

Usage, from any folder::

    py packaging/build_samples_dist.py            # wheel only (default)
    py packaging/build_samples_dist.py --sdist    # wheel + sdist
"""
import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(REPO_ROOT, 'packaging', 'accim-samples')
SAMPLES_SRC = os.path.join(REPO_ROOT, 'accim', 'sample_files')
STAGE_DIR = os.path.join(REPO_ROOT, 'build', 'samples_stage')
DEFAULT_OUTDIR = os.path.join(REPO_ROOT, 'dist')

DIST_NAME = 'accim-samples'
# Default per-file upload limit of PyPI (it can be raised on request).
PYPI_FILE_LIMIT_MB = 100
IGNORED_PATTERNS = ('__pycache__', '*.pyc', '*.pyo', '.ipynb_checkpoints')
TEMPLATE_FILES = ('setup.py', 'MANIFEST.in', 'README.md')


def read_accim_version():
    """Return ``__version__`` from accim/__init__.py without importing accim."""
    init_path = os.path.join(REPO_ROOT, 'accim', '__init__.py')
    with open(init_path, encoding='utf-8') as f:
        content = f.read()
    match = re.search(
        r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE
    )
    if not match:
        raise RuntimeError(f'__version__ not found in {init_path}')
    return match.group(1)


def _make_writable_and_retry(func, path, _exc):
    """Error handler for shutil.rmtree: clear read-only flags (Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _rmtree(path):
    if not os.path.exists(path):
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_make_writable_and_retry)
    else:
        shutil.rmtree(path, onerror=_make_writable_and_retry)


def _folder_stats(path):
    n_files, n_bytes = 0, 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for filename in filenames:
            n_files += 1
            n_bytes += os.path.getsize(os.path.join(dirpath, filename))
    return n_files, n_bytes / 1024 ** 2


def stage(version):
    """Create the staging folder and return its path."""
    if not os.path.isdir(SAMPLES_SRC):
        raise FileNotFoundError(f'Sample files folder not found: {SAMPLES_SRC}')

    _rmtree(STAGE_DIR)
    os.makedirs(STAGE_DIR)

    for filename in TEMPLATE_FILES:
        shutil.copy2(os.path.join(TEMPLATE_DIR, filename), STAGE_DIR)
    shutil.copy2(os.path.join(REPO_ROOT, 'LICENSE'), STAGE_DIR)
    with open(os.path.join(STAGE_DIR, 'VERSION'), 'w', encoding='utf-8') as f:
        f.write(version + '\n')

    # Only accim/sample_files is copied; accim/__init__.py must never be
    # part of this distribution.
    shutil.copytree(
        SAMPLES_SRC,
        os.path.join(STAGE_DIR, 'accim', 'sample_files'),
        ignore=shutil.ignore_patterns(*IGNORED_PATTERNS),
    )
    return STAGE_DIR


def build(outdir, with_sdist, no_isolation):
    """Run ``python -m build`` in the staging folder."""
    cmd = [sys.executable, '-m', 'build', '--outdir', outdir]
    if not with_sdist:
        cmd.append('--wheel')
    if no_isolation:
        cmd.append('--no-isolation')
    print('Running:', ' '.join(cmd))
    return subprocess.call(cmd, cwd=STAGE_DIR)


def check_wheel(wheel_path):
    """Return the problems found in the built wheel (empty list if none)."""
    problems = []
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
    for name in names:
        if name.split('/', 1)[0].endswith('.dist-info'):
            continue
        if not name.startswith('accim/sample_files/'):
            problems.append(f'unexpected file outside accim/sample_files: {name}')
    if not any(name.startswith('accim/sample_files/') for name in names):
        problems.append('the wheel does not contain accim/sample_files')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Build the accim-samples distribution (accim/sample_files).'
    )
    parser.add_argument(
        '--outdir', default=DEFAULT_OUTDIR,
        help='Output folder for the distribution files (default: dist/).',
    )
    parser.add_argument(
        '--sdist', action='store_true',
        help='Also build a source distribution (by default only the wheel is '
             'built, to halve the size uploaded to PyPI).',
    )
    parser.add_argument(
        '--no-isolation', action='store_true',
        help='Pass --no-isolation to "python -m build" (offline builds; '
             'requires setuptools and wheel in the current environment).',
    )
    args = parser.parse_args(argv)
    outdir = os.path.abspath(args.outdir)

    version = read_accim_version()
    print(f'Building {DIST_NAME} {version}')

    stage(version)
    n_files, size_mb = _folder_stats(os.path.join(STAGE_DIR, 'accim'))
    print(f'Staged {n_files} files ({size_mb:.1f} MB) in {STAGE_DIR}')

    if build(outdir, args.sdist, args.no_isolation) != 0:
        print('ERROR: "python -m build" failed. If the module is missing, run: '
              'py -m pip install --upgrade build')
        return 1

    normalized = DIST_NAME.replace('-', '_')
    produced = sorted(
        filename for filename in os.listdir(outdir)
        if filename.startswith(f'{normalized}-{version}')
    )
    if not any(filename.endswith('.whl') for filename in produced):
        print(f'ERROR: no {DIST_NAME} {version} wheel was found in {outdir}')
        return 1

    exit_code = 0
    for filename in produced:
        path = os.path.join(outdir, filename)
        file_mb = os.path.getsize(path) / 1024 ** 2
        print(f'  {filename}: {file_mb:.1f} MB')
        if file_mb > PYPI_FILE_LIMIT_MB:
            print(f'  WARNING: {filename} exceeds the default PyPI upload limit '
                  f'of {PYPI_FILE_LIMIT_MB} MB. Reduce the sample files or ask '
                  'PyPI for a larger limit for this project.')
        if filename.endswith('.whl'):
            problems = check_wheel(path)
            for problem in problems:
                print(f'  ERROR: {problem}')
            if problems:
                exit_code = 1

    if exit_code == 0:
        print(f'{DIST_NAME} {version} built successfully in {outdir}')
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
