import pandas as pd
import damicore
from scipy.cluster.hierarchy import linkage, dendrogram
import numpy as np

def damicore_distance_matrix(df):
    """
    Gera a matriz de distância de consenso usando DAMICORE.
    Retorna a matriz de distância (numpy array) e os nomes das variáveis.
    """
    # DAMICORE espera dados no formato (samples, features)
    # Aqui consideramos as colunas como variáveis (features)
    # Transpor para (features, samples) para matriz de distância entre variáveis
    data = df.values.T
    # Executa DAMICORE
    consensus = damicore.Consensus()
    consensus.fit(data)
    dist_matrix = consensus.get_distance_matrix()
    return dist_matrix, list(df.columns)


def print_ascii_dendrogram(dist_matrix, labels):
    """
    Exibe um dendrograma ASCII das variáveis usando a matriz de distância.
    """
    # linkage espera condensed distance matrix
    from scipy.spatial.distance import squareform
    Z = linkage(squareform(dist_matrix), method='average')
    # Use scipy's dendrogram to get the tree structure
    ddata = dendrogram(Z, labels=labels, no_plot=True)
    # Build ASCII tree from ddata['ivl'] (leaves order)
    # For now, print the order as a flat list (improve to true ASCII tree later)
    print('Dendrogram order (leaf labels):')
    for idx, label in enumerate(ddata['ivl']):
        print(f"{idx}: {label}")

if __name__ == '__main__':
    # Exemplo de uso
    df = pd.read_csv('your_data.csv')
    dist_matrix, labels = damicore_distance_matrix(df)
    print_ascii_dendrogram(dist_matrix, labels)
