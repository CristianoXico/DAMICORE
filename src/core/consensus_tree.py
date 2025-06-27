import numpy as np
from scipy.cluster import hierarchy

class ConsensusTreeBuilder:
    def __init__(self):
        self.tree = None
        self.support_values = None

    def build_tree(self, matrix, labels):
        """Constrói árvore de consenso a partir da matriz de distância"""
        # Using scipy's hierarchical clustering instead of toytree
        self.tree = hierarchy.linkage(matrix, method='average')
        return self.tree

    def get_ascii_tree(self):
        """Retorna representação ASCII da árvore"""
        if self.tree is None:
            return "Tree not built yet"
            
        # Create ASCII representation using scipy's dendrogram
        return hierarchy.dendrogram(self.tree, labels=self.labels, no_plot=True)