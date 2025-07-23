#!/usr/bin/env python3
"""
Script para gerar visualizações (Cloud Tree, Consensus Tree, Biopython Tree) 
a partir de arquivos newick já existentes em um diretório.

Baseado na lógica do DAMICORE_Filograma_script.py, mas focado apenas na visualização.
"""

import os
import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
# Configurar backend não-interativo do matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import toytree
import toyplot
import toyplot.pdf
from Bio import Phylo
from io import StringIO

def get_column_mapping_from_csv(csv_path):
    """
    Extrai o mapeamento de índices para nomes de colunas do arquivo CSV original.
    """
    try:
        # Lê apenas o header do CSV
        df = pd.read_csv(csv_path, nrows=0)
        columns = df.columns.tolist()
        
        # Cria mapeamento índice -> nome
        index_to_name = {str(i): name for i, name in enumerate(columns)}
        name_to_index = {name: str(i) for i, name in enumerate(columns)}
        
        print(f"✅ Mapeamento de colunas carregado: {len(columns)} colunas")
        return index_to_name, name_to_index
        
    except Exception as e:
        print(f"⚠️  Erro ao carregar CSV: {e}")
        print("Usando mapeamento genérico...")
        return None, None

def collect_newick_files(newick_dir):
    """
    Coleta todos os arquivos .newick de um diretório.
    """
    newick_files = []
    plain_newicks = []
    
    if not os.path.exists(newick_dir):
        print(f"❌ Diretório não encontrado: {newick_dir}")
        return [], []
    
    print(f"📂 Coletando arquivos newick de: {newick_dir}")
    
    for filename in sorted(os.listdir(newick_dir)):
        if filename.endswith('.newick'):
            filepath = os.path.join(newick_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                    if content:  # Só adiciona se não estiver vazio
                        plain_newicks.append(content)
                        newick_files.append(filename)
            except Exception as e:
                print(f"⚠️  Erro ao ler {filename}: {e}")
    
    print(f"✅ {len(plain_newicks)} arquivos newick coletados")
    return plain_newicks, newick_files

def generate_cloud_tree(plain_newicks, index_to_name, output_dir):
    """
    Gera Cloud Tree usando toytree.
    """
    try:
        print("📊 Gerando Cloud Tree...")
        
        string_newicks = "\n".join(plain_newicks)
        mtree = toytree.mtree(string_newicks)
        
        # Processar os labels para Cloud Tree
        cloud_new_list = []
        for i in mtree.get_tip_labels():
            j = i.strip("''")  # Remove aspas
            # Extrair apenas o número do nome do arquivo (entre 'col_' e '.txt')
            if 'col_' in j and '.txt' in j:
                num = j.split('col_')[1].split('.txt')[0]
                cloud_new_list.append(num)
            else:
                cloud_new_list.append(j)  # Usa o label original se não seguir o padrão
        
        # Converter índices para nomes originais se disponível
        cloud_tip_labels = []
        for m in cloud_new_list:
            if index_to_name and m in index_to_name:
                cloud_tip_labels.append(index_to_name[m])
            else:
                cloud_tip_labels.append(f"col_{m}")  # Fallback genérico
        
        # Desenhar Cloud Tree
        canvas_tuple = mtree.draw_cloud_tree(
            tip_labels=cloud_tip_labels,
            node_labels=False,
            use_edge_lengths=False,
            node_sizes=16
        )
        canvas = canvas_tuple[0]
        
        cloud_tree_path = os.path.join(output_dir, "cloud_tree.pdf")
        toyplot.pdf.render(canvas, cloud_tree_path)
        
        print(f"✅ Cloud tree salva em: {cloud_tree_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar Cloud Tree: {e}")
        return False

def generate_consensus_tree(plain_newicks, index_to_name, output_dir):
    """
    Gera Consensus Tree usando toytree.
    """
    try:
        print("📊 Gerando Consensus Tree...")
        
        string_newicks = "\n".join(plain_newicks)
        mtree = toytree.mtree(string_newicks)
        ctre = mtree.get_consensus_tree()
        
        # Processar os labels para Consensus Tree
        new_list = []
        for i in ctre.get_tip_labels():
            j = i.strip("''")  # Remove aspas
            # Extrair apenas o número do nome do arquivo (entre 'col_' e '.txt')
            if 'col_' in j and '.txt' in j:
                num = j.split('col_')[1].split('.txt')[0]
                new_list.append(num)
            else:
                new_list.append(j)  # Usa o label original se não seguir o padrão
        
        # Converter índices para nomes originais se disponível
        new_tip_labels = []
        for m in new_list:
            if index_to_name and m in index_to_name:
                new_tip_labels.append(index_to_name[m])
            else:
                new_tip_labels.append(f"col_{m}")  # Fallback genérico
        
        # Garantir que os valores de suporte estejam acessíveis
        for node in ctre.treenode.traverse():
            node.support = node.support
        
        # Desenhar a árvore de consenso
        canvas_tuple = ctre.draw(
            tip_labels=new_tip_labels,
            node_labels='support',
            use_edge_lengths=False,
            node_sizes=32
        )
        consensus_canvas = canvas_tuple[0]
        
        consensus_tree_path = os.path.join(output_dir, "consensus_tree.pdf")
        toyplot.pdf.render(consensus_canvas, consensus_tree_path)
        
        print(f"✅ Consensus tree salva em: {consensus_tree_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar Consensus Tree: {e}")
        return False

def generate_biopython_tree(plain_newicks, index_to_name, output_dir):
    """
    Gera visualização usando Biopython (primeira árvore newick).
    """
    try:
        print("📊 Gerando visualização Biopython...")
        
        if not plain_newicks:
            print("❌ Nenhum arquivo newick disponível")
            return False
        
        # Criar um arquivo temporário com o primeiro newick
        temp_newick_path = os.path.join(output_dir, 'temp_tree.newick')
        with open(temp_newick_path, 'w') as f:
            f.write(plain_newicks[0])
        
        # Ler e processar a árvore
        tree = Phylo.read(temp_newick_path, 'newick')
        
        # Substituir os nós folha pelos nomes originais
        for leaf in tree.get_terminals():
            if leaf.name and 'col_' in leaf.name and '.txt' in leaf.name:
                num = leaf.name.split('col_')[1].split('.txt')[0]
                if index_to_name and num in index_to_name:
                    leaf.name = index_to_name[num]
                else:
                    leaf.name = f"col_{num}"
        
        # Configurar a figura
        fig = plt.figure(figsize=(12, 8))
        axes = fig.add_subplot(1, 1, 1)
        
        # Desenhar a árvore com nomes originais
        Phylo.draw(tree, axes=axes, show_confidence=True)
        plt.title('Árvore Filogenética (Biopython)')
        
        biopython_tree_path = os.path.join(output_dir, 'tree_biopython.png')
        plt.savefig(biopython_tree_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Árvore Biopython salva em: {biopython_tree_path}")
        
        # Remove arquivo temporário
        if os.path.exists(temp_newick_path):
            os.remove(temp_newick_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar visualização Biopython: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Gera visualizações a partir de arquivos newick existentes"
    )
    parser.add_argument(
        "newick_dir", 
        help="Diretório contendo arquivos .newick"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Diretório de saída (padrão: mesmo diretório dos newick)",
        default=None
    )
    parser.add_argument(
        "-c", "--csv", 
        help="Arquivo CSV original para mapeamento de colunas",
        default=None
    )
    parser.add_argument(
        "--cloud-only", 
        action="store_true",
        help="Gera apenas Cloud Tree"
    )
    parser.add_argument(
        "--consensus-only", 
        action="store_true",
        help="Gera apenas Consensus Tree"
    )
    parser.add_argument(
        "--biopython-only", 
        action="store_true",
        help="Gera apenas visualização Biopython"
    )
    
    args = parser.parse_args()
    
    # Configurar diretórios
    newick_dir = os.path.abspath(args.newick_dir)
    output_dir = args.output if args.output else newick_dir
    output_dir = os.path.abspath(output_dir)
    
    print("=" * 80)
    print("🎨 GERADOR DE VISUALIZAÇÕES A PARTIR DE ARQUIVOS NEWICK")
    print("=" * 80)
    print(f"📂 Diretório de entrada: {newick_dir}")
    print(f"📁 Diretório de saída: {output_dir}")
    
    # Criar diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Carregar mapeamento de colunas se CSV fornecido
    index_to_name = None
    if args.csv:
        print(f"📄 Carregando mapeamento de colunas de: {args.csv}")
        index_to_name, _ = get_column_mapping_from_csv(args.csv)
    
    # Coletar arquivos newick
    plain_newicks, newick_files = collect_newick_files(newick_dir)
    
    if not plain_newicks:
        print("❌ Nenhum arquivo newick válido encontrado!")
        sys.exit(1)
    
    print(f"📊 Arquivos encontrados: {newick_files[:5]}..." if len(newick_files) > 5 else f"📊 Arquivos: {newick_files}")
    
    # Gerar visualizações
    success_count = 0
    
    if not any([args.cloud_only, args.consensus_only, args.biopython_only]):
        # Gerar todas as visualizações
        if generate_cloud_tree(plain_newicks, index_to_name, output_dir):
            success_count += 1
        if generate_consensus_tree(plain_newicks, index_to_name, output_dir):
            success_count += 1
        if generate_biopython_tree(plain_newicks, index_to_name, output_dir):
            success_count += 1
    else:
        # Gerar apenas as visualizações selecionadas
        if args.cloud_only and generate_cloud_tree(plain_newicks, index_to_name, output_dir):
            success_count += 1
        if args.consensus_only and generate_consensus_tree(plain_newicks, index_to_name, output_dir):
            success_count += 1
        if args.biopython_only and generate_biopython_tree(plain_newicks, index_to_name, output_dir):
            success_count += 1
    
    # Resumo final
    print("\n" + "=" * 80)
    print("🎉 GERAÇÃO DE VISUALIZAÇÕES CONCLUÍDA!")
    print("=" * 80)
    print(f"✅ {success_count} visualizações geradas com sucesso")
    
    # Listar arquivos gerados
    generated_files = []
    for filename in ["cloud_tree.pdf", "consensus_tree.pdf", "tree_biopython.png"]:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath) / 1024  # KB
            generated_files.append(f"  ✅ {filename} ({file_size:.1f} KB)")
    
    if generated_files:
        print("\n📁 ARQUIVOS GERADOS:")
        for file_info in generated_files:
            print(file_info)
    
    print(f"\n📁 Todos os resultados salvos em: {output_dir}")
    print("=" * 80)

if __name__ == "__main__":
    main()
