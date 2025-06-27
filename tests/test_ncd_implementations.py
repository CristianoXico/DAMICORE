"""
Testes para as implementações de cálculo de matriz NCD.

Este módulo contém testes para validar e comparar as diferentes implementações
de cálculo de matriz NCD disponíveis no projeto.
"""

import os
import sys
import time
import tempfile
import numpy as np
import pandas as pd
import unittest
from pathlib import Path
from typing import Tuple, Dict, Any, List

# Adiciona o diretório raiz ao path para importar módulos locais
sys.path.insert(0, str(Path(__file__).parent.parent))

# Tenta importar as implementações
try:
    from ncd_matrix import ncd_matrix_from_dataframe as zlib_ncd_matrix
    ZLIB_AVAILABLE = True
except ImportError:
    ZLIB_AVAILABLE = False
    print("Aviso: Implementação zlib não encontrada")

try:
    from damicore_ncd import generate_ncd_matrix as damicore_generate_ncd_matrix
    DAMICORE_AVAILABLE = True
except ImportError:
    DAMICORE_AVAILABLE = False
    print("Aviso: Implementação DAMICORE não encontrada")

# Dados de teste para os testes
TEST_DATA_SMALL = {
    'col1': [1, 2, 3, 4, 5],
    'col2': [1.1, 2.2, 3.3, 4.4, 5.5],
    'col3': [10, 20, 30, 40, 50],
    'col4': [1.5, 2.5, 3.5, 4.5, 5.5],
}

TEST_DATA_MEDIUM = {
    f'col{i}': np.random.rand(20) * 100 for i in range(10)
}

TEST_DATA_LARGE = {
    f'col{i}': np.random.rand(100) * 1000 for i in range(50)
}

class TestNCDMatrix(unittest.TestCase):    
    """Testes para a implementação zlib da matriz NCD."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        if not ZLIB_AVAILABLE:
            raise unittest.SkipTest("Implementação zlib não disponível")
            
        cls.small_df = pd.DataFrame(TEST_DATA_SMALL)
        cls.medium_df = pd.DataFrame(TEST_DATA_MEDIUM)
        cls.large_df = pd.DataFrame(TEST_DATA_LARGE)
    
    def test_small_matrix(self):
        """Testa o cálculo da matriz NCD para um conjunto pequeno de dados."""
        matrix, labels = zlib_ncd_matrix(self.small_df)
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (4, 4))
        
        # Verifica se a diagonal principal é zero
        np.testing.assert_array_almost_equal(
            np.diag(matrix), 
            np.zeros(4),
            decimal=10,
            err_msg="A diagonal principal deve ser zero"
        )
        
        # Verifica se a matriz é simétrica
        np.testing.assert_array_almost_equal(
            matrix, 
            matrix.T,
            decimal=10,
            err_msg="A matriz deve ser simétrica"
        )
        
        # Verifica se os valores estão no intervalo [0, 1]
        self.assertTrue(
            np.all((matrix >= 0) & (matrix <= 1)),
            "Todos os valores da matriz devem estar no intervalo [0, 1]"
        )
    
    def test_medium_matrix(self):
        """Testa o cálculo da matriz NCD para um conjunto médio de dados."""
        matrix, labels = zlib_ncd_matrix(self.medium_df)
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (10, 10))
        self._validate_ncd_matrix(matrix)
    
    def test_large_matrix(self):
        """Testa o cálculo da matriz NCD para um conjunto grande de dados."""
        # Teste opcional - pode ser lento
        if '--run-slow' not in sys.argv:
            self.skipTest("Testes lentos pulados. Use --run-slow para executar.")
            
        matrix, labels = zlib_ncd_matrix(self.large_df)
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (50, 50))
        self._validate_ncd_matrix(matrix)
    
    def test_matrix_with_missing_values(self):
        """Testa o cálculo da matriz NCD com valores ausentes."""
        df = self.small_df.copy()
        df.loc[0, 'col1'] = np.nan
        df.loc[2, 'col2'] = None
        
        matrix, labels = zlib_ncd_matrix(df)
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (4, 4))
        self._validate_ncd_matrix(matrix)
    
    def test_matrix_with_different_data_types(self):
        """Testa o cálculo da matriz NCD com diferentes tipos de dados."""
        df = pd.DataFrame({
            'int': [1, 2, 3, 4],
            'float': [1.1, 2.2, 3.3, 4.4],
            'str': ['a', 'b', 'c', 'd'],
            'bool': [True, False, True, False],
            'mixed': [1, 'a', 2.5, True]
        })
        
        matrix, labels = zlib_ncd_matrix(df)
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (5, 5))
        self._validate_ncd_matrix(matrix)
    
    def _validate_ncd_matrix(self, matrix: np.ndarray):
        """Valida as propriedades básicas de uma matriz NCD."""
        n = matrix.shape[0]
        
        # Verifica se a matriz é quadrada
        self.assertEqual(matrix.shape, (n, n), "A matriz deve ser quadrada")
        
        # Verifica se a diagonal principal é zero
        np.testing.assert_array_almost_equal(
            np.diag(matrix), 
            np.zeros(n),
            decimal=10,
            err_msg="A diagonal principal deve ser zero"
        )
        
        # Verifica se a matriz é simétrica
        np.testing.assert_array_almost_equal(
            matrix, 
            matrix.T,
            decimal=10,
            err_msg="A matriz deve ser simétrica"
        )
        
        # Verifica se os valores estão no intervalo [0, 1]
        self.assertTrue(
            np.all((matrix >= 0) & (matrix <= 1)),
            "Todos os valores da matriz devem estar no intervalo [0, 1]"
        )
        
        # Verifica a desigualdade triangular (aproximadamente)
        # NCD(x,z) <= NCD(x,y) + NCD(y,z) + epsilon
        epsilon = 0.1  # Tolerância para erros de ponto flutuante
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    self.assertLessEqual(
                        matrix[i, k], 
                        matrix[i, j] + matrix[j, k] + epsilon,
                        f"Falha na desigualdade triangular para ({i},{j},{k})"
                    )


class TestDAMICORENCD(unittest.TestCase):
    """Testes para a implementação DAMICORE da matriz NCD."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        if not DAMICORE_AVAILABLE:
            raise unittest.SkipTest("Implementação DAMICORE não disponível")
            
        # Cria dataframes de teste
        cls.small_df = pd.DataFrame(TEST_DATA_SMALL)
        cls.medium_df = pd.DataFrame(TEST_DATA_MEDIUM)
        
        # Cria um diretório temporário para os testes
        cls.temp_dir = tempfile.mkdtemp(prefix="damicore_test_")
        cls.small_dir = os.path.join(cls.temp_dir, "small")
        os.makedirs(cls.small_dir, exist_ok=True)
        
        # Salva os dados em arquivos para o DAMICORE processar
        for col in cls.small_df.columns:
            cls.small_df[col].to_csv(
                os.path.join(cls.small_dir, f"{col}.txt"),
                index=False,
                header=False
            )
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes."""
        # Remove o diretório temporário
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_small_matrix(self):
        """Testa o cálculo da matriz NCD para um conjunto pequeno de dados."""
        # Gera a matriz NCD usando o DAMICORE
        matrix, labels = damicore_generate_ncd_matrix(
            input_dir=self.small_dir,
            compressor="gzip",
            max_workers=2
        )
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (4, 4))
        
        # Valida as propriedades básicas da matriz
        self._validate_ncd_matrix(matrix)
    
    def test_medium_matrix(self):
        """Testa o cálculo da matriz NCD para um conjunto médio de dados."""
        # Cria diretório para dados médios
        medium_dir = os.path.join(self.temp_dir, "medium")
        os.makedirs(medium_dir, exist_ok=True)
        
        # Salva os dados em arquivos
        for col in self.medium_df.columns:
            self.medium_df[col].to_csv(
                os.path.join(medium_dir, f"{col}.txt"),
                index=False,
                header=False
            )
        
        # Gera a matriz NCD usando o DAMICORE
        matrix, labels = damicore_generate_ncd_matrix(
            input_dir=medium_dir,
            compressor="gzip",
            max_workers=2
        )
        
        # Verifica se a matriz tem as dimensões corretas
        self.assertEqual(matrix.shape, (10, 10))
        
        # Valida as propriedades básicas da matriz
        self._validate_ncd_matrix(matrix)
    
    def _validate_ncd_matrix(self, matrix: np.ndarray):
        """Valida as propriedades básicas de uma matriz NCD."""
        n = matrix.shape[0]
        
        # Verifica se a matriz é quadrada
        self.assertEqual(matrix.shape, (n, n), "A matriz deve ser quadrada")
        
        # Verifica se a diagonal principal é zero
        np.testing.assert_array_almost_equal(
            np.diag(matrix), 
            np.zeros(n),
            decimal=10,
            err_msg="A diagonal principal deve ser zero"
        )
        
        # Verifica se a matriz é simétrica
        np.testing.assert_array_almost_equal(
            matrix, 
            matrix.T,
            decimal=10,
            err_msg="A matriz deve ser simétrica"
        )
        
        # Verifica se os valores estão no intervalo [0, 1]
        self.assertTrue(
            np.all((matrix >= 0) & (matrix <= 1)),
            "Todos os valores da matriz devem estar no intervalo [0, 1]"
        )


class TestNCDImplementationsComparison(unittest.TestCase):
    """Testes comparativos entre as implementações de NCD."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        if not ZLIB_AVAILABLE or not DAMICORE_AVAILABLE:
            raise unittest.SkipTest("Ambas as implementações (zlib e DAMICORE) são necessárias para comparação")
        
        # Cria um dataframe de teste pequeno para comparação
        cls.df = pd.DataFrame(TEST_DATA_SMALL)
        
        # Cria um diretório temporário para o DAMICORE
        cls.temp_dir = tempfile.mkdtemp(prefix="ncd_comparison_")
        cls.data_dir = os.path.join(cls.temp_dir, "data")
        os.makedirs(cls.data_dir, exist_ok=True)
        
        # Salva os dados em arquivos para o DAMICORE processar
        for col in cls.df.columns:
            cls.df[col].to_csv(
                os.path.join(cls.data_dir, f"{col}.txt"),
                index=False,
                header=False
            )
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes."""
        # Remove o diretório temporário
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_implementations_consistency(self):
        """Verifica a consistência entre as implementações zlib e DAMICORE."""
        # Calcula a matriz usando zlib
        zlib_matrix, zlib_labels = zlib_ncd_matrix(self.df)
        
        # Calcula a matriz usando DAMICORE
        damicore_matrix, damicore_labels = damicore_generate_ncd_matrix(
            input_dir=self.data_dir,
            compressor="gzip",
            max_workers=1
        )
        
        # Ordena as colunas para garantir a mesma ordem
        zlib_order = sorted(zlib_labels)
        damicore_order = sorted(damicore_labels)
        
        # Verifica se as mesmas colunas foram processadas
        self.assertEqual(
            set(zlib_order), 
            set(damicore_order),
            "As implementações processaram colunas diferentes"
        )
        
        # Reordena as matrizes para a mesma ordem de colunas
        zlib_indices = [zlib_order.index(col) for col in sorted(zlib_order)]
        damicore_indices = [damicore_order.index(col) for col in sorted(damicore_order)]
        
        zlib_matrix_ordered = zlib_matrix[zlib_indices][:, zlib_indices]
        damicore_matrix_ordered = damicore_matrix[damicore_indices][:, damicore_indices]
        
        # Calcula a diferença absoluta média entre as matrizes
        diff = np.abs(zlib_matrix_ordered - damicore_matrix_ordered)
        mean_diff = np.mean(diff)
        max_diff = np.max(diff)
        
        print(f"\nComparação entre implementações:")
        print(f"- Diferença absoluta média: {mean_diff:.6f}")
        print(f"- Diferença absoluta máxima: {max_diff:.6f}")
        
        # Verifica se as matrizes são aproximadamente iguais
        # Como as implementações são diferentes, esperamos alguma diferença
        self.assertLess(
            mean_diff, 
            0.2,  # Tolerância para diferença média
            "As implementações produziram resultados muito diferentes"
        )
        
        self.assertLess(
            max_diff, 
            0.5,  # Tolerância para diferença máxima
            "Algum par de elementos tem diferença muito grande"
        )


def run_performance_test():
    """Executa testes de desempenho para as implementações de NCD."""
    if not ZLIB_AVAILABLE or not DAMICORE_AVAILABLE:
        print("Ambas as implementações (zlib e DAMICORE) são necessárias para o teste de desempenho")
        return
    
    print("\n=== Teste de Desempenho ===")
    
    # Teste com dados pequenos
    small_df = pd.DataFrame(TEST_DATA_SMALL)
    
    # Teste com dados médios
    medium_df = pd.DataFrame(TEST_DATA_MEDIUM)
    
    # Teste com dados grandes (opcional)
    if '--run-slow' in sys.argv:
        large_df = pd.DataFrame(TEST_DATA_LARGE)
        test_cases = [
            ("Pequeno", small_df, 4, 1),
            ("Médio", medium_df, 10, 1),
            ("Grande", large_df, 50, 1),
        ]
    else:
        test_cases = [
            ("Pequeno", small_df, 4, 1),
            ("Médio", medium_df, 10, 1),
        ]
    
    print("\nTempo de execução (segundos):")
    print("-" * 80)
    print(f"{'Tamanho':<10} | {'Colunas':<8} | {'zlib':<15} | {'DAMICORE':<15} | '--run-slow' para testar com dados grandes")
    print("-" * 80)
    
    for name, df, n_cols, _ in test_cases:
        # Teste zlib
        start = time.time()
        zlib_ncd_matrix(df)
        zlib_time = time.time() - start
        
        # Prepara diretório temporário para o DAMICORE
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = os.path.join(temp_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Salva os dados em arquivos
            for col in df.columns:
                df[col].to_csv(
                    os.path.join(data_dir, f"{col}.txt"),
                    index=False,
                    header=False
                )
            
            # Teste DAMICORE
            start = time.time()
            damicore_generate_ncd_matrix(
                input_dir=data_dir,
                compressor="gzip",
                max_workers=2
            )
            damicore_time = time.time() - start
        
        print(f"{name:<10} | {n_cols:<8} | {zlib_time:<15.4f} | {damicore_time:<15.4f}")
    
    print("-" * 80)
    print("Nota: Os tempos podem variar dependendo do hardware e carga do sistema.")


if __name__ == "__main__":
    # Executa os testes
    unittest.main(argv=sys.argv[:1], exit=False)
    
    # Executa o teste de desempenho
    run_performance_test()
