"""
Pacote principal do projeto DAMICORE.

Este pacote fornece ferramentas para análise de dados usando a distância de compressão normalizada (NCD).
"""

from .damicore_ncd import generate_ncd_matrix
from .ncd_matrix import ncd_matrix_from_dataframe

__all__ = ['generate_ncd_matrix', 'ncd_matrix_from_dataframe']
