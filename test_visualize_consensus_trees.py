# -*- coding: utf-8 -*-
"""Testes para a função visualize_consensus_trees.

Este módulo contém testes para validar o funcionamento da função
visualize_consensus_trees, incluindo a geração de múltiplas árvores,
validação de entrada e tratamento de erros.
"""

import os
import sys
import unittest
import numpy as np
import tempfile
import shutil
from typing import List, Dict, Any, Optional

# Adiciona o diretório raiz ao path para importar o módulo principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa a função a ser testada
try:
    from pipeline_novo import visualize_consensus_trees
except ImportError as e:
    print("[ERRO] Falha ao importar visualize_consensus_trees: {}".format(str(e)))
    raise

try:
    from validacao_matriz import validar_matriz_distancia, processar_matriz_distancia
except ImportError as e:
    print("[ERRO] Falha ao importar funções de validação de matriz: {}".format(str(e)))
    raise


class TestVisualizeConsensusTrees(unittest.TestCase):
    """Classe de testes para a função visualize_consensus_trees."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        # Cria um diretório temporário para os arquivos de saída
        import tempfile
        cls.temp_dir = tempfile.mkdtemp(prefix='test_consensus_trees_')
        print("\nDiretório temporário para testes: {}".format(cls.temp_dir))
        
        # Configuração de logging
        import logging
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
    
    def test_valid_input(self):
        """Testa a função com uma entrada válida."""
        print("\n🔍 Testando com entrada válida...")
        
        # Cria uma matriz de distância válida
        n = 5
        np.random.seed(42)
        X = np.random.rand(n, 3)  # 5 pontos em 3D
        dist_matrix = np.zeros((n, n))
        
        # Preenche a matriz de distância (incluindo diagonal zero)
        for i in range(n):
            for j in range(i+1, n):
                dist = np.linalg.norm(X[i] - X[j])
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist
        
        # Rótulos para as amostras
        labels = ['Amostra_{}'.format(i+1) for i in range(n)]
        
        # Chama a função com um número reduzido de árvores para teste rápido
        result = visualize_consensus_trees(
            dist_matrix, 
            labels, 
            max_trees=3  # Número reduzido para teste rápido
        )
        
        # Verifica se o resultado é um dicionário
        self.assertIsInstance(result, dict)
        
        # Verifica se os arquivos foram gerados
        if 'arquivos_gerados' in result:
            for key, path in result['arquivos_gerados'].items():
                self.assertTrue(os.path.exists(path), "Arquivo {} não encontrado: {}".format(key, path))
    
    def test_invalid_matrix(self):
        """Testa a função com uma matriz de distância inválida."""
        print("\n🔍 Testando com matriz inválida...")
        
        # Matriz não quadrada
        invalid_matrix = np.random.rand(3, 4)
        labels = ['A', 'B', 'C']
        
        with self.assertRaises(ValueError):
            visualize_consensus_trees(invalid_matrix, labels)
    
    def test_single_sample(self):
        """Testa a função com apenas uma amostra."""
        print("\n🔍 Testando com uma única amostra...")
        
        # Matriz com uma única amostra
        single_matrix = np.zeros((1, 1))
        labels = ['Amostra_única']
        
        with self.assertRaises(ValueError):
            visualize_consensus_trees(single_matrix, labels)
    
    def test_duplicate_labels(self):
        """Testa a função com rótulos duplicados."""
        print("\n🔍 Testando com rótulos duplicados...")
        
        # Matriz de distância válida
        dist_matrix = np.array([
            [0.0, 0.5, 0.7],
            [0.5, 0.0, 0.3],
            [0.7, 0.3, 0.0]
        ])
        
        # Rótulos com duplicatas (não permitido)
        labels = ['A', 'A', 'B']
        
        with self.assertRaises(ValueError):
            visualize_consensus_trees(dist_matrix, labels)
    
    def test_matrix_processing(self):
        """Testa o processamento de matrizes com problemas comuns."""
        print("\n🔍 Testando processamento de matrizes...")
        
        # Cria uma matriz com problemas comuns
        n = 4
        np.random.seed(42)
        X = np.random.rand(n, 3)
        dist_matrix = np.zeros((n, n))
        
        # Preenche a matriz de distância (incluindo diagonal zero)
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist = np.linalg.norm(X[i] - X[j])
                    dist_matrix[i, j] = dist
        
        # Adiciona problemas à matriz
        dist_matrix[0, 1] = -0.1  # Valor negativo
        dist_matrix[1, 0] = -0.1  # Garante simetria
        dist_matrix[0, 2] = np.nan  # Valor NaN
        dist_matrix[2, 0] = np.nan  # Garante simetria
        
        # Rótulos para as amostras
        labels = ['Ponto_{}'.format(i+1) for i in range(n)]
        
        # Testa a validação
        is_valid, message = validar_matriz_distancia(dist_matrix)
        self.assertFalse(is_valid)
        
        # Testa o processamento
        processed_matrix, _ = processar_matriz_distancia(dist_matrix)
        is_valid, message = validar_matriz_distancia(processed_matrix)
        self.assertTrue(is_valid, "A matriz processada ainda não é válida: {}".format(message))
        
        # Verifica se a matriz processada é simétrica
        self.assertTrue(np.allclose(processed_matrix, processed_matrix.T))
        
        # Verifica se não há valores negativos
        self.assertTrue(np.all(processed_matrix >= 0))
        
        # Verifica se não há valores NaN ou infinitos
        self.assertFalse(np.any(np.isnan(processed_matrix)))
        self.assertFalse(np.any(np.isinf(processed_matrix)))


if __name__ == "__main__":
    # Executa os testes
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Mantém o diretório temporário para inspeção
    print("\nOs arquivos de teste foram salvos em: {}".format(TestVisualizeConsensusTrees.temp_dir))
    print("ATENCAO: Lembre-se de remover o diretorio apos a inspecao.")
