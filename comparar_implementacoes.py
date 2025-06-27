#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar as implementações de cálculo de matriz NCD (zlib vs DAMICORE).

Este script executa as duas implementações em paralelo, compara os resultados e gera
um relatório detalhado com métricas de comparação e visualizações.
"""

import os
import sys
import time
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('comparacao_implementacoes.log')
    ]
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao path para importar módulos locais
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Importa as funções necessárias
try:
    from damicore_ncd import generate_ncd_matrix
    from ncd_matrix import ncd_matrix_from_dataframe as ncd_zlib
    logger.info("Módulos locais importados com sucesso")
except ImportError as e:
    logger.error("Erro ao importar módulos locais: {}".format(e))
    sys.exit(1)

def carregar_dados(diretorio):
    """
    Carrega os dados de texto dos arquivos em um dicionário.
    
    Args:
        diretorio: Caminho para o diretório com os arquivos de texto
        
    Returns:
        Dicionário com os dados carregados: {nome_arquivo: [linhas]}
    """
    diretorio = Path(diretorio)
    dados = {}
    
    for arquivo in diretorio.glob('*.txt'):
        try:
            with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                linhas = [linha.strip() for linha in f if linha.strip()]
                if linhas:
                    dados[arquivo.stem] = linhas
        except Exception as e:
            logger.warning("Erro ao ler %s: %s" % (str(arquivo), str(e)))
    
    return dados

def executar_zlib(dados):
    """
    Executa o cálculo da matriz NCD usando a implementação zlib.
    
    Args:
        dados: Dicionário com os dados a serem processados
        
    Returns:
        Tupla com a matriz NCD e a lista de rótulos
    """
    try:
        logger.info("Iniciando cálculo NCD com zlib...")
        inicio = time.time()
        
        # Converte para DataFrame
        df = pd.DataFrame(dados)
        
        # Calcula a matriz NCD
        matriz, rotulos = ncd_zlib(df)
        
        tempo = time.time() - inicio
        logger.info("Cálculo zlib concluído em {:.2f} segundos".format(tempo))
        
        return matriz, rotulos
        
    except Exception as e:
        logger.error("Erro no cálculo zlib: %s" % str(e), exc_info=True)
        raise

def executar_damicore(diretorio, compressor='gzip'):
    """
    Executa o cálculo da matriz NCD usando o DAMICORE.
    
    Args:
        diretorio: Caminho para o diretório com os arquivos de texto
        compressor: Algoritmo de compressão a ser usado
        
    Returns:
        Tupla com a matriz NCD e a lista de rótulos
    """
    try:
        logger.info("Iniciando cálculo NCD com DAMICORE ({})...".format(compressor))
        inicio = time.time()
        
        # Executa o DAMICORE
        matriz, rotulos = generate_ncd_matrix(
            input_dir=str(diretorio),
            compressor=compressor,
            max_workers=4,
            cleanup=True,
            verbose=False
        )
        
        tempo = time.time() - inicio
        logger.info("Cálculo DAMICORE ({}) concluído em {:.2f} segundos".format(compressor, tempo))
        
        return matriz, rotulos
        
    except Exception as e:
        logger.error("Erro no cálculo DAMICORE: %s" % str(e), exc_info=True)
        raise

def comparar_matrizes(
    matriz1, 
    matriz2, 
    rotulos1, 
    rotulos2,
    nome1="zlib",
    nome2="DAMICORE",
    tolerancia=1e-5
):
    """
    Compara duas matrizes NCD e retorna métricas de similaridade.
    
    Args:
        matriz1: Primeira matriz NCD
        matriz2: Segunda matriz NCD
        rotulos1: Rótulos da primeira matriz
        rotulos2: Rótulos da segunda matriz
        nome1: Nome da primeira implementação
        nome2: Nome da segunda implementação
        tolerancia: Tolerância para comparação de valores flutuantes
        
    Returns:
        Dicionário com métricas de comparação
    """
    resultados = {
        'igual_tamanho': False,
        'rotulos_iguais': False,
        'simetria1': False,
        'simetria2': False,
        'diagonal1_ok': False,
        'diagonal2_ok': False,
        'diferenca_media': None,
        'diferenca_max': None,
        'correlacao': None,
        'diferencas': None
    }
    
    try:
        # Verifica se as matrizes têm o mesmo tamanho
        resultados['tamanho1'] = matriz1.shape
        resultados['tamanho2'] = matriz2.shape
        
        if matriz1.shape != matriz2.shape:
            logger.warning("Matrizes têm tamanhos diferentes: %s vs %s" % (str(matriz1.shape), str(matriz2.shape)))
            return resultados
            
        resultados['igual_tamanho'] = True
        
        # Verifica se os rótulos são iguais (mesma ordem)
        rotulos_iguais = rotulos1 == rotulos2
        resultados['rotulos_iguais'] = rotulos_iguais
        
        if not rotulos_iguais:
            logger.warning("Os rótulos das matrizes são diferentes ou estão em ordem diferente")
        
        # Verifica simetria das matrizes
        simetria1 = np.allclose(matriz1, matriz1.T, atol=tolerancia)
        simetria2 = np.allclose(matriz2, matriz2.T, atol=tolerancia)
        
        resultados['simetria1'] = simetria1
        resultados['simetria2'] = simetria2
        
        if not simetria1:
            logger.warning("A matriz %s não é simétrica" % nome1)
        if not simetria2:
            logger.warning("A matriz %s não é simétrica" % nome2)
        
        # Verifica diagonal (deve ser zero)
        diagonal1_ok = np.allclose(np.diag(matriz1), 0, atol=tolerancia)
        diagonal2_ok = np.allclose(np.diag(matriz2), 0, atol=tolerancia)
        
        resultados['diagonal1_ok'] = diagonal1_ok
        resultados['diagonal2_ok'] = diagonal2_ok
        
        if not diagonal1_ok:
            logger.warning("A diagonal da matriz %s não é zero" % nome1)
        if not diagonal2_ok:
            logger.warning("A diagonal da matriz %s não é zero" % nome2)
        
        # Calcula diferenças
        diferencas = np.abs(matriz1 - matriz2)
        resultados['diferenca_media'] = np.mean(diferencas)
        resultados['diferenca_max'] = np.max(diferencas)
        
        # Calcula correlação
        try:
            correlacao = np.corrcoef(matriz1.flatten(), matriz2.flatten())[0, 1]
            resultados['correlacao'] = correlacao
        except Exception as e:
            logger.warning("Erro ao calcular correlação: %s" % str(e))
        
        # Adiciona as diferenças para análise posterior
        resultados['diferencas'] = diferencas
        
        return resultados
        
    except Exception as e:
        logger.error("Erro ao comparar matrizes: %s" % str(e), exc_info=True)
        return resultados

def gerar_relatorio(resultados, diretorio_saida):
    """
    Gera um relatório detalhado com as comparações.
    
    Args:
        resultados: Dicionário com os resultados das comparações
        diretorio_saida: Diretório para salvar os resultados
    """
    diretorio_saida = Path(diretorio_saida)
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    
    # Cria um relatório de texto
    relatorio = []
    relatorio.append("=" * 80)
    relatorio.append("COMPARAÇÃO DAS IMPLEMENTAÇÕES DE CÁLCULO DE MATRIZ NCD")
    relatorio.append("=" * 80)
    relatorio.append("")
    
    # Resumo das matrizes
    relatorio.append("RESUMO DAS MATRIZES")
    relatorio.append("-" * 40)
    relatorio.append("Matriz zlib: {} (tempo: {:.2f}s)".format(resultados['zlib']['matriz'].shape, resultados['zlib'].get('tempo', 0)))
    relatorio.append("Matriz DAMICORE: {} (tempo: {:.2f}s)".format(resultados['damicore']['matriz'].shape, resultados['damicore'].get('tempo', 0)))
    relatorio.append("")
    
    # Comparação
    comp = resultados['comparacao']
    relatorio.append("COMPARAÇÃO DAS MATRIZES")
    relatorio.append("-" * 40)
    relatorio.append("Tamanhos iguais: {}".format(comp['igual_tamanho']))
    relatorio.append("Rótulos iguais: {}".format(comp['rotulos_iguais']))
    relatorio.append("Matriz zlib é simétrica: {}".format(comp['simetria1']))
    relatorio.append("Matriz DAMICORE é simétrica: {}".format(comp['simetria2']))
    relatorio.append("Diagonal zlib OK: {}".format(comp['diagonal1_ok']))
    relatorio.append("Diagonal DAMICORE OK: {}".format(comp['diagonal2_ok']))
    relatorio.append("Diferença média: {:.6f}".format(comp['diferenca_media']))
    relatorio.append("Diferença máxima: {:.6f}".format(comp['diferenca_max']))
    relatorio.append("Correlação: {:.6f}".format(comp['correlacao']))
    relatorio.append("")
    
    # Salva o relatório
    caminho_relatorio = diretorio_saida / "relatorio.txt"
    with open(caminho_relatorio, 'w', encoding='utf-8') as f:
        f.write("\n".join(relatorio))
    
    logger.info("Relatório salvo em: {}".format(caminho_relatorio))
    
    # Gera visualizações
    if comp['diferencas'] is not None:
        try:
            plt.figure(figsize=(12, 10))
            
            # Matriz de diferenças
            plt.subplot(2, 2, 1)
            sns.heatmap(comp['diferencas'], cmap='viridis')
            plt.title('Diferenças entre as matrizes')
            
            # Histograma das diferenças
            plt.subplot(2, 2, 2)
            sns.histplot(comp['diferencas'].flatten(), kde=True)
            plt.title('Distribuição das diferenças')
            
            # Matriz zlib
            plt.subplot(2, 2, 3)
            sns.heatmap(resultados['zlib']['matriz'], cmap='viridis')
            plt.title('Matriz zlib')
            
            # Matriz DAMICORE
            plt.subplot(2, 2, 4)
            sns.heatmap(resultados['damicore']['matriz'], cmap='viridis')
            plt.title('Matriz DAMICORE')
            
            plt.tight_layout()
            caminho_imagem = diretorio_saida / "comparacao_matrizes.png"
            plt.savefig(caminho_imagem, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("Visualização salva em: {}".format(caminho_imagem))
            
        except Exception as e:
            logger.error("Erro ao gerar visualizações: %s" % str(e), exc_info=True)

def main():
    """Função principal que orquestra a execução."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comparar implementações de cálculo de matriz NCD')
    parser.add_argument('--dados', type=str, default='test_data/portugues',
                        help='Diretório com os arquivos de texto para processar')
    parser.add_argument('--saida', type=str, default='resultados_comparacao',
                        help='Diretório para salvar os resultados')
    parser.add_argument('--compressor', type=str, default='gzip',
                        choices=['gzip', 'bzip2', 'ppmd'],
                        help='Algoritmo de compressão para o DAMICORE')
    parser.add_argument('--threads', type=int, default=4,
                        help='Número de threads para processamento paralelo')
    
    args = parser.parse_args()
    
    try:
        # Carrega os dados
        logger.info("Carregando arquivos de %s..." % str(args.dados))
        dados = carregar_dados(args.dados)
        
        if not dados:
            logger.error("Nenhum dado válido encontrado")
            return 1
            
        logger.info("Carregados %d arquivos com sucesso" % len(dados))
        logger.info("Carregados %d arquivos com sucesso" % len(dados))
        
        # Executa as implementações em paralelo
        resultados = {}
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submete as tarefas
            future_zlib = executor.submit(executar_zlib, dados)
            future_damicore = executor.submit(executar_damicore, args.dados, args.compressor)
            
            # Aguarda e coleta os resultados
            try:
                matriz_zlib, rotulos_zlib = future_zlib.result()
                resultados['zlib'] = {
                    'matriz': matriz_zlib,
                    'rotulos': rotulos_zlib,
                    'tempo': future_zlib.result().get('tempo', 0) if hasattr(future_zlib.result(), 'get') else 0
                }
                logger.info("Cálculo zlib concluído com sucesso")
            except Exception as e:
                logger.error("Erro no cálculo zlib: {}".format(e), exc_info=True)
                return 1
                
            try:
                matriz_damicore, rotulos_damicore = future_damicore.result()
                resultados['damicore'] = {
                    'matriz': matriz_damicore,
                    'rotulos': rotulos_damicore,
                    'tempo': future_damicore.result().get('tempo', 0) if hasattr(future_damicore.result(), 'get') else 0
                }
                logger.info("Cálculo DAMICORE concluído com sucesso")
            except Exception as e:
                logger.error("Erro no cálculo DAMICORE: {}".format(e), exc_info=True)
                return 1
        
        # Compara as matrizes
        logger.info("Comparando as matrizes...")
        comparacao = comparar_matrizes(
            resultados['zlib']['matriz'], 
            resultados['damicore']['matriz'],
            resultados['zlib']['rotulos'],
            resultados['damicore']['rotulos']
        )
        
        resultados['comparacao'] = comparacao
        
        # Gera o relatório
        logger.info("Gerando relatório...")
        gerar_relatorio(resultados, args.saida)
        
        logger.info("Processo concluído com sucesso!")
        return 0
        
    except Exception as e:
        logger.error("Erro durante a execução: %s" % str(e), exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
