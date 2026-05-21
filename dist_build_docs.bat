@echo off
REM build_docs.bat
REM Este script automatiza la generación de la documentación de accim.
REM Debe ser ejecutado desde la raíz del proyecto.

REM Asegura ejecución desde la raíz del proyecto.
cd /d "%~dp0"

REM Usa el lanzador de Python para evitar conflictos con otros python.exe en PATH.
where py >nul 2>&1
IF ERRORLEVEL 1 (
	ECHO ERROR: No se encontro el lanzador de Python ^('py'^) en el sistema.
	PAUSE
	EXIT /B 1
)

ECHO --- [Paso 1 de 3] Limpiando compilaciones anteriores...
REM Borra el contenido de la carpeta de salida para asegurar una compilación limpia.
REM El flag /Q ejecuta el borrado sin pedir confirmación.
IF EXIST docs\_build rmdir /s /q docs\_build

ECHO.
ECHO --- [Paso 2 de 3] Generando archivos .rst de la API con sphinx-apidoc...
REM Ejecuta sphinx-apidoc para generar/actualizar los archivos .rst desde el código fuente.
REM -o docs\source\api: Directorio de salida para los archivos .rst.
REM accim: Ruta al paquete que se va a documentar.
REM accim/sample_files/*: Patrón para excluir archivos que no deben ser documentados.
REM --force: Sobrescribe los archivos existentes.
py -m sphinx.ext.apidoc --force -o docs\source\api accim accim/sample_files/*
IF ERRORLEVEL 1 (
	ECHO ERROR: Fallo la generacion de archivos .rst.
	ECHO Instala dependencias con: py -m pip install -r docs\requirements.txt
	PAUSE
	EXIT /B 1
)

ECHO.
ECHO --- [Paso 3 de 3] Construyendo la documentación HTML con Sphinx...
REM Ejecuta Sphinx sin depender de scripts externos en PATH.
py -m sphinx -M html docs\source docs\_build
IF ERRORLEVEL 1 (
	ECHO ERROR: Fallo la construccion HTML de la documentacion.
	PAUSE
	EXIT /B 1
)

ECHO.
ECHO --- Proceso completado ---
ECHO La documentacion HTML ha sido generada en: docs\_build\html\index.html
PAUSE