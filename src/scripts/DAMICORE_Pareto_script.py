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

def run_damicore_analysis(input_path):
    """Executa a análise DAMICORE no arquivo de entrada."""
    print("\n=== Iniciando Análise DAMICORE ===")
    
    # Configuração de diretórios
    SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(input_path))[0]
    OUTPUT_DIR = os.path.join(os.path.dirname(input_path), SCRIPTS_OUTPUT_BASE)
    DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
    os.makedirs(DAMICORE_DIR, exist_ok=True)

    # === 1. Carregamento e pré-processamento ===
    print("Carregando dados...")
    original_df = pd.read_csv(input_path, encoding="utf-8", low_memory=False)
    original_columns = original_df.columns.tolist()

    # Criar dicionários para mapeamento bidirecional entre índices e nomes originais
    index_to_name = {str(i): name for i, name in enumerate(original_columns)}
    name_to_index = {name: str(i) for i, name in enumerate(original_columns)}

    # Criar DataFrame de trabalho com índices como nomes das colunas
    df = original_df.copy()
    df.columns = [str(i) for i in range(len(df.columns))]
    df = df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

    # === 2. Reamostragem bootstrap ===
    print("Realizando reamostragem bootstrap...")
    resampled_df_l = [df]
    for i in range(22):
        resampled_df_l.append(df.sample(n=df.shape[0], replace=True, random_state=i))

    # === 3. Salvamento das amostras ===
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    for idx, resampled_df in enumerate(resampled_df_l):
        resample_dir = os.path.join(sample_dir, f"resample_{idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        for col in resampled_df.columns:
            col_path = os.path.join(resample_dir, f"col_{col}.txt")
            resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")

    # === 4. Execução do DAMICORE para cada amostra ===
    print("Executando análise DAMICORE...")
    DAMICORE_CLI_PATH = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py"
    results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
    os.makedirs(results_dir, exist_ok=True)
    
    for m in os.listdir(sample_dir):
        resampleddatasource = os.path.join(sample_dir, m)
        if not os.path.isdir(resampleddatasource):
            continue
        tree_output = os.path.join(results_dir, f"{m}-tree.newick")
        argv = [
            "python", DAMICORE_CLI_PATH,
            "--compressor", "gzip",
            "--tree-output", tree_output,
            resampleddatasource
        ]
        print(f"Executando DAMICORE: {argv}")
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            print(f"Erro ao executar DAMICORE para {resampleddatasource} (código {process.returncode})")

    # === 5. Coleta dos arquivos newick ===
    plain_newicks = []
    for tf in os.listdir(results_dir):
        if tf.endswith("-tree.newick"):
            tf_path = os.path.join(results_dir, tf)
            with open(tf_path, "r") as f:
                plain_newicks.append(f.read())

    if not plain_newicks:
        print("Nenhum arquivo .newick encontrado.")
        return
    else:
        print(f"Total de arquivos newick coletados: {len(plain_newicks)}")

    string_newicks = "\n".join(plain_newicks)

    # === 6. Visualização: Cloud Tree e Consenso ===
    print("Gerando visualizações...")
    if string_newicks.strip():
        # Cloud Tree com nomes originais
        mtree = toytree.mtree(string_newicks)
        
        cloud_new_list = []
        for i in mtree.get_tip_labels():
            j = i.strip("''")
            num = j.split('col_')[1].split('.txt')[0]
            cloud_new_list.append(num)
        
        cloud_tip_labels = []
        for m in cloud_new_list:
            n = index_to_name[m]
            cloud_tip_labels.append(n)
        
        canvas_tuple = mtree.draw_cloud_tree(
            tip_labels=cloud_tip_labels,
            node_labels=False,
            use_edge_lengths=False,
            node_sizes=16
        )
        canvas = canvas_tuple[0]
        toyplot.pdf.render(canvas, os.path.join(DAMICORE_DIR, "cloud_tree.pdf"))
        print(f"Cloud tree salva em {os.path.join(DAMICORE_DIR, 'cloud_tree.pdf')}")

        # Consensus Tree
        ctre = mtree.get_consensus_tree()
        
        new_list = []
        for i in ctre.get_tip_labels():
            j = i.strip("''")
            num = j.split('col_')[1].split('.txt')[0]
            new_list.append(num)
        
        new_tip_labels = []
        for m in new_list:
            n = index_to_name[m]
            new_tip_labels.append(n)
        
        for node in ctre.treenode.traverse():
            node.support = node.support
        
        canvas_tuple = ctre.draw(
            tip_labels=new_tip_labels,
            node_labels='support',
            use_edge_lengths=False,
            node_sizes=32
        )
        consensus_canvas = canvas_tuple[0]
        toyplot.pdf.render(consensus_canvas, os.path.join(DAMICORE_DIR, "consensus_tree.pdf"))
        print(f"Consensus tree salva em {os.path.join(DAMICORE_DIR, 'consensus_tree.pdf')}")

    # Visualização com Biopython
    if plain_newicks:
        temp_newick_path = os.path.join(DAMICORE_DIR, 'temp_tree.newick')
        with open(temp_newick_path, 'w') as f:
            f.write(plain_newicks[0])
        
        tree = Phylo.read(temp_newick_path, 'newick')
        
        for leaf in tree.get_terminals():
            if leaf.name and 'col_' in leaf.name:
                num = leaf.name.split('col_')[1].split('.txt')[0]
                if num in index_to_name:
                    leaf.name = index_to_name[num]
        
        fig = plt.figure(figsize=(12, 8))
        axes = fig.add_subplot(1, 1, 1)
        Phylo.draw(tree, axes=axes, show_confidence=True)
        plt.title('Árvore Filogenética (Biopython)')
        plt.savefig(os.path.join(DAMICORE_DIR, 'tree_biopython.png'), dpi=300, bbox_inches='tight')
        plt.close()

        if os.path.exists(temp_newick_path):
            os.remove(temp_newick_path)

    print("Análise DAMICORE concluída com sucesso!")
    return original_df

def run_pareto_analysis(df, output_dir):
    """Executa a análise de Fronteira de Pareto no DataFrame."""
    print("\n=== Iniciando Análise de Fronteira de Pareto ===")
    
    # Criar diretório para resultados do Pareto
    pareto_dir = os.path.join(output_dir, "pareto_analysis")
    os.makedirs(pareto_dir, exist_ok=True)

    # Lista todas as possíveis variáveis (colunas) do arquivo
    all_columns = list(df.columns)
    print("\nVariáveis disponíveis para filtragem:")
    print(", ".join(all_columns))

    # Solicita as variáveis de interesse ao usuário
    variables_input = input("Digite as variáveis a serem filtradas (separadas por vírgula): ").strip()
    variables = [v.strip() for v in variables_input.split(",") if v.strip()]

    # Função vetorizada de ordenação não-dominada
    def non_dominated_sort_fast(objs):
        n, m = objs.shape
        le_matrix = np.all(objs[:, None, :] <= objs[None, :, :], axis=2)
        lt_matrix = np.any(objs[:, None, :] < objs[None, :, :], axis=2)
        dominates = le_matrix & lt_matrix
        dominated_count = np.sum(dominates, axis=0)
        current_front = np.where(dominated_count == 0)[0].tolist()
        rank = np.zeros(n, dtype=int)
        i = 1
        while current_front:
            for p in current_front:
                rank[p] = i
                for q in np.where(dominates[p])[0]:
                    dominated_count[q] -= 1
            next_front = [q for p in current_front for q in np.where(dominates[p])[0] if dominated_count[q] == 0]
            i += 1
            current_front = list(set(next_front))
        return rank

    # Função para extrair valor numérico/mode de célula
    def extract_value(cell):
        try:
            val = ast.literal_eval(str(cell))
        except Exception:
            return pd.NA
        if isinstance(val, (set, list, tuple)):
            vals = list(val)
        else:
            vals = [val]
        vals = [v for v in vals if v not in ('', None)]
        if not vals:
            return pd.NA
        if len(vals) > 1:
            chosen = multimode(vals)[0]
        else:
            chosen = vals[0]
        try:
            return int(chosen)
        except:
            try:
                return float(chosen)
            except:
                return chosen

    print("Processando dados para análise de Pareto...")
    
    # Aplica transformação nas colunas desejadas
    df_pareto = df.copy()
    for col in ['join_CENSITARIO'] + variables:
        df_pareto[col] = df_pareto[col].astype(str).apply(extract_value)

    # Remove linhas com valores vazios nas colunas de interesse
    df_pareto = df_pareto.dropna(subset=['join_CENSITARIO'] + variables, how='any')

    # Seleciona objetivos e aplica ordenação não-dominada
    objetivos = df_pareto[variables].to_numpy()
    df_pareto['pareto_frontier'] = non_dominated_sort_fast(objetivos)

    # Garante unicidade de join_CENSITARIO e melhor rank
    df_out = df_pareto.loc[df_pareto.groupby('join_CENSITARIO')['pareto_frontier'].idxmin()]
    df_out = df_out[['join_CENSITARIO'] + variables + ['pareto_frontier']]

    # Salva o resultado
    output_filename = f"pareto_filtered_{'_'.join(variables).lower()}.csv"
    output_path = os.path.join(pareto_dir, output_filename)
    df_out.to_csv(output_path, index=False)
    
    print(f"Análise de Pareto concluída. Resultados salvos em: {output_path}")
    print("\nPrimeiras linhas do resultado:")
    print(df_out.head())

def main():
    print("=== DAMICORE + Análise de Pareto ===")
    
    # Solicita o caminho do arquivo de entrada
    input_path = input("Digite o caminho do arquivo CSV de entrada: ").strip()
    
    # Verifica se o arquivo existe
    if not os.path.exists(input_path):
        print(f"Erro: O arquivo {input_path} não existe.")
        return
    
    # Cria diretório base para resultados
    output_base = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.join(os.path.dirname(input_path), output_base)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Executa análise DAMICORE
        df = run_damicore_analysis(input_path)
        
        # Pergunta se deseja continuar com a análise de Pareto
        continue_pareto = input("\nDeseja realizar a análise de Fronteira de Pareto? (s/n): ").strip().lower()
        if continue_pareto == 's':
            run_pareto_analysis(df, output_dir)
        
        print("\nTodas as análises foram concluídas com sucesso!")
        print(f"Os resultados foram salvos em: {output_dir}")
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
        raise

if __name__ == "__main__":
    main()
