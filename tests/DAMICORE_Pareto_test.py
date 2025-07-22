                                                                                                                                                                                # DAMICORE_Pareto_test.py
# Versão de teste do script principal DAMICORE_Pareto_script.py
# Este arquivo é usado como ambiente de sandbox para experimentação e desenvolvimento
# de novas funcionalidades e melhorias no projeto.

# Importações originais mantidas
import os
import pandas as pd
import numpy as np
import ast
from statistics import multimode
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import toytree
import toyplot
import toyplot.svg
from Bio import Phylo
from io import StringIO
from sklearn.cluster import AgglomerativeClustering
import seaborn as sns

def get_matching_resample_indices(results_dir, consensus_tree):
    """
    Compara cada árvore .newick no diretório de resultados com a árvore de consenso.
    Retorna os índices dos resamples que formaram a árvore de consenso.
    """
    matching_indices = []

    print("Aviso: comparação de topologia entre árvores desativada (ToyTree moderno não possui .compare). Nenhuma reamostragem será marcada como idêntica ao consenso.")
    return []


def draw_tree_with_barplot(tree, original_df, output_path, name_to_index, results_dir, sample_dir):
    """
    Visualização de árvore filogenética com barra dupla:
    - Azul: número de vezes que a variável apareceu no dataset original
    - Laranja: número de vezes que apareceu na estratificação da árvore de consenso
    """
    try:
        import toyplot

        if isinstance(tree, toytree.MultiTree):
            tree = tree.get_consensus_tree()

        # Inicializar estrutura
        tip_labels = tree.get_tip_labels()
        canvas = toyplot.Canvas(width=1200, height=1000)
        ax_tree = canvas.cartesian(bounds=(50, 500, 50, 950), padding=20)
        ax_bar = canvas.cartesian(bounds=(550, 1150, 50, 950), padding=20)
        all_resample_counts = {}

        # Calcular frequência da variável em todas as reamostragens (cloud tree)
        for resample_folder in os.listdir(sample_dir):
            folder_path = os.path.join(sample_dir, resample_folder)
            if not os.path.isdir(folder_path):
                continue
            for file in os.listdir(folder_path):
                if not file.endswith('.txt'):
                    continue
                col_name = file.replace('.txt', '')
                col_path = os.path.join(folder_path, file)
                try:
                    s = pd.read_csv(col_path, header=None, names=[col_name], dtype=str)
                    count = s[col_name].notna().sum()
                    if col_name not in all_resample_counts:
                        all_resample_counts[col_name] = count
                    else:
                        all_resample_counts[col_name] += count
                except Exception as e:
                    print(f"Erro ao processar {col_path}: {e}")
                    continue

        consensus_vals = []
        original_vals = []
        labels = []

        # LOG DE DEBUG: exemplos de labels e name_to_index
        print("[DEBUG] Exemplos de labels das folhas da árvore:")
        for i, label in enumerate(tip_labels[:5]):
            print(f"  [{i}] {label}")
        print("[DEBUG] name_to_index (primeiros 10 itens):")
        if name_to_index:
            for i, (k, v) in enumerate(list(name_to_index.items())[:10]):
                print(f"  {k}: {v}")
        else:
            print("  name_to_index está vazio ou None")

        # Construir index_to_name para mapear índice para nome de coluna
        index_to_name = {str(v): k for k, v in name_to_index.items()} if name_to_index else {}
        print("[DEBUG] index_to_name (primeiros 10 itens):")
        for i, (k, v) in enumerate(list(index_to_name.items())[:10]):
            print(f"  {k}: {v}")

        def parse_label_to_colname(label, name_to_index, index_to_name):
            # Remove aspas e extensões
            j = label.strip("'\"")
            # Tenta padrões conhecidos
            if j.startswith('col_') and j.endswith('.txt'):
                num = j[4:-4]
            elif j.endswith('.csv'):
                num = j[:-4]
            elif j.isdigit():
                num = j
            else:
                # fallback: pega só os dígitos
                import re
                nums = re.findall(r'\d+', j)
                num = nums[0] if nums else None
            # Primeiro tenta pelo índice
            if num and index_to_name and num in index_to_name:
                return index_to_name[num]
            # Depois tenta pelo nome direto
            if num and name_to_index and num in name_to_index:
                return name_to_index[num]
            return None

        for idx, label in enumerate(tip_labels):
            try:
                col_name = parse_label_to_colname(label, name_to_index, index_to_name)
                if col_name:
                    labels.append(col_name)
                    # Valor no dataset original
                    original_val = original_df[col_name].notna().sum()
                    # Valor em todas as reamostragens (cloud tree)
                    consensus_val = all_resample_counts.get(col_name, 0)
                    original_vals.append(original_val)
                    consensus_vals.append(consensus_val)
                else:
                    print(f"Label {label} não pôde ser mapeado para coluna do dataset.")
            except Exception as e:
                print(f"Erro com label {label}: {e}")
                continue

        # Remover chamada duplicada e garantir que axes não seja usado se não existir

        # Se não houver dados de consenso, preencha com zeros
        if not consensus_vals or len(consensus_vals) != len(original_vals):
            print("Aviso: Nenhuma reamostragem foi marcada como formando o consenso. O barplot mostrará apenas o dataset original (azul) e zero para consenso (laranja).")
            consensus_vals = [0] * len(original_vals)

        if not labels or not original_vals:
            print("Nenhum dado para gerar o barplot da árvore de consenso. Barplot será omitido.")
            return

        # Normalizar para visualização (opcional)
        max_val = max(max(original_vals), max(consensus_vals)) if (original_vals and consensus_vals) else 1
        orig_norm = [v / max_val for v in original_vals]
        cons_norm = [v / max_val for v in consensus_vals]
        y_pos = np.arange(len(labels))

        # Desenhar árvore
        result = tree.draw(
            axes=axes,
            tip_labels=labels,
            tip_labels_align=True,
            tip_labels_style={"font-size": "10px"},
        )
        if isinstance(result, tuple):
            axes = result[0]

        for i, (orig_val, cons_val) in enumerate(zip(original_norm, consensus_norm)):
            x_base = tree.get_max_distance() + 0.1
            y_pos = i

            # Azul = original
            axes.rect(
                x_base, y_pos - 0.15, orig_val, 0.1,
                style={"fill": "steelblue", "stroke": "black", "opacity": 0.9}
            )

            # Laranja = consenso
            axes.rect(
                x_base + orig_val + 0.05, y_pos - 0.15, cons_val, 0.1,
                style={"fill": "#FFA07A", "stroke": "black", "opacity": 0.9}
            )

        canvas.legend([
            ("Ocorrência no Dataset Original", {"fill": "steelblue"}),
            ("Ocorrência na Árvore de Consenso", {"fill": "#FFA07A"})
        ], coordinates=(700, 50))

        canvas.text(500, 30, "Ocorrência: Original (azul) + Consenso (laranja)",
                    style={"font-size": "16px", "font-weight": "bold"})

        toyplot.pdf.render(canvas, output_path)
        print(f"Visualização salva em: {output_path}")

    except Exception as e:
        print(f"Erro ao gerar visualização com barra dupla: {e}")
        raise

def run_damicore_analysis(input_path):
    """Executa a análise DAMICORE no arquivo de entrada."""
    print("\n=== Iniciando Análise DAMICORE ===")
    
    # Configuração de diretórios
    SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(input_path))[0]
    OUTPUT_DIR = os.path.join(os.path.dirname(input_path), SCRIPTS_OUTPUT_BASE)
    DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
    os.makedirs(DAMICORE_DIR, exist_ok=True)

    # === 1. Carregamento e pré-processamento ===
    print("Carregando dados...")
    original_df = pd.read_csv(input_path, encoding="utf-8", low_memory=False)
    original_columns = original_df.columns.tolist()

    # Criar dicionários para mapeamento bidirecional entre índices e nomes originais
    index_to_name = {str(i): name for i, name in enumerate(original_columns)}
    name_to_index = {name: str(i) for i, name in enumerate(original_columns)}

    # Criar DataFrame de trabalho com índices como nomes das colunas
    df = original_df.copy()
    df.columns = [str(i) for i in range(len(df.columns))]
    df = df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

    # === 2. Reamostragem bootstrap ===
    print("Realizando reamostragem bootstrap...")
    resampled_df_l = [df]
    for i in range(22):
        resampled_df_l.append(df.sample(n=df.shape[0], replace=True, random_state=i))

    # === 3. Salvamento das amostras ===
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    for i, df_sample in enumerate(resampled_df_l):
        sample_file = os.path.join(sample_dir, f"resample_{i:02d}.csv")
        df_sample.to_csv(sample_file, index=False)
        print(f"Amostra {i:02d} salva em {sample_file}")

    # === 4. Execução do DAMICORE para cada amostra ===
    print("\n=== Executando DAMICORE para cada amostra ===")
    damicore_results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
    os.makedirs(damicore_results_dir, exist_ok=True)
    
    # Carregar configuração do DAMICORE
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
    if not os.path.exists(config_path):
        print(f"Erro: Arquivo de configuração {config_path} não encontrado!")
        return

    with open(config_path, 'r') as config_file:
        config_content = config_file.read()
    
    # Extrair o caminho do damicore_cli_path do config.ini
    damicore_cli_path = None
    for line in config_content.split('\n'):
        if line.startswith('damicore_cli_path = '):
            damicore_cli_path = line.split('=')[1].strip()
            break
    
    if not damicore_cli_path:
        print("Erro: Não foi possível encontrar o caminho do damicore_cli_path no config.ini!")
        return

    # Executar DAMICORE para cada amostra
    cloud_trees = []
    for i, df_sample in enumerate(resampled_df_l):
        # Criar diretório temporário para cada resample
        sample_dir = os.path.join(DAMICORE_DIR, f"resample_{i:02d}")
        os.makedirs(sample_dir, exist_ok=True)
        
        # Salvar o DataFrame como múltiplos arquivos CSV no diretório
        # Cada coluna será salva como um arquivo separado
        for col in df_sample.columns:
            col_file = os.path.join(sample_dir, f"{col}.csv")
            df_sample[[col]].to_csv(col_file, index=False)
            print(f"Arquivo de entrada criado: {col_file}")
        
        # Configurar caminho de saída para a árvore
        output_tree = os.path.join(damicore_results_dir, f"resample_{i:02d}-tree.newick")
        
        # Comando para executar o DAMICORE
        cmd = ["python", damicore_cli_path, "--compressor", "gzip", "--tree-output", output_tree, sample_dir]
        print(f"\nExecutando DAMICORE para {sample_dir}")
        print(f"Comando: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Erro ao executar DAMICORE para {sample_dir} (código {result.returncode})")
                print(f"Saída de erro: {result.stderr}")
                continue
            
            # Carregar a árvore NEWICK gerada
            if os.path.exists(output_tree):
                with open(output_tree, 'r') as f:
                    # Remover o nome 'data.csv' da árvore newick antes de carregar
                    newick_str = f.read()
                    print(f"Conteúdo original do arquivo .newick:")
                    print(newick_str)
                    
                    if 'data.csv' in newick_str:
                        newick_str = newick_str.replace('data.csv', 'root')
                        print(f"Conteúdo após substituição:")
                        print(newick_str)
                    
                    try:
                        tree = toytree.tree(newick_str)
                        print(f"Tipo da árvore: {type(tree)}")
                        print(f"Árvore {i:02d} carregada com sucesso!")
                        cloud_trees.append(tree)
                    except Exception as e:
                        print(f"Erro ao carregar árvore {i:02d}: {str(e)}")
            else:
                print(f"Erro: Arquivo {output_tree} não encontrado após execução do DAMICORE")
        except Exception as e:
            print(f"Erro ao executar DAMICORE para {sample_file}: {str(e)}")

    # === 5. Gerar visualizações ===
    if cloud_trees:
        print("\nGerando visualizações...")
        
        # Gerar árvore de nuvem (cloud tree)
        print("\nIniciando combinação das árvores...")
        print(f"Número total de árvores: {len(cloud_trees)}")
        print(f"Tipo da primeira árvore: {type(cloud_trees[0])}")
        
        # Criar uma nova árvore baseada na primeira
        cloud_tree = cloud_trees[0].copy()
        print("Árvore base criada com sucesso")
        
        # Combinar todas as árvores restantes usando o método correto do ToyTree
        for i, tree in enumerate(cloud_trees[1:], 1):
            print(f"\nCombinando árvore {i} de {len(cloud_trees)-1}")
            print(f"Tipo da árvore {i}: {type(tree)}")
            
            try:
                # Criar uma nova árvore combinada usando a string Newick
                combined_tree = toytree.tree(
                    f"({cloud_tree.write(format=9)},{tree.write(format=9)});"
                )
                cloud_tree = combined_tree
                print(f"Árvore {i} combinada com sucesso!")
            except Exception as e:
                print(f"Erro ao combinar árvore {i}: {str(e)}")
                print(f"Árvore problemática: {tree}")
                raise
        
        # Obter todos os nós da árvore usando o método correto do ToyTree
        all_nodes = cloud_tree.get_tip_labels() + list(cloud_tree.get_node_data().keys())
        print(f"Número total de nós na árvore: {len(all_nodes)}")

        # Criar Canvas para visualização com barplot
        canvas = toyplot.Canvas(width=1200, height=800)
        
        # Adicionar árvore no primeiro eixo
        ax0 = canvas.cartesian(bounds=(50, 600, 50, 700), padding=15)
        cloud_tree.draw(
            axes=ax0,
            tip_labels_align=True,
            tip_labels_style={"font-size": "8px"},
            width=550,
            height=650
        )
        
        # Obter dados para o barplot (suporte dos nós)
        node_data = cloud_tree.get_node_data()
        support_values = []
        
        # Mapear suporte para cada nó na ordem correta
        for node in all_nodes:
            if node in node_data and 'support' in node_data[node]:
                support_values.append(float(node_data[node]['support']))
            else:
                support_values.append(0)
        
        # Adicionar barplot no segundo eixo
        ax1 = canvas.cartesian(bounds=(650, 1150, 50, 700), padding=15)
        ax1.bars(
            np.arange(len(support_values)),
            support_values,
            along='y',
            title="Support Values"
        )
        
        # Estilizar eixos
        ax0.show = False
        ax1.show = True


        # Salvar visualização no diretório correto (subdiretório duplicado)
        visualization_dir = os.path.join(DAMICORE_DIR, "damicore_analysis", "damicore_analysis")
        os.makedirs(visualization_dir, exist_ok=True)
        
        # Salvar arquivos no diretório de visualização
        svg_path = os.path.join(visualization_dir, "cloud_tree_with_barplot.svg")
        newick_path = os.path.join(visualization_dir, "cloud_tree_with_barplot.newick")
        
        # Salvar visualização
        try:
            toyplot.svg.render(canvas, svg_path)
            print(f"Arquivo SVG salvo com sucesso em: {svg_path}")
        except Exception as e:
            print(f"Erro ao salvar arquivo SVG: {e}")
            raise
        
        try:
            cloud_tree.write(newick_path)
            print(f"Arquivo Newick salvo com sucesso em: {newick_path}")
        except Exception as e:
            print(f"Erro ao salvar arquivo Newick: {e}")
            raise
        
        print(f"Visualização salva em: {svg_path}")
        print(f"Árvore combinada salva em: {newick_path}")
        
        # Gerar árvore de consenso usando ToyTree
        try:
            # Definir results_dir corretamente antes de usá-la
            results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
            tree_files = [f for f in os.listdir(results_dir) if f.endswith("-tree.newick")]
            if not tree_files:
                raise ValueError("Nenhuma árvore .newick encontrada para gerar consenso")

            # Carregar todas as árvores
            trees = []
            for tree_file in tree_files:
                tree_path = os.path.join(results_dir, tree_file)
                try:
                    tree = toytree.tree(open(tree_path).read())
                    trees.append(tree)
                except Exception as e:
                    print(f"Erro ao carregar árvore {tree_file}: {e}")
                    continue

            if not trees:
                raise ValueError("Nenhuma árvore válida encontrada para gerar consenso")

            # Gerar árvore de consenso usando DendroPy
            import dendropy
            tree_list = dendropy.TreeList()
            for tree_file in tree_files:
                tree_path = os.path.join(results_dir, tree_file)
                tree_list.read(path=tree_path, schema="newick")
            if not tree_list:
                raise ValueError("Nenhuma árvore válida encontrada para consenso em DendroPy")
            # Consenso majoritário (padrão)
            consensus_tree_dpy = tree_list.consensus(min_freq=0.5)
            consensus_newick = consensus_tree_dpy.as_string("newick")
            print("Árvore de consenso (DendroPy) gerada com sucesso.")
            # Remover prefixo '[&U]' se presente
            if consensus_newick.startswith("[&U]"):
                consensus_newick = consensus_newick.replace("[&U]", "", 1).strip()
            # Carregar consenso no ToyTree para visualização
            consensus_tree = toytree.tree(consensus_newick)

            # === 6. Visualização: Consensus Tree com Barplot (PDF) ===
            visualization_dir = os.path.join(DAMICORE_DIR, "damicore_analysis", "damicore_analysis")
            os.makedirs(visualization_dir, exist_ok=True)
            consensus_barplot_pdf = os.path.join(visualization_dir, "consensus_tree_with_barplot.pdf")
            consensus_newick_path = os.path.join(visualization_dir, "consensus_tree_with_barplot.newick")
            
            # Salvar árvore consenso em formato Newick
            with open(consensus_newick_path, 'w') as f:
                f.write(consensus_tree.write())
            
            # Gerar visualização PDF com barplot (usando função já existente)
            draw_tree_with_barplot(
                consensus_tree,
                original_df,
                consensus_barplot_pdf,
                name_to_index,
                results_dir,
                sample_dir
            )
            print(f"Consensus tree com barplot salva em: {consensus_barplot_pdf}")

        except Exception as e:
            print(f"Erro ao gerar árvore de consenso: {str(e)}")
            raise
        
        print("\nAnálise DAMICORE concluída com sucesso!")
    else:
        print("\nNenhuma árvore foi gerada. Verifique os logs de erro acima.")

def run_pareto_analysis(df, output_dir):
    """Executa a análise de Fronteira de Pareto no DataFrame."""
    print("\n=== Iniciando Análise de Fronteira de Pareto ===")

    # Variáveis disponíveis para filtragem
    available_vars = df.columns.tolist()
    print("Variáveis disponíveis para filtragem:")
    print(", ".join(available_vars))
    
    # Solicitar variáveis de filtragem
    variables_input = input("Digite as variáveis a serem filtradas (separadas por vírgula): ").strip()
    if not variables_input:
        print("Nenhuma variável selecionada. Análise de Pareto cancelada.")
        return

    # Processar variáveis de entrada
    variables = [v.strip() for v in variables_input.split(',')]
    invalid_vars = [v for v in variables if v not in available_vars]
    
    if invalid_vars:
        print(f"Variáveis inválidas: {', '.join(invalid_vars)}")
        print("Análise de Pareto cancelada.")
        return

    # Criar diretório para resultados
    pareto_dir = os.path.join(output_dir, "pareto_analysis")
    os.makedirs(pareto_dir, exist_ok=True)

    # Realizar análise de Pareto
    try:
        # Aqui você pode adicionar a lógica específica para análise de Pareto
        # Por exemplo, criar gráficos, calcular fronteiras, etc.
        print("\nRealizando análise de Pareto...")
        
        # Exemplo de gráfico básico
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x=variables[0], y=variables[1])
        plt.title(f"Análise de Pareto para {variables[0]} vs {variables[1]}")
        plt.savefig(os.path.join(pareto_dir, "pareto_analysis.png"))
        plt.close()
        
        print(f"\nAnálise de Pareto concluída. Resultados salvos em {pareto_dir}")
    except Exception as e:
        print(f"Erro ao realizar análise de Pareto: {str(e)}")

def main():
    """Função principal do script."""
    # Verificar se foi fornecido um arquivo CSV como argumento
    import sys
    if len(sys.argv) != 2:
        print("Uso: python DAMICORE_Pareto_test.py <arquivo_csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Erro: Arquivo {input_file} não encontrado!")
        sys.exit(1)

    # Executar análise DAMICORE
    run_damicore_analysis(input_file)

    # Perguntar se deseja realizar análise de Pareto
    pareto_input = input("\nDeseja realizar a análise de Fronteira de Pareto? (s/n): ").strip().lower()
    if pareto_input == 's':
        # Carregar dados novamente para análise de Pareto
        df = pd.read_csv(input_file, encoding="utf-8", low_memory=False)
        output_dir = os.path.splitext(os.path.basename(input_file))[0]
        run_pareto_analysis(df, output_dir)

if __name__ == "__main__":
    main()
