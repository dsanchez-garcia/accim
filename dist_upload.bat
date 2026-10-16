@echo off
REM dist_upload.bat
REM Sube a PyPI (el repositorio OFICIAL) la version actual de accim: primero
REM accim-samples y despues accim, desde los archivos que ha dejado
REM dist_build_package.bat en dist\. Antes conviene probarla con
REM dist_upload_test.bat (TestPyPI).
REM
REM packaging\release.py se encarga de las comprobaciones:
REM   - solo sube los archivos de la version de accim\__init__.py; los de otras
REM     versiones que haya en dist\ se ignoran;
REM   - revisa el contenido y los metadatos de las dos distribuciones (twine check);
REM   - omite lo que ya este publicado en PyPI;
REM   - pide escribir la version para confirmar: una version subida no se puede
REM     volver a subir, ni siquiera borrandola.
REM
REM Credenciales: twine las lee del archivo .pypirc de tu carpeta de usuario.
REM Para accim usa la seccion [pypi]; para accim-samples, la seccion
REM [accim-samples] si existe (y esta en index-servers), o si no tambien
REM [pypi]. Un token limitado al proyecto accim no puede subir accim-samples:
REM la primera subida de accim-samples crea el proyecto y necesita un token de
REM toda la cuenta.

REM Ejecuta desde la raiz del proyecto, se llame desde donde se llame.
cd /d "%~dp0"

REM El lanzador 'py' evita usar otro python.exe que este antes en el PATH.
where py >nul 2>&1
IF ERRORLEVEL 1 GOTO no_py

ECHO --- [Paso 1 de 2] Comprobando las herramientas...
py packaging\release.py tools upload || GOTO failed

ECHO.
ECHO --- [Paso 2 de 2] Comprobando y subiendo las distribuciones a PyPI...
py packaging\release.py upload --repository pypi
SET "RC=%ERRORLEVEL%"
ECHO.
PAUSE
EXIT /B %RC%

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
