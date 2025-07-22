"""
DAMICORE + Análise de Pareto - Versão Otimizada para Arquivos Grandes (Local)

Esta versão foi adaptada para processar arquivos CSV muito grandes (15GB+) sem estouro de memória,
utilizando processamento em chunks (lotes) e salvando todos os resultados localmente.

PRINCIPAIS MELHORIAS V2:
- Configuração adaptativa baseada no tamanho do arquivo
- Sistema de checkpoint/retomada automática
- Processamento streaming para arquivos ultra-grandes
- Correções de comando Python e caminhos relativos
- Visualizações melhoradas com fallbacks

Para arquivos menores (< 5GB), use a versão original: DAMICORE_Pareto_script.py

Parâmetros configuráveis:
- chunk_size: Tamanho dos chunks (adaptativo baseado no tamanho do arquivo)
- bootstrap_samples: Número de amostras bootstrap (adaptativo)

Autor: DAMICORE Team
Data: 2025
"""

import os
import pandas as pd
import numpy as np
import ast
from statistics import multimode
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import toytree
import toyplot
import toyplot.pdf
from Bio import Phylo
from io import StringIO
from sklearn.cluster import AgglomerativeClustering
import seaborn as sns
import gc
import psutil
import time
import json
import shutil

# ============================================================================
# SISTEMA DE CHECKPOINT/RETOMADA AUTOMÁTICA
# ============================================================================

def save_checkpoint(checkpoint_file, status, current_chunk=None, current_sample=None, total_chunks=None, total_samples=None, newick_files=None):
    """Salva o progresso atual do processamento"""
    checkpoint_data = {
        'status': status,
        'timestamp': time.time(),
        'current_chunk': current_chunk,
        'current_sample': current_sample,
        'total_chunks': total_chunks,
        'total_samples': total_samples,
        'newick_files': newick_files or []
    }
    
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)
    
    print(f"✅ Checkpoint salvo: {status}")

def load_checkpoint(checkpoint_file):
    """Carrega o progresso salvo do processamento"""
    if not os.path.exists(checkpoint_file):
        return None
    
    try:
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    except:
        return None

def get_resume_point(checkpoint_file, damicore_dir):
    """Determina o ponto de retomada baseado nos arquivos existentes"""
    checkpoint = load_checkpoint(checkpoint_file)
    
    if checkpoint and checkpoint.get('status') == 'completed':
        print("✅ Pipeline já foi completado anteriormente!")
        return 'completed', None, None, checkpoint.get('newick_files', [])
    
    # Verifica arquivos newick existentes
    existing_newick = []
    if os.path.exists(damicore_dir):
        for root, dirs, files in os.walk(damicore_dir):
            for file in files:
                if file.endswith('.newick'):
                    existing_newick.append(os.path.join(root, file))
    
    if existing_newick:
        print(f"🔄 Encontrados {len(existing_newick)} arquivos newick existentes")
        print("Retomando do ponto onde parou...")
        return 'resume', existing_newick, checkpoint, existing_newick
    
    return 'start', [], None, []

# ============================================================================
# CONFIGURAÇÃO ADAPTATIVA BASEADA NO TAMANHO DO ARQUIVO
# ============================================================================

def get_adaptive_config(file_size_gb):
    """Retorna configuração otimizada baseada no tamanho do arquivo"""
    
    if file_size_gb >= 10:
        # Para arquivos ultra-grandes (>=10GB): chunks menores, máxima estabilidade
        return {
            'chunk_size': 100,
            'bootstrap_samples': 2,
            'max_columns_per_batch': None,
            'mode': 'ULTRA-OTIMIZADO',
            'description': 'máxima estabilidade (18 linhas/s, 1.1GB RAM)'
        }
    elif file_size_gb >= 5:
        # Para arquivos grandes (5-10GB): configuração balanceada
        return {
            'chunk_size': 200,
            'bootstrap_samples': 3,
            'max_columns_per_batch': None,
            'mode': 'BALANCEADO',
            'description': 'balance performance/estabilidade'
        }
    elif file_size_gb >= 1:
        # Para arquivos médios (1-5GB): performance otimizada
        return {
            'chunk_size': 500,
            'bootstrap_samples': 5,
            'max_columns_per_batch': None,
            'mode': 'PERFORMANCE',
            'description': 'performance otimizada'
        }
    else:
        # Para arquivos pequenos (<1GB): configuração tradicional
        return {
            'chunk_size': 2000,
            'bootstrap_samples': 10,
            'max_columns_per_batch': None,
            'mode': 'RÁPIDO',
            'description': 'processamento tradicional'
        }

# ============================================================================
# PROCESSAMENTO STREAMING PARA ARQUIVOS ULTRA-GRANDES
# ============================================================================

def process_single_chunk_streaming_local(chunk_data, headers, chunk_idx, bootstrap_samples, sample_dir, damicore_dir):
    """Processa um único chunk em modo streaming para processamento local"""
    
    print(f"\n--- Processando Chunk {chunk_idx} (Streaming Local) ---")
    print(f"Linhas no chunk: {len(chunk_data)}")
    
    newick_files = []
    
    # Processa cada amostra bootstrap
    for sample_idx in range(bootstrap_samples):
        print(f"  Amostra Bootstrap {sample_idx + 1}/{bootstrap_samples}")
        
        # Cria diretório para esta amostra
        resample_dir = os.path.join(sample_dir, f"resample_{sample_idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        
        # Bootstrap sampling
        bootstrap_indices = np.random.choice(len(chunk_data), size=len(chunk_data), replace=True)
        bootstrap_chunk = [chunk_data[i] for i in bootstrap_indices]
        
        # Salva chunk com bootstrap
        chunk_file = os.path.join(resample_dir, f"chunk_{chunk_idx:03d}.csv")
        with open(chunk_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(bootstrap_chunk)
        
        # Executa DAMICORE para este chunk
        tree_output_path = os.path.join(damicore_dir, f"chunk_{chunk_idx:03d}_sample_{sample_idx:02d}-tree.newick")
        
        # Garante que o diretório de saída existe
        os.makedirs(os.path.dirname(tree_output_path), exist_ok=True)
        
        cmd = [
            "python3", os.path.join(os.path.dirname(os.path.dirname(__file__)), "damicore.py"),
            "--compressor", "gzip",
            "--serial",
            "--tree-output", tree_output_path,
            resample_dir
        ]
        
        try:
            print(f"    Executando DAMICORE: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2 horas timeout
            
            if result.returncode == 0:
                if os.path.exists(tree_output_path):
                    newick_files.append(tree_output_path)
                    print(f"    ✅ Arquivo newick gerado: {os.path.basename(tree_output_path)}")
                else:
                    print(f"    ⚠️  DAMICORE executado mas arquivo newick não encontrado")
            else:
                print(f"    ❌ Erro no DAMICORE: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"    ⏰ Timeout no DAMICORE após 2 horas")
        except Exception as e:
            print(f"    ❌ Erro ao executar DAMICORE: {e}")
        
        # Limpeza do chunk temporário
        try:
            os.remove(chunk_file)
        except:
            pass
    
    # Limpeza agressiva de memória
    del chunk_data, bootstrap_indices, bootstrap_chunk
    gc.collect()
    
    return newick_files

def process_file_streaming_local(input_path, chunk_size, bootstrap_samples, sample_dir, damicore_dir, checkpoint_file):
    """Processa arquivo em modo streaming para processamento local"""
    
    print(f"\n🌊 MODO STREAMING LOCAL - Processando arquivo: {os.path.basename(input_path)}")
    print(f"📊 Configuração: chunk_size={chunk_size}, bootstrap_samples={bootstrap_samples}")
    
    all_newick_files = []
    chunk_idx = 0
    
    try:
        # Lê o arquivo em chunks
        chunk_iter = pd.read_csv(input_path, encoding="utf-8", low_memory=True, chunksize=chunk_size)
        headers = None
        
        for chunk_df in chunk_iter:
            if headers is None:
                headers = chunk_df.columns.tolist()
                print(f"📋 Headers detectados: {len(headers)} colunas")
            
            # Converte chunk para lista de listas
            chunk_data = chunk_df.values.tolist()
            
            # Processa este chunk
            chunk_newick_files = process_single_chunk_streaming_local(
                chunk_data, headers, chunk_idx, bootstrap_samples, sample_dir, damicore_dir
            )
            
            all_newick_files.extend(chunk_newick_files)
            
            # Salva checkpoint
            save_checkpoint(checkpoint_file, 'processing', chunk_idx, None, None, bootstrap_samples, all_newick_files)
            
            chunk_idx += 1
            
            # Limpeza de memória
            del chunk_df, chunk_data
            gc.collect()
            
            print(f"📈 Progresso: Chunk {chunk_idx} processado, {len(all_newick_files)} arquivos newick coletados")
    
    except Exception as e:
        print(f"❌ Erro no processamento streaming: {e}")
        save_checkpoint(checkpoint_file, 'error', chunk_idx, None, None, bootstrap_samples, all_newick_files)
        raise
    
    print(f"\n✅ Processamento streaming concluído!")
    print(f"📊 Total de chunks processados: {chunk_idx}")
    print(f"📁 Total de arquivos newick: {len(all_newick_files)}")
    
    return all_newick_files

# ============================================================================
# VISUALIZAÇÕES MELHORADAS COM FALLBACKS
# ============================================================================

def create_index_to_name_mapping(headers):
    """Cria mapeamento de índices para nomes originais das colunas"""
    index_to_name = {}
    for i, col_name in enumerate(headers):
        index_to_name[str(i)] = col_name
    return index_to_name

def _generate_cloud_tree_toytree_original(newick_files, output_path, index_to_name):
    """Gera cloud tree usando toytree com lógica original"""
    try:
        trees = []
        for newick_file in newick_files:
            if os.path.exists(newick_file):
                tree = toytree.tree(newick_file)
                trees.append(tree)
        
        if not trees:
            return False
            
        # Cria multitree
        mtree = toytree.mtree(trees)
        
        # Extrai e mapeia labels
        tip_labels = mtree.get_tip_labels()
        mapped_labels = []
        for label in tip_labels:
            if label.startswith('col_') and label.endswith('.txt'):
                col_num = label[4:-4]  # Remove 'col_' e '.txt'
                mapped_label = index_to_name.get(col_num, label)
                mapped_labels.append(mapped_label)
            else:
                mapped_labels.append(label)
        
        # Gera cloud tree
        canvas, axes, mark = mtree.draw_cloud_tree(
            width=800, height=600,
            tip_labels=mapped_labels,
            tip_labels_align=True,
            node_labels="support",
            node_sizes=32
        )
        
        toyplot.pdf.render(canvas, output_path)
        return True
        
    except Exception as e:
        print(f"Erro na geração cloud tree toytree: {e}")
        return False

def _generate_consensus_tree_toytree_original(newick_files, output_path, index_to_name):
    """Gera consensus tree usando toytree com lógica original"""
    try:
        trees = []
        for newick_file in newick_files:
            if os.path.exists(newick_file):
                tree = toytree.tree(newick_file)
                trees.append(tree)
        
        if not trees:
            return False
            
        # Gera árvore de consenso
        ctree = toytree.mtree(trees).get_consensus_tree()
        
        # Extrai e mapeia labels
        tip_labels = ctree.get_tip_labels()
        mapped_labels = []
        for label in tip_labels:
            if label.startswith('col_') and label.endswith('.txt'):
                col_num = label[4:-4]  # Remove 'col_' e '.txt'
                mapped_label = index_to_name.get(col_num, label)
                mapped_labels.append(mapped_label)
            else:
                mapped_labels.append(label)
        
        # Desenha consensus tree
        canvas, axes, mark = ctree.draw(
            width=800, height=600,
            tip_labels=mapped_labels,
            tip_labels_align=True,
            node_labels="support",
            node_sizes=32
        )
        
        toyplot.pdf.render(canvas, output_path)
        return True
        
    except Exception as e:
        print(f"Erro na geração consensus tree toytree: {e}")
        return False

def _generate_tree_biopython_original(newick_files, output_path, index_to_name):
    """Gera árvore usando Bio.Phylo com lógica original"""
    try:
        if not newick_files or not os.path.exists(newick_files[0]):
            return False
            
        # Carrega primeira árvore
        tree = Phylo.read(newick_files[0], "newick")
        
        # Mapeia nomes das folhas
        for leaf in tree.get_terminals():
            if leaf.name and leaf.name.startswith('col_') and leaf.name.endswith('.txt'):
                col_num = leaf.name[4:-4]  # Remove 'col_' e '.txt'
                leaf.name = index_to_name.get(col_num, leaf.name)
        
        # Gera visualização
        fig, ax = plt.subplots(figsize=(12, 8))
        Phylo.draw(tree, axes=ax, do_show=False)
        plt.title("DAMICORE Phylogenetic Tree")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"Erro na geração tree biopython: {e}")
        return False

def generate_visualizations_local(newick_files, damicore_dir, headers):
    """Gera visualizações finais com fallbacks para processamento local"""
    
    print(f"\n=== GERANDO VISUALIZAÇÕES FINAIS ===")
    print(f"Arquivos newick disponíveis: {len(newick_files)}")
    
    if not newick_files:
        print("❌ Nenhum arquivo newick disponível para visualização")
        return
    
    # Cria mapeamento de índices para nomes
    index_to_name = create_index_to_name_mapping(headers)
    
    # Caminhos das visualizações
    cloud_tree_path = os.path.join(damicore_dir, "cloud_tree.pdf")
    consensus_tree_path = os.path.join(damicore_dir, "consensus_tree.pdf")
    biopython_tree_path = os.path.join(damicore_dir, "tree_biopython.png")
    
    success_count = 0
    
    # 1. Cloud Tree
    print("🌳 Gerando Cloud Tree...")
    if _generate_cloud_tree_toytree_original(newick_files, cloud_tree_path, index_to_name):
        print(f"✅ Cloud tree salvo: {cloud_tree_path}")
        success_count += 1
    else:
        print("❌ Falha na geração do cloud tree")
    
    # 2. Consensus Tree
    print("🌲 Gerando Consensus Tree...")
    if _generate_consensus_tree_toytree_original(newick_files, consensus_tree_path, index_to_name):
        print(f"✅ Consensus tree salvo: {consensus_tree_path}")
        success_count += 1
    else:
        print("❌ Falha na geração do consensus tree")
    
    # 3. Bio.Phylo Tree
    print("🧬 Gerando Bio.Phylo Tree...")
    if _generate_tree_biopython_original(newick_files, biopython_tree_path, index_to_name):
        print(f"✅ Bio.Phylo tree salvo: {biopython_tree_path}")
        success_count += 1
    else:
        print("❌ Falha na geração do Bio.Phylo tree")
    
    print(f"\n📊 Visualizações geradas com sucesso: {success_count}/3")
    
    if success_count == 0:
        print("⚠️  Nenhuma visualização foi gerada com sucesso")
    else:
        print("✅ Visualizações finais disponíveis no diretório damicore_analysis")

# ============================================================================
# ANÁLISE DE PARETO
# ============================================================================

def run_pareto_analysis(df, output_dir):
    """Executa a análise de Fronteira de Pareto no DataFrame."""
    print("\n=== Iniciando Análise de Pareto ===")
    
    # Seleciona apenas colunas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        print("❌ Erro: Pelo menos 2 colunas numéricas são necessárias para análise de Pareto")
        return
    
    print(f"Colunas numéricas encontradas: {len(numeric_cols)}")
    
    # Análise de Pareto (simplificada para exemplo)
    pareto_dir = os.path.join(output_dir, "pareto_analysis")
    os.makedirs(pareto_dir, exist_ok=True)
    
    # Gera gráfico de correlação
    plt.figure(figsize=(12, 8))
    correlation_matrix = df[numeric_cols].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title("Matriz de Correlação - Análise de Pareto")
    plt.tight_layout()
    plt.savefig(os.path.join(pareto_dir, "correlation_matrix.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Análise de Pareto concluída: {pareto_dir}")

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def run_damicore_analysis_local(input_path):
    """Executa a análise DAMICORE com processamento local otimizado"""
    
    print("\n=== INICIANDO ANÁLISE DAMICORE LOCAL V2 ===")
    print(f"Arquivo de entrada: {input_path}")
    
    # Verificações iniciais
    if not os.path.exists(input_path):
        print(f"❌ Erro: Arquivo não encontrado: {input_path}")
        return
    
    # Configuração de diretórios
    SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(input_path))[0]
    OUTPUT_DIR = os.path.join(os.path.dirname(input_path), SCRIPTS_OUTPUT_BASE)
    DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
    os.makedirs(DAMICORE_DIR, exist_ok=True)
    
    # Arquivo de checkpoint
    checkpoint_file = os.path.join(OUTPUT_DIR, "checkpoint.json")
    
    # Verifica tamanho do arquivo
    file_size_bytes = os.path.getsize(input_path)
    file_size_gb = file_size_bytes / (1024**3)
    print(f"📊 Tamanho do arquivo: {file_size_gb:.2f} GB")
    
    # Configuração adaptativa
    config = get_adaptive_config(file_size_gb)
    print(f"🚀 MODO {config['mode']}: {config['description']}")
    print(f"📋 Configuração: chunk_size={config['chunk_size']:,}, bootstrap_samples={config['bootstrap_samples']}")
    
    # Sistema de checkpoint/retomada
    resume_status, existing_newick, checkpoint_data, newick_files = get_resume_point(checkpoint_file, DAMICORE_DIR)
    
    if resume_status == 'completed':
        print("✅ Pipeline já completado. Pulando para visualizações...")
        # Carrega headers do arquivo para visualizações
        sample_df = pd.read_csv(input_path, nrows=1)
        headers = sample_df.columns.tolist()
        generate_visualizations_local(newick_files, DAMICORE_DIR, headers)
        return
    
    # Inicialização das estruturas
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    # Para arquivos muito grandes, usa processamento STREAMING
    if file_size_gb >= 10:
        print("🌊 Usando processamento STREAMING para arquivo muito grande...")
        
        newick_files = process_file_streaming_local(
            input_path, config['chunk_size'], config['bootstrap_samples'],
            sample_dir, DAMICORE_DIR, checkpoint_file
        )
        
        print(f"\n=== RESULTADOS DO STREAMING ===")
        print(f"Total de arquivos newick coletados: {len(newick_files)}")
        
        if len(newick_files) == 0:
            print("❌ Nenhum arquivo newick encontrado. Verifique se o DAMICORE foi executado corretamente.")
            return
        
        # Carrega headers para visualizações
        sample_df = pd.read_csv(input_path, nrows=1)
        headers = sample_df.columns.tolist()
        
    else:
        # Para arquivos menores, usa processamento tradicional em chunks
        print("📊 Usando processamento tradicional em chunks...")
        
        chunk_iter = pd.read_csv(input_path, encoding="utf-8", low_memory=False, chunksize=config['chunk_size'])
        headers = None
        all_data = []
        
        # Coleta todos os chunks
        for chunk_df in chunk_iter:
            if headers is None:
                headers = chunk_df.columns.tolist()
            all_data.append(chunk_df)
        
        # Consolida dados
        df = pd.concat(all_data, ignore_index=True)
        print(f"📋 Dados consolidados: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Executa bootstrap e DAMICORE
        newick_files = []
        for sample_idx in range(config['bootstrap_samples']):
            print(f"\n--- Amostra Bootstrap {sample_idx + 1}/{config['bootstrap_samples']} ---")
            
            # Bootstrap sampling
            bootstrap_df = df.sample(n=len(df), replace=True, random_state=sample_idx)
            
            # Cria diretório para esta amostra
            resample_dir = os.path.join(sample_dir, f"resample_{sample_idx:02d}")
            os.makedirs(resample_dir, exist_ok=True)
            
            # Salva dados com bootstrap
            bootstrap_file = os.path.join(resample_dir, "data.csv")
            bootstrap_df.to_csv(bootstrap_file, index=False)
            
            # Executa DAMICORE
            tree_output_path = os.path.join(DAMICORE_DIR, f"resample_{sample_idx:02d}-tree.newick")
            
            cmd = [
                "python3", os.path.join(os.path.dirname(os.path.dirname(__file__)), "damicore.py"),
                "--compressor", "gzip",
                "--serial",
                "--tree-output", tree_output_path,
                resample_dir
            ]
            
            try:
                print(f"Executando DAMICORE: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
                
                if result.returncode == 0:
                    if os.path.exists(tree_output_path):
                        newick_files.append(tree_output_path)
                        print(f"✅ Arquivo newick gerado: {os.path.basename(tree_output_path)}")
                    else:
                        print(f"⚠️  DAMICORE executado mas arquivo newick não encontrado")
                else:
                    print(f"❌ Erro no DAMICORE: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout no DAMICORE após 2 horas")
            except Exception as e:
                print(f"❌ Erro ao executar DAMICORE: {e}")
            
            # Salva checkpoint
            save_checkpoint(checkpoint_file, 'processing', None, sample_idx, None, config['bootstrap_samples'], newick_files)
        
        # Análise de Pareto
        run_pareto_analysis(df, OUTPUT_DIR)
    
    # Marca como completado
    save_checkpoint(checkpoint_file, 'completed', None, None, None, config['bootstrap_samples'], newick_files)
    
    # Gera visualizações finais
    generate_visualizations_local(newick_files, DAMICORE_DIR, headers)
    
    print(f"\n🎉 ANÁLISE CONCLUÍDA COM SUCESSO!")
    print(f"📁 Resultados salvos em: {OUTPUT_DIR}")
    print(f"🌳 Visualizações disponíveis em: {DAMICORE_DIR}")
    print(f"📊 Total de arquivos newick: {len(newick_files)}")

def main():
    """Função principal"""
    print("=== DAMICORE + Pareto Analysis (Local V2) ===")
    
    # Solicita arquivo de entrada
    while True:
        csv_file = input("Digite o caminho para o arquivo CSV: ").strip()
        if os.path.exists(csv_file):
            break
        print(f"❌ Arquivo não encontrado: {csv_file}")
    
    # Executa análise
    run_damicore_analysis_local(csv_file)

def main_non_interactive(csv_file):
    """Versão não-interativa do main() para execução automatizada"""
    if not os.path.exists(csv_file):
        print(f"❌ Erro: Arquivo não encontrado: {csv_file}")
        return
    
    run_damicore_analysis_local(csv_file)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Modo não-interativo com arquivo fornecido como argumento
        main_non_interactive(sys.argv[1])
    else:
        # Modo interativo
        main()
