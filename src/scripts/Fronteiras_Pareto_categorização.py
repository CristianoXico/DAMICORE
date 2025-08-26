import os
import re
from collections import Counter
from urllib.parse import urlparse

import gdown
import numpy as np
import pandas as pd
import requests


def load_data(input_path: str) -> pd.DataFrame:
    """
    Carrega dados de um caminho local ou URL.
    Suporta: CSV, XLSX (local e online), Google Drive.
    """
    if input_path.startswith("http"):
        # Google Drive link
        if "drive.google.com" in input_path:
            file_id = None
            if "id=" in input_path:
                file_id = input_path.split("id=")[1]
            elif "/d/" in input_path:
                file_id = input_path.split("/d/")[1].split("/")[0]

            if not file_id:
                raise ValueError(
                    "Não foi possível extrair o ID do link do Google Drive."
                )

            output_file = "temp_download.csv"
            gdown.download(id=file_id, output=output_file, quiet=False)
            input_path = output_file

        else:
            # Download direto com requests
            response = requests.get(input_path)
            if response.status_code != 200:
                raise ValueError(f"Erro ao baixar arquivo: {response.status_code}")

            # Detecta extensão
            parsed_url = urlparse(input_path)
            ext = os.path.splitext(parsed_url.path)[1].lower()

            output_file = f"temp_download{ext}"
            with open(output_file, "wb") as f:
                f.write(response.content)
            input_path = output_file

    # Detecta extensão local
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(input_path)
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(input_path)
    else:
        raise ValueError(f"Extensão de arquivo não suportada: {ext}")

    return df


def categorize_dataframe(df: pd.DataFrame):
    """
    Identifica colunas tipo array/string e as categoriza pela frequência dos elementos.
    Retorna df categorizado e dicionário de legendas.
    """
    potential_array_columns = []
    for col in df.columns:
        if df[col].dtype == "object":
            if df[col].dropna().astype(str).str.contains(",").any():
                potential_array_columns.append(col)

    categorization_legends = {}
    df_categorized = df.copy()

    for col in potential_array_columns:
        modal_elements_list = []

        for _, row in df.iterrows():
            val = row[col]
            if isinstance(val, str):
                elements = [e.strip() for e in val.split(",") if e.strip()]
                if elements:
                    counts = Counter(elements)
                    modal_element = counts.most_common(1)[0][0]
                    modal_elements_list.append(modal_element)
                else:
                    modal_elements_list.append(np.nan)
            elif pd.notna(val):
                modal_elements_list.append(val)
            else:
                modal_elements_list.append(np.nan)

        modal_elements_series = pd.Series(modal_elements_list, index=df.index)
        modal_element_counts_series = modal_elements_series.value_counts(dropna=False)

        # Ordenar do menos frequente para o mais frequente
        sorted_unique_modal_elements = modal_element_counts_series.sort_values(
            ascending=True
        ).index.tolist()
        legend_mapping = {
            modal_value: code
            for code, modal_value in enumerate(sorted_unique_modal_elements)
        }

        categorization_legends[col] = {
            "legend": legend_mapping,
            "frequencies": modal_element_counts_series.to_dict(),
        }

        df_categorized.loc[:, col] = modal_elements_series.map(legend_mapping)

    return df_categorized, categorization_legends


def save_results(df_categorized, categorization_legends, base_filename="output"):
    """
    Salva o DataFrame categorizado em CSV e as legendas em TXT.
    """
    df_categorized.to_csv(f"{base_filename}_categorized.csv", index=False)

    legends_file = f"categorization_legends_{base_filename}.txt"
    with open(legends_file, "w") as f:
        for col, legend_data in categorization_legends.items():
            legend = legend_data["legend"]
            freqs = legend_data["frequencies"]

            f.write(f"Column '{col}':\n")
            f.write("{")
            sorted_legend_items = sorted(legend.items(), key=lambda item: item[1])
            for i, (key, value) in enumerate(sorted_legend_items):
                key_str = "nan" if pd.isna(key) else f"'{key}'"
                freq = freqs.get(key, 0)
                f.write(f"{key_str}: {value} ({freq})")
                if i < len(sorted_legend_items) - 1:
                    f.write(", ")
            f.write("}\n\n")

    print(f"Resultados salvos em:\n- {base_filename}_categorized.csv\n- {legends_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Processa dados para análise de Fronteira de Pareto.')
    parser.add_argument('input_file', type=str, help='Caminho para o arquivo de entrada (CSV/XLSX) ou URL')
    parser.add_argument('--output', '-o', type=str, default='output', help='Nome base para os arquivos de saída (sem extensão)')
    args = parser.parse_args()
    
    try:
        # Carrega os dados
        print(f"Carregando dados de: {args.input_file}")
        df = load_data(args.input_file)
        print(f"Dados carregados com sucesso. Dimensões: {df.shape}")
        
        # Processa os dados
        print("Processando categorização...")
        df_categorized, legends = categorize_dataframe(df)
        
        # Salva os resultados
        print(f"Salvando resultados em {args.output}.csv e {args.output}_legendas.txt")
        save_results(df_categorized, legends, args.output)
        print("Processo concluído com sucesso!")
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}\n")
        print("Certifique-se de que:")
        print("1. O caminho do arquivo está correto")
        print("2. O arquivo está no formato suportado (CSV ou XLSX)")
        print("3. Você tem permissão para acessar o arquivo")
        if "drive.google.com" in str(args.input_file):
            print("4. O link do Google Drive é público ou você tem permissão de acesso")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
    # input_path = "https://example.com/arquivo.csv"
    # input_path = "https://drive.google.com/file/d/FILE_ID/view?usp=sharing"
    input_path = "dados.csv"  # ajuste aqui

    df = load_data(input_path)
    df_categorized, categorization_legends = categorize_dataframe(df)
    save_results(df_categorized, categorization_legends, base_filename="saida")
