"""
Arquivo de configuração do pytest para adicionar o diretório raiz ao PYTHONPATH.
Isso permite que os testes importem módulos do pacote src corretamente.
"""
import os
import sys

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
