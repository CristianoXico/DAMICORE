#!/usr/bin/env python3
"""
Script de teste para verificar a compilação dos arquivos newick.
Testa se os arquivos newick estão sendo encontrados e compilados corretamente.
"""

import os
import sys
import json
import glob
from pathlib import Path

def test_newick_compilation():
    """
    Testa a compilação dos arquivos newick de um processamento existente.
    """
    print("🔍 TESTE DE COMPILAÇÃO DOS ARQUIVOS NEWICK")
    print("="*60)
    
    # Diretório de teste (ajustar conforme necessário)
    test_dirs = [
        "/media/cristiano-xico/sandbox/DAMICORE_RESULTS/aggrada-inct-fome-2025-06-20-city-yearly_sliced_results",
        "/home/cristianosantos/aggrada-inct-fome-2025-06-20-city-yearly_sliced_results"
    ]
    
    output_dir = None
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            output_dir = test_dir
            break
    
    if not output_dir:
        print("❌ Nenhum diretório de teste encontrado!")
        return False
    
    print(f"📁 Diretório de teste: {output_dir}")
    
    # 1. Verificar checkpoint
    checkpoint_file = os.path.join(output_dir, "slicer_progress.json")
    if not os.path.exists(checkpoint_file):
        print("❌ Arquivo de checkpoint não encontrado!")
        return False
    
    print(f"✅ Checkpoint encontrado: {checkpoint_file}")
    
    # 2. Carregar checkpoint
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar checkpoint: {e}")
        return False
    
    # 3. Analisar estrutura do checkpoint
    slice_results = checkpoint_data.get("slice_results", {})
    print(f"📊 Fatias no checkpoint: {len(slice_results)}")
    
    total_newick_files = 0
    found_newick_files = 0
    missing_newick_files = []
    
    # 4. Verificar cada fatia
    for slice_idx_str, slice_data in slice_results.items():
        slice_idx = int(slice_idx_str)
        
        # Verificar se slice_data é um dicionário
        if isinstance(slice_data, dict):
            newick_files = slice_data.get("newick_files", [])
        else:
            print(f"⚠️  Estrutura inesperada para fatia {slice_idx}: {type(slice_data)}")
            continue
        
        print(f"📁 Fatia {slice_idx + 1}: {len(newick_files)} arquivos newick listados")
        total_newick_files += len(newick_files)
        
        # Verificar se os arquivos existem
        for newick_file in newick_files:
            if os.path.exists(newick_file):
                found_newick_files += 1
            else:
                missing_newick_files.append(newick_file)
                if len(missing_newick_files) <= 5:  # Mostrar apenas os primeiros 5
                    print(f"  ❌ Arquivo não encontrado: {newick_file}")
    
    # 5. Resumo
    print(f"\n📊 RESUMO:")
    print(f"🌳 Total de arquivos newick listados: {total_newick_files}")
    print(f"✅ Arquivos encontrados: {found_newick_files}")
    print(f"❌ Arquivos não encontrados: {len(missing_newick_files)}")
    
    if missing_newick_files:
        print(f"⚠️  {len(missing_newick_files)} arquivos estão listados no checkpoint mas não existem no disco")
    
    # 6. Buscar arquivos newick reais no diretório
    print(f"\n🔍 BUSCA REAL DE ARQUIVOS NEWICK:")
    newick_pattern = os.path.join(output_dir, "**", "*.newick")
    real_newick_files = glob.glob(newick_pattern, recursive=True)
    print(f"🌳 Arquivos .newick encontrados no disco: {len(real_newick_files)}")
    
    if real_newick_files:
        print("📁 Exemplos de arquivos encontrados:")
        for i, newick_file in enumerate(real_newick_files[:5]):
            rel_path = os.path.relpath(newick_file, output_dir)
            print(f"  ✅ {rel_path}")
        if len(real_newick_files) > 5:
            print(f"  ... e mais {len(real_newick_files) - 5} arquivos")
    
    # 7. Testar compilação simulada
    print(f"\n🧪 TESTE DE COMPILAÇÃO SIMULADA:")
    compiled_dir = os.path.join(output_dir, "compiled_results_test")
    os.makedirs(compiled_dir, exist_ok=True)
    
    compiled_count = 0
    for newick_file in real_newick_files:
        if os.path.exists(newick_file):
            # Extrair informação da fatia do caminho
            path_parts = newick_file.split(os.sep)
            slice_info = "unknown"
            for part in path_parts:
                if part.startswith("slice_"):
                    slice_info = part
                    break
            
            # Criar nome único
            original_name = os.path.basename(newick_file)
            compiled_name = f"{slice_info}_{original_name}"
            compiled_path = os.path.join(compiled_dir, compiled_name)
            
            try:
                import shutil
                shutil.copy2(newick_file, compiled_path)
                compiled_count += 1
            except Exception as e:
                print(f"❌ Erro ao copiar {newick_file}: {e}")
    
    print(f"✅ Arquivos compilados com sucesso: {compiled_count}")
    print(f"📁 Diretório de teste: {compiled_dir}")
    
    # 8. Verificar se a compilação funcionou
    compiled_files = glob.glob(os.path.join(compiled_dir, "*.newick"))
    print(f"🌳 Arquivos na pasta compilada: {len(compiled_files)}")
    
    if compiled_files:
        print("✅ COMPILAÇÃO FUNCIONANDO CORRETAMENTE!")
        return True
    else:
        print("❌ COMPILAÇÃO FALHOU!")
        return False

if __name__ == "__main__":
    success = test_newick_compilation()
    sys.exit(0 if success else 1)
