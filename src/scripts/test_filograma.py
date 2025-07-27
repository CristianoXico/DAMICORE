#!/usr/bin/env python3
"""
Script de teste para verificar se o DAMICORE_Filograma_script.py restaurado funciona corretamente
"""

import os
import subprocess
import sys
import time

def test_filograma_script():
    """Testa a execução do DAMICORE_Filograma_script.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filograma_path = os.path.join(script_dir, "DAMICORE_Filograma_script.py")
    
    # Verificar se o script existe
    if not os.path.exists(filograma_path):
        print(f"❌ Script não encontrado: {filograma_path}")
        return False
    
    # Criar um arquivo CSV de teste pequeno
    test_csv_path = "/tmp/test_small_file.csv"
    if not os.path.exists(test_csv_path):
        print(f"Criando arquivo CSV de teste: {test_csv_path}")
        with open(test_csv_path, 'w') as f:
            f.write("col1,col2,col3,col4\n")
            for i in range(20):
                f.write(f"{i},{i*2},{i*3},{i*4}\n")
    
    # Criar diretório de saída
    test_output_dir = "/tmp/test_filograma_output"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Executar o script
    print(f"📋 Testando execução do script: {filograma_path}")
    print(f"📊 Arquivo CSV: {test_csv_path}")
    print(f"📁 Diretório de saída: {test_output_dir}")
    
    cmd = ["python3", filograma_path, test_csv_path]
    print(f"🔧 Comando: {' '.join(cmd)}")
    
    # Mudar para diretório de saída
    original_cwd = os.getcwd()
    os.chdir(test_output_dir)
    
    try:
        # Executar com timeout
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        elapsed_time = time.time() - start_time
        
        # Verificar resultado
        if result.returncode == 0:
            print(f"✅ Script executado com sucesso em {elapsed_time:.2f} segundos")
            print("📋 Saída:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            
            # Verificar se arquivos newick foram gerados
            newick_files = [f for f in os.listdir() if f.endswith('.newick')]
            if newick_files:
                print(f"✅ {len(newick_files)} arquivos newick gerados")
                print(f"📋 Exemplos: {', '.join(newick_files[:3])}")
            else:
                print("❌ Nenhum arquivo newick gerado")
            
            return True
        else:
            print(f"❌ Script falhou com código {result.returncode}")
            print("📋 Saída de erro:")
            print(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout após {elapsed_time:.2f} segundos")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar script: {e}")
        return False
    finally:
        # Voltar para diretório original
        os.chdir(original_cwd)

if __name__ == "__main__":
    success = test_filograma_script()
    
    if success:
        print("\n✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)
