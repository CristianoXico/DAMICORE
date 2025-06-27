import os
import pandas as pd
import numpy as np
# Configurar backend não-interativo do matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import toytree
import toyplot
import toyplot.pdf
from Bio import Phylo
from io import StringIO

# === CONFIGURAÇÃO ===
DATA_PATH = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/test_data/sample_dengue.csv"  # Altere conforme necessário
SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(DATA_PATH))[0]
OUTPUT_DIR = os.path.join(os.path.dirname(DATA_PATH), SCRIPTS_OUTPUT_BASE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 1. Carregamento e pré-processamento ===
# Ler o DataFrame original para preservar os nomes das colunas
original_df = pd.read_csv(DATA_PATH, encoding="utf-8", low_memory=False)
original_columns = original_df.columns.tolist()

# Criar dicionários para mapeamento bidirecional entre índices e nomes originais
index_to_name = {str(i): name for i, name in enumerate(original_columns)}
name_to_index = {name: str(i) for i, name in enumerate(original_columns)}

# Criar DataFrame de trabalho com índices como nomes das colunas
df = original_df.copy()
df.columns = [str(i) for i in range(len(df.columns))]
df = df.applymap(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

# === 2. Reamostragem bootstrap ===
resampled_df_l = [df]
for i in range(22):
    resampled_df_l.append(df.sample(n=df.shape[0], replace=True, random_state=i))

# === 3. Salvamento das amostras ===
sample_dir = os.path.join(OUTPUT_DIR, "sample_full")
os.makedirs(sample_dir, exist_ok=True)
for idx, resampled_df in enumerate(resampled_df_l):
    resample_dir = os.path.join(sample_dir, f"resample_{idx:02d}")
    os.makedirs(resample_dir, exist_ok=True)
    for col in resampled_df.columns:
        col_path = os.path.join(resample_dir, f"col_{col}.txt")
        resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")

# === 4. Execução do DAMICORE para cada amostra ===
DAMICORE_CLI_PATH = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py"
results_dir = os.path.join(OUTPUT_DIR, "damicore_results")
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
    exit()
else:
    print(f"Total de arquivos newick coletados: {len(plain_newicks)}")

string_newicks = "\n".join(plain_newicks)

# === 6. Visualização: Cloud Tree e Consenso ===
if string_newicks.strip():
    # Cloud Tree com nomes originais
    mtree = toytree.mtree(string_newicks)
    
    # Processar os labels para Cloud Tree
    cloud_new_list = []
    for i in mtree.get_tip_labels():
        j = i.strip("''")  # Remove aspas
        # Extrair apenas o número do nome do arquivo (entre 'col_' e '.txt')
        num = j.split('col_')[1].split('.txt')[0]
        cloud_new_list.append(num)
    
    # Converter índices para nomes originais
    cloud_tip_labels = []
    for m in cloud_new_list:
        n = index_to_name[m]  # Usar o dicionário index_to_name em vez de Dict_columns
        cloud_tip_labels.append(n)
    
    # Desenhar Cloud Tree de forma simplificada
    canvas_tuple = mtree.draw_cloud_tree(
        tip_labels=cloud_tip_labels,
        node_labels=False,
        use_edge_lengths=False,
        node_sizes=16
    )
    canvas = canvas_tuple[0]
    toyplot.pdf.render(canvas, os.path.join(OUTPUT_DIR, "cloud_tree.pdf"))
    print(f"Cloud tree salva em {os.path.join(OUTPUT_DIR, 'cloud_tree.pdf')}")

    # Consensus Tree
    ctre = mtree.get_consensus_tree()
    
    # Processar os labels para Consensus Tree
    new_list = []
    for i in ctre.get_tip_labels():
        j = i.strip("''")  # Remove aspas
        # Extrair apenas o número do nome do arquivo (entre 'col_' e '.txt')
        num = j.split('col_')[1].split('.txt')[0]
        new_list.append(num)
    
    # Converter índices para nomes originais
    new_tip_labels = []
    for m in new_list:
        n = index_to_name[m]  # Usar o dicionário index_to_name em vez de Dict_columns
        new_tip_labels.append(n)
    
    # Garantir que os valores de suporte estejam acessíveis
    for node in ctre.treenode.traverse():
        node.support = node.support
    
    # Desenhar a árvore de consenso de forma simplificada
    canvas_tuple = ctre.draw(
        tip_labels=new_tip_labels,
        node_labels='support',
        use_edge_lengths=False,
        node_sizes=32
    )
    consensus_canvas = canvas_tuple[0]
    toyplot.pdf.render(consensus_canvas, os.path.join(OUTPUT_DIR, "consensus_tree.pdf"))
    print(f"Consensus tree salva em {os.path.join(OUTPUT_DIR, 'consensus_tree.pdf')}")
else:
    print("Nenhum dado newick disponível para visualização das árvores.")

# === 5. Visualização com Biopython ===
# Usar o primeiro arquivo newick da lista para visualização
if plain_newicks:
    # Criar um arquivo temporário com o primeiro newick
    temp_newick_path = os.path.join(OUTPUT_DIR, 'temp_tree.newick')
    with open(temp_newick_path, 'w') as f:
        f.write(plain_newicks[0])
    
    # Ler e processar a árvore
    tree = Phylo.read(temp_newick_path, 'newick')
    
    # Substituir os nós folha pelos nomes originais
    for leaf in tree.get_terminals():
        # Extrair apenas o número do nome do arquivo
        if leaf.name and 'col_' in leaf.name:
            num = leaf.name.split('col_')[1].split('.txt')[0]
            if num in index_to_name:
                leaf.name = index_to_name[num]
    
    # Configurar a figura
    fig = plt.figure(figsize=(12, 8))
    axes = fig.add_subplot(1, 1, 1)

# Desenhar a árvore com nomes originais
Phylo.draw(tree, axes=axes, show_confidence=True)
plt.title('Árvore Filogenética (Biopython)')
plt.savefig(os.path.join(OUTPUT_DIR, 'tree_biopython.png'), dpi=300, bbox_inches='tight')
plt.close()

# === 8. Análise de distâncias cophenéticas (placeholder) ===
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
# Criar lista de nomes originais para os eixos do heatmap
variable_names = [f"Árvore {i+1}" for i in range(n_trees)]
sns.heatmap(cophenetic_matrix, cmap="viridis", 
            xticklabels=variable_names, 
            yticklabels=variable_names)
plt.title("Matriz de Distâncias Cophenéticas entre Árvores")
plt.xlabel("Árvore")
plt.ylabel("Árvore")
plt.tight_layout()  # Ajustar layout para acomodar labels
plt.savefig(os.path.join(OUTPUT_DIR, "cophenetic_matrix.png"))
plt.close()
print(f"Matriz de distâncias cophenéticas salva em {os.path.join(OUTPUT_DIR, 'cophenetic_matrix.png')}")

# === 9. Clusterização ===
from sklearn.cluster import AgglomerativeClustering
n_clusters = 3
clustering = AgglomerativeClustering(n_clusters=n_clusters, metric='precomputed', linkage='average')
labels = clustering.fit_predict(cophenetic_matrix)
plt.figure(figsize=(8,4))
plt.hist(labels, bins=n_clusters)
plt.title("Distribuição dos Clusters das Árvores")
plt.xlabel("Cluster")
plt.ylabel("Número de Árvores")
plt.savefig(os.path.join(OUTPUT_DIR, "tree_clusters_hist.png"))
plt.close()
print(f"Histograma de clusters salvo em {os.path.join(OUTPUT_DIR, 'tree_clusters_hist.png')}")

# === 10. Exportação de resultados ===
np.save(os.path.join(OUTPUT_DIR, "cophenetic_matrix.npy"), cophenetic_matrix)
np.save(os.path.join(OUTPUT_DIR, "tree_clusters.npy"), labels)
print(f"Resultados exportados para: {OUTPUT_DIR}")

# === 6. Visualização do Heatmap ===
plt.figure(figsize=(12, 10))
sns.heatmap(
    cophenetic_matrix,
    annot=True,
    cmap='YlOrRd',
    xticklabels=[index_to_name[str(i)] for i in range(len(cophenetic_matrix))],
    yticklabels=[index_to_name[str(i)] for i in range(len(cophenetic_matrix))],
    fmt='.2f'
)
plt.title('Matriz de Distâncias Cophenéticas')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'heatmap_distances.png'), dpi=300, bbox_inches='tight')
plt.close()

# Limpeza do arquivo temporário
if os.path.exists(temp_newick_path):
    os.remove(temp_newick_path)
