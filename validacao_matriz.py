"""Módulo de validação de matrizes de distância para o pipeline DAMICORE.

Este módulo fornece funções para validar e processar matrizes de distância, garantindo
que estejam no formato correto para geração de árvores filogenéticas.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any

def validar_matriz_distancia(matriz: np.ndarray) -> Tuple[bool, str]:
    """Valida uma matriz de distância quanto ao formato e valores.
    
    Args:
        matriz: Matriz de distância a ser validada
        
    Returns:
        tuple: (sucesso, mensagem) onde sucesso é booleano indicando se a validação 
              foi bem-sucedida e mensagem contém detalhes sobre qualquer problema encontrado.
    """
    # Verifica se é um array numpy
    if not isinstance(matriz, np.ndarray):
        return False, "A matriz de distância deve ser um array NumPy"
    
    # Verifica a dimensionalidade
    if matriz.ndim != 2:
        return False, f"A matriz deve ser 2D, mas tem {matriz.ndim} dimensões"
    
    # Verifica se é quadrada
    n_linhas, n_colunas = matriz.shape
    if n_linhas != n_colunas:
        return False, f"A matriz deve ser quadrada, mas tem formato {n_linhas}x{n_colunas}"
    
    # Verifica valores NaN ou infinitos
    if np.any(np.isnan(matriz)):
        return False, "A matriz contém valores NaN"
        
    if np.any(np.isinf(matriz)):
        return False, "A matriz contém valores infinitos"
    
    # Verifica se a diagonal principal é zero
    if not np.allclose(np.diag(matriz), 0):
        return False, "A diagonal principal da matriz deve conter apenas zeros"
    
    # Verifica simetria (com tolerância para erros de ponto flutuante)
    if not np.allclose(matriz, matriz.T, atol=1e-8):
        return False, "A matriz de distância não é simétrica"
    
    # Verifica se todos os valores são não-negativos
    if np.any(matriz < 0):
        return False, "A matriz contém valores negativos"
    
    return True, "Matriz de distância válida"

def processar_matriz_distancia(matriz: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Processa uma matriz de distância, garantindo que esteja no formato correto.
    
    Esta função aplica correções comuns a matrizes de distância, como garantir
    simetria, valores não-negativos e diagonal zero.
    
    Args:
        matriz: Matriz de distância a ser processada
        
    Returns:
        tuple: (matriz_processada, metadados) onde matriz_processada é a matriz 
              após o processamento e metadados contém informações sobre as alterações
              realizadas.
    """
    metadados = {
        'alteracoes': [],
        'avaliacao': 'A matriz foi validada com sucesso sem necessidade de correções.'
    }
    
    # Faz uma cópia para não modificar a matriz original
    matriz_proc = matriz.copy()
    
    # 1. Garante que a diagonal seja zero
    if not np.allclose(np.diag(matriz_proc), 0):
        np.fill_diagonal(matriz_proc, 0)
        metadados['alteracoes'].append('Diagonal principal definida como zero')
    
    # 2. Garante simetria
    if not np.allclose(matriz_proc, matriz_proc.T, atol=1e-8):
        # Calcula a média entre a matriz e sua transposta para garantir simetria
        matriz_proc = (matriz_proc + matriz_proc.T) / 2
        metadados['alteracoes'].append('Matriz tornada simétrica')
    
    # 3. Remove valores negativos (se houver)
    if np.any(matriz_proc < 0):
        matriz_proc = np.maximum(matriz_proc, 0)
        metadados['alteracoes'].append('Valores negativos definidos como zero')
    
    # 4. Remove valores NaN ou infinitos (substituindo por zero)
    if np.any(~np.isfinite(matriz_proc)):
        matriz_proc[~np.isfinite(matriz_proc)] = 0
        metadados['alteracoes'].append('Valores NaN ou infinitos substituídos por zero')
    
    # Atualiza a mensagem de avaliação se houver alterações
    if metadados['alteracoes']:
        metadados['avaliacao'] = "Foram aplicadas as seguintes correções: " + 
                                "; ".join(metadados['alteracoes'])
    
    return matriz_proc, metadados

def validar_e_processar_matriz(matriz: np.ndarray) -> Tuple[bool, str, Optional[np.ndarray], Dict[str, Any]]:
    """Valida e processa uma matriz de distância.
    
    Combina validação e processamento em uma única função conveniente.
    
    Args:
        matriz: Matriz de distância a ser validada e processada
        
    Returns:
        tuple: (sucesso, mensagem, matriz_processada, metadados) onde:
            - sucesso: booleano indicando se a validação foi bem-sucedida
            - mensagem: string com detalhes sobre a validação/processamento
            - matriz_processada: matriz após o processamento (ou None se falhar)
            - metadados: dicionário com informações adicionais
    """
    # Primeiro valida a matriz
    valido, mensagem = validar_matriz_distancia(matriz)
    
    if not valido:
        # Tenta processar a matriz para corrigir problemas comuns
        try:
            matriz_proc, metadados = processar_matriz_distancia(matriz)
            # Valida novamente após o processamento
            valido, msg_pos_processamento = validar_matriz_distancia(matriz_proc)
            if valido:
                return True, f"Matriz corrigida com sucesso. {msg_pos_processamento}", matriz_proc, metadados
            else:
                return False, f"Não foi possível corrigir a matriz: {mensagem}", None, {}
        except Exception as e:
            return False, f"Erro ao processar a matriz: {str(e)}", None, {}
    else:
        # Matriz já é válida, retorna sem processamento adicional
        return True, mensagem, matriz, {'avaliacao': 'Matriz válida sem necessidade de correção'}

# Funções auxiliares para análise da matriz
def analisar_matriz_distancia(matriz: np.ndarray) -> Dict[str, Any]:
    """Analisa uma matriz de distância, fornecendo estatísticas úteis.
    
    Args:
        matriz: Matriz de distância a ser analisada
        
    Returns:
        dict: Dicionário com estatísticas da matriz
    """
    # Cria uma máscara para os elementos fora da diagonal
    mask = ~np.eye(matriz.shape[0], dtype=bool)
    
    # Obtém os valores fora da diagonal
    valores = matriz[mask]
    
    return {
        'tamanho': matriz.shape[0],
        'min': float(np.min(valores)) if valores.size > 0 else 0,
        'max': float(np.max(valores)) if valores.size > 0 else 0,
        'media': float(np.mean(valores)) if valores.size > 0 else 0,
        'mediana': float(np.median(valores)) if valores.size > 0 else 0,
        'desvio_padrao': float(np.std(valores)) if valores.size > 0 else 0,
        'simetrica': bool(np.allclose(matriz, matriz.T, atol=1e-8)),
        'diagonal_zero': bool(np.allclose(np.diag(matriz), 0)),
        'valores_negativos': int(np.sum(matriz < 0)),
        'valores_nan': int(np.sum(np.isnan(matriz))),
        'valores_inf': int(np.sum(np.isinf(matriz)))
    }
