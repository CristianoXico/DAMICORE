"""
Módulo para análise de Pareto e otimização multiobjetivo.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
import os
from datetime import datetime


def identificar_fronteira_pareto(df: pd.DataFrame, objetivos: List[str], 
                               maximizar: Union[bool, List[bool]] = True) -> pd.DataFrame:
    """
    Identifica a fronteira de Pareto para múltiplos objetivos.
    
    Args:
        df: DataFrame com os dados
        objetivos: Lista de nomes das colunas que são objetivos
        maximizar: Se True, maximiza os objetivos. Pode ser uma lista com um valor por objetivo.
                 
    Returns:
        DataFrame contendo apenas as soluções não-dominadas (fronteira de Pareto)
    """
    # Converte para array numpy para operações vetorizadas
    data = df[objetivos].values
    n_objetivos = len(objetivos)
    
    # Se maximizar for um único booleano, aplica a todos os objetivos
    if isinstance(maximizar, bool):
        maximizar = [maximizar] * n_objetivos
    
    # Inverte os objetivos que devem ser minimizados
    for i in range(n_objetivos):
        if not maximizar[i]:
            data[:, i] = -data[:, i]
    
    n_solucoes = len(data)
    nao_dominadas = np.ones(n_solucoes, dtype=bool)
    
    # Compara cada par de soluções para encontrar as não-dominadas
    for i in range(n_solucoes):
        if nao_dominadas[i]:
            # Encontra todas as soluções dominadas por i
            dominadas = np.all(data <= data[i], axis=1)
            # Marca como dominadas as que são piores em todos os objetivos
            dominadas[i] = False  # Não marca a si mesma
            nao_dominadas[dominadas] = False
    
    return df[nao_dominadas].copy()


def calcular_hipervolume(pontos: np.ndarray, ponto_referencia: np.ndarray) -> float:
    """
    Calcula o hipervolume dominado por um conjunto de pontos.
    
    Args:
        pontos: Array com os pontos da fronteira de Pareto (cada linha é um ponto)
        ponto_referencia: Ponto de referência (pior ponto possível)
        
    Returns:
        Valor do hipervolume
    """
    if len(pontos) == 0:
        return 0.0
        
    # Ordena os pontos
    pontos = np.asarray(pontos)
    n_pontos, n_dims = pontos.shape
    
    # Ordena os pontos pela primeira dimensão
    idx = np.argsort(pontos[:, 0])
    pontos = pontos[idx]
    
    # Função recursiva para cálculo do hipervolume
    def hv_volume(pontos, n_dims, volume, count):
        while True:
            if n_dims == 1:
                # Caso base: calcula o comprimento
                return volume * (ponto_referencia[0] - pontos[-1, 0])
            elif n_dims == 2:
                # Caso 2D: soma as áreas dos retângulos
                return volume * sum(
                    (ponto_referencia[0] - pontos[i, 0]) * 
                    (ponto_referencia[1] - pontos[i, 1])
                    for i in range(len(pontos))
                )
            else:
                # Para mais dimensões, usa o algoritmo de cálculo recursivo
                volume *= ponto_referencia[-1] - pontos[-1, -1]
                pontos = pontos[:-1, :-1]
                n_dims -= 1
    
    return hv_volume(pontos, n_dims, 1.0, 0)


def normalizar_fronteira(df: pd.DataFrame, objetivos: List[str]) -> pd.DataFrame:
    """
    Normaliza os valores da fronteira de Pareto para o intervalo [0, 1].
    
    Args:
        df: DataFrame com os dados
        objetivos: Lista de nomes das colunas que são objetivos
        
    Returns:
        DataFrame com os valores normalizados
    """
    df_norm = df.copy()
    for obj in objetivos:
        min_val = df[obj].min()
        max_val = df[obj].max()
        if max_val > min_val:  # Evita divisão por zero
            df_norm[obj] = (df[obj] - min_val) / (max_val - min_val)
        else:
            df_norm[obj] = 0.5  # Valor padrão se todos forem iguais
    return df_norm


def exportar_resultados_pareto(
    df_fronteira: pd.DataFrame, 
    variaveis_objetivo: List[str],
    diretorio_saida: str,
    prefixo: str = "pareto"
) -> str:
    """
    Exporta os resultados da análise de Pareto para um arquivo CSV.
    
    Args:
        df_fronteira: DataFrame com a fronteira de Pareto
        variaveis_objetivo: Lista com os nomes das variáveis objetivo
        diretorio_saida: Diretório onde o arquivo será salvo
        prefixo: Prefixo para o nome do arquivo
        
    Returns:
        Caminho completo para o arquivo salvo
    """
    # Cria o diretório se não existir
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Gera um nome de arquivo único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{prefixo}_{'_'.join(variaveis_objetivo)[:50]}_{timestamp}.csv"
    caminho_arquivo = os.path.join(diretorio_saida, nome_arquivo)
    
    # Salva o DataFrame em CSV
    df_fronteira.to_csv(caminho_arquivo, index=False, encoding='utf-8')
    
    return caminho_arquivo


def analisar_fronteira_pareto(
    df: pd.DataFrame,
    variaveis_objetivo: List[str],
    maximizar: Union[bool, List[bool]] = True,
    normalizar: bool = True,
    calcular_hipervol: bool = True,
    ponto_referencia: Optional[np.ndarray] = None
) -> Dict[str, any]:
    """
    Realiza uma análise completa da fronteira de Pareto.
    
    Args:
        df: DataFrame com os dados
        variaveis_objetivo: Lista de nomes das colunas que são objetivos
        maximizar: Se True, maximiza os objetivos. Pode ser uma lista com um valor por objetivo.
        normalizar: Se True, normaliza os valores dos objetivos para [0, 1]
        calcular_hipervol: Se True, calcula o hipervolume da fronteira
        ponto_referencia: Ponto de referência para cálculo do hipervolume (opcional)
        
    Returns:
        Dicionário com os resultados da análise
    """
    # Faz uma cópia para não modificar o DataFrame original
    df_analise = df.copy()
    
    # Identifica a fronteira de Pareto
    df_fronteira = identificar_fronteira_pareto(
        df_analise, variaveis_objetivo, maximizar
    )
    
    # Normaliza os valores se solicitado
    if normalizar:
        df_fronteira = normalizar_fronteira(df_fronteira, variaveis_objetivo)
    
    # Calcula o hipervolume se solicitado
    hipervolume = None
    if calcular_hipervol and len(df_fronteira) > 0:
        if ponto_referencia is None:
            # Define um ponto de referência pior que todos os pontos
            ponto_referencia = np.ones(len(variaveis_objetivo)) * 1.1  # 10% acima do máximo normalizado
        pontos = df_fronteira[variaveis_objetivo].values
        hipervolume = calcular_hipervolume(pontos, ponto_referencia)
    
    # Prepara o resultado
    resultado = {
        'fronteira': df_fronteira,
        'n_solucoes': len(df_fronteira),
        'variaveis_objetivo': variaveis_objetivo,
        'maximizar': maximizar if isinstance(maximizar, list) else [maximizar] * len(variaveis_objetivo),
        'normalizado': normalizar,
        'hipervolume': hipervolume,
        'ponto_referencia': ponto_referencia.tolist() if ponto_referencia is not None else None
    }
    
    return resultado
