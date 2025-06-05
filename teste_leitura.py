#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para leitura de arquivos CSV.
"""

import os
import sys
import io
import pandas as pd

# Configura a saída padrão para usar UTF-8 no Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    print("=== Teste de Leitura de Arquivo CSV ===\n")
    
    # Caminho para o arquivo de exemplo
    input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exemplo_dados.csv')
    
    print(f"Tentando ler o arquivo: {input_file}")
    print(f"Arquivo existe: {os.path.exists(input_file)}")
    
    # Tenta ler o arquivo com diferentes codificações
    encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1', 'utf-16']
    
    for encoding in encodings:
        try:
            print(f"\nTentando ler com {encoding}...")
            df = pd.read_csv(input_file, encoding=encoding)
            print(f"[SUCESSO] Arquivo lido com sucesso usando {encoding}!")
            print("\nPrimeiras linhas do DataFrame:")
            print(df.head())
            print("\nColunas do DataFrame:", df.columns.tolist())
            print("\nTipos de dados:")
            print(df.dtypes)
            return
        except Exception as e:
            print(f"[ERRO] Falha ao ler com {encoding}: {str(e)[:200]}")
    
    print("\nTodas as tentativas de leitura falharam.")

if __name__ == "__main__":
    main()
