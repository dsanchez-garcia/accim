@echo off
REM dist_upload.bat
REM Este script sube las distribuciones del paquete al repositorio OFICIAL de PyPI.
REM Asume que el archivo .pypirc está correctamente configurado.

REM Asegura ejecución desde la raíz del proyecto.
cd /d "%~dp0"

REM Usa el lanzador de Python para evitar conflictos con otros python.exe en PATH.
where py >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ERROR: No se encontro el lanzador de Python ^('py'^) en el sistema.
    PAUSE
    EXIT /B 1
)

ECHO --- [Paso 1 de 2] Verificando que el directorio 'dist' existe...
IF NOT EXIST dist (
    ECHO ERROR: El directorio 'dist' no fue encontrado.
    ECHO Por favor, construye el paquete primero ejecutando: dist_build_package.bat
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- [Paso 2 de 2] Subiendo distribuciones a PyPI...
REM Al no especificar --repository, twine usa la configuración 'pypi' por defecto.
py -m twine upload dist/*
IF ERRORLEVEL 1 (
    ECHO ERROR: Fallo la subida a PyPI.
    ECHO Si falta twine, instala con: py -m pip install --upgrade twine
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- Proceso completado ---
ECHO ¡Tu paquete debería estar disponible públicamente en PyPI!
PAUSE