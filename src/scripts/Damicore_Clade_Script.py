import os
import csv
import toytree
from collections import defaultdict, Counter
from typing import List, Dict, Any

csv.field_size_limit(10_000_000)

# ============================================================
# CARREGAR MAPEAMENTO DINÂMICO
# ============================================================


def carregar_mapeamento(csv_path):
    """
    Lê o cabeçalho do CSV e cria o dicionário:
    'col_N.txt' -> header[N]
    robusto contra espaços, aspas e BOM.
    """
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

    mapping = {}

    for i, name in enumerate(header):
        clean = str(name).strip().replace('"', "").replace("'", "")
        key = f"col_{i}.txt".strip()
        mapping[key] = clean

    print(f"[INFO] Mapeamento dinâmico gerado com {len(mapping)} variáveis.")
    return mapping


def traduzir_label(label, mapping):
    """
    Traduz qualquer label de árvore do formato DAMICORE para o nome original.
    Lida com vários formatos inesperados.
    """
    if label is None:
        return None

    original = label.strip()

    # normalizar: remover aspas, parênteses, espaços etc.
    norm = (
        original.replace('"', "")
        .replace("'", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    # caso seja exatamente col_N.txt
    if norm in mapping:
        return mapping[norm]

    # caso venha com lixo tipo col_0.txt:0.00231
    if ":" in norm:
        base = norm.split(":")[0]
        if base in mapping:
            return mapping[base]

    # caso venha com comentários ou símbolos
    base = norm.split()[0]
    if base in mapping:
        return mapping[base]

    return original


# ============================================================
# LER ARQUIVOS NEWICK
# ============================================================


def ler_newicks_da_pasta(pasta: str) -> List[str]:
    arvs = []
    for fn in sorted(os.listdir(pasta)):
        if fn.endswith(".newick"):
            with open(os.path.join(pasta, fn), "r") as f:
                txt = f.read().strip()
                if txt:
                    arvs.append(txt)
    return arvs


# ============================================================
# EXTRAIR CLADOS DE UMA ÁRVORE
# ============================================================


def extrair_clados(tree: toytree.ToyTree):
    clados = {}
    for node in tree.treenode.traverse():
        if not node.is_leaf():
            leaves = tuple(sorted(leaf.name for leaf in node.get_leaves()))
            suporte = node.dist
            clados[leaves] = suporte
    return clados


# ============================================================
# FREQUÊNCIA + SUPORTE MÉDIO DE TODOS OS CLADOS
# ============================================================


def calcular_frequencias(newicks: List[str]):
    total = len(newicks)
    freq = Counter()
    suportes = defaultdict(list)

    for nw in newicks:
        t = toytree.tree(nw)  # << CORRIGIDO

        clados = extrair_clados(t)
        for c, s in clados.items():
            freq[c] += 1
            if s is not None:
                suportes[c].append(s)

    stats = {}
    for c, count in freq.items():
        lista = suportes.get(c, [])
        stats[c] = {
            "freq": count / total,
            "suporte_medio": sum(lista) / len(lista) if lista else None,
            "lista_suportes": lista,
        }
    return stats


# ============================================================
# ESCOLHER ÁRVORE DE CONSENSO (Best Representative Tree)
# ============================================================


def escolher_arvore_referencia(newicks: List[str], stats_all):
    melhor_score = -1
    melhor = None

    for nw in newicks:
        t = toytree.tree(nw)  # << CORRIGIDO
        clados = extrair_clados(t)

        score = sum(stats_all[c]["freq"] for c in clados if c in stats_all)
        if score > melhor_score:
            melhor_score = score
            melhor = t

    return melhor


# ============================================================
# CLASSIFICAÇÃO DO CLAdo
# ============================================================


def classificar(freq):
    if freq >= 0.85:
        return "CLADO MUITO ESTÁVEL"
    elif freq >= 0.65:
        return "CLADO ESTÁVEL"
    elif freq >= 0.50:
        return "CLADO MODERADO"
    else:
        return "CLADO FRACO"


# ============================================================
# SALVAR RELATÓRIO CSV
# ============================================================


def salvar_csv(path, dados):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["clado", "variaveis", "frequencia", "suporte_medio", "classificacao"]
        )

        for d in dados:
            w.writerow(
                [
                    ";".join(d["clado"]),
                    ";".join(d["traduzido"]),
                    d["freq"],
                    d["suporte"],
                    d["classe"],
                ]
            )


# ============================================================
# SALVAR RELATÓRIO TEXTUAL
# ============================================================


def salvar_txt(path, dados, nome):
    with open(path, "w") as f:
        f.write("===========================================\n")
        f.write(f"ANÁLISE DE CLADOS — CONSENSO ({nome})\n")
        f.write("===========================================\n\n")

        for i, d in enumerate(dados, 1):
            f.write("-------------------------------------------\n")
            f.write(f"CLADO {i}: {', '.join(d['traduzido'])}\n")
            f.write(f"Frequência: {d['freq']:.3f}\n")
            f.write(f"Suporte médio: {d['suporte']}\n")
            f.write(f"Classificação: {d['classe']}\n\n")


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================


def processar_base(base_path, csv_map=None):
    mapping = carregar_mapeamento(csv_map)
    globais = []

    for root, dirs, files in os.walk(base_path):
        if "damicore_results" not in dirs:
            continue

        pasta = os.path.join(root, "damicore_results")
        estado = os.path.basename(root)

        print(f"[INFO] Processando {estado}")

        newicks = ler_newicks_da_pasta(pasta)
        stats = calcular_frequencias(newicks)
        consenso = escolher_arvore_referencia(newicks, stats)

        dados = []
        clados_consenso = extrair_clados(consenso)

        for clado, suporte in clados_consenso.items():
            info = stats.get(clado, {"freq": 0, "suporte_medio": None})
            freq = info["freq"]

            dados.append(
                {
                    "clado": clado,
                    "traduzido": [mapping.get(x, x) for x in clado],
                    "freq": freq,
                    "suporte": suporte,
                    "classe": classificar(freq),
                }
            )

        out_csv = os.path.join(root, f"consenso_{estado}.csv")
        out_txt = os.path.join(root, f"consenso_{estado}.txt")

        salvar_csv(out_csv, dados)
        salvar_txt(out_txt, dados, estado)

        globais.extend(dados)

    # RELATÓRIO GLOBAL
    salvar_csv(os.path.join(base_path, "consenso_GLOBAL.csv"), globais)
    salvar_txt(os.path.join(base_path, "consenso_GLOBAL.txt"), globais, "GLOBAL")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    base = input("Digite o caminho base: ").strip()
    csv_map = input("CSV de mapeamento ou ENTER: ").strip()
    csv_map = csv_map if csv_map else None
    processar_base(base, csv_map)
