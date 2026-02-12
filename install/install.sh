#!/bin/bash

echo "================================================"
echo "  ACC Race Recorder - Instalación Automática"
echo "================================================"
echo ""

# Verificar Python
echo "[1/4] Verificando Python..."
if ! command -v python3 &> /dev/null
then
    echo "ERROR: Python3 no encontrado. Instala Python 3.8+ desde https://www.python.org/"
    read -p "Presiona Enter para salir..."
    exit 1
fi
python3 --version
echo ""

# Verificar FFmpeg
echo "[2/4] Verificando FFmpeg..."
if ! command -v ffmpeg &> /dev/null
then
    echo ""
    echo "WARNING: FFmpeg no encontrado en el PATH"
    echo ""
    echo "Opciones de instalación:"
    echo "  1. Con Homebrew: brew install ffmpeg"
    echo "  2. Con MacPorts: sudo port install ffmpeg"
    echo "  3. Descarga manual: https://ffmpeg.org/download.html"
    echo ""
    echo "Después de instalar, reinicia esta terminal y ejecuta este script nuevamente."
    echo ""
    read -p "Presiona Enter para salir..."
    exit 1
fi
echo "FFmpeg instalado correctamente"
ffmpeg -version | head -n 1
echo ""

# Crear entorno virtual
echo "[3/4] Creando entorno virtual..."
if [ -d "venv" ]; then
    echo "Entorno virtual ya existe, omitiendo..."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual"
        read -p "Presiona Enter para salir..."
        exit 1
    fi
    echo "Entorno virtual creado"
fi
echo ""

# Activar entorno e instalar dependencias
echo "[4/4] Instalando dependencias..."
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias"
    read -p "Presiona Enter para salir..."
    exit 1
fi
echo ""

echo "================================================"
echo "  INSTALACIÓN COMPLETADA"
echo "================================================"
echo ""
echo "Para ejecutar el ACC Race Recorder:"
echo "  1. Abre una terminal en esta carpeta"
echo "  2. Ejecuta: source venv/bin/activate"
echo "  3. Ejecuta: python3 acc_recorder_gui.py"
echo ""
echo "O usa el archivo 'run_recorder.sh' para ejecutar directamente."
echo ""
read -p "Presiona Enter para salir..."
