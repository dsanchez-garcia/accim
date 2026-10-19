# Guía de publicación de accim

Esta guía reúne lo necesario para publicar una versión de accim: construir las dos distribuciones,
probarlas, subirlas a TestPyPI y a PyPI, y cerrar la versión (etiqueta, release de GitHub y Read the
Docs). Los detalles de cada script están en su docstring o en sus comentarios; aquí se resumen. Lo
que toca a la documentación al publicar está en [../docs/README.md](../docs/README.md) (§8).

Revisada el 19/10/2026, con accim 0.8.2.

## 1. Qué se publica

- Cada versión son **dos distribuciones**, con el mismo número:
  - `accim`: la librería, sin `accim/sample_files` (sdist y wheel);
  - `accim-samples`: solo `accim/sample_files` (wheel), que se instala con
    `pip install "accim[samples]"`.
- Se exigen la una a la otra: el extra `samples` de accim pide `accim-samples==X.Y.Z`, y
  accim-samples pide `accim==X.Y.Z`. Por eso hay que subir las dos en cada versión.
- El número está en un solo sitio: `__version__` en `accim/__init__.py`. `setup.py` importa accim
  para leerlo, y `build_samples_dist.py` lo lee del archivo sin importar accim.
- Páginas: <https://pypi.org/project/accim/> y <https://pypi.org/project/accim-samples/> (en
  TestPyPI, <https://test.pypi.org/project/accim/> y <https://test.pypi.org/project/accim-samples/>).
- **Una versión no se puede volver a subir, ni siquiera después de borrarla**, ni en PyPI ni en
  TestPyPI. Cualquier arreglo necesita un número nuevo: la 0.8.1 solo añadió `pulp<4` a la 0.8.0.

## 2. Archivos y scripts

| Qué | Dónde |
|---|---|
| Versión | [../accim/__init__.py](../accim/__init__.py) (`__version__`) |
| Metadatos de accim: dependencias, extra `samples`, versiones de Python | [../setup.py](../setup.py) |
| Qué entra en el sdist de accim | [../MANIFEST.in](../MANIFEST.in) (`prune accim/sample_files`) |
| Descripción de accim en PyPI | [../README.md](../README.md) |
| Plantilla de accim-samples (`setup.py`, `MANIFEST.in`, `README.md`) | [accim-samples/](accim-samples) |
| Construye accim-samples | [build_samples_dist.py](build_samples_dist.py) |
| Comprueba las distribuciones y las sube | [release.py](release.py) |
| Construye las dos distribuciones | [../dist_build_package.bat](../dist_build_package.bat) |
| Sube a TestPyPI o a PyPI | [../dist_upload_test.bat](../dist_upload_test.bat) y [../dist_upload.bat](../dist_upload.bat) |
| Historial de versiones | [../CHANGELOG.md](../CHANGELOG.md) |
| Salida | `dist/`, más `build/` y `*.egg-info` (git los ignora) |

Los otros `.bat` de la raíz no intervienen: `dist_build_docs.bat` compila la documentación, y
`reinstall_*.bat` y `sync_branch.bat` sirven para probar ramas.

## 3. Lo que hace falta (una vez)

- El lanzador `py` de Python para Windows: los `.bat` lo usan para no tomar otro `python.exe` del
  PATH.
- Las herramientas: `build` para construir, y `twine` 6.1 o posterior para subir (las anteriores
  no leen los metadatos 2.4 que escribe setuptools). `py packaging\release.py tools build` y
  `py packaging\release.py tools upload` las comprueban y ofrecen instalar las que falten; los
  `.bat` lo hacen en su primer paso.
- Las credenciales, en `%USERPROFILE%\.pypirc`, de donde las lee twine. Nunca las copies en el
  repositorio ni las muestres:

  ```ini
  [distutils]
  index-servers =
      pypi
      testpypi

  [pypi]
  username = __token__
  password = <token de PyPI>

  [testpypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = <token de TestPyPI>
  ```

  Los tokens de `[pypi]` y `[testpypi]` valen para toda la cuenta (19/10/2026). Si quieres un
  token por proyecto, añade las secciones `[accim-samples]` y `[testpypi-accim-samples]` (con
  `repository`, `username` y `password`) y ponlas en `index-servers`: `release.py` las usa para
  accim-samples. La primera subida de un proyecto lo crea, y eso necesita un token de toda la
  cuenta.

## 4. Paso a paso

### 4.1 Antes de empezar

1. Decide el número. `CHANGELOG.md` dice que el proyecto sigue Semantic Versioning: arreglos, la
   última cifra (0.8.1); funciones nuevas, la del medio (0.9.0). El autor publicó como 0.8.2 una
   versión con funciones nuevas.
2. Todo lo que va en la versión tiene que estar en `master`, y los tests tienen que pasar:

   ```
   py -m pytest tests/core tests/parametric_and_optimisation
   ```

   Con la 0.8.2 pasaron 130 y 209. Algunos tests de `tests/core` ejecutan EnergyPlus, con las
   versiones instaladas.
3. Revisa los textos de la documentación que cambian con la versión: lista de la §8 de
   [../docs/README.md](../docs/README.md).

### 4.2 Commit de la versión

1. Cambia `__version__` en `accim/__init__.py`.
2. En `CHANGELOG.md`, convierte lo que hay bajo `## [Unreleased]` en `## [X.Y.Z] - AAAA-MM-DD`,
   deja encima un `## [Unreleased]` vacío y actualiza los enlaces del final:

   ```
   [Unreleased]: https://github.com/dsanchez-garcia/accim/compare/vX.Y.Z...HEAD
   [X.Y.Z]: https://github.com/dsanchez-garcia/accim/compare/v<anterior>...vX.Y.Z
   ```

3. Haz el commit con el mensaje `Release vX.Y.Z`, con un resumen en el cuerpo. Deja la copia de
   trabajo limpia: las distribuciones se construyen con los archivos tal como están, y
   `release.py` avisa si hay cambios sin commit en `accim`, `setup.py`, `MANIFEST.in`, `README.md`
   o `packaging/accim-samples`.

### 4.3 Construir y comprobar

Ejecuta `dist_build_package.bat` (doble clic, o desde cmd). Sus cinco pasos:

1. comprueba las herramientas;
2. borra `dist\`, `build\` y `*.egg-info`;
3. construye accim, sdist y wheel (`py -m build`);
4. construye la wheel de accim-samples (`py packaging\build_samples_dist.py`), que copia
   `accim/sample_files` (sin `__pycache__` ni `.ipynb_checkpoints`), la plantilla de
   `packaging/accim-samples`, `LICENSE` y un archivo `VERSION` a `build\samples_stage`, la
   construye ahí y avisa si pasa de 100 MB, el límite de PyPI por archivo;
5. comprueba `dist\` (`py packaging\release.py check`): que están las dos wheels y el sdist de la
   versión, que la wheel de accim no lleva `sample_files` y su extra pide `accim-samples==X.Y.Z`,
   que la de accim-samples solo lleva `accim/sample_files` y pide `accim==X.Y.Z`, y pasa
   `twine check --strict`. Los archivos de otras versiones que haya en `dist\` se ignoran.

Tamaños con la 0.8.2: la wheel de accim, 0,6 MB; su sdist, 0,5 MB; la wheel de accim-samples,
21,4 MB, con 133 archivos de muestra.

### 4.4 Probar las wheels en un entorno limpio, antes de subir nada

Instala las wheels de `dist\` en un entorno nuevo, con las dependencias de PyPI, desde una carpeta
fuera del repositorio. En la raíz del repositorio, pip toma tu copia de desarrollo
(`accim.egg-info`). Así se habría visto antes de publicar la 0.8.0 que pip instalaba PuLP 4 y que
`accim.parametric_and_optimisation` no se importaba. En tu Python había PuLP 3.3.0, y los tests no
lo vieron. En cmd:

```
cd /d C:\tmp
py -m venv C:\tmp\accim_test
C:\tmp\accim_test\Scripts\python -m pip install --find-links D:\Python\accim\dist "accim[samples]==X.Y.Z"
C:\tmp\accim_test\Scripts\python -m pip check
C:\tmp\accim_test\Scripts\python -c "import accim, os; from accim.parametric_and_optimisation import ParametricSimulation, OptimisationSimulation; from accim.data.preprocessing import rename_epw_files; from accim.sim import accis; d = os.path.join(os.path.dirname(accim.__file__), 'sample_files'); print(accim.__version__, accim.__file__); print(sum(len(f) for _, _, f in os.walk(d)), 'sample files')"
```

La última orden tiene que dar la versión nueva, una ruta dentro de `C:\tmp\accim_test` (no
`D:\Python\accim`) y unos 133 archivos de muestra. Para una prueba más completa, genera con
`addAccis()` un IDF del `TestModel` de muestra y simula un día con EnergyPlus. Al terminar, borra
el entorno (`rmdir /s /q C:\tmp\accim_test`).

Si algo falla, corrige, haz un commit nuevo y vuelve a §4.3: todavía no se ha publicado nada.

### 4.5 Etiqueta

Pon la etiqueta en el commit de la versión, ligera como las anteriores:

```
git tag vX.Y.Z
```

No la subas todavía (§4.8).

### 4.6 TestPyPI

1. Ejecuta `dist_upload_test.bat`, que lanza `py packaging\release.py upload --repository testpypi
   --verbose`. Vuelve a comprobar `dist\`, dice qué está ya publicado (lo salta), sube primero
   accim-samples y después accim (si falla la primera subida, no queda publicado un accim cuyo
   extra no se puede instalar) y antes pide escribir la versión para confirmar.
2. Prueba la instalación desde TestPyPI en otro entorno nuevo. Instala de TestPyPI solo accim y
   accim-samples, y sus dependencias de PyPI: cualquiera puede subir a TestPyPI paquetes con los
   nombres de las dependencias, así que no uses el `--extra-index-url` que sugiere el script.

   ```
   py -m venv C:\tmp\accim_testpypi
   C:\tmp\accim_testpypi\Scripts\python -m pip install --no-deps --index-url https://test.pypi.org/simple/ accim==X.Y.Z accim-samples==X.Y.Z
   C:\tmp\accim_testpypi\Scripts\python -c "from importlib.metadata import requires; print('\n'.join(r for r in requires('accim') if 'extra ==' not in r))" > C:\tmp\deps.txt
   C:\tmp\accim_testpypi\Scripts\python -m pip install -r C:\tmp\deps.txt
   C:\tmp\accim_testpypi\Scripts\python -m pip check
   ```

   Después, la misma comprobación de imports que en §4.4.

Si algo falla aquí, TestPyPI ya no deja volver a subir esa versión: para probar el arreglo en
TestPyPI hace falta otro número (en PyPI, X.Y.Z sigue libre).

### 4.7 PyPI

1. Ejecuta `dist_upload.bat`: hace lo mismo que en §4.6, en PyPI.
2. Prueba la instalación desde PyPI en otro entorno nuevo, sin la caché de pip:

   ```
   py -m venv C:\tmp\accim_pypi
   C:\tmp\accim_pypi\Scripts\python -m pip install --no-cache-dir "accim[samples]==X.Y.Z"
   C:\tmp\accim_pypi\Scripts\python -m pip check
   ```

   y la comprobación de imports de §4.4. Justo después de subir, pip puede decir «No matching
   distribution found» aunque la página ya muestre la versión: la CDN de PyPI tarda unos minutos
   (3 con la 0.8.1, 1 con la 0.8.2). Espera y repite.

### 4.8 Subir a GitHub

```
git push origin master
git push origin vX.Y.Z
```

**Nunca uses `git push --tags` ni `--follow-tags`:** la etiqueta local
`archive/codex-paper-simple-energy` no se publica. Con el push, Read the Docs compila `master` y
`latest` con la versión nueva.

### 4.9 Release de GitHub

Se llama `Version vX.Y.Z`, sale de la etiqueta y lleva adjuntos los tres archivos de `dist\`. Con
la CLI de GitHub (desde la raíz):

```
gh release create vX.Y.Z dist/accim-X.Y.Z-py3-none-any.whl dist/accim-X.Y.Z.tar.gz dist/accim_samples-X.Y.Z-py3-none-any.whl --repo dsanchez-garcia/accim --title "Version vX.Y.Z" --notes-file notas.md
```

Las notas de la 0.8.2 (`gh release view v0.8.2 --repo dsanchez-garcia/accim`) siguen este orden:
un bloque **Installation** con `pip install accim` y `pip install "accim[samples]"`; un párrafo con
lo principal de la versión y cómo actualizar (`pip install --upgrade "accim[samples]"`); avisos de
lo que cambia para los usuarios; un enlace a la release v0.8.0, la que separó accim-samples; el
enlace a la documentación; y la sección de la versión del `CHANGELOG.md`.

### 4.10 Read the Docs

Activa la versión `vX.Y.Z` en Read the Docs y comprueba su página: §2 de
[../docs/README.md](../docs/README.md).

### 4.11 Registro

Anota la publicación en `DEVLOG.md` (entrada `Release X.Y.Z`: contexto, cambios, archivos,
comprobaciones y siguiente paso) y en `notes/work-log.md`, y haz el commit
(`docs: log the X.Y.Z release`).

## 5. Desde Git Bash o un agente

- `cmd //c dist_build_package.bat < /dev/null`: con la entrada vacía, los `PAUSE` siguen solos.
  Desde Git Bash, `cmd` hereda el PATH de Git, donde `find` y `sort` son los de Unix: no los uses
  en los `.bat`.
- `printf 'X.Y.Z\n' | py packaging/release.py upload --repository pypi` confirma la versión sin
  escribirla.
- `py packaging/release.py upload --repository pypi --dry-run` hace las comprobaciones y muestra las
  órdenes de twine sin subir nada.
- Para esperar a que PyPI muestre la versión, un bucle de Python con `time.sleep`; un bucle de Bash
  en segundo plano con `sleep 30` terminó al minuto, sin esperar.
- Para saber qué versión hay publicada: `https://pypi.org/pypi/accim/json` (`info.version`).

## 6. Problemas frecuentes

- **`400 File already exists` o «filename has already been used».** Esa versión ya se subió:
  cambia `__version__` y construye de nuevo.
- **`403 Forbidden`.** El token de esa sección de `.pypirc` no puede subir ese proyecto: la primera
  subida de un proyecto necesita un token de toda la cuenta (§3). Si falla accim-samples, accim no
  se ha subido; si falla accim, accim-samples ya está y basta con lanzar el script otra vez.
- **«No matching distribution found» justo después de subir.** La CDN de PyPI (§4.7).
- **pip instala tu copia de desarrollo en vez de la publicada.** Estás en la raíz del repositorio:
  prueba desde otra carpeta y en un entorno nuevo (§4.4).
- **`pip show accim` dice 0.7.6 en tu Python.** La instalación editable conserva los metadatos de
  cuando se hizo (0.7.6, el 19/10/2026): el código que se importa es el del repositorio, pero pip e
  `importlib.metadata` ven la versión y las dependencias de entonces (sin geopy, `pulp<4`, SALib ni
  seaborn). `py -m pip install -e .`, desde la raíz, los actualiza.
- **`release.py` avisa de cambios sin commit.** Las distribuciones llevan esos archivos tal como
  están: haz commit (o apártalos) y construye de nuevo.
- **`py -m build` falla al importar accim.** `setup.py` importa accim para leer la versión, en un
  entorno aislado sin las dependencias: `accim/__init__.py` solo puede importar dependencias dentro
  de `try`/`except`, como ya hace con besos.
- **Una versión nueva de una dependencia rompe accim** (PuLP 4 con la 0.8.0). Acótala en
  `install_requires` de `setup.py`, con un comentario que explique por qué, y publica un arreglo.

## 7. Pendiente (19/10/2026)

- La wheel de accim instala también el paquete `tests` (61 archivos) en site-packages, porque
  `setuptools.find_packages()` de `setup.py` encuentra `tests/__init__.py`. Se arreglaría
  excluyéndolo (`exclude=SAMPLES_PACKAGES + ['tests', 'tests.*']`) en la próxima versión, y
  `release.py check` podría comprobarlo.
