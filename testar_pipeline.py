#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar o pipeline completo do DAMICORE Python 3.
"""

import os
import sys
import shutil
import tempfile
import numpy as np
from pipeline_novo import generate_ncd_matrix_damicore, visualize_consensus_trees

def criar_arquivos_teste(diretorio, n_arquivos=5, tamanho=1000):
    """Cria arquivos de teste com conteúdo aleatório."""
    os.makedirs(diretorio, exist_ok=True)
    
    print(f"\nCriando {n_arquivos} arquivos de teste em {diretorio}")
    
    for i in range(n_arquivos):
        # Gera conteúdo aleatório para cada arquivo
        conteudo = f"Arquivo de teste {i+1}\n" + "="*50 + "\n"
        
        # Adiciona linhas de texto aleatórias
        for _ in range(tamanho // 10):  # Aproximadamente o tamanho desejado
            linha = f"Linha {_+1}: " + " ".join([f"palavra_{j}" for j in range(10)]) + "\n"
            conteudo += linha
        
        # Salva o arquivo
        caminho = os.path.join(diretorio, f"teste_{i+1}.txt")
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print(f"  - {caminho} ({len(conteudo)} bytes)")

def testar_pipeline():
    """Testa o pipeline completo do DAMICORE Python 3."""
    # Cria um diretório temporário para os testes
    temp_dir = tempfile.mkdtemp(prefix="teste_damicore_")
    print(f"\n📁 Diretório temporário para testes: {temp_dir}")
    
    try:
        # Cria arquivos de teste
        dados_dir = os.path.join(temp_dir, "dados")
        criar_arquivos_teste(dados_dir, n_arquivos=5)
        
        # 1. Gera a matriz NCD
        print("\n🔍 Gerando matriz NCD...")
        ncd_matrix, labels = generate_ncd_matrix_damicore(
            input_dir=dados_dir,
            compressor="gzip",
            max_workers=1  # Usa 1 worker para evitar problemas de concorrência
        )
        
        print("\n✅ Matriz NCD gerada com sucesso!")
        print(f"Dimensões: {ncd_matrix.shape}")
        print(f"Rótulos: {', '.join(labels)}")
        
        # 2. Gera as visualizações
        print("\n🎨 Gerando visualizações...")
        resultados = visualize_consensus_trees(ncd_matrix, labels)
        
        if resultados and 'arquivos_gerados' in resultados:
            print("\n📂 Arquivos gerados:")
            for tipo, caminho in resultados['arquivos_gerados'].items():
                print(f"  - {tipo.replace('_', ' ').title()}: {caminho}")
        
        print("\n✅ Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Remove o diretório temporário após o teste
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"\n🗑️  Diretório temporário removido: {temp_dir}")
        except Exception as e:
            print(f"\n⚠️  Não foi possível remover o diretório temporário: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando teste do pipeline DAMICORE Python 3")
    testar_pipeline()
