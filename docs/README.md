# Guía de la documentación de accim

Esta guía reúne lo necesario para mantener la documentación de accim en Read the Docs
(<https://accim.readthedocs.io>): dónde está cada cosa, cómo se publica, cómo se compila en local y
cómo se regeneran las páginas de los notebooks. Sphinx solo lee `docs/source`, así que esta guía no
sale en Read the Docs. Los detalles de cada script están en su docstring; aquí se resumen.

Revisada el 19/10/2026, con accim 0.8.2.

## 1. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Configuración de Sphinx (extensiones, versión, LaTeX) | [source/conf.py](source/conf.py) |
| Configuración de Read the Docs | [../.readthedocs.yaml](../.readthedocs.yaml) |
| Paquetes que instala Read the Docs | [requirements.txt](requirements.txt) |
| Portada y menú lateral (`toctree`) | [source/index.rst](source/index.rst) |
| Guía de usuario (Markdown con MyST) | `source/1_requirements.md` a `source/7_credits.md` |
| Documentación de versiones anteriores | [source/8_pdfs_for_prev_versions.md](source/8_pdfs_for_prev_versions.md) y `source/_static/previous_versions_pdfs/` |
| Páginas del módulo paramétrico (reST) | `source/parametric_and_optimisation.rst`, `source/hourly_plotting.rst` y `source/filter_output_csvs.rst` |
| Referencia de la API (generada, §6) | `source/api/*.rst` |
| **Notebooks ejecutados, con sus resultados (lo que muestra Read the Docs)** | [source/jupyter_notebooks/](source/jupyter_notebooks) (§7.1) |
| Notebooks fuente, sin resultados (los que se editan) | [../accim/sample_files/jupyter_notebooks/](../accim/sample_files/jupyter_notebooks) |
| Scripts que ejecutan los notebooks y los exportan | [prepare_howto_notebooks.py](prepare_howto_notebooks.py) y [prepare_parametric_notebooks.py](prepare_parametric_notebooks.py) |
| Compilación local | [../dist_build_docs.bat](../dist_build_docs.bat), o `python -m sphinx` (§3) |
| Tabla completa de consignas | `source/html_files/full_setpoint_table.html` |
| Imágenes y estilo | `source/images/` y `source/_static/custom.css` |
| Salida de la compilación local | `_build/` (git la ignora) |

## 2. Cómo se publica (Read the Docs)

- Cada push a `master` compila en Read the Docs (proyecto `accim`) las versiones `master` y
  `latest`, con lo que haya en el repositorio; tarda 4-5 minutos. No hay vistas previas de los pull
  requests: lo que se ve es lo que está en `master` o en una etiqueta.
- Entorno (`.readthedocs.yaml`): Ubuntu 22.04 y Python 3.9. Instala accim desde el repositorio
  (`pip install .`) y `docs/requirements.txt`. `conf.py` importa accim para leer la versión
  (`accim.__version__`, que sale en los títulos) y los docstrings. Formatos: HTML, PDF y EPUB.
- `docs/requirements.txt` es solo para Read the Docs (Python 3.9, `numpy<2`, `matplotlib<=3.7`): no
  lo instales en tu Python.
- Versiones: `latest` (la de por defecto) y `master` siguen la rama `master`; las etiquetas `v0.7.5`
  a `v0.8.2` están activas, cada una con su HTML, PDF y EPUB, y aparecen en el menú de Read the Docs
  (abajo a la derecha de cada página). `stable` está desactivada: `/en/stable/` da 404.
- **Al publicar una versión**, Read the Docs ve la etiqueta nueva, pero no la compila hasta
  activarla: en el panel del proyecto, Versions → «Add version» (o «Edit», si ya aparece) → marcar
  «Active» → «Update version». Hace falta la sesión del autor (con GitHub). Después, comprueba que
  `https://accim.readthedocs.io/en/vX.Y.Z/` dice «accim X.Y.Z documentation».
- Consultar las compilaciones sin entrar en el panel (API pública):
  - últimas compilaciones (versión, estado, commit y duración):
    <https://readthedocs.org/api/v2/build/?project__slug=accim&limit=5>
  - una compilación, con la salida de cada orden y los avisos de Sphinx:
    `https://readthedocs.org/api/v2/build/<id>/`
  - versiones activas y sus descargas:
    <https://readthedocs.org/api/v2/version/?project__slug=accim&active=true>
- PDF: Read the Docs lo compila con pdflatex y no falla por errores de LaTeX, así que un carácter
  Unicode que pdflatex no conoce desaparece del PDF sin que nada lo avise. Los que usan las páginas
  (λ, ≤, −, ⌈, ⌉ y algunos emoji) están definidos en `latex_elements` de `conf.py`: añade ahí los
  nuevos. Los 9 errores «Too deeply nested» del paso de LaTeX vienen de docstrings.
- **URL que imprime el código.** `addAccis()` imprime enlaces a la portada, a cinco páginas de
  How-to y a `4_detailed%20use.html`, siempre en `/en/master/` (`accim/sim/accis.py`,
  `accis_single_idf.py` y `accis_single_idf_funcs.py`), y `accim/sim/accim_IDFgeneration.py` enlaza
  `html_files/full_setpoint_table.html` en GitHub (con htmlpreview). `README.md` también enlaza
  páginas. Si renombras o mueves una de esas páginas, cambia el código y añade una redirección en
  la configuración del proyecto en Read the Docs (Redirects), porque las versiones ya publicadas
  seguirán imprimiendo la URL antigua. Por eso `4_detailed use.md` y `3_quick tutorial.md` (cuya
  URL imprimían versiones antiguas) conservan los espacios en el nombre.

## 3. Compilar en local

Conviene compilar en local y mirar los avisos antes de subir cambios de las páginas.

- Herramientas: sphinx, sphinx-rtd-theme, nbsphinx, myst-parser, ipython y pandoc (nbsphinx lo usa
  para las celdas Markdown de los notebooks). `py packaging\release.py tools docs` comprueba los
  paquetes, ofrece instalar los que falten y avisa si falta pandoc.
- **Opción 1**: `dist_build_docs.bat`, en la raíz. Comprueba las herramientas, borra `docs\_build`,
  regenera la referencia de la API (§6), compila el HTML y cuenta los avisos. Si han cambiado las
  páginas de la API, lo dice: haz commit de `docs/source/api`.
- **Opción 2**, solo compilar, sin tocar la API (desde la raíz; unos 2 minutos):

  ```
  python -m sphinx -E -b html docs/source docs/_build/html -w docs/_build/sphinx_warnings.txt
  ```

  `make.bat html`, desde `docs`, también sirve (necesita `sphinx-build` en el PATH). El `Makefile`
  no: apunta a `.` en lugar de a `source`.
- El resultado está en `docs/_build/html/index.html`. La salida tiene que estar en la misma unidad
  que las fuentes: con las fuentes en D: y la salida en C:, Sphinx falla al calcular rutas
  relativas entre unidades.
- Avisos: el 19/10/2026 había 41 en local, todos de docstrings (pendiente, §10). En Read the Docs
  salen 39 de docstrings y 5 más, ya conocidos: el del resolvedor de pip al instalar,
  `too large :maxdepth:` (del `toctree` de la portada), el tipo MIME del PDF de 0.6.12 (en el EPUB)
  y dos «Could not fetch remote image» de la figura de ComfMod de `4_detailed use.md`, que se
  enlaza desde MDPI: MDPI responde 403 a Read the Docs, así que la figura se ve en el HTML pero
  falta en el PDF y en el EPUB. Para ver solo los avisos que no son de docstrings (cmd; en Git Bash,
  `grep -v "docstring of"`):

  ```
  findstr /V /C:"docstring of" docs\_build\sphinx_warnings.txt
  ```

  Un aviso que no venga de docstrings suele ser un enlace roto, una página que no está en ningún
  `toctree` o un error de sintaxis de una página.
- En un venv, crea el venv con `--system-site-packages` o instala en él las herramientas. Si
  nbconvert no encuentra sus plantillas, define `JUPYTER_PATH=<Python base>\share\jupyter`.

## 4. Escribir y cambiar páginas

- Las páginas de la guía de usuario son Markdown con MyST (`.md`); la portada y las del módulo
  paramétrico, reST (`.rst`). Toda página tiene que estar en un `toctree` de `index.rst` (o de otro
  índice, como `jupyter_notebooks/parametric_and_optimisation_examples/index.rst`).
- Enlaces internos: en MyST, `` {doc}`jupyter_notebooks/Table/using_Table` `` y
  `` {ref}`etiqueta` ``; en reST, `:doc:` y `:ref:`.
- La versión de accim en el texto: en `.md`, `{{ version }}` (definido con `myst_substitutions` en
  `conf.py`); `|version|` solo funciona en `.rst`. Ninguna de las dos se sustituye dentro de un
  bloque de código.
- Las celdas de las tablas pueden partir líneas gracias a `_static/custom.css` (sphinx-rtd-theme
  pone `nowrap`).
- **Textos repetidos que hay que cambiar a la vez:**
  - el rango de versiones de EnergyPlus (hoy, 9.1 a 26.2): `README.md`, `1_requirements.md`,
    `4_detailed use.md` (transcripciones, tabla de argumentos y texto), `5_troubleshooting.md`, el
    texto de `using_addAccis` y `full_example_IBPSA` (en las fuentes; después, exportar, §7.2) y,
    en el código, los mensajes y docstrings de `accim/sim/accis.py`, `accim/sim/accis_single_idf.py`,
    `accim/sim/accis_single_idf_funcs.py`, `accim/run/run.py`, `accim/utils.py`, `accim/lists.py` y
    `accim/sim/lists.py`. Para encontrarlos todos: `git grep -nF "26.2"`;
  - la versión de accim en las dos cabeceras de las transcripciones de `4_detailed use.md`
    («Adaptive-Comfort-Control-Implemented Model (ACCIM) vX.Y.Z», §5);
  - la instalación y los requisitos: `README.md` es también la descripción de accim en PyPI (lo lee
    `setup.py`), así que tiene que decir lo mismo que `1_requirements.md` y `2_installation.md`;
    accim-samples tiene la suya, `packaging/accim-samples/README.md`, que también explica la
    instalación.

## 5. Transcripciones de `addAccis()` en Detailed use

`4_detailed use.md` copia dos transcripciones de `addAccis()`: las preguntas, las respuestas y lo
que imprime.

- Si solo cambia la versión, edita a mano las dos cabeceras.
- Para regenerarlas, ejecuta `addAccis()` con un `input()` que lea las respuestas de un archivo y
  las imprima tras cada pregunta, como si se hubieran escrito. Guarda esto como `transcript.py`:

  ```python
  # Run addAccis() answering its questions with the lines of answers.txt (an empty line is
  # hitting enter), and print each question followed by its answer, as if it was typed.
  import builtins

  answers = iter(open('answers.txt', encoding='utf-8').read().splitlines())


  def scripted_input(prompt=''):
      answer = next(answers)
      print(f'{prompt}{answer}')
      return answer


  builtins.input = scripted_input

  from accim.sim import accis  # noqa: E402

  accis.addAccis()
  ```

  En `answers.txt` va una respuesta por línea: lo que hay tras los dos puntos de cada pregunta en la
  transcripción (una línea vacía es pulsar Intro). Las respuestas de los notebooks están en
  `ANSWERS` de `prepare_howto_notebooks.py`. Ejecútalo en una carpeta con una copia de
  `accim/sample_files/jupyter_notebooks/addAccis/TestModel.idf`, con
  `python transcript.py > transcript.txt`, y copia lo que haga falta: la página corta la parte
  central de la salida con puntos.

## 6. Referencia de la API

- `source/api/*.rst` los genera `sphinx-apidoc`: un archivo por paquete, con `automodule` y las
  opciones `:members:`, `:undoc-members:` y `:show-inheritance:`. No los edites a mano:
  `dist_build_docs.bat` los regenera con

  ```
  py -m sphinx.ext.apidoc --force -o docs\source\api accim "accim/sample_files/*"
  ```

  Las funciones y clases nuevas de un módulo que ya existe aparecen solas. Un módulo o un paquete
  nuevo necesita regenerarlos y hacer commit de `docs/source/api`.
- Los docstrings están en reST, con `:param:` y `:type:` (napoleon entiende también los estilos de
  Google y NumPy). Los avisos de formato de la compilación salen de ellos.

## 7. Páginas de los notebooks

### 7.1 Dónde están

Read the Docs no ejecuta los notebooks (`nbsphinx_execute = 'never'` en `conf.py`, porque
necesitan EnergyPlus): muestra copias ya ejecutadas, con los resultados guardados, que están en
`docs/source/jupyter_notebooks/`. **No edites esas copias.** Edita la fuente, en
`accim/sample_files/jupyter_notebooks/` (sin resultados; es lo que se distribuye en accim-samples),
y regenera la copia con su script (§7.2 y §7.3).

How-to Guides:

| Página | Copia ejecutada, en `docs/source/jupyter_notebooks/` | Fuente, en `accim/sample_files/jupyter_notebooks/` | Tiempo |
|---|---|---|---|
| Using addAccis() | `addAccis/using_addAccis.ipynb` | `addAccis/` | 1 min |
| Using rename_epw_files() | `rename_epw_files/using_rename_epw_files.ipynb` | `rename_epw_files/` | < 2 min |
| Using runEp() | `runEp/using_runEp.ipynb` | `runEp/` | < 2 min |
| Using the class Table() | `Table/using_Table.ipynb` | `Table/` | 2 min |
| Full example (IBPSA) | `full_example_IBPSA/full_example_IBPSA.ipynb` | `full_example_IBPSA/` | 6 min |
| Research paper case study | `research_paper_case_study/research_paper_case_study.ipynb` | `research_paper_case_study_v0-7-3/` | 27 min |
| aPMV setpoints | `example_apmv_setpoints_paper/using_apmv_setpoints.ipynb` | `example_apmv_setpoints_paper/` | < 2 min |

Simulación paramétrica y optimización: los tutoriales `00` a `10` y los flujos completos `wf1` a
`wf5`, con el mismo nombre en `docs/source/jupyter_notebooks/parametric_and_optimisation_examples/`
(copias ejecutadas) y en `accim/sample_files/jupyter_notebooks/parametric_and_optimisation_examples/`
(fuentes). El `index.rst` de esa carpeta de la documentación, que presenta los notebooks y da los
tiempos de los flujos completos, no es un notebook: se edita directamente.

### 7.2 Regenerar las páginas de How-to

```
python docs/prepare_howto_notebooks.py run --run-dir D:\runs --only using_addAccis full_example_IBPSA
python docs/prepare_howto_notebooks.py export --executed-dir D:\runs --only using_addAccis full_example_IBPSA
```

- Sin `--only`, los siete. `--only` admite el nombre del notebook o el de su carpeta, o su
  principio.
- `run` borra y vuelve a copiar la subcarpeta de cada notebook dentro de la carpeta de trabajo, lo
  ejecuta ahí (las muestras no cambian) y deja `<nombre>_executed.ipynb`. Al final da el tiempo y
  los problemas de cada notebook. Contesta a las preguntas de `input()` con `ANSWERS` del script y
  avisa si sobran o faltan respuestas: si cambian las preguntas de un notebook, cambia `ANSWERS`.
- Usa una carpeta de trabajo con una ruta corta, como `D:\runs`: EnergyPlus falla si la ruta de un
  archivo de salida pasa de 260 caracteres, y los nombres de los archivos de accim son largos.
- Necesitan EnergyPlus 25.1, la versión de sus modelos. `rename_epw_files()` necesita además
  internet (OpenStreetMap) y geopy.
- `export` toma la copia ejecutada más reciente y la limpia antes de escribirla en
  `docs/source/jupyter_notebooks/`: rutas relativas o genéricas, sin barras de progreso, registros
  de más de 100 líneas acortados (las 30 primeras y las 15 últimas, con
  «[... n lines not shown in the documentation ...]») y figuras reducidas (`--max-width`, 1400 px
  por defecto). No exporta, y escribe «NOT EXPORTED», si el notebook tiene errores, si su código no
  coincide con la fuente o si queda una ruta personal (`\Users\`, `AppData`, `OneDrive` o el nombre
  de usuario).

### 7.3 Regenerar las páginas paramétricas

```
python docs/prepare_parametric_notebooks.py run --run-dir D:\runs_param --only 05 wf1
python docs/prepare_parametric_notebooks.py export --executed-dir D:\runs_param --only 05 wf1
```

- Sin `--only`, todos: los tutoriales `00` a `10` en orden y después `wf1` a `wf5`. `--only` admite
  el principio del nombre (`05`, `wf1`). `run` copia los notebooks y los IDF y EPW de muestra a la
  carpeta de trabajo; `export` hace la misma limpieza que en §7.2.
- Los tutoriales 09 y 10 leen los resultados de 02 y 07: ejecuta antes esos dos. Para refrescar 09
  sin cambiar 02 y 07, copia `nb02_parametric_predefined_results` y
  `nb07_basic_optimization_results` de la carpeta de la ejecución anterior a la nueva, y exporta
  con las dos carpetas (`--executed-dir` se puede repetir).
- Necesitan EnergyPlus 25.2. Tiempos del 16/10/2026, con 12 CPU lógicas: los tutoriales sin el 03,
  unos 10 min; `wf1`, 3 min; `wf2`, 6 min; `wf3`, 1-2 min; `wf4`, 7,5 min; `wf5`, 3-3,5 min.
- Resultados aleatorios: solo `wf4` y `wf5` fijan una semilla. 00, 01, 05 y `wf1` (LHS, Sobol y
  Morris) y 07 y 08 (NSGA-II) dan valores nuevos en cada ejecución; en `wf4` y `wf5` cambia el
  orden de las filas (se evalúan en paralelo), y con él los índices y algunos píxeles de sus
  figuras. Para comprobar una regeneración, mira las páginas deterministas: 02, 04, 06, `wf2` y
  `wf3`.
- Antes de cambiar el contenido de `wf1`-`wf5` o de `00`-`10`, lee
  `llm_project_files/HANDOFF_notebooks_claude_code.md` (carpeta local, fuera de git): relaciona los
  notebooks con el artículo. Los notebooks van en inglés, sin rutas personales y con simulaciones
  ligeras que dan resultados anuales (las explica el `index.rst` de la sección).

### 7.4 Comprobar una página regenerada

Cambios normales entre dos ejecuciones: la cabecera de versión de accim, las direcciones de los
objetos (`0x...`), los tiempos, los metadatos de ejecución, el orden de las zonas y de algunas
columnas (salen de conjuntos de Python y cambian de una ejecución a otra) y qué parte de un
registro largo queda recortada (depende de los trozos en que llega la salida). En un notebook
determinista, las tablas y las figuras de resultados no deberían cambiar.

Para verlo, este script compara las salidas de una página con las de una revisión de git (`HEAD`,
si no se indica): dice qué celdas cambian de código, las primeras líneas de texto distintas de cada
celda y si sus figuras cambian. Ejecútalo desde la raíz, con
`python compare_page.py docs/source/jupyter_notebooks/Table/using_Table.ipynb`:

```python
# Changes in the outputs of a notebook page against a git revision (HEAD by default).
# Usage, from the root of the repository: python compare_page.py <page.ipynb> [<revision>]
import difflib
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
page, rev = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'HEAD')
old = json.loads(subprocess.run(['git', 'show', f'{rev}:{page}'], capture_output=True, check=True).stdout)
new = json.load(open(page, encoding='utf-8'))


def outputs(cell):
    texts, images = [], []
    for o in cell.get('outputs', []):
        data = o.get('data', {})
        texts.append(''.join(o.get('text', data.get('text/plain', ''))))
        images += [''.join(data['image/png'])] if 'image/png' in data else []
    return '\n'.join(texts).splitlines(), images


for i, (a, b) in enumerate(zip(old['cells'], new['cells'])):
    (text_a, images_a), (text_b, images_b) = outputs(a), outputs(b)
    if ''.join(a['source']) != ''.join(b['source']):
        print(f'cell {i}: the source changed')
    if text_a != text_b:
        diff = [d for d in difflib.unified_diff(text_a, text_b, lineterm='', n=0)
                if d[:1] in '+-' and d[:3] not in ('+++', '---')]
        print(f'cell {i}: {len(diff)} lines of text differ', *diff[:8], sep='\n    ')
    if images_a != images_b:
        print(f'cell {i}: the figures differ')
```

### 7.5 Ejecutar los notebooks con otra copia de accim

Los notebooks importan el accim instalado, que está en modo editable y apunta a `D:\Python\accim`.
Para usar otra copia (un worktree, o el código de un commit mientras la copia de trabajo tiene
otros cambios), pon su carpeta la primera en `PYTHONPATH`. Por ejemplo, en Git Bash:

```
git archive <commit> accim ":(exclude)accim/sample_files" | tar -x -C <carpeta>
export PYTHONPATH=<carpeta>
```

`run` anota qué copia usó, y `export` quita también esa ruta de las salidas.

## 8. Al publicar una versión

Lo que toca a la documentación. La construcción del paquete y la subida a PyPI están en
[../packaging/README.md](../packaging/README.md).

1. `__version__` en `accim/__init__.py`: `conf.py` la lee, así que las páginas la muestran en
   cuanto se compila `master`.
2. Las dos cabeceras de las transcripciones de `4_detailed use.md` (§5).
3. Si cambian las versiones de EnergyPlus, los requisitos o la instalación, los textos repetidos de
   §4.
4. `CHANGELOG.md`, y el registro del trabajo en `DEVLOG.md` y `notes/work-log.md`.
5. Tras subir la etiqueta, activa la versión en Read the Docs (§2) y comprueba
   `/en/vX.Y.Z/` y su PDF. `8_pdfs_for_prev_versions.md` no cambia: el menú de Read the Docs añade
   la versión solo.
6. Opcional: vuelve a ejecutar las páginas que imprimen la cabecera de `addAccis()` con la versión:
   `using_addAccis`, `full_example_IBPSA` y `research_paper_case_study` (unos 35 min en total,
   §7.2) y, si quieres, las de los 12 notebooks paramétricos que también la imprimen (todos salvo
   03, 09, `wf3` y `wf5`, §7.3), sabiendo que cambian sus resultados aleatorios.

## 9. Dudas y problemas frecuentes

- **Una página de notebook muestra una versión vieja de accim o un texto viejo.** Son salidas
  guardadas: corrige la fuente si hace falta y regenera la página (§7).
- **`|version|` sale tal cual en una página `.md`.** Usa `{{ version }}`.
- **Falta un carácter en el PDF.** Defínelo en `latex_elements` de `conf.py` (§2).
- **Sphinx falla con un error de rutas entre unidades.** Pon la salida en la misma unidad que las
  fuentes (§3).
- **EnergyPlus no puede abrir `eplusout.audit` u otro archivo de salida.** La ruta pasa de 260
  caracteres: usa una carpeta de trabajo corta (§7.2).
- **`export` escribe «NOT EXPORTED».** Lee el motivo: errores en el notebook, código distinto de la
  fuente o rutas personales en las salidas (§7.2).
- **`/en/stable/` da 404.** La versión `stable` está desactivada; los enlaces usan `/en/master/`.
- **Las zonas salen en otro orden que en la versión anterior de la página.** Salen de un conjunto
  (`set`); la tarea está en `TODO.md` («Deterministic order of the occupied zones in
  `scan_zones`»).
- **`make html` no funciona en `docs`.** El `Makefile` apunta a `.`; usa §3.

## 10. Pendiente (19/10/2026)

- Los avisos de formato de los docstrings (41 en local, 39 en Read the Docs).
- La figura de ComfMod de `4_detailed use.md` se enlaza desde MDPI y falta en el PDF y el EPUB; se
  arreglaría copiándola a `source/images`, con su cita.
- Las páginas de 12 notebooks paramétricos imprimen todavía «(ACCIM) v0.7.8», una versión que
  nunca se publicó.
- Una redirección en Read the Docs de `jupyter_notebooks/full_example/full_example.html`, que
  imprimen accim 0.7.7 y anteriores, a `full_example_IBPSA` (propuesta, no hecha).
- Otras mejoras de la revisión del 16/10/2026 (una referencia de la API con solo lo público,
  dividir Detailed use, el contenido duplicado entre `README.md` y la documentación): sección 5 de
  `llm_project_files/REVISION_DOCUMENTACION_2026-10-16.md` (local).

Las tareas activas están en `TODO.md`.

## 11. Registro de los cambios

Cada bloque de trabajo se anota en `DEVLOG.md` (con la plantilla del principio del archivo) y, en
corto, en `notes/work-log.md`. Los cambios que ve el usuario van a `CHANGELOG.md` al preparar la
versión.
