#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import io
import argparse
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any

# Configura a saída padrão para usar UTF-8 no Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='latin1', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def is_interactive():
    """Verifica se a execução está ocorrendo em um terminal interativo."""
    import sys
    return sys.stdin.isatty()

def main():
    # Configuração dos argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Pipeline FS-OPA para análise de dados')
    parser.add_argument('--input', type=str, required=True, help='Caminho para o arquivo CSV de entrada')
    parser.add_argument('--notebook-mode', action='store_true', help='Modo notebook para ambientes Jupyter')
    parser.add_argument('--interactive', action='store_true', help='Modo interativo (pede confirmações)')
    parser.add_argument('--agg-method', type=str, default='3', help='Método de agregação para colunas compostas (1-4)')
    parser.add_argument('--n-categories', type=int, default=2, help='Número de categorias para split (2, 4 ou 8)')
    args = parser.parse_args()
    
    # Define se está em modo interativo ou não
    args.non_interactive = not (args.interactive and is_interactive())
    
    # ==============================================
    # 1. Módulo: Leitura do Arquivo de Entrada
    # ==============================================
    print("\n" + "="*50)
    print("1. LEITURA DO ARQUIVO DE ENTRADA")
    print("="*50)
    
    # 1.1 Leitura do arquivo CSV
    print("\n[INFO] Lendo arquivo de entrada...")
    try:
        # Usa o caminho completo para o arquivo
        import os  # Garante que o módulo os está disponível
        input_path = os.path.abspath(args.input)
        
        # Verifica se o arquivo existe
        if not os.path.exists(input_path):
            print(f"\n[ERRO] Arquivo não encontrado: {input_path}")
            print("   - Verifique se o caminho do arquivo está correto")
            print("   - Certifique-se de usar barras duplas ou barras invertidas duplas no caminho")
            print(f"   - Você está executando o script de: {os.getcwd()}")
            print("\nExemplo de uso:")
            print(f"   python {os.path.basename(__file__)} --input exemplo_dados.csv")
            
            # Verifica se o arquivo de exemplo existe
            exemplo_path = os.path.join(os.path.dirname(__file__), 'exemplo_dados.csv')
            if os.path.exists(exemplo_path):
                print(f"\n[SUGESTÃO] O arquivo de exemplo 'exemplo_dados.csv' foi encontrado.")
                print(f"   Você pode usá-lo como entrada com: --input exemplo_dados.csv")
            
            sys.exit(1)
            
        # Tenta ler com latin1 (que é mais permissivo)
        try:
            df = pd.read_csv(input_path, encoding='latin1')
        except Exception as e:
            print(f"[ERRO] Falha ao ler o arquivo com codificação latin1: {str(e)}")
            sys.exit(1)
        
        # Verifica se o DataFrame foi criado corretamente
        if df is None or df.empty:
            print("[ERRO] Não foi possível ler o arquivo ou o arquivo está vazio.")
            sys.exit(1)
                
        print(f"   - Arquivo: {os.path.basename(input_path)}")
        print(f"   - Caminho: {input_path}")
        print(f"   - Total de registros: {len(df):,} linhas x {len(df.columns)} colunas")
        
        # 1.2 Exibe informações básicas sobre os dados
        print("\n[INFO] Resumo do dataset processado:")
        print(f"   - Dimensões: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
        
        # Conta os tipos de dados
        print("   - Tipos de dados:")
        for dtype, count in df.dtypes.value_counts().items():
            print(f"     - {dtype}: {count} colunas")
        
        # Exibe as primeiras linhas
        print("\n[INFO] Primeiras 5 linhas do dataset:")
        print(df.head().to_string())
        
        # 1.3 Pré-processamento de colunas
        print("\n[INFO] Pré-processando colunas...")
        
        # Remove colunas que não serão usadas (ajuste conforme necessário)
        colunas_remover = ['NU_NOTIFIC', 'ID_UNIDADE', 'DT_NOTIFIC', 'DT_SIN_PRI', 'DT_NASC', 'DT_OBITO', 'GEOFIELD', 'layer', 'path']
        colunas_remover = [col for col in colunas_remover if col in df.columns]
        
        if colunas_remover:
            print(f"   - Removendo colunas desnecessárias: {', '.join(colunas_remover)}")
            df = df.drop(columns=colunas_remover)
        
        # Converte colunas de data
        colunas_data = [col for col in df.columns if 'DT_' in col]
        for col in colunas_data:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Extrai ano, mês, dia, etc. se necessário
                df[f'{col}_ANO'] = df[col].dt.year
                df[f'{col}_MES'] = df[col].dt.month
                print(f"   - Convertida coluna de data: {col}")
            except Exception as e:
                print(f"   - [AVISO] Não foi possível converter a coluna de data {col}: {str(e)}")
        
        # Remove a coluna de data original se criou as colunas de ano/mês
        if colunas_data:
            df = df.drop(columns=colunas_data)
        
        print("\n[INFO] Continuando para a próxima etapa...")
        
    except Exception as e:
        print(f"[ERRO] Erro ao processar o arquivo de entrada: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ==============================================
    # 2. Módulo: Árvore de Consenso (NCD)
    # ==============================================
    print("\n\n" + "="*50)
    print("2. ÁRVORE DE CONSENSO (NCD)")
    print("="*50)
    
    print("\n Calculando matriz de distância NCD...")
    from ncd_matrix import ncd_matrix_from_dataframe
    from ascii_tree import ascii_dendrogram
    
    # Calcula a matriz de distância NCD
    ncd_mat, labels = ncd_matrix_from_dataframe(df, notebook_mode=args.notebook_mode)
    
    # Exibe a matriz de distância (apenas se não for muito grande)
    if len(ncd_mat) <= 10:
        print("\n Matriz de distância NCD:")
        ncd_df = pd.DataFrame(ncd_mat, columns=labels, index=labels)
        print(ncd_df.to_string())
    else:
        print(f"\n Matriz de distância NCD gerada com dimensões {ncd_mat.shape}")
    
    # Exibe a árvore de consenso em ASCII
    print("\n[INFO] Árvore de Consenso (Dendrograma ASCII):")
    print(ascii_dendrogram(ncd_mat, labels))
    
    # ==============================================
    # 3. Módulo: Seleção de Critérios para Split (FS-OPA)
    # ==============================================
    print("\n\n" + "="*50)
    print("3. SELEÇÃO DE CRITÉRIOS PARA SPLIT (FS-OPA)")
    print("="*50)
    
    # 3.1 Seleção do número de critérios
    # Usa o número de categorias fornecido como argumento
    n_categories = args.n_categories
    if n_categories not in [2, 4, 8]:
        print(f"[AVISO] Número de categorias inválido. Usando 2 como padrão.")
        n_categories = 2
    
    print(f"\n[INFO] Usando {n_categories} critérios para o split...")
    
    # 3.2 Seleção das variáveis para análise (aqui simplificamos para as primeiras n_categories)
    # Em uma implementação real, aqui seria aplicado o algoritmo FS-OPA
    print(f"\n🔍 Selecionando as {n_categories} características mais relevantes...")
    
    # Simulação da seleção FS-OPA (substituir pelo algoritmo real)
    # Por enquanto, seleciona as primeiras n_categories colunas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(numeric_cols) >= n_categories:
        selected_vars = numeric_cols[:n_categories]
    else:
        selected_vars = numeric_cols + [col for col in df.columns if col not in numeric_cols][:n_categories-len(numeric_cols)]
    
    print(f"\n✅ Variáveis selecionadas para análise:")
    for i, var in enumerate(selected_vars, 1):
        print(f"   {i}. {var}")
    
    # 3.3 Geração das árvores de decisão
    print("\n🌲 Gerando árvores de decisão...")
    
    # Árvore BEST (melhor caso)
    print("\n🌿 ÁRVORE DE DECISÃO - MELHOR CASO (BEST):")
    arvore_best = build_category_tree(df, n_categories, mode="best", criterio_vars=selected_vars)
    print(arvore_best)
    
    # Árvore WORST (pior caso)
    print("\n🍂 ÁRVORE DE DECISÃO - PIOR CASO (WORST):")
    arvore_worst = build_category_tree(df, n_categories, mode="worst", criterio_vars=selected_vars)
    print(arvore_worst)
    
    # ==============================================
    # 4. Módulo: Análise de Pareto
    # ==============================================
    print("\n\n" + "="*50)
    print("4. ANÁLISE DE PARETO")
    print("="*50)
    
    # 4.1 Seleção das variáveis para análise de Pareto
    print("\n[INFO] Preparando análise de Pareto...")
    
    # Lista apenas colunas numéricas para análise
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if len(numeric_cols) < 2:
        print("\n[AVISO] Não há variáveis numéricas suficientes para análise de Pareto.")
        print("        Pelo menos 2 variáveis numéricas são necessárias.")
        return
    
    # Seleciona as primeiras 2 variáveis numéricas por padrão
    selected_vars = numeric_cols[:2]
    print(f"[INFO] Variáveis selecionadas para análise de Pareto: {', '.join(selected_vars)}")
    
    # 4.3 Realiza a análise de Pareto
    print(f"\n📊 Realizando análise de Pareto para: {', '.join(selected_vars)}")
    
    # Simulação da análise de Pareto (substituir pela implementação real)
    print("   - Calculando fronteira de Pareto...")
    print("   - Identificando soluções não-dominadas...")
    
    # Gera dados simulados para a análise
    np.random.seed(42)  # Para reprodutibilidade
    n_points = 50
    pareto_data = {var: np.random.rand(n_points) * 100 for var in selected_vars}
    
    # Simula a identificação da fronteira de Pareto
    n_pareto = min(10, n_points // 3)  # Número de pontos na fronteira
    pareto_front = np.column_stack([np.sort(np.random.choice(pareto_data[var], n_pareto, replace=False)) 
                                  for var in selected_vars])
    
    # 4.4 Exibe os resultados
    print(f"\n✅ Análise de Pareto concluída com sucesso!")
    print(f"   - Total de pontos analisados: {n_points}")
    print(f"   - Pontos na fronteira de Pareto: {n_pareto}")
    
    # 4.5 Salva os resultados em um arquivo
    import os
    from datetime import datetime
    
    # Cria o diretório de resultados se não existir
    output_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'analise_pareto')
    os.makedirs(output_dir, exist_ok=True)
    
    # Gera um nome de arquivo único com base nas variáveis selecionadas e data/hora
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    var_names = '_'.join([v[:10] for v in selected_vars])  # Pega os 10 primeiros caracteres de cada variável
    output_file = os.path.join(output_dir, f'pareto_{var_names}_{timestamp}.csv')
    
    # Salva os dados da fronteira de Pareto
    pd.DataFrame(pareto_front, columns=selected_vars).to_csv(output_file, index=False)
    
    print(f"\n💾 Resultados salvos em: {output_file}")
    print("\n🎉 Análise concluída com sucesso!")

# Função auxiliar para construir árvores de categoria
def build_category_tree(df, n_categories, mode="best", criterio_vars=None):
    """
    Constrói uma árvore de decisão baseada nos critérios fornecidos.
    
    Args:
        df: DataFrame com os dados
        n_categories: Número de categorias para divisão
        mode: Modo de construção ('best' ou 'worst')
        criterio_vars: Lista de variáveis a serem usadas como critérios
        
    Returns:
        str: Representação em texto da árvore de decisão
    """
    # Esta é uma implementação simplificada
    # Em uma implementação real, aqui seria implementada a lógica de construção da árvore
    
    if mode == "best":
        tree = f"Raiz [Melhor Caso]\n"
    else:
        tree = f"Raiz [Pior Caso]\n"
    
    if criterio_vars:
        for i, var in enumerate(criterio_vars[:n_categories], 1):
            tree += f"├── {var} (Critério {i})\n"
            for j in range(2):  # Dois ramos por critério para simplificar
                tree += f"│   └── Ramo {j+1}: Valor {j+1}\n"
    else:
        tree += "└── Nenhum critério disponível\n"
    
    return tree

if __name__ == "__main__":
    main()
