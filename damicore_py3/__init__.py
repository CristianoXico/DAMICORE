"""
Pacote DAMICORE adaptado para Python 3.

Este pacote contém a implementação do DAMICORE (Data Analysis and Mining of Complex 
Data Using Compression-Based Methods) atualizado para funcionar com Python 3.

Módulos:
    - ncd: Implementa o cálculo de distância de compressão normalizada (NCD)
    - tree: Implementa estruturas de árvore para análise filogenética
    - tree_simplification: Algoritmos para simplificação de árvores
    - progress_bar: Utilitário para exibição de barras de progresso
"""

__version__ = "0.1.0"

# Importa as funções principais para o namespace do pacote
from .ncd import distance_matrix, to_matrix, phylip_format, csv_format
from .tree import Node, Leaf, Edge, Tree

# Símbolos que serão importados com 'from damicore_py3 import *'
__all__ = [
    'distance_matrix', 'to_matrix', 'phylip_format', 'csv_format',
    'Node', 'Leaf', 'Edge', 'Tree'
]
