from split_export import export_split_columns
import os

def split_and_export(df, split_column, out_base_dir, prefix):
    """
    Para cada valor único em split_column, cria um DataFrame filtrado e exporta todas as colunas usando export_split_columns,
    salvando na pasta <out_base_dir>/<prefix><valor>/
    """
    unique_vals = df[split_column].dropna().unique()
    for val in unique_vals:
        df_split = df[df[split_column] == val]
        split_dir = os.path.join(out_base_dir, f"{prefix}{val}")
        print(f"Exportando split: {split_dir} ({len(df_split)} linhas)")
        export_split_columns(df_split, split_dir)

# Exemplo de uso:
# split_and_export(df, 'categoria', './splits', 'B2C_')
