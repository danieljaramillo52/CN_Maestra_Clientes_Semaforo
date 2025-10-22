@echo off
echo ===============================
echo Ejecucion proyecto maestra univeros directa...
echo ===============================

echo Ejecutando la automatizacion...

REM Ir a la carpeta raiz del proyecto (sube desde bat/)
cd /d "%~dp0\.."

REM Ejecutar streamlit usando el python embebido
.\python-3.12.5-emb\python.exe src\main.py

echo.
echo  Proceso finalizado.
echo Cierre esta ventana o presione una tecla para continuar.
pause
