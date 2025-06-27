#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar uma matriz de referência a partir dos arquivos de texto.
"""

import os
import sys
import numpy as np
import pandas as pd
import logging
from pathlib import Path

def carregar_arquivos(diretorio):
    """
    Carrega os arquivos de texto do diretório e retorna um DataFrame.
    
    Args:
        diretorio: Caminho para o diretório com os arquivos de texto
        
    Returns:
        DataFrame com os dados carregados
    """
    dados = {}
    
    # Lista os arquivos .txt no diretório
    arquivos = [f for f in os.listdir(diretorio) if f.endswith('.txt')]
    
    for arquivo in arquivos:
        caminho = os.path.join(diretorio, arquivo)
        try:
            with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
                # Lê todas as linhas do arquivo e remove linhas vazias
                linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
                if linhas:  # Só adiciona se houver linhas válidas
                    # Usa o nome do arquivo sem extensão como chave
                    chave = os.path.splitext(arquivo)[0]
                    dados[chave] = linhas
        except Exception as e:
            print(f"Erro ao ler o arquivo {arquivo}: {e}")
    
    # Converte para DataFrame
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in dados.items()]))
    return df

def calcular_matriz_ncd(df):
    """
    Calcula a matriz NCD a partir de um DataFrame.
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Matriz NCD e lista de rótulos
    """
    import zlib
    
    # Função para calcular o tamanho comprimido
    def tamanho_comprimido(texto):
        if isinstance(texto, str):
            return len(zlib.compress(texto.encode('utf-8')))
        return 0
    
    # Obtém os nomes das colunas (rótulos)
    rotulos = df.columns.tolist()
    n = len(rotulos)
    
    # Inicializa a matriz NCD
    ncd_mat = np.zeros((n, n))
    
    # Pré-calcula os tamanhos comprimidos
    tamanhos = {}
    for i, col in enumerate(rotulos):
        # Concatena todas as linhas não nulas da coluna
        texto = ' '.join(str(x) for x in df[col].dropna())
        tamanhos[col] = tamanho_comprimido(texto)
    
    # Calcula a matriz NCD
    for i in range(n):
        for j in range(i, n):
            if i == j:
                ncd_mat[i, j] = 0.0
            else:
                # Obtém os textos das colunas i e j
                texto_i = ' '.join(str(x) for x in df[rotulos[i]].dropna())
                texto_j = ' '.join(str(x) for x in df[rotulos[j]].dropna())
                
                # Calcula os tamanhos comprimidos
                c_i = tamanhos[rotulos[i]]
                c_j = tamanhos[rotulos[j]]
                c_ij = tamanho_comprimido(texto_i + ' ' + texto_j)
                
                # Calcula o NCD
                ncd = (c_ij - min(c_i, c_j)) / max(c_i, c_j)
                ncd = max(0.0, min(1.0, ncd))  # Garante entre 0 e 1
                
                ncd_mat[i, j] = ncd
                ncd_mat[j, i] = ncd  # Matriz simétrica
    
    return ncd_mat, rotulos

def salvar_matriz_referencia(matriz, rotulos, caminho_saida):
    """
    Salva a matriz de referência e os rótulos em arquivos.
    
    Args:
        matriz: Matriz NCD
        rotulos: Lista de rótulos
        caminho_saida: Caminho para salvar os arquivos
    """
    # Cria o diretório de saída se não existir
    os.makedirs(caminho_saida, exist_ok=True)
    
    # Salva a matriz
    np.savetxt(os.path.join(caminho_saida, 'matriz_referencia.txt'), matriz)
    
    # Salva os rótulos
    with open(os.path.join(caminho_saida, 'rotulos_referencia.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(rotulos))
    
    print(f"Matriz de referência salva em: {os.path.join(caminho_saida, 'matriz_referencia.txt')}")
    print(f"Rótulos salvos em: {os.path.join(caminho_saida, 'rotulos_referencia.txt')}")

def main():
    # Configuração de logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Diretório com os arquivos de texto
    diretorio_dados = 'test_data/portugues'
    
    # Verifica se o diretório existe
    if not os.path.exists(diretorio_dados):
        print(f"Erro: O diretório {diretorio_dados} não existe.")
        sys.exit(1)
    
    # Carrega os arquivos
    print(f"Carregando arquivos de {diretorio_dados}...")
    df = carregar_arquivos(diretorio_dados)
    
    if df.empty:
        print("Nenhum dado válido encontrado nos arquivos.")
        sys.exit(1)
    
    print(f"Arquivos carregados: {len(df.columns)}")
    
    # Calcula a matriz NCD
    print("Calculando matriz NCD...")
    matriz, rotulos = calcular_matriz_ncd(df)
    
    # Salva a matriz de referência
    diretorio_saida = 'test_data/referencia'
    salvar_matriz_referencia(matriz, rotulos, diretorio_saida)
    
    print("\nMatriz de referência gerada com sucesso!")
    print(f"Dimensões: {matriz.shape}")
    print(f"Valores: min={np.min(matriz):.4f}, max={np.max(matriz):.4f}, média={np.mean(matriz):.4f}")

if __name__ == "__main__":
    main()
