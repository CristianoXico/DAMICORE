#!/usr/bin/env python3
"""
Análise Rápida de Arquivos Newick
=================================

Script para verificação rápida do status de geração de arquivos .newick
nas fatias processadas pelo DAMICORE_File_Slicer_Processor.py
"""

import os
import sys
import glob
import json
from pathlib import Path

def quick_analysis(base_dir):
    """Análise rápida do diretório de resultados"""
    
    print(f"🔍 Analisando: {base_dir}")
    print("="*50)
    
    if not os.path.exists(base_dir):
        print(f"❌ Diretório não existe: {base_dir}")
        return
    
    # Verifica checkpoint
    checkpoint_file = os.path.join(base_dir, "pipeline_progress.json")
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            slices_status = checkpoint.get('slices_status', {})
            total = len(slices_status)
            completed = sum(1 for s in slices_status.values() if s == 'completed')
            failed = sum(1 for s in slices_status.values() if s == 'failed')
            pending = sum(1 for s in slices_status.values() if s == 'pending')
            
            print(f"📊 Checkpoint Status:")
            print(f"   Total fatias: {total}")
            print(f"   ✅ Concluídas: {completed}")
            print(f"   ❌ Falhadas: {failed}")
            print(f"   ⏳ Pendentes: {pending}")
            
        except Exception as e:
            print(f"⚠️ Erro ao ler checkpoint: {e}")
    else:
        print(f"❌ Checkpoint não encontrado")
    
    # Conta fatias e arquivos newick
    slice_dirs = []
    total_newick = 0
    slices_with_newick = 0
    
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and item.startswith('slice_'):
            slice_dirs.append(item_path)
            
            # Conta arquivos newick nesta fatia
            newick_files = glob.glob(os.path.join(item_path, "**/*.newick"), recursive=True)
            slice_newick_count = len(newick_files)
            total_newick += slice_newick_count
            
            if slice_newick_count > 0:
                slices_with_newick += 1
    
    print(f"\n📁 Estrutura de Fatias:")
    print(f"   Total fatias encontradas: {len(slice_dirs)}")
    print(f"   Fatias com arquivos .newick: {slices_with_newick}")
    print(f"   Total arquivos .newick: {total_newick}")
    
    # Status resumido
    print(f"\n🎯 Status Resumido:")
    if total_newick == 0:
        print(f"   ❌ CRÍTICO: Nenhum arquivo .newick gerado")
        print(f"   🔧 Todas as fatias falharam na geração de newick")
    elif slices_with_newick < len(slice_dirs):
        print(f"   ⚠️ PARCIAL: {slices_with_newick}/{len(slice_dirs)} fatias geraram newick")
        print(f"   🔧 Algumas fatias falharam na geração")
    else:
        print(f"   ✅ SUCESSO: Todas as fatias geraram arquivos newick")
    
    # Mostra detalhes das primeiras fatias
    print(f"\n📋 Detalhes das Primeiras Fatias:")
    for i, slice_dir in enumerate(sorted(slice_dirs)[:5]):
        slice_name = os.path.basename(slice_dir)
        newick_files = glob.glob(os.path.join(slice_dir, "**/*.newick"), recursive=True)
        csv_files = glob.glob(os.path.join(slice_dir, "*.csv"))
        
        print(f"   {slice_name}:")
        print(f"     CSV: {len(csv_files)} arquivo(s)")
        print(f"     Newick: {len(newick_files)} arquivo(s)")
        
        # Se tem CSV mas não tem newick, é uma falha
        if len(csv_files) > 0 and len(newick_files) == 0:
            print(f"     ❌ FALHA: CSV presente mas sem newick")
        elif len(newick_files) > 0:
            print(f"     ✅ OK: Newick gerado")
    
    if len(slice_dirs) > 5:
        print(f"   ... e mais {len(slice_dirs) - 5} fatias")

def main():
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        # Tenta detectar diretório automaticamente
        possible_dirs = [
            "/media/cristiano-xico/sandbox/DAMICORE_RESULTS",
            "/tmp/damicore_results",
            "./damicore_results"
        ]
        
        base_dir = None
        for possible_dir in possible_dirs:
            if os.path.exists(possible_dir):
                base_dir = possible_dir
                break
        
        if not base_dir:
            base_dir = input("📁 Digite o caminho do diretório de resultados: ").strip()
    
    if base_dir:
        quick_analysis(base_dir)
    else:
        print("❌ Diretório não especificado")

if __name__ == "__main__":
    main()
