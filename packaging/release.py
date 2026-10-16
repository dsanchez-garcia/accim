"""Checks and uploads for the release scripts of accim (``dist_*.bat`` in the repository root).

Each version of accim (``__version__`` in ``accim/__init__.py``) is published as two
distributions, which ``dist_build_package.bat`` builds in ``dist/``:

- ``accim``: the library, without ``accim/sample_files`` (sdist and wheel);
- ``accim-samples``: only ``accim/sample_files`` (wheel, see ``build_samples_dist.py``),
  installed with ``pip install "accim[samples]"``.

``accim[samples]`` requires ``accim-samples==<version>`` and ``accim-samples`` requires
``accim==<version>``, so both must be uploaded for every version.

Usage, from any folder::

    py packaging/release.py tools build|upload|docs   # check (and install) the tools of a script
    py packaging/release.py check                     # check the files in dist/
    py packaging/release.py upload --repository testpypi [--dry-run] [--verbose]
    py packaging/release.py upload --repository pypi [--dry-run] [--verbose]

``check`` takes the files of the current version in ``dist/`` (files of other versions are
listed and left out), checks the content and metadata of both wheels and runs
``twine check --strict`` when twine is installed.

``upload`` runs the same checks, asks the index which of the two distributions of this version
are already published (those are skipped), asks you to type the version to confirm, and uploads
``accim-samples`` before ``accim``: if the first upload fails, ``accim`` is not published with a
``samples`` extra that cannot be installed.

twine reads the credentials from ``~/.pypirc``: the sections ``pypi`` and ``testpypi`` are used
for ``accim``. If the section ``accim-samples`` (PyPI) or ``testpypi-accim-samples`` (TestPyPI)
is defined and listed in ``index-servers``, it is used for ``accim-samples``, so that each project
can have its own token. The first upload of ``accim-samples`` creates the project, which a token
restricted to another project cannot do: use a token for the entire account for that upload.
"""
import argparse
import configparser
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from email.parser import HeaderParser

import build_samples_dist as samples

REPO_ROOT = samples.REPO_ROOT
DIST_DIR = samples.DEFAULT_OUTDIR
CORE = 'accim'
SAMPLES = samples.DIST_NAME

INDEX_URLS = {'pypi': 'https://pypi.org', 'testpypi': 'https://test.pypi.org'}
UPLOAD_URLS = {'pypi': 'https://upload.pypi.org/legacy/', 'testpypi': 'https://test.pypi.org/legacy/'}
INDEX_LABELS = {'pypi': 'PyPI', 'testpypi': 'TestPyPI'}
# Sections of ~/.pypirc used for accim-samples when they are defined.
SAMPLES_SECTIONS = {'pypi': 'accim-samples', 'testpypi': 'testpypi-accim-samples'}

# (module to import, requirement to install) for the tools of each dist_*.bat script.
TOOLS = {
    'build': [('build', 'build')],
    'upload': [('twine', 'twine>=6.1')],
    'docs': [
        ('sphinx', 'sphinx'),
        ('sphinx_rtd_theme', 'sphinx-rtd-theme'),
        ('nbsphinx', 'nbsphinx'),
        ('myst_parser', 'myst-parser'),
        ('IPython', 'ipython'),
    ],
}
# twine < 6.1 cannot read the metadata (version 2.4) written by current setuptools.
MIN_TWINE = (6, 1)
MAX_LISTED_CHANGES = 15


def _ask_yes(question):
    try:
        answer = input(f'{question} [y/N]: ')
    except EOFError:
        answer = ''
    return answer.strip().lower() in ('y', 'yes', 's', 'si')


def _version_tuple(text):
    return tuple(int(number) for number in re.findall(r'\d+', text)[:2])


def _missing_tools(group):
    missing = [requirement for module, requirement in TOOLS[group]
               if importlib.util.find_spec(module) is None]
    if group == 'upload' and not missing:
        from importlib.metadata import version
        if _version_tuple(version('twine')) < MIN_TWINE:
            missing.append('twine>=6.1')
    return missing


def cmd_tools(args):
    """Check the packages needed by a dist_*.bat script and offer to install the missing ones."""
    missing = _missing_tools(args.group)
    if missing:
        quoted = ' '.join(f'"{req}"' if '>' in req else req for req in missing)
        print(f'Missing packages: {", ".join(missing)}')
        print(f'They can be installed in this Python ({sys.executable}) with:')
        print(f'    py -m pip install {quoted}')
        if args.group == 'docs':
            print('(Do not use docs/requirements.txt here: it is meant for Read the Docs, with '
                  'Python 3.9, and pins numpy<2 and matplotlib<=3.7.)')
        if not _ask_yes('Install them now?'):
            print('Not installed.')
            return 1
        if subprocess.call([sys.executable, '-m', 'pip', 'install', *missing]) != 0:
            print('ERROR: pip could not install the packages.')
            return 1
        importlib.invalidate_caches()
        missing = _missing_tools(args.group)
        if missing:
            print(f'ERROR: still missing after the installation: {", ".join(missing)}')
            return 1
    if args.group == 'docs' and shutil.which('pandoc') is None:
        print('ERROR: pandoc was not found in PATH. nbsphinx needs it for the Markdown cells of the '
              'notebooks: https://pandoc.org/installing.html (or: winget install --id JohnMacFarlane.Pandoc)')
        return 1
    print(f'Tools for "{args.group}": OK ({sys.executable})')
    return 0


def _normalized(version):
    """Version as written in the file names of the distributions (PEP 440 normal form)."""
    try:
        from packaging.version import InvalidVersion, Version
    except ImportError:
        return version
    try:
        return str(Version(version))
    except InvalidVersion:
        return version


def release_files(version):
    """Split ``dist/`` into the files of ``version`` ({distribution: [paths]}) and the rest."""
    stems = {name: f'{name.replace("-", "_")}-{_normalized(version)}' for name in (CORE, SAMPLES)}
    found = {name: [] for name in stems}
    others = []
    if os.path.isdir(DIST_DIR):
        for filename in sorted(os.listdir(DIST_DIR)):
            for name, stem in stems.items():
                if filename == f'{stem}.tar.gz' or (
                        filename.startswith(f'{stem}-') and filename.endswith('.whl')):
                    found[name].append(os.path.join(DIST_DIR, filename))
                    break
            else:
                others.append(filename)
    return found, others


def _wheel_info(path):
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        metadata = next(name for name in names if name.endswith('.dist-info/METADATA'))
        headers = HeaderParser().parsestr(wheel.read(metadata).decode('utf-8'))
    return names, headers


def _requirements(headers):
    """``Requires-Dist`` entries, lower case, without spaces and with '-' instead of '_'."""
    return [req.replace(' ', '').replace('_', '-').lower()
            for req in headers.get_all('Requires-Dist') or []]


def check_files(version, found):
    """Return the problems of the release files of ``version`` (empty list if none)."""
    problems = []
    pinned = version.lower()
    core_wheels = [path for path in found[CORE] if path.endswith('.whl')]
    samples_wheels = [path for path in found[SAMPLES] if path.endswith('.whl')]
    if not core_wheels:
        problems.append(f'the wheel of {CORE} {version} is missing')
    if not any(path.endswith('.tar.gz') for path in found[CORE]):
        problems.append(f'the sdist of {CORE} {version} is missing')
    if not samples_wheels:
        problems.append(f'the wheel of {SAMPLES} {version} is missing')

    for path in core_wheels:
        filename = os.path.basename(path)
        names, headers = _wheel_info(path)
        if 'accim/__init__.py' not in names:
            problems.append(f'{filename} does not contain accim/__init__.py')
        if any(name.startswith('accim/sample_files/') for name in names):
            problems.append(f'{filename} contains accim/sample_files, which belong in {SAMPLES}')
        if not any(req.startswith(f'{SAMPLES}=={pinned};') and 'extra=="samples"' in req
                   for req in _requirements(headers)):
            problems.append(f'the extra "samples" of {filename} does not require {SAMPLES}=={version}')

    for path in samples_wheels:
        filename = os.path.basename(path)
        _names, headers = _wheel_info(path)
        problems.extend(f'{filename}: {problem}' for problem in samples.check_wheel(path))
        if f'{CORE}=={pinned}' not in [req.split(';')[0] for req in _requirements(headers)]:
            problems.append(f'{filename} does not require {CORE}=={version}')
    return problems


def _git(*args):
    return subprocess.run(['git', *args], cwd=REPO_ROOT, capture_output=True, check=True,
                          encoding='utf-8', errors='replace').stdout


def print_git_state():
    """Print the branch and the uncommitted changes that end up in the distributions."""
    try:
        branch = _git('rev-parse', '--abbrev-ref', 'HEAD').strip()
        changes = _git('status', '--porcelain', '--', 'accim', 'setup.py', 'MANIFEST.in',
                       'README.md', 'packaging/accim-samples').splitlines()
    except (OSError, subprocess.CalledProcessError):
        return
    print(f'git branch: {branch}')
    if branch != 'master':
        print('  NOTE: releases are usually made from master, the branch that Read the Docs builds.')
    if changes:
        print(f'  WARNING: {len(changes)} uncommitted change(s); the distributions contain the '
              'files as they are in the working copy:')
        for line in changes[:MAX_LISTED_CHANGES]:
            print(f'    {line}')
        if len(changes) > MAX_LISTED_CHANGES:
            print(f'    ... and {len(changes) - MAX_LISTED_CHANGES} more')


def _print_files(found, others):
    for paths in found.values():
        for path in paths:
            print(f'  {os.path.basename(path)}  ({os.path.getsize(path) / 1024 ** 2:.1f} MB)')
    if others:
        print('Files of other versions in dist/ (they are left out):')
        for filename in others:
            print(f'  {filename}')


def twine_check(paths):
    if importlib.util.find_spec('twine') is None:
        print('twine is not installed: "twine check" skipped (dist_upload*.bat installs it).')
        return True
    return subprocess.call([sys.executable, '-m', 'twine', 'check', '--strict', *paths]) == 0


def checked_release(version):
    """Check the release files of ``version``; return {distribution: [paths]} or None."""
    found, others = release_files(version)
    print(f'accim version (accim/__init__.py): {version}')
    print_git_state()
    print(f'Release files in {DIST_DIR}:')
    _print_files(found, others)
    problems = check_files(version, found)
    for problem in problems:
        print(f'ERROR: {problem}')
    if problems:
        print('Build both distributions with dist_build_package.bat.')
        return None
    if not twine_check([path for paths in found.values() for path in paths]):
        print('ERROR: "twine check" found problems in the distributions.')
        return None
    return found


def cmd_check(_args):
    version = samples.read_accim_version()
    if checked_release(version) is None:
        return 1
    print(f'dist/ is ready to upload {CORE} {version} and {SAMPLES} {version}.')
    return 0


def is_published(index_url, name, version):
    """True or False whether the index has ``name`` ``version``; None if it cannot be checked."""
    try:
        with urllib.request.urlopen(f'{index_url}/pypi/{name}/{version}/json', timeout=20):
            return True
    except urllib.error.HTTPError as error:
        return False if error.code == 404 else None
    except (urllib.error.URLError, OSError, ValueError):
        return None


def latest_version(index_url, name):
    try:
        with urllib.request.urlopen(f'{index_url}/pypi/{name}/json', timeout=20) as response:
            return json.load(response)['info']['version']
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _is_older(version, other):
    try:
        from packaging.version import InvalidVersion, Version
    except ImportError:
        return False
    try:
        return Version(version) < Version(other)
    except InvalidVersion:
        return False


def pypirc_sections():
    """Sections of ~/.pypirc that twine can use (defined and listed in ``index-servers``)."""
    path = os.path.join(os.path.expanduser('~'), '.pypirc')
    parser = configparser.RawConfigParser()
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            parser.read_file(f)
    except (OSError, configparser.Error):
        return set()
    servers = parser.get('distutils', 'index-servers', fallback='pypi testpypi').split()
    return {name for name in servers if parser.has_section(name)}


def _print_upload_error(name, version, repository, section):
    label = INDEX_LABELS[repository]
    print()
    print(f'ERROR: the upload of {name} {version} to {label} failed (see the messages of twine above).')
    print(f'- 403 Forbidden: the token of the section [{section}] of ~/.pypirc cannot upload to {name}.')
    if name == SAMPLES:
        print(f'  The first upload of {SAMPLES} creates the project, which needs a token for the entire')
        print(f'  account. To keep one token per project, add a section [{SAMPLES_SECTIONS[repository]}]')
        print(f'  with "repository = {UPLOAD_URLS[repository]}", "username = __token__" and the token')
        print('  as password, and list it in index-servers.')
        print(f'  {CORE} has not been uploaded.')
    else:
        print(f'  {SAMPLES} {version} is uploaded: run the script again to upload {CORE} only.')
    print('- 400 "File already exists" or "filename has already been used": a version cannot be')
    print('  uploaded twice, even after deleting it; increase __version__ and build again.')


def cmd_upload(args):
    repository = args.repository
    label = INDEX_LABELS[repository]
    index_url = INDEX_URLS[repository]
    version = samples.read_accim_version()

    found = checked_release(version)
    if found is None:
        return 1

    sections = pypirc_sections()
    section = {CORE: repository, SAMPLES: repository}
    if SAMPLES_SECTIONS[repository] in sections:
        section[SAMPLES] = SAMPLES_SECTIONS[repository]

    print()
    print(f'Upload to {label} ({index_url}), {SAMPLES} first:')
    pending = []
    for name in (SAMPLES, CORE):
        published = is_published(index_url, name, version)
        if published:
            state = 'already published, skipped'
        else:
            pending.append(name)
            state = 'not published yet' if published is False else 'could not be checked'
            state += f', will be uploaded with the section [{section[name]}] of ~/.pypirc'
        print(f'  {name} {version}: {state}')
    latest = latest_version(index_url, CORE)
    if latest and _is_older(version, latest):
        print(f'  WARNING: {version} is lower than the latest version of {CORE} on {label} ({latest}).')
    if not pending:
        print(f'Both distributions of {version} are already on {label}: nothing to upload.')
        return 0

    commands = []
    for name in pending:
        command = [sys.executable, '-m', 'twine', 'upload', '--repository', section[name], '--skip-existing']
        if args.verbose:
            command.append('--verbose')
        commands.append((name, command + found[name]))

    if args.dry_run:
        print('Dry run, nothing uploaded. These commands would run:')
        for _name, command in commands:
            print('  ' + subprocess.list2cmdline(command))
        return 0

    print()
    print(f'An upload to {label} cannot be undone: the same version can never be uploaded again.')
    try:
        answer = input(f'Type the version ({version}) to upload it to {label}, or press Enter to cancel: ')
    except EOFError:
        answer = ''
    if answer.strip() != version:
        print('Upload cancelled: nothing has been uploaded.')
        return 2

    for name, command in commands:
        print()
        print(f'Uploading {name} {version} to {label}...')
        if subprocess.call(command) != 0:
            _print_upload_error(name, version, repository, section[name])
            return 1

    print()
    print(f'Done. Pages on {label} (they can take a few minutes to show the new version):')
    for name in (CORE, SAMPLES):
        print(f'  {index_url}/project/{name}/{version}/')
    print('Check the installation in a new virtual environment with:')
    if repository == 'testpypi':
        print('  py -m pip install --index-url https://test.pypi.org/simple/ '
              f'--extra-index-url https://pypi.org/simple/ "accim[samples]=={version}"')
    else:
        print(f'  py -m pip install "accim[samples]=={version}"')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Checks and uploads for the release scripts of accim.')
    sub = parser.add_subparsers(dest='command', required=True)
    tools_parser = sub.add_parser('tools', help='check (and install) the packages of a dist_*.bat script')
    tools_parser.add_argument('group', choices=sorted(TOOLS))
    sub.add_parser('check', help='check the files of the current version in dist/')
    upload_parser = sub.add_parser('upload', help=f'upload {SAMPLES} and {CORE} to PyPI or TestPyPI')
    upload_parser.add_argument('--repository', choices=sorted(INDEX_URLS), required=True)
    upload_parser.add_argument('--dry-run', action='store_true',
                               help='run the checks and show the twine commands without uploading')
    upload_parser.add_argument('--verbose', action='store_true', help='pass --verbose to twine upload')
    args = parser.parse_args(argv)
    # Keep the order of these messages and those of the subprocesses (pip, twine) in logs.
    sys.stdout.reconfigure(line_buffering=True)
    commands = {'tools': cmd_tools, 'check': cmd_check, 'upload': cmd_upload}
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
