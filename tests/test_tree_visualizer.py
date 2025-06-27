import pytest
import toyplot
from pathlib import Path
from src.visualization.tree_visualizer import TreeVisualizer

@pytest.fixture
def sample_newick_trees():
    return [
        "(A:1,(B:1,(C:1,D:1):0.5):0.5);",
        "(A:1,(B:1,(D:1,C:1):0.5):0.5);",
        "(A:1,(B:1,(C:1,D:1):0.5):0.5);"
    ]

@pytest.fixture
def visualizer():
    return TreeVisualizer()

def test_init(visualizer):
    """Testa inicialização do visualizador"""
    assert visualizer.mtree is None
    assert visualizer.consensus_tree is None
    assert visualizer._default_style is not None
    assert visualizer._available_formats['svg'] is True

def test_load_newick_trees(visualizer, sample_newick_trees):
    """Testa carregamento de árvores Newick"""
    visualizer.load_newick_trees(sample_newick_trees)
    assert visualizer.mtree is not None
    
def test_load_newick_trees_empty(visualizer):
    """Testa erro ao carregar lista vazia"""
    with pytest.raises(ValueError, match="Lista de árvores Newick vazia"):
        visualizer.load_newick_trees([])

def test_create_consensus_tree(visualizer, sample_newick_trees):
    """Testa criação de árvore consenso"""
    visualizer.load_newick_trees(sample_newick_trees)
    visualizer.create_consensus_tree()
    assert visualizer.consensus_tree is not None

def test_create_consensus_tree_without_trees(visualizer):
    """Testa erro ao criar consenso sem árvores carregadas"""
    with pytest.raises(ValueError, match="Carregue as árvores primeiro"):
        visualizer.create_consensus_tree()

def test_draw_cloud_tree(visualizer, sample_newick_trees):
    """Testa desenho de cloud tree"""
    visualizer.load_newick_trees(sample_newick_trees)
    canvas = visualizer.draw_cloud_tree()
    assert isinstance(canvas, toyplot.canvas.Canvas)

def test_draw_cloud_tree_without_trees(visualizer):
    """Testa erro ao desenhar cloud tree sem árvores"""
    with pytest.raises(ValueError, match="Carregue as árvores primeiro"):
        visualizer.draw_cloud_tree()

def test_draw_consensus_tree(visualizer, sample_newick_trees):
    """Testa desenho de árvore consenso"""
    visualizer.load_newick_trees(sample_newick_trees)
    visualizer.create_consensus_tree()
    canvas = visualizer.draw_consensus_tree()
    assert isinstance(canvas, toyplot.Canvas)
    
def test_save_visualization_svg(visualizer, sample_newick_trees, tmp_path):
    """Test SVG visualization export"""
    visualizer.load_newick_trees(sample_newick_trees)
    canvas = visualizer.draw_cloud_tree()
    
    svg_path = tmp_path / "test.svg"
    visualizer.save_visualization(canvas, svg_path, format='svg')
    assert svg_path.exists()

def test_save_visualization_invalid_format(visualizer, sample_newick_trees, tmp_path):
    """Test error on invalid format"""
    visualizer.load_newick_trees(sample_newick_trees)
    canvas = visualizer.draw_cloud_tree()
    
    with pytest.raises(ValueError, match="Apenas o formato 'svg' é suportado"):
        visualizer.save_visualization(canvas, tmp_path / "test.jpg", format='jpg')

def test_check_dependencies(visualizer):
    """Test dependency checking"""
    formats = visualizer._check_dependencies()
    assert isinstance(formats, dict)
    assert 'svg' in formats
    assert formats['svg'] is True
    
def test_save_visualization_error_handling(visualizer, sample_newick_trees, tmp_path, monkeypatch):
    """Test error handling in save_visualization"""
    visualizer.load_newick_trees(sample_newick_trees)
    canvas = visualizer.draw_cloud_tree()
    
    # Mock toyplot.svg.render to raise an error
    def mock_render(*args, **kwargs):
        raise IOError("Mock write error")
        
    monkeypatch.setattr(visualizer._toyplot.svg, 'render', mock_render)
    
    with pytest.raises(RuntimeError, match="Erro ao salvar visualização"):
        visualizer.save_visualization(canvas, tmp_path / "test.svg")

def test_draw_consensus_tree_custom_style(visualizer, sample_newick_trees):
    """Test consensus tree drawing with custom style"""
    custom_style = {
        "node_style": {
            "fill": "red",
            "stroke": "black"
        }
    }
    
    visualizer.load_newick_trees(sample_newick_trees)
    visualizer.create_consensus_tree()
    canvas = visualizer.draw_consensus_tree(
        width=1000,
        height=800,
        tip_labels=False,
        node_labels=None,
        node_sizes=20,
        tip_colors=["red", "blue", "green", "yellow"],
        style=custom_style
    )
    assert isinstance(canvas, toyplot.Canvas)

def test_check_dependencies(visualizer):
    """Test dependency checking"""
    formats = visualizer._check_dependencies()
    assert isinstance(formats, dict)
    assert 'svg' in formats
    assert formats['svg'] is True