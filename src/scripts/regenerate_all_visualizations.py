#!/usr/bin/env python3
"""
Script para regenerar TODAS as visualizações dos slices já executados
Aplica nomes de variáveis originais e dimensões adaptativas automaticamente
"""

import os
import sys
from pathlib import Path
from visualization_fixer import DAMICOREVisualizationFixer

def main():
    """Regenera visualizações para todos os slices executados"""
    print("=" * 80)
    print("🔄 REGENERAÇÃO AUTOMÁTICA DE TODAS AS VISUALIZAÇÕES")
    print("=" * 80)
    print("🎯 Aplicando nomes originais e dimensões adaptativas")
    print("=" * 80)
    
    # Diretório de resultados principal
    results_base = "/media/cristiano-xico/sandbox/DAMICORE_RESULTS"
    
    # Encontra todos os diretórios de resultados
    results_dirs = []
    for item in Path(results_base).iterdir():
        if item.is_dir() and "sliced_results" in item.name:
            results_dirs.append(item)
    
    if not results_dirs:
        print("❌ Nenhum diretório de resultados encontrado")
        return
    
    print(f"📊 Encontrados {len(results_dirs)} diretórios de resultados:")
    for results_dir in results_dirs:
        print(f"   - {results_dir.name}")
    
    # Processa cada diretório de resultados
    total_processed = 0
    total_slices = 0
    
    for results_dir in results_dirs:
        print(f"\n🔄 Processando: {results_dir.name}")
        print("-" * 60)
        
        # Inicializa o fixer para este diretório
        fixer = DAMICOREVisualizationFixer(str(results_dir))
        
        # Detecta CSV original e cria mapeamento
        if not fixer.create_variable_mapping():
            print(f"❌ Falha ao criar mapeamento para {results_dir.name}")
            continue
        
        # Encontra todos os slices com dados
        slice_dirs = []
        for item in results_dir.iterdir():
            if (item.is_dir() and 
                item.name.startswith("slice_") and 
                not item.name.endswith("_results")):
                
                # Verifica se tem damicore_results
                damicore_results = item / "damicore_results"
                if damicore_results.exists():
                    slice_dirs.append(item)
        
        print(f"📁 Encontrados {len(slice_dirs)} slices com dados para processar")
        total_slices += len(slice_dirs)
        
        # Processa cada slice
        success_count = 0
        for slice_dir in sorted(slice_dirs):
            print(f"   🔄 Processando {slice_dir.name}...", end=" ")
            
            if fixer.regenerate_visualizations_for_slice(slice_dir):
                print("✅")
                success_count += 1
            else:
                print("❌")
        
        print(f"✅ {results_dir.name}: {success_count}/{len(slice_dirs)} slices processados")
        total_processed += success_count
        
        # Gera relatório para este diretório
        fixer._generate_correction_report(success_count, len(slice_dirs))
    
    # Relatório final
    print("\n" + "=" * 80)
    print("📋 RELATÓRIO FINAL DA REGENERAÇÃO")
    print("=" * 80)
    print(f"📊 Total de slices processados: {total_processed}/{total_slices}")
    print(f"📈 Taxa de sucesso: {(total_processed/total_slices*100):.1f}%" if total_slices > 0 else "N/A")
    print("\n🎨 Visualizações regeneradas:")
    print("   ✅ Nomes de variáveis originais aplicados")
    print("   ✅ Dimensões adaptativas calculadas")
    print("   ✅ Arquivos *_corrected.pdf/png gerados")
    print("   ✅ Relatórios de correção salvos")
    
    if total_processed > 0:
        print(f"\n🎉 Regeneração concluída com sucesso!")
        print(f"📁 Verifique os arquivos *_corrected.* nos diretórios dos slices")
    else:
        print(f"\n❌ Nenhuma visualização foi regenerada")
        print(f"💡 Verifique se os slices têm arquivos newick válidos")

if __name__ == "__main__":
    main()
