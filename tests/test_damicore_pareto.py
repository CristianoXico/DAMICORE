import unittest
import os
import sys
import pandas as pd
import numpy as np

# Adicionar o diretório do projeto ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar o módulo principal diretamente
import scripts_modulares.DAMICORE_Pareto_script as damicore

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
            # Executar análise
            damicore.run_damicore_analysis(self.test_csv)
            
            # Verificar estrutura de diretórios
            base_dir = os.path.splitext(os.path.basename(self.test_csv))[0]
            output_dir = os.path.join(self.test_data_dir, base_dir)
            damicore_dir = os.path.join(output_dir, "damicore_analysis")
            
            # Verificar diretórios principais
            self.assertTrue(os.path.exists(output_dir), f"Diretório de saída não encontrado: {output_dir}")
            self.assertTrue(os.path.exists(damicore_dir), f"Diretório DAMICORE não encontrado: {damicore_dir}")
            
            # Verificar diretório de resultados
            results_dir = os.path.join(damicore_dir, "damicore_results")
            self.assertTrue(os.path.exists(results_dir), f"Diretório de resultados não encontrado: {results_dir}")
            
            # Verificar número de arquivos .newick
            newick_files = [f for f in os.listdir(results_dir) if f.endswith("-tree.newick")]
            self.assertTrue(len(newick_files) >= 23, f"Número insuficiente de arquivos .newick: {len(newick_files)}")
            
            # Verificar arquivos de visualização
            visualization_dir = os.path.join(damicore_dir, "damicore_analysis")
            cloud_tree_svg = os.path.join(visualization_dir, "cloud_tree_with_barplot.svg")
            cloud_tree_newick = os.path.join(visualization_dir, "cloud_tree_with_barplot.newick")
            
            self.assertTrue(os.path.exists(cloud_tree_svg), f"Arquivo SVG não encontrado: {cloud_tree_svg}")
            self.assertTrue(os.path.exists(cloud_tree_newick), f"Arquivo Newick não encontrado: {cloud_tree_newick}")
            
            # Verificar conteúdo dos arquivos
            with open(cloud_tree_newick, 'r') as f:
                newick_content = f.read()
                self.assertTrue(len(newick_content) > 0, "Arquivo .newick está vazio")
                self.assertTrue(newick_content.startswith('('), "Formato Newick inválido")
                self.assertTrue(newick_content.endswith(';'), "Formato Newick inválido")
            
            with open(cloud_tree_svg, 'r') as f:
                svg_content = f.read()
                self.assertTrue(len(svg_content) > 0, "Arquivo SVG está vazio")
                self.assertTrue(svg_content.startswith('<?xml'), "Formato SVG inválido")
            
            # Verificar estrutura do diretório de samples
            sample_dir = os.path.join(damicore_dir, "sample_full")
            self.assertTrue(os.path.exists(sample_dir), f"Diretório de samples não encontrado: {sample_dir}")
            
            # Verificar número de diretórios de resample
            resample_dirs = os.listdir(sample_dir)
            self.assertTrue(len(resample_dirs) >= 23, f"Número insuficiente de diretórios de resample: {len(resample_dirs)}")
            
            # Verificar conteúdo de um diretório de resample
            if resample_dirs:
                test_resample = os.path.join(sample_dir, resample_dirs[0])
                self.assertTrue(os.path.exists(test_resample), f"Diretório de resample não encontrado: {test_resample}")
                
                # Verificar número de arquivos .csv
                csv_files = [f for f in os.listdir(test_resample) if f.endswith('.csv')]
                self.assertTrue(len(csv_files) > 0, f"Diretório de resample está vazio: {test_resample}")
                
                # Verificar conteúdo de um arquivo .csv
                if csv_files:
                    test_csv = os.path.join(test_resample, csv_files[0])
                    self.assertTrue(os.path.exists(test_csv), f"Arquivo CSV não encontrado: {test_csv}")
                    df = pd.read_csv(test_csv)
                    self.assertTrue(len(df.columns) == 1, "Arquivo CSV deve ter exatamente uma coluna")
                    
        except Exception as e:
            import traceback
            print(f"Erro detalhado: {traceback.format_exc()}")
            self.fail(f"run_damicore_analysis falhou com erro: {str(e)}")
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
            damicore.run_pareto_analysis(df, output_dir)
            
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
