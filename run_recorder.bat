@echo off
echo Iniciando ACC Race Recorder...
echo.

REM Verificar que existe el entorno virtual
if not exist venv (
    echo ERROR: Entorno virtual no encontrado.
    echo Ejecuta primero 'install.bat' para instalar las dependencias.
    pause
    exit /b 1
)

REM Activar entorno virtual y ejecutar
call venv\Scripts\activate.bat
python acc_recorder_gui.py

REM Si hay error, mostrar mensaje
if %errorlevel% neq 0 (
    echo.
    echo Error al ejecutar la aplicacion.
    pause
)
