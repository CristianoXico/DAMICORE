from unidecode import unidecode
from unidecode import unidecode
import argparse
import os
import sys
import pandas as pd
from fs_opa import aplicar_fs_opa, build_category_tree
from damicore_pipeline import consensus_tree_from_dataframe
from pareto import non_dominated_sort_fast


def main():
    parser = argparse.ArgumentParser(description='DAMICORE - Análise Multi-Critério')
    parser.add_argument('--input', type=str, required=True, help='Caminho para o arquivo CSV de entrada')
    parser.add_argument('--vars', type=str, required=False, help='Índices das variáveis para Pareto, separados por vírgula (ex: 2,5,7)')
    parser.add_argument('--categories', type=int, choices=[2,4,8], default=2, help='Número de categorias (2, 4 ou 8) para visualização das árvores')
    parser.add_argument('--agg', type=str, help='Agregações para colunas compostas, separadas por vírgula (ex: mean,median,mode)')
    parser.add_argument('--notebook-mode', action='store_true', help='Ativa modo compatível com notebook DAMICORE')
    parser.add_argument('--ncd-matrix', action='store_true', help='Calcula e imprime matriz NCD em Python (sem DAMICORE CLI)')
    args = parser.parse_args()

    print(f"Lendo arquivo: {args.input}")
    import pandas as pd
    df = pd.read_csv(args.input)
    print(df.head())

    # 1. Unificar valores compostos em cada célula usando média simples
    def aggregate_cell(cell):
        # Se for lista, set ou tuple, retorna média
        if isinstance(cell, (list, set, tuple)):
            vals = [float(x) for x in cell if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())]
            return sum(vals)/len(vals) if vals else None
        # Se for dict, retorna média dos valores
        if isinstance(cell, dict):
            vals = [float(x) for x in cell.values() if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())]
            return sum(vals)/len(vals) if vals else None
        # Se for string representando set/list, tenta eval
        if isinstance(cell, str) and (cell.strip().startswith('{') or cell.strip().startswith('[')):
            import ast
            try:
                parsed = ast.literal_eval(cell)
                return aggregate_cell(parsed)
            except Exception:
                return None
        # Caso contrário, tenta converter para float
        try:
            return float(cell)
        except Exception:
            return None

    # Se notebook_mode, pula agregação/interação
    if not args.notebook_mode:
        # Detecta colunas compostas
        composed_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, (list, set, tuple, dict)) or (isinstance(x, str) and (x.strip().startswith('{') or x.strip().startswith('[')))).any()]
        import statistics
        if composed_cols:
            print(f"Colunas compostas detectadas: {composed_cols}.")
            agg_map = {'mean': lambda vals: sum(vals)/len(vals) if vals else None,
                      'median': lambda vals: statistics.median(vals) if vals else None,
                      'mode': lambda vals: statistics.mode(vals) if vals else None,
                      'sum': lambda vals: sum(vals) if vals else None}
            agg_choices = []
            if args.agg:
                agg_choices = [a.strip().lower() for a in args.agg.split(',')]
                print(f"Usando agregações fornecidas por argumento: {agg_choices}")
            for i, col in enumerate(composed_cols):
                if agg_choices and i < len(agg_choices) and agg_choices[i] in agg_map:
                    agg_func = agg_map[agg_choices[i]]
                    print(f"Coluna {col}: agregação = {agg_choices[i]}")
                elif not agg_choices:
                    print(f"\nColuna: {col}")
                    print("Escolha a estatística de agregação para unificar cada célula:")
                    print("[1] Média (mean) [default]")
                    print("[2] Mediana (median)")
                    print("[3] Moda (mode)")
                    print("[4] Soma (sum)")
                    choice = input("Digite o número da opção desejada para esta coluna (pressione Enter para média): ").strip()
                    if choice == '2':
                        agg_func = agg_map['median']
                    elif choice == '3':
                        agg_func = agg_map['mode']
                    elif choice == '4':
                        agg_func = agg_map['sum']
                    else:
                        agg_func = agg_map['mean']
                else:
                    print(f"Coluna {col}: agregação padrão = média (mean)")
                    agg_func = agg_map['mean']

                def aggregate_cell_custom(cell):
                    # Se for lista, set ou tuple
                    if isinstance(cell, (list, set, tuple)):
                        vals = [float(x) for x in cell if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())]
                        return agg_func(vals)
                    # Se for dict
                    if isinstance(cell, dict):
                        vals = [float(x) for x in cell.values() if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())]
                        return agg_func(vals)
                    # Se for string representando set/list
                    if isinstance(cell, str) and (cell.strip().startswith('{') or cell.strip().startswith('[')):
                        import ast
                        try:
                            parsed = ast.literal_eval(cell)
                            return aggregate_cell_custom(parsed)
                        except Exception:
                            return None
                    # Caso contrário, tenta converter para float
                    try:
                        return float(cell)
                    except Exception:
                        return None

                df[col] = df[col].apply(aggregate_cell_custom)
        else:
            print("Nenhuma coluna composta detectada. Seguindo normalmente.")

    # 1. Leitura e Pré-processamento
    print("\n=== Módulo 1: Leitura e Pré-processamento ===\n")
    
    # 1.1 Leitura do arquivo CSV
    print("1. Lendo arquivo de entrada...")
    print(f"   - Arquivo: {args.input}")
    print(f"   - Total de linhas: {len(df)}")
    print(f"   - Colunas: {', '.join(df.columns)}")
    
    # 1.2 Detecção e processamento de colunas compostas
    print("\n2. Verificando colunas compostas...")
    compound_columns = []
    for col in df.columns:
        # Verifica se a coluna contém strings que parecem listas ou dicionários
        if df[col].apply(lambda x: isinstance(x, str) and ('[' in x or '{' in x)).any():
            compound_columns.append(col)
    
    if compound_columns:
        print(f"   - Colunas compostas detectadas: {', '.join(compound_columns)}")
        
        # 1.3 Processamento de colunas compostas
        print("\n3. Processando colunas compostas...")
        print("   Selecione o método de agregação para cada coluna:")
        print("   [1] Média (para valores numéricos)")
        print("   [2] Mediana (para valores numéricos)")
        print("   [3] Moda (para valores categóricos)")
        print("   [4] Soma (para valores numéricos)")
        
        for col in compound_columns:
            while True:
                try:
                    choice = int(input(f"   Método para '{col}': ").strip())
                    if choice in [1, 2, 3, 4]:
                        break
                    print("      ❌ Opção inválida. Escolha 1, 2, 3 ou 4.")
                except ValueError:
                    print("      ❌ Por favor, digite um número.")
            
            # Aplica o método de agregação selecionado
            if choice == 1:  # Média
                df[col] = df[col].apply(lambda x: np.mean(eval(x)) if pd.notna(x) else np.nan)
                print(f"      ✅ Aplicada MÉDIA em '{col}'")
            elif choice == 2:  # Mediana
                df[col] = df[col].apply(lambda x: np.median(eval(x)) if pd.notna(x) else np.nan)
                print(f"      ✅ Aplicada MEDIANA em '{col}'")
            elif choice == 3:  # Moda
                from statistics import mode
                df[col] = df[col].apply(lambda x: mode(eval(x)) if pd.notna(x) else np.nan)
                print(f"      ✅ Aplicada MODA em '{col}'")
            elif choice == 4:  # Soma
                df[col] = df[col].apply(lambda x: sum(eval(x)) if pd.notna(x) else 0)
                print(f"      ✅ Aplicada SOMA em '{col}'")
    else:
        print("   Nenhuma coluna composta detectada.")
    
    # 1.4 Resumo do pré-processamento
    print("\n4. Resumo do pré-processamento:")
    print(f"   - Total de colunas: {len(df.columns)}")
    print(f"   - Total de linhas: {len(df)}")
    print("   - Tipos de dados por coluna:")
    for col, dtype in df.dtypes.items():
        print(f"     - {col}: {dtype}")
    
    # 1.5 Opção para visualizar as primeiras linhas
    if input("\nDeseja visualizar as primeiras linhas do dataset processado? (s/n): ").strip().lower() == 's':
        print("\nPrimeiras 5 linhas do dataset processado:")
        print(df.head())
    
    print("\n✅ Pré-processamento concluído com sucesso!\n")

    # 4. Escolher variáveis para metodologia Pareto (apenas uma vez, após as árvores)
    num_cols = list(df.select_dtypes(include=["number"]).columns)
    if args.vars:
        pareto_indices = [int(i) for i in args.vars.split(",") if i.strip().isdigit()]
    else:
        print("\nVariáveis disponíveis para Pareto:")
        for idx, col in enumerate(num_cols):
            print(f"[{idx}] {col}")
        entrada = input("Digite os índices das variáveis para Pareto, separados por vírgula: ")
        pareto_indices = [int(i) for i in entrada.split(",") if i.strip().isdigit() and int(i) < len(num_cols)]
    pareto_vars = [(i, num_cols[i]) for i in pareto_indices]
    if pareto_vars:
        print("\nVariáveis selecionadas para Pareto:")
        for idx, nome in pareto_vars:
            print(f"[{idx}] {nome}")
        # Chamar metodologia de Pareto
        print("Executando metodologia de fronteira de Pareto...")
        try:
            var_names = [nome for _, nome in pareto_vars]
            resultado = non_dominated_sort_fast(df[var_names].values)
            print("Calculando fronteira de Pareto...")
            pareto_df = df[var_names].copy()
            pareto_df.insert(0, 'pareto_rank', resultado)
            print(pareto_df.head())
            import pathlib
            import getpass
            import platform
            def get_downloads_folder():
                # Windows
                if platform.system() == "Windows":
                    return str(pathlib.Path.home() / "Downloads")
                # Mac/Linux
                return str(pathlib.Path.home() / "Downloads")
            downloads_folder = get_downloads_folder()
            out_name = f"output_pareto_{'_'.join(var_names)}.csv"
            out_path = os.path.join(downloads_folder, out_name)
            pareto_df.to_csv(out_path, index=False)
            print(f"Arquivo de saída Pareto salvo em: {out_path}")
        except Exception as e:
            print("Erro ao executar Pareto:", e)
    else:
        print("Nenhuma variável selecionada para Pareto.")

    # 4. Seleção de variáveis para análise de Pareto
    print("\nColunas disponíveis para análise de Pareto:")
    for i, col in enumerate(df.columns):
        print(f"[{i}] {col}")

    if args.vars:
        indices = [int(idx.strip()) for idx in args.vars.split(',')]
        print(f"Usando variáveis dos índices fornecidos: {indices}")
    else:
        indices = input("Digite os índices das variáveis (separados por vírgula): ")
        indices = [int(idx.strip()) for idx in indices.split(',')]
    vars_pareto = [df.columns[idx] for idx in indices]

    print(f"Variáveis selecionadas: {vars_pareto}")
    objs = df[vars_pareto].to_numpy()

    # 3. Aplicar Pareto
    print("\nCalculando fronteira de Pareto...")
    ranks = non_dominated_sort_fast(objs)
    df['pareto_rank'] = ranks
    print(df[['pareto_rank'] + vars_pareto].head())
    # Salvar resultado com nome dinâmico
    var_str = '_'.join(vars_pareto)
    output_filename = f'output_pareto_{var_str}.csv'
    df.to_csv(output_filename, index=False)
    print(f"\nArquivo '{output_filename}' gerado com os ranks de Pareto.")

if __name__ == "__main__":
    main()
