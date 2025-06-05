import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

def plot_ncd_tree(ncd_mat, labels, n_clusters=2):
    # linkage espera uma matriz de distâncias condensada
    from scipy.spatial.distance import squareform
    dist_vec = squareform(ncd_mat, checks=False)
    Z = linkage(dist_vec, method='average')
    plt.figure(figsize=(12, 6))
    dendro = dendrogram(Z, labels=labels, color_threshold=None)
    plt.title(f'Árvore de Consenso (NCD) - {n_clusters} categorias')
    plt.xlabel('Variáveis')
    plt.ylabel('Distância NCD')
    # Destacar clusters
    clusters = fcluster(Z, n_clusters, criterion='maxclust')
    for i, label in enumerate(labels):
        plt.text(i, 0, f'C{clusters[i]}', ha='center', va='bottom', fontsize=9, color='red')
    plt.tight_layout()
    plt.show()
