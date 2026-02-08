#!/bin/bash

# Script para ejecutar ACC Race Recorder en Mac
# Equivalente a run_recorder.bat

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: No se encontró el entorno virtual."
    echo "Ejecuta primero ./install.sh"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Ejecutar la aplicación GUI
echo "Iniciando ACC Race Recorder GUI..."
python3 acc_recorder_gui.py

# Mantener la terminal abierta si hay error
if [ $? -ne 0 ]; then
    echo ""
    echo "Error al ejecutar la aplicación"
    read -p "Presiona Enter para salir..."
fi
