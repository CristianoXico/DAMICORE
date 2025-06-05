import numpy as np
import zlib
import ast

def ncd_matrix_from_dataframe(df, notebook_mode=False):
    """
    Calcula a matriz NCD entre as colunas exportadas do DataFrame.
    Usa zlib para compressão. Retorna matriz numpy e lista de labels.
    """
    def to_simple(cell):
        if isinstance(cell, (set, list, tuple)):
            if len(cell) > 0:
                return next(iter(cell))
            else:
                return ''
        if isinstance(cell, dict):
            if len(cell) > 0:
                return next(iter(cell.values()))
            else:
                return ''
        if isinstance(cell, str) and (cell.strip().startswith('{') or cell.strip().startswith('[')):
            try:
                parsed = ast.literal_eval(cell)
                return to_simple(parsed)
            except Exception:
                return cell
        return cell

    df_no_empty = df.dropna(axis=1, how='all')
    series_list = []
    labels = []
    for col in df_no_empty.columns:
        col_data = df_no_empty[col].dropna().apply(to_simple)
        col_data = col_data[col_data.astype(str).str.strip() != '']
        # Tentar converter cada valor para float
        def try_float(x):
            try:
                return float(x)
            except Exception:
                return None
        col_data_num = col_data.apply(try_float).dropna()
        if len(col_data_num) < 2:
            continue
        # Serializa como string única separada por vírgula
        s = ','.join(str(x) for x in col_data_num)
        series_list.append(s)
        labels.append(col)
    n = len(series_list)
    ncd_mat = np.zeros((n, n))
    def csize(s):
        return len(zlib.compress(s.encode('utf-8')))
    for i in range(n):
        for j in range(n):
            if i == j:
                ncd_mat[i, j] = 0.0
            else:
                c_x = csize(series_list[i])
                c_y = csize(series_list[j])
                c_xy = csize(series_list[i] + series_list[j])
                ncd = (c_xy - min(c_x, c_y)) / max(c_x, c_y)
                ncd_mat[i, j] = ncd
    return ncd_mat, labels
