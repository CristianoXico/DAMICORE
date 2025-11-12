import os
import json
import pickle
import pandas as pd
from Bio import Phylo
from io import StringIO
from itertools import combinations

# ============================================================
# 🔹 Função para carregar o dicionário de mapeamento
# ============================================================

def load_mapping(file_path):
    if not file_path or not os.path.exists(file_path):
        print("Nenhum arquivo de mapeamento fornecido. Usando labels originais.")
        return {}
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pkl':
        with open(file_path, 'rb') as f:
            mapping = pickle.load(f)
    elif ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Assuming the JSON file is a dictionary of variables
        # and we want to map the index to the variable name
        mapping = {i: var_name for i, var_name in enumerate(data.keys())}
    elif ext == '.csv':
        df = pd.read_csv(file_path)
        # Assuming the CSV has at least two columns: ID and Descricao
        if df.shape[1] >= 2:
            mapping = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
        else:
            print("CSV de mapeamento não tem colunas suficientes. Usando labels originais.")
            return {}
    else:
        print("Formato de mapeamento não suportado. Usando labels originais.")
        return {}
    print(f"✔ Dicionário de mapeamento carregado com {len(mapping)} entradas.")
    return mapping


# ============================================================
# 🔹 Função para traduzir os labels numéricos para nomes reais
# ============================================================

def translate_label(label, mapping):
    """Traduz rótulo numérico de nó para o nome original da variável."""
    if not mapping:
        return label
    try:
        clean_label = str(label).replace("col_", "").replace(".txt", "").strip()
        num = int(clean_label)
        return mapping.get(num, label)
    except ValueError:
        return mapping.get(label, label)


# ============================================================
# 🔹 Extrai clados (nível 2 e 3) de uma árvore newick
# ============================================================

def extract_clades_from_tree(tree_str, mapping):
    try:
        tree = Phylo.read(StringIO(tree_str), "newick")
    except Exception:
        return []
    clades = []
    for clade in tree.get_nonterminals():
        leaves = [translate_label(leaf.name, mapping) for leaf in clade.get_terminals() if leaf.name]
        level = len(leaves)
        if level in [2, 3]:
            clades.append(tuple(sorted(leaves)))
    return clades


# ============================================================
# 🔹 Calcula frequências relativas e absolutas
# ============================================================

def summarize_clades(all_clades):
    freq = pd.Series(all_clades).value_counts().reset_index()
    freq.columns = ['Clade_Variables', 'Frequency']
    freq['Relative_Frequency (%)'] = 100 * freq['Frequency'] / freq['Frequency'].sum()
    freq['Level'] = freq['Clade_Variables'].apply(len)
    return freq


# ============================================================
# 🔹 Maximiza repetições ao testar subconjuntos do clado
# ============================================================

def maximize_repetition(clade_vars, global_summary):
    best = {'vars': clade_vars, 'reps': 0}
    for r in range(len(clade_vars), 1, -1):
        for subset in combinations(clade_vars, r):
            subset_set = set(subset)
            match = global_summary[global_summary['Clade_Variables'].apply(lambda v: set(v) == subset_set)]
            if not match.empty:
                reps = match['Occurrences_in_Folders'].iloc[0]
                if reps > best['reps']:
                    best = {'vars': list(subset), 'reps': reps}
    return best


# ============================================================
# 🔹 Gera o relatório final de seleção e otimização de clados
# ============================================================

def generate_clade_selection(global_summary):
    selected = global_summary[
        ((global_summary['Level'] == 2) & (global_summary['Mean_Frequency'] >= 40)) |
        ((global_summary['Level'] == 3) & (global_summary['Mean_Frequency'] >= 20))
    ].copy()

    results = []
    for _, row in selected.iterrows():
        vars_list = list(row['Clade_Variables'])
        optimized = maximize_repetition(vars_list, global_summary)
        removed = list(set(vars_list) - set(optimized['vars']))
        status = 'Mantido' if not removed else 'Reduzido'
        results.append({
            'Original_Clade_Variables': vars_list,
            'Optimized_Clade_Variables': optimized['vars'],
            'Removed_Variables': removed,
            'Original_Level': row['Level'],
            'Original_Frequency (%)': row['Mean_Frequency'],
            'Occurrences_in_Folders': row['Occurrences_in_Folders'],
            'Optimized_Repetitions': optimized['reps'],
            'Final_Status': status
        })

    df = pd.DataFrame(results)
    df.to_csv("clade_selection_report.csv", index=False)
    print("✅ Relatório de seleção salvo como clade_selection_report.csv")


# ============================================================
# 🔹 Função principal: varre pastas e gera relatórios
# ============================================================

def main():
    base_path = input("Digite o caminho base: ").strip()
    map_path = '/home/cristiano/Area_de_trabalho/inct_fome/no_nan_categorization_estado_amazonas.json'
    mapping = load_mapping(map_path)
    reports = []

    for root, dirs, files in os.walk(base_path):
        if "damicore_results" in root:
            tree_files = [f for f in files if f.startswith("resample_") and f.endswith(".newick")]
            all_clades = []
            for tf in tree_files:
                with open(os.path.join(root, tf)) as fh:
                    tree_str = fh.read()
                    all_clades.extend(extract_clades_from_tree(tree_str, mapping))
            if not all_clades:
                continue
            df = summarize_clades(all_clades)
            out_path = os.path.join(root, "clade_report.csv")
            df.to_csv(out_path, index=False)
            print(f"📄 Relatório local salvo: {out_path}")
            df['Path'] = root
            reports.append(df)

    if not reports:
        print("Nenhum resultado encontrado.")
        return

    # 🌎 Geração do relatório global
    global_df = pd.concat(reports)
    summary = global_df.groupby("Clade_Variables").agg({
        "Relative_Frequency (%)": "mean",
        "Path": lambda x: list(set(x))
    }).reset_index()
    summary.rename(columns={"Relative_Frequency (%)": "Mean_Frequency"}, inplace=True)
    summary['Occurrences_in_Folders'] = summary['Path'].apply(len)
    summary['Level'] = summary['Clade_Variables'].apply(len)
    summary.to_csv("global_clade_summary.csv", index=False)
    print("🌎 Relatório global salvo como global_clade_summary.csv")

    # 🧬 Seleção e otimização
    generate_clade_selection(summary)


# ============================================================
# 🔹 Execução
# ============================================================

if __name__ == "__main__":
    main()

