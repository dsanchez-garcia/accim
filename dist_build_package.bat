@echo off
REM build.bat
REM This script cleans old artifacts and builds the package for distribution.

REM Ensure the script runs from the project root regardless of caller location.
cd /d "%~dp0"

REM Use Python Launcher on Windows to avoid picking a random python.exe from PATH.
where py >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ERROR: No se encontro el lanzador de Python ^('py'^) en el sistema.
    ECHO Instala Python para Windows y vuelve a intentarlo.
    PAUSE
    EXIT /B 1
)

ECHO --- [Step 1 of 3] Cleaning previous build artifacts...
REM Delete the contents of old build folders to ensure a clean build.
REM The /s flag is for subdirectories, and /q is for quiet mode (no confirmation).
IF EXIST dist rmdir /s /q dist
IF EXIST build rmdir /s /q build
FOR /d %%d IN (*.egg-info) DO rmdir /s /q "%%d"

ECHO.
ECHO --- [Step 2 of 3] Building the package using 'py -m build'...
py -m build
IF ERRORLEVEL 1 (
    ECHO ERROR: Fallo el comando de build.
    ECHO Si falta la dependencia, ejecuta: py -m pip install --upgrade build
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- [Step 3 of 3] Verifying build results...
IF NOT EXIST dist (
    ECHO ERROR: The 'dist' directory was not created. The build may have failed.
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- Process complete ---
ECHO The distribution files have been successfully created in the 'dist' directory.
PAUSE