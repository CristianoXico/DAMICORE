#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar o DAMICORE atualizado para Python 3.
"""

import sys
import os

# Adiciona o diretório do DAMICORE ao path
sys.path.insert(0, os.path.abspath('damicore_py3'))

try:
    # Tenta importar o módulo DAMICORE
    import damicore
    from ncd import distance_matrix, to_matrix
    
    print("DAMICORE importado com sucesso!")
    print(f"Versão do DAMICORE: {getattr(damicore, '__version__', 'não especificada')}")
    
    # Testa a criação de uma matriz de distância simples
    print("\nTestando cálculo de matriz de distância...")
    diretorio_teste = os.path.abspath('test_data/ncd_input')
    
    if os.path.exists(diretorio_teste):
        print(f"Diretório de teste encontrado: {diretorio_teste}")
        
        # Lista os arquivos no diretório de teste
        arquivos = [os.path.join(diretorio_teste, f) for f in os.listdir(diretorio_teste) 
                   if os.path.isfile(os.path.join(diretorio_teste, f))]
        
        if len(arquivos) >= 2:
            print(f"Arquivos encontrados: {len(arquivos)}")
            
            # Testa com um subconjunto pequeno para verificação
            arquivos_teste = arquivos[:2]
            print(f"Testando com arquivos: {[os.path.basename(f) for f in arquivos_teste]}")
            
            # Calcula a matriz de distância
            try:
                resultados = distance_matrix(
                    directory=diretorio_teste,
                    compression_name='gzip',
                    pairing_name='concat',
                    is_parallel=False
                )
                
                # Converte para matriz
                m, ids = to_matrix(resultados)
                print("\nMatriz de distância calculada com sucesso!")
                print(f"Dimensões: {len(m)}x{len(m[0])}")
                print(f"IDs: {ids}")
                
                # Exibe a matriz
                print("\nMatriz de distância:")
                for i in range(len(m)):
                    print(f"{ids[i]:<15} {m[i]}")
                    
            except Exception as e:
                print(f"Erro ao calcular a matriz de distância: {e}")
                print("Verifique se os compressores (gzip, bzip2) estão instalados no sistema.")
        else:
            print("Número insuficiente de arquivos para teste. Pelo menos 2 arquivos são necessários.")
    else:
        print(f"Diretório de teste não encontrado: {diretorio_teste}")
        print("Certifique-se de que os arquivos de teste estão no local correto.")
    
except ImportError as e:
    print(f"Erro ao importar o DAMICORE: {e}")
    print("Verifique se todas as dependências estão instaladas corretamente.")
    print("Dependências necessárias: igraph, python-igraph, numpy, scipy")
    print("\nPara instalar as dependências, execute:")
    print("pip install igraph python-igraph numpy scipy")

except Exception as e:
    print(f"Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
