#!/usr/bin/env python3
"""
Quick diagnostic script to identify why newick files aren't being generated.
Run this on the server to quickly diagnose the issue.
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

def quick_debug():
    print("🔍 DIAGNÓSTICO RÁPIDO - FALHA NA GERAÇÃO DE NEWICK")
    print("=" * 60)
    
    # 1. Verificar se o DAMICORE existe e é executável
    print("1️⃣ Verificando DAMICORE:")
    damicore_paths = [
        "/home/cristianosantos/DAMICORE/src/damicore.py",
        "/home/cristianosantos/DAMICORE/damicore_py3/damicore.py",
        "./src/damicore.py",
        "./damicore_py3/damicore.py"
    ]
    
    damicore_found = None
    for path in damicore_paths:
        if os.path.exists(path):
            damicore_found = path
            print(f"   ✅ DAMICORE encontrado: {path}")
            break
    
    if not damicore_found:
        print("   ❌ DAMICORE não encontrado!")
        print("   🔍 Procurando recursivamente...")
        result = subprocess.run(["find", "/home/cristianosantos", "-name", "damicore.py", "-type", "f"], 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"   📁 Encontrados: {result.stdout.strip()}")
        else:
            print("   ❌ Nenhum damicore.py encontrado no sistema!")
    
    # 2. Verificar diretórios de fatias
    print("\n2️⃣ Verificando diretórios de fatias:")
    slice_patterns = [
        "/home/cristianosantos/aggrada-inct-fome-2025-06-20-state-yearly_sliced_results/slices/slice_*",
        "/home/cristianosantos/*sliced_results/slices/slice_*",
        "./slices/slice_*"
    ]
    
    slice_dirs = []
    for pattern in slice_patterns:
        found = glob.glob(pattern)
        slice_dirs.extend(found)
    
    if slice_dirs:
        print(f"   ✅ {len(slice_dirs)} diretórios de fatias encontrados")
        sample_slice = slice_dirs[0]
        print(f"   📁 Exemplo: {sample_slice}")
        
        # Verificar conteúdo de uma fatia
        if os.path.isdir(sample_slice):
            files = os.listdir(sample_slice)
            print(f"   📄 Arquivos na fatia: {len(files)}")
            
            # Procurar arquivos newick
            newick_files = [f for f in files if f.endswith('.newick')]
            print(f"   🌳 Arquivos .newick: {len(newick_files)}")
            
            # Procurar diretórios de amostra
            sample_dirs = [f for f in files if os.path.isdir(os.path.join(sample_slice, f)) and f.startswith('resample_')]
            print(f"   📂 Diretórios de amostra: {len(sample_dirs)}")
            
            if sample_dirs:
                sample_dir = os.path.join(sample_slice, sample_dirs[0])
                sample_files = os.listdir(sample_dir)
                txt_files = [f for f in sample_files if f.endswith('.txt')]
                tree_files = [f for f in sample_files if 'tree' in f.lower()]
                print(f"   📄 Arquivos .txt na amostra: {len(txt_files)}")
                print(f"   🌳 Arquivos de árvore na amostra: {len(tree_files)}")
                
                # Teste rápido do DAMICORE
                if damicore_found and txt_files:
                    print(f"\n3️⃣ Teste rápido do DAMICORE:")
                    print(f"   🧪 Testando em: {sample_dir}")
                    try:
                        # Executar DAMICORE na amostra
                        result = subprocess.run([
                            "python3", damicore_found, sample_dir
                        ], capture_output=True, text=True, timeout=30, cwd=sample_dir)
                        
                        print(f"   📤 Código de saída: {result.returncode}")
                        if result.returncode != 0:
                            print(f"   ❌ ERRO no DAMICORE:")
                            print(f"      STDERR: {result.stderr[:300]}...")
                        else:
                            print(f"   ✅ DAMICORE executou sem erro")
                            
                        # Verificar se arquivos foram gerados
                        after_files = os.listdir(sample_dir)
                        new_tree_files = [f for f in after_files if 'tree' in f.lower() and f not in sample_files]
                        print(f"   🌳 Novos arquivos de árvore: {len(new_tree_files)}")
                        
                    except subprocess.TimeoutExpired:
                        print("   ⏰ Timeout na execução (>30s)")
                    except Exception as e:
                        print(f"   ❌ Erro na execução: {e}")
    else:
        print("   ❌ Nenhum diretório de fatias encontrado!")
    
    # 4. Verificar permissões
    print(f"\n4️⃣ Verificando permissões:")
    if slice_dirs:
        sample_slice = slice_dirs[0]
        try:
            # Testar escrita
            test_file = os.path.join(sample_slice, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("   ✅ Permissões de escrita OK")
        except Exception as e:
            print(f"   ❌ Problema de permissões: {e}")
    
    # 5. Verificar espaço em disco
    print(f"\n5️⃣ Verificando espaço em disco:")
    try:
        result = subprocess.run(["df", "-h", "/home/cristianosantos"], capture_output=True, text=True)
        print(f"   💾 Espaço em disco:")
        print(f"      {result.stdout}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar espaço: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 PRÓXIMOS PASSOS RECOMENDADOS:")
    
    if not damicore_found:
        print("   1. Localizar e corrigir caminho do DAMICORE")
    
    if not slice_dirs:
        print("   2. Verificar localização dos diretórios de fatias")
    else:
        print("   3. Executar diagnóstico completo em uma fatia específica")
        print(f"      python3 debug_slice_processing.py {slice_dirs[0]}/slice_0000.csv")
    
    print("   4. Verificar logs detalhados do DAMICORE_Filograma_script.py")
    print("   5. Testar execução manual do DAMICORE em uma amostra")
    
    print("=" * 60)

if __name__ == "__main__":
    quick_debug()
