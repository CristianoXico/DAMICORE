import unittest
import tempfile
import os
import sys
import toytree

# Adiciona o diretório atual ao path para importar o módulo pipeline_novo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestVisualizacaoArvoreConsenso(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para os testes"""
        # Configura a saída para UTF-8
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
        # Dados de teste
        cls.newick1 = "((A:0.1,B:0.2)0.9:0.3,(C:0.3,D:0.4)0.8:0.5);"
        cls.newick2 = "((A:0.2,B:0.3)0.85:0.4,(C:0.4,D:0.5)0.75:0.6);"
        cls.newick3 = "((A:0.15,B:0.25)0.95:0.35,(C:0.35,D:0.45)0.7:0.55);"
        
        # Cria um diretório temporário para os testes
        cls.temp_dir = tempfile.mkdtemp(prefix="test_arvore_")
        print("\n[INFO] Diretorio temporario para testes: {}".format(cls.temp_dir))
    
    def test_extrair_suportes(self):
        """Testa a extração de suportes de uma árvore"""
        from pipeline_novo import extrair_suportes
        
        print("\n[TESTE] Testando extracao de suportes...")
        
        # Cria uma arvore de teste
        arvore = toytree.tree(self.newick1)
        
        # Extrai os suportes
        suportes, estatisticas = extrair_suportes(arvore)
        
        # Exibe informacoes de depuracao
        print("  - Suportes extraidos: {}".format(suportes))
        print("  - Estatisticas: {}".format(estatisticas))
        
        # Verificações
        self.assertGreater(len(suportes), 0, "Deveria ter extraído pelo menos um valor de suporte")
        self.assertIn('total_nos_internos', estatisticas)
        self.assertIn('nos_com_suporte', estatisticas)
        self.assertGreaterEqual(estatisticas['nos_com_suporte'], 1)
        
        print("[OK] Teste de extracao de suportes concluido com sucesso!")
    
    def test_estilo_arvore(self):
        """Testa a geração de estilos para a árvore"""
        from pipeline_novo import obter_estilo_arvore
        
        print("\n[TESTE] Testando geracao de estilos...")
        
        # Cria uma árvore de teste
        arvore = toytree.tree(self.newick1)
        
        # Obtém os estilos
        estilo = obter_estilo_arvore(arvore)
        
        # Exibe informações de depuração
        print("  - Estilo basico: {}".format(list(estilo.keys())))
        
        # Verificações
        self.assertIn('layout', estilo)
        self.assertIn('width', estilo)
        self.assertIn('height', estilo)
        self.assertIn('node_style', estilo)
        
        # Testa com suportes
        suportes = {0: 0.9, 1: 0.8}  # Índices e valores de suporte fictícios
        estilo_com_suporte = obter_estilo_arvore(arvore, suportes)
        
        # Exibe informações de depuração
        print("  - Estilo com suportes: {}".format(list(estilo_com_suporte.keys())))
        
        # Verificações adicionais para estilos com suporte
        self.assertIn('node_labels', estilo_com_suporte)
        self.assertIn('node_labels_style', estilo_com_suporte)
        
        print("[OK] Teste de geracao de estilos concluido com sucesso!")
    
    def test_visualizar_arvore_consenso(self):
        """Testa a geração de visualizações a partir de múltiplas árvores"""
        from pipeline_novo import visualizar_arvore_consenso
        
        print("\n[TESTE] Testando geracao de visualizacoes...")
        
        # Lista de árvores de teste
        arvores = [self.newick1, self.newick2, self.newick3]
        
        # Gera as visualizações
        resultado = visualizar_arvore_consenso(
            arvores,
            output_dir=os.path.join(self.temp_dir, "resultados"),
            prefixo="teste_consenso"
        )
        
        # Exibe informações de depuração
        print("  - Resultado: {}".format('Sucesso' if resultado.get('sucesso', False) else 'Falha'))
        if 'erros' in resultado and resultado['erros']:
            print("  - Erros: {}".format(resultado['erros']))
        
        # Verificações
        self.assertTrue(resultado['sucesso'], "A geração das visualizações falhou")
        
        # Verifica se os arquivos foram criados
        if 'arquivos_gerados' in resultado:
            print("  - Arquivos gerados:")
            for tipo, caminho in resultado['arquivos_gerados'].items():
                existe = os.path.exists(caminho)
                print("    - {}: {} ({})".format(tipo.upper(), caminho, 'Existe' if existe else 'Nao existe'))
                self.assertTrue(existe, f"Arquivo {tipo} não encontrado: {caminho}")
        
        # Verifica estatísticas
        if 'estatisticas' in resultado:
            print("  - Estatisticas:")
            for chave, valor in resultado['estatisticas'].items():
                if chave not in ['fontes_suporte', 'valores_unicos']:
                    print("    - {}: {}".format(chave, valor))
        
        print("[OK] Teste de geracao de visualizacoes concluido com sucesso!")

if __name__ == '__main__':
    unittest.main(verbosity=2)
