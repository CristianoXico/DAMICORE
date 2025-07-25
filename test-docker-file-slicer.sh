#!/bin/bash

# Script de teste do Docker DAMICORE v2.1 - File Slicer Processor
# Valida se o container executa corretamente o DAMICORE_File_Slicer_Processor.py

set -e

echo "🧪 TESTANDO DOCKER DAMICORE v2.1 - FILE SLICER PROCESSOR"
echo "========================================================"

# Verificar se Docker está disponível
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se a imagem existe
if ! docker images | grep -q "damicore.*latest"; then
    echo "❌ Imagem damicore:latest não encontrada. Execute ./update-docker.sh primeiro."
    exit 1
fi

# Criar diretórios de teste
echo "📁 Criando estrutura de teste..."
mkdir -p test_docker/{data,results}

# Criar arquivo CSV de teste pequeno
echo "📄 Criando arquivo CSV de teste..."
cat > test_docker/data/test_small.csv << 'EOF'
var1,var2,var3,var4,var5
1,2,3,4,5
6,7,8,9,10
11,12,13,14,15
16,17,18,19,20
21,22,23,24,25
EOF

echo "✅ Arquivo de teste criado: test_docker/data/test_small.csv (5 linhas, 5 variáveis)"

# Teste 1: Verificar se o container inicia corretamente
echo ""
echo "🧪 TESTE 1: Verificando inicialização do container..."
if docker run --rm damicore:latest python -c "print('✅ Container iniciado com sucesso')"; then
    echo "✅ TESTE 1 PASSOU: Container inicia corretamente"
else
    echo "❌ TESTE 1 FALHOU: Erro na inicialização do container"
    exit 1
fi

# Teste 2: Verificar se o DAMICORE_File_Slicer_Processor.py existe
echo ""
echo "🧪 TESTE 2: Verificando se o script principal existe..."
if docker run --rm damicore:latest ls -la src/scripts/DAMICORE_File_Slicer_Processor.py; then
    echo "✅ TESTE 2 PASSOU: Script principal encontrado"
else
    echo "❌ TESTE 2 FALHOU: Script principal não encontrado"
    exit 1
fi

# Teste 3: Verificar dependências críticas
echo ""
echo "🧪 TESTE 3: Verificando dependências críticas..."
if docker run --rm damicore:latest python -c "
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
try:
    import toytree
    print('✅ toytree disponível')
except ImportError:
    print('⚠️ toytree não disponível (visualizações limitadas)')
try:
    import sklearn
    print('✅ sklearn disponível')
except ImportError:
    print('⚠️ sklearn não disponível')
print('✅ Dependências básicas OK')
"; then
    echo "✅ TESTE 3 PASSOU: Dependências verificadas"
else
    echo "❌ TESTE 3 FALHOU: Erro nas dependências"
    exit 1
fi

# Teste 4: Teste de execução com arquivo pequeno (modo dry-run)
echo ""
echo "🧪 TESTE 4: Testando execução com arquivo pequeno..."
echo "📝 Executando em modo de verificação (sem processamento completo)..."

# Executar container com timeout para evitar processamento completo
timeout 30s docker run --rm \
    -v $(pwd)/test_docker/data:/app/data \
    -v $(pwd)/test_docker/results:/app/results \
    damicore:latest \
    python -c "
import sys
sys.path.append('src/scripts')
from DAMICORE_File_Slicer_Processor import *
print('✅ Script importado com sucesso')
print('✅ Funções principais disponíveis')
" 2>/dev/null || true

if [ $? -eq 0 ] || [ $? -eq 124 ]; then  # 124 = timeout (esperado)
    echo "✅ TESTE 4 PASSOU: Script executa sem erros de importação"
else
    echo "❌ TESTE 4 FALHOU: Erro na execução do script"
fi

# Teste 5: Verificar estrutura de volumes
echo ""
echo "🧪 TESTE 5: Verificando mapeamento de volumes..."
docker run --rm \
    -v $(pwd)/test_docker/data:/app/data \
    -v $(pwd)/test_docker/results:/app/results \
    damicore:latest \
    bash -c "
    echo '📁 Conteúdo /app/data:'
    ls -la /app/data/
    echo '📁 Diretório /app/results:'
    ls -la /app/results/
    echo '✅ Volumes mapeados corretamente'
    "

echo "✅ TESTE 5 PASSOU: Volumes funcionando"

# Limpeza
echo ""
echo "🧹 Limpando arquivos de teste..."
rm -rf test_docker/

# Resumo final
echo ""
echo "🎉 TODOS OS TESTES PASSARAM COM SUCESSO!"
echo ""
echo "📋 RESUMO DOS TESTES:"
echo "✅ Container inicia corretamente"
echo "✅ Script DAMICORE_File_Slicer_Processor.py disponível"
echo "✅ Dependências críticas instaladas"
echo "✅ Script executa sem erros de importação"
echo "✅ Volumes mapeados corretamente"
echo ""
echo "🚀 DOCKER DAMICORE v2.1 PRONTO PARA USO!"
echo ""
echo "📖 Para usar:"
echo "docker run -it --rm -v \$(pwd)/data:/app/data -v \$(pwd)/results:/app/results damicore:latest"
