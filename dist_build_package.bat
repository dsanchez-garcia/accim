@echo off
REM build.bat
REM This script cleans old artifacts and builds the packages for distribution:
REM   - accim          : the library, WITHOUT accim/sample_files (lightweight).
REM   - accim-samples  : accim/sample_files only (installed with
REM                      pip install "accim[samples]").
REM Both distributions get the same version (accim.__version__).

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

ECHO --- [Step 1 of 4] Cleaning previous build artifacts...
REM Delete the contents of old build folders to ensure a clean build.
REM The /s flag is for subdirectories, and /q is for quiet mode (no confirmation).
IF EXIST dist rmdir /s /q dist
IF EXIST build rmdir /s /q build
FOR /d %%d IN (*.egg-info) DO rmdir /s /q "%%d"

ECHO.
ECHO --- [Step 2 of 4] Building the core package 'accim' (without sample_files) using 'py -m build'...
py -m build
IF ERRORLEVEL 1 (
    ECHO ERROR: Fallo el comando de build.
    ECHO Si falta la dependencia, ejecuta: py -m pip install --upgrade build
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- [Step 3 of 4] Building the 'accim-samples' package (accim/sample_files)...
py packaging\build_samples_dist.py
IF ERRORLEVEL 1 (
    ECHO ERROR: Fallo el build de accim-samples.
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- [Step 4 of 4] Verifying build results...
IF NOT EXIST dist (
    ECHO ERROR: The 'dist' directory was not created. The build may have failed.
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- Process complete ---
ECHO The distribution files of 'accim' and 'accim-samples' have been successfully created in the 'dist' directory.
DIR /B dist
PAUSE