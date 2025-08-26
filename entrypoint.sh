#!/bin/bash
set -e

# Configura o PATH para incluir o diretório de binários do usuário
export PATH="/home/damicore/.local/bin:${PATH}"

# Verifica se o pandas está instalado no sistema ou no diretório do usuário
if ! python -c "import pandas" &> /dev/null; then
    echo "Pandas não encontrado. Instalando dependências..."
    # Instala no diretório do usuário para garantir permissões corretas
    pip install --user --no-cache-dir -r /app/requirements.txt
fi

# Executa o script principal com o Python do sistema
exec python /app/src/scripts/DAMICORE_File_Slicer_Processor.py "$@"
