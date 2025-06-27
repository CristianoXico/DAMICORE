#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simples para testar o cálculo NCD entre dois arquivos de texto.
"""

import os
import sys

# Adiciona o diretório atual ao PATH para importar os módulos do DAMICORE
current_dir = os.path.abspath('.')
sys.path.insert(0, current_dir)

# Verifica se o diretório damicore_py3 existe
damicore_dir = os.path.join(current_dir, 'damicore_py3')
if not os.path.exists(damicore_dir):
    print(f"Erro: Diretório 'damicore_py3' não encontrado em {current_dir}")
    sys.exit(1)

# Adiciona o diretório damicore_py3 ao PATH
sys.path.insert(0, damicore_dir)

# Tenta importar os módulos necessários
try:
    from ncd import ncd, compression, pairing
except ImportError as e:
    print(f"Erro ao importar módulos do DAMICORE: {e}")
    print("Verifique se os arquivos necessários estão no diretório 'damicore_py3'.")
    sys.exit(1)

def testar_ncd(arquivo1, arquivo2, metodo_compressao='gzip'):
    """Testa o cálculo NCD entre dois arquivos."""
    print(f"\nTestando NCD entre '{os.path.basename(arquivo1)}' e '{os.path.basename(arquivo2)}'")
    
    # Verifica se os arquivos existem
    if not os.path.exists(arquivo1) or not os.path.exists(arquivo2):
        print("Erro: Um ou ambos os arquivos não foram encontrados.")
        return
    
    # Obtém as funções de compressão e emparelhamento
    compressao_fn = compression.get(metodo_compressao)
    if not compressao_fn:
        print(f"Erro: Método de compressão '{metodo_compressao}' não suportado.")
        print(f"Métodos disponíveis: {', '.join(compression.keys())}")
        return
    
    # Usa a função de concatenação para emparelhamento
    emparelhamento_fn = pairing['concat']
    
    try:
        # Calcula o NCD
        resultado = ncd(compressao_fn, emparelhamento_fn, arquivo1, arquivo2)
        
        # Exibe os resultados
        print(f"Tamanho comprimido de {os.path.basename(arquivo1)}: {resultado.zx} bytes")
        print(f"Tamanho comprimido de {os.path.basename(arquivo2)}: {resultado.zy} bytes")
        print(f"Tamanho comprimido do par: {resultado.zxy} bytes")
        print(f"NCD = {resultado.ncd:.4f}")
        
        return resultado.ncd
        
    except Exception as e:
        print(f"Erro ao calcular NCD: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Caminhos para os arquivos de teste
    dir_teste = os.path.join('test_data', 'ncd_input')
    
    # Verifica se o diretório de teste existe
    if not os.path.exists(dir_teste):
        print(f"Erro: Diretório de teste não encontrado: {dir_teste}")
        sys.exit(1)
    
    # Lista os arquivos de teste
    arquivos = [os.path.join(dir_teste, f) for f in os.listdir(dir_teste) 
               if os.path.isfile(os.path.join(dir_teste, f))]
    
    if len(arquivos) < 2:
        print("Erro: Pelo menos 2 arquivos são necessários para o teste.")
        sys.exit(1)
    
    print(f"Arquivos de teste encontrados: {len(arquivos)}")
    
    # Testa diferentes combinações
    for i in range(min(3, len(arquivos))):
        for j in range(i+1, min(i+3, len(arquivos))):
            testar_ncd(arquivos[i], arquivos[j])
