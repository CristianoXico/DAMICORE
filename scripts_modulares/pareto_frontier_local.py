# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import ast
from statistics import multimode
import os
import csv

# Solicita o caminho do arquivo de entrada ao usuário
input_path = input("Digite o caminho do arquivo CSV de entrada: ").strip()

# Tenta carregar o arquivo de entrada de forma robusta
try:
    df = pd.read_csv(
        input_path,
        encoding="latin1",
        low_memory=False,
        sep=',',
        on_bad_lines="skip",  # pandas >= 1.3
        quoting=csv.QUOTE_MINIMAL
    )
except Exception as e:
    print(f"Erro ao ler o arquivo CSV: {e}")
    exit(1)

# Lista todas as possíveis variáveis (colunas) do arquivo
all_columns = list(df.columns)
print("\nVariáveis disponíveis para filtragem:")
print(", ".join(all_columns))

# Solicita as variáveis de interesse ao usuário (separadas por vírgula)
variables_input = input("Digite as variáveis a serem filtradas (separadas por vírgula): ").strip()
variables = [v.strip() for v in variables_input.split(",") if v.strip()]

# Gera nome do arquivo de saída com prefixo e variáveis
input_filename = os.path.splitext(os.path.basename(input_path))[0]
output_dir = os.path.dirname(input_path)
output_filename = f"pareto_filtered_{input_filename}_{'_'.join(variables).lower()}.csv"
output_path = os.path.join(output_dir, output_filename)

print(f"Arquivo de saída será salvo em: {output_path}")


# Função vetorizada de ordenação não-dominada
def non_dominated_sort_fast(objs):
    n, m = objs.shape
    le_matrix = np.all(objs[:, None, :] <= objs[None, :, :], axis=2)
    lt_matrix = np.any(objs[:, None, :] < objs[None, :, :], axis=2)
    dominates = le_matrix & lt_matrix
    dominated_count = np.sum(dominates, axis=0)
    current_front = np.where(dominated_count == 0)[0].tolist()
    rank = np.zeros(n, dtype=int)
    i = 1
    while current_front:
        for p in current_front:
            rank[p] = i
            for q in np.where(dominates[p])[0]:
                dominated_count[q] -= 1
        next_front = [q for p in current_front for q in np.where(dominates[p])[0] if dominated_count[q] == 0]
        i += 1
        current_front = list(set(next_front))
    return rank

# Função para extrair valor numérico/mode de célula
def extract_value(cell):
    try:
        val = ast.literal_eval(cell)
    except Exception:
        return pd.NA
    if isinstance(val, (set, list, tuple)):
        vals = list(val)
    else:
        vals = [val]
    vals = [v for v in vals if v not in ('', None)]
    if not vals:
        return pd.NA
    if len(vals) > 1:
        chosen = multimode(vals)[0]
    else:
        chosen = vals[0]
    try:
        return int(chosen)
    except:
        try:
            return float(chosen)
        except:
            return chosen

# Aplica transformação nas colunas desejadas
for col in ['join_CENSITARIO'] + variables:
    df[col] = df[col].astype(str).apply(extract_value)

# Remove linhas com valores vazios nas colunas de interesse
df = df.dropna(subset=['join_CENSITARIO'] + variables, how='any')

# Seleciona objetivos e aplica ordenação não-dominada
objetivos = df[variables].to_numpy()
df['pareto_frontier'] = non_dominated_sort_fast(objetivos)

# Garante unicidade de join_CENSITARIO e melhor rank
df_out = df.loc[df.groupby('join_CENSITARIO')['pareto_frontier'].idxmin()]
df_out = df_out[['join_CENSITARIO'] + variables + ['pareto_frontier']]

# Garante que o diretório de saída existe
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Salva o CSV localmente
df_out.to_csv(output_path, index=False)
print(f"Arquivo salvo em: {output_path}")
print(df_out.head())