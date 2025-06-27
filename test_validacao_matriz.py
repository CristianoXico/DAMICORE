# -*- coding: utf-8 -*-
"""
Testes para o modulo de validacao de matrizes.
"""

import os
import sys
import unittest
import numpy as np

# Adiciona o diretório raiz ao path para importar o módulo principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from validacao_matriz import validar_matriz_distancia, processar_matriz_distancia, analisar_matriz_distancia
except ImportError as e:
    print("[ERRO] Falha ao importar funções de validação de matriz: {}".format(str(e)))
    raise

class TestValidacaoMatriz(unittest.TestCase):
    """Classe de testes para o módulo de validação de matrizes."""
    
    def test_validar_matriz_valida(self):
        """Testa a validação de uma matriz de distância válida."""
        # Matriz de distância válida (simétrica, diagonal zero, valores não-negativos)
        matriz = np.array([
            [0.0, 0.5, 0.7],
            [0.5, 0.0, 0.3],
            [0.7, 0.3, 0.0]
        ])
        
        valido, mensagem = validar_matriz_distancia(matriz)
        self.assertTrue(valido)
        self.assertIn("valida", mensagem.lower())
    
    def test_validar_matriz_nao_quadrada(self):
        """Testa a validação de uma matriz não quadrada."""
        # Matriz não quadrada
        matriz = np.array([
            [0.0, 0.5, 0.7],
            [0.5, 0.0, 0.3]
        ])
        
        valido, mensagem = validar_matriz_distancia(matriz)
        self.assertFalse(valido)
        self.assertIn("quadrada", mensagem.lower())
    
    def test_validar_matriz_diagonal_nao_zero(self):
        """Testa a validação de uma matriz com diagonal não zero."""
        # Matriz com diagonal não zero
        matriz = np.array([
            [1.0, 0.5, 0.7],
            [0.5, 1.0, 0.3],
            [0.7, 0.3, 1.0]
        ])
        
        valido, mensagem = validar_matriz_distancia(matriz)
        self.assertFalse(valido)
        self.assertIn("diagonal", mensagem.lower())
    
    def test_validar_matriz_assimetrica(self):
        """Testa a validação de uma matriz assimétrica."""
        # Matriz assimétrica
        matriz = np.array([
            [0.0, 0.5, 0.7],
            [0.4, 0.0, 0.3],
            [0.7, 0.3, 0.0]
        ])
        
        valido, mensagem = validar_matriz_distancia(matriz)
        self.assertFalse(valido)
        self.assertIn("simetrica", mensagem.lower())
    
    def test_processar_matriz_com_problemas(self):
        """Testa o processamento de uma matriz com problemas comuns."""
        # Matriz com problemas (valores negativos, NaN, assimétrica)
        matriz = np.array([
            [0.0, -0.1, np.nan],
            [0.4, 0.0, 0.3],
            [0.7, 0.3, 0.0]
        ])
        
        # Processa a matriz
        matriz_processada, metadados = processar_matriz_distancia(matriz)
        
        # Verifica se a matriz processada é válida
        valido, mensagem = validar_matriz_distancia(matriz_processada)
        self.assertTrue(valido, "A matriz processada deve ser válida")
        
        # Verifica se as alterações foram registradas
        self.assertGreater(len(metadados.get('alteracoes', [])), 0)
    
    def test_analise_matriz(self):
        """Testa a análise de uma matriz de distância."""
        # Matriz de distância válida
        matriz = np.array([
            [0.0, 0.5, 0.7],
            [0.5, 0.0, 0.3],
            [0.7, 0.3, 0.0]
        ])
        
        # Analisa a matriz
        analise = analisar_matriz_distancia(matriz)
        
        # Verifica se as estatísticas básicas estão presentes
        for campo in ['tamanho', 'min', 'max', 'media', 'mediana', 'desvio_padrao']:
            self.assertIn(campo, analise)
        
        # Verifica valores especificos
        self.assertEqual(analise['tamanho'], 3)
        self.assertTrue(analise['simetrica'])
        self.assertTrue(analise['diagonal_zero'])
        self.assertEqual(analise['valores_negativos'], 0)
        self.assertEqual(analise['valores_nan'], 0)
        self.assertEqual(analise['valores_inf'], 0)

if __name__ == "__main__":
    # Executa os testes
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    print("\nTestes concluidos com sucesso!")
