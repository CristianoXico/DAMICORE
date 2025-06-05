import pandas as pd
import numpy as np
from unidecode import unidecode
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import json


def normalize_columns(df):
    """
    Normaliza os nomes das colunas: translitera e remove caracteres especiais.
    Retorna novo DataFrame e dicionário de mapeamento.
    """
    chars2replac = ['_', ' ', '[', ']', '/', '.', '%', '(', ')']
    col_map = {}
    new_cols = []
    for col in df.columns:
        fname = unidecode(str(col))
        for c in chars2replac:
            fname = fname.replace(c, '')
        col_map[fname] = str(col)
        new_cols.append(fname)
    df_norm = df.copy()
    df_norm.columns = new_cols
    return df_norm, col_map


def fuzzy_partition_placeholder(df):
    """
    Placeholder para lógica de partição fuzzy.
    No momento, retorna o DataFrame sem alterações.
    """
    # TODO: Implementar partição fuzzy real
    return df


def build_category_tree(df, n_categories=2, mode="best", criterio_vars=None):
    """
    Gera uma árvore de decisão genérica para n_categories mostrando índices e nomes dos leaves.
    Se criterio_vars for passado, usa apenas essas colunas.
    """
    if criterio_vars is not None:
        leaf_vars = [(df.columns.get_loc(col), col) for col in criterio_vars]
    else:
        leaf_vars = list(enumerate(df.columns))
    if n_categories > len(leaf_vars):
        n_categories = len(leaf_vars)
    selected = leaf_vars[:n_categories]
    tree_str = "ROOT\n"
    for i, (idx, name) in enumerate(selected):
        label = f"[{mode.upper()} {i+1}]"
        tree_str += f"|-- {label} LEAF ({idx}: {name})\n"
    return tree_str

def print_full_tree(df):
    """
    Exibe uma árvore completa (dendrograma simples) mostrando todos os índices e nomes das colunas do DataFrame.
    """
    leaves = list(enumerate(df.columns))
    def build_ascii_tree(leaves, prefix="", is_last=True):
        if len(leaves) == 1:
            idx, name = leaves[0]
            branch = "`-- " if is_last else "|-- "
            return f"{prefix}{branch}{idx}: {name}\n"
        mid = len(leaves) // 2
        left = build_ascii_tree(leaves[:mid], prefix + ("    " if is_last else "|   "), False)
        right = build_ascii_tree(leaves[mid:], prefix + ("    " if is_last else "|   "), True)
        return left + right
    tree_str = build_ascii_tree(leaves, "", True)
    print("Árvore completa de variáveis (índice: nome):")
    print(tree_str)

def calcular_dispersao_por_grupo(df: pd.DataFrame, coluna_grupo: str, variaveis: List[str]) -> pd.DataFrame:
    """
    Calcula métricas de dispersão para cada variável em cada grupo.
    
    Args:
        df: DataFrame com os dados
        coluna_grupo: Nome da coluna que contém os grupos
        variaveis: Lista de variáveis para análise
        
    Returns:
        DataFrame com as métricas de dispersão por grupo e variável
    """
    resultados = []
    
    for grupo in df[coluna_grupo].unique():
        grupo_df = df[df[coluna_grupo] == grupo]
        
        for var in variaveis:
            if var == coluna_grupo:
                continue
                
            if pd.api.types.is_numeric_dtype(grupo_df[var]):
                # Para variáveis numéricas, calcula média, desvio padrão e coeficiente de variação
                media = grupo_df[var].mean()
                desvio = grupo_df[var].std()
                cv = (desvio / media) * 100 if media != 0 else float('inf')
                
                resultados.append({
                    'grupo': grupo,
                    'variavel': var,
                    'tipo': 'numerica',
                    'media': media,
                    'desvio_padrao': desvio,
                    'coef_variacao': cv,
                    'mediana': grupo_df[var].median(),
                    'q1': grupo_df[var].quantile(0.25),
                    'q3': grupo_df[var].quantile(0.75)
                })
            else:
                # Para variáveis categóricas, calcula moda e contagem de categorias
                contagem = grupo_df[var].value_counts()
                moda = contagem.idxmax() if not contagem.empty else None
                
                resultados.append({
                    'grupo': grupo,
                    'variavel': var,
                    'tipo': 'categorica',
                    'moda': moda,
                    'n_categorias': len(contagem),
                    'frequencia_moda': contagem.max() if not contagem.empty else 0,
                    'total': len(grupo_df[var].dropna())
                })
    
    return pd.DataFrame(resultados)

def selecionar_variaveis_por_dispersao(df: pd.DataFrame, coluna_grupo: str, n_variaveis: int = 8) -> List[str]:
    """
    Seleciona as variáveis mais discriminantes com base na dispersão entre grupos.
    
    Args:
        df: DataFrame com os dados
        coluna_grupo: Nome da coluna que contém os grupos
        n_variaveis: Número de variáveis a serem selecionadas
        
    Returns:
        Lista com os nomes das variáveis selecionadas
    """
    # Identifica variáveis numéricas e categóricas
    variaveis_numericas = df.select_dtypes(include=['number']).columns.tolist()
    variaveis_categoricas = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Remove a coluna de grupo das variáveis a serem analisadas
    if coluna_grupo in variaveis_numericas:
        variaveis_numericas.remove(coluna_grupo)
    if coluna_grupo in variaveis_categoricas:
        variaveis_categoricas.remove(coluna_grupo)
    
    # Calcula a dispersão para cada tipo de variável
    resultados = []
    
    # Para variáveis numéricas: usa o coeficiente de variação entre grupos
    if variaveis_numericas:
        dispersao_numericas = calcular_dispersao_por_grupo(
            df, coluna_grupo, variaveis_numericas
        )
        
        # Calcula a média do coeficiente de variação por variável
        cv_por_variavel = dispersao_numericas.groupby('variavel')['coef_variacao'].mean()
        
        # Ordena por maior CV (maior variabilidade entre grupos)
        cv_por_variavel = cv_por_variavel.sort_values(ascending=False)
        
        # Adiciona ao resultado
        for var, cv in cv_por_variavel.items():
            resultados.append({
                'variavel': var,
                'tipo': 'numerica',
                'score': cv,
                'metrica': 'coef_variacao_medio'
            })
    
    # Para variáveis categóricas: usa a entropia entre grupos
    if variaveis_categoricas:
        for var in variaveis_categoricas:
            # Calcula a entropia da distribuição entre grupos
            tabela_contingencia = pd.crosstab(df[var], df[coluna_grupo])
            proporcoes = tabela_contingencia.div(tabela_contingencia.sum(axis=0), axis=1)
            entropias = (-proporcoes * np.log2(proporcoes + 1e-10)).sum(axis=0)
            entropia_media = entropias.mean()
            
            resultados.append({
                'variavel': var,
                'tipo': 'categorica',
                'score': entropia_media,
                'metrica': 'entropia_media'
            })
    
    # Converte para DataFrame e ordena pelo score
    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.sort_values('score', ascending=False)
    
    # Seleciona as N melhores variáveis
    melhores_variaveis = df_resultados.head(n_variaveis)['variavel'].tolist()
    
    return melhores_variaveis

def aplicar_fs_opa(df: pd.DataFrame, n_variaveis: int = 8) -> Dict[str, Any]:
    """
    Aplica a metodologia FS OPA para seleção de variáveis.
    
    Args:
        df: DataFrame com os dados
        n_variaveis: Número de variáveis a serem selecionadas
        
    Returns:
        Dicionário com as variáveis selecionadas e estatísticas
    """
    # Verifica se há uma coluna de grupo/cluster
    if 'cluster' not in df.columns:
        raise ValueError("O DataFrame deve conter uma coluna 'cluster' com os grupos")
    
    # Normaliza os nomes das colunas
    df_norm, col_map = normalize_columns(df)
    
    # Mapeia a coluna de cluster de volta para o nome normalizado se necessário
    coluna_grupo = 'cluster'
    if coluna_grupo not in df_norm.columns and coluna_grupo in col_map.values():
        # Encontra o nome normalizado da coluna de cluster
        coluna_grupo = next(k for k, v in col_map.items() if v == coluna_grupo)
    
    # Seleciona as variáveis mais discriminantes
    variaveis_selecionadas = selecionar_variaveis_por_dispersao(
        df_norm, coluna_grupo, n_variaveis
    )
    
    # Prepara o resultado
    resultado = {
        'variaveis_selecionadas': variaveis_selecionadas,
        'total_variaveis_analisadas': len(df_norm.columns) - 1,  # -1 para a coluna de cluster
        'coluna_grupo': col_map.get(coluna_grupo, coluna_grupo),
        'variaveis_por_tipo': {
            'numericas': df_norm.select_dtypes(include=['number']).columns.tolist(),
            'categoricas': df_norm.select_dtypes(include=['object', 'category']).columns.tolist()
        }
    }
    
    return resultado

def exportar_resultados_fs_opa(resultado: Dict[str, Any], diretorio_saida: str) -> str:
    """
    Exporta os resultados da análise FS-OPA para arquivos.
    
    Args:
        resultado: Dicionário com os resultados da análise
        diretorio_saida: Diretório onde os arquivos serão salvos
        
    Returns:
        Caminho para o arquivo principal de resultados
    """
    import os
    import json
    from datetime import datetime
    
    # Cria o diretório de saída se não existir
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Gera um nome de arquivo único com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = f'fs_opa_resultados_{timestamp}.json'
    caminho_arquivo = os.path.join(diretorio_saida, nome_arquivo)
    
    # Salva os resultados em JSON
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        # Converte os tipos NumPy para tipos nativos do Python para serialização
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            return obj
        
        json.dump(resultado, f, ensure_ascii=False, indent=2, default=convert_numpy)
    
    return caminho_arquivo
