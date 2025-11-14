@echo off
echo Generando ejecutable con PyInstaller...
cd /d "C:\Users\user\OneDrive\Escritorio\ALCALDIA-AUDITORIA\audit"

:: Limpiar compilaciones anteriores
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "auditoria_mejorada.spec" del "auditoria_mejorada.spec"

:: Generar el ejecutable
py -m PyInstaller --onefile --console --name "Auditoria" --hidden-import psutil audit\auditoria_mejorada.py
--add-data "audit\pc_info.py;." audit\auditoria_mejorada.py

echo.
echo Ejecutable generado en: dist\Auditoria.exe
echo.
pause