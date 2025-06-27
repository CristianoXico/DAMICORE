#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para o módulo matrix_utils.py
"""

import os
import sys
import numpy as np
import tempfile
import shutil
import unittest
from matrix_utils import (
    copy_reference_matrix,
    validate_matrix,
    align_matrices,
    compare_matrices
)

class TestMatrixUtils(unittest.TestCase):
    """Testes para as funções do módulo matrix_utils."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        # Cria um diretório temporário para os testes
        cls.test_dir = tempfile.mkdtemp(prefix="test_matrix_utils_")
        
        # Cria matrizes de exemplo para os testes
        np.random.seed(42)
        
        # Matriz de referência (5x5)
        cls.ref_matrix = np.random.rand(5, 5)
        cls.ref_matrix = (cls.ref_matrix + cls.ref_matrix.T) / 2  # Torna simétrica
        np.fill_diagonal(cls.ref_matrix, 0)  # Diagonal zero
        cls.ref_labels = [f"sample_{i}" for i in range(5)]
        
        # Matriz de teste com alguns rótulos em comum (3 em comum)
        cls.test_matrix = np.random.rand(4, 4)
        cls.test_matrix = (cls.test_matrix + cls.test_matrix.T) / 2
        np.fill_diagonal(cls.test_matrix, 0)
        cls.test_labels = ["sample_1", "sample_2", "sample_3", "sample_10"]
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes."""
        # Remove o diretório temporário
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def test_copy_reference_matrix(self):
        """Testa a cópia da matriz de referência."""
        output_dir = os.path.join(self.test_dir, "test_copy")
        
        # Testa a cópia bem-sucedida
        success, message = copy_reference_matrix(
            self.ref_matrix, 
            self.ref_labels, 
            output_dir,
            reference_name="test_reference"
        )
        
        self.assertTrue(success, f"Falha ao copiar matriz de referência: {message}")
        
        # Verifica se os arquivos foram criados
        matrix_path = os.path.join(output_dir, "test_reference_matrix.npy")
        labels_path = os.path.join(output_dir, "test_reference_labels.txt")
        
        self.assertTrue(os.path.exists(matrix_path), "Arquivo da matriz não foi criado")
        self.assertTrue(os.path.exists(labels_path), "Arquivo de rótulos não foi criado")
        
        # Verifica se os dados foram salvos corretamente
        loaded_matrix = np.load(matrix_path)
        np.testing.assert_array_almost_equal(loaded_matrix, self.ref_matrix, 
                                           err_msg="Matriz carregada não é igual à original")
        
        with open(labels_path, 'r', encoding='utf-8') as f:
            loaded_labels = [line.strip() for line in f.readlines()]
            
        self.assertListEqual(loaded_labels, self.ref_labels, 
                           "Rótulos carregados não são iguais aos originais")
    
    def test_validate_matrix(self):
        """Testa a validação de matrizes."""
        # Testa matriz válida
        valid, message = validate_matrix(self.ref_matrix, "Matriz de teste")
        self.assertTrue(valid, f"Matriz válida foi rejeitada: {message}")
        
        # Testa matriz não quadrada
        invalid_matrix = np.random.rand(3, 4)
        valid, message = validate_matrix(invalid_matrix, "Matriz não quadrada")
        self.assertFalse(valid, "Matriz não quadrada foi considerada válida")
        
        # Testa matriz com diagonal não zero
        bad_diag = self.ref_matrix.copy()
        bad_diag[0, 0] = 1.0
        valid, message = validate_matrix(bad_diag, "Matriz com diagonal não zero")
        self.assertFalse(valid, "Matriz com diagonal não zero foi considerada válida")
        
        # Testa matriz não simétrica
        not_symmetric = self.ref_matrix.copy()
        not_symmetric[0, 1] += 1.0
        valid, message = validate_matrix(not_symmetric, "Matriz não simétrica")
        self.assertFalse(valid, "Matriz não simétrica foi considerada válida")
    
    def test_align_matrices(self):
        """Testa o alinhamento de matrizes com rótulos diferentes."""
        # Matrizes com alguns rótulos em comum
        m1 = np.array([
            [0, 1, 2],
            [1, 0, 3],
            [2, 3, 0]
        ])
        l1 = ["A", "B", "C"]
        
        m2 = np.array([
            [0, 4, 5],
            [4, 0, 6],
            [5, 6, 0]
        ])
        l2 = ["B", "C", "D"]
        
        # Rótulos em comum: B, C
        expected_common = ["B", "C"]
        
        # Matrizes alinhadas esperadas (apenas linhas/colunas B e C)
        expected_m1 = np.array([
            [0, 3],
            [3, 0]
        ])
        
        # Na matriz 2, o valor entre B e C é 4 (linha B, coluna C)
        # Ajustando a expectativa para refletir o valor correto
        expected_m2 = np.array([
            [0, 4],  # B
            [4, 0]   # C
        ])
        
        # Executa o alinhamento
        aligned_m1, aligned_m2, common_labels, message = align_matrices(m1, l1, m2, l2)
        
        # Verifica os resultados
        self.assertIsNotNone(aligned_m1, "Falha ao alinhar matriz 1")
        self.assertIsNotNone(aligned_m2, "Falha ao alinhar matriz 2")
        
        # Verifica os rótulos comuns
        self.assertListEqual(sorted(common_labels), sorted(expected_common),
                           "Rótulos comuns incorretos")
        
        # Verifica as matrizes alinhadas
        np.testing.assert_array_almost_equal(aligned_m1, expected_m1,
                                           err_msg="Matriz 1 alinhada incorretamente")
        np.testing.assert_array_almost_equal(aligned_m2, expected_m2,
                                           err_msg="Matriz 2 alinhada incorretamente")
    
    def test_compare_matrices(self):
        """Testa a comparação de matrizes."""
        output_dir = os.path.join(self.test_dir, "test_compare")
        os.makedirs(output_dir, exist_ok=True)
        
        # Executa a comparação
        result = compare_matrices(
            self.ref_matrix,
            self.test_matrix,
            self.ref_labels,
            self.test_labels,
            output_dir
        )
        
        # Verifica se a comparação foi bem-sucedida
        self.assertTrue(result['success'], f"Falha na comparação: {result.get('message', '')}")
        
        # Verifica as métricas de comparação
        metrics = result.get('comparison_metrics', {})
        self.assertIn('num_common_labels', metrics, "Número de rótulos comuns não encontrado")
        self.assertEqual(metrics['num_common_labels'], 3, "Número incorreto de rótulos comuns")
        
        # Verifica se os arquivos de saída foram criados
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'aligned_matrix1.csv')), 
                       "Arquivo da matriz 1 alinhada não encontrado")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'aligned_matrix2.csv')), 
                       "Arquivo da matriz 2 alinhada não encontrado")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'common_labels.txt')), 
                       "Arquivo de rótulos comuns não encontrado")
        
        # Verifica se as matrizes alinhadas têm o mesmo tamanho
        aligned_m1 = result.get('aligned_matrix1')
        aligned_m2 = result.get('aligned_matrix2')
        
        self.assertIsNotNone(aligned_m1, "Matriz 1 alinhada não retornada")
        self.assertIsNotNone(aligned_m2, "Matriz 2 alinhada não retornada")
        self.assertEqual(aligned_m1.shape, aligned_m2.shape, 
                         "Matrizes alinhadas têm tamanhos diferentes")
        self.assertEqual(aligned_m1.shape[0], metrics['num_common_labels'],
                         "Tamanho da matriz alinhada não corresponde ao número de rótulos comuns")

if __name__ == "__main__":
    unittest.main()
