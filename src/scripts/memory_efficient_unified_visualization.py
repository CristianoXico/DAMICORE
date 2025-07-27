#!/usr/bin/env python3
"""
Geração de Visualização Unificada com Eficiência de Memória

Este script implementa uma abordagem otimizada para gerar visualizações unificadas
sem causar OOM (Out of Memory), usando estratégias de:

1. 🔄 SAMPLING: Processa apenas uma amostra representativa dos arquivos newick
2. 🧹 CLEANUP: Limpeza agressiva de memória após cada etapa
3. 📊 STREAMING: Processamento incremental dos arquivos
4. 🎯 FALLBACK: Visualizações simplificadas quando necessário

Autor: Cristiano Xico
Data: 2025-07-27
"""

import os
import sys
import gc
import random
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

def calculate_memory_safe_sample_size(total_files, available_memory_gb=2):
    """
    Calcula um tamanho de amostra seguro baseado na memória disponível.
    
    Args:
        total_files (int): Número total de arquivos newick
        available_memory_gb (float): Memória disponível estimada em GB
    
    Returns:
        int: Número seguro de arquivos para processar
    """
    # Estimativa: cada árvore newick consome ~1-5MB na memória
    # Para ser conservador, assumimos 5MB por árvore
    max_files_per_gb = 200  # ~200 árvores por GB
    max_safe_files = int(available_memory_gb * max_files_per_gb)
    
    # Limites absolutos
    min_sample = 10   # Mínimo para ter representatividade
    max_sample = 50   # Máximo para evitar OOM mesmo em sistemas pequenos
    
    safe_sample = min(max_safe_files, total_files, max_sample)
    safe_sample = max(safe_sample, min_sample)
    
    print(f"📊 Amostra calculada: {safe_sample} de {total_files} arquivos ({safe_sample/total_files*100:.1f}%)")
    return safe_sample

def select_representative_sample(newick_files, sample_size):
    """
    Seleciona uma amostra representativa dos arquivos newick.
    
    Args:
        newick_files (list): Lista completa de arquivos newick
        sample_size (int): Tamanho da amostra desejada
    
    Returns:
        list: Amostra representativa dos arquivos
    """
    if len(newick_files) <= sample_size:
        return newick_files
    
    # Estratégia: pegar arquivos distribuídos uniformemente
    step = len(newick_files) // sample_size
    representative_sample = []
    
    for i in range(0, len(newick_files), step):
        if len(representative_sample) < sample_size:
            representative_sample.append(newick_files[i])
    
    # Se ainda não temos o suficiente, pegar aleatoriamente do resto
    remaining_needed = sample_size - len(representative_sample)
    if remaining_needed > 0:
        remaining_files = [f for f in newick_files if f not in representative_sample]
        if remaining_files:
            additional = random.sample(remaining_files, min(remaining_needed, len(remaining_files)))
            representative_sample.extend(additional)
    
    print(f"🎯 Amostra selecionada: {len(representative_sample)} arquivos")
    return representative_sample

def generate_memory_efficient_cloud_tree(newick_files, output_path, index_to_name, num_variables):
    """
    Gera cloud tree com uso eficiente de memória.
    """
    try:
        import toytree
        print("🌳 Gerando Cloud Tree (memory-efficient)...")
        
        # Processar em lotes pequenos para evitar OOM
        batch_size = 10
        all_trees = []
        
        for i in range(0, len(newick_files), batch_size):
            batch = newick_files[i:i+batch_size]
            batch_strings = []
            
            for newick_file in batch:
                try:
                    with open(newick_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            batch_strings.append(content)
                except Exception as e:
                    print(f"⚠️  Erro ao ler {newick_file}: {e}")
                    continue
            
            if batch_strings:
                # Processar lote
                batch_mtree = toytree.mtree(batch_strings)
                all_trees.extend(batch_mtree.treelist)
                
                # Limpeza de memória
                del batch_mtree
                del batch_strings
                gc.collect()
        
        if not all_trees:
            print("❌ Nenhuma árvore válida para cloud tree")
            return False
        
        # Criar multitree final
        mtree = toytree.mtree([tree.write() for tree in all_trees])
        
        # Aplicar mapeamento de nomes
        if index_to_name:
            for tree in mtree.treelist:
                for node in tree.treenode.traverse():
                    if node.is_leaf() and node.name in index_to_name:
                        node.name = index_to_name[node.name]
        
        # Dimensões adaptativas (conservadoras)
        width = max(600, min(1200, num_variables * 10))
        height = max(400, min(800, num_variables * 8))
        
        canvas, axes, mark = mtree.draw(
            width=width,
            height=height,
            node_labels=False,
            tip_labels=True,
            tip_labels_style={"font-size": max(6, min(10, 150 // num_variables))}
        )
        
        import toyplot.pdf
        toyplot.pdf.render(canvas, output_path)
        print(f"✅ Cloud Tree salva: {os.path.basename(output_path)}")
        
        # Limpeza final
        del mtree
        del all_trees
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao gerar Cloud Tree: {e}")
        return False

def generate_memory_efficient_consensus_tree(newick_files, output_path, index_to_name, num_variables):
    """
    Gera consensus tree com uso eficiente de memória.
    """
    try:
        import toytree
        print("🌲 Gerando Consensus Tree (memory-efficient)...")
        
        # Usar apenas uma amostra menor para consensus
        sample_for_consensus = newick_files[:20]  # Máximo 20 árvores para consensus
        
        newick_strings = []
        for newick_file in sample_for_consensus:
            try:
                with open(newick_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        newick_strings.append(content)
            except Exception as e:
                continue
        
        if not newick_strings:
            print("❌ Nenhuma árvore válida para consensus")
            return False
        
        # Criar multitree e consensus
        mtree = toytree.mtree(newick_strings)
        consensus_tree = mtree.get_consensus_tree()
        
        # Aplicar mapeamento de nomes
        if index_to_name:
            for node in consensus_tree.treenode.traverse():
                if node.is_leaf() and node.name in index_to_name:
                    node.name = index_to_name[node.name]
        
        # Dimensões adaptativas
        width = max(600, min(1200, num_variables * 10))
        height = max(400, min(800, num_variables * 8))
        
        canvas, axes, mark = consensus_tree.draw(
            width=width,
            height=height,
            node_labels=True,
            node_labels_style={"font-size": 8},
            tip_labels=True,
            tip_labels_style={"font-size": max(6, min(10, 150 // num_variables))}
        )
        
        import toyplot.pdf
        toyplot.pdf.render(canvas, output_path)
        print(f"✅ Consensus Tree salva: {os.path.basename(output_path)}")
        
        # Limpeza
        del mtree
        del consensus_tree
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao gerar Consensus Tree: {e}")
        return False

def generate_memory_efficient_biopython_tree(newick_files, output_path, index_to_name, num_variables):
    """
    Gera árvore biopython com uso eficiente de memória.
    """
    try:
        from Bio import Phylo
        print("🧬 Gerando Biopython Tree (memory-efficient)...")
        
        # Usar apenas a primeira árvore válida
        for newick_file in newick_files[:5]:  # Tentar até 5 arquivos
            try:
                tree = Phylo.read(newick_file, "newick")
                break
            except Exception:
                continue
        else:
            print("❌ Nenhuma árvore válida para biopython")
            return False
        
        # Aplicar mapeamento de nomes
        if index_to_name:
            for clade in tree.find_clades():
                if clade.name and clade.name in index_to_name:
                    original_name = index_to_name[clade.name]
                    # Truncar nomes longos
                    if len(original_name) > 15:
                        clade.name = original_name[:12] + "..."
                    else:
                        clade.name = original_name
        
        # Dimensões adaptativas
        fig_width = max(8, min(20, num_variables * 0.3))
        fig_height = max(6, min(15, num_variables * 0.25))
        
        plt.figure(figsize=(fig_width, fig_height))
        Phylo.draw(tree, do_show=False, 
                  axes=plt.gca(),
                  label_func=lambda x: x.name if x.name else "")
        
        plt.title("Phylogenetic Tree (Unified)", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Biopython Tree salva: {os.path.basename(output_path)}")
        
        # Limpeza
        del tree
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao gerar Biopython Tree: {e}")
        return False

def generate_processing_summary(newick_files, output_path, total_files):
    """
    Gera um resumo visual do processamento.
    """
    try:
        print("📊 Gerando resumo do processamento...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Estatísticas gerais
        ax1.text(0.5, 0.7, f"Total de Arquivos Newick: {total_files}", 
                ha='center', va='center', fontsize=14, fontweight='bold')
        ax1.text(0.5, 0.5, f"Amostra Processada: {len(newick_files)}", 
                ha='center', va='center', fontsize=12)
        ax1.text(0.5, 0.3, f"Percentual: {len(newick_files)/total_files*100:.1f}%", 
                ha='center', va='center', fontsize=12)
        ax1.set_title("Estatísticas do Processamento")
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        
        # 2. Distribuição por fatia (se possível extrair do nome)
        slice_counts = {}
        for f in newick_files:
            try:
                # Extrair número da fatia do nome do arquivo
                basename = os.path.basename(f)
                if 'slice_' in basename:
                    slice_num = basename.split('slice_')[1].split('_')[0]
                    slice_counts[slice_num] = slice_counts.get(slice_num, 0) + 1
            except:
                pass
        
        if slice_counts:
            slices = list(slice_counts.keys())[:10]  # Mostrar apenas 10 primeiras
            counts = [slice_counts[s] for s in slices]
            ax2.bar(range(len(slices)), counts)
            ax2.set_title("Distribuição por Fatia (Top 10)")
            ax2.set_xlabel("Fatia")
            ax2.set_ylabel("Número de Arquivos")
            ax2.set_xticks(range(len(slices)))
            ax2.set_xticklabels(slices, rotation=45)
        else:
            ax2.text(0.5, 0.5, "Distribuição por fatia\nnão disponível", 
                    ha='center', va='center')
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
        
        # 3. Tamanhos dos arquivos
        file_sizes = []
        for f in newick_files[:50]:  # Amostra de 50 arquivos
            try:
                size = os.path.getsize(f) / 1024  # KB
                file_sizes.append(size)
            except:
                pass
        
        if file_sizes:
            ax3.hist(file_sizes, bins=20, alpha=0.7, edgecolor='black')
            ax3.set_title("Distribuição de Tamanhos")
            ax3.set_xlabel("Tamanho (KB)")
            ax3.set_ylabel("Frequência")
        else:
            ax3.text(0.5, 0.5, "Dados de tamanho\nnão disponíveis", 
                    ha='center', va='center')
            ax3.set_xlim(0, 1)
            ax3.set_ylim(0, 1)
            ax3.axis('off')
        
        # 4. Informações técnicas
        ax4.text(0.5, 0.8, "Configuração de Memória", 
                ha='center', va='center', fontsize=14, fontweight='bold')
        ax4.text(0.5, 0.6, "✅ Amostragem Representativa", 
                ha='center', va='center', fontsize=10)
        ax4.text(0.5, 0.5, "✅ Processamento em Lotes", 
                ha='center', va='center', fontsize=10)
        ax4.text(0.5, 0.4, "✅ Limpeza Agressiva de Memória", 
                ha='center', va='center', fontsize=10)
        ax4.text(0.5, 0.3, "✅ Fallbacks Robustos", 
                ha='center', va='center', fontsize=10)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        
        plt.suptitle("Resumo da Visualização Unificada (Memory-Efficient)", 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Resumo salvo: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao gerar resumo: {e}")
        return False

def generate_memory_efficient_unified_visualization(compiled_newick_files, output_dir, original_file):
    """
    Versão otimizada da geração de visualização unificada que evita OOM.
    
    Args:
        compiled_newick_files (list): Lista de arquivos newick compilados
        output_dir (str): Diretório de saída
        original_file (str): Arquivo original processado
    """
    print(f"\n🚀 GERANDO VISUALIZAÇÃO UNIFICADA (MEMORY-EFFICIENT)")
    print("="*60)
    
    if not compiled_newick_files:
        print("❌ Nenhum arquivo newick disponível para visualização")
        return
    
    viz_dir = os.path.join(output_dir, "unified_visualization")
    os.makedirs(viz_dir, exist_ok=True)
    
    total_files = len(compiled_newick_files)
    print(f"📊 Total de arquivos newick: {total_files}")
    
    # Criar mapeamento de nomes das variáveis
    try:
        df = pd.read_csv(original_file)
        index_to_name = {f"col_{i}.txt": col for i, col in enumerate(df.columns)}
        num_variables = len(df.columns)
        print(f"📋 Variáveis detectadas: {num_variables}")
    except Exception as e:
        print(f"⚠️  Erro ao ler arquivo original: {e}")
        index_to_name = {}
        num_variables = 50  # fallback
    
    # Calcular amostra segura
    safe_sample_size = calculate_memory_safe_sample_size(total_files)
    representative_files = select_representative_sample(compiled_newick_files, safe_sample_size)
    
    # Forçar limpeza de memória antes de começar
    gc.collect()
    
    success_count = 0
    
    # === CLOUD TREE ===
    cloud_path = os.path.join(viz_dir, "cloud_tree.pdf")
    if generate_memory_efficient_cloud_tree(representative_files, cloud_path, index_to_name, num_variables):
        success_count += 1
    
    # === CONSENSUS TREE ===
    consensus_path = os.path.join(viz_dir, "consensus_tree.pdf")
    if generate_memory_efficient_consensus_tree(representative_files, consensus_path, index_to_name, num_variables):
        success_count += 1
    
    # === BIOPYTHON TREE ===
    biopython_path = os.path.join(viz_dir, "tree_biopython.png")
    if generate_memory_efficient_biopython_tree(representative_files, biopython_path, index_to_name, num_variables):
        success_count += 1
    
    # === RESUMO DO PROCESSAMENTO ===
    summary_path = os.path.join(viz_dir, "processing_summary_efficient.png")
    if generate_processing_summary(representative_files, summary_path, total_files):
        success_count += 1
    
    # Limpeza final
    gc.collect()
    
    print(f"\n🎯 VISUALIZAÇÃO UNIFICADA CONCLUÍDA")
    print(f"✅ {success_count}/4 visualizações geradas com sucesso")
    print(f"📁 Diretório: {viz_dir}")
    print(f"💾 Uso de memória otimizado: {len(representative_files)}/{total_files} arquivos processados")

if __name__ == "__main__":
    # Teste básico
    print("🧪 Testando geração de visualização memory-efficient...")
    
    # Exemplo de uso
    test_files = ["/path/to/newick1.newick", "/path/to/newick2.newick"]
    test_output = "/tmp/test_viz"
    test_original = "/path/to/original.csv"
    
    # generate_memory_efficient_unified_visualization(test_files, test_output, test_original)
    print("✅ Script carregado com sucesso!")
