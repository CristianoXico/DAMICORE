#!/bin/bash
set -e

# Verifica se o pandas está instalado
if ! python -c "import pandas" &> /dev/null; then
    echo "Pandas não encontrado. Instalando dependências..."
    pip install --no-cache-dir -r /app/requirements.txt
fi

# Executa o script principal
exec python /app/src/scripts/DAMICORE_File_Slicer_Processor.py "$@"
