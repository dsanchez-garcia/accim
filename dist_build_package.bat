@echo off
REM dist_build_package.bat
REM Construye en dist\ las dos distribuciones de la version actual de accim
REM (__version__ en accim\__init__.py):
REM   - accim         : la libreria SIN accim\sample_files (sdist y wheel).
REM   - accim-samples : solo accim\sample_files (wheel); se instala con
REM                     pip install "accim[samples]".
REM accim[samples] exige accim-samples de la misma version y accim-samples exige
REM accim de la misma version, asi que hay que subir las dos en cada version.
REM
REM Para publicar una version nueva:
REM   1. Cambia __version__ en accim\__init__.py y haz commit (mejor en master).
REM   2. Ejecuta este script.
REM   3. Ejecuta dist_upload_test.bat (TestPyPI, opcional) y dist_upload.bat (PyPI).
REM
REM Los archivos se empaquetan tal como estan en la carpeta de trabajo: el paso 5
REM avisa si hay cambios sin commit.

REM Ejecuta desde la raiz del proyecto, se llame desde donde se llame.
cd /d "%~dp0"

REM El lanzador 'py' evita usar otro python.exe que este antes en el PATH.
where py >nul 2>&1
IF ERRORLEVEL 1 GOTO no_py

ECHO --- [Paso 1 de 5] Comprobando las herramientas...
py packaging\release.py tools build || GOTO failed

ECHO.
ECHO --- [Paso 2 de 5] Borrando dist\, build\ y *.egg-info...
IF EXIST dist rmdir /s /q dist
IF EXIST build rmdir /s /q build
FOR /d %%d IN (*.egg-info) DO rmdir /s /q "%%d"

ECHO.
ECHO --- [Paso 3 de 5] Construyendo accim (sdist y wheel, sin accim\sample_files)...
py -m build || GOTO failed

ECHO.
ECHO --- [Paso 4 de 5] Construyendo accim-samples (wheel con accim\sample_files)...
py packaging\build_samples_dist.py || GOTO failed

ECHO.
ECHO --- [Paso 5 de 5] Comprobando las distribuciones de dist\...
py packaging\release.py check || GOTO failed

ECHO.
ECHO --- Proceso completado ---
ECHO Siguiente paso: dist_upload_test.bat (TestPyPI) o dist_upload.bat (PyPI).
PAUSE
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
