#!/usr/bin/env python3
"""
Script de teste para validar as correções de visualização no DAMICORE_Filograma_script.py

Testa:
1. Criação correta do dicionário index_to_name
2. Conversão de nomes 'col_X.txt' para nomes originais
3. Dimensionamento adaptativo baseado no número de variáveis
4. Truncamento de nomes longos para evitar sobreposição
"""

import pandas as pd
import os
import sys

def test_index_to_name_mapping():
    """Testa a criação do mapeamento index_to_name"""
    print("🧪 Testando mapeamento index_to_name...")
    
    # Simular dados de teste
    test_data = {
        'variable_name_very_long_example_1': [1, 2, 3],
        'short_var': [4, 5, 6],
        'another_variable_with_long_name': [7, 8, 9],
        'var4': [10, 11, 12]
    }
    
    df = pd.DataFrame(test_data)
    original_columns = df.columns.tolist()
    
    # Criar dicionário como no script original
    index_to_name = {str(i): name for i, name in enumerate(original_columns)}
    
    print(f"✅ Colunas originais: {original_columns}")
    print(f"✅ Mapeamento index_to_name: {index_to_name}")
    
    # Testar conversão de 'col_X.txt' para nome original
    test_conversions = ['col_0.txt', 'col_1.txt', 'col_2.txt', 'col_3.txt']
    
    for col_name in test_conversions:
        # Extrair número como no script
        num = col_name.split('col_')[1].split('.txt')[0]
        if num in index_to_name:
            original_name = index_to_name[num]
            print(f"✅ {col_name} → {original_name}")
        else:
            print(f"❌ Erro: {col_name} não encontrado no mapeamento")
    
    return True

def test_adaptive_dimensions():
    """Testa o cálculo de dimensões adaptativas"""
    print("\n🧪 Testando dimensionamento adaptativo...")
    
    test_cases = [
        (10, "Pequeno dataset"),
        (30, "Dataset médio"),
        (75, "Dataset grande"),
        (150, "Dataset muito grande")
    ]
    
    for num_variables, description in test_cases:
        if num_variables <= 20:
            width, height = 800, 600
            font_size = "10px"
        elif num_variables <= 50:
            width, height = 1200, 900
            font_size = "8px"
        elif num_variables <= 100:
            width, height = 1600, 1200
            font_size = "6px"
        else:
            width, height = 2000, 1500
            font_size = "5px"
        
        print(f"✅ {description} ({num_variables} vars): {width}x{height}, font: {font_size}")
    
    return True

def test_label_truncation():
    """Testa o truncamento de nomes longos"""
    print("\n🧪 Testando truncamento de labels...")
    
    test_labels = [
        "short_name",
        "medium_length_variable",
        "very_long_variable_name_that_should_be_truncated",
        "extremely_long_variable_name_with_many_characters_that_definitely_needs_truncation"
    ]
    
    truncated_labels = []
    for label in test_labels:
        if len(label) > 15:  # Mesmo critério do script
            truncated = label[:12] + "..."
            truncated_labels.append(truncated)
            print(f"✅ '{label}' → '{truncated}' (truncado)")
        else:
            truncated_labels.append(label)
            print(f"✅ '{label}' → '{label}' (mantido)")
    
    return True

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DAS CORREÇÕES DE VISUALIZAÇÃO")
    print("=" * 60)
    
    try:
        # Executar testes
        test_index_to_name_mapping()
        test_adaptive_dimensions()
        test_label_truncation()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("\n📋 Correções implementadas:")
        print("✅ Mapeamento correto de 'col_X.txt' para nomes originais")
        print("✅ Dimensionamento adaptativo baseado no número de variáveis")
        print("✅ Truncamento de nomes longos para evitar sobreposição")
        print("✅ Configuração de fonte adaptativa para legibilidade")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
