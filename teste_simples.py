#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste simples para verificar o ambiente
"""

def testar_imports():
    """Testa a importação dos módulos necessários"""
    try:
        import toytree
        from Bio import Phylo
        import numpy as np
        
        print("✅ Módulos importados com sucesso!")
        return True
    except ImportError as e:
        print("❌ Erro ao importar modulos: {}".format(e))
        return False

if __name__ == "__main__":
    testar_imports()
