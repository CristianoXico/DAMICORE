#!/usr/bin/env python3
"""
Script abrangente para regenerar TODAS as visualizações de TODOS os slices
Processa tanto slices no diretório raiz quanto no subdiretório slices/
"""

import os
import sys
from pathlib import Path
from visualization_fixer import DAMICOREVisualizationFixer

def find_all_slice_directories(base_path):
    """Encontra todos os diretórios de slices com arquivos newick"""
    slice_dirs = []
    base = Path(base_path)
    
    # Procura em todos os subdiretórios
    for root, dirs, files in os.walk(base):
        root_path = Path(root)
        
        # Verifica se é um diretório de slice com damicore_results
        if (root_path.name.startswith('slice_') and 
            not root_path.name.endswith('_results')):
            
            damicore_results = root_path / 'damicore_results'
            if damicore_results.exists():
                # Verifica se tem arquivos newick
                newick_files = list(damicore_results.glob('*.newick'))
                if newick_files:
                    slice_dirs.append(root_path)
    
    return sorted(slice_dirs)

def main():
    """Regenera visualizações para TODOS os slices encontrados"""
    print("=" * 80)
    print("🔄 REGENERAÇÃO ABRANGENTE DE TODAS AS VISUALIZAÇÕES")
    print("=" * 80)
    print("🎯 Processando TODOS os slices com arquivos newick")
    print("=" * 80)
    
    # Diretório principal de resultados
    results_dir = "/media/cristiano-xico/sandbox/DAMICORE_RESULTS/aggrada-inct-fome-2025-06-20-city-yearly_sliced_results"
    
    if not os.path.exists(results_dir):
        print(f"❌ Diretório não encontrado: {results_dir}")
        return
    
    # Inicializa o fixer
    print("🔧 Inicializando DAMICORE Visualization Fixer...")
    fixer = DAMICOREVisualizationFixer(results_dir)
    
    # Detecta CSV original e cria mapeamento
    print("📊 Detectando CSV original e criando mapeamento de variáveis...")
    if not fixer.create_variable_mapping():
        print("❌ Falha ao criar mapeamento de variáveis")
        return
    
    print(f"✅ Mapeamento criado para {fixer.num_variables} variáveis")
    print(f"📋 Primeiras 5 variáveis: {list(fixer.index_to_name.values())[:5]}")
    
    # Encontra TODOS os slices com dados
    print("\n🔍 Procurando por todos os slices com arquivos newick...")
    all_slice_dirs = find_all_slice_directories(results_dir)
    
    if not all_slice_dirs:
        print("❌ Nenhum slice com arquivos newick encontrado")
        return
    
    print(f"📁 Encontrados {len(all_slice_dirs)} slices com dados:")
    for slice_dir in all_slice_dirs:
        relative_path = slice_dir.relative_to(Path(results_dir))
        newick_count = len(list((slice_dir / 'damicore_results').glob('*.newick')))
        print(f"   - {relative_path} ({newick_count} arquivos newick)")
    
    # Calcula dimensões adaptativas
    width, height = fixer.calculate_adaptive_dimensions()
    print(f"\n📐 Dimensões adaptativas: {width}x{height} para {fixer.num_variables} variáveis")
    
    # Processa cada slice
    print(f"\n🔄 Iniciando processamento de {len(all_slice_dirs)} slices...")
    print("-" * 80)
    
    success_count = 0
    failed_slices = []
    
    for i, slice_dir in enumerate(all_slice_dirs, 1):
        relative_path = slice_dir.relative_to(Path(results_dir))
        print(f"[{i:2d}/{len(all_slice_dirs)}] 🔄 Processando {relative_path}...", end=" ")
        
        try:
            if fixer.regenerate_visualizations_for_slice(slice_dir):
                print("✅")
                success_count += 1
            else:
                print("❌")
                failed_slices.append(str(relative_path))
        except Exception as e:
            print(f"💥 ERRO: {e}")
            failed_slices.append(str(relative_path))
    
    # Relatório final detalhado
    print("\n" + "=" * 80)
    print("📋 RELATÓRIO FINAL ABRANGENTE")
    print("=" * 80)
    print(f"📊 Total de slices encontrados: {len(all_slice_dirs)}")
    print(f"✅ Slices processados com sucesso: {success_count}")
    print(f"❌ Slices com falha: {len(failed_slices)}")
    print(f"📈 Taxa de sucesso: {(success_count/len(all_slice_dirs)*100):.1f}%")
    
    if failed_slices:
        print(f"\n❌ Slices que falharam:")
        for failed in failed_slices:
            print(f"   - {failed}")
    
    print(f"\n🎨 Visualizações regeneradas para {success_count} slices:")
    print("   ✅ Nomes de variáveis originais aplicados")
    print("   ✅ Dimensões adaptativas: {width}x{height}")
    print("   ✅ Arquivos *_corrected.pdf/png gerados")
    print("   ✅ Conteúdo newick com nomes corrigidos")
    
    # Gera relatório final
    fixer._generate_correction_report(success_count, len(all_slice_dirs))
    
    if success_count > 0:
        print(f"\n🎉 Regeneração abrangente concluída!")
        print(f"📁 Verifique os arquivos *_corrected.* nos diretórios dos slices")
        print(f"📋 Relatório detalhado salvo em visualization_correction_report.json")
    else:
        print(f"\n❌ Nenhuma visualização foi regenerada")

if __name__ == "__main__":
    main()
