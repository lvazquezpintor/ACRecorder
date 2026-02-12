#!/bin/bash

# Script para dar permisos de ejecución a los scripts de shell
# Ejecuta este archivo desde la carpeta ACRecorder

echo "Dando permisos de ejecución a los scripts..."
chmod +x install.sh
chmod +x run_recorder.sh

echo "✓ Permisos concedidos"
echo ""
echo "Ahora puedes ejecutar:"
echo "  ./install.sh    - Para instalar dependencias"
echo "  ./run_recorder.sh - Para ejecutar la aplicación"
