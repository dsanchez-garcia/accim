"""Run the configurations of the golden master and compare their outputs.

The test ``tests/core/test_golden_master.py`` imports this module. As a script, it runs the configurations with
the accim that Python imports first (set ``PYTHONPATH`` to the folder of another version, for instance a git
worktree), each one in its own process, and writes the canonical text of the outputs of each configuration to
``OUT_DIR/<name>.txt``; ``compare`` compares two such folders, or one with the golden files of the repository::

    python tests/core/golden_master/runner.py write OUT_DIR [--legacy] [--jobs 4] [--only NAME ...]
    python tests/core/golden_master/runner.py compare DIR_A DIR_B [--ignore-order] [--only NAME ...]

``--legacy`` calls the functions of accim 0.x, with the names of its arguments. ``--ignore-order`` compares the
objects of each IDF in any order (accim 0.x did not always write them in the same order). See README.md.
"""
import argparse
import difflib
import lzma
import os
import subprocess
import sys
import tempfile
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from . import configs
except ImportError:  # run as a script
    import configs

HERE = Path(__file__).resolve().parent
INPUTS = HERE / 'inputs'
GOLDEN = HERE / 'golden'
FILE_MARK = '### '


def copy_input_model(model, folder):
    """Write the input model ``model`` (inputs/<model>.idf.xz) to ``folder``; return its path."""
    path = Path(folder) / f'{model}.idf'
    path.write_bytes(lzma.decompress((INPUTS / f'{model}.idf.xz').read_bytes()))
    return path


def _arguments(kwargs, legacy, names=None):
    names = configs.LEGACY_NAMES if names is None else names
    return {names.get(k, k): v for k, v in kwargs.items()} if legacy else dict(kwargs)


def _add_accis(kwargs, legacy):
    from accim.sim import accis
    return accis.addAccis(**kwargs) if legacy else accis.AddAccis(**kwargs)


def _run_batch(name, work, legacy):
    cfg = configs.BATCH[name]
    for model in cfg['models']:
        copy_input_model(model, work)
    kwargs = _arguments(cfg['kwargs'], legacy)
    gen_df, take_df = _arguments({'make_outputs_dataframe': 0, 'outputs_dataframe': 0}, legacy)
    cwd = os.getcwd()
    os.chdir(work)
    try:
        if cfg.get('take_dataframe'):
            first = _add_accis(dict(kwargs, **{gen_df: True}), legacy)
            df = first.df_outputs
            kwargs[take_df] = df[df['variable_name'].str.contains('Temperature')]
            for path in Path(work).glob('*[[]*.idf'):
                path.unlink()
        result = _add_accis(kwargs, legacy)
    finally:
        os.chdir(cwd)
    outputs = {path.name: path.read_bytes() for path in sorted(Path(work).iterdir())
               if path.suffix == '.idf' and path.stem not in cfg['models']}
    df = getattr(result, 'df_outputs', None)
    if df is not None:
        outputs['df_outputs.csv'] = df.to_csv(index=False).encode('utf-8')
    return outputs


def _run_single(name, work, legacy):
    from besos.eppy_funcs import get_building

    cfg = configs.SINGLE[name]
    building = get_building(str(copy_input_model(cfg['model'], work)))
    outputs = {}
    for call, kwargs in cfg['calls']:
        apmv_call = call in ('apmv_vrf', 'apmv')
        kwargs = _arguments(kwargs, legacy, configs.LEGACY_APMV_NAMES if apmv_call else None)
        if call in ('add', 'class_add', 'modify', 'gen_outputs_df'):
            if legacy:
                from accim.sim import accis_single_idf, accis_single_idf_funcs as funcs
                function = {'add': lambda **kw: funcs.addAccis(idf=building, **kw),
                            'class_add': lambda **kw: accis_single_idf.addAccis(idf=building, **kw),
                            'modify': lambda **kw: funcs.modifyAccis(building, **kw),
                            'gen_outputs_df': lambda **kw: funcs.gen_outputs_df(idf=building, **kw)}[call]
            else:
                from accim.sim import accis
                function = {'add': accis.add_accis_to_idf, 'class_add': accis.add_accis_to_idf,
                            'modify': accis.modify_accis, 'gen_outputs_df': accis.gen_outputs_df}[call]
                function = (lambda f: lambda **kw: f(building, **kw))(function)
            result = function(**kwargs)
            if call == 'gen_outputs_df':
                outputs['df_outputs.csv'] = result.to_csv(index=False).encode('utf-8')
        elif apmv_call:
            if legacy:
                from accim.sim import apmv_setpoints as apmv
            else:
                from accim.sim import apmv
            if call == 'apmv_vrf':
                apmv.add_vrf_system(building, **_arguments({'verbose': False}, legacy, configs.LEGACY_APMV_NAMES))
                continue
            for key, value in list(kwargs.items()):
                if isinstance(value, dict) and '*first*' in value:
                    kwargs[key] = {apmv.get_available_target_names(building)[0]: value['*first*']}
            apmv.apply_apmv_setpoints(building, **kwargs)
        else:
            raise ValueError(f'Unknown call {call!r} in the configuration {name}')
    path = Path(work) / f'{name}.idf'
    building.saveas(str(path))
    outputs[path.name] = path.read_bytes()
    return dict(sorted(outputs.items()))


def run_config(name, work, legacy=False):
    """Run the configuration ``name`` in the empty folder ``work``; return {file name: content} of its outputs."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        if name in configs.BATCH:
            return _run_batch(name, work, legacy)
        return _run_single(name, work, legacy)


def idf_objects(text):
    """The objects of an IDF text, as lists of fields (the class first), without comments or spaces."""
    text = '\n'.join(line.split('!', 1)[0] for line in text.replace('\r\n', '\n').split('\n'))
    objects = []
    for block in text.split(';'):
        fields = [field.strip() for field in block.split(',')]
        if any(fields):
            objects.append(fields)
    return objects


def canonical_idf(text):
    """The objects of an IDF text in their order, one field per line, without comments or formatting."""
    lines = []
    for fields in idf_objects(text):
        if len(fields) == 1:
            lines.append(fields[0] + ';')
        else:
            lines.append(fields[0] + ',')
            lines.extend(f'    {field},' for field in fields[1:-1])
            lines.append(f'    {fields[-1]};')
        lines.append('')
    return '\n'.join(lines)


def canonical_outputs(outputs):
    """The canonical text (bytes) of the outputs of a configuration: each file under a '### <name>' line."""
    chunks = []
    for file_name, content in sorted(outputs.items()):
        text = content.decode('utf-8', 'surrogateescape')
        text = canonical_idf(text) if file_name.lower().endswith('.idf') else text.replace('\r\n', '\n')
        chunks.append(f'{FILE_MARK}{file_name}\n{text}')
    if not chunks:
        chunks.append(f'{FILE_MARK}(no output files)\n')
    return '\n'.join(chunks).encode('utf-8', 'surrogateescape')


def split_outputs(text):
    """{file name: canonical text} of the canonical text of a configuration."""
    files = {}
    name = None
    for line in text.split('\n'):
        if line.startswith(FILE_MARK):
            name = line[len(FILE_MARK):]
            files[name] = []
        elif name is not None:
            files[name].append(line)
    return {name: '\n'.join(lines).strip('\n') for name, lines in files.items()}


# Command line --------------------------------------------------------------------------------------------------

def _read(folder, name):
    for path in (Path(folder) / f'{name}.txt', Path(folder) / f'{name}.txt.xz'):
        if path.exists():
            data = path.read_bytes()
            return (lzma.decompress(data) if path.suffix == '.xz' else data).decode('utf-8', 'surrogateescape')
    return None


def _names(folder):
    return {p.name.split('.')[0] for p in Path(folder).iterdir() if p.name.endswith(('.txt', '.txt.xz'))}


def _object_set(text):
    """Objects of a canonical IDF text, as sorted tuples, with the normalisation of the comparisons with 0.x."""
    objects = []
    for fields in idf_objects(text):
        fields[0] = fields[0].upper()
        while len(fields) > 1 and fields[-1] == '':
            fields.pop()
        # accim 0.x re-created the People objects, which added the IDD defaults of the stress thresholds
        if fields[0] == 'PEOPLE' and fields[-2:] == ['15.56', '30']:
            del fields[-2:]
            while len(fields) > 1 and fields[-1] == '':
                fields.pop()
        objects.append(tuple(fields))
    return sorted(objects)


def compare_file(a, b, ignore_order):
    """None if two canonical file texts are the same, or a description of their differences."""
    if a == b:
        return None
    if ignore_order and '\n    ' in a:
        oa, ob = _object_set(a), _object_set(b)
        if oa == ob:
            return None
        sa, sb = set(oa), set(ob)
        only_a = [o for o in oa if o not in sb]
        only_b = [o for o in ob if o not in sa]
        lines = [f'{len(only_a)} objects only in A, {len(only_b)} only in B (A {len(oa)}, B {len(ob)})']
        lines += ['  A: ' + ','.join(o)[:300] for o in only_a[:4]]
        lines += ['  B: ' + ','.join(o)[:300] for o in only_b[:4]]
        return '\n'.join(lines)
    diff = list(difflib.unified_diff(a.split('\n'), b.split('\n'), 'A', 'B', lineterm='', n=1))
    return '\n'.join(diff[:40] + ([f'... ({len(diff) - 40} more lines)'] if len(diff) > 40 else []))


def cmd_compare(args):
    names = args.only or sorted(_names(args.a) | _names(args.b))
    different = 0
    for name in names:
        ta, tb = _read(args.a, name), _read(args.b, name)
        if ta is None or tb is None:
            print(f'[MISSING] {name}: only in {"B" if ta is None else "A"}')
            different += 1
            continue
        fa, fb = split_outputs(ta), split_outputs(tb)
        problems = [f'only in A: {f}' for f in sorted(set(fa) - set(fb))]
        problems += [f'only in B: {f}' for f in sorted(set(fb) - set(fa))]
        same = 0
        for file_name in sorted(set(fa) & set(fb)):
            diff = compare_file(fa[file_name], fb[file_name], args.ignore_order)
            if diff:
                problems.append(f'DIFFERENT {file_name}\n{diff}')
            else:
                same += 1
        different += bool(problems)
        print(f'[{"DIFFERENT" if problems else "SAME"}] {name}: {same} files the same')
        for problem in problems[:args.max_problems]:
            print('   ' + problem.replace('\n', '\n   '))
        if len(problems) > args.max_problems:
            print(f'   ... {len(problems) - args.max_problems} more')
    print(f'{different} of {len(names)} configurations are different')
    return 1 if different else 0


def cmd_run_one(args):
    with tempfile.TemporaryDirectory() as work:
        outputs = run_config(args.name, work, legacy=args.legacy)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f'{args.name}.txt').write_bytes(canonical_outputs(outputs))
    print(f'{args.name}: {len(outputs)} files')
    return 0


def cmd_write(args):
    import accim
    print(f'accim {getattr(accim, "__version__", "?")} from {Path(accim.__file__).parent}', flush=True)
    names = args.only or configs.NAMES

    def run(name):
        command = [sys.executable, str(Path(__file__).resolve()), 'run-one', name, args.out]
        env = dict(os.environ)
        if args.legacy:
            command.append('--legacy')
            # accim 0.x did not always write the objects in the same order
            env['PYTHONHASHSEED'] = '0'
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        return name, result

    failed = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for name, result in pool.map(run, names):
            ok = result.returncode == 0
            failed += not ok
            print(f'[{"ok" if ok else "FAILED"}] {name}', flush=True)
            if not ok:
                print('   ' + '\n   '.join((result.stdout + result.stderr).strip().splitlines()[-12:]))
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    write = sub.add_parser('write', help='write the canonical outputs of the configurations to a folder')
    write.add_argument('out')
    write.add_argument('--legacy', action='store_true', help='use the functions and argument names of accim 0.x')
    write.add_argument('--jobs', type=int, default=4)
    write.add_argument('--only', nargs='*', choices=configs.NAMES, metavar='NAME')
    one = sub.add_parser('run-one', help='run one configuration in this process (what write runs for each one)')
    one.add_argument('name', choices=configs.NAMES)
    one.add_argument('out')
    one.add_argument('--legacy', action='store_true')
    compare = sub.add_parser('compare', help='compare two folders of canonical outputs (.txt or .txt.xz)')
    compare.add_argument('a')
    compare.add_argument('b', nargs='?', default=str(GOLDEN), help='the golden files of the repository by default')
    compare.add_argument('--ignore-order', action='store_true')
    compare.add_argument('--only', nargs='*', metavar='NAME')
    compare.add_argument('--max-problems', type=int, default=6)
    args = parser.parse_args(argv)
    return {'write': cmd_write, 'run-one': cmd_run_one, 'compare': cmd_compare}[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
