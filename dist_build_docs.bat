@echo off
REM dist_build_docs.bat
REM Construye en local la documentacion HTML de accim (docs\_build\html).
REM
REM Read the Docs construye la documentacion publica por su cuenta en cada push
REM a master (ver .readthedocs.yaml), con lo que haya en el repositorio. Este
REM script sirve para revisarla antes y para regenerar las paginas de la API.
REM
REM - docs\source\api se regenera con sphinx-apidoc a partir del codigo. No
REM   edites esos archivos a mano: este script los sobrescribe. Si cambian, haz
REM   commit de docs\source\api para que Read the Docs muestre los cambios.
REM - Las paginas de notebooks son copias ya ejecutadas (nbsphinx_execute =
REM   'never' en docs\source\conf.py): aqui no se ejecuta ningun notebook. Las
REM   de parametric_and_optimisation se regeneran con
REM   docs\prepare_parametric_notebooks.py (run y export).
REM - accim-samples no afecta a la documentacion: conf.py importa accim desde la
REM   raiz del repositorio y la documentacion no usa accim\sample_files.
REM - Los avisos de Sphinx quedan tambien en docs\_build\sphinx_warnings.txt.

REM Ejecuta desde la raiz del proyecto, se llame desde donde se llame.
cd /d "%~dp0"

REM El lanzador 'py' evita usar otro python.exe que este antes en el PATH.
where py >nul 2>&1
IF ERRORLEVEL 1 GOTO no_py

ECHO --- [Paso 1 de 4] Comprobando las herramientas...
py packaging\release.py tools docs || GOTO failed

ECHO.
ECHO --- [Paso 2 de 4] Borrando la compilacion anterior (docs\_build)...
IF EXIST docs\_build rmdir /s /q docs\_build

ECHO.
ECHO --- [Paso 3 de 4] Regenerando las paginas de la API (docs\source\api)...
REM "accim/sample_files/*" deja fuera los archivos de ejemplo.
py -m sphinx.ext.apidoc --force -o docs\source\api accim "accim/sample_files/*" || GOTO failed

ECHO.
ECHO --- [Paso 4 de 4] Construyendo la documentacion HTML con Sphinx...
py -m sphinx -M html docs\source docs\_build -w docs\_build\sphinx_warnings.txt || GOTO failed

ECHO.
ECHO --- Proceso completado ---
ECHO Documentacion HTML: docs\_build\html\index.html
REM Cuenta las lineas con avisos (sin "find", que puede ser el de Git en el PATH).
SET "NWARN=0"
FOR /F "delims=" %%l IN ('findstr /C:"WARNING:" /C:"ERROR:" "docs\_build\sphinx_warnings.txt"') DO SET /A NWARN+=1
ECHO Avisos de Sphinx: %NWARN% (lista en docs\_build\sphinx_warnings.txt)
git status --porcelain -- docs/source/api 2>nul | findstr . >nul
IF ERRORLEVEL 1 GOTO ask_open
ECHO.
ECHO Han cambiado las paginas de la API. Haz commit de docs\source\api para que
ECHO Read the Docs las muestre:
git status --short -- docs/source/api

:ask_open
ECHO.
SET "ANSWER="
SET /P "ANSWER=Abrir la documentacion en el navegador? [S/N]: "
IF /I "%ANSWER%"=="S" START "" "docs\_build\html\index.html"
EXIT /B 0

:no_py
ECHO ERROR: No se encontro el lanzador de Python ('py').
ECHO Instala Python para Windows y vuelve a intentarlo.
PAUSE
EXIT /B 1

:failed
ECHO.
ECHO ERROR: El proceso se ha detenido; revisa los mensajes de arriba.
PAUSE
EXIT /B 1
