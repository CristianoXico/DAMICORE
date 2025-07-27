#!/usr/bin/env python3
"""
Teste da implementação memory-efficient para visualização unificada.
"""

import os
import sys

def test_memory_efficient_functions():
    """
    Testa as funções memory-efficient implementadas.
    """
    print("🧪 TESTANDO IMPLEMENTAÇÃO MEMORY-EFFICIENT")
    print("="*50)
    
    # Importar as funções do script principal
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    
    try:
        from DAMICORE_File_Slicer_Processor import (
            calculate_memory_safe_sample_size,
            select_representative_sample
        )
        
        # Teste 1: Cálculo de amostra segura
        print("\n📊 Teste 1: Cálculo de amostra segura")
        test_cases = [100, 500, 1000, 2000]
        for total_files in test_cases:
            safe_size = calculate_memory_safe_sample_size(total_files)
            print(f"   Total: {total_files} → Amostra: {safe_size}")
        
        # Teste 2: Seleção de amostra representativa
        print("\n🎯 Teste 2: Seleção de amostra representativa")
        test_files = [f"file_{i:04d}.newick" for i in range(100)]
        sample = select_representative_sample(test_files, 20)
        print(f"   Arquivos originais: {len(test_files)}")
        print(f"   Amostra selecionada: {len(sample)}")
        print(f"   Primeiros 5: {sample[:5]}")
        
        print("\n✅ Todos os testes passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return False

if __name__ == "__main__":
    success = test_memory_efficient_functions()
    sys.exit(0 if success else 1)
