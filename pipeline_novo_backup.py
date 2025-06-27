#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import sys
import io
import argparse
import numpy as np
import pandas as pd

try:
    from typing import List, Tuple, Dict, Any, Optional
except ImportError:
    pass  # Para versões antigas do Python

try:
    import toytree
except ImportError:
    print("AVISO: Modulo 'toytree' nao encontrado. Algumas funcionalidades podem estar limitadas.")

try:
    from Bio import Phylo
except ImportError:
    print("AVISO: Modulo 'biopython' nao encontrado. Visualizacoes em formato Newick podem nao funcionar.")

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("AVISO: Modulo 'matplotlib' nao encontrado. Visualizacoes graficas podem nao funcionar.")

from io import StringIO
import tempfile
import shutil
import logging
import subprocess
import json
import warnings

# Configura avisos
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Configura o encoding para UTF-8
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # Configura a saída padrão para usar UTF-8 no Windows
    if sys.platform == 'win32':
        try:
            # Python 3
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except AttributeError:
            # Python 2
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

def is_interactive():
    """Verifica se a execução está ocorrendo em um terminal interativo."""
    import sys
    return sys.stdin.isatty()

def generate_ncd_matrix_damicore(
    input_dir,
    output_dir=None,
    compressor="gzip",
    max_workers=4
):
    """
    Gera a matriz NCD a partir de um diretório de arquivos usando o método do DAMICORE.
    
    Args:
        input_dir: Diretório contendo os arquivos de entrada
        output_dir: Diretório para salvar os resultados (opcional)
        compressor: Algoritmo de compressão a ser usado (gzip, bzip2, ppmd)
        max_workers: Número máximo de processos paralelos (não utilizado na versão atual)
        
    Returns:
        Tupla contendo a matriz NCD e a lista de rótulos
    """
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)
    
    # Adiciona o diretório atual ao PATH para importar os módulos do DAMICORE
    current_dir = os.path.abspath('.')
    sys.path.insert(0, current_dir)
    
    # Verifica se o diretório damicore_py3 existe
    damicore_dir = os.path.join(current_dir, 'damicore_py3')
    if not os.path.exists(damicore_dir):
        msg = "Diretorio 'damicore_py3' nao encontrado em {}".format(current_dir)
        raise FileNotFoundError(msg)
    
    # Adiciona o diretório damicore_py3 ao PATH
    sys.path.insert(0, damicore_dir)
    
    # Importa os módulos necessários do DAMICORE
    try:
        from ncd import distance_matrix, to_matrix
    except ImportError as e:
        logger.error(f"Erro ao importar módulos do DAMICORE: {e}")
        raise
    
    # Usa um diretório temporário se nenhum for especificado
    if output_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="damicore_ncd_")
        is_temp = True
    else:
        os.makedirs(output_dir, exist_ok=True)
        temp_dir = output_dir
        is_temp = False
    
    try:
        logger.info(f"Iniciando geração da matriz NCD para arquivos em: {input_dir}")
        
        # Verifica se o diretório de entrada existe
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Diretório de entrada não encontrado: {input_dir}")
        
        # Lista de arquivos a serem processados (apenas arquivos, sem diretórios)
        files_to_process = [
            os.path.join(input_dir, f) for f in os.listdir(input_dir) 
            if os.path.isfile(os.path.join(input_dir, f))
        ]
        
        if not files_to_process:
            raise ValueError(f"Nenhum arquivo encontrado no diretório: {input_dir}")
        
        logger.info(f"Encontrados {len(files_to_process)} arquivos para processar")
        
        # Cria diretório de saída se não existir
        os.makedirs(temp_dir, exist_ok=True)
        
        # Define os parâmetros para o cálculo da matriz de distância
        pairing_name = 'concat'  # Pode ser 'concat' ou 'interleave'
        
        logger.info(f"Calculando matriz de distância usando {compressor} e {pairing_name}...")
        
        # Calcula a matriz de distância
        ncd_results = distance_matrix(
            directory=input_dir,
            compression_name=compressor,
            pairing_name=pairing_name,
            is_parallel=False  # Desativa o paralelismo para evitar problemas
        )
        
        # Converte os resultados para uma matriz
        ncd_matrix, labels = to_matrix(ncd_results)
        
        # Converte a matriz de lista para array NumPy, se necessário
        if not isinstance(ncd_matrix, np.ndarray):
            ncd_matrix = np.array(ncd_matrix)
        
        # Obtém os nomes dos arquivos sem o caminho completo
        labels = [os.path.splitext(os.path.basename(f))[0] for f in files_to_process]
        
        # Garante que temos o mesmo número de rótulos que a dimensão da matriz
        if len(labels) != ncd_matrix.shape[0]:
            logger.warning("Número de rótulos diferente da dimensão da matriz. Usando índices como rótulos.")
            labels = [f"Arquivo_{i}" for i in range(ncd_matrix.shape[0])]
        
        # Salva a matriz NCD
        output_matrix_path = os.path.join(temp_dir, "ncd_matrix.csv")
        np.savetxt(output_matrix_path, ncd_matrix, delimiter=",", fmt="%.6f")
        logger.info(f"Matriz NCD salva em: {output_matrix_path}")
        
        # Salva os rótulos
        labels_path = os.path.join(temp_dir, "labels.txt")
        with open(labels_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(labels))
        logger.info(f"Rótulos salvos em: {labels_path}")
        
        return ncd_matrix, labels
        
    except Exception as e:
        logger.error(f"Erro ao gerar matriz NCD: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Remove o diretório temporário se for o caso
        if is_temp and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Diretório temporário removido: {temp_dir}")
            except Exception as e:
                logger.warning(f"Não foi possível remover o diretório temporário {temp_dir}: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    # Configuração dos argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Pipeline FS-OPA para análise de dados')
    parser.add_argument('--input', type=str, required=True, help='Caminho para o arquivo CSV de entrada')
    parser.add_argument('--ncd-mode', action='store_true', help='Modo de geração de matriz NCD a partir de múltiplos arquivos')
    parser.add_argument('--compressor', type=str, default='gzip', choices=['gzip', 'bzip2', 'lzma'], 
                       help='Algoritmo de compressão para NCD (padrão: gzip)')
    parser.add_argument('--jobs', type=int, default=4, help='Número de trabalhos paralelos para NCD')
    parser.add_argument('--notebook-mode', action='store_true', help='Modo notebook para ambientes Jupyter')
    args = parser.parse_args()
    
    # ==============================================
    # 1. Módulo: Processamento Inicial
    # ==============================================
    print("\n" + "="*50)
    print("1. PROCESSAMENTO INICIAL")
    print("="*50)
    
    # Verifica se está no modo NCD
    if args.ncd_mode:
        print("\n[INFO] Modo NCD ativado. Gerando matriz de distância NCD...")
        try:
            # Gera a matriz NCD
            ncd_matrix, labels = generate_ncd_matrix_damicore(
                input_dir=args.input,
                compressor=args.compressor,
                max_workers=args.jobs
            )
            
            print("\n[SUCESSO] Matriz NCD gerada com sucesso!")
            print(f"Dimensões: {ncd_matrix.shape}")
            print(f"Rótulos: {', '.join(labels)}")
            
            # Visualiza a árvore de consenso
            print("\n[INFO] Gerando visualização da árvore de consenso...")
            result = visualize_consensus_trees(ncd_matrix, labels)
            
            if result and 'arquivos_gerados' in result:
                print("\nArquivos gerados:")
                for tipo, caminho in result['arquivos_gerados'].items():
                    print(f"- {tipo.replace('_', ' ').title()}: {caminho}")
            
            return
            
        except Exception as e:
            print(f"\n[ERRO] Falha ao gerar matriz NCD: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Modo normal (análise de um único arquivo CSV)
    # ==============================================
    # 1.1 Leitura do arquivo CSV
    print("\n[INFO] Lendo arquivo de entrada...")
    try:
        # Usa o caminho completo para o arquivo
        import os
        input_path = os.path.abspath(args.input)
        
        # Verifica se o arquivo existe
        if not os.path.exists(input_path):
            print(f"\n[ERRO] Arquivo não encontrado: {input_path}")
            print("   - Verifique se o caminho do arquivo está correto")
            print("   - Certifique-se de usar barras duplas ou barras invertidas duplas no caminho")
            print(f"   - Você está executando o script de: {os.getcwd()}")
            print("\nExemplo de uso:")
            print(f"   python {os.path.basename(__file__)} --input exemplo_dados.csv")
            
            # Verifica se o arquivo de exemplo existe
            exemplo_path = os.path.join(os.path.dirname(__file__), 'exemplo_dados.csv')
            if os.path.exists(exemplo_path):
                print(f"\n[SUGESTÃO] O arquivo de exemplo 'exemplo_dados.csv' foi encontrado.")
                print(f"   Você pode usá-lo como entrada com: --input exemplo_dados.csv")
            
            sys.exit(1)
            
        # Tenta ler com latin1 (que é mais permissivo)
        try:
            df = pd.read_csv(input_path, encoding='latin1')
        except Exception as e:
            print(f"[ERRO] Falha ao ler o arquivo com codificação latin1: {str(e)}")
            sys.exit(1)
        
        # Verifica se o DataFrame foi criado corretamente
        if df is None or df.empty:
            print("[ERRO] Não foi possível ler o arquivo ou o arquivo está vazio.")
            sys.exit(1)
                
        print(f"   - Arquivo: {os.path.basename(input_path)}")
        print(f"   - Caminho: {input_path}")
        print(f"   - Total de registros: {len(df):,} linhas x {len(df.columns)} colunas")
        
        # 1.2 Exibe informações básicas sobre os dados
        print("\n[INFO] Resumo do dataset:")
        print(f"   - Dimensões: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
        
        # Conta os tipos de dados
        print("   - Tipos de dados:")
        for dtype, count in df.dtypes.value_counts().items():
            print(f"     - {dtype}: {count} colunas")
        
    except Exception as e:
        print(f"[ERRO] Erro ao processar o arquivo de entrada: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ==============================================
    # 2. Módulo: Árvore de Consenso (NCD)
    # ==============================================
    print("\n\n" + "="*50)
    print("2. ÁRVORE DE CONSENSO (NCD)")
    print("="*50)
    
    print("\n🔍 Calculando matriz de distância NCD...")
    from ncd_matrix import ncd_matrix_from_dataframe
    
    try:
        # Calcula a matriz de distância NCD
        ncd_mat, labels = ncd_matrix_from_dataframe(df, notebook_mode=args.notebook_mode)
        
        # Exibe a matriz de distância (apenas se não for muito grande)
        if len(ncd_mat) <= 10:
            print("\n📊 Matriz de distância NCD:")
            ncd_df = pd.DataFrame(ncd_mat, columns=labels, index=labels)
            print(ncd_df.to_string())
        else:
            print(f"\n📊 Matriz de distância NCD gerada com dimensões {ncd_mat.shape}")
        
        # Gera as visualizações da árvore de consenso
        print("\n🌳 Gerando visualizações da árvore de consenso...")
        viz_paths = visualize_consensus_trees(ncd_mat, labels)
        
        if not viz_paths:
            print("\n⚠️  Não foi possível gerar as visualizações. Verifique os logs para mais detalhes.")
        
        print("\n✅ Análise concluída com sucesso!")
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante o processamento NCD: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ==============================================
    # 3. Módulos desativados (simplificação do pipeline)
    # ==============================================
    print("\n\n" + "="*50)
    print("3. MÓDULOS DESATIVADOS")
    print("="*50)
    print("\n[INFO] Os seguintes módulos foram desativados para simplificação do pipeline:")
    print("   - Seleção de Critérios para Split (FS-OPA)")
    print("   - Geração de Árvores de Decisão")
    print("   - Análise de Pareto")
    print("\n[INFO] Para ativar esses módulos, consulte a documentação.")
    
    print("\n🎉 Pipeline simplificado concluído com sucesso!")

def extrair_suportes(arvore):
    """
    Extrai e valida os valores de suporte dos nós internos de uma árvore.
    
    Args:
        arvore: Objeto de árvore do toytree
        
    Returns:
        tuple: (dicionário de {índice_do_nó: valor_suporte}, estatísticas)
    """
    suportes = {}
    estatisticas = {
        'total_nos_internos': 0,
        'nos_com_suporte': 0,
        'valores_unicos': set(),
        'fontes_suporte': {}
    }
    
    # Contadores para diferentes fontes de suporte
    fontes = {
        'atributo_support': 0,
        'features': 0,
        'nome_do_no': 0,
        'outros_atributos': 0
    }
    
    # Percorre todos os nós da árvore
    for idx, no in enumerate(arvore.treenode.traverse()):
        if no.is_leaf():
            continue
            
        estatisticas['total_nos_internos'] += 1
        suporte = None
        fonte = None
        
        # 1. Tenta obter do atributo 'support' direto
        if hasattr(no, 'support') and no.support is not None:
            try:
                suporte = float(no.support)
                fonte = 'atributo_support'
                fontes['atributo_support'] += 1
            except (ValueError, TypeError):
                pass
                
        # 2. Tenta obter dos features do nó (se disponível)
        if suporte is None and hasattr(no, 'features') and 'support' in no.features:
            try:
                suporte = float(no.features['support'])
                fonte = 'features'
                fontes['features'] += 1
            except (ValueError, TypeError, KeyError):
                pass
                
        # 3. Tenta extrair do nome do nó (padrão comum: (0.95) ou [0.95])
        if suporte is None and hasattr(no, 'name') and no.name:
            import re
            match = re.search(r'[\(\[\{]([0-9]*\.?[0-9]+)[\)\]\}]', str(no.name))
            if match:
                try:
                    suporte = float(match.group(1))
                    fonte = 'nome_do_no'
                    fontes['nome_do_no'] += 1
                except (ValueError, TypeError):
                    pass
                    
        # 4. Tenta outros atributos comuns
        if suporte is None:
            for attr in ['confidence', 'bootstrap', 'posterior', 'prob']:
                if hasattr(no, attr) and getattr(no, attr) is not None:
                    try:
                        suporte = float(getattr(no, attr))
                        fonte = f'atributo_{attr}'
                        fontes['outros_atributos'] += 1
                        break
                    except (ValueError, TypeError):
                        continue
        
        # Se encontrou um valor de suporte válido
        if suporte is not None and fonte is not None:
            suportes[idx] = suporte
            estatisticas['valores_unicos'].add(round(suporte, 4))
            estatisticas['fontes_suporte'][fonte] = estatisticas['fontes_suporte'].get(fonte, 0) + 1
            estatisticas['nos_com_suporte'] += 1
    
    # Calcula estatísticas adicionais
    if suportes:
        valores = list(suportes.values())
        estatisticas.update({
            'media': sum(valores) / len(valores),
            'minimo': min(valores),
            'maximo': max(valores),
            'desvio_padrao': (sum((x - (sum(valores) / len(valores))) ** 2 for x in valores) / len(valores)) ** 0.5 if len(valores) > 1 else 0,
            'fontes': fontes
        })
    
    return suportes, estatisticas

def obter_estilo_arvore(arvore, suportes=None):
    """
    Retorna um dicionário com os estilos para desenhar a árvore.
    
    Args:
        arvore: Objeto de árvore do toytree
        suportes: Dicionário com os valores de suporte por índice de nó
        
    Returns:
        dict: Dicionário com os estilos
    """
    # Estilo base
    estilo = {
        'layout': 'rectangular',
        'edge_type': 'p',
        'width': 1200,
        'height': 800,
        'tip_labels': True,
        'node_sizes': 12,
        'node_colors': '#1f77b4',
        'use_edge_lengths': False,
        'node_style': {
            'stroke': '#2c3e50',
            'stroke-width': 1.5,
            'stroke-opacity': 0.8
        }
    }
    
    # Se houver suportes, adiciona estilos para exibi-los
    if suportes:
        estilo.update({
            'node_labels': "support",
            'node_labels_style': {
                'font-size': '10px',
                'font-weight': 'bold',
                'fill': '#e74c3c',
                'text-anchor': 'middle',
                'paint-order': 'stroke',
                'stroke': '#ffffff',
                'stroke-width': '3px',
                'stroke-linecap': 'butt',
                'stroke-linejoin': 'miter',
                'stroke-opacity': 0.8
            }
        })
    
    return estilo

def salvar_arvore_svg(arvore, caminho, estilo=None, tentativas=3):
    """
    Salva a árvore em um arquivo SVG com tratamento de erros robusto.
    
    Args:
        arvore: Objeto de árvore do toytree
        caminho: Caminho para salvar o arquivo SVG
        estilo: Dicionário com estilos para desenhar a árvore
        tentativas: Número de tentativas em caso de falha
        
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    import os
    import toyplot.svg
    from datetime import datetime
    
    if estilo is None:
        estilo = obter_estilo_arvore(arvore)
    
    # Garante que o diretório de saída existe
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    
    # Tenta salvar com diferentes abordagens
    for tentativa in range(1, tentativas + 1):
        try:
            # Abordagem 1: Usar o método draw padrão
            if tentativa == 1:
                canvas, axes, mark = arvore.draw(**estilo)
                toyplot.svg.render(canvas, caminho)
                return True
                
            # Abordagem 2: Usar configurações mínimas
            elif tentativa == 2:
                estilo_minimo = {
                    'layout': 'rectangular',
                    'tip_labels': True,
                    'node_sizes': 12,
                    'use_edge_lengths': False
                }
                canvas, axes, mark = arvore.draw(**estilo_minimo)
                toyplot.svg.render(canvas, caminho)
                return True
                
            # Abordagem 3: Usar to_svg() diretamente
            elif tentativa == 3:
                svg_content = arvore.draw(
                    width=1200,
                    height=1000,
                    layout='rectangular',
                    edge_type='p',
                    scale_bar=False,
                    tip_labels=True,
                    node_sizes=12,
                    node_colors='#1f77b4',
                    use_edge_lengths=False
                ).to_svg()
                
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                return True
                
        except Exception as e:
            print(f"⚠️  Tentativa {tentativa} falhou: {str(e)}")
            if tentativa == tentativas:
                print("❌ Todas as tentativas de salvar a árvore falharam.")
                return False
            continue
            
    return False

def visualizar_arvore_consenso(newick_strings, labels, outgroup_index=0):
    """
    Gera visualizações da árvore de consenso seguindo o fluxo:
    1. Junta múltiplas strings Newick
    2. Cria mtree com toytree
    3. Gera cloud tree
    4. Obtém e enraiza a árvore de consenso
    5. Visualiza com Biopython
    
    Esta função foi aprimorada para fornecer uma extração mais robusta dos valores de suporte
    dos nós internos, com melhor tratamento de erros e visualização.
    
    Args:
        newick_strings: Lista de strings no formato Newick
        labels: Lista de rótulos para as folhas da árvore
        outgroup_index: Índice do nó a ser usado como outgroup (padrão: 0)
        
    Returns:
        dict: Dicionário com os caminhos dos arquivos gerados e objetos das visualizações
    """
    import os
    import tempfile
    from io import StringIO
    from Bio import Phylo
    import toytree
    import toyplot
    import sys
    import traceback
    
    # Inicializa o dicionário de resultados
    result = {
        'arquivos_gerados': {},
        'visualizacoes': {}
    }
    
    try:
        # 1. Cria um diretório temporário para salvar as imagens
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Diretório temporário para visualizações: {temp_dir}")
        
        # 2. Junta as árvores Newick em uma única string
        print("\n🌿 Processando árvores Newick...")
        newick_combined = "\n".join(newick_strings)
        
        # 3. Cria o objeto mtree com toytree
        print("🌳 Criando árvore múltipla (mtree) com toytree...")
        try:
            mtree = toytree.mtree(newick_combined)
            
            # 4. Gera a visualização da árvore de nuvem
            print("\n☁️  Gerando visualização 1/3: Árvore de nuvem...")
            try:
                cloud_path = os.path.join(temp_dir, "arvore_nuvem.png")
                
                # Usa o método draw_cloud_tree para criar uma visualização de nuvem de árvores
                # Este método é ideal para visualizar múltiplas árvores simultaneamente
                # Desenhar uma nuvem de árvores
              
                canvas, axes, mark = mtree.draw_cloud_tree(
                    width=1200,  # Largura maior para melhor visualização
                    height=1000,  # Altura adequada para a visualização
                    tip_labels_style={
                        'font-size': '10px',  # Tamanho da fonte ajustável
                        'font-weight': 'normal',
                        'fill': '#333333'  # Cor do texto escuro para melhor contraste
                    },
                    node_sizes=6,  # Tamanho dos nós reduzido para melhor visualização
                    node_colors='#2ecc71',  # Cor verde para os nós
                    edge_colors='#7f8c8d',  # Cor cinza para as arestas
                    edge_widths=1.2,  # Largura das arestas
                    tip_labels_align=True,  # Alinhar rótulos das pontas
                    scale_bar=False  # Remove a barra de escala para maior clareza
                )
                
                # Adiciona um título à visualização
                # Usando toyplot.text para adicionar o título diretamente ao canvas
                # Posicionando o título acima da visualização
                canvas.text(
                    canvas.width / 2,  # Centralizado horizontalmente
                    30,  # 30 pixels do topo
                    "Árvore Filogenética",
                    style={
                        'font-size': '16px',
                        'font-weight': 'bold',
                        'text-anchor': 'middle',
                        'fill': '#000000'
                    }
                )
                
                # Salva a imagem em SVG (não requer Ghostscript)
                cloud_path = cloud_path.replace('.png', '.svg')
                import toyplot.svg
                toyplot.svg.render(canvas, cloud_path)
                result['arquivos_gerados']['arvore_nuvem'] = cloud_path
                result['visualizacoes']['cloud_tree'] = canvas
                print(f"   ✅ Árvore de nuvem salva em: {cloud_path}")
                
            except Exception as e:
                print(f"   ⚠️  Erro ao gerar árvore de nuvem: {str(e)}")
                traceback.print_exc()
            
            # 5. Gera a árvore de consenso
            print("\n🌳 Gerando visualização 2/3: Árvore de consenso...")
            try:
                consenso_path = os.path.join(temp_dir, "arvore_consenso.png")
                
                # Obtém a árvore de consenso com suporte
                print("\n🔍 Obtendo árvore de consenso...")
                
                # Verifica se há árvores suficientes para gerar um consenso
                if len(mtree.treelist) < 2:
                    print("⚠️ Aviso: É necessário pelo menos 2 árvores para gerar um consenso!")
                    print(f"  Número de árvores fornecidas: {len(mtree.treelist)}")
                    print("  Retornando a primeira árvore como consenso...")
                    ctre = mtree.treelist[0].copy()
                    
                    # Adiciona suporte padrão de 100% a todos os nós internos
                    for node in ctre.treenode.traverse():
                        if not node.is_leaf() and not hasattr(node, 'support'):
                            node.support = 1.0
                else:
                    print(f"  Gerando árvore de consenso a partir de {len(mtree.treelist)} árvores...")
                    
                    # Verifica se as árvores de entrada têm topologias diferentes
                    topologias_unicas = set()
                    topologias_por_arvore = []
                    
                    for tree in mtree.treelist:
                        topologia = []
                        for node in tree.treenode.traverse():
                            if not node.is_leaf():
                                # Ordena os nomes das folhas para garantir consistência
                                folhas = sorted(node.get_leaf_names())
                                topologia.append(tuple(folhas))
                        
                        # Ordena a topologia para garantir consistência
                        topologia_ordenada = tuple(sorted(topologia))
                        topologias_unicas.add(topologia_ordenada)
                        topologias_por_arvore.append(topologia_ordenada)
                    
                    print(f"  Número de topologias únicas encontradas: {len(topologias_unicas)}")
                    
                    # Calcula a similaridade entre as topologias
                    similaridades = []
                    for i in range(len(topologias_por_arvore)):
                        for j in range(i+1, len(topologias_por_arvore)):
                            set_i = set(topologias_por_arvore[i])
                            set_j = set(topologias_por_arvore[j])
                            intersecao = len(set_i.intersection(set_j))
                            uniao = len(set_i.union(set_j))
                            similaridade = intersecao / uniao if uniao > 0 else 0.0
                            similaridades.append(similaridade)
                    
                    if similaridades:
                        media_similaridade = sum(similaridades) / len(similaridades)
                        print(f"  Similaridade média entre as topologias: {media_similaridade:.2f}")
                        if media_similaridade > 0.9:
                            print("⚠️  AVISO: As árvores de entrada são muito semelhantes!")
                            print("  Isso pode resultar em valores de suporte altos e pouco informativos.")
                    
                    if len(topologias_unicas) == 1:
                        print("⚠️  AVISO: Todas as árvores de entrada têm a mesma topologia!")
                        print("  Isso resultará em valores de suporte iguais para todos os nós internos.")
                        print("  Considere usar árvores com topologias diferentes para obter suportes variados.")
                    
                    # Gera a árvore de consenso com suporte
                    print("  Gerando árvore de consenso...")
                    ctre = mtree.get_consensus_tree()
                    
                    # Verifica se a árvore de consenso foi gerada corretamente
                    if ctre is None:
                        raise ValueError("Falha ao gerar a árvore de consenso. Retornando None.")
                    
                    print(f"  ✅ Árvore de consenso gerada com sucesso!")
                    print(f"  Número de folhas: {ctre.ntips}")
                    print(f"  Número total de nós: {ctre.nnodes}")
                    print(f"  Número de nós internos: {ctre.nnodes - ctre.ntips}")
            
                # Verifica se a árvore de consenso foi gerada corretamente
                if ctre is None:
                    raise ValueError("❌ Falha ao gerar a árvore de consenso!")
                
                print(f"  ✅ Árvore de consenso gerada com sucesso!")
                print(f"  Número de folhas: {ctre.ntips}")
                print(f"  Número total de nós: {ctre.nnodes}")
                
                # Verifica se a árvore tem nós internos
                if ctre.nnodes - ctre.ntips == 0:
                    print("⚠️ Aviso: A árvore de consenso não possui nós internos!")
                    print("  Verifique se as árvores de entrada têm topologias diferentes.")
                
                # Verifica se há valores de suporte nos nós internos
                has_support = False
                support_values = []
                for node in ctre.treenode.traverse():
                    if not node.is_leaf():
                        if hasattr(node, 'support') and node.support is not None:
                            has_support = True
                            support_values.append(node.support)
                
                if not has_support:
                    print("⚠️ Aviso: Nenhum valor de suporte encontrado nos nós internos da árvore de consenso!")
                    print("  Verifique se as árvores de entrada têm valores de suporte.")
                else:
                    print(f"  ✅ Valores de suporte encontrados em {len(support_values)} nós internos.")
                    if support_values:
                        print(f"  Média dos suportes: {sum(support_values)/len(support_values):.4f}")
                        print(f"  Mínimo: {min(support_values):.4f}, Máximo: {max(support_values):.4f}")
                        
                        # Verifica se todos os suportes são iguais
                        if len(set(round(s, 4) for s in support_values)) == 1:
                            print("⚠️  AVISO: Todos os nós internos têm o mesmo valor de suporte!")
                            print("  Isso pode indicar que as árvores de entrada têm a mesma topologia.")
                
                # Obtém os rótulos das folhas
                tip_labels = ctre.get_tip_labels()
                print(f"  Rótulos das folhas: {', '.join(tip_labels[:5])}{'...' if len(tip_labels) > 5 else ''}")
                
                # Verifica se o outgroup está presente nas folhas
                if outgroup_index < len(tip_labels):
                    outgroup = tip_labels[outgroup_index]
                    if outgroup not in tip_labels:
                        print(f"⚠️ Aviso: O outgroup '{outgroup}' não foi encontrado nas folhas da árvore!")
                        print(f"  Folhas disponíveis: {', '.join(tip_labels[:5])}{'...' if len(tip_labels) > 5 else ''}")
                        print(f"  Usando a primeira folha como outgroup: {tip_labels[0]}")
                        outgroup_index = 0
                
                # Define o outgroup
                if outgroup_index < len(tip_labels):
                    outgroup = tip_labels[outgroup_index]
                    print(f"🌱 Enraizando a árvore no outgroup: {outgroup}")
                    ctre = ctre.root(outgroup)
                
                # Configura os estilos para os nós internos
                node_sizes = [12 if i < ctre.ntips else 30 for i in range(ctre.nnodes)]
                node_colors = ["#2ecc71" if i < ctre.ntips else "#e74c3c" for i in range(ctre.nnodes)]
                
                # Obtém os valores de suporte dos nós internos e formata como porcentagem
                print("📊 Extraindo valores de suporte dos nós internos...")
                node_supports = {}
                
                # Primeiro, verifica se os nós têm o atributo 'support' e imprime para depuração
                print("\n🔍 Valores de suporte brutos dos nós internos:")
                
                # Obtém a lista de nós internos (não-folhas)
                internal_nodes = [node for node in ctre.treenode.traverse() if not node.is_leaf()]
                
                # Se não houver nós internos, não há o que fazer
                if not internal_nodes:
                    print("  ⚠️ Nenhum nó interno encontrado na árvore!")
                    return None
                
                # Verifica se há suportes nos nós internos
                has_support = any(hasattr(node, 'support') for node in internal_nodes)
                
                if not has_support:
                    print("  ℹ️ Nenhum valor de suporte encontrado nos nós internos.")
                    print("  ℹ️ Usando valores de suporte padrão (100%) para todos os nós internos.")
                    
                    # Atribui 100% de suporte a todos os nós internos
                    for node in internal_nodes:
                        node_supports[node.idx] = 1.0
                        print(f"  Nó {node.idx} - Suporte padrão: 1.0 (100%)")
                else:
                    # Processa os suportes dos nós internos
                    for node in internal_nodes:
                        # Tenta obter o valor de suporte de diferentes fontes
                        support_value = None
                        
                        # 1. Tenta obter do atributo 'support' direto
                        if hasattr(node, 'support') and node.support is not None:
                            support_value = node.support
                        # 2. Tenta obter do dicionário de features
                        elif hasattr(node, 'features') and 'support' in node.features:
                            support_value = node.features['support']
                        # 3. Tenta obter do dicionário de atributos
                        elif hasattr(node, 'up') and hasattr(node.up, 'features') and 'support' in node.up.features:
                            support_value = node.up.features['support']
                        
                        # Se encontrou algum valor de suporte
                        if support_value is not None:
                            try:
                                # Converte para float e normaliza para 0-1
                                support_float = float(support_value)
                                if support_float > 1.0:  # Se estiver em formato de porcentagem (0-100)
                                    support_float = support_float / 100.0
                                elif support_float < 0:  # Garante que não seja negativo
                                    support_float = 0.0
                                elif support_float > 1.0:  # Garante que não seja maior que 1.0
                                    support_float = 1.0
                                    
                                node_supports[node.idx] = support_float
                                print(f"  Nó {node.idx} - Suporte processado: {support_float:.4f} ({support_float*100:.1f}%)")
                                
                            except (ValueError, TypeError) as e:
                                print(f"  ⚠️ Erro ao processar suporte do nó {node.idx}: {e}")
                                node_supports[node.idx] = 1.0  # Valor padrão em caso de erro
                        else:
                            # Se não encontrou suporte, usa 1.0 (100%)
                            node_supports[node.idx] = 1.0
                            print(f"  Nó {node.idx} - Sem suporte, usando valor padrão: 1.0 (100%)")
                
                # Se não encontrou nenhum suporte, usa 100% para todos os nós
                if not node_supports and internal_nodes:
                    print("  ℹ️ Nenhum valor de suporte válido encontrado. Usando 100% para todos os nós.")
                    for node in internal_nodes:
                        node_supports[node.idx] = 1.0
                
                # Configura os rótulos dos nós com os valores de suporte formatados
                print("\n📝 Configurando rótulos dos nós com valores de suporte...")
                node_labels = {}
                
                # Verifica se há suportes válidos para os nós internos
                if not node_supports:
                    print("⚠️ Aviso: Nenhum valor de suporte encontrado para os nós internos!")
                    print("   Verifique se as árvores de entrada têm valores de suporte.")
                    print("   Usando valores de suporte padrão (100%) para todos os nós.")
                    for node in ctre.treenode.traverse():
                        if not node.is_leaf():
                            node_labels[node.idx] = "100%"
                            node_colors[node.idx] = "#2ecc71"  # Verde para suporte alto
                else:
                    # Se houver suportes, formata-os adequadamente
                    for node in ctre.treenode.traverse():
                        if not node.is_leaf() and node.idx in node_supports:
                            # Obtém o valor de suporte já processado
                            support_value = node_supports[node.idx]
                            
                            # Converte para porcentagem (0-100)
                            support_percent = support_value * 100
                            
                            # Formatação condicional baseada no valor de suporte
                            if support_percent < 50:
                                # Suporte muito baixo (vermelho)
                                node_labels[node.idx] = f"{support_percent:.1f}%"
                                node_colors[node.idx] = "#e74c3c"  # Vermelho
                                # print(f"  Nó {node.idx} - Suporte muito baixo: {support_percent:.1f}%")
                            elif support_percent < 70:
                                # Suporte baixo (amarelo)
                                node_labels[node.idx] = f"{support_percent:.1f}%"
                                node_colors[node.idx] = "#f1c40f"  # Amarelo
                                # print(f"  Nó {node.idx} - Suporte baixo: {support_percent:.1f}%")
                            elif support_percent < 90:
                                # Suporte médio (laranja)
                                node_labels[node.idx] = f"{support_percent:.0f}%"
                                node_colors[node.idx] = "#e67e22"  # Laranja
                                # print(f"  Nó {node.idx} - Suporte médio: {support_percent:.0f}%")
                            else:
                                # Suporte alto (verde)
                                node_labels[node.idx] = f"{support_percent:.0f}%"
                                node_colors[node.idx] = "#2ecc71"  # Verde
                                # print(f"  Nó {node.idx} - Suporte alto: {support_percent:.0f}%")
                
                # Log final dos rótulos configurados (comentado conforme solicitado)
                # if node_labels:
                #     print(f"\n✅ Configurados rótulos para {len(node_labels)} nós internos.")
                # else:
                #     print("⚠️ Nenhum rótulo de nó interno foi configurado.")
                
                # Se não houver nós internos com suporte, adiciona um aviso ao log
                if not node_labels:
                    print("⚠️ Aviso: Nenhum nó interno encontrado com valores de suporte válidos!")
                    print("   A árvore será exibida sem valores de suporte.")
                
                # Verificação final dos valores de suporte antes de desenhar (comentado conforme solicitado)
                # print("\n🔍 Verificação final dos valores de suporte:")
                # print(f"  Total de nós internos: {ctre.nnodes - ctre.ntips}")
                # print(f"  Nós com suporte definido: {len(node_labels)}/{ctre.nnodes - ctre.ntips}")
                
                # Se não houver suportes, tenta extrair de outra forma (comentado conforme solicitado)
                if not node_labels and hasattr(ctre, 'get_node_data'):
                    # print("  ⚠️ Tentando extrair suportes alternativamente...")
                    node_data = ctre.get_node_data()
                    for idx, node in node_data.iterrows():
                        if not node['is_leaf'] and 'support' in node:
                            support = node['support']
                            if pd.notna(support):
                                support_percent = support * 100
                                node_labels[idx] = f"{support_percent:.0f}%"
                                # print(f"  Nó {idx} - Suporte alternativo: {support_percent:.1f}%")
                
                # Se ainda não houver suportes, adiciona um aviso ao log (mantido apenas o aviso principal)
                if not node_labels:
                    print("  ⚠️ Não foi possível extrair valores de suporte. A árvore será desenhada sem eles.")
                # else:
                #     print(f"  ✅ Valores de suporte configurados para {len(node_labels)} nós internos.")
                
                # Desenha a árvore com suporte nos nós internos
                # print("\n🎨 Desenhando a árvore de consenso...")
                
                # Prepara os argumentos para o desenho
                draw_args = {
                    'tip_labels': labels if len(labels) == len(tip_labels) else tip_labels,
                    'node_sizes': node_sizes,
                    'node_colors': node_colors,
                    'node_style': {
                        "stroke": "#2c3e50",  # Azul escuro para contorno
                        "stroke-width": 1.5,
                        "stroke-opacity": 0.8
                    },
                    'node_labels_style': {
                        "font-size": "10px",
                        "font-weight": "bold",
                        "fill": "white",
                        "paint-order": "stroke",
                        "stroke": "#2c3e50",
                        "stroke-width": "3px",
                        "stroke-linecap": "butt",
                        "stroke-linejoin": "miter",
                        "stroke-opacity": 0.8
                    },
                    'use_edge_lengths': False,
                    'width': 1200,
                }
                
                # Cria a máscara de nós internos e prepara os rótulos
                try:
                    # print("\n🔍 Preparando máscara de nós e rótulos...")
                    
                    # Obtém todos os nós da árvore
                    all_nodes = list(ctre.treenode.traverse())
                    
                    # Obtém as folhas (nós sem filhos)
                    leaves = [node for node in all_nodes if node.is_leaf()]
                    n_leafs = len(leaves)
                    n_nodes = len(all_nodes)
                    
                    # print(f"  - Total de nós na árvore: {n_nodes}")
                    # print(f"  - Número de folhas: {n_leafs}")
                    # print(f"  - Número de nós internos esperado: {n_nodes - n_leafs}")
                    # print(f"  - Número de rótulos fornecidos: {len(node_labels) if node_labels else 0}")
                    
                    # Inicializa as listas
                    node_mask = []
                    node_labels_final = [""] * n_nodes  # Inicializa com strings vazias
                    
                    # Contador para índices dos nós internos
                    internal_node_idx = 0
                    
                    # Preenche a máscara e os rótulos
                    for i, node in enumerate(all_nodes):
                        is_leaf = node.is_leaf()
                        node_mask.append(not is_leaf)
                        
                        # Se for nó interno, tenta adicionar o rótulo
                        if not is_leaf and node_labels and internal_node_idx < len(node_labels):
                            node_labels_final[i] = node_labels[internal_node_idx]
                            internal_node_idx += 1
                    
                    # Verificação final (comentada conforme solicitado)
                    # n_internal = sum(node_mask)
                    # n_labels = len([x for x in node_labels_final if x])
                    # 
                    # print(f"  - Nós internos encontrados: {n_internal}")
                    # print(f"  - Rótulos atribuídos: {n_labels}")
                    # 
                    # if n_labels == 0:
                    #     print("  ⚠️ Nenhum rótulo de nó interno foi atribuído!")
                    
                    # Atualiza os argumentos de desenho
                    draw_args['node_mask'] = node_mask
                    draw_args['node_labels'] = node_labels_final
                    
                except Exception as e:
                    print(f"  ❌ Erro ao preparar máscara e rótulos: {str(e)}")
                    print("  ⚠️ Continuando sem máscara de nós e rótulos...")
                    # Remove as chaves problemáticas para evitar erros
                    draw_args.pop('node_mask', None)
                    draw_args.pop('node_labels', None)
                
                # Configurações de desenho otimizadas para exibir todas as 39 colunas
                draw_args = {
                    'layout': 'rectangular',  # Layout retangular
                    'edge_type': 'p',         # Linhas retas
                    'scale_bar': False,       # Remove a barra de escala
                    'width': 1600,            # Largura maior para acomodar todas as colunas
                    'height': 1000,           # Altura maior para melhor visualização
                    'tip_labels': True,       # Mostra rótulos das folhas
                    'node_sizes': 16,         # Tamanho dos nós (aumentado para melhor visibilidade)
                    'node_colors': '#1f77b4', # Cor dos nós
                    'use_edge_lengths': False, # Desativa comprimentos de aresta
                    'tip_labels_align': True,  # Alinha os rótulos das folhas
                    'tip_labels_style': {
                        'font-size': '10px',  # Tamanho da fonte ajustado
                        'font-weight': 'normal',
                        'fill': '#333333'  # Cor do texto escuro para melhor contraste
                    },
                    'node_labels': 'support',  # Mostra valores de suporte nos nós internos
                    'node_labels_style': {
                        'font-size': '10px',
                        'font-weight': 'bold',
                        'fill': '#e74c3c',  # Cor vermelha para os valores de suporte
                        'text-anchor': 'middle'
                    }
                }
                
                # Configura os valores de suporte
                try:
                    # Tenta extrair os valores de suporte dos nós internos
                    supports = []
                    for node in ctre.treenode.traverse():
                        if not node.is_leaf():
                            if hasattr(node, 'support') and node.support is not None:
                                try:
                                    support_val = float(node.support)
                                    supports.append(support_val)
                                    node.support = support_val
                                except (ValueError, TypeError):
                                    node.support = 1.0  # Valor padrão se não for possível converter
                                    supports.append(1.0)
                            else:
                                # Se não tiver suporte, não define um valor padrão
                                # Isso fará com que o toytree use sua lógica interna
                                pass
                    
                    # Se encontrou suportes, adiciona ao draw_args
                    if supports:
                        draw_args['node_labels'] = "support"
                        draw_args['node_labels_style'] = {
                            'font-size': '10',  # Sem unidade para evitar problemas
                            'fill': '#e74c3c',
                            'text-anchor': 'middle',
                            'font-weight': 'bold'
                        }
                        
                        # Adiciona informações de suporte ao resultado
                        result['suporte_estatisticas'] = {
                            'media': float(np.mean(supports)) if supports else 0,
                            'minimo': float(np.min(supports)) if supports else 0,
                            'maximo': float(np.max(supports)) if supports else 0,
                            'desvio_padrao': float(np.std(supports)) if len(supports) > 1 else 0,
                            'total_nos': len(supports)
                        }
                        
                except Exception as e:
                    print(f"⚠️  Aviso ao processar valores de suporte: {str(e)}")
                    # Remove a referência a node_labels para evitar erros
                    draw_args.pop('node_labels', None)
                    draw_args.pop('node_labels_style', None)
                # Desenha a árvore com tratamento de erros robusto
                print("\n🎨 Renderizando a árvore de consenso...")
                try:
                    # Tenta desenhar a árvore com os argumentos fornecidos
                    try:
                        canvas, axes, mark = ctre.draw(**draw_args)
                        print("✅ Árvore de consenso renderizada com sucesso!")
                        
                        # Ajusta o layout para garantir que todas as dicas sejam visíveis
                        if hasattr(axes, 'show'):
                            axes.show = True
                            
                        # Ajusta o tamanho da fonte das dicas se necessário
                        if hasattr(axes, 'text'):
                            for text in axes.text:
                                if hasattr(text, 'style'):
                                    text.style['font-size'] = '10px'
                                    
                    except Exception as e:
                        print(f"⚠️ Erro ao desenhar a árvore: {str(e)}")
                        print("Tentando com configurações alternativas...")
                        
                        # Tenta com configurações mais simples
                        try:
                            canvas, axes, mark = ctre.draw(
                                tip_labels=True,
                                node_labels='support',
                                use_edge_lengths=False,
                                node_sizes=16,
                                width=1600,
                                height=1000
                            )
                            print("✅ Árvore de consenso renderizada com configurações alternativas!")
                        except Exception as alt_error:
                            print(f"❌ Falha ao desenhar a árvore: {str(alt_error)}")
                            return result
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    print(f"❌ Erro ao desenhar a árvore de consenso: {error_msg}")
                    
                    # Verifica se o erro está relacionado a estilos ou formatação
                    if any(term in error_msg for term in ['style', 'font', 'size', 'color']):
                        print("⚠️  Problema detectado nos estilos. Tentando com configurações simplificadas...")
                        
                        # Tenta novamente com configurações mínimas
                        try:
                            # Configurações mínimas sem estilos complexos
                            minimal_args = {
                                'layout': 'rectangular',
                                'edge_type': 'p',
                                'node_align': True,
                                'width': 1200,
                                'height': 1000,
                                'tip_labels': True,
                                'node_labels': "support",
                                'node_sizes': 24,
                                'node_colors': '#1f77b4',
                                'use_edge_lengths': False
                            }
                            
                            canvas, axes, mark = ctre.draw(**minimal_args)
                            print("✅ Árvore de consenso renderizada com configurações simplificadas.")
                            
                        except Exception as minimal_error:
                            print(f"❌ Falha ao desenhar com configurações mínimas: {str(minimal_error)}")
                            
                            # Última tentativa com o mínimo absoluto
                            try:
                                print("⚠️  Tentando com configuração mínima absoluta...")
                                canvas, axes, mark = ctre.draw(
                                    layout='rectangular',
                                    tip_labels=True,
                                    node_labels="support"
                                )
                                print("✅ Árvore de consenso renderizada com configuração mínima.")
                                
                            except Exception as last_error:
                                print(f"❌ Falha crítica ao desenhar a árvore: {str(last_error)}")
                                print("⚠️  Não foi possível gerar a visualização da árvore.")
                                # Adiciona informações de erro ao resultado para diagnóstico
                                result['erro_visualizacao'] = {
                                    'tipo': str(type(last_error).__name__),
                                    'mensagem': str(last_error),
                                    'traceback': traceback.format_exc()
                                }
                                return result
                    else:
                        # Se o erro não for relacionado a estilos, tenta uma abordagem diferente
                        print(f"⚠️  Erro inesperado. Tentando abordagem alternativa...")
                        try:
                            # Tenta desenhar apenas com os parâmetros essenciais
                            canvas, axes, mark = ctre.draw(
                                tip_labels=True,
                                node_labels="support",
                                node_sizes=24,
                                use_edge_lengths=False
                            )
                            print("✅ Árvore de consenso renderizada com abordagem alternativa.")
                        except:
                            # Se tudo falhar, retorna None para indicar falha
                            print("❌ Todas as tentativas de renderização falharam.")
                            return None
                
                # Verificação final dos valores de suporte
                print("\n🔍 Verificação final dos valores de suporte:")
                
                # Obtém todos os nós internos
                nos_internos = [node for node in ctre.treenode.traverse() if not node.is_leaf()]
                
                # Verifica se há valores de suporte nos nós internos
                nos_com_suporte = [node for node in nos_internos 
                                if hasattr(node, 'support') and node.support is not None]
                
                print(f"  Total de nós internos: {len(nos_internos)}")
                print(f"  Nós com suporte definido: {len(nos_com_suporte)}")
                
                # Se houver nós com suporte, exibe estatísticas detalhadas
                if nos_com_suporte:
                    suportes = [node.support for node in nos_com_suporte]
                    
                    print(f"\n📊 Estatísticas dos valores de suporte:")
                    print(f"  Média: {sum(suportes)/len(suportes):.4f}")
                    print(f"  Mínimo: {min(suportes):.4f}")
                    print(f"  Máximo: {max(suportes):.4f}")
                    
                    # Calcula o desvio padrão se houver mais de um valor
                    if len(suportes) > 1:
                        import numpy as np
                        print(f"  Desvio padrão: {np.std(suportes):.4f}")
                    
                    # Verifica se todos os suportes são iguais
                    suportes_arredondados = [round(s, 4) for s in suportes]
                    if len(set(suportes_arredondados)) == 1:
                        print("\n⚠️  AVISO: Todos os nós internos têm o mesmo valor de suporte!")
                        print(f"  Valor de suporte: {suportes[0]:.4f}")
                        print("  Isso pode indicar que:")
                        print("  1. Todas as árvores de entrada têm a mesma topologia.")
                        print("  2. O método de consenso não está preservando os valores de suporte corretamente.")
                        print("  3. As árvores de entrada não têm valores de suporte definidos.")
                
                # Se não houver suportes, tenta extrair de outra forma
                if not nos_com_suporte:
                    print("\n⚠️  Nenhum valor de suporte encontrado nos nós internos!")
                    print("  Tentando extrair suportes alternativamente...")
                    
                    # Tenta obter suportes do dicionário de features
                    if hasattr(ctre, 'get_node_data'):
                        try:
                            node_data = ctre.get_node_data()
                            if 'support' in node_data.columns:
                                supports = node_data[~node_data['is_leaf'] & node_data['support'].notna()]['support']
                                if not supports.empty:
                                    print(f"  ✅ Encontrados {len(supports)} valores de suporte alternativos!")
                                    print(f"  Média: {supports.mean():.4f}")
                                    print(f"  Mínimo: {supports.min():.4f}")
                                    print(f"  Máximo: {supports.max():.4f}")
                                    
                                    # Atualiza os valores de suporte nos nós
                                    for idx, support in supports.items():
                                        if idx < len(ctre.treenode.traverse()):
                                            node = list(ctre.treenode.traverse())[idx]
                                            if not node.is_leaf():
                                                node.support = support
                                                print(f"  Atualizado suporte do nó {idx} para {support:.4f}")
                        except Exception as e:
                            print(f"  ⚠️  Erro ao tentar extrair suportes alternativos: {str(e)}")
                
                # Verificação final antes de salvar
                print("\n🔍 Verificação final antes de salvar a árvore de consenso:")
                
                # Verifica se há valores de suporte nos nós internos
                nos_internos = [node for node in ctre.treenode.traverse() if not node.is_leaf()]
                nos_com_suporte = [node for node in nos_internos 
                                if hasattr(node, 'support') and node.support is not None]
                
                print(f"  Total de nós internos: {len(nos_internos)}")
                print(f"  Nós com suporte definido: {len(nos_com_suporte)}")
                
                # Se não houver suportes, tenta uma última abordagem para extraí-los
                if not nos_com_suporte and hasattr(ctre, 'get_node_data'):
                    print("  ⚠️  Nenhum valor de suporte encontrado. Tentando abordagem alternativa...")
                    try:
                        node_data = ctre.get_node_data()
                        if 'support' in node_data.columns:
                            supports = node_data[~node_data['is_leaf'] & node_data['support'].notna()]['support']
                            if not supports.empty:
                                print(f"  ✅ Encontrados {len(supports)} valores de suporte alternativos!")
                                
                                # Atualiza os valores de suporte nos nós
                                for idx, support in supports.items():
                                    if idx < len(ctre.treenode.traverse()):
                                        node = list(ctre.treenode.traverse())[idx]
                                        if not node.is_leaf():
                                            node.support = support
                                            print(f"  Atualizado suporte do nó {idx} para {support:.4f}")
                                
                                # Atualiza a contagem de nós com suporte
                                nos_com_suporte = [node for node in nos_internos 
                                                if hasattr(node, 'support') and node.support is not None]
                    except Exception as e:
                        print(f"  ⚠️  Erro ao tentar extrair suportes alternativos: {str(e)}")
                
                # Se ainda não houver suportes, adiciona um aviso ao desenho
                if not nos_com_suporte:
                    print("\n❌ ATENÇÃO: Nenhum valor de suporte foi encontrado nos nós internos da árvore de consenso.")
                    print("  A árvore será salva sem valores de suporte.")
                    print("\n  Possíveis causas:")
                    print("  1. As árvores de entrada não têm valores de suporte.")
                    print("  2. O método de consenso não está preservando os valores de suporte.")
                    print("  3. As árvores de entrada têm topologias idênticas.")
                    print("\n  Sugestões:")
                    print("  - Verifique se as árvores de entrada têm valores de suporte.")
                    print("  - Considere usar um método de consenso diferente que preserve os valores de suporte.")
                    print("  - Verifique se as árvores de entrada têm topologias diferentes.")
                
                # Salva a imagem em SVG (não requer Ghostscript)
                consenso_path = consenso_path.replace('.png', '.svg')
                print(f"\n💾 Salvando árvore de consenso em: {consenso_path}")
                
                # Tenta salvar com configurações otimizadas
                try:
                    # Cria o diretório de saída se não existir
                    os.makedirs(os.path.dirname(consenso_path), exist_ok=True)
                    
                    # Configurações de estilo mínimas para evitar problemas com unidades
                    style = {
                        'text': {
                            'font-size': '10',  # Sem unidade 'px' para evitar problemas
                            'font-weight': 'normal',
                            'fill': '#000000'
                        },
                        'line': {
                            'stroke': '#000000',
                            'stroke-width': '1'
                        }
                    }
                    
                    # Tenta salvar o SVG com as configurações mínimas
                    import toyplot.svg
                    toyplot.svg.render(canvas, consenso_path, style=style)
                    print("✅ Árvore de consenso salva com sucesso!")
                    
                    # Atualiza o resultado
                    result['arquivos_gerados']['arvore_consenso'] = consenso_path
                    result['visualizacoes']['consensus_tree'] = canvas
                    
                except Exception as render_error:
                    print(f"⚠️  Erro ao salvar a árvore: {str(render_error)}")
                    print("Tentando abordagem alternativa...")
                    
                    try:
                        # Tenta salvar usando o método to_svg() do toytree
                        svg_content = ctre.draw(
                            width=1200,
                            height=1000,
                            layout='rectangular',
                            edge_type='p',
                            scale_bar=False,
                            tip_labels=True,
                            node_sizes=12,
                            node_colors='#1f77b4',
                            use_edge_lengths=False
                        ).to_svg()
                        
                        # Salva o conteúdo SVG manualmente
                        with open(consenso_path, 'w', encoding='utf-8') as f:
                            f.write(svg_content)
                            
                        print("✅ Árvore de consenso salva com sucesso usando to_svg()!")
                        result['arquivos_gerados']['arvore_consenso'] = consenso_path
                        
                    except Exception as alt_error:
                        print(f"❌ Falha ao salvar a árvore: {str(alt_error)}")
                        print("A árvore será salva apenas em formato ASCII.")
                        
                        # Tenta salvar como último recurso usando o método write() do toytree
                        try:
                            ctre.draw(
                                width=1200,
                                height=1000,
                                layout='rectangular'
                            ).write(consenso_path)
                            print("✅ Árvore de consenso salva com método write()!")
                            result['arquivos_gerados']['arvore_consenso'] = consenso_path
                        except Exception as final_error:
                            print(f"❌ Falha final ao salvar a árvore: {str(final_error)}")
                            print("A árvore será salva apenas em formato ASCII.")
                            return result
                
                # Adiciona informações sobre os suportes ao resultado
                if nos_com_suporte:
                    suportes = [node.support for node in nos_com_suporte]
                    result['estatisticas_suporte'] = {
                        'media': sum(suportes)/len(suportes),
                        'minimo': min(suportes),
                        'maximo': max(suportes),
                        'desvio_padrao': np.std(suportes) if len(suportes) > 1 else 0,
                        'total_nos_internos': len(nos_internos),
                        'nos_com_suporte': len(nos_com_suporte)
                    }
                    
                    print("\n📊 Estatísticas finais dos valores de suporte:")
                    print(f"  Média: {result['estatisticas_suporte']['media']:.4f}")
                    print(f"  Mínimo: {result['estatisticas_suporte']['minimo']:.4f}")
                    print(f"  Máximo: {result['estatisticas_suporte']['maximo']:.4f}")
                    if len(suportes) > 1:
                        print(f"  Desvio padrão: {result['estatisticas_suporte']['desvio_padrao']:.4f}")
                    print(f"  Nós com suporte: {result['estatisticas_suporte']['nos_com_suporte']}/{result['estatisticas_suporte']['total_nos_internos']} ({(result['estatisticas_suporte']['nos_com_suporte']/result['estatisticas_suporte']['total_nos_internos']*100):.1f}%)")
                
            except Exception as e:
                print(f"   ⚠️  Erro ao gerar árvore de consenso: {str(e)}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"   ⚠️  Erro ao carregar as árvores: {str(e)}")
            traceback.print_exc()
            return result
        
        # 5. Gera a visualização ASCII com Bio.Phylo
        print("\n📜 Gerando visualização 3/3: Árvore ASCII...")
        ascii_path = os.path.join(temp_dir, "arvore_ascii.txt")
        
        try:
            # Tenta ler as árvores com Bio.Phylo
            trees = list(Phylo.parse(StringIO("\n".join(newick_strings)), "newick"))
            
            if not trees:
                raise ValueError("Nenhuma árvore foi carregada pelo Bio.Phylo")
            
            # Redireciona temporariamente a saída padrão para capturar a árvore ASCII
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                # Tenta desenhar a árvore ASCII
                Phylo.draw_ascii(trees[0])
                ascii_tree = sys.stdout.getvalue()
                
                # Verifica se a árvore ASCII foi gerada corretamente
                if not ascii_tree or len(ascii_tree.strip()) < 10:  # Valor arbitrário mínimo para considerar válido
                    raise ValueError("A árvore ASCII gerada está vazia ou incompleta")
                
                # Salva a árvore ASCII em um arquivo
                with open(ascii_path, 'w', encoding='utf-8') as f:
                    f.write("ÁRVORE DE CONSENSO ASCII\n")
                    f.write("="*70 + "\n\n")
                    f.write(ascii_tree)
                    f.write("\n" + "="*70 + "\n")
                
                result['arquivos_gerados']['arvore_ascii'] = ascii_path
                result['visualizacoes']['ascii_tree'] = ascii_tree
                print(f"   ✅ Visualização ASCII salva em: {ascii_path}")
                
                # Exibe a árvore ASCII no console
                print("\n" + "="*70)
                print("VISUALIZAÇÃO DA ÁRVORE DE CONSENSO (ASCII)")
                print("="*70 + "\n")
                print(ascii_tree)
                print("\n" + "="*70)
                
            except Exception as draw_error:
                print(f"   ⚠️  Erro ao desenhar a árvore ASCII: {str(draw_error)}")
                print("   Tentando método alternativo para gerar visualização...")
                
                # Método alternativo: usa a representação em string da árvore de consenso
                try:
                    ascii_tree = str(ctre)
                    with open(ascii_path, 'w', encoding='utf-8') as f:
                        f.write("REPRESENTAÇÃO ALTERNATIVA DA ÁRVORE DE CONSENSO\n")
                        f.write("="*70 + "\n\n")
                        f.write(ascii_tree)
                        f.write("\n" + "="*70 + "\n")
                    
                    result['arquivos_gerados']['arvore_ascii'] = ascii_path
                    result['visualizacoes']['ascii_tree'] = ascii_tree
                    print(f"   ✅ Visualização alternativa salva em: {ascii_path}")
                    
                    print("\n" + "="*70)
                    print("REPRESENTAÇÃO ALTERNATIVA DA ÁRVORE DE CONSENSO")
                    print("="*70 + "\n")
                    print(ascii_tree)
                    print("\n" + "="*70)
                    
                except Exception as alt_error:
                    print(f"   ❌ Falha ao gerar visualização alternativa: {str(alt_error)}")
            
            finally:
                # Garante que o stdout seja restaurado mesmo em caso de erro
                sys.stdout = old_stdout
            
        except Exception as parse_error:
            print(f"   ⚠️  Erro ao processar árvores para visualização ASCII: {str(parse_error)}")
            print("   Tentando método alternativo para gerar visualização...")
            
            # Método alternativo: usa a representação em string da árvore de consenso
            try:
                ascii_tree = str(ctre)
                with open(ascii_path, 'w', encoding='utf-8') as f:
                    f.write("REPRESENTAÇÃO ALTERNATIVA DA ÁRVORE DE CONSENSO\n")
                    f.write("="*70 + "\n\n")
                    f.write(ascii_tree)
                    f.write("\n" + "="*70 + "\n")
                
                result['arquivos_gerados']['arvore_ascii'] = ascii_path
                result['visualizacoes']['ascii_tree'] = ascii_tree
                print(f"   ✅ Visualização alternativa salva em: {ascii_path}")
                
                print("\n" + "="*70)
                print("REPRESENTAÇÃO ALTERNATIVA DA ÁRVORE DE CONSENSO")
                print("="*70 + "\n")
                print(ascii_tree)
                print("\n" + "="*70)
                
            except Exception as alt_error:
                print(f"   ❌ Falha ao gerar visualização alternativa: {str(alt_error)}")
        
        # 6. Retorna os resultados
        print("\n✅ Visualizações geradas com sucesso!")
        print("\n📂 Arquivos gerados:")
        for tipo, caminho in result['arquivos_gerados'].items():
            print(f"   - {tipo.replace('_', ' ').title()}: {caminho}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ [ERRO] Falha ao gerar visualizações: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def visualize_consensus_trees(ncd_mat, labels):
    """
    Gera visualizações da árvore de consenso, incluindo árvore de nuvens e visualização ASCII.
    
    Esta função utiliza a função visualizar_arvore_consenso internamente para gerar as visualizações,
    seguindo o fluxo recomendado com toytree.
    
    Args:
        ncd_mat: Matriz de distância NCD
        labels: Lista de rótulos (nomes das colunas)
        
    Returns:
        dict: Dicionário com os caminhos dos arquivos gerados
    """
    import os
    import tempfile
    import numpy as np
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import squareform
    from io import StringIO
    
    # Inicializa o dicionário de resultados
    result = {}
    
    try:
        # Cria um diretório temporário para salvar as imagens
        temp_dir = tempfile.mkdtemp()
        print(f"\n📁 Diretório temporário para visualizações: {temp_dir}")
        
        # 1. Calcula o linkage a partir da matriz de distância
        print("\n🔍 Calculando árvore de consenso...")
        
        # Converte a matriz de distância para o formato condensado
        condensed_dist = squareform(ncd_mat, force='tovector', checks=False)
        
        # Calcula o linkage usando o método de ligação média
        Z = linkage(condensed_dist, method='average')
        
        # 2. Gera múltiplas árvores Newick a partir do linkage
        # Para este exemplo, geramos apenas uma árvore, mas poderíamos gerar várias
        print("\n🌿 Gerando árvores Newick a partir do linkage...")
        
        # Função auxiliar para converter um nó da árvore para Newick
        def node_to_newick(node, n, labels, dist_matrix, parent_dist, newick=''):
            if node < n:
                return f"{labels[node]}:{parent_dist:.4f}{newick}"
            else:
                left = int(Z[node - n, 0])
                right = int(Z[node - n, 1])
                dist = Z[node - n, 2]
                left_newick = node_to_newick(left, n, labels, dist_matrix, dist)
                right_newick = node_to_newick(right, n, labels, dist_matrix, dist)
                return f"({left_newick},{right_newick})"
        
        # Gera a árvore Newick a partir do linkage
        n = len(labels)
        newick_str = node_to_newick(2 * n - 2, n, labels, Z, 0.0) + ";"
        
        # 3. Salva a representação Newick em um arquivo
        newick_path = os.path.join(temp_dir, "arvore.newick")
        try:
            with open(newick_path, 'w', encoding='utf-8') as f:
                f.write(newick_str)
            print(f"   - Árvore Newick salva em: {newick_path}")
            result['arvore_newick'] = newick_path
        except Exception as e:
            print(f"   - [ERRO] Falha ao salvar a árvore Newick: {str(e)}")
        
        # 4. Usa a função visualizar_arvore_consenso para gerar as visualizações
        print("\n🔄 Usando a função visualizar_arvore_consenso para gerar visualizações...")
        
        # Prepara os parâmetros para visualizar_arvore_consenso
        # Usamos a mesma árvore múltiplas vezes para simular múltiplas árvores
        newick_strings = [newick_str] * 3  # Usamos a mesma árvore 3 vezes como exemplo
        
        # Chama a função visualizar_arvore_consenso
        viz_result = visualizar_arvore_consenso(newick_strings, labels)
        
        # Atualiza o dicionário de resultados com os caminhos dos arquivos gerados
        if viz_result and 'arquivos_gerados' in viz_result:
            result.update(viz_result['arquivos_gerados'])
            
            # Exibe mensagem de sucesso e os caminhos dos arquivos gerados
            print("\n✅ Visualizações geradas com sucesso!")
            print("\n📂 Arquivos gerados:")
            for key, path in viz_result['arquivos_gerados'].items():
                print(f"   - {key.replace('_', ' ').title()}: {path}")
                
            # Adiciona a visualização ASCII ao resultado, se disponível
            if 'arvore_ascii' in viz_result['arquivos_gerados']:
                try:
                    with open(viz_result['arquivos_gerados']['arvore_ascii'], 'r', encoding='utf-8') as f:
                        ascii_content = f.read()
                    # Exibe a visualização ASCII no console
                    print("\n" + "="*70)
                    print("VISUALIZAÇÃO DA ÁRVORE DE CONSENSO (ASCII)")
                    print("="*70 + "\n")
                    print(ascii_content)
                except Exception as e:
                    print(f"   - [AVISO] Não foi possível exibir a visualização ASCII: {str(e)}")
        else:
            print("\n⚠️  Nenhuma visualização pôde ser gerada pela função visualizar_arvore_consenso.")
        
    except Exception as e:
        print(f"\n❌ [ERRO] Falha ao gerar visualizações: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return result

# Função auxiliar para construir árvores de categoria
def build_category_tree(df, n_categories, mode="best", criterio_vars=None):
    """
    Constrói uma árvore de decisão baseada nos critérios fornecidos.
    
    Esta função gera uma representação em texto de uma árvore de decisão baseada
    nos critérios fornecidos. Pode ser usada para visualizar a hierarquia de
    categorias e seus respectivos critérios.
    
    Args:
        df: DataFrame com os dados
        n_categories: Número de categorias para divisão
        mode: Modo de construção ('best' ou 'worst')
        criterio_vars: Lista de variáveis a serem usadas como critérios
        
    Returns:
        str: Representação em texto da árvore de decisão
    """
    # Esta é uma implementação simplificada
    # Em uma implementação real, aqui seria implementada a lógica de construção da árvore
    
    if mode == "best":
        tree = f"Raiz [Melhor Caso]\n"
    else:
        tree = f"Raiz [Pior Caso]\n"
    
    if criterio_vars:
        for i, var in enumerate(criterio_vars[:n_categories], 1):
            tree += f"├── {var} (Critério {i})\n"
            for j in range(2):  # Dois ramos por critério para simplificar
                tree += f"│   └── Ramo {j+1}: Valor {j+1}\n"
    else:
        tree += "└── Nenhum critério disponível\n"
    
    return tree

def configurar_logging():
    """Configura o sistema de logging da aplicacao."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('damicore_pipeline.log', encoding='utf-8')
        ]
    )

if __name__ == "__main__":
    try:
        # Configura o sistema de logging
        configurar_logging()
        logging.info("Iniciando execução do DAMICORE Pipeline")
        
        # Executa a função principal
        main()
        
        logging.info("Execução concluída com sucesso!")
        
    except KeyboardInterrupt:
        logging.warning("Execução interrompida pelo usuário.")
        sys.exit(1)
        
    except Exception as e:
        logging.error(f"Erro crítico durante a execução: {str(e)}", exc_info=True)
        print(f"\n❌ Ocorreu um erro durante a execução: {str(e)}")
        print("Consulte o arquivo de log 'damicore_pipeline.log' para mais detalhes.")
        sys.exit(1)
