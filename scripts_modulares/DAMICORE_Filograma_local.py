import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from distutils.dir_util import mkpath

# Importação do DAMICORE como módulo
try:
    import damicore as dm
except ImportError:
    print("ERRO: O pacote damicore não está instalado ou não está acessível.")
    exit(1)

import toytree

# 1. Caminho do arquivo de dados
data_path = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/test_data/group_by_quarteirao_quarter.csv"

# 2. Carregamento dos dados
df = pd.read_csv(data_path, encoding="utf-8", low_memory=False)
print(f"Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas.")

# 3. Renomear colunas para índices numéricos e criar dicionário de rótulos
new_col_labels = [str(i) for i in range(len(df.columns))]
col_rename_dict = {i: j for i, j in zip(df.columns, new_col_labels)}
Dict_columns = {i: col for i, col in enumerate(df.columns)}
df.rename(columns=col_rename_dict, inplace=True)

# 4. Criar diretórios para resultados e amostras
results_dir = "./damicore_results"
mkpath(results_dir)
sample_dir = os.path.join(results_dir, "sample_full")
mkpath(sample_dir)

# Limpar caracteres especiais (ASCII)
df = df.applymap(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

# 2.1. Reamostragem estatística 23x (bootstrap)
resampled_df_l = [df]  # 0 - original
for i in range(22):
    resampled_df_l.append(df.sample(n=df.shape[0], replace=True))

# 2.2. Salvar cada coluna de cada reamostragem como arquivos de texto separados
for idx, resampled_df in enumerate(resampled_df_l):
    resample_dir = os.path.join(sample_dir, f"resample_{idx:02d}")
    mkpath(resample_dir)
    for col in resampled_df.columns:
        col_path = os.path.join(resample_dir, f"col_{col}.txt")
        # Salva cada coluna como arquivo texto (um valor por linha)
        resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")

# 5. Executar DAMICORE para cada amostra (subpasta)
import sys
import subprocess

resampledsource = sample_dir
results = results_dir

damicore_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../damicore_py3/damicore.py"))

for m in os.listdir(resampledsource):
    resampleddatasource = os.path.join(resampledsource, m)
    if not os.path.isdir(resampleddatasource):
        continue
    argv = [sys.executable, damicore_script, "--normalize-weights", "--compressor", "gzip", "--results-dir", results, resampleddatasource]
    print(f"Executando DAMICORE: {argv}")
    try:
        subprocess.run(argv, check=True)
    except Exception as e:
        print(f"Erro ao rodar DAMICORE para {resampleddatasource}: {e}")

# 6. Coletar arquivos newick (como no Colab)
plain_newicks = []
for tf in os.listdir(results):
    tf_path = tf + '/001-tree.newick'
    full_path = os.path.join(results, tf_path)
    if os.path.isfile(full_path):
        with open(full_path, "r+") as f:
            plain_newicks += [f.read()]

if not plain_newicks:
    print("Nenhum arquivo .newick encontrado.")
    exit(1)

string_newicks = "\n".join(plain_newicks)

# 7. Visualização com toytree (cloud tree e consenso)
mtree = toytree.mtree(string_newicks)
canvas, axes, mark = mtree.draw_cloud_tree(width=800, height=600)
script_dir = os.path.dirname(os.path.abspath(__file__))
cloud_tree_path = os.path.join(script_dir, "cloud_tree.png")
canvas.canvas.savefig(cloud_tree_path)
print(f"Cloud tree salva em {cloud_tree_path}")

ctre = mtree.get_consensus_tree()
consensus_canvas = ctre.draw(node_labels="support", node_sizes=32, use_edge_lengths=False)
consensus_tree_path = os.path.join(script_dir, "consensus_tree.png")
consensus_canvas.canvas.savefig(consensus_tree_path)
print(f"Consensus tree salva em {consensus_tree_path}")

# 8. Análise de Distâncias Topológicas/Cophenéticas
# Placeholder: matriz de distâncias fake (substitua por função real se desejar)
def fake_tree_distance(tree1, tree2):
    return np.random.rand()

n_trees = len(plain_newicks)
cophenetic_matrix = np.zeros((n_trees, n_trees))
for i in range(n_trees):
    for j in range(i+1, n_trees):
        d = fake_tree_distance(plain_newicks[i], plain_newicks[j])
        cophenetic_matrix[i, j] = cophenetic_matrix[j, i] = d

plt.figure(figsize=(8,6))
import seaborn as sns
sns.heatmap(cophenetic_matrix, cmap="viridis")
plt.title("Matriz de Distâncias Cophenéticas entre Árvores")
plt.xlabel("Árvore")
plt.ylabel("Árvore")
plt.savefig(os.path.join(results_dir, "cophenetic_matrix_heatmap.png"))
plt.close()

# 9. Clusterização das árvores
from sklearn.cluster import AgglomerativeClustering
n_clusters = 3  # Ajuste conforme necessário
clustering = AgglomerativeClustering(n_clusters=n_clusters, affinity='precomputed', linkage='average')
labels = clustering.fit_predict(cophenetic_matrix)

plt.figure(figsize=(8,4))
plt.hist(labels, bins=n_clusters)
plt.title("Distribuição dos Clusters das Árvores")
plt.xlabel("Cluster")
plt.ylabel("Número de Árvores")
plt.savefig(os.path.join(results_dir, "tree_clusters_hist.png"))
plt.close()

# 10. Exportação dos resultados
np.save(os.path.join(results_dir, "cophenetic_matrix.npy"), cophenetic_matrix)
np.save(os.path.join(results_dir, "tree_clusters.npy"), labels)
print("Resultados exportados para:", results_dir)
print("Processamento finalizado.")