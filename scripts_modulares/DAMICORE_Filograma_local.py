import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from distutils.dir_util import mkpath

# Import DAMICORE and phylogenetic libraries
try:
    import damicore  # Importação apenas para garantir dependência, execução será via subprocess
except ImportError:
    print("ERRO: O pacote damicore não está instalado ou não está acessível.")
    exit(1)

import toytree
import toyplot
from ete3 import Tree
from Bio import Phylo

# 1. Caminho do arquivo de dados
data_path = r"C:\Users\55179\Desktop\Workspace_vscode\Analise_Dados\PPPP-Arbovirose\entrega\group_by_censitario_quarter.csv"  # ajuste conforme necessário

# 2. Carregamento dos dados
df = pd.read_csv(data_path, encoding="utf-8", low_memory=False)
print(f"Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas.")

# 3. Renomear colunas para índices numéricos e criar dicionário de rótulos
new_col_labels = [str(i) for i in range(len(df.columns))]
col_rename_dict = {i: j for i, j in zip(df.columns, new_col_labels)}
Dict_columns = {i: col for i, col in enumerate(df.columns)}
df.rename(columns=col_rename_dict, inplace=True)

# 4. Salvar cada coluna do DataFrame como um arquivo separado (ASCII)
results_dir = "./damicore_results"
mkpath(results_dir)
sample_dir = os.path.join(results_dir, "sample_full")
mkpath(sample_dir)

# Limpar caracteres especiais (ASCII)
df = df.applymap(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

# Salvar o DataFrame inteiro como CSV (igual ao Colab)
df.to_csv(os.path.join(sample_dir, "data.csv"), index=False, encoding="utf-8")

# 5. Executar DAMICORE via subprocess
import sys
import os
import subprocess

# Caminho do damicore.py no ambiente virtual
damicore_path = os.path.join(
    os.path.dirname(sys.executable),
    "..", "Lib", "site-packages", "damicore", "damicore.py"
)
damicore_path = os.path.abspath(damicore_path)

cmd = [
    sys.executable, damicore_path,
    "--normalize-weights",
    "--compressor", "zlib",
    "--serial",
    "--results-dir", results_dir,
    sample_dir
]
print("Executando DAMICORE para o DataFrame completo via subprocess...")
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
print(f"Resultados DAMICORE salvos em {results_dir}")

# 6. Coletar arquivos newick
plain_newicks = []
for root, dirs, files in os.walk(results_dir):
    for file in files:
        if file.endswith(".newick"):
            with open(os.path.join(root, file), "r") as f:
                plain_newicks.append(f.read())

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
consensus_canvas = ctre.draw(node_labels="support", use_edge_lengths=False, node_sizes=16)
consensus_tree_path = os.path.join(script_dir, "consensus_tree.png")
consensus_canvas.canvas.savefig(consensus_tree_path)
print(f"Consensus tree salva em {consensus_tree_path}")

# 8. Visualização com Biopython
from io import StringIO
trees = list(Phylo.parse(StringIO(string_newicks), "newick"))
fig = plt.figure(figsize=(10, 8))
Phylo.draw(trees[0], do_show=False, axes=fig.gca())
biopython_tree_path = os.path.join(script_dir, "biopython_tree.png")
plt.savefig(biopython_tree_path)
plt.close()
print(f"Árvore Biopython salva em {biopython_tree_path}")

# 9. Visualização com ete3
t_ete3 = Tree(plain_newicks[0])
ete3_tree_path = os.path.join(script_dir, "ete3_tree.png")
try:
    t_ete3.render(ete3_tree_path)
    print(f"Árvore ETE3 salva em {ete3_tree_path}")
except Exception as e:
    print(f"Não foi possível salvar a árvore ETE3: {e}")

# 10. Matriz cophenética usando ete3
mTree = [Tree(ctre.newick)]
evtime_m, labels = mTree[0].cophenetic_matrix()
evtime_dist = dict(zip(labels, evtime_m))
evtime_matrix = np.array(list(evtime_dist.values()))
evtime_matrix_norm = evtime_matrix / evtime_matrix.max()
cophenetic_matrix_path = os.path.join(script_dir, "cophenetic_matrix_norm.csv")
np.savetxt(cophenetic_matrix_path, evtime_matrix_norm, delimiter=",")
print(f"Matriz cophenética normalizada salva em {cophenetic_matrix_path}")

# 11. Visualização da matriz cophenética
plt.figure(figsize=(10, 8))
plt.imshow(evtime_matrix_norm, cmap="viridis")
plt.title("Matriz Cophenética Normalizada")
plt.colorbar()
cophenetic_img_path = os.path.join(script_dir, "cophenetic_matrix_norm.png")
plt.savefig(cophenetic_img_path)
plt.close()
print(f"Imagem da matriz cophenética salva em {cophenetic_img_path}")

# 12. Exportar clusters (opcional, se módulos estiverem disponíveis)
try:
    import clustering
    from tree import to_graph
    import tree_simplification as nj

    tree = nj.neighbor_joining(evtime_matrix, ids=labels)
    g = to_graph(tree)
    membership, clustering_result, dendrogram = clustering.tree_clustering(
        g, labels, community_detection_name='fast', is_normalize_weights=True
    )

    # Exportar clusters
    import csv
    membership_path = os.path.join(script_dir, "membership.csv")
    with open(membership_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Label", "Cluster"])
        for label, cluster in membership.items():
            writer.writerow([label, cluster])
    print(f"Clusters salvos em {membership_path}")
except Exception as e:
    print(f"Clusterização não executada: {e}")

print("Processamento finalizado.")