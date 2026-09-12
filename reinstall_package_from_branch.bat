@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "PACKAGE="
set "BRANCH="
set "DRY_RUN=0"

:parse_args
if "%~1"=="" goto args_done

if /I "%~1"=="--dry-run" (
  set "DRY_RUN=1"
  shift
  goto parse_args
)

if not defined PACKAGE (
  set "PACKAGE=%~1"
) else if not defined BRANCH (
  set "BRANCH=%~1"
) else (
  echo [WARN] Argumento extra ignorado: %~1
)

shift
goto parse_args

:args_done
if not defined PACKAGE set "PACKAGE=accim"
if not defined BRANCH set "BRANCH=refactor/modular-setast"

set "OWNER=dsanchez-garcia"
set "REPO_URL=https://github.com/%OWNER%/%PACKAGE%.git"

where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro el launcher de Python ^("py"^) en PATH.
  exit /b 1
)

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro git en PATH. Es necesario para instalar desde rama.
  exit /b 1
)

echo [INFO] Paquete: %PACKAGE%
echo [INFO] Rama: %BRANCH%
echo [INFO] Repositorio: %REPO_URL%
echo.

if "%DRY_RUN%"=="1" (
  echo [DRY-RUN] py -m pip uninstall -y %PACKAGE%
  echo [DRY-RUN] py -m pip install --upgrade "git+%REPO_URL%@%BRANCH%"
  exit /b 0
)

echo [INFO] Desinstalando %PACKAGE% (si existe)...
py -m pip uninstall -y %PACKAGE%
if errorlevel 1 (
  echo [WARN] La desinstalacion devolvio error. Continuando con la instalacion...
)

echo.
echo [INFO] Instalando el ultimo commit de %BRANCH%...
py -m pip install --upgrade "git+%REPO_URL%@%BRANCH%"
if errorlevel 1 (
  echo [ERROR] Fallo la instalacion desde %REPO_URL%@%BRANCH%.
  exit /b 1
)

echo.
echo [OK] Instalacion completada.
echo [INFO] Datos del paquete instalado:
py -m pip show %PACKAGE% | findstr /R "^Name: ^Version: ^Location:"

exit /b 0


