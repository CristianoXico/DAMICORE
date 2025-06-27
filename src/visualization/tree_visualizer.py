import toytree
import toyplot
import toyplot.svg
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class TreeVisualizer:
    """Classe para visualização de árvores filogenéticas"""
    
    def __init__(self):
        self.mtree = None
        self.consensus_tree = None
        self._toyplot = toyplot  # Store toyplot reference
        self._default_style = {
            "edge_style": {
                "stroke-opacity": 0.3,
                "stroke-width": 3,
            },
            "node_style": {
                "fill": "steelblue",
                "stroke": "white",
            }
        }
        self._available_formats = {'svg': True}
        self._check_dependencies()

    def _check_dependencies(self) -> Dict[str, bool]:
        """
        Verifica dependências disponíveis.
        
        Retorna:
            Dicionário com os formatos suportados (apenas SVG)
        """
        # Suporta apenas SVG para simplificação e remoção de dependências externas
        return {'svg': True}

    def load_newick_trees(self, newick_strings: List[str]) -> None:
        """
        Carrega árvores no formato Newick
        
        Args:
            newick_strings: Lista de strings no formato Newick
        """
        if not newick_strings:
            raise ValueError("Lista de árvores Newick vazia")
            
        self.mtree = toytree.mtree("\n".join(newick_strings))

    def create_consensus_tree(self, 
                            rooted: bool = True, 
                            min_freq: float = 0.5) -> None:
        """
        Cria árvore de consenso
        
        Args:
            rooted: Se True, cria árvore enraizada
            min_freq: Frequência mínima para incluir nós
        """
        if self.mtree is None:
            raise ValueError("Carregue as árvores primeiro usando load_newick_trees()")
            
        self.consensus_tree = self.mtree.get_consensus_tree(
            rooted=rooted,
            min_freq=min_freq
        )

    def draw_cloud_tree(self, 
                       width: int = 800, 
                       height: int = 600,
                       **kwargs) -> Any:
        """
        Gera visualização cloud tree
        
        Args:
            width: Largura da visualização
            height: Altura da visualização
            **kwargs: Argumentos adicionais para personalização
        
        Returns:
            Canvas do Toyplot com a visualização
        """
        if self.mtree is None:
            raise ValueError("Carregue as árvores primeiro usando load_newick_trees()")
            
        style = self._default_style.copy()
        style.update(kwargs.get('style', {}))
            
        canvas, axes, mark = self.mtree.draw_cloud_tree(
            width=width,
            height=height,
            edge_style=style["edge_style"]
        )
        return canvas

    def draw_consensus_tree(self,
                          width: int = 800,
                          height: int = 600,
                          tip_labels: bool = True,
                          node_labels: str = 'support',
                          node_sizes: int = 16,
                          tip_colors: Optional[List[str]] = None,
                          **kwargs) -> Any:
        """
        Desenha árvore de consenso
        
        Args:
            width: Largura da visualização
            height: Altura da visualização
            tip_labels: Se True, mostra rótulos nas pontas
            node_labels: Tipo de rótulo dos nós ('support' ou None)
            node_sizes: Tamanho dos nós
            tip_colors: Cores para os rótulos das pontas
            **kwargs: Argumentos adicionais para personalização
            
        Returns:
            Canvas do Toyplot com a visualização
        """
        if self.consensus_tree is None:
            raise ValueError("Crie a árvore de consenso primeiro usando create_consensus_tree()")
            
        style = self._default_style.copy()
        style.update(kwargs.get('style', {}))
        
        # Create canvas and axes for drawing
        canvas = toyplot.Canvas(width=width, height=height)
        axes = canvas.cartesian()
        
        # Draw tree on axes
        self.consensus_tree.draw(
            axes=axes,
            tip_labels=tip_labels,
            node_labels=node_labels,
            node_sizes=node_sizes,
            tip_labels_colors=tip_colors,
            node_style=style["node_style"]
        )
        
        return canvas

    def save_visualization(self, 
                         canvas: Any, 
                         output_path: Union[str, Path],
                         format: str = 'svg') -> None:
        """
        Salva a visualização em arquivo SVG.
        
        Args:
            canvas: Canvas do Toyplot para salvar
            output_path: Caminho para salvar o arquivo
            format: Formato de saída (apenas 'svg' é suportado)
            
        Raises:
            ValueError: Se o formato não for 'svg'
            RuntimeError: Se ocorrer um erro ao salvar o arquivo
        """
        if format.lower() != 'svg':
            raise ValueError("Apenas o formato 'svg' é suportado nesta versão.")
            
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self._toyplot.svg.render(canvas, str(output_path))
        except Exception as e:
            raise RuntimeError(f"Erro ao salvar visualização SVG: {str(e)}")