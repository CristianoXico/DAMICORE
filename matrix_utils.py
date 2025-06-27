"""
Módulo de utilidades para manipulação e validação de matrizes NCD.

Este módulo fornece funções para copiar, validar e alinhar matrizes NCD e seus rótulos.
"""

import os
import shutil
import numpy as np
from typing import Tuple, Dict, List, Optional, Union, Any
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def copy_reference_matrix(
    source_matrix: np.ndarray,
    source_labels: List[str],
    output_dir: str,
    reference_name: str = "reference"
) -> Tuple[bool, str]:
    """
    Copia a matriz de referência e seus rótulos para o diretório de saída.
    
    Args:
        source_matrix: Matriz NumPy a ser salva
        source_labels: Lista de rótulos correspondentes às linhas/colunas da matriz
        output_dir: Diretório de saída onde a matriz será salva
        reference_name: Nome base para os arquivos de saída
        
    Returns:
        Tuple[bool, str]: (sucesso, mensagem) indicando o resultado da operação
    """
    try:
        # Cria o diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Define os caminhos dos arquivos de saída
        matrix_path = os.path.join(output_dir, f"{reference_name}_matrix.npy")
        labels_path = os.path.join(output_dir, f"{reference_name}_labels.txt")
        
        # Salva a matriz em formato binário do NumPy
        np.save(matrix_path, source_matrix)
        
        # Salva os rótulos em um arquivo de texto
        with open(labels_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(source_labels))
        
        logger.info(f"Matriz de referência salva em: {matrix_path}")
        logger.info(f"Rótulos de referência salvos em: {labels_path}")
        
        return True, "Matriz de referência copiada com sucesso"
        
    except Exception as e:
        error_msg = f"Erro ao copiar matriz de referência: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def validate_matrix(matrix: np.ndarray, matrix_name: str = "matriz") -> Tuple[bool, str]:
    """
    Valida se uma matriz está em um formato adequado para comparação.
    
    Args:
        matrix: Matriz a ser validada
        matrix_name: Nome da matriz para mensagens de erro
        
    Returns:
        Tuple[bool, str]: (válida, mensagem) indicando se a matriz é válida
    """
    if matrix.size == 0:
        return False, f"{matrix_name} está vazia"
        
    if not np.isfinite(matrix).all():
        return False, f"{matrix_name} contém valores não finitos (NaN ou inf)"
        
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return False, f"{matrix_name} deve ser uma matriz quadrada"
        
    # Verifica se a matriz é simétrica (com tolerância para erros de ponto flutuante)
    if not np.allclose(matrix, matrix.T, atol=1e-8):
        return False, f"{matrix_name} não é simétrica"
        
    # Verifica se a diagonal é zero (com tolerância para erros de ponto flutuante)
    if not np.allclose(np.diag(matrix), 0, atol=1e-8):
        return False, f"Diagonal de {matrix_name} não é zero"
        
    return True, f"{matrix_name} válida"

def align_matrices(
    matrix1: np.ndarray, 
    labels1: List[str],
    matrix2: np.ndarray, 
    labels2: List[str]
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[str], str]:
    """
    Alinha duas matrizes NCD com base em seus rótulos.
    
    Args:
        matrix1: Primeira matriz NCD
        labels1: Rótulos da primeira matriz
        matrix2: Segunda matriz NCD
        labels2: Rótulos da segunda matriz
        
    Returns:
        Tuple contendo:
        - Matriz1 alinhada (ou None em caso de erro)
        - Matriz2 alinhada (ou None em caso de erro)
        - Rótulos alinhados (na ordem da primeira matriz)
        - Mensagem de status
    """
    try:
        logger.debug("="*50)
        logger.debug("INÍCIO DO ALINHAMENTO DE MATRIZES")
        logger.debug("="*50)
        
        # Log detalhado das matrizes de entrada
        logger.debug(f"Matriz 1 original ({len(labels1)}x{len(labels1)}):")
        logger.debug(f"Rótulos: {labels1}")
        logger.debug(f"Valores:\n{matrix1}")
        
        logger.debug(f"\nMatriz 2 original ({len(labels2)}x{len(labels2)}):")
        logger.debug(f"Rótulos: {labels2}")
        logger.debug(f"Valores:\n{matrix2}")
        
        # Encontra a interseção dos rótulos, mantendo a ordem da primeira matriz
        common_labels = [label for label in labels1 if label in set(labels2)]
        logger.debug(f"\nRótulos comuns (ordem da matriz 1): {common_labels}")
        
        if not common_labels:
            return None, None, [], "Nenhum rótulo em comum entre as matrizes"
        
        # Para a primeira matriz, mantemos a ordem dos rótulos
        idx1 = [labels1.index(label) for label in common_labels]
        logger.debug(f"\nÍndices na matriz 1 para os rótulos comuns: {idx1}")
        aligned_matrix1 = matrix1[np.ix_(idx1, idx1)]
        
        # Para a segunda matriz, precisamos extrair os valores corretos com base nos rótulos comuns
        # Primeiro, obtemos os índices na ordem em que aparecem na segunda matriz
        idx2 = [labels2.index(label) for label in common_labels]
        logger.debug(f"Índices na matriz 2 para os rótulos comuns: {idx2}")
        
        # Extraímos os valores da matriz 2 usando os índices corretos
        # Precisamos garantir que estamos pegando os valores corretos para cada par de rótulos
        n = len(common_labels)
        aligned_matrix2 = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                # Obtemos os índices dos rótulos na matriz 2
                idx_i = labels2.index(common_labels[i])
                idx_j = labels2.index(common_labels[j])
                aligned_matrix2[i, j] = matrix2[idx_i, idx_j]
        
        logger.debug(f"\nMatriz 2 alinhada (extração manual):\n{aligned_matrix2}")
        
        # Verificamos se a matriz resultante é simétrica
        if not np.allclose(aligned_matrix2, aligned_matrix2.T, atol=1e-8):
            logger.warning("A matriz alinhada 2 não é simétrica!")
        
        # Garantimos que a diagonal seja zero
        np.fill_diagonal(aligned_matrix2, 0)
        
        logger.debug("\n" + "="*50)
        logger.debug("RESULTADO FINAL DO ALINHAMENTO")
        logger.debug("="*50)
        logger.debug(f"Matriz 1 alinhada ({len(common_labels)}x{len(common_labels)}):")
        logger.debug(f"Rótulos: {common_labels}")
        logger.debug(f"Valores:\n{aligned_matrix1}")
        
        logger.debug(f"\nMatriz 2 alinhada ({len(common_labels)}x{len(common_labels)}):")
        logger.debug(f"Rótulos: {common_labels}")
        logger.debug(f"Valores:\n{aligned_matrix2}")
        
        return aligned_matrix1, aligned_matrix2, common_labels, "Matrizes alinhadas com sucesso"
        
    except Exception as e:
        error_msg = f"Erro ao alinhar matrizes: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, None, [], error_msg

def compare_matrices(
    matrix1: np.ndarray,
    matrix2: np.ndarray,
    labels1: List[str],
    labels2: List[str],
    output_dir: str
) -> Dict[str, Any]:
    """
    Compara duas matrizes NCD e gera métricas de comparação.
    
    Args:
        matrix1: Primeira matriz NCD
        matrix2: Segunda matriz NCD
        labels1: Rótulos da primeira matriz
        labels2: Rótulos da segunda matriz
        output_dir: Diretório para salvar os resultados
        
    Returns:
        Dicionário com os resultados da comparação
    """
    result = {
        'success': False,
        'message': '',
        'common_labels': [],
        'matrix1_shape': matrix1.shape,
        'matrix2_shape': matrix2.shape,
        'comparison_metrics': {}
    }
    
    try:
        # Valida as matrizes de entrada
        valid1, msg1 = validate_matrix(matrix1, "Matriz 1")
        if not valid1:
            result['message'] = f"Matriz 1 inválida: {msg1}"
            return result
            
        valid2, msg2 = validate_matrix(matrix2, "Matriz 2")
        if not valid2:
            result['message'] = f"Matriz 2 inválida: {msg2}"
            return result
        
        # Alinha as matrizes
        aligned1, aligned2, common_labels, align_msg = align_matrices(
            matrix1, labels1, matrix2, labels2
        )
        
        if aligned1 is None or aligned2 is None:
            result['message'] = f"Falha ao alinhar matrizes: {align_msg}"
            return result
            
        # Calcula métricas de comparação
        diff = np.abs(aligned1 - aligned2)
        
        metrics = {
            'num_common_labels': len(common_labels),
            'mean_absolute_difference': float(np.mean(diff)),
            'max_absolute_difference': float(np.max(diff)),
            'min_absolute_difference': float(np.min(diff)),
            'std_absolute_difference': float(np.std(diff)),
            'correlation': float(np.corrcoef(aligned1.flatten(), aligned2.flatten())[0, 1])
        }
        
        # Salva as matrizes alinhadas
        os.makedirs(output_dir, exist_ok=True)
        np.savetxt(os.path.join(output_dir, 'aligned_matrix1.csv'), aligned1, delimiter=',')
        np.savetxt(os.path.join(output_dir, 'aligned_matrix2.csv'), aligned2, delimiter=',')
        
        with open(os.path.join(output_dir, 'common_labels.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(common_labels))
        
        # Atualiza o resultado
        result.update({
            'success': True,
            'message': 'Comparação concluída com sucesso',
            'common_labels': common_labels,
            'comparison_metrics': metrics,
            'aligned_matrix1': aligned1,
            'aligned_matrix2': aligned2
        })
        
        return result
        
    except Exception as e:
        error_msg = f"Erro ao comparar matrizes: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['message'] = error_msg
        return result
