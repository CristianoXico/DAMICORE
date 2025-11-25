#!/usr/bin/env python3
"""
damicore_consensus_clade_analyzer_v5.3.py

🔥 Versão 5.3 - Mapeamento dinâmico a partir de CSV de amostra. Clados de tamanho variável (>=2), mínimo de 20 newicks, sem filtro global.

- Cada subpasta "damicore_results" é processada isoladamente e gera:
    clade_report_<regionalidade>.csv  → todos os clados, com variáveis mapeadas.

- O relatório global é gerado a partir de todas as regiões:
    clados_summary.csv  → inclui todos os clados consolidados, com variáveis mapeadas.
    clados_summary.md   → versão markdown.

- Frequências são médias dos pares (nível 2) e trios (nível 3) contidos no clado.
"""

import os
import re
import json
import pickle
import pandas as pd
from pathlib import Path
from collections import defaultdict, OrderedDict
from itertools import combinations

try:
    from Bio import Phylo
except Exception:
    raise RuntimeError("Biopython não encontrado. Instale com: pip install biopython")


# ------------------ UTILIDADES DE MAPEAMENTO ------------------ #
def create_dynamic_mapping(csv_path):
    """Cria um dicionário de mapeamento dinâmico a partir do cabeçalho de um CSV."""
    try:
        # Lê apenas o cabeçalho
        df = pd.read_csv(csv_path, nrows=0)
        mapping = {}
        for i, col_name in enumerate(df.columns):
            # Cria o mapeamento: col_N.txt -> nome_da_coluna
            mapping[f"col_{i}.txt"] = col_name
        print(
            f"[INFO] Mapeamento dinâmico criado a partir de {csv_path} ({len(mapping)} colunas)."
        )
        return mapping
    except FileNotFoundError:
        print(f"[WARN] Arquivo CSV de amostra não encontrado: {csv_path}")
        return {}
    except Exception as e:
        print(f"[ERROR] Falha ao ler o cabeçalho do CSV: {e}")
        return {}


def load_mapping(source):
    """Carrega dicionário de mapeamento de colunas (pkl/json/csv) ou usa um dicionário fornecido."""
    if isinstance(source, dict):
        mapping = source
        # Se for um dicionário, não precisamos da lógica de arquivo, mas precisamos da normalização.
        # A normalização será feita abaixo.
    elif not source:
        return {}
    else:
        p = Path(source)
        if not p.exists():
            print(f"[WARN] Arquivo de mapeamento não encontrado: {source}")
            return {}
        ext = p.suffix.lower()
        if ext == ".pkl":
            with open(p, "rb") as f:
                mapping = pickle.load(f)
        elif ext == ".json":
            with open(p, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        elif ext in [".csv", ".tsv"]:
            df = pd.read_csv(p)
            mapping = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))
        else:
            print(f"[WARN] Formato de mapeamento não suportado: {ext}")
            return {}

    norm = {}
    for k, v in mapping.items():
        ks = str(k)
        val = str(v)

        # 1. Mapeamento direto (ex: 'col_0.txt' -> 'spatial_id')
        norm[ks] = val

        # 2. Mapeamento numérico (ex: 0 -> 'spatial_id')
        try:
            ki = int(re.sub(r"\D", "", ks))
            norm[ki] = val
        except Exception:
            pass

        # 3. Mapeamento de rótulos de coluna (ex: '0' -> 'spatial_id')
        # Extrai o número da coluna (ex: '0' de 'col_0.txt')
        col_num_str = re.sub(r"\D", "", ks.replace("col_", "").replace(".txt", ""))
        if col_num_str:
            # Cria a chave no formato que vem da árvore (ex: 'col_0.txt')
            col_key = f"col_{col_num_str}.txt"
            norm[col_key] = val

            # Cria a chave no formato numérico (ex: 0)
            try:
                norm[int(col_num_str)] = val
            except Exception:
                pass

    print(f"[INFO] Mapeamento carregado ({len(norm)} chaves).")
    return norm


def translate_label(label, mapping):
    """Traduz o label numérico para o nome real da variável usando o dicionário."""
    if label is None:
        return None
    s = str(label)
    if not mapping:
        return s
    candidates = [
        s,
        s.strip(),
        s.replace("'", "").replace('"', ""),
        s.replace("col_", "").replace(".txt", ""),
        s.replace(".txt", ""),
        f"col_{s}",
        f"{s}.txt",
        f"col_{s}.txt",
    ]
    for c in candidates:
        try:
            ki = int(c)
            if ki in mapping:
                return mapping[ki]
        except Exception:
            pass
        if c in mapping:
            return mapping[c]
    digits = re.sub(r"\D", "", s)
    if digits:
        try:
            di = int(digits)
            if di in mapping:
                return mapping[di]
        except Exception:
            pass
    return s


# ------------------ EXTRAÇÃO DE CLADOS ------------------ #
def extract_clades_from_tree(tree, mapping):
    """Extrai todos os clados com 2 ou mais terminais (sem limite superior)."""
    clades = []
    for clade in tree.get_nonterminals(order="level"):
        terminals = [t.name for t in clade.get_terminals() if t.name is not None]
        mapped = [translate_label(x, mapping) for x in terminals]
        if len(mapped) >= 2:
            clades.append(tuple(sorted(mapped)))
    return clades


# ------------------ ANÁLISE LOCAL ------------------ #
def analyze_region(results_dir, mapping):
    """Analisa as árvores dentro de uma pasta damicore_results e retorna DataFrame local."""
    results_dir = Path(results_dir)
    newick_files = sorted(
        [
            p
            for p in results_dir.iterdir()
            if p.name.startswith("resample_") and p.suffix == ".newick"
        ]
    )
    if not newick_files:
        return None, 0

    nres = len(newick_files)
    if nres < 20:
        print(
            f"[WARN] Apenas {nres} arquivos .newick encontrados. Mínimo de 20 é necessário para análise. Pulando."
        )
        return None, 0

    clade_counts = defaultdict(int)
    clade_files = defaultdict(set)

    for f in newick_files:
        try:
            trees = list(Phylo.parse(str(f), "newick"))
        except Exception as e:
            print(f"[WARN] Falha ao ler {f.name}: {e}")
            continue
        for tree in trees:
            extracted = extract_clades_from_tree(tree, mapping)
            for clade in extracted:
                clade_counts[clade] += 1
                clade_files[clade].add(f.name)

    rows = []
    for clade, count in clade_counts.items():
        files = sorted(list(clade_files[clade]))
        size = len(clade)
        rows.append(
            {
                "Clade_ID": abs(hash(clade)),
                "Clade_Terminals": ",".join(clade),
                "Clade_Variables": list(clade),
                "Presence_Count": len(files),
                "Level2_freq": 0.0,
                "Level3_freq": 0.0,
                "Files": ";".join(files),
                "Size": size,
            }
        )

    df = pd.DataFrame(rows)
    df["Level2_freq"] = df["Presence_Count"] / float(nres)
    df["Level3_freq"] = df["Presence_Count"] / float(nres)
    return df, nres


# ------------------ CONSOLIDAÇÃO GLOBAL ------------------ #
def consolidate_all(local_results):
    """
    Consolida resultados de todas as regiões, incluindo todos os clados.
    """
    regions = list(local_results.keys())
    all_vars = set()
    for df, _ in local_results.values():
        for clade_vars in df["Clade_Variables"]:
            all_vars.update(clade_vars)

    summary_rows = []
    for region, (df, nres) in local_results.items():
        for _, row in df.iterrows():
            summary_rows.append(
                {
                    "Region": region,
                    "Clade_Variables": tuple(sorted(row["Clade_Variables"])),
                    "Level2_freq": row["Level2_freq"],
                    "Level3_freq": row["Level3_freq"],
                    "Presence_Count": row["Presence_Count"],
                    "Files": row["Files"],
                }
            )

    all_clades = {}
    for r in summary_rows:
        key = tuple(sorted(r["Clade_Variables"]))
        if key not in all_clades:
            all_clades[key] = {
                "Level2_vals": [],
                "Level3_vals": [],
                "Presence": 0,
                "Files": set(),
            }
        all_clades[key]["Level2_vals"].append(r["Level2_freq"])
        all_clades[key]["Level3_vals"].append(r["Level3_freq"])
        all_clades[key]["Files"].update(r["Files"].split(";"))
        all_clades[key]["Presence"] += 1

    summary = []
    for clade, vals in all_clades.items():
        mean_l2 = sum(vals["Level2_vals"]) / len(vals["Level2_vals"])
        mean_l3 = sum(vals["Level3_vals"]) / len(vals["Level3_vals"])
        summary.append(
            {
                "Clade_ID": abs(hash(clade)),
                "Clade_Variables": list(clade),
                "Presence_Count": vals["Presence"],
                "Level2_freq": round(mean_l2, 4),
                "Level3_freq": round(mean_l3, 4),
                "Files": ";".join(sorted(list(vals["Files"]))),
            }
        )

    summary_df = pd.DataFrame(summary)
    summary_df = summary_df.sort_values(
        ["Presence_Count", "Level2_freq", "Level3_freq"], ascending=False
    )
    return summary_df


# ------------------ SAÍDA MARKDOWN ------------------ #
def write_markdown(summary_df, out_path):
    lines = []
    lines.append("# Sumário Global de Clados (v5.3)\n")
    lines.append("Todos os clados consolidados de regiões com 20+ arquivos newick.\n")
    lines.append(
        "| Clade_ID | Clade_Variables | Presence_Count | Level2_freq | Level3_freq | Files |"
    )
    lines.append("|---|---|:---:|:---:|:---:|---|")
    for _, r in summary_df.iterrows():
        lines.append(
            f"| {r['Clade_ID']} | {r['Clade_Variables']} | {r['Presence_Count']} | {r['Level2_freq']:.3f} | {r['Level3_freq']:.3f} | {r['Files']} |"
        )
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Markdown salvo em: {out_path}")


# ------------------ MAIN ------------------ #
def main():
    print(
        "DAMICORE Consensus Clade Analyzer v5.3 — Clados >=2, 20+ newicks, sem filtro global, mapeamento dinâmico"
    )
    base = input("Digite o caminho base (ex: /home/cristiano/city_regioes/): ").strip()
    mapf = input(
        "Arquivo de mapeamento (.pkl/.json/.csv) ou ENTER para usar o mapeamento dinâmico: "
    ).strip()
    if not base:
        print("Caminho não informado. Saindo.")
        return

    # Se o usuário não fornecer um arquivo de mapeamento, solicitamos o CSV de amostra
    if not mapf:
        csv_sample_path = input(
            "Caminho para o CSV de amostra (ex: /caminho/para/estado_Acre_sample.csv): "
        ).strip()
        if not csv_sample_path:
            print("Caminho do CSV de amostra não fornecido. Saindo.")
            return

        # 1. Cria o mapeamento dinâmico a partir do CSV
        dynamic_map = create_dynamic_mapping(csv_sample_path)

        # 2. Normaliza o mapeamento
        mapping = load_mapping(dynamic_map)
    else:
        mapping = load_mapping(mapf)

    if not mapping:
        print("Mapeamento não carregado. Saindo.")
        return

    local_results = OrderedDict()
    for root, dirs, _ in os.walk(base):
        if "damicore_results" in dirs:
            region_dir = Path(root) / "damicore_results"
            region_name = Path(root).name
            print(f"\n[INFO] Processando {region_name}")
            df_local, nres = analyze_region(region_dir, mapping)
            if df_local is None or df_local.empty:
                print(f"[WARN] Nenhum clado em {region_name}")
                continue
            out_local = Path(root) / f"clade_report_{region_name}.csv"
            df_local.to_csv(out_local, index=False)
            print(f"[OK] Relatório local salvo: {out_local}")
            local_results[region_name] = (df_local, nres)

    if not local_results:
        print("Nenhuma pasta com damicore_results encontrada.")
        return

    summary_df = consolidate_all(local_results)
    if summary_df.empty:
        print("Nenhum clado encontrado nas regiões analisadas.")
        return

    out_csv = Path(base) / "clados_summary.csv"
    summary_df.to_csv(out_csv, index=False)
    print(f"[OK] Relatório global salvo em: {out_csv}")

    out_md = Path(base) / "clados_summary.md"
    write_markdown(summary_df, out_md)
    print("✅ Concluído com sucesso!")


if __name__ == "__main__":
    main()
