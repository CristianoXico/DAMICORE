import networkx as nx
import community
import numpy as np
from typing import Dict, Any, List
from tqdm import tqdm

class NewmanCommunityDetector:
    def __init__(self):
        """Initialize detector with empty graph and communities"""
        self.graph = None
        self.communities = None
        self.metrics = {}

    def detect_communities(self, distance_matrix: np.ndarray) -> Dict[int, List[int]]:
        """
        Detecta comunidades usando o algoritmo de Newman-Girvan
        
        Args:
            distance_matrix: Matriz de similaridade NxN
            
        Returns:
            dict: Mapeamento de nós para comunidades
        """
        # Criar grafo a partir da matriz de distância
        self.graph = nx.Graph()
        n = len(distance_matrix)
        
        # Converter distâncias para similaridades
        print("Construindo grafo...")
        for i in tqdm(range(n)):
            for j in range(i+1, n):
                if distance_matrix[i,j] > 0:
                    # Converter distância para similaridade
                    similarity = 1 - distance_matrix[i,j]
                    self.graph.add_edge(i, j, weight=similarity)
        
        print("Detectando comunidades...")
        self.communities = community.best_partition(self.graph)
        
        # Calcular métricas
        print("Calculando métricas...")
        self._calculate_metrics()
        
        return self.communities

    def _calculate_metrics(self):
        """Calculate community detection metrics"""
        if not self.graph or not self.communities:
            return
            
        # Group nodes by community
        comm_groups = {}
        for node, comm_id in self.communities.items():
            if comm_id not in comm_groups:
                comm_groups[comm_id] = []
            comm_groups[comm_id].append(node)
            
        self.metrics = {
            'n_communities': len(comm_groups),
            'modularity': community.modularity(self.communities, self.graph),
            'avg_clustering': nx.average_clustering(self.graph),
            'density': nx.density(self.graph)
        }

    def get_metrics(self) -> Dict[str, float]:
        """Returns community detection metrics"""
        return {
            k: round(v, 4) if isinstance(v, float) else v 
            for k, v in self.metrics.items()
        }