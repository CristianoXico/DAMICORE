import os
import toytree
import toyplot
import toyplot.pdf
import toyplot.png
import toyplot.svg
from Bio import Phylo
from io import StringIO
# Configurar backend não-interativo do matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Configuração do teste
PROJECT_DIR = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/test_data/sample_dengue"
RESULTS_DIR = os.path.join(PROJECT_DIR, "damicore_results")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "visualization_tests")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_newick_data():
    """Carregar dados Newick reais do projeto"""
    plain_newicks = []
    for tf in os.listdir(RESULTS_DIR):
        if tf.endswith("-tree.newick"):
            tf_path = os.path.join(RESULTS_DIR, tf)
            with open(tf_path, "r") as f:
                plain_newicks.append(f.read())
    return "\n".join(plain_newicks)

def test_toytree_draw():
    """Testar diferentes métodos de desenho e salvamento com ToyTree"""
    print("\nTestando visualizações com ToyTree...")
    
    # Carregar dados Newick reais
    test_newick = get_newick_data()
    if not test_newick.strip():
        print("❌ Nenhum dado Newick encontrado!")
        return
    
    # Método 1: Cloud Tree com toyplot (forma básica)
    print("\nMétodo 1: Cloud Tree com toyplot")
    try:
        mtree = toytree.mtree(test_newick)
        canvas_tuple = mtree.draw_cloud_tree()  # Forma mais simples
        canvas1 = canvas_tuple[0]
        toyplot.pdf.render(canvas1, os.path.join(OUTPUT_DIR, "cloud_tree_1.pdf"))
        print("✓ Salvamento método 1 bem sucedido")
    except Exception as e:
        print(f"✗ Erro no método 1: {e}")

    # Método 2: Tree com estilo personalizado
    print("\nMétodo 2: Tree com estilo personalizado")
    try:
        canvas_tuple = mtree.draw(
            width=800,
            height=600,
            node_sizes=20,
            node_style={"fill": "lightgreen"},
            edge_style={"stroke": "darkgreen", "stroke-width": 2}
        )
        canvas2 = canvas_tuple[0]
        toyplot.pdf.render(canvas2, os.path.join(OUTPUT_DIR, "tree_2.pdf"))
        print("✓ Salvamento método 2 bem sucedido")
    except Exception as e:
        print(f"✗ Erro no método 2: {e}")

    # Método 3: Consensus Tree com especificações detalhadas
    print("\nMétodo 3: Consensus Tree")
    try:
        ctree = mtree.get_consensus_tree()
        
        # Garantir que os valores de suporte estejam acessíveis
        for node in ctree.treenode.traverse():
            node.support = node.support
        
        # Desenhar a árvore de consenso com configurações específicas
        canvas_tuple = ctree.draw(
            width=800,
            height=600,
            node_labels="support",     # Mostrar frequências dos nós como labels
            node_sizes=32,             # Tamanho dos nós para melhor visibilidade
            use_edge_lengths=False,    # Desabilitar comprimentos das arestas
            node_style={
                "fill": "lightgreen",
                "stroke": "black",
                "stroke-width": 1
            },
            edge_style={
                "stroke": "darkgreen",
                "stroke-width": 2
            }
        )
        canvas3 = canvas_tuple[0]
        toyplot.pdf.render(canvas3, os.path.join(OUTPUT_DIR, "consensus_tree_3.pdf"))
        print("✓ Salvamento método 3 bem sucedido")
    except Exception as e:
        print(f"✗ Erro no método 3: {e}")

def test_biopython_draw():
    """Testar visualização com Biopython"""
    print("\nTestando visualização com Biopython...")
    
    test_newick = get_newick_data()
    try:
        trees = list(Phylo.parse(StringIO(test_newick), "newick"))
        fig, ax = plt.subplots(figsize=(10, 20))
        Phylo.draw(trees[0], axes=ax, do_show=False,
                  branch_labels=lambda c: c.branch_length)
        plt.title("Phylogenetic Tree (Biopython)")
        plt.savefig(os.path.join(OUTPUT_DIR, "biopython_tree.png"))
        plt.close(fig)
        print("✓ Salvamento Biopython bem sucedido")
    except Exception as e:
        print(f"✗ Erro na visualização Biopython: {e}")

if __name__ == "__main__":
    print(f"Testando visualizações de árvores... Resultados serão salvos em: {OUTPUT_DIR}")
    test_toytree_draw()
    test_biopython_draw()
    print("\nTestes concluídos. Verifique os arquivos gerados no diretório de saída.")
