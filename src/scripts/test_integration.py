#!/usr/bin/env python3
"""
Script de teste para verificar a integração entre DAMICORE_File_Slicer_Processor.py e DAMICORE_Filograma_script.py
"""

import os
import subprocess
import sys

def test_integration():
    """Testa a integração entre os scripts"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filograma_path = os.path.join(script_dir, "DAMICORE_Filograma_script.py")
    slicer_path = os.path.join(script_dir, "DAMICORE_File_Slicer_Processor.py")
    
    # Verificar se os scripts existem
    if not os.path.exists(filograma_path):
        print(f"❌ Script Filograma não encontrado: {filograma_path}")
        return False
    
    if not os.path.exists(slicer_path):
        print(f"❌ Script Slicer não encontrado: {slicer_path}")
        return False
    
    # Criar um arquivo CSV de teste pequeno
    test_csv_path = "/tmp/test_small_file.csv"
    if not os.path.exists(test_csv_path):
        print(f"Criando arquivo CSV de teste: {test_csv_path}")
        with open(test_csv_path, 'w') as f:
            f.write("col1,col2,col3,col4\n")
            for i in range(20):
                f.write(f"{i},{i*2},{i*3},{i*4}\n")
    
    # Simular a chamada que o DAMICORE_File_Slicer_Processor.py faz para o DAMICORE_Filograma_script.py
    print(f"📋 Testando integração entre scripts")
    print(f"📊 Arquivo CSV: {test_csv_path}")
    
    # Criar diretório de saída para o teste
    test_output_dir = "/tmp/test_integration_output"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Simular a chamada do subprocess
    cmd = ["python3", filograma_path, test_csv_path]
    print(f"🔧 Comando: {' '.join(cmd)}")
    
    # Mudar para diretório de saída
    original_cwd = os.getcwd()
    os.chdir(test_output_dir)
    
    try:
        # Executar com timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minuto
        )
        
        # Verificar resultado
        if result.returncode == 0:
            print(f"✅ Integração testada com sucesso")
            return True
        else:
            print(f"❌ Falha na integração")
            print("📋 Saída de erro:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout ao executar o comando")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar o comando: {e}")
        return False
    finally:
        # Voltar para diretório original
        os.chdir(original_cwd)

if __name__ == "__main__":
    success = test_integration()
    
    if success:
        print("\n✅ Teste de integração concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste de integração falhou!")
        sys.exit(1)
