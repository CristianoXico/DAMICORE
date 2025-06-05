from unidecode import unidecode
import os
import pandas as pd

def export_split_columns(df, out_dir):
    """
    Exporta cada coluna do DataFrame para um arquivo CSV separado com nome seguro, transliterado e limpo.
    Retorna um dicionário de nomes limpos para nomes originais e a lista de arquivos criados.
    """
    dic = {}
    fnamel = []
    k = 0
    chars2replac = ['_', ' ', '[', ']', '/', '.', '%', '(', ')']
    os.makedirs(out_dir, exist_ok=True)
    for col in df.columns:
        fname = str(col)
        fname = unidecode(fname)
        for c in chars2replac:
            fname = fname.replace(c, '')
        dic[fname] = str(col)
        full_path = os.path.join(out_dir, fname + '.csv')
        print(f"Salvando: {full_path}")
        fnamel.append(full_path)
        df[col].to_csv(full_path, index=False)
        k += 1
    print(f"Verificador de sucesso: {k} arquivos escritos.")
    return dic, fnamel

# Exemplo de uso (para integrar no pipeline):
# export_split_columns(df_split, 'CAMINHO/PASTA/DO/SPLIT')
