#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar a saída do DAMICORE local com a saída do Colab.

Este script executa o DAMICORE localmente em um conjunto de dados de teste e compara
a matriz NCD gerada com uma matriz de referência (gerada pelo Colab).
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

# Configuração de logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('comparacao_damicore.log')
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

def carregar_rotulos_referencia(caminho_rotulos: str) -> List[str]:
    """
    Carrega os rótulos da matriz de referência.
    
    Args:
        caminho_rotulos: Caminho para o arquivo de rótulos
        
    Returns:
        Lista de rótulos
    """
    try:
        if not os.path.exists(caminho_rotulos):
            logger.warning(f"Arquivo de rótulos não encontrado: {caminho_rotulos}")
            return []
            
        logger.info(f"Lendo rótulos de: {caminho_rotulos}")
        
        # Lê o arquivo como texto
        with open(caminho_rotulos, 'r', encoding='utf-8') as f:
            # Lê todas as linhas, remove linhas vazias e espaços em branco
            rotulos = [linha.strip() for linha in f if linha.strip()]
        
        # Verifica se o arquivo está vazio
        if not rotulos:
            logger.warning(f"Arquivo de rótulos vazio: {caminho_rotulos}")
            return []
        
        # Verificação simplificada para dados numéricos
        # Se a primeira linha contiver apenas números, pontos, espaços e sinais, pode ser uma matriz
        primeira_linha = rotulos[0].replace(' ', '').replace('+', '').replace('-', '').replace('.', '').replace('e', '').replace('E', '')
        if primeira_linha.replace('0', '').isdigit() and len(rotulos) > 1:
            logger.warning("Arquivo de rótulos parece conter dados numéricos. Verificando estrutura...")
            # Verifica se todas as linhas têm o mesmo comprimento (características de matriz)
            comprimento = len(rotulos[0].split())
            if all(len(linha.split()) == comprimento for linha in rotulos):
                logger.warning("Arquivo parece ser uma matriz numérica. Verifique se o caminho do arquivo de rótulos está correto.")
                return []
        
        logger.info(f"Carregados {len(rotulos)} rótulos do arquivo {caminho_rotulos}")
        logger.debug(f"Primeiros 5 rótulos: {rotulos[:5]}")
        return rotulos
            
    except UnicodeDecodeError:
        logger.error(f"Erro de codificação ao ler o arquivo de rótulos: {caminho_rotulos}")
        return []
    except Exception as e:
        logger.error(f"Erro ao carregar rótulos de {caminho_rotulos}: {e}", exc_info=True)
        return []

def carregar_matriz_referencia(caminho_matriz: str, caminho_rotulos: str = None) -> Tuple[np.ndarray, List[str]]:
    """
    Carrega a matriz de referência e seus rótulos.
    
    Args:
        caminho_matriz: Caminho para o arquivo da matriz de referência
        caminho_rotulos: Caminho opcional para o arquivo de rótulos
        
    Returns:
        Tupla contendo a matriz numpy e a lista de rótulos
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(caminho_matriz):
            logger.error(f"Arquivo de referência não encontrado: {caminho_matriz}")
            return None, []
        
        # Tenta carregar a matriz
        try:
            logger.info(f"Tentando carregar matriz de referência de: {caminho_matriz}")
            
            # Lê o arquivo como texto primeiro
            with open(caminho_matriz, 'r', encoding='utf-8') as f:
                linhas = [linha.strip() for linha in f if linha.strip()]
            
            # Converte as linhas para uma matriz numpy
            matriz = np.array([[float(valor) for valor in linha.split()] for linha in linhas])
            
            # Verifica se a matriz está vazia
            if matriz.size == 0:
                logger.error("Matriz de referência vazia")
                return None, []
                
            logger.info(f"Matriz de referência carregada: {matriz.shape}")
            
            # Garante que a matriz seja 2D
            if len(matriz.shape) != 2:
                logger.error(f"Matriz deve ser 2D, mas tem forma {matriz.shape}")
                return None, []
            
            # Garante que a matriz seja quadrada
            if matriz.shape[0] != matriz.shape[1]:
                logger.warning(f"Matriz não quadrada: {matriz.shape}. Ajustando para quadrada.")
                min_dim = min(matriz.shape[0], matriz.shape[1])
                matriz = matriz[:min_dim, :min_dim]
                logger.info(f"Matriz ajustada para: {matriz.shape}")
                    
        except Exception as e:
            logger.error(f"Falha ao carregar a matriz de referência: {e}", exc_info=True)
            return None, []
        
        # Tenta carregar os rótulos
        rotulos = []
        if caminho_rotulos and os.path.exists(caminho_rotulos):
            logger.info(f"Carregando rótulos de referência de: {caminho_rotulos}")
            rotulos = carregar_rotulos_referencia(caminho_rotulos)
        
        # Se não conseguiu carregar os rótulos, usa índices numéricos
        if not rotulos:
            rotulos = [f"REF-{i+1}" for i in range(matriz.shape[0])]
            logger.warning(f"Usando rótulos numéricos: {len(rotulos)} rótulos gerados")
        
        # Verifica consistência entre matriz e rótulos
        if len(rotulos) != matriz.shape[0]:
            logger.warning(
                f"Número de rótulos ({len(rotulos)}) não corresponde ao tamanho da matriz ({matriz.shape[0]})\n"
                "Ajustando para corresponder ao tamanho da matriz."
            )
            # Ajusta os rótulos para corresponder ao tamanho da matriz
            rotulos = rotulos[:matriz.shape[0]] if len(rotulos) > matriz.shape[0] else rotulos + [f"REF-{i+1}" for i in range(len(rotulos), matriz.shape[0])]
        
        logger.info(f"Matriz de referência carregada com sucesso. Dimensões: {matriz.shape}, Rótulos: {len(rotulos)}")
        logger.debug(f"Primeiros 5 rótulos: {rotulos[:5]}")
        logger.debug(f"Dimensões da matriz: {matriz.shape}")
        logger.debug(f"Primeiros 3x3 da matriz:\n{matriz[:3, :3]}")
        
        return matriz, rotulos
        
    except Exception as e:
        logger.error(f"Erro ao carregar matriz de referência: {e}", exc_info=True)
        return None, []
        return None, []

def comparar_matrizes(
    matriz_local: np.ndarray, 
    matriz_ref: np.ndarray, 
    rotulos_local: list, 
    rotulos_ref: list,
    tolerancia: float = 1e-5
) -> Dict[str, Any]:
    """
    Compara duas matrizes NCD e retorna métricas de similaridade.
    
    Args:
        matriz_local: Matriz NCD gerada localmente
        matriz_ref: Matriz NCD de referência (Colab)
        rotulos_local: Rótulos da matriz local
        rotulos_ref: Rótulos da matriz de referência
        tolerancia: Tolerância para comparação de valores flutuantes
        
    Returns:
        Dicionário com métricas de comparação
    """
    resultado = {
        'dimensoes_iguais': False,
        'rotulos_compativeis': False,
        'correlacao': None,
        'diferenca_media': None,
        'diferenca_maxima': None,
        'matriz_diferencas': None,
        'erro': None
    }
    
    try:
        # Verifica dimensoes
        if matriz_local.shape != matriz_ref.shape:
            resultado['erro'] = "Dimensoes diferentes: local={}, ref={}".format(
                matriz_local.shape, matriz_ref.shape)
            return resultado
            
        resultado['dimensoes_iguais'] = True
        
        # Verifica se os rótulos são compatíveis
        if len(rotulos_local) == len(rotulos_ref) and all(l == r for l, r in zip(rotulos_local, rotulos_ref)):
            resultado['rotulos_compativeis'] = True
        else:
            logger.warning("Rótulos não são idênticos, comparando apenas a estrutura da matriz")
        
        # Calcula métricas de similaridade
        diferencas = np.abs(matriz_local - matriz_ref)
        resultado['diferenca_media'] = np.mean(diferencas)
        resultado['diferenca_maxima'] = np.max(diferencas)
        resultado['matriz_diferencas'] = diferencas
        
        # Calcula correlação (apenas se as matrizes não forem constantes)
        if not (np.all(matriz_local == matriz_local[0,0]) or np.all(matriz_ref == matriz_ref[0,0])):
            resultado['correlacao'] = np.corrcoef(matriz_local.flatten(), matriz_ref.flatten())[0, 1]
        
        return resultado
        
    except Exception as e:
        resultado['erro'] = "Erro ao comparar matrizes: {}".format(e)
        return resultado

def executar_teste_comparacao(
    diretorio_dados: str,
    caminho_matriz_ref: Optional[str] = None,
    usar_zlib: bool = False,
    compressor: str = 'gzip',
    max_workers: int = 4,
    limpar_temporarios: bool = True
) -> Dict[str, Any]:
    """
    Executa o teste de comparação entre as implementações local e de referência.
    
    Args:
        diretorio_dados: Caminho para o diretório com os dados de entrada
        caminho_matriz_ref: Caminho opcional para a matriz de referência
        usar_zlib: Se True, usa a implementação zlib em vez do DAMICORE
        compressor: Algoritmo de compressão a ser usado ('gzip', 'bzip2' ou 'ppmd')
        max_workers: Número de processos paralelos
        limpar_temporarios: Se True, remove arquivos temporários após o teste
        
    Returns:
        Dicionário com os resultados do teste
    """
    # Configura diretório de saída
    diretorio_saida = Path("test_results") / "comparacao_damicore"
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    
    # Cria um diretório temporário
    diretorio_temp = Path(tempfile.mkdtemp(prefix='damicore_test_'))
    logger.info(f"Diretório temporário: {diretorio_temp}")
    
    try:
        # Passo 1: Executar o DAMICORE local
        logger.info("Iniciando geração da matriz NCD local...")
        
        if usar_zlib:
            # Usa a implementação zlib
            logger.info("Usando implementação zlib...")
            df = pd.DataFrame()
            
            # Carrega a lista de arquivos de referência
            caminho_rotulos_ref = os.path.join(os.path.dirname(caminho_matriz_ref), 'rotulos_referencia.txt')
            if not os.path.exists(caminho_rotulos_ref):
                raise FileNotFoundError(f"Arquivo de rótulos de referência não encontrado: {caminho_rotulos_ref}")
                
            # Lê os rótulos de referência
            with open(caminho_rotulos_ref, 'r', encoding='utf-8') as f:
                rotulos_referencia = [linha.strip() for linha in f if linha.strip()]
            
            # Remove a extensão .txt se existir nos rótulos
            rotulos_referencia = [os.path.splitext(r)[0] for r in rotulos_referencia]
            
            logger.info(f"Rótulos de referência carregados: {len(rotulos_referencia)} itens")
            
            # Primeiro, lista todos os arquivos .txt no diretório
            arquivos_disponiveis = [f for f in os.listdir(diretorio_dados) 
                                 if f.lower().endswith('.txt') and 
                                    os.path.isfile(os.path.join(diretorio_dados, f))]
            
            # Remove a extensão .txt para comparação
            arquivos_sem_ext = [os.path.splitext(f)[0] for f in arquivos_disponiveis]
            
            # Cria um mapeamento de nome sem extensão para nome com extensão
            mapeamento_arquivos = {os.path.splitext(f)[0]: f for f in arquivos_disponiveis}
            
            # Encontra a interseção mantendo a ordem dos rótulos de referência
            arquivos_para_ler = []
            for rotulo in rotulos_referencia:
                if rotulo in mapeamento_arquivos:
                    arquivos_para_ler.append(mapeamento_arquivos[rotulo])
            
            logger.info(f"Encontrados {len(arquivos_para_ler)} arquivos correspondentes aos rótulos de referência")
            
            if len(arquivos_para_ler) < 2:
                raise ValueError(f"Pelo menos 2 arquivos são necessários. Encontrados: {len(arquivos_para_ler)}")
            
            # Lê os arquivos e constrói o DataFrame
            max_linhas = 0
            conteudos = {}
            
            for arquivo in arquivos_para_ler:
                caminho_arquivo = os.path.join(diretorio_dados, arquivo)
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                        # Lê todas as linhas do arquivo e remove linhas vazias
                        linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
                        if linhas:
                            conteudos[arquivo] = linhas
                            max_linhas = max(max_linhas, len(linhas))
                except Exception as e:
                    logger.warning(f"Erro ao ler arquivo {arquivo}: {e}")
            
            # Cria o DataFrame com o tamanho adequado
            df = pd.DataFrame(index=range(max_linhas))
            
            # Preenche o DataFrame com os dados dos arquivos
            for arquivo, linhas in conteudos.items():
                nome_coluna = os.path.splitext(arquivo)[0]
                # Preenche com None se for menor que o tamanho máximo
                if len(linhas) < max_linhas:
                    linhas = linhas + [None] * (max_linhas - len(linhas))
                df[nome_coluna] = linhas
            
            # Remove linhas que contêm apenas valores nulos
            df = df.dropna(how='all')
            
            if df.empty:
                raise ValueError("Nenhum dado válido encontrado nos arquivos de entrada")
            
            # Gera a matriz NCD usando zlib com os rótulos de referência
            logger.info("Gerando matriz NCD com zlib...")
            try:
                # Passa os rótulos de referência originais (sem extensão)
                matriz_local, rotulos_local = ncd_zlib(
                    df, 
                    notebook_mode=True, 
                    rotulos_referencia=rotulos_referencia
                )
                logger.info(f"Matriz NCD gerada com sucesso. Dimensões: {matriz_local.shape}")
                
                # Verifica se as dimensões estão corretas
                if len(rotulos_referencia) != matriz_local.shape[0]:
                    logger.warning(f"Aviso: Número de rótulos ({len(rotulos_referencia)}) diferente da dimensão da matriz ({matriz_local.shape[0]})")
                
            except Exception as e:
                logger.error(f"Erro ao gerar matriz NCD: {e}")
                raise
            
        else:
            # Usa o DAMICORE
            logger.info("Usando DAMICORE com compressor {}...".format(compressor))
            
            # Cria um diretório temporário para os arquivos processados
            dir_entrada = diretorio_temp / "entrada"
            dir_entrada.mkdir(parents=True, exist_ok=True)
            
            # Copia os arquivos para o diretorio de entrada
            for arquivo in os.listdir(diretorio_dados):
                if arquivo.endswith('.txt'):
                    shutil.copy2(
                        Path(diretorio_dados) / arquivo,
                        dir_entrada / arquivo
                    )
            
            # Executa o DAMICORE
            try:
                matriz_local, rotulos_local = generate_ncd_matrix(
                    input_dir=str(dir_entrada),
                    output_dir=str(diretorio_temp / "saida"),
                    compressor=compressor,
                    max_workers=max_workers,
                    cleanup=limpar_temporarios,
                    verbose=True
                )
            except Exception as e:
                logger.error("Erro ao executar DAMICORE: {}".format(e), exc_info=True)
                raise
        
        # Salva a matriz local para referência
        np.savetxt(diretorio_saida / 'matriz_local.txt', matriz_local)
        # Garante que todos os rótulos sejam strings antes de fazer o join
        rotulos_str = [str(rotulo) for rotulo in rotulos_local]
        (diretorio_saida / 'rotulos_local.txt').write_text('\n'.join(rotulos_str))
        
        logger.info("Matriz local gerada: {}".format(matriz_local.shape))
        
        # Passo 2: Carregar a matriz de referência (se fornecida)
        if caminho_matriz_ref and os.path.exists(caminho_matriz_ref):
            logger.info("Carregando matriz de referencia: {}".format(caminho_matriz_ref))
            
            # Tenta encontrar o arquivo de rótulos correspondente
            caminho_rotulos = None
            if caminho_matriz_ref.endswith('_matriz.txt'):
                caminho_rotulos = caminho_matriz_ref.replace('_matriz.txt', '_rotulos.txt')
            elif caminho_matriz_ref.endswith('_ncd.txt'):
                caminho_rotulos = caminho_matriz_ref.replace('_ncd.txt', '_rotulos.txt')
            
            # Se não encontrou um arquivo de rótulos correspondente, tenta carregar um arquivo de rótulos genérico
            if not caminho_rotulos or not os.path.exists(caminho_rotulos):
                caminho_rotulos = os.path.join(os.path.dirname(caminho_matriz_ref), 'rotulos.txt')
                if not os.path.exists(caminho_rotulos):
                    caminho_rotulos = None
            
            # Carrega a matriz e os rótulos de referência
            matriz_ref, rotulos_ref = carregar_matriz_referencia(caminho_matriz_ref, caminho_rotulos)
            
            if matriz_ref is not None:
                # Salva a matriz de referência para referência
                np.savetxt(diretorio_saida / 'matriz_referencia.txt', matriz_ref)
                
                # Salva os rótulos de referência
                with open(diretorio_saida / 'rotulos_referencia.txt', 'w', encoding='utf-8') as f:
                    if isinstance(rotulos_ref, np.ndarray):
                        # Se for um array numpy, converte para lista
                        rotulos_ref = rotulos_ref.tolist()
                    # Garante que todos os rótulos sejam strings
                    rotulos_str = [str(rotulo) for rotulo in rotulos_ref]
                    f.write('\n'.join(rotulos_str))
                
                # Passo 3: Comparar as matrizes
                logger.info("Comparando matrizes...")
                comparacao = comparar_matrizes(
                    matriz_local, matriz_ref, rotulos_local, rotulos_ref
                )
                
                # Gera um relatório de comparacao
                implementacao = 'zlib' if usar_zlib else 'DAMICORE ({})'.format(compressor)
                relatorio = """
                === Relatorio de Comparacao ===
                
                Configuracao:
                - Implementacao: {0}
                - Diretorio de dados: {1}
                - Matriz de referencia: {2}
                
                Resultados:
                - Dimensoes iguais: {3}
                - Rotulos compativeis: {4}
                - Correlacao: {5}
                - Diferenca media: {6}
                - Diferenca maxima: {7}
                - Erro: {8}
                """.format(
                    implementacao,
                    diretorio_dados,
                    caminho_matriz_ref,
                    comparacao.get('dimensoes_iguais', False),
                    comparacao.get('rotulos_compativeis', False),
                    comparacao.get('correlacao', 'N/A'),
                    comparacao.get('diferenca_media', 'N/A'),
                    comparacao.get('diferenca_maxima', 'N/A'),
                    comparacao.get('erro', 'Nenhum')
                )
                
                logger.info(relatorio)
                
                # Salva o relatório em um arquivo
                (diretorio_saida / 'relatorio_comparacao.txt').write_text(relatorio)
                
                return {
                    'sucesso': True,
                    'matriz_local': matriz_local,
                    'matriz_referencia': matriz_ref,
                    'rotulos_local': rotulos_local,
                    'rotulos_referencia': rotulos_ref,
                    'comparacao': comparacao,
                    'relatorio': relatorio
                }
            else:
                logger.warning("Não foi possível carregar a matriz de referência")
                return {
                    'sucesso': False,
                    'erro': 'Falha ao carregar matriz de referência',
                    'matriz_local': matriz_local,
                    'rotulos_local': rotulos_local
                }
        else:
            logger.info("Nenhuma matriz de referência fornecida, apenas gerando a matriz local")
            return {
                'sucesso': True,
                'matriz_local': matriz_local,
                'rotulos_local': rotulos_local,
                'aviso': 'Nenhuma matriz de referência fornecida para comparação'
            }
            
    except Exception as e:
        logger.error("Erro durante o teste: {}".format(e), exc_info=True)
        return {
            'sucesso': False,
            'erro': str(e)
        }
    finally:
        # Limpa os arquivos temporários, se solicitado
        if limpar_temporarios and diretorio_temp.exists():
            try:
                shutil.rmtree(diretorio_temp)
                logger.info(f"Diretório temporário removido: {diretorio_temp}")
            except Exception as e:
                logger.warning("Nao foi possivel remover o diretorio temporario {}: {}".format(diretorio_temp, e))

def test_carregar_matriz_referencia():
    """Testa o carregamento da matriz de referência e dos rótulos."""
    # Caminhos para os arquivos de teste
    diretorio_teste = Path(__file__).parent / "test_data" / "referencia"
    caminho_matriz = diretorio_teste / "matriz_referencia.txt"
    caminho_rotulos = diretorio_teste / "rotulos_referencia.txt"
    
    # Verifica se os arquivos existem
    assert caminho_matriz.exists(), f"Arquivo de matriz não encontrado: {caminho_matriz}"
    assert caminho_rotulos.exists(), f"Arquivo de rótulos não encontrado: {caminho_rotulos}"
    
    # Carrega a matriz e os rótulos
    matriz, rotulos = carregar_matriz_referencia(str(caminho_matriz), str(caminho_rotulos))
    
    # Verifica se a matriz foi carregada corretamente
    assert matriz is not None, "Falha ao carregar a matriz de referência"
    assert len(matriz.shape) == 2, "A matriz deve ser 2D"
    assert matriz.shape[0] == matriz.shape[1], "A matriz deve ser quadrada"
    
    # Verifica se os rótulos foram carregados corretamente
    assert len(rotulos) > 0, "Nenhum rótulo foi carregado"
    assert len(rotulos) == matriz.shape[0], "Número de rótulos deve ser igual à dimensão da matriz"
    
    logger.info("Teste de carregamento da matriz de referência concluído com sucesso!")


def test_comparacao_matrizes():
    """Testa a comparação entre matrizes NCD."""
    # Cria matrizes de teste
    matriz1 = np.array([[0.0, 0.5, 0.7],
                       [0.5, 0.0, 0.3],
                       [0.7, 0.3, 0.0]])
    
    matriz2 = np.array([[0.0, 0.51, 0.71],
                        [0.51, 0.0, 0.29],
                        [0.71, 0.29, 0.0]])
    
    rotulos = ["A", "B", "C"]
    
    # Compara as matrizes
    resultado = comparar_matrizes(matriz1, matriz2, rotulos, rotulos)
    
    # Verifica os resultados
    assert resultado['dimensoes_iguais'], "As matrizes devem ter as mesmas dimensões"
    assert resultado['rotulos_compativeis'], "Os rótulos devem ser compatíveis"
    assert resultado['correlacao'] > 0.9, f"As matrizes devem ser altamente correlacionadas. Correlação: {resultado['correlacao']}"
    assert resultado['diferenca_media'] < 0.02, f"A diferença média deve ser pequena. Diferença: {resultado['diferenca_media']}"
    
    logger.info("Teste de comparação de matrizes concluído com sucesso!")


if __name__ == "__main__":
    import argparse
    
    # Executa os testes se solicitado
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        import pytest
        sys.exit(pytest.main([__file__]))
    
    parser = argparse.ArgumentParser(description='Comparar saída do DAMICORE local com referência')
    parser.add_argument('--dados', required=True, help='Diretório com os dados de entrada')
    parser.add_argument('--referencia', help='Caminho para a matriz de referência (opcional)')
    parser.add_argument('--zlib', action='store_true', help='Usar implementação zlib em vez do DAMICORE')
    parser.add_argument('--compressor', default='gzip', choices=['gzip', 'bzip2', 'ppmd'], 
                       help='Algoritmo de compressão a ser usado com o DAMICORE')
    parser.add_argument('--workers', type=int, default=4, help='Número de processos paralelos')
    parser.add_argument('--manter-temporarios', action='store_true', 
                       help='Manter arquivos temporários após a execução')
    
    args = parser.parse_args()
    
    # Executa o teste
    resultado = executar_teste_comparacao(
        diretorio_dados=args.dados,
        caminho_matriz_ref=args.referencia,
        usar_zlib=args.zlib,
        compressor=args.compressor,
        max_workers=args.workers,
        limpar_temporarios=not args.manter_temporarios
    )
    
    # Exibe um resumo
    if resultado.get('sucesso', False):
        if 'comparacao' in resultado:
            comp = resultado['comparacao']
            print("\n=== RESULTADO DA COMPARACAO ===")
            print("Dimensoes iguais: {}".format(comp.get('dimensoes_iguais', False)))
            print("Rotulos compativeis: {}".format(comp.get('rotulos_compativeis', False)))
            print("Correlacao: {}".format(comp.get('correlacao', 'N/A')))
            print("Diferenca media: {}".format(comp.get('diferenca_media', 'N/A')))
            print("Diferenca maxima: {}".format(comp.get('diferenca_maxima', 'N/A')))
            if 'erro' in comp:
                print("Aviso: {}".format(comp['erro']))
        else:
            print("\nMatriz local gerada com sucesso: {}".format(resultado['matriz_local'].shape))
            if 'aviso' in resultado:
                print("Aviso: {}".format(resultado['aviso']))
    else:
        print("\nERRO: {}".format(resultado.get('erro', 'Erro desconhecido')))
    
    print("\nLogs salvos em: comparacao_damicore.log")
    if 'relatorio' in resultado:
        print("Relatorio salvo em: test_results/comparacao_damicore/relatorio_comparacao.txt")
