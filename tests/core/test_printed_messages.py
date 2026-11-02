"""The texts that accim prints can be written in the encoding of a redirected output on Windows (cp1252).

Found on 2026-11-02 while running the full-workflow scripts with their output redirected to a file: Python writes a
standard output redirected to a file in the encoding of the system (cp1252 in Western Windows), so ``print()`` raises
``UnicodeEncodeError`` when a message has a character that cp1252 lacks (the standard error, where the warnings go,
replaces these characters instead). ``get_hourly_df_optimisation`` stopped at '→', and ``accim.utils.verification``
printed '→', '✓', '✗' and '−'.
"""
import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / 'accim'
# Not part of the package (the sample files and the legacy scripts of misc)
SKIPPED = ('sample_files', 'misc')
# The characters of the labels of the window of the GUI and of the figures, which are not printed
LABELS = {
    'gui/app.py': 'λ',
    'gui/forms.py': 'λ',
    'parametric_and_optimisation/hourly_plotting.py': 'ρ≤',
    'parametric_and_optimisation/plotting.py': '―',
}


def _encodes(character: str) -> bool:
    try:
        character.encode('cp1252')
    except UnicodeEncodeError:
        return False
    return True


def _texts(tree):
    """The string constants of a module (also the parts of the f-strings), except the docstrings."""
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node


def test_the_texts_of_accim_can_be_printed_in_cp1252():
    problems = []
    for path in sorted(PACKAGE.rglob('*.py')):
        relative = path.relative_to(PACKAGE).as_posix()
        if relative.startswith(SKIPPED):
            continue
        allowed = LABELS.get(relative, '')
        for node in _texts(ast.parse(path.read_text(encoding='utf-8'))):
            missing = sorted({c for c in node.value if c not in allowed and not _encodes(c)})
            if missing:
                problems.append(f'accim/{relative}:{node.lineno}: {"".join(missing)!r}')

    assert not problems, 'Texts with characters that cp1252 lacks:\n' + '\n'.join(problems)


def test_the_test_finds_the_characters_that_cp1252_lacks():
    tree = ast.parse('def f():\n    """Docstring →."""\n    print(f"{1} → {2}", "✓")\n')

    texts = [node.value for node in _texts(tree)]

    assert sorted(texts) == sorted([' → ', '✓'])
    assert not _encodes('→') and _encodes('°') and _encodes('…') and _encodes('×')
