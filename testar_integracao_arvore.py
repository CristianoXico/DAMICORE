"""
Script para testar a integração da função visualizar_arvore_consenso no pipeline principal.
"""
import numpy as np
import os
import sys

# Adiciona o diretório atual ao path para importar o módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa a função do pipeline
from pipeline_novo import visualize_consensus_trees

def testar_visualizacao_consenso():
    """Testa a geração de visualizações de árvore de consenso."""
    print("="*70)
    print("TESTE DE INTEGRAÇÃO DA ÁRVORE DE CONSENSO")
    print("="*70)
    
    # Matriz de distância de exemplo (NCD)
    ncd_mat = np.array([
        [0.0, 0.5, 0.8, 0.9],
        [0.5, 0.0, 0.7, 0.8],
        [0.8, 0.7, 0.0, 0.3],
        [0.9, 0.8, 0.3, 0.0]
    ])
    
    # Rótulos para as amostras
    labels = ['Amostra 1', 'Amostra 2', 'Amostra 3', 'Amostra 4']
    
    print("\n🔍 Iniciando teste da visualização de consenso...")
    print(f"   - Número de amostras: {len(labels)}")
    print(f"   - Dimensões da matriz NCD: {ncd_mat.shape}")
    
    try:
        # Chama a função do pipeline que foi atualizada
        print("\n🔄 Chamando visualize_consensus_trees...")
        resultado = visualize_consensus_trees(ncd_mat, labels)
        
        if resultado:
            print("\n✅ Teste concluído com sucesso!")
            print("\n📂 Arquivos gerados:")
            for key, path in resultado.items():
                if os.path.exists(path):
                    print(f"   - {key}: {path} ({os.path.getsize(path):,} bytes)")
                else:
                    print(f"   - {key}: {path} (arquivo não encontrado)")
        else:
            print("\n❌ Falha ao gerar as visualizações.")
            
        return resultado
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    testar_visualizacao_consenso()
