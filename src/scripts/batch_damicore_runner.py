import json
import os
import subprocess
import sys


def is_fully_processed(output_dir):
    """Verifica se o checkpoint indica processamento completo"""
    checkpoint_path = os.path.join(output_dir, "filograma_checkpoint.json")
    if not os.path.exists(checkpoint_path):
        return False

    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            steps = data.get("completed_steps", {})
            return all(steps.values())
    except Exception as e:
        print(f"⚠️ Erro ao ler checkpoint em {output_dir}: {e}")
        return False


def run_damicore_on_csv(csv_path, script_path, external_output_root=None):
    csv_name = os.path.splitext(os.path.basename(csv_path))[0]

    # Diretório de saída
    if external_output_root:
        output_dir = os.path.join(external_output_root, csv_name)
    else:
        output_dir = os.path.join(os.path.dirname(csv_path), csv_name)

    if is_fully_processed(output_dir):
        print(f"⏭️  Pulando {csv_name}: já processado com sucesso.")
        return

    os.makedirs(output_dir, exist_ok=True)

    print(f"\n🔄 Iniciando processamento: {csv_path}")
    print(f"📁 Salvando em: {output_dir}")

    try:
        result = subprocess.run(
            ["python3", script_path, csv_path],
            cwd=output_dir,
            check=True,
            text=True,
            capture_output=True,
        )
        print(f"✅ Concluído: {csv_path}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao processar {csv_path}:")
        print(e.stdout)
        print(e.stderr)


def main():
    if len(sys.argv) < 2:
        print(
            "Uso: python3 batch_damicore_runner.py <pasta_com_csvs> [caminho_para_drive_externo]"
        )
        sys.exit(1)

    input_dir = sys.argv[1]
    external_output_root = sys.argv[2] if len(sys.argv) > 2 else None
    script_path = os.path.join(
        os.path.dirname(__file__), "DAMICORE_Filograma_script.py"
    )

    if not os.path.isdir(input_dir):
        print(f"❌ Diretório inválido: {input_dir}")
        sys.exit(1)

    if external_output_root and not os.path.isdir(external_output_root):
        print(f"❌ Caminho inválido para drive externo: {external_output_root}")
        sys.exit(1)

    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]

    if not csv_files:
        print("⚠️ Nenhum arquivo .csv encontrado.")
        sys.exit(0)

    for csv_file in csv_files:
        csv_path = os.path.join(input_dir, csv_file)
        run_damicore_on_csv(csv_path, script_path, external_output_root)


if __name__ == "__main__":
    main()
