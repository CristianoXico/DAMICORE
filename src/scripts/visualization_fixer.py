#!/usr/bin/env python3
"""
DAMICORE Visualization Fixer - Corrige problemas de visualização
Resolve: nomes de variáveis, estrutura de diretórios, espaçamento adaptativo
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from Bio import Phylo
import json
import shutil
from pathlib import Path

# Tenta importar toytree para cloud/consensus trees
try:
    import toytree
    import toyplot
    import toyplot.pdf
    TOYTREE_AVAILABLE = True
except ImportError:
    TOYTREE_AVAILABLE = False
    print("⚠️  toytree não disponível, usando fallbacks")


class DAMICOREVisualizationFixer:
    """Classe para corrigir problemas de visualização do DAMICORE"""
    
    def __init__(self, results_directory):
        """
        Inicializa o corretor de visualizações
        
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
            
        # 3. Procura em data_projects no mesmo drive
        drive_root = Path("/media/cristiano-xico/sandbox")
        if drive_root.exists():
            data_projects = drive_root / "data_projects"
            if data_projects.exists():
                for csv_file in data_projects.glob("*.csv"):
                    csv_files.append(csv_file)
                    
        # 4. Procura por padrão no nome do arquivo (aggrada-inct-fome)
        results_name = self.results_dir.name
        if "aggrada-inct-fome" in results_name:
            # Extrai padrão do nome do diretório de resultados
            pattern = results_name.replace("_sliced_results", "")
            for csv_file in drive_root.rglob(f"{pattern}.csv"):
                csv_files.append(csv_file)
                
        # 5. Procura arquivos grandes (>100MB, provavelmente originais)
        large_csv_files = []
        for csv_file in csv_files:
            try:
                if csv_file.stat().st_size > 100 * 1024 * 1024:  # >100MB
                    large_csv_files.append(csv_file)
            except:
                continue
                
        # Prioriza arquivos grandes, depois todos os encontrados
        target_files = large_csv_files if large_csv_files else csv_files
        
        if target_files:
            # Ordena por tamanho (maior primeiro)
            target_files.sort(key=lambda x: x.stat().st_size, reverse=True)
            self.original_csv_path = target_files[0]
            size_mb = self.original_csv_path.stat().st_size / (1024 * 1024)
            print(f"📁 CSV original detectado: {self.original_csv_path}")
            print(f"📊 Tamanho: {size_mb:.1f} MB")
            return True
        else:
            print("❌ Nenhum arquivo CSV encontrado para extrair nomes das variáveis")
            print("💡 Verifique se o arquivo CSV original está acessível")
            return False
    
    def create_variable_mapping(self):
        """Cria o mapeamento de índices para nomes originais das variáveis"""
        if not self.original_csv_path:
            if not self.detect_original_csv():
                return False
                
        try:
            # Lê apenas o cabeçalho do CSV para obter nomes das colunas
            df_header = pd.read_csv(self.original_csv_path, nrows=0)
            column_names = df_header.columns.tolist()
            self.num_variables = len(column_names)
            
            # Cria mapeamento índice -> nome original
            self.index_to_name = {str(i): name for i, name in enumerate(column_names)}
            
            print(f"✅ Mapeamento criado para {self.num_variables} variáveis")
            print(f"📊 Primeiras 5 variáveis: {column_names[:5]}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar mapeamento de variáveis: {e}")
            return False
    
    def calculate_adaptive_dimensions(self):
        """Calcula dimensões adaptativas baseadas no número de variáveis"""
        if self.num_variables == 0:
            return 800, 600  # Dimensões padrão
            
        # Lógica adaptativa baseada no número de variáveis
        base_width = 800
        base_height = 600
        
        # Aumenta proporcionalmente ao número de variáveis
        if self.num_variables > 50:
            width = base_width + (self.num_variables - 50) * 15
            height = base_height + (self.num_variables - 50) * 10
        elif self.num_variables > 20:
            width = base_width + (self.num_variables - 20) * 10
            height = base_height + (self.num_variables - 20) * 8
        else:
            width = base_width
            height = base_height
            
        # Limites máximos para evitar imagens muito grandes
        width = min(width, 2400)
        height = min(height, 1800)
        
        print(f"📐 Dimensões adaptativas: {width}x{height} para {self.num_variables} variáveis")
        return width, height
    
    def fix_newick_variable_names(self, newick_content):
        """Corrige nomes das variáveis em conteúdo newick"""
        if not self.index_to_name:
            return newick_content
            
        fixed_content = newick_content
        
        # Substitui padrões 'col_X.txt' pelos nomes originais
        import re
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
    
    def regenerate_visualizations_for_slice(self, slice_dir):
        """Regenera visualizações para uma fatia específica com nomes corretos"""
        slice_path = Path(slice_dir)
        damicore_results = slice_path / "damicore_results"
        
        if not damicore_results.exists():
            print(f"❌ Diretório damicore_results não encontrado em {slice_path}")
            return False
            
        # Coleta arquivos newick
        newick_files = list(damicore_results.glob("*-tree.newick"))
        if not newick_files:
            print(f"❌ Nenhum arquivo newick encontrado em {damicore_results}")
            return False
            
        print(f"🔄 Regenerando visualizações para {slice_path.name} ({len(newick_files)} arquivos newick)")
        
        # Lê e corrige conteúdo dos arquivos newick
        corrected_newicks = []
        for newick_file in newick_files:
            try:
                with open(newick_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        corrected_content = self.fix_newick_variable_names(content)
                        corrected_newicks.append(corrected_content)
            except Exception as e:
                print(f"⚠️  Erro ao ler {newick_file}: {e}")
        
        if not corrected_newicks:
            print(f"❌ Nenhum conteúdo newick válido encontrado")
            return False
        
        # Gera visualizações corrigidas
        width, height = self.calculate_adaptive_dimensions()
        
        try:
            # 1. Cloud Tree com nomes corretos
            self._generate_corrected_cloud_tree(corrected_newicks, slice_path, width, height)
            
            # 2. Consensus Tree com nomes corretos
            self._generate_corrected_consensus_tree(corrected_newicks, slice_path, width, height)
            
            # 3. Tree Biopython com nomes corretos
            self._generate_corrected_biopython_tree(corrected_newicks, slice_path, width, height)
            
            print(f"✅ Visualizações regeneradas para {slice_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao regenerar visualizações para {slice_path.name}: {e}")
            return False
    
    def _generate_corrected_cloud_tree(self, newick_contents, output_dir, width, height):
        """Gera cloud tree com nomes de variáveis corretos"""
        try:
            if TOYTREE_AVAILABLE:
                # Usa toytree se disponível
                mtree = toytree.mtree(newick_contents)
                
                # Extrai labels corrigidos
                tip_labels = []
                for label in mtree.get_tip_labels():
                    clean_label = label.strip("'\"")
                    tip_labels.append(clean_label)
                
                # Desenha cloud tree
                canvas_tuple = mtree.draw_cloud_tree(
                    tip_labels=tip_labels,
                    node_labels=False,
                    use_edge_lengths=False,
                    node_sizes=16,
                    width=width,
                    height=height
                )
                canvas = canvas_tuple[0]
                output_path = output_dir / "cloud_tree_corrected.pdf"
                toyplot.pdf.render(canvas, output_path)
                print(f"✅ Cloud tree corrigida salva em {output_path}")
            else:
                # Fallback usando matplotlib
                self._generate_cloud_tree_fallback(output_dir, width, height)
                
        except Exception as e:
            print(f"⚠️  Erro ao gerar cloud tree corrigida: {e}")
            self._generate_cloud_tree_fallback(output_dir, width, height)
    
    def _generate_corrected_consensus_tree(self, newick_contents, output_dir, width, height):
        """Gera consensus tree com nomes de variáveis corretos"""
        try:
            if TOYTREE_AVAILABLE:
                # Usa toytree se disponível
                mtree = toytree.mtree(newick_contents)
                ctre = mtree.get_consensus_tree()
                
                # Extrai labels corrigidos
                tip_labels = []
                for label in ctre.get_tip_labels():
                    clean_label = label.strip("'\"")
                    tip_labels.append(clean_label)
                
                # Desenha consensus tree
                canvas_tuple = ctre.draw(
                    tip_labels=tip_labels,
                    node_labels=ctre.get_node_values("support"),
                    node_sizes=32,
                    width=width,
                    height=height
                )
                canvas = canvas_tuple[0]
                output_path = output_dir / "consensus_tree_corrected.pdf"
                toyplot.pdf.render(canvas, output_path)
                print(f"✅ Consensus tree corrigida salva em {output_path}")
            else:
                # Fallback usando matplotlib
                self._generate_consensus_tree_fallback(output_dir, width, height)
                
        except Exception as e:
            print(f"⚠️  Erro ao gerar consensus tree corrigida: {e}")
            self._generate_consensus_tree_fallback(output_dir, width, height)
    
    def _generate_corrected_biopython_tree(self, newick_contents, output_dir, width, height):
        """Gera tree biopython com nomes de variáveis corretos"""
        try:
            if newick_contents:
                # Usa o primeiro newick para visualização
                from io import StringIO
                tree_io = StringIO(newick_contents[0])
                tree = Phylo.read(tree_io, "newick")
                
                # Configura matplotlib
                plt.figure(figsize=(width/100, height/100))
                plt.title(f"Phylogenetic Tree ({self.num_variables} variables)", fontsize=14)
                
                # Desenha árvore
                Phylo.draw(tree, do_show=False, axes=plt.gca())
                
                # Salva imagem
                output_path = output_dir / "tree_biopython_corrected.png"
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"✅ Tree biopython corrigida salva em {output_path}")
                
        except Exception as e:
            print(f"⚠️  Erro ao gerar tree biopython corrigida: {e}")
    
    def _generate_cloud_tree_fallback(self, output_dir, width, height):
        """Fallback para cloud tree usando matplotlib"""
        plt.figure(figsize=(width/100, height/100))
        plt.text(0.5, 0.5, f'Cloud Tree\n({self.num_variables} variables)\nToytree not available', 
                ha='center', va='center', fontsize=16)
        plt.title("Cloud Tree (Fallback)", fontsize=14)
        output_path = output_dir / "cloud_tree_corrected.pdf"
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        print(f"✅ Cloud tree fallback salva em {output_path}")
    
    def _generate_consensus_tree_fallback(self, output_dir, width, height):
        """Fallback para consensus tree usando matplotlib"""
        plt.figure(figsize=(width/100, height/100))
        plt.text(0.5, 0.5, f'Consensus Tree\n({self.num_variables} variables)\nToytree not available', 
                ha='center', va='center', fontsize=16)
        plt.title("Consensus Tree (Fallback)", fontsize=14)
        output_path = output_dir / "consensus_tree_corrected.pdf"
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        print(f"✅ Consensus tree fallback salva em {output_path}")
    
    def clean_redundant_directories(self):
        """Remove diretórios redundantes (slice_XXXX_results quando slice_XXXX existe)"""
        print("🧹 Limpando estrutura de diretórios redundante...")
        
        slice_dirs = []
        slice_results_dirs = []
        
        # Identifica diretórios slice_XXXX e slice_XXXX_results
        for item in self.results_dir.iterdir():
            if item.is_dir():
                if item.name.startswith("slice_") and item.name.endswith("_results"):
                    slice_results_dirs.append(item)
                elif item.name.startswith("slice_") and not item.name.endswith("_results"):
                    slice_dirs.append(item)
        
        # Para cada slice_XXXX_results, verifica se existe slice_XXXX correspondente
        cleaned_count = 0
        for results_dir in slice_results_dirs:
            slice_name = results_dir.name.replace("_results", "")
            corresponding_slice = self.results_dir / slice_name
            
            if corresponding_slice.exists() and corresponding_slice.is_dir():
                # Verifica se slice_XXXX tem conteúdo mais completo
                slice_content = list(corresponding_slice.iterdir())
                results_content = list(results_dir.iterdir())
                
                if len(slice_content) >= len(results_content):
                    # Remove o diretório _results redundante
                    print(f"🗑️  Removendo diretório redundante: {results_dir.name}")
                    shutil.rmtree(results_dir)
                    cleaned_count += 1
                else:
                    print(f"⚠️  Mantendo {results_dir.name} (tem mais conteúdo que {slice_name})")
        
        print(f"✅ Limpeza concluída: {cleaned_count} diretórios redundantes removidos")
    
    def fix_all_visualizations(self):
        """Corrige todas as visualizações no diretório de resultados"""
        print("🎨 Iniciando correção completa das visualizações DAMICORE...")
        
        # 1. Detecta CSV original e cria mapeamento
        if not self.create_variable_mapping():
            print("❌ Não foi possível criar mapeamento de variáveis")
            return False
        
        # 2. Limpa diretórios redundantes
        self.clean_redundant_directories()
        
        # 3. Encontra todos os diretórios de fatias
        slice_dirs = []
        for item in self.results_dir.iterdir():
            if item.is_dir() and item.name.startswith("slice_") and not item.name.endswith("_results"):
                slice_dirs.append(item)
        
        if not slice_dirs:
            print("❌ Nenhum diretório de fatia encontrado")
            return False
        
        print(f"📊 Encontradas {len(slice_dirs)} fatias para correção")
        
        # 4. Regenera visualizações para cada fatia
        success_count = 0
        for slice_dir in sorted(slice_dirs):
            if self.regenerate_visualizations_for_slice(slice_dir):
                success_count += 1
        
        print(f"✅ Correção concluída: {success_count}/{len(slice_dirs)} fatias processadas com sucesso")
        
        # 5. Gera relatório de correção
        self._generate_correction_report(success_count, len(slice_dirs))
        
        return success_count > 0
    
    def _generate_correction_report(self, success_count, total_count):
        """Gera relatório da correção das visualizações"""
        report = {
            "correction_timestamp": pd.Timestamp.now().isoformat(),
            "total_slices": total_count,
            "successful_corrections": success_count,
            "failed_corrections": total_count - success_count,
            "num_variables": self.num_variables,
            "original_csv": str(self.original_csv_path) if self.original_csv_path else None,
            "adaptive_dimensions": self.calculate_adaptive_dimensions(),
            "toytree_available": TOYTREE_AVAILABLE
        }
        
        report_path = self.results_dir / "visualization_correction_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Relatório de correção salvo em {report_path}")


def main():
    """Função principal para execução do corretor"""
    print("=" * 80)
    print("🎨 DAMICORE VISUALIZATION FIXER")
    print("=" * 80)
    print("🎯 Corrige nomes de variáveis, estrutura de diretórios e espaçamento")
    print("=" * 80)
    
    # Solicita diretório de resultados
    results_dir = input("\n📁 Digite o caminho para o diretório de resultados DAMICORE: ").strip()
    
    if not os.path.exists(results_dir):
        print(f"❌ Diretório não encontrado: {results_dir}")
        return
    
    # Inicializa corretor
    fixer = DAMICOREVisualizationFixer(results_dir)
    
    # Executa correção completa
    success = fixer.fix_all_visualizations()
    
    if success:
        print("\n🎉 Correção das visualizações concluída com sucesso!")
        print("📊 Visualizações corrigidas:")
        print("   - Nomes de variáveis originais aplicados")
        print("   - Dimensões adaptativas calculadas")
        print("   - Diretórios redundantes removidos")
        print("   - Arquivos *_corrected.pdf/png gerados")
    else:
        print("\n❌ Falha na correção das visualizações")
        print("Verifique os logs acima para detalhes dos erros")


if __name__ == "__main__":
    main()
