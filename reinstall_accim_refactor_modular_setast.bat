@echo off
setlocal EnableExtensions

set "REPO_SPEC=git+https://github.com/dsanchez-garcia/accim.git@refactor/modular-setast"
set "PYTHON_CMD="
set "SCRIPT_DIR=%~dp0"
set "DRY_RUN=0"

if /I "%~1"=="--dry-run" set "DRY_RUN=1"

REM 1) Si hay venv activo, usarlo.
if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" set "PYTHON_CMD=%VIRTUAL_ENV%\Scripts\python.exe"
)

REM 2) Si no hay venv activo, buscar venv locales comunes.
if not defined PYTHON_CMD if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" set "PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not defined PYTHON_CMD if exist "%SCRIPT_DIR%venv\Scripts\python.exe" set "PYTHON_CMD=%SCRIPT_DIR%venv\Scripts\python.exe"
if not defined PYTHON_CMD if exist "%SCRIPT_DIR%env\Scripts\python.exe" set "PYTHON_CMD=%SCRIPT_DIR%env\Scripts\python.exe"

REM 3) Fallback al Python global.
if not defined PYTHON_CMD set "PYTHON_CMD=python"

echo.
echo Usando interprete: "%PYTHON_CMD%"
echo.

if "%DRY_RUN%"=="1" (
    echo [DRY-RUN] "%PYTHON_CMD%" -m pip uninstall -y accim
    echo [DRY-RUN] "%PYTHON_CMD%" -m pip install --upgrade "%REPO_SPEC%"
    exit /b 0
)

"%PYTHON_CMD%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: No se pudo ejecutar pip con "%PYTHON_CMD%".
    echo Revisa que Python/pip esten disponibles en ese entorno.
    exit /b 1
)

echo [1/2] Desinstalando accim actual...
"%PYTHON_CMD%" -m pip uninstall -y accim
if errorlevel 1 (
    echo AVISO: La desinstalacion devolvio error o no habia una instalacion previa.
)

echo [2/2] Instalando version desde git (rama refactor/modular-setast)...
"%PYTHON_CMD%" -m pip install --upgrade "%REPO_SPEC%"
if errorlevel 1 (
    echo ERROR: Fallo la instalacion desde GitHub.
    exit /b 1
)

echo.
echo Listo. accim se ha instalado desde:
echo %REPO_SPEC%
echo.
exit /b 0

