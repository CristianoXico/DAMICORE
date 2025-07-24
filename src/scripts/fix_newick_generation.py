#!/usr/bin/env python3
"""
Script to fix the newick generation issue in DAMICORE slice processing.
This script addresses the most common causes of newick file generation failure.
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def fix_newick_generation(slice_results_dir):
    """
    Fix newick generation issues in slice processing.
    """
    print("🔧 CORRIGINDO GERAÇÃO DE ARQUIVOS NEWICK")
    print("=" * 60)
    
    results_path = Path(slice_results_dir)
    if not results_path.exists():
        print(f"❌ Diretório não encontrado: {slice_results_dir}")
        return False
    
    slices_dir = results_path / "slices"
    if not slices_dir.exists():
        print(f"❌ Diretório de fatias não encontrado: {slices_dir}")
        return False
    
    # Encontrar todas as fatias
    slice_dirs = [d for d in slices_dir.iterdir() if d.is_dir() and d.name.startswith('slice_')]
    print(f"📁 Fatias encontradas: {len(slice_dirs)}")
    
    if not slice_dirs:
        print("❌ Nenhuma fatia encontrada!")
        return False
    
    # Localizar DAMICORE
    damicore_paths = [
        "/home/cristianosantos/DAMICORE/src/damicore.py",
        "/home/cristianosantos/DAMICORE/damicore_py3/damicore.py"
    ]
    
    damicore_path = None
    for path in damicore_paths:
        if os.path.exists(path):
            damicore_path = path
            break
    
    if not damicore_path:
        print("❌ DAMICORE não encontrado nos caminhos padrão!")
        return False
    
    print(f"✅ DAMICORE encontrado: {damicore_path}")
    
    # Processar primeira fatia como teste
    slice_dir = sorted(slice_dirs)[0]
    print(f"\n🔄 Testando fatia: {slice_dir.name}")
    
    # Procurar diretórios de amostra
    sample_dirs = [d for d in slice_dir.iterdir() if d.is_dir() and d.name.startswith('resample_')]
    print(f"   📂 Amostras encontradas: {len(sample_dirs)}")
    
    if not sample_dirs:
        print("   ❌ Nenhuma amostra encontrada!")
        return False
    
    # Testar primeira amostra
    sample_dir = sample_dirs[0]
    print(f"   🧪 Testando amostra: {sample_dir.name}")
    
    # Verificar arquivos .txt
    txt_files = list(sample_dir.glob("*.txt"))
    print(f"      📄 Arquivos .txt: {len(txt_files)}")
    
    if not txt_files:
        print("      ❌ Nenhum arquivo .txt encontrado!")
        return False
    
    # Executar DAMICORE na amostra
    print(f"      🔧 Executando DAMICORE...")
    try:
        original_cwd = os.getcwd()
        os.chdir(sample_dir)
        
        result = subprocess.run([
            "python3", damicore_path, "."
        ], capture_output=True, text=True, timeout=60)
        
        os.chdir(original_cwd)
        
        print(f"      📤 Código de saída: {result.returncode}")
        
        if result.returncode != 0:
            print(f"      ❌ DAMICORE falhou:")
            if result.stderr:
                print(f"         STDERR: {result.stderr}")
            if result.stdout:
                print(f"         STDOUT: {result.stdout}")
            return False
        
        # Verificar arquivos gerados
        new_files = list(sample_dir.iterdir())
        tree_files = [f for f in new_files if 'tree' in f.name.lower()]
        newick_files = [f for f in new_files if f.name.endswith('.newick')]
        
        print(f"      🌳 Arquivos de árvore: {len(tree_files)}")
        print(f"      🌳 Arquivos .newick: {len(newick_files)}")
        
        if tree_files or newick_files:
            print("      ✅ DAMICORE gerou arquivos com sucesso!")
            return True
        else:
            print("      ❌ DAMICORE não gerou arquivos de árvore!")
            return False
            
    except Exception as e:
        print(f"      ❌ Erro na execução: {e}")
        os.chdir(original_cwd)
        return False

def main():
    if len(sys.argv) != 2:
        print("Uso: python fix_newick_generation.py <diretorio_resultados>")
        print("Exemplo: python fix_newick_generation.py /home/cristianosantos/aggrada-inct-fome-2025-06-20-state-yearly_sliced_results")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    success = fix_newick_generation(results_dir)
    
    if success:
        print("\n✅ Teste bem-sucedido! O problema foi identificado e pode ser corrigido.")
    else:
        print("\n❌ Problema persistente. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
