import os
import shutil
import subprocess
import tempfile
import pandas as pd

def export_columns_as_files(df, outdir, notebook_mode=False):
    """
    Se notebook_mode=True, exporta todas as colunas (exceto totalmente vazias), convertendo cada célula para string, sem filtrar por tipo.
    Caso contrário, exporta apenas colunas numéricas, remove NaN, mostra preview dos arquivos exportados.
    """
    import os
    os.makedirs(outdir, exist_ok=True)
    exportados = []
    if notebook_mode:
        import ast
        def to_simple(cell):
            # Se for set/list/tuple, pega o primeiro elemento
            if isinstance(cell, (set, list, tuple)):
                if len(cell) > 0:
                    return next(iter(cell))
                else:
                    return ''
            # Se for dict, pega o primeiro valor
            if isinstance(cell, dict):
                if len(cell) > 0:
                    return next(iter(cell.values()))
                else:
                    return ''
            # Se for string representando set/list, tenta eval
            if isinstance(cell, str) and (cell.strip().startswith('{') or cell.strip().startswith('[')):
                try:
                    parsed = ast.literal_eval(cell)
                    return to_simple(parsed)
                except Exception:
                    return cell
            # Caso contrário, retorna como string
            return cell

        df_no_empty = df.dropna(axis=1, how='all')
        print(f"[Notebook Mode] Exportando todas as colunas (exceto vazias): {list(df_no_empty.columns)}")
        for col in df_no_empty.columns:
            col_data = df_no_empty[col].dropna().apply(to_simple)
            # Remove linhas vazias
            col_data = col_data[col_data.astype(str).str.strip() != '']
            # Tentar converter cada valor para float, manter apenas os que conseguem
            def try_float(x):
                try:
                    return float(x)
                except Exception:
                    return None
            col_data_num = col_data.apply(try_float).dropna()
            if len(col_data_num) < 2:
                print(f"[Notebook Mode] Coluna {col} ignorada (não numérica ou menos de 2 dados numéricos)")
                continue
            path = os.path.join(outdir, str(col))
            with open(path, 'w', encoding='utf-8') as f:
                for v in col_data_num:
                    f.write(str(v) + '\n')
            exportados.append((col, path))
            print(f"[Notebook Mode] Arquivo exportado: {path} (n={len(col_data_num)}) | Preview: {list(col_data_num.head(5))}")
    else:
        num_df = df.select_dtypes(include=['number'])
        num_df = num_df.dropna(axis=1, how='all')
        print(f"Exportando as seguintes colunas numéricas para DAMICORE: {list(num_df.columns)}")
        for col in num_df.columns:
            col_data = num_df[col].dropna()
            if len(col_data) < 2:
                print(f"Coluna {col} ignorada (menos de 2 dados válidos após agregação)")
                continue
            path = os.path.join(outdir, str(col))
            with open(path, 'w', encoding='utf-8') as f:
                for v in col_data:
                    f.write(str(v) + '\n')
            exportados.append((col, path))
            print(f"Arquivo exportado: {path} (n={len(col_data)}) | Preview: {list(col_data.head(5))}")
    if len(exportados) < 2:
        raise RuntimeError(f"Menos de 2 arquivos válidos exportados para DAMICORE em {outdir}. Verifique os dados de entrada.")
    print(f"Todos arquivos exportados em: {outdir}")


def run_damicore(input_dir, tree_output, compressor='zlib'):
    """
    Executa o DAMICORE via subprocess, usando caminho explícito para damicore.py.
    """
    import sys
    damicore_py = r"C:/Users/55179/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/local-packages/Python312/site-packages/damicore/damicore.py"
    cmd = [
        sys.executable, damicore_py,
        input_dir,
        '--compressor', compressor,
        '--tree-output', tree_output,
        '--community-detection', 'fast',
        '--serial'
    ]
    subprocess.run(cmd, check=True)


def read_newick_tree(tree_file):
    """
    Lê o arquivo .newick gerado pelo DAMICORE.
    """
    with open(tree_file, 'r', encoding='utf-8') as f:
        return f.read().strip()


def consensus_tree_from_dataframe(df, compressor='zlib', notebook_mode=False):
    """
    Pipeline principal: exporta colunas, roda DAMICORE, lê o resultado.
    Se notebook_mode=True, exporta todas as colunas (exceto vazias), sem filtrar por tipo.
    """
    import tempfile
    with tempfile.TemporaryDirectory(prefix='DAMI_TMP_B2C') as tmpdir:
        export_columns_as_files(df, tmpdir, notebook_mode=notebook_mode)
        tree_file = os.path.join(tmpdir, 'tree.newick')
        run_damicore(tmpdir, tree_file, compressor=compressor)
        with open(tree_file, 'r', encoding='utf-8') as f:
            newick = f.read()
    return newick
