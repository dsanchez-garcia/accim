"""Utilidades compartidas para los tests de caracterizacion (golden-file).

La salida de addAccis es estable en CONTENIDO pero el ORDEN de los objetos dentro
de cada tipo puede variar entre procesos (algunas zonas se recorren via `set`, cuyo
orden depende de la aleatorizacion de hash de Python). El orden de objetos dentro de
un mismo tipo NO afecta al resultado de EnergyPlus, por lo que la comparacion se hace
sobre una forma CANONICA insensible al orden:

  - se elimina el formateo y los comentarios '!- ...',
  - cada objeto IDF se reduce a la tupla de sus campos,
  - los objetos se ordenan,

de modo que dos salidas con el mismo contenido pero distinto orden son equivalentes.
Si el refactor cambia valores de campo o anade/elimina objetos, la forma canonica
difiere y el test falla.
"""

import difflib
import gzip
from pathlib import Path

FS = "\x1f"  # separador de campos (no aparece en IDFs)


def canonicalize_idf_text(text):
    """Convierte el texto de un IDF en una representacion canonica (bytes), ordenada
    e insensible al orden de los objetos."""
    text = text.replace("\r\n", "\n")
    # 1. Quitar comentarios.
    no_comments = []
    for line in text.split("\n"):
        if "!" in line:
            line = line.split("!", 1)[0]
        no_comments.append(line)
    joined = "\n".join(no_comments)
    # 2. Separar objetos (cada objeto IDF termina en ';').
    blocks = []
    for raw in joined.split(";"):
        fields = [f.strip() for f in raw.split(",")]
        # Saltar el "objeto" vacio que queda entre objetos (solo espacios/saltos).
        if not any(fields):
            continue
        blocks.append(FS.join(fields))
    blocks.sort()
    return "\n".join(blocks).encode("utf-8", "surrogateescape")


def short_diff(expected, actual, max_lines=40):
    exp = expected.decode("latin-1").splitlines()
    act = actual.decode("latin-1").splitlines()
    diff = list(difflib.unified_diff(exp, act, "golden", "actual", lineterm=""))
    if len(diff) > max_lines:
        diff = diff[:max_lines] + [f"... (+{len(diff) - max_lines} lineas mas)"]
    return "\n".join(diff)


def assert_or_write_golden(golden_file, actual, update, dump_suffix=".actual.txt"):
    """Compara `actual` (bytes) contra el golden gzip almacenado. Si update es True o
    el golden no existe, lo (re)escribe. Devuelve un mensaje de error si difiere, o
    None si todo bien."""
    golden_file = Path(golden_file)
    if update or not golden_file.exists():
        golden_file.parent.mkdir(parents=True, exist_ok=True)
        # mtime=0 -> gzip determinista (sin timestamp), para no generar diffs
        # espurios en git al regenerar goldens cuyo contenido no cambia.
        golden_file.write_bytes(gzip.compress(actual, mtime=0))
        return None
    expected = gzip.decompress(golden_file.read_bytes())
    if actual == expected:
        return None
    dump = golden_file.with_suffix("")  # quita .gz
    dump = dump.with_name(dump.stem + dump_suffix)
    dump.write_bytes(actual)
    return f"Volcado: {dump}\n\n" + short_diff(expected, actual)
