import plotly.graph_objects as go
import networkx as nx
import numpy as np
import pickle
import os
from pathlib import Path

class DAMICOREVisualizer:
    def __init__(self, output_dir='results'):
        """Initialize visualizer with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def save_results(self, results, filename):
        """Salva resultados em arquivo com timestamp"""
        filepath = self.output_dir / filename
        with open(filepath, 'wb') as f:
            pickle.dump(results, f)
        return filepath
    
    def plot_community_graph(self, G, communities, title="Community Graph"):
        """Visualiza grafo de comunidades com melhorias"""
        pos = nx.spring_layout(G, k=1/np.sqrt(G.number_of_nodes()))
        
        # Criar visualização interativa com cores por comunidade
        edge_trace = go.Scatter(
            x=[], y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_trace = go.Scatter(
            x=[], y=[],
            mode='markers+text',
            hoverinfo='text',
            text=[],  # Node labels
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                size=15,
                color=[],  # Node colors
                line=dict(width=1, color='#888'),
                colorbar=dict(
                    thickness=15,
                    title='Community',
                    xanchor='left',
                    titleside='right'
                )
            ))

        # Adicionar nós e arestas com informações
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])

        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([f'Node: {node}<br>Community: {communities[node]}'])
            node_trace['marker']['color'] += tuple([communities[node]])
            
        # Layout melhorado
        layout = go.Layout(
            title=dict(
                text=title,
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            template='plotly_white'
        )
        
        # Criar e salvar figura
        fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
        return fig
    
    def save_plot(self, fig, filename):
        """Salva plot em HTML interativo"""
        filepath = self.output_dir / filename
        fig.write_html(filepath)
        return filepath

    def plot_metrics(self, metrics):
        """Plota métricas de qualidade"""
        fig = go.Figure()
        
        for metric, value in metrics.items():
            fig.add_trace(go.Bar(
                name=metric,
                x=[metric],
                y=[value],
                text=[f'{value:.3f}'],
                textposition='auto',
            ))
            
        fig.update_layout(
            title="Community Quality Metrics",
            yaxis_title="Score",
            template='plotly_white'
        )
        
        return fig