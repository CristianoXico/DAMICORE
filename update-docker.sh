#!/bin/bash

# Script de atualização do Docker DAMICORE v2.1
# Inclui as correções de visualização e melhorias do pipeline

set -e

echo "🐳 ATUALIZANDO DOCKER DAMICORE v2.1 - FILE SLICER PROCESSOR"
echo "==========================================================="

# Verificar se Docker está disponível
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

# Parar e remover containers existentes
echo "🛑 Parando containers DAMICORE existentes..."
docker stop damicore-container 2>/dev/null || true
docker rm damicore-container 2>/dev/null || true

# Remover imagem antiga
echo "🗑️  Removendo imagem antiga..."
docker rmi damicore:latest 2>/dev/null || true
docker rmi damicore:2.0 2>/dev/null || true

# Limpar cache do Docker
echo "🧹 Limpando cache do Docker..."
docker system prune -f

# Construir nova imagem
echo "🔨 Construindo nova imagem DAMICORE v2.1..."
docker build -t damicore:2.1 -t damicore:latest .

# Verificar se a construção foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "✅ Imagem DAMICORE v2.1 construída com sucesso!"
    
    # Mostrar informações da imagem
    echo ""
    echo "📋 INFORMAÇÕES DA NOVA IMAGEM:"
    docker images damicore:latest
    
    echo ""
    echo "🏷️  LABELS DA IMAGEM:"
    docker inspect damicore:latest | grep -A 20 '"Labels"'
    
    echo ""
    echo "🎉 DOCKER DAMICORE v2.1 ATUALIZADO COM SUCESSO!"
    echo ""
    echo "📋 NOVIDADES DESTA VERSÃO:"
    echo "✅ DAMICORE_File_Slicer_Processor.py como script principal"
    echo "✅ Correção de nomes das variáveis nas visualizações"
    echo "✅ Dimensionamento adaptativo para datasets grandes"
    echo "✅ Truncamento inteligente de labels longos"
    echo "✅ Fatiamento automático para arquivos ≥100 linhas"
    echo "✅ Sistema de checkpoint/retomada integrado"
    echo "✅ Suporte a drive externo automático"
    echo "✅ Visualizações corrigidas por fatia"
    echo ""
    echo "🚀 COMANDOS DE EXECUÇÃO:"
    echo "# Básico:"
    echo "docker run -it --rm -v \$(pwd)/data:/app/data -v \$(pwd)/results:/app/results damicore:latest"
    echo ""
    echo "# Com drive externo:"
    echo "docker run -it --rm -v \$(pwd)/data:/app/data -v /external/drive:/app/external_drive -v \$(pwd)/results:/app/results damicore:latest"
    echo ""
    echo "# Modo interativo:"
    echo "docker run -it --rm -v \$(pwd)/data:/app/data -v \$(pwd)/results:/app/results damicore:latest /bin/bash"
    echo ""
    echo "📖 Documentação completa: DOCKER_FILE_SLICER.md"
    
else
    echo "❌ Erro na construção da imagem Docker!"
    exit 1
fi
