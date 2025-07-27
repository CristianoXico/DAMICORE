#!/usr/bin/env python3
"""
Script de teste para validar a correção da coleta de arquivos newick
"""

import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'scripts'))

def test_newick_collection():
    """Testa a lógica de coleta de arquivos newick corrigida"""
    
    # Simular dados de uma fatia processada
    slice_file = "/media/cristiano-xico/sandbox/DAMICORE_RESULTS/aggrada-inct-fome-2025-06-20-city-yearly_sliced_results/slices/slice_0000.csv"
    
    # Aplicar a lógica corrigida
    slice_name = os.path.splitext(os.path.basename(slice_file))[0]  # slice_0000
    expected_results_dir = os.path.join(os.path.dirname(slice_file), slice_name, "damicore_results")
    
    print(f"🔍 Testando lógica de coleta de arquivos newick")
    print(f"📁 Arquivo de fatia: {slice_file}")
    print(f"📂 Nome da fatia: {slice_name}")
    print(f"📍 Diretório esperado: {expected_results_dir}")
    
    # Verificar se o diretório existe
    if os.path.exists(expected_results_dir):
        print(f"✅ Diretório encontrado: {expected_results_dir}")
        
        # Listar arquivos newick
        newick_files = []
        for file in os.listdir(expected_results_dir):
            if file.endswith('.newick'):
                newick_path = os.path.join(expected_results_dir, file)
                newick_files.append(newick_path)
        
        print(f"🌳 Arquivos newick encontrados: {len(newick_files)}")
        for i, nf in enumerate(newick_files[:5]):  # Mostrar apenas os primeiros 5
            print(f"  {i+1}. {os.path.basename(nf)}")
        
        if len(newick_files) > 5:
            print(f"  ... e mais {len(newick_files) - 5} arquivos")
            
        return len(newick_files) > 0
    else:
        print(f"❌ Diretório não encontrado: {expected_results_dir}")
        return False

def test_existing_structure():
    """Testa a estrutura de diretórios existente"""
    
    base_dir = "/media/cristiano-xico/sandbox/DAMICORE_RESULTS/aggrada-inct-fome-2025-06-20-city-yearly_sliced_results"
    
    print(f"\n🔍 Analisando estrutura existente")
    print(f"📂 Diretório base: {base_dir}")
    
    if os.path.exists(base_dir):
        print("✅ Diretório base existe")
        
        # Listar conteúdo
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                print(f"📁 {item}/")
                
                # Se for o diretório slices, explorar mais
                if item == "slices":
                    slices_dir = item_path
                    for slice_item in os.listdir(slices_dir):
                        slice_path = os.path.join(slices_dir, slice_item)
                        if os.path.isdir(slice_path):
                            print(f"  📁 {slice_item}/")
                            
                            # Verificar se tem damicore_results
                            damicore_results = os.path.join(slice_path, "damicore_results")
                            if os.path.exists(damicore_results):
                                newick_count = len([f for f in os.listdir(damicore_results) if f.endswith('.newick')])
                                print(f"    📁 damicore_results/ ({newick_count} arquivos .newick)")
            else:
                print(f"📄 {item}")
    else:
        print("❌ Diretório base não existe")

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TESTE DE COLETA DE ARQUIVOS NEWICK")
    print("=" * 80)
    
    # Testar estrutura existente
    test_existing_structure()
    
    print("\n" + "=" * 80)
    
    # Testar lógica corrigida
    success = test_newick_collection()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 TESTE PASSOU: Lógica de coleta corrigida funciona!")
    else:
        print("❌ TESTE FALHOU: Problema na lógica de coleta")
    print("=" * 80)
