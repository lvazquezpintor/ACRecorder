@echo off
echo ================================================
echo   ACC Race Recorder - Instalacion Automatica
echo ================================================
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado. Instala Python 3.8+ desde https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Verificar FFmpeg
echo [2/4] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: FFmpeg no encontrado en el PATH
    echo.
    echo Opciones de instalacion:
    echo   1. Con Chocolatey: choco install ffmpeg
    echo   2. Descarga manual: https://ffmpeg.org/download.html
    echo.
    echo Despues de instalar, reinicia esta terminal y ejecuta este script nuevamente.
    echo.
    pause
    exit /b 1
)
echo FFmpeg instalado correctamente
echo.

REM Crear entorno virtual
echo [3/4] Creando entorno virtual...
if exist venv (
    echo Entorno virtual ya existe, omitiendo...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo Entorno virtual creado
)
echo.

REM Activar entorno e instalar dependencias
echo [4/4] Instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo.

echo ================================================
echo   INSTALACION COMPLETADA
echo ================================================
echo.
echo Para ejecutar el ACC Race Recorder:
echo   1. Abre una terminal en esta carpeta
echo   2. Ejecuta: venv\Scripts\activate
echo   3. Ejecuta: python acc_recorder.py
echo.
echo O usa el archivo 'run_recorder.bat' para ejecutar directamente.
echo.
pause
