#!/usr/bin/env python3
"""
Script de diagnóstico para investigar o problema da compilação dos arquivos newick.
"""

import os
import json
import sys
import shutil
from pathlib import Path

def debug_compilation_issue():
    """Diagnostica o problema da compilação dos arquivos newick."""
    
    print("🔍 DIAGNÓSTICO DO PROBLEMA DE COMPILAÇÃO")
    print("=" * 60)
    
    # Diretório de teste
    base_dir = "/media/cristiano-xico/sandbox/DAMICORE_RESULTS/aggrada-inct-fome-2025-06-20-city-yearly_sliced_results"
    
    if not os.path.exists(base_dir):
        print(f"❌ Diretório base não encontrado: {base_dir}")
        return
    
    print(f"📁 Diretório base: {base_dir}")
    
    # 1. Verificar checkpoint
    checkpoint_file = os.path.join(base_dir, "slicer_progress.json")
    if not os.path.exists(checkpoint_file):
        print(f"❌ Checkpoint não encontrado: {checkpoint_file}")
        return
    
    print(f"✅ Checkpoint encontrado: {checkpoint_file}")
    
    with open(checkpoint_file, 'r') as f:
        checkpoint_data = json.load(f)
    
    slice_results = checkpoint_data.get("slice_results", {})
    print(f"📊 Fatias no checkpoint: {len(slice_results)}")
    
    # 2. Verificar arquivos newick listados no checkpoint
    all_newick_from_checkpoint = []
    missing_files = []
    existing_files = []
    
    for slice_idx_str, slice_data in slice_results.items():
        slice_idx = int(slice_idx_str)
        newick_files = slice_data.get("newick_files", [])
        
        print(f"📁 Fatia {slice_idx + 1}: {len(newick_files)} arquivos listados")
        
        for newick_file in newick_files:
            all_newick_from_checkpoint.append(newick_file)
            if os.path.exists(newick_file):
                existing_files.append(newick_file)
            else:
                missing_files.append(newick_file)
    
    print(f"\n📊 ANÁLISE DOS ARQUIVOS LISTADOS NO CHECKPOINT:")
    print(f"🌳 Total listados: {len(all_newick_from_checkpoint)}")
    print(f"✅ Existem no disco: {len(existing_files)}")
    print(f"❌ Não existem: {len(missing_files)}")
    
    if missing_files:
        print(f"\n❌ ARQUIVOS FALTANTES (primeiros 10):")
        for i, missing_file in enumerate(missing_files[:10]):
            print(f"   {i+1}. {missing_file}")
        if len(missing_files) > 10:
            print(f"   ... e mais {len(missing_files) - 10} arquivos")
    
    # 3. Buscar arquivos newick reais no disco
    print(f"\n🔍 BUSCA REAL DE ARQUIVOS NEWICK NO DISCO:")
    real_newick_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.newick'):
                full_path = os.path.join(root, file)
                real_newick_files.append(full_path)
    
    print(f"🌳 Arquivos .newick encontrados no disco: {len(real_newick_files)}")
    
    # 4. Comparar checkpoint vs realidade
    checkpoint_set = set(all_newick_from_checkpoint)
    real_set = set(real_newick_files)
    
    only_in_checkpoint = checkpoint_set - real_set
    only_in_disk = real_set - checkpoint_set
    in_both = checkpoint_set & real_set
    
    print(f"\n📊 COMPARAÇÃO CHECKPOINT vs DISCO:")
    print(f"🔄 Em ambos: {len(in_both)}")
    print(f"📋 Só no checkpoint: {len(only_in_checkpoint)}")
    print(f"💾 Só no disco: {len(only_in_disk)}")
    
    if only_in_disk:
        print(f"\n💾 ARQUIVOS NO DISCO MAS NÃO NO CHECKPOINT (primeiros 10):")
        for i, extra_file in enumerate(list(only_in_disk)[:10]):
            print(f"   {i+1}. {extra_file}")
        if len(only_in_disk) > 10:
            print(f"   ... e mais {len(only_in_disk) - 10} arquivos")
    
    # 5. Testar compilação manual
    print(f"\n🧪 TESTE DE COMPILAÇÃO MANUAL:")
    compiled_dir = os.path.join(base_dir, "compiled_results_debug")
    os.makedirs(compiled_dir, exist_ok=True)
    
    # Usar arquivos que existem no disco
    files_to_compile = existing_files if existing_files else real_newick_files
    
    print(f"📋 Compilando {len(files_to_compile)} arquivos...")
    compiled_count = 0
    
    for i, newick_file in enumerate(files_to_compile):
        if not os.path.exists(newick_file):
            continue
            
        # Criar nome único
        original_name = os.path.basename(newick_file)
        path_parts = newick_file.split(os.sep)
        slice_info = "unknown"
        for part in path_parts:
            if part.startswith("slice_"):
                slice_info = part
                break
        
        compiled_name = f"{slice_info}_{original_name}"
        compiled_path = os.path.join(compiled_dir, compiled_name)
        
        try:
            shutil.copy2(newick_file, compiled_path)
            compiled_count += 1
            
            if i < 5:
                print(f"  ✅ {compiled_name}")
            elif i == 5:
                print(f"  ... compilando mais arquivos...")
                
        except Exception as e:
            print(f"  ❌ Erro ao copiar {newick_file}: {e}")
    
    print(f"\n✅ COMPILAÇÃO MANUAL CONCLUÍDA!")
    print(f"📁 Arquivos compilados: {compiled_count}")
    print(f"📁 Diretório: {compiled_dir}")
    
    # 6. Verificar pasta compiled_results original
    original_compiled_dir = os.path.join(base_dir, "compiled_results")
    if os.path.exists(original_compiled_dir):
        files_in_original = os.listdir(original_compiled_dir)
        print(f"\n📁 PASTA compiled_results ORIGINAL:")
        print(f"🌳 Arquivos: {len(files_in_original)}")
        if files_in_original:
            print(f"📋 Primeiros arquivos:")
            for file in files_in_original[:5]:
                print(f"   ✅ {file}")
        else:
            print("❌ Pasta vazia!")
    else:
        print(f"\n❌ Pasta compiled_results não existe!")
    
    # 7. Diagnóstico final
    print(f"\n🎯 DIAGNÓSTICO FINAL:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if len(only_in_disk) > len(in_both):
        print(f"🚨 PROBLEMA IDENTIFICADO: Checkpoint desatualizado!")
        print(f"   • Há {len(only_in_disk)} arquivos no disco não listados no checkpoint")
        print(f"   • Isso explica por que a compilação falha")
        print(f"   • Solução: Atualizar checkpoint ou usar busca direta no disco")
    
    if len(only_in_checkpoint) > 0:
        print(f"⚠️  ARQUIVOS FALTANTES: {len(only_in_checkpoint)} arquivos listados no checkpoint não existem")
        print(f"   • Isso pode indicar arquivos movidos ou deletados")
    
    if compiled_count > 0:
        print(f"✅ COMPILAÇÃO MANUAL FUNCIONOU: {compiled_count} arquivos compilados com sucesso")
        print(f"   • O problema está na lógica do pipeline principal")
    
    return {
        'checkpoint_files': len(all_newick_from_checkpoint),
        'existing_files': len(existing_files),
        'missing_files': len(missing_files),
        'real_files': len(real_newick_files),
        'compiled_manual': compiled_count,
        'only_in_disk': len(only_in_disk),
        'only_in_checkpoint': len(only_in_checkpoint)
    }

if __name__ == "__main__":
    results = debug_compilation_issue()
    print(f"\n🏁 Diagnóstico concluído!")
