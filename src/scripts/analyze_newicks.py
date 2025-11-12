"""
analyze_newicks.py

Uso:
    python analyze_newicks.py /caminho/para/newicks_dir

Saídas:
    - clados_summary.csv
    - clados_summary.docx
    - plain_newicks.txt  (concatenação dos 22 newicks)
"""

import os
import sys
import glob
import re
from collections import defaultdict
from typing import Tuple, Set, List, Dict, Any

import pandas as pd
import hashlib

# Dependência para parse Newick:
"""
analyze_newicks.py

Uso:
    python analyze_newicks.py /caminho/para/newicks_dir

Saídas:
    - clados_summary.csv
    - plain_newicks.txt  (concatenação dos newicks)
"""

import os
import sys
import glob
from collections import defaultdict
from typing import Tuple, List, Dict

import pandas as pd
import hashlib

from Bio import Phylo
from Bio.Phylo.Newick import Clade


def normalize_label(l: str) -> str:
    """Remove aspas externas e espaços."""
    if l is None:
        return ""
    return l.strip().strip('"')


def min_distance_to_leaf(clade: Clade) -> int:
    """
    Retorna o menor número de arestas entre este nó e qualquer folha
    (0 para folha).
    """
    if clade.is_terminal():
        return 0
    child_dists = [min_distance_to_leaf(c) for c in clade.clades if c is not None]
    if not child_dists:
        return 0
    return 1 + min(child_dists)


def gather_terminals(clade: Clade) -> Tuple[str, ...]:
    names = [normalize_label(term.name) for term in clade.get_terminals()]
    names = [n for n in names if n]
    return tuple(sorted(names))


def analyze_newicks(
    path: str,
    metadata_csv: str = None,
    var_mapping_csv: str = None,
    threshold_3=0.20,
    threshold_2=0.40,
    save_prefix: str = "clados_summary",
):
    """Analisa arquivos .newick em 'path' e retorna um dict com DataFrame em 'df'."""
    files = sorted(glob.glob(os.path.join(path, "*.newick")))
    if not files:
        files = sorted(glob.glob(os.path.join(path, "**", "*.newick"), recursive=True))
        if not files:
            raise FileNotFoundError(f"Nenhum arquivo .newick encontrado em {path}")

    filenames = [os.path.basename(f) for f in files]
    n_files = len(files)

    # metadata mapping
    file_to_region: Dict[str, str] = {}
    if metadata_csv and os.path.exists(metadata_csv):
        try:
            md = pd.read_csv(metadata_csv, dtype=str)
            # heurística simples para colunas
            col_file = None
            for c in md.columns:
                if c.lower() in ("filename", "file", "file_name", "nome_arquivo"):
                    col_file = c
                    break
            col_region = None
            for c in md.columns:
                if c.lower() in ("region", "regiao", "region_sigla", "uf"):
                    col_region = c
                    break
            if col_file:
                for _, r in md.iterrows():
                    key = r.get(col_file)
                    if pd.isna(key):
                        continue
                    key = str(key)
                    region_val = r.get(col_region) if col_region else key
                    file_to_region[key] = region_val
        except Exception:
            pass

    for fn in filenames:
        file_to_region.setdefault(fn, fn)

    # load var mapping
    var_map: Dict[str, str] = {}
    headers: List[str] = []
    if var_mapping_csv and os.path.exists(var_mapping_csv):
        try:
            vm = pd.read_csv(var_mapping_csv, dtype=str, nrows=0)
            headers = list(vm.columns)
            # try reading a small chunk to check structure
            vm_full = None
            try:
                vm_full = pd.read_csv(var_mapping_csv, dtype=str)
            except Exception:
                vm_full = None

            if vm_full is not None and set(
                c.lower() for c in vm_full.columns
            ).issuperset({"original", "mapped"}):
                # long-format mapping provided
                for _, r in vm_full.iterrows():
                    orig = str(r.get("original", "")).strip()
                    mapped = str(r.get("mapped", "")).strip()
                    if orig:
                        var_map[orig] = mapped if mapped else orig
                # try to find an 'original' CSV in the same directory to fill positional fallbacks
                try:
                    var_dir = os.path.dirname(var_mapping_csv) or "."
                    candidates = [
                        os.path.join(var_dir, f)
                        for f in os.listdir(var_dir)
                        if f.lower().endswith(".csv")
                        and os.path.join(var_dir, f) != var_mapping_csv
                    ]
                    for cand in candidates:
                        try:
                            head = pd.read_csv(cand, dtype=str, nrows=0)
                            if len(head.columns) >= 5:
                                headers = list(head.columns)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
                # If we still don't have headers, try to find an original CSV under the input path
                try:
                    # 'path' variable is the input directory passed to analyze_newicks
                    if not headers and path and os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            for f in files:
                                if f.lower().endswith(".csv"):
                                    cand = os.path.join(root, f)
                                    try:
                                        head = pd.read_csv(cand, dtype=str, nrows=0)
                                        if len(head.columns) >= 2:
                                            headers = list(head.columns)
                                            raise StopIteration
                                    except StopIteration:
                                        break
                                    except Exception:
                                        continue
                            if headers:
                                break
                except Exception:
                    pass
                # if we found headers from an original CSV, populate positional keys for any missing
                if headers:
                    for i, h in enumerate(headers):
                        key_txt = f"col_{i}.txt"
                        key_noext = f"col_{i}"
                        if key_txt not in var_map:
                            var_map[key_txt] = h
                        if key_noext not in var_map:
                            var_map[key_noext] = h
            else:
                # treat the provided file as the original-data CSV: use its headers for positional mapping
                for i, h in enumerate(headers):
                    key_txt = f"col_{i}.txt"
                    key_noext = f"col_{i}"
                    var_map[key_txt] = h
                    var_map[key_noext] = h
        except Exception:
            # fallback: no mapping available
            headers = []

    clade_stats = defaultdict(lambda: {"files": set(), "level2": 0, "level3": 0})
    plain_newicks_list: List[str] = []

    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            tree = Phylo.read(fpath, "newick")
        except Exception:
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                plain_newicks_list.append(fh.read().strip())
        except Exception:
            pass

        for clade in tree.find_clades(order="level"):
            if clade.is_terminal():
                continue
            terms = gather_terminals(clade)
            if len(terms) < 2:
                continue
            key = hashlib.md5("|".join(terms).encode("utf-8")).hexdigest()
            clade_stats[key]["files"].add(fname)
            level = min_distance_to_leaf(clade)
            if level == 1:
                clade_stats[key]["level2"] += 1
            if level == 2:
                clade_stats[key]["level3"] += 1

    rows = []
    for clade_key, stats in clade_stats.items():
        # reconstruct terminals by scanning files
        matched = None
        for fpath in files:
            try:
                tree = Phylo.read(fpath, "newick")
            except Exception:
                continue
            for clade in tree.find_clades(order="level"):
                if clade.is_terminal():
                    continue
                terms = gather_terminals(clade)
                if len(terms) < 2:
                    continue
                k = hashlib.md5("|".join(terms).encode("utf-8")).hexdigest()
                if k == clade_key:
                    matched = terms
                    break
            if matched:
                break
        if not matched:
            continue
        terminals = list(matched)
        # map each terminal strictly: do not allow unmapped 'col_X.txt' to pass through
        mapped = []
        for t in terminals:
            t_key = t
            mapped_name = None
            # direct map
            if t_key in var_map:
                mapped_name = var_map[t_key]
            else:
                # try without extension
                t_noext = t_key.replace(".txt", "")
                if t_noext in var_map:
                    mapped_name = var_map[t_noext]
                else:
                    # try positional extraction: col_N, allow different separators and optional .txt
                    m = re.search(r"col[_\\.\-]?(\\d+)(?:\\.txt)?$", t_key)
                    if m:
                        idx = int(m.group(1))
                        if headers and 0 <= idx < len(headers):
                            mapped_name = headers[idx]
                        else:
                            # headers not available: synthesize a stable name (without .txt)
                            mapped_name = f"col_{idx}"
            if mapped_name is None:
                # As a last resort, keep original but normalized (should not happen if headers available)
                mapped_name = t_key.replace(".txt", "")
            mapped.append(mapped_name)
        seen = set()
        mapped_unique = [x for x in mapped if not (x in seen or seen.add(x))]
        rows.append(
            {
                "Clade_ID": clade_key,
                "Clade_Terminals": ",".join(terminals),
                "Clade_Variables": "; ".join(mapped_unique),
                "Presence_Count": len(stats["files"]),
                "Presence_Prop": len(stats["files"]) / max(1, n_files),
                "Level2_Count": stats.get("level2", 0),
                "Level3_Count": stats.get("level3", 0),
                "Files": ",".join(sorted(list(stats["files"]))),
            }
        )

    df = pd.DataFrame(rows)
    out_csv = os.path.join(path, f"{save_prefix}.csv")
    try:
        df.to_csv(out_csv, index=False)
    except Exception:
        pass
    out_plain = os.path.join(path, "plain_newicks.txt")
    try:
        with open(out_plain, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(plain_newicks_list))
    except Exception:
        pass
    return {"df": df, "plain_newicks": plain_newicks_list}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso: python analyze_newicks.py /caminho/para/newicks_dir [metadata.csv] [var_mapping.csv]"
        )
        sys.exit(1)
    path = sys.argv[1]
    metadata = None
    var_mapping_file = None
    if len(sys.argv) >= 3:
        arg2 = sys.argv[2]
        if arg2.lower().endswith(".csv") and (
            "var_mapping" in arg2.lower()
            or "mapping" in arg2.lower()
            or arg2.lower().startswith("var_")
        ):
            var_mapping_file = arg2
        else:
            metadata = arg2
    if len(sys.argv) >= 4:
        var_mapping_file = sys.argv[3]
    if not var_mapping_file:
        default_mapping = "var_mapping.csv"
        if os.path.exists(default_mapping):
            var_mapping_file = default_mapping
        elif os.path.exists(os.path.join(path, "var_mapping.csv")):
            var_mapping_file = os.path.join(path, "var_mapping.csv")
    if var_mapping_file and os.path.exists(var_mapping_file):
        print(f"Usando arquivo de mapeamento: {var_mapping_file}")
    analyze_newicks(path, metadata_csv=metadata, var_mapping_csv=var_mapping_file)
    analyze_newicks(path, metadata_csv=metadata, var_mapping_csv=var_mapping_file)
