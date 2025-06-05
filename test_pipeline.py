#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para o pipeline FS-OPA.

Este script testa as principais funcionalidades do pipeline:
1. Leitura e pré-processamento de dados
2. Cálculo da matriz NCD e geração da árvore de consenso
3. Seleção de critérios FS-OPA
4. Análise de Pareto
"""

import os
import sys
import pandas as pd
import numpy as np
from pipeline_novo import main as run_pipeline
from fs_opa import aplicar_fs_opa, exportar_resultados_fs_opa
from pareto_analysis import analisar_fronteira_pareto, exportar_resultados_pareto

def test_ncd_matrix():
    """Testa o cálculo da matriz NCD."""
    print("\n=== Testando cálculo da matriz NCD ===")
    
    # Dados de exemplo
    data = {
        'col1': [1, 2, 3, 4, 5],
        'col2': [1.1, 2.2, 3.3, 4.4, 5.5],
        'col3': ['a', 'b', 'c', 'd', 'e']
    }
    df = pd.DataFrame(data)
    
    # Importa a função de cálculo da matriz NCD
    from ncd_matrix import ncd_matrix_from_dataframe
    
    try:
        ncd_mat, labels = ncd_matrix_from_dataframe(df)
        print(f"Matriz NCD calculada com sucesso! Dimensões: {ncd_mat.shape}")
        print(f"Labels: {labels}")
        return True
    except Exception as e:
        print(f"Erro ao calcular matriz NCD: {e}")
        return False

def test_fs_opa():
    """Testa a seleção de variáveis FS-OPA."""
    print("\n=== Testando seleção de variáveis FS-OPA ===")
    
    # Dados de exemplo com grupos
    np.random.seed(42)
    n = 100
    data = {
        'feature1': np.random.normal(0, 1, n),
        'feature2': np.random.normal(5, 2, n),
        'feature3': np.random.normal(10, 3, n),
        'cluster': np.random.choice([0, 1, 2], size=n)
    }
    df = pd.DataFrame(data)
    
    try:
        # Aplica FS-OPA
        resultado = aplicar_fs_opa(df, n_variaveis=2)
        print("Variáveis selecionadas:", resultado['variaveis_selecionadas'])
        
        # Exporta resultados
        output_dir = os.path.join(os.getcwd(), 'test_results')
        os.makedirs(output_dir, exist_ok=True)
        
        export_path = exportar_resultados_fs_opa(resultado, output_dir)
        print(f"Resultados exportados para: {export_path}")
        return True
    except Exception as e:
        print(f"Erro na análise FS-OPA: {e}")
        return False

def test_pareto_analysis():
    """Testa a análise de Pareto."""
    print("\n=== Testando análise de Pareto ===")
    
    # Dados de exemplo
    np.random.seed(42)
    n = 50
    data = {
        'custo': np.random.uniform(10, 100, n),
        'qualidade': np.random.uniform(0.5, 1.0, n),
        'tempo': np.random.uniform(1, 24, n)
    }
    df = pd.DataFrame(data)
    
    try:
        # Realiza análise de Pareto
        objetivos = ['custo', 'qualidade']
        maximizar = [False, True]  # Minimizar custo, maximizar qualidade
        
        resultado = analisar_fronteira_pareto(
            df, 
            objetivos,
            maximizar=maximizar,
            normalizar=True,
            calcular_hipervol=True
        )
        
        print(f"Soluções na fronteira de Pareto: {resultado['n_solucoes']}")
        
        # Exporta resultados
        output_dir = os.path.join(os.getcwd(), 'test_results')
        os.makedirs(output_dir, exist_ok=True)
        
        export_path = exportar_resultados_pareto(
            resultado['fronteira'],
            objetivos,
            output_dir,
            prefixo="teste_pareto"
        )
        print(f"Resultados exportados para: {export_path}")
        return True
    except Exception as e:
        print(f"Erro na análise de Pareto: {e}")
        return False

def test_full_pipeline():
    """Testa o pipeline completo com dados de exemplo."""
    print("\n=== Testando pipeline completo ===")
    
    # Caminho para o arquivo de exemplo
    input_file = os.path.join(os.getcwd(), 'exemplo_dados.csv')
    
    if not os.path.exists(input_file):
        print(f"Arquivo de exemplo não encontrado: {input_file}")
        return False
    
    try:
        # Executa o pipeline
        import sys
        sys.argv = ['pipeline_novo.py', '--input', input_file]
        
        # Redireciona a saída padrão para capturar a saída
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        # Executa o pipeline
        run_pipeline()
        
        # Restaura a saída padrão
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Verifica se a execução foi bem-sucedida
        if "Análise concluída com sucesso" in output:
            print("✅ Pipeline executado com sucesso!")
            return True
        else:
            print("❌ Falha na execução do pipeline")
            print("Saída:", output)
            return False
    except Exception as e:
        print(f"Erro ao executar o pipeline: {e}")
        return False

if __name__ == "__main__":
    print("=== Iniciando testes do pipeline FS-OPA ===\n")
    
    # Executa os testes
    test_results = {
        'NCD Matrix': test_ncd_matrix(),
        'FS-OPA': test_fs_opa(),
        'Análise de Pareto': test_pareto_analysis(),
        'Pipeline Completo': test_full_pipeline()
    }
    
    # Exibe resumo dos testes
    print("\n=== Resumo dos Testes ===")
    for test_name, result in test_results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    # Conta quantos testes passaram
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes foram aprovados!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique as mensagens de erro acima.")
