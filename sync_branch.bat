@echo off
:: Se sitúa en la carpeta donde está el archivo (la raíz del proyecto)
cd /d "%~dp0"

set BRANCH_NAME=%1

if "%BRANCH_NAME%"=="" (
    echo Error: Debes especificar el nombre de la rama.
    echo Uso: sync_branch.bat nombre_de_la_rama
    pause
    exit /b
)

echo ==========================================================
echo Sincronizando rama: %BRANCH_NAME% en la raiz
echo ==========================================================

:: 1. Limpieza de archivos basura
git clean -fd

:: 2. Actualización de datos
git fetch --all

:: 3. Cambiar de rama y traer los cambios
git checkout %BRANCH_NAME%
git pull origin %BRANCH_NAME%

echo ==========================================================
echo PROCESO COMPLETADO
echo ==========================================================
pause