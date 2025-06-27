import numpy as np
import pandas as pd
import zlib
import logging
import json
import os
from typing import List, Tuple, Union, Dict, Any, Optional, AnyStr, ByteString

# Configuração de logging
logger = logging.getLogger(__name__)

def ncd_zlib(df, notebook_mode=False, rotulos_referencia=None):
    """
    Função de conveniência para compatibilidade com o código existente.
    Chama ncd_matrix_from_dataframe com os mesmos parâmetros.
    
    Args:
        df: DataFrame de entrada com os dados
        notebook_mode: Se True, exibe logs adicionais
        rotulos_referencia: Lista opcional de rótulos de referência para garantir a ordem
        
    Returns:
        Tuple[np.ndarray, List[str]]: Matriz NCD e lista de rótulos
    """
    return ncd_matrix_from_dataframe(df, notebook_mode, rotulos_referencia)

def ncd_matrix_from_dataframe(df, notebook_mode=False, rotulos_referencia=None):
    """
    Calcula a matriz NCD entre as colunas exportadas do DataFrame.
    Usa zlib para compressão. Retorna matriz numpy e lista de labels.
    
    Args:
        df: DataFrame de entrada com os dados
        notebook_mode: Se True, exibe logs adicionais
        rotulos_referencia: Lista opcional de rótulos de referência para garantir a ordem
        
    Returns:
        Tuple[np.ndarray, List[str]]: Matriz NCD e lista de rótulos
    """
    def to_serializable(obj: Any) -> str:
        """
        Converte valores para formato serializável.
        
        Args:
            obj: Valor a ser convertido
            
        Returns:
            str: Representação em string do objeto
        """
        if obj is None or (hasattr(pd, 'isna') and pd.isna(obj)):
            return ""
        
        # Se for um tipo numérico, converter para string
        if isinstance(obj, (int, float, bool)):
            return str(obj)
        
        # Se for string, retorna direto
        if isinstance(obj, str):
            return obj
        
        # Se for um tipo numpy, converte para Python nativo
        if hasattr(obj, 'item'):
            try:
                return str(obj.item())
            except (ValueError, TypeError):
                pass
        
        # Tenta converter para JSON se for um dicionário ou lista
        try:
            return json.dumps(obj, ensure_ascii=False)
        except (TypeError, ValueError):
            pass
        
        # Último recurso: converter para string
        try:
            return str(obj)
        except Exception as e:
            logging.warning(f"Erro ao serializar {type(obj)}: {e}")
            return ""

    # Processa cada coluna
    processed_columns = {}
    labels = []
    
    # Se houver rótulos de referência, garante que estão na ordem correta
    if rotulos_referencia is not None:
        # Remove extensão .txt dos nomes das colunas do DataFrame para comparação
        colunas_sem_extensao = [os.path.splitext(col)[0] for col in df.columns]
        
        # Cria um mapeamento de nome sem extensão para nome com extensão
        mapeamento_colunas = {os.path.splitext(col)[0]: col for col in df.columns}
        
        # Encontra a interseção mantendo a ordem dos rótulos de referência
        colunas_validas = []
        for rotulo in rotulos_referencia:
            # Remove .txt se presente para comparação
            rotulo_base = os.path.splitext(rotulo)[0]
            if rotulo_base in mapeamento_colunas:
                colunas_validas.append(mapeamento_colunas[rotulo_base])
        
        if len(colunas_validas) < 2:
            raise ValueError(f"Pelo menos 2 colunas válidas são necessárias para calcular a matriz NCD. Encontradas: {len(colunas_validas)}")
        
        # Usa a ordem dos rótulos de referência
        colunas_para_processar = colunas_validas
        
        if notebook_mode:
            logger.info(f"Processando {len(colunas_para_processar)} colunas na ordem dos rótulos de referência")
            logger.debug(f"Colunas a serem processadas: {colunas_para_processar}")
    else:
        # Usa todas as colunas do DataFrame na ordem original
        colunas_para_processar = df.columns
    
    for col in colunas_para_processar:
        try:
            # Converte para string e remove valores vazios
            col_data = df[col].dropna().apply(to_serializable)
            col_data = col_data[col_data != ""]
            
            if len(col_data) < 2:
                logger.warning(f"Coluna '{col}' tem menos de 2 valores válidos e será ignorada")
                continue
                
            # Junta todos os valores em uma única string
            processed_columns[col] = "\n".join(col_data)
            labels.append(col)
            
            if notebook_mode:
                logger.info(f"Processada coluna: {col} com {len(col_data)} linhas")
                
        except Exception as e:
            logger.error(f"Erro ao processar coluna {col}: {e}")
            continue
    
    n = len(processed_columns)
    if n == 0:
        raise ValueError("Nenhuma coluna válida encontrada para processamento")
        
    # Garante que temos pelo menos 2 colunas
    if n < 2:
        raise ValueError(f"Pelo menos 2 colunas válidas são necessárias. Encontradas: {n}")
        
    # Se houver rótulos de referência, verifica se todas as colunas foram encontradas
    if rotulos_referencia is not None:
        # Remove extensões para comparação
        labels_sem_ext = [os.path.splitext(l)[0] for l in labels]
        ref_sem_ext = [os.path.splitext(r)[0] for r in rotulos_referencia]
        
        # Encontra rótulos faltantes
        faltantes = [r for r in ref_sem_ext if r not in labels_sem_ext]
        
        if faltantes:
            logger.warning(f"{len(faltantes)} rótulos de referência não encontrados nos dados: {faltantes[:10]}{'...' if len(faltantes) > 10 else ''}")
        
        if n != len(rotulos_referencia):
            logger.warning(f"Número de colunas processadas ({n}) difere do número de rótulos de referência ({len(rotulos_referencia)})")
            logger.debug(f"Colunas processadas: {labels}")
            logger.debug(f"Rótulos de referência: {rotulos_referencia}")
    
    # Inicializa a matriz
    ncd_mat = np.zeros((n, n))
    
    # Função auxiliar para calcular tamanho comprimido
    def compressed_size(s):
        return len(zlib.compress(s.encode('utf-8')))
    
    # Pré-calcula os tamanhos comprimidos
    sizes = {}
    for col, s in processed_columns.items():
        try:
            sizes[col] = compressed_size(s)
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho comprimido para {col}: {e}")
            # Usa um valor padrão alto para evitar divisão por zero
            sizes[col] = 1e6
    
    # Preenche a matriz de forma simétrica
    cols = list(processed_columns.keys())
    
    # Verifica se temos tamanhos válidos
    if not sizes:
        raise ValueError("Nenhum tamanho de compressão válido calculado")
    
    # Preenche a diagonal principal com zeros
    np.fill_diagonal(ncd_mat, 0.0)
    
    # Preenche o restante da matriz
    for i in range(n):
        for j in range(i+1, n):  # Apenas metade superior (sem a diagonal)
            try:
                s1 = processed_columns[cols[i]]
                s2 = processed_columns[cols[j]]
                
                c_x = sizes[cols[i]]
                c_y = sizes[cols[j]]
                
                # Evita divisão por zero
                if c_x == 0 or c_y == 0:
                    ncd = 1.0  # Máxima distância se um dos tamanhos for zero
                else:
                    # Calcula o tamanho da concatenação
                    c_xy = compressed_size(s1 + s2)
                    
                    # Calcula NCD normalizado
                    ncd = (c_xy - min(c_x, c_y)) / max(c_x, c_y)
                    ncd = max(0.0, min(1.0, ncd))  # Garante entre 0 e 1
                
                ncd_mat[i, j] = ncd
                ncd_mat[j, i] = ncd  # Mantém a simetria
                
            except Exception as e:
                logger.error(f"Erro ao calcular NCD entre {cols[i]} e {cols[j]}: {e}")
                ncd = 1.0  # Máxima distância em caso de erro
                ncd_mat[i, j] = ncd
                ncd_mat[j, i] = ncd
    
    return ncd_mat, labels
