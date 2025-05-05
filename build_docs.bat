@echo off
echo Generando archivos fuente de la API con sphinx-apidoc...
sphinx-apidoc -o docs/source ../accim -f
if errorlevel 1 goto error_apidoc

echo.
echo Navegando al directorio docs...
cd docs
if errorlevel 1 goto error_cd_docs

echo.
echo Construyendo la documentación HTML con make.bat...
.\make.bat html
if errorlevel 1 goto error_make_html

echo.
echo Proceso de documentación completado exitosamente.
goto end

:error_apidoc
echo.
echo Error al ejecutar sphinx-apidoc.
goto end

:error_cd_docs
echo.
echo Error al cambiar al directorio docs.
goto end

:error_make_html
echo.
echo Error al ejecutar make.bat.
goto end

:end
pause