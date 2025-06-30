#!/usr/bin/env python3
import os
import configparser
import sys
from pathlib import Path

def find_damicore_cli():
    """Localiza o caminho do damicore.py na estrutura do projeto."""
    possible_paths = [
        "damicore_py3/damicore.py",
        "../damicore_py3/damicore.py",
        "DAMICORE/damicore_py3/damicore.py"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None

def create_config():
    """Cria o arquivo config.ini baseado no ambiente atual."""
    config = configparser.ConfigParser()
    
    # Detecta o diretório base do projeto
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Paths
    config['Paths'] = {
        'DAMICORE_CLI_PATH': find_damicore_cli() or 'damicore_py3/damicore.py',
    }
    
    # Scripts
    config['Scripts'] = {
        'DAMICORE_PARETO_SCRIPT': 'scripts_modulares/DAMICORE_Pareto_script.py',
        'PARETO_FRONTIER_SCRIPT': 'scripts_modulares/pareto_frontier_local.py',
    }
    
    # Data
    config['Data'] = {
        'INPUT_DIR': 'test_data_scripts_modulares',
        'EXAMPLES_DIR': 'examples',
    }
    
    # Output
    config['Output'] = {
        'RESULTS_DIR': 'results',
        'TEMP_DIR': 'temp',
    }
    
    # Escreve o arquivo de configuração
    config_path = os.path.join(project_root, 'config.ini')
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"Arquivo de configuração criado em: {config_path}")
    return config_path

def validate_config(config_path):
    """Valida se os caminhos essenciais existem."""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Verifica o caminho do DAMICORE CLI
    damicore_cli = config['Paths']['DAMICORE_CLI_PATH']
    if not os.path.exists(damicore_cli):
        print(f"Aviso: DAMICORE CLI não encontrado em {damicore_cli}")
    
    # Verifica diretórios essenciais
    for dir_path in [config['Data']['INPUT_DIR'], config['Data']['EXAMPLES_DIR']]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Diretório criado: {dir_path}")

def main():
    print("=== Configuração do DAMICORE ===")
    config_path = create_config()
    validate_config(config_path)
    print("\nConfiguração concluída com sucesso!")

if __name__ == "__main__":
    main()
