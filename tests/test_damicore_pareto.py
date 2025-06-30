import unittest
import os
import pandas as pd
import numpy as np
from scripts_modulares.DAMICORE_Pareto_script import run_damicore_analysis, run_pareto_analysis

class TestDAMICOREPareto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuração inicial dos testes."""
        # Criar dados de teste
        cls.test_data_dir = "tests/test_data"
        os.makedirs(cls.test_data_dir, exist_ok=True)
        
        # Criar arquivo CSV de teste
        cls.test_csv = os.path.join(cls.test_data_dir, "test_input.csv")
        df = pd.DataFrame({
            'join_CENSITARIO': range(1, 6),
            'populacao': [1000, 1500, 800, 2000, 1200],
            'renda': [2500, 3000, 2000, 3500, 2800],
            'idade_media': [35, 40, 30, 45, 38]
        })
        df.to_csv(cls.test_csv, index=False)
    
    def test_damicore_analysis(self):
        """Testa a análise DAMICORE."""
        try:
            df = run_damicore_analysis(self.test_csv)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 5)  # Número esperado de linhas
        except Exception as e:
            self.fail(f"run_damicore_analysis falhou com erro: {str(e)}")
    
    def test_pareto_analysis(self):
        """Testa a análise de Fronteira de Pareto."""
        df = pd.read_csv(self.test_csv)
        output_dir = os.path.join(self.test_data_dir, "output")
        
        # Simula input do usuário
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: "populacao,renda"
        
        try:
            run_pareto_analysis(df, output_dir)
            
            # Verifica se o arquivo de saída foi criado
            expected_output = os.path.join(output_dir, "pareto_analysis", "pareto_filtered_populacao_renda.csv")
            self.assertTrue(os.path.exists(expected_output))
            
            # Verifica o conteúdo do arquivo
            result_df = pd.read_csv(expected_output)
            self.assertTrue('pareto_frontier' in result_df.columns)
        except Exception as e:
            self.fail(f"run_pareto_analysis falhou com erro: {str(e)}")
        finally:
            builtins.input = original_input
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após os testes."""
        import shutil
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)

if __name__ == '__main__':
    unittest.main()
