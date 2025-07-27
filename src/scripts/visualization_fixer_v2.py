#!/usr/bin/env python3
"""
DAMICORE Visualization Fixer V2 - Versão Aprimorada
Resolve: nomes de variáveis, estrutura de diretórios, espaçamento adaptativo para 100+ variáveis
Cria pasta dedicada 'visualizations' para organizar melhor os arquivos
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from Bio import Phylo
import json
import shutil
from pathlib import Path
import re

# Tenta importar toytree para cloud/consensus trees
try:
    import toytree
    import toyplot
    import toyplot.pdf
    TOYTREE_AVAILABLE = True
except ImportError:
    TOYTREE_AVAILABLE = False
    print("⚠️  toytree não disponível, usando fallbacks")


class DAMICOREVisualizationFixerV2:
    """Classe aprimorada para corrigir problemas de visualização do DAMICORE"""
    
    def __init__(self, results_directory):
        """
        Inicializa o corretor de visualizações V2
        
        Args:
            results_directory: Diretório principal dos resultados DAMICORE
        """
        self.results_dir = Path(results_directory)
        self.original_csv_path = None
        self.index_to_name = {}
        self.num_variables = 0
        
    def detect_original_csv(self):
        """Detecta o arquivo CSV original para extrair nomes das variáveis"""
        csv_files = []
        
        # 1. Procura no diretório de resultados
        for csv_file in self.results_dir.glob("*.csv"):
            csv_files.append(csv_file)
            
        # 2. Procura no diretório pai
        parent_dir = self.results_dir.parent
        for csv_file in parent_dir.glob("*.csv"):
            csv_files.append(csv_file)
            
        # 3. Procura em data_projects (estrutura comum DAMICORE)
        data_projects_dirs = [
            parent_dir / "data_projects",
            parent_dir.parent / "data_projects",
            Path.home() / "data_projects"
        ]
        
        for data_dir in data_projects_dirs:
            if data_dir.exists():
                for csv_file in data_dir.rglob("*.csv"):
                    csv_files.append(csv_file)
        
        if not csv_files:
            print("❌ Nenhum arquivo CSV encontrado para detectar nomes das variáveis")
            return False
            
        # Seleciona o maior arquivo CSV (provavelmente o dataset original)
        largest_csv = max(csv_files, key=lambda f: f.stat().st_size if f.exists() else 0)
        self.original_csv_path = largest_csv
        
        print(f"📊 CSV original detectado: {self.original_csv_path}")
        print(f"📏 Tamanho: {self.original_csv_path.stat().st_size / (1024**3):.2f} GB")
        
        return True
    
    def create_index_to_name_mapping(self):
        """Cria mapeamento de índices para nomes originais das variáveis"""
        if not self.original_csv_path or not self.original_csv_path.exists():
            print("❌ Arquivo CSV original não encontrado")
            return False
            
        try:
            # Lê apenas o cabeçalho para extrair nomes das colunas
            df_header = pd.read_csv(self.original_csv_path, nrows=0)
            column_names = df_header.columns.tolist()
            self.num_variables = len(column_names)
            
            # Cria mapeamento índice -> nome
            self.index_to_name = {str(i): name for i, name in enumerate(column_names)}
            
            print(f"📋 Mapeamento criado para {self.num_variables} variáveis")
            print(f"📝 Primeiras 5 variáveis: {column_names[:5]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar mapeamento: {e}")
            return False
    
    def calculate_adaptive_dimensions_v2(self):
        """
        Calcula dimensões adaptativas V2 - Otimizado para 100+ variáveis
        Evita sobreposição de labels e garante legibilidade
        """
        if self.num_variables == 0:
            return 1200, 900  # Dimensões padrão maiores
            
        # Configurações base para diferentes faixas de variáveis
        if self.num_variables >= 100:
            # Para 100+ variáveis: dimensões muito grandes + espaçamento generoso
            base_width = 2000
            base_height = 1500
            width_factor = 25  # Mais espaço horizontal por variável
            height_factor = 15  # Mais espaço vertical por variável
            
        elif self.num_variables >= 50:
            # Para 50-99 variáveis: dimensões grandes
            base_width = 1600
            base_height = 1200
            width_factor = 20
            height_factor = 12
            
        elif self.num_variables >= 20:
            # Para 20-49 variáveis: dimensões médias
            base_width = 1200
            base_height = 900
            width_factor = 15
            height_factor = 10
            
        else:
            # Para <20 variáveis: dimensões padrão
            base_width = 800
            base_height = 600
            width_factor = 10
            height_factor = 8
        
        # Calcula dimensões finais
        width = base_width + (self.num_variables * width_factor)
        height = base_height + (self.num_variables * height_factor)
        
        # Limites máximos para evitar imagens excessivamente grandes
        max_width = 4000 if self.num_variables >= 100 else 3000
        max_height = 3000 if self.num_variables >= 100 else 2400
        
        width = min(width, max_width)
        height = min(height, max_height)
        
        print(f"📐 Dimensões V2 otimizadas: {width}x{height} para {self.num_variables} variáveis")
        return width, height
    
    def calculate_font_sizes_v2(self):
        """Calcula tamanhos de fonte adaptivos para evitar sobreposição"""
        if self.num_variables >= 100:
            return {
                'tip_labels': 6,      # Labels das variáveis
                'node_labels': 8,     # Labels dos nós
                'title': 12,          # Título
                'legend': 8           # Legenda
            }
        elif self.num_variables >= 50:
            return {
                'tip_labels': 8,
                'node_labels': 10,
                'title': 14,
                'legend': 10
            }
        elif self.num_variables >= 20:
            return {
                'tip_labels': 10,
                'node_labels': 12,
                'title': 16,
                'legend': 12
            }
        else:
            return {
                'tip_labels': 12,
                'node_labels': 14,
                'title': 18,
                'legend': 14
            }
    
    def create_visualizations_directory(self, slice_dir):
        """Cria diretório dedicado 'visualizations' dentro do slice"""
        slice_path = Path(slice_dir)
        viz_dir = slice_path / "visualizations"
        
        # Cria diretório se não existir
        viz_dir.mkdir(exist_ok=True)
        
        print(f"📁 Diretório de visualizações: {viz_dir}")
        return viz_dir
    
    def fix_newick_variable_names(self, newick_content):
        """Corrige nomes das variáveis em conteúdo newick"""
        if not self.index_to_name:
            return newick_content
            
        fixed_content = newick_content
        
        # Substitui padrões 'col_X.txt' pelos nomes originais
        pattern = r"'col_(\d+)\.txt'"
        
        def replace_match(match):
            col_index = match.group(1)
            if col_index in self.index_to_name:
                original_name = self.index_to_name[col_index]
                # Sanitiza o nome para uso em newick (remove caracteres especiais)
                sanitized_name = re.sub(r'[^\w\-_.]', '_', original_name)
                return f"'{sanitized_name}'"
            return match.group(0)
        
        fixed_content = re.sub(pattern, replace_match, fixed_content)
        return fixed_content
    
    def regenerate_visualizations_for_slice_v2(self, slice_dir):
        """Regenera visualizações V2 para uma fatia específica com melhorias"""
        slice_path = Path(slice_dir)
        damicore_results = slice_path / "damicore_results"
        
        if not damicore_results.exists():
            print(f"❌ Diretório damicore_results não encontrado em {slice_path}")
            return False
            
        # Cria diretório dedicado para visualizações
        viz_dir = self.create_visualizations_directory(slice_path)
        
        # Coleta arquivos newick
        newick_files = list(damicore_results.glob("*-tree.newick"))
        if not newick_files:
            print(f"❌ Nenhum arquivo newick encontrado em {damicore_results}")
            return False
            
        print(f"🔍 Encontrados {len(newick_files)} arquivos newick")
        
        # Processa arquivos newick com nomes corretos
        corrected_newicks = []
        for newick_file in newick_files:
            try:
                with open(newick_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        fixed_content = self.fix_newick_variable_names(content)
                        corrected_newicks.append(fixed_content)
            except Exception as e:
                print(f"⚠️  Erro ao processar {newick_file}: {e}")
        
        if not corrected_newicks:
            print(f"❌ Nenhum conteúdo newick válido encontrado")
            return False
        
        # Gera visualizações corrigidas V2
        width, height = self.calculate_adaptive_dimensions_v2()
        font_sizes = self.calculate_font_sizes_v2()
        
        try:
            # 1. Cloud Tree V2 com nomes corretos
            self._generate_corrected_cloud_tree_v2(corrected_newicks, viz_dir, width, height, font_sizes)
            
            # 2. Consensus Tree V2 com nomes corretos
            self._generate_corrected_consensus_tree_v2(corrected_newicks, viz_dir, width, height, font_sizes)
            
            # 3. Tree Biopython V2 com nomes corretos
            self._generate_corrected_biopython_tree_v2(corrected_newicks, viz_dir, width, height, font_sizes)
            
            print(f"✅ Visualizações V2 regeneradas para {slice_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao regenerar visualizações V2 para {slice_path.name}: {e}")
            return False
    
    def _generate_corrected_cloud_tree_v2(self, newick_contents, output_dir, width, height, font_sizes):
        """Gera cloud tree V2 com parâmetros otimizados"""
        try:
            if TOYTREE_AVAILABLE:
                # Usa toytree com parâmetros V2 otimizados
                mtree = toytree.mtree(newick_contents)
                
                # Extrai labels corrigidos
                tip_labels = []
                for label in mtree.get_tip_labels():
                    clean_label = label.strip("'\"")
                    tip_labels.append(clean_label)
                
                # Parâmetros V2 otimizados para 100+ variáveis
                canvas_tuple = mtree.draw_cloud_tree(
                    tip_labels=tip_labels,
                    node_labels=False,
                    use_edge_lengths=False,
                    node_sizes=8 if self.num_variables >= 100 else 16,  # Nós menores para muitas variáveis
                    width=width,
                    height=height,
                    tip_labels_style={
                        'font-size': f'{font_sizes["tip_labels"]}px',
                        'font-family': 'Arial, sans-serif'
                    },
                    edge_style={
                        'stroke-width': 1 if self.num_variables >= 100 else 2
                    }
                )
                canvas = canvas_tuple[0]
                output_path = output_dir / "cloud_tree_v2.pdf"
                toyplot.pdf.render(canvas, output_path)
                print(f"✅ Cloud tree V2 salva em {output_path}")
            else:
                # Fallback usando matplotlib V2
                self._generate_cloud_tree_fallback_v2(output_dir, width, height, font_sizes)
                
        except Exception as e:
            print(f"⚠️  Erro ao gerar cloud tree V2: {e}")
            self._generate_cloud_tree_fallback_v2(output_dir, width, height, font_sizes)
    
    def _generate_corrected_consensus_tree_v2(self, newick_contents, output_dir, width, height, font_sizes):
        """Gera consensus tree V2 com parâmetros otimizados"""
        try:
            if TOYTREE_AVAILABLE:
                # Usa toytree com parâmetros V2 otimizados
                mtree = toytree.mtree(newick_contents)
                ctre = mtree.get_consensus_tree()
                
                # Extrai labels corrigidos
                tip_labels = []
                for label in ctre.get_tip_labels():
                    clean_label = label.strip("'\"")
                    tip_labels.append(clean_label)
                
                # Parâmetros V2 otimizados
                canvas_tuple = ctre.draw(
                    tip_labels=tip_labels,
                    node_labels=ctre.get_node_values("support"),
                    node_sizes=16 if self.num_variables >= 100 else 32,  # Nós menores para muitas variáveis
                    width=width,
                    height=height,
                    tip_labels_style={
                        'font-size': f'{font_sizes["tip_labels"]}px',
                        'font-family': 'Arial, sans-serif'
                    },
                    node_labels_style={
                        'font-size': f'{font_sizes["node_labels"]}px',
                        'font-family': 'Arial, sans-serif'
                    },
                    edge_style={
                        'stroke-width': 1 if self.num_variables >= 100 else 2
                    }
                )
                canvas = canvas_tuple[0]
                output_path = output_dir / "consensus_tree_v2.pdf"
                toyplot.pdf.render(canvas, output_path)
                print(f"✅ Consensus tree V2 salva em {output_path}")
            else:
                # Fallback usando matplotlib V2
                self._generate_consensus_tree_fallback_v2(output_dir, width, height, font_sizes)
                
        except Exception as e:
            print(f"⚠️  Erro ao gerar consensus tree V2: {e}")
            self._generate_consensus_tree_fallback_v2(output_dir, width, height, font_sizes)
    
    def _generate_corrected_biopython_tree_v2(self, newick_contents, output_dir, width, height, font_sizes):
        """Gera tree biopython V2 com parâmetros otimizados"""
        try:
            from io import StringIO
            import matplotlib.pyplot as plt
            
            # Usa o primeiro arquivo newick válido
            newick_content = newick_contents[0]
            
            # Carrega árvore com Bio.Phylo
            tree_io = StringIO(newick_content)
            tree = Phylo.read(tree_io, "newick")
            
            # Renomeia folhas com nomes originais das variáveis
            for leaf in tree.get_terminals():
                if leaf.name:
                    # Extrai índice do padrão col_X.txt
                    match = re.search(r'col_(\d+)\.txt', leaf.name)
                    if match and match.group(1) in self.index_to_name:
                        leaf.name = self.index_to_name[match.group(1)]
            
            # Configurações V2 para matplotlib
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Parâmetros V2 otimizados
            axes = plt.gca()
            
            # Desenha árvore com parâmetros otimizados
            Phylo.draw(tree, axes=axes, 
                      do_show=False,
                      branch_labels=None,
                      label_func=lambda x: x.name if x.name else "",
                      label_colors='black')
            
            # Ajusta fonte dos labels
            for text in axes.texts:
                text.set_fontsize(font_sizes["tip_labels"])
                text.set_fontfamily('Arial')
            
            # Configurações do plot V2
            plt.title(f'DAMICORE Phylogenetic Tree V2 ({self.num_variables} variables)', 
                     fontsize=font_sizes["title"], fontweight='bold')
            plt.tight_layout()
            
            # Salva com alta resolução
            output_path = output_dir / "tree_biopython_v2.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"✅ Tree biopython V2 salva em {output_path}")
            
        except Exception as e:
            print(f"⚠️  Erro ao gerar tree biopython V2: {e}")
    
    def _generate_cloud_tree_fallback_v2(self, output_dir, width, height, font_sizes):
        """Fallback V2 para cloud tree usando matplotlib"""
        try:
            plt.figure(figsize=(width/100, height/100), dpi=100)
            plt.text(0.5, 0.5, f'Cloud Tree V2\n({self.num_variables} variables)\nToytree não disponível', 
                    ha='center', va='center', fontsize=font_sizes["title"])
            plt.title('DAMICORE Cloud Tree V2 (Fallback)', fontsize=font_sizes["title"])
            
            output_path = output_dir / "cloud_tree_v2_fallback.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✅ Cloud tree V2 fallback salva em {output_path}")
        except Exception as e:
            print(f"❌ Erro no fallback cloud tree V2: {e}")
    
    def _generate_consensus_tree_fallback_v2(self, output_dir, width, height, font_sizes):
        """Fallback V2 para consensus tree usando matplotlib"""
        try:
            plt.figure(figsize=(width/100, height/100), dpi=100)
            plt.text(0.5, 0.5, f'Consensus Tree V2\n({self.num_variables} variables)\nToytree não disponível', 
                    ha='center', va='center', fontsize=font_sizes["title"])
            plt.title('DAMICORE Consensus Tree V2 (Fallback)', fontsize=font_sizes["title"])
            
            output_path = output_dir / "consensus_tree_v2_fallback.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✅ Consensus tree V2 fallback salva em {output_path}")
        except Exception as e:
            print(f"❌ Erro no fallback consensus tree V2: {e}")
    
    def process_all_slices_v2(self):
        """Processa todas as fatias encontradas com melhorias V2"""
        if not self.detect_original_csv():
            return False
            
        if not self.create_index_to_name_mapping():
            return False
        
        # Encontra todos os diretórios de slices
        slice_dirs = []
        
        # Padrão 1: slice_XXXX na raiz
        for item in self.results_dir.iterdir():
            if item.is_dir() and item.name.startswith('slice_'):
                slice_dirs.append(item)
        
        # Padrão 2: slices/slice_XXXX
        slices_subdir = self.results_dir / "slices"
        if slices_subdir.exists():
            for item in slices_subdir.iterdir():
                if item.is_dir() and item.name.startswith('slice_'):
                    slice_dirs.append(item)
        
        if not slice_dirs:
            print("❌ Nenhum diretório de slice encontrado")
            return False
        
        print(f"🔍 Encontrados {len(slice_dirs)} slices para processar")
        
        # Processa cada slice
        success_count = 0
        total_count = len(slice_dirs)
        
        for slice_dir in sorted(slice_dirs):
            print(f"\n🔄 Processando {slice_dir.name}...")
            if self.regenerate_visualizations_for_slice_v2(slice_dir):
                success_count += 1
            
        # Relatório final
        report = {
            "version": "V2",
            "total_slices": total_count,
            "successful_slices": success_count,
            "failed_slices": total_count - success_count,
            "num_variables": self.num_variables,
            "original_csv": str(self.original_csv_path),
            "dimensions_used": self.calculate_adaptive_dimensions_v2(),
            "font_sizes_used": self.calculate_font_sizes_v2()
        }
        
        # Salva relatório
        report_path = self.results_dir / "visualization_correction_report_v2.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 RELATÓRIO FINAL V2:")
        print(f"✅ Slices processados com sucesso: {success_count}/{total_count}")
        print(f"📐 Dimensões otimizadas: {report['dimensions_used']}")
        print(f"🔤 Tamanhos de fonte: {report['font_sizes_used']}")
        print(f"📄 Relatório salvo em: {report_path}")
        
        return success_count > 0


def main():
    """Função principal para execução do corretor V2"""
    print("=" * 80)
    print("🎨 DAMICORE VISUALIZATION FIXER V2 - Versão Aprimorada")
    print("=" * 80)
    print("🔧 Correções V2:")
    print("   • Pasta dedicada 'visualizations' para cada slice")
    print("   • Dimensões otimizadas para 100+ variáveis")
    print("   • Tamanhos de fonte adaptativos")
    print("   • Espaçamento generoso para evitar sobreposição")
    print("=" * 80)
    
    # Solicita diretório de resultados
    results_dir = input("\n📁 Digite o caminho do diretório de resultados DAMICORE: ").strip().strip('"\'')
    
    if not os.path.exists(results_dir):
        print(f"❌ Diretório não encontrado: {results_dir}")
        return
    
    # Inicializa corretor V2
    fixer = DAMICOREVisualizationFixerV2(results_dir)
    
    # Executa correções V2
    print(f"\n🚀 Iniciando correções V2 em: {results_dir}")
    success = fixer.process_all_slices_v2()
    
    if success:
        print("\n🎉 CORREÇÕES V2 CONCLUÍDAS COM SUCESSO!")
        print("📁 Visualizações salvas em pasta dedicada 'visualizations' de cada slice")
        print("📐 Dimensões e fontes otimizadas para máxima legibilidade")
    else:
        print("\n❌ Falha nas correções V2")


if __name__ == "__main__":
    main()
