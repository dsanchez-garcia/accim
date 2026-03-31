@echo off
REM dist_upload_test.bat
REM Este script sube las distribuciones del paquete al repositorio de PRUEBAS (TestPyPI).
REM Asume que el archivo .pypirc está correctamente configurado.

ECHO --- [Paso 1 de 2] Verificando que el directorio 'dist' existe...
IF NOT EXIST dist (
    ECHO ERROR: El directorio 'dist' no fue encontrado.
    ECHO Por favor, construye el paquete primero ejecutando: dist_build_package.bat
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO --- [Paso 2 de 2] Subiendo distribuciones a TestPyPI...
twine upload --repository testpypi dist/* --verbose

ECHO.
ECHO --- Proceso completado ---
ECHO Revisa tu paquete en: https://test.pypi.org/project/accim/
PAUSE