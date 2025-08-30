#!/usr/bin/env python3
"""
Script para executar análise de bootstrap no DAMICORE com múltiplas sementes aleatórias.

Uso:
    python run_bootstrap_analysis.py input.csv --n_bootstraps 100 --output_dir resultados_bootstrap
"""

import os
import sys
import subprocess
import argparse
import json
import shutil
import random
import numpy as np
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_damicore(input_file, output_dir, seed=None):
    """Executa o DAMICORE com uma semente aleatória específica."""
    try:
        # Criar diretório de saída para esta execução
        run_dir = os.path.join(output_dir, f"run_{seed}" if seed is not None else "original")
        os.makedirs(run_dir, exist_ok=True)
        
        # Configurar a semente aleatória se fornecida
        if seed is not None:
            # Criar uma cópia temporária do arquivo de entrada com amostragem aleatória
            import pandas as pd
            df = pd.read_csv(input_file)
            sampled_df = df.sample(frac=1.0, replace=True, random_state=seed).reset_index(drop=True)
            temp_input = os.path.join(output_dir, f"temp_bootstrap_{seed}.csv")
            sampled_df.to_csv(temp_input, index=False)
            input_to_use = temp_input
        else:
            input_to_use = input_file
        
        # Comando para executar o DAMICORE
        cmd = [
            sys.executable,  # Usa o mesmo interpretador Python
            os.path.join(os.path.dirname(__file__), "src/scripts/DAMICORE_Filograma_script.py"),
            input_to_use,
            "--output", run_dir
        ]
        
        # Executar o comando
        print(f"🚀 Executando DAMICORE com semente {seed}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Limpar arquivo temporário se criado
        if seed is not None and os.path.exists(temp_input):
            os.remove(temp_input)
        
        # Verificar se a execução foi bem-sucedida
        if result.returncode != 0:
            print(f"❌ Erro na execução com semente {seed}:")
            print(result.stderr)
            return None
            
        # Encontrar o arquivo de árvore gerado
        tree_file = os.path.join(run_dir, "tree.newick")
        if not os.path.exists(tree_file):
            print(f"⚠️  Arquivo de árvore não encontrado em {run_dir}")
            return None
            
        return {
            'seed': seed,
            'directory': run_dir,
            'tree_file': tree_file,
            'output': result.stdout
        }
        
    except Exception as e:
        print(f"❌ Erro ao executar DAMICORE com semente {seed}: {str(e)}")
        return None

def generate_consensus_tree(tree_files, output_file, min_support=0.8):
    """Gera uma árvore de consenso a partir de múltiplas árvores."""
    try:
        import toytree
        
        # Carregar todas as árvores
        trees = []
        for tf in tree_files:
            try:
                tree = toytree.tree(tf)
                trees.append(tree)
            except Exception as e:
                print(f"⚠️  Erro ao carregar árvore {tf}: {str(e)}")
        
        if not trees:
            print("❌ Nenhuma árvore válida para gerar consenso")
            return False
            
        # Gerar árvore de consenso
        print(f"🌳 Gerando árvore de consenso com suporte mínimo de {min_support*100}%...")
        consensus = toytree.mtree(trees).consensus(
            min_support=min_support,
            rooted=True
        )
        
        # Salvar árvore de consenso
        consensus.write(output_file)
        print(f"✅ Árvore de consenso salva em {output_file}")
        
        # Gerar visualização se possível
        try:
            canvas, axes = consensus.draw(
                width=1600,
                height=1200,
                tip_labels=True,
                node_labels='support',
                node_sizes=12,
                node_colors='black',
                tip_labels_style={"font-size": "10px"}
            )
            
            viz_file = output_file.replace('.newick', '.pdf')
            import toyplot.pdf
            toyplot.pdf.Writer().write(canvas, viz_file)
            print(f"✅ Visualização da árvore salva em {viz_file}")
        except Exception as e:
            print(f"⚠️  Não foi possível gerar visualização: {str(e)}")
        
        return True
        
    except ImportError:
        print("⚠️  Biblioteca toytree não encontrada. Não foi possível gerar árvore de consenso.")
        return False
    except Exception as e:
        print(f"❌ Erro ao gerar árvore de consenso: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Executar análise de bootstrap no DAMICORE')
    parser.add_argument('input_file', help='Arquivo CSV de entrada')
    parser.add_argument('--n_bootstraps', type=int, default=100,
                       help='Número de reamostragens bootstrap (padrão: 100)')
    parser.add_argument('--output_dir', default='bootstrap_results',
                       help='Diretório de saída (padrão: bootstrap_results)')
    parser.add_argument('--n_jobs', type=int, default=os.cpu_count(),
                       help='Número de jobs paralelos (padrão: número de CPUs)')
    parser.add_argument('--min_support', type=float, default=0.8,
                       help='Suporte mínimo para árvore de consenso (0-1, padrão: 0.8)')
    
    args = parser.parse_args()
    
    # Criar diretório de saída
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🚀 Iniciando análise de bootstrap com {args.n_bootstraps} reamostragens")
    print(f"📁 Diretório de saída: {output_dir}")
    print(f"⚡ Usando {args.n_jobs} núcleos de CPU")
    
    # Executar a análise original (sem bootstrap primeiro)
    print("\n🔍 Executando análise original (sem bootstrap)...")
    original_result = run_damicore(args.input_file, output_dir, seed=None)
    
    if original_result is None:
        print("❌ Falha na execução da análise original. Abortando...")
        return 1
    
    # Executar as reamostragens bootstrap em paralelo
    print(f"\n🔄 Iniciando {args.n_bootstraps} reamostragens bootstrap...")
    seeds = list(range(1, args.n_bootstraps + 1))
    all_results = [original_result]
    
    with ProcessPoolExecutor(max_workers=args.n_jobs) as executor:
        futures = {
            executor.submit(run_damicore, args.input_file, output_dir, seed): seed 
            for seed in seeds
        }
        
        for future in as_completed(futures):
            seed = futures[future]
            try:
                result = future.result()
                if result is not None:
                    all_results.append(result)
                    print(f"✅ Concluído bootstrap {seed}/{args.n_bootstraps}")
            except Exception as e:
                print(f"❌ Erro no bootstrap {seed}: {str(e)}")
    
    # Coletar arquivos de árvore
    tree_files = [r['tree_file'] for r in all_results if r is not None and 'tree_file' in r]
    
    if len(tree_files) < 2:
        print("❌ Número insuficiente de árvores válidas para gerar consenso")
        return 1
    
    # Gerar árvore de consenso
    consensus_file = os.path.join(output_dir, "consensus_tree.newick")
    if generate_consensus_tree(tree_files, consensus_file, args.min_support):
        print(f"\n✅ Análise de bootstrap concluída com sucesso!")
        print(f"🌳 Árvore de consenso salva em: {consensus_file}")
        print(f"📊 Total de árvores usadas no consenso: {len(tree_files)}")
    else:
        print("❌ Não foi possível gerar a árvore de consenso")
        return 1
    
    # Salvar metadados da execução
    metadata = {
        'input_file': os.path.abspath(args.input_file),
        'output_dir': output_dir,
        'n_bootstraps': args.n_bootstraps,
        'n_successful': len(tree_files) - 1,  # menos a execução original
        'min_support': args.min_support,
        'completion_time': datetime.now().isoformat(),
        'tree_files': tree_files
    }
    
    with open(os.path.join(output_dir, 'bootstrap_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
